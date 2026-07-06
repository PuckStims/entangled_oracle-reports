#!/usr/bin/env python3
"""
generate.py — Entangled Oracle Report Generator
Main entry point. Run from the command line.

Usage:
    python generate.py horoscope --name "Puck" --date 1992-03-21 --time 08:11 --location "Peoria, IL"
    python generate.py year_ahead --name "Puck" --date 1992-03-21 --time 08:11 --location "Peoria, IL"
    python generate.py soul_journey --name "Puck" --date 1992-03-21 --time 08:11 --location "Peoria, IL"
    python generate.py asteroid_portrait --name "Puck" --date 1992-03-21 --time 08:11 --location "Peoria, IL"
    python generate.py identity_profile --name "Puck" --date 1992-03-21 --time 08:11 --location "Peoria, IL"

DOB-only mode (simple horoscope, no birth time needed):
    python generate.py horoscope --name "Visitor" --date 1990-06-15 --simple
"""
import argparse
import os
import sys
import json
import re
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))
from config import OUTPUT_DIR, TEMPLATES_DIR

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    print("Warning: jinja2 not installed. Run: pip install jinja2")


# ── Input Parsing ──────────────────────────────────────────────

def parse_birth_data(args) -> dict:
    """Parses CLI arguments into a birth data dict."""
    birth_data = {
        "name": args.name,
        "date": args.date,
        "location": args.location or "Unknown location",
        "simple_mode": getattr(args, "simple", False)
    }
    if hasattr(args, "time") and args.time and not birth_data["simple_mode"]:
        birth_data["time"] = args.time
    else:
        birth_data["time"] = None
        birth_data["simple_mode"] = True
    return birth_data


# ── Engine Integration ─────────────────────────────────────────

def get_payload(birth_data: dict) -> dict:
    """Builds the normalized natal-chart payload through the live natal engine."""
    from engine.natal_engine import generate_payload
    return generate_payload(birth_data)


# ── Report Generators ──────────────────────────────────────────

def _add_one_year(start: datetime) -> datetime:
    """Returns the same calendar date one year later, with leap-day safety."""
    try:
        return start.replace(year=start.year + 1)
    except ValueError:
        return start.replace(year=start.year + 1, month=2, day=28)


def generate_report(
    report_type: str,
    birth_data: dict,
    output_filename: str | None = None,
    content_pack: str = "plainspeak",
) -> str:
    """
    Master report generator.
    Returns the path to the generated HTML file.
    """
    from formulas.proprietary_indexes import compute_all_indexes
    from selectors.variable_resolver import resolve_all

    payload = get_payload(birth_data)

    print("[Formulas] Computing indexes...")
    index_results = compute_all_indexes(payload)

    report_start = datetime.now(timezone.utc)
    report_end = _add_one_year(report_start)

    print("[Variables] Resolving...")
    variables = resolve_all(
        payload=payload,
        index_results=index_results,
        querent_name=birth_data["name"],
        current_location=birth_data.get("current_location") or birth_data["location"],
        report_start_date=report_start,
        report_end_date=report_end,
    )

    print("[Blocks] Selecting...")
    context = build_report_context(
        report_type,
        variables,
        index_results,
        payload,
        report_start=report_start,
        report_end=report_end,
        content_pack=content_pack,
    )

    print("[Render] Building HTML...")
    html = render_template(report_type, context)

    if output_filename is None:
        safe_name = birth_data["name"].replace(" ", "_").lower()
        timestamp = report_start.strftime("%Y%m%d_%H%M")
        output_filename = f"{safe_name}_{report_type}_{timestamp}.html"

    output_path = os.path.join(OUTPUT_DIR, output_filename)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write(html)

    print(f"[Done] Report saved: {output_path}")
    return output_path


def build_report_context(
    report_type: str,
    variables: dict,
    index_results: dict,
    payload: dict,
    report_start: datetime | None = None,
    report_end: datetime | None = None,
    content_pack: str = "plainspeak",
) -> dict:
    """
    Builds the full template context dict for a given report type.
    Selects all paragraph blocks and merges them with variable data.

    Each report type has its own block selection logic defined here.
    """
    from selectors.block_selector import select_block, select_tier_block

    ctx = dict(variables)  # start with all resolved variables

    if report_type == "horoscope":
        ctx.update(_build_horoscope_context(variables, index_results, payload))

    elif report_type == "year_ahead":
        ctx.update(_build_year_ahead_context(variables, index_results, payload, report_start, report_end, content_pack))

    elif report_type == "soul_journey":
        ctx.update(_build_soul_journey_context(variables, index_results, payload))

    elif report_type == "asteroid_portrait":
        ctx.update(_build_asteroid_portrait_context(variables, index_results, payload))

    elif report_type == "identity_profile":
        from products.identity_profile.runtime.identity_profile_context import build_identity_profile_context
        ctx.update(build_identity_profile_context(variables, index_results, payload))

    return ctx


