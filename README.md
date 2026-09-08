# Map-Discovery CVID + Preview-to-Unlock Communication Finality

> Runnable, provider-neutral reference implementation with 125 adversarial tests.

This repository implements the central architecture described in **“Privacy-by-Design, GDPR-Aligned Communication Finality for Google Maps, Apple Maps, and Other Map-Based Business Discovery Using Query-Scoped Non-Bearer Authorization.”** Google Maps and Apple Maps are illustrative deployment contexts only. No affiliation, endorsement, adoption, or technical alignment is implied.

The implementation also uses the companion CVID principle:

> A visible or machine-usable communication handle identifies a bounded context. Possession of that handle is not, by itself, permission to contact the user.

The reference flow separates a limited first **Preview Authority** from later **Future-Contact Authority**. It holds every attempted call, message, WebRTC session, callback, or notification in a non-effective state until a downstream enforcement point verifies the actual attempted act, verifies current protected state, atomically reserves quota, and issues a short-lived Bounded Release Capability. Only the controlled resource allocator can create the simulated communication effect.

## What this package proves

- A copied CVID does not provide reachability.
- Map ranking or business eligibility is not communication authority.
- A successful preview does not silently create future reachability.
- Payment or commercial state can be an issuance predicate but is not self-executing authority.
- Authority is inseparably bound to query, inquiry, user, property/listing, business, actor/delegate, handle, phase, direction, channel, purpose, effect, nonce, validity, epochs, device, and enforcement point.
- The enforcement point reconstructs the attempted act rather than trusting application intent.
- Concurrent requests cannot consume the same final quota independently.
- SIP-style retransmission of one logical act is idempotent rather than a second contact.
- Successful verification produces a non-general, resource-specific release capability.
- No valid capability means no protected resource allocation in the governed path.

## Architecture

```text
Map query / user inquiry
        ↓
Query Context + query-scoped CVID
        ↓
Preview Authority ── first bounded interaction
        ↓
User selection and/or applicable marketplace condition
        ↓
NEW Future-Contact Authority
        ↓
Candidate Communication Act — NON-EFFECTIVE
        ↓
Enforcement Point reconstructs actual attempt
        ↓
Integrity + scope + current protected-state verification
        ↓
Atomic reservation / consumption
        ↓
Bounded Release Capability
        ↓
Controlled Resource Allocator — EFFECTIVE or DENIED
```

The load-bearing separation is implemented by four components:

| Component | Responsibility |
|---|---|
| `AuthorityService` | Creates query contexts, rotates CVIDs, and issues separately signed preview/future authority. |
| `ProtectedStateStore` | Holds current query/handle state, selection, commercial predicates, epochs, nonces, quota, transactions, and reservations. |
| `CommunicationEnforcementPoint` | Verifies authority integrity, reconstructs and compares the actual attempted scope, checks current state, and reserves quota. |
| `ResourceAllocator` | Accepts only a valid actor/resource/audience-bound capability and performs the final state commit before recording the external effect. |

## Quick start

