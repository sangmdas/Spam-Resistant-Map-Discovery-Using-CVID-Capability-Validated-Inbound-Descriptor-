"""Reproducible local microbenchmark; excludes network, SIP, durable storage, HSM and media."""
import argparse
import statistics
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from map_cvid import *


def pct(values, p): return sorted(values)[min(len(values) - 1, int(len(values) * p))]


def stats(name, samples, elapsed):
    print(f"{name}: count={len(samples)} throughput_ops_s={len(samples)/elapsed:.0f} "
          f"p50_us={statistics.median(samples):.2f} p95_us={pct(samples,.95):.2f} "
          f"p99_us={pct(samples,.99):.2f} max_us={max(samples):.2f}")


def measure(count, function):
    values=[]; start=time.perf_counter_ns()
    for i in range(count):
        t=time.perf_counter_ns(); function(i); values.append((time.perf_counter_ns()-t)/1000)
    return values, (time.perf_counter_ns()-start)/1e9


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--iterations", type=int, default=50_000); args=parser.parse_args()
    now=datetime.now(timezone.utc); key=b"benchmark-only-key-material-32-bytes!!"
    state=ProtectedStateStore(); signer=HMACSigner(key); service=AuthorityService("maps.example", "edge:west", signer, state)
    context=service.create_context("i", "u", ("p",), now-timedelta(seconds=1), now+timedelta(days=30))
    handle=service.create_handle(context, now+timedelta(days=29)); state.set_selection(context.query_context_id,"p","b")

    issued=[]
    def issue(i): issued.append(service.issue_preview(context,handle,"b","actor","p",now=now,quota=1))
    values,elapsed=measure(args.iterations,issue); stats("cold_path_issue_and_hmac_sign",values,elapsed)

    authority=service.issue_preview(context,handle,"b","actor","p",now=now,quota=args.iterations+1)
    enforcement=CommunicationEnforcementPoint("edge:west",signer,state)
    def make_attempt(i, purpose="initial-enquiry"):
        return AttemptDescriptor(f"tx-{i}",authority.authority_id,authority.query_context_id,authority.inquiry_id,
            authority.business_identity,authority.requesting_actor_id,authority.user_binding,authority.property_id,
            authority.handle_id,authority.phase,authority.direction,authority.channel,purpose,authority.permitted_effect,
            authority.nonce,authority.enforcement_point_id)
    decisions=[]
    values,elapsed=measure(args.iterations,lambda i: decisions.append(enforcement.evaluate(authority,make_attempt(i),now)))
    stats("hot_path_verify_hmac_state_and_reserve",values,elapsed)

    allocator=ResourceAllocator("edge:west",signer,state)
    values,elapsed=measure(args.iterations,lambda i: allocator.allocate(decisions[i].capability,"actor",decisions[i].capability.resource_id,now))
    stats("finality_allocate_and_commit",values,elapsed)

    rejected=[]
    values,elapsed=measure(args.iterations,lambda i: rejected.append(enforcement.evaluate(authority,make_attempt(i+args.iterations,purpose="marketing"),now)))
    stats("early_reject_purpose_mismatch",values,elapsed)
    assert all(not x.allowed and x.code=="PURPOSE_MISMATCH" for x in rejected)
    print("scope=single-process Python, HMAC-SHA256, in-memory locked state; no network/SIP/CPaaS/media/durable-store/HSM/TEE")

if __name__=="__main__": main()
