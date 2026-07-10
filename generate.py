#!/usr/bin/env python3
"""
generate.py — Entangled Oracle Report Generator
Main entry point. Run from the command line.

Usage:
    python generate.py horoscope --name "Puck" --date 1992-03-21 --time 08:11 --location "Peoria, IL"
    python generate.py weekly_horoscope --name "Puck" --date 1992-03-21 --time 08:11 --location "Peoria, IL"
    python generate.py year_ahead --name "Puck" --date 1992-03-21 --time 08:11 --location "Peoria, IL"
    python generate.py personal_forecast --name "Puck" --date 1992-03-21 --time 08:11 --location "Peoria, IL"
    python generate.py soul_ecosystem --name "Puck" --date 1992-03-21 --time 08:11 --location "Peoria, IL"

DOB-only mode (simple horoscope, no birth time needed):
    python generate.py horoscope --name "Visitor" --date 1990-06-15 --simple
"""
import argparse
import hashlib
import html
import os
import sys
import json
import re
import uuid
import webbrowser
from functools import lru_cache
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import OUTPUT_DIR, TEMPLATES_DIR, PRODUCTS_DIR
from formulas.standard.forecast_activation import build_ranking_diagnostics
from formulas.standard.forecast_synthesis import build_forecast_synthesis
from formulas.standard.methodology_profiles import get_active_methodology_metadata
from product_versions import (
    REPORT_MANIFEST_SCHEMA_VERSION,
    build_version_registry,
    report_version,
    template_path,
    write_json,
)

# Dev-only content trace. Set EO_CONTENT_TRACE=1 to print station source/subtitle
# resolution to the terminal. Never written to HTML or PDF output.
def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


_EO_CONTENT_TRACE = _env_flag("EO_CONTENT_TRACE")

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    print("Warning: jinja2 not installed. Run: pip install jinja2")


# ── Input Parsing ──────────────────────────────────────────────

class InputValidationError(ValueError):
    """Raised when CLI-supplied birth data is malformed. Caught in main()
    for a clean one-line error instead of a raw Python traceback."""


def parse_birth_data(args) -> dict:
    """Parses CLI arguments into a birth data dict."""
    name = args.name
    if not name or not name.strip():
        raise InputValidationError("--name cannot be empty or whitespace-only.")

    date_string = args.date
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise InputValidationError(
            f"--date '{date_string}' is not a valid date in YYYY-MM-DD format."
        ) from None

    birth_data = {
        "name": name,
        "date": date_string,
        "location": args.location or "",
        "simple_mode": getattr(args, "simple", False)
    }
    if hasattr(args, "time") and args.time and not birth_data["simple_mode"]:
        time_string = args.time
        time_format = "%H:%M:%S" if time_string.count(":") == 2 else "%H:%M"
        try:
            datetime.strptime(time_string, time_format)
        except ValueError:
            raise InputValidationError(
                f"--time '{time_string}' is not a valid 24-hour time in HH:MM or HH:MM:SS format."
            ) from None
        birth_data["time"] = time_string
    else:
        birth_data["time"] = None
        birth_data["simple_mode"] = True
    birth_data["palette"] = getattr(args, "palette", "vibrant")
    birth_data["report_date"] = getattr(args, "report_date", None)
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


def _align_to_week_start(moment: datetime) -> datetime:
    """Returns UTC midnight of the Monday in the same calendar week as moment."""
    day_start = moment.replace(hour=0, minute=0, second=0, microsecond=0)
    return day_start - timedelta(days=day_start.weekday())


def _report_window(report_type: str, report_start: datetime) -> tuple[datetime, datetime]:
    """
    Returns (report_start, report_end) for a report type's forecast window.

    weekly_horoscope aligns to the Monday-Friday work week containing
    report_start, regardless of which day generation happens to run on —
    so a whole cohort generated together (the intended B2B batch-export
    use case) shares identical week boundaries rather than each member's
    window drifting by generation time. Clinical / theory / off-day
    custom schedules are an explicit later follow-on; Monday-Friday is
    just the default for now.
    """
    if report_type == "weekly_horoscope":
        monday = _align_to_week_start(report_start)
        return monday, monday + timedelta(days=5)
    return report_start, _add_one_year(report_start)


def _stdout_report_paths_enabled() -> bool:
    return _env_flag("EO_STDOUT_REPORT_PATHS")


def _stdout_verbose_enabled() -> bool:
    return _env_flag("EO_VERBOSE_STDOUT")


def _log_verbose(message: str) -> None:
    if _stdout_verbose_enabled():
        print(message)


