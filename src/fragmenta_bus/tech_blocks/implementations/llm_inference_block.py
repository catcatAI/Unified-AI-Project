from typing import Dict, Any, Optional
from ...common.tech_block_interface import TechBlock
from ...common.data_models import TechBlockInput, TechBlockOutput, TechBlockManifest
from src.services.llm_interface import LLMInterface, LLMInterfaceConfig

class LLMInferenceBlock(TechBlock):
    """
    A TechBlock that performs LLM inference using the LLMInterface.
    """
    def __init__(self, block_id: str, version: str, config: Optional[Dict[str, Any]] = None, llm_interface: Optional[LLMInterface] = None):
        super().__init__(block_id, version, config)
        self.llm_interface = llm_interface # Injected LLMInterface instance
        if not self.llm_interface:
            # Fallback to a default LLMInterface if not provided (e.g., for standalone testing)
            self.llm_interface = LLMInterface() # Uses default mock config if no config is passed

    @classmethod
    def get_class_manifest(cls) -> TechBlockManifest:
        return TechBlockManifest(
            id="llm.inference.v1",
            name="LLM Inference Block",
            version="1.0.0",
            description="Performs inference using a configured LLMInterface.",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "The prompt for the LLM.", "min_length": 1}
                },
                "required": ["prompt"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string", "description": "The LLM's response.", "min_length": 0}
                },
                "required": ["result"]
            },
            config_schema={
                "type": "object",
                "properties": {
                    "model_name": {"type": "string", "description": "Optional model name override.", "default": None},
                    "params": {"type": "object", "description": "Optional LLM generation parameters.", "default": {}}
                }
            },
            tags=["llm", "inference"]
        )

    async def execute(self, input_data: TechBlockInput, context: Optional[Dict[str, Any]] = None) -> TechBlockOutput:
        prompt = input_data.get("data", {}).get("prompt")
        if not prompt:
            return TechBlockOutput(result=None, status="error", error_message="Prompt is required for LLMInferenceBlock.")

        model_name = input_data.get("config", {}).get("model_name", self._instance_config.get("model_name"))
        params = input_data.get("config", {}).get("params", self._instance_config.get("params", {}))

        try:
            response = self.llm_interface.generate_response(prompt=prompt, model_name=model_name, params=params)
            return TechBlockOutput(result=response, status="success", error_message=None)
        except Exception as e:
            return TechBlockOutput(result=None, status="error", error_message=f"LLM inference failed: {e}")
