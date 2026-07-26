"""Build structured EIA reports from existing Entangled Oracle payloads."""

from __future__ import annotations

from typing import Any

from eia_engine.content_pack import content_for, load_modes_catalog
from eia_engine.feature_extraction import extract_astrology_features
from eia_engine.mode_selection import select_dominant_mode, select_secondary_mode
from eia_engine.models import EIARegisterBlock, EIAReport, EIAPressurePattern, EIASourceEvidence
from eia_engine.register_scoring import score_register_modes
from eia_engine.schema import REGISTERS, validate_report_dict
from eia_engine.state_overlay import build_state_snapshot, normalize_state_overlay


def build_eia_report(
    natal_chart: dict[str, Any],
    eas_indexes: dict[str, Any] | None = None,
    state_overlay: dict[str, Any] | None = None,
    client_checkin: dict[str, Any] | None = None,
    content_dir: str | None = None,
) -> EIAReport:
    modes_catalog = load_modes_catalog(content_dir)
    features = extract_astrology_features(natal_chart)
    normalized_state = normalize_state_overlay(state_overlay)

    registers = {}
    scoring_table = []
    for register in REGISTERS:
        modes = modes_catalog[register]
        mode_scores = score_register_modes(register, modes, features, eas_indexes, normalized_state, client_checkin)
        dominant = select_dominant_mode(mode_scores, modes)
        secondary = select_secondary_mode(mode_scores, dominant, modes)
        copy = content_for(register, dominant, content_dir)
        registers[register] = EIARegisterBlock(
            register=register,
            dominant_mode=dominant,
            secondary_mode=secondary,
            score=mode_scores[dominant],
            mechanism=copy["mechanism"],
            distortion=copy["distortion"],
            restoration=copy["restoration"],
            experiment=copy["experiment"],
            source_evidence=_source_evidence(register, dominant, eas_indexes),
        )
        scoring_table.extend(
            {"register": register, "mode": mode, "score": score}
            for mode, score in sorted(mode_scores.items(), key=lambda item: (-item[1], item[0]))
        )

    report = EIAReport(
        client=_client_block(natal_chart),
        method=_method_block(),
        architecture_summary=_architecture_summary(registers),
        registers=registers,
        pressure_patterns=_pressure_patterns(registers),
        mythic_overlay_optional=_mythic_overlay(eas_indexes),
        state_snapshot_optional=build_state_snapshot(state_overlay),
        technical_appendix={
            "natal_positions": _natal_positions(natal_chart),
            "register_scores": scoring_table,
        },
    )
    validate_report_dict(report.to_dict())
    return report


def _source_evidence(register: str, dominant: str, eas_indexes: dict[str, Any] | None) -> list[EIASourceEvidence]:
    evidence = [
        EIASourceEvidence("natal_astrology", f"{register} scored toward {dominant} from chart features.", 0.55),
        EIASourceEvidence("polarity_model", "Current-flow metaphor adjusted the mode score from element balance.", 0.15),
        EIASourceEvidence("biophysical_metaphor", "Signal, load, threshold, and recovery language shaped the copy.", 0.10),
    ]
    if eas_indexes:
        evidence.append(EIASourceEvidence("eas", "Existing EO/EAS indexes were included as resonance signals.", 0.20))
    return evidence


def _client_block(natal_chart: dict[str, Any]) -> dict[str, Any]:
    profile = natal_chart.get("user_profile", {})
    client = natal_chart.get("client", {})
    return {
        "name": client.get("name") or profile.get("name") or "Sample Client",
        "birth_datetime": client.get("birth_datetime") or profile.get("birth_datetime") or profile.get("birth_date") or "",
        "birth_location": client.get("birth_location") or profile.get("birth_location") or profile.get("location") or "",
        "birth_time_confidence": natal_chart.get("birth_time_confidence") or client.get("birth_time_confidence") or profile.get("birth_time_confidence") or "exact",
    }


def _method_block() -> dict[str, Any]:
    return {
        "house_system": "source natal payload",
        "zodiac": "source natal payload",
        "source_layers": ["natal_astrology", "eas_optional", "polarity_model", "state_overlay_optional"],
        "notes": "EIA is a symbolic operating-map engine, not a diagnostic system or command structure.",
    }


def _architecture_summary(registers: dict[str, EIARegisterBlock]) -> dict[str, Any]:
    return {
        "dominant_themes": [f"{register.title()}: {block.dominant_mode}" for register, block in registers.items()],
        "integration_sentence": (
            f"Movement tends to begin through {registers['ignition'].dominant_mode}; "
            f"clarity stabilizes through {registers['decision'].dominant_mode}; "
            f"coherence returns through {registers['restoration'].dominant_mode}."
        ),
    }