def _build_horoscope_context(variables, index_results, payload) -> dict:
    from selectors.block_selector import select_block
    v = variables
    ctx = {}

    # Today's Sky block
    ctx["todays_sky_block"] = select_block(
        "daily_horoscope", "todays_sky",
        _moon_phase_key(v.get("moon_phase_descriptor", "")),
        v.get("moon_sign_element", "fallback")
    )

    # Your Activation block
    ctx["activation_block"] = select_block(
        "daily_horoscope", "your_activation",
        v.get("activation_planet", "fallback"),
        str(v.get("activation_house_number", "fallback"))
    )

    # Day Ruler block
    ctx["day_ruler_block"] = select_block(
        "daily_horoscope", "day_ruler",
        v.get("day_ruler_name", "fallback")
    )

    # Proprietary Reference block
    dominant_idx = v.get("dominant_dimension", "fallback")
    ctx["proprietary_block"] = select_block(
        "daily_horoscope", "proprietary_reference",
        dominant_idx, "dominant"
    )
    ctx["activated_index_name"] = v.get("dimension_names", {}).get(dominant_idx, "")

    # Closing Line
    ctx["closing_block"] = select_block(
        "daily_horoscope", "closing_line",
        _moon_phase_key(v.get("moon_phase_descriptor", ""))
    )

    return ctx


def _build_soul_journey_context(variables, index_results, payload) -> dict:
    from selectors.block_selector import select_block, select_tier_block
    v = variables
    ctx = {}

    ctx["souls_story_block"] = select_block(
        "soul_journey", "souls_story",
        v.get("sun_moon_relationship", "unaspected"),
        v.get("dominant_element", "fallback")
    )
    ctx["south_node_sign_block"] = select_block(
        "soul_journey", "south_node_sign", v.get("south_node_sign", "fallback")
    )
    ctx["south_node_house_block"] = select_block(
        "soul_journey", "south_node_house", str(v.get("south_node_house", "fallback"))
    )
    ctx["saturn_block"] = select_block(
        "soul_journey", "saturn_sign", v.get("saturn_sign", "fallback")
    )
    ctx["pluto_generation_block"] = select_block(
        "soul_journey", "pluto_generation", v.get("pluto_sign", "fallback")
    )
    # 12th house (conditional)
    ctx["twelfth_house_blocks"] = []
    for planet in v.get("planets_in_12th", [])[:2]:
        block = select_block("soul_journey", "twelfth_house_planets", planet)
        ctx["twelfth_house_blocks"].append({"planet": planet, "block": block})

    # Ancestral layer (conditional)
    ahl = index_results.get("AHL", {})
    if ahl.get("fires"):
        ctx["ancestral_block"] = select_block(
            "soul_journey", "ancestral_layer", ahl.get("tier", "PRESENT")
        )
    else:
        ctx["ancestral_block"] = None

    ctx["north_node_sign_block"] = select_block(
        "soul_journey", "north_node_sign", v.get("north_node_sign", "fallback")
    )
    ctx["north_node_house_block"] = select_block(
        "soul_journey", "north_node_house", str(v.get("north_node_house", "fallback"))
    )
    ctx["midheaven_block"] = select_block(
        "soul_journey", "midheaven", v.get("mc_sign", "fallback")
    )
    ctx["jupiter_block"] = select_block(
        "soul_journey", "jupiter_sign", v.get("jupiter_sign", "fallback")
    )
    ctx["sun_moon_integration_block"] = select_block(
        "soul_journey", "sun_moon_integration",
        v.get("sun_sign_element", "fallback"),
        v.get("moon_sign_element", "fallback"),
        v.get("sun_moon_aspect_character", "unaspected")
    )
    ctx["chiron_block"] = select_block(
        "soul_journey", "chiron_house", str(v.get("chiron_house", "fallback"))
    )

    # Proprietary index (whichever scores highest)
    soul_idx = v.get("soul_journey_dominant_index", "MKI")
    if soul_idx == "MKI":
        ctx["proprietary_section_title"] = "Your Knowledge Legacy"
        ctx["proprietary_section_block"] = select_block(
            "soul_journey", "knowledge_legacy",
            index_results["MKI"]["archetype"].lower().replace(" ","_").replace("/","_")
        )
    else:
        ctx["proprietary_section_title"] = "Your Impact Pattern" if soul_idx == "CATALYST" \
                                            else "Your Foresight Pattern"
        ctx["proprietary_section_block"] = select_block(
            "soul_journey", "impact_pattern",
            soul_idx,
            index_results[soul_idx]["archetype"].lower().replace(" ","_").replace("/","_")
        )

    # Archetypes
    ctx["primary_archetype_name"]  = f"The {v.get('mc_sign','')} Archetype"
    ctx["secondary_archetype_name"] = f"The {v.get('north_node_sign','')} Archetype"
    ctx["primary_archetype_block"] = select_block(
        "soul_journey", "archetypal_support", "primary", v.get("mc_sign","fallback")
    )
    ctx["secondary_archetype_block"] = select_block(
        "soul_journey", "archetypal_support", "secondary", v.get("north_node_sign","fallback")
    )

    # Soul's Promise
    ctx["souls_promise_block"] = select_block(
        "soul_journey", "souls_promise",
        v.get("north_node_element", "fallback"),
        v.get("mc_element", "fallback")
    )

    return ctx


