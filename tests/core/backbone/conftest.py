# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""Shared fixtures for backbone tests.

Provides a fresh Backbone instance per test (isolated from the process-wide
singleton) via ``reset_backbone()`` + ``get_backbone()``.
"""

import pytest


@pytest.fixture(autouse=True)
def _fresh_backbone():
    from core.backbone import reset_backbone

    reset_backbone()
    yield
    reset_backbone()


@pytest.fixture
def backbone():
    from core.backbone import get_backbone

    return get_backbone()
