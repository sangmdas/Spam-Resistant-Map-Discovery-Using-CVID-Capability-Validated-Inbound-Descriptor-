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

  ## Reference Implementation: Map-Discovery CVID, Preview Authority, and Communication Finality

**Implementation name:** Map-Discovery CVID + Preview-to-Unlock Communication-Finality Reference Implementation
**Implementation version:** 1.0.0
**Implementation status:** Runnable research reference implementation
**Programming language:** Python 3.11 or later
**Runtime dependencies:** Python standard library only
**Distribution formats:** ZIP and TAR.GZ
**Test suite:** 125 automated tests
**Test result:** 125 passed; zero skipped; zero expected failures
**License status:** No open-source or patent license is implied by publication. An explicit license should be added before third-party reuse or contribution.

### Purpose

This implementation demonstrates the semantic and state-transition model described in the Internet-Draft concerning privacy-preserving map-based business discovery using query-scoped, non-bearer communication handles, bounded Preview Authority, separate Future-Contact Authority, and communication-finality enforcement.

The implementation uses the companion CVID principle as its starting point:

> Possession of a visible or machine-usable communication handle is not, by itself, authority to create a communication effect.

A map result, property listing, query-scoped handle, previous conversation, lead assignment, payment event, general API credential, or copied authorization reference is therefore insufficient by itself to create future reachability.

The implementation represents each proposed call, message, callback, WebRTC session, notification, or similar operation as a Candidate Communication Act. The act remains non-effective until a downstream Communication Enforcement Point:

1. verifies the integrity of the authority;
2. reconstructs the actual attempted communication;
3. compares the attempted act with the authorized scope;
4. checks current protected state;
5. atomically reserves the required quota or single-use state; and
6. issues a short-lived Bounded Release Capability.

A separate Resource Allocator verifies that capability before creating the simulated externally effective communication resource.

The implementation therefore demonstrates a finality boundary rather than only an application-level Boolean such as `business_allowed = true`.

### Implemented components

The implementation contains the following logical components.

#### 1. Query Context Service

The Query Context Service creates a bounded discovery context containing:

* query-context identifier;
* inquiry identifier;
* pseudonymous user binding;
* permitted property or listing identifiers;
* validity start and end;
* optional opaque regional designation.

Search ranking and listing eligibility do not automatically create communication authority.

#### 2. Query-Scoped CVID

The implementation creates a rotated Query-Scoped Communication Handle, referred to as a CVID.

The CVID is bound to:

* one query context;
* one pseudonymous user binding;
* one platform;
* one expiry time.

The CVID does not contain the user’s telephone number. Its purpose is to identify the protected context that must be evaluated. Copying or retaining the CVID does not transfer communication authority.

A CVID cannot outlive its associated query context.

#### 3. Communication Authority Service

The Communication Authority Service creates integrity-protected authorization objects.

Two authority phases are implemented:

* `PREVIEW`: permits a bounded first interaction;
* `FUTURE`: permits separately authorized later communication.

Preview Authority and Future-Contact Authority receive different authority identifiers and different nonces. A Preview Authority cannot encode a future-contact effect, and a Future-Contact Authority cannot encode a preview effect.

Future authority may require:

* current user selection or shortlisting;
* a callback or booking decision;
* an applicable marketplace condition;
* a current business-side commercial predicate; or
* a combination of these conditions.

Commercial or payment state is treated only as an input to authority issuance. It is not self-executing communication authority.

#### 4. Communication Scope Descriptor

Each authority binds the following load-bearing fields:

* authority identifier;
* inquiry identifier;
* query-context identifier;
* pseudonymous user binding;
* query-scoped CVID;
* requesting actor;
* business identity;
* explicitly authorized actors or delegates;
* property or listing identifier;
* communication phase;
* direction;
* channel;
* purpose;
* permitted effect;
* validity start;
* validity end;
* nonce;
* quota;
* revocation epoch;
* policy epoch;
* enforcement-point identifier;
* optional commercial-state requirement;
* optional selection requirement; and
* optional device binding.