def _build_asteroid_portrait_context(variables, index_results, payload) -> dict:

    from selectors.block_selector import select_block, select_tier_block

    from formulas.proprietary_indexes import get_dimension_order

    from config import INDEX_DIMENSION_NAMES

    v = variables

    for k, v in index_results.items():
        print(f"[Debug] {k}: {v}")

    dim_order = get_dimension_order(index_results)

    dominant  = dim_order[0] if dim_order else "KVQ"

    # FIX 2: pull aspect_character from formula results instead of hardcoding

    aspect_character = index_results.get(dominant, {}).get("aspect_character", "harmonious")

    ctx = {

        "portrait_overview_block": select_block(

            "asteroid_portrait", "portrait_overview", dominant

        ),

        "dimension_order":    dim_order,

        "dimension_sections": [],

        "portrait_synthesis_block": select_block(

            "asteroid_portrait", "portrait_synthesis", dominant, aspect_character

        )

    }

    file_map = {

        "KVQ":      "foresight_pattern",

        "MKI":      "knowledge_legacy",

        "RWI":      "reality_field",

        "DFIS":     "power_current",

        "MAGNETIC": "magnetic_frequency",

        "CATALYST": "impact_radius",

        "AHL":      "ancestral_thread"

    }

    for i, dim_key in enumerate(dim_order):

        idx = index_results.get(dim_key, {})

        block_file = file_map.get(dim_key, dim_key.lower())

        archetype = idx.get("archetype", "")

        activation_score = idx.get("activation_score", 0)

        if i == 0 and activation_score >= 6.5:

            display_tier = "DOMINANT"

        elif activation_score >= 3.5:

            display_tier = "PRESENT"

        else:

            display_tier = "SUBTLE"

        # AHL uses its own DEEP/PRESENT content tier — keep that separate

        if dim_key == "AHL":

            ahl_content_tier = idx.get("tier", "PRESENT")

            block = select_block("asteroid_portrait", "ancestral_thread", ahl_content_tier)

        else:

            block = select_tier_block("asteroid_portrait", block_file, archetype, display_tier)

        ctx["dimension_sections"].append({

            "key":       dim_key,

            "name":      INDEX_DIMENSION_NAMES.get(dim_key, dim_key),

            "archetype": archetype if display_tier == "DOMINANT" else "",

            "tier":      display_tier,

            "block":     block

        })

    return ctx



# ── Year Ahead Timeline Assembly ───────────────────────────────


def _usable_block(value: str) -> str:
    """
    Returns clean user-facing block text.

    The content library was authored partly from Markdown source material.
    This removes internal source headers and wrapper brackets while preserving
    actual report copy. TODO or unresolved block markers are suppressed.
    """
    if not isinstance(value, str):
        return ""

    cleaned = value.replace("\r\n", "\n").replace("\r", "\n").strip()

    if not cleaned or re.match(r"^\[\s*TODO\b", cleaned, flags=re.IGNORECASE):
        return ""

    # Some finished overview blocks were stored as [full paragraph].
    # Remove only a single outer wrapper pair after TODO handling.
    if cleaned.startswith("[") and cleaned.endswith("]"):
        cleaned = cleaned[1:-1].strip()

    # Source headings such as "### JUPITER TRANSITS: PLUTO" accidentally
    # travelled with a few JSON block values. They are authoring metadata,
    # not reader-facing copy, so strip them whether they appear on a line
    # of their own or appended to the end of a paragraph.
    cleaned = re.sub(
        r"\s*#{2,6}\s+[A-Z][A-Z0-9\s:–—\-()/]*?(?=\n|$)",
        "",
        cleaned,
    )

    # Do not surface unresolved TODO blocks anywhere in a report.
    if re.search(r"\[\s*TODO\b", cleaned, flags=re.IGNORECASE):
        return ""

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned

def _ordinal(number: int) -> str:
    """Formats 1 as 1st, 2 as 2nd, and so on."""
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def _position_display(data: dict) -> str:
    """Formats one natal position for the report's compact chart table."""
    sign = data.get("sign", "")
    degree = data.get("degree", 0)
    minute = data.get("minute", 0)

    if not sign:
        return "—"

    return f"{degree}°{int(minute):02d}' {sign}"


