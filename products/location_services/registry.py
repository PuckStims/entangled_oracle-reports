"""
Location Services Product Registry

This module defines the pluggable architecture for Location Services products.
It allows Place Resonance and the expanding location product family to
register themselves as distinct modules without hardcoding them into the
main routing logic.
"""
from typing import Callable, Dict, Type

class LocationProduct:
    """
    Base class for all Location Services products.
    Each product must inherit from this and define its report_type.
    """
    report_type: str = ""

    def build_context(self, *args, **kwargs) -> dict:
        """
        Builds the context object for this product.
        The exact signature may vary by product depending on inputs required.
        """
        raise NotImplementedError("build_context must be implemented by subclasses.")

    def render_html(self, context: dict) -> str:
        """
        Renders the context object into HTML.
        """
        raise NotImplementedError("render_html must be implemented by subclasses.")


_PRODUCT_REGISTRY: Dict[str, LocationProduct] = {}


def register_location_product(report_type: str) -> Callable[[Type[LocationProduct]], Type[LocationProduct]]:
    """
    Decorator to register a LocationProduct implementation into the global registry.
    """
    def decorator(cls: Type[LocationProduct]) -> Type[LocationProduct]:
        if not issubclass(cls, LocationProduct):
            raise TypeError(f"Class {cls.__name__} must inherit from LocationProduct")
        _PRODUCT_REGISTRY[report_type] = cls()
        return cls
    return decorator


def get_location_product(report_type: str) -> LocationProduct:
    """
    Retrieves a registered LocationProduct instance.
    """
    if report_type not in _PRODUCT_REGISTRY:
        raise ValueError(f"Unknown location product: {report_type}")
    return _PRODUCT_REGISTRY[report_type]

def list_location_products() -> list[str]:
    """
    Returns a list of all registered location product report types.
    """
    return list(_PRODUCT_REGISTRY.keys())