The implementation supports voice, messaging, WebRTC, and notification channel semantics in the data model. The runnable example exercises voice-preview and future-contact flows.

#### 5. Attempt Descriptor

The Communication Enforcement Point does not rely only on an application’s statement of intended behavior.

An Attempt Descriptor is constructed from observed or trusted inputs describing the actual requested act, including:

* transaction identifier;
* authority reference;
* query and inquiry;
* business and requesting actor;
* recipient binding;
* property or listing;
* CVID;
* preview or future phase;
* communication direction;
* requested channel;
* purpose;
* requested effect;
* nonce;
* enforcement point; and
* optional device binding.

Every material mismatch results in denial before the protected resource is allocated.

#### 6. Protected State Store

The reference Protected State Store maintains:

* registered query contexts;
* registered CVIDs;
* current revocation epochs;
* current policy epochs;
* current user-selection state;
* current commercial predicates;
* authority nonce state;
* remaining authority quota;
* transaction-to-reservation mappings;
* reservation status; and
* committed, released, or poisoned outcomes.

The store is protected by a process-local re-entrant lock for deterministic concurrency testing.

A production implementation would require a durable transactional or consensus-backed state mechanism appropriate to its deployment and failure model.

#### 7. Atomic reservation and consumption

Quota is reserved before resource effectuation.

The implementation distinguishes:

* a new logical communication act;
* a retransmission of the same logical transaction;
* a new replay after quota exhaustion;
* a pending reservation;
* a committed reservation;
* a rolled-back reservation; and
* an uncertain or poisoned outcome.

A SIP-style retransmission carrying the same stable transaction identity is treated idempotently and does not consume additional quota.

A materially new transaction requires additional available quota.

#### 8. Bounded Release Capability

Successful verification produces a short-lived Bounded Release Capability bound to:

* the authority identifier;
* transaction identifier;
* protected reservation;
* authorized actor;
* exact resource identifier;
* permitted effect;
* enforcement-point audience; and
* expiry.

The reference capability has a maximum lifetime of five seconds and is not intended to operate as a general-purpose bearer credential.

Copying the capability does not authorize:

* another actor;
* another resource;
* another enforcement point;
* another transaction; or
* use after expiry.

#### 9. Resource Allocator

The Resource Allocator is the only reference component that records the simulated external communication effect.

It rejects:

* missing capabilities;
* unsigned capabilities;
* integrity failures;
* expired capabilities;
* actor substitution;
* resource widening;
* enforcement-point substitution;
* released reservations; and
* poisoned or uncertain outcomes.

The allocator commits the protected reservation before recording the communication effect. Repeated allocation of the same transaction and identical resource is idempotent.

### Integrity configuration

The reference implementation uses:

* canonical JSON serialization;
* deterministic field ordering;
* UTF-8 encoding;
* HMAC-SHA256;
* constant-time signature comparison; and
* a minimum 32-byte prototype key.

HMAC-SHA256 was selected to keep the implementation dependency-free and easy to audit. It demonstrates integrity and binding semantics; it is not a mandatory protocol selection.

A production implementation may use:

* asymmetric signatures;
* JWT or CWT profiles;
* PASSporT-related structures;
* DPoP or mTLS sender constraints;
* managed key services;
* HSM-backed keys;
* secure-enclave or TEE protection; or
* another deployment-appropriate protected authorization representation.

The reference implementation does not define an IETF wire format, registered SIP header, PASSporT claim, OAuth authorization-details type, or IANA registration.

### Deployment variations

Five configuration variations are included.

#### Variation 1: Platform-local CPaaS gateway

The map or marketplace platform places enforcement at its callback bridge, virtual-number service, messaging gateway, or CPaaS boundary.

Possible transports include HTTP, SIP, and conventional PSTN mediation.

