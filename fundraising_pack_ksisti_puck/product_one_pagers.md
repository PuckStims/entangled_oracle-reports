# Product One-Pagers

## Entangled Oracle

### Product

Entangled Oracle is a local-first astrology and symbolic report platform with a Python report engine, Android companion surfaces, and a web dashboard.

### Current Assets

- Astrology calculation/report generator.
- Swiss Ephemeris-backed engine path.
- Authored JSON interpretation blocks.
- Year-ahead, personal forecast, horoscope, soul ecosystem, identity, and location-service surfaces.
- Android frontend scaffold via Entangled Astrology.
- Vite dashboard with tarot/rune/astrology adapters and optional OpenRouter synthesis.
- Deterministic tarot/rune Android prototype through EntangledOracle.

### User Problem

Existing astrology and symbolic tools often separate calculation, interpretation, journaling, and report delivery. Entangled Oracle aims to connect them through inspectable, source-aware, local-first tooling.

### Near-Term Product

- Local paid report generator.
- Android astrology companion.
- Symbolic dashboard for tarot/runes/astrology.
- Demo report workflow.

### Differentiation

- Authored domain content.
- Source/provenance posture.
- Local-first generation.
- Cross-platform symbolic ecosystem.

### Risks

- Crowded market.
- Production polish still required.
- Some planned location/report surfaces remain scaffolded.
- Must avoid unsupported deterministic/predictive claims.

### Next Milestones

1. Stabilize engine test environment.
2. Package three strong report demos.
3. Connect Android and dashboard to the engine cleanly.
4. Define one paid entry product.

## Shadow Compass

### Product

Shadow Compass is a guided reflection and emotional-regulation platform for structured check-ins, state shifting, journaling, pattern review, reports, and practitioner-created journeys.

### Current Assets

- Next.js App Router web/PWA shell.
- Modular packages for UI, domain, DB, analytics, AI gateway, content, jobs, config, and testing.
- Prisma schema blueprint.
- Consent-aware check-ins.
- State Shift and Guided Session routing.
- Journal/history visibility.
- User-owned pattern review.
- Hypothesis-language report draft.
- Mock AI gateway with provider-neutral contracts.

### User Problem

Users need reflective tools that help identify patterns without overreaching, diagnosing, or turning private emotional material into ordinary engagement data.

### Near-Term Product

- Privacy-forward journaling and check-in app.
- Guided reflection subscription.
- Pattern review and weekly report surfaces.
- Practitioner journey studio later.

### Differentiation

- Consent-first architecture.
- User-confirmed pattern model.
- Regulation-before-interpretation principle.
- AI as bounded task support, not companion authority.

### Risks

- Crowded wellness/journaling market.
- No real auth or billing yet.
- AI is mocked in v0.1.
- Must avoid therapy replacement claims.

### Next Milestones

1. Add real auth.
2. Harden persistence around real users.
3. Add E2E tests for the foundation loop.
4. Create a polished demo path and product page.

## ChartTrace ScribeShield

### Product

ScribeShield is a documentation-integrity review tool that compares a clinician-authorized source packet with a generated clinical note and surfaces seeded or future-detected documentation drift before signature.

### Current Assets

- Next.js review workspace.
- Synthetic clinical cases.
- Deterministic audit engine.
- Risk scoring.
- Claim-level findings.
- Severity/confidence taxonomy.
- Supervisor queue.
- Reviewer rationale workflow.
- Markdown exports for clinician, supervisor, compliance, and validation audiences.
- Tests and threat model.

### User Problem

AI-assisted clinical documentation can introduce unsupported claims, contradictions, overstatement, or attribution errors. Reviewers need fast, source-grounded pre-signature QA.

### Near-Term Product

- Synthetic validation demo.
- Buyer/clinician discovery packet.
- Pilot workflow with de-identified or synthetic cases.
- Future semantic evidence mapping.

### Differentiation

- Reviews notes instead of generating them.
- Source-packet-first workflow.
- Supervisor and compliance exports.
- Clear taxonomy for documentation drift.

### Risks

- Real note parsing/NLP is not implemented yet.
- Clinical environments require security, privacy, and validation.
- EHR integration is absent.

### Next Milestones

1. Expand synthetic dataset.
2. Add upload/paste source-note workflow.
3. Implement first real evidence-mapping prototype.
4. Conduct clinician discovery interviews.

## FlareFrame MG Signal

### Product

MG Signal is a local-first Android companion for Myasthenia Gravis symptom, flare, treatment, recovery, function, and appointment-summary tracking.

### Current Assets

- Kotlin/Jetpack Compose Android app.
- Fast log screen.
- Flare lifecycle.
- MG symptom buttons.
- Medication, infusion, rest-needed, and quick-note event types.
- Daily function and weekly QOL check-ins.
- Local JSON persistence.
- Doctor Visit Mode summary builder.
- Cautious insight engine that refuses to infer from insufficient data.
- Weather and Health Connect integration boundaries.
- No fake patient data posture.
- Reported positive micro-feedback from disabled individuals.

### User Problem

People with MG may lack the bandwidth to reconstruct symptoms, timing, treatment proximity, recovery, and functional impact during medical appointments.

### Near-Term Product

- Android symptom and flare tracker.
- Doctor Visit Mode summary.
- Export/share workflow.
- Structured disability-community beta.

### Differentiation

- MG-first workflow.
- No fabricated missing data.
- Recovery and function emphasis.
- Clinician-ready plain text output.

### Risks

- Health privacy and medical-claims boundary.
- Needs accessibility testing.
- Needs real export, backup, and possibly encrypted storage.
- Positive feedback is not clinical validation.

### Next Milestones

1. Verify repeatable builds/tests.
2. Add PDF/share export.
3. Add encrypted backup/import/export plan.
4. Run structured beta feedback with disabled users.

