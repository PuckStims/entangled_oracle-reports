# Synastry Computation First Draft

Status: planning contract, not yet implemented.

Purpose: define synastry as a computation-first system whose client-facing
claims are seconded by the depth, complexity, and accuracy of the base
mathematics. This file is the Tier 6 working spec for the first backend
build pass.

## Core Position

Synastry should not be scoped as a thin relationship report. It should be a
two-chart mathematical layer with explicit confidence states, traceable
formula outputs, and tests for the conditions under which each computation
is valid.

The priority order is:

1. Pair-chart data model.
2. Cross-chart aspect mathematics.
3. Directional house and angle overlays.
4. Mutual/contact normalization.
5. Composite chart mathematics.
6. Relationship-specific topic and convergence formulas.
7. Relationship timing, only when each input clock has a real implemented
   scanner and a clear target domain.
8. Report prose and templates after the evidence layer is stable enough to
   support product claims.

This is a positive feature priority, not a feature-minimization rule. Every
feature can be planned, but no feature should be described as live,
finished, or product-ready until its mathematical contract, confidence
policy, fixtures, and sidecar trace are implemented.

## Existing Hooks To Reuse

- Natal payload generation: `engine/natal_engine.py::generate_payload`
- Broad natal aspect detector: `engine/natal_engine.py::detect_aspect`
- Synastry orb config: `config.ORB_CONFIG["max_orb_synastry"]`
- Major aspect vocabulary: `config.MAJOR_ASPECTS`
- Birth-time confidence states: `formulas/standard/confidence.py`
- Current architecture source: `ARCHITECTURE.md`

The first implementation should reuse two complete natal payloads rather
than inventing a second birth/chart path.

## Pair-Chart Payload

The pair payload should be a new object, not a mutated natal payload:

```python
{
    "schema_version": "synastry_pair_v0.1",
    "person_a": {
        "label": "A",
        "natal_payload": {...},
        "birth_time_state": "exact_birth_time",
        "angle_eligible": True,
    },
    "person_b": {
        "label": "B",
        "natal_payload": {...},
        "birth_time_state": "unknown_birth_time",
        "angle_eligible": False,
    },
    "relationship_meta": {
        "relationship_type": "unspecified",
        "consent_state": "unreviewed",
        "calculated_at": "ISO-8601",
    },
    "computations": {
        "directional_aspects": [],
        "mutual_aspects": [],
        "house_overlays": [],
        "repeated_natal_themes": [],
        "composite": {},
        "relationship_topic_signatures": [],
    },
    "confidence": {
        "angle_house_policy": {},
        "withheld_records": [],
        "assumptions": [],
    },
    "provenance": {
        "source_payload_ids": [],
        "formula_versions": [],
    },
}
```

The object should preserve the separateness of both natal charts. A pair
calculation is not a new single chart until a specific composite/Davison
method constructs one.

## Body And Point Eligibility

Start with a controlled target set:

- Luminaries: Sun, Moon
- Personal planets: Mercury, Venus, Mars
- Social planets: Jupiter, Saturn
- Outer planets: Uranus, Neptune, Pluto
- Chiron if present in both payloads
- Lunar nodes if already present under a stable payload key
- Angles/points: Ascendant, Descendant, Midheaven, Imum Coeli, Vertex

Eligibility rules:

- Planet-to-planet and planet-to-node contacts are time-optional once both
  longitudes exist.
- Angle contacts require the relevant person's birth-time state to be exact
  or explicitly angle-eligible.
- House overlays require the house-owner's Ascendant/house structure to be
  exact or explicitly angle-eligible.
- Asteroids should wait for a separate policy pass unless the product owner
  chooses a small named set with explicit rationale and orb rules.

## Cross-Chart Aspect Mathematics

For every eligible source body/point and target body/point:

```python
distance = min(abs((source_lon - target_lon) % 360),
               360 - abs((source_lon - target_lon) % 360))
orb = abs(distance - exact_aspect_angle)
```

An aspect is active when:

```python
orb <= configured_synastry_orb(source, target, aspect)
```

Initial configured orb:

- Use `config.ORB_CONFIG["max_orb_synastry"]` as the hard cap.
- Allow tighter per-body/per-aspect policy later, but do not exceed the
  synastry cap without changing config and tests together.
- Record `orb`, `exact_angle`, `measured_distance`, and `orb_fraction`.

Suggested `orb_fraction`:

```python
orb_fraction = 1.0 - (orb / max_orb)
```

Clamp to `[0.0, 1.0]`.

## Directional Aspects

