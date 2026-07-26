"""Generate a deterministic EIA v0.1 sample report JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from eia_engine import build_eia_report


SAMPLE_NATAL_CHART = {
    "client": {
        "name": "EIA Fixture",
        "birth_datetime": "1992-03-21T08:11:00-06:00",
        "birth_location": "Peoria, IL",
        "birth_time_confidence": "exact",
    },
    "standard_planets": {
        "Sun": {"sign": "Aries", "degree": 1.2, "house": 1},
        "Moon": {"sign": "Cancer", "degree": 12.5, "house": 4},
        "Mercury": {"sign": "Pisces", "degree": 28.0, "house": 12},
        "Venus": {"sign": "Taurus", "degree": 6.4, "house": 2},
        "Mars": {"sign": "Leo", "degree": 17.9, "house": 5},
        "Jupiter": {"sign": "Libra", "degree": 21.0, "house": 7},
        "Saturn": {"sign": "Aquarius", "degree": 14.0, "house": 11},
        "Uranus": {"sign": "Capricorn", "degree": 18.0, "house": 10},
        "Neptune": {"sign": "Capricorn", "degree": 19.0, "house": 10},
        "Pluto": {"sign": "Scorpio", "degree": 22.0, "house": 8},
    },
    "angles": {
        "Ascendant": {"sign": "Aries", "house": 1},
        "Midheaven": {"sign": "Capricorn", "house": 10},
    },
    "aspects": [{"body1": "Mars", "body2": "Uranus", "aspect": "trine"}],
    "birth_time_confidence": "exact",
}


def main() -> None:
    output_path = Path("output") / "eia_sample_report_v0_1.json"
    output_path.parent.mkdir(exist_ok=True)
    report = build_eia_report(
        SAMPLE_NATAL_CHART,
        eas_indexes={
            "dominant_current": "Catalyst Index",
            "expression": "Narrative translation",
            "activation_state": "baseline",
        },
        state_overlay={
            "method": "tarot_entropy",
            "seed_id": "eia-fixture-001",
            "active_register": "decision",
            "symbol": "Temperance",
            "state_message": "The current field favors pacing, return, and integration.",
            "experiment": "Wait one sleep cycle before converting first recognition into commitment.",
            "mode_hints": ["Tidal Knowing"],
        },
    )
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
