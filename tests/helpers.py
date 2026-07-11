"""Shared helper: load a module from a number-prefixed package directory.

The AURORA-SWING modules live in directories like ``01_data`` whose names start
with a digit, so they cannot be imported with a normal ``import`` statement.
These tests load individual leaf module files by path via importlib.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from types import ModuleType

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_module(rel_path: str, name: str) -> ModuleType:
    """Load ``<repo>/<rel_path>`` as a module object registered under ``name``."""
    path = os.path.join(ROOT, rel_path)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {rel_path}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod
