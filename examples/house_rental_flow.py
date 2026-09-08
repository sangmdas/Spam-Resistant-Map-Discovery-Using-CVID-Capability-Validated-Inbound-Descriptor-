"""Runnable Q1007 / P1 / D1 preview-to-future example."""
from datetime import datetime, timedelta, timezone
from map_cvid import *

now=datetime.now(timezone.utc); signer=HMACSigner(b"example-only-key-material-at-least-32-bytes")
state=ProtectedStateStore(); authority_service=AuthorityService("map:B","edge:E1",signer,state)
query=authority_service.create_context("inquiry:house-near-me","user:A",("property:P1","property:P2"),now,now+timedelta(days=4))
cvid=authority_service.create_handle(query,now+timedelta(days=3))
preview=authority_service.issue_preview(query,cvid,"business:D1","actor:D1","property:P1",now=now)
edge=CommunicationEnforcementPoint("edge:E1",signer,state); allocator=ResourceAllocator("edge:E1",signer,state)

def observed(authority, tx):
    return AttemptDescriptor(tx,authority.authority_id,authority.query_context_id,authority.inquiry_id,
        authority.business_identity,authority.requesting_actor_id,authority.user_binding,authority.property_id,
        authority.handle_id,authority.phase,authority.direction,authority.channel,authority.purpose,
        authority.permitted_effect,authority.nonce,authority.enforcement_point_id)

decision=edge.evaluate(preview,observed(preview,"preview-call-1"),now)
result=allocator.allocate(decision.capability,"actor:D1",decision.capability.resource_id,now)
print("preview:",result.code)

# Preview did not silently create future reachability. A new selection and authority are required.
state.set_selection(query.query_context_id,"property:P1","business:D1")
future=authority_service.issue_future(query,cvid,"business:D1","actor:D1","property:P1",now=now,quota=3)
decision=edge.evaluate(future,observed(future,"future-call-1"),now)
result=allocator.allocate(decision.capability,"actor:D1",decision.capability.resource_id,now)
print("future:",result.code)
