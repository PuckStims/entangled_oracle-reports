"""Context builder for the Internal Architecture report."""

from __future__ import annotations

from typing import Any

from eia_engine import build_eia_report
from eia_engine.content_pack import content_for


REGISTER_ORDER = ("ignition", "reception", "decision", "current", "boundary", "contact", "restoration")
REPORT_DEPTHS = ("core", "expanded", "advanced")

REGISTER_TITLES = {
    "ignition": "Ignition Register",
    "reception": "Reception Register",
    "decision": "Decision Register",
    "current": "Current Register",
    "boundary": "Boundary Register",
    "contact": "Contact Register",
    "restoration": "Restoration Register",
}

REGISTER_QUESTIONS = {
    "ignition": "How movement begins",
    "reception": "How signal enters the system",
    "decision": "How clarity becomes trustworthy",
    "current": "How energy moves, spends, and returns",
    "boundary": "How selfhood holds shape under contact",
    "contact": "What happens when you enter a field",
    "restoration": "How coherence returns",
}


DISPLAY_NAMES = {
    "KVQ": "Foresight Pattern",
    "MKI": "Knowledge Legacy",
    "RWI": "Reality Field",
    "DFIS": "Power Current",
    "NGE": "Narrative Gravity",
    "CATALYST": "Impact Radius",
    "AHL": "Ancestral Thread",
}

PRESSURE_DISTORTION_TARGETS = {
    "Forced Emergence": (
        "The ignition register: private preparation, timing, and the point at which readiness becomes visible."
    ),
    "Surge Burn": (
        "The current register: energy pacing, recovery, and the difference between a true surge and a sustainable rhythm."
    ),
    "False Certainty": (
        "The decision register: first knowing, context checking, and the space between recognition and commitment."
    ),
}


