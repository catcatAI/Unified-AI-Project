import unittest
from unittest.mock import MagicMock
import json
from typing import List, Dict, Optional, Any

# Adjust import path based on project structure
# Assuming 'src' is a top-level package recognized in PYTHONPATH for tests
from src.core_ai.learning.self_critique_module import SelfCritiqueModule
from src.services.llm_interface import LLMInterface # For type hinting mock
from src.shared.types.common_types import CritiqueResult

class TestSelfCritiqueModule(unittest.TestCase):

    def setUp(self):
        """Set up for each test method."""
        self.mock_llm_interface = MagicMock(spec=LLMInterface)
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        # Sample operational_config, can be customized per test if needed
        self.sample_operational_config = {
            "timeouts": {
                "llm_critique_request": 30
            }
        }

=======
=======
>>>>>>> Stashed changes
        
        # Sample operational_config, can be customized per test if needed
        self.sample_operational_config = {
            "timeouts": {
                "llm_critique_request": 30 
            }
        }
        
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        self.critique_module = SelfCritiqueModule(
            llm_interface=self.mock_llm_interface,
            operational_config=self.sample_operational_config
        )

    def test_initialization(self):
        """Test that the SelfCritiqueModule initializes correctly."""
        self.assertIsNotNone(self.critique_module)
        self.assertEqual(self.critique_module.llm_interface, self.mock_llm_interface)
        self.assertEqual(self.critique_module.operational_config, self.sample_operational_config)
        self.assertEqual(self.critique_module.default_critique_timeout, 30)

    def test_critique_interaction_success(self):
        """Test successful critique generation and parsing."""
        user_input = "Tell me a joke."
        ai_response = "Why did the chicken cross the road? To get to the other side!"
        history = []
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
        
>>>>>>> Stashed changes
=======
        
>>>>>>> Stashed changes
        mock_llm_output = {
            "score": 0.8,
            "reason": "Classic joke, delivered clearly.",
            "suggested_alternative": "Perhaps a more original joke could be even better."
        }
        self.mock_llm_interface.generate_response.return_value = json.dumps(mock_llm_output)
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        result = self.critique_module.critique_interaction(user_input, ai_response, history)

=======
        
        result = self.critique_module.critique_interaction(user_input, ai_response, history)
        
>>>>>>> Stashed changes
=======
        
        result = self.critique_module.critique_interaction(user_input, ai_response, history)
        
>>>>>>> Stashed changes
        self.assertIsNotNone(result)
        self.assertEqual(result["score"], 0.8)
        self.assertEqual(result["reason"], mock_llm_output["reason"])
        self.assertEqual(result["suggested_alternative"], mock_llm_output["suggested_alternative"])
        self.mock_llm_interface.generate_response.assert_called_once()
        # We can also assert the prompt construction if needed, by checking call_args

    def test_critique_interaction_missing_optional_suggestion(self):
        """Test critique when LLM provides no suggested_alternative."""
        user_input = "Thanks!"
        ai_response = "You're welcome!"
        history = []
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
        
>>>>>>> Stashed changes
=======
        
>>>>>>> Stashed changes
        mock_llm_output = {
            "score": 0.95,
            "reason": "Polite and appropriate response."
            # "suggested_alternative" is intentionally missing
        }
        self.mock_llm_interface.generate_response.return_value = json.dumps(mock_llm_output)
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        result = self.critique_module.critique_interaction(user_input, ai_response, history)

=======
        
        result = self.critique_module.critique_interaction(user_input, ai_response, history)
        
>>>>>>> Stashed changes
=======
        
        result = self.critique_module.critique_interaction(user_input, ai_response, history)
        
>>>>>>> Stashed changes
        self.assertIsNotNone(result)
        self.assertEqual(result["score"], 0.95)
        self.assertEqual(result["reason"], mock_llm_output["reason"])
        self.assertIsNone(result["suggested_alternative"])

    def test_critique_interaction_llm_returns_non_json(self):
        """Test handling when LLM returns a non-JSON string."""
        user_input = "Query"
        ai_response = "Response"
        history = []
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        self.mock_llm_interface.generate_response.return_value = "This is not JSON."

        with self.assertLogs(logger='src.core_ai.learning.self_critique_module', level='ERROR') as cm:
            result = self.critique_module.critique_interaction(user_input, ai_response, history)

=======
=======
>>>>>>> Stashed changes
        
        self.mock_llm_interface.generate_response.return_value = "This is not JSON."
        
        with self.assertLogs(logger='src.core_ai.learning.self_critique_module', level='ERROR') as cm:
            result = self.critique_module.critique_interaction(user_input, ai_response, history)
        
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        self.assertIsNone(result)
        self.assertTrue(any("Could not decode JSON response" in message for message in cm.output))

    def test_critique_interaction_llm_returns_malformed_json(self):
        """Test handling of malformed JSON from LLM."""
        user_input = "Query"
        ai_response = "Response"
        history = []
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        self.mock_llm_interface.generate_response.return_value = "{\"score\": 0.7, \"reason\": \"Good but" # Missing closing brace

        with self.assertLogs(logger='src.core_ai.learning.self_critique_module', level='ERROR') as cm:
            result = self.critique_module.critique_interaction(user_input, ai_response, history)