def _duration_descriptor(event: dict) -> str:
    """Creates a readable timing line for transit-window cards."""
    if event.get("event_type") != "transit":
        return ""

    peak = event.get("peak_date", "")
    duration = event.get("duration_days", 0.0)
    in_orb_at_start = (
        event.get("in_orb_at_forecast_start")
        or event.get("active_at_report_start")
    )
    continues_past_end = (
        event.get("continues_after_forecast_end")
        or event.get("active_at_report_end")
    )

    pieces = []

    if in_orb_at_start:
        pieces.append("Already active at the start of this forecast")
    elif event.get("entry_date"):
        pieces.append(f"Enters orb {event['entry_date']}")

    if peak:
        perfection_type = event.get("perfection_type", "closest_approach")
        if perfection_type == "exact":
            pieces.append(f"Exact: {peak}")
        else:
            pieces.append(f"Closest approach: {peak}")

    if continues_past_end:
        pieces.append("Continues beyond this report")
    elif event.get("leave_date"):
        pieces.append(f"Leaves orb {event['leave_date']}")

    if duration:
        pieces.append(f"{duration:.0f}-day window")

    return " · ".join(pieces)


def _add_months(moment: datetime, months: int) -> datetime:
    """Adds calendar months while preserving the day whenever possible."""
    import calendar

    month_index = (moment.month - 1) + months
    year = moment.year + (month_index // 12)
    month = (month_index % 12) + 1
    day = min(moment.day, calendar.monthrange(year, month)[1])

    return moment.replace(year=year, month=month, day=day)


def _interval_overlaps(
    entry: datetime | None,
    leave: datetime | None,
    period_start: datetime,
    period_end: datetime,
) -> bool:
    """Returns True when a dated event is active at any point in a forecast month."""
    if entry is None:
        return False

    event_end = leave or entry
    return entry < period_end and event_end >= period_start


def _intensity_label(score: float) -> tuple[str, str]:
    """Returns the display label and printable bar for an intensity score."""
    from config import INTENSITY_LEVELS

    for threshold, label, bar in INTENSITY_LEVELS:
        if score >= threshold:
            return label, bar

    return "Passing", "█"


def _select_year_block(event: dict, pack_paths: dict) -> str:
    """Selects the correct JSON paragraph block for one timeline event."""
    from selectors.block_selector import select_block_from_path

    event_type = event.get("event_type")

    if event_type == "transit":
        return _usable_block(
            select_block_from_path(
                pack_paths["transits"],
                event.get("transit_planet", "fallback"),
                event.get("aspect", "fallback"),
                event.get("natal_target", "fallback"),
            )
        )

    if event_type == "ingress":
        return _usable_block(
            select_block_from_path(
                pack_paths["ingresses"],
                event.get("transit_planet", "fallback"),
                str(event.get("house_number", "fallback")),
            )
        )

    if event_type == "eclipse":
        # eclipse_key controls which event field drives the JSON lookup:
        #   "natal_target_key"  → planet-order index (plainspeak: Sun=1 … Jupiter=6 …)
        #   "natal_house"       → Whole Sign house number (entangled_oracle: 1–12)
        eclipse_key_field = pack_paths.get("eclipse_key", "natal_target_key")
        if eclipse_key_field == "natal_house":
            house = event.get("natal_house") or event.get("whole_sign_house") or 0
            eclipse_key = str(house) if house else "fallback"
        else:
            eclipse_key = event.get("natal_target_key", "fallback")
        return _usable_block(
            select_block_from_path(
                pack_paths["eclipses"],
                event.get("eclipse_type", "fallback"),
                eclipse_key,
            )
        )

    if event_type == "station":
        return _usable_block(
            select_block_from_path(
                pack_paths["stations"],
                event.get("transit_planet", "fallback"),
                event.get("station_type", "fallback"),
            )
        )

    return ""


def _event_tone(event: dict) -> str:
    """Provides a stable visual tone class for every event type."""
    event_type = event.get("event_type")

    if event_type == "transit":
        return event.get("aspect_character", "neutral")

    if event_type == "eclipse":
        return "eclipse"

    if event_type == "station":
        return "flowing" if event.get("station_type") == "Direct" else "challenging"

    if event_type == "ingress":
        return "ingress"

    return "neutral"


def _format_timeline_event(event: dict, house_domains: dict, pack_paths: dict) -> dict:
    """Converts raw engine output into a self-contained template card."""
    event_type = event.get("event_type", "event")
    natal_house = int(event.get("natal_house") or 0)
    house_domain = house_domains.get(natal_house, "")

    result = dict(event)
    result["tone"] = _event_tone(event)
    result["block"] = _select_year_block(event, pack_paths)
    result["house_domain"] = house_domain
    result["duration_descriptor"] = _duration_descriptor(event)
    result["date_label"] = event.get("peak_date") or event.get("entry_date") or ""

    if event_type == "transit":
        result["event_label"] = "Natal Transit"
        result["title"] = (
            f"{event.get('transit_planet', '')} "
            f"{event.get('aspect', '')} "
            f"natal {event.get('natal_target', '')}"
        )
        result["subtitle"] = event.get("natal_target_display", "")

    elif event_type == "ingress":
        house_number = int(event.get("house_number") or 0)
        result["event_label"] = "Whole Sign Ingress"
        result["title"] = (
            f"{event.get('transit_planet', '')} enters your "
            f"{_ordinal(house_number)} house"
        )
        result["subtitle"] = house_domains.get(house_number, "")

    elif event_type == "eclipse":
        eclipse_type = event.get("eclipse_type", "")
        eclipse_sign = event.get("eclipse_sign", "")
        eclipse_degree = event.get("eclipse_degree", "")
        result["event_label"] = "Eclipse Contact"
        result["title"] = f"{eclipse_type} eclipse · {eclipse_degree}° {eclipse_sign}"
        result["subtitle"] = (
            f"Activates {event.get('natal_target_display', 'a natal point')}"
        )

    elif event_type == "station":
        planet = event.get("transit_planet", "")
        station_type = event.get("station_type", "")
        result["event_label"] = "Planetary Station"
        result["title"] = f"{planet} stations {station_type}"
        result["subtitle"] = event.get("natal_target_display", "")

    else:
        result["event_label"] = "Timing Event"
        result["title"] = event_type.replace("_", " ").title()
        result["subtitle"] = ""

    return result


def _filter_monthly_events(events: list[dict]) -> list[dict]:
    """
    Applies the published Year Ahead priority filter.

    Priority A entries are always retained. When a period becomes dense,
    only the two highest-intensity Priority B entries are added.
    """
    qualified = [
        event
        for event in events
        if (
            event.get("event_type") != "transit"
            or event.get("combined_intensity_score", 0.0) >= 0.20
        )
    ]

    if len(qualified) <= 6:
        return sorted(
            qualified,
            key=lambda event: (
                event.get("peak_datetime"),
                -event.get("combined_intensity_score", 0.0),
            ),
        )

    priority_a = [
        event for event in qualified
        if event.get("priority", "A") == "A"
    ]

    priority_b = sorted(
        [
            event for event in qualified
            if event.get("priority", "A") != "A"
        ],
        key=lambda event: event.get("combined_intensity_score", 0.0),
        reverse=True,
    )[:2]

    return sorted(
        priority_a + priority_b,
        key=lambda event: (
            event.get("peak_datetime"),
            -event.get("combined_intensity_score", 0.0),
        ),
    )


def _event_month_relevance(
    event: dict,
    period_start: datetime,
    period_end: datetime,
) -> float:
    """
    Scores how locally relevant an event is to one forecast month.

    A year-long transit should inform the background, but it should not win
    every monthly snapshot merely because it stays in orb. Exact peaks are
    therefore weighted most heavily; entries and exits matter next; a
    continuing-but-not-local transit remains a lighter background signal.
    """
    base_score = float(event.get("combined_intensity_score", 0.0))
    if base_score <= 0:
        return 0.0

    peak = event.get("peak_datetime")
    entry = event.get("entry_datetime")
    leave = event.get("leave_datetime")

    if peak is not None and period_start <= peak < period_end:
        timing_weight = 1.00
    elif entry is not None and period_start <= entry < period_end:
        timing_weight = 0.72
    elif leave is not None and period_start <= leave < period_end:
        timing_weight = 0.52
    else:
        # This preserves a quieter continuity signal for long windows without
        # allowing them to flatten every month into the same theme.
        timing_weight = 0.22

    return base_score * timing_weight


def _monthly_peak_score(
    active_events: list[dict],
    period_start: datetime,
    period_end: datetime,
) -> float:
    """Returns the strongest locally weighted intensity for one month."""
    return max(
        (
            _event_month_relevance(event, period_start, period_end)
            for event in active_events
        ),
        default=0.0,
    )


def _most_activated_domains(
    active_events: list[dict],
    house_domains: dict,
    period_start: datetime,
    period_end: datetime,
    top_n: int = 3,
) -> list[dict]:
    """
    Computes the most activated life areas for one forecast month.

    Scores use local timing relevance so a distant peak in a long-running
    transit does not repeat the same domains across the entire year.
    """
    scores: dict[str, float] = {}

    for event in active_events:
        house = event.get("natal_house")

        if not house and event.get("event_type") == "ingress":
            house = event.get("house_number")

        try:
            house = int(house or 0)
        except (TypeError, ValueError):
            house = 0

        domain = house_domains.get(house, "")
        if not domain:
            continue

        score = _event_month_relevance(event, period_start, period_end)
        if score <= 0:
            continue

        scores[domain] = scores.get(domain, 0.0) + score

    if not scores:
        return []

    peak_score = max(scores.values()) or 1.0
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_n]

    return [
        {
            "domain": domain,
            "score": round(score, 3),
            "bar": "█" * max(1, round((score / peak_score) * 12)),
        }
        for domain, score in ordered
    ]