Requires Python 3.11 or later and no third-party runtime dependency.

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python examples/house_rental_flow.py
PYTHONPATH=src python tools/benchmark.py --iterations 50000
```

Expected example output:

```text
preview: RESOURCE_ALLOCATED
future: RESOURCE_ALLOCATED
```

## Test results

The packaged version was executed on 8 September 2026:

```text
Ran 125 tests in 0.066s
OK
```

| Module | Tests | Primary property |
|---|---:|---|
| `test_attempt_binding.py` | 17 | Every load-bearing attempted field independently matches or fails closed. |
| `test_authority_issuance.py` | 19 | CVID/query binding, preview/future separation, selection and commercial predicates, delegation, effect restrictions. |
| `test_end_to_end_flows.py` | 13 | Preview, future contact, stolen handles, property/business/purpose pivots, AI agents, device binding. |
| `test_finality_allocator.py` | 14 | Capability integrity, expiry, actor/resource/audience binding, commit, uncertain outcome, no-capability denial. |
| `test_integrity_and_time.py` | 9 | Authority signing, tamper detection, wrong keys, precise validity boundaries, timezone safety. |
| `test_model_invariants.py` | 20 | Strict construction, non-empty fields, valid ranges, immutability, phase/effect consistency. |
| `test_protected_state.py` | 15 | Query/handle status, revocation, policy freshness, nonce, selection and commercial-state withdrawal. |
| `test_quota_replay_concurrency.py` | 10 | Quotas, logical replay, retransmission, 50-way races, rollback, poison and isolation. |
| `test_variations_and_privacy.py` | 8 | Five deployment variations and minimization of phone, exact-location and payment-record disclosure. |
| **Total** | **125** | **All passed.** |

The expanded suite found and corrected one real implementation error during development: `selection_required` and `commercial_required` were initially mapped in reversed order. The final archive includes the corrected mapping and a fully passing suite.

See [docs/TEST-RESULTS.md](docs/TEST-RESULTS.md) for the full matrix and [docs/PERFORMANCE.md](docs/PERFORMANCE.md) for benchmark interpretation.

## CVID + preview-to-unlock flow

1. The user creates an enquiry; the map platform creates a bounded `QueryContext`.
2. The platform creates a rotated `QueryScopedHandle` that contains no underlying telephone number.
3. Preview authorization is issued for a selected listing/business and one limited interaction.
4. The business submits a candidate attempt. The handle only identifies which context should be evaluated.
5. The enforcement point compares observed signaling with the signed authority and current state.
6. A successful decision reserves quota and produces a five-second, transaction-specific release capability.
7. The allocator verifies the capability and commits the reservation before creating the resource.
8. The preview ends without permanent reachability.
9. Continued contact requires a newly issued `FUTURE` authority based on current selection and any required commercial condition.

## Variations included

| Configuration | Intended boundary | Honest claim limit |
|---|---|---|
| `platform-local-cpaas.json` | Platform callback/CPaaS gateway | Cannot claim absent-path if a public number remains reachable. |
| `regional-edge.json` | Regional verifier before communication allocation | Stale replicas must fail closed or escalate. |
| `absent-path-relay.json` | Private resolver and controlled relay | Every equivalent route and identifier must be controlled. |
| `device-assisted.json` | Cloud verifier plus OS/device broker | Cloud and device effect paths must enforce the same authority. |
| `high-assurance-attested.json` | HSM/TEE/enclave/attested verifier | Attestation strengthens the verifier but does not replace act authority. |

The semantic core is transport-neutral. A production adapter may sit before a SIP bridge, SBC, CPaaS call, WebRTC room, TURN allocation, messaging thread, push notification, or device broker.

## Performance results and targets

The included benchmark measures only Python/HMAC/in-memory behavior. On the packaged test environment, 50,000 operations per path produced:

| Path | Throughput | p50 | p95 | p99 |
|---|---:|---:|---:|---:|
| Cold-path issue + HMAC sign | 11,649 ops/s | 56.37 µs | 125.28 µs | 447.32 µs |
| Hot-path verify + state + reserve | 7,432 ops/s | 89.89 µs | 203.27 µs | 749.30 µs |
| Finality allocate + commit | 31,627 ops/s | 20.85 µs | 32.15 µs | 105.87 µs |
| Early purpose-mismatch rejection | 11,244 ops/s | 49.49 µs | 132.07 µs | 1,016.37 µs |

These are reproducibility results, **not carrier-grade latency claims**. They exclude SIP parsing, asymmetric signature verification, network transport, durable or replicated state, CPaaS processing, media setup, HSM/TEE access, and failure recovery. Large maximum outliers observed in the shared test environment reflect scheduling noise and are reported in `docs/PERFORMANCE.md` rather than hidden.

Suggested engineering budgets to validate—not protocol requirements—are sub-1 ms p99 for a co-located local verifier, sub-5 ms p99 when durable same-edge reservation is required, and sub-20 ms p99 for a nearby online policy/epoch check. Cross-region synchronous validation should be measured separately and is not recommended as the default voice hot path.

## Package contents

| Path | Contents |
|---|---|
| `src/map_cvid/` | Models, canonical HMAC integrity, authority issuance, protected state, verification, bounded capability, allocator. |
| `tests/` | 125 runnable unit, adversarial, concurrency, invariant, privacy, and end-to-end tests. |
| `examples/house_rental_flow.py` | Q1007/P1/D1-style preview followed by separately authorized future contact. |
| `tools/benchmark.py` | Cold path, hot path, allocation and rejection microbenchmarks with percentiles. |
| `configs/` | Five deployment and assurance variations with explicit claim limits. |
| `docs/` | Test results, performance methodology, security model, limitations and GitHub upload guidance. |
| `.github/workflows/tests.yml` | CI job for Python 3.11, 3.12 and 3.13. |

## Production limitations

This is a semantic and concurrency reference, not a production telecom platform.

- HMAC is used for deterministic demonstration. Production deployments need managed keys, key identifiers, rotation, issuer discovery, and potentially asymmetric verification or HSM-backed operations.
- The protected store is in-memory and single-process. Distributed use needs durable atomicity, partition behavior, replication consistency, crash recovery and uncertain-outcome policy.
- Authenticated actor identity is supplied to the attempt adapter. Production systems must derive it from a trusted SIP/STIR, mTLS, workload identity, DPoP, carrier, OS, device, or equivalent context.
- The allocator records a simulated effect. A real integration must ensure every equivalent CPaaS/SIP/WebRTC/message/push path is structurally downstream of enforcement.
- Emergency and legally mandated routes require separate always-available policy and must not be disabled by ordinary grant-service failure.
- Privacy-law compliance depends on the full processing context. This implementation demonstrates minimization and technical constraints; it does not certify GDPR or other legal compliance.
- Attestation can strengthen confidence in the verifier. It does not prove a finality property that the measured component or resource allocator does not enforce.

## IPR and license status

This repository is a technical reference implementation. No open-source license or patent license is implied merely by publication. Before third-party reuse or contributions, add an explicit code license and any applicable IPR notice consistent with the author’s intended licensing position.
