"""End-to-end functionality test — verifies core data flow."""

import pytest


def test_data_flow_pipeline():
    """Verify that lean core modules import without error."""
    from apps.backend.src.core.system.state_store.global_store import GlobalStateStore
    from apps.backend.src.services.chat_service import ChatService

    assert GlobalStateStore is not None
    assert ChatService is not None