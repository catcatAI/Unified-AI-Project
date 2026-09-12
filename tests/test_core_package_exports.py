"""Package-level export guards (R16): a dead name in a try/except import
block once nulled a whole package (core.allocation.AllocationStage did not
exist → AllocationPolicy et al. were all None at runtime).

Every __all__ entry must resolve to a non-None object.
"""

import importlib

import pytest

PACKAGES = [
    "core.allocation",
    "core.ripple",
    "core.state",
    "core.influence",
    "services.handlers",
]


@pytest.mark.parametrize("pkg", PACKAGES)
def test_all_exports_resolve(pkg):
    mod = importlib.import_module(pkg)
    assert mod.__all__, pkg
    for name in mod.__all__:
        assert getattr(mod, name, None) is not None, f"{pkg}.{name}"


def test_allocation_stage_dead_name_gone():
    import core.allocation as a

    assert "AllocationStage" not in a.__all__
    assert isinstance(a.AllocationPolicy, type)
