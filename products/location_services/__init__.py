"""
Location Services Module.

Initializes the pluggable architecture for location services products.
Importing this package automatically registers the available products.
"""
import os
import importlib

from products.location_services.registry import get_location_product, list_location_products, LocationProduct
from products.location_services.routing import (
    LOCATION_REPORT_TYPE_MAP,
    build_location_report_artifacts,
    is_location_report_type,
    location_report_window,
    public_location_report_type,
    resolve_location_report_type,
)

# Dynamically load all plugins in subdirectories so they register themselves
_PACKAGE_DIR = os.path.dirname(__file__)

for _item in os.listdir(_PACKAGE_DIR):
    _item_path = os.path.join(_PACKAGE_DIR, _item)
    if os.path.isdir(_item_path) and not _item.startswith("_") and not _item.startswith("."):
        _plugin_file = os.path.join(_item_path, "plugin.py")
        if os.path.exists(_plugin_file):
            importlib.import_module(f"products.location_services.{_item}.plugin")

__all__ = [
    "get_location_product",
    "list_location_products",
    "LocationProduct",
    "LOCATION_REPORT_TYPE_MAP",
    "build_location_report_artifacts",
    "is_location_report_type",
    "location_report_window",
    "public_location_report_type",
    "resolve_location_report_type",
]
