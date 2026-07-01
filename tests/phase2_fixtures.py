import os
import sys
from copy import deepcopy

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
if "selectors" in sys.modules:
    selectors_module = sys.modules["selectors"]
    selectors_path = getattr(selectors_module, "__file__", "") or ""
    if "C:\\entangled_oracle\\selectors" not in selectors_path.replace("/", "\\"):
        del sys.modules["selectors"]

from config import MAJOR_ASPECTS
from selectors.utils import angular_distance, get_max_orb

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

STANDARD_BODIES = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
    "Pluto",
    "Chiron",
]

DEFAULT_LONGITUDES = {
    "Sun": 15.0,
    "Moon": 52.0,
    "Mercury": 88.0,
    "Venus": 134.0,
    "Mars": 182.0,
    "Jupiter": 219.0,
    "Saturn": 266.0,
    "Uranus": 301.0,
    "Neptune": 328.0,
    "Pluto": 345.0,
    "Chiron": 112.0,
}

DEFAULT_SPEEDS = {
    "Sun": 1.0,
    "Moon": 13.0,
    "Mercury": 1.2,
    "Venus": 1.0,
    "Mars": 0.5,
    "Jupiter": 0.1,
    "Saturn": 0.08,
    "Uranus": 0.03,
    "Neptune": 0.02,
    "Pluto": 0.01,
    "Chiron": 0.03,
}


