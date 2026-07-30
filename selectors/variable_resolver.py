"""
selectors/variable_resolver.py — Entangled Oracle Variable Resolver

Flattens natal-chart data and formula results into template-ready variables.

Supports both:
- Legacy Asteroid Portrait variables (MAGNETIC compatibility)
- EAS v0.2 variables (NGE, expression names, activation states)

This preserves the existing report templates while exposing the newer
formula layer for the next template migration.
"""

from datetime import datetime, timezone
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import INDEX_DIMENSION_NAMES
from selectors.utils import get_sign_element, get_sign_modality
from formulas.standard_indexes import (
    get_day_ruler,
    get_dominant_element,
    get_house_domain,
    get_house_theme,
    get_sun_moon_relationship,
)


# ── Naming / Compatibility ─────────────────────────────────────

EAS_DIMENSION_NAMES = {
    "KVQ": "Your Foresight Pattern",
    "MKI": "Your Knowledge Legacy",
    "RWI": "Your Reality Field",
    "DFIS": "Your Power Current",
    "NGE": "Your Narrative Genre",
    "CATALYST": "Your Impact Radius",
    "AHL": "Your Ancestral Thread",
}


def _record(data) -> dict:
    """Returns a safe dictionary for an optional payload or index record."""
    return data if isinstance(data, dict) else {}


