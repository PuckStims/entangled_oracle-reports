"""
Place Resonance Search context wrapper.

This package currently reuses the single-location Place Resonance evidence
path while presenting a distinct report identity for the emerging search
product.
"""
from __future__ import annotations

import copy

from products.location_services.place_resonance.assembler import (
    assemble_place_resonance_context as _assemble_place_resonance_context,
)
from products.location_services.place_resonance.assembler import (
    build_place_resonance_context as _build_place_resonance_context,
)
from products.location_services.place_resonance.assembler import (
    select_synthesis_category,
)


CONTEXT_VERSION = "place_resonance_search_context_v0.1.0"
REPORT_TYPE = "location_services.place_resonance_search"
PRODUCT_NAME = "Place Resonance Search"


def _retitle_context(context: dict) -> dict:
    updated = copy.deepcopy(context)
    updated["context_version"] = CONTEXT_VERSION
    updated["report_type"] = REPORT_TYPE
    updated["product_name"] = PRODUCT_NAME
    updated["source_product"] = "location_services.place_resonance"
    return updated


def assemble_place_resonance_search_context(evidence_record: dict) -> dict:
    return _retitle_context(_assemble_place_resonance_context(evidence_record))


def build_place_resonance_search_context(
    natal_payload: dict,
    destination: dict,
    *,
    purpose_lens: str | None = None,
    relationship_to_place: str | None = None,
) -> dict:
    return _retitle_context(
        _build_place_resonance_context(
            natal_payload,
            destination,
            purpose_lens=purpose_lens,
            relationship_to_place=relationship_to_place,
        )
    )
