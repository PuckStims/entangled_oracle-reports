"""Advanced synthesis layers for Internal Architecture reports."""

from __future__ import annotations

from typing import Any


REGISTER_LABELS = {
    "ignition": "Ignition",
    "reception": "Reception",
    "decision": "Decision",
    "current": "Current",
    "boundary": "Boundary",
    "contact": "Contact",
    "restoration": "Restoration",
}

REGISTER_FUNCTIONS = {
    "ignition": "how movement begins",
    "reception": "how information earns trust",
    "decision": "how recognition becomes choice",
    "current": "how energy spends and returns",
    "boundary": "how access is shaped",
    "contact": "how the field changes when the person enters it",
    "restoration": "how coherence comes back",
}

MODE_BEHAVIORS = {
    "Quiet Accumulation": "gathers privately until enough evidence, density, or pressure has collected",
    "Threshold Break": "marks the moment when staying hidden costs more than emerging",
    "Pattern Receiver": "waits for recurrence before trusting meaning",
    "Mirror System": "uses reflection from people and rooms as part of the signal",
    "Immediate Knowing": "catches the first clean answer before explanation crowds it",
    "Pattern Recognition": "checks first recognition against the larger structure",
    "Pulse Current": "moves through surges, output, and integration phases",
    "Steady Flame": "keeps energy usable through rhythm and repeatable devotion",
    "Gate": "keeps contact honest by naming access, timing, and scope",
    "Anchor": "steadies the field without becoming responsible for all of it",
    "Challenger": "names friction directly when false peace is weakening the field",
    "Translator": "turns friction into language other people can actually use",
    "Trusted Witnessing": "returns coherence through clear, kind reflection",
    "Clean Agreement": "turns repair into explicit terms, limits, or next commitments",
}

MODE_MISREADS = {
    "Quiet Accumulation": {
        "others": "Others may read the quiet phase as hesitation when it is often active preparation.",
        "self": "From the inside, preparation can start to look like delay if no emergence marker is named.",
    },
    "Threshold Break": {
        "others": "Others may read the break as sudden when the pressure has often been gathering for a long time.",
        "self": "From the inside, urgency can make every strain look like the threshold.",
    },
    "Pattern Receiver": {
        "others": "Others may read the need for repeated evidence as doubt when it is often the accuracy process.",
        "self": "From the inside, a partial pattern can feel complete before enough evidence has arrived.",
    },
    "Mirror System": {
        "others": "Others may read reflection as changeability when the system is actually sorting field from self.",
        "self": "From the inside, another person's state can become too easy to mistake for your own signal.",
    },
    "Immediate Knowing": {
        "others": "Others may read fast clarity as impulsive when it may be the first clean signal arriving intact.",
        "self": "From the inside, first knowing can be mistaken for final certainty.",
    },
    "Pattern Recognition": {
        "others": "Others may read pattern-checking as overthinking when it is often how the choice becomes trustworthy.",
        "self": "From the inside, the mind can close the pattern before the present situation has finished reporting.",
    },
    "Pulse Current": {
        "others": "Others may read surging output as the normal baseline when it is only one phase of the current.",
        "self": "From the inside, the high-output phase can start to feel like the only legitimate version.",
    },
    "Steady Flame": {
        "others": "Others may read consistency as endless availability when it still has a real maintenance cost.",
        "self": "From the inside, devotion can drift into obligation if recovery is not protected.",
    },
    "Gate": {
        "others": "Others may read Gate as distance when it is often the condition that lets contact stay honest.",
        "self": "From the inside, a clean limit can feel harsher than it is when connection matters.",
    },
    "Anchor": {
        "others": "Others may read steadiness as capacity to hold everything.",
        "self": "From the inside, being useful can blur into becoming the floor for the room.",
    },
    "Challenger": {
        "others": "Others may read direct friction as attack when the intended function is to make avoidance visible.",
        "self": "From the inside, truth can arrive sharper than the relationship can use.",
    },
    "Translator": {
        "others": "Others may read translation as interpretation they did not consent to receive.",
        "self": "From the inside, explanation can continue after the signal is already clear.",
    },
    "Trusted Witnessing": {
        "others": "Others may read the need for witness as dependence when it is often the repair pathway.",
        "self": "From the inside, the wrong audience can start to feel like coherence.",
    },
    "Clean Agreement": {
        "others": "Others may read explicit terms as formality when they are often what keeps repair usable.",
        "self": "From the inside, agreement can become control if every loose edge feels unsafe.",
    },
}

PRESSURE_CASCADE_ORDER = ("ignition", "reception", "current", "decision", "boundary", "contact", "restoration")