def _numeric(value, default: float = 0.0) -> float:
    """Returns a template-ready float for score-like values."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _slug_component_key(name: str) -> str:
    """Normalizes component names to safe snake_case suffixes."""
    slug = []
    previous_was_sep = False
    for char in str(name or "").strip().lower():
        if char.isalnum():
            slug.append(char)
            previous_was_sep = False
        elif not previous_was_sep:
            slug.append("_")
            previous_was_sep = True
    return "".join(slug).strip("_")


def _flatten_numeric_components(
    variables: dict,
    prefix: str,
    components: dict,
) -> None:
    """Exposes numeric component entries as additional flat variables."""
    for component_key, value in _record(components).items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        flat_key = _slug_component_key(component_key)
        if not flat_key:
            continue
        variables[f"{prefix}_{flat_key}"] = _numeric(value)


def _ranked_items(values: dict) -> list[tuple[str, float]]:
    """
    Returns descending (key, score) pairs while preserving source order on ties.
    """
    ordered = list(_record(values).items())
    return sorted(
        (
            (str(key), _numeric(value))
            for key, value in ordered
            if not isinstance(value, bool) and isinstance(value, (int, float))
        ),
        key=lambda item: item[1],
        reverse=True,
    )


def _store_index_variables(
    variables: dict,
    prefix: str,
    index_record: dict,
) -> None:
    """
    Exposes the shared EAS result shape as flat, template-ready variables.

    Example for prefix 'rwi':
        rwi_score
        rwi_archetype
        rwi_expression
        rwi_activation
        rwi_driver_body
        rwi_driver_modality
    """
    result = _record(index_record)

    variables[f"{prefix}_score"] = _numeric(result.get("score", 0.0))
    variables[f"{prefix}_raw_score"] = _numeric(result.get("raw_score", 0.0))
    variables[f"{prefix}_activation_score"] = _numeric(
        result.get("activation_score", 0.0)
    )
    variables[f"{prefix}_tier"] = result.get("tier", "SUBTLE")
    variables[f"{prefix}_archetype"] = result.get("archetype", "")
    variables[f"{prefix}_expression"] = result.get("expression", "")
    variables[f"{prefix}_activation"] = result.get("activation", "")
    variables[f"{prefix}_driver_body"] = result.get("driver_body", "")
    variables[f"{prefix}_driver_modality"] = result.get("driver_modality", "unknown")
    variables[f"{prefix}_suppressed"] = bool(result.get("suppressed", False))
    variables[f"{prefix}_subtle_signal"] = bool(result.get("subtle_signal", False))
    variables[f"{prefix}_display_full"] = bool(result.get("display_full", False))
    variables[f"{prefix}_components"] = _record(result.get("components"))
    _flatten_numeric_components(
        variables,
        prefix,
        variables[f"{prefix}_components"],
    )


def resolve_all(
    payload: dict,
    index_results: dict,
    querent_name: str = "",
    current_location: str = "",
    report_start_date: datetime | None = None,
    report_end_date: datetime | None = None,
    standard_report_bundle: dict | None = None,
) -> dict:
    """
    Master resolver for every currently supported Entangled Oracle report.

    Returns a flat dictionary suitable for Jinja2 template rendering.
    """
    now = datetime.now(timezone.utc)

    if report_start_date is None:
        report_start_date = now
    elif report_start_date.tzinfo is None:
        # Guard: ensure any naive datetime reaching here is treated as UTC
        report_start_date = report_start_date.replace(tzinfo=timezone.utc)

    variables = {}
    user_profile = _record(payload.get("user_profile"))
    methodology = _record(user_profile.get("methodology"))

    # ── Metadata ───────────────────────────────────────────────

    variables["querent_name"] = querent_name
    variables["generation_date"] = now.strftime("%B %d, %Y")
    variables["generation_location"] = current_location
    variables["display_date"] = report_start_date.strftime("%B %d, %Y")
    variables["report_start_date"] = report_start_date.strftime("%B %d, %Y")
    variables["report_end_date"] = (
        report_end_date.strftime("%B %d, %Y")
        if report_end_date
        else ""
    )
    variables["house_system"] = user_profile.get("house_system", "")
    variables["zodiac"] = (
        methodology.get("zodiac")
        or user_profile.get("zodiac", "")
    )
    variables["methodology_id"] = (
        methodology.get("id")
        or user_profile.get("methodology_id", "")
    )
    variables["methodology_label"] = (
        methodology.get("label")
        or user_profile.get("methodology_label", "")
    )
    variables["birth_time_state"] = user_profile.get("birth_time_state", "")

    # ── Standard Bodies ────────────────────────────────────────
    #
    # Include nodes and BML here as well, so future templates can use them
    # without requiring another resolver change.

    standard_planets = _record(payload.get("standard_planets"))

    standard_body_names = [
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
        "North_Node",
        "South_Node",
        "Lilith_BML",
    ]

    for body_name in standard_body_names:
        data = _record(standard_planets.get(body_name))
        key = body_name.lower()

        variables[f"{key}_sign"] = data.get("sign", "")
        variables[f"{key}_house"] = data.get("house", 0)
        variables[f"{key}_degree"] = data.get("degree_decimal", 0.0)
        variables[f"{key}_retrograde"] = bool(data.get("retrograde", False))
        variables[f"{key}_sign_element"] = get_sign_element(
            data.get("sign", "")
        )
        variables[f"{key}_sign_modality"] = get_sign_modality(
            data.get("sign", "")
        )

    # ── Angles ─────────────────────────────────────────────────

    angles = _record(payload.get("angles"))

    angle_key_map = {
        "Ascendant": "ascendant",
        "Midheaven": "midheaven",
        "Descendant": "descendant",
        "Imum_Coeli": "ic",
        "Vertex": "vertex",
    }

    for angle_name, variable_prefix in angle_key_map.items():
        angle = _record(angles.get(angle_name))
        sign = angle.get("sign", "")

        variables[f"{variable_prefix}_sign"] = sign
        variables[f"{variable_prefix}_degree"] = angle.get(
            "degree_decimal",
            0.0,
        )
        variables[f"{variable_prefix}_longitude"] = angle.get(
            "longitude",
            0.0,
        )
        variables[f"{variable_prefix}_element"] = get_sign_element(sign)
        variables[f"{variable_prefix}_modality"] = get_sign_modality(sign)

    # Existing report compatibility aliases.
    variables["mc_sign"] = variables["midheaven_sign"]
    variables["mc_element"] = variables["midheaven_element"]
    variables["mc_modality"] = variables["midheaven_modality"]

    # ── Derived Natal Variables ─────────────────────────────────

    variables["dominant_element"] = get_dominant_element(payload)
    variables["sun_moon_relationship"] = get_sun_moon_relationship(payload)
    variables["sun_moon_aspect_character"] = (
        variables["sun_moon_relationship"]
    )

    # ── Nodes ──────────────────────────────────────────────────
    #
    # These aliases keep the prior report builders unchanged.

    variables["north_node_sign"] = variables["north_node_sign"]
    variables["north_node_house"] = variables["north_node_house"]
    variables["north_node_element"] = variables["north_node_sign_element"]

    variables["south_node_sign"] = variables["south_node_sign"]
    variables["south_node_house"] = variables["south_node_house"]

    # ── House Themes ───────────────────────────────────────────

    for house_number in range(1, 13):
        variables[f"house_{house_number}_domain"] = get_house_domain(
            house_number
        )
        variables[f"house_{house_number}_theme"] = get_house_theme(
            house_number
        )

    variables["saturn_house_theme"] = get_house_theme(
        variables.get("saturn_house", 0)
    )
    variables["jupiter_house_theme"] = get_house_theme(
        variables.get("jupiter_house", 0)
    )

    # ── Day Ruler ──────────────────────────────────────────────

    variables["day_ruler_name"] = get_day_ruler(report_start_date)

    # ── Formula / EAS Variables ────────────────────────────────

    index_results = _record(index_results)

    # Legacy mapping remains available because the current Asteroid Portrait
    # template and blocks still use MAGNETIC.
    all_dimension_names = dict(INDEX_DIMENSION_NAMES)
    all_dimension_names.update(EAS_DIMENSION_NAMES)

    variables["dimension_names"] = all_dimension_names

    # Core EAS indexes.
    for index_key in ["KVQ", "MKI", "RWI", "DFIS", "CATALYST", "NGE"]:
        _store_index_variables(
            variables,
            index_key.lower(),
            index_results.get(index_key),
        )

    # KVQ extra field: easy Kassandra–Mercury contact signals a clear communication day.
    variables["kvq_clear_translator"] = bool(
        _record(index_results.get("KVQ")).get("clear_translator", False)
    )
    variables["kvq_clear_translator_strength"] = _numeric(
        variables.get("kvq_kass_merc_easy", 0.0)
    )

    # NGE-specific fields.
    nge = _record(index_results.get("NGE"))
    variables["nge_genre"] = nge.get("genre", "")
    variables["nge_dominant_body"] = nge.get("dominant_body", "")
    variables["nge_dominant_facet"] = nge.get("dominant_facet", "")
    variables["nge_narrative_question"] = nge.get(
        "narrative_question",
        "",
    )
    variables["nge_facets"] = _record(nge.get("facets"))
    variables["nge_apollo_weight"] = _numeric(variables.get("nge_apollo", 0.0))
    variables["nge_themis_weight"] = _numeric(variables.get("nge_themis", 0.0))
    variables["nge_terpsichore_weight"] = _numeric(
        variables.get("nge_terpsichore", 0.0)
    )
    variables["nge_sirene_weight"] = _numeric(variables.get("nge_sirene", 0.0))
    variables["nge_aphrodite_weight"] = _numeric(
        variables.get("nge_aphrodite", 0.0)
    )

    ranked_nge_bodies = _ranked_items(_record(nge.get("components")))

    # Ties follow the original formula-emission order because Python's sort is
    # stable and the source component dictionary is insertion ordered.
    secondary_body_key = ranked_nge_bodies[1][0] if len(ranked_nge_bodies) > 1 else ""
    secondary_facet = ""
    if secondary_body_key:
        secondary_facets = _ranked_items(
            _record(variables["nge_facets"]).get(secondary_body_key.title())
        )
        secondary_facet = secondary_facets[0][0] if secondary_facets else ""

    variables["nge_secondary_body"] = secondary_body_key.title() if secondary_body_key else ""
    variables["nge_secondary_facet"] = secondary_facet

    # AHL is an ancillary signal, not one of the six EAS primary dimensions.
    ahl = _record(index_results.get("AHL"))
    variables["ahl_score"] = _numeric(ahl.get("score", 0.0))
    variables["ahl_normalized_score"] = _numeric(ahl.get("normalized_score", 0.0))
    variables["ahl_raw_score"] = _numeric(ahl.get("raw_score", 0.0))
    variables["ahl_activation_score"] = _numeric(ahl.get("activation_score", 0.0))
    variables["ahl_tier"] = ahl.get("tier", "BELOW_THRESHOLD")
    variables["ahl_fires"] = bool(ahl.get("fires", False))
    variables["ahl_suppressed"] = bool(ahl.get("suppressed", False))
    variables["ahl_subtle_signal"] = bool(ahl.get("subtle_signal", False))
    variables["ahl_display_full"] = bool(ahl.get("display_full", False))
    variables["ahl_components"] = _record(ahl.get("components"))
    _flatten_numeric_components(variables, "ahl", variables["ahl_components"])
    variables["dfis_lilith_source"] = _record(index_results.get("DFIS")).get(
        "lilith_source",
        "",
    )

    from formulas.proprietary_indexes import get_eas_dimension_order

    eas_dimension_order = get_eas_dimension_order(index_results)

    variables["eas_dimension_order"] = eas_dimension_order
    variables["dominant_eas_dimension"] = (
        eas_dimension_order[0] if eas_dimension_order else ""
    )
    variables["dominant_eas_dimension_name"] = all_dimension_names.get(
        variables["dominant_eas_dimension"],
        "",
    )

    secondary_eas_dimension = eas_dimension_order[1] if len(eas_dimension_order) > 1 else ""
    tertiary_eas_dimension = eas_dimension_order[2] if len(eas_dimension_order) > 2 else ""
    secondary_record = _record(index_results.get(secondary_eas_dimension))
    tertiary_record = _record(index_results.get(tertiary_eas_dimension))

    variables["secondary_eas_dimension"] = secondary_eas_dimension
    variables["secondary_eas_dimension_name"] = all_dimension_names.get(
        secondary_eas_dimension,
        "",
    )
    variables["secondary_eas_dimension_score"] = _numeric(
        secondary_record.get("score", 0.0)
    )
    variables["secondary_eas_dimension_archetype"] = secondary_record.get(
        "archetype",
        "",
    )
    variables["secondary_eas_dimension_expression"] = secondary_record.get(
        "expression",
        "",
    )

    variables["tertiary_eas_dimension"] = tertiary_eas_dimension
    variables["tertiary_eas_dimension_name"] = all_dimension_names.get(
        tertiary_eas_dimension,
        "",
    )
    variables["tertiary_eas_dimension_score"] = _numeric(
        tertiary_record.get("score", 0.0)
    )
    variables["tertiary_eas_dimension_archetype"] = tertiary_record.get(
        "archetype",
        "",
    )
    variables["tertiary_eas_dimension_expression"] = tertiary_record.get(
        "expression",
        "",
    )

    # Soul Ecosystem dominant index — whichever of the 6 active EAS indexes
    # scored highest overall. Used by _build_soul_ecosystem_context to route
    # the proprietary section block.
    variables["soul_ecosystem_dominant_index"] = variables["dominant_eas_dimension"] or "MKI"

    # ── Standard Result Bundle ──────────────────────────────────

    bundle = _record(standard_report_bundle)
    standard_result_bundle = _record(bundle.get("standard_result_bundle"))
    variables["standard_report_bundle"] = bundle
    variables["standard_result_bundle"] = standard_result_bundle
    variables["standard_report_profile"] = bundle.get("report_profile", "")
    variables["standard_bundle_available"] = bool(standard_result_bundle)

    chart_ruler_bundle = _record(standard_result_bundle.get("chart_ruler"))
    chart_ruler_data = _record(chart_ruler_bundle.get("traceable_source_data"))
    chart_ruler_body = ""
    chart_ruler_condition_label = ""
    chart_ruler_prominence_tier = ""
    if (
        chart_ruler_bundle.get("routing_state") != "suppressed"
        and chart_ruler_data.get("status") == "success"
    ):
        chart_ruler_body = chart_ruler_data.get("primary_ruler", "")
        chart_ruler_condition_label = (
            _record(_record(chart_ruler_data.get("condition_record")).get("dignity")).get("classification", "")
        )

    prominence_bundle = _record(standard_result_bundle.get("planetary_prominence"))
    prominence_data = _record(prominence_bundle.get("traceable_source_data"))
    prominence_rankings = (
        prominence_data.get("rankings", [])
        if isinstance(prominence_data.get("rankings"), list)
        else []
    )
    for item in prominence_rankings:
        if isinstance(item, dict) and item.get("body") == chart_ruler_body:
            chart_ruler_prominence_tier = item.get("tier", "")
            break

    variables["chart_ruler_body"] = chart_ruler_body
    variables["chart_ruler_condition_label"] = chart_ruler_condition_label
    variables["chart_ruler_prominence_tier"] = chart_ruler_prominence_tier
    variables["planet_prominence_top_bodies"] = [
        item.get("body", "")
        for item in prominence_rankings[:3]
        if isinstance(item, dict) and item.get("body")
    ]

    house_bundle = _record(standard_result_bundle.get("house_emphasis"))
    house_data = _record(house_bundle.get("traceable_source_data"))
    house_rankings = (
        house_data.get("rankings", [])
        if isinstance(house_data.get("rankings"), list)
        else []
    )
    variables["house_emphasis_top_domains"] = [
        str(item.get("sign") or f"House {item.get('house')}")
        for item in house_rankings[:3]
        if isinstance(item, dict)
    ]

    convergence_bundle = _record(standard_result_bundle.get("natal_convergence"))
    convergence_data = _record(convergence_bundle.get("traceable_source_data"))
    central_domains = (
        convergence_data.get("central_life_domains", [])
        if isinstance(convergence_data.get("central_life_domains"), list)
        else []
    )
    primary_theme = ""
    if central_domains and isinstance(central_domains[0], dict):
        primary_theme = central_domains[0].get("label", "")
    variables["natal_convergence_primary_theme"] = primary_theme

    forecast_bundle = _record(standard_result_bundle.get("forecast_natal_priority"))
    forecast_data = _record(forecast_bundle.get("traceable_source_data"))
    top_targets = _record(forecast_data.get("top_target_weights"))
    variables["forecast_priority_chart_ruler_active"] = bool(
        chart_ruler_body and chart_ruler_body in top_targets
    )
    variables["forecast_priority_luminary_active"] = bool(
        "Sun" in top_targets or "Moon" in top_targets
    )

    # ── Horoscope Sky Variables ────────────────────────────────────
    #
    # simple_mode is stored at the top level of the natal payload.
    variables["simple_mode"] = bool(
        user_profile.get("simple_mode", payload.get("simple_mode", False))
    )

    # moon_phase_descriptor, activation_planet, activation_house_number, and
    # natal_house_name all require today's live planetary positions via Swiss
    # Ephemeris. swisseph is an optional dependency — fall back to empty values
    # gracefully so non-horoscope reports are unaffected.
    try:
        import swisseph as _swe
        from datetime import timezone as _tz, timedelta as _timedelta
        from engine.transit_engine import (
            ZODIAC_SIGNS,
            _whole_sign_house,
            compute_daily_activation_transits,
            scan_stations,
        )

        if report_start_date.tzinfo is None:
            _now_utc = report_start_date.replace(tzinfo=_tz.utc)
        else:
            _now_utc = report_start_date.astimezone(_tz.utc)
        _jd = _swe.julday(
            _now_utc.year,
            _now_utc.month,
            _now_utc.day,
            _now_utc.hour + _now_utc.minute / 60.0 + _now_utc.second / 3600.0,
        )

        # Moon phase — Sun-Moon angular distance mapped to 8 named phases.
        _sun_lon  = _swe.calc_ut(_jd, _swe.SUN)[0][0]
        _moon_lon = _swe.calc_ut(_jd, _swe.MOON)[0][0]
        _phase_angle = (_moon_lon - _sun_lon) % 360
        _moon_sign = ZODIAC_SIGNS[int(_moon_lon // 30) % 12]

        _PHASE_NAMES = [
            (45,  "New Moon"),
            (90,  "Waxing Crescent"),
            (135, "First Quarter"),
            (180, "Waxing Gibbous"),
            (225, "Full Moon"),
            (270, "Waning Gibbous"),
            (315, "Last Quarter"),
            (360, "Balsamic"),
        ]
        variables["moon_phase_descriptor"] = next(
            name for threshold, name in _PHASE_NAMES if _phase_angle < threshold
        )
        variables["sky_moon_sign"] = _moon_sign
        variables["sky_moon_sign_element"] = get_sign_element(_moon_sign)

        _asc_lon = variables.get("ascendant_longitude", 0.0)

        # ── Today's Activation — priority chain ──────────────────────
        #
        # 1. A planet stationing (retrograde/direct) today outranks
        #    everything else — stations are rare, specifically-dated
        #    events, not a background condition.
        # 2. Failing that, the highest-scoring same-day transit-to-natal
        #    contact across every planet but the Moon
        #    (compute_daily_activation_transits — its own tight, speed-
        #    graduated orbs, sized for "true today" rather than reusing
        #    Year Ahead's week/month-scale orbs; see that function's
        #    docstring for why the naive version of this failed an
        #    empirical sweep).
        # 3. Failing that, fall back to the Moon's current Whole Sign
        #    house — the steady daily baseline that's always available,
        #    since the Moon changes house every ~2.5 days.
        #
        # House number always uses _whole_sign_house() (sign-based), the
        # same formula the rest of the engine uses for Whole Sign houses
        # elsewhere (ingresses, eclipses). The house number previously
        # computed here used a degree-offset-from-Ascendant formula, which
        # is Equal House, not Whole Sign, and gave a different (incorrect)
        # answer whenever the Ascendant wasn't near 0 degrees of its sign.
        _BODY_IDS = {
            "Sun": _swe.SUN, "Moon": _swe.MOON, "Mercury": _swe.MERCURY,
            "Venus": _swe.VENUS, "Mars": _swe.MARS, "Jupiter": _swe.JUPITER,
            "Saturn": _swe.SATURN, "Uranus": _swe.URANUS,
            "Neptune": _swe.NEPTUNE, "Pluto": _swe.PLUTO,
        }

        def _live_longitude(planet_name):
            return _swe.calc_ut(_jd, _BODY_IDS[planet_name])[0][0]

        _winner_planet = "Moon"
        _winner_longitude = _moon_lon
        _activation_source = "moon_house_fallback"
        _activation_basis_line = (
            "No rarer station or tighter same-day natal contact outranked the baseline sky; "
            "today's activation is localized through the Moon's current Whole Sign house."
        )

        try:
            _today_start = _now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
            _today_end = _today_start + _timedelta(days=1)
            _stations_today = scan_stations(payload, _today_start, _today_end)
        except Exception:
            _stations_today = []

        if _stations_today:
            _stations_today.sort(key=lambda e: e["score"], reverse=True)
            _winner_planet = _stations_today[0]["transit_planet"]
            _winner_longitude = _live_longitude(_winner_planet)
            _activation_source = "planetary_station"
            _station_type = _stations_today[0].get("station_type", "station")
            _activation_basis_line = (
                f"{_winner_planet} stations {_station_type} today, so it outranks ordinary "
                "same-day contact and becomes the localized activation."
            )
        else:
            try:
                _candidates = compute_daily_activation_transits(payload, _now_utc)
            except Exception:
                _candidates = []

            if _candidates:
                _candidates.sort(key=lambda e: e["score"], reverse=True)
                _selected_activation = _candidates[0]
                _winner_planet = _selected_activation["transit_planet"]
                _winner_longitude = _live_longitude(_winner_planet)
                _activation_source = "same_day_natal_contact"
                _activation_basis_line = (
                    f"{_winner_planet} makes the strongest retained same-day natal contact "
                    f"({ _selected_activation.get('aspect', 'aspect').lower() } "
                    f"{ _selected_activation.get('natal_target_display') or _selected_activation.get('natal_target', 'your chart') }), "
                    "using tight daily orbs rather than broad year-ahead windows."
                )

        _activation_house = _whole_sign_house(_winner_longitude, _asc_lon)

        variables["activation_planet"]       = _winner_planet
        variables["activation_house_number"] = _activation_house
        variables["natal_house_name"]        = get_house_domain(_activation_house)
        variables["activation_source"]       = _activation_source
        variables["activation_basis_line"]   = _activation_basis_line

    except Exception:
        variables["moon_phase_descriptor"]   = ""
        variables["sky_moon_sign"]           = ""
        variables["sky_moon_sign_element"]   = "unknown"
        variables["activation_planet"]       = ""
        variables["activation_house_number"] = 0
        variables["natal_house_name"]        = ""
        variables["activation_source"]       = ""
        variables["activation_basis_line"]   = ""

    # secondary_activation_line is authored content; nothing generates it yet.
    variables["secondary_activation_line"] = ""

    # ── Planets in the Twelfth House ────────────────────────────

    planets_in_12th = []

    for planet_name, planet_data in standard_planets.items():
        data = _record(planet_data)

        if data.get("house") == 12:
            planets_in_12th.append(planet_name)

    variables["planets_in_12th"] = planets_in_12th
    variables["has_12th_house_planets"] = bool(planets_in_12th)

    return variables
