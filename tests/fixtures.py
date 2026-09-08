import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from map_cvid import *

NOW = datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc)
KEY = b"reference-only-test-key-32-bytes-minimum!!"


def world(selection=True, commercial=True, preview=True, quota=1, device_binding=""):
    state = ProtectedStateStore(); signer = HMACSigner(KEY)
    service = AuthorityService("maps.example", "edge:west", signer, state)
    context = service.create_context("inquiry-1007", "user:A", ("property:P1", "property:P2"), NOW - timedelta(minutes=1), NOW + timedelta(hours=96), "region:opaque")
    handle = service.create_handle(context, NOW + timedelta(hours=90))
    if selection: state.set_selection(context.query_context_id, "property:P1", "business:D1")
    if commercial: state.set_commercial(context.query_context_id, "property:P1", "business:D1")
    if preview:
        authority = service.issue_preview(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, quota=quota, device_binding=device_binding)
    else:
        authority = service.issue_future(context, handle, "business:D1", "actor:D1", "property:P1", now=NOW, quota=quota, require_selection=True, require_commercial=True, device_binding=device_binding)
    enforcement = CommunicationEnforcementPoint("edge:west", signer, state)
    allocator = ResourceAllocator("edge:west", signer, state)
    return state, signer, service, context, handle, authority, enforcement, allocator


def attempt(authority, **changes):
    fields = dict(transaction_id="transaction-1", authority_id=authority.authority_id,
        observed_query_context=authority.query_context_id, observed_inquiry_id=authority.inquiry_id,
        observed_business_identity=authority.business_identity, observed_actor_id=authority.requesting_actor_id,
        observed_user_binding=authority.user_binding, observed_property_id=authority.property_id,
        observed_handle=authority.handle_id, observed_phase=authority.phase, observed_direction=authority.direction,
        observed_channel=authority.channel, observed_purpose=authority.purpose,
        observed_effect=authority.permitted_effect, observed_nonce=authority.nonce,
        observed_enforcement_point=authority.enforcement_point_id,
        observed_device_binding=authority.device_binding)
    fields.update(changes); return AttemptDescriptor(**fields)


def resign(authority, signer, **changes):
    return signer.sign(replace(authority, **changes, signature=""))
