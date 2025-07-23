import aiounittest
import pytest
from src.core_ai.dialogue.dialogue_manager import DialogueManager

class TestKnowledgeUpdate(aiounittest.AsyncTestCase):
    """
    A class for testing the knowledge update capabilities of the system.
    """

    @pytest.mark.timeout(10)
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
            learning_manager=MagicMock(),
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

        await dialogue_manager._assess_and_improve()

        self.assertTrue(dialogue_manager.tool_dispatcher.models[0].trained)

        model = DummyModel()
        dialogue_manager.tool_dispatcher.models = [model]
        dialogue_manager.tool_dispatcher.tools = []

        dialogue_manager.tool_dispatcher.models = [model]
        dialogue_manager.tool_dispatcher.tools = []

        with open("data/raw_datasets/DummyModel.json", "w") as f:
            f.write('[{"input": 1, "output": 1}]')

        await dialogue_manager._assess_and_improve()

        self.assertTrue(model.trained)

if __name__ == "__main__":
    import asyncio
    asyncio.run(unittest.main())
