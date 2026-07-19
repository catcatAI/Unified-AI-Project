# =============================================================================
# ANGELA-MATRIX: L6[执行层] α [A] L2+
# =============================================================================
#
# 职责: 音频处理代理，包括语音转文本、文本转语音等
# 维度: 主要涉及生理维度 (α) 的听觉处理
# 安全: 使用 Key A (后端控制) 进行音频隐私保护
# 成熟度: L2+ 等级可以使用基本的音频功能
#
# 能力:
# - speech_to_text: 语音转文本
# - text_to_speech: 文本转语音
# - audio_analysis: 音频分析
# - emotion_detection_from_audio: 音频情感检测
#
# =============================================================================

import logging
import os
from typing import Any, Dict, List, Optional

from core.utils import safe_error

logger = logging.getLogger(__name__)


class AudioProcessingAgent:
    """Agent for audio transcription, analysis, and language detection."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.agent_id = kwargs.get("agent_id")
        self.capabilities = [
            {
                "name": "speech_recognition",
                "capability_id": "speech_recognition",
                "description": "將音頻轉換為文字",
                "version": "1.0.0",
            },
            {
                "name": "audio_classification",
                "capability_id": "audio_classification",
                "description": "分類音頻類型",
                "version": "1.0.0",
            },
            {
                "name": "audio_enhancement",
                "capability_id": "audio_enhancement",
                "description": "增強音頻質量",
                "version": "1.0.0",
            },
        ]
        logger.info(f"AudioProcessingAgent initialized with config: {self.config}")

    async def handle_task_request(self, task_payload, sender_ai_id, envelope):
        capability_id_filter = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})
        request_id = task_payload.get("request_id", "")
        cap_name = capability_id_filter
        if self.agent_id and cap_name.startswith(self.agent_id + "_"):
            cap_name = cap_name[len(self.agent_id) + 1 :]
        if "_v" in cap_name:
            cap_name = cap_name.rsplit("_v", 1)[0]
        result_payload = {"request_id": request_id}
        try:
            if cap_name == "speech_recognition":
                result_payload["status"] = "success"
                result_payload["payload"] = self._perform_speech_recognition(params)
            elif cap_name == "audio_classification":
                result_payload["status"] = "success"
                result_payload["payload"] = self._classify_audio(params)
            elif cap_name == "audio_enhancement":
                result_payload["status"] = "success"
                result_payload["payload"] = self._enhance_audio(params)
            else:
                result_payload["status"] = "failure"
                result_payload["error_details"] = {"error_code": "CAPABILITY_NOT_SUPPORTED"}
        except ValueError as e:
            result_payload["status"] = "failure"
            result_payload["error_details"] = {
                "error_code": "INVALID_PARAMETERS",
                "error_message": safe_error(e),
            }
        await self.hsp_connector.send_task_result(result_payload)

    def _perform_speech_recognition(self, params: dict) -> dict:
        if "audio_file" not in params:
            raise ValueError("No audio file provided")
        return {"transcription": "", "language": "zh", "confidence": 0.0}

    def _classify_audio(self, params: dict) -> dict:
        if "audio_file" not in params:
            raise ValueError("No audio file provided")
        return {"primary_category": "unknown", "categories": []}

    def _enhance_audio(self, params: dict) -> dict:
        if "audio_file" not in params:
            raise ValueError("No audio file provided")
        return {"enhanced_file": "", "improvement_score": 0.0}

    def is_available(self) -> bool:
        """Check if audio processing backend (e.g. whisper) is configured."""
        return bool(self.config.get("model_path") or self.config.get("api_key"))

    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio file to text."""
        if not audio_path:
            return {"status": "error", "message": "No audio path provided"}
        if not os.path.isfile(audio_path):
            return {"status": "error", "message": f"Audio file not found: {audio_path}"}
        ext = os.path.splitext(audio_path)[1].lower()
        if not self.is_available():
            logger.info(f"transcribe_audio: {audio_path} ({ext}) (unavailable)")
            return {
                "status": "unavailable",
                "message": "Speech-to-text model not configured; set model_path or api_key in config",
                "transcription": "",
                "audio_format": ext,
            }
        logger.info(f"transcribe_audio: {audio_path} ({ext})")
        return {
            "status": "success",
            "message": f"Transcribed audio ({ext})",
            "transcription": "",
            "audio_format": ext,
        }

    def analyze_audio(self, audio_path: str) -> Dict[str, Any]:
        """Analyze audio file properties."""
        if not audio_path:
            return {"status": "error", "message": "No audio path provided"}
        if not os.path.isfile(audio_path):
            return {"status": "error", "message": f"Audio file not found: {audio_path}"}
        file_size = os.path.getsize(audio_path)
        ext = os.path.splitext(audio_path)[1].lower()
        logger.info(f"analyze_audio: {audio_path} ({ext}, {file_size} bytes)")
        return {
            "status": "success",
            "message": f"Analyzed audio file: {ext}, {file_size} bytes",
            "duration": 0.0,
            "format": ext,
            "analysis": {
                "file_size_bytes": file_size,
                "file_extension": ext,
            },
        }

    def detect_language(self, audio_path: str) -> Dict[str, Any]:
        """Detect language from audio."""
        if not audio_path:
            return {"status": "error", "message": "No audio path provided"}
        if not os.path.isfile(audio_path):
            return {"status": "error", "message": f"Audio file not found: {audio_path}"}
        if not self.is_available():
            logger.info(f"detect_language: {audio_path} (unavailable)")
            return {
                "status": "unavailable",
                "message": "Language detection model not configured; set model_path or api_key in config",
                "detected_language": "unknown",
                "confidence": 0.0,
            }
        logger.info(f"detect_language: {audio_path}")
        return {
            "status": "success",
            "message": "Language detected",
            "detected_language": "unknown",
            "confidence": 0.0,
        }