Every cross-chart aspect should have a directional record:

```python
{
    "record_type": "directional_aspect",
    "source_person": "A",
    "source_body": "Venus",
    "target_person": "B",
    "target_body": "Mars",
    "aspect": "Square",
    "exact_angle": 90.0,
    "measured_distance": 91.2,
    "orb": 1.2,
    "max_orb": 5.0,
    "orb_fraction": 0.76,
    "source_domain": "affection/attraction/value",
    "target_domain": "desire/assertion/action",
    "directional_dependency": "body_to_body",
    "confidence_state": "exact_birth_time",
    "withheld": False,
}
```

Direction matters when:

- a body from one chart falls in the other person's houses;
- the target is an angle or house-sensitive point;
- later prose describes whose planet activates whose field.

Direction does not mean blame, diagnosis, or causality. It is a routing and
localization property.

## Mutual Aspect Normalization

After directional aspects are computed, build mutual records for each
unordered cross-chart body pair:

```python
mutual_key = frozenset({
    ("A", source_body),
    ("B", target_body),
})
```

The mutual record should:

- keep both directional records when both exist;
- store one canonical aspect identity;
- identify whether the contact is purely body-to-body, angle-dependent,
  or house-dependent;
- expose a single salience score while retaining the raw directions.

Suggested first salience formula:

```python
salience = (
    body_weight(source_body)
    * body_weight(target_body)
    * aspect_weight(aspect)
    * orb_fraction
    * confidence_modifier
)
```

Where initial weights are conservative and transparent:

- Luminaries and angles: 1.20
- Venus, Mars, Mercury: 1.10
- Jupiter, Saturn: 1.00
- Uranus, Neptune, Pluto, Chiron, nodes: 0.85
- Conjunction/Opposition: 1.15
- Square/Trine: 1.00
- Sextile: 0.80

These are ranking weights only. They should be presented as selection
logic, not ontological truth.

## House Overlays

House overlays are directional:

- A body in B house.
- B body in A house.

For Whole Sign houses, calculate against the house-owner's Ascendant sign
or existing house payload. Prefer reusing the natal payload's house
structure rather than recalculating independently.

Overlay record:

```python
{
    "record_type": "house_overlay",
    "source_person": "A",
    "source_body": "Moon",
    "target_person": "B",
    "target_house": 4,
    "target_house_sign": "Cancer",
    "source_longitude": 102.4,
    "confidence_state": "exact_birth_time",
    "withheld": False,
}
```

Withholding policy:

- If B's birth time is unknown, A-in-B house overlays are withheld.
- If A's birth time is unknown, B-in-A house overlays are withheld.
- If a body longitude exists but the house-owner's angles are unavailable,
  keep the body-to-body aspects but omit house localization.

## Angle Dependency

Angle contact validity depends on the chart that owns the angle.

Examples:

- A Venus conjunct B Ascendant requires B angle eligibility.
- B Mars square A Midheaven requires A angle eligibility.
- A Moon trine B Moon does not require angle eligibility.

Angle-dependent records should fail closed:

- `withheld = True`
- `confidence_state = "angle_dependent_unavailable"`
- include `missing_inputs = ["B.birth_time"]` or equivalent
- do not route into salience ranking as a live contact

## Repeated Natal Themes Between Charts

This layer should compare precomputed natal structures without inventing
interpretation:

- same sign emphasis;
- same element or modality concentration;
- repeated aspect pattern families;
- repeated prominent planets;
- shared angular/house emphases only when both charts are angle-eligible;
- mirrored planet-condition themes when existing standard formulas expose
  stable fields.

Records should identify source evidence from each natal payload:

```python
{
    "record_type": "repeated_theme",
    "theme_key": "venus_saturn_contact",
    "person_a_evidence": {...},
    "person_b_evidence": {...},
    "confidence_state": "exact_birth_time",
    "salience": 0.62,
}
```

## Composite Chart Mathematics

Composite computation should be included in the first formula roadmap, with
implementation gated by tests rather than excluded from scope.

Midpoint formula for each pair of matching bodies:

```python
delta = ((lon_b - lon_a + 540.0) % 360.0) - 180.0
midpoint = (lon_a + (delta / 2.0)) % 360.0
```

If `abs(abs(delta) - 180.0)` is near zero, the midpoint is ambiguous.
Record the ambiguity rather than silently choosing an arbitrary side.

Composite payload should include:

- composite body longitudes;
- composite signs/degrees;
- composite aspects using the same aspect math with composite-specific
  orb policy;
