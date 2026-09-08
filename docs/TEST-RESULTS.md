# Test results and adversarial matrix

## Verified result

Command:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result on 8 September 2026:

```text
Ran 125 tests in 0.066s
OK
```

The suite has no skipped or expected-failure cases. It uses only the Python standard library.

## Requirement coverage

| Draft property | Representative tests | Result |
|---|---|---|
| R1 — identifier possession is not authority | stolen/copied handle, handle mismatch, authority ID mismatch, actor substitution | PASS |
| R2 — preview/future separation | distinct IDs/nonces/phases, preview cannot encode future effect, next-day reuse denied | PASS |
| R3 — attempt-specific binding | independent query, inquiry, property, business, user, actor, direction, channel, purpose, effect, nonce, audience and device mismatch | PASS |
| R4 — pre-effectuation verification | allocator rejects missing, unsigned, tampered, expired or mis-scoped release capability | PASS |
| R5 — atomic reservation | 50 distinct attempts race for quota one; exactly one succeeds | PASS |
| R6 — replay resistance | new logical act denied after exhaustion; same transport transaction idempotent | PASS |
| R7 — revocation/freshness | missing or mismatched policy/revocation state, inactive query, expired handle and altered nonce deny | PASS |
| R8 — identity/delegation control | business/actor substitution denied; explicit delegate and AI-agent delegation allowed | PASS |
| R9 — enforcement-point binding | attempt audience and capability audience mismatches deny | PASS |
| R10 — privacy minimization | no phone, latitude, longitude, exact region or payment record in authority object | PASS |
| R11 — fail closed | missing protected state, poisoned outcome, released reservation and absent capability deny | PASS |

## Concurrency and state-transition coverage

- 50 simultaneous distinct transaction IDs compete for one remaining quota: one is authorized, 49 return `QUOTA_EXHAUSTED`.
- 50 simultaneous retransmissions with the same transaction ID share one reservation and remain idempotent.
- Pending reservation rollback restores quota.
- Committed reservation cannot be rolled back.
- A poisoned uncertain outcome cannot be replayed or allocated.
- A released reservation cannot be silently reused through the same transaction.
- Separate authority IDs maintain independent quota domains.

## Defect found by the suite

During the first 125-test run, `selection_required` and `commercial_required` were found to be passed into the protected authority object in reversed order. One test failed. The mapping was corrected, and the complete suite then passed. This history is recorded because it demonstrates that the tests exercised two distinct predicates rather than merely increasing a test count.

## What is not tested here

Carrier SIP conformance, STIR certificate processing, real WebRTC/TURN allocation, durable database consensus, distributed partitions, HSM/TEE behavior, remote attestation, platform SDK behavior, emergency routing and legal compliance require integration environments outside this standard-library reference package.
