"""Pytest bootstrap for the local source tree.

The project has a historical package named ``selectors``. Python also ships a
stdlib module with that name, and pytest/subprocess imports can load the
stdlib module before tests import ``selectors.utils``. For active tests, pin
the repo package into ``sys.modules`` so collection exercises project code.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SELECTORS_INIT = ROOT / "selectors" / "__init__.py"


def _pin_local_selectors_package() -> None:
    loaded = sys.modules.get("selectors")
    if loaded is not None and hasattr(loaded, "__path__"):
        return

    spec = importlib.util.spec_from_file_location(
        "selectors",
        SELECTORS_INIT,
        submodule_search_locations=[str(SELECTORS_INIT.parent)],
    )
    if spec is None or spec.loader is None:
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules["selectors"] = module
    spec.loader.exec_module(module)


_pin_local_selectors_package()