- composite houses only if a house method is explicitly chosen and
  mathematically justified;
- a `composite_method` field, initially `"midpoint_composite"`.

Composite houses need special care because a midpoint composite does not
automatically have a reliable birthplace/time in the same way a natal chart
does. Do not borrow one person's houses for the relationship chart.

## Davison Chart Mathematics

Davison should be treated as a distinct method, not a synonym for composite.

Required inputs:

- both full birth datetimes;
- both birth coordinates;
- a clear midpoint-in-time rule;
- a clear midpoint-in-space rule;
- ephemeris calculation of the resulting chart.

Davison records should identify the method explicitly:

```python
"relationship_chart_method": "davison_space_time_midpoint"
```

This can share downstream aspect/condition summarizers only after its
chart payload is built from its own valid inputs.

## Relationship Topic Signatures

Topic signatures should be computed from evidence families, not prose
similarity.

Initial evidence families:

- attachment/emotional rhythm: Moon contacts, IC/4th overlays when eligible;
- affection/value/attraction: Venus contacts and overlays;
- desire/friction/action: Mars contacts and overlays;
- communication: Mercury contacts and 3rd-house overlays when eligible;
- commitment/constraint/time: Saturn contacts and overlays;
- visibility/public path: Sun/MC/10th indicators when eligible;
- growth/meaning: Jupiter/9th indicators when eligible;
- intensity/merging/shared resources: Pluto/8th indicators when eligible.

Each signature should expose:

- contributing records;
- supportive/tensional/mixed distribution;
- confidence by evidence family;
- whether the signature is body-only, house-localized, or angle-localized.

## Relationship Convergence Scoring

Relationship convergence should be an evidence aggregator over synastry
records, not a one-number compatibility verdict.

First output shape:

```python
{
    "signature_key": "communication_pressure_and_growth",
    "score": 0.71,
    "polarity": "mixed",
    "evidence_count": 5,
    "independent_evidence_families": [
        "mercury_contacts",
        "saturn_contacts",
        "third_house_overlay"
    ],
    "confidence_state": "exact_birth_time",
    "trace": [...]
}
```

Use convergence to rank report material and expose traceability. Do not
turn it into a verdict such as "compatible", "doomed", "soulmate", or
other deterministic relationship labels.

## Relationship Timing

Relationship timing belongs in the architecture, but every timing signal
must declare its target domain:

- `person_a_natal`
- `person_b_natal`
- `composite`
- `davison`
- `shared_window`

Allowed timing sources only when implemented and tested:

- current transits to Person A natal;
- current transits to Person B natal;
- current transits to composite;
- current transits to Davison if Davison exists;
- progressions/Solar Arc to relationship charts only when the relevant
  single-chart method is already implemented and validated.

No timing event should claim relationship outcomes. It should report
symbolic activation of a person chart or relationship chart target.

## Sidecar And Claim Safety

Every synastry output must be able to answer:

- which two source charts were used;
- which computations ran;
- which computations were withheld;
- which formula versions produced the records;
- which records were excluded because of birth-time confidence;
- which records support each selected topic or ranking.

The sidecar should include explicit non-live states:

- `not_implemented`
- `withheld_missing_birth_time`
- `withheld_angle_dependency`
- `withheld_missing_payload_field`
- `implemented_unverified`
- `implemented_verified`

This prevents an audit from mistaking scaffolding for a finished engine.

## Initial Acceptance Tests

The first implementation is not accepted until tests cover:

- two complete exact-time natal payloads produce a pair payload;
- unknown birth time on Person A withholds B-in-A overlays and A-owned
  angle contacts;
- unknown birth time on Person B withholds A-in-B overlays and B-owned
  angle contacts;
- body-to-body aspects still compute when one or both birth times are
  unknown;
- synastry aspects respect `max_orb_synastry`;
- exact circular midpoint math handles signs across 0 Aries;
- opposite-point composite ambiguity is flagged;
- mutual aspect normalization keeps directional evidence;
- salience rankings remain traceable to raw aspect/overlay records;
- sidecar status distinguishes scaffolded, implemented, verified, and
  withheld features.

## First Build Slice

The first code slice should implement:

1. `engine/synastry.py`
2. pair payload builder
3. directional aspect scanner
4. mutual aspect normalizer
5. house overlay scanner with confidence gating
6. composite midpoint body positions with ambiguity flags
7. pytest fixtures for exact/exact, exact/unknown, and unknown/exact pairs

No product template should call synastry "available" until the sidecar
shows implemented and verified status for the relevant computation layers.
