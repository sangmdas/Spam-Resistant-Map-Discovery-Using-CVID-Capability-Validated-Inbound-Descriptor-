from dataclasses import replace
from datetime import datetime, timedelta, timezone
from itertools import count

from .crypto import HMACSigner
from .models import (AuthorityPhase, Channel, CommunicationAuthority, Direction,
                     Effect, QueryContext, QueryScopedHandle)
from .state import ProtectedStateStore


class AuthorityService:
    def __init__(self, platform_id: str, enforcement_point_id: str, signer: HMACSigner, state: ProtectedStateStore):
        self.platform_id = platform_id; self.enforcement_point_id = enforcement_point_id
        self.signer = signer; self.state = state; self._ids = count(1)

    def create_context(self, inquiry_id, user_binding, listing_ids, valid_from, valid_until, region=""):
        context = QueryContext(f"query-{next(self._ids)}", inquiry_id, user_binding, tuple(listing_ids), valid_from, valid_until, region)
        self.state.register_context(context); return context

    def create_handle(self, context: QueryContext, expires_at: datetime):
        if context.query_context_id not in self.state.contexts: raise ValueError("query context is not registered")
        if expires_at > context.valid_until: raise ValueError("handle cannot outlive query context")
        handle = QueryScopedHandle(f"cvid-{next(self._ids)}", context.query_context_id, context.user_binding, self.platform_id, expires_at)
        self.state.register_handle(handle); return handle

    def issue_preview(self, context, handle, business, actor, property_id, channel=Channel.VOICE,
                      effect=Effect.PREVIEW_CALL, purpose="initial-enquiry", quota=1, duration=timedelta(minutes=2),
                      now=None, direction=Direction.BUSINESS_TO_USER, authorized_actors=(), device_binding=""):
        now = now or datetime.now(timezone.utc)
        return self._issue(context, handle, business, actor, property_id, AuthorityPhase.PREVIEW, channel, effect,
                           purpose, quota, duration, now, direction, authorized_actors, False, False, device_binding)

    def issue_future(self, context, handle, business, actor, property_id, channel=Channel.VOICE,
                     effect=Effect.FUTURE_CONTACT, purpose="continued-enquiry", quota=3, duration=timedelta(hours=72),
                     now=None, direction=Direction.BUSINESS_TO_USER, authorized_actors=(),
                     require_selection=True, require_commercial=False, device_binding=""):
        now = now or datetime.now(timezone.utc)
        key = (context.query_context_id, property_id, business)
        if require_selection and key not in self.state.selected: raise PermissionError("future authority requires current user selection")
        if require_commercial and key not in self.state.commercial: raise PermissionError("future authority requires current commercial state")
        return self._issue(context, handle, business, actor, property_id, AuthorityPhase.FUTURE, channel, effect,
                           purpose, quota, duration, now, direction, authorized_actors, require_selection,
                           require_commercial, device_binding)

    def _issue(self, context, handle, business, actor, property_id, phase, channel, effect, purpose, quota,
               duration, now, direction, authorized_actors, selection_required, commercial_required, device_binding):
        if context.query_context_id not in self.state.contexts: raise ValueError("query context is not registered")
        if handle.handle_id not in self.state.handles or handle.query_context_id != context.query_context_id: raise ValueError("handle is not bound to query")
        if property_id not in context.listing_ids: raise ValueError("property is outside query results")
        if not (context.valid_from <= now < context.valid_until): raise ValueError("query context is inactive")
        end = min(now + duration, context.valid_until, handle.expires_at)
        actors = tuple(dict.fromkeys((actor,) + tuple(authorized_actors)))
        aid = f"authority-{next(self._ids)}"; nonce = f"nonce-{next(self._ids)}"
        authority = CommunicationAuthority(aid, context.inquiry_id, context.query_context_id, context.user_binding,
            handle.handle_id, actor, business, actors, property_id, phase, direction, channel, purpose, effect, now,
            end, nonce, quota, self.state.revocation_epochs[context.query_context_id],
            self.state.policy_epochs[context.query_context_id], self.enforcement_point_id, commercial_required,
            selection_required, device_binding)
        authority = self.signer.sign(authority); self.state.register_authority(authority); return authority