def _snapshot_for_month(
    active_events: list[dict],
    period_start: datetime,
    period_end: datetime,
    pack_paths: dict,
) -> tuple[str, str, str]:
    """
    Returns the monthly snapshot block and its dominant planet/tone metadata.

    Long-running transits remain part of the context, but events peaking,
    entering, or resolving in the current month outrank background windows.
    """
    from selectors.block_selector import select_block_from_path

    snapshot_candidates = [
        event
        for event in active_events
        if (
            event.get("event_type") == "transit"
            and event.get("transit_planet")
            in {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Mars"}
        )
    ]

    if not snapshot_candidates:
        return "", "", ""

    dominant = max(
        snapshot_candidates,
        key=lambda event: (
            _event_month_relevance(event, period_start, period_end),
            event.get("combined_intensity_score", 0.0),
            -float(event.get("duration_days", 0.0)),
        ),
    )

    planet = dominant.get("transit_planet", "")
    character = dominant.get("aspect_character", "flowing")

    block = _usable_block(
        select_block_from_path(
            pack_paths["monthly_snapshots"],
            planet,
            character,
        )
    )

    return block, planet, character

def _build_natal_positions(payload: dict) -> list[dict]:
    """Creates compact natal-position rows for the Year Ahead audit table."""
    rows: list[dict] = []
    standard_planets = payload.get("standard_planets", {})

    for name in [
        "Sun", "Moon", "Mercury", "Venus", "Mars",
        "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    ]:
        data = standard_planets.get(name, {})

        if not isinstance(data, dict):
            continue

        house = data.get("house", 0)
        rows.append(
            {
                "name": name,
                "position": _position_display(data),
                "house": _ordinal(int(house)) if house else "—",
            }
        )

    angle_map = {
        "Ascendant": "Ascendant",
        "Midheaven": "Midheaven",
    }

    for label, payload_key in angle_map.items():
        data = payload.get("angles", {}).get(payload_key, {})

        if not isinstance(data, dict):
            continue

        rows.append(
            {
                "name": label,
                "position": _position_display(data),
                "house": "1st" if label == "Ascendant" else "10th",
            }
        )

    return rows


def _dominant_slow_theme(transit_events: list[dict]) -> tuple[dict | None, str, str]:
    """
    Selects a year-level slow-planet theme from the whole forecast.

    It aggregates the sustained influence of Jupiter through Pluto rather than
    relying on one arbitrary tie among saturated 1.0 event scores.
    """
    eligible = [
        event
        for event in transit_events
        if event.get("transit_planet") in {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}
    ]

    if not eligible:
        return None, "", "flowing"

    planet_scores: dict[str, float] = {}
    character_scores: dict[tuple[str, str], float] = {}

    for event in eligible:
        planet = event.get("transit_planet", "")
        character = event.get("aspect_character", "flowing")
        duration = max(0.0, float(event.get("duration_days", 0.0)))
        intensity = max(0.0, float(event.get("combined_intensity_score", 0.0)))

        # Duration is intentionally capped: a 365-day window matters more
        # than a six-week window, but cannot eclipse all other evidence alone.
        duration_weight = 0.70 + min(duration, 180.0) / 180.0
        contribution = intensity * duration_weight

        planet_scores[planet] = planet_scores.get(planet, 0.0) + contribution
        character_key = (planet, character)
        character_scores[character_key] = (
            character_scores.get(character_key, 0.0) + contribution
        )

    dominant_planet = max(planet_scores, key=planet_scores.get)
    dominant_character = max(
        (
            character
            for (planet, character) in character_scores
            if planet == dominant_planet
        ),
        key=lambda character: character_scores[(dominant_planet, character)],
    )

    representative = max(
        (
            event
            for event in eligible
            if event.get("transit_planet") == dominant_planet
            and event.get("aspect_character", "flowing") == dominant_character
        ),
        key=lambda event: (
            event.get("combined_intensity_score", 0.0),
            event.get("duration_days", 0.0),
        ),
    )

    return representative, dominant_planet, dominant_character


def _build_year_ahead_context(
    variables: dict,
    index_results: dict,
    payload: dict,
    report_start: datetime | None = None,
    report_end: datetime | None = None,
    content_pack: str = "plainspeak",
) -> dict:
    """
    Assembles the full 12-month Year Ahead report context.

    The transit engine calculates dates and intensity. This layer:
    - applies priority filtering
    - selects existing interpretation blocks
    - groups events into 12 chronological forecast periods
    - computes annual arc and domain summaries
    - prepares template-ready cards
    """
    from engine.transit_engine import compute_year_ahead_events
    from config import (
        CONTENT_PACKS,
        HOUSE_DOMAINS,
        LANDMARK_MAX_COUNT,
        LANDMARK_MIN_DAYS,
        LANDMARK_MIN_SCORE,
    )
    from selectors.block_selector import select_block_from_path
    pack = CONTENT_PACKS[content_pack]

    report_start = report_start or datetime.now(timezone.utc)
    report_end = report_end or _add_one_year(report_start)

    print("[Timeline] Scanning 12-month transit events...")
    timeline = compute_year_ahead_events(
        payload,
        start_date=report_start,
        end_date=report_end,
    )

    all_events = timeline.get("all_events", [])
    transit_events = timeline.get("transits", [])

    # A "landmark" is intentionally only a sustained, high-intensity natal transit.
    landmark_candidates = [
        event
        for event in transit_events
        if (
            event.get("transit_planet") != "Mars"
            and event.get("combined_intensity_score", 0.0) >= LANDMARK_MIN_SCORE
            and event.get("duration_days", 0.0) >= LANDMARK_MIN_DAYS
        )
    ]

    landmark_candidates.sort(
        key=lambda event: (
            event.get("combined_intensity_score", 0.0),
            event.get("duration_days", 0.0),
        ),
        reverse=True,
    )

    landmarks = [
        _format_timeline_event(event, HOUSE_DOMAINS, pack)
        for event in landmark_candidates[:LANDMARK_MAX_COUNT]
    ]

    # Build the annual orientation from the aggregated slow-planet pattern
    # rather than whichever individual event happens to win a score tie.
    dominant_event, dominant_planet, dominant_character = _dominant_slow_theme(
        transit_events
    )

    year_overview_block = ""
    year_integration_block = ""
    year_integration_theme = ""

    if dominant_event:
        year_overview_block = _usable_block(
            select_block_from_path(
                pack["year_overview"],
                dominant_planet,
                dominant_character,
            )
        )

        year_integration_theme = pack["integration_themes"].get(
            dominant_planet,
            "",
        )

        if year_integration_theme:
            year_integration_block = _usable_block(
                select_block_from_path(
                    pack["year_integration"],
                    year_integration_theme,
                    dominant_character,
                )
            )

    months: list[dict] = []

    for offset in range(12):
        period_start = _add_months(report_start, offset)
        period_end = min(_add_months(report_start, offset + 1), report_end)

        # The monthly chronology is organized by an event's exact/peak date,
        # not by the day a long transit first entered orb. That keeps December
        # events out of June's chapter while the overview still preserves the
        # long-running context.
        events_peaking = [
            event
            for event in all_events
            if (
                event.get("peak_datetime") is not None
                and period_start <= event["peak_datetime"] < period_end
            )
        ]

        events_active = [
            event
            for event in all_events
            if _interval_overlaps(
                event.get("entry_datetime"),
                event.get("leave_datetime"),
                period_start,
                period_end,
            )
        ]

        selected_events = _filter_monthly_events(events_peaking)
        formatted_events = [
            _format_timeline_event(event, HOUSE_DOMAINS, pack)
            for event in selected_events
        ]

        peak_score = _monthly_peak_score(
            events_active,
            period_start,
            period_end,
        )
        intensity_label, intensity_bar = _intensity_label(peak_score)
        snapshot_block, month_planet, month_character = _snapshot_for_month(
            events_active,
            period_start,
            period_end,
            pack,
        )

        months.append(
            {
                "id": f"month-{offset + 1}",
                "number": offset + 1,
                "name": period_start.strftime("%B %Y"),
                "short_name": period_start.strftime("%b"),
                "range": (
                    f"{period_start.strftime('%B %d, %Y')} – "
                    f"{(period_end - timedelta(days=1)).strftime('%B %d, %Y')}"
                ),
                "arc_score": round(peak_score, 4),
                "arc_percent": max(2, round(peak_score * 100)),
                "arc_label": intensity_label,
                "arc_bar": intensity_bar,
                "dominant_planet": month_planet,
                "dominant_aspect_character": month_character,
                "snapshot_block": snapshot_block,
                "activated_domains": _most_activated_domains(
                    events_active,
                    HOUSE_DOMAINS,
                    period_start,
                    period_end,
                ),
                "events": formatted_events,
                "event_count": len(formatted_events),
            }
        )

    return {
        "natal_positions": _build_natal_positions(payload),
        "house_system": variables.get("house_system", "Whole Sign"),
        "tropical_zodiac": True,
        "timeline_start": timeline.get("report_start"),
        "timeline_end": timeline.get("report_end"),
        "timeline_event_count": len(all_events),
        "landmarks": landmarks,
        # Compatibility alias for any downstream code still using the old key.
        "landmark_influences": landmarks,
        "year_overview_block": year_overview_block,
        "year_integration_block": year_integration_block,
        "year_integration_theme": year_integration_theme,
        "dominant_slow_planet": dominant_planet,
        "dominant_aspect_type": (
            dominant_event.get("aspect", "")
            if dominant_event else ""
        ),
        "dominant_aspect_character": dominant_character,
        "annual_arc": months,
        "months": months,
        "active_transit_count": len(transit_events),
    }


# ── Template Rendering ─────────────────────────────────────────

def render_template(report_type: str, context: dict) -> str:
    """Renders a Jinja2 HTML template with the given context."""
    if not JINJA2_AVAILABLE:
        return _render_fallback(report_type, context)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template_map = {
        "horoscope":         "daily_horoscope/templates/daily_horoscope.html",
        "year_ahead":        "year_ahead/templates/active/year_ahead.html",
        "soul_journey":      "soul_ecosystem/templates/soul_ecosystem.html",
        "asteroid_portrait": "asteroid_portrait/templates/asteroid_portrait.html",
        "identity_profile":  "identity_profile/templates/entangled_identity_profile.html",
    }
    template_name = template_map.get(
        report_type,
        "daily_horoscope/templates/daily_horoscope.html",
    )
    try:
        template = env.get_template(template_name)
        return template.render(**context)
    except Exception as e:
        print(f"[Render] Template error: {e}")
        return _render_fallback(report_type, context)


def _render_fallback(report_type: str, context: dict) -> str:
    """Simple fallback renderer when Jinja2 isn't available."""
    html = f"""<!DOCTYPE html>
<html><head><title>{report_type}</title>
<meta charset="utf-8">
<style>
  body {{ background: #0A0A0C; color: #E0E0E0; font-family: Georgia, serif;
          max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
  h1 {{ color: #00FF88; }} h2 {{ color: #B088FF; }} h3 {{ color: #88BBFF; }}
  .block {{ margin: 20px 0; line-height: 1.8; }}
</style>
</head><body>
<h1>{context.get('querent_name','')}</h1>
<h2>{report_type.replace('_',' ').title()}</h2>
<p style="color:#888">{context.get('generation_date','')} · {context.get('generation_location','')}</p>
<hr style="border-color:#333">
"""
    for key, val in context.items():
        if isinstance(val, str) and len(val) > 30 and not key.startswith("_"):
            html += f'<h3>{key.replace("_"," ").title()}</h3>\n'
            html += f'<div class="block">{val}</div>\n'
    html += "</body></html>"
    return html


# ── Moon Phase Key ─────────────────────────────────────────────

def _moon_phase_key(phase_descriptor: str) -> str:
    """Maps a moon phase descriptor string to a JSON key."""
    phase_map = {
        "New Moon": "new_moon", "Waxing Crescent": "waxing_crescent",
        "First Quarter": "first_quarter", "Waxing Gibbous": "waxing_gibbous",
        "Full Moon": "full_moon", "Waning Gibbous": "waning_gibbous",
        "Last Quarter": "last_quarter", "Balsamic": "balsamic"
    }
    for key, val in phase_map.items():
        if key.lower() in phase_descriptor.lower():
            return val
    return "fallback"


# ── CLI ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Entangled Oracle Report Generator"
    )
    parser.add_argument("report_type",
        choices=["horoscope","year_ahead","soul_journey","asteroid_portrait","identity_profile"],
        help="Type of report to generate"
    )
    parser.add_argument("--name",     required=True,  help="Querent name")
    parser.add_argument("--date",     required=True,  help="Birth date (YYYY-MM-DD)")
    parser.add_argument("--time",     required=False, help="Birth time (HH:MM), 24h format")
    parser.add_argument("--location", required=False, help="Birth location (city, state)")
    parser.add_argument("--current-location", required=False,
                        help="Current/festival location (defaults to birth location)")
    parser.add_argument("--simple",   action="store_true",
                        help="Simple mode: DOB only, no birth time needed")
    parser.add_argument("--no-browser", action="store_true",
                        help="Don't open browser after generation")
    parser.add_argument("--output",   required=False, help="Output filename (optional)")
    parser.add_argument(
        "--content-pack",
        dest="content_pack",
        choices=["plainspeak", "entangled_oracle"],
        default="plainspeak",
        help="Interpretation block library: plainspeak (default) or entangled_oracle",
    )

    args = parser.parse_args()
    birth_data = parse_birth_data(args)
    birth_data["current_location"] = args.current_location or args.location or ""

    output_path = generate_report(args.report_type, birth_data, args.output, args.content_pack)

    if not args.no_browser:
        webbrowser.open(f"file://{os.path.abspath(output_path)}")
    else:
        print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