def longitude_to_sign(longitude: float) -> str:
    return SIGNS[int((longitude % 360) // 30)]


def whole_sign_house(longitude: float, asc_longitude: float) -> int:
    body_sign_index = int((longitude % 360) // 30)
    asc_sign_index = int((asc_longitude % 360) // 30)
    return ((body_sign_index - asc_sign_index) % 12) + 1


def make_body(longitude: float, asc_longitude: float, speed: float = 1.0) -> dict:
    sign = longitude_to_sign(longitude)
    degree_decimal = round(longitude % 30, 4)
    return {
        "longitude": round(longitude % 360, 4),
        "speed": round(speed, 4),
        "retrograde": speed < 0,
        "house": whole_sign_house(longitude, asc_longitude),
        "sign": sign,
        "degree": int(degree_decimal),
        "minute": int((degree_decimal % 1) * 60),
        "degree_decimal": degree_decimal,
    }


def make_houses(asc_sign: str) -> dict:
    asc_index = SIGNS.index(asc_sign)
    houses = {}
    for offset in range(12):
        sign = SIGNS[(asc_index + offset) % 12]
        longitude = ((asc_index + offset) % 12) * 30.0
        houses[f"House_{offset + 1}"] = {
            "longitude": longitude,
            "sign": sign,
            "degree": 0,
            "minute": 0,
            "degree_decimal": 0.0,
        }
    return houses


def make_angles(asc_longitude: float) -> dict:
    asc_sign = longitude_to_sign(asc_longitude)
    mc_longitude = 270.0
    dsc_longitude = (asc_longitude + 180.0) % 360
    ic_longitude = (mc_longitude + 180.0) % 360
    return {
        "Ascendant": make_body(asc_longitude, asc_longitude, speed=0.0),
        "Midheaven": make_body(mc_longitude, asc_longitude, speed=0.0),
        "Descendant": make_body(dsc_longitude, asc_longitude, speed=0.0),
        "Imum_Coeli": make_body(ic_longitude, asc_longitude, speed=0.0),
        "Vertex": make_body(210.0, asc_longitude, speed=0.0),
    }


def build_aspects(placements: dict[str, float]) -> list[dict]:
    aspects = []
    names = [name for name in STANDARD_BODIES if name in placements]
    for index, body_a in enumerate(names):
        for body_b in names[index + 1:]:
            distance = angular_distance(placements[body_a], placements[body_b])
            best = None
            for aspect_name, exact_angle in MAJOR_ASPECTS:
                orb = abs(distance - exact_angle)
                max_orb = get_max_orb(body_a, body_b, aspect_name)
                if orb > max_orb:
                    continue
                candidate = {
                    "body_1": body_a,
                    "body_2": body_b,
                    "aspect": aspect_name,
                    "orb": round(orb, 4),
                    "angle": round(distance, 4),
                }
                if best is None or candidate["orb"] < best["orb"]:
                    best = candidate
            if best:
                aspects.append(best)
    return aspects


def build_payload(
    asc_sign: str = "Aries",
    placements: dict[str, float] | None = None,
    speeds: dict[str, float] | None = None,
    simple_mode: bool = False,
    custom_asteroids: dict[str, dict] | None = None,
    user_profile_overrides: dict | None = None,
) -> dict:
    asc_longitude = SIGNS.index(asc_sign) * 30.0
    placements = {**DEFAULT_LONGITUDES, **(placements or {})}
    speeds = {**DEFAULT_SPEEDS, **(speeds or {})}
    standard_planets = {
        body: make_body(placements[body], asc_longitude, speeds[body])
        for body in STANDARD_BODIES
    }
    user_profile = {
        "simple_mode": simple_mode,
        "house_system": "Whole Sign",
        "zodiac": "Tropical",
        "methodology_id": "tropical_whole",
        "methodology_label": "Tropical zodiac + Whole Sign houses",
        "methodology": {
            "id": "tropical_whole",
            "label": "Tropical zodiac + Whole Sign houses",
            "zodiac": "Tropical",
            "house_system": "Whole Sign",
        },
    }
    if user_profile_overrides:
        user_profile.update(user_profile_overrides)

    return {
        "simple_mode": simple_mode,
        "user_profile": user_profile,
        "standard_planets": standard_planets,
        "angles": make_angles(asc_longitude),
        "houses": make_houses(asc_sign),
        "aspects": build_aspects(placements),
        "custom_asteroids": custom_asteroids or {},
    }


PHASE8_REQUIRED_SCENARIOS = {
    "exact_birth_time",
    "approximate_birth_time",
    "unknown_birth_time",
    "day_chart",
    "night_chart",
    "chart_ruler_in_angular_house",
    "chart_ruler_in_cadent_house",
    "traditional_ruler_emphasis",
    "modern_ruler_modifier_case",
    "high_prominence_planet",
    "low_prominence_planet",
    "retrograde_planet",
    "station_proximity",
    "high_dignity",
    "low_dignity",
    "mutual_reception",
    "dispositor_loop",
    "strong_aspect_hub",
    "isolated_planet",
    "valid_named_pattern",
    "no_named_pattern",
    "strong_vocational_structure",
    "strong_relational_structure",
    "strong_inner_life_structure",
    "asteroid_rich_established_niche_chart",
    "eo_index_rich_chart",
    "forecast_convergence_period",
    "forecast_quiet_period",
    "long_duration_transit",
    "multiple_pass_retrograde_transit",
    "eclipse_to_central_natal_factor",
    "simple_dob_only_chart",
}


def _asteroids_for_rich_fixture(asc_longitude: float) -> dict:
    return {
        "Kassandra": make_body(2.0, asc_longitude, speed=0.04),
        "Aphrodite": make_body(31.0, asc_longitude, speed=0.03),
        "Sirene": make_body(62.0, asc_longitude, speed=0.02),
        "Medusa": make_body(94.0, asc_longitude, speed=0.02),
        "Persephone": make_body(181.0, asc_longitude, speed=0.01),
        "Psyche": make_body(214.0, asc_longitude, speed=0.02),
    }


def _phase8_fixture_definitions() -> dict[str, dict]:
    return {
        "exact_day_angular_ruler": {
            "description": "Exact-time day chart with an angular chart ruler, vocational emphasis, and several strong structural signatures.",
            "report_name": "Phase8 Exact Day",
            "birth_data": {
                "name": "Phase8 Exact Day",
                "date": "1992-03-21",
                "time": "08:11",
                "location": "Peoria, IL",
                "report_date": "2026-01-01",
            },
            "payload": build_payload(
                asc_sign="Leo",
                placements={
                    "Sun": 5.0,
                    "Moon": 65.0,
                    "Mercury": 8.0,
                    "Venus": 42.0,
                    "Mars": 98.0,
                    "Jupiter": 122.0,
                    "Saturn": 275.0,
                    "Uranus": 281.0,
                    "Neptune": 350.0,
                    "Pluto": 256.0,
                    "Chiron": 111.0,
                },
                speeds={"Mercury": -0.05, "Jupiter": 0.01},
            ),
            "scenarios": [
                "exact_birth_time",
                "day_chart",
                "chart_ruler_in_angular_house",
                "traditional_ruler_emphasis",
                "high_prominence_planet",
                "retrograde_planet",
                "station_proximity",
                "high_dignity",
                "strong_aspect_hub",
                "valid_named_pattern",
                "strong_vocational_structure",
                "forecast_convergence_period",
                "long_duration_transit",
                "eclipse_to_central_natal_factor",
            ],
        },
        "approximate_night_cadent_ruler": {
            "description": "Approximate-time night chart with a cadent ruler, inner-life emphasis, and reduced-confidence safety expectations.",
            "report_name": "Phase8 Approximate Night",
            "birth_data": {
                "name": "Phase8 Approximate Night",
                "date": "1988-11-04",
                "time": "21:17",
                "location": "Austin, TX",
                "report_date": "2026-01-01",
            },
            "payload": build_payload(
                asc_sign="Virgo",
                placements={
                    "Sun": 223.0,
                    "Moon": 342.0,
                    "Mercury": 292.0,
                    "Venus": 188.0,
                    "Mars": 26.0,
                    "Jupiter": 56.0,
                    "Saturn": 87.0,
                    "Uranus": 170.0,
                    "Neptune": 205.0,
                    "Pluto": 244.0,
                    "Chiron": 14.0,
                },
                speeds={"Venus": -0.02, "Saturn": 0.005},
                user_profile_overrides={
                    "birth_time_state": "approximate",
                    "birth_time_confidence": "approximate",
                },
            ),
            "scenarios": [
                "approximate_birth_time",
                "night_chart",
                "chart_ruler_in_cadent_house",
                "low_prominence_planet",
                "station_proximity",
                "low_dignity",
                "isolated_planet",
                "no_named_pattern",
                "strong_inner_life_structure",
                "forecast_quiet_period",
            ],
        },
        "exact_modern_relational": {
            "description": "Exact-time chart designed to stress relational themes, modern-ruler modifier handling, and mutual-reception style routing.",
            "report_name": "Phase8 Relational",
            "birth_data": {
                "name": "Phase8 Relational",
                "date": "1995-02-15",
                "time": "18:42",
                "location": "Seattle, WA",
                "report_date": "2026-01-01",
            },
            "payload": build_payload(
                asc_sign="Aquarius",
                placements={
                    "Sun": 326.0,
                    "Moon": 147.0,
                    "Mercury": 301.0,
                    "Venus": 359.0,
                    "Mars": 179.0,
                    "Jupiter": 89.0,
                    "Saturn": 312.0,
                    "Uranus": 305.0,
                    "Neptune": 294.0,
                    "Pluto": 242.0,
                    "Chiron": 59.0,
                },
                speeds={"Mars": -0.03},
            ),
            "scenarios": [
                "exact_birth_time",
                "night_chart",
                "modern_ruler_modifier_case",
                "mutual_reception",
                "dispositor_loop",
                "strong_relational_structure",
                "multiple_pass_retrograde_transit",
            ],
        },
        "exact_asteroid_rich": {
            "description": "Exact-time chart with dense asteroid support for established-niche routing and asteroid portrait review.",
            "report_name": "Phase8 Asteroid Rich",
            "birth_data": {
                "name": "Phase8 Asteroid Rich",
                "date": "1990-06-15",
                "time": "14:22",
                "location": "Chicago, IL",
                "report_date": "2026-01-01",
            },
            "payload": build_payload(
                asc_sign="Aries",
                placements={
                    "Sun": 84.0,
                    "Moon": 122.0,
                    "Mercury": 88.0,
                    "Venus": 61.0,
                    "Mars": 3.0,
                    "Jupiter": 244.0,
                    "Saturn": 276.0,
                    "Uranus": 274.0,
                    "Neptune": 286.0,
                    "Pluto": 231.0,
                    "Chiron": 97.0,
                },
                custom_asteroids=_asteroids_for_rich_fixture(0.0),
            ),
            "scenarios": [
                "exact_birth_time",
                "asteroid_rich_established_niche_chart",
                "eo_index_rich_chart",
            ],
        },
        "simple_dob_only": {
            "description": "DOB-only simple chart used to verify unknown-time fallbacks stay explicit and humane.",
            "report_name": "Phase8 Simple DOB",
            "birth_data": {
                "name": "Phase8 Simple DOB",
                "date": "1990-06-15",
                "time": None,
                "location": "Unknown location",
                "report_date": "2026-01-01",
                "simple_mode": True,
            },
            "payload": build_payload(
                asc_sign="Aries",
                simple_mode=True,
                placements={
                    "Sun": 84.0,
                    "Moon": 122.0,
                    "Mercury": 88.0,
                    "Venus": 61.0,
                    "Mars": 3.0,
                    "Jupiter": 244.0,
                    "Saturn": 276.0,
                    "Uranus": 274.0,
                    "Neptune": 286.0,
                    "Pluto": 231.0,
                    "Chiron": 97.0,
                },
            ),
            "scenarios": [
                "unknown_birth_time",
                "simple_dob_only_chart",
            ],
        },
    }


def get_phase8_fixture_library() -> dict[str, dict]:
    library = {}
    for key, spec in _phase8_fixture_definitions().items():
        entry = deepcopy(spec)
        entry["scenarios"] = sorted(set(entry.get("scenarios", [])))
        library[key] = entry
    return library


def build_phase8_fixture(name: str) -> dict:
    library = get_phase8_fixture_library()
    if name not in library:
        raise KeyError(f"Unknown Phase 8 fixture '{name}'")
    return deepcopy(library[name])