def build_internal_architecture_context(
    variables: dict[str, Any],
    index_results: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Builds template-ready EIA context from the existing EO payload/indexes."""
    report = build_eia_report(
        payload,
        eas_indexes=_eas_overlay(index_results),
    )
    report_dict = report.to_dict()
    client_name, sample_identity_note = _client_identity(variables, report_dict)
    report_dict["client"]["name"] = client_name
    score_lookup = _score_lookup(report_dict)
    register_blocks = [
        _consumer_register_block(register, report_dict["registers"][register], score_lookup[register])
        for register in REGISTER_ORDER
    ]
    practitioner_rows = [
        _practitioner_row(block)
        for block in register_blocks
    ]
    include_practitioner_appendix = bool(variables.get("include_practitioner_appendix"))
    include_debug_json = bool(variables.get("include_debug_json"))
    report_depth = _report_depth(variables)
    advanced_layers = report_dict.get("advanced_layers_optional") or {}
    context = {
        "report_version": "Internal Architecture v0.1",
        "report_depth": report_depth,
        "is_expanded_internal_architecture": report_depth in {"expanded", "advanced"},
        "is_advanced_internal_architecture": report_depth == "advanced",
        "internal_architecture": report_dict,
        "internal_architecture_advanced_layers": advanced_layers,
        "internal_architecture_registers": register_blocks,
        "internal_architecture_pressure_patterns": _consumer_pressure_patterns(register_blocks),
        "internal_architecture_summary": _consumer_summary(register_blocks),
        "internal_architecture_json": report_dict,
        "internal_architecture_practitioner_rows": practitioner_rows,
        "include_practitioner_appendix": include_practitioner_appendix,
        "include_debug_json": include_debug_json,
        "method_note": report_dict["method"]["notes"],
        "client_name": client_name,
        "sample_identity_note": sample_identity_note,
        "birth_time_confidence": _birth_time_confidence_label(
            report_dict["client"].get("birth_time_confidence")
            or variables.get("birth_time_confidence")
        ),
        "architecture_at_a_glance": _architecture_at_a_glance(register_blocks),
        "opening_synthesis": _opening_synthesis(register_blocks),
        "pressure_patterns_intro": _section_intro(variables, report_dict, "pressure_patterns"),
        "signal_path_paragraphs": _signal_path(register_blocks),
        "calculation_basis": _calculation_basis(report_dict, payload),
    }
    footer_text = _report_footer_text(variables)
    if footer_text:
        context["report_footer_text"] = footer_text
    return context


def _client_identity(variables: dict[str, Any], report_dict: dict[str, Any]) -> tuple[str, str]:
    mode = str(variables.get("sample_identity_mode") or "").strip().lower()
    if mode == "anonymized":
        return str(variables.get("sample_display_name") or "Sample Client").strip() or "Sample Client", (
            "Public sample; client name anonymized."
        )
    name = str(variables.get("querent_name") or report_dict.get("client", {}).get("name") or "").strip()
    if mode == "founder_demo":
        return name or "Founder Demo", "Founder demo, shared with consent."
    return name, ""


def _report_footer_text(variables: dict[str, Any]) -> str | None:
    if str(variables.get("sample_identity_mode") or "").strip().lower() != "anonymized":
        return None
    generation_date = str(variables.get("generation_date") or "").strip()
    footer = "Entangled Oracle - Public sample"
    return f"{footer} - Generated {generation_date}" if generation_date else footer


def _section_intro(variables: dict[str, Any], report_dict: dict[str, Any], key: str) -> str:
    section_intros = variables.get("section_intros")
    if isinstance(section_intros, dict) and section_intros.get(key):
        return str(section_intros[key]).strip()
    report_section_intros = report_dict.get("section_intros")
    if isinstance(report_section_intros, dict) and report_section_intros.get(key):
        return str(report_section_intros[key]).strip()
    return ""


def _report_depth(variables: dict[str, Any]) -> str:
    depth = str(variables.get("report_depth") or "core").strip().lower()
    return depth if depth in REPORT_DEPTHS else "core"


def _eas_overlay(index_results: dict[str, Any]) -> dict[str, Any]:
    if not index_results:
        return {}
    candidates = []
    for key, result in index_results.items():
        if not isinstance(result, dict):
            continue
        score = float(result.get("activation_score", result.get("score", 0.0)) or 0.0)
        expression = result.get("expression") or result.get("archetype") or key
        candidates.append((score, key, expression, result.get("activation", "")))
    candidates.sort(reverse=True)
    if not candidates:
        return {}
    score, key, expression, activation = candidates[0]
    return {
        "dominant_current": DISPLAY_NAMES.get(key, key),
        "expression": expression,
        "activation_state": activation or "baseline",
        "ranked_currents": [
            {
                "key": key,
                "name": DISPLAY_NAMES.get(key, key),
                "score": score,
                "expression": expression,
                "activation": activation,
            }
            for score, key, expression, activation in candidates[:5]
        ],
    }


def _score_lookup(report_dict: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    lookup = {register: [] for register in REGISTER_ORDER}
    for row in report_dict.get("technical_appendix", {}).get("register_scores", []):
        register = row.get("register")
        if register in lookup:
            lookup[register].append(row)
    for rows in lookup.values():
        rows.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
    return lookup


def _consumer_register_block(register: str, raw: dict[str, Any], scores: list[dict[str, Any]]) -> dict[str, Any]:
    dominant = raw["dominant_mode"]
    secondary = raw.get("secondary_mode")
    copy = content_for(register, dominant)
    top_score = float(scores[0]["score"]) if scores else float(raw.get("score", 0.0))
    second_score = float(scores[1]["score"]) if len(scores) > 1 else 0.0
    second_mode = str(scores[1]["mode"]) if len(scores) > 1 else ""
    signal_language = _signal_language(top_score, second_score)
    if not secondary and second_mode and top_score - second_score <= 0.18 and second_score >= 0.42:
        secondary = second_mode
    return {
        **raw,
        "title": REGISTER_TITLES[register],
        "question": REGISTER_QUESTIONS[register],
        "mode_line": f"{dominant} + {secondary}" if secondary else dominant,
        "consumer_description": copy["consumer_description"],
        "mechanism": copy["mechanism"],
        "distortion": copy["distortion"],
        "restoration": copy["restoration"],
        "experiment": copy["experiment"],
        "when_supported": copy["when_supported"],
        "when_pressured": copy["when_pressured"],
        "evidence_sentence": copy.get("evidence_sentence", ""),
        "signal_language": signal_language,
        "summary_sentence": _summary_sentence(register, dominant, secondary, signal_language, copy),
        "primary_score": top_score,
        "secondary_score": second_score,
        "source_basis": _source_basis(raw),
    }


def _signal_language(top_score: float, second_score: float) -> str:
    spread = top_score - second_score
    if second_score >= 0.50 and spread <= 0.08:
        return "Blended register"
    if second_score >= 0.50 and spread <= 0.18:
        return "Blended-clear signal"
    if top_score >= 0.68:
        return "Clear signal"
    if top_score >= 0.54:
        return "Supporting signal"
    return "Distributed pattern"


def _summary_sentence(register: str, dominant: str, secondary: str | None, signal_language: str, copy: dict[str, str]) -> str:
    if secondary and signal_language in {"Blended register", "Blended-clear signal"}:
        return f"{dominant} leads, with {secondary} close enough to shape how this register expresses."
    return copy["consumer_description"]


def _source_basis(raw: dict[str, Any]) -> str:
    layers = []
    for evidence in raw.get("source_evidence", []):
        layer = evidence.get("source_layer", "")
        if layer == "natal_astrology":
            layers.append("natal chart")
        elif layer == "eas":
            layers.append("EO resonance")
        elif layer == "polarity_model":
            layers.append("current model")
        elif layer == "biophysical_metaphor":
            layers.append("signal/load")
    return "; ".join(dict.fromkeys(layers)) or "symbolic evidence"


def _consumer_summary(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "integration_sentence": (
            f"Your architecture begins through {blocks[0]['dominant_mode']}, "
            f"knows through {blocks[2]['dominant_mode']}, spends energy through {blocks[3]['dominant_mode']}, "
            f"meets contact through {blocks[5]['dominant_mode']}, and restores through {blocks[6]['dominant_mode']}."
        )
    }


def _architecture_at_a_glance(blocks: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "label": block["title"],
            "value": block["mode_line"],
            "primary_mode": block["dominant_mode"],
            "secondary_mode": block.get("secondary_mode") or "",
            "signal": block["signal_language"],
            "summary": "" if _summary_is_generated_pairing(block) else block["summary_sentence"],
        }
        for block in blocks
    ]


def _summary_is_generated_pairing(block: dict[str, Any]) -> bool:
    return bool(block.get("secondary_mode")) and block.get("signal_language") in {
        "Blended register",
        "Blended-clear signal",
    }


def _opening_synthesis(blocks: list[dict[str, Any]]) -> list[str]:
    ignition, reception, decision, current, boundary, contact, restoration = blocks
    return [
        (
            f"Your Internal Architecture describes a signal path rather than a fixed label. "
            f"Movement begins through {ignition['dominant_mode']}, while perception gathers through "
            f"{reception['dominant_mode']} and decision-making organizes through {decision['dominant_mode']}."
        ),
        (
            f"Energy in this map is not treated as an endless supply. It moves through "
            f"{current['dominant_mode']}, meets the world through a {boundary['dominant_mode']} boundary interface, "
            f"and changes the contact field through {contact['dominant_mode']}."
        ),
        (
            f"The restoration key is {restoration['dominant_mode']}: the practice that helps the system return to coherence "
            f"after pressure, contact, speed, or overextension. Read the modes below as patterns to test, not commands to obey."
        ),
    ]


def _signal_path(blocks: list[dict[str, Any]]) -> list[str]:
    ignition, reception, decision, current, boundary, contact, restoration = blocks
    paragraphs = [
        (
            f"This architecture can look paradoxical in motion: {ignition['dominant_mode']} describes how movement starts, "
            f"while {decision['dominant_mode']} describes how clarity becomes trustworthy. The first signal matters, but the "
            f"system becomes wiser when ignition and decision tempo are allowed to speak to each other."
        ),
        (
            f"Reception and boundary form the filter. {reception['dominant_mode']} shows how information enters; "
            f"{boundary['dominant_mode']} shows how access is shaped once contact, demand, or intimacy is involved. "
            f"When this pair is supported, sensitivity does not have to become overexposure."
        ),
        (
            f"Current and contact describe how the architecture behaves in real life. {current['dominant_mode']} names the "
            f"energy economy, while {contact['dominant_mode']} names what your presence tends to do in a shared field. "
            f"Restoration through {restoration['dominant_mode']} gives the whole pattern a way to come home."
        ),
    ]
    if boundary["dominant_mode"] == "Gate" and contact["dominant_mode"] == "Challenger":
        paragraphs.append(
            "A chosen boundary interface makes direct contact more constructive. Challenge becomes useful when the terms of engagement are clean."
        )
    if current["dominant_mode"] == "Pulse Current":
        paragraphs.append(
            f"Because energy may arrive in surges, restoration cannot be an afterthought. {restoration['dominant_mode']} is part of the current, not a reward after it."
        )
    return paragraphs


def _consumer_pressure_patterns(blocks: list[dict[str, Any]]) -> list[dict[str, str]]:
    selected = sorted(blocks, key=lambda block: float(block["primary_score"]), reverse=True)[:3]
    seen = set()
    patterns = []
    for block in selected:
        name = _pressure_name(block)
        if name in seen:
            name = f"{block['dominant_mode']} Under Pressure"
        seen.add(name)
        patterns.append(
            {
                "name": name,
                "activated": f"Activated when {block['dominant_mode']} is rushed, overused, or asked to solve pressure in the {block['title'].lower()}.",
                "feels": block["when_pressured"],
                "distorts": _pressure_distortion_target(name, block),
                "correction": block["restoration"],
                "practice": block["experiment"],
            }
        )
    return patterns


def _pressure_name(block: dict[str, Any]) -> str:
    names = {
        "Quiet Accumulation": "Forced Emergence",
        "Pulse Current": "Surge Burn",
        "Immediate Knowing": "False Certainty",
        "Pattern Receiver": "False Pattern",
        "Challenger": "Combative Clarity",
        "Gate": "Vague Access",
        "Threshold Break": "Forced Breakthrough",
        "Open Field": "Signal Flood",
        "Trusted Witnessing": "Audience Dependence",
    }
    return names.get(block["dominant_mode"], block["distortion"])


def _pressure_distortion_target(name: str, block: dict[str, Any]) -> str:
    if name in PRESSURE_DISTORTION_TARGETS:
        return PRESSURE_DISTORTION_TARGETS[name]
    return f"The {str(block['title']).lower()}: {block['question']}."


def _practitioner_row(block: dict[str, Any]) -> dict[str, str]:
    return {
        "register": block["title"],
        "primary_mode": block["dominant_mode"],
        "secondary_mode": block.get("secondary_mode") or "None",
        "signal_strength": block["signal_language"],
        "confidence": _confidence_label(block["primary_score"]),
        "source_basis": block["source_basis"],
    }


def _confidence_label(score: float) -> str:
    if score >= 0.68:
        return "High"
    if score >= 0.54:
        return "Moderate"
    return "Exploratory"


def _calculation_basis(report_dict: dict[str, Any], payload: dict[str, Any]) -> dict[str, str]:
    confidence = report_dict.get("client", {}).get("birth_time_confidence", "exact")
    return {
        "calculation_basis": (
            "Internal Architecture is built from the natal chart, selected Entangled Oracle resonance layers, "
            "polarity-style current modeling, and symbolic signal/load/recovery language. It is a baseline operating-map "
            "report, not a diagnostic system or command structure. It translates chart-derived and Entangled Oracle "
            "framework signals into an operating map for self-observation."
        ),
        "method_note": (
            "Calculated from the available natal payload using Tropical zodiac and the source house system. Register modes "
            "are selected through weighted symbolic evidence and translated into consumer-facing reflection."
        ),
        "birth_time_confidence": (
            f"Birth-time confidence: {_birth_time_confidence_label(confidence)}. House and angle-dependent material should remain conditional "
            "when birth time is approximate or unknown."
        ),
        "proprietary_layer": (
            "EIA register language and related pattern outputs are interpretive frameworks for reflection, coherence, and "
            "practical self-observation. They are meant to deepen discernment, not settle practical decisions for the reader. "
            "This report is not a diagnosis, prescription, or substitute for lived context, consent, or practical decision-making."
        ),
    }


def _birth_time_confidence_label(value: Any) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    labels = {
        "exact": "Exact birth time",
        "exact_birth_time": "Exact birth time",
        "exact_time_supplied": "Exact birth time",
        "approximate": "Approximate birth time",
        "approximate_birth_time": "Approximate birth time",
        "birth_time_unknown_or_approximate": "Approximate birth time",
        "unknown": "Unknown birth time",
        "unknown_birth_time": "Unknown birth time",
    }
    return labels.get(normalized, str(value or "Unknown birth time").replace("_", " ").strip().capitalize())
