"""
测试模块 - test_learning_and_trust
"""

import pytest
import uuid
from unittest.mock import MagicMock


class TestLearningAndTrustIntegration:

    @pytest.fixture(autouse=True)
    def learning_manager_setup(self):
        self.ai_id = "test_host_ai"
        self.trust_manager = MagicMock()

        self.ham_memory = MagicMock()
        self.ham_memory.query_core_memory.return_value = []
        self.ham_memory.increment_metadata_field.return_value = True
        self.ham_memory.store_experience.return_value = f"ham_{uuid.uuid4().hex}"

        mock_content_analyzer = MagicMock()
        mock_content_analyzer.process_hsp_fact_content.return_value = {}

        self.learning_manager = MagicMock()
    async def test_duplicate_fact_increments_corroboration(self):
        existing_ham_id = "ham_existing_fact_001"
        fact_id = "hsp_fact_duplicate_test"
        originator_id = "did:hsp:originator_1"

        existing_record = {
            "id": existing_ham_id,
            "metadata": {
                "hsp_fact_id": fact_id,
                "hsp_originator_ai_id": originator_id,
                "corroboration_count": 1
            }
        }
        self.ham_memory.query_core_memory.return_value = [existing_record]

        result = await self.learning_manager.process_and_store_hsp_fact(
            MagicMock(), "did:hsp:sender_2", MagicMock()
        )

        assert result is None
        self.ham_memory.query_core_memory.assert_called_once()
        self.ham_memory.store_experience.assert_not_called()
        self.ham_memory.increment_metadata_field.assert_called_once_with(
            existing_ham_id, "corroboration_count"
        )
    async def test_fact_from_low_trust_source_is_discarded(self):
        low_trust_sender_id = "did:hsp:untrusted_sender"
        self.trust_manager.update_trust_score = MagicMock()

        result = await self.learning_manager.process_and_store_hsp_fact(
            MagicMock(), low_trust_sender_id, MagicMock()
        )

        assert result is None
        self.ham_memory.store_experience.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])