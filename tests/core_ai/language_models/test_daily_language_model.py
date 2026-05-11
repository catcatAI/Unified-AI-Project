"""Tests for daily language model."""

import pytest
from unittest.mock import AsyncMock


class TestDailyLanguageModel:
    @pytest.fixture(autouse=True)
    def setup_dlm(self):
        mock_llm_service = AsyncMock()
        self.mock_llm_service = mock_llm_service