"""Entangled Oracle selector package.

This package intentionally contains report-selection modules such as
``selectors.variable_resolver``. Because its name shadows Python's stdlib
``selectors`` module, localhost tooling that imports ``selectors`` directly
can land here instead. Re-export the stdlib selector primitives so Werkzeug's
development server can keep using ``selectors.DefaultSelector`` while EO code
continues to import local selector submodules.
"""

from __future__ import annotations

import importlib.util
import sysconfig
from pathlib import Path


def _load_stdlib_selectors():
    stdlib_path = Path(sysconfig.get_path("stdlib")) / "selectors.py"
    spec = importlib.util.spec_from_file_location("_eo_stdlib_selectors", stdlib_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load stdlib selectors from {stdlib_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_stdlib_selectors = _load_stdlib_selectors()

for _name in getattr(_stdlib_selectors, "__all__", ()):
    globals()[_name] = getattr(_stdlib_selectors, _name)

EVENT_READ = _stdlib_selectors.EVENT_READ
EVENT_WRITE = _stdlib_selectors.EVENT_WRITE
DefaultSelector = _stdlib_selectors.DefaultSelector
