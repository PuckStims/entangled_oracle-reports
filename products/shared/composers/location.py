"""Location Services contexts -> shared semantic document composition."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..document_model import (
    CalloutBlock,
    CoverSection,
    DataTable,
    KeyValueRow,
    Paragraph,
    ParityEntry,
    PillRow,
    ReportDocument,
    ReportFooter,
    ReportHeader,
    Section,
    SupportCard,
    as_nodes,
)
from ._helpers import footer, metadata, text


def _label(value: Any) -> str:
    return text(value).replace("_", " ").replace(":", " - ").title()


def _leaf_text(item: dict[str, Any], variables: dict[str, Any]) -> str:
    leaf = item.get("leaf") or item.get("selected_leaf") or {}
    body = text(item.get("body") or (leaf.get("body") if isinstance(leaf, dict) else ""))
    source = item.get("source") or {}
    values = {**{key: value for key, value in variables.items() if not isinstance(value, (dict, list))}, **source}
    for key, value in values.items():
        body = body.replace("{" + str(key) + "}", text(value))
    return body


def _block_card(block: dict[str, Any], variables: dict[str, Any]) -> SupportCard:
    leaf = block.get("leaf") or block.get("selected_leaf") or {}
    source = block.get("source") or {}
    note = leaf.get("note") if isinstance(leaf, dict) else None
    rows = list(metadata(("Note", note), ("Evidence", ", ".join(map(str, block.get("evidence", {}).get("ids", []))) if isinstance(block.get("evidence"), dict) else None)))
    for key in ("count", "raw_warning_count", "warning_summary_count"):
        if block.get(key) is not None:
            rows.append(KeyValueRow(_label(key), text(block[key])))
    if isinstance(source, dict):
        for key in ("body", "angle", "contact_strength", "relocated_house", "movement_type"):
            if text(source.get(key)):
                rows.append(KeyValueRow(_label(key), text(source[key])))
    return SupportCard(
        title=text(block.get("title")) or _label(block.get("id")) or "Location evidence",
        body=_leaf_text(block, variables),
        metadata=tuple(rows),
    )


def _section_nodes(section: dict[str, Any], variables: dict[str, Any]) -> list[Any]:
    nodes: list[Any] = []
    if text(_leaf_text(section, variables)):
        nodes.append(Paragraph(_leaf_text(section, variables)))
    nodes.extend(_block_card(block, variables) for block in section.get("blocks", []) if isinstance(block, dict))
    rows = section.get("rows") or []
    if rows:
        rendered_rows = []
        for row in rows:
            if isinstance(row, dict):
                rendered_rows.append((_label(row.get("label") or row.get("id") or "Evidence"), _leaf_text(row, variables) or text(row.get("value"))))
        if rendered_rows:
            nodes.append(DataTable(("Evidence", "Details"), tuple(rendered_rows)))
    return nodes


def _comparison_nodes(section_id: str, context: dict) -> list[Any]:
    comparison = context.get("comparison_record") or {}
    if section_id == "comparison_summary":
        return [CalloutBlock("Comparison summary", text(comparison.get("comparison_summary")), "highlight")]
    if section_id == "place_profiles":
        cards = []
        for key, name in (("compact_profile_a", context.get("name_a")), ("compact_profile_b", context.get("name_b"))):
            profile = context.get(key) or {}
            goals = profile.get("goal_highlights") or []
            goal_text = "; ".join(text(goal.get("goal_label") or goal.get("goal_key")) for goal in goals if isinstance(goal, dict))
            cards.append(SupportCard(text(name) or "Place profile", text(profile.get("summary") or profile.get("body")), metadata=metadata(("Goal highlights", goal_text))))
        return cards
    if section_id in {"shared_themes", "divergent_themes"}:
        return [PillRow(tuple(_label(item) for item in comparison.get(section_id, []) if text(item)))]
    key = "strongest_differences" if section_id == "strongest_differences" else "tradeoffs"
    if section_id in {"strongest_differences", "tradeoffs"}:
        return [SupportCard(_label(item.get("goal_label") or item.get("type") or "Comparison"), text(item.get("description")), metadata=metadata(("Difference", item.get("delta")))) for item in comparison.get(key, []) if isinstance(item, dict)]
    if section_id == "decision_notes":
        return [Paragraph(text(note.get("body") if isinstance(note, dict) else note)) for note in context.get("decision_notes", []) if text(note.get("body") if isinstance(note, dict) else note)]
    return []


def _search_document(context: dict) -> ReportDocument:
    selected = [item for item in context.get("selected_locations", []) if isinstance(item, dict)]
    pool = context.get("candidate_pool") or {}
    variables = {"candidate_count": pool.get("evaluated_count"), "dominant_theme": _label(context.get("dominant_search_theme"))}
    nodes: list[Any] = [
        CoverSection(ReportHeader(text(context.get("product_name")) or "Place Resonance Search", metadata=metadata(("Candidate pool", pool.get("evaluated_count")), ("Purpose lens", context.get("purpose_lens"))))),
        Section("Search overview", tuple(Paragraph(_leaf_text({"selected_leaf": leaf}, variables)) for leaf in (context.get("selected_leaves") or {}).values() if isinstance(leaf, dict)), marker="search-overview"),
    ]
    buckets: dict[str, list[dict]] = defaultdict(list)
    for location in selected:
        buckets[text(location.get("bucket")) or "results"].append(location)
    for bucket, locations in buckets.items():
        bucket_leaf = (context.get("bucket_leaves") or {}).get(bucket)
        section_nodes: list[Any] = [Paragraph(_leaf_text({"selected_leaf": bucket_leaf}, {**variables, "bucket": locations[0].get("bucket_label"), "count": len(locations)}))] if isinstance(bucket_leaf, dict) else []
        for location in locations:
            location_id = location.get("location_id")
            details = (context.get("tile_detail_leaves") or {}).get(location_id) or {}
            location_vars = {
                **variables,
                "city_name": location.get("display_name"),
                "bucket": location.get("bucket_label") or location.get("bucket"),
                "primary_score": (location.get("scores") or {}).get("overall_resonance"),
                "evidence_refs": ", ".join(map(str, (location.get("evidence_refs") or [])[:4])),
            }
            prose = [_leaf_text({"selected_leaf": leaf}, location_vars) for leaf in details.values() if isinstance(leaf, dict)]
            recommendation = _leaf_text({"selected_leaf": (context.get("recommendation_leaves") or {}).get(location_id)}, location_vars)
            section_nodes.append(SupportCard(text(location.get("display_name")) or "Location", "\n\n".join(part for part in [recommendation, *prose] if part), metadata=metadata(("Rank", location.get("selection_rank")), ("Themes", ", ".join(_label(item) for item in location.get("dominant_themes", []))), ("Overall score", (location.get("scores") or {}).get("overall_resonance")))))
        nodes.append(Section(text(locations[0].get("bucket_label")) or _label(bucket), tuple(section_nodes), marker=f"bucket-{bucket}"))
    nodes.append(ReportFooter(footer(context)))
    return ReportDocument(title=text(context.get("product_name")) or "Place Resonance Search", nodes=as_nodes(nodes), report_subtype="location_services", theme_id="vibrant", metadata={"report_family": "location_services"}, parity_manifest=(ParityEntry("search-overview", "selected_locations"),))


def compose_location_report(context: dict) -> ReportDocument:
    """Compose any completed Location Services context by its semantic shape."""
    if context.get("selected_locations") is not None and not context.get("sections"):
        return _search_document(context)
    destination = context.get("destination_context") or context.get("location_a") or {}
    sections = [section for section in context.get("sections", []) if isinstance(section, dict)]
    variables = {**context, **destination}
    nodes: list[Any] = [CoverSection(ReportHeader(text(context.get("product_name")) or "Location Services", subtitle=text(destination.get("display_name")) or None, metadata=metadata(("Purpose lens", context.get("purpose_lens")), ("Relationship to place", context.get("relationship_to_place")))))]
    is_comparison = bool(context.get("comparison_record"))
    for section in sections:
        section_id = text(section.get("id"))
        section_nodes = _comparison_nodes(section_id, context) if is_comparison else _section_nodes(section, variables)
        nodes.append(Section(text(section.get("title")) or "Report section", tuple(section_nodes), kicker=text(section.get("kicker")) or None, marker=section_id or None))
    nodes.append(ReportFooter(footer(context)))
    return ReportDocument(
        title=text(context.get("product_name")) or "Location Services",
        nodes=as_nodes(nodes),
        subject_name=text(destination.get("display_name")) or None,
        report_subtype="location_services",
        theme_id="vibrant",
        metadata={"report_family": "location_services"},
        parity_manifest=tuple(ParityEntry(text(section.get("id")), "sections") for section in sections if text(section.get("id"))),
    )
