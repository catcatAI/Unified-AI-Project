import aiounittest
import pytest
from src.core_ai.dialogue.dialogue_manager import DialogueManager

class TestSelfImprovement(aiounittest.AsyncTestCase):
    """
    A class for testing the self-improvement capabilities of the system.
    """

    @pytest.mark.timeout(10)
    async def test_self_improvement(self):
        """
        Tests the self-improvement capabilities of the system.
        """
        dialogue_manager = DialogueManager()

        class DummyModel:
            def __init__(self):
                self.name = "DummyModel"

            def evaluate(self, input):
                return input

        model = DummyModel()
        dialogue_manager.tool_dispatcher.models = [model]
        dialogue_manager.tool_dispatcher.tools = []

        await dialogue_manager._assess_and_improve()

        self.assertNotEqual(dialogue_manager.tool_dispatcher.models[0], model)

if __name__ == "__main__":
    unittest.main()
