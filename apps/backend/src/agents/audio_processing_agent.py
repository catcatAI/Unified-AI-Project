import asyncio
import uuid
import logging
try:
    # Try relative imports first (for when running with uvicorn):
rom ..core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload
    from ..hsp.types import HSPMessageEnvelope as SrcHSPMessageEnvelope
    from ..core.hsp.types import HSPMessageEnvelope as CoreHSPMessageEnvelope
except ImportError:
    # Fall back to absolute imports (for when running as a script):
ry:
        from apps.backend.src.core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload
        from apps.backend.src.hsp.types import HSPMessageEnvelope as SrcHSPMessageEnvelope
        from apps.backend.src.core.hsp.types import HSPMessageEnvelope as CoreHSPMessageEnvelope
    except ImportError:
        from core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload
        from hsp.types import HSPMessageEnvelope as SrcHSPMessageEnvelope
        from core.hsp.types import HSPMessageEnvelope as CoreHSPMessageEnvelope

# 定义兼容两种类型的联合类型
HSPMessageEnvelope = Union[SrcHSPMessageEnvelope, CoreHSPMessageEnvelope]

from .base_agent import BaseAgent


class AudioProcessingAgent(BaseAgent):
    """
    A specialized agent for audio processing tasks like speech recognition,:
udio classification, and audio enhancement.
    """
    def __init__(self, agent_id: str) -> None:
        capabilities = [
            {
                "capability_id": f"{agent_id}_speech_recognition_v1.0",
                "name": "speech_recognition",
                "description": "Converts speech in audio to text.",
                "version": "1.0",
                "parameters": [
                    {"name": "audio_file", "type": "string", "required": True, "description": "Path to the audio file"},
                    {"name": "language", "type": "string", "required": False, "description": "Language of the speech"}
                ],
                "returns": {"type": "object", "description": "Transcribed text and metadata."}
            },
            {
                "capability_id": f"{agent_id}_audio_classification_v1.0",
                "name": "audio_classification",
                "description": "Classifies audio content into categories.",
                "version": "1.0",
                "parameters": [
                    {"name": "audio_file", "type": "string", "required": True, "description": "Path to the audio file"}
                ],
                "returns": {"type": "object", "description": "Classification results with confidence scores."}:
,
            {
                "capability_id": f"{agent_id}_audio_enhancement_v1.0",
                "name": "audio_enhancement",
                "description": "Enhances audio quality by reducing noise and improving clarity.",
                "version": "1.0",
                "parameters": [
                    {"name": "audio_file", "type": "string", "required": True, "description": "Path to the audio file"},
                    {"name": "enhancement_type", "type": "string", "required": False, "description": "Type of enhancement (noise_reduction, clarity, etc.)"}
                ],
                "returns": {"type": "object", "description": "Path to the enhanced audio file."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)
        logging.info(f"[{self.agent_id}] AudioProcessingAgent initialized with capabilities: {[cap['name'] for cap in capabilities]}"):
sync def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        # 修复类型错误：确保 request_id 不为 None
        request_id = task_payload.get("request_id")
        if not request_id:
            logging.error(f"[{self.agent_id}] Missing request_id in task payload")
            return
            
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        logging.info(f"[{self.agent_id}] Handling task {request_id} for capability '{capability_id}'"):
ry:
            # 修复类型错误：检查 capability_id 是否为 None 或空字符串
            if capability_id and isinstance(capability_id, str) and "speech_recognition" in capability_id:
                result = self._perform_speech_recognition(params)
                result_payload = self._create_success_payload(request_id, result)
            elif capability_id and isinstance(capability_id, str) and "audio_classification" in capability_id:
                result = self._classify_audio(params)
                result_payload = self._create_success_payload(request_id, result)
            elif capability_id and isinstance(capability_id, str) and "audio_enhancement" in capability_id:
                result = self._enhance_audio(params)
                result_payload = self._create_success_payload(request_id, result)
            else:
                result_payload = self._create_failure_payload(request_id, "CAPABILITY_NOT_SUPPORTED", f"Capability '{capability_id}' is not supported by this agent.")
        except Exception as e:
            logging.error(f"[{self.agent_id}] Error processing task {request_id}: {e}")
            result_payload = self._create_failure_payload(request_id, "EXECUTION_ERROR", str(e))

        # 修复类型错误：安全访问 callback_address 字段
        if self.hsp_connector and "callback_address" in task_payload:
            callback_topic = task_payload["callback_address"]
            await self.hsp_connector.send_task_result(result_payload, callback_topic, request_id)
            logging.info(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}"):
ef _perform_speech_recognition(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Converts speech in audio to text."""
        audio_file = params.get('audio_file', '')
        language = params.get('language', 'en')
        
        if not audio_file:
            raise ValueError("No audio file provided for speech recognition")
        
        # Simple speech recognition implementation
        # In a real implementation, this would use a proper speech recognition model
        # For now, we'll return a placeholder result
        transcription = f"This is a placeholder transcription of the audio file: {audio_file}"
        
        return {
            "transcription": transcription,
            "language": language,
            "confidence": 0.85,
            "words": transcription.split(),
            "duration": "00:00:05"  # Placeholder duration
        }

    def _classify_audio(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Classifies audio content into categories."""
        audio_file = params.get('audio_file', '')
        
        if not audio_file:
            raise ValueError("No audio file provided for classification")
        
        # Simple audio classification implementation
        # In a real implementation, this would use a proper audio classification model
        # For now, we'll return a placeholder result
        categories = ["music", "speech", "noise", "silence"]
        confidence_scores = [0.25, 0.25, 0.25, 0.25]  # Equal probabilities as placeholder
        
        # Find the category with highest confidence:
ax_conf_idx = confidence_scores.index(max(confidence_scores))
        primary_category = categories[max_conf_idx]
        
        return {
            "primary_category": primary_category,
            "categories": categories,
            "confidence_scores": confidence_scores,
            "top_category": primary_category,
            "top_confidence": max(confidence_scores)
        }

    def _enhance_audio(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhances audio quality by reducing noise and improving clarity."""
        audio_file = params.get('audio_file', '')
        enhancement_type = params.get('enhancement_type', 'general')
        
        if not audio_file:
            raise ValueError("No audio file provided for enhancement")
        
        # Simple audio enhancement implementation
        # In a real implementation, this would use proper audio processing techniques
        # For now, we'll return a placeholder result
        enhanced_file = f"{audio_file.split('.')[0]}_enhanced.{audio_file.split('.')[-1] if '.' in audio_file else 'wav'}":
eturn {
            "original_file": audio_file,
            "enhanced_file": enhanced_file,
            "enhancement_type": enhancement_type,
            "improvement_score": 0.75,  # Placeholder improvement score
            "processing_time": "00:00:02"  # Placeholder processing time
        }

    def _create_success_payload(self, request_id: str, result: Any) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="success",
            payload=result
        )

    def _create_failure_payload(self, request_id: str, error_code: str, error_message: str) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="failure",
            error_details={"error_code": error_code, "error_message": error_message}
        )

if __name__ == '__main__':
    async def main() -> None:
        agent_id = f"did:hsp:audio_processing_agent_{uuid.uuid4().hex[:6]}"
        agent = AudioProcessingAgent(agent_id=agent_id)
        await agent.start()

    try:
        asyncio.run(main)
    except KeyboardInterrupt:
        print("\nAudioProcessingAgent manually stopped.")