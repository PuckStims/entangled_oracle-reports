# Methods, Methodology, and Choices

This document is the short reviewer-facing statement of the active Entangled Oracle production method.

## Active chart methodology

Entangled Oracle currently generates production reports with:

- Tropical zodiac
- Whole Sign houses
- Swiss Ephemeris chart calculation

The system does not currently route to alternate production methodologies such as Sidereal or Placidus-house reports.

## Core methodological choices

### Angles

- Ascendant and Midheaven are treated as core angle targets.
- Descendant and Imum Coeli are retained as derived display angles.
- Vertex is active as an independent calculated point.

Derived opposite angles are not treated as independent natal aspect targets in the shared natal aspect matrix.

### Nodes

- True Node is used.
- South Node is derived from the North Node axis.

### Black Moon Lilith

- Mean lunar apogee (`MEAN_APOG`) is used for Black Moon Lilith.

### Chiron

- Chiron is included as an active body in the broader Entangled Oracle methodology.
- Chiron does not automatically inherit every core-standard dignity, rulership, or sect rule.

### Forecasting

The active forecast layer uses:

- natal transits
- Whole Sign house ingresses
- planetary stations
- eclipse contacts to selected natal targets

Forecast timing is interpretive rather than deterministic.
It is meant to describe conditions, emphasis, and recurring themes rather than one guaranteed external event.

## Layer distinction

Entangled Oracle has three interpretive layers:

### Standard astrology

Core chart foundation such as luminaries, planets, houses, rulership, aspects, and chart structure.

### Established-niche material

Specialist bodies or methods that remain distinct from the standard chart foundation.

### EO proprietary material

Additional proprietary indexes and synthesis systems that extend or refract patterns already established through the standard chart.

## Proprietary layer

The EO layer is implemented in real calculation code rather than static copy alone.
Active production indexes currently include:

- KVQ
- MKI
- RWI
- DFIS
- Catalyst
- AHL
- NGE

These indexes are not a replacement for the standard chart foundation.
They are an additional interpretive layer on top of it.

## Birth-time confidence

When an exact birth time is available, angle- and house-dependent language can be used more directly.

When birth time is unknown or approximate, time-sensitive material should be reduced, softened, or withheld rather than presented as exact.

## Current limits

The active production system does not claim to provide:

- a single fixed future
- clinical or diagnostic judgment
- exhaustive methodological universality

It is a symbolic interpretive system with declared technical choices.

## Current implementation note

The active production codebase is mid-hardening rather than frozen.
That affects maintainability and presentation risk more than the core methodology itself.
