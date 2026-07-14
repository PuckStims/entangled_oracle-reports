# Standard Clock Integration Audit

**Status:** Local-file audit completed before Location Services expansion.  
**Purpose:** Confirm which standard predictive clocks are already integrated into existing reports, which are indirect only, and which are not report-ready.

## Executive Result

EO should not treat the standard predictive clocks as a blank backend project. Most of the computation already exists. The practical work is report-contract cleanup: keep client-visible clocks in the right report, prevent overreach, and make documentation match runtime truth.

## Current Integration Matrix

| Clock | Computes Locally | Year Ahead | Personal Forecast | Current Product Meaning |
| --- | --- | --- | --- | --- |
| Secondary progressions | Yes, `engine/progressions.py` | Visible in Directed Clock Highlights when selected as year texture | Modifier-scale Moon progression contacts feed `all_events` and can affect themes/timing/predictive surface | Integrated, but split by scope |
| Solar Arc directions | Yes, `engine/solar_arc.py` | Visible in Directed Clock Highlights | Not consumed directly | Integrated for Year Ahead only |
| Exact returns | Yes, `engine/returns.py` | Visible as grouped Timing Notes & Recurring Clocks | Included in forecast synthesis / predictive research candidate evidence | Timestamp-level integration, not return-chart interpretation |
| Annual profections | Yes, `engine/profections.py` | Visible as grouped Timing Notes & Recurring Clocks and used as transit weighting support | Included in forecast synthesis / predictive research candidate evidence | Integrated as time-lord context, not full annual-profection delineation |
| Zodiacal Releasing | Yes, `engine/zodiacal_releasing.py` | Visible as grouped Timing Notes & Recurring Clocks and forecast terrain evidence | Included in forecast synthesis / predictive research candidate evidence | Integrated as research/timing context, not a full standalone ZR report |
| Lots | Yes, `engine/lots.py` | Substrate for Zodiacal Releasing | Substrate for Zodiacal Releasing | Computed support layer only; no standalone Lots report content |
| Return charts | No | Not available | Not available | New computation required |
| Relocated returns | No | Not available | Not available | New computation required |

## Report Path Evidence

`engine/transit_engine.py` is the shared scan surface. `compute_year_ahead_events()` returns:

```text
transits
ingresses
stations
eclipses
lunations
progressions
return_events
zodiacal_releasing_events
time_lord_periods
zodiacal_releasing_periods
year_texture_progressions
year_texture_solar_arc
all_events
```

`products/year_ahead/templates/active/year_ahead.html` renders:

- `year_texture_progressions`
- `year_texture_solar_arc`
- `tier5_predictive_surfaces.annual_profections`
- `tier5_predictive_surfaces.zodiacal_releasing`
- `tier5_predictive_surfaces.exact_returns`
- `tier5_predictive_surfaces.forecast_terrain`
- `predictive_report_surface`

`products/personal_forecast/templates/personal_forecast.html` renders `predictive_report_surface`, which is built from `forecast_synthesis`.

## Findings By Clock

### Progressions

Year Ahead already has a dedicated visible section for chapter-scale secondary progressions and Solar Arc. The selection boundary lives in `_select_client_year_texture_events()`, which keeps only client-eligible chapter events and excludes raw sandbox-style contacts.

Personal Forecast already calls:

```python
compute_year_ahead_events(..., include_moon_progressions=True)
```

Those returned progression events are included in `timeline["all_events"]`, so they can affect Personal Forecast themes, timing windows, event counts, and forecast synthesis. The local runtime check confirmed this path.

The issue found during this audit was narrower: `_filter_moon_progression_events()` admitted a few chapter-scale non-Moon events when they targeted the Moon. That is now tightened so Personal Forecast keeps only modifier-scale Moon progression events; chapter-scale progressions remain Year Ahead texture.

### Solar Arc

Solar Arc is production-visible in Year Ahead via Directed Clock Highlights. It is not consumed by Personal Forecast directly. That is coherent with its current governance status because Solar Arc is chapter-scale, not a 90-day modifier by default.

### Returns

Exact returns are computed and surfaced in Year Ahead as grouped timing notes. They are also available to Personal Forecast's `forecast_synthesis`, so they can appear through the predictive research surface as method-family evidence.

This is not return-chart interpretation. The repo still does not compute return chart angles, houses, chart aspects, or return-to-natal overlays.

### Annual Profections

Annual profections are computed as `time_lord_periods`, used internally as a transit weighting support, and surfaced in Year Ahead grouped timing notes. Personal Forecast can receive them through `forecast_synthesis`.

This is time-lord context, not a full profection report with dignity, monthly lord handoff, or complete annual technique prose.

### Zodiacal Releasing

ZR computes Fortune/Spirit period trees and events. Year Ahead surfaces grouped timing notes and forecast terrain context. Personal Forecast can receive ZR method evidence through forecast synthesis and candidate-family prose.

This is a research/timing-note integration, not a standalone Zodiacal Releasing product.

### Lots

Lots are computed as natal points and used by ZR. They do not directly enter the report event pipeline and do not have standalone report content. For Location Services, they should be treated as a support substrate unless a future product deliberately opens natal Lots interpretation.

## Content Block Status

The old Tier 5 timing blocks began as literal `TODO` scaffolds, but the current local test contract now prevents reintroducing literal TODO placeholders into:

```text
products/year_ahead/blocks/plainspeak/annual_profection_blocks.json
products/year_ahead/blocks/plainspeak/zodiacal_releasing_blocks.json
products/year_ahead/blocks/plainspeak/return_blocks.json
products/year_ahead/blocks/plainspeak/forecast_synthesis_blocks.json
```

Personal Forecast already has in-depth predictive candidate leaves for:

```text
return_family_sun
return_family_moon
return_family_jupiter
return_family_saturn
progression_family
solar_arc_family
profection_family
zr_family_fortune
zr_family_spirit
```

That means the next unlock should usually be wiring/selection/visibility, not blank prose creation.

## Location Services Implication

Living Map should reuse the existing standard-clock infrastructure after the static location baseline is correct. Location Services should not rebuild returns, profections, ZR, Lots, progressions, or Solar Arc as parallel systems.

The true new locational work remains:

- relocated chart construction from the preserved birth UTC instant;
- astrocartography line geometry;
- distance-to-line and nearest-point math;
- Local Space;
- parans;
- relocated return charts, if opened later;
- `LocationEvidenceRecord` assembly and product rendering.
