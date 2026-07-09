# Next Upgrade Outline

This outline details the remaining tasks to fully wire up the new **Year Ahead Texture** events (Progressions & Solar Arcs) and address the quarantined "mad-libs" style prose files.

## 1. Content Block Creation (Progressions & Solar Arcs)
The engine is currently calculating Progressions and Solar Arcs, but they have no prose blocks. Four new JSON files must be created to store this text:

- `blocks/entangled_oracle/EO_Standard_Progression_Blocks.json`
- `blocks/plainspeak/progression_blocks.json`
- `blocks/entangled_oracle/EO_Standard_Solar_Arc_Blocks.json`
- `blocks/plainspeak/solar_arc_blocks.json`

## 2. Prose Rewrite (Quarantined Files)
The following files were quarantined into `blocks/TODO/` due to highly repetitive, mad-libs style prose. They need to be rewritten with dynamic, plainspoken language before they can be safely re-integrated into the active pipeline:
- `predictive_chapters.json`
- `transit_blocks.json` (and `EO_standard_transit_blocks_working.json`)
- `year_overview.json` (and `EO_Standard_Year_Overview_Blocks.json`)
- `year_integration.json` (and `EO_Standard_Year_Integration_Blocks.json`)
- `eclipse_blocks.json` (and `EO_Standard_Eclipse_Blocks.json`)

## 3. Core Wiring Updates

### `config.py`
Update the `CONTENT_PACKS` dictionary to include new keys (e.g., `year_texture_progressions` and `year_texture_solar_arc`) pointing to the newly created JSON files for both `plainspeak` and `entangled_oracle` packs.

### `generate.py`
In the `year_ahead` report generation function (~line 7310), iterate over `year_texture_progressions` and `year_texture_solar_arc`. Use `select_block_from_path(pack["year_texture_progressions"], ...)` to extract the localized prose from the new JSON blocks and inject it into each event dictionary.

### HTML Templates (`products/year_ahead/templates/year_ahead.html`)
Add a new designated output section in the HTML template. Use Jinja loops (`{% for event in year_texture_progressions %}`) to visually render the event titles, dates, and newly attached prose.
