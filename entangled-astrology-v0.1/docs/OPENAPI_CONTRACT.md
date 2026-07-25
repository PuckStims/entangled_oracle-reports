# OpenAPI Contract

The canonical machine-readable contract is `openapi/entangled-oracle-v1.yaml`.

The Kotlin models intentionally use ISO-8601 strings for temporal values. The backend owns timezone resolution and must return the effective timezone in each calculated response.

## Contract philosophy

- Required fields are genuinely required.
- Unknown response keys are rejected by the Android client in v0.1.
- Every synthesized pattern references concrete event IDs.
- Every calculated object carries engine and module provenance.
- Birth-time-sensitive results are marked explicitly.
- Empty supported results are valid; fabricated substitutes are not.