def build_advanced_layers(
    registers: dict[str, Any],
    pressure_patterns: list[Any],
    technical_appendix: dict[str, Any],
    client: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blocks = {register: _block_dict(block) for register, block in registers.items()}
    blends = [_blend_for(register, blocks[register]) for register in REGISTER_LABELS if register in blocks]
    pressure = [_pattern_dict(pattern) for pattern in pressure_patterns]
    return {
        "blend_grammar": blends,
        "core_operating_tension": _core_operating_tension(blocks),
        "pressure_cascade": _pressure_cascade(blocks, pressure),
        "misread_lenses": _misread_lenses(blocks),
        "operating_contexts": _operating_contexts(blocks),
        "restoration_matrix": _restoration_matrix(blocks, pressure),
        "evidence_appendix": _evidence_appendix(blocks, technical_appendix, client or {}),
    }


def _block_dict(block: Any) -> dict[str, Any]:
    if isinstance(block, dict):
        return block
    return {
        "register": block.register,
        "dominant_mode": block.dominant_mode,
        "secondary_mode": block.secondary_mode,
        "score": block.score,
        "mechanism": block.mechanism,
        "distortion": block.distortion,
        "restoration": block.restoration,
        "experiment": block.experiment,
        "source_evidence": [getattr(item, "__dict__", item) for item in block.source_evidence],
    }


def _pattern_dict(pattern: Any) -> dict[str, str]:
    if isinstance(pattern, dict):
        return pattern
    return {
        "name": pattern.name,
        "trigger": pattern.trigger,
        "presentation": pattern.presentation,
        "what_it_distorts": pattern.what_it_distorts,
        "correction": pattern.correction,
    }


def _blend_for(register: str, block: dict[str, Any]) -> dict[str, str]:
    primary = block.get("dominant_mode", "")
    secondary = block.get("secondary_mode") or ""
    blend_type = _blend_type(primary, secondary, register)
    return {
        "register": register,
        "label": REGISTER_LABELS[register],
        "primary_mode": primary,
        "secondary_mode": secondary,
        "blend_type": blend_type,
        "description": _blend_description(register, primary, secondary, blend_type),
    }


def _blend_type(primary: str, secondary: str, register: str) -> str:
    if not secondary:
        return "reinforcing"
    pair = {primary, secondary}
    if pair & {"Translator", "Mirror System", "Pattern Recognition", "Clean Agreement"}:
        return "translating"
    if pair & {"Steady Flame", "Anchor", "Gate"}:
        return "corrective"
    if pair & {"Threshold Break", "Pulse Current", "Immediate Knowing", "Challenger"} and register in {"ignition", "decision", "contact"}:
        return "paradoxical"
    if pair & {"Threshold Break", "Blade", "Wall", "Movement and Heat"}:
        return "pressure-activated"
    return "reinforcing"


def _blend_description(register: str, primary: str, secondary: str, blend_type: str) -> str:
    primary_behavior = MODE_BEHAVIORS.get(primary, f"organizes {REGISTER_FUNCTIONS.get(register, 'this register')}")
    if not secondary:
        return f"{primary} is the main engine here: it {primary_behavior}."
    secondary_behavior = MODE_BEHAVIORS.get(secondary, f"modifies how {primary} expresses")
    if blend_type == "corrective":
        return f"{primary} leads: it {primary_behavior}. {secondary} keeps that movement from overextending because it {secondary_behavior}."
    if blend_type == "paradoxical":
        return f"{primary} leads: it {primary_behavior}. {secondary} introduces a timing tension because it {secondary_behavior}."
    if blend_type == "translating":
        return f"{primary} leads: it {primary_behavior}. {secondary} makes the signal more legible because it {secondary_behavior}."
    if blend_type == "pressure-activated":
        return f"{primary} leads: it {primary_behavior}. Under load, {secondary} becomes more visible because it {secondary_behavior}."
    return f"{primary} leads: it {primary_behavior}. {secondary} reinforces the same register because it {secondary_behavior}."


def _core_operating_tension(blocks: dict[str, dict[str, Any]]) -> dict[str, str]:
    ignition = _mode(blocks, "ignition")
    reception = _mode(blocks, "reception")
    decision = _mode(blocks, "decision")
    current = _mode(blocks, "current")
    boundary = _mode(blocks, "boundary")
    contact = _mode(blocks, "contact")
    restoration = _mode(blocks, "restoration")
    return {
        "title": "How This Architecture Moves",
        "summary": (
            f"The central intelligence of this map is sequenced trust: {ignition} lets movement gather before it is exposed, "
            f"{reception} asks the signal to prove itself over time, and {decision} can move quickly once enough of the pattern is known."
        ),
        "tension": (
            f"The distortion appears when one register tries to solve the whole system alone. {decision} can close too soon, "
            f"{current} can spend energy as proof, {boundary} can turn access into the whole question, and {contact} can make friction louder than repair."
        ),
        "integration": (
            f"The architecture becomes more trustworthy when {boundary} controls the terms of contact, {current} is allowed to include recovery, "
            f"and {restoration} gives the field somewhere clear to return."
        ),
    }


def _pressure_cascade(blocks: dict[str, dict[str, Any]], pressure_patterns: list[dict[str, str]]) -> dict[str, Any]:
    pattern_by_register = {_register_from_pattern(pattern, blocks): pattern for pattern in pressure_patterns}
    ordered_registers = [register for register in PRESSURE_CASCADE_ORDER if register in pattern_by_register]
    if not ordered_registers:
        ordered_registers = [block.get("register", "") for block in blocks.values()][:3]
    first = ordered_registers[0]
    second = ordered_registers[1] if len(ordered_registers) > 1 else "current"
    third = ordered_registers[2] if len(ordered_registers) > 2 else "decision"
    restoration = blocks.get("restoration", {})
    return {
        "first_distortion": _pattern_name(pattern_by_register.get(first), blocks.get(first)),
        "compensating_distortion": _pattern_name(pattern_by_register.get(second), blocks.get(second)),
        "secondary_distortion": _pattern_name(pattern_by_register.get(third), blocks.get(third)),
        "sequence": (
            f"When {_mode(blocks, first)} is rushed or overloaded, {_pattern_name(pattern_by_register.get(first), blocks.get(first))} can appear first. "
            f"The system may then compensate through {_mode(blocks, second)}, which can create {_pattern_name(pattern_by_register.get(second), blocks.get(second))}. "
            f"If that compensation feels relieving, {_mode(blocks, third)} may treat relief as the whole truth, creating {_pattern_name(pattern_by_register.get(third), blocks.get(third))}."
        ),
        "earliest_repair_point": (
            f"The earliest repair point is before compensation becomes proof: pause at {_mode(blocks, first)} and name what is actually known before {_mode(blocks, second)} spends more energy."
        ),
        "restoration_key": (
            f"{_mode(blocks, 'restoration')} restores the chain by reflecting what is known, what is not known yet, and what agreement or next step can safely hold."
        ),
        "steps": [
            {"label": "First distortion", "value": _pattern_name(pattern_by_register.get(first), blocks.get(first))},
            {"label": "Compensating distortion", "value": _pattern_name(pattern_by_register.get(second), blocks.get(second))},
            {"label": "Secondary distortion", "value": _pattern_name(pattern_by_register.get(third), blocks.get(third))},
            {"label": "Restoration key", "value": restoration.get("dominant_mode", "")},
        ],
    }


def _misread_lenses(blocks: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    lenses = []
    for register in REGISTER_LABELS:
        block = blocks.get(register, {})
        primary = block.get("dominant_mode", "")
        if primary not in MODE_MISREADS:
            continue
        lenses.append(
            {
                "register": REGISTER_LABELS[register],
                "mode": primary,
                "others": MODE_MISREADS[primary]["others"],
                "self": MODE_MISREADS[primary]["self"],
            }
        )
    return lenses


def _operating_contexts(blocks: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    ignition = _mode(blocks, "ignition")
    decision = _mode(blocks, "decision")
    current = _mode(blocks, "current")
    boundary = _mode(blocks, "boundary")
    contact = _mode(blocks, "contact")
    restoration = _mode(blocks, "restoration")
    reception = _mode(blocks, "reception")
    return [
        {
            "context": "Work / Vocation",
            "description": f"{current} works best when contribution can happen in defined bursts and {boundary} names scope before capacity is assumed.",
        },
        {
            "context": "Relationships",
            "description": f"{contact} is more useful when truth-telling has somewhere safe to land; {restoration} helps reflection become repair instead of performance.",
        },
        {
            "context": "Creative Process",
            "description": f"{ignition} may keep the work invisible until the pattern has enough density; {decision} helps choose the moment when private formation becomes a first visible move.",
        },
        {
            "context": "Conflict",
            "description": f"{boundary} should set the terms before {contact} intensifies the field, so clarity can expose the issue without taking over the whole relationship.",
        },
        {
            "context": "Rest and Recovery",
            "description": f"{current} needs recovery treated as part of the operating rhythm, and {restoration} gives that return a witness or agreement instead of leaving it vague.",
        },
        {
            "context": "Major Transitions",
            "description": f"{reception} helps separate real patterns from charged noise, while {ignition} and {decision} need to speak before the next commitment is treated as final.",
        },
    ]


def _restoration_matrix(blocks: dict[str, dict[str, Any]], pressure_patterns: list[dict[str, str]]) -> list[dict[str, str]]:
    boundary = _mode(blocks, "boundary")
    current = _mode(blocks, "current")
    restoration = _mode(blocks, "restoration")
    rows = [
        {
            "state": "When the system is overexposed",
            "repair": f"Let {boundary} reduce the audience before interpretation starts.",
        },
        {
            "state": "When the system is overcommitted",
            "repair": "Renegotiate the agreement before treating endurance as the only proof of care.",
        },
        {
            "state": "When input gets too loud",
            "repair": "Lower noise before meaning-making, then check which signals repeat after the field quiets.",
        },
        {
            "state": "When certainty arrives too fast",
            "repair": "Insert one pause, one body check, and one consequence check before commitment.",
        },
        {
            "state": "When output has burned through recovery",
            "repair": f"Plan the integration phase before {current} spends the next surge.",
        },
        {
            "state": "When repair needs a place to land",
            "repair": f"Use {restoration} to name what was heard, what is still unknown, and what can be agreed next.",
        },
    ]
    active_names = {pattern.get("name") for pattern in pressure_patterns}
    if "Forced Emergence" in active_names:
        rows.insert(0, {"state": "When emergence is being forced", "repair": "Protect the incubation period and name the concrete marker for readiness."})
    return rows


def _evidence_appendix(
    blocks: dict[str, dict[str, Any]],
    technical_appendix: dict[str, Any],
    client: dict[str, Any],
) -> list[dict[str, Any]]:
    scores = technical_appendix.get("register_scores", []) if isinstance(technical_appendix, dict) else []
    by_register: dict[str, list[dict[str, Any]]] = {}
    for row in scores:
        register = str(row.get("register", ""))
        if register:
            by_register.setdefault(register, []).append(row)
    appendix = []
    for register in REGISTER_LABELS:
        block = blocks.get(register, {})
        ranked = sorted(by_register.get(register, []), key=lambda row: float(row.get("score", 0.0)), reverse=True)
        appendix.append(
            {
                "register": REGISTER_LABELS[register],
                "primary_mode": block.get("dominant_mode", ""),
                "secondary_mode": block.get("secondary_mode") or "",
                "blend_status": _blend_type(block.get("dominant_mode", ""), block.get("secondary_mode") or "", register),
                "strongest_source_layers": _source_layers(block),
                "close_alternates": [row.get("mode", "") for row in ranked[2:5] if row.get("mode")],
                "confidence_note": _confidence_note(float(block.get("score", 0.0))),
                "birth_time_sensitivity": _birth_time_sensitivity(client),
            }
        )
    return appendix


def _birth_time_sensitivity(client: dict[str, Any]) -> str:
    confidence = str(client.get("birth_time_confidence") or "").strip().lower()
    if confidence in {"exact", "exact_birth_time", "exact time supplied"}:
        return "Exact birth time supports house and angle-sensitive register evidence."
    if confidence:
        return "House and angle-sensitive evidence should be held more softly for this birth-time confidence state."
    return "Birth-time confidence was not supplied; house and angle-sensitive evidence should be held softly."


def _source_layers(block: dict[str, Any]) -> list[str]:
    labels = {
        "natal_astrology": "natal chart",
        "polarity_model": "current model",
        "biophysical_metaphor": "signal/load language",
        "eas": "EO resonance",
    }
    layers = []
    for evidence in block.get("source_evidence", []) or []:
        layer = evidence.get("source_layer", "") if isinstance(evidence, dict) else getattr(evidence, "source_layer", "")
        if layer:
            layers.append(labels.get(layer, layer.replace("_", " ")))
    return list(dict.fromkeys(layers))


def _confidence_note(score: float) -> str:
    if score >= 0.68:
        return "Primary signal is strong for this register."
    if score >= 0.54:
        return "Primary signal is usable, with nearby modes worth keeping in view."
    return "Signal is distributed; treat mode language as exploratory."


def _mode(blocks: dict[str, dict[str, Any]], register: str) -> str:
    return blocks.get(register, {}).get("dominant_mode", REGISTER_LABELS.get(register, register))


def _pattern_name(pattern: dict[str, str] | None, block: dict[str, Any] | None) -> str:
    if pattern and pattern.get("name"):
        return pattern["name"]
    if block:
        return str(block.get("distortion") or f"{block.get('dominant_mode', 'Register')} under pressure")
    return "pressure distortion"


def _register_from_pattern(pattern: dict[str, str], blocks: dict[str, dict[str, Any]]) -> str:
    distorted = pattern.get("what_it_distorts", "").lower()
    for register in REGISTER_LABELS:
        if register in distorted:
            return register
    trigger = pattern.get("trigger", "").lower()
    for register, block in blocks.items():
        mode = str(block.get("dominant_mode", "")).lower()
        if mode and mode in trigger:
            return register
    return ""
