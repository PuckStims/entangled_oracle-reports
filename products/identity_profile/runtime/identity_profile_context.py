"""
products/identity_profile/runtime/identity_profile_context.py

Context builder for the Entangled Identity Profile.

Design goals
------------
- Uses EAS v0.2's standardized result fields:
  activation_score, activation, expression, archetype, driver_body,
  driver_modality, display_full, suppressed, subtle_signal, components.
- Reuses the current Asteroid Portrait dimension blocks without copying them.
- Uses NGE rather than the deprecated MAGNETIC compatibility adapter.
- Makes tension and mythic-cast sections operationally conditional:
  no invented tension if the selected driver bodies do not form a hard aspect.
- Leaves all prose in JSON block files so later rewrites do not require
  changes to the rendering code.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any

# Reader-facing names. Keep internal formula acronyms out of report prose.
DISPLAY_NAMES = {
    "KVQ": "Foresight Pattern",
    "MKI": "Knowledge Legacy",
    "RWI": "Reality Field",
    "DFIS": "Power Current",
    "NGE": "Narrative Gravity",
    "CATALYST": "Impact Radius",
    "AHL": "Ancestral Thread",
}

# Existing Asteroid Portrait content files remain the source of truth for
# the five current non-NGE EAS dimension cards.
LEGACY_BLOCK_FILES = {
    "KVQ": "foresight_pattern",
    "MKI": "knowledge_legacy",
    "RWI": "reality_field",
    "DFIS": "power_current",
    "CATALYST": "impact_radius",
}

HARD_TENSION_ASPECTS = {"square", "opposition"}

# Formula-body keys are useful for routing but not always reader-friendly.
BODY_DISPLAY_NAMES = {
    "Lilith_BML": "Black Moon Lilith",
    "Lilith": "Lilith",
}


def _key(value: str) -> str:
    """Converts a display label into the JSON key convention."""
    return (
        (value or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
    )


def _body_label(body_name: str) -> str:
    """Returns reader-facing text while preserving raw keys for lookups."""
    if not body_name:
        return ""
    return BODY_DISPLAY_NAMES.get(body_name, body_name.replace("_", " "))


def _driver_body_for_result(index_key: str, result: dict[str, Any]) -> str:
    """
    Resolves the body that actually drove an index result.

    DFIS can prefer Black Moon Lilith but validly fall back to asteroid Lilith.
    The formula exposes ``lilith_source`` specifically so renderer lookups,
    placements, cast cards, and tension checks all use the body that exists in
    the chart rather than an abstract default label.
    """
    if index_key == "DFIS":
        return result.get("lilith_source") or result.get("driver_body", "")
    return result.get("driver_body", "")


def _ordinal(number: int | None) -> str:
    """Formats a Whole Sign house number for compact display."""
    if not number:
        return ""

    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")

    return f"{number}{suffix} house"


def _body_record(payload: dict[str, Any], body_name: str) -> dict[str, Any]:
    """Returns a normalized body/angle record from the current payload."""
    for group_name in ("standard_planets", "custom_asteroids", "angles"):
        group = payload.get(group_name, {})
        record = group.get(body_name)
        if isinstance(record, dict):
            return record
    return {}


def _position_label(payload: dict[str, Any], body_name: str) -> tuple[str, str]:
    """Creates compact placement and Whole Sign house labels for a cast card."""
    record = _body_record(payload, body_name)
    if not record:
        return "", ""

    degree = record.get("degree")
    minute = record.get("minute")
    sign = record.get("sign", "")

    if degree is None or not sign:
        position = ""
    else:
        position = f"{degree}°{int(minute or 0):02d}' {sign}"

    house = _ordinal(record.get("house"))
    return position, house


def _safe_select(
    select_block,
    report_type: str,
    block_file: str,
    *keys: str,
) -> str:
    """
    Calls the shared selector but never allows a missing-file marker or TODO
    string to reach a paid report.
    """
    try:
        value = select_block(report_type, block_file, *keys, fallback="")
    except TypeError:
        # Supports older selector implementations that do not expose the
        # optional fallback keyword. Their missing markers are still filtered
        # immediately below.
        value = select_block(report_type, block_file, *keys)

    if not isinstance(value, str):
        return ""

    clean = value.strip()
    if not clean:
        return ""
    if clean.startswith("[MISSING BLOCK FILE") or clean.startswith("[BLOCK NOT FOUND"):
        return ""
    if clean.startswith("[TODO"):
        return ""
    return clean


def _legacy_content_tier(result: dict[str, Any]) -> str:
    """
    Bridges EAS v0.2 states to the current Asteroid Portrait block schema.

    Existing JSON uses:
      dominant / present / subtle

    EAS v0.2 exposes:
      Sovereign / Embodied / Awakening

    This keeps the current files live while preventing the old renderer's
    normalized-score >= 2.0 bug.
    """
    activation = result.get("activation", "")

    if activation == "Sovereign":
        return "dominant"
    if activation == "Embodied":
        return "present"
    return "subtle"


def _generated_nge_block(result: dict[str, Any]) -> str:
    """Safe v0.1 fallback while NGE-specific copy is being authored."""
    genre = result.get("genre") or result.get("archetype") or "a living narrative"
    expression = result.get("expression") or genre
    driver = result.get("dominant_body") or result.get("driver_body") or "the chart"
    facet = result.get("dominant_facet") or "its strongest facet"
    question = result.get("narrative_question") or ""

    opening = (
        f"Your Narrative Gravity is organized around {genre}, expressed here as "
        f"{expression}. {driver} is the primary genre driver, with {facet} "
        f"providing the strongest tonal cue."
    )
    if question:
        return f"{opening} The guiding question of this lens is: {question}"
    return opening


def _generated_synthesis(
    narrative_result: dict[str, Any],
    primary_key: str,
    primary_result: dict[str, Any],
) -> str:
    """Safe v0.1 synthesis fallback that does not make deterministic claims."""
    narrative = (
        narrative_result.get("expression")
        or narrative_result.get("archetype")
        or "your narrative field"
    )
    primary_name = DISPLAY_NAMES.get(primary_key, primary_key)
    primary_expression = (
        primary_result.get("expression")
        or primary_result.get("archetype")
        or "its strongest expression"
    )

    return (
        f"{narrative} provides the story-frame for this profile, while "
        f"{primary_name} brings its clearest lived emphasis through "
        f"{primary_expression}. Read them together as a working relationship: "
        f"one names the kind of story that gathers meaning for you, while the "
        f"other describes the pattern most available for conscious practice."
    )


def _get_eas_order(index_results: dict[str, Any]) -> list[str]:
    """Uses v0.2 ordering when available, with a defensive fallback."""
    try:
        from formulas.proprietary_indexes import get_eas_dimension_order
        return list(get_eas_dimension_order(index_results))
    except Exception:
        primary = ["KVQ", "MKI", "RWI", "DFIS", "NGE", "CATALYST"]
        ordered = sorted(
            primary,
            key=lambda key: float(index_results.get(key, {}).get("score", 0.0)),
            reverse=True,
        )
        if index_results.get("AHL", {}).get("fires"):
            ordered.append("AHL")
        return ordered


def _make_dimension_block(
    index_key: str,
    result: dict[str, Any],
    select_block,
    select_tier_block,
) -> str:
    """Selects the right paragraph source for one active/quiet EAS dimension."""
    if index_key == "NGE":
        genre_key = _key(result.get("genre") or result.get("archetype"))
        activation_key = _key(result.get("activation"))
        block = _safe_select(
            select_block,
            "shared",
            "nge_narrative_gravity",
            genre_key,
            activation_key,
        )
        if not block:
            block = _safe_select(
                select_block,
                "shared",
                "nge_narrative_gravity",
                genre_key,
                "fallback",
            )
        return block or _generated_nge_block(result)

    if index_key == "AHL":
        tier = result.get("tier", "PRESENT")
        block = _safe_select(
            select_block,
            "asteroid_portrait",
            "ancestral_thread",
            tier,
        )
        return block or (
            "This ancestral signal is included as a supplemental lineage theme. "
            "Treat it as a reflective invitation rather than a factual claim "
            "about family history."
        )

    block_file = LEGACY_BLOCK_FILES.get(index_key)
    if not block_file:
        return ""

    selected = select_tier_block(
        "asteroid_portrait",
        block_file,
        result.get("archetype", ""),
        _legacy_content_tier(result),
    )
    if not isinstance(selected, str):
        return ""
    selected = selected.strip()
    if selected.startswith("[MISSING BLOCK FILE") or selected.startswith("[BLOCK NOT FOUND"):
        return ""
    if selected.startswith("[TODO"):
        return ""
    return selected


def _make_system_section(
    index_key: str,
    result: dict[str, Any],
    payload: dict[str, Any],
    select_block,
    select_tier_block,
) -> dict[str, Any]:
    """Builds one template-ready active system card."""
    if index_key == "AHL":
        expression = "The Ancestral Thread"
        archetype = (
            "Deep lineage signal"
            if result.get("tier") == "DEEP"
            else "Present lineage signal"
        )
        driver = ""
        modality = ""
        activation = result.get("tier", "PRESENT").title()
    else:
        expression = result.get("expression") or result.get("archetype", "")
        archetype = result.get("archetype", "")
        driver = _driver_body_for_result(index_key, result)
        modality = result.get("driver_modality", "")
        activation = result.get("activation", "Awakening")

    position, house = _position_label(payload, driver)
    driver_label = _body_label(driver)

    details = [
        detail
        for detail in (
            f"Driver · {driver_label}" if driver_label else "",
            position,
            house,
            f"{modality.title()} expression" if modality else "",
        )
        if detail
    ]

    return {
        "key": index_key,
        "name": DISPLAY_NAMES.get(index_key, index_key),
        "activation": activation,
        "expression": expression,
        "archetype": archetype,
        "tagline": "",
        "block": _make_dimension_block(
            index_key,
            result,
            select_block,
            select_tier_block,
        ),
        "details": details,
    }


def _make_quiet_section(
    index_key: str,
    result: dict[str, Any],
    select_block,
    select_tier_block,
) -> dict[str, Any]:
    """Builds one optional 0.1–1.9 subtle-signal card."""
    archetype = result.get("archetype", "")
    expression = result.get("expression") or archetype

    if index_key == "AHL":
        note = _make_dimension_block(index_key, result, select_block, select_tier_block)
        archetype = "Ancestral Thread"
    else:
        note = _make_dimension_block(index_key, result, select_block, select_tier_block)

    return {
        "key": index_key,
        "name": DISPLAY_NAMES.get(index_key, index_key),
        "archetype": expression,
        "note": note,
    }


def _find_hard_aspect(
    payload: dict[str, Any],
    body_a: str,
    body_b: str,
) -> dict[str, Any] | None:
    """Finds a direct square/opposition from the broad natal aspect matrix."""
    if not body_a or not body_b or body_a == body_b:
        return None

    for aspect in payload.get("aspects", []):
        pair = {aspect.get("body_1"), aspect.get("body_2")}
        aspect_key = _key(aspect.get("aspect", ""))
        if pair == {body_a, body_b} and aspect_key in HARD_TENSION_ASPECTS:
            return aspect

    return None


def _build_tension_sections(
    active_pairs: list[tuple[str, dict[str, Any]]],
    payload: dict[str, Any],
    select_block,
    max_sections: int = 1,
) -> list[dict[str, Any]]:
    """
    Produces tension cards only when two active driver bodies form a natal
    square or opposition. That makes this an auditable chart relationship,
    not an invented conflict between whichever two labels rank highest.
    """
    candidates: list[tuple[tuple[float, float], dict[str, Any]]] = []

    for (left_key, left), (right_key, right) in combinations(active_pairs, 2):
        if "AHL" in {left_key, right_key}:
            continue

        left_driver = _driver_body_for_result(left_key, left)
        right_driver = _driver_body_for_result(right_key, right)
        aspect = _find_hard_aspect(
            payload,
            left_driver,
            right_driver,
        )
        if not aspect:
            continue

        pair_key = "__".join(sorted((_key(left_key), _key(right_key))))
        aspect_key = _key(aspect.get("aspect", ""))
        block = _safe_select(
            select_block,
            "identity_profile",
            "archetypal_tensions",
            pair_key,
            aspect_key,
        )

        left_expression = left.get("expression") or left.get("archetype") or DISPLAY_NAMES.get(left_key, left_key)
        right_expression = right.get("expression") or right.get("archetype") or DISPLAY_NAMES.get(right_key, right_key)

        if not block:
            block = (
                f"{left_expression} and {right_expression} are carried by chart "
                f"drivers in a {aspect.get('aspect', '').lower()} relationship. "
                f"This does not cancel either pattern; it highlights a place where "
                f"their needs may ask for different timing, strategies, or forms of expression."
            )

        rank = (
            float(aspect.get("orb", 99.0)),
            -(
                float(left.get("activation_score", 0.0))
                + float(right.get("activation_score", 0.0))
            ),
        )

        candidates.append(
            (
                rank,
                {
                    "label": f"{aspect.get('aspect', 'Dynamic')} dialogue",
                    "left": left_expression,
                    "right": right_expression,
                    "block": block,
                },
            )
        )

    candidates.sort(key=lambda item: item[0])
    return [item[1] for item in candidates[:max_sections]]


def _build_mythic_cast(
    active_pairs: list[tuple[str, dict[str, Any]]],
    payload: dict[str, Any],
    select_block,
    max_entities: int = 6,
) -> list[dict[str, Any]]:
    """
    Builds an entity cast from actual active driver bodies, deduplicating
    bodies that operate in more than one EAS dimension.
    """
    cast: dict[str, dict[str, Any]] = {}

    for index_key, result in active_pairs:
        if index_key == "AHL":
            continue

        body = _driver_body_for_result(index_key, result)
        if not body:
            continue

        position, house = _position_label(payload, body)
        if not position:
            continue

        role = (
            result.get("expression")
            or result.get("archetype")
            or DISPLAY_NAMES.get(index_key, index_key)
        )
        domain = DISPLAY_NAMES.get(index_key, index_key)
        entry = cast.setdefault(
            body,
            {
                "raw_name": body,
                "domain_parts": [],
                "role_parts": [],
                "position": position,
                "house": house,
            },
        )
        if domain not in entry["domain_parts"]:
            entry["domain_parts"].append(domain)
        if role not in entry["role_parts"]:
            entry["role_parts"].append(role)

    cards: list[dict[str, Any]] = []

    for body, entry in cast.items():
        authored = _safe_select(
            select_block,
            "identity_profile",
            "entity_cast",
            _key(body),
        )
        role = " · ".join(entry["role_parts"])
        block = authored or (
            f"{body} is a direct chart driver for the role shown above. Its "
            f"placement identifies where this pattern becomes most visible in "
            f"the portrait; it does not reduce the person to a single trait."
        )

        cards.append(
            {
                "name": _body_label(body),
                "domain": " · ".join(entry["domain_parts"]),
                "role": role,
                "position": entry["position"],
                "house": entry["house"],
                "block": block,
            }
        )

    return cards[:max_entities]


def build_identity_profile_context(
    variables: dict[str, Any],
    index_results: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Builds the template context used by entangled_identity_profile.html.

    This deliberately uses the v0.2 EAS stack:
      KVQ, MKI, RWI, DFIS, NGE, Catalyst
    plus optional AHL.

    MAGNETIC is intentionally excluded. It remains a compatibility adapter for
    the legacy Asteroid Portrait and can later become its own mini product.
    """
    from selectors.block_selector import select_block, select_tier_block

    dimension_order = _get_eas_order(index_results)

    active_pairs: list[tuple[str, dict[str, Any]]] = []
    quiet_pairs: list[tuple[str, dict[str, Any]]] = []

    for index_key in dimension_order:
        result = index_results.get(index_key, {})
        if not isinstance(result, dict):
            continue

        if result.get("display_full"):
            active_pairs.append((index_key, result))
        elif result.get("subtle_signal"):
            quiet_pairs.append((index_key, result))

    # NGE needs to lead the profile only when it has qualified for display.
    narrative_result = index_results.get("NGE", {})
    narrative_active = (
        isinstance(narrative_result, dict)
        and narrative_result.get("display_full")
    )

    # The focal current is the first display-qualified primary result in the
    # v0.2 ranking. NGE is eligible because it is a real sixth EAS index; AHL
    # is not, because it remains ancillary.
    focal_candidates = [pair for pair in active_pairs if pair[0] != "AHL"]
    if focal_candidates:
        primary_key, primary_result = focal_candidates[0]
    else:
        primary_key, primary_result = "KVQ", index_results.get("KVQ", {})

    # NGE card comes first whenever it is an active field, followed by the
    # rest in formula-engine order.
    ordered_active = []
    if narrative_active:
        ordered_active.append(("NGE", narrative_result))
    ordered_active.extend(
        pair for pair in active_pairs
        if pair[0] != "NGE"
    )

    active_sections = [
        _make_system_section(
            index_key,
            result,
            payload,
            select_block,
            select_tier_block,
        )
        for index_key, result in ordered_active
    ]

    quiet_sections = [
        _make_quiet_section(
            index_key,
            result,
            select_block,
            select_tier_block,
        )
        for index_key, result in quiet_pairs
        if index_key != "NGE"
    ]

    # The existing portrait overview is used only as a temporary bridge for
    # the legacy non-NGE system cards. NGE has its own authored Narrative
    # Gravity paragraph and should not be forced into a legacy overview key.
    overview = ""
    if primary_result.get("display_full") and primary_key in LEGACY_BLOCK_FILES:
        overview = _safe_select(
            select_block,
            "asteroid_portrait",
            "portrait_overview",
            primary_key,
        )
    if not overview:
        overview = (
            "This profile maps the active symbolic relationships in the chart "
            "without treating them as a fixed personality label. The strongest "
            "patterns are presented as a living field: some lead, some support, "
            "and some remain present at the edge of the story."
        )

    # Identity Synthesis is intentionally unavailable when NGE has not met
    # the runtime display gate. A tie-resolved zero-score genre must never
    # become a full concluding story simply because its label exists.
    synthesis = ""
    if narrative_active and primary_result.get("display_full"):
        synthesis = _safe_select(
            select_block,
            "identity_profile",
            "identity_synthesis",
            _key(narrative_result.get("genre") or narrative_result.get("archetype")),
            _key(primary_key),
            _key(primary_result.get("activation")),
        )
        if not synthesis:
            synthesis = _generated_synthesis(
                narrative_result,
                primary_key,
                primary_result,
            )

    narrative_value = (
        narrative_result.get("expression")
        if narrative_active
        else "Not foregrounded in this profile"
    )
    primary_expression = (
        (
            primary_result.get("expression")
            or primary_result.get("archetype")
            or "No full signal yet"
        )
        if primary_result.get("display_full")
        else "No full signal yet"
    )
    primary_driver = (
        _body_label(_driver_body_for_result(primary_key, primary_result))
        if primary_result.get("display_full")
        else "—"
    )
    primary_activation = (
        primary_result.get("activation", "Emerging")
        if primary_result.get("display_full")
        else "Emerging"
    )

    return {
        "portrait_overview_block": overview,
        "portrait_synthesis_block": synthesis,
        "has_portrait_synthesis": bool(synthesis),
        "identity_at_a_glance": [
            {"label": "Narrative gravity", "value": narrative_value},
            {"label": "Strongest current", "value": primary_expression},
            {"label": "Primary driver", "value": primary_driver},
            {"label": "Field state", "value": primary_activation},
        ],
        "active_index_sections": active_sections,
        "quiet_signal_sections": quiet_sections,
        "tension_sections": _build_tension_sections(
            ordered_active,
            payload,
            select_block,
        ),
        "mythic_cast": _build_mythic_cast(
            ordered_active,
            payload,
            select_block,
        ),
    }
