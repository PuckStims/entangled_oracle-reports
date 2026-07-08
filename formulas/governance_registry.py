"""
Authoritative governance registries for bodies, methods, and report-layer policy.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

METHOD_STATUS_CORE_STANDARD = "core_standard"
METHOD_STATUS_ESTABLISHED_NICHE = "established_niche"
METHOD_STATUS_EO_PROPRIETARY = "eo_proprietary"

REPORT_PROFILE_CORE_STANDARD_ONLY = "core_standard_only"
REPORT_PROFILE_CORE_STANDARD_PLUS_ESTABLISHED_NICHE = "core_standard_plus_established_niche"
REPORT_PROFILE_CORE_STANDARD_PLUS_EO = "core_standard_plus_eo"
REPORT_PROFILE_FULL_ENTANGLED_ORACLE = "full_entangled_oracle"

BODY_KIND_BODY = "body"
BODY_KIND_ANGLE = "angle"
BODY_KIND_CALCULATED_POINT = "calculated_point"
BODY_KIND_ASTEROID = "asteroid"
BODY_KIND_ASPECT_METHOD = "aspect_method"
BODY_KIND_TIMING_METHOD = "timing_method"
BODY_KIND_DERIVED_CHART_STRUCTURE = "derived_chart_structure"
BODY_KIND_EO_FORMULA = "EO_formula/index"


@dataclass(frozen=True)
class RegistryRecord:
    internal_key: str
    display_name: str
    method_status: str
    item_kind: str
    lineage_tags: tuple[str, ...] = ()
    payload_locations: tuple[str, ...] = ()
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["lineage_tags"] = list(self.lineage_tags)
        data["payload_locations"] = list(self.payload_locations)
        return data


@dataclass(frozen=True)
class AsteroidEligibilityRecord:
    display_name: str
    internal_key: str
    catalog_number: int
    body_type: str
    method_status: str
    lineage: tuple[str, ...]
    available_payload_data: tuple[str, ...]
    eligible_report_types: tuple[str, ...]
    default_visibility: str
    birth_time_dependency: str
    confidence_requirements: tuple[str, ...]
    allowed_use_cases: tuple[str, ...]
    restricted_use_cases: tuple[str, ...]
    notes: str = ""
    eo_proprietary_uses: tuple[str, ...] = ()
    usable_now: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in (
            "lineage",
            "available_payload_data",
            "eligible_report_types",
            "confidence_requirements",
            "allowed_use_cases",
            "restricted_use_cases",
            "eo_proprietary_uses",
        ):
            data[key] = list(data[key])
        return data


REPORT_LAYER_RULES = {
    REPORT_PROFILE_CORE_STANDARD_ONLY: {
        "allow_core_standard": True,
        "allow_established_niche": False,
        "allow_eo_proprietary": False,
    },
    REPORT_PROFILE_CORE_STANDARD_PLUS_ESTABLISHED_NICHE: {
        "allow_core_standard": True,
        "allow_established_niche": True,
        "allow_eo_proprietary": False,
    },
    REPORT_PROFILE_CORE_STANDARD_PLUS_EO: {
        "allow_core_standard": True,
        "allow_established_niche": False,
        "allow_eo_proprietary": True,
    },
    REPORT_PROFILE_FULL_ENTANGLED_ORACLE: {
        "allow_core_standard": True,
        "allow_established_niche": True,
        "allow_eo_proprietary": True,
    },
}

REPORT_TYPE_TO_PROFILE = {
    "horoscope": REPORT_PROFILE_CORE_STANDARD_ONLY,
    "year_ahead": REPORT_PROFILE_CORE_STANDARD_PLUS_EO,
    "personal_forecast": REPORT_PROFILE_CORE_STANDARD_PLUS_EO,
    "soul_ecosystem": REPORT_PROFILE_FULL_ENTANGLED_ORACLE,
}

BODY_REGISTRY: dict[str, RegistryRecord] = {
    "Sun": RegistryRecord("Sun", "Sun", METHOD_STATUS_CORE_STANDARD, BODY_KIND_BODY, ("traditional", "modern"), ("standard_planets",)),
    "Moon": RegistryRecord("Moon", "Moon", METHOD_STATUS_CORE_STANDARD, BODY_KIND_BODY, ("traditional", "modern"), ("standard_planets",)),
    "Mercury": RegistryRecord("Mercury", "Mercury", METHOD_STATUS_CORE_STANDARD, BODY_KIND_BODY, ("traditional", "modern"), ("standard_planets",)),
    "Venus": RegistryRecord("Venus", "Venus", METHOD_STATUS_CORE_STANDARD, BODY_KIND_BODY, ("traditional", "modern"), ("standard_planets",)),
    "Mars": RegistryRecord("Mars", "Mars", METHOD_STATUS_CORE_STANDARD, BODY_KIND_BODY, ("traditional", "modern"), ("standard_planets",)),
    "Jupiter": RegistryRecord("Jupiter", "Jupiter", METHOD_STATUS_CORE_STANDARD, BODY_KIND_BODY, ("traditional", "modern"), ("standard_planets",)),
    "Saturn": RegistryRecord("Saturn", "Saturn", METHOD_STATUS_CORE_STANDARD, BODY_KIND_BODY, ("traditional", "modern"), ("standard_planets",)),
    "Uranus": RegistryRecord("Uranus", "Uranus", METHOD_STATUS_CORE_STANDARD, BODY_KIND_BODY, ("modern",), ("standard_planets",)),
    "Neptune": RegistryRecord("Neptune", "Neptune", METHOD_STATUS_CORE_STANDARD, BODY_KIND_BODY, ("modern",), ("standard_planets",)),
    "Pluto": RegistryRecord("Pluto", "Pluto", METHOD_STATUS_CORE_STANDARD, BODY_KIND_BODY, ("modern",), ("standard_planets",)),
    "North_Node": RegistryRecord("North_Node", "North Node", METHOD_STATUS_CORE_STANDARD, BODY_KIND_CALCULATED_POINT, ("traditional", "modern"), ("standard_planets",)),
    "South_Node": RegistryRecord("South_Node", "South Node", METHOD_STATUS_CORE_STANDARD, BODY_KIND_CALCULATED_POINT, ("traditional", "modern"), ("standard_planets",)),
    "Ascendant": RegistryRecord("Ascendant", "Ascendant", METHOD_STATUS_CORE_STANDARD, BODY_KIND_ANGLE, ("traditional", "modern"), ("angles",)),
    "Midheaven": RegistryRecord("Midheaven", "Midheaven", METHOD_STATUS_CORE_STANDARD, BODY_KIND_ANGLE, ("traditional", "modern"), ("angles",)),
    "Descendant": RegistryRecord("Descendant", "Descendant", METHOD_STATUS_CORE_STANDARD, BODY_KIND_ANGLE, ("traditional", "modern"), ("angles",)),
    "Imum_Coeli": RegistryRecord("Imum_Coeli", "Imum Coeli", METHOD_STATUS_CORE_STANDARD, BODY_KIND_ANGLE, ("traditional", "modern"), ("angles",)),
    "Vertex": RegistryRecord("Vertex", "Vertex", METHOD_STATUS_ESTABLISHED_NICHE, BODY_KIND_CALCULATED_POINT, ("modern",), ("angles",)),
    "Chiron": RegistryRecord("Chiron", "Chiron", METHOD_STATUS_ESTABLISHED_NICHE, BODY_KIND_BODY, ("modern", "specialist"), ("standard_planets",), notes="Available in live payload but excluded from core-standard dignity, dispositorship, sect, and rulership logic."),
    "Lilith_BML": RegistryRecord("Lilith_BML", "Black Moon Lilith", METHOD_STATUS_ESTABLISHED_NICHE, BODY_KIND_CALCULATED_POINT, ("modern", "lunar_apogee"), ("standard_planets",), notes="Calculated lunar-apogee point; never interchangeable with asteroid Lilith."),
    "Lilith_Asteroid": RegistryRecord("Lilith_Asteroid", "Asteroid Lilith", METHOD_STATUS_ESTABLISHED_NICHE, BODY_KIND_ASTEROID, ("modern", "asteroid"), ("custom_asteroids",), notes="Asteroid Lilith; distinct from Black Moon Lilith."),
}

METHOD_REGISTRY_CATALOG: dict[str, RegistryRecord] = {
    "rulership_network": RegistryRecord("rulership_network", "Rulership Network", METHOD_STATUS_CORE_STANDARD, BODY_KIND_DERIVED_CHART_STRUCTURE, ("traditional",), ("standard_results",)),
    "aspect_architecture": RegistryRecord("aspect_architecture", "Aspect Architecture", METHOD_STATUS_CORE_STANDARD, BODY_KIND_ASPECT_METHOD, ("traditional", "modern"), ("standard_results",)),
    "named_configurations": RegistryRecord("named_configurations", "Named Configurations", METHOD_STATUS_CORE_STANDARD, BODY_KIND_DERIVED_CHART_STRUCTURE, ("traditional", "modern"), ("standard_results",)),
    "chart_structure": RegistryRecord("chart_structure", "Chart Structure", METHOD_STATUS_CORE_STANDARD, BODY_KIND_DERIVED_CHART_STRUCTURE, ("standard_natal",), ("standard_results",)),
    "standard_natal_convergence": RegistryRecord("standard_natal_convergence", "Standard Natal Convergence", METHOD_STATUS_CORE_STANDARD, BODY_KIND_DERIVED_CHART_STRUCTURE, ("standard_natal",), ("standard_results",)),
    "specialist_body_context": RegistryRecord("specialist_body_context", "Specialist Body Context", METHOD_STATUS_ESTABLISHED_NICHE, BODY_KIND_DERIVED_CHART_STRUCTURE, ("specialist",), ("established_niche_results",)),
    "KVQ": RegistryRecord("KVQ", "Kassandra Validation Quotient", METHOD_STATUS_EO_PROPRIETARY, BODY_KIND_EO_FORMULA, ("EO",), ("index_results",)),
    "MKI": RegistryRecord("MKI", "Mythkeeper Index", METHOD_STATUS_EO_PROPRIETARY, BODY_KIND_EO_FORMULA, ("EO",), ("index_results",)),
    "RWI": RegistryRecord("RWI", "Reality Weaver Index", METHOD_STATUS_EO_PROPRIETARY, BODY_KIND_EO_FORMULA, ("EO",), ("index_results",)),
    "DFIS": RegistryRecord("DFIS", "Dark Feminine Integration Score", METHOD_STATUS_EO_PROPRIETARY, BODY_KIND_EO_FORMULA, ("EO",), ("index_results",)),
    "CATALYST": RegistryRecord("CATALYST", "Catalyst Index", METHOD_STATUS_EO_PROPRIETARY, BODY_KIND_EO_FORMULA, ("EO",), ("index_results",)),
    "NGE": RegistryRecord("NGE", "Narrative Genre Engine", METHOD_STATUS_EO_PROPRIETARY, BODY_KIND_EO_FORMULA, ("EO",), ("index_results",)),
    "AHL": RegistryRecord("AHL", "Ancestral Lineage Thread", METHOD_STATUS_EO_PROPRIETARY, BODY_KIND_EO_FORMULA, ("EO",), ("index_results",)),
}

ASTEROID_ELIGIBILITY_REGISTRY: dict[str, AsteroidEligibilityRecord] = {
    "Lilith_Asteroid": AsteroidEligibilityRecord(
        display_name="Asteroid Lilith",
        internal_key="Lilith_Asteroid",
        catalog_number=11181,
        body_type=BODY_KIND_ASTEROID,
        method_status=METHOD_STATUS_ESTABLISHED_NICHE,
        lineage=("modern", "asteroid"),
        available_payload_data=("longitude", "sign", "degree", "house", "retrograde_state", "speed", "aspects", "angle_contacts", "transit availability"),
        eligible_report_types=("soul_ecosystem",),
        default_visibility="expanded_section",
        birth_time_dependency="angle_contacts_and_house_require_exact_time",
        confidence_requirements=("exact_birth_time", "angle_dependent_unavailable"),
        allowed_use_cases=("natal sign placement", "natal house placement", "natal aspect context", "angle contact", "forecast transit", "technical appendix", "expanded report inclusion"),
        restricted_use_cases=("not part of core-standard dominance scoring", "not permitted to override chart ruler", "not permitted to override luminaries", "not permitted to generate deterministic claims", "not permitted to become EO proprietary evidence unless explicitly defined"),
        notes="Distinct from Black Moon Lilith and never a fallback for it.",
    ),
}

_SHARED_ASTEROID_USE_CASES = (
    "natal sign placement",
    "natal house placement",
    "natal aspect context",
    "angle contact",
    "retrograde context",
    "forecast transit",
    "technical appendix",
    "expanded report inclusion",
)
_SHARED_ASTEROID_RESTRICTIONS = (
    "not part of core-standard dominance scoring",
    "not permitted to override chart ruler",
    "not permitted to override luminaries",
    "not permitted to generate deterministic claims",
    "not permitted to become EO proprietary evidence unless explicitly defined",
)

for key, display_name, catalog_number, eo_uses in (
    ("Sirene", "Sirene", 11009, ("NGE", "MCQ", "SIREN", "MAGNETIC")),
    ("Aphrodite", "Aphrodite", 11388, ("NGE", "SIREN", "MAGNETIC")),
    ("Apollo", "Apollo", 11862, ("RWI", "NGE", "MCQ")),
    ("Kassandra", "Kassandra", 10114, ("KVQ",)),
    ("Karma", "Karma", 13811, ("CATALYST",)),
    ("Destinn", "Destinn", 16583, ("CATALYST", "NGE")),
    ("Mnemosyne", "Mnemosyne", 10057, ("MKI",)),
    ("Atlantis", "Atlantis", 11198, ("MKI",)),
    ("Sophia", "Sophia", 10251, ("MKI",)),
    ("Arachne", "Arachne", 10407, ("RWI",)),
    ("Chaos", "Chaos", 29521, ("RWI",)),
    ("Hermes", "Hermes", 79230, ("MKI", "RWI", "CATALYST")),
    ("Themis", "Themis", 10024, ("RWI", "NGE", "MCQ")),
    ("Euterpe", "Euterpe", 10027, ()),
    ("Urania", "Urania", 10030, ()),
    ("Polyhymnia", "Polyhymnia", 10033, ()),
    ("Circe", "Circe", 10034, ("DFIS",)),
    ("Isis", "Isis", 10042, ()),
    ("Melete", "Melete", 10056, ()),
    ("Sappho", "Sappho", 10080, ()),
    ("Terpsichore", "Terpsichore", 10081, ("NGE",)),
    ("Minerva", "Minerva", 10093, ()),
    ("Hekate", "Hekate", 10100, ("DFIS",)),
    ("Medea", "Medea", 10212, ("DFIS",)),
    ("Aletheia", "Aletheia", 10259, ()),
    ("Industria", "Industria", 10389, ()),
    ("Alma", "Alma", 10390, ()),
    ("Moirai", "Moirai", 10638, ("MCQ", "NGE")),
    ("Anubis", "Anubis", 11912, ("AHL",)),
    ("Kaali", "Kaali", 14227, ("DFIS",)),
    ("Child", "Child", 14580, ("AHL",)),
    ("Angel", "Angel", 21911, ()),
    ("DNA", "DNA", 65555, ("AHL",)),
):
    ASTEROID_ELIGIBILITY_REGISTRY[key] = AsteroidEligibilityRecord(
        display_name=display_name,
        internal_key=key,
        catalog_number=catalog_number,
        body_type=BODY_KIND_ASTEROID,
        method_status=METHOD_STATUS_ESTABLISHED_NICHE,
        lineage=("modern", "asteroid", "specialist"),
        available_payload_data=("longitude", "sign", "degree", "house", "retrograde_state", "speed", "aspects", "angle_contacts", "transit availability"),
        eligible_report_types=("soul_ecosystem",),
        default_visibility="technical_reference",
        birth_time_dependency="angle_contacts_and_house_require_exact_time",
        confidence_requirements=("exact_birth_time", "angle_dependent_unavailable"),
        allowed_use_cases=_SHARED_ASTEROID_USE_CASES,
        restricted_use_cases=_SHARED_ASTEROID_RESTRICTIONS,
        notes="Presence in payload does not imply core-standard weighting or automatic report inclusion.",
        eo_proprietary_uses=eo_uses,
    )


def get_body_registry_record(internal_key: str) -> RegistryRecord | None:
    if internal_key in BODY_REGISTRY:
        return BODY_REGISTRY[internal_key]
    if internal_key in ASTEROID_ELIGIBILITY_REGISTRY:
        record = ASTEROID_ELIGIBILITY_REGISTRY[internal_key]
        return RegistryRecord(
            internal_key=record.internal_key,
            display_name=record.display_name,
            method_status=record.method_status,
            item_kind=record.body_type,
            lineage_tags=tuple(record.lineage),
            payload_locations=("custom_asteroids",),
            notes=record.notes,
        )
    return None


def get_method_registry_record(method_key: str) -> RegistryRecord | None:
    return METHOD_REGISTRY_CATALOG.get(method_key)


def get_report_layer_profile(report_type: str) -> str:
    return REPORT_TYPE_TO_PROFILE.get(report_type, REPORT_PROFILE_CORE_STANDARD_ONLY)


def layer_allows(method_status: str, report_profile: str) -> bool:
    rules = REPORT_LAYER_RULES.get(report_profile, REPORT_LAYER_RULES[REPORT_PROFILE_CORE_STANDARD_ONLY])
    if method_status == METHOD_STATUS_CORE_STANDARD:
        return rules["allow_core_standard"]
    if method_status == METHOD_STATUS_ESTABLISHED_NICHE:
        return rules["allow_established_niche"]
    if method_status == METHOD_STATUS_EO_PROPRIETARY:
        return rules["allow_eo_proprietary"]
    return False


def authoritative_catalog() -> dict[str, Any]:
    return {
        "bodies_and_points": {
            key: value.to_dict()
            for key, value in sorted(
                {**BODY_REGISTRY, **{k: get_body_registry_record(k) for k in ASTEROID_ELIGIBILITY_REGISTRY}}.items()
            )
        },
        "methods": {
            key: value.to_dict()
            for key, value in sorted(METHOD_REGISTRY_CATALOG.items())
        },
        "asteroid_eligibility": {
            key: value.to_dict()
            for key, value in sorted(ASTEROID_ELIGIBILITY_REGISTRY.items())
        },
        "report_layer_rules": REPORT_LAYER_RULES,
        "report_type_defaults": REPORT_TYPE_TO_PROFILE,
    }
