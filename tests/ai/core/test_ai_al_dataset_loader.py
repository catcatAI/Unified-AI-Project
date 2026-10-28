# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""
Unit tests for the AI + AL Dataset Loader.
Ensures development tools and training pipelines can correctly query,
filter, and batch AI+AL joint training records.
"""

import pytest
from ai.core.ai_al_dataset_loader import (
    AiAlDatasetLoader,
    AiAlRecord,
    get_ai_al_loader,
)


def test_dataset_loader_initialization():
    """Verify loader successfully initializes and loads records."""
    loader = AiAlDatasetLoader()
    records = loader.get_all()
    assert len(records) >= 10
    assert isinstance(records[0], AiAlRecord)


def test_dataset_loader_batching():
    """Verify batch retrieval returns requested number of records."""
    loader = AiAlDatasetLoader()
    batch = loader.get_batch(3)
    assert len(batch) == 3


def test_dataset_loader_filtering():
    """Verify filtering by routing mode works correctly."""
    loader = AiAlDatasetLoader()
    exploratory_records = loader.filter_by_routing_mode("exploratory")
    conservative_records = loader.filter_by_routing_mode("conservative")

    assert len(exploratory_records) > 0
    assert len(conservative_records) > 0

    for r in exploratory_records:
        assert r.al_state_in.routing_mode == "exploratory"


def test_singleton_loader():
    """Verify singleton getter works properly."""
    loader1 = get_ai_al_loader()
    loader2 = get_ai_al_loader()
    assert loader1 is loader2
    assert len(loader1.get_all()) == len(loader2.get_all())
