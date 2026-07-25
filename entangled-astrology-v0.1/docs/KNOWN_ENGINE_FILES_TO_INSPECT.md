# Known Engine Files to Inspect

Begin with the files and paths already identified in Entangled Oracle diagnostics, then verify them against the supplied repository:

- `ARCHITECTURE.md`
- `agents/README.md`
- `agents/PROFESSIONAL_GRADE_UPGRADE_DIRECTIVES.md`
- `agents/HIGH_THROUGHPUT_AGENT_PROMPTS.md`
- `agents/PLANNED_UPDATES.md`
- `agents/REVISIONS.md`
- `engine/transit_engine.py`
- `engine/forecast_event_adapter.py`
- `engine/normalization.py` if present at the supplied revision
- `formulas/standard/forecast_activation.py`
- `formulas/governance_registry.py`
- progression and solar-arc engines
- report generation entry point and `generate.py`
- `build_report_context`
- `_select_year_block`
- `CONTENT_PACKS`

This list is a starting map, not permission to assume current paths or behavior. Codex must inspect the actual supplied revision.
