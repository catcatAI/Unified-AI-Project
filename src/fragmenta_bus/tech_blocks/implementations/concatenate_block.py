from typing import Dict, Any, Optional
from ...common.tech_block_interface import TechBlock
from ...common.data_models import TechBlockInput, TechBlockOutput, TechBlockManifest

class StringConcatenateBlock(TechBlock):
    """
    A TechBlock that concatenates two input strings.
    """
    @classmethod
    def get_class_manifest(cls) -> TechBlockManifest:
        return TechBlockManifest(
            id="core.string.concatenate.v1",
            name="String Concatenation Block",
            version="1.0.0",
            description="Concatenates two input strings.",
            input_schema={
                "type": "object",
                "properties": {
                    "string1": {"type": "string", "description": "The first string.", "default": ""},
                    "string2": {"type": "string", "description": "The second string.", "default": ""}
                },
                "required": ["string1", "string2"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"type": "string", "description": "The concatenated string."}
                },
                "required": ["result"]
            },
            config_schema={
                "type": "object",
                "properties": {
                    "separator": {"type": "string", "description": "Optional separator string.", "default": ""}
                }
            },
            tags=["string", "utility"]
        )

    async def execute(self, input_data: TechBlockInput, context: Optional[Dict[str, Any]] = None) -> TechBlockOutput:
        string1 = input_data.get("data", {}).get("string1", "")
        string2 = input_data.get("data", {}).get("string2", "")
        separator = input_data.get("config", {}).get("separator", self._instance_config.get("separator", ""))
        
        concatenated_string = f"{string1}{separator}{string2}"
        return TechBlockOutput(result=concatenated_string, status="success", error_message=None)
