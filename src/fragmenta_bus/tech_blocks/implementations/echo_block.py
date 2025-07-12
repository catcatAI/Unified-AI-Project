from typing import Dict, Any, Optional
from ...common.tech_block_interface import TechBlock
from ...common.data_models import TechBlockInput, TechBlockOutput, TechBlockManifest

class EchoBlock(TechBlock):
    """
    A simple TechBlock that echoes its input data as its result.
    """
    @classmethod
    def get_class_manifest(cls) -> TechBlockManifest:
        return TechBlockManifest(
            id="core.echo.v1",
            name="Echo Block",
            version="1.0.0",
            description="Echoes the input data as the output result.",
            input_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Any data to be echoed."}
                },
                "required": ["data"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string", "description": "The echoed data."}
                },
                "required": ["result"]
            },
            config_schema={
                "type": "object",
                "properties": {
                    "prefix": {"type": "string", "description": "Optional prefix to add to the echoed data.", "default": ""}
                }
            },
            tags=["utility", "debug"]
        )

    async def execute(self, input_data: TechBlockInput, context: Optional[Dict[str, Any]] = None) -> TechBlockOutput:
        # EchoBlock expects its primary input in input_data['data']
        # The input_data['data'] itself might be a dictionary if mapped from a complex source.
        # For this simple EchoBlock, we assume the relevant string is directly in input_data['data']
        # or if it's a dict, we take a specific key from it.
        
        # For the test case, input_data['data'] will be {"text": "Hello Fragmenta"}
        # We need to extract the actual string to echo.
        
        data_to_echo = input_data.get("data")
        if isinstance(data_to_echo, dict) and "text" in data_to_echo:
            data_to_echo = data_to_echo["text"]
        elif not isinstance(data_to_echo, str):
            return TechBlockOutput(result=None, status="error", error_message="EchoBlock expects string or dict with 'text' in data.")

        prefix = input_data.get("config", {}).get("prefix", self._instance_config.get("prefix", ""))
        echoed_data = f"{prefix}{data_to_echo}"
        return TechBlockOutput(result=echoed_data, status="success", error_message=None)