=======
=======
>>>>>>> Stashed changes
        
        self.mock_llm_interface.generate_response.return_value = "{\"score\": 0.7, \"reason\": \"Good but" # Missing closing brace
        
        with self.assertLogs(logger='src.core_ai.learning.self_critique_module', level='ERROR') as cm:
            result = self.critique_module.critique_interaction(user_input, ai_response, history)
            
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        self.assertIsNone(result)
        self.assertTrue(any("Could not decode JSON response" in message for message in cm.output))

    def test_critique_interaction_llm_json_missing_score(self):
        """Test handling when 'score' key is missing in LLM's JSON response."""
        user_input = "Query"
        ai_response = "Response"
        history = []
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        mock_llm_output = {"reason": "A response without a score."}
        self.mock_llm_interface.generate_response.return_value = json.dumps(mock_llm_output)

        with self.assertLogs(logger='src.core_ai.learning.self_critique_module', level='ERROR') as cm:
            result = self.critique_module.critique_interaction(user_input, ai_response, history)

=======
=======
>>>>>>> Stashed changes
        
        mock_llm_output = {"reason": "A response without a score."}
        self.mock_llm_interface.generate_response.return_value = json.dumps(mock_llm_output)
        
        with self.assertLogs(logger='src.core_ai.learning.self_critique_module', level='ERROR') as cm:
            result = self.critique_module.critique_interaction(user_input, ai_response, history)
            
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        self.assertIsNone(result)
        self.assertTrue(any("LLM critique missing required fields 'score' or 'reason'" in message for message in cm.output))

    def test_critique_interaction_llm_json_score_not_number(self):
        """Test handling when 'score' is not a number."""
        user_input = "Query"
        ai_response = "Response"
        history = []
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        mock_llm_output = {"score": "high", "reason": "Score is a string."}
        self.mock_llm_interface.generate_response.return_value = json.dumps(mock_llm_output)

        with self.assertLogs(logger='src.core_ai.learning.self_critique_module', level='ERROR') as cm:
            result = self.critique_module.critique_interaction(user_input, ai_response, history)

=======
=======
>>>>>>> Stashed changes
        
        mock_llm_output = {"score": "high", "reason": "Score is a string."}
        self.mock_llm_interface.generate_response.return_value = json.dumps(mock_llm_output)
        
        with self.assertLogs(logger='src.core_ai.learning.self_critique_module', level='ERROR') as cm:
            result = self.critique_module.critique_interaction(user_input, ai_response, history)
            
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        self.assertIsNone(result)
        self.assertTrue(any("LLM critique 'score' is not a number" in message for message in cm.output))

    def test_critique_interaction_score_normalization(self):
        """Test that scores are normalized to be between 0.0 and 1.0."""
        user_input = "Query"
        ai_response = "Response"
        history = []

        # Test score > 1.0
        mock_llm_high_score = {"score": 1.5, "reason": "Too high."}
        self.mock_llm_interface.generate_response.return_value = json.dumps(mock_llm_high_score)
        result_high = self.critique_module.critique_interaction(user_input, ai_response, history)
        self.assertIsNotNone(result_high)
        self.assertEqual(result_high["score"], 1.0)

        # Test score < 0.0
        mock_llm_low_score = {"score": -0.5, "reason": "Too low."}
        self.mock_llm_interface.generate_response.return_value = json.dumps(mock_llm_low_score)
        result_low = self.critique_module.critique_interaction(user_input, ai_response, history)
        self.assertIsNotNone(result_low)
        self.assertEqual(result_low["score"], 0.0)

    def test_construct_critique_prompt_format(self):
        """Test the structure and content of the generated critique prompt."""
        user_input = "User says this."
        ai_response = "AI replies with that."
        history = [
            {"speaker": "user", "text": "Previous user turn."},
            {"speaker": "ai", "text": "Previous AI turn."}
        ]
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        prompt = self.critique_module._construct_critique_prompt(user_input, ai_response, history)

=======
        
        prompt = self.critique_module._construct_critique_prompt(user_input, ai_response, history)
        
>>>>>>> Stashed changes
=======
        
        prompt = self.critique_module._construct_critique_prompt(user_input, ai_response, history)
        
>>>>>>> Stashed changes
        self.assertIn("You are an AI assistant that evaluates the quality of a dialogue turn.", prompt)
        self.assertIn("Evaluate the AI's response based on: Relevance, Helpfulness, Coherence, Safety, and Tone", prompt)
        self.assertIn("Previous conversation turns (most recent last):", prompt)
        self.assertIn("User: Previous user turn.", prompt)
        self.assertIn("Ai: Previous AI turn.", prompt) # Note: Module capitalizes speaker
        self.assertIn(f"User Input: \"{user_input}\"", prompt)
        self.assertIn(f"AI Response: \"{ai_response}\"", prompt)
        self.assertIn("\"score\": <a float between 0.0 (very bad) and 1.0 (excellent) representing overall quality>,", prompt)
        self.assertIn("\"reason\": \"<a brief explanation for the score, highlighting strengths or weaknesses>\",", prompt)
        self.assertIn("\"suggested_alternative\": \"<if the response could be improved, a brief suggestion, otherwise null>\"", prompt)

    def test_critique_interaction_no_llm_interface(self):
        """Test behavior when LLMInterface is None."""
        self.critique_module.llm_interface = None # type: ignore
        user_input = "Query"
        ai_response = "Response"
        history = []
        with self.assertLogs(logger='src.core_ai.learning.self_critique_module', level='INFO') as cm: # Prints info
            result = self.critique_module.critique_interaction(user_input, ai_response, history)
        self.assertIsNone(result)
        self.assertTrue(any("LLMInterface not available" in message for message in cm.output))


if __name__ == '__main__':
    unittest.main()