This is the simplest incremental deployment. It may provide blocked-path or pre-routing enforcement. It must not claim complete absent-path protection if the underlying telephone number or an alternate route remains independently reachable.

#### Variation 2: Regional edge verification

Pre-issued authority, verification keys, current epochs, nonce state, and quota are placed close to a regional communication boundary.

The regional verifier operates before SIP, WebRTC, CPaaS, messaging, or notification resource allocation.

Stale replicas must not recreate revoked or consumed authority. When required current state cannot be established, the implementation must fail closed or escalate to a higher-assurance verifier.

#### Variation 3: Absent-path controlled relay

The CVID does not independently resolve to an effective communication route.

A private resolver or controlled relay releases the destination or communication path only after successful authorization.

This is the strongest deployment variation, but it is valid only if equivalent paths are controlled. An ordinary telephone number, SIP URI, messaging account, alternate CPaaS API, forwarding rule, notification service, or other identifier must not bypass the same enforcement property.

#### Variation 4: Device-assisted enforcement

A cloud verifier checks business identity, query context, property binding, channel, purpose, commercial state, quota, and epochs.

An operating-system or device-side broker may additionally enforce:

* device binding;
* user presence;
* current notification permission;
* device-side revocation;
* assistant scope; or
* another local protected condition.

Both the cloud path and the device communication-effect path must enforce the bounded authority. A device check alone does not correct an uncontrolled cloud or carrier path.

#### Variation 5: High-assurance or attested enforcement

The finality verifier, protected state, or key material may be placed in:

* an HSM;
* a trusted execution environment;
* a secure enclave;
* an attested workload;
* a protected operating-system service; or
* another higher-assurance enforcement domain.

Remote attestation can strengthen confidence that an expected verifier is operating in an acceptable environment. Attestation does not replace communication authority and does not establish that an uncontrolled resource allocator will obey the decision.

### Tested security properties

The automated suite contains 125 tests across nine modules.

| Test category                                    |   Tests |
| ------------------------------------------------ | ------: |
| Attempt-specific field binding                   |      17 |
| Authority issuance and preview/future separation |      19 |
| End-to-end map-discovery flows                   |      13 |
| Finality capability and resource allocation      |      14 |
| Integrity and validity boundaries                |       9 |
| Data-model invariants                            |      20 |
| Protected state and freshness                    |      15 |
| Quota, replay and concurrency                    |      10 |
| Deployment variations and privacy minimization   |       8 |
| **Total**                                        | **125** |

The suite covers:

* CVID theft and copying;
* authority-reference substitution;
* business substitution;
* actor and affiliate pivot;
* property or listing pivot;
* recipient substitution;
* query and inquiry substitution;
* preview-to-future widening;
* communication-direction widening;
* voice-to-message channel widening;
* purpose laundering;
* effect widening;
* nonce substitution;
* enforcement-point substitution;
* device substitution;
* unsigned authority;
* modified signed authority;
* wrong signing key;
* not-yet-valid authority;
* exact expiry boundary;
* expired query;
* expired CVID;
* missing revocation state;
* missing policy state;
* revocation-epoch change;
* policy-epoch change;
* nonce-state change;
* withdrawn user selection;
* withdrawn commercial state;
* quota exhaustion;
* logical replay;
* transport retransmission;
* concurrent double-consumption attempts;
* rollback before effectuation;
* attempted rollback after commitment;
* released reservation reuse;
* uncertain or poisoned outcomes;
* missing release capability;
* capability theft;
* resource widening;
* capability-audience substitution; and
* capability expiry.

A 50-way concurrent test causes distinct transaction identifiers to compete for one remaining quota. Exactly one attempt is authorized and 49 return `QUOTA_EXHAUSTED`.

A separate 50-way retransmission test uses the same transaction identifier. All attempts resolve to the same reservation and are treated idempotently.

### Test results

The final packaged implementation produced:

```text
Ran 125 tests in 0.066s
OK
```

