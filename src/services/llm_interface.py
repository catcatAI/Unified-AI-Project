from typing import Dict, Any, Optional, List

import json
import requests # Added for Ollama integration
import re # For more robust mock matching
# from typing import Dict, Any, Optional, List # Redundant with line 1

# Attempt to import LLMInterfaceConfig, handle if module run directly or types not generated yet
# Assuming 'src' is in PYTHONPATH, making 'shared' a top-level package
from shared.types.common_types import (
    LLMInterfaceConfig, LLMProviderOllamaConfig,
    LLMProviderOpenAIConfig, OperationalConfig, LLMModelInfo # Added LLMModelInfo
)


class LLMInterface:
    def __init__(self, config: Optional[LLMInterfaceConfig] = None):
        self.config: LLMInterfaceConfig = config if config else self._get_default_config() # type: ignore
        self.active_provider_name: Optional[str] = None
        self.active_llm_client: Any = None # Could be a client object or a string like "mock"

        self._initialize_client()
        print(f"LLMInterface: Initialized. Active provider: {self.active_provider_name or 'None'}")

    def _get_default_config(self) -> LLMInterfaceConfig:
        # Provides a basic default config if none is passed, useful for standalone testing or simple use.
        print("LLMInterface: No configuration provided, using default mock configuration.")
        return { # type: ignore
            "default_provider": "mock",
            "default_model": "mock-generic-v1",
            "providers": {
                # Ollama config is here as an example, but won't be used by default mock
                "ollama": {"base_url": "http://localhost:11434"},
                "openai": {"api_key": "YOUR_OPENAI_KEY_HERE_IF_YOU_HAD_ONE"}
            },
            "default_generation_params": {"temperature": 0.7}
        }

    def _initialize_client(self):
        """Initializes a specific LLM client based on config."""
        self.active_provider_name = self.config.get("default_provider")
        provider_configs = self.config.get("providers", {})

        if self.active_provider_name == "mock":
            self.active_llm_client = "mock" # Special string to indicate mock client
            print("LLMInterface: Initialized MOCK client.")
        elif self.active_provider_name == "ollama":
            # Placeholder for Ollama client initialization
            # ollama_conf: Optional[LLMProviderOllamaConfig] = provider_configs.get('ollama') # type: ignore
            # if ollama_conf and ollama_conf.get('base_url'):
            #     print(f"LLMInterface: Ollama client would be initialized with base_url: {ollama_conf['base_url']}")
            #     # self.active_llm_client = OllamaClient(base_url=ollama_conf['base_url']) # Example
            # else:
            ollama_config: Optional[LLMProviderOllamaConfig] = provider_configs.get('ollama') # type: ignore
            if ollama_config and ollama_config.get('base_url'):
                self.active_llm_client = {"base_url": ollama_config["base_url"]} # Store base_url for requests
                print(f"LLMInterface: Initialized Ollama provider. Base URL: {ollama_config['base_url']}")
                # No persistent client object needed for requests-based approach for Ollama
            else:
                print("LLMInterface: Warning - Ollama provider configured but base_url is missing. Falling back to MOCK.")
                self.active_provider_name = "mock"
                self.active_llm_client = "mock"

        elif self.active_provider_name == "openai":
            # Placeholder for OpenAI client
            # openai_conf: Optional[LLMProviderOpenAIConfig] = provider_configs.get('openai') # type: ignore
            # if openai_conf and openai_conf.get('api_key'):
            #      print(f"LLMInterface: OpenAI client would be initialized.")
            #      # self.active_llm_client = OpenAIClient(api_key=openai_conf['api_key']) # Example
            # else:
            #      print("LLMInterface: Warning - OpenAI provider configured but api_key is missing.")
            print("LLMInterface: OpenAI client initialization is NOT YET IMPLEMENTED.")
            self.active_llm_client = "mock" # Fallback to mock
            self.active_provider_name = "mock"
            print("LLMInterface: Falling back to MOCK client as OpenAI is not implemented.")
        else:
            print(f"LLMInterface: Unknown or unsupported provider '{self.active_provider_name}'. Falling back to MOCK.")
            self.active_provider_name = "mock"
            self.active_llm_client = "mock"

    def _get_mock_response(self, prompt: str, model_name: Optional[str]) -> str:
        """Generates a predefined mock response."""
        # print(f"LLMInterface (Mock): ENTERING _get_mock_response. Prompt starts with: '{prompt[:150].replace('\n', '\\n')}' for model='{model_name}'")

        is_tool_prompt_check_available = "Available tools:" in prompt
        is_tool_prompt_check_query = "User Query:" in prompt
        # print(f"LLMInterface (Mock): Check 'Available tools:': {is_tool_prompt_check_available}") # DEBUG
        # print(f"LLMInterface (Mock): Check 'User Query:': {is_tool_prompt_check_query}") # DEBUG

        if is_tool_prompt_check_available and is_tool_prompt_check_query:
            # print(f"LLMInterface (Mock): Tool prompt condition MET.") # DEBUG
            query_match = re.search(r"User Query: \"(.*?)\"", prompt, re.S)
            actual_query_in_prompt = query_match.group(1).strip() if query_match else ""
            # print(f"LLMInterface (Mock): Extracted query for tool prompt: '{actual_query_in_prompt}'") # DEBUG

            if actual_query_in_prompt == "calculate 2 + 2":
                # print("LLMInterface Mock: Matched 'calculate 2 + 2'") # DEBUG
                return json.dumps({"tool_name": "calculate", "parameters": {"query": "2 + 2", "original_query": "calculate 2 + 2"}})
            elif actual_query_in_prompt == "evaluate true AND false":
                # print("LLMInterface Mock: Matched 'evaluate true AND false'") # DEBUG
                return json.dumps({"tool_name": "evaluate_logic", "parameters": {"query": "true AND false", "original_query": "evaluate true AND false"}})
            elif actual_query_in_prompt == "NOT (true OR false)":
                # print("LLMInterface Mock: Matched 'NOT (true OR false)'") # DEBUG
                return json.dumps({"tool_name": "evaluate_logic", "parameters": {"query": "NOT (true OR false)", "original_query": "NOT (true OR false)"}})
            elif actual_query_in_prompt == "translate '你好' to English":
                # print("LLMInterface Mock: Matched 'translate '你好' to English'") # DEBUG
                return json.dumps({"tool_name": "translate_text", "parameters": {"text_to_translate": "你好", "target_language": "English", "original_query": "translate '你好' to English"}})

            # print(f"LLMInterface Mock: Tool selection prompt for query '{actual_query_in_prompt}' was detected but NOT MATCHED by specific tool rules. Returning NO_TOOL.") # DEBUG
            return json.dumps({"tool_name": "NO_TOOL", "parameters": {}})
        else:
            # print(f"LLMInterface (Mock): Tool prompt condition NOT MET (is_tool_prompt_check_available={is_tool_prompt_check_available}, is_tool_prompt_check_query={is_tool_prompt_check_query}). Falling back to other mock responses or generic.") # DEBUG
            if "hello" in prompt.lower():
                return f"Mock model {model_name or 'default_mock'} says: Hello there! How can I help you today?"
            elif "capital of france" in prompt.lower():
                return f"Mock model {model_name or 'default_mock'} says: Paris, of course!"
            elif "weather" in prompt.lower():
                return f"Mock model {model_name or 'default_mock'} says: The weather is mockingly perfect!"

        # print(f"LLMInterface (Mock): No specific mock rule matched in _get_mock_response. Returning generic response for prompt: {prompt[:50]}...") # DEBUG
        return f"This is a generic mock response from {model_name or 'default_mock'} to the prompt: \"{prompt}\""

    def generate_response(self, prompt: str, model_name: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a response from the configured LLM.
        """
        effective_model_name = model_name or self.config.get("default_model", "default_model_unspecified")
        generation_params = {**self.config.get("default_generation_params", {}), **(params or {})}

        if self.active_llm_client == "mock" or (model_name and "mock" in model_name.lower()): # Allow specific mock model
            return self._get_mock_response(prompt, effective_model_name)

        if self.active_provider_name == "ollama":
            if isinstance(self.active_llm_client, dict) and "base_url" in self.active_llm_client:
                base_url = self.active_llm_client["base_url"]
                api_url = f"{base_url.rstrip('/')}/api/generate"
                payload = {
                    "model": effective_model_name,
                    "prompt": prompt,
                    "stream": False, # Keep it simple for now
                    "options": generation_params # Pass other params like temperature here
                }
                try:
                    print(f"LLMInterface (Ollama): Sending request to {api_url} with model {effective_model_name}")
                    response = requests.post(api_url, json=payload, timeout=self.config.get("operational_configs", {}).get("timeouts", {}).get("llm_ollama_request", 60)) # Add timeout
                    response.raise_for_status() # Raise an exception for HTTP errors
                    response_data = response.json()
                    return response_data.get("response", "Error: No 'response' field in Ollama output.")
                except requests.exceptions.Timeout:
                    print(f"LLMInterface (Ollama): Request timed out to {api_url}.")
                    return "Error: Ollama request timed out."
                except requests.exceptions.RequestException as e:
                    print(f"LLMInterface (Ollama): Request failed: {e}")
                    return f"Error: Ollama request failed - {e}"
                except json.JSONDecodeError:
                    print(f"LLMInterface (Ollama): Failed to decode JSON response from {api_url}.")
                    return "Error: Ollama returned non-JSON response."
            else:
                print("LLMInterface (Ollama): Ollama client not properly configured (missing base_url).")
                return "Error: Ollama client misconfigured."

        elif self.active_provider_name == "openai":
            # Actual OpenAI call
            print(f"LLMInterface (OpenAI - NOT IMPLEMENTED): Would generate response for prompt='{prompt[:50]}...' using model='{effective_model_name}' with params={generation_params}.")
            return f"Placeholder OPENAI response from {effective_model_name} (not really): {prompt}"

        # Fallback if no client is properly configured or active_llm_client is None/unsupported string
        print(f"LLMInterface: No active LLM client for provider '{self.active_provider_name}'. Returning generic placeholder.")
        return f"Generic placeholder response (no active client) for model {effective_model_name} to: {prompt}"

    def list_available_models(self) -> List[LLMModelInfo]:
        """
        Lists available models from the configured provider.
        Returns a list of LLMModelInfo objects.
        """
        if self.active_llm_client == "mock" or self.active_provider_name == "mock":
            print("LLMInterface (Mock): Listing available mock models.")
            return [
                LLMModelInfo(id="mock-generic-v1", provider="mock"),
                LLMModelInfo(id="mock-creative-v1", provider="mock"),
                LLMModelInfo(id="mock-code-v1", provider="mock"),
            ]
        elif self.active_provider_name == "ollama":
            if isinstance(self.active_llm_client, dict) and "base_url" in self.active_llm_client:
                base_url = self.active_llm_client["base_url"]
                api_url = f"{base_url.rstrip('/')}/api/tags"
                try:
                    print(f"LLMInterface (Ollama): Fetching available models from {api_url}")
                    # Safely access operational_configs and timeouts
                    op_configs = self.config.get("operational_configs", {})
                    timeouts = op_configs.get("timeouts", {}) if isinstance(op_configs, dict) else {}
                    timeout_duration = timeouts.get("llm_ollama_list_models_request", 10)

                    response = requests.get(api_url, timeout=timeout_duration)
                    response.raise_for_status()
                    models_data = response.json()

                    ollama_models: List[LLMModelInfo] = []
                    if "models" in models_data and isinstance(models_data["models"], list):
                        for model_info in models_data["models"]:
                            if isinstance(model_info, dict) and model_info.get("name"):
                                ollama_models.append(LLMModelInfo(
                                    id=model_info["name"], # Ollama's 'name' is the ID
                                    provider="ollama",
                                    name=model_info.get("name"), # Can include name separately too
                                    modified_at=model_info.get("modified_at"),
                                    size_bytes=model_info.get("size") # Ollama uses 'size' for bytes
                                ))
                        return ollama_models
                    else:
                        print("LLMInterface (Ollama): Unexpected format for /api/tags response.")
                        return [LLMModelInfo(id="ollama-error-parsing-models", provider="ollama")]
                except requests.exceptions.Timeout:
                    print(f"LLMInterface (Ollama): Request timed out fetching models from {api_url}.")
                    return [LLMModelInfo(id="ollama-timeout-listing-models", provider="ollama")]
                except requests.exceptions.RequestException as e:
                    print(f"LLMInterface (Ollama): Failed to fetch models: {e}")
                    return [LLMModelInfo(id="ollama-error-listing-models", provider="ollama")]
                except json.JSONDecodeError:
                    print(f"LLMInterface (Ollama): Failed to decode JSON when fetching models from {api_url}.")
                    return [LLMModelInfo(id="ollama-json-decode-error-listing-models", provider="ollama")]
            else:
                print("LLMInterface (Ollama): Ollama client not properly configured for listing models.")
                return [LLMModelInfo(id="ollama-misconfigured-listing-models", provider="ollama")]

        print(f"LLMInterface: list_available_models not implemented for provider '{self.active_provider_name}'.")
        return [LLMModelInfo(id="unknown-model", provider=str(self.active_provider_name))]

if __name__ == '__main__':
    print("--- LLMInterface Test ---")

    # Test with default (mock) configuration
    print("\n1. Testing with default mock configuration:")
    interface_default_mock = LLMInterface() # Uses _get_default_config()
    models_mock = interface_default_mock.list_available_models()
    print(f"  Available mock models: {models_mock}")
    prompt1 = "Hello, how are you?"
    response1 = interface_default_mock.generate_response(prompt1)
    print(f"  Prompt: {prompt1}\n  Response: {response1}")
    prompt2 = "What is the capital of France?"
    response2 = interface_default_mock.generate_response(prompt2, model_name="mock-creative-v1")
    print(f"  Prompt: {prompt2} (model: mock-creative-v1)\n  Response: {response2}")

    # Test with explicit mock configuration passed
    print("\n2. Testing with explicit mock configuration:")
    explicit_mock_config: LLMInterfaceConfig = { # type: ignore
        "default_provider": "mock",
        "default_model": "my-custom-mock",
        "providers": {}, # No other providers needed for this test
        "default_generation_params": {"temperature": 0.1}
    }
    interface_explicit_mock = LLMInterface(config=explicit_mock_config)
    prompt3 = "Tell me about weather."
    response3 = interface_explicit_mock.generate_response(prompt3)
    print(f"  Prompt: {prompt3}\n  Response: {response3}")

    # Test with a placeholder for a non-mock provider (e.g., Ollama)
    # This will currently fall back to mock because Ollama client is not implemented.
    print("\n3. Testing with Ollama configuration (expecting actual Ollama interaction or errors if server not running):")
    ollama_test_config: LLMInterfaceConfig = { # type: ignore
        "default_provider": "ollama",
        "default_model": "nous-hermes2:latest", # Replace with a model you have downloaded in Ollama
        "providers": {
            "ollama": {"base_url": "http://localhost:11434"}
        },
        "operational_configs": { # Add operational_configs for timeouts for testing
            "timeouts": {
                "llm_ollama_request": 60,
                "llm_ollama_list_models_request": 10
            }
        }
    }
    interface_ollama = LLMInterface(config=ollama_test_config) # Changed variable name

    print("  Listing models from Ollama:")
    ollama_models = interface_ollama.list_available_models()
    print(f"  Available Ollama models: {ollama_models}")
    # Basic check:
    if any(m["id"] == ollama_test_config["default_model"] for m in ollama_models):
        print(f"  Default model {ollama_test_config['default_model']} found in Ollama list.")
    elif ollama_models and not any("error" in m["id"] or "timeout" in m["id"] for m in ollama_models):
        print(f"  WARNING: Default model {ollama_test_config['default_model']} not found in Ollama list: {ollama_models}. Ensure the model is pulled and accessible.")


    prompt4 = "Explain the concept of recursion in programming in one sentence."
    print(f"  Prompt to Ollama: {prompt4}")
    response4 = interface_ollama.generate_response(prompt4)
    print(f"  Response from Ollama: {response4}")

    print("\n  Test with a different model (if you have one, e.g., orca-mini):")
    # You can change 'orca-mini:latest' to another model you have locally
    # If you don't have a second model, this will likely just use the default or fail if the model doesn't exist.
    # Ensure the model name is correct as per your local Ollama setup.
    custom_model_name = "orca-mini:latest" # Example, change if needed
    if any(m["id"] == custom_model_name for m in ollama_models):
        prompt5 = "What are the key benefits of using Python?"
        print(f"  Prompt to Ollama ({custom_model_name}): {prompt5}")
        response5 = interface_ollama.generate_response(prompt5, model_name=custom_model_name)
        print(f"  Response from Ollama ({custom_model_name}): {response5}")
    else:
        print(f"  Skipping test for model '{custom_model_name}' as it's not found in the listed Ollama models or an error occurred during listing.")


    print("\nLLM Interface script with Ollama tests finished (or attempted).")
