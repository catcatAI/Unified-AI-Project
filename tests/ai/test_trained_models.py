"""
Import tests for ai.models (deleted in Phase 9-12 cleanup).

Preserved as informative skips so any re-introduction is noticed.
"""

import importlib

import pytest

_MODELS = [
    "ai.models.model_data_types",
    "ai.models.model_types",
    "ai.models.trained_model_manager",
]


def _try_import(mod_path: str):
    try:
        return importlib.import_module(mod_path)
    except (ImportError, ModuleNotFoundError):
        return None


@pytest.mark.parametrize("module_path", _MODELS,
                         ids=lambda x: x.split(".")[-1])
def test_model_module_import(module_path: str) -> None:
    mod = _try_import(module_path)
    if mod is None:
        pytest.skip(f"{module_path} — deleted in Phase 9-12 cleanup")