There were:

* zero skipped tests;
* zero expected failures; and
* zero remaining test failures.

The expanded suite identified one genuine implementation error during development: the `selection_required` and `commercial_required` fields were initially passed to the authority object in reversed order. The mapping was corrected, and the complete suite was rerun successfully.

### Test environment

The reported functional tests and microbenchmarks were executed in the following environment:

* operating system: Linux;
* kernel: Linux 6.18.35;
* architecture: x86-64;
* processor reported by the environment: Intel Xeon Platinum 8573C;
* logical CPUs available to the environment: 9;
* Python implementation: CPython;
* Python version: 3.12.13;
* Python compiler: Clang 22.1.3;
* C library: glibc 2.39;
* external Python packages: none;
* state implementation: process-local in-memory dictionaries protected by a re-entrant lock;
* integrity algorithm: HMAC-SHA256;
* network operations: none;
* persistent database: none;
* SIP or CPaaS provider: none;
* HSM, TEE or secure enclave: none.

The environment is shared or virtualized. Maximum-latency outliers may therefore include operating-system scheduling and shared-host effects.

The continuous-integration workflow included in the repository is configured for Python 3.11, 3.12, and 3.13 on GitHub-hosted Ubuntu runners. The recorded 125-test result above was obtained locally with Python 3.12.13; the inclusion of a CI matrix is not itself a claim that the package has already been executed by GitHub on all three versions.

### Measured microbenchmark

The included benchmark was run with 50,000 operations for each path.

| Operation                                                    |          Throughput |      p50 |       p95 |         p99 |       Maximum |
| ------------------------------------------------------------ | ------------------: | -------: | --------: | ----------: | ------------: |
| Cold-path authority issue and HMAC signing                   | 11,649 operations/s | 56.37 µs | 125.28 µs |   447.32 µs | 167,971.34 µs |
| Hot-path verification, protected-state check and reservation |  7,432 operations/s | 89.89 µs | 203.27 µs |   749.30 µs | 165,473.52 µs |
| Finality allocation and state commitment                     | 31,627 operations/s | 20.85 µs |  32.15 µs |   105.87 µs | 137,841.05 µs |
| Early purpose-mismatch rejection                             | 11,244 operations/s | 49.49 µs | 132.07 µs | 1,016.37 µs |  57,387.02 µs |

These measurements include:

* Python object processing;
* canonical serialization;
* HMAC-SHA256;
* protected-state checks;
* exact field comparison;
* process-local locking;
* quota reservation;
* capability creation; and
* reservation commitment.

They exclude:

* network latency;
* DNS and TLS;
* SIP parsing;
* STIR certificate processing;
* asymmetric-signature verification;
* persistent or replicated storage;
* CPaaS-provider processing;
* PSTN call setup;
* WebRTC negotiation;
* TURN allocation;
* push delivery;
* recipient-device wake-up;
* media allocation and RTP;
* HSM access;
* TEE or secure-enclave transitions;
* remote attestation;
* regional failover; and
* crash recovery.

The figures are implementation measurements, not protocol requirements, carrier-grade performance claims, or service-level guarantees.

The large maximum values are retained because they occurred in the shared execution environment. Percentiles and throughput are more informative for this local microbenchmark.

### Expected deployment latency

No universal latency is asserted by the implementation or draft.

Possible engineering budgets for future deployment testing are:

* co-located local verification: target p99 below 1 ms;
* local verification with durable same-edge reservation: target p99 below 5 ms;
* nearby online policy or revocation validation: target p99 below 20 ms;
* cross-region synchronous validation: separately measured and not recommended as the default voice hot path.

These values are suggested evaluation budgets, not measured production results or normative requirements.

Map search, ranking, AI inference, fraud scoring, lead pricing, payment calculation and authority construction can occur on the cold path. The communication hot path should be limited to deterministic verification of pre-issued authority and current protected state.

### Runnable example

