# Versioning Policy

## Purpose

Every generated report must be traceable to the formulas, templates, block files, and report-generation code used to create it.

## Active Versioned Layers

- Formula modules
- Standard engine package
- Established-niche registry
- EO proprietary formula package
- Content libraries
- Block files
- Templates
- Visual system / CSS
- Report-generation code
- Output package

## Operational Rule

Each generated report writes a sidecar manifest:

- `<report>.manifest.json`

That manifest records:

- report version
- methodology
- birth-time confidence
- active standard modules
- active established-niche modules
- EO layer status
- content-pack version
- template version
- formula version bundle
- block-library version
- warnings or missing inputs
- trace reference when available

## Version Form

Two forms are used together:

1. Human-readable package versions
2. File fingerprints derived from active production files

Human-readable package versions communicate release intent.
Fingerprints make the exact local input set reproducible.

## Report-Level Traceability

At minimum, a report is considered operationally traceable only when its manifest contains:

- Tropical zodiac
- Whole Sign houses
- report version
- content pack name and fingerprint
- template fingerprint
- block-library fingerprint
- formula bundle fingerprints

## Excluded from Active Production Metadata

The active production manifest must not rely on inactive concepts such as:

- Sidereal
- Placidus
- ayanamsa
- synthesis profile

## Change Discipline

Any intentional change to formulas, routing, templates, CSS, or content libraries should produce a different fingerprint in the next generated manifest, even when the human-readable package version is not yet bumped.

Human-readable package versions should be bumped when a change is intentionally accepted into the production baseline.
