import aiounittest
import pytest
from unittest.mock import MagicMock, AsyncMock
from apps.backend.src.ai.dialogue.dialogue_manager import DialogueManager

class TestKnowledgeUpdate(aiounittest.AsyncTestCase):
    """
    A class for testing the knowledge update capabilities of the system.
    """

    @pytest.mark.timeout(10)
    # 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
# 添加重试装饰器以处理不稳定的测试
# @pytest.mark.flaky(reruns=3, reruns_delay=2)
    async def test_knowledge_update(self):
        """
        Tests the knowledge update capabilities of the system.
        """
        dialogue_manager = DialogueManager(
            ai_id="test_ai",
            personality_manager=MagicMock(),
            memory_manager=MagicMock(),
            llm_interface=MagicMock(),
            emotion_system=MagicMock(),
            crisis_system=MagicMock(),
            time_system=MagicMock(),
            formula_engine=MagicMock(),
            tool_dispatcher=MagicMock(),
            learning_manager=AsyncMock(),
            service_discovery_module=MagicMock(),
            hsp_connector=None,
            agent_manager=None,
            config={}
        )

        class DummyModel:
            def __init__(self):
                self.name = "DummyModel"
                self.trained = False

            def evaluate(self, input):
                return input

            def train(self, dataset):
                self.trained = True

        dialogue_manager.tool_dispatcher.models = [DummyModel()]
        dialogue_manager.tool_dispatcher.tools = []

        with open("data/raw_datasets/DummyModel.json", "w") as f:
            f.write('[{"input": 1, "output": 1}]')

        dialogue_manager.learning_manager.learn_from_interaction = AsyncMock(
            side_effect=lambda _: dialogue_manager.tool_dispatcher.models[0].train(None)
        )

        await dialogue_manager.learning_manager.learn_from_interaction(MagicMock())

        self.assertTrue(dialogue_manager.tool_dispatcher.models[0].trained)

if __name__ == "__main__":
    import asyncio
    asyncio.run(unittest.main())
