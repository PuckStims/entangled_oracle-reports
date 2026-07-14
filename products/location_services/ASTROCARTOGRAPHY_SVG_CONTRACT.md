# Astrocartography SVG Contract

**Status:** Wired visual contract, no planetary line geometry yet.  
**Primary code:** [engine/astrocartography_svg.py](C:/entangled_oracle/engine/astrocartography_svg.py)

## Purpose

This seam gives Location Services a real astrocartography visual payload before
astrocartography itself is implemented. It is intentionally honest:

- projection frame: implemented
- birth/destination anchor plotting: implemented
- planetary ASC/DSC/MC/IC line geometry: not implemented
- nearest-point / distance bands: not implemented

The goal is to let report surfaces, HTML templates, and future selectors wire
against a stable map contract now, without pretending line computation already
exists.

## Public Contract

`build_astrocartography_svg_contract(natal_payload, place_context) -> dict`

Stable top-level keys:

- `contract_version`
- `title`
- `status`
- `projection`
- `viewbox`
- `width`
- `height`
- `note`
- `capability_boundary`
- `anchors`
- `layers`
- `warnings`
- `svg`

## Current Semantics

### `status`

Current status is:

```text
contract_ready_future_method
```

Meaning:

- the visual surface is wired
- the report may safely render the panel
- planetary-line claims remain out of bounds

### `anchors`

Current anchor payload:

- `anchors.birth`
  - sourced from `natal_payload.user_profile.resolved_coordinates`
- `anchors.destination`
  - sourced from `place_context.destination_context`

Each anchor includes:

- `x`, `y` SVG coordinates
- `latitude`, `longitude`
- `label`
- `display_name`
- `source`

### `layers`

Current layer IDs:

- `projection_frame`
- `graticule`
- `birth_anchor`
- `destination_anchor`
- `planetary_lines`
- `distance_bands`

The first four may render now. The last two are explicitly marked
`future_method`.

## Projection

The current contract uses:

```text
equirectangular
```

This is simple, stable, and explicit. It is good enough for:

- fixed SVG framing
- anchor plotting
- future line-path serialization

If projection changes later, that should be a versioned contract change, not a
silent swap.

## Rendered Surface

Place Resonance now renders the contract into the visual slot in:

- [products/location_services/place_resonance_renderer.py](C:/entangled_oracle/products/location_services/place_resonance_renderer.py)
- [products/location_services/templates/place_resonance.html](C:/entangled_oracle/products/location_services/templates/place_resonance.html)

The current sample output is:

- [output/location_services/sample_place_resonance.html](C:/entangled_oracle/output/location_services/sample_place_resonance.html)

## Next Geometry Step

When real astrocartography line computation begins, the cleanest next payload
shape is:

```python
{
  "Sun": {
    "MC": [{"lat": ..., "lon": ...}, ...],
    "IC": [{"lat": ..., "lon": ...}, ...],
    "ASC": [{"lat": ..., "lon": ...}, ...],
    "DSC": [{"lat": ..., "lon": ...}, ...],
  },
  ...
}
```

That shape is compatible with the current contract because the `planetary_lines`
layer already exists as a named slot.

## Boundaries

This contract does **not** currently authorize:

- line proximity claims
- map-based interpretive prose
- cluster claims
- nearest-line ranking
- remote activation
- parans
- Local Space

Those remain future methods and should only be surfaced after real computation
exists.
