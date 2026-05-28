"""Smoke test for apps.backend.src.hsp_fixture_fix."""

import pytest


def test_hsp_fixture_fix_imports():
    """Smoke test: apps.backend.src.hsp_fixture_fix imports successfully."""
    import hsp_fixture_fix
    assert hsp_fixture_fix is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