def _atomic_write_text(path: str, content: str) -> None:
    directory = os.path.dirname(path) or "."
    Path(directory).mkdir(parents=True, exist_ok=True)
    temp_name = f".{os.path.basename(path)}.{uuid.uuid4().hex}.tmp"
    temp_path = os.path.join(directory, temp_name)
    try:
        with open(temp_path, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def _default_output_filename(report_type: str, birth_data: dict, report_start: datetime) -> str:
    safe_name = birth_data["name"].replace(" ", "_").lower()
    timestamp = report_start.strftime("%Y%m%d_%H%M%S")
    request_id = uuid.uuid4().hex[:8]
    return f"{safe_name}_{report_type}_{timestamp}_{request_id}.html"


def generate_report(
    report_type: str,
    birth_data: dict,
    output_filename: str | None = None,
    content_pack: str = "plainspeak",
    output_dir: str | None = None,
) -> str:
    """
    Master report generator.
    Returns the path to the generated HTML file.
    """
    from formulas.proprietary_indexes import compute_all_indexes
    from formulas.report_surface import build_layered_report_bundle
    from selectors.variable_resolver import resolve_all

    payload = get_payload(birth_data)

    _log_verbose("[Formulas] Computing indexes...")
    index_results = compute_all_indexes(payload)
    standard_report_bundle = build_layered_report_bundle(
        payload,
        report_type,
        index_results=index_results,
    )

    if birth_data.get("report_date"):
        report_start = datetime.strptime(birth_data["report_date"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        report_start = datetime.now(timezone.utc)
    report_start, report_end = _report_window(report_type, report_start)

    _log_verbose("[Variables] Resolving...")
    variables = resolve_all(
        payload=payload,
        index_results=index_results,
        standard_report_bundle=standard_report_bundle,
        querent_name=birth_data["name"],
        current_location=birth_data.get("current_location") or birth_data["location"],
        report_start_date=report_start,
        report_end_date=report_end,
    )
    variables["palette"] = birth_data.get("palette", "vibrant")

    # Predictive engine (Testable Predictive Formulas Experimental v0.1) is
    # quarantined — see quarantine/predictive_testable_v0_1/README.md.
    # These keys are kept present (always empty) so any leftover template
    # reference degrades to blank instead of a Jinja UndefinedError.
    variables["predictive_results"] = {}
    variables["predictive_sidecar"] = {}

    _log_verbose("[Blocks] Selecting...")
    context = build_report_context(
        report_type,
        variables,
        index_results,
        payload,
        report_start=report_start,
        report_end=report_end,
        content_pack=content_pack,
        standard_report_bundle=standard_report_bundle,
    )

    _log_verbose("[Render] Building HTML...")
    html = render_template(report_type, context)

    if output_filename is None:
        output_filename = _default_output_filename(report_type, birth_data, report_start)

    effective_dir = output_dir if output_dir else OUTPUT_DIR
    output_path = os.path.join(effective_dir, output_filename)
    os.makedirs(effective_dir, exist_ok=True)

    _atomic_write_text(output_path, html)

    manifest_path = _write_report_manifest(
        report_type=report_type,
        birth_data=birth_data,
        payload=payload,
        index_results=index_results,
        standard_report_bundle=standard_report_bundle,
        context=context,
        content_pack=content_pack,
        output_path=output_path,
        report_start=report_start,
        report_end=report_end,
    )

    print(f"[Done] Report saved: {os.path.basename(output_path)}")
    print(f"[Done] Manifest saved: {os.path.basename(manifest_path)}")

    if _stdout_report_paths_enabled():
        print(f"[Done] Report path: {output_path}")
        print(f"[Done] Manifest path: {manifest_path}")
    return output_path


def build_report_context(
    report_type: str,
    variables: dict,
    index_results: dict,
    payload: dict,
    report_start: datetime | None = None,
    report_end: datetime | None = None,
    content_pack: str = "plainspeak",
    standard_report_bundle: dict | None = None,
) -> dict:
    """
    Builds the full template context dict for a given report type.
    Selects all paragraph blocks and merges them with variable data.

    Each report type has its own block selection logic defined here.
    """
    from selectors.block_selector import select_block, select_tier_block

    from formulas.report_surface import build_layered_report_bundle, build_report_bundle_context_view

    ctx = dict(variables)  # start with all resolved variables
    standard_report_bundle = standard_report_bundle or build_layered_report_bundle(
        payload,
        report_type,
        index_results=index_results,
    )
    ctx["standard_report_bundle"] = standard_report_bundle
    ctx["standard_result_bundle"] = standard_report_bundle.get("standard_result_bundle", {})
    ctx["report_surface_trace"] = standard_report_bundle.get("trace", {})
    ctx["standard_report_context_view"] = build_report_bundle_context_view(
        standard_report_bundle,
        report_type,
    )

    if report_type == "horoscope":
        ctx.update(_build_horoscope_context(variables, index_results, payload))

    elif report_type == "weekly_horoscope":
        ctx.update(_build_weekly_horoscope_context(variables, index_results, payload, report_start, report_end))

    elif report_type == "year_ahead":
        ctx.update(
            _build_year_ahead_context(
                variables,
                index_results,
                payload,
                report_start,
                report_end,
                content_pack,
                standard_report_bundle=standard_report_bundle.get("standard_result_bundle", {}),
            )
        )
        
    elif report_type == "personal_forecast":
        ctx.update(_build_personal_forecast_context(variables, index_results, payload, report_start, content_pack))

    elif report_type == "soul_ecosystem":
        ctx.update(_build_soul_ecosystem_context(variables, index_results, payload))

    elif report_type == "identity_profile":
        from products.identity_profile.runtime.identity_profile_context import build_identity_profile_context
        ctx.update(build_identity_profile_context(variables, index_results, payload))

    trace = ctx.get("report_surface_trace", {})
    if isinstance(trace, dict):
        trace["template_fields_populated"] = sorted(ctx.keys())
        trace["generation_date"] = ctx.get("generation_date", "")
        trace["methodology_marker"] = {
            "id": ctx.get("methodology_id", ""),
            "label": ctx.get("methodology_label", ""),
            "zodiac": ctx.get("zodiac", ""),
            "house_system": ctx.get("house_system", ""),
        }
    return ctx


def _dict_lookup_with_fallback(data: dict, *keys: str, fallback: str = "fallback") -> str:
    cursor = data
    for key in keys:
        if not isinstance(cursor, dict):
            return ""
        key = str(key or fallback)
        cursor = cursor.get(key) or cursor.get(fallback)
    if isinstance(cursor, str):
        return cursor
    if isinstance(cursor, dict) and isinstance(cursor.get(fallback), str):
        return cursor[fallback]
    return ""


def _raw_select_block(path: str, *keys: str, fallback: str = "fallback") -> str:
    """Select a block without suppressing literal TODO scaffolding markers."""
    data = _load_json_file(path)
    return _dict_lookup_with_fallback(data, *keys, fallback=fallback)


def _pack_path(pack: dict, key: str) -> str:
    from config import CONTENT_PACKS
    return pack.get(key) or CONTENT_PACKS["plainspeak"].get(key, "")


def _display_any_date(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%B %d, %Y")
    if isinstance(value, str) and value.strip():
        text = value.strip()
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return parsed.strftime("%B %d, %Y")
        except ValueError:
            return text[:10]
    return ""


def _period_date_range(period: dict) -> str:
    start = _display_any_date(period.get("start_at"))
    end = _display_any_date(period.get("end_at"))
    return " - ".join(part for part in (start, end) if part)


def _topic_to_domain_key(topic_keys: list[str], remap: dict) -> str:
    topic_remap = remap.get("topic_key") if isinstance(remap.get("topic_key"), dict) else {}
    for topic in topic_keys or []:
        topic = str(topic or "")
        if topic in topic_remap:
            return topic_remap[topic]
        if topic.startswith("house:") and topic_remap.get(topic):
            return topic_remap[topic]
    return topic_remap.get("fallback", "fallback")


def _chapter_kind_from_tier4(chapter: dict, remap: dict) -> str:
    chapter_remap = remap.get("chapter_type") if isinstance(remap.get("chapter_type"), dict) else {}
    chapter_type = str(chapter.get("chapter_type") or "fallback")
    label = str(chapter.get("label") or "fallback")
    typed = chapter_remap.get(chapter_type)
    if isinstance(typed, dict):
        return typed.get(label) or typed.get("fallback") or chapter_remap.get("fallback") or "fallback"
    if isinstance(typed, str):
        return typed
    return chapter_remap.get("fallback", "fallback")


def _build_predictive_report_surface(
    sidecar: dict,
    report_type: str,
    forecast_synthesis: dict | None = None,
    pack_paths: dict | None = None,
) -> dict:
    """
    Report-facing predictive research cards remapped from the quarantined
    Phase 9b sidecar contract onto Tier 4 forecast_synthesis output.

    The authored predictive JSON remains the prose source of truth; its
    _tier4_remap metadata translates synthesis chapter labels and method
    families to the existing block keys.
    """
    del sidecar  # The old convergence sidecar is intentionally not trusted.
    pack_paths = pack_paths or {}
    synthesis = forecast_synthesis if isinstance(forecast_synthesis, dict) else {}
    chapters_path = (
        pack_paths.get("predictive_chapters")
        if report_type == "year_ahead"
        else pack_paths.get("personal_predictive_chapters")
    )
    if not chapters_path:
        from config import CONTENT_PACKS
        chapters_path = (
            CONTENT_PACKS["plainspeak"].get("predictive_chapters")
            if report_type == "year_ahead"
            else CONTENT_PACKS["plainspeak"].get("personal_predictive_chapters")
        )
    candidates_path = pack_paths.get("personal_predictive_candidates")
    if not candidates_path:
        from config import CONTENT_PACKS
        candidates_path = CONTENT_PACKS["plainspeak"].get("personal_predictive_candidates")
    chapter_library = _load_json_file(chapters_path or "")
    chapter_remap = chapter_library.get("_tier4_remap", {})

    cards = []
    for chapter in (synthesis.get("evidence_chapters") or [])[:6]:
        if not isinstance(chapter, dict):
            continue
        chapter_kind = _chapter_kind_from_tier4(chapter, chapter_remap)
        domain_key = _topic_to_domain_key(chapter.get("topic_keys") or [], chapter_remap)
        block = _dict_lookup_with_fallback(chapter_library, chapter_kind, domain_key)
        if not block:
            block = _dict_lookup_with_fallback(chapter_library, "fallback")
        cards.append({
            "title": str(chapter.get("time_scope") or "Forecast chapter"),
            "kicker": str(chapter.get("chapter_type") or "tier4_chapter"),
            "body": block,
            "chapter_kind": chapter_kind,
            "domain_key": domain_key,
            "tier4_label": str(chapter.get("label") or ""),
            "source": "forecast_synthesis.evidence_chapters",
            "source_event_ids": list(chapter.get("supporting_event_ids") or [])[:8],
            "complicating_event_ids": list(chapter.get("complicating_event_ids") or [])[:8],
            "provenance": list(chapter.get("provenance") or [])[:4],
        })

    candidates = []
    if report_type == "personal_forecast":
        candidate_library = _load_json_file(candidates_path or "")
        candidate_remap = candidate_library.get("_tier4_remap", {})
        annual = synthesis.get("annual_terrain_map") if isinstance(synthesis.get("annual_terrain_map"), dict) else {}
        domain_key = _topic_to_domain_key(annual.get("dominant_topics") or [], candidate_remap)
        method_remap = candidate_remap.get("method_family") if isinstance(candidate_remap.get("method_family"), dict) else {}
        for family in (annual.get("method_families") or [])[:6]:
            family_key = method_remap.get(str(family).upper()) or method_remap.get("fallback", "fallback")
            block = _dict_lookup_with_fallback(candidate_library, domain_key, family_key)
            if not block:
                block = _dict_lookup_with_fallback(candidate_library, "fallback")
            candidates.append({
                "title": domain_key.replace("_", " ").title() if domain_key != "fallback" else "Predictive candidate",
                "kicker": str(family),
                "body": block,
                "domain_key": domain_key,
                "family_key": family_key,
                "source": "forecast_synthesis.annual_terrain_map",
            })

    return {
        "enabled": bool(cards or candidates),
        "report_type": report_type,
        "chapters": cards,
        "candidates": candidates,
        "source_contract": "forecast_synthesis.tier4_remap",
    }


def _zr_event_kind(event: dict) -> str:
    variant = str(event.get("method_variant") or "").lower()
    if "lob" in variant:
        return "loosing_of_the_bond"
    if "peak" in variant:
        return "peak"
    return "transition"


def _build_tier5_year_ahead_surfaces(timeline: dict, forecast_synthesis: dict, pack: dict) -> dict:
    profection_path = _pack_path(pack, "annual_profections")
    zr_path = _pack_path(pack, "zodiacal_releasing")
    returns_path = _pack_path(pack, "exact_returns")
    terrain_path = _pack_path(pack, "forecast_synthesis_blocks")

    annual_profections = []
    for period in timeline.get("time_lord_periods", []):
        if str(period.get("system") or "") != "annual_profection":
            continue
        house_key = str(period.get("period_house") or "fallback")
        annual_profections.append({
            "title": "Annual Profection",
            "kicker": _period_date_range(period),
            "body": _raw_select_block(profection_path, house_key, str(period.get("period_lord") or "fallback")),
            "period_lord": period.get("period_lord", ""),
            "period_house": period.get("period_house", ""),
            "period_sign": period.get("period_sign", ""),
            "confidence": period.get("confidence", 0.0),
            "source": "time_lord_periods.annual_profection",
        })

    zr_periods_by_id = {
        period.get("period_id"): period
        for period in timeline.get("zodiacal_releasing_periods", [])
        if isinstance(period, dict)
    }
    zodiacal_releasing = []
    for event in timeline.get("zodiacal_releasing_events", [])[:8]:
        period = zr_periods_by_id.get(event.get("period_id"), {})
        level = str(period.get("level") or ("L1" if str(event.get("method_variant") or "").startswith("zr_l1") else "L2"))
        if level not in {"L1", "L2"}:
            continue
        kind = _zr_event_kind(event)
        zodiacal_releasing.append({
            "title": "Zodiacal Releasing",
            "kicker": _display_any_date(event.get("peak_datetime")),
            "body": _raw_select_block(zr_path, level, kind),
            "level": level,
            "event_kind": kind,
            "period_lord": event.get("period_lord", ""),
            "period_sign": event.get("period_sign", ""),
            "lot_name": event.get("natal_target", ""),
            "source": "zodiacal_releasing_events",
        })

    exact_returns = []
    for event in timeline.get("return_events", [])[:8]:
        variant = str(event.get("method_variant") or "fallback")
        exact_returns.append({
            "title": "Exact Return",
            "kicker": _display_any_date(event.get("peak_datetime")),
            "body": _raw_select_block(returns_path, variant),
            "return_body": event.get("return_body", event.get("transit_planet", "")),
            "method_variant": variant,
            "temporal_precision": event.get("temporal_precision", ""),
            "confidence": event.get("confidence", 0.0),
            "source": "return_events",
        })

    annual = forecast_synthesis.get("annual_terrain_map") if isinstance(forecast_synthesis, dict) else {}
    terrain = {
        "annual": {
            "title": "Forecast Terrain",
            "kicker": str(annual.get("label") or ""),
            "body": _raw_select_block(terrain_path, "agreement_labels", str(annual.get("label") or "fallback")),
            "method_families": list(annual.get("method_families") or []),
            "dominant_topics": list(annual.get("dominant_topics") or [])[:6],
            "source": "forecast_synthesis.annual_terrain_map",
        },
        "months": [
            {
                "title": month.get("month_name", ""),
                "kicker": month.get("zone", ""),
                "body": _raw_select_block(terrain_path, "monthly_zones", str(month.get("zone") or "fallback")),
                "relative_intensity": month.get("relative_intensity", 0.0),
                "method_families": list(month.get("method_families") or []),
                "dominant_topics": list(month.get("dominant_topics") or [])[:4],
                "source": "forecast_synthesis.monthly_terrain",
            }
            for month in (forecast_synthesis.get("monthly_terrain") or [])
            if isinstance(month, dict) and month.get("zone") != "background"
        ][:6],
        "chapters": [
            {
                "title": chapter.get("time_scope", ""),
                "kicker": chapter.get("label", ""),
                "body": _raw_select_block(
                    terrain_path,
                    "chapter_types",
                    str(chapter.get("chapter_type") or "fallback"),
                    str(chapter.get("label") or "fallback"),
                ),
                "topic_keys": list(chapter.get("topic_keys") or [])[:4],
                "source": "forecast_synthesis.evidence_chapters",
            }
            for chapter in (forecast_synthesis.get("evidence_chapters") or [])[:6]
            if isinstance(chapter, dict)
        ],
        "contradictions": [
            {
                "title": "Forecast contradiction",
                "kicker": item.get("label", ""),
                "body": _raw_select_block(terrain_path, "contradictions", str(item.get("label") or "fallback")),
                "method_families": list(item.get("method_families") or []),
                "operations": list(item.get("operations") or []),
                "source": "forecast_synthesis.contradictions",
            }
            for item in (forecast_synthesis.get("contradictions") or [])[:4]
            if isinstance(item, dict)
        ],
    }

    return {
        "annual_profections": annual_profections,
        "zodiacal_releasing": zodiacal_releasing,
        "exact_returns": exact_returns,
        "forecast_terrain": terrain,
    }


THEME_LABELS = {
    "career_visibility":      "Public Emergence",
    "identity_direction":     "Self in Motion",
    "relationships_agreements": "Bonds & Boundaries",
    "work_health_capacity":   "The Daily Craft",
    "home_foundation":        "Roots & Sanctuary",
    "creativity_pleasure":    "The Pleasure Current",
    "money_resources":        "Material Sovereignty",
    "inner_life_rest":        "The Quiet Current",
}

# Priority order: natal_target → natal_house → transit_planet
# First match wins.
THEME_MAP = {
    # natal_target rules (highest priority)
    "natal_target": {
        "MC":      "career_visibility",
        "Sun":     "career_visibility",   # Sun in 10th overrides below; house check refines
        "ASC":     "identity_direction",
        "Moon":    "home_foundation",
        "Venus":   "relationships_agreements",
        "Mars":    "work_health_capacity",
        "Mercury": "work_health_capacity",
        "Jupiter": "career_visibility",
        "Saturn":  "inner_life_rest",
        "Uranus":  "identity_direction",
        "Neptune": "inner_life_rest",
        "Pluto":   "identity_direction",
    },
    # natal_house override (applied after natal_target; can shift theme)
    "natal_house": {
        1:  "identity_direction",
        2:  "money_resources",
        4:  "home_foundation",
        5:  "creativity_pleasure",
        6:  "work_health_capacity",
        7:  "relationships_agreements",
        8:  "money_resources",
        10: "career_visibility",
        11: "relationships_agreements",
        12: "inner_life_rest",
        # houses 3, 9 fall through to transit_planet fallback
    },
    # transit_planet fallback (lowest priority)
    "transit_planet": {
        "Jupiter": "career_visibility",
        "Saturn":  "inner_life_rest",
        "Uranus":  "identity_direction",
        "Neptune": "inner_life_rest",
        "Pluto":   "identity_direction",
        "Mars":    "work_health_capacity",
    },
}


def _assign_theme(event: dict) -> str:
    natal_target = event.get("natal_target", "")
    natal_house  = int(event.get("natal_house") or 0)
    transit_planet = event.get("transit_planet", "")
    event_type   = event.get("event_type", "")

    # Eclipses hitting Sun, Moon, ASC, MC always go to their primary theme
    if event_type == "eclipse":
        return THEME_MAP["natal_target"].get(natal_target,
               THEME_MAP["natal_house"].get(natal_house, "inner_life_rest"))

    # Ingresses are defined by the Whole Sign house entered. Their engine
    # contract uses house_number, not natal_house.
    if event_type == "ingress":
        ingress_house = int(event.get("house_number") or natal_house or 0)
        return THEME_MAP["natal_house"].get(ingress_house,
               THEME_MAP["transit_planet"].get(transit_planet, "identity_direction"))

    # Transits and stations: natal_target → natal_house → transit_planet
    theme = THEME_MAP["natal_target"].get(natal_target)
    if theme:
        # natal_house can override for strong house signals
        house_theme = THEME_MAP["natal_house"].get(natal_house)
        if house_theme and natal_house in (1, 4, 7, 10):  # angular houses override
            return house_theme
        return theme

    return (THEME_MAP["natal_house"].get(natal_house) or
            THEME_MAP["transit_planet"].get(transit_planet) or
            "inner_life_rest")


def _group_into_themes(all_events: list[dict]) -> list[dict]:
    """
    Accepts the full sorted event list from compute_year_ahead_events().
    Returns exactly 3 theme dicts, representing the strongest forecast themes.

    Each theme dict contains:
      - theme_key        (str)   e.g. "career_visibility"
      - theme_label      (str)   e.g. "Public Emergence"
      - anchor_event     (dict)  highest-scoring event assigned to this theme
      - supporting_events (list) remaining events in this theme, sorted by score desc
      - theme_score      (float) anchor_event's combined_intensity_score
    """
    # 1. Drop passing-tier noise
    qualified_events = [e for e in all_events if e.get("combined_intensity_score", 0.0) >= 0.20]

    # 2. Map events to themes
    grouped = {}
    for event in qualified_events:
        t_key = _assign_theme(event)
        if t_key not in grouped:
            grouped[t_key] = []
        grouped[t_key].append(event)

    themes = []
    # 3. Form anchor events and lists
    for t_key, events in grouped.items():
        sorted_events = sorted(events, key=lambda e: e.get("combined_intensity_score", 0.0), reverse=True)
        anchor = sorted_events[0]
        
        themes.append({
            "theme_key": t_key,
            "theme_label": THEME_LABELS.get(t_key, t_key),
            "anchor_event": anchor,
            "supporting_events": sorted_events[1:],
            "theme_score": float(anchor.get("combined_intensity_score", 0.0))
        })

    # 4 & 5. Sort by anchor event score descending and return the top 3
    themes.sort(key=lambda t: t["theme_score"], reverse=True)
    return themes[:3]


# ── Personal Forecast Assembly ─────────────────────────────────
#
# The Personal Forecast block file is deliberately a synthesis library.
# Event-level interpretation remains in the transit, ingress, eclipse, and
# station libraries. This layer turns the selected 90-day event architecture
# into the specific fields required by templates/personal_forecast.html.

PERSONAL_FORECAST_THEME_ALIASES = {
    "career_visibility": "public_emergence",
    "identity_direction": "self_in_motion",
    "relationships_agreements": "bonds_and_boundaries",
    "work_health_capacity": "daily_craft",
    "home_foundation": "roots_and_sanctuary",
    "creativity_pleasure": "pleasure_current",
    "money_resources": "material_sovereignty",
    "inner_life_rest": "quiet_current",
}


@lru_cache(maxsize=4)
def _load_personal_forecast_blocks(block_path: str) -> dict:
    """Loads and caches the Personal Forecast synthesis library."""
    with open(block_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _personal_forecast_theme_key(theme_key: str) -> str:
    """Normalizes legacy selector keys to the synthesis library's keys."""
    return PERSONAL_FORECAST_THEME_ALIASES.get(theme_key, theme_key)


def _personal_forecast_character(event: dict) -> str:
    """Returns the two-state tone key used by the Personal Forecast library."""
    character = event.get("aspect_character")
    if character in {"flowing", "challenging"}:
        return character

    # Stations do not carry an aspect character, but their direction change
    # has a coherent experiential polarity for this report's purposes.
    if event.get("event_type") == "station":
        return "flowing" if event.get("station_type") == "Direct" else "challenging"

    return "flowing"


def _personal_forecast_event_house(event: dict) -> int:
    """Gets the most relevant Whole Sign house across all forecast event types."""
    keys = (
        ("house_number", "natal_house", "whole_sign_house")
        if event.get("event_type") == "ingress"
        else ("natal_house", "whole_sign_house", "house_number")
    )
    for key in keys:
        try:
            house = int(event.get(key) or 0)
        except (TypeError, ValueError):
            house = 0
        if 1 <= house <= 12:
            return house
    return 0


def _personal_forecast_score(event: dict) -> float:
    """Reads the normalized event score without failing on sparse event types."""
    try:
        return float(event.get("combined_intensity_score", event.get("score", 0.0)) or 0.0)
    except (TypeError, ValueError):
        return 0.0


PERSONAL_FORECAST_TYPE_BONUS = {
    "eclipse": 0.18,
    "station": 0.12,
    "ingress": 0.08,
    "transit": 0.00,
    "proprietary_transit": 0.10,
}


def _event_ranking_diagnostics(
    event: dict,
    *,
    context: str,
    rank_score: float | None = None,
    rank_basis: str = "combined_intensity_score",
    local_relevance: float | None = None,
) -> dict:
    try:
        return build_ranking_diagnostics(
            event,
            context=context,
            rank_score=rank_score,
            rank_basis=rank_basis,
            local_relevance=local_relevance,
        )
    except Exception:
        return {
            "context": context,
            "rank_score": round(float(rank_score or 0.0), 4),
            "rank_basis": rank_basis,
            "top_components": [],
            "unsupported_components": ["score_components"],
            "local_relevance": round(local_relevance, 4) if local_relevance is not None else None,
        }


def _personal_forecast_rank_score(event: dict) -> float:
    return _personal_forecast_score(event) + PERSONAL_FORECAST_TYPE_BONUS.get(event.get("event_type"), 0.0)


def _personal_forecast_event_identity(event: dict) -> tuple:
    """Creates a stable identity used to mark the featured timing window."""
    return (
        event.get("event_type", ""),
        event.get("peak_date") or event.get("entry_date") or "",
        event.get("transit_planet", ""),
        event.get("aspect", ""),
        event.get("natal_target", ""),
        _personal_forecast_event_house(event),
        event.get("station_type", ""),
        event.get("eclipse_type", ""),
    )


def _personal_forecast_date_sort_key(event: dict) -> datetime:
    """Returns the engine timestamp used to restore chronological display order."""
    for key in ("peak_datetime", "entry_datetime", "leave_datetime"):
        value = event.get(key)
        if isinstance(value, datetime):
            return value
    return datetime.max.replace(tzinfo=timezone.utc)


def _personal_forecast_timeline_position_pct(
    event: dict,
    start_date: datetime,
    end_date: datetime,
) -> int:
    """Maps an event timestamp onto the report window as a 0-100 percentage."""
    event_date = _personal_forecast_date_sort_key(event)
    if event_date == datetime.max.replace(tzinfo=timezone.utc):
        return 50

    if event_date.tzinfo is None and start_date.tzinfo is not None:
        event_date = event_date.replace(tzinfo=start_date.tzinfo)

    total_seconds = (end_date - start_date).total_seconds()
    if total_seconds <= 0:
        return 50

    elapsed_seconds = (event_date - start_date).total_seconds()
    pct = int(round((elapsed_seconds / total_seconds) * 100))
    return max(0, min(100, pct))


def _select_personal_forecast_timing_events(
    all_events: list[dict],
    featured_event: dict | None,
    max_windows: int = 4,
) -> list[dict]:
    """
    Selects a compact, varied set of high-signal timing windows.

    The engine remains authoritative for timing and score. This function only
    limits density for the compact Personal Forecast table, then restores the
    engine's chronological order for display.
    """
    candidates = [
        event for event in all_events
        if _personal_forecast_score(event) >= 0.20
        and (event.get("peak_date") or event.get("entry_date"))
    ]

    ranked = sorted(
        candidates,
        key=lambda event: (
            _personal_forecast_rank_score(event),
            _personal_forecast_score(event),
        ),
        reverse=True,
    )

    selected: list[dict] = []
    used_identities: set[tuple] = set()
    used_dates: set[str] = set()

    for event in ranked:
        identity = _personal_forecast_event_identity(event)
        date_label = event.get("peak_date") or event.get("entry_date") or ""
        if identity in used_identities or date_label in used_dates:
            continue
        selected.append(event)
        used_identities.add(identity)
        used_dates.add(date_label)
        if len(selected) >= max_windows:
            break

    # The featured event must be visible on the timeline as well as in the
    # Turning Point card. Replace the lowest-ranked selected entry if needed.
    if featured_event:
        featured_identity = _personal_forecast_event_identity(featured_event)
        if featured_identity not in used_identities:
            if len(selected) >= max_windows:
                selected.pop()
            selected.append(featured_event)

    return sorted(selected, key=_personal_forecast_date_sort_key)


def _personal_forecast_intensity(score: float) -> str:
    """Maps engine score bands to the compact template's visual classes."""
    if score >= 0.60:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def _personal_forecast_event_label(event: dict) -> str:
    """
    Returns a concise, human-readable event label for context consumers.

    Produces predictable strings per event type:
      transit  → "Jupiter Trine Moon"
      ingress  → "Jupiter enters House 8"
      station  → "Saturn Direct"
      eclipse  → "Solar Eclipse on Sun"
    Returns "" for unknown types or missing fields rather than raising.
    """
    etype = event.get("event_type", "")

    if etype == "transit":
        parts = [
            event.get("transit_planet", ""),
            event.get("aspect", ""),
            event.get("natal_target", ""),
        ]
        return " ".join(p for p in parts if p)

    if etype == "ingress":
        planet = event.get("transit_planet", "")
        house = _personal_forecast_event_house(event)
        house_str = f"House {house}" if house else ""
        parts = [p for p in (planet, "enters", house_str) if p]
        return " ".join(parts)

    if etype == "station":
        planet = event.get("transit_planet", "")
        direction = event.get("station_type", "")
        return " ".join(p for p in (planet, direction) if p)

    if etype == "eclipse":
        eclipse_type = (event.get("eclipse_type") or "").title()
        target = event.get("natal_target", "")
        parts = [eclipse_type, "Eclipse"]
        if target:
            parts.extend(["on", target])
        return " ".join(p for p in parts if p)

    return ""


def _normalize_forecast_event(event: dict | None) -> dict:
    """
    Produces a stable, reader-safe event summary regardless of event type.

    Always returns a dict with the same keys. Absent or None inputs produce
    an empty-but-valid structure; no key is ever missing. Raw engine dicts
    are not forwarded—only the subset relevant to context consumers is kept.
    """
    if not isinstance(event, dict):
        return {
            "label": "",
            "event_type": "",
            "peak_date": "",
            "transit_planet": "",
            "aspect": "",
            "natal_target": "",
            "natal_house": 0,
            "score": 0.0,
            "character": "",
        }
    return {
        "label": _personal_forecast_event_label(event),
        "event_type": event.get("event_type", ""),
        "peak_date": event.get("peak_date") or event.get("entry_date") or "",
        "transit_planet": event.get("transit_planet", ""),
        "aspect": event.get("aspect", ""),
        "natal_target": event.get("natal_target", ""),
        "natal_house": _personal_forecast_event_house(event),
        "score": _personal_forecast_score(event),
        "character": _personal_forecast_character(event),
    }


def _build_personal_forecast_context(
    variables: dict,
    index_results: dict,
    payload: dict,
    report_start: datetime | None = None,
    content_pack: str = "plainspeak",
) -> dict:
    """
    Assembles the complete 90-day Personal Forecast template context.

    Selection order:
      1. Transit engine produces dated, scored events.
      2. Existing selector logic groups them into the strongest life themes.
      3. EO_Standard_Personal_Forecast_Blocks.json synthesizes those themes
         into template-ready snapshot, cards, timing language, guidance, and
         closing integration.
    """
    from config import CONTENT_PACKS, HOUSE_DOMAINS
    from engine.transit_engine import compute_year_ahead_events

    start_date = report_start or datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=90)

    pack = CONTENT_PACKS.get(content_pack) or CONTENT_PACKS["entangled_oracle"]
    block_path = pack.get("personal_forecast")
    if not block_path:
        block_path = CONTENT_PACKS["entangled_oracle"]["personal_forecast"]
    blocks = _load_personal_forecast_blocks(block_path)

    _log_verbose("[Timeline] Scanning 90-day personal forecast events...")
    timeline = compute_year_ahead_events(
        payload,
        start_date=start_date,
        end_date=end_date,
        include_moon_progressions=True,
    )
    all_events = timeline.get("all_events", [])
    predictive_evidence_events = (
        all_events
        + timeline.get("return_events", [])
        + timeline.get("zodiacal_releasing_events", [])
        + timeline.get("time_lord_periods", [])
    )
    forecast_synthesis = build_forecast_synthesis(
        predictive_evidence_events,
        report_start=start_date,
        report_end=end_date,
        house_domains=HOUSE_DOMAINS,
    )

    counts = {"transits": 0, "ingresses": 0, "stations": 0, "eclipses": 0, "other": 0}
    count_keys = {
        "transit": "transits",
        "ingress": "ingresses",
        "station": "stations",
        "eclipse": "eclipses",
    }
    for event in all_events:
        count_key = count_keys.get(event.get("event_type", ""), "other")
        counts[count_key] += 1

    _log_verbose(f"[Timeline] Found {len(all_events)} events in 90 days:")
    _log_verbose(f"  - Transits: {counts['transits']}")
    _log_verbose(f"  - Ingresses: {counts['ingresses']}")
    _log_verbose(f"  - Stations: {counts['stations']}")
    _log_verbose(f"  - Eclipses: {counts['eclipses']}")

    # Retrograde cluster climate note: is a stretch of 2+ simultaneous
    # retrogrades active right now (at report_start)? Additive/optional —
    # any failure here is non-fatal and simply omits the section.
    retrograde_cluster_active = False
    retrograde_cluster_tier = ""
    retrograde_cluster_planets = []
    retrograde_cluster_block = ""
    try:
        from engine.transit_engine import detect_retrograde_clusters
        from selectors.block_selector import select_block
        clusters = detect_retrograde_clusters(payload, start_date, end_date)
        current_cluster = next(
            (c for c in clusters if c["start"] <= start_date <= c["end"]),
            None,
        )
        if current_cluster:
            retrograde_cluster_active = True
            retrograde_cluster_tier = current_cluster["tier"]
            retrograde_cluster_planets = current_cluster["planets"]
            variant_index = sum(ord(ch) for ch in "".join(retrograde_cluster_planets)) % 3
            variant_key = ["v1", "v2", "v3"][variant_index]
            retrograde_cluster_block = _usable_block(
                select_block(
                    "personal_forecast", "retrograde_cluster_blocks",
                    retrograde_cluster_tier, variant_key,
                    fallback=select_block("personal_forecast", "retrograde_cluster_blocks", "fallback"),
                )
            )
    except Exception as retrograde_cluster_error:
        print(f"[RetrogradeCluster] Skipped (non-fatal): {retrograde_cluster_error}")

    # Void-of-Course Moon note: the next (or currently active) VOC window
    # from report_start. Unlike the retrograde climate note above, VOC
    # windows are hours long rather than months long, so a "current
    # snapshot" would usually already be over by the time the report is
    # read — a forward-looking "next window" is more useful here.
    # Additive/optional — any failure here is non-fatal and simply omits
    # the section.
    voc_next_active = False
    voc_next_tier = ""
    voc_next_start = None
    voc_next_duration_hours = 0.0
    voc_next_block = ""
    try:
        from engine.transit_engine import detect_void_of_course_windows
        from selectors.block_selector import select_block
        voc_windows = detect_void_of_course_windows(start_date, end_date)
        next_voc = next(
            (w for w in voc_windows if w["end"] >= start_date),
            None,
        )
        if next_voc:
            voc_next_active = True
            voc_next_tier = next_voc["tier"]
            voc_next_start = next_voc["start"]
            voc_next_duration_hours = next_voc["duration_hours"]
            variant_index = int(next_voc["duration_hours"] * 10) % 3
            variant_key = ["v1", "v2", "v3"][variant_index]
            voc_next_block = _usable_block(
                select_block(
                    "personal_forecast", "void_of_course_moon_blocks",
                    voc_next_tier, variant_key,
                    fallback=select_block("personal_forecast", "void_of_course_moon_blocks", "fallback"),
                )
            )
    except Exception as voc_error:
        print(f"[VoidOfCourse] Skipped (non-fatal): {voc_error}")

    raw_themes = _group_into_themes(all_events)
    theme_metadata = blocks["theme_metadata"]
    theme_cards = []

    for raw_theme in raw_themes:
        theme_key = _personal_forecast_theme_key(raw_theme["theme_key"])
        character = _personal_forecast_character(raw_theme["anchor_event"])
        card = blocks["theme_cards"].get(theme_key, {}).get(character)
        # A missing card leaves prose fields empty but does not drop the theme.
        # This ensures every grouped theme appears in the context with a
        # consistent shape even when synthesis blocks are not yet authored.

        theme_cards.append({
            "theme_key": theme_key,
            "theme_label": theme_metadata.get(theme_key, {}).get("label", raw_theme["theme_label"]),
            "title": card["title"] if card else "",
            "body": card["body"] if card else "",
            "action": card["action"] if card else "",
            "anchor_event": _normalize_forecast_event(raw_theme["anchor_event"]),
            "supporting_events": [
                _normalize_forecast_event(e) for e in raw_theme["supporting_events"]
            ],
            "theme_score": raw_theme["theme_score"],
            "character": character,
        })

    opening_blocks = blocks["opening_snapshot"]
    fallback_opening = opening_blocks["fallback"]

    if theme_cards:
        dominant_theme = theme_cards[0]
        dominant_key = dominant_theme["theme_key"]
        dominant_character = dominant_theme["character"]
        dominant_text = opening_blocks["dominant"].get(dominant_key, {}).get(
            dominant_character,
            fallback_opening["dominant"],
        )
        development_text = opening_blocks["dominant_development"].get(dominant_key, {}).get(
            dominant_character,
            "",
        )
        closing_reframe = theme_metadata.get(dominant_key, {}).get(
            "closing_reframe",
            "making room for what is true and sustainable",
        )
    else:
        dominant_theme = None
        dominant_key = ""
        dominant_character = "flowing"
        dominant_text = fallback_opening["dominant"]
        development_text = ""
        closing_reframe = "making room for what is true and sustainable"

    if len(theme_cards) >= 2:
        secondary_theme = theme_cards[1]
        secondary_text = opening_blocks["secondary"].get(secondary_theme["theme_key"], {}).get(
            secondary_theme["character"],
            fallback_opening["secondary"],
        )
    else:
        secondary_text = fallback_opening["secondary"]

    opening_parts = [part for part in (dominant_text, development_text, secondary_text) if part]
    if len(theme_cards) >= 3:
        relational_theme = theme_cards[2]
        relational_text = opening_blocks["relational"].get(relational_theme["theme_key"], {}).get(
            relational_theme["character"],
            fallback_opening["relational"],
        )
        if relational_text:
            opening_parts.append(relational_text)
    opening_parts.append(opening_blocks["closing_template"].format(closing_reframe=closing_reframe))
    opening_snapshot = " ".join(opening_parts)

    featured_raw = raw_themes[0]["anchor_event"] if raw_themes else None
    if featured_raw is None and all_events:
        featured_raw = max(all_events, key=_personal_forecast_score)

    featured_event = None
    if featured_raw:
        featured_house = _personal_forecast_event_house(featured_raw)
        featured_character = _personal_forecast_character(featured_raw)
        featured_core = blocks["featured_event"]["domain_core"].get(
            str(featured_house),
            blocks["featured_event"]["fallback"],
        )
        featured_event = {
            "peak_date": featured_raw.get("peak_date") or featured_raw.get("entry_date") or "",
            "title": featured_core["title"],
            "body_1": featured_core["body_1"],
            "body_2": blocks["featured_event"]["character_adjustment"].get(
                featured_character,
                "",
            ),
            # Existing event-level blocks are intentionally not appended here:
            # they are full paragraphs and would duplicate the synthesis card.
            "body_3": None,
            "action": featured_core["action"],
        }

    timing_windows = []
    featured_identity = _personal_forecast_event_identity(featured_raw) if featured_raw else None
    for event in _select_personal_forecast_timing_events(all_events, featured_raw):
        house = _personal_forecast_event_house(event)
        character = _personal_forecast_character(event)
        timing_source = blocks["timing_windows"].get(str(house), blocks["timing_windows"]["fallback"])
        timing_copy = timing_source.get(character, blocks["timing_windows"]["fallback"][character])
        timing_windows.append({
            "date_label": event.get("peak_date") or event.get("entry_date") or "",
            "theme": timing_copy["theme"],
            "best_use": timing_copy["best_use"],
            "intensity": _personal_forecast_intensity(_personal_forecast_score(event)),
            "featured": _personal_forecast_event_identity(event) == featured_identity,
            "timeline_position_pct": _personal_forecast_timeline_position_pct(
                event,
                start_date,
                end_date,
            ),
            "ranking_diagnostics": _event_ranking_diagnostics(
                event,
                context="personal_forecast_timing_window",
                rank_score=_personal_forecast_rank_score(event),
                rank_basis="combined_intensity_score_plus_type_bonus",
            ),
        })

    guidance = blocks["guidance"]
    guidance_focus = guidance["theme_focus"].get(dominant_key, guidance["fallback"])
    guidance_adjustment = guidance["character_adjustment"].get(dominant_character, {})
    guidance_context = {
        "guidance_professional": " ".join(filter(None, (
            guidance_focus.get("professional"), guidance_adjustment.get("professional")
        ))),
        "guidance_relationships": " ".join(filter(None, (
            guidance_focus.get("relationships"), guidance_adjustment.get("relationships")
        ))),
        "guidance_capacity": " ".join(filter(None, (
            guidance_focus.get("capacity"), guidance_adjustment.get("capacity")
        ))),
    }

    closing_blocks = blocks["closing_integration"]
    closing_core = closing_blocks["theme_core"].get(dominant_key, closing_blocks["fallback"])
    closing_finish = closing_blocks["character_finish"].get(dominant_character, "")
    closing_integration = " ".join(filter(None, (closing_core, closing_finish)))

    birth_meta = _build_birth_metadata(payload)
    methodology = _build_methodology_metadata(payload, variables)
    birth_time_status = birth_meta["birth_time_status"]
    timeline_json = json.dumps(timeline, indent=2, default=str)

    chart_wheel_data = None
    chart_wheel_svg = ""
    wheel_transit_retrograde_planets = []
    if _has_exact_birth_time(payload):
        try:
            from engine.chart_wheel import build_chart_wheel_data, render_natal_wheel_svg
            from engine.transit_engine import current_retrograde_planets
            transit_rx = current_retrograde_planets(start_date)
            chart_wheel_data = build_chart_wheel_data(
                payload, report_type="personal_forecast", current_retrograde=transit_rx
            )
            if chart_wheel_data:
                chart_wheel_svg = render_natal_wheel_svg(chart_wheel_data, compact=True)
                wheel_transit_retrograde_planets = sorted(
                    b["name"] for b in chart_wheel_data.get("bodies", [])
                    if b.get("currently_retrograde")
                )
        except Exception as chart_wheel_error:
            print(f"[ChartWheel] Skipped (non-fatal): {chart_wheel_error}")

    from config import PALETTES as _PALETTES
    _pf_palette_name = variables.get("palette", "vibrant")
    _pf_palette = _PALETTES.get(_pf_palette_name, _PALETTES["vibrant"])

    return {
        "report_start_display": start_date.strftime("%B %d, %Y"),
        "report_end_display": end_date.strftime("%B %d, %Y"),
        "birth_date_display": birth_meta["birth_date_display"],
        "birth_time_display": birth_meta["birth_time_display"],
        "birth_location": payload.get("birth_location") or payload.get("location") or birth_meta["birth_location"],
        "event_counts": counts,
        "total_events": len(all_events),
        "opening_snapshot": opening_snapshot,
        "themes": theme_cards,
        "timing_windows": timing_windows,
        "featured_event": featured_event,
        **guidance_context,
        "closing_integration": closing_integration,
        "birth_time_status": birth_time_status,
        "birth_time_state": birth_meta["birth_time_state"],
        **methodology,
        "timeline_data_json": timeline_json,
        "chart_wheel_data": chart_wheel_data,
        "chart_wheel_svg": chart_wheel_svg,
        "wheel_transit_retrograde_planets": wheel_transit_retrograde_planets,
        "palette_name":        _pf_palette_name,
        "palette":             _pf_palette,
        "predictive_results":  variables.get("predictive_results", {}),
        "forecast_synthesis":  forecast_synthesis,
        "predictive_report_surface": _build_predictive_report_surface(
            variables.get("predictive_sidecar", {}),
            "personal_forecast",
            forecast_synthesis,
            pack,
        ),
        "retrograde_cluster_active":  retrograde_cluster_active,
        "retrograde_cluster_tier":    retrograde_cluster_tier,
        "retrograde_cluster_planets": retrograde_cluster_planets,
        "retrograde_cluster_block":   retrograde_cluster_block,
        "voc_next_active":         voc_next_active,
        "voc_next_tier":           voc_next_tier,
        "voc_next_start_display":  voc_next_start.strftime("%B %d, %Y, %I:%M %p UTC") if voc_next_start else "",
        "voc_next_duration_hours": voc_next_duration_hours,
        "voc_next_block":          voc_next_block,
    }

def _build_horoscope_context(variables, index_results, payload) -> dict:
    from selectors.block_selector import select_block
    v = variables
    ctx = {}

    # Today's Sky block
    ctx["todays_sky_block"] = select_block(
        "daily_horoscope", "todays_sky",
        _moon_phase_key(v.get("moon_phase_descriptor", "")),
        v.get("sky_moon_sign_element") or v.get("moon_sign_element", "fallback")
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

    # Proprietary Reference block — uses EAS ordering (NGE, not legacy MAGNETIC)
    dominant_idx = v.get("dominant_eas_dimension", "fallback")
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

    # ── Secondary Activation Hook ──────────────────────────────────────────────
    # secondary_activation_line is intentionally blank at this stage.
    # The resolver sets it to "" as a safe default (variable_resolver.py).
    # When an approved activation rule is ready, populate it HERE by replacing
    # this passthrough with a call to the new rule:
    #
    #   ctx["secondary_activation_line"] = _compute_secondary_activation(v, payload)
    #
    # Until then, this passthrough preserves the resolver's blank value and
    # ensures the key is always present in the horoscope context dict.
    ctx["secondary_activation_line"] = v.get("secondary_activation_line", "")

    from config import PALETTES as _PALETTES
    _h_palette_name = variables.get("palette", "vibrant")
    ctx["palette_name"] = _h_palette_name
    ctx["palette"] = _PALETTES.get(_h_palette_name, _PALETTES["vibrant"])

    return ctx


def _build_weekly_horoscope_context(
    variables: dict,
    index_results: dict,
    payload: dict,
    report_start: datetime | None = None,
    report_end: datetime | None = None,
) -> dict:
    """
    Foundational Weekly Horoscope context.

    Reuses the same Today's Timeline engine that Daily Horoscope's engine
    layer already ships (compute_daily_timeline), pointed at a 7-day window
    instead of a single day — the function is date-range-agnostic, so no
    engine changes were needed to generalize it to a week.

    Content blocks are intentionally not wired here yet (out of scope for
    this pass). This only assembles the computed timeline moments and the
    simple/exact-birth-time gating so a template and block library can be
    built on top of a working data layer.
    """
    from engine.transit_engine import compute_daily_timeline
    from config import PALETTES as _PALETTES

    v = variables
    report_start = report_start or _align_to_week_start(datetime.now(timezone.utc))
    report_end = report_end or (report_start + timedelta(days=5))
    simple_mode = bool(payload.get("simple_mode") or v.get("simple_mode"))

    _log_verbose("[Timeline] Scanning 7-day window for weekly moments...")
    raw_moments = compute_daily_timeline(
        payload,
        day_start=report_start,
        day_end=report_end,
        count=10,
        include_angles=not simple_mode,
    )
    raw_moments = sorted(
        raw_moments,
        key=lambda moment: moment.get("peak_datetime") or datetime.max.replace(tzinfo=timezone.utc),
    )

    weekly_timeline = []
    for moment in raw_moments:
        peak_dt = moment.get("peak_datetime")
        time_label = peak_dt.strftime("%I:%M %p UTC").lstrip("0") if peak_dt else ""
        weekly_timeline.append({
            "day_label": peak_dt.strftime("%A, %B %d") if peak_dt else "",
            "time_label": time_label,
            "peak_datetime": peak_dt.isoformat() if peak_dt else "",
            "transit_planet": moment.get("transit_planet", ""),
            "aspect": moment.get("aspect", ""),
            "aspect_character": moment.get("aspect_character", ""),
            "natal_target": moment.get("natal_target", ""),
            "natal_target_display": moment.get("natal_target_display", ""),
            "natal_house": moment.get("natal_house", ""),
            "score": moment.get("score", 0),
        })

    _palette_name = v.get("palette", "vibrant")

    return {
        "simple_mode": simple_mode,
        "week_start_display": report_start.strftime("%B %d, %Y"),
        # report_end is the exclusive window boundary (Saturday 00:00 UTC for a
        # Mon-Fri window) — display the actual last covered day, Friday.
        "week_end_display": (report_end - timedelta(days=1)).strftime("%B %d, %Y"),
        "weekly_timeline": weekly_timeline,
        "weekly_timeline_count": len(weekly_timeline),
        "weekly_timeline_mode": "chronological_selected_exact_contacts",
        "weekly_scope_note": "Selected exact contacts, shown in chronological order.",
        "palette_name": _palette_name,
        "palette": _PALETTES.get(_palette_name, _PALETTES["vibrant"]),
    }


def _safe_mapping(value) -> dict:
    return value if isinstance(value, dict) else {}


def _safe_sequence(value) -> list:
    return value if isinstance(value, list) else []


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _resolver_index_activation_score(variables: dict, index_key: str) -> float:
    return _safe_float(variables.get(f"{str(index_key or '').lower()}_activation_score"), 0.0)


def _soul_ecosystem_eas_entry(
    slot: str,
    index_key: str,
    titles: dict[str, str],
    variables: dict,
    index_results: dict,
    *,
    fallback_name: str = "",
    fallback_score: float = 0.0,
    fallback_archetype: str = "",
    fallback_expression: str = "",
) -> dict:
    record = _safe_mapping(index_results.get(index_key, {})) if index_key else {}
    components = _safe_mapping(record.get("components", {}))
    title = titles.get(index_key, fallback_name or "")
    score = _safe_float(record.get("score"), fallback_score)
    activation_score = _safe_float(
        record.get("activation_score"),
        _resolver_index_activation_score(variables, index_key),
    )
    archetype = str(record.get("archetype") or fallback_archetype or "")
    expression = str(record.get("expression") or fallback_expression or "")
    activation = str(record.get("activation") or "")
    driver_body = str(record.get("driver_body") or "")
    driver_modality = str(record.get("driver_modality") or "")
    available = bool(index_key) and bool(
        record or title or archetype or expression or score or activation_score
    )

    nge_secondary_body = ""
    nge_secondary_facet = ""
    if index_key == "NGE":
        nge_secondary_body = str(record.get("secondary_body") or variables.get("nge_secondary_body") or "")
        nge_secondary_facet = str(record.get("secondary_facet") or variables.get("nge_secondary_facet") or "")

    return {
        "slot": slot,
        "available": available,
        "index": index_key or "",
        "title": title,
        "score": score,
        "activation_score": activation_score,
        "archetype": archetype,
        "expression": expression,
        "activation": activation,
        "driver": {
            "body": driver_body,
            "modality": driver_modality,
        },
        "components": components,
        "nge": {
            "dominant_facet": str(record.get("dominant_facet") or ""),
            "narrative_question": str(record.get("narrative_question") or ""),
            "secondary_body": nge_secondary_body,
            "secondary_facet": nge_secondary_facet,
        },
    }


def _build_soul_ecosystem_depth_payload(
    variables: dict,
    index_results: dict,
    titles: dict[str, str],
    dominant_index: str,
) -> dict:
    dominant = _soul_ecosystem_eas_entry(
        "dominant",
        dominant_index,
        titles,
        variables,
        index_results,
        fallback_name=titles.get(dominant_index, ""),
    )
    secondary = _soul_ecosystem_eas_entry(
        "secondary",
        str(variables.get("secondary_eas_dimension") or ""),
        titles,
        variables,
        index_results,
        fallback_name=str(variables.get("secondary_eas_dimension_name") or ""),
        fallback_score=_safe_float(variables.get("secondary_eas_dimension_score"), 0.0),
        fallback_archetype=str(variables.get("secondary_eas_dimension_archetype") or ""),
        fallback_expression=str(variables.get("secondary_eas_dimension_expression") or ""),
    )
    tertiary = _soul_ecosystem_eas_entry(
        "tertiary",
        str(variables.get("tertiary_eas_dimension") or ""),
        titles,
        variables,
        index_results,
        fallback_name=str(variables.get("tertiary_eas_dimension_name") or ""),
        fallback_score=_safe_float(variables.get("tertiary_eas_dimension_score"), 0.0),
        fallback_archetype=str(variables.get("tertiary_eas_dimension_archetype") or ""),
        fallback_expression=str(variables.get("tertiary_eas_dimension_expression") or ""),
    )

    return {
        "dominant": dominant,
        "secondary": secondary,
        "tertiary": tertiary,
        "available_slots": [
            entry["slot"]
            for entry in (dominant, secondary, tertiary)
            if entry.get("available")
        ],
        "has_optional_depth": bool(secondary.get("available") or tertiary.get("available")),
    }


def _build_soul_ecosystem_context(variables, index_results, payload) -> dict:
    import os as _os
    from selectors.block_selector import select_block_traced
    from engine.chart_wheel import build_chart_wheel_data, render_natal_wheel_svg

    v = variables
    birth_meta = _build_birth_metadata(payload)
    methodology = _build_methodology_metadata(payload, v)
    birth_time_status = birth_meta["birth_time_status"]

    # Development-only selection trace. Set SE_TRACE=1 in the environment to
    # write a sidecar JSON manifest for every block selected in this report.
    _SE_TRACE = _os.environ.get("SE_TRACE", "0") == "1"
    _se_trace_log = []

    def _tsel(field, file, *keys, inputs=None):
        """Traced select_block wrapper. Records resolution details when SE_TRACE=1."""
        text, resolved, fallback_used = select_block_traced("soul_ecosystem", file, *keys)
        if _SE_TRACE:
            _se_trace_log.append({
                "field": field,
                "block_file": f"blocks/soul_ecosystem/{file}.json",
                "requested_key_path": list(keys),
                "resolved_key_path": resolved,
                "fallback_used": fallback_used,
                "selector_inputs": inputs or {},
            })
        # select_block_traced can return literal "[BLOCK NOT FOUND: ...]" /
        # "[MISSING BLOCK FILE: ...]" markers with no filtering of its own —
        # scrub those (and any stray [TODO] markers) before they reach the template.
        return _usable_block(text)

    chart_wheel_data = None
    chart_wheel_svg = ""
    wheel_transit_retrograde_planets = []
    if _has_exact_birth_time(payload):
        try:
            from engine.transit_engine import current_retrograde_planets
            transit_rx = current_retrograde_planets()
            chart_wheel_data = build_chart_wheel_data(
                payload, "soul_ecosystem", current_retrograde=transit_rx
            )
            if chart_wheel_data:
                chart_wheel_svg = render_natal_wheel_svg(chart_wheel_data)
                wheel_transit_retrograde_planets = sorted(
                    b["name"] for b in chart_wheel_data.get("bodies", [])
                    if b.get("currently_retrograde")
                )
        except Exception as _cw_err:
            print(f"[ChartWheel] Skipped (non-fatal): {_cw_err}")

    ctx = {}

    ctx["souls_story_block"] = _tsel(
        "souls_story_block", "souls_story",
        v.get("sun_moon_relationship", "unaspected"),
        v.get("dominant_element", "fallback"),
        inputs={"sun_moon_relationship": v.get("sun_moon_relationship"),
                "dominant_element": v.get("dominant_element")},
    )
    ctx["south_node_sign_block"] = _tsel(
        "south_node_sign_block", "south_node_sign",
        v.get("south_node_sign", "fallback"),
        inputs={"south_node_sign": v.get("south_node_sign")},
    )
    ctx["south_node_house_block"] = _tsel(
        "south_node_house_block", "south_node_house",
        str(v.get("south_node_house", "fallback")),
        inputs={"south_node_house": v.get("south_node_house")},
    )
    ctx["saturn_block"] = _tsel(
        "saturn_block", "saturn_sign",
        v.get("saturn_sign", "fallback"),
        inputs={"saturn_sign": v.get("saturn_sign")},
    )
    ctx["pluto_generation_block"] = _tsel(
        "pluto_generation_block", "pluto_generation",
        v.get("pluto_sign", "fallback"),
        inputs={"pluto_sign": v.get("pluto_sign")},
    )

    # 12th house (conditional)
    ctx["twelfth_house_blocks"] = []
    for _planet in v.get("planets_in_12th", [])[:2]:
        _block_text, _resolved, _fb = select_block_traced(
            "soul_ecosystem", "twelfth_house_planets", _planet
        )
        if _SE_TRACE:
            _se_trace_log.append({
                "field": f"twelfth_house_blocks[{_planet}]",
                "block_file": "blocks/soul_ecosystem/twelfth_house_planets.json",
                "requested_key_path": [_planet],
                "resolved_key_path": _resolved,
                "fallback_used": _fb,
                "selector_inputs": {"planet": _planet},
            })
        ctx["twelfth_house_blocks"].append({"planet": _planet, "block": _block_text})

    # Ancestral layer (conditional)
    ahl = _safe_mapping(index_results.get("AHL", {}))
    if ahl.get("fires"):
        ctx["ancestral_block"] = _tsel(
            "ancestral_block", "ancestral_layer",
            ahl.get("tier", "PRESENT"),
            inputs={"ahl_tier": ahl.get("tier"), "ahl_fires": ahl.get("fires")},
        )
    else:
        ctx["ancestral_block"] = None

    ctx["north_node_sign_block"] = _tsel(
        "north_node_sign_block", "north_node_sign",
        v.get("north_node_sign", "fallback"),
        inputs={"north_node_sign": v.get("north_node_sign")},
    )
    ctx["north_node_house_block"] = _tsel(
        "north_node_house_block", "north_node_house",
        str(v.get("north_node_house", "fallback")),
        inputs={"north_node_house": v.get("north_node_house")},
    )
    ctx["midheaven_block"] = _tsel(
        "midheaven_block", "midheaven",
        v.get("mc_sign", "fallback"),
        inputs={"mc_sign": v.get("mc_sign")},
    )
    ctx["jupiter_block"] = _tsel(
        "jupiter_block", "jupiter_sign",
        v.get("jupiter_sign", "fallback"),
        inputs={"jupiter_sign": v.get("jupiter_sign")},
    )
    ctx["sun_moon_integration_block"] = _tsel(
        "sun_moon_integration_block", "sun_moon_integration",
        v.get("sun_sign_element", "fallback"),
        v.get("moon_sign_element", "fallback"),
        v.get("sun_moon_aspect_character", "unaspected"),
        inputs={"sun_sign_element": v.get("sun_sign_element"),
                "moon_sign_element": v.get("moon_sign_element"),
                "sun_moon_aspect_character": v.get("sun_moon_aspect_character")},
    )
    ctx["chiron_block"] = _tsel(
        "chiron_block", "chiron_house",
        str(v.get("chiron_house", "fallback")),
        inputs={"chiron_house": v.get("chiron_house")},
    )

    # ── Proprietary EAS routing ──────────────────────────────────
    # Maps all active primary indexes to their Soul Ecosystem display titles.
    # NGE uses "Narrative Current" here (vs. "Narrative Gravity" used by other
    # reports) because the Soul Ecosystem framing emphasises ongoing story voice.
    _SE_EAS_TITLES = {
        "KVQ":      "Your Foresight Pattern",
        "MKI":      "Your Knowledge Legacy",
        "RWI":      "Your Reality Field",
        "DFIS":     "Your Power Current",
        "CATALYST": "Your Impact Radius",
        "NGE":      "Your Narrative Current",
    }

    # One dedicated block file per index. No longer routes non-MKI indexes
    # through the legacy impact_pattern.json (which only held CATALYST and KVQ).
    _SE_EAS_BLOCK_FILES = {
        "KVQ":      "foresight_pattern",
        "MKI":      "knowledge_legacy",
        "RWI":      "reality_field",
        "DFIS":     "power_current",
        "CATALYST": "impact_radius",
        "AHL":      "ancestral_thread",
        "NGE":      "narrative_current",
    }

    soul_idx = v.get("soul_ecosystem_dominant_index", "MKI")
    if soul_idx not in _SE_EAS_TITLES:
        soul_idx = "MKI"

    soul_data     = _safe_mapping(index_results.get(soul_idx, {}))
    archetype_raw = str(soul_data.get("archetype") or "fallback")
    archetype_key = archetype_raw.lower().replace(" ", "_").replace("/", "_")
    tier          = str(soul_data.get("tier") or "SUBTLE")

    ctx["proprietary_section_title"] = _SE_EAS_TITLES.get(soul_idx, "Your Knowledge Legacy")

    _prop_file  = _SE_EAS_BLOCK_FILES.get(soul_idx, "knowledge_legacy")
    _blocks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blocks", "soul_ecosystem")

    if soul_idx == "NGE" and not os.path.exists(
        os.path.join(_blocks_dir, "narrative_current.json")
    ):
        # narrative_current.json not yet authored. Preserve the visible generic
        # fallback text from impact_pattern but flag the trace as MISSING_NGE_LIBRARY.
        _fallback_text, _, _ = select_block_traced("soul_ecosystem", "impact_pattern", "fallback")
        ctx["proprietary_section_block"] = _fallback_text
        if _SE_TRACE:
            _se_trace_log.append({
                "field": "proprietary_section_block",
                "block_file": "blocks/soul_ecosystem/narrative_current.json",
                "requested_key_path": [archetype_key, tier.lower()],
                "resolved_key_path": ["MISSING_NGE_LIBRARY"],
                "fallback_used": True,
                "selector_inputs": {
                    "soul_ecosystem_dominant_index": soul_idx,
                    "archetype": archetype_raw,
                    "archetype_key": archetype_key,
                    "tier": tier,
                    "note": "narrative_current.json not found in blocks/soul_ecosystem/",
                },
            })
    else:
        if soul_idx == "NGE":
            # NGE library schema: genre_key → activation_key → text.
            # Uses genre (narrative category) and activation level, not tier.
            _nge_genre_raw = str(soul_data.get("genre") or archetype_raw)
            _nge_genre_key = _nge_genre_raw.lower().replace(" ", "_").replace("/", "_")
            _nge_activation = str(soul_data.get("activation") or "fallback").lower()
            _prop_keys = (_nge_genre_key, _nge_activation)
            _trace_inputs = {
                "soul_ecosystem_dominant_index": soul_idx,
                "nge_genre": _nge_genre_raw,
                "nge_genre_key": _nge_genre_key,
                "activation": soul_data.get("activation"),
                "tier": tier,
                "block_file": _prop_file,
            }
        elif soul_idx == "KVQ":
            _prop_keys = ("subtle",) if tier == "SUBTLE" else (archetype_key,)
            _trace_inputs = {
                "soul_ecosystem_dominant_index": soul_idx,
                "archetype": archetype_raw,
                "archetype_key": archetype_key,
                "tier": tier,
                "block_file": _prop_file,
            }
        elif tier == "SUBTLE":
            # Non-NGE SUBTLE: route to root "subtle" key in the per-index library.
            _prop_keys = ("subtle",)
            _trace_inputs = {
                "soul_ecosystem_dominant_index": soul_idx,
                "archetype": archetype_raw,
                "archetype_key": archetype_key,
                "tier": tier,
                "block_file": _prop_file,
            }
        else:
            # Non-NGE DOMINANT or PRESENT: archetype_key → tier_lowercase → text.
            _prop_keys = (archetype_key, tier.lower())
            _trace_inputs = {
                "soul_ecosystem_dominant_index": soul_idx,
                "archetype": archetype_raw,
                "archetype_key": archetype_key,
                "tier": tier,
                "block_file": _prop_file,
            }

        ctx["proprietary_section_block"] = _tsel(
            "proprietary_section_block", _prop_file, *_prop_keys,
            inputs=_trace_inputs,
        )

    # Dominant EAS index context — available to templates and future block routing.
    ctx["soul_ecosystem_eas_index"]                  = soul_idx
    ctx["soul_ecosystem_eas_title"]                  = _SE_EAS_TITLES.get(soul_idx, "")
    ctx["soul_ecosystem_eas_archetype"]              = soul_data.get("archetype", "")
    ctx["soul_ecosystem_eas_expression"]             = soul_data.get("expression", "")
    ctx["soul_ecosystem_eas_activation"]             = soul_data.get("activation", "")
    ctx["soul_ecosystem_eas_driver_body"]            = soul_data.get("driver_body", "")
    ctx["soul_ecosystem_eas_driver_modality"]        = soul_data.get("driver_modality", "")
    ctx["soul_ecosystem_eas_score"]                  = soul_data.get("score", 0.0)
    ctx["soul_ecosystem_eas_components"]             = soul_data.get("components", {})
    ctx["soul_ecosystem_eas_nge_dominant_facet"]     = soul_data.get("dominant_facet", "") if soul_idx == "NGE" else ""
    ctx["soul_ecosystem_eas_nge_narrative_question"] = soul_data.get("narrative_question", "") if soul_idx == "NGE" else ""
    ctx["soul_ecosystem_eas_depth"] = _build_soul_ecosystem_depth_payload(
        v,
        index_results,
        _SE_EAS_TITLES,
        soul_idx,
    )

    # Archetypes
    ctx["primary_archetype_name"]   = f"The {v.get('mc_sign', '')} Archetype"
    ctx["secondary_archetype_name"] = f"The {v.get('north_node_sign', '')} Archetype"
    ctx["primary_archetype_block"] = _tsel(
        "primary_archetype_block", "archetypal_support",
        "primary", v.get("mc_sign", "fallback"),
        inputs={"archetype_tier": "primary", "mc_sign": v.get("mc_sign")},
    )
    ctx["secondary_archetype_block"] = _tsel(
        "secondary_archetype_block", "archetypal_support",
        "secondary", v.get("north_node_sign", "fallback"),
        inputs={"archetype_tier": "secondary", "north_node_sign": v.get("north_node_sign")},
    )

    # Soul's Promise
    ctx["souls_promise_block"] = _tsel(
        "souls_promise_block", "souls_promise",
        v.get("north_node_element", "fallback"),
        v.get("mc_element", "fallback"),
        inputs={"north_node_element": v.get("north_node_element"),
                "mc_element": v.get("mc_element")},
    )

    # Astrologer's Index — formatted natal position table
    _ANGLE_LABELS = {
        "Ascendant":  "A1",
        "Midheaven":  "A10",
        "Descendant": "A7",
        "Imum_Coeli": "A4",
    }

    def _fmt_natal_row(name: str, data: dict, house_label: str = "") -> str:
        sign  = data.get("sign", "").ljust(14)
        deg   = int(data.get("degree", 0))
        mins  = int(data.get("minute", 0))
        pos   = f"{deg}°{mins:02d}'".ljust(8)
        retro = "Rx" if data.get("retrograde") else ""
        return f"{name.ljust(14)} {sign} {pos} {house_label.ljust(4)} {retro}".rstrip()

    planet_order = [
        "Sun", "Moon", "Mercury", "Venus", "Mars",
        "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
        "Chiron", "North_Node", "South_Node", "Lilith_BML"
    ]
    planets = payload.get("standard_planets", {})
    index_rows = []
    for name in planet_order:
        if name in planets:
            index_rows.append(_fmt_natal_row(name, planets[name],
                                             f"H{planets[name].get('house', '?')}"))

    angles = payload.get("angles", {})
    for angle in ["Ascendant", "Midheaven", "Descendant", "Imum_Coeli"]:
        if angle in angles:
            index_rows.append(_fmt_natal_row(angle, angles[angle],
                                             _ANGLE_LABELS[angle]))

    natal_index_data = "\n".join(index_rows)

    from config import PALETTES as _PALETTES
    _se_palette_name = variables.get("palette", "vibrant")
    ctx.update({
        "birth_time_status":  birth_time_status,
        "birth_time_state":   birth_meta["birth_time_state"],
        "birth_date_display": birth_meta["birth_date_display"],
        "birth_time_display": birth_meta["birth_time_display"],
        "birth_location":     birth_meta["birth_location"],
        **methodology,
        "generation_date":    datetime.now().strftime("%B %d, %Y"),
        "chart_wheel_svg":    chart_wheel_svg,
        "wheel_transit_retrograde_planets": wheel_transit_retrograde_planets,
        "chart_wheel_data":   chart_wheel_data,
        "natal_index_data":   natal_index_data,
        "palette_name":       _se_palette_name,
        "palette":            _PALETTES.get(_se_palette_name, _PALETTES["vibrant"]),
    })

    # Write selection trace sidecar (dev-only, SE_TRACE=1).
    if _SE_TRACE:
        import json as _json
        _querent = v.get("querent_name") or payload.get("name") or "unknown"
        _trace_name = _querent.lower().replace(" ", "_")
        _out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(_out_dir, exist_ok=True)
        _trace_path = os.path.join(_out_dir, f"se_trace_{_trace_name}.json")
        with open(_trace_path, "w", encoding="utf-8") as _tf:
            _json.dump({"querent": _querent, "selections": _se_trace_log}, _tf, indent=2)
        print(f"[SE_TRACE] Written: {_trace_path}")

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

    if not cleaned or re.match(
        r"^\[\s*(TODO|BLOCK NOT FOUND|MISSING BLOCK FILE)\b", cleaned, flags=re.IGNORECASE
    ):
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


_YEAR_AHEAD_SENTENCE_VARIANTS = {
    "supportive": {
        "opening_condition": [
            {
                "prefixes": (
                    "The conditions around ",
                    "There is usable ease here: ",
                    "A lower-friction current opens around ",
                    "There is an opening here, small enough to miss and real enough to matter, in the area of ",
                    "A workable opening appears around ",
                ),
                "variants": (
                    "The workable conditions around ",
                    "A supportive opening develops around ",
                    "There is practical ease around ",
                ),
            },
        ],
        "domain_focus": [
            {
                "prefixes": (
                    "The focus is your ",
                    "Expect the emphasis to land in your ",
                    "Expect the emphasis to land in ",
                ),
                "variants": (
                    "The live emphasis is your ",
                    "Attention gathers around your ",
                    "This current lands most clearly in your ",
                ),
            },
        ],
        "opportunity_resource": [
            {
                "prefixes": (
                    "This is a good time to notice ",
                    "The absence of crisis is part of the resource: ",
                    "That ease is not a guarantee, but ",
                    "The benefit is not a windfall; it is ",
                    "Support can be easy to underuse because ",
                ),
                "variants": (
                    "This is a useful time to notice ",
                    "Part of the resource here is that ",
                    "Ease is not a promise, but ",
                    "The opening is not a windfall; it is ",
                    "Because nothing forces your hand, ",
                ),
            },
        ],
        "caution": [
            {
                "prefixes": (
                    "Keep an eye on ",
                    "The particular caution here is ",
                    "Here, overreach can look like ",
                ),
                "variants": (
                    "Watch for ",
                    "The caution here is ",
                    "In this setting, overreach can look like ",
                ),
            },
        ],
        "practical_action": [
            {
                "prefixes": (
                    "Let this be a season of practical permission: ",
                    "Use the calmer terrain to ",
                    "A modest, well-timed step can ",
                    "Give the invitation a form: ",
                    "Choose a real, proportionate action and ",
                    "Follow the line of least unnecessary resistance, but ",
                ),
                "variants": (
                    "Treat this as a season of practical permission: ",
                    "Use the steadier terrain to ",
                    "A modest, timely step can ",
                    "Give the opening a form: ",
                    "Choose one proportionate action and ",
                    "Follow the least resistant path, but ",
                ),
            },
        ],
    },
    "challenging": {
        "opening_condition": [
            {
                "prefixes": (
                    "What has been manageable in ",
                    "Pressure gathers around ",
                    "The tension here is real: ",
                    "A productive but uncomfortable friction develops around ",
                    "This is a mirror transit for ",
                    "The issue becomes easier to see through contrast: ",
                    "A pull in two directions emerges around ",
                ),
                "variants": (
                    "What has been workable in ",
                    "Pressure is gathering around ",
                    "The friction here is real: ",
                    "A useful but uncomfortable friction develops around ",
                    "This becomes a mirror for ",
                    "Contrast makes the issue easier to see: ",
                    "Two competing pulls emerge around ",
                ),
            },
        ],
        "domain_focus": [
            {
                "prefixes": (
                    "It adds heat, courage, urgency, and a demand for movement, especially through your ",
                    "The focus is your ",
                    "Expect the emphasis to land in your ",
                    "Expect the emphasis to land in ",
                ),
                "variants": (
                    "It adds heat, urgency, and a demand for movement, especially through your ",
                    "The live pressure falls on your ",
                    "The strongest emphasis lands in your ",
                    "This pressure shows up most clearly in ",
                ),
            },
        ],
        "opportunity_resource": [
            {
                "prefixes": (
                    "This is not a verdict and does not require an instant solution. ",
                    "A square can create urgency, but urgency is not the same as clarity; ",
                    "The friction often shows where ",
                    "Oppositions can make projection tempting. ",
                    "The work is not to absorb every external pressure, nor to reject it automatically; ",
                ),
                "variants": (
                    "This is not a verdict, and it does not require an instant solution. ",
                    "A square can create urgency, but urgency is not clarity; ",
                    "The friction often reveals where ",
                    "Oppositions can make projection tempting, so ",
                    "The task is not to absorb every outside pressure or reject it automatically; ",
                ),
            },
        ],
        "caution": [
            {
                "prefixes": (
                    "Here, urgency can look like ",
                    "The particular caution here is ",
                ),
                "variants": (
                    "Here, urgency may look like ",
                    "The caution here is ",
                ),
            },
        ],
        "practical_action": [
            {
                "prefixes": (
                    "Let the pressure sharpen ",
                    "Choose the change that ",
                    "Name the conflict plainly, ",
                    "Work the problem in parts: ",
                    "The aim is balance with agency: ",
                    "A direct conversation, more accurate boundary, or revised plan can ",
                ),
                "variants": (
                    "Let the pressure clarify ",
                    "Choose the shift that ",
                    "Name the conflict directly, ",
                    "Work the problem in parts - ",
                    "The aim is balance with agency, so ",
                    "A direct conversation, clearer boundary, or revised plan can ",
                ),
            },
        ],
    },
    "conjunction": {
        "opening_condition": [
            {
                "prefixes": (
                    "The emphasis tightens: ",
                    "A horizon-expanding current comes into direct contact with ",
                    "This direct contact carries ",
                ),
                "variants": (
                    "The emphasis concentrates: ",
                    "A direct contact forms with ",
                    "This direct contact brings ",
                ),
            },
        ],
        "domain_focus": [
            {
                "prefixes": (
                    "The focus is your ",
                    "Expect the emphasis to land in your ",
                    "Expect the emphasis to land in ",
                ),
                "variants": (
                    "The concentration falls on your ",
                    "This direct emphasis lands in your ",
                    "The strongest emphasis lands in ",
                ),
            },
        ],
        "opportunity_resource": [
            {
                "prefixes": (
                    "Because the signal is strong, ",
                    "This contact can make ",
                ),
                "variants": (
                    "Because the signal is concentrated, ",
                    "This contact can bring ",
                ),
            },
        ],
        "caution": [
            {
                "prefixes": (
                    "Here, overreach can look like ",
                    "Keep an eye on ",
                    "The particular caution here is ",
                ),
                "variants": (
                    "Here, overreach may look like ",
                    "Watch for ",
                    "The caution here is ",
                ),
            },
        ],
        "practical_action": [
            {
                "prefixes": (
                    "Use the concentration to ",
                    "Stay close to the actual facts of your life while ",
                    "The clearest path is ",
                ),
                "variants": (
                    "Use this concentration to ",
                    "Stay close to the actual facts of your life as ",
                    "The clearest move is ",
                ),
            },
        ],
    },
    "ingress": {
        "opening_condition": [
            {
                "patterns": (
                    r"^With (?P<planet>\w+) moving through the (?P<house>\d{1,2}(?:st|nd|rd|th)) house, the current works through (?P<rest>.+)$",
                    r"^The arrival of (?P<planet>\w+) in the (?P<house>\d{1,2}(?:st|nd|rd|th)) house centers (?P<rest>.+)$",
                    r"^As (?P<planet>\w+) enters the (?P<house>\d{1,2}(?:st|nd|rd|th)) house, the focus turns to (?P<rest>.+)$",
                    r"^The active territory becomes (?P<rest>.+) as (?P<planet>\w+) enters the (?P<house>\d{1,2}(?:st|nd|rd|th)) house\.$",
                ),
                "variants": (
                    "{planet} moving through the {house} house brings its emphasis to {rest}",
                    "As {planet} moves through the {house} house, attention gathers around {rest}",
                    "With {planet} in the {house} house, the live territory is {rest}",
                ),
            },
        ],
        "domain_focus": [
            {
                "prefixes": (
                    "Watch the practical movement in ",
                    "The chapter becomes tangible through ",
                    "Look to ",
                ),
                "variants": (
                    "Watch the practical movement through ",
                    "The chapter becomes concrete through ",
                    "Look to ",
                ),
            },
        ],
        "caution": [
            {
                "prefixes": (
                    "Do not let the chapter become louder than it needs to be: ",
                    "Keep an eye on ",
                    "The useful caution is ",
                ),
                "variants": (
                    "Do not let this chapter become louder than it needs to be: ",
                    "Watch for ",
                    "The practical caution is ",
                ),
            },
        ],
        "practical_action": [
            {
                "prefixes": (
                    "Choose the opportunity with genuine capacity behind it; ",
                    "Use repetition to your advantage: ",
                    "Tend the foundation in concrete ways: ",
                    "Reduce friction first. ",
                    "Name the terms in plain language: ",
                    "Bring the practical and emotional terms into the same room; ",
                    "Let conviction meet evidence. ",
                    "Invest in reciprocal participation. ",
                    "Protect time away from performance. ",
                    "Pick the next clean action. ",
                ),
                "variants": (
                    "Choose the opportunity that has real capacity behind it; ",
                    "Use repetition to your advantage - ",
                    "Tend the foundation in concrete ways: ",
                    "Reduce friction first. ",
                    "Name the terms plainly: ",
                    "Bring the practical and emotional terms into the same room; ",
                    "Let conviction meet evidence. ",
                    "Invest in reciprocal participation. ",
                    "Protect time away from performance. ",
                    "Pick the next clean action. ",
                ),
            },
        ],
    },
    "station": {
        "opening_condition": [
            {
                "prefixes": (
                    "A planetary station marks ",
                    "The atmosphere suddenly thickens as ",
                    "The mental fog suddenly lifts, ",
                ),
                "variants": (
                    "A planetary station signals ",
                    "The atmosphere thickens as ",
                    "The mental fog lifts, ",
                ),
            },
        ],
        "domain_focus": [
            {
                "prefixes": (
                    "Matters linked to this planet may ",
                    "Your ",
                ),
                "variants": (
                    "Matters linked to this planet can ",
                    "Your ",
                ),
            },
        ],
        "practical_action": [
            {
                "prefixes": (
                    "Give the shift time to ",
                    "Treat this as a ",
                ),
                "variants": (
                    "Allow the shift time to ",
                    "Treat this as ",
                ),
            },
        ],
    },
    "eclipse": {
        "opening_condition": [
            {
                "prefixes": (
                    "A new direction becomes available around ",
                    "The next chapter is beginning to gather around ",
                    "Something begins to reorient around ",
                    "A solar eclipse begins a new chapter around ",
                    "The contrast sharpens around ",
                    "What has been building around ",
                    "A lunar eclipse brings a point of visibility around ",
                    "An emotional or practical culmination arrives around ",
                ),
                "variants": (
                    "A new direction is opening around ",
                    "The next chapter begins to gather around ",
                    "Something starts to reorient around ",
                    "A solar eclipse opens a new chapter around ",
                    "The contrast becomes sharper around ",
                    "What has been building becomes clearer around ",
                    "A lunar eclipse brings visibility around ",
                    "An emotional or practical culmination gathers around ",
                ),
            },
        ],
        "domain_focus": [
            {
                "prefixes": (
                    "Watch for movement in your ",
                    "The emphasis lands in your ",
                    "The invitation concerns your ",
                    "Pay attention to your ",
                    "The focus is your ",
                ),
                "variants": (
                    "Watch for movement in your ",
                    "The emphasis gathers in your ",
                    "The invitation centers on your ",
                    "Pay attention to your ",
                    "The focus is your ",
                ),
            },
        ],
        "opportunity_resource": [
            {
                "prefixes": (
                    "The first signal may be subtle: ",
                    "This may begin as a small deviation from the expected route, ",
                    "The practical work is to recognize the shift without rushing to name its final outcome. ",
                    "Release does not have to mean rupture. ",
                    "Let the insight settle before turning it into a sweeping conclusion. ",
                    "Let early information remain information. ",
                ),
                "variants": (
                    "The first signal may be subtle - ",
                    "This may begin as a small deviation from the expected route, ",
                    "The practical work is to notice the shift without rushing to name its final outcome. ",
                    "Release does not have to mean rupture. ",
                    "Let the insight settle before making it into a sweeping conclusion. ",
                    "Let early information remain information. ",
                ),
            },
        ],
        "practical_action": [
            {
                "prefixes": (
                    "Give the revelation a practical home: ",
                    "Start with one grounded response. ",
                    "Use what becomes visible to make one honest adjustment. ",
                ),
                "variants": (
                    "Give the revelation a practical home: ",
                    "Begin with one grounded response. ",
                    "Use what becomes visible to make one honest adjustment. ",
                ),
            },
        ],
    },
    "convergence": {
        "opening_condition": [
            {
                "prefixes": (
                    "Several meaningful currents can gather around ",
                    "As multiple lines of attention converge around ",
                    "When several meaningful currents gather here, ",
                    "This convergence can bring questions of ",
                    "When several meaningful currents gather around ",
                ),
                "variants": (
                    "Several meaningful currents may gather around ",
                    "As multiple lines of attention meet around ",
                    "When several meaningful currents gather here, ",
                    "This convergence can bring questions of ",
                    "When several meaningful currents cluster around ",
                ),
            },
        ],
        "practical_action": [
            {
                "prefixes": (
                    "Use the pause to notice ",
                    "Let the presentation match the capacity behind it. ",
                    "Make the practical terms visible. ",
                    "Make a small container for the experiment. ",
                    "Let the update be usable. ",
                    "Reliability is the aim. ",
                ),
                "variants": (
                    "Use the pause to notice ",
                    "Let the presentation match the capacity behind it. ",
                    "Make the practical terms visible. ",
                    "Create a small container for the experiment. ",
                    "Let the update stay usable. ",
                    "Reliability is the aim. ",
                ),
            },
        ],
    },
}


def _year_ahead_event_identity(event: dict) -> str:
    """Builds a stable identity key for deterministic prose variation."""
    parts = [
        event.get("event_type", ""),
        event.get("cycle_id", ""),
        event.get("transit_planet", ""),
        event.get("aspect", ""),
        event.get("natal_target", ""),
        str(event.get("house_number", "")),
        str(event.get("natal_house", "")),
        event.get("station_type", ""),
        event.get("eclipse_type", ""),
        event.get("convergence_pattern", ""),
        event.get("peak_date", ""),
        event.get("entry_date", ""),
        event.get("title", ""),
    ]
    return "|".join(str(part) for part in parts)


def _stable_variant_index(stable_key: str, size: int) -> int:
    if size <= 0:
        return 0
    digest = hashlib.sha256(stable_key.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) % size


def _choose_stable_variant(stable_key: str, variants: tuple[str, ...]) -> str:
    return variants[_stable_variant_index(stable_key, len(variants))]


def _year_ahead_condition_family(event: dict) -> str:
    event_type = event.get("event_type", "")
    if event_type in {"ingress", "station", "eclipse", "convergence"}:
        return event_type

    aspect = event.get("aspect", "")
    if aspect == "Conjunction":
        return "conjunction"
    if aspect in {"Trine", "Sextile"} or event.get("aspect_character") == "flowing":
        return "supportive"
    return "challenging"


def _apply_prefix_variants(
    sentence: str,
    stable_key: str,
    rules: list[dict],
) -> tuple[str, bool]:
    for rule in rules:
        prefixes = tuple(rule.get("prefixes", ()))
        variants = tuple(rule.get("variants", ()))
        indexed_prefixes = sorted(
            enumerate(prefixes),
            key=lambda item: len(item[1]),
            reverse=True,
        )
        for index, prefix in indexed_prefixes:
            if sentence.startswith(prefix):
                if len(variants) == len(prefixes):
                    variant = variants[index]
                else:
                    variant = _choose_stable_variant(
                        f"{stable_key}|prefix|{prefix}",
                        variants,
                    )
                return variant + sentence[len(prefix):], True
    return sentence, False


def _apply_pattern_variants(
    sentence: str,
    stable_key: str,
    rules: list[dict],
) -> tuple[str, bool]:
    for rule in rules:
        for pattern in rule.get("patterns", ()):
            match = re.match(pattern, sentence)
            if not match:
                continue
            template = _choose_stable_variant(
                f"{stable_key}|pattern|{pattern}",
                tuple(rule["variants"]),
            )
            return template.format(**match.groupdict()), True
    return sentence, False


def _apply_year_ahead_prose_variation(text: str, event: dict) -> str:
    """
    Applies deterministic authored scaffold variation to Year Ahead event prose.

    The selected block remains the source of meaning. This layer only varies
    repeated lead constructions and sentence scaffolds using stable event keys.
    """
    cleaned = _usable_block(text)
    if not cleaned:
        return ""

    family = _year_ahead_condition_family(event)
    family_rules = _YEAR_AHEAD_SENTENCE_VARIANTS.get(family, {})
    if not family_rules:
        return cleaned

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", cleaned)
        if sentence.strip()
    ]
    if not sentences:
        return cleaned

    stable_event_key = _year_ahead_event_identity(event)
    varied: list[str] = []

    for index, sentence in enumerate(sentences):
        updated = sentence
        matched = False
        for role, rules in family_rules.items():
            updated, matched = _apply_pattern_variants(
                updated,
                f"{stable_event_key}|{role}|{index}",
                rules,
            )
            if matched:
                break
            updated, matched = _apply_prefix_variants(
                updated,
                f"{stable_event_key}|{role}|{index}",
                rules,
            )
            if matched:
                break
        varied.append(updated)

    return " ".join(varied)

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


_CHART_CHARACTERISTIC_BODIES = [
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
]

_ELEMENT_BY_SIGN = {
    "Aries": "Fire",
    "Leo": "Fire",
    "Sagittarius": "Fire",
    "Taurus": "Earth",
    "Virgo": "Earth",
    "Capricorn": "Earth",
    "Gemini": "Air",
    "Libra": "Air",
    "Aquarius": "Air",
    "Cancer": "Water",
    "Scorpio": "Water",
    "Pisces": "Water",
}

_MODALITY_BY_SIGN = {
    "Aries": "Cardinal",
    "Cancer": "Cardinal",
    "Libra": "Cardinal",
    "Capricorn": "Cardinal",
    "Taurus": "Fixed",
    "Leo": "Fixed",
    "Scorpio": "Fixed",
    "Aquarius": "Fixed",
    "Gemini": "Mutable",
    "Virgo": "Mutable",
    "Sagittarius": "Mutable",
    "Pisces": "Mutable",
}


def _duration_descriptor(event: dict) -> str:
    """Creates a readable timing line for transit-window cards.

    Uses only neutral range language — no 'Exact:', 'Closest approach:',
    'perfection', or similar false-precision wording.  Contact dates from
    the refined solver are available in event['contacts'] for future use
    but are not surfaced here until the display contract is finalized.
    """
    if event.get("event_type") not in {"transit", "eclipse"}:
        return ""

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

    entry_date = event.get("entry_date") or event.get("cycle_start_date") or ""
    leave_date = event.get("leave_date") or event.get("cycle_end_date") or ""

    if in_orb_at_start:
        pieces.append("Already in effect at the start of this forecast")
        if not continues_past_end and leave_date:
            pieces.append(f"through {leave_date}")
    else:
        if entry_date and leave_date:
            pieces.append(f"{entry_date} through {leave_date}")
        elif entry_date:
            pieces.append(f"From {entry_date}")

    if continues_past_end:
        pieces.append("Continues beyond this report")

    if duration and duration > 1:
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


def _year_ahead_primary_event_type(event: dict) -> str:
    raw_type = str(event.get("event_type") or "").strip()
    return _YEAR_AHEAD_EVENT_TYPE_MAP.get(raw_type, raw_type)


def _event_type_matches(event: dict, *types: str) -> bool:
    raw_type = str(event.get("event_type") or "").strip()
    canonical = _YEAR_AHEAD_EVENT_TYPE_MAP.get(raw_type, raw_type)
    accepted = set(types)
    return raw_type in accepted or canonical in accepted


def _iso_date_or_none(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    return text or None


def _ordinary_orb_status(event: dict, primary_type: str) -> str:
    if primary_type in {"house_ingress", "planetary_station", "convergence_window"}:
        return "not_applicable"
    orb = abs(float(event.get("orb", 0.0) or 0.0))
    if orb <= 0.10:
        return "exact"
    if orb <= 1.00:
        return "close"
    return "active_window"


def _ordinary_duration_class(event: dict) -> str:
    duration = float(event.get("duration_days", 0.0) or 0.0)
    if duration >= 90:
        return "sustained"
    if duration >= 21:
        return "moderate"
    return "brief"


def _ordinary_target_class(event: dict) -> str:
    target = str(event.get("natal_target") or "").strip()
    if not target:
        return "not_applicable"
    normalized = _normalize_climate_target(target)
    if normalized in {"Ascendant", "Midheaven", "Descendant", "Imum_Coeli"}:
        return "angle"
    if normalized in {"Sun", "Moon"}:
        return "luminary"
    if normalized in {"Mercury", "Venus", "Mars"}:
        return "personal_planet"
    if normalized in {"Jupiter", "Saturn"}:
        return "social_planet"
    if normalized in {"Uranus", "Neptune", "Pluto"}:
        return "outer_planet"
    if normalized in {"North Node", "South Node", "Node"}:
        return "node"
    if normalized == "Vertex":
        return "vertex"
    if "house" in normalized.lower():
        return "house_axis"
    return "not_applicable"


def _ordinary_contact_phase(event: dict, primary_type: str) -> str:
    if primary_type in {"house_ingress", "planetary_station", "convergence_window"}:
        return "not_applicable"
    contact_count = int(event.get("contact_count", 0) or 0)
    if contact_count > 1:
        return "multi_pass"
    if event.get("peak_date") or event.get("display_anchor_date"):
        return "exact"
    return "not_applicable"


def _ordinary_motion_state(event: dict, primary_type: str) -> str:
    if primary_type == "planetary_station":
        station_type = str(event.get("station_type") or "").strip().lower()
        if station_type == "retrograde":
            return "stationary_retrograde"
        if station_type == "direct":
            return "stationary_direct"
        return "stationary"
    motion = str(event.get("motion_direction") or "").strip().lower()
    if motion == "retrograde":
        return "retrograde"
    if motion == "direct":
        return "direct"
    return "not_applicable"


def _ordinary_recurrence_class(event: dict) -> str:
    if int(event.get("contact_count", 0) or 0) > 1:
        return "multi_pass"
    if event.get("station_type"):
        return "station_linked"
    return "single_pass"


def _ordinary_angular_activation(event: dict) -> str:
    target_class = _ordinary_target_class(event)
    if target_class == "angle":
        return "angular"
    for house_key in ("natal_house", "house_number"):
        try:
            house = int(event.get(house_key) or 0)
        except (TypeError, ValueError):
            house = 0
        if house in {1, 4, 7, 10}:
            return "angular"
    return "non_angular"


def _ordinary_aspect_family(event: dict, primary_type: str) -> str:
    if primary_type == "house_ingress":
        return "ingress"
    if primary_type == "planetary_station":
        return "station"
    if primary_type == "eclipse":
        return "eclipse"
    if primary_type == "lunation":
        return "lunation"
    aspect = str(event.get("aspect") or "").strip().lower()
    return aspect or "not_applicable"


def _derive_interim_display_status(
    event: dict,
    primary_type: str,
    ordinary_salience: dict,
) -> tuple[str, str]:
    """
    Interim display statuses use conventional event-structure signals and are
    not the finalized Entangled Oracle weighting model.
    """
    if primary_type == "convergence_window":
        return ("not_applicable", "not_applicable")

    orb_status = ordinary_salience.get("orb_status", "not_applicable")
    duration_class = ordinary_salience.get("duration_class", "brief")
    target_class = ordinary_salience.get("target_class", "not_applicable")
    motion_state = ordinary_salience.get("motion_state", "not_applicable")
    recurrence_class = ordinary_salience.get("recurrence_class", "not_applicable")
    angular_activation = ordinary_salience.get("angular_activation", "non_angular")

    exact = orb_status == "exact"
    close = orb_status == "close"
    sustained = duration_class == "sustained"
    multi_pass = recurrence_class == "multi_pass"
    station_linked = recurrence_class == "station_linked"
    angular = angular_activation == "angular"
    prominent_target = target_class in {"angle", "luminary", "personal_planet", "vertex"}
    eclipse_like = primary_type in {"eclipse", "lunation"}
    stationary = primary_type == "planetary_station" or motion_state.startswith("stationary")
    ingress = primary_type == "house_ingress"

    if stationary or eclipse_like:
        if exact or angular or prominent_target:
            return ("key_window", "interim_standard_astrology")
        return ("significant", "interim_standard_astrology")

    if exact and (multi_pass or sustained or angular or prominent_target or station_linked):
        return ("key_window", "interim_standard_astrology")

    if multi_pass and sustained:
        return ("significant", "interim_standard_astrology")

    if exact or angular or prominent_target or station_linked:
        return ("significant", "interim_standard_astrology")

    if ingress or close or sustained or duration_class == "moderate":
        return ("active", "interim_standard_astrology")

    return ("background", "interim_standard_astrology")


def _year_ahead_event_id(event: dict, primary_type: str) -> str:
    if primary_type == "convergence_window":
        convergence_id = str(event.get("convergence_id") or "").strip()
        if convergence_id:
            return convergence_id
    parts = [
        primary_type,
        str(event.get("cycle_id") or ""),
        str(event.get("transit_planet") or ""),
        str(event.get("aspect") or ""),
        str(event.get("natal_target") or ""),
        str(event.get("house_number") or ""),
        str(event.get("natal_house") or ""),
        str(event.get("station_type") or ""),
        str(event.get("eclipse_type") or ""),
        str(event.get("peak_date") or event.get("entry_date") or event.get("display_anchor_date") or ""),
    ]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"ya_{primary_type}_{digest}"


def _eo_landmark_payload(event: dict) -> dict:
    return {
        "eligible": bool(
            event.get("transit_planet") != "Mars"
            and float(event.get("duration_days", 0.0) or 0.0) >= 42
            and float(event.get("structural_score", event.get("combined_intensity_score", 0.0)) or 0.0) >= 0.65
        ),
        "structural_score": round(float(event.get("structural_score", 0.0) or 0.0), 4),
        "combined_intensity_score": round(float(event.get("combined_intensity_score", 0.0) or 0.0), 4),
        "duration_days": round(float(event.get("duration_days", 0.0) or 0.0), 2),
        "landmark_min_score": 0.65,
        "landmark_min_days": 42,
    }


def _canonicalize_year_ahead_event(
    event: dict,
    house_domains: dict,
) -> dict:
    primary_type = _year_ahead_primary_event_type(event)
    transiting_body = str(
        event.get("transiting_body")
        or event.get("transit_planet")
        or event.get("eclipse_type")
        or ""
    ).strip() or None
    transit_house = event.get("house_number")
    natal_house = event.get("natal_house")
    canonical = dict(event)
    canonical["legacy_event_type"] = str(event.get("event_type") or "").strip()
    canonical["event_type"] = primary_type
    canonical["event_id"] = _year_ahead_event_id(event, primary_type)
    canonical["exact_date"] = _iso_date_or_none(
        event.get("peak_date") or event.get("display_anchor_date")
    )
    canonical["active_start"] = _iso_date_or_none(
        event.get("entry_date") or event.get("cycle_start_date")
    )
    canonical["active_end"] = _iso_date_or_none(
        event.get("leave_date") or event.get("cycle_end_date")
    )
    canonical["transiting_body"] = transiting_body
    canonical["natal_target"] = str(event.get("natal_target") or "").strip() or None
    canonical["transit_house"] = int(transit_house) if str(transit_house or "").strip() else None
    canonical["natal_house"] = int(natal_house) if str(natal_house or "").strip() else None
    canonical["motion_state"] = _ordinary_motion_state(event, primary_type)
    canonical["contact_phase"] = _ordinary_contact_phase(event, primary_type)
    canonical["continues_beyond_report"] = bool(
        event.get("continues_after_forecast_end") or event.get("active_at_report_end")
    )
    canonical["ordinary_salience"] = {
        "aspect_family": _ordinary_aspect_family(event, primary_type),
        "orb_status": _ordinary_orb_status(event, primary_type),
        "contact_phase": canonical["contact_phase"],
        "duration_class": _ordinary_duration_class(event),
        "target_class": _ordinary_target_class(event),
        "motion_state": canonical["motion_state"],
        "recurrence_class": _ordinary_recurrence_class(event),
        "angular_activation": _ordinary_angular_activation(event),
    }
    display_status, display_status_source = _derive_interim_display_status(
        event,
        primary_type,
        canonical["ordinary_salience"],
    )
    canonical["eo_landmark"] = _eo_landmark_payload(event)
    canonical["display_status"] = display_status
    canonical["display_status_source"] = display_status_source
    canonical["legacy_intensity_label"] = str(event.get("intensity_label") or "").strip()
    canonical["legacy_intensity_bar"] = str(event.get("intensity_bar") or "").strip()
    canonical["intensity_label"], canonical["intensity_bar"] = _DISPLAY_STATUS_PRESENTATION.get(
        display_status,
        ("", ""),
    )
    if primary_type == "convergence_window":
        canonical["display_status"] = "not_applicable"
        canonical["display_status_source"] = "not_applicable"
        canonical["intensity_label"] = ""
        canonical["intensity_bar"] = ""
    return canonical


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

    if event_type in {"transit", "natal_transit"}:
        return _usable_block(
            select_block_from_path(
                pack_paths["transits"],
                event.get("transit_planet", "fallback"),
                event.get("aspect", "fallback"),
                event.get("natal_target", "fallback"),
            )
        )

    if event_type in {"ingress", "house_ingress"}:
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

    if event_type in {"station", "planetary_station"}:
        return _usable_block(
            select_block_from_path(
                pack_paths["stations"],
                event.get("transit_planet", "fallback"),
                event.get("station_type", "fallback"),
            )
        )

    if event_type == "progression":
        return _usable_block(
            select_block_from_path(
                pack_paths["year_texture_progressions"],
                event.get("transit_planet", "fallback"),
                event.get("aspect", "fallback"),
                event.get("natal_target", "fallback"),
            )
        )

    if event_type == "solar_arc":
        return _usable_block(
            select_block_from_path(
                pack_paths["year_texture_solar_arc"],
                event.get("transit_planet", "fallback"),
                event.get("aspect", "fallback"),
                event.get("natal_target", "fallback"),
            )
        )

    return ""


def _event_tone(event: dict) -> str:
    """Provides a stable visual tone class for every event type."""
    event_type = event.get("event_type")

    if event_type in {"transit", "natal_transit"}:
        return event.get("aspect_character", "neutral")

    if event_type == "eclipse":
        return "eclipse"

    if event_type == "station":
        return "flowing" if event.get("station_type") == "Direct" else "challenging"

    if event_type in {"ingress", "house_ingress"}:
        return "ingress"

    return "neutral"


def _format_timeline_event(
    event:              dict,
    house_domains:      dict,
    pack_paths:         dict,
    standard_bundle:    "dict | None" = None,
    payload:            "dict | None" = None,
    index_results:      "dict | None" = None,
    lens_ctx:           "_LensContext | None" = None,
    rendered_cycle_ids: "set | None" = None,
) -> dict:
    """Converts raw engine output into a self-contained template card.

    rendered_cycle_ids — shared mutable set; if the event carries a cycle_id
    that is already present, this card is marked as a cycle milestone and
    receives no prose block (prevents repeated full-body cards for the same
    transit cycle).  The set is mutated on first render.
    """
    raw_event_type = str(event.get("event_type") or "event").strip()

    # Synthetic convergence cards are pre-formatted; fill only display defaults.
    if raw_event_type == "convergence" or _year_ahead_primary_event_type(event) == "convergence_window":
        result = _canonicalize_year_ahead_event(event, house_domains)
        result.setdefault("constellation_lens", "")
        result.setdefault("constellation_lens_label", "")
        result.setdefault("duration_descriptor", "")
        result.setdefault("house_domain", "")
        result.setdefault("why_this_matters", "")
        return result

    natal_house  = int(event.get("natal_house") or 0)
    house_domain = house_domains.get(natal_house, "")

    result = dict(event)
    result["tone"]                = _event_tone(event)
    result["house_domain"]        = house_domain
    result["duration_descriptor"] = _duration_descriptor(event)
    result["date_label"]          = (
        event.get("display_anchor_date")
        or event.get("peak_date")
        or event.get("entry_date")
        or ""
    )

    # Cycle deduplication — transit cycles render their prose block only once.
    # The landmark section renders first; monthly arc cards for the same cycle
    # receive an empty block so the prose does not repeat.
    cycle_id = event.get("cycle_id", "")
    _is_cycle_milestone = (
        raw_event_type == "transit"
        and bool(cycle_id)
        and rendered_cycle_ids is not None
        and cycle_id in rendered_cycle_ids
    )

    if _is_cycle_milestone:
        result["block"] = ""
        result["is_cycle_milestone"] = True
    else:
        result["block"] = _apply_year_ahead_prose_variation(
            _select_year_block(event, pack_paths),
            event,
        )
        result["is_cycle_milestone"] = False
        if raw_event_type == "transit" and cycle_id and rendered_cycle_ids is not None:
            rendered_cycle_ids.add(cycle_id)

    lens_text, lens_label = ("", "")
    if payload is not None and index_results is not None and lens_ctx is not None:
        lens_text, lens_label = _select_refraction_bridge(
            event, payload, index_results, lens_ctx
        )
    result["constellation_lens"]       = lens_text
    result["constellation_lens_label"] = lens_label

    if raw_event_type == "transit":
        result["event_label"] = "Natal Transit"
        result["title"] = (
            f"{event.get('transit_planet', '')} "
            f"{event.get('aspect', '')} "
            f"natal {event.get('natal_target', '')}"
        )
        result["subtitle"] = event.get("natal_target_display", "")

    elif raw_event_type == "ingress":
        house_number = int(event.get("house_number") or 0)
        result["event_label"] = "Whole Sign Ingress"
        result["title"] = (
            f"{event.get('transit_planet', '')} enters your "
            f"{_ordinal(house_number)} house"
        )
        result["subtitle"] = house_domains.get(house_number, "")

    elif raw_event_type == "eclipse":
        eclipse_type = event.get("eclipse_type", "")
        eclipse_sign = event.get("eclipse_sign", "")
        eclipse_degree = event.get("eclipse_degree", "")
        result["event_label"] = "Eclipse Contact"
        result["title"] = f"{eclipse_type} eclipse · {eclipse_degree}° {eclipse_sign}"
        result["subtitle"] = (
            f"Activates {event.get('natal_target_display', 'a natal point')}"
        )

    elif raw_event_type == "station":
        planet = event.get("transit_planet", "")
        station_type = event.get("station_type", "")
        result["event_label"] = "Planetary Station"
        result["title"] = f"{planet} stations {station_type}"
        _nat_display = event.get("natal_target_display", "")
        _relationship = event.get("relationship", "")
        if not _nat_display:
            result["subtitle"] = ""
        elif _relationship:
            result["subtitle"] = f"{_relationship} {_nat_display}"
        else:
            result["subtitle"] = f"Activating {_nat_display}"
        if _EO_CONTENT_TRACE:
            print(f"[Station Source] {pack_paths.get('stations', '<unknown>')}")
            print(f"[Station Event] {planet} {station_type}")
            print(f"[Station Target] {event.get('natal_target', '')} | house={event.get('natal_house', '')} | relationship={_relationship or 'none'}")
            print(f"[Station Subtitle] {result['subtitle']}")

    elif raw_event_type == "progression":
        result["event_label"] = "Progression Texture"
        result["title"] = (
            f"Progressed {event.get('transit_planet', '')} "
            f"{event.get('aspect', '')} "
            f"natal {event.get('natal_target', '')}"
        )
        result["subtitle"] = event.get("natal_target_display", "")

    elif raw_event_type == "solar_arc":
        result["event_label"] = "Solar Arc Texture"
        result["title"] = (
            f"{event.get('transit_planet', '')} solar arc "
            f"{event.get('aspect', '')} "
            f"natal {event.get('natal_target', '')}"
        )
        result["subtitle"] = event.get("natal_target_display", "")

    else:
        result["event_label"] = "Timing Event"
        result["title"] = raw_event_type.replace("_", " ").title()
        result["subtitle"] = ""

    result["why_this_matters"] = _build_event_why_this_matters(
        result,
        standard_bundle or {},
        pack_paths,
        house_domains,
    )
    result["ranking_diagnostics"] = _event_ranking_diagnostics(
        result,
        context="year_ahead_timeline_event",
    )

    return _canonicalize_year_ahead_event(result, house_domains)


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


def _monthly_peak_diagnostics(
    active_events: list[dict],
    period_start: datetime,
    period_end: datetime,
) -> dict:
    scored = sorted(
        [
            (event, _event_month_relevance(event, period_start, period_end))
            for event in active_events
        ],
        key=lambda item: item[1],
        reverse=True,
    )
    contributors = [
        {
            "event_id": _year_ahead_event_id(
                event,
                _year_ahead_primary_event_type(event),
            ),
            "event_type": _year_ahead_primary_event_type(event),
            "title": str(event.get("title") or event.get("event_label") or ""),
            "local_relevance": round(score, 4),
            "ranking_diagnostics": _event_ranking_diagnostics(
                event,
                context="year_ahead_monthly_peak_contributor",
                rank_score=score,
                rank_basis="monthly_local_relevance",
                local_relevance=score,
            ),
        }
        for event, score in scored[:3]
        if score > 0
    ]
    peak_score = scored[0][1] if scored else 0.0
    return {
        "context": "year_ahead_monthly_peak",
        "peak_score": round(peak_score, 4),
        "rank_basis": "max_monthly_local_relevance",
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "top_contributors": contributors,
        "top_event_diagnostics": contributors[0]["ranking_diagnostics"] if contributors else {},
    }


def _derive_forecast_shape(months: list[dict]) -> str:
    """
    Returns a concise descriptive label from the existing monthly arc scores.

    This stays structural on purpose. It describes how intensity is distributed
    across the forecast year without inventing additional interpretation.
    """
    if not months:
        return "A Developing Annual Story"

    scores = [
        float(month.get("arc_score", 0.0) or 0.0)
        for month in months
        if month.get("arc_score") is not None
    ]

    if len(scores) < 4:
        return "A Developing Annual Story"

    first = sum(scores[:4]) / len(scores[:4])
    middle_slice = scores[4:8]
    final_slice = scores[8:]

    if not middle_slice or not final_slice:
        return "A Developing Annual Story"

    middle = sum(middle_slice) / len(middle_slice)
    final = sum(final_slice) / len(final_slice)
    peak_index = max(range(len(scores)), key=scores.__getitem__)

    if final > first * 1.25 and peak_index >= 8:
        return "Late-Year Expansion"

    if first > middle * 1.20 and first > final * 1.20:
        return "Early Momentum"

    if middle > first * 1.20 and middle > final * 1.15:
        return "Midyear Turning Point"

    if scores[-1] > scores[0] * 1.35:
        return "Gradual Build"

    if scores[0] > scores[-1] * 1.35:
        return "Slow Integration"

    return "A Developing Annual Story"


def _season_title_for_month_index(index: int) -> str:
    season_titles = [
        "Opening Season",
        "Building Season",
        "Turning Season",
        "Integration Season",
    ]
    if index < 0:
        return season_titles[0]
    season_index = min(index // 3, len(season_titles) - 1)
    return season_titles[season_index]


def _normalize_shape_values(scores: list[float]) -> list[int]:
    if not scores:
        return []
    peak = max(scores)
    if peak <= 0:
        return [0 for _ in scores]
    return [round((score / peak) * 100) for score in scores]


def _forecast_distribution_note(label: str, scores: list[float]) -> str:
    if not scores:
        return "No month-level concentration data is available yet."

    spread = max(scores) - min(scores)
    if spread <= 0.08:
        return "Month-level concentration is relatively even across the forecast window."

    if label == "Late-Year Expansion":
        return "Concentration becomes more visible in the later part of the year."
    if label == "Early Momentum":
        return "Concentration is strongest near the opening portion of the forecast."
    if label == "Midyear Turning Point":
        return "Concentration gathers most clearly around the middle stretch of the year."
    if label == "Gradual Build":
        return "Month-level concentration climbs gradually as the year progresses."
    if label == "Slow Integration":
        return "The forecast opens with more visible concentration, then gradually settles."

    return "Concentration shifts across the year without resolving into a single dominant cluster."


def _build_forecast_shape_details(
    months: list[dict],
    birth_time_status: str = "exact",
) -> dict:
    """
    Build a display-oriented description of the existing month-level intensity curve.

    This helper does not create a new score. It only reorganizes existing
    `arc_score` month values into a label, neutral summary notes, and normalized
    values suitable for bar/line-like display in the report.
    """
    label = _derive_forecast_shape(months)
    if not months:
        return {
            "label": label,
            "short_explanation": "This label summarizes how the existing monthly concentration is distributed across the forecast year.",
            "peak_month": "Still forming",
            "quiet_month": "Still forming",
            "peak_season": "Still forming",
            "curve_note": "No month-level concentration data is available yet.",
            "distribution_note": "No month-level concentration data is available yet.",
            "legend_label": "Relative month concentration",
            "confidence_note": (
                "Built from the current report's existing month-level concentration values."
                if birth_time_status == "exact"
                else "Built from the current report's existing month-level concentration values. Reduced birth-time confidence can narrow how precisely some patterns are localized elsewhere in the report."
            ),
            "months": [],
        }

    scored_months = []
    for index, month in enumerate(months):
        score = float(month.get("arc_score", 0.0) or 0.0)
        scored_months.append((index, month, score))

    scores = [score for _index, _month, score in scored_months]
    normalized = _normalize_shape_values(scores)
    peak_entry = max(scored_months, key=lambda item: item[2])
    quiet_entry = min(scored_months, key=lambda item: item[2])
    peak_month_index = peak_entry[0]
    peak_month = peak_entry[1]
    quiet_month = quiet_entry[1]

    detail_months = []
    for normalized_value, (_index, month, score) in zip(normalized, scored_months):
        detail_months.append(
            {
                "name": month.get("name", ""),
                "short_name": month.get("short_name", ""),
                "arc_label": month.get("arc_label", ""),
                "score": round(score, 4),
                "normalized_value": normalized_value,
                "display_value": max(6, normalized_value) if normalized_value > 0 else 0,
                "aria_label": (
                    f"{month.get('name', month.get('short_name', 'Month'))}: "
                    f"{month.get('arc_label', 'Concentration recorded')} "
                    f"at {normalized_value}% of this year's peak month concentration."
                ),
            }
        )

    curve_note = _forecast_distribution_note(label, scores)
    confidence_note = (
        "Built from the current report's existing month-level concentration values."
        if birth_time_status == "exact"
        else "Built from the current report's existing month-level concentration values. Reduced birth-time confidence can narrow how precisely some patterns are localized elsewhere in the report."
    )

    return {
        "label": label,
        "short_explanation": "This label summarizes how the existing monthly concentration is distributed across the forecast year.",
        "peak_month": f"{peak_month.get('name', '')} - {peak_month.get('arc_label', '')}",
        "quiet_month": f"{quiet_month.get('name', '')} - {quiet_month.get('arc_label', '')}",
        "peak_season": _season_title_for_month_index(peak_month_index),
        "curve_note": curve_note,
        "distribution_note": curve_note,
        "legend_label": "Relative month concentration",
        "confidence_note": confidence_note,
        "months": detail_months,
    }


def _display_value(value: object, fallback: str) -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _parse_payload_local_datetime(payload: dict) -> datetime | None:
    local_value = (
        payload.get("user_profile", {}).get("local_datetime")
        if isinstance(payload, dict) else None
    )
    if not local_value:
        return None
    try:
        return datetime.fromisoformat(local_value)
    except ValueError:
        return None


def _format_clock(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.strftime("%I:%M %p").lstrip("0")


def _build_methodology_metadata(payload: dict, variables: dict | None = None) -> dict:
    user_profile = payload.get("user_profile", {}) if isinstance(payload, dict) else {}
    methodology = user_profile.get("methodology", {}) if isinstance(user_profile, dict) else {}
    variables = variables if isinstance(variables, dict) else {}
    fallback = get_active_methodology_metadata()

    methodology_id = (
        methodology.get("id")
        or user_profile.get("methodology_id")
        or variables.get("methodology_id")
        or fallback["id"]
    )
    methodology_label = (
        methodology.get("label")
        or user_profile.get("methodology_label")
        or variables.get("methodology_label")
        or fallback["label"]
    )
    zodiac_label = (
        methodology.get("zodiac")
        or user_profile.get("zodiac")
        or variables.get("zodiac")
        or fallback["zodiac"]
    )
    house_system_label = (
        methodology.get("house_system")
        or user_profile.get("house_system")
        or variables.get("house_system")
        or fallback["house_system"]
    )

    return {
        "methodology_id": methodology_id,
        "methodology_label": methodology_label,
        "zodiac_label": zodiac_label,
        "house_system_label": house_system_label,
        "methodology_summary": f"{zodiac_label} zodiac + {house_system_label} houses",
        "tropical_zodiac": zodiac_label == "Tropical",
    }


def _build_birth_metadata(payload: dict) -> dict:
    user_profile = payload.get("user_profile", {}) if isinstance(payload, dict) else {}
    local_dt = _parse_payload_local_datetime(payload)
    simple_mode = bool(user_profile.get("simple_mode") or payload.get("simple_mode"))
    methodology = _build_methodology_metadata(payload)
    raw_state = str(user_profile.get("birth_time_state") or user_profile.get("birth_time_confidence") or "").lower()

    birth_date_display = local_dt.strftime("%B %d, %Y") if local_dt else "Birth date unavailable"
    birth_time_display = (
        "Birth time not supplied"
        if simple_mode else
        (_format_clock(local_dt) or "Birth time unavailable")
    )
    if simple_mode or "unknown" in raw_state:
        birth_time_status = "unknown"
        birth_time_confidence = "Birth time unknown or approximate"
    elif "approximate" in raw_state:
        birth_time_status = "approximate"
        birth_time_confidence = "Birth time unknown or approximate"
    else:
        birth_time_status = "exact"
        birth_time_confidence = "Exact time supplied"
    birth_location = (
        payload.get("birth_location")
        or payload.get("location")
        or user_profile.get("queried_location")
        or "Birth location unavailable"
    )

    return {
        "birth_date_display": birth_date_display,
        "birth_time_display": birth_time_display,
        "birth_time_status": birth_time_status,
        "birth_time_confidence": birth_time_confidence,
        "birth_location": birth_location,
        "birth_time_state": user_profile.get("birth_time_state", birth_time_status),
        **methodology,
    }


def _has_exact_birth_time(payload: dict) -> bool:
    user_profile = payload.get("user_profile", {}) if isinstance(payload, dict) else {}
    if bool(user_profile.get("simple_mode") or payload.get("simple_mode")):
        return False
    state = str(user_profile.get("birth_time_state") or "").lower()
    if "approximate" in state or "unknown" in state:
        return False
    return True


def _birth_time_manifest_state(payload: dict) -> tuple[str, str]:
    birth_meta = _build_birth_metadata(payload)
    raw_state = str(birth_meta.get("birth_time_state") or birth_meta.get("birth_time_status") or "").lower()
    if "approximate" in raw_state:
        return "approximate_birth_time", "Birth time supplied as approximate; angle- and house-sensitive statements require caution."
    if "unknown" in raw_state or "not supplied" in raw_state:
        return "unknown_birth_time", "Birth time unavailable; angle- and house-dependent statements are withheld or softened."
    return "exact_birth_time", "Exact birth time supplied."


def _active_standard_module_manifest(standard_report_bundle: dict) -> list[dict]:
    modules = []
    for key, record in (standard_report_bundle.get("core_standard") or {}).items():
        modules.append(
            {
                "key": key,
                "routing_state": record.get("routing_state", ""),
                "formula_version": record.get("formula_version", "unknown"),
                "confidence_state": record.get("confidence_state", "unknown"),
            }
        )
    return modules


def _active_established_niche_manifest(standard_report_bundle: dict) -> list[dict]:
    modules = []
    for key, record in (standard_report_bundle.get("established_niche") or {}).items():
        modules.append(
            {
                "key": key,
                "visibility_state": record.get("visibility_state", ""),
                "routing_state": record.get("routing_state", ""),
                "confidence_state": record.get("confidence_state", "unknown"),
            }
        )
    return modules


def _eo_layer_manifest(standard_report_bundle: dict) -> dict:
    eo_results = standard_report_bundle.get("eo_proprietary") or {}
    active_keys = sorted(eo_results.keys())
    legacy_bridge_keys = sorted(
        key for key, value in eo_results.items()
        if "legacy_bridge" in (value.get("lineage_tags") or [])
    )
    return {
        "status": "active" if active_keys else "inactive",
        "active_modules": active_keys,
        "legacy_bridge_modules": legacy_bridge_keys,
        "module_count": len(active_keys),
    }


def _manifest_warnings(trace: dict, payload: dict) -> list[str]:
    warnings = []
    for item in trace.get("warnings_or_missing_data", []) or []:
        category = str((item or {}).get("category") or "")
        limitations = ", ".join(str(value) for value in ((item or {}).get("limitations") or []))
        if category and limitations:
            warnings.append(f"{category}: {limitations}")
    birth_state, birth_note = _birth_time_manifest_state(payload)
    if birth_state != "exact_birth_time":
        warnings.append(birth_note)
    return warnings


def _trace_file_reference(report_type: str, output_path: str, context: dict) -> str:
    explicit = str(context.get("trace_file_reference") or "").strip()
    if explicit:
        return explicit
    output_dir = os.path.dirname(output_path)
    querent = str(context.get("querent_name") or "").strip().lower().replace(" ", "_")
    if report_type == "soul_ecosystem" and querent:
        candidate = os.path.join(output_dir, f"se_trace_{querent}.json")
        if os.path.exists(candidate):
            return candidate
    return ""


def _write_report_manifest(
    *,
    report_type: str,
    birth_data: dict,
    payload: dict,
    index_results: dict,
    standard_report_bundle: dict,
    context: dict,
    content_pack: str,
    output_path: str,
    report_start: datetime,
    report_end: datetime,
) -> str:
    birth_meta = _build_birth_metadata(payload)
    birth_state, birth_note = _birth_time_manifest_state(payload)
    trace = context.get("report_surface_trace", {}) if isinstance(context.get("report_surface_trace"), dict) else {}
    version_registry = build_version_registry(report_type, content_pack)
    output_root, _extension = os.path.splitext(output_path)
    manifest_path = f"{output_root}.manifest.json"

    manifest = {
        "manifest_schema_version": REPORT_MANIFEST_SCHEMA_VERSION,
        "generation_date": datetime.now(timezone.utc).isoformat(),
        "report_type": report_type,
        "report_version": report_version(report_type),
        "report_path": output_path,
        "report_output_basename": os.path.basename(output_path),
        "report_date_range": {
            "start": report_start.strftime("%Y-%m-%d"),
            "end": report_end.strftime("%Y-%m-%d"),
        },
        "querent": {
            "name": birth_data.get("name", ""),
            "birth_date": birth_data.get("date", ""),
            "birth_time": birth_data.get("time"),
            "location": birth_data.get("location", ""),
        },
        "methodology": {
            "id": birth_meta["methodology_id"],
            "label": birth_meta["methodology_label"],
            "zodiac": "Tropical",
            "houses": "Whole Sign",
            "summary": birth_meta["methodology_summary"],
        },
        "birth_data_confidence": {
            "state": birth_state,
            "label": birth_meta["birth_time_confidence"],
            "note": birth_note,
        },
        "active_standard_modules": _active_standard_module_manifest(standard_report_bundle),
        "active_established_niche_modules": _active_established_niche_manifest(standard_report_bundle),
        "eo_layer_status": _eo_layer_manifest(standard_report_bundle),
        "content_pack": version_registry["content_pack"],
        "template_version": version_registry["templates"],
        "formula_version": {
            "formula_modules": version_registry["formula_modules"],
            "standard_engine_package": version_registry["standard_engine_package"],
            "established_niche_registry": version_registry["established_niche_registry"],
            "eo_proprietary_formula_package": version_registry["eo_proprietary_formula_package"],
            "report_generation_code": version_registry["report_generation_code"],
        },
        "block_library_version": version_registry["block_files"],
        "visual_system_version": version_registry["visual_system_css"],
        "output_package_version": version_registry["output_package"],
        "template_path": os.path.relpath(template_path(report_type), os.path.dirname(output_path)).replace("\\", "/"),
        "warnings_or_missing_inputs": _manifest_warnings(trace, payload),
        "trace_file_reference": _trace_file_reference(report_type, output_path, context),
        "report_surface_trace_summary": {
            "selected_routing_decisions": trace.get("selected_routing_decisions", {}),
            "selected_block_files": trace.get("selected_block_files", []),
            "requested_block_keys": trace.get("requested_block_keys", []),
            "fallback_use": trace.get("fallback_use", []),
            "suppressed_candidates": trace.get("suppressed_candidates", []),
        },
        "environment": {
            "content_pack": content_pack,
            "jinja2_available": JINJA2_AVAILABLE,
        },
    }

    write_json(manifest_path, manifest)
    return manifest_path


def _chart_bodies_for_reference(payload: dict) -> list[tuple[str, dict]]:
    standard_planets = payload.get("standard_planets", {}) if isinstance(payload, dict) else {}
    bodies: list[tuple[str, dict]] = []
    for name in _CHART_CHARACTERISTIC_BODIES:
        data = standard_planets.get(name, {})
        if isinstance(data, dict) and data.get("sign"):
            bodies.append((name, data))
    return bodies


def _tied_leaders(counts: dict[str, int]) -> list[str]:
    if not counts:
        return []
    lead = max(counts.values())
    if lead <= 0:
        return []
    return [name for name, count in counts.items() if count == lead]


def _format_leading_counts(counts: dict[str, int], noun: str) -> str:
    leaders = _tied_leaders(counts)
    if not leaders:
        return f"No clear {noun.lower()} lead"
    lead_count = counts[leaders[0]]
    if len(leaders) == 1:
        return f"{leaders[0]} leads ({lead_count})"
    return f"Tie: {', '.join(leaders)} ({lead_count} each)"


def _format_distribution(counts: dict[str, int], order: list[str]) -> str:
    parts = [f"{name} {counts.get(name, 0)}" for name in order]
    return " · ".join(parts)


def _format_house_list(houses: list[int]) -> str:
    if not houses:
        return ""
    if len(houses) == 1:
        return _ordinal(houses[0])
    if len(houses) == 2:
        return f"{_ordinal(houses[0])} and {_ordinal(houses[1])}"
    return ", ".join(_ordinal(house) for house in houses[:-1]) + f", and {_ordinal(houses[-1])}"


def _make_characteristic_card(
    label: str,
    value: str,
    explanation: str,
    availability_note: str = "",
    is_available: bool = True,
) -> dict:
    return {
        "label": label,
        "value": value,
        "explanation": explanation,
        "availability_note": availability_note,
        "is_available": is_available,
    }


def _build_chart_characteristics(payload: dict) -> dict:
    """
    Build a compact, reference-led chart architecture summary for Section II.

    Rules:
    - Element and modality counts use Sun through Pluto only.
    - Angle-, house-, and hemisphere-based characteristics are shown only when
      the birth time is exact enough to trust Ascendant-based house placement.
    - Stellium indicators use a simple threshold of 3 or more tracked planets
      in the same sign or, when available, the same house.
    """
    bodies = _chart_bodies_for_reference(payload)
    has_exact_time = _has_exact_birth_time(payload)

    element_counts = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    modality_counts = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}
    house_counts = {house: 0 for house in range(1, 13)}
    sign_counts: dict[str, int] = {}

    for _name, data in bodies:
        sign = data.get("sign")
        element = _ELEMENT_BY_SIGN.get(sign)
        modality = _MODALITY_BY_SIGN.get(sign)
        house = int(data.get("house") or 0)
        if element:
            element_counts[element] += 1
        if modality:
            modality_counts[modality] += 1
        if has_exact_time and 1 <= house <= 12:
            house_counts[house] += 1
        if sign:
            sign_counts[sign] = sign_counts.get(sign, 0) + 1

    cards = [
        _make_characteristic_card(
            "Leading element",
            _format_leading_counts(element_counts, "element"),
            "Counts the ten tracked planets by sign element to show which elemental emphasis is most represented in the natal map.",
        ),
        _make_characteristic_card(
            "Leading modality",
            _format_leading_counts(modality_counts, "modality"),
            "Counts the ten tracked planets by sign modality to show the strongest movement style in the natal structure.",
        ),
    ]

    if has_exact_time:
        upper = sum(house_counts[house] for house in range(7, 13))
        lower = sum(house_counts[house] for house in range(1, 7))
        eastern = sum(house_counts[house] for house in (10, 11, 12, 1, 2, 3))
        western = sum(house_counts[house] for house in (4, 5, 6, 7, 8, 9))
        angular = sum(house_counts[house] for house in (1, 4, 7, 10))
        succedent = sum(house_counts[house] for house in (2, 5, 8, 11))
        cadent = sum(house_counts[house] for house in (3, 6, 9, 12))

        cards.extend(
            [
                _make_characteristic_card(
                    "Hemisphere balance",
                    f"Upper {upper} · Lower {lower}",
                    "Uses houses 7–12 for the upper hemisphere and 1–6 for the lower hemisphere, based on the exact Ascendant.",
                ),
                _make_characteristic_card(
                    "Eastern / Western",
                    f"Eastern {eastern} · Western {western}",
                    "Uses houses 10–3 for the eastern hemisphere and 4–9 for the western hemisphere, describing how the tracked planets fall around the horizon axis.",
                ),
                _make_characteristic_card(
                    "Angular emphasis",
                    f"Angular {angular} · Succedent {succedent} · Cadent {cadent}",
                    "Groups the tracked planets by angular, succedent, and cadent houses using the exact birth-time chart.",
                ),
            ]
        )

        top_house_count = max(house_counts.values()) if house_counts else 0
        concentrated_houses = sorted(
            [house for house, count in house_counts.items() if count == top_house_count and count > 0]
        )
        if top_house_count >= 2 and concentrated_houses:
            house_value = f"{_format_house_list(concentrated_houses)} house{'s' if len(concentrated_houses) > 1 else ''} ({top_house_count})"
        else:
            house_value = "No house concentration above one tracked planet"

        cards.append(
            _make_characteristic_card(
                "House concentration",
                house_value,
                "Highlights the house or houses containing the largest number of the ten tracked planets.",
            )
        )
    else:
        qualification = "With birth time unknown or approximate, angle- and house-dependent distributions are withheld rather than inferred from the noon placeholder chart."
        cards.extend(
            [
                _make_characteristic_card(
                    "Hemisphere balance",
                    "Unavailable without exact birth time",
                    "Upper/lower and eastern/western hemisphere counts depend on reliable houses and angles.",
                    availability_note=qualification,
                    is_available=False,
                ),
                _make_characteristic_card(
                    "Angular emphasis",
                    "Unavailable without exact birth time",
                    "Angular, succedent, and cadent distributions depend on reliable house placement.",
                    availability_note=qualification,
                    is_available=False,
                ),
                _make_characteristic_card(
                    "House concentration",
                    "Unavailable without exact birth time",
                    "House concentrations are not shown when the chart uses a reduced-confidence time.",
                    availability_note=qualification,
                    is_available=False,
                ),
            ]
        )

    sign_stelliums = sorted(
        [
            (sign, count)
            for sign, count in sign_counts.items()
            if count >= 3
        ],
        key=lambda item: (-item[1], item[0]),
    )
    if sign_stelliums:
        sign_value = "; ".join(f"{sign} ({count})" for sign, count in sign_stelliums)
    else:
        sign_value = "No sign stellium at the 3-planet threshold"

    cards.append(
        _make_characteristic_card(
            "Sign stellium indicator",
            sign_value,
            "Flags any sign containing three or more of the ten tracked planets.",
        )
    )

    if has_exact_time:
        house_stelliums = sorted(
            [
                (house, count)
                for house, count in house_counts.items()
                if count >= 3
            ],
            key=lambda item: (-item[1], item[0]),
        )
        if house_stelliums:
            house_stellium_value = "; ".join(f"{_ordinal(house)} house ({count})" for house, count in house_stelliums)
        else:
            house_stellium_value = "No house stellium at the 3-planet threshold"
        cards.append(
            _make_characteristic_card(
                "House stellium indicator",
                house_stellium_value,
                "Flags any house containing three or more of the ten tracked planets in the exact-time chart.",
            )
        )
    else:
        cards.append(
            _make_characteristic_card(
                "House stellium indicator",
                "Unavailable without exact birth time",
                "House-based stellium checks depend on reliable house placement.",
                availability_note="Noon placeholder houses are not surfaced as natal architecture.",
                is_available=False,
            )
        )

    return {
        "cards": cards,
        "has_exact_birth_time": has_exact_time,
        "tracked_body_count": len(bodies),
        "element_distribution": _format_distribution(element_counts, ["Fire", "Earth", "Air", "Water"]),
        "modality_distribution": _format_distribution(modality_counts, ["Cardinal", "Fixed", "Mutable"]),
        "method_note": (
            "Counts use Sun through Pluto only. House, angle, and hemisphere references appear only when an exact birth time is available."
        ),
    }


def _format_forecast_window(start: datetime | None, end: datetime | None) -> str:
    if not start or not end:
        return "Forecast window unavailable"
    end_display = end - timedelta(days=1)
    return (
        f"{start.strftime('%B %d, %Y')} - "
        f"{end_display.strftime('%B %d, %Y')}"
    )


def _aggregate_domain_names(months: list[dict], limit: int = 3) -> list[str]:
    scores: dict[str, float] = {}
    for month in months:
        for domain in month.get("activated_domains", []):
            name = (domain.get("domain") or "").strip()
            if not name:
                continue
            scores[name] = scores.get(name, 0.0) + float(domain.get("score", 0.0) or 0.0)
    return [
        name
        for name, _score in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]


def _describe_season_trend(months: list[dict]) -> str:
    if not months:
        return "This portion of the year is still developing."

    scores = [float(month.get("arc_score", 0.0) or 0.0) for month in months]
    first = scores[0]
    last = scores[-1]
    peak_index = max(range(len(scores)), key=scores.__getitem__)

    if len(scores) >= 2 and last > first * 1.2:
        return f"Activity builds across the season and peaks in {months[peak_index]['name']}."
    if len(scores) >= 2 and first > last * 1.2:
        return f"The season opens with the strongest concentration, then gradually settles by {months[-1]['name']}."
    if peak_index == 1 and len(months) == 3:
        return f"The middle month, {months[peak_index]['name']}, acts as the hinge point for this stretch."
    return "The season moves with a relatively even rhythm, without one month overpowering the others."


def _build_season_summaries(months: list[dict]) -> list[dict]:
    season_titles = [
        "Opening Season",
        "Building Season",
        "Turning Season",
        "Integration Season",
    ]
    summaries: list[dict] = []

    for index, title in enumerate(season_titles):
        season_months = months[index * 3:(index + 1) * 3]
        if not season_months:
            continue

        peak_month = max(season_months, key=lambda month: float(month.get("arc_score", 0.0) or 0.0))
        quiet_month = min(season_months, key=lambda month: float(month.get("arc_score", 0.0) or 0.0))
        domains = _aggregate_domain_names(season_months, limit=3)

        summaries.append(
            {
                "title": title,
                "months_label": ", ".join(month["short_name"] for month in season_months),
                "summary": _describe_season_trend(season_months),
                "peak_month": peak_month["name"],
                "quiet_month": quiet_month["name"],
                "dominant_domains": ", ".join(domains) if domains else "No dominant chart areas surfaced clearly.",
            }
        )

    return summaries


def _build_annual_rhythm_quarters(
    months: list[dict],
    all_events: list[dict],
    house_domains: dict,
) -> list[dict]:
    """
    Builds four fixed-calendar quarterly orientation cards for the Annual Rhythm section.

    Groups the 12 forecast months into four blocks of three. Each card surfaces which
    slow-planet transit cycles are structurally active across the quarter and which life
    areas are most activated. No intensity labels or pacing claims are emitted.
    """
    if not months:
        return []

    _SLOW_PLANETS = {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"}

    def _season_from_month(month_number: int) -> str:
        if month_number in {12, 1, 2}:
            return "Winter"
        if month_number in {3, 4, 5}:
            return "Spring"
        if month_number in {6, 7, 8}:
            return "Summer"
        return "Autumn"

    def _format_quarter_cycle(event: dict, q_start: datetime, q_end: datetime) -> str:
        planet = str(event.get("transit_planet") or "").strip()
        aspect = str(event.get("aspect") or "").strip()
        target = str(event.get("natal_target_display") or event.get("natal_target") or "").strip()
        base = " ".join(p for p in [planet, aspect, f"natal {target}" if target else ""] if p)
        entry = event.get("entry_datetime")
        leave = event.get("leave_datetime")
        if entry is not None and q_start <= entry < q_end:
            return f"{base} — begins {entry.strftime('%b %d, %Y')}"
        if leave is not None and q_start <= leave < q_end:
            return f"{base} — resolves {leave.strftime('%b %d, %Y')}"
        return f"{base} — carries through this stretch"

    quarters: list[dict] = []
    for q_index in range(4):
        q_months = months[q_index * 3:(q_index + 1) * 3]
        if not q_months:
            continue

        try:
            q_start = datetime.strptime(q_months[0]["name"], "%B %Y").replace(tzinfo=timezone.utc)
            q_end = _add_months(
                datetime.strptime(q_months[-1]["name"], "%B %Y").replace(tzinfo=timezone.utc), 1
            )
        except (ValueError, KeyError):
            continue

        months_label = " · ".join(m.get("short_name", "") for m in q_months)
        season_name = _season_from_month(q_start.month)

        q_active = [
            event for event in all_events
            if isinstance(event, dict)
            and _interval_overlaps(
                event.get("entry_datetime"),
                event.get("leave_datetime"),
                q_start,
                q_end,
            )
        ]

        slow_transits = sorted(
            [
                event for event in q_active
                if _year_ahead_primary_event_type(event) == "natal_transit"
                and str(event.get("transit_planet") or "").strip() in _SLOW_PLANETS
            ],
            key=lambda e: float(e.get("combined_intensity_score", 0.0) or 0.0),
            reverse=True,
        )

        dominant_cycles = [
            {
                "description": _format_quarter_cycle(e, q_start, q_end),
                "planet": str(e.get("transit_planet") or "").strip(),
            }
            for e in slow_transits[:2]
        ]

        activated_domains = _most_activated_domains(q_active, house_domains, q_start, q_end, top_n=2)

        station_in_quarter = any(
            _year_ahead_primary_event_type(e) == "planetary_station"
            and e.get("peak_datetime") is not None
            and q_start <= e["peak_datetime"] < q_end
            for e in q_active
        )
        resolving_cycle = any(
            e.get("leave_datetime") is not None and q_start <= e["leave_datetime"] < q_end
            for e in slow_transits[:2]
        )

        if station_in_quarter:
            footnote = (
                "A station date sits inside this window — "
                "these tend to mark a shift in direction rather than a single event."
            )
        elif len(dominant_cycles) >= 2:
            footnote = (
                "Two long cycles overlap here — "
                "worth reading their individual monthly chapters together rather than in isolation."
            )
        elif resolving_cycle:
            footnote = "This is the closing stretch of a cycle that has been present most of the year."
        else:
            footnote = (
                "No single month in this stretch is positioned as more decisive than another — "
                "see the month-by-month chapters for dated detail."
            )

        quarters.append(
            {
                "index": f"0{q_index + 1}",
                "months_label": months_label,
                "season_name": season_name,
                "dominant_cycles": dominant_cycles,
                "activated_domains": activated_domains,
                "footnote": footnote,
            }
        )

    return quarters


def _build_year_orientation_summary(
    months: list[dict],
    landmarks: list[dict],
    dominant_planet: str,
    forecast_shape_details: dict | None = None,
) -> dict:
    if not months:
        return {
            "quietest_period": "Still forming",
            "highest_concentration_period": "Still forming",
            "strongest_annual_themes": [],
            "long_cycle_emphasis": "No sustained long-cycle emphasis is available yet.",
        }

    quietest_month = min(months, key=lambda month: float(month.get("arc_score", 0.0) or 0.0))
    strongest_month = max(months, key=lambda month: float(month.get("arc_score", 0.0) or 0.0))
    strongest_themes = [event.get("title", "") for event in landmarks[:3] if event.get("title")]

    if landmarks:
        lead_landmark = landmarks[0]
        long_cycle_emphasis = lead_landmark.get("title", "")
    elif dominant_planet:
        long_cycle_emphasis = f"{dominant_planet} carries the strongest long-range emphasis in this forecast."
    else:
        long_cycle_emphasis = "No sustained long-cycle emphasis is available yet."

    details = forecast_shape_details or _build_forecast_shape_details(months)

    if not SHOW_EO_LANDMARK_VISUALS:
        strongest_themes = []

    return {
        "quietest_period": details.get("quiet_month") or f"{quietest_month['name']} - {quietest_month['arc_label']}",
        "highest_concentration_period": details.get("peak_month") or f"{strongest_month['name']} - {strongest_month['arc_label']}",
        "strongest_annual_themes": strongest_themes,
        "long_cycle_emphasis": long_cycle_emphasis,
        "shape_explanation": details.get("short_explanation") or "This label summarizes the year’s existing month-by-month intensity pattern, rather than adding a new interpretive layer.",
        "highest_concentration_explanation": "This marks where concentration is most visible in the existing annual rhythm.",
        "quietest_period_explanation": "This is the softest point in the current annual rhythm and often works as a recovery or integration interval.",
        "long_cycle_explanation": "This shows the sustained background cycle already carrying the most structural weight across the forecast.",
        "themes_explanation": (
            "This summary remains intentionally withheld while EO Landmark visuals are disabled."
            if not SHOW_EO_LANDMARK_VISUALS
            else "These are the strongest landmark-level themes already selected elsewhere in the report."
        ),
    }


def _related_month_label(event: dict, months: list[dict]) -> str:
    event_dt = event.get("peak_datetime") or event.get("entry_datetime")
    if event_dt is not None:
        for month in months:
            month_name = month.get("name", "")
            try:
                period_start = datetime.strptime(month_name, "%B %Y").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            period_end = _add_months(period_start, 1)
            if period_start <= event_dt < period_end:
                return month_name
    return "Shown in the nearest matching monthly chapter"


def _augment_landmarks(landmarks: list[dict], months: list[dict]) -> list[dict]:
    augmented: list[dict] = []
    for landmark in landmarks:
        supporting_symbolism = (
            landmark.get("subtitle")
            or landmark.get("house_domain")
            or landmark.get("constellation_lens_label")
            or "See the supporting symbolism in the monthly chapter and ledger entries."
        )
        why_it_matters = landmark.get("block") or landmark.get("subtitle") or landmark.get("title") or ""
        item = dict(landmark)
        item["related_month"] = _related_month_label(landmark, months)
        item["supporting_symbolism"] = supporting_symbolism
        item["why_it_matters"] = why_it_matters
        item["active_period"] = landmark.get("duration_descriptor") or "See dated entries in the monthly chapters."
        augmented.append(item)
    return augmented


def _concise_turning_reason(text: str) -> str:
    cleaned = _usable_block(text)
    if not cleaned:
        return "This marks one of the year’s more durable structural windows."
    normalized = " ".join(cleaned.split())
    parts = re.split(r"(?<=[.!?])\s+", normalized)
    first = parts[0].strip() if parts else normalized
    return first[:220].rstrip() if len(first) > 220 else first


def _build_turning_point_timeline(months: list[dict], landmarks: list[dict]) -> list[dict]:
    month_order: list[tuple[str, str]] = []
    month_lookup: dict[str, dict] = {}
    for month in months:
        name = str(month.get("name") or "").strip()
        if not name:
            continue
        month_order.append((name, month.get("short_name", "")))
        month_lookup[name] = {
            "name": name,
            "short_name": month.get("short_name", ""),
            "entries": [],
        }

    for landmark in landmarks:
        related_month = str(landmark.get("related_month") or "").strip()
        target_month = related_month if related_month in month_lookup else ""
        if not target_month:
            peak_dt = landmark.get("peak_datetime") or landmark.get("entry_datetime")
            if peak_dt is not None:
                target_month = peak_dt.strftime("%B %Y")
        if target_month not in month_lookup:
            continue

        natal_target = str(
            landmark.get("natal_target_display")
            or landmark.get("subtitle")
            or landmark.get("house_domain")
            or "Natal reference not surfaced"
        ).strip()
        intensity = f"{landmark.get('intensity_bar', '')} {landmark.get('intensity_label', '')}".strip()
        month_lookup[target_month]["entries"].append(
            {
                "title": str(landmark.get("title") or ""),
                "date_label": str(landmark.get("peak_date") or landmark.get("date_label") or ""),
                "window_label": str(landmark.get("active_period") or landmark.get("duration_descriptor") or "Timing window recorded in the report"),
                "intensity_label": intensity or "Intensity recorded",
                "intensity_text": str(landmark.get("intensity_label") or ""),
                "natal_target": natal_target or "Natal reference not surfaced",
                "related_month": str(landmark.get("related_month") or target_month),
                "reason_line": _concise_turning_reason(
                    str(landmark.get("why_it_matters") or landmark.get("block") or landmark.get("subtitle") or "")
                ),
                "tone": str(landmark.get("tone") or ""),
                "ranking_diagnostics": landmark.get("ranking_diagnostics", {}),
            }
        )

    timeline: list[dict] = []
    for month_name, short_name in month_order:
        bucket = month_lookup[month_name]
        if not bucket["entries"]:
            continue
        bucket["entries"].sort(
            key=lambda item: (
                item.get("date_label", ""),
                item.get("title", ""),
            )
        )
        timeline.append(bucket)

    return timeline


def _build_month_timing_windows(month: dict) -> list[dict]:
    events = [
        event for event in month.get("events", []) or []
        if _year_ahead_primary_event_type(event) != "convergence_window"
    ]
    if not events:
        return []

    ranked = sorted(
        events,
        key=lambda event: (
            float(event.get("combined_intensity_score", 0.0) or 0.0),
            event.get("peak_datetime") or event.get("entry_datetime") or datetime.min.replace(tzinfo=timezone.utc),
        ),
        reverse=True,
    )

    return [
        {
            "title": event.get("title", ""),
            "date_label": event.get("date_label", ""),
            "event_label": event.get("event_label", ""),
            "intensity_label": event.get("intensity_label", ""),
            "subtitle": event.get("subtitle", ""),
            "ranking_diagnostics": _event_ranking_diagnostics(
                event,
                context="year_ahead_month_timing_window",
                rank_score=float(event.get("combined_intensity_score", 0.0) or 0.0),
            ),
        }
        for event in ranked[:3]
    ]


def _build_month_convergence_windows(month: dict) -> list[dict]:
    events = [
        event for event in month.get("events", []) or []
        if _year_ahead_primary_event_type(event) == "convergence_window"
    ]
    events.sort(
        key=lambda event: event.get("peak_datetime") or event.get("entry_datetime") or datetime.min.replace(tzinfo=timezone.utc)
    )
    return [
        {
            "title": str(event.get("title") or "Convergence Window"),
            "date_label": str(event.get("date_label") or ""),
            "scope_label": str(event.get("scope_label") or "Convergence window"),
            "shared_emphasis": str(event.get("shared_emphasis") or ""),
        }
        for event in events
    ]


_CLIMATE_FIELD_ORDER = [
    "connection",
    "capacity",
    "direction",
    "resources",
    "meaning",
    "visibility",
    "restoration",
]

_CLIMATE_WEIGHTS = {
    "domain": 0.50,
    "target": 0.25,
    "planet": 0.15,
}

_CLIMATE_BANDS = [
    ("most_visible", "Most visible this year", 85),
    ("strongly_present", "Strongly present", 65),
    ("present", "Present", 45),
    ("background", "Background", 20),
    ("minimal", "Minimal", 0),
]

_CLIMATE_SIGNAL_LABELS = {
    "sustained_cycle": "Sustained cycle",
    "peak_window": "Peak window",
    "house_shift": "House shift",
    "clustered_activity": "Clustered activity",
    "mixed_activity": "Mixed activity",
}

SHOW_EO_LANDMARK_VISUALS = False
SHOW_LANDMARK_VISUALS = SHOW_EO_LANDMARK_VISUALS
SHOW_FORECAST_SHAPE_VISUALS = True

_YEAR_AHEAD_EVENT_TYPE_MAP = {
    "transit": "natal_transit",
    "ingress": "house_ingress",
    "station": "planetary_station",
    "eclipse": "eclipse",
    "lunation": "lunation",
    "convergence": "convergence_window",
}

_YEAR_AHEAD_ALLOWED_EVENT_TYPES = {
    "natal_transit",
    "house_ingress",
    "planetary_station",
    "eclipse",
    "lunation",
    "convergence_window",
}

_DISPLAY_STATUS_MAP = {
    "Background": "background",
    "Active": "active",
    "Significant": "significant",
    "Key Window": "key_window",
    "Passing": "passing",
    "Convergence": "not_applicable",
}

_DISPLAY_STATUS_PRESENTATION = {
    "background": ("Background", "○"),
    "active": ("Active", "●"),
    "significant": ("Significant", "◆"),
    "key_window": ("Key Window", "✦"),
    "not_applicable": ("", ""),
    "passing": ("Background", "○"),
}

_DISPLAY_STATUS_METHOD_NOTE = (
    "Display statuses (Background, Active, Significant, Key Window) describe how concentrated a "
    "timing window is relative to the rest of its stretch of the calendar — they are a reading aid, "
    "not a ranking of importance across your whole year."
)

_ANGLE_TARGET_ALIASES = {
    "ASC": "Ascendant",
    "MC": "Midheaven",
    "DSC": "Descendant",
    "IC": "Imum_Coeli",
    "DESCENDANT": "Descendant",
    "ASCENDANT": "Ascendant",
    "MIDHEAVEN": "Midheaven",
    "IMUM_COELI": "Imum_Coeli",
    "IC": "Imum_Coeli",
    "VERTEX": "Vertex",
}

_WITHHELD_ANGLE_TARGETS = {
    "Ascendant",
    "Midheaven",
    "Descendant",
    "Vertex",
    "Imum_Coeli",
}

_CLIMATE_FIELD_DEFINITIONS = {
    "connection": {
        "label": "Connection",
        "description": "Belonging, reciprocity, agreements, and the conditions that make contact workable.",
        "primary_houses": {7, 11, 3},
        "secondary_houses": {5, 4},
        "primary_targets": {"Moon", "Venus", "Descendant", "Vertex"},
        "secondary_targets": {"Mercury"},
        "primary_planets": {"Venus", "Moon", "Mercury"},
        "secondary_planets": {"Saturn"},
    },
    "capacity": {
        "label": "Capacity",
        "description": "Energy, pacing, maintenance, physical reality, workload, and recovery.",
        "primary_houses": {6, 1},
        "secondary_houses": {10, 4},
        "primary_targets": {"Saturn", "Mars", "Sun", "Ascendant"},
        "secondary_targets": {"Moon"},
        "primary_planets": {"Saturn", "Mars", "Sun"},
        "secondary_planets": {"Jupiter"},
    },
    "direction": {
        "label": "Direction",
        "description": "Initiation, decision-making, revision, movement, and practical purpose.",
        "primary_houses": {1, 10, 9},
        "secondary_houses": {3, 11},
        "primary_targets": {"Sun", "Mars", "Ascendant", "Midheaven"},
        "secondary_targets": {"Mercury", "Jupiter"},
        "primary_planets": {"Mars", "Sun", "Jupiter"},
        "secondary_planets": {"Uranus", "Mercury"},
    },
    "resources": {
        "label": "Resources",
        "description": "Time, money, support, exchange, material conditions, and sustainability.",
        "primary_houses": {2, 8},
        "secondary_houses": {11, 4, 6},
        "primary_targets": {"Venus", "Jupiter", "Saturn", "Pluto"},
        "secondary_targets": {"Moon"},
        "primary_planets": {"Venus", "Jupiter", "Saturn"},
        "secondary_planets": {"Pluto"},
    },
    "meaning": {
        "label": "Meaning",
        "description": "Learning, imagination, identity coherence, belief, and the wider why.",
        "primary_houses": {9, 3, 12},
        "secondary_houses": {5},
        "primary_targets": {"Jupiter", "Neptune", "Mercury"},
        "secondary_targets": {"Sun", "Moon"},
        "primary_planets": {"Jupiter", "Neptune", "Mercury"},
        "secondary_planets": {"Uranus"},
    },
    "visibility": {
        "label": "Visibility",
        "description": "Contribution, recognition, witness, reputation, and public legibility.",
        "primary_houses": {10, 11, 1},
        "secondary_houses": {5},
        "primary_targets": {"Sun", "Midheaven", "Ascendant"},
        "secondary_targets": {"Saturn", "Jupiter"},
        "primary_planets": {"Sun", "Saturn", "Jupiter"},
        "secondary_planets": {"Mars"},
    },
    "restoration": {
        "label": "Restoration",
        "description": "Privacy, repair, retreat, grief, integration, and the conditions that let you exhale.",
        "primary_houses": {12, 4},
        "secondary_houses": {6, 7},
        "primary_targets": {"Moon", "Neptune", "Venus", "Imum_Coeli"},
        "secondary_targets": {"Saturn"},
        "primary_planets": {"Moon", "Neptune", "Venus"},
        "secondary_planets": {"Saturn"},
    },
}


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _slugify_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (value or "").strip().lower()).strip("_")


def _normalize_climate_target(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return _ANGLE_TARGET_ALIASES.get(text.upper(), text)


def _humanize_climate_cycle_title(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    cleaned = re.sub(r"\bnatal\s+", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\byour\s+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip(" -")


def _climate_event_identity(event: dict) -> str:
    event_type = str(event.get("event_type") or "").strip()
    cycle_id = str(event.get("cycle_id") or "").strip()
    if event_type == "transit" and cycle_id:
        return f"transit:{cycle_id}"
    parts = [
        event_type,
        str(event.get("transit_planet") or "").strip(),
        str(event.get("aspect") or "").strip(),
        _normalize_climate_target(
            event.get("natal_target_display") or event.get("natal_target")
        ),
        str(event.get("house_number") or event.get("natal_house") or "").strip(),
        str(
            event.get("peak_date")
            or event.get("entry_date")
            or event.get("display_anchor_date")
            or ""
        ).strip(),
    ]
    return "|".join(parts)


def _climate_house_for_event(event: dict) -> int | None:
    raw_house = event.get("house_number")
    if raw_house in (None, ""):
        raw_house = event.get("natal_house")
    try:
        house = int(raw_house)
    except (TypeError, ValueError):
        return None
    return house if 1 <= house <= 12 else None


def _climate_domain_for_house(house: int | None, house_domains: dict) -> str:
    if not house:
        return ""
    if isinstance(house_domains, dict):
        return str(house_domains.get(house) or house_domains.get(str(house)) or "").strip()
    return ""


def _climate_event_weight(event: dict) -> tuple[float, float]:
    event_type = _year_ahead_primary_event_type(event)
    concentration = _clamp(float(event.get("combined_intensity_score", 0.0) or 0.0), 0.0, 1.25)
    if event_type == "natal_transit":
        structural = float(event.get("structural_score", concentration) or concentration)
        structural_lift = _clamp(structural - concentration, 0.0, 0.45)
        return concentration + structural_lift, structural_lift
    multiplier = {
        "planetary_station": 0.90,
        "eclipse": 0.95,
        "house_ingress": 0.75,
    }.get(event_type, 1.0)
    return concentration * multiplier, 0.0


def _climate_match_score(value: object, primary: set[str] | set[int], secondary: set[str] | set[int]) -> float:
    if value in primary:
        return 1.0
    if value in secondary:
        return 0.5
    return 0.0


def _climate_event_type_bonus(event: dict, house_score: float, target_score: float) -> float:
    event_type = _year_ahead_primary_event_type(event)
    routed = house_score > 0 or target_score > 0
    if event_type == "planetary_station" and routed:
        return 0.10
    if event_type == "eclipse" and routed:
        return 0.15
    if event_type == "house_ingress" and house_score > 0:
        return 0.15
    return 0.0


def _climate_relevance_breakdown(
    field_key: str,
    event: dict,
    house_domains: dict,
    confidence: str,
) -> dict:
    field = _CLIMATE_FIELD_DEFINITIONS[field_key]
    target = _normalize_climate_target(event.get("natal_target_display") or event.get("natal_target"))
    planet = str(event.get("transit_planet") or "").strip()
    house = _climate_house_for_event(event) if confidence == "exact" else None
    house_score = _climate_match_score(
        house,
        field["primary_houses"],
        field["secondary_houses"],
    ) if house else 0.0
    target_score = _climate_match_score(
        target,
        field["primary_targets"],
        field["secondary_targets"],
    ) if target else 0.0
    planet_score = _climate_match_score(
        planet,
        field["primary_planets"],
        field["secondary_planets"],
    ) if planet else 0.0
    weighted_base = (
        _CLIMATE_WEIGHTS["domain"] * house_score +
        _CLIMATE_WEIGHTS["target"] * target_score +
        _CLIMATE_WEIGHTS["planet"] * planet_score
    )
    type_bonus = _climate_event_type_bonus(event, house_score, target_score)
    relevance = min(1.0, weighted_base + type_bonus)
    domain_label = _climate_domain_for_house(house, house_domains)
    return {
        "relevance": relevance,
        "house_score": house_score,
        "target_score": target_score,
        "planet_score": planet_score,
        "type_bonus": type_bonus,
        "house": house,
        "domain_label": domain_label,
        "target": target,
        "planet": planet,
    }


def _climate_event_title(event: dict) -> str:
    title = str(event.get("title") or "").strip()
    if title:
        return _humanize_climate_cycle_title(title)
    planet = str(event.get("transit_planet") or "").strip()
    aspect = str(event.get("aspect") or "").strip()
    target = _normalize_climate_target(event.get("natal_target_display") or event.get("natal_target"))
    if _event_type_matches(event, "transit", "natal_transit") and planet and aspect and target:
        return _humanize_climate_cycle_title(f"{planet} {aspect} {target}")
    if _event_type_matches(event, "station", "planetary_station") and planet:
        station_type = str(event.get("station_type") or "").strip()
        if station_type:
            return _humanize_climate_cycle_title(f"{planet} stations {station_type}")
        return _humanize_climate_cycle_title(f"{planet} station")
    if _event_type_matches(event, "eclipse"):
        eclipse_type = str(event.get("eclipse_type") or "").strip()
        if eclipse_type and target:
            return _humanize_climate_cycle_title(f"{eclipse_type} eclipse on {target}")
        if eclipse_type:
            return _humanize_climate_cycle_title(f"{eclipse_type} eclipse")
    if _event_type_matches(event, "ingress", "house_ingress") and planet and event.get("house_number"):
        return _humanize_climate_cycle_title(
            f"{planet} ingress into {_ordinal(int(event.get('house_number')))} house"
        )
    return _humanize_climate_cycle_title(title or str(event.get("event_type") or "Event").title())


def _climate_event_label(event: dict) -> str:
    mapping = {
        "transit": "Natal Transit",
        "natal_transit": "Natal Transit",
        "station": "Station",
        "planetary_station": "Station",
        "eclipse": "Eclipse",
        "ingress": "House Ingress",
        "house_ingress": "House Ingress",
        "convergence": "Convergence",
        "convergence_window": "Convergence",
    }
    return mapping.get(event.get("event_type", ""), "Event")


def _climate_timing_note(event: dict) -> str:
    duration = _duration_descriptor(event)
    if duration:
        return duration
    date_label = str(event.get("date_label") or "").strip()
    if date_label:
        return date_label
    peak_date = str(event.get("peak_date") or event.get("entry_date") or "").strip()
    if peak_date:
        return peak_date
    return "Timing available in the report chronology."


def _collect_climate_events(
    transit_events: list[dict],
    all_events: list[dict],
    confidence: str,
) -> list[dict]:
    retained: list[dict] = []
    seen: set[str] = set()

    def maybe_add(event: dict):
        if not isinstance(event, dict):
            return
        event_type = _year_ahead_primary_event_type(event)
        if event_type not in {"natal_transit", "planetary_station", "eclipse", "house_ingress"}:
            return
        if confidence != "exact" and event_type == "house_ingress":
            return
        target = _normalize_climate_target(event.get("natal_target_display") or event.get("natal_target"))
        if confidence != "exact" and target in _WITHHELD_ANGLE_TARGETS:
            return
        identity = _climate_event_identity(event)
        if identity in seen:
            return
        seen.add(identity)
        retained.append(event)

    for event in transit_events:
        maybe_add(event)

    for event in all_events:
        if _year_ahead_primary_event_type(event) in {"planetary_station", "eclipse", "house_ingress"}:
            maybe_add(event)

    return retained


def _climate_band(normalized_score: int) -> tuple[str, str]:
    for band_key, band_label, threshold in _CLIMATE_BANDS:
        if normalized_score >= threshold:
            return band_key, band_label
    return "minimal", "Minimal"


def _climate_top_list(scores: dict[str, float], limit: int = 3) -> list[str]:
    return [
        label
        for label, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        if score > 0
    ][:limit]


def _climate_signal_family(
    top_support: dict | None,
    convergence_bonus: float,
    landmark_cycle_ids: set[str],
) -> str:
    if top_support:
        event = top_support["event"]
        event_type = _year_ahead_primary_event_type(event)
        if event_type == "natal_transit":
            if top_support.get("structural_lift", 0.0) >= 0.15 or event.get("ordinary_salience", {}).get("duration_class") == "sustained":
                return "sustained_cycle"
        if event_type in {"planetary_station", "eclipse"}:
            return "peak_window"
        if event_type == "house_ingress" and top_support.get("house_score", 0.0) >= 0.50:
            return "house_shift"
    if convergence_bonus > 0:
        return "clustered_activity"
    return "mixed_activity"


def _climate_peak_driver(
    domain_scores: dict[str, float],
    target_scores: dict[str, float],
    planet_scores: dict[str, float],
) -> dict:
    channels = []
    if domain_scores:
        domain = max(domain_scores.items(), key=lambda item: item[1])
        channels.append(("domain", domain[0], domain[1]))
    if target_scores:
        target = max(target_scores.items(), key=lambda item: item[1])
        channels.append(("target", target[0], target[1]))
    if planet_scores:
        planet = max(planet_scores.items(), key=lambda item: item[1])
        channels.append(("planet", planet[0], planet[1]))
    if not channels:
        return {"source": "mixed", "key": "none", "label": "No dominant driver surfaced"}
    top_score = max(score for _source, _label, score in channels)
    top_channels = [item for item in channels if item[2] == top_score]
    if len(top_channels) > 1:
        labels = " / ".join(item[1] for item in top_channels)
        return {"source": "mixed", "key": _slugify_label(labels), "label": labels}
    source, label, _score = top_channels[0]
    return {"source": source, "key": _slugify_label(label), "label": label}


def _climate_convergence_bonus(
    field_key: str,
    convergence_events: list[dict],
    house_domains: dict,
    confidence: str,
) -> float:
    total = 0.0
    for event in convergence_events:
        if not _event_type_matches(event, "convergence", "convergence_window"):
            continue
        qualifying: set[str] = set()
        for constituent in event.get("constituent_events", []) or []:
            if not isinstance(constituent, dict):
                continue
            if confidence != "exact" and _event_type_matches(constituent, "ingress", "house_ingress"):
                continue
            target = _normalize_climate_target(
                constituent.get("natal_target_display") or constituent.get("natal_target")
            )
            if confidence != "exact" and target in _WITHHELD_ANGLE_TARGETS:
                continue
            breakdown = _climate_relevance_breakdown(field_key, constituent, house_domains, confidence)
            if breakdown["relevance"] >= 0.50:
                qualifying.add(_climate_event_identity(constituent))
        if len(qualifying) >= 2:
            total += 0.08
    return min(0.16, total)


def _build_forecast_climate(
    transit_events: list[dict],
    all_events: list[dict],
    convergence_events: list[dict],
    landmarks: list[dict],
    house_domains: dict,
    birth_time_status: str,
    pack_paths: dict,
) -> dict:
    from selectors.block_selector import select_block_from_path

    confidence = "exact" if birth_time_status == "exact" else "reduced"
    retained_events = _collect_climate_events(transit_events, all_events, confidence)
    landmark_cycle_ids = {
        str(event.get("cycle_id") or "").strip()
        for event in landmarks
        if isinstance(event, dict) and str(event.get("cycle_id") or "").strip()
    }

    field_data: dict[str, dict] = {}
    for field_key in _CLIMATE_FIELD_ORDER:
        definition = _CLIMATE_FIELD_DEFINITIONS[field_key]
        field_data[field_key] = {
            "field_key": field_key,
            "field_label": definition["label"],
            "description": definition["description"],
            "event_total": 0.0,
            "event_support": [],
            "repeat_candidates": set(),
            "domain_scores": {},
            "target_scores": {},
            "planet_scores": {},
        }

    for event in retained_events:
        annual_weight, structural_lift = _climate_event_weight(event)
        if annual_weight <= 0:
            continue
        identity = _climate_event_identity(event)
        for field_key in _CLIMATE_FIELD_ORDER:
            breakdown = _climate_relevance_breakdown(field_key, event, house_domains, confidence)
            relevance = breakdown["relevance"]
            if relevance <= 0:
                continue
            contribution = annual_weight * relevance
            if contribution <= 0:
                continue
            bucket = field_data[field_key]
            bucket["event_total"] += contribution
            if contribution >= 0.18:
                bucket["repeat_candidates"].add(identity)
            if breakdown["domain_label"]:
                bucket["domain_scores"][breakdown["domain_label"]] = (
                    bucket["domain_scores"].get(breakdown["domain_label"], 0.0) + contribution
                )
            if breakdown["target"]:
                bucket["target_scores"][breakdown["target"]] = (
                    bucket["target_scores"].get(breakdown["target"], 0.0) + contribution
                )
            if breakdown["planet"]:
                bucket["planet_scores"][breakdown["planet"]] = (
                    bucket["planet_scores"].get(breakdown["planet"], 0.0) + contribution
                )
            bucket["event_support"].append(
                {
                    "event": event,
                    "event_id": identity,
                    "contribution": contribution,
                    "structural_lift": structural_lift,
                    "house_score": breakdown["house_score"],
                    "target_score": breakdown["target_score"],
                    "planet_score": breakdown["planet_score"],
                }
            )

    raw_scores: dict[str, float] = {}
    for field_key, bucket in field_data.items():
        distinct_count = len(bucket["repeat_candidates"])
        repeat_bonus = min(0.20, 0.05 * max(0, distinct_count - 1))
        convergence_bonus = _climate_convergence_bonus(
            field_key,
            convergence_events,
            house_domains,
            confidence,
        )
        raw_scores[field_key] = bucket["event_total"] + repeat_bonus + convergence_bonus
        bucket["repeat_bonus"] = repeat_bonus
        bucket["convergence_bonus"] = convergence_bonus

    max_raw = max(raw_scores.values()) if raw_scores else 0.0
    rendered_fields = []
    for field_key in _CLIMATE_FIELD_ORDER:
        bucket = field_data[field_key]
        raw_score = raw_scores.get(field_key, 0.0)
        normalized = 0 if max_raw <= 0 else round((raw_score / max_raw) * 100)
        band_key, band_label = _climate_band(normalized)
        ranked_support = sorted(
            bucket["event_support"],
            key=lambda item: (
                item["contribution"],
                float(item["event"].get("structural_score", 0.0) or 0.0),
                float(item["event"].get("combined_intensity_score", 0.0) or 0.0),
            ),
            reverse=True,
        )
        top_support = ranked_support[0] if ranked_support else None
        signal_family_key = _climate_signal_family(
            top_support,
            bucket["convergence_bonus"],
            landmark_cycle_ids,
        )
        selected_block = select_block_from_path(
            pack_paths["forecast_climate"],
            field_key,
            band_key,
            signal_family_key,
            fallback="",
        )
        top_domains = _climate_top_list(bucket["domain_scores"])
        top_targets = _climate_top_list(bucket["target_scores"])
        top_planets = _climate_top_list(bucket["planet_scores"])
        summary_bits = []
        if top_domains:
            summary_bits.append("Domains: " + ", ".join(top_domains[:2]))
        if top_targets:
            summary_bits.append("Targets: " + ", ".join(top_targets[:2]))
        if top_planets:
            summary_bits.append("Transit planets: " + ", ".join(top_planets[:2]))
        supporting_events = []
        for support in ranked_support[:3]:
            event = support["event"]
            intensity_label = str(event.get("intensity_label") or "").strip()
            if not intensity_label:
                intensity_label, _ = _intensity_label(float(event.get("combined_intensity_score", 0.0) or 0.0))
            supporting_events.append(
                {
                    "event_id": support["event_id"],
                    "title": _climate_event_title(event),
                    "event_label": _climate_event_label(event),
                    "event_type": _year_ahead_primary_event_type(event),
                    "intensity_label": intensity_label,
                    "timing_note": _climate_timing_note(event),
                }
            )
        rendered_fields.append(
            {
                "field_key": field_key,
                "field_label": bucket["field_label"],
                "description": bucket["description"],
                "raw_score": round(raw_score, 2),
                "normalized_score": normalized,
                "band_key": band_key,
                "band_label": band_label,
                "signal_family_key": signal_family_key,
                "signal_family_label": _CLIMATE_SIGNAL_LABELS[signal_family_key],
                "peak_driver": _climate_peak_driver(
                    bucket["domain_scores"],
                    bucket["target_scores"],
                    bucket["planet_scores"],
                ),
                "top_domains": top_domains,
                "top_targets": top_targets,
                "top_planets": top_planets,
                "score_components": {
                    "event_total": round(bucket["event_total"], 2),
                    "repeat_bonus": round(bucket["repeat_bonus"], 2),
                    "convergence_bonus": round(bucket["convergence_bonus"], 2),
                },
                "supporting_events": supporting_events,
                "selected_block_key_path": [field_key, band_key, signal_family_key],
                "block": selected_block,
                "summary_line": " · ".join(summary_bits) if summary_bits else "No stronger supporting emphasis surfaced in the retained event set.",
            }
        )

    return {
        "confidence": confidence,
        "normalization_basis": "relative_within_report",
        "prominence_note": "These entries describe where concentration is most visible across the existing annual event set.",
        "certainty_note": "They do not predict outcomes or guarantee external events.",
        "confidence_note": (
            ""
            if confidence == "exact"
            else "Built from planet and retained target activity only. House- and angle-based routing is withheld without exact birth time."
        ),
        "fields": rendered_fields,
    }


def _event_family_label(event: dict) -> str:
    mapping = {
        "transit": "natal transit activity",
        "natal_transit": "natal transit activity",
        "station": "station activity",
        "planetary_station": "station activity",
        "eclipse": "eclipse activity",
        "ingress": "house-ingress activity",
        "house_ingress": "house-ingress activity",
        "convergence": "convergence activity",
        "convergence_window": "convergence activity",
    }
    return mapping.get(_year_ahead_primary_event_type(event), "event activity")


def _shared_cycle_map(month: dict) -> dict[str, dict]:
    shared: dict[str, dict] = {}
    for event in month.get("events", []):
        cycle_id = event.get("cycle_id")
        if not cycle_id:
            continue
        existing = shared.get(cycle_id)
        score = float(event.get("combined_intensity_score", 0.0) or 0.0)
        duration = float(event.get("duration_days", 0.0) or 0.0)
        if existing is None:
            shared[cycle_id] = event
            continue
        existing_score = float(existing.get("combined_intensity_score", 0.0) or 0.0)
        existing_duration = float(existing.get("duration_days", 0.0) or 0.0)
        if (score, duration) > (existing_score, existing_duration):
            shared[cycle_id] = event
    return shared


def _top_domain_name(month: dict) -> str:
    domains = month.get("activated_domains", [])
    if not domains:
        return ""
    return (domains[0].get("domain") or "").strip()


def _dominant_family(month: dict) -> str:
    events = month.get("events", [])
    if not events:
        return ""
    ranked = sorted(
        events,
        key=lambda event: (
            float(event.get("combined_intensity_score", 0.0) or 0.0),
            float(event.get("duration_days", 0.0) or 0.0),
        ),
        reverse=True,
    )
    return _event_family_label(ranked[0])


def _landmark_lookup(landmarks: list[dict]) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for item in landmarks:
        cycle_id = item.get("cycle_id")
        if cycle_id:
            lookup[cycle_id] = item
    return lookup


def _continuity_from_shared_cycle(
    source_month: dict,
    target_month: dict,
    landmark_by_cycle: dict[str, dict],
    direction: str,
) -> dict | None:
    source_cycles = _shared_cycle_map(source_month)
    target_cycles = _shared_cycle_map(target_month)
    shared_ids = [cycle_id for cycle_id in source_cycles if cycle_id in target_cycles]
    if not shared_ids:
        return None

    shared_ids.sort(
        key=lambda cycle_id: (
            float(target_cycles[cycle_id].get("combined_intensity_score", 0.0) or 0.0),
            float(target_cycles[cycle_id].get("duration_days", 0.0) or 0.0),
        ),
        reverse=True,
    )
    cycle_id = shared_ids[0]
    event = target_cycles[cycle_id]
    reference = landmark_by_cycle.get(cycle_id) or event
    title = reference.get("title") or event.get("title") or "a longer cycle"
    text = (
        f"This continues the longer {title} cycle already active in the prior chapter."
        if direction == "from_previous"
        else f"This longer {title} cycle remains active as the next chapter begins."
    )
    return {
        "kind": "shared_cycle",
        "cycle_id": cycle_id,
        "source_title": title,
        "event_type": event.get("event_type", ""),
        "text": text,
    }


def _continuity_from_domain_shift(
    current_month: dict,
    adjacent_month: dict,
    direction: str,
) -> dict | None:
    current_domain = _top_domain_name(current_month)
    adjacent_domain = _top_domain_name(adjacent_month)
    if not current_domain or not adjacent_domain or current_domain == adjacent_domain:
        return None

    current_family = _dominant_family(current_month)
    adjacent_family = _dominant_family(adjacent_month)
    family_text = adjacent_family or current_family
    if not family_text:
        return None

    text = (
        f"The emphasis shifts from {adjacent_domain} toward {current_domain} as {current_family} becomes more visible."
        if direction == "from_previous"
        else f"The emphasis shifts from {current_domain} toward {adjacent_domain} as {adjacent_family} becomes more visible."
    )
    return {
        "kind": "domain_shift",
        "from_domain": adjacent_domain if direction == "from_previous" else current_domain,
        "to_domain": current_domain if direction == "from_previous" else adjacent_domain,
        "event_family": family_text,
        "text": text,
    }


def _continuity_from_sustained_domain(
    current_month: dict,
    adjacent_month: dict,
    direction: str,
) -> dict | None:
    current_domain = _top_domain_name(current_month)
    adjacent_domain = _top_domain_name(adjacent_month)
    if not current_domain or current_domain != adjacent_domain:
        return None

    current_family = _dominant_family(current_month)
    adjacent_family = _dominant_family(adjacent_month)
    family_text = current_family or adjacent_family
    if not family_text:
        return None

    text = (
        f"The emphasis remains with {current_domain} even as the month’s immediate events reorganize."
        if direction == "from_previous"
        else f"{current_domain} continues to carry forward even as the next month’s immediate events change."
    )
    return {
        "kind": "sustained_domain",
        "domain": current_domain,
        "event_family": family_text,
        "text": text,
    }


def _build_month_continuity(months: list[dict], landmarks: list[dict]) -> list[dict]:
    landmark_by_cycle = _landmark_lookup(landmarks)
    augmented: list[dict] = []

    for index, month in enumerate(months):
        item = dict(month)
        previous_month = months[index - 1] if index > 0 else None
        next_month = months[index + 1] if index + 1 < len(months) else None

        from_previous = None
        if previous_month:
            from_previous = _continuity_from_shared_cycle(previous_month, month, landmark_by_cycle, "from_previous")
            if from_previous is None:
                from_previous = _continuity_from_domain_shift(month, previous_month, "from_previous")
            if from_previous is None:
                from_previous = _continuity_from_sustained_domain(month, previous_month, "from_previous")

        into_next = None
        if next_month:
            into_next = _continuity_from_shared_cycle(month, next_month, landmark_by_cycle, "into_next")
            if into_next is None:
                into_next = _continuity_from_domain_shift(month, next_month, "into_next")
            if into_next is None:
                into_next = _continuity_from_sustained_domain(month, next_month, "into_next")

        signals = [signal for signal in (from_previous, into_next) if signal]
        item["continuity_from_previous"] = from_previous["text"] if from_previous else ""
        item["continuity_into_next"] = into_next["text"] if into_next else ""
        item["continuity_signals"] = signals
        augmented.append(item)

    return augmented


def _build_looking_ahead(months: list[dict], index: int) -> str:
    if index + 1 >= len(months):
        return "This chapter closes the forecast period and leads directly into the year-integration section."

    next_month = months[index + 1]
    domains = [domain.get("domain", "") for domain in next_month.get("activated_domains", []) if domain.get("domain")]
    domains_text = ", ".join(domains[:2])
    base = f"{next_month['name']} brings the next chapter of the report into view."
    carry_forward = ""
    next_convergences = [
        event for event in next_month.get("events", []) or []
        if _year_ahead_primary_event_type(event) == "convergence_window"
        and bool(event.get("crosses_month_boundary"))
    ]
    if next_convergences:
        carry_forward = f" A cross-month convergence carries forward through {next_convergences[0].get('date_label', '')}: {next_convergences[0].get('title', 'Convergence Window')}."
    if domains_text:
        return f"{base} The next concentration gathers most clearly around {domains_text}.{carry_forward}"
    return f"{base}{carry_forward}"


def _chapter_density_label(event_count: int) -> str:
    if event_count <= 3:
        return "Quiet chapter"
    if event_count <= 8:
        return "Steady chapter"
    if event_count <= 14:
        return "Active chapter"
    return "Dense chapter"


def _augment_months_for_template(months: list[dict], landmarks: list[dict] | None = None) -> list[dict]:
    augmented: list[dict] = []
    continuity_ready = _build_month_continuity(months, landmarks or [])
    for index, month in enumerate(months):
        item = dict(continuity_ready[index])
        item["month_overview"] = month.get("snapshot_block") or "No standalone monthly overview is available for this period."
        item["major_timing_windows"] = _build_month_timing_windows(month)
        item["convergence_windows"] = _build_month_convergence_windows(month)
        item["looking_ahead"] = _build_looking_ahead(months, index)
        item["chapter_focus"] = _top_domain_name(month) or ""
        item["chapter_driver"] = _dominant_family(month) or ""
        item["chapter_density"] = _chapter_density_label(int(month.get("event_count", 0) or 0))
        item["chapter_signal"] = (
            item["major_timing_windows"][0].get("title", "")
            if item["major_timing_windows"] else ""
        )
        item["activated_areas_summary"] = ", ".join(
            domain.get("domain", "")
            for domain in month.get("activated_domains", [])
            if domain.get("domain")
        ) or "No specific chart areas clearly dominated this month."
        augmented.append(item)
    return augmented


def _build_calculation_record(
    payload: dict,
    variables: dict,
    report_start: datetime,
    report_end: datetime,
) -> list[dict]:
    user_profile = payload.get("user_profile", {}) if isinstance(payload, dict) else {}
    coords = user_profile.get("resolved_coordinates", {}) if isinstance(user_profile, dict) else {}
    birth_meta = _build_birth_metadata(payload)
    methodology = _build_methodology_metadata(payload, variables)

    resolved_location = ""
    latitude = coords.get("latitude")
    longitude = coords.get("longitude")
    if latitude is not None and longitude is not None:
        resolved_location = f"{latitude}, {longitude}"

    return [
        {"label": "Birth date", "value": birth_meta["birth_date_display"]},
        {"label": "Birth time", "value": birth_meta["birth_time_display"]},
        {"label": "Birth-time confidence", "value": birth_meta["birth_time_confidence"]},
        {"label": "Birth location", "value": birth_meta["birth_location"]},
        {"label": "Resolved location", "value": _display_value(resolved_location, "Resolved coordinates unavailable")},
        {"label": "Timezone", "value": _display_value(user_profile.get("timezone"), "Timezone unavailable")},
        {"label": "Forecast window", "value": _format_forecast_window(report_start, report_end)},
        {"label": "Generated", "value": datetime.now().strftime("%B %d, %Y")},
        {"label": "Methodology", "value": methodology["methodology_label"]},
        {"label": "Zodiac", "value": methodology["zodiac_label"]},
        {"label": "House system", "value": _display_value(
            methodology["house_system_label"],
            "House system unavailable",
        )},
        {"label": "Ephemeris", "value": "Swiss Ephemeris"},
        {"label": "Report version", "value": "Year Ahead v2.0"},
    ]


def _ledger_month_bucket(months: list[dict]) -> tuple[list[dict], dict[tuple[int, int], dict]]:
    ordered: list[dict] = []
    keyed: dict[tuple[int, int], dict] = {}
    for month in months:
        name = str(month.get("name") or "").strip()
        if not name:
            continue
        try:
            month_start = datetime.strptime(name, "%B %Y")
        except ValueError:
            continue
        bucket = {
            "name": name,
            "short_name": month.get("short_name", ""),
            "entries": [],
        }
        ordered.append(bucket)
        keyed[(month_start.year, month_start.month)] = bucket
    return ordered, keyed


def _ledger_event_title(event: dict, house_domains: dict) -> tuple[str, str]:
    event_type = _year_ahead_primary_event_type(event)
    if event_type == "natal_transit":
        return (
            f"{event.get('transit_planet', '')} {event.get('aspect', '')} natal {event.get('natal_target', '')}".strip(),
            event.get("natal_target_display", ""),
        )
    if event_type == "house_ingress":
        house_number = int(event.get("house_number") or 0)
        return (
            f"{event.get('transit_planet', '')} enters your {_ordinal(house_number)} house".strip(),
            house_domains.get(house_number, ""),
        )
    if event_type == "eclipse":
        return (
            f"{event.get('eclipse_type', '')} eclipse · {event.get('eclipse_degree', '')}° {event.get('eclipse_sign', '')}".strip(),
            f"Activates {event.get('natal_target_display', 'a natal point')}".strip(),
        )
    if event_type == "planetary_station":
        target = event.get("natal_target_display", "")
        return (
            f"{event.get('transit_planet', '')} stations {event.get('station_type', '')}".strip(),
            f"Activating {target}".strip() if target else "",
        )
    if event_type == "convergence_window":
        return (
            str(event.get("title") or "Convergence"),
            str(event.get("subtitle") or ""),
        )
    return (
        str(event.get("title") or str(event_type or "Timing event").replace("_", " ").title()),
        str(event.get("subtitle") or ""),
    )


def _ledger_event_label(event: dict) -> str:
    return {
        "transit": "Natal Transit",
        "natal_transit": "Natal Transit",
        "ingress": "Whole Sign Ingress",
        "house_ingress": "Whole Sign Ingress",
        "eclipse": "Eclipse",
        "station": "Planetary Station",
        "planetary_station": "Planetary Station",
        "convergence": "Convergence Window",
        "convergence_window": "Convergence Window",
        "lunation": "Lunation",
    }.get(_year_ahead_primary_event_type(event), "Timing Event")


def _ledger_timing_note(event: dict) -> str:
    event_type = _year_ahead_primary_event_type(event)
    if event_type == "convergence_window":
        entry = event.get("entry_date") or ""
        leave = event.get("leave_date") or ""
        if entry and leave:
            return f"Cluster window: {entry} through {leave}"
        return str(event.get("subtitle") or "Clustered timing window")

    duration = _duration_descriptor(event)
    if duration:
        return duration

    entry = event.get("entry_date") or ""
    leave = event.get("leave_date") or ""
    if entry and leave and entry != leave:
        return f"Window: {entry} through {leave}"
    if event_type in {"planetary_station", "house_ingress", "eclipse", "lunation"}:
        return "Single-date emphasis"
    return entry or event.get("peak_date") or "Timing recorded in the forecast window"


def _ledger_technical_fields(event: dict, house_domains: dict) -> list[dict]:
    event_type = _year_ahead_primary_event_type(event)
    fields: list[dict] = []

    if event_type == "natal_transit":
        natal_house = int(event.get("natal_house") or 0)
        fields.extend(
            [
                {"label": "Type", "value": _ledger_event_label(event)},
                {"label": "Intensity", "value": f"{event.get('intensity_bar', '')} {event.get('intensity_label', '')}".strip()},
                {"label": "Timing note", "value": _ledger_timing_note(event)},
                {"label": "Cycle ID", "value": str(event.get("cycle_id") or "Unavailable")},
                {"label": "Target", "value": str(event.get("natal_target_display") or event.get("natal_target") or "Unavailable")},
                {"label": "House", "value": house_domains.get(natal_house, _ordinal(natal_house)) if natal_house else "Unavailable"},
                {"label": "Aspect", "value": f"{event.get('transit_planet', '')} {event.get('aspect', '')}".strip()},
                {"label": "Orb", "value": f"{float(event.get('orb', 0.0) or 0.0):.3f}°"},
                {"label": "Contact count", "value": str(event.get("contact_count", 0) or 0)},
            ]
        )
        return fields

    if event_type == "planetary_station":
        natal_house = int(event.get("natal_house") or 0)
        fields.extend(
            [
                {"label": "Type", "value": _ledger_event_label(event)},
                {"label": "Intensity", "value": f"{event.get('intensity_bar', '')} {event.get('intensity_label', '')}".strip()},
                {"label": "Timing note", "value": _ledger_timing_note(event)},
                {"label": "Station", "value": str(event.get("station_type") or "Unavailable")},
                {"label": "Nearest target", "value": str(event.get("natal_target_display") or event.get("natal_target") or "No natal target recorded")},
                {"label": "House", "value": house_domains.get(natal_house, _ordinal(natal_house)) if natal_house else "Unavailable"},
                {"label": "Distance", "value": f"{float(event.get('distance_to_natal_target', 0.0) or 0.0):.3f}°"},
            ]
        )
        return fields

    if event_type == "house_ingress":
        house_number = int(event.get("house_number") or 0)
        previous_house = int(event.get("previous_house_number") or 0)
        fields.extend(
            [
                {"label": "Type", "value": _ledger_event_label(event)},
                {"label": "Intensity", "value": f"{event.get('intensity_bar', '')} {event.get('intensity_label', '')}".strip()},
                {"label": "Timing note", "value": _ledger_timing_note(event)},
                {"label": "Transit planet", "value": str(event.get("transit_planet") or "Unavailable")},
                {"label": "House shift", "value": f"{_ordinal(previous_house)} → {_ordinal(house_number)}" if previous_house and house_number else "Unavailable"},
                {"label": "Entered area", "value": house_domains.get(house_number, _ordinal(house_number)) if house_number else "Unavailable"},
            ]
        )
        return fields

    if event_type == "eclipse":
        natal_house = int(event.get("natal_house") or 0)
        fields.extend(
            [
                {"label": "Type", "value": _ledger_event_label(event)},
                {"label": "Intensity", "value": f"{event.get('intensity_bar', '')} {event.get('intensity_label', '')}".strip()},
                {"label": "Timing note", "value": _ledger_timing_note(event)},
                {"label": "Eclipse type", "value": str(event.get("eclipse_type") or "Unavailable")},
                {"label": "Target", "value": str(event.get("natal_target_display") or event.get("natal_target") or "Unavailable")},
                {"label": "House", "value": house_domains.get(natal_house, _ordinal(natal_house)) if natal_house else "Unavailable"},
                {"label": "Distance", "value": f"{float(event.get('distance_to_natal_target', 0.0) or 0.0):.3f}°"},
            ]
        )
        return fields

    if event_type == "convergence_window":
        constituent_events = event.get("constituent_events", []) or []
        families = sorted({
            _year_ahead_primary_event_type(item)
            for item in constituent_events
            if isinstance(item, dict) and _year_ahead_primary_event_type(item)
        })
        fields.extend(
            [
                {"label": "Type", "value": _ledger_event_label(event)},
                {"label": "Intensity", "value": f"{event.get('intensity_bar', '')} {event.get('intensity_label', '')}".strip()},
                {"label": "Timing note", "value": _ledger_timing_note(event)},
                {"label": "Pattern", "value": str(event.get("convergence_pattern") or "Mixed activity")},
                {"label": "Source count", "value": str(len(constituent_events))},
                {"label": "Source families", "value": ", ".join(families) if families else "Unavailable"},
            ]
        )
        return fields

    return [
        {"label": "Type", "value": _ledger_event_label(event)},
        {"label": "Timing note", "value": _ledger_timing_note(event)},
    ]


def _ledger_date_window(event: dict) -> str:
    event_type = _year_ahead_primary_event_type(event)
    date_label = str(event.get("date_label") or event.get("peak_date") or event.get("entry_date") or "").strip()
    entry = str(event.get("entry_date") or "").strip()
    leave = str(event.get("leave_date") or "").strip()
    if event_type in {"planetary_station", "house_ingress", "eclipse", "lunation"}:
        return date_label or entry or "Recorded date"
    if entry and leave and entry != leave:
        return f"{entry} – {leave}"
    return date_label or entry or "Recorded date"


def _ledger_astrological_status(event: dict) -> str:
    event_type = _year_ahead_primary_event_type(event)
    salience = event.get("ordinary_salience", {}) or {}
    motion_state = salience.get("motion_state", "not_applicable")
    recurrence_class = salience.get("recurrence_class", "not_applicable")
    orb_status = salience.get("orb_status", "not_applicable")
    duration_class = salience.get("duration_class", "brief")
    angular = salience.get("angular_activation") == "angular"

    if event_type == "house_ingress":
        return "Whole Sign ingress"
    if event_type == "planetary_station":
        direction = str(event.get("station_type") or "").strip().lower()
        if direction == "retrograde":
            return "Exact stationary retrograde"
        if direction == "direct":
            return "Exact stationary direct"
        return "Stationary emphasis"
    if event_type == "eclipse":
        return "Eclipse contact" + (" · Angular activation" if angular else "")
    if event_type == "lunation":
        return "Lunation contact" + (" · Angular activation" if angular else "")
    if event_type == "convergence_window":
        return "Convergence window"

    if recurrence_class == "multi_pass" and duration_class == "sustained":
        return "Sustained multi-pass cycle" + (" · Angular activation" if angular else "")
    if orb_status == "exact":
        if motion_state == "retrograde":
            return "Exact retrograde pass" + (" · Angular activation" if angular else "")
        if motion_state == "direct":
            return "Exact direct pass" + (" · Angular activation" if angular else "")
        return "Exact contact" + (" · Angular activation" if angular else "")
    if recurrence_class == "multi_pass":
        label = "Multi-pass cycle"
    elif motion_state == "retrograde":
        label = "Retrograde pass"
    elif motion_state == "direct":
        label = "Direct pass"
    elif duration_class == "sustained":
        label = "Sustained cycle"
    else:
        label = "Windowed cycle"
    if angular:
        label += " · Angular activation"
    return label


def _ledger_target_house(event: dict, house_domains: dict) -> str:
    event_type = _year_ahead_primary_event_type(event)
    target = str(event.get("natal_target_display") or event.get("natal_target") or "").strip()
    natal_house = int(event.get("natal_house") or 0) if str(event.get("natal_house") or "").strip() else 0
    transit_house = int(event.get("house_number") or 0) if str(event.get("house_number") or "").strip() else 0

    if event_type == "house_ingress":
        if transit_house:
            return house_domains.get(transit_house, f"{_ordinal(transit_house)} house")
        return "Whole Sign house change"
    if event_type in {"eclipse", "lunation"}:
        house_label = house_domains.get(natal_house, f"{_ordinal(natal_house)} house") if natal_house else ""
        if target and house_label:
            return f"{target} · {house_label}"
        return target or house_label or "Natal point activation"
    if event_type == "planetary_station":
        house_label = house_domains.get(natal_house, f"{_ordinal(natal_house)} house") if natal_house else ""
        if target and house_label:
            return f"{target} · {house_label}"
        return target or house_label or "Nearest natal point"
    if event_type == "natal_transit":
        house_label = house_domains.get(natal_house, f"{_ordinal(natal_house)} house") if natal_house else ""
        if target and house_label:
            return f"{target} · {house_label}"
        return target or house_label or "Natal target"
    return target or "—"


def _ledger_cycle_structure(event: dict) -> str:
    parts: list[str] = []
    duration_days = float(event.get("duration_days", 0.0) or 0.0)
    event_type = _year_ahead_primary_event_type(event)
    if duration_days >= 1 and event_type not in {"planetary_station", "house_ingress", "eclipse", "lunation"}:
        parts.append(f"{round(duration_days):.0f}-day window")
    elif event_type in {"planetary_station", "house_ingress", "eclipse", "lunation"}:
        parts.append("Single-date contact")

    contact_count = int(event.get("contact_count", 0) or 0)
    if contact_count > 1:
        parts.append(f"{contact_count}-pass cycle")
    elif event_type == "natal_transit":
        parts.append("Single-pass contact")

    if event.get("ordinary_salience", {}).get("recurrence_class") == "station_linked":
        parts.append("Station-linked cycle")

    if bool(event.get("continues_beyond_report")):
        parts.append("Continues beyond forecast")

    if event_type == "planetary_station":
        parts.append(f"{str(event.get('station_type') or 'Station').strip()} station")
    return " · ".join(parts) if parts else "Recorded in forecast registry"


def _ledger_structure_notes_sections() -> list[dict]:
    return [
        {
            "key": "transit_contact_notes",
            "title": "Transit Contact Notes",
            "columns": [
                "Transit Body",
                "Natal Target",
                "Aspect",
                "Closest Orb",
                "Phase",
                "Window Dates",
                "Pass Count",
                "Motion",
            ],
            "rows": [],
        },
        {
            "key": "station_ingress_notes",
            "title": "Station and Ingress Notes",
            "columns": [
                "Body",
                "Event",
                "Whole Sign House",
                "Relevant Date",
                "Related Selected Events",
            ],
            "rows": [],
        },
        {
            "key": "eclipse_lunation_notes",
            "title": "Eclipse and Lunation Notes",
            "columns": [
                "Event Type",
                "Sign and Degree",
                "Whole Sign House",
                "Natal Contact",
                "Window Date",
                "Closest Orb",
            ],
            "rows": [],
        },
    ]


def _ledger_contact_rows(event: dict) -> list[dict]:
    contacts = event.get("contacts", []) or []
    rows: list[dict] = []
    for contact in contacts:
        if not isinstance(contact, dict):
            continue
        motion = str(contact.get("motion_direction") or "").strip()
        rows.append(
            {
                "sequence_label": f"Pass {int(contact.get('sequence_index', len(rows) + 1) or len(rows) + 1)}",
                "date_label": str(contact.get("contact_date") or ""),
                "motion_label": motion.capitalize() if motion else "Recorded",
                "orb_label": f"{float(contact.get('contact_orb', 0.0) or 0.0):.4f}°",
                "exactness_label": "Exact" if bool(contact.get("is_exact")) else "Closest approach",
            }
        )
    return rows


def _build_related_convergence_lookup(source_events: list[dict], house_domains: dict) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for raw_event in source_events:
        if not isinstance(raw_event, dict):
            continue
        if _year_ahead_primary_event_type(raw_event) != "convergence_window":
            continue
        title = str(raw_event.get("title") or "Convergence Window").strip()
        for event_id in raw_event.get("constituent_event_ids", []) or []:
            event_id = str(event_id or "").strip()
            if not event_id:
                continue
            bucket = lookup.setdefault(event_id, [])
            if title and title not in bucket:
                bucket.append(title)
    return lookup


def _build_convergence_index(source_events: list[dict]) -> list[dict]:
    convergences = [
        event for event in source_events
        if isinstance(event, dict) and _year_ahead_primary_event_type(event) == "convergence_window"
    ]
    convergences.sort(
        key=lambda event: event.get("entry_datetime") or event.get("peak_datetime") or datetime.min.replace(tzinfo=timezone.utc)
    )
    return [
        {
            "window": str(event.get("date_label") or "Recorded window"),
            "title": str(event.get("title") or "Convergence Window"),
            "shared_emphasis": str(event.get("shared_emphasis") or "Shared emphasis across related conditions"),
            "participating_conditions": str(event.get("participating_condition_line") or "—"),
            "activated_territories": " · ".join(event.get("activated_territories", []) or []) or "—",
        }
        for event in convergences
    ]


def _append_structure_note_row(sections: list[dict], section_key: str, row: list[str]) -> None:
    for section in sections:
        if section.get("key") == section_key:
            section.setdefault("rows", []).append(row)
            return


def _build_raw_cycle_ledger(
    months: list[dict],
    source_events: list[dict],
    house_domains: dict,
) -> dict:
    """
    Build a report-safe Cycle Ledger directly from raw Year Ahead source events.

    Contract:
    - preserves merged transit-cycle records and exact contacts when available
    - preserves only genuine fields for stations, ingresses, eclipses, and
      convergence windows
    - excludes debug-only internals such as `_duration_modifier`
    - groups entries by the report's existing month buckets
    """
    ordered_months, month_lookup = _ledger_month_bucket(months)
    if not ordered_months:
        return {"months": [], "uses_raw_records": False, "migration_fallback_ready": True}

    related_convergences = _build_related_convergence_lookup(source_events, house_domains)
    convergence_index = _build_convergence_index(source_events)
    structure_sections = _ledger_structure_notes_sections()

    relevant_events = [
        _canonicalize_year_ahead_event(event, house_domains)
        for event in source_events
        if isinstance(event, dict)
        and _year_ahead_primary_event_type(event) in {
            "natal_transit", "planetary_station", "house_ingress", "eclipse", "lunation"
        }
        and event.get("peak_datetime") is not None
    ]
    relevant_events.sort(
        key=lambda event: (
            event.get("peak_datetime"),
            _ledger_event_label(event),
            str(event.get("title") or ""),
        )
    )

    for event in relevant_events:
        peak_dt = event.get("peak_datetime")
        bucket = month_lookup.get((peak_dt.year, peak_dt.month)) if peak_dt else None
        if bucket is None:
            continue

        title, _subtitle = _ledger_event_title(event, house_domains)
        related_titles = related_convergences.get(str(event.get("event_id") or "").strip(), [])
        related_convergence = " · ".join(related_titles) if related_titles else "—"
        bucket["entries"].append(
            {
                "event_type_key": _year_ahead_primary_event_type(event),
                "event_type_label": _ledger_event_label(event),
                "date_window": _ledger_date_window(event),
                "title": title,
                "astrological_status": _ledger_astrological_status(event),
                "target_house": _ledger_target_house(event, house_domains),
                "cycle_structure": _ledger_cycle_structure(event),
                "related_convergence": related_convergence,
            }
        )

        event_type = _year_ahead_primary_event_type(event)
        if event_type == "natal_transit":
            contact_motion = " / ".join(
                sorted(
                    {
                        str(contact.get("motion_direction") or "").strip().capitalize()
                        for contact in event.get("contacts", []) or []
                        if isinstance(contact, dict) and str(contact.get("motion_direction") or "").strip()
                    }
                )
            ) or (
                str(event.get("ordinary_salience", {}).get("motion_state", ""))
                .replace("_", " ")
                .title()
            )
            _append_structure_note_row(
                structure_sections,
                "transit_contact_notes",
                [
                    str(event.get("transit_planet") or "—"),
                    str(event.get("natal_target_display") or event.get("natal_target") or "—"),
                    str(event.get("aspect") or "—").title(),
                    f"{float(event.get('orb', 0.0) or 0.0):.3f}°",
                    str(event.get("contact_phase") or "not_applicable").replace("_", " ").title(),
                    _ledger_date_window(event),
                    str(int(event.get("contact_count", 0) or 0)),
                    contact_motion or "Recorded",
                ],
            )
        elif event_type in {"planetary_station", "house_ingress"}:
            house_number = int(event.get("house_number") or event.get("natal_house") or 0) if str(event.get("house_number") or event.get("natal_house") or "").strip() else 0
            related_label = title
            _append_structure_note_row(
                structure_sections,
                "station_ingress_notes",
                [
                    str(event.get("transit_planet") or event.get("transiting_body") or "—"),
                    (
                        f"{str(event.get('station_type') or '').strip()} station".strip()
                        if event_type == "planetary_station"
                        else "Whole Sign ingress"
                    ),
                    house_domains.get(house_number, f"{_ordinal(house_number)} house") if house_number else "—",
                    str(event.get("date_label") or event.get("peak_date") or event.get("entry_date") or "—"),
                    related_label,
                ],
            )
        elif event_type in {"eclipse", "lunation"}:
            natal_house = int(event.get("natal_house") or 0) if str(event.get("natal_house") or "").strip() else 0
            sign_degree = " ".join(
                part for part in [
                    str(event.get("eclipse_degree") or "").strip() + "°" if str(event.get("eclipse_degree") or "").strip() else "",
                    str(event.get("eclipse_sign") or "").strip(),
                ] if part
            ) or "—"
            _append_structure_note_row(
                structure_sections,
                "eclipse_lunation_notes",
                [
                    _ledger_event_label(event),
                    sign_degree,
                    house_domains.get(natal_house, f"{_ordinal(natal_house)} house") if natal_house else "—",
                    str(event.get("natal_target_display") or event.get("natal_target") or "—"),
                    str(event.get("date_label") or event.get("peak_date") or "—"),
                    (
                        f"{float(event.get('distance_to_natal_target', event.get('orb', 0.0)) or 0.0):.3f}°"
                        if event.get("distance_to_natal_target") is not None or event.get("orb") is not None
                        else "—"
                    ),
                ],
            )

    rendered_months = [month for month in ordered_months if month["entries"]]
    structure_sections = [section for section in structure_sections if section.get("rows")]
    return {
        "title": "Cycle Ledger — Forecast Event Registry",
        "subtitle": "A chronological technical index of the selected forecast events, organized by event type and ordinary astrological structure rather than hidden weighting layers.",
        "status_method_note": _DISPLAY_STATUS_METHOD_NOTE,
        "months": rendered_months,
        "uses_raw_records": bool(rendered_months),
        "migration_fallback_ready": True,
        "field_notes": [
            {"event_type": "natal_transit", "summary": "Natal transits are listed by date window and described through ordinary structural signals such as exactness, pass structure, motion, and duration."},
            {"event_type": "planetary_station", "summary": "Planetary stations remain single-date turning points and are labeled through stationary condition rather than hidden ranking logic."},
            {"event_type": "house_ingress", "summary": "Whole Sign ingresses mark house changes and stay distinct from transit-cycle rankings."},
            {"event_type": "eclipse", "summary": "Eclipses and lunations remain event types in their own right and are described through contact structure, natal activation, and house emphasis."},
        ],
        "convergence_index": convergence_index,
        "structure_notes": structure_sections,
    }


def _build_ledger_months(months: list[dict]) -> list[dict]:
    return [
        {
            "name": month.get("name", ""),
            "short_name": month.get("short_name", ""),
            "entries": [
                {
                    "title": event.get("title", ""),
                    "date_label": event.get("date_label", ""),
                    "event_label": event.get("event_label", ""),
                    "intensity": f"{event.get('intensity_bar', '')} {event.get('intensity_label', '')}".strip(),
                    "timing_note": event.get("duration_descriptor") or "Single-date emphasis",
                    "subtitle": event.get("subtitle", ""),
                }
                for event in month.get("events", [])
            ],
        }
        for month in months
        if month.get("events")
    ]


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

        if not house and _event_type_matches(event, "ingress", "house_ingress"):
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
    used_snapshot_blocks: set[str] | None = None,
) -> tuple[str, str, str]:
    """
    Returns the monthly snapshot block and its dominant planet/tone metadata.

    Long-running transits remain part of the context, but events peaking,
    entering, or resolving in the current month outrank background windows.

    Each (planet, aspect_character) bucket in the content pack holds exactly
    one fixed text, so when a slow-moving planet (Saturn especially) stays
    dominant across more than one month in the same report, always taking
    the single top-ranked candidate would repeat that text verbatim. When
    used_snapshot_blocks is supplied, the top-ranked candidate is used only
    if its text hasn't already appeared this report; otherwise the next-best
    distinct candidate is used. Falls back to the top candidate's text (a
    repeat) only once every ranked candidate has already been used.
    """
    from selectors.block_selector import select_block_from_path

    snapshot_candidates = [
        event
        for event in active_events
        if (
            _event_type_matches(event, "transit", "natal_transit")
            and event.get("transit_planet")
            in {"Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Mars"}
        )
    ]

    if not snapshot_candidates:
        return "", "", ""

    ranked = sorted(
        snapshot_candidates,
        key=lambda event: (
            _event_month_relevance(event, period_start, period_end),
            event.get("combined_intensity_score", 0.0),
            -float(event.get("duration_days", 0.0)),
        ),
        reverse=True,
    )

    fallback: tuple[str, str, str] | None = None
    for candidate in ranked:
        planet = candidate.get("transit_planet", "")
        character = candidate.get("aspect_character", "flowing")
        block = _usable_block(
            select_block_from_path(
                pack_paths["monthly_snapshots"],
                planet,
                character,
            )
        )
        if fallback is None:
            fallback = (block, planet, character)
        if used_snapshot_blocks is None or block not in used_snapshot_blocks:
            if used_snapshot_blocks is not None:
                used_snapshot_blocks.add(block)
            return block, planet, character

    return fallback

def _build_natal_positions(payload: dict) -> list[dict]:
    """Creates compact natal-position rows for the Year Ahead audit table."""
    rows: list[dict] = []
    standard_planets = payload.get("standard_planets", {})
    has_exact_time = _has_exact_birth_time(payload)

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
                "house": _ordinal(int(house)) if has_exact_time and house else "—",
            }
        )

    if not has_exact_time:
        return rows

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


def _get_dominant_index(index_results: dict) -> str:
    """Return the EAS index key with the highest score, or 'fallback'."""
    eas_keys = {"KVQ", "MKI", "RWI", "DFIS", "CATALYST", "NGE"}
    candidates = {k: v for k, v in index_results.items() if k in eas_keys}
    if not candidates:
        return "fallback"
    return max(candidates, key=lambda k: candidates[k].get("score", 0.0))


def _load_json_file(path: str) -> dict:
    """Load a JSON file; return empty dict if missing or malformed."""
    import json
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}
    except Exception as exc:
        # A missing file is a normal, expected condition at many call
        # sites — but a file that EXISTS and fails to parse is a real
        # content bug that would otherwise silently degrade to blank
        # prose with no trace of why.
        print(f"[Content] Failed to parse JSON file {path} (using empty content): {exc}")
        return {}


def _template_text(mapping: dict, key: str, fallback_key: str = "fallback") -> str:
    if not isinstance(mapping, dict):
        return ""
    value = mapping.get(key)
    if isinstance(value, str):
        return value
    fallback = mapping.get(fallback_key)
    return fallback if isinstance(fallback, str) else ""


def _format_body_list(bodies: list[str]) -> str:
    cleaned = [str(body).strip() for body in (bodies or []) if str(body).strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]}"
    return ", ".join(cleaned[:-1]) + f", and {cleaned[-1]}"


def _house_domain_label(house: int, house_domains: dict[int, str]) -> str:
    return str(house_domains.get(int(house or 0), "the life area this house describes") or "the life area this house describes")


def _build_standard_natal_foundation(
    standard_bundle: dict,
    payload: dict,
    pack_paths: dict,
    house_domains: dict[int, str],
) -> dict:
    raw = _load_json_file(pack_paths.get("standard_natal_foundation", ""))
    blocks = raw.get("foundation", raw) if isinstance(raw, dict) else {}
    if not isinstance(standard_bundle, dict) or not blocks:
        return {"intro": "", "sections": [], "methodology_note": "", "closing": ""}

    orientation = ((standard_bundle.get("chart_orientation") or {}).get("traceable_source_data") or {})
    prominence = ((standard_bundle.get("planetary_prominence") or {}).get("traceable_source_data") or {})
    chart_ruler = ((standard_bundle.get("chart_ruler") or {}).get("traceable_source_data") or {})
    houses = ((standard_bundle.get("house_emphasis") or {}).get("traceable_source_data") or {})
    luminary = ((standard_bundle.get("luminary_structure") or {}).get("traceable_source_data") or {})
    aspects = ((standard_bundle.get("aspect_architecture") or {}).get("traceable_source_data") or {})
    rulership = ((standard_bundle.get("rulership_and_dispositors") or {}).get("traceable_source_data") or {})
    configurations = ((standard_bundle.get("named_configurations") or {}).get("traceable_source_data") or {})
    convergence = ((standard_bundle.get("natal_convergence") or {}).get("traceable_source_data") or {})

    sections: list[dict] = []

    element_key = (((orientation.get("core_standard_distribution") or {}).get("dominance_assessment") or {}).get("elements") or {}).get("dominant_key", "")
    modality_key = (((orientation.get("core_standard_distribution") or {}).get("dominance_assessment") or {}).get("modalities") or {}).get("dominant_key", "")
    if element_key and modality_key:
        element_action = {
            "fire": "initiative, appetite, and forward movement",
            "earth": "tangible results, stability, and practical follow-through",
            "air": "language, interpretation, and relational perspective",
            "water": "feeling, memory, and emotional pattern recognition",
        }.get(element_key, "a repeatable way of meeting experience")
        modality_action = {
            "cardinal": "starting, redirecting, and setting the pace",
            "fixed": "holding, consolidating, and intensifying what matters",
            "mutable": "adapting, translating, and revising as conditions change",
        }.get(modality_key, "a consistent movement style")
        sections.append(
            {
                "title": "Chart orientation",
                "body": _template_text(blocks, "orientation_supported").format(
                    element_label=element_key.title(),
                    modality_label=modality_key,
                    element_action=element_action,
                    modality_action=modality_action,
                ),
                "source_categories": ["chart_orientation"],
            }
        )
    else:
        sections.append(
            {
                "title": "Chart orientation",
                "body": _template_text(blocks, "orientation_fallback"),
                "source_categories": ["chart_orientation"],
            }
        )

    rankings = prominence.get("rankings") or []
    top_prominent = rankings[0] if rankings else {}
    prominent_planet = str(top_prominent.get("body") or "")
    chart_ruler_body = str(chart_ruler.get("primary_ruler") or "")
    condition_label = ((((chart_ruler.get("condition_record") or {}).get("dignity") or {}).get("classification")) or "").replace("_", " ")
    if chart_ruler_body or prominent_planet:
        condition_sentence = (
            f"The ruler is currently described as {condition_label}, so condition modifies how readily that central function can operate."
            if condition_label else
            "The ruler remains part of the hierarchy even when no extra condition modifier needs separate prose."
        )
        driver_sentence = ""
        drivers = top_prominent.get("drivers") or []
        if drivers:
            driver_sentence = f"Its prominence is traceable through {', '.join(drivers[:3]).lower()}."
        template_key = "central_planet_same" if prominent_planet and prominent_planet == chart_ruler_body else "central_planet_split"
        sections.append(
            {
                "title": "Central planets and condition",
                "body": _template_text(blocks, template_key).format(
                    planet=chart_ruler_body or prominent_planet,
                    prominent_planet=prominent_planet or chart_ruler_body,
                    chart_ruler=chart_ruler_body or prominent_planet,
                    condition_sentence=condition_sentence,
                    driver_sentence=driver_sentence,
                ),
                "source_categories": ["planetary_prominence", "chart_ruler", "planetary_conditions"],
            }
        )

    house_rankings = houses.get("rankings") or []
    top_house = house_rankings[0] if house_rankings else {}
    second_house = house_rankings[1] if len(house_rankings) > 1 else top_house
    if top_house:
        sections.append(
            {
                "title": "House and domain emphasis",
                "body": _template_text(blocks, "house_emphasis").format(
                    top_house_ordinal=_ordinal(int(top_house.get("house") or 0)),
                    second_house_ordinal=_ordinal(int(second_house.get("house") or 0)),
                    top_domain=_house_domain_label(int(top_house.get("house") or 0), house_domains).lower(),
                    second_domain=_house_domain_label(int(second_house.get("house") or 0), house_domains).lower(),
                ),
                "source_categories": ["house_emphasis"],
            }
        )

    luminary_arch = luminary.get("sun_moon_architecture") or {}
    lunar_phase = luminary.get("lunar_phase") or {}
    luminary_state = str(luminary_arch.get("state") or "a meaningful Sun-Moon relationship").replace("_", " ")
    lunar_phase_label = str(lunar_phase.get("phase_category") or "cyclical developmental")
    sections.append(
        {
            "title": "Luminaries and phase",
            "body": _template_text(blocks, "luminary").format(
                luminary_state=luminary_state,
                lunar_phase_label=lunar_phase_label.replace("_", " "),
            ),
            "source_categories": ["luminary_structure"],
        }
    )

    connections = aspects.get("connections") or []
    supportive = next((item for item in connections if item.get("classification") == "supportive"), None)
    if supportive is None:
        supportive = next((item for item in connections if item.get("classification") == "neutral"), None)
    tensional = next((item for item in connections if item.get("classification") == "tensional"), None)
    aspect_sentence = "Major aspect networks remain backgrounded because no single support-or-tension pattern clearly outranked the rest."
    if supportive or tensional:
        support_label = ""
        tension_label = ""
        if supportive:
            support_label = f"{supportive.get('body_1', '')} {str(supportive.get('aspect', '')).lower()} {supportive.get('body_2', '')}".strip()
        if tensional:
            tension_label = f"{tensional.get('body_1', '')} {str(tensional.get('aspect', '')).lower()} {tensional.get('body_2', '')}".strip()
        if support_label and tension_label:
            aspect_sentence = f"The aspect network is not one-note: support is visible through {support_label}, while pressure concentrates around {tension_label}."
        elif tension_label:
            aspect_sentence = f"The main support-tension structure gathers most clearly around {tension_label}, which is why later forecasts touching that pattern deserve context rather than generic keywords."
        else:
            aspect_sentence = f"Supportive patterning is clearest through {support_label}, making it part of the chart's baseline rather than a one-off trait."

    final_dispositors = rulership.get("final_dispositors") or []
    if len(final_dispositors) == 1:
        rulership_sentence = f"Rulership and dispositorship simplify toward {final_dispositors[0]}, giving several chart functions a common point of return."
    elif len(final_dispositors) > 1:
        rulership_sentence = f"Rulership does not collapse into one authority alone; { _format_body_list(final_dispositors[:3]) } share the chart's final dispositor logic."
    else:
        rulership_sentence = "Rulership remains useful as background architecture even where no single final dispositor dominates the whole chart."

    config_items = configurations.get("configurations") or []
    if config_items:
        primary_configuration = config_items[0]
        configuration_sentence = (
            f"A named configuration is surfaced only because it adds real explanatory value here: {str(primary_configuration.get('type') or 'configuration').replace('_', ' ')}."
        )
    else:
        configuration_sentence = "No named configuration needs to be foregrounded unless it adds more than the planets and aspects already described."

    sections.append(
        {
            "title": "Support, tension, and rulership",
            "body": _template_text(blocks, "aspect_rulership").format(
                aspect_sentence=aspect_sentence,
                rulership_sentence=rulership_sentence,
                configuration_sentence=configuration_sentence,
            ),
            "source_categories": ["aspect_architecture", "rulership_and_dispositors", "named_configurations"],
        }
    )

    convergence_label = ""
    central_domains = convergence.get("central_life_domains") or []
    if central_domains:
        convergence_label = str(central_domains[0].get("label") or "")
    if convergence_label:
        sections.append(
            {
                "title": "Convergence theme",
                "body": _template_text(blocks, "convergence").format(convergence_label=convergence_label),
                "source_categories": ["natal_convergence"],
            }
        )

    return {
        "intro": _template_text(blocks, "opening"),
        "sections": sections,
        "methodology_note": _template_text(blocks, "methodology"),
        "closing": _template_text(blocks, "closing"),
    }


def _build_event_why_this_matters(
    event: dict,
    standard_bundle: dict,
    pack_paths: dict,
    house_domains: dict[int, str],
) -> str:
    raw = _load_json_file(pack_paths.get("standard_natal_foundation", ""))
    blocks = raw.get("forecast_context", raw) if isinstance(raw, dict) else {}
    if not isinstance(standard_bundle, dict) or not isinstance(blocks, dict):
        return ""

    event_type = _year_ahead_primary_event_type(event)
    forecast_priority = ((standard_bundle.get("forecast_natal_priority") or {}).get("traceable_source_data") or {})
    chart_ruler = ((standard_bundle.get("chart_ruler") or {}).get("traceable_source_data") or {})
    top_targets = forecast_priority.get("top_target_weights") or {}
    top_houses = forecast_priority.get("top_house_weights") or {}
    target_label = str(event.get("natal_target_display") or event.get("natal_target") or "").strip()
    target_key = str(event.get("natal_target") or "").strip()
    house_number = int(event.get("natal_house") or event.get("house_number") or 0)
    house_domain = _house_domain_label(house_number, house_domains)
    target_weight = float(top_targets.get(target_key, 0.0) or 0.0)
    house_weight = float(top_houses.get(house_number, top_houses.get(str(house_number), 0.0)) or 0.0)
    chart_ruler_body = str(chart_ruler.get("primary_ruler") or "")
    is_luminary = target_key in {"Sun", "Moon"}
    is_central_target = target_key == chart_ruler_body or is_luminary or target_weight >= 0.78
    is_supporting_target = target_weight >= 0.5

    if event_type in {"transit", "natal_transit"}:
        if is_central_target and target_label:
            return _template_text(blocks, "transit_central").format(target_label=target_label)
        if is_supporting_target and target_label:
            return _template_text(blocks, "transit_supporting").format(target_label=target_label)
        if house_number:
            return _template_text(blocks, "transit_house").format(house_domain=house_domain.lower())
        return _template_text(blocks, "transit_fallback")

    if event_type in {"ingress", "house_ingress"}:
        if house_weight >= 0.55:
            return _template_text(blocks, "ingress_headline").format(house_domain=house_domain)
        if house_weight >= 0.3:
            return _template_text(blocks, "ingress_supporting").format(house_domain=house_domain)
        return _template_text(blocks, "ingress_background").format(house_domain=house_domain)

    if event_type in {"station", "planetary_station"}:
        station_type = str(event.get("station_type") or "").lower()
        if is_central_target and target_label:
            template_key = "station_retrograde_central" if station_type == "retrograde" else "station_direct_central"
            return _template_text(blocks, template_key).format(target_label=target_label)
        template_key = "station_retrograde_background" if station_type == "retrograde" else "station_direct_background"
        return _template_text(blocks, template_key)

    if event_type == "eclipse":
        if is_central_target and target_label:
            return _template_text(blocks, "eclipse_targeted").format(target_label=target_label)
        if house_number:
            return _template_text(blocks, "eclipse_house").format(house_domain=house_domain.lower())
        return ""

    return ""


class _VariantTracker:
    """Deterministic, non-repeating selector for variant arrays within a report."""

    def __init__(self):
        self._used: dict[str, int] = {}

    def pick(self, pool_key: str, variants: list) -> str:
        if not variants:
            return ""
        idx = self._used.get(pool_key, 0)
        if idx >= len(variants):
            return ""
        self._used[pool_key] = idx + 1
        return variants[idx]


def _generate_archetypal_opening(
    payload: dict,
    index_results: dict,
    pack_paths: dict,
    dominant_planet: str,
    dominant_character: str,
) -> dict:
    """Compose a 2–3 page opening section from modular archetypal JSON blocks."""
    path = pack_paths.get("archetypal_opening_blocks", "")
    if not path:
        return {}
    raw = _load_json_file(path)
    if not raw:
        return {}

    try:
        scaffold = raw.get("opening_scaffold", raw)

        dominant_index = _get_dominant_index(index_results)
        # Movement quality comes from the dominant EAS driver body's modality,
        # not from a chart-wide count.
        movement_modality = (
            index_results.get(dominant_index, {}).get("driver_modality", "")
            or "cardinal"
        ).lower()

        # Tension type: dominant_planet aspects 2+ natal points already?
        natal_aspects = payload.get("aspects", [])
        planet_aspect_count = sum(
            1 for asp in natal_aspects
            if dominant_planet in (asp.get("body_1", ""), asp.get("body_2", ""))
        )
        tension_type = "verified_tension" if planet_aspect_count >= 2 else "no_verified_tension"

        index_key = f"high_{dominant_index.lower()}"
        index_core_block = (
            scaffold.get("index_core", {}).get(index_key)
            or scaffold.get("index_core", {}).get("high_fallback", "")
        )
        movement_block   = scaffold.get("movement_quality", {}).get(movement_modality, "")
        pressure_block   = scaffold.get("annual_pressure_bridge", {}).get(dominant_planet, "")
        relationship_block = scaffold.get("relationship_bridge", {}).get(tension_type, "")

        paragraphs = [b for b in [index_core_block, movement_block, pressure_block, relationship_block] if b]
        if not paragraphs:
            return {}

        return {
            "title": "Your Archetypal Year",
            "subtitle": "How Your Constellation Encounters This Year's Pressure",
            "body": "\n\n".join(paragraphs),
            "paragraph_count": len(paragraphs),
        }
    except Exception as exc:
        # This section is optional/decorative — a failure here shouldn't
        # break the report — but it drops an entire section silently
        # without this, with no way to tell that happened short of
        # diffing output length against a working run.
        print(f"[ArchetypalOpening] Section skipped (non-fatal): {exc}")
        return {}


# ── Multi-index constellation routing ──────────────────────────

_INDEX_LABELS: dict[str, str] = {
    "KVQ":      "Foresight Pattern",
    "MKI":      "Knowledge Legacy",
    "RWI":      "Reality Field",
    "DFIS":     "Power Current",
    "CATALYST": "Impact Radius",
    "NGE":      "Narrative Gravity",
}

# Directional affinities for event-function relevance scoring.
# This is a relevance system for choosing an interpretive lens, not
# a claim that the index itself is being transited.
_INDEX_AFFINITIES: dict[str, dict] = {
    "KVQ": {
        "planets": {"Mercury", "Neptune", "Saturn"},
        "houses":  {3, 12},
    },
    "MKI": {
        "planets": {"Mercury", "Jupiter", "Saturn"},
        "houses":  {3, 4, 9},
    },
    "RWI": {
        "planets": {"Uranus", "Saturn", "Mercury"},
        "houses":  {10, 11},
    },
    "DFIS": {
        "planets": {"Mars", "Pluto", "Saturn"},
        "houses":  {1, 7, 8},
    },
    "CATALYST": {
        "planets":       {"Uranus", "Mars", "Pluto"},
        "houses":        {7},
        "natal_targets": {"Vertex", "Descendant"},
    },
    "NGE": {
        "planets": {"Sun", "Venus", "Jupiter"},
        "houses":  {5, 9, 10, 11},
    },
}

_LENS_ELIGIBLE_TYPES   = {"transit", "natal_transit", "eclipse"}
_LENS_ELIGIBLE_LABELS  = {"Key Window", "Significant"}
_LENS_BUDGET           = 12


class _LensContext:
    """
    Shared state for event-level constellation-lens selection within one report.
    Bundles the variant tracker, selection history, and budget cap.
    """

    def __init__(self, index_results: dict, refraction_lib: dict):
        self._index_results  = index_results
        self._lib            = refraction_lib
        self._tracker        = _VariantTracker()
        self._recent: list[str]       = []   # last two index keys selected
        self._usage:  dict[str, int]  = {}   # total uses per index key
        self._budget_used = 0

    def budget_ok(self) -> bool:
        return self._budget_used < _LENS_BUDGET

    def has_variant(self, index_key: str, timing_quality: str) -> bool:
        variants = self._lib.get(index_key, {}).get(timing_quality, [])
        if isinstance(variants, str):
            variants = [variants]
        used = self._tracker._used.get(f"refraction:{index_key}:{timing_quality}", 0)
        return used < len(variants)

    def pick_variant(self, index_key: str, timing_quality: str) -> str:
        variants = self._lib.get(index_key, {}).get(timing_quality, [])
        if isinstance(variants, str):
            variants = [variants]
        return self._tracker.pick(f"refraction:{index_key}:{timing_quality}", variants)

    def recency_penalty(self, index_key: str) -> float:
        penalty = 0.0
        if self._recent and self._recent[-1] == index_key:
            penalty += 6.0   # immediately prior — strong
        elif len(self._recent) >= 2 and self._recent[-2] == index_key:
            penalty += 3.0   # two before — moderate
        return penalty

    def overuse_penalty(self, index_key: str, eligible_count: int) -> float:
        if eligible_count > 1 and self._usage.get(index_key, 0) >= 2:
            return 4.0
        return 0.0

    def record(self, index_key: str) -> None:
        self._recent.append(index_key)
        if len(self._recent) > 2:
            self._recent.pop(0)
        self._usage[index_key] = self._usage.get(index_key, 0) + 1
        self._budget_used += 1


def _get_body_natal_house(payload: dict, body: str) -> int:
    """Return the natal house number for a body, or 0 if not found."""
    for group in (payload.get("standard_planets", {}), payload.get("custom_asteroids", {})):
        data = group.get(body, {})
        if isinstance(data, dict):
            h = data.get("house")
            if h:
                return int(h)
    return 0


def _event_timing_quality(event: dict) -> str:
    ac = event.get("aspect_character", "")
    if ac in ("trine", "sextile", "flowing"):
        return "flowing_timing"
    return "challenging_timing"


def _select_event_archetypal_index(
    event:         dict,
    payload:       dict,
    index_results: dict,
    lens_ctx:      "_LensContext",
) -> "tuple[str, str] | None":
    """
    Return (index_key, timing_quality) for the best-fit eligible EAS index,
    or None when no index has real relevance to this event.
    """
    timing_quality  = _event_timing_quality(event)
    transit_planet  = event.get("transit_planet", "")
    natal_house     = int(event.get("natal_house") or event.get("house_number") or 0)
    natal_target    = event.get("natal_target", "")

    # 1. Build eligible set: not suppressed (activation_score > 0), has unused variant.
    # display_full (score >= 2.0) is intentionally not required — many valid clients have
    # every index in the subtle-signal range. The affinity scoring below enforces that
    # a subtle index is only selected when it has real event relevance, not for variety alone.
    eligible = [
        k for k in _INDEX_LABELS
        if (
            k in index_results
            and not index_results[k].get("suppressed", False)
            and index_results[k].get("activation_score", 0) > 0
            and lens_ctx.has_variant(k, timing_quality)
        )
    ]
    if not eligible:
        return None

    # 2. Score each eligible index.
    scored: dict[str, float] = {}
    for k in eligible:
        idx = index_results[k]
        aff = _INDEX_AFFINITIES.get(k, {})
        affinity = 0.0

        # A. Direct driver relevance — strongest signal.
        driver_body = idx.get("driver_body", "")
        if driver_body:
            if natal_target and driver_body.lower() in natal_target.lower():
                affinity += 3.0
            driver_house = _get_body_natal_house(payload, driver_body)
            if driver_house and natal_house == driver_house:
                affinity += 2.0

        # B. Event-function affinity.
        if transit_planet and transit_planet in aff.get("planets", set()):
            affinity += 2.0
        if natal_house and natal_house in aff.get("houses", set()):
            affinity += 1.0
        for nt_frag in aff.get("natal_targets", set()):
            if natal_target and nt_frag.lower() in natal_target.lower():
                affinity += 1.0
                break

        # No real relevance to this event — skip entirely.
        if affinity <= 0:
            continue

        # C. Activation strength — tie-breaker only.
        total = affinity + idx.get("activation_score", 0.0) * 0.05

        # D. Recency and overuse penalties.
        total -= lens_ctx.recency_penalty(k)
        total -= lens_ctx.overuse_penalty(k, len(eligible))

        scored[k] = total

    if not scored:
        return None

    winner = max(scored, key=lambda k: scored[k])
    return (winner, timing_quality)


def _select_refraction_bridge(
    event:         dict,
    payload:       dict,
    index_results: dict,
    lens_ctx:      "_LensContext",
) -> "tuple[str, str]":
    """
    Return (lens_text, lens_label) for an eligible event, or ("", "").

    Eligible: Key Window or Significant transit/eclipse cards only.
    Convergence, station, ingress, Background, and Active cards receive nothing.
    """
    if not lens_ctx.budget_ok():
        return ("", "")
    if _year_ahead_primary_event_type(event) not in _LENS_ELIGIBLE_TYPES:
        return ("", "")
    if event.get("intensity_label") not in _LENS_ELIGIBLE_LABELS:
        return ("", "")

    selection = _select_event_archetypal_index(event, payload, index_results, lens_ctx)
    if selection is None:
        return ("", "")

    index_key, timing_quality = selection
    text = lens_ctx.pick_variant(index_key, timing_quality)
    if not text:
        return ("", "")

    lens_ctx.record(index_key)
    return (text, _INDEX_LABELS.get(index_key, index_key))


# ── Convergence detection ───────────────────────────────────────

_CONVERGENCE_TITLES: dict[str, str] = {
    "private_signal_convergence":           "Private Signal Convergence",
    "public_emergence_convergence":         "Public Emergence Convergence",
    "relational_recalibration_convergence": "Relational Recalibration Convergence",
    "creative_catalyst_convergence":        "Creative Catalyst Convergence",
    "identity_emergence_convergence":       "Identity Emergence Convergence",
    "foundation_rebuild_convergence":       "Foundation Rebuild Convergence",
    "default":                              "Convergence",
}

_CONVERGENCE_MIN_EVENTS = 2
_CONVERGENCE_PROXIMITY_DAYS = 5
_CONVERGENCE_SHARED_RELATIONSHIP_MIN = 1

def _convergence_title(pattern: str) -> str:
    return _CONVERGENCE_TITLES.get(pattern, "Convergence")


def _convergence_event_bounds(event: dict) -> tuple[datetime | None, datetime | None]:
    peak = event.get("peak_datetime")
    entry = event.get("entry_datetime") or peak
    leave = event.get("leave_datetime") or peak or entry
    return entry, leave


def _convergence_dates_link(event_a: dict, event_b: dict, proximity_days: int = _CONVERGENCE_PROXIMITY_DAYS) -> bool:
    entry_a, leave_a = _convergence_event_bounds(event_a)
    entry_b, leave_b = _convergence_event_bounds(event_b)
    if entry_a and leave_a and entry_b and leave_b and entry_a <= leave_b and entry_b <= leave_a:
        return True
    peak_a = event_a.get("peak_datetime") or leave_a or entry_a
    peak_b = event_b.get("peak_datetime") or leave_b or entry_b
    if peak_a and peak_b:
        return abs((peak_b - peak_a).days) <= proximity_days
    return False


def _convergence_house_set(event: dict) -> set[int]:
    houses: set[int] = set()
    for key in ("natal_house", "house_number"):
        try:
            house = int(event.get(key) or 0)
        except (TypeError, ValueError):
            house = 0
        if 1 <= house <= 12:
            houses.add(house)
    return houses


def _convergence_domain_set(event: dict, house_domains: dict) -> set[str]:
    return {
        str(house_domains.get(house) or "").strip()
        for house in _convergence_house_set(event)
        if str(house_domains.get(house) or "").strip()
    }


def _convergence_field_focus_set(event: dict, house_domains: dict, birth_time_status: str) -> set[str]:
    confidence = "exact" if birth_time_status == "exact" else "reduced"
    labels: set[str] = set()
    for field_key in _CLIMATE_FIELD_ORDER:
        breakdown = _climate_relevance_breakdown(field_key, event, house_domains, confidence)
        if breakdown["relevance"] >= 0.5:
            labels.add(_CLIMATE_FIELD_DEFINITIONS[field_key]["label"])
    return labels


def _convergence_relationship_details(
    anchor: dict,
    candidate: dict,
    house_domains: dict,
    birth_time_status: str,
) -> list[str]:
    details: list[str] = []
    shared_houses = _convergence_house_set(anchor) & _convergence_house_set(candidate)
    shared_domains = _convergence_domain_set(anchor, house_domains) & _convergence_domain_set(candidate, house_domains)
    shared_fields = _convergence_field_focus_set(anchor, house_domains, birth_time_status) & _convergence_field_focus_set(candidate, house_domains, birth_time_status)
    anchor_planet = str(anchor.get("transit_planet") or "").strip()
    candidate_planet = str(candidate.get("transit_planet") or "").strip()
    if shared_houses:
        details.append("shared activated house")
    if shared_domains:
        details.append("shared practical territory")
    if shared_fields:
        details.append("shared field quality")
    if anchor_planet and anchor_planet == candidate_planet:
        details.append("shared transiting-body cycle")
    if _ordinary_angular_activation(anchor) == "angular" and _ordinary_angular_activation(candidate) == "angular":
        details.append("shared angular emphasis")
    anchor_type = _year_ahead_primary_event_type(anchor)
    candidate_type = _year_ahead_primary_event_type(candidate)
    if {anchor_type, candidate_type} & {"planetary_station", "eclipse", "lunation"}:
        if shared_domains or shared_houses or shared_fields:
            details.append("turning-point event inside an already-related active cycle")
    return list(dict.fromkeys(details))


def _convergence_scope_label(scope: str) -> str:
    return {
        "brief": "Brief convergence",
        "sustained": "Sustained convergence",
        "cross_month": "Cross-month convergence",
    }.get(scope, "Convergence window")


def _convergence_date_label(start_dt: datetime | None, end_dt: datetime | None) -> str:
    if not start_dt and not end_dt:
        return ""
    if start_dt and end_dt and start_dt.date() != end_dt.date():
        if start_dt.year == end_dt.year:
            if start_dt.month == end_dt.month:
                return f"{start_dt.strftime('%B %d')}–{end_dt.strftime('%d, %Y')}"
            return f"{start_dt.strftime('%B %d')}–{end_dt.strftime('%B %d, %Y')}"
        return f"{start_dt.strftime('%B %d, %Y')}–{end_dt.strftime('%B %d, %Y')}"
    point = start_dt or end_dt
    return point.strftime("%B %d, %Y") if point else ""


def _convergence_participating_conditions(cluster: list[dict]) -> list[str]:
    conditions: list[str] = []
    for event in cluster:
        title = _climate_event_title(event)
        if title and title not in conditions:
            conditions.append(title)
    return conditions


def _convergence_shared_emphasis(field_focus: list[str], territories: list[str]) -> str:
    parts: list[str] = []
    if field_focus:
        parts.append(", ".join(field_focus[:2]))
    if territories:
        parts.append(", ".join(territories[:2]))
    return " and ".join(parts) if parts else "Shared emphasis across related conditions"


def _convergence_selection_rationale(
    cluster: list[dict],
    relationship_labels: list[str],
    territories: list[str],
    field_focus: list[str],
) -> str:
    pieces = [f"{len(cluster)} independently selected ordinary events"]
    if relationship_labels:
        pieces.append("sharing " + ", ".join(relationship_labels[:2]))
    if territories:
        pieces.append("across " + ", ".join(territories[:2]))
    if field_focus:
        pieces.append("with field focus in " + ", ".join(field_focus[:2]))
    return "; ".join(pieces) + "."


def _build_convergence_window(
    cluster: list[dict],
    pattern: str,
    block_text: str,
    house_domains: dict,
    birth_time_status: str,
    relationship_labels: list[str],
) -> dict:
    canonical_cluster = [_canonicalize_year_ahead_event(event, house_domains) for event in cluster]
    canonical_cluster.sort(
        key=lambda event: event.get("peak_datetime") or event.get("entry_datetime") or datetime.min.replace(tzinfo=timezone.utc)
    )
    entry_dates = [event.get("entry_datetime") or event.get("peak_datetime") for event in canonical_cluster if event.get("entry_datetime") or event.get("peak_datetime")]
    leave_dates = [event.get("leave_datetime") or event.get("peak_datetime") or event.get("entry_datetime") for event in canonical_cluster if event.get("leave_datetime") or event.get("peak_datetime") or event.get("entry_datetime")]
    start_dt = min(entry_dates) if entry_dates else None
    end_dt = max(leave_dates) if leave_dates else start_dt
    confidence = "exact" if birth_time_status == "exact" else "reduced"
    field_scores: dict[str, float] = {}
    for event in canonical_cluster:
        for field_key in _CLIMATE_FIELD_ORDER:
            breakdown = _climate_relevance_breakdown(field_key, event, house_domains, confidence)
            if breakdown["relevance"] <= 0:
                continue
            label = _CLIMATE_FIELD_DEFINITIONS[field_key]["label"]
            field_scores[label] = field_scores.get(label, 0.0) + breakdown["relevance"]
    field_focus = [
        label
        for label, _score in sorted(field_scores.items(), key=lambda item: item[1], reverse=True)[:2]
    ]
    territories: list[str] = []
    for event in canonical_cluster:
        for domain in _convergence_domain_set(event, house_domains):
            if domain and domain not in territories:
                territories.append(domain)
    participating_conditions = _convergence_participating_conditions(canonical_cluster)
    crosses_month_boundary = bool(start_dt and end_dt and (start_dt.year, start_dt.month) != (end_dt.year, end_dt.month))
    span_days = ((end_dt - start_dt).days + 1) if start_dt and end_dt else len(canonical_cluster)
    if crosses_month_boundary:
        scope = "cross_month"
    elif span_days >= 21 or len(canonical_cluster) >= 3:
        scope = "sustained"
    else:
        scope = "brief"
    convergence_id = "conv_" + hashlib.sha256(
        "|".join(str(event.get("event_id") or "") for event in canonical_cluster).encode("utf-8")
    ).hexdigest()[:16]
    marker_count = max(1, min(6, len({
        str(event.get("transiting_body") or event.get("transit_planet") or "").strip()
        for event in canonical_cluster
        if str(event.get("transiting_body") or event.get("transit_planet") or "").strip()
    })))
    shared_emphasis = _convergence_shared_emphasis(field_focus, territories)
    peak_dt = canonical_cluster[len(canonical_cluster) // 2].get("peak_datetime")
    return {
        "convergence_id": convergence_id,
        "event_type": "convergence_window",
        "tone": "convergence",
        "event_label": "Convergence Window",
        "title": _convergence_title(pattern),
        "start_date": _iso_date_or_none(start_dt),
        "end_date": _iso_date_or_none(end_dt),
        "date_label": _convergence_date_label(start_dt, end_dt),
        "scope": scope,
        "scope_label": _convergence_scope_label(scope),
        "field_focus": field_focus,
        "activated_territories": territories[:3],
        "constituent_event_ids": [str(event.get("event_id") or "") for event in canonical_cluster if str(event.get("event_id") or "").strip()],
        "selection_rationale": _convergence_selection_rationale(canonical_cluster, relationship_labels, territories, field_focus),
        "reader_synthesis": block_text,
        "crosses_month_boundary": crosses_month_boundary,
        "shared_emphasis": shared_emphasis,
        "participating_conditions": participating_conditions[:4],
        "participating_condition_line": " · ".join(participating_conditions[:4]),
        "participating_markers": "▲" * marker_count,
        "subtitle": _convergence_scope_label(scope),
        "peak_datetime": peak_dt,
        "entry_datetime": start_dt,
        "leave_datetime": end_dt,
        "peak_date": _convergence_date_label(peak_dt, peak_dt),
        "display_anchor_date": _convergence_date_label(start_dt, end_dt),
        "combined_intensity_score": 0.0,
        "priority": "A",
        "block": block_text,
        "constellation_lens": "",
        "constellation_lens_label": "",
    }


def _is_convergence_anchor_event(event: dict) -> bool:
    event_type = _year_ahead_primary_event_type(event)
    if event_type in {"planetary_station", "eclipse", "lunation"}:
        return True
    if event_type == "house_ingress":
        return str(event.get("transit_planet") or "").strip() in {
            "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Mars"
        }
    if event_type != "natal_transit":
        return False
    orb = abs(float(event.get("orb", 0.0) or 0.0))
    duration = float(event.get("duration_days", 0.0) or 0.0)
    contacts = int(event.get("contact_count", 0) or 0)
    return orb <= 1.0 or duration >= 42 or contacts > 1


def _classify_convergence_pattern(cluster: list) -> str:
    house_counts: dict[int, int] = {}
    planets: list[str] = []

    for event in cluster:
        house = event.get("natal_house") or event.get("house_number")
        if house:
            house_counts[int(house)] = house_counts.get(int(house), 0) + 1
        planet = event.get("transit_planet", "")
        if planet:
            planets.append(planet)

    dominant_house = max(house_counts, key=lambda h: house_counts[h]) if house_counts else 0

    if dominant_house == 12 or ("Moon" in planets and "Mercury" in planets):
        return "private_signal_convergence"
    if dominant_house == 10 or ("Mars" in planets and "Saturn" in planets):
        return "public_emergence_convergence"
    if dominant_house == 7 or ("Moon" in planets and "Venus" in planets):
        return "relational_recalibration_convergence"
    if dominant_house == 5 or "Mars" in planets:
        return "creative_catalyst_convergence"
    if dominant_house == 1 or "Sun" in planets:
        return "identity_emergence_convergence"
    if dominant_house == 4 or "Saturn" in planets:
        return "foundation_rebuild_convergence"
    return "default"


def _detect_and_frame_convergences_legacy_dead(
    all_events:   list,
    pack_paths:   dict,
    conv_tracker: "_VariantTracker",
    house_domains: dict,
    birth_time_status: str,
    window_days:  int = 14,
) -> list:
    """
    Find conservative overlap windows among independently selected ordinary
    events and produce separate convergence objects when they share at least
    one meaningful structural relationship.
    """
    path = pack_paths.get("convergence_blocks", "")
    if not path:
        return []
    raw = _load_json_file(path)
    if not raw:
        return []
    patterns_lib = raw.get("convergence_patterns", raw)

    # Only non-synthetic events with a peak date participate in clustering.
    qualifying = [
        e for e in all_events
        if e.get("peak_datetime") is not None
        and not _event_type_matches(e, "convergence", "convergence_window")
    ]
    if not qualifying:
        return []

    dated_sorted = sorted(qualifying, key=lambda e: e["peak_datetime"])
    window       = timedelta(days=window_days)
    results: list[dict] = []
    consumed_ids: set[int] = set()

    for anchor in dated_sorted:
        anchor_id = id(anchor)
        if anchor_id in consumed_ids:
            continue

        anchor_dt = anchor["peak_datetime"]
        cluster = [anchor]
        relationship_labels: list[str] = []
        for candidate in dated_sorted:
            if candidate is anchor:
                continue
            if id(candidate) in consumed_ids:
                continue
            candidate_dt = candidate.get("peak_datetime")
            if candidate_dt is None or candidate_dt > anchor_dt + window:
                continue
            if not _convergence_dates_link(anchor, candidate):
                continue
            shared_relationships = _convergence_relationship_details(
                anchor,
                candidate,
                house_domains,
                birth_time_status,
            )
            if not shared_relationships:
                continue
            cluster.append(candidate)
            for label in shared_relationships:
                if label not in relationship_labels:
                    relationship_labels.append(label)

        if len(cluster) < _CONVERGENCE_MIN_EVENTS:
            continue

        if len(relationship_labels) < _CONVERGENCE_SHARED_RELATIONSHIP_MIN:
            continue

        if not any(_is_convergence_anchor_event(e) for e in cluster):
            continue

        # Consume all cluster members to prevent overlapping cards.
        for e in cluster:
            consumed_ids.add(id(e))

        pattern  = _classify_convergence_pattern(cluster)
        variants = patterns_lib.get(pattern, [])
        if isinstance(variants, str):
            variants = [variants]

        pool_key   = f"convergence:{pattern}"
        block_text = conv_tracker.pick(pool_key, variants)

        # Do not emit an empty card.
        if not block_text:
            continue

        # Date range spans the first to last peak_datetime in the cluster.
        first_dt = cluster[0]["peak_datetime"]
        last_dt  = cluster[-1]["peak_datetime"]
        peak_dt  = cluster[len(cluster) // 2]["peak_datetime"]
        date_range = (
            f"{first_dt.strftime('%B %d')} – {last_dt.strftime('%B %d, %Y')}"
            if first_dt.date() != last_dt.date() else first_dt.strftime("%B %d, %Y")
        )

        results.append({
            "event_type":   "convergence",
            "tone":         "convergence",
            "event_label":  "Convergence Window",
            "title":        _convergence_title(pattern),
            "subtitle":     date_range,
            "date_label":   peak_dt.strftime("%B %d, %Y"),
            "peak_date":    peak_dt.strftime("%B %d, %Y"),
            "peak_datetime":   peak_dt,
            "entry_datetime":  first_dt,
            "leave_datetime":  last_dt,
            "duration_descriptor":      "",
            "intensity_label":          "Convergence",
            "intensity_bar":            "▲▲▲",
            "combined_intensity_score": 0.0,
            "priority":                 "A",
            "block":                    block_text,
            "constellation_lens":       "",
            "constellation_lens_label": "",
            "convergence_pattern":      pattern,
            "constituent_events":       cluster,
        })

    return results


def _detect_and_frame_convergences(
    all_events: list,
    pack_paths: dict,
    conv_tracker: "_VariantTracker",
    house_domains: dict,
    birth_time_status: str,
    window_days: int = 14,
) -> list:
    """
    Conservative convergence detector.

    Threshold:
    - at least 2 independently selected ordinary events
    - overlapping active dates or <=5-day proximity
    - at least 1 shared structural relationship
    - at least 1 structurally weighty anchor event in the cluster
    """
    path = pack_paths.get("convergence_blocks", "")
    if not path:
        return []
    raw = _load_json_file(path)
    if not raw:
        return []
    patterns_lib = raw.get("convergence_patterns", raw)

    qualifying = [
        event for event in all_events
        if event.get("peak_datetime") is not None
        and not _event_type_matches(event, "convergence", "convergence_window")
    ]
    if not qualifying:
        return []

    dated_sorted = sorted(qualifying, key=lambda event: event["peak_datetime"])
    window = timedelta(days=window_days)
    results: list[dict] = []
    consumed_ids: set[int] = set()

    for anchor in dated_sorted:
        if id(anchor) in consumed_ids:
            continue

        anchor_dt = anchor["peak_datetime"]
        cluster = [anchor]
        relationship_labels: list[str] = []

        for candidate in dated_sorted:
            if candidate is anchor:
                continue
            if id(candidate) in consumed_ids:
                continue
            candidate_dt = candidate.get("peak_datetime")
            if candidate_dt is None or candidate_dt > anchor_dt + window:
                continue
            if not _convergence_dates_link(anchor, candidate):
                continue
            shared_relationships = _convergence_relationship_details(
                anchor,
                candidate,
                house_domains,
                birth_time_status,
            )
            if not shared_relationships:
                continue
            cluster.append(candidate)
            for label in shared_relationships:
                if label not in relationship_labels:
                    relationship_labels.append(label)

        if len(cluster) < _CONVERGENCE_MIN_EVENTS:
            continue
        if len(relationship_labels) < _CONVERGENCE_SHARED_RELATIONSHIP_MIN:
            continue
        if not any(_is_convergence_anchor_event(event) for event in cluster):
            continue

        for event in cluster:
            consumed_ids.add(id(event))

        pattern = _classify_convergence_pattern(cluster)
        variants = patterns_lib.get(pattern, [])
        if isinstance(variants, str):
            variants = [variants]
        block_text = conv_tracker.pick(f"convergence:{pattern}", variants)
        if not block_text:
            continue

        results.append(
            _build_convergence_window(
                cluster,
                pattern,
                block_text,
                house_domains,
                birth_time_status,
                relationship_labels,
            )
        )

    return results


def _validate_year_ahead_render_contract(context: dict) -> None:
    errors: list[str] = []
    allowed_types = set(_YEAR_AHEAD_ALLOWED_EVENT_TYPES)

    rendered_events: list[dict] = []
    for month in context.get("months", []) or []:
        rendered_events.extend(month.get("events", []) or [])
    rendered_events.extend(context.get("landmarks", []) or [])

    for event in rendered_events:
        event_type = str(event.get("event_type") or "").strip()
        event_id = str(event.get("event_id") or event.get("title") or "<unknown>")
        if event_type not in allowed_types:
            errors.append(f"Invalid event_type for rendered event {event_id}: {event_type or '<blank>'}")
            continue
        if event_type == "convergence_window":
            if str(event.get("display_status") or "").strip() not in {"", "not_applicable"}:
                errors.append(f"Convergence window {event_id} carries ordinary display_status.")
            if str(event.get("display_status_source") or "").strip() not in {"", "not_applicable"}:
                errors.append(f"Convergence window {event_id} carries a display_status_source.")
            if str(event.get("intensity_label") or "").strip():
                errors.append(f"Convergence window {event_id} still carries an intensity label.")

    if not context.get("show_landmark_visuals", False):
        # Forecast Shape visuals are standard, non-landmark content (derived from
        # arc_score / combined_intensity_score, not landmark data) and are
        # intentionally independent of the EO Landmark visuals flag.
        strongest = context.get("orientation_summary", {}).get("strongest_annual_themes", []) or []
        if strongest:
            errors.append("Landmark-derived strongest annual themes remain exposed while EO Landmark visuals are disabled.")

    forecast_climate = context.get("forecast_climate", {}) or {}
    for field in forecast_climate.get("fields", []) or []:
        for text in [
            field.get("block", ""),
            field.get("summary_line", ""),
            field.get("field_label", ""),
        ]:
            if re.search(r"\b(?:domain|target|planet):", str(text), re.IGNORECASE):
                errors.append(f"Raw internal metadata leaked into Forecast Climate field {field.get('field_key', '<unknown>')}.")
                break
        for support in field.get("supporting_events", []) or []:
            for text in [support.get("title", ""), support.get("timing_note", ""), support.get("event_label", "")]:
                if re.search(r"\b(?:domain|target|planet):", str(text), re.IGNORECASE):
                    errors.append(f"Raw internal metadata leaked into supporting event {support.get('event_id', '<unknown>')}.")
                    break

    if str(context.get("year_arc_sort_basis") or "").strip() == "landmark_score":
        errors.append("Client-facing Year Arcs are still marked as sorted by Landmark score.")
    for month in context.get("months", []) or []:
        if str(month.get("event_sort_basis") or "").strip() == "landmark_score":
            errors.append(f"Monthly chapter {month.get('name', '<unknown>')} is still marked as sorted by Landmark score.")
        for item in month.get("major_timing_windows", []) or []:
            text = " ".join(str(item.get(key) or "") for key in ("title", "event_label", "subtitle"))
            if re.search(r"\bconvergence\b", text, re.IGNORECASE):
                errors.append(f"Monthly chapter {month.get('name', '<unknown>')} still mixes convergence windows into major timing windows.")
        for item in month.get("convergence_windows", []) or []:
            text = " ".join(str(item.get(key) or "") for key in ("title", "shared_emphasis", "scope_label"))
            if re.search(r"\b(?:domain|target|planet):", text, re.IGNORECASE):
                errors.append(f"Raw internal metadata leaked into convergence windows for {month.get('name', '<unknown>')}.")

    raw_cycle_ledger = context.get("raw_cycle_ledger", {}) or {}
    if raw_cycle_ledger:
        for month in raw_cycle_ledger.get("months", []) or []:
            for entry in month.get("entries", []) or []:
                combined_text = " ".join(
                    str(entry.get(key) or "")
                    for key in [
                        "title",
                        "event_type_label",
                        "astrological_status",
                        "target_house",
                        "cycle_structure",
                        "related_convergence",
                    ]
                )
                if re.search(r"\blandmark\b", combined_text, re.IGNORECASE):
                    errors.append(f"Landmark terminology leaked into Cycle Ledger row {entry.get('title', '<unknown>')}.")
                if re.search(r"\b(?:domain|target|planet):", combined_text, re.IGNORECASE):
                    errors.append(f"Raw internal metadata leaked into Cycle Ledger row {entry.get('title', '<unknown>')}.")
                if re.search(r"\bya_[a-z_0-9]+\b", combined_text, re.IGNORECASE):
                    errors.append(f"Internal event identifier leaked into Cycle Ledger row {entry.get('title', '<unknown>')}.")
        for section in raw_cycle_ledger.get("structure_notes", []) or []:
            for row in section.get("rows", []) or []:
                row_text = " ".join(str(cell or "") for cell in row)
                if re.search(r"\blandmark\b", row_text, re.IGNORECASE):
                    errors.append(f"Landmark terminology leaked into Event Structure Notes section {section.get('title', '<unknown>')}.")
                if re.search(r"\b(?:domain|target|planet):", row_text, re.IGNORECASE):
                    errors.append(f"Raw internal metadata leaked into Event Structure Notes section {section.get('title', '<unknown>')}.")
        for row in raw_cycle_ledger.get("convergence_index", []) or []:
            row_text = " ".join(str(row.get(key) or "") for key in ("window", "title", "shared_emphasis", "participating_conditions", "activated_territories"))
            if re.search(r"\blandmark\b", row_text, re.IGNORECASE):
                errors.append(f"Landmark terminology leaked into Convergence Index row {row.get('title', '<unknown>')}.")
            if re.search(r"\b(?:domain|target|planet):", row_text, re.IGNORECASE):
                errors.append(f"Raw internal metadata leaked into Convergence Index row {row.get('title', '<unknown>')}.")
            if re.search(r"\b(?:background|active|significant|key window)\b", row_text, re.IGNORECASE):
                errors.append(f"Convergence Index row {row.get('title', '<unknown>')} still uses ordinary intensity language.")

    if errors:
        raise ValueError("Year Ahead render contract validation failed:\n- " + "\n- ".join(errors))


def _build_year_ahead_curated_summaries(
    forecast_shape_details: dict,
    orientation_summary: dict,
    season_summaries: list[dict],
    forecast_climate: dict,
) -> dict:
    shape = _safe_mapping(forecast_shape_details)
    orientation = _safe_mapping(orientation_summary)
    climate = _safe_mapping(forecast_climate)

    seasonal_highlights = []
    for season in _safe_sequence(season_summaries)[:4]:
        season_map = _safe_mapping(season)
        seasonal_highlights.append(
            {
                "title": str(season_map.get("title") or ""),
                "months_label": str(season_map.get("months_label") or ""),
                "summary": str(season_map.get("summary") or ""),
                "peak_month": str(season_map.get("peak_month") or ""),
                "dominant_domains": str(season_map.get("dominant_domains") or ""),
            }
        )

    climate_highlights = []
    ranked_fields = sorted(
        _safe_sequence(climate.get("fields")),
        key=lambda field: (
            _safe_float(_safe_mapping(field).get("normalized_score"), 0.0),
            _safe_float(_safe_mapping(field).get("raw_score"), 0.0),
        ),
        reverse=True,
    )
    for rank, field in enumerate(ranked_fields[:3], start=1):
        field_map = _safe_mapping(field)
        climate_highlights.append(
            {
                "rank": rank,
                "field_key": str(field_map.get("field_key") or ""),
                "field_label": str(field_map.get("field_label") or ""),
                "band_label": str(field_map.get("band_label") or ""),
                "signal_family_label": str(field_map.get("signal_family_label") or ""),
                "summary_line": str(field_map.get("summary_line") or ""),
                "supporting_event_titles": [
                    str(_safe_mapping(event).get("title") or "")
                    for event in _safe_sequence(field_map.get("supporting_events"))[:2]
                    if str(_safe_mapping(event).get("title") or "").strip()
                ],
            }
        )

    return {
        "forecast_shape": {
            "label": str(shape.get("label") or ""),
            "peak_month": str(shape.get("peak_month") or ""),
            "quiet_month": str(shape.get("quiet_month") or ""),
            "peak_season": str(shape.get("peak_season") or ""),
            "curve_note": str(shape.get("curve_note") or ""),
            "confidence_note": str(shape.get("confidence_note") or ""),
        },
        "orientation": {
            "highest_concentration_period": str(orientation.get("highest_concentration_period") or ""),
            "quietest_period": str(orientation.get("quietest_period") or ""),
            "long_cycle_emphasis": str(orientation.get("long_cycle_emphasis") or ""),
            "shape_explanation": str(orientation.get("shape_explanation") or ""),
        },
        "seasonal_highlights": seasonal_highlights,
        "climate_highlights": climate_highlights,
    }


def _build_year_ahead_context(
    variables: dict,
    index_results: dict,
    payload: dict,
    report_start: datetime | None = None,
    report_end: datetime | None = None,
    content_pack: str = "plainspeak",
    standard_report_bundle: dict | None = None,
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
    standard_report_bundle = standard_report_bundle or {}

    report_start = report_start or datetime.now(timezone.utc)
    report_end = report_end or _add_one_year(report_start)

    _log_verbose("[Timeline] Scanning 12-month transit events...")
    timeline = compute_year_ahead_events(
        payload,
        start_date=report_start,
        end_date=report_end,
        include_year_texture=True,
    )

    all_events     = timeline.get("all_events", [])
    transit_events = timeline.get("transits", [])
    year_texture_progressions = timeline.get("year_texture_progressions", [])
    year_texture_solar_arc = timeline.get("year_texture_solar_arc", [])

    # ── EO_TRANSIT_TRACE — terminal-only diagnostic, not written to HTML ──
    _TRANSIT_TRACE = _env_flag("EO_TRANSIT_TRACE")
    if _TRANSIT_TRACE:
        multi_contact = [e for e in transit_events if e.get("contact_count", 0) > 1]
        print(f"[Transit Engine] {len(transit_events)} transit cycle(s) found")
        print(f"[Transit Engine] {sum(e.get('contact_count', 0) for e in transit_events)} refined contact(s) total")
        print(f"[Transit Engine] {len(multi_contact)} multi-contact cycle(s)")
        for event in transit_events:
            cid      = event.get("cycle_id", "?")
            planet   = event.get("transit_planet", "?")
            aspect   = event.get("aspect", "?")
            target   = event.get("natal_target", "?")
            cs_date  = event.get("cycle_start_date") or event.get("entry_date", "?")
            ce_date  = event.get("cycle_end_date") or event.get("leave_date", "(ongoing)")
            contacts = event.get("contacts", [])
            anchor   = event.get("display_anchor_date") or event.get("peak_date", "?")
            print(f"[Transit Cycle]")
            print(f"  id={cid}")
            print(f"  {planet} {aspect} natal {target}")
            print(f"  active={cs_date} through {ce_date}")
            print(f"  contacts={len(contacts)}")
            for c in contacts:
                print(f"  {c['sequence_index']} {c['motion_direction']} {c['contact_date']}")
            print(f"  display_anchor={anchor}")

    # ── EO_SCORE_TRACE — per-cycle and per-month scoring breakdown ──
    _SCORE_TRACE = _env_flag("EO_SCORE_TRACE")
    if _SCORE_TRACE:
        print("[Score Trace] Per-cycle breakdown (concentration -> tier | structural -> landmark eligibility)")
        print(f"  {'Transit':<40} {'Dur':>6} {'Orb':>5} {'Base':>6} {'DurMod':>7} {'Struct':>7} {'Conc':>6}  Tier")
        print(f"  {'-'*40} {'-'*6} {'-'*5} {'-'*6} {'-'*7} {'-'*7} {'-'*6}  ----")
        for _ev in transit_events:
            _pln  = _ev.get("transit_planet", "?")
            _asp  = _ev.get("aspect", "?")
            _tgt  = _ev.get("natal_target", "?")
            _lbl  = f"{_pln} {_asp} {_tgt}"
            _dur  = _ev.get("_duration_days") or _ev.get("duration_days", 0.0)
            _orb  = _ev.get("_best_orb") or _ev.get("orb", 0.0)
            _base = _ev.get("concentration_score") or _ev.get("raw_score", 0.0)
            _dmod = _ev.get("_duration_modifier", 1.0)
            _str  = _ev.get("structural_score", 0.0)
            _con  = _ev.get("combined_intensity_score", 0.0)
            _tier = _ev.get("intensity_label", "?")
            print(f"  {_lbl:<40} {_dur:>6.0f} {_orb:>5.2f} {_base:>6.3f} {_dmod:>7.3f} {_str:>7.3f} {_con:>6.3f}  {_tier}")

    # Load refraction library once; build the shared lens context.
    _refraction_raw = _load_json_file(pack.get("refraction_bridges", ""))
    _refraction_lib = _refraction_raw.get("refraction_bridges", {})
    lens_ctx    = _LensContext(index_results, _refraction_lib)
    conv_tracker = _VariantTracker()

    # Shared set — tracks which cycle_ids have already received a prose block.
    # Landmarks render first; the monthly arc suppresses repeated prose.
    rendered_cycle_ids: set = set()
    birth_meta = _build_birth_metadata(payload)

    convergence_events = _detect_and_frame_convergences(
        all_events,
        pack,
        conv_tracker,
        HOUSE_DOMAINS,
        birth_meta["birth_time_status"],
    )
    all_events = list(all_events) + convergence_events

    # A "landmark" is intentionally only a sustained, high-intensity natal transit.
    # Landmarks represent sustained developmental themes, so they are selected
    # by structural_score (concentration × duration weight) rather than
    # concentration_score alone.  This preserves long-running outer-planet
    # cycles as landmarks while the reader-facing tier label uses concentration.
    landmark_candidates = [
        event
        for event in transit_events
        if (
            event.get("transit_planet") != "Mars"
            and event.get("structural_score", event.get("combined_intensity_score", 0.0)) >= LANDMARK_MIN_SCORE
            and event.get("duration_days", 0.0) >= LANDMARK_MIN_DAYS
        )
    ]

    landmark_candidates.sort(
        key=lambda event: (
            event.get("structural_score", event.get("combined_intensity_score", 0.0)),
            event.get("duration_days", 0.0),
        ),
        reverse=True,
    )

    year_arc_candidates = [
        event
        for event in transit_events
        if (
            _event_type_matches(event, "transit", "natal_transit")
            and event.get("transit_planet") != "Mars"
            and float(event.get("duration_days", 0.0) or 0.0) >= LANDMARK_MIN_DAYS
        )
    ]
    year_arc_candidates.sort(
        key=lambda event: (
            float(event.get("duration_days", 0.0) or 0.0),
            int(event.get("contact_count", 0) or 0),
            -abs(float(event.get("orb", 99.0) or 99.0)),
            float(event.get("combined_intensity_score", 0.0) or 0.0),
        ),
        reverse=True,
    )

    landmarks = [
        _format_timeline_event(event, HOUSE_DOMAINS, pack, standard_report_bundle, payload, index_results, lens_ctx,
                               rendered_cycle_ids=rendered_cycle_ids)
        for event in year_arc_candidates[:LANDMARK_MAX_COUNT]
    ]

    # Progressions & Solar Arc run on their own season-scale clock (chapter-role,
    # ~60-90 day windows) and are never folded into all_events/months, so they
    # get their own formatted card lists for a dedicated "Year Texture" section.
    year_texture_progressions = [
        _format_timeline_event(event, HOUSE_DOMAINS, pack, standard_report_bundle, payload, index_results, lens_ctx,
                               rendered_cycle_ids=rendered_cycle_ids)
        for event in year_texture_progressions
    ]
    year_texture_solar_arc = [
        _format_timeline_event(event, HOUSE_DOMAINS, pack, standard_report_bundle, payload, index_results, lens_ctx,
                               rendered_cycle_ids=rendered_cycle_ids)
        for event in year_texture_solar_arc
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
    used_snapshot_blocks: set[str] = set()

    for offset in range(12):
        period_start = _add_months(report_start, offset)
        period_end = min(_add_months(report_start, offset + 1), report_end)

        # The monthly chronology is organized by an event's exact/peak date,
        # not by the day a long transit first entered orb. That keeps December
        # events out of June's chapter while the overview still preserves the
        # long-running context.
        events_peaking = []
        events_active = []
        for event in all_events:
            peak_datetime = event.get("peak_datetime")
            if peak_datetime is not None and period_start <= peak_datetime < period_end:
                events_peaking.append(event)
            if _interval_overlaps(
                event.get("entry_datetime"),
                event.get("leave_datetime"),
                period_start,
                period_end,
            ):
                events_active.append(event)

        selected_events = _filter_monthly_events(events_peaking)
        formatted_events = [
            _format_timeline_event(event, HOUSE_DOMAINS, pack, standard_report_bundle, payload, index_results, lens_ctx,
                                   rendered_cycle_ids=rendered_cycle_ids)
            for event in selected_events
        ]

        peak_score = _monthly_peak_score(
            events_active,
            period_start,
            period_end,
        )
        monthly_peak_diagnostics = _monthly_peak_diagnostics(
            events_active,
            period_start,
            period_end,
        )
        intensity_label, intensity_bar = _intensity_label(peak_score)

        if _SCORE_TRACE:
            _month_name = period_start.strftime("%B %Y")
            _scored = sorted(
                (
                    (e, _event_month_relevance(e, period_start, period_end))
                    for e in events_active
                ),
                key=lambda x: x[1],
                reverse=True,
            )
            _top = _scored[:3]
            _contributors = ", ".join(
                f"{e.get('transit_planet','?')} {e.get('aspect','')}{' '+e.get('natal_target','') if e.get('natal_target') else ''} ({s:.3f})"
                for e, s in _top if s > 0
            ) or "none"
            print(f"[Month Score] {_month_name}: arc_score={peak_score:.3f}  tier={intensity_label}  top={_contributors}")
        snapshot_block, month_planet, month_character = _snapshot_for_month(
            events_active,
            period_start,
            period_end,
            pack,
            used_snapshot_blocks,
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
                "monthly_peak_diagnostics": monthly_peak_diagnostics,
                "arc_percent": max(2, round(peak_score * 100)),
                "arc_label": intensity_label,
                "arc_bar": intensity_bar,
                "event_sort_basis": "chronology_then_standard_intensity",
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

    # ── Natal chart wheel ───────────────────────────────────────
    chart_wheel_data = None
    chart_wheel_svg = ""
    wheel_transit_retrograde_planets = []
    has_exact_birth_time = _has_exact_birth_time(payload)
    if has_exact_birth_time:
        try:
            from engine.chart_wheel import build_chart_wheel_data, render_natal_wheel_svg
            from engine.transit_engine import current_retrograde_planets
            transit_rx = current_retrograde_planets(report_start)
            chart_wheel_data = build_chart_wheel_data(
                payload, report_type="year_ahead", current_retrograde=transit_rx
            )
            if chart_wheel_data:
                chart_wheel_svg = render_natal_wheel_svg(chart_wheel_data, compact=False)
                wheel_transit_retrograde_planets = sorted(
                    b["name"] for b in chart_wheel_data.get("bodies", [])
                    if b.get("currently_retrograde")
                )
        except Exception as _cw_err:
            print(f"[ChartWheel] Skipped (non-fatal): {_cw_err}")

    # Retrograde cluster climate note: is a stretch of 2+ simultaneous
    # retrogrades active right now (at report_start)? Same pattern as
    # Personal Forecast — additive/optional, non-fatal on failure.
    retrograde_cluster_active = False
    retrograde_cluster_tier = ""
    retrograde_cluster_planets = []
    retrograde_cluster_block = ""
    try:
        from engine.transit_engine import detect_retrograde_clusters
        from selectors.block_selector import select_block_from_path
        ya_clusters = detect_retrograde_clusters(payload, report_start, report_end)
        ya_current_cluster = next(
            (c for c in ya_clusters if c["start"] <= report_start <= c["end"]),
            None,
        )
        if ya_current_cluster:
            retrograde_cluster_active = True
            retrograde_cluster_tier = ya_current_cluster["tier"]
            retrograde_cluster_planets = ya_current_cluster["planets"]
            ya_variant_index = sum(ord(ch) for ch in "".join(retrograde_cluster_planets)) % 3
            ya_variant_key = ["v1", "v2", "v3"][ya_variant_index]
            retrograde_cluster_block = _usable_block(
                select_block_from_path(
                    pack["retrograde_cluster_blocks"], retrograde_cluster_tier, ya_variant_key,
                    fallback=select_block_from_path(pack["retrograde_cluster_blocks"], "fallback"),
                )
            )
    except Exception as _retrograde_cluster_error:
        print(f"[RetrogradeCluster] Skipped (non-fatal): {_retrograde_cluster_error}")

    # Void-of-Course Moon note: the next (or currently active) VOC window
    # from report_start. Same pattern as Personal Forecast.
    voc_next_active = False
    voc_next_tier = ""
    voc_next_start = None
    voc_next_duration_hours = 0.0
    voc_next_block = ""
    try:
        from engine.transit_engine import detect_void_of_course_windows
        from selectors.block_selector import select_block_from_path
        ya_voc_windows = detect_void_of_course_windows(report_start, report_end)
        ya_next_voc = next(
            (w for w in ya_voc_windows if w["end"] >= report_start),
            None,
        )
        if ya_next_voc:
            voc_next_active = True
            voc_next_tier = ya_next_voc["tier"]
            voc_next_start = ya_next_voc["start"]
            voc_next_duration_hours = ya_next_voc["duration_hours"]
            ya_voc_variant_index = int(ya_next_voc["duration_hours"] * 10) % 3
            ya_voc_variant_key = ["v1", "v2", "v3"][ya_voc_variant_index]
            voc_next_block = _usable_block(
                select_block_from_path(
                    pack["void_of_course_moon_blocks"], voc_next_tier, ya_voc_variant_key,
                    fallback=select_block_from_path(pack["void_of_course_moon_blocks"], "fallback"),
                )
            )
    except Exception as _voc_error:
        print(f"[VoidOfCourse] Skipped (non-fatal): {_voc_error}")

    months = _augment_months_for_template(months, landmarks)
    landmarks = _augment_landmarks(landmarks, months)
    turning_point_timeline = _build_turning_point_timeline(months, landmarks)
    chart_characteristics = _build_chart_characteristics(payload)
    standard_natal_foundation = _build_standard_natal_foundation(
        standard_report_bundle,
        payload,
        pack,
        HOUSE_DOMAINS,
    )
    calculation_record = _build_calculation_record(payload, variables, report_start, report_end)
    season_summaries = _build_season_summaries(months)
    annual_rhythm_quarters = _build_annual_rhythm_quarters(months, all_events, HOUSE_DOMAINS)
    forecast_shape_details = _build_forecast_shape_details(months, birth_meta["birth_time_status"])
    for month, detail in zip(months, forecast_shape_details.get("months", [])):
        month["shape_percent"] = detail.get("display_value", 0)
    _max_events = max((m["event_count"] for m in months), default=1) or 1
    for m in months:
        m["event_count_percent"] = max(4, round(m["event_count"] / _max_events * 100))
    orientation_summary = _build_year_orientation_summary(
        months,
        landmarks,
        dominant_planet,
        forecast_shape_details,
    )
    raw_cycle_ledger = _build_raw_cycle_ledger(
        months,
        all_events,
        HOUSE_DOMAINS,
    )
    forecast_climate = _build_forecast_climate(
        transit_events,
        all_events,
        convergence_events,
        landmarks,
        HOUSE_DOMAINS,
        birth_meta["birth_time_status"],
        pack,
    )
    predictive_evidence_events = (
        all_events
        + year_texture_progressions
        + year_texture_solar_arc
        + timeline.get("return_events", [])
        + timeline.get("zodiacal_releasing_events", [])
        + timeline.get("time_lord_periods", [])
    )
    forecast_synthesis = build_forecast_synthesis(
        predictive_evidence_events,
        report_start=report_start,
        report_end=report_end,
        months=months,
        house_domains=HOUSE_DOMAINS,
    )
    tier5_predictive_surfaces = _build_tier5_year_ahead_surfaces(
        timeline,
        forecast_synthesis,
        pack,
    )
    ledger_months = _build_ledger_months(months)

    from config import PALETTES as _PALETTES
    __ya_palette_name = variables.get("palette", "vibrant")
    __ya_palette = _PALETTES.get(__ya_palette_name, _PALETTES["vibrant"])
    _generation_date = datetime.now().strftime("%B %d, %Y")

    context = {
        "natal_positions": _build_natal_positions(payload),
        "chart_characteristics": chart_characteristics,
        "standard_natal_foundation": standard_natal_foundation,
        "house_system": variables.get("house_system", "Whole Sign"),
        "archetypal_opening_section": _generate_archetypal_opening(
            payload, index_results, pack, dominant_planet, dominant_character
        ),
        "tropical_zodiac": birth_meta["tropical_zodiac"],
        "methodology_id": birth_meta["methodology_id"],
        "methodology_label": birth_meta["methodology_label"],
        "zodiac_label": birth_meta["zodiac_label"],
        "house_system_label": birth_meta["house_system_label"],
        "methodology_summary": birth_meta["methodology_summary"],
        "timeline_start": timeline.get("report_start"),
        "timeline_end": timeline.get("report_end"),
        "timeline_event_count": len(all_events),
        "landmarks": landmarks,
        # Compatibility alias for any downstream code still using the old key.
        "landmark_influences": landmarks,
        "turning_point_timeline": turning_point_timeline,
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
        "year_texture_progressions": year_texture_progressions,
        "year_texture_solar_arc": year_texture_solar_arc,
        "forecast_shape": forecast_shape_details["label"],
        "forecast_shape_details": forecast_shape_details,
        "year_ahead_curated_summaries": _build_year_ahead_curated_summaries(
            forecast_shape_details,
            orientation_summary,
            season_summaries,
            forecast_climate,
        ),
        "forecast_climate": forecast_climate,
        "forecast_synthesis": forecast_synthesis,
        "tier5_predictive_surfaces": tier5_predictive_surfaces,
        "year_arc_sort_basis": "ordinary_salience_duration_then_timing",
        "season_summaries": season_summaries,
        "annual_rhythm_quarters": annual_rhythm_quarters,
        "orientation_summary": orientation_summary,
        "raw_cycle_ledger": raw_cycle_ledger,
        "calculation_record": calculation_record,
        "ledger_months": ledger_months,
        "active_transit_count": len(transit_events),
        "chart_wheel_data": chart_wheel_data,
        "chart_wheel_svg": chart_wheel_svg,
        "wheel_transit_retrograde_planets": wheel_transit_retrograde_planets,
        "birth_date_display": birth_meta["birth_date_display"],
        "birth_time_display": birth_meta["birth_time_display"],
        "birth_location":     birth_meta["birth_location"],
        "generation_date":    _generation_date,
        "birth_time_status":  birth_meta["birth_time_status"],
        "birth_time_state": birth_meta["birth_time_state"],
        "birth_time_confidence": birth_meta["birth_time_confidence"],
        "palette_name":       __ya_palette_name,
        "palette":            __ya_palette,
        "predictive_results": variables.get("predictive_results", {}),
        "predictive_report_surface": _build_predictive_report_surface(
            variables.get("predictive_sidecar", {}),
            "year_ahead",
            forecast_synthesis,
            pack,
        ),
        "report_version":     "Year Ahead v2.0",
        "show_landmark_visuals": SHOW_LANDMARK_VISUALS,
        "show_forecast_shape_visuals": SHOW_FORECAST_SHAPE_VISUALS,
        "retrograde_cluster_active":  retrograde_cluster_active,
        "retrograde_cluster_tier":    retrograde_cluster_tier,
        "retrograde_cluster_planets": retrograde_cluster_planets,
        "retrograde_cluster_block":   retrograde_cluster_block,
        "voc_next_active":         voc_next_active,
        "voc_next_tier":           voc_next_tier,
        "voc_next_start_display":  voc_next_start.strftime("%B %d, %Y, %I:%M %p UTC") if voc_next_start else "",
        "voc_next_duration_hours": voc_next_duration_hours,
        "voc_next_block":          voc_next_block,
    }

    _validate_year_ahead_render_contract(context)
    return context



# ── Template Rendering ─────────────────────────────────────────

def render_template(report_type: str, context: dict) -> str:
    """Renders a Jinja2 HTML template with the given context."""
    render_context = dict(_build_render_defaults(context))
    render_context.update(context)

    template_map = {
        "horoscope":          "daily_horoscope/templates/daily_horoscope.html",
        "weekly_horoscope":   "weekly_horoscope/templates/weekly_horoscope.html",
        "year_ahead":         "year_ahead/templates/active/year_ahead.html",
        "personal_forecast":  "personal_forecast/templates/personal_forecast.html",
        "soul_ecosystem":     "soul_ecosystem/templates/soul_ecosystem.html",
        "identity_profile":   "identity_profile/templates/entangled_identity_profile.html",
    }
    if report_type not in template_map:
        raise ValueError(
            f"Unknown report_type '{report_type}' — no template mapping. "
            f"Valid types: {', '.join(sorted(template_map))}."
        )
    template_name = template_map[report_type]

    if not JINJA2_AVAILABLE:
        print("[Render] Jinja2 is not available — using plain-text fallback renderer.")
        return _render_fallback(report_type, render_context)

    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    try:
        template = env.get_template(template_name)
        return template.render(**render_context)
    except Exception as e:
        # The full traceback is printed so the failure is actually
        # diagnosable instead of a one-line "Template error" easy to lose
        # in the log, but a client-facing run still degrades to the
        # simplified fallback page rather than hard-crashing.
        import traceback as _tb
        print(f"[Render] Template error for '{report_type}': {e}")
        _tb.print_exc()
        return _render_fallback(report_type, context)


_SHARED_REPORT_CSS_PATH = os.path.join(TEMPLATES_DIR, "shared", "report_visual_system.css")
_PDF_WORKFLOW_DOC_PATH = os.path.join(TEMPLATES_DIR, "shared", "REPORT_PDF_WORKFLOW.md")


def _load_shared_report_css() -> str:
    try:
        with open(_SHARED_REPORT_CSS_PATH, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def _build_render_defaults(context: dict | None = None) -> dict:
    current = context or {}
    generation_date = current.get("generation_date", "")
    footer = "Entangled Oracle - Ksisti-Puck LLC"
    if generation_date:
        footer = f"{footer} - Generated {generation_date}"
    return {
        "shared_report_css": _load_shared_report_css(),
        "report_brand_line": "Entangled Oracle - Ksisti-Puck LLC",
        "report_footer_text": footer,
        "pdf_workflow": {
            "route": "browser_print",
            "approved_browser": "Chrome",
            "background_graphics_required": True,
            "html_is_source_of_truth": True,
            "workflow_doc_path": _PDF_WORKFLOW_DOC_PATH,
        },
    }


def _render_fallback(report_type: str, context: dict) -> str:
    """Simple fallback renderer when Jinja2 isn't available."""
    def _escape(value) -> str:
        return html.escape(str(value or ""), quote=True)

    def _render_fallback_sections(report_type: str, context: dict) -> list[str]:
        sections: list[str] = []

        if report_type == "soul_ecosystem":
            depth = context.get("soul_ecosystem_eas_depth", {})
            dominant = depth.get("dominant", {}) if isinstance(depth, dict) else {}
            if dominant.get("available"):
                sections.append("<h3>Pattern Depth</h3>")
                sections.append(
                    "<div class=\"block\">This layer can translate complexity into usable language when the dominant ecosystem signal is active.</div>"
                )

        if report_type == "year_ahead":
            curated = context.get("year_ahead_curated_summaries", {})
            if isinstance(curated, dict):
                seasonal = curated.get("seasonal_highlights", [])
                climate = curated.get("climate_highlights", [])
                if seasonal:
                    sections.append("<h3>Seasonal Highlights</h3>")
                    for item in seasonal:
                        if not isinstance(item, dict):
                            continue
                        sections.append(
                            f"<div class=\"block\"><strong>{_escape(item.get('title', ''))}</strong><br>{_escape(item.get('summary', ''))}</div>"
                        )
                if climate:
                    sections.append("<h3>Field Highlights</h3>")
                    for item in climate:
                        if not isinstance(item, dict):
                            continue
                        sections.append(
                            f"<div class=\"block\"><strong>{_escape(item.get('field_label', ''))}</strong><br>{_escape(item.get('summary_line', ''))}</div>"
                        )
                orientation = curated.get("orientation", {})
                if isinstance(orientation, dict) and orientation.get("long_cycle_emphasis"):
                    sections.append("<h3>Dominant long cycle</h3>")
                    sections.append(
                        f"<div class=\"block\">{_escape(orientation.get('long_cycle_emphasis', ''))}</div>"
                    )

        return sections

    merged = dict(_build_render_defaults(context))
    merged.update(context)

    fallback_html = f"""<!DOCTYPE html>
<html><head><title>{_escape(report_type)}</title>
<meta charset="utf-8">
<style>
  {merged.get('shared_report_css', '')}
  body {{ background: #0A0A0C; color: #E0E0E0; font-family: Georgia, serif;
          max-width: 800px; margin: 0 auto; padding: 40px 20px; }}
  h1 {{ color: #00FF88; }} h2 {{ color: #B088FF; }} h3 {{ color: #88BBFF; }}
  .block {{ margin: 20px 0; line-height: 1.8; }}
</style>
</head><body>
<h1>{_escape(merged.get('querent_name',''))}</h1>
<h2>{_escape(report_type.replace('_',' ').title())}</h2>
<p style="color:#888">{_escape(merged.get('generation_date',''))} · {_escape(merged.get('generation_location',''))}</p>
<p style="color:#888">{_escape(merged.get('report_brand_line',''))}</p>
<hr style="border-color:#333">
"""
    for key, val in merged.items():
        if isinstance(val, str) and len(val) > 30 and not key.startswith("_"):
            fallback_html += f'<h3>{_escape(key.replace("_"," ").title())}</h3>\n'
            fallback_html += f'<div class="block">{_escape(val)}</div>\n'
    for section in _render_fallback_sections(report_type, merged):
        fallback_html += f"{section}\n"
    fallback_html += f"<footer>{_escape(merged.get('report_footer_text', ''))}</footer></body></html>"
    return fallback_html


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
        choices=["horoscope", "weekly_horoscope", "year_ahead", "personal_forecast", "soul_ecosystem", "identity_profile"],
        help="Type of report to generate"
    )
    parser.add_argument("--name",     required=True,  help="Querent name")
    parser.add_argument("--date",     required=True,  help="Birth date (YYYY-MM-DD)")
    parser.add_argument("--time",     required=False, help="Birth time (HH:MM), 24h format")
    parser.add_argument("--location", required=True,  help="Birth location (city, state) — required; every report type resolves real coordinates from it, even in --simple mode")
    parser.add_argument("--current-location", required=False,
                        help="Current/festival location (defaults to birth location)")
    parser.add_argument("--simple",   action="store_true",
                        help="Simple mode: DOB only, no birth time needed")
    parser.add_argument("--no-browser", action="store_true",
                        help="Don't open browser after generation")
    parser.add_argument("--output",          required=False, help="Output filename (optional)")
    parser.add_argument("--output-dir",      required=False, dest="output_dir",      help="Output directory (overrides default)")
    parser.add_argument("--output-filename", required=False, dest="output_filename", help="Exact output filename (overrides auto-generated name)")
    parser.add_argument(
        "--content-pack",
        dest="content_pack",
        choices=["plainspeak", "entangled_oracle"],
        default="plainspeak",
        help="Interpretation block library: plainspeak (default) or entangled_oracle",
    )
    parser.add_argument(
        "--palette",
        choices=["vibrant", "muted"],
        default="vibrant",
        help="Color palette: vibrant (dark arcane, default) or muted (parchment arcane)",
    )
    parser.add_argument(
        "--report-date",
        default=None,
        help="Report start date (YYYY-MM-DD). Defaults to today if not provided.",
    )

    args = parser.parse_args()
    try:
        birth_data = parse_birth_data(args)
    except InputValidationError as exc:
        raise SystemExit(str(exc))
    birth_data["current_location"] = args.current_location or args.location or ""

    output_filename = args.output_filename or args.output
    try:
        output_path = generate_report(args.report_type, birth_data, output_filename, args.content_pack, args.output_dir)
    except Exception as exc:
        try:
            from engine.offline_place_resolver import LocationResolutionError
        except Exception:
            LocationResolutionError = None
        try:
            from engine.natal_engine import ChartCalculationError
        except Exception:
            ChartCalculationError = None
        clean_exit_errors = tuple(
            cls for cls in (LocationResolutionError, ChartCalculationError) if cls
        )
        if clean_exit_errors and isinstance(exc, clean_exit_errors):
            raise SystemExit(str(exc))
        raise

    if not args.no_browser:
        webbrowser.open(f"file://{os.path.abspath(output_path)}")
    else:
        print(f"Output: {os.path.basename(output_path)}")
        if _stdout_report_paths_enabled():
            print(f"Output path: {output_path}")


if __name__ == "__main__":
    main()
