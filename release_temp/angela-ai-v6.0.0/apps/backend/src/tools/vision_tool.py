from typing import Any, Dict
from pydantic import BaseModel, Field
from apps.backend.src.tools.base_tool import BaseTool
from apps.backend.src.services.vision_service import vision_manager

class VisionToolSchema(BaseModel):
    image_source: str = Field(..., description="URL or path to the image.")
    processing_type: str = Field("object_detection", description="Type of processing: 'object_detection', 'ocr', 'captioning'.")
    parameters: Dict[str, Any] = Field({}, description="Additional parameters.")

class VisionTool(BaseTool):
    @property
    def name(self) -> str:
        return "vision_processing"

    @property
    def description(self) -> str:
        return "Processes images for computer vision tasks."

    @property
    def args_schema(self) -> type[BaseModel]:
        return VisionToolSchema

    async def execute(self, **kwargs: Any) -> Any:
        return await vision_manager.process_image(**kwargs)
