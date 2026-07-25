# Data Provenance Requirements

Every calculation response must identify:

- engine version,
- schema version,
- calculation modules,
- whether normalization was applied,
- content-pack identifiers used,
- fallback tier used, if any,
- warnings and uncertainty.

Every field pattern must reference supporting event IDs present in the same response. The Android validator rejects orphaned synthesis.

## Logging

Do not log raw birth profiles, chart payloads, generated reports, or full serialization exceptions by default. Use request IDs and sanitized diagnostics.
