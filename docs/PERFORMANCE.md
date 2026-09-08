# Performance methodology and results

## Measured local result

Command:

```bash
PYTHONPATH=src python tools/benchmark.py --iterations 50000
```

| Operation | Throughput | p50 µs | p95 µs | p99 µs | Maximum µs |
|---|---:|---:|---:|---:|---:|
| Cold-path issue and HMAC sign | 11,649/s | 56.37 | 125.28 | 447.32 | 167,971.34 |
| Hot-path verify, state check and reserve | 7,432/s | 89.89 | 203.27 | 749.30 | 165,473.52 |
| Finality allocate and commit | 31,627/s | 20.85 | 32.15 | 105.87 | 137,841.05 |
| Early purpose-mismatch rejection | 11,244/s | 49.49 | 132.07 | 1,016.37 | 57,387.02 |

The high maxima are preserved because a transparent benchmark should expose scheduling pauses in a shared environment. Percentiles and throughput are more informative for this microbenchmark, but none of these numbers represent a service-level objective.

## Included work

- HMAC-SHA256 integrity generation or verification;
- canonical JSON serialization;
- immutable descriptor construction;
- query/handle/epoch/nonce/predicate checks;
- lock-protected quota reservation or commit;
- exact field comparison;
- bounded capability generation.

## Excluded work

- network latency, TLS and DNS;
- SIP/STIR parsing and asymmetric certificate validation;
- CPaaS provider processing;
- persistent or replicated database operations;
- HSM, secure enclave, TEE or attestation operations;
- recipient notification, PSTN setup, media allocation and RTP;
- crash recovery, regional failover and partition reconciliation.

## Test variations required for a deployment claim

Report warm and cold keys, cache hit/miss, valid/rejected decision mix, online revocation, storage durability, concurrency, same-zone and cross-region placement, failover, stale replica, issuer unavailable, quota race, SIP retransmission and fork behavior. Publish hardware, OS, runtime, commit, cryptographic algorithm, request size, workers, cache ratio, throughput, p50/p95/p99/p99.9 and errors.

Map ranking, AI inference, lead auctions and payment computation belong on the cold path. A communication hot path should verify precomputed authority and current protected state without repeating those operations.

