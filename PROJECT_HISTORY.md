# Entangled Oracle — Project History

**Ksisti-Puck LLC**

This is a concise narrative of how Entangled Oracle's report engine and
product suite reached its current state. It exists for partners,
collaborators, and investors who want a fast, honest picture of the
project's trajectory without reading the underlying engineering logs
line by line. Those logs — audits, phase plans, and a running revision
history — are all preserved in this repository in full; pointers to them
are listed at the end of this document for anyone who wants to go
deeper on a specific phase.

## Where things stand today

Five report products are live and production-ready: **Daily Horoscope**,
**Weekly Horoscope**, **Personal Forecast**, **Soul Ecosystem**, and
**Year Ahead** — spanning a single day of activation up through a full
annual predictive almanac. All five share one calculation core (a
Swiss-Ephemeris-based natal and transit engine) and one proprietary
interpretive layer, so a client's chart is read consistently whether
they're holding a two-page Daily or a 100-page Year Ahead.

## How it got here

**Foundation and hardening.** The five core report products were built
and then put through a first commercial-readiness pass: real bugs were
found and fixed (date handling, house-system logic, a print-CSS issue
that was rendering PDFs functionally blank), a sixth early product
(Asteroid Portrait) was retired once its content was confirmed fully
covered elsewhere, and the packaging and dependency setup were put on a
reproducible footing.

**An ambitious build, and a deliberate self-correction.** In a short,
intensive stretch, the team designed and built a large predictive
architecture — spanning solar and lunar returns, annual profections,
solar arc directions, secondary progressions, planetary lots, and
zodiacal releasing, tied together by a discrete-event forecasting layer
with its own evidence and validation framework. Partway through, the
project's own review process caught that one experimental, not-yet-
validated component of that system had been wired into real
client-facing report language before it had cleared the bar the project
sets for itself. That component was isolated in full the same day the
gap was found — not deleted, but clearly quarantined and marked
non-production, preserved for reference rather than lost. The six
underlying astrological techniques that same effort had produced
(returns, profections, solar arc, progressions, lots, and zodiacal
releasing) were independently reviewed, found sound, and carried
forward as the real foundation for what came next. This is, candidly,
the single most consequential turn in the project's history — and the
outcome that matters is that the review process worked and caught it
before it ever reached a customer.

**Rebuilding on solid ground.** The team then re-approached the same
technical territory through a formal, tiered process — each tier
reviewed and signed off before the next began. A computation ledger and
canonical event-tracking layer went in first; then a registry
formalizing the six legitimate predictive techniques; then confidence
scoring and a synthesis layer that preserves genuine disagreement in the
data rather than smoothing it away. This process caught two further
instances of scope drift along the way — both corrected in place before
they could compound. By the close of this phase, the technical
foundation was complete and independently verified against a full
regression suite.

**Product depth and polish.** With computation on solid footing, the
work shifted to the reader's experience: a full visual rebuild of the
Year Ahead almanac (moving it from a "dashboard exported to PDF" feel to
something closer to an actual book), an honest audit of how much
authored interpretive depth the shorter reports actually had versus what
their underlying data could support, and — most recently — a
cross-suite consistency and proofing pass that brought all five reports
from soft-launch quality to paid-release quality: fixed pagination and
orphaned headings, resolved a real content-assembly bug that was
duplicating guidance sentences, removed internal debug labels that had
leaked into client-facing prose, and aligned version numbers, suite
framing, and branding across the whole family.

## What's next

The next planned tier is **Synastry** (relationship-chart comparison),
alongside a scoped content-expansion pass for Soul Ecosystem's
proprietary interpretive layer. Both are planned, not yet started.

## Source documents

The full detail behind this narrative — phase-by-phase audits, method
charters, and a running revision log — remains in this repository:

- `ARCHITECTURE.md`, `METHODS.md` — current system design and method reference
- `EO_PREDICTIVE_ARCHITECTURE_PROGRAM.md`, `EO_UPGRADE_PHASES_1_9_AGENT_PROMPTS.md` — the predictive-architecture program and its phase plan
- `CLIENT_FORECAST_ENGINE_ADEQUACY_AUDIT.md`, `ENGINE_CAPABILITY_SURFACE_AUDIT.md`, `EO_MULTICLOCK_ASTEROID_PREDICTIVE_READINESS_AUDIT.md` — point-in-time engineering audits
- `PHASE2_SIDECAR_BODY_CLASSIFICATION_FINDING.md`, `PHASE3_ASTEROID_POLICY_REVIEW.md`, `CODEX_BRIEF_PHASE_D_YEAR_TEXTURE.md`, `EO_PHASE_D_E_REMAINING_WORK.md` — individual phase records
- `CLIENT_FORECAST_CLAIM_CLEANUP_QUEUE.md`, `LIGHTWEIGHT_FORECAST_SURFACE_AUDIT.md`, `HOROSCOPE_PROSE_COVERAGE_AUDIT.md` — content and claims accuracy audits
- `agents/PROFESSIONAL_GRADE_UPGRADE_DIRECTIVES.md`, `agents/PLANNED_UPDATES.md`, `agents/FORECAST_COMPUTATION_LEDGER.md` — the current tiered upgrade program and its open items
- `agents/REVISIONS.md` — the complete, unabridged revision-by-revision log

*Last updated 2026-07-13.*
