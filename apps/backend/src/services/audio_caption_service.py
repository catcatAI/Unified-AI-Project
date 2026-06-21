"""
AudioCaptionService — LLM Audio API captioning for semantic audio understanding.

Uses Google Gemini (multimodal audio) and OpenAI (Whisper) APIs
to generate semantic descriptions of audio content. Supports Chinese and English.

P40: Audio semantic understanding layer — allows Angela to "hear" and
describe audio content (speech, music, environmental sounds).

Usage:
  svc = AudioCaptionService()
  result = await svc.caption(audio_wav_bytes, prompt="描述這段音頻")
  # -> {"caption": "...", "backend": "gemini", "language": "zh", "time_ms": 1234}
"""

import asyncio
import base64
import logging
import math
import os
import struct
import time
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from core.system.config.network_defaults import (
    GOOGLE_API_BASE,
    OPENAI_API_BASE,
    GOOGLE_TIMEOUT,
    OPENAI_TIMEOUT,
)

logger = logging.getLogger(__name__)

# Default prompt templates
AUDIO_CAPTION_PROMPT_ZH = "请详细描述这段音频内容，包括说话内容、背景音、音乐、环境声以及整体氛围。"
AUDIO_CAPTION_PROMPT_EN = "Describe this audio in detail, including speech content, background sounds, music, environmental noises, and overall atmosphere."
AUDIO_TRANSCRIBE_PROMPT_ZH = "请转录这段语音的内容（中文）。"
AUDIO_TRANSCRIBE_PROMPT_EN = "Please transcribe the speech in this audio (English)."


