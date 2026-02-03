from typing import Any, Dict
from pydantic import BaseModel, Field
from apps.backend.src.tools.base_tool import BaseTool
from apps.backend.src.services.nlp_service import nlp_manager

class NLPToolSchema(BaseModel):
    text: str = Field(..., description="The text to process.")
    processing_type: str = Field("sentiment", description="Type of processing: 'sentiment', 'entity_extraction', 'summarization'.")
    parameters: Dict[str, Any] = Field({}, description="Additional parameters.")

class NLPTool(BaseTool):
    @property
    def name(self) -> str:
        return "nlp_processing"

    @property
    def description(self) -> str:
        return "Processes natural language text."

    @property
    def args_schema(self) -> type[BaseModel]:
        return NLPToolSchema

    async def execute(self, **kwargs: Any) -> Any:
        return await nlp_manager.process_text(**kwargs)
