from dataclasses import replace
from datetime import datetime, timedelta, timezone
from itertools import count

from .crypto import HMACSigner
from .models import AttemptDescriptor, BoundedReleaseCapability, CommunicationAuthority, Decision
from .state import ProtectedStateStore


class CommunicationEnforcementPoint:
    def __init__(self, enforcement_point_id: str, signer: HMACSigner, state: ProtectedStateStore):
        self.id = enforcement_point_id; self.signer = signer; self.state = state; self._ids = count(1)

    def evaluate(self, authority: CommunicationAuthority, attempt: AttemptDescriptor, now=None) -> Decision:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None: raise ValueError("evaluation time must be timezone-aware")
        now = now.astimezone(timezone.utc)
        if not self.signer.verify(authority): return Decision(False, "AUTHORITY_INTEGRITY_INVALID")
        if attempt.authority_id != authority.authority_id: return Decision(False, "AUTHORITY_ID_MISMATCH")
        if now < authority.validity_start: return Decision(False, "AUTHORITY_NOT_YET_VALID")
        if now >= authority.validity_end: return Decision(False, "AUTHORITY_EXPIRED")
        checks = (
            ("QUERY_MISMATCH", authority.query_context_id, attempt.observed_query_context),
            ("INQUIRY_MISMATCH", authority.inquiry_id, attempt.observed_inquiry_id),
            ("BUSINESS_MISMATCH", authority.business_identity, attempt.observed_business_identity),
            ("ACTOR_UNAUTHORIZED", True, attempt.observed_actor_id in authority.authorized_actor_ids),
            ("USER_BINDING_MISMATCH", authority.user_binding, attempt.observed_user_binding),
            ("PROPERTY_MISMATCH", authority.property_id, attempt.observed_property_id),
            ("HANDLE_MISMATCH", authority.handle_id, attempt.observed_handle),
            ("PHASE_MISMATCH", authority.phase, attempt.observed_phase),
            ("DIRECTION_MISMATCH", authority.direction, attempt.observed_direction),
            ("CHANNEL_MISMATCH", authority.channel, attempt.observed_channel),
            ("PURPOSE_MISMATCH", authority.purpose, attempt.observed_purpose),
            ("EFFECT_MISMATCH", authority.permitted_effect, attempt.observed_effect),
            ("NONCE_MISMATCH", authority.nonce, attempt.observed_nonce),
            ("ENFORCEMENT_POINT_MISMATCH", authority.enforcement_point_id, attempt.observed_enforcement_point),
            ("DEVICE_BINDING_MISMATCH", authority.device_binding, attempt.observed_device_binding),
        )
        for code, expected, actual in checks:
            if expected != actual: return Decision(False, code)
        state_code = self.state.inspect(authority, now)
        if state_code != "OK": return Decision(False, state_code)
        code, reservation_id, idempotent = self.state.reserve(authority.authority_id, attempt.transaction_id)
        if code != "OK": return Decision(False, code, reservation_id, idempotent=idempotent)
        capability = BoundedReleaseCapability(f"brc-{next(self._ids)}", authority.authority_id, attempt.transaction_id,
            reservation_id, attempt.observed_actor_id, f"resource:{attempt.observed_channel.value}:{attempt.transaction_id}",
            attempt.observed_effect, self.id, min(authority.validity_end, now + timedelta(seconds=5)))
        capability = self.signer.sign(capability)
        return Decision(True, "AUTHORIZED", reservation_id, capability, idempotent)


class ResourceAllocator:
    """Only this component creates the simulated external communication effect."""
    def __init__(self, enforcement_point_id: str, signer: HMACSigner, state: ProtectedStateStore):
        self.id = enforcement_point_id; self.signer = signer; self.state = state; self.effects: dict[str, str] = {}

    def allocate(self, capability: BoundedReleaseCapability | None, actor_id: str, resource_id: str, now=None) -> Decision:
        now = now or datetime.now(timezone.utc)
        if capability is None: return Decision(False, "CAPABILITY_REQUIRED")
        if not self.signer.verify(capability): return Decision(False, "CAPABILITY_INTEGRITY_INVALID")
        if now.tzinfo is None: raise ValueError("allocation time must be timezone-aware")
        now = now.astimezone(timezone.utc)
        if now >= capability.expires_at: return Decision(False, "CAPABILITY_EXPIRED")
        if capability.enforcement_point_id != self.id: return Decision(False, "CAPABILITY_AUDIENCE_MISMATCH")
        if capability.actor_id != actor_id: return Decision(False, "CAPABILITY_ACTOR_MISMATCH")
        if capability.resource_id != resource_id: return Decision(False, "CAPABILITY_RESOURCE_MISMATCH")
        code, idempotent = self.state.commit(capability.reservation_id)
        if code != "OK": return Decision(False, code, capability.reservation_id)
        previous = self.effects.get(capability.transaction_id)
        if previous is not None and previous != resource_id: return Decision(False, "TRANSACTION_EFFECT_CONFLICT", capability.reservation_id)
        self.effects[capability.transaction_id] = resource_id
        return Decision(True, "RESOURCE_ALLOCATED", capability.reservation_id, capability, idempotent)
