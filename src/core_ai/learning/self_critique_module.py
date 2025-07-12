import json
from typing import List, Dict, Optional, Any

# Assuming 'src' is in PYTHONPATH, making 'services' and 'shared' top-level packages
from services.llm_interface import LLMInterface, LLMInterfaceConfig
from shared.types.common_types import CritiqueResult


class SelfCritiqueModule:
    def __init__(self, llm_interface: LLMInterface, operational_config: Optional[Dict[str, Any]] = None):
        self.llm_interface = llm_interface
        self.operational_config = operational_config or {}
        self.default_critique_timeout = self.operational_config.get("timeouts", {}).get("llm_critique_request", 45)
        print(f"SelfCritiqueModule initialized. Default critique timeout: {self.default_critique_timeout}s")

    def _construct_critique_prompt(self, user_input: str, ai_response: str, context_history: List[Dict[str, str]]) -> str:
        prompt = "You are an AI assistant that evaluates the quality of a dialogue turn.\n"
        prompt += "Consider the user's input, the AI's response, and the preceding conversation history.\n"
        prompt += "Evaluate the AI's response based on: Relevance, Helpfulness, Coherence, Safety, and Tone (should be generally helpful and neutral unless context dictates otherwise).\n\n"

        if context_history:
            prompt += "Previous conversation turns (most recent last):\n"
            for turn in context_history:
                prompt += f"{turn['speaker'].capitalize()}: {turn['text']}\n"
            prompt += "\n"

        prompt += f"User Input: \"{user_input}\"\n"
        prompt += f"AI Response: \"{ai_response}\"\n\n"

        prompt += "Provide your evaluation in JSON format with the following structure:\n"
        prompt += "{\n"
        prompt += "  \"score\": <a float between 0.0 (very bad) and 1.0 (excellent) representing overall quality>,\n"
        prompt += "  \"reason\": \"<a brief explanation for the score, highlighting strengths or weaknesses>\",\n"
        prompt += "  \"suggested_alternative\": \"<if the response could be improved, a brief suggestion, otherwise null>\"\n"
        prompt += "}\n"
        prompt += "Focus on constructive feedback. If the response is good, state why.\n"
        return prompt

    def critique_interaction(self, user_input: str, ai_response: str, context_history: List[Dict[str, str]]) -> Optional[CritiqueResult]:
        """
        Uses an LLM to critique the AI's response in the context of the user's input and history.
        """
        if not self.llm_interface:
            print("SelfCritiqueModule: LLMInterface not available. Cannot perform critique.")
            return None

        prompt = self._construct_critique_prompt(user_input, ai_response, context_history)

        print(f"SelfCritiqueModule: Sending prompt to LLM for critique:\n---\n{prompt}\n---")

        llm_critique_str = self.llm_interface.generate_response(prompt, model_name="critique_model_placeholder") # Suggests a specific model might be better

        print(f"SelfCritiqueModule: Received raw critique from LLM:\n---\n{llm_critique_str}\n---")

        try:
            parsed_critique = json.loads(llm_critique_str)

            # Validate structure (basic check)
            if not all(k in parsed_critique for k in ["score", "reason"]):
                print(f"SelfCritiqueModule: Error - LLM critique missing required fields 'score' or 'reason'. Response: {llm_critique_str}")
                return None
            if not isinstance(parsed_critique["score"], (float, int)):
                 print(f"SelfCritiqueModule: Error - LLM critique 'score' is not a number. Response: {llm_critique_str}")
                 return None

            critique_result: CritiqueResult = {
                "score": float(parsed_critique["score"]),
                "reason": parsed_critique.get("reason"),
                "suggested_alternative": parsed_critique.get("suggested_alternative")
            }
            # Normalize score to be between 0 and 1 if it's outside for some reason
            critique_result["score"] = max(0.0, min(1.0, critique_result["score"]))

            print(f"SelfCritiqueModule: Parsed critique: {critique_result}")
            return critique_result

        except json.JSONDecodeError:
            print(f"SelfCritiqueModule: Error - Could not decode JSON response from LLM for critique: {llm_critique_str}")
            return None
        except Exception as e:
            print(f"SelfCritiqueModule: Error processing LLM critique response: {e}")
            return None

