"""
ANGELA-MATRIX: [L3] [βγ] [A] [L3]

ImageGenerationHandler — text→image for the chat path.

WHY this exists: image generation was only reachable through
``POST /api/v1/image/generate``. A chat request like 「生成一張貓咪的圖片」 was
classified as ``vision``, so ExecutionGate dispatched the *vision analysis*
handler and the user was told 「請提供圖片路徑」 — while a working generator sat
behind an HTTP route the chat path could not call. This handler gives the chat
path the same engine (ai.multimodal.generator.gvv_generator) and reports the
real result, including the concept the GVV pipeline actually resolved (a
compositional renderer cannot draw a cat; it draws primitives, and the reply
must say so rather than imply a photorealistic picture).
"""

import base64
import hashlib
import logging
import os
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_OUTPUT_DIR = os.environ.get(
    "ANGELA_IMAGE_OUTPUT_DIR",
    os.path.join("data", "generated_images"),
)

# Strip the generation instruction so the description handed to the concept
# mapper is the subject, not the request.
_INSTRUCTION_PREFIX = re.compile(
    r"^\s*(?:請|帮我|幫我|麻煩|請幫我)?\s*"
    r"(?:生成|產生|畫|繪|畫一張|畫一隻|做|生|生一張|來一張)\s*"
    r"(?:一張|一隻|一個|一張圖|圖片|圖|圖畫|插畫|照片|圖片嗎|照片嗎)?\s*"
    r"(?:的|一個|一隻)?\s*",
)


class ImageGenerationHandler:
    """Generates an image from the chat text and persists the PNG."""

    def __init__(self, output_dir: Optional[str] = None) -> None:
        self._output_dir = output_dir or _OUTPUT_DIR

    async def handle(self, text: str, intent: str = "image_generation") -> str:
        """Generate an image and describe what was actually produced."""
        subject = self._subject(text)
        if not subject:
            return "（圖像生成）想生成什麼圖呢？請告訴我主體，例如「生成一張貓咪的圖片」。"

        from ai.multimodal.generator.gvv_generator import generate_image

        try:
            result = generate_image(subject, canvas_size=128, num_iterations=30)
        except RuntimeError as e:
            return f"（圖像生成）生成服務不可用：{e}"
        except Exception as e:
            logger.warning("Image generation failed for %r: %s", subject, e, exc_info=True)
            return f"（圖像生成）生成失敗：{e}"

        path = self._persist(subject, result["image_base64"])
        metrics = result.get("metrics") or {}
        concept = metrics.get("concept") or "unknown"
        similarity = metrics.get("similarity")
        similarity_text = f"{similarity:.2f}" if isinstance(similarity, (int, float)) else "n/a"
        saved = f"，已存到 {path}" if path else ""
        return (
            f"（圖像生成）已用 GVV 複合繪圖管線生成 {result['width']}x{result['height']} 圖：\n"
            f"• 描述：{subject}\n"
            f"• 對應概念：{concept}（相似度 {similarity_text}）\n"
            f"• 這是幾何圖元組成的抽象畫，不是照片或寫實影像{saved}"
        )

    @staticmethod
    def _subject(text: str) -> str:
        """Extract the subject from a generation request."""
        cleaned = _INSTRUCTION_PREFIX.sub("", (text or "").strip())
        cleaned = cleaned.strip(" 的。．.，,、!！?？：: ")
        cleaned = re.sub(r"^(?:一張|一隻|一個)\s*", "", cleaned)
        return cleaned.strip()

    def _persist(self, subject: str, image_base64: str) -> str:
        """Write the PNG next to the runtime data. Returns "" on failure."""
        try:
            os.makedirs(self._output_dir, exist_ok=True)
            digest = hashlib.sha1(f"{subject}|{image_base64[:64]}".encode("utf-8")).hexdigest()[:12]
            safe = re.sub(r"[^\w\-]+", "_", subject)[:32] or "image"
            path = os.path.join(self._output_dir, f"{safe}_{digest}.png")
            with open(path, "wb") as fh:
                fh.write(base64.b64decode(image_base64))
            return path
        except Exception as e:
            logger.warning("Could not persist generated image: %s", e, exc_info=True)
            return ""

    def describe_capability(self) -> Dict[str, Any]:
        """Capability metadata (used by the runtime capability catalog)."""
        from ai.multimodal.generator import gvv_generator

        return {
            "id": "image_generation",
            "pipeline": "gvv",
            "models_available": gvv_generator._find_models_dir() is not None,
            "output_dir": self._output_dir,
        }