The repository includes a house-rental example corresponding to the draft’s illustrative A–E participant model.

The example:

1. creates a property-search query;
2. creates a query-scoped CVID;
3. issues Preview Authority for Business D1 and Property P1;
4. submits the observed preview attempt;
5. verifies and reserves authority;
6. allocates the bounded preview resource;
7. records a separate user-selection event;
8. issues a new Future-Contact Authority;
9. independently verifies the later attempt; and
10. allocates the bounded future-contact resource.

Expected output:

```text
preview: RESOURCE_ALLOCATED
future: RESOURCE_ALLOCATED
```

The example does not convert the preview authority into future authority. A new authority object is issued.

### Package contents

The ZIP and TAR.GZ distributions contain:

* Python source code;
* 125-test automated suite;
* map/property-discovery example;
* benchmark tool;
* five deployment configurations;
* detailed README;
* test-results report;
* performance methodology;
* security model;
* distribution manifest;
* run-all script; and
* GitHub Actions workflow.

Generated Python bytecode, cache directories, local virtual environments and temporary benchmark output are excluded.

### Limitations

This is a reference implementation of architecture and authorization semantics. It is not:

* a production map service;
* a Google Maps or Apple Maps integration;
* a property-listing platform;
* a telecom carrier;
* a production SBC;
* an IMS implementation;
* a SIP extension;
* a STIR/SHAKEN implementation;
* an OAuth authorization server;
* a CPaaS provider integration;
* a production WebRTC or TURN service;
* a distributed database;
* a production HSM or TEE implementation;
* a remote-attestation verifier;
* an emergency-call-routing implementation; or
* a certification of GDPR or other legal compliance.

The reference implementation trusts that observed attempt fields are supplied by a protected adapter. A production system must derive actor, business, destination, channel, effect, device and enforcement-point information from authenticated or otherwise trusted protocol and platform inputs.

The in-memory lock demonstrates atomic behavior inside one Python process. It does not solve distributed consensus, network partitions, replica rollback, multi-region double spending, durable crash recovery, clock synchronization, key compromise, or disaster recovery.

The simulated Resource Allocator records a communication effect in memory. A production integration must ensure that the real communication-bearing component is structurally downstream of the verification result and that no equivalent API, public number, alternate relay, forwarding rule, messaging path, notification service or administrator path can bypass enforcement.

Emergency and legally mandated communication paths require separate, always-available treatment and must not be unintentionally disabled by failure of an ordinary grant service.

### Interoperability status

The implementation validates a provider-neutral semantic model. It does not yet demonstrate interoperability between independent vendors because the accompanying document does not select a single wire encoding or transport binding.

Potential future adapters may include:

* an HTTP/JSON authority and attempt API;
* a SIP header or body reference;
* a PASSporT-related claim;
* an OAuth Rich Authorization Request profile;
* a CWT representation;
* a CPaaS request field;
* a WebRTC signaling object;
* a TURN-allocation authorization reference;
* a messaging-envelope field; or
* a device-broker interface.

Interoperability work would need to define canonical encoding, issuer discovery, key identification, error semantics, transaction identity, replay and fork behavior, reservation commitment, delegation, privacy minimization, revocation freshness, and cross-provider trust.

### Reproduction commands

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python examples/house_rental_flow.py
PYTHONPATH=src python tools/benchmark.py --iterations 50000
```

The included convenience script runs all three operations:

```bash
sh scripts/run-all.sh 50000
```

### Summary

The implementation demonstrates that a map-derived communication handle can remain a non-bearer context reference; that first preview and future reachability can be separately authorized; and that actual communication effectuation can be placed downstream of integrity verification, attempted-act reconstruction, current protected-state validation, atomic quota reservation, and bounded resource-specific release.

The implementation is intended to support technical review of the architecture and to identify which semantics, if any, would benefit from interoperable IETF specification.


## IPR and license status

CC-BY-NC- 4.0 