def _pressure_patterns(registers: dict[str, EIARegisterBlock]) -> list[EIAPressurePattern]:
    selected = sorted(registers.values(), key=lambda block: block.score, reverse=True)[:3]
    patterns = []
    used_names = set()
    for block in selected:
        pattern = _pressure_pattern_for(block)
        if pattern.name in used_names:
            pattern = EIAPressurePattern(
                name=f"{block.dominant_mode} Under Pressure",
                trigger=pattern.trigger,
                presentation=pattern.presentation,
                what_it_distorts=pattern.what_it_distorts,
                correction=pattern.correction,
            )
        used_names.add(pattern.name)
        patterns.append(pattern)
    return patterns


def _pressure_pattern_for(block: EIARegisterBlock) -> EIAPressurePattern:
    mode = block.dominant_mode
    names = {
        "Quiet Accumulation": "Forced Emergence",
        "Threshold Break": "Forced Breakthrough",
        "Direct Spark": "Spark Rush",
        "Responsive Pull": "Borrowed Yes",
        "Structured Commitment": "Rigid Start",
        "Relational Opening": "Contact Obligation",
        "Pattern Receiver": "False Pattern",
        "Mirror System": "Identity Blur",
        "Open Field": "Signal Flood",
        "Low-Noise Receiver": "Withdrawal Loop",
        "Selective Gate": "Over-Filtering",
        "Deep Sponge": "Emotional Saturation",
        "Immediate Knowing": "False Certainty",
        "Pattern Recognition": "Premature Pattern",
        "Stillness First": "Vanishing Pause",
        "Tidal Knowing": "Premature Yes",
        "Dialogic Knowing": "Over-Consulting",
        "Embodied Check": "Body Override",
        "Pulse Current": "Surge Burn",
        "Steady Flame": "Over-Obligation",
        "Seasonal Field": "Cycle Shame",
        "Borrowed Charge": "Borrowed Urgency",
        "Precision Battery": "Vague Drain",
        "Deep Reservoir": "Depth Drag",
        "Gate": "Vague Access",
        "Anchor": "Over-Holding",
        "Vessel": "Over-Containment",
        "Membrane": "Boundary Saturation",
        "Mirror": "Reflected Responsibility",
        "Blade": "Sharp Severance",
        "Wall": "Fortress Reflex",
        "Challenger": "Combative Clarity",
        "Translator": "Over-Translation",
        "Amplifier": "Volume Spill",
        "Witness": "Silent Certainty",
        "Catalyst": "Activation Overload",
        "Sanctuary": "Unbounded Holding",
        "Stabilizer": "Caretaker Drift",
        "Trusted Witnessing": "Audience Dependence",
        "Clean Agreement": "Vague Obligation",
        "Beauty and Pleasure": "Comfort Fog",
        "Movement and Heat": "Restless Repair",
        "Naming and Writing": "Explanation Loop",
        "Ritual and Repetition": "Ritual Lock",
        "Solitude and Sleep": "Disappearing Repair",
        "Material Simplification": "Control Cleanup",
    }
    name = names.get(mode, f"{mode} Under Pressure")
    return EIAPressurePattern(
        name=name,
        trigger=f"Activated when {mode} is rushed, overused, or asked to carry more than the {block.register} register can honestly process.",
        presentation=f"{block.when_pressured if hasattr(block, 'when_pressured') else block.distortion}",
        what_it_distorts=_pressure_distortion_target(name, block),
        correction=block.restoration,
    )


def _pressure_distortion_target(name: str, block: EIARegisterBlock) -> str:
    targets = {
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
    if name in targets:
        return targets[name]
    return f"The {block.register} register: the operating pattern under pressure."


def _mythic_overlay(eas_indexes: dict[str, Any] | None) -> dict[str, Any] | None:
    if not eas_indexes:
        return None
    return {
        "eas_current": str(eas_indexes.get("dominant_current", "available")),
        "expression": str(eas_indexes.get("expression", "EO resonance layer included")),
        "activation_state": str(eas_indexes.get("activation_state", "baseline")),
        "integration_note": "EAS material is treated as mythic resonance, not the skeleton of the EIA report.",
    }


def _natal_positions(natal_chart: dict[str, Any]) -> list[dict[str, Any]]:
    positions = []
    for body, point in natal_chart.get("standard_planets", {}).items():
        if isinstance(point, dict):
            positions.append(
                {
                    "body": body,
                    "sign": point.get("sign", ""),
                    "degree": str(point.get("degree", point.get("longitude", ""))),
                    "house": str(point.get("house", "")),
                }
            )
    return positions