class AudioCaptionService:
    """Generate semantic descriptions of audio using LLM Audio APIs.

    Supports multiple backends with automatic fallback:
      1. Gemini 1.5 Flash (Google) — native audio support via inline_data
      2. OpenAI Whisper API — speech-to-text transcription

    Lazy-loads API keys from environment (no hard dependencies).
    """

    GEMINI_AUDIO_MODEL: str = "gemini-1.5-flash"
    OPENAI_WHISPER_MODEL: str = "whisper-1"
    MAX_AUDIO_SIZE: int = 10 * 1024 * 1024  # 10MB max for API upload

    def __init__(self):
        self._gemini_key: Optional[str] = None
        self._openai_key: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._available_backends: List[str] = []
        self._initialized: bool = False

    async def initialize(self) -> bool:
        """Check which backends are available by reading env vars.

        Returns True if at least one backend is configured.
        """
        self._gemini_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GOOGLE_API_KEY", "")
        self._openai_key = os.environ.get("OPENAI_API_KEY", "")

        self._available_backends = []
        if self._gemini_key and "your_" not in self._gemini_key and "PLACEHOLDER" not in self._gemini_key:
            self._available_backends.append("gemini")
        if self._openai_key and "your_" not in self._openai_key and "PLACEHOLDER" not in self._openai_key:
            self._available_backends.append("openai")

        self._initialized = True
        if self._available_backends:
            logger.info("AudioCaptionService initialized with backends: %s", self._available_backends)
            return True
        logger.warning("AudioCaptionService: no LLM Audio API keys configured (GEMINI_API_KEY / OPENAI_API_KEY)")
        return False

    def _get_session(self) -> aiohttp.ClientSession:
        """Lazy-init HTTP session with connection pooling."""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(limit=5, keepalive_timeout=30)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session. Call during shutdown."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    @property
    def is_available(self) -> bool:
        return self._initialized and len(self._available_backends) > 0

    @property
    def backends(self) -> List[str]:
        return list(self._available_backends)

    # --- Main caption method ---

    async def caption(
        self,
        audio_data: bytes,
        prompt: Optional[str] = None,
        language: str = "zh",
        preferred_backend: Optional[str] = None,
        mode: str = "auto",
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """Generate a semantic caption/transcription for the given audio.

        Args:
            audio_data: Raw WAV audio bytes
            prompt: Optional custom prompt (default: language-appropriate)
            language: "zh" for Chinese, "en" for English
            preferred_backend: "gemini", "openai", or None for auto
            mode: "auto" (describe), "transcribe" (speech-to-text), "describe" (full caption)
            timeout: API call timeout in seconds

        Returns:
            dict with:
              - caption (str): The generated description/transcription
              - backend (str): Which backend was used ("gemini", "openai", "none")
              - language (str): Language of the caption
              - mode (str): "auto", "transcribe", or "describe"
              - duration (float): Audio duration in seconds
              - time_ms (float): Processing time
              - error (str, optional): Error message if failed
        """
        if not self._initialized:
            await self.initialize()

        if not self.is_available:
            return {
                "caption": "", "backend": "none", "language": language,
                "mode": mode, "duration": 0.0,
                "error": "No LLM Audio API keys configured",
                "time_ms": 0.0,
            }

        if not audio_data:
            return {"caption": "", "backend": "none", "language": language,
                    "mode": mode, "duration": 0.0, "error": "Empty audio data", "time_ms": 0.0}

        if len(audio_data) > self.MAX_AUDIO_SIZE:
            return {"caption": "", "backend": "none", "language": language,
                    "mode": mode, "duration": 0.0,
                    "error": f"Audio too large: {len(audio_data)} bytes (max {self.MAX_AUDIO_SIZE})",
                    "time_ms": 0.0}

        t0 = time.time()
        caption_text = ""
        backend_used = "none"
        duration = self._detect_audio_duration(audio_data)

        # Determine caption prompt based on mode
        if prompt:
            caption_prompt = prompt
        elif mode == "transcribe":
            caption_prompt = AUDIO_TRANSCRIBE_PROMPT_ZH if language == "zh" else AUDIO_TRANSCRIBE_PROMPT_EN
        else:
            caption_prompt = AUDIO_CAPTION_PROMPT_ZH if language == "zh" else AUDIO_CAPTION_PROMPT_EN

        # Try backends in order: preferred -> gemini -> openai
        backends_to_try = []
        if preferred_backend and preferred_backend in self._available_backends:
            backends_to_try.append(preferred_backend)
        for b in ["gemini", "openai"]:
            if b in self._available_backends and b not in backends_to_try:
                backends_to_try.append(b)

        for backend in backends_to_try:
            try:
                if backend == "gemini":
                    caption_text = await self._caption_gemini(audio_data, caption_prompt, timeout)
                elif backend == "openai":
                    if mode == "transcribe":
                        caption_text = await self._transcribe_openai(audio_data, language, timeout)
                    else:
                        caption_text = await self._caption_openai(audio_data, caption_prompt, language, timeout)

                if caption_text:
                    backend_used = backend
                    break
            except Exception as e:
                logger.warning("AudioCaption %s failed: %s", backend, e, exc_info=True)
                continue

        elapsed = (time.time() - t0) * 1000
        result: Dict[str, Any] = {
            "caption": caption_text,
            "backend": backend_used,
            "language": language,
            "mode": mode,
            "duration": round(duration, 3),
            "time_ms": round(elapsed, 1),
        }
        if not caption_text:
            result["error"] = f"All backends failed: {', '.join(backends_to_try)}"
        return result

    # --- Gemini Audio ---

    async def _caption_gemini(
        self, audio_data: bytes, prompt: str, timeout: float
    ) -> str:
        """Generate caption using Gemini API (native audio support)."""
        session = self._get_session()
        b64 = base64.b64encode(audio_data).decode("utf-8")

        payload = {
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": "audio/wav", "data": b64}},
                    {"text": prompt},
                ]
            }],
            "generationConfig": {
                "maxOutputTokens": 512,
                "temperature": 0.3,
                "topP": 0.9,
            },
        }

        url = f"{GOOGLE_API_BASE.rstrip('/')}/models/{self.GEMINI_AUDIO_MODEL}:generateContent"
        async with session.post(
            url,
            params={"key": self._gemini_key},
            json=payload,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            if resp.status != 200:
                err_text = await resp.text()
                logger.error("Gemini Audio error: HTTP %d: %s", resp.status, err_text[:300])
                return ""
            data = await resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return ""
            return parts[0].get("text", "").strip()

    # --- OpenAI Whisper ASR ---

    async def _transcribe_openai(
        self, audio_data: bytes, language: str, timeout: float
    ) -> str:
        """Transcribe speech using OpenAI Whisper API."""
        session = self._get_session()

        # OpenAI Whisper uses multipart form upload
        data = aiohttp.FormData()
        data.add_field(
            "file",
            audio_data,
            filename="audio.wav",
            content_type="audio/wav",
        )
        data.add_field("model", self.OPENAI_WHISPER_MODEL)
        data.add_field("response_format", "json")
        if language == "zh":
            data.add_field("language", "zh")

        url = f"{OPENAI_API_BASE.rstrip('/')}/audio/transcriptions"
        async with session.post(
            url,
            data=data,
            headers={"Authorization": f"Bearer {self._openai_key}"},
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            if resp.status != 200:
                err_text = await resp.text()
                logger.error("OpenAI Whisper error: HTTP %d: %s", resp.status, err_text[:200])
                return ""
            result = await resp.json()
            return result.get("text", "").strip()

    # --- OpenAI GPT-4o Audio ---

    async def _caption_openai(
        self, audio_data: bytes, prompt: str, language: str, timeout: float
    ) -> str:
        """Generate audio description using OpenAI (Whisper + GPT-4o).

        Two-step pipeline:
          1. Transcribe via Whisper API
          2. Send transcription + prompt to GPT-4o-mini for analysis

        Args:
            audio_data: Raw WAV bytes
            prompt: User prompt for the description
            language: "zh" or "en" — passed to Whisper for accurate transcription
            timeout: API timeout in seconds
        """
        # Step 1: Transcribe via Whisper with correct language
        transcript = await self._transcribe_openai(audio_data, language, timeout)
        if not transcript:
            return ""

        # Build a combined analysis prompt
        analysis_prompt = f"{prompt}\n\nAudio transcript: {transcript}"

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": analysis_prompt},
            ],
            "max_tokens": 512,
            "temperature": 0.3,
        }

        session = self._get_session()
        url = f"{OPENAI_API_BASE.rstrip('/')}/chat/completions"
        async with session.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {self._openai_key}", "Content-Type": "application/json"},
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp:
            if resp.status != 200:
                err_text = await resp.text()
                logger.error("OpenAI Chat error: HTTP %d: %s", resp.status, err_text[:200])
                return ""
            data = await resp.json()
            choices = data.get("choices", [])
            if not choices:
                return ""
            return choices[0].get("message", {}).get("content", "").strip()

    # --- Utility ---

    @staticmethod
    def _detect_audio_duration(audio_data: bytes) -> float:
        """Detect audio duration in seconds from WAV header."""
        if len(audio_data) < 44:
            return 0.0
        try:
            if audio_data[:4] != b"RIFF":
                return 0.0
            channels = struct.unpack("<H", audio_data[22:24])[0]
            sample_rate = struct.unpack("<I", audio_data[24:28])[0]
            bits_per_sample = struct.unpack("<H", audio_data[34:36])[0]
            data_size = len(audio_data) - 44
            bytes_per_sec = channels * sample_rate * bits_per_sample // 8
            if bytes_per_sec == 0:
                return 0.0
            return data_size / bytes_per_sec
        except (struct.error, IndexError):
            return 0.0

    @staticmethod
    def generate_silence(duration_sec: float = 0.5, sample_rate: int = 16000) -> bytes:
        """Generate a silent WAV file for testing.

        Args:
            duration_sec: Duration in seconds
            sample_rate: Sample rate in Hz

        Returns:
            WAV bytes containing silence
        """
        num_samples = int(sample_rate * duration_sec)
        # Generate WAV manually
        data_size = num_samples * 2  # 16-bit mono
        buf = bytearray()
        # RIFF header
        buf.extend(b"RIFF")
        buf.extend(struct.pack("<I", 36 + data_size))
        buf.extend(b"WAVE")
        # fmt chunk
        buf.extend(b"fmt ")
        buf.extend(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
        # data chunk
        buf.extend(b"data")
        buf.extend(struct.pack("<I", data_size))
        buf.extend(b"\x00\x00" * num_samples)
        return bytes(buf)


# --- Global singleton ---

_AUDIO_CAPTION: Optional[AudioCaptionService] = None
_AUDIO_CAPTION_LOCK = asyncio.Lock()


async def get_audio_caption_service() -> AudioCaptionService:
    """Get or create the global AudioCaptionService singleton."""
    global _AUDIO_CAPTION
    if _AUDIO_CAPTION is None:
        async with _AUDIO_CAPTION_LOCK:
            if _AUDIO_CAPTION is None:
                svc = AudioCaptionService()
                await svc.initialize()
                _AUDIO_CAPTION = svc
    return _AUDIO_CAPTION


__all__ = [
    "AudioCaptionService",
    "get_audio_caption_service",
]