if __name__ == '__main__':
    print("--- SelfCritiqueModule Standalone Test ---")

    # We need a PatchedLLMInterface similar to the one in DailyLanguageModel's test
    # to simulate LLM responses for critique.
    class PatchedLLMInterfaceForCritique(LLMInterface):
        def _get_mock_response(self, prompt: str, model_name: Optional[str]) -> str:
            # This mock will respond to critique prompts
            if "Evaluate the AI's response based on" in prompt:
                if "User Input: \"Hello\"" in prompt and "AI Response: \"Hello there!\"" in prompt:
                    return json.dumps({
                        "score": 0.9,
                        "reason": "Good, relevant, and friendly greeting.",
                        "suggested_alternative": None
                    })
                elif "User Input: \"What is my favorite color?\"" in prompt and \
                     "AI Response: \"I'm sorry, I don't know your favorite color.\"" in prompt and \
                     "User: My favorite color is blue." in prompt: # Context provided
                    return json.dumps({
                        "score": 0.3,
                        "reason": "AI failed to recall previously stated information from context.",
                        "suggested_alternative": "You mentioned your favorite color is blue."
                    })
                elif "User Input: \"gibberishasdasd\"" in prompt:
                     return json.dumps({
                        "score": 0.5,
                        "reason": "AI responded appropriately to unclear input, but could offer to help in other ways.",
                        "suggested_alternative": "I'm not sure how to help with that. Can I assist with something else?"
                    })
                else: # Default critique
                    return json.dumps({
                        "score": 0.7,
                        "reason": "A generic but acceptable response.",
                        "suggested_alternative": "Could be more specific."
                    })
            # Fallback for non-critique prompts if any were sent through this patched version
            return super()._get_mock_response(prompt, model_name)

    # Setup a mock LLMInterface for testing
    mock_llm_config_for_critique: LLMInterfaceConfig = { #type: ignore
        "default_provider": "mock",
        "default_model": "critique-mock-v1",
        "providers": {},
        "default_generation_params": {}
    }
    patched_llm_interface = PatchedLLMInterfaceForCritique(config=mock_llm_config_for_critique)

    critique_module = SelfCritiqueModule(llm_interface=patched_llm_interface)

    # Test case 1: Simple good interaction
    print("\nTest Case 1: Good Interaction")
    history1: List[Dict[str, str]] = []
    user_in1 = "Hello"
    ai_res1 = "Hello there!"
    critique1 = critique_module.critique_interaction(user_in1, ai_res1, history1)
    print(f"Critique 1: {critique1}")
    assert critique1 and critique1["score"] == 0.9

    # Test case 2: AI fails to use context
    print("\nTest Case 2: AI fails context")
    history2: List[Dict[str, str]] = [
        {"speaker": "user", "text": "My favorite color is blue."},
        {"speaker": "ai", "text": "That's a lovely color!"}
    ]
    user_in2 = "What is my favorite color?"
    ai_res2 = "I'm sorry, I don't know your favorite color."
    critique2 = critique_module.critique_interaction(user_in2, ai_res2, history2)
    print(f"Critique 2: {critique2}")
    assert critique2 and critique2["score"] == 0.3
    assert critique2["suggested_alternative"] == "You mentioned your favorite color is blue."

    # Test case 3: AI handles gibberish
    print("\nTest Case 3: AI handles gibberish")
    history3: List[Dict[str, str]] = []
    user_in3 = "gibberishasdasd"
    ai_res3 = "I'm not sure I understand. Could you rephrase?"
    critique3 = critique_module.critique_interaction(user_in3, ai_res3, history3)
    print(f"Critique 3: {critique3}") # Will use the default critique from PatchedLLM
    # This assertion depends on the default mock response in PatchedLLMInterface
    assert critique3 and critique3["score"] == 0.7


    print("\nSelfCritiqueModule standalone test finished.")
