from typing import Any, Dict
from pydantic import BaseModel, Field
from apps.backend.src.tools.base_tool import BaseTool
from apps.backend.src.services.audio_service import audio_manager

class AudioToolSchema(BaseModel):
    audio_source: str = Field(..., description="URL or path to the audio file.")
    processing_type: str = Field("speech_to_text", description="Type of processing: 'speech_to_text', 'text_to_speech'.")
    parameters: Dict[str, Any] = Field({}, description="Additional parameters.")

class AudioTool(BaseTool):
    @property
    def name(self) -> str:
        return "audio_processing"

    @property
    def description(self) -> str:
        return "Processes audio files."

    @property
    def args_schema(self) -> type[BaseModel]:
        return AudioToolSchema

    async def execute(self, **kwargs: Any) -> Any:
        return await audio_manager.process_audio(**kwargs)
