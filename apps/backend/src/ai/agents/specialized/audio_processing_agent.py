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

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from core.utils import safe_error

logger = logging.getLogger(__name__)


def _run_coro_sync(coro):
    """在同步方法內跑協程：有運行中 loop 時用獨立線程，避免嵌套。"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result(timeout=180)


def _stt_text(audio_path: str) -> Optional[Dict[str, Any]]:
    """真實轉錄 via AudioService（延遲 import；引擎缺失/失敗回 None）。

     R26 接線：faster-whisper 已緩存時走離線引擎，否則回 None
    （呼叫方保持舊的 unavailable/空轉錄形狀，不崩潰）。
    """
    try:
        with open(audio_path, "rb") as f:
            data = f.read()
    except OSError:
        return None
    if not data:
        return None
    try:
        from services.audio_service import AudioService
    except ImportError:
        return None

    async def _go():
        return await AudioService().speech_to_text(data)

    try:
        result = _run_coro_sync(_go())
    except Exception as e:
        logger.warning(f"STT engine failed: {e}", exc_info=True)
        return None
    if not isinstance(result, dict) or not result.get("text"):
        return None
    return result


class AudioProcessingAgent:
    """Agent for audio transcription, analysis, and language detection."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.agent_id = kwargs.get("agent_id")
        self.hsp_connector: Optional[Any] = None
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
        if self.hsp_connector is None:
            logger.warning(
                f"AudioProcessingAgent hsp_connector not set; dropping task result for request {request_id}",
            )
            return
        await self.hsp_connector.send_task_result(result_payload)

    def _perform_speech_recognition(self, params: dict) -> dict:
        if "audio_file" not in params:
            raise ValueError("No audio file provided")
        stt = _stt_text(str(params["audio_file"]))
        if stt is None:
            return {"transcription": "", "language": "zh", "confidence": 0.0}
        return {
            "transcription": stt.get("text", ""),
            "language": stt.get("language", "zh"),
            "confidence": stt.get("confidence", 0.85),
        }

    def _classify_audio(self, params: dict) -> dict:
        if "audio_file" not in params:
            raise ValueError("No audio file provided")
        return {"primary_category": "unknown", "categories": []}

    def _enhance_audio(self, params: dict) -> dict:
        if "audio_file" not in params:
            raise ValueError("No audio file provided")
        return {"enhanced_file": "", "improvement_score": 0.0}

    def is_available(self) -> bool:
        """Check if audio processing backend is usable.

        R26: 除配置外，離線 faster-whisper 可用也算可用（已緩存即免配置）。
        find_spec 探測（不直接 import，避免無 stubs 誤報）。
        """
        if self.config.get("model_path") or self.config.get("api_key"):
            return True
        import importlib.util

        return importlib.util.find_spec("faster_whisper") is not None

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
        stt = _stt_text(audio_path)
        if stt is None:
            return {
                "status": "unavailable",
                "message": "Speech-to-text engine failed or produced no text",
                "transcription": "",
                "audio_format": ext,
            }
        return {
            "status": "success",
            "message": f"Transcribed audio ({ext})",
            "transcription": stt.get("text", ""),
            "language": stt.get("language", "zh"),
            "confidence": stt.get("confidence", 0.85),
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
        stt = _stt_text(audio_path)
        if stt is None:
            return {
                "status": "unavailable",
                "message": "Language detection engine failed or produced no text",
                "detected_language": "unknown",
                "confidence": 0.0,
            }
        return {
            "status": "success",
            "message": "Language detected",
            "detected_language": stt.get("language", "unknown"),
            "confidence": stt.get("confidence", 0.0),
        }
