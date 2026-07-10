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


@dataclass(frozen=True)
class PredictiveMethodRecord:
    display_name: str
    internal_key: str
    calculation_convention: str
    required_inputs: tuple[str, ...]
    birth_time_dependency: str
    supported_bodies_and_points: tuple[str, ...]
    orb_and_window_policy: str
    confidence_policy: str
    report_surface_permission: tuple[str, ...]
    method_status: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("required_inputs", "supported_bodies_and_points", "report_surface_permission"):
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


PREDICTIVE_METHOD_REGISTRY: dict[str, PredictiveMethodRecord] = {
    "annual_profections": PredictiveMethodRecord(
        display_name="Annual Profections",
        internal_key="annual_profections",
        calculation_convention="Phase 4 whole-sign annual periods",
        required_inputs=("birth_date", "ascendant_sign"),
        birth_time_dependency="none",
        supported_bodies_and_points=("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"),
        orb_and_window_policy="1 year window per period",
        confidence_policy="0.8415 if time known, 0.65 if unknown",
        report_surface_permission=("internal_rd", "engineering_diagnostic"),
        method_status="internal",
        notes=(
            "Calculates: a full TimeLordPeriod span per year (not just a "
            "window) -- profected sign/house from the natal Ascendant, the "
            "traditional ruler of that sign as time lord, and that lord's "
            "real house/sign/retrograde state pulled from the natal payload. "
            "Does not calculate: the time lord's aspects (always empty) or a "
            "real dignity/essential-condition read -- 'condition' is only "
            "available/unavailable (data presence), not domicile/exalted/"
            "fallen; no monthly-profection period logic exists in this file. "
            "Can claim: which planet is time lord for a given year, and "
            "whether it's angular/retrograde/in a known house. Merely "
            "contextualizes: currently consumed only as an internal transit-"
            "scoring weight via time_lord_periods; no standalone 'Lord of "
            "the Year' content exists in any report."
        ),
    ),
    "progressions": PredictiveMethodRecord(
        display_name="Secondary Progressions",
        internal_key="progressions",
        calculation_convention="One ephemeris day per tropical year (Naibod)",
        required_inputs=("birth_date", "julian_day", "standard_planets", "angles"),
        birth_time_dependency="hard for angles, soft for planets",
        supported_bodies_and_points=("Sun", "Moon", "Mercury", "Venus", "Mars", "Ascendant", "Midheaven", "Custom Asteroids"),
        orb_and_window_policy="1.0 degree contact orb, 0.5 angle orb",
        confidence_policy="0.90 max, withheld if angle involved without exact time",
        report_surface_permission=("year_ahead", "personal_forecast", "internal_rd", "engineering_diagnostic"),
        method_status="production",
        notes=(
            "Calculates: three distinct variants -- progressed body-to-natal "
            "contacts, progressed sign ingresses, and progressed lunation "
            "phase events (new/full moon in the progressed chart) -- one "
            "ephemeris day per year of life. Does not calculate: anything "
            "about progressed houses beyond Ascendant/Midheaven contacts; no "
            "progressed-chart interpretation beyond these three event types. "
            "Can claim: the date a progressed contact/ingress/phase becomes "
            "exact, and a confidence score gated on birth-time exactness for "
            "angle-involved contacts. Merely contextualizes: computed into "
            "report context today -- Moon-progression contacts feed "
            "personal_forecast (include_moon_progressions), 'year texture' "
            "progressions feed year_ahead (include_year_texture) -- but "
            "neither is rendered by a template/prose block yet; context "
            "presence is not proof of client-visible copy."
        ),
    ),
    "solar_arc": PredictiveMethodRecord(
        display_name="Solar Arc Directions",
        internal_key="solar_arc",
        calculation_convention="Naibod secondary-Sun arc applied to natal points",
        required_inputs=("birth_date", "julian_day", "standard_planets"),
        birth_time_dependency="hard for angles, soft for planets",
        supported_bodies_and_points=("Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto", "Chiron", "Ascendant", "Midheaven", "Vertex", "Custom Asteroids"),
        orb_and_window_policy="1.0 degree orb, 90 day chapter window",
        confidence_policy="0.90 max, withheld if angle involved without exact time",
        report_surface_permission=("year_ahead", "internal_rd", "engineering_diagnostic"),
        method_status="production",
        notes=(
            "Calculates: Naibod-adjusted solar-arc contacts -- the natal "
            "Sun's progressed daily motion applied uniformly to all natal "
            "points, then checked for aspect contacts to natal targets. Does "
            "not calculate: any arc convention other than the single Naibod "
            "one declared above (no alternate arc conventions are mixed in "
            "the same formula version). Can claim: the date a solar-arc "
            "contact becomes exact, and a confidence score gated on "
            "birth-time exactness for angle-involved contacts. Merely "
            "contextualizes: computed into year_ahead context today as "
            "'year texture' (include_year_texture); not consumed by "
            "personal_forecast, and not rendered by a template/prose block "
            "yet."
        ),
    ),
    "returns": PredictiveMethodRecord(
        display_name="Exact Returns",
        internal_key="returns",
        calculation_convention="Exact longitudinal return to natal position",
        required_inputs=("standard_planets",),
        birth_time_dependency="none",
        supported_bodies_and_points=("Sun", "Moon", "Jupiter", "Saturn"),
        orb_and_window_policy="0.01 degree tolerance",
        confidence_policy="0.833",
        report_surface_permission=("internal_rd", "engineering_diagnostic"),
        method_status="internal",
        notes=(
            "Calculates: the exact moment (0.01-degree tolerance) a body "
            "returns to its natal longitude. Does not calculate: anything "
            "about the return chart itself -- no return-chart houses, "
            "angles, or aspects; the module's own docstring states "
            "return-chart interpretation is 'intentionally deferred.' Can "
            "claim: the date/time of a return, with a confidence score for "
            "that timing. Merely contextualizes: a bare timestamp today, "
            "nothing about what the return 'means' beyond that moment; not "
            "consumed by any report path."
        ),
    ),
    "lots": PredictiveMethodRecord(
        display_name="Calculated Lots",
        internal_key="lots",
        calculation_convention="Fortune/Spirit/Necessity with day/night sect reversal",
        required_inputs=("Sun", "Moon", "Mercury", "Ascendant", "Sect"),
        birth_time_dependency="hard",
        supported_bodies_and_points=("Fortune", "Spirit", "Necessity"),
        orb_and_window_policy="Natal position",
        confidence_policy="1.0 if sect resolved, 0.5 if unknown",
        report_surface_permission=("internal_rd", "engineering_diagnostic"),
        method_status="internal",
        notes=(
            "Calculates: Fortune/Spirit/Necessity longitude, sign, and house "
            "via the day/night sect formulas; when sect can't be resolved "
            "(Sun exactly on the horizon axis) it falls back to the day "
            "formula and flags sect_state='unknown' with reduced confidence "
            "rather than guessing. Does not calculate: any event or period "
            "of its own -- Lots are static natal points with no timing, so "
            "they never enter the ForecastEvent/TimeLordPeriod pipeline "
            "directly. Can claim: a chart position, exactly like a natal "
            "point. Merely contextualizes: they exist to feed Zodiacal "
            "Releasing's period math; no standalone Lots content exists in "
            "any report today."
        ),
    ),
    "zodiacal_releasing": PredictiveMethodRecord(
        display_name="Zodiacal Releasing",
        internal_key="zodiacal_releasing",
        calculation_convention="Vettius Valens periods from Lot of Fortune/Spirit",
        required_inputs=("birth_date", "Lot of Fortune", "Lot of Spirit"),
        birth_time_dependency="soft",
        supported_bodies_and_points=("L1", "L2", "L3", "L4", "Peak", "LOB"),
        orb_and_window_policy="Valens fixed years by sign",
        confidence_policy="0.80",
        report_surface_permission=("internal_rd", "engineering_diagnostic"),
        method_status="internal",
        notes=(
            "Calculates: a full L1-L4 TimeLordPeriod tree from Lot of "
            "Fortune/Spirit using the Vettius Valens year-per-sign table, "
            "including peak and Loosing-of-the-Bond detection; the period "
            "lord's real house/sign/retrograde state (lord_natal_state, "
            "same convention as annual_profections -- previously a "
            "hardcoded stub, activated 2026-07-10). Does not calculate: the "
            "lord's aspects (always empty, same limit as annual_profections) "
            "or a real dignity/essential-condition read -- 'condition' is "
            "only available/unavailable (data presence), not domicile/"
            "exalted/fallen. Can claim: which sign/lord governs a given "
            "span at each of the four levels, whether that span is a peak "
            "or Loosing-of-the-Bond moment, and that lord's real house/"
            "retrograde placement. Merely contextualizes: not consumed by "
            "any report path yet; L3/L4 are "
            "explicitly modifier-scale only per the module's own docstring, "
            "not meant to justify a candidate on their own."
        ),
    ),
}


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


def get_predictive_method_record(method_key: str) -> PredictiveMethodRecord | None:
    return PREDICTIVE_METHOD_REGISTRY.get(method_key)


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
        "predictive_methods": {
            key: value.to_dict()
            for key, value in sorted(PREDICTIVE_METHOD_REGISTRY.items())
        },
        "asteroid_eligibility": {
            key: value.to_dict()
            for key, value in sorted(ASTEROID_ELIGIBILITY_REGISTRY.items())
        },
        "report_layer_rules": REPORT_LAYER_RULES,
        "report_type_defaults": REPORT_TYPE_TO_PROFILE,
    }
