# =============================================================================
# ANGELA-MATRIX: L6[执行层] γ [A] L2+
# =============================================================================
#
# 职责: 计算机视觉处理，包括图像分类、物体检测等
# 维度: 主要涉及物理维度 (γ) 的视觉数据处理
# 安全: 使用 Key A (后端控制) 进行图像隐私保护
# 成熟度: L2+ 等级可以使用基本的视觉功能
#
# 能力:
# - image_classification: 图像分类
# - object_detection: 物体检测
# - facial_recognition: 人脸识别
# - image_captioning: 图像描述生成
#
# =============================================================================

import logging
import os
import re
from typing import Any, Dict, List, Optional

from PIL import Image

logger = logging.getLogger(__name__)

try:
    import pytesseract

    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


class VisionProcessingAgent:
    """Agent for image analysis, object detection, and text extraction."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.agent_id = kwargs.get("agent_id")
        logger.info(f"VisionProcessingAgent initialized. OCR available: {PYTESSERACT_AVAILABLE}")

    def is_available(self) -> Dict[str, bool]:
        """Check which backends are available."""
        return {"pytesseract": PYTESSERACT_AVAILABLE}

    # Mirrors the three conventions VisionHandler._extract_image_path accepts, so
    # a path embedded in the message is found the same way in both paths. The
    # duplication is pinned by a test that asserts both extractors agree — if one
    # gains a convention the other must follow.
    _IMAGE_RE = re.compile(r"[\w\\/:.\-]+\.(?:png|jpg|jpeg|gif|bmp|webp|svg)", re.IGNORECASE)
    _OCR_HINTS = re.compile(r"(文字|文本|字|ocr|text|lettering|word|words)", re.IGNORECASE)

    def extract_image_path(self, prompt: str) -> Optional[str]:
        """First image path in the text. Pure string work — no file access."""
        m = re.search(r"```(?:image|img|pic)?\s*\n(.*?)```", prompt or "", re.DOTALL)
        if m:
            candidate = m.group(1).strip().split("\n")[0].strip()
            if candidate:
                return candidate
        m = re.search(r"`([^`]+\.(?:png|jpg|jpeg|gif|bmp|webp|svg))`", prompt or "", re.IGNORECASE)
        if m:
            return m.group(1)
        m = self._IMAGE_RE.search(prompt or "")
        return m.group(0) if m else None

    def handle_request(self, prompt: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Read text out of the image, or list what is in it.

        WHY this exists: `image_detail` maps to this agent, but the router passes
        the message under generic keys while this class needs an `image_path`.
        Without this entry point every request came back "No image path provided".
        """
        text = (prompt or "").strip()
        path = image_path or self.extract_image_path(text)
        if not path:
            return {
                "status": "error",
                "message": "No image path found; attach the image or name its file",
            }
        if self._OCR_HINTS.search(text):
            return self.extract_text(path)
        return self.detect_objects(path)

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze image and return dimensions, format, analysis result."""
        if not image_path:
            return {"status": "error", "message": "No image path provided"}
        if not os.path.isfile(image_path):
            return {"status": "error", "message": f"Image not found: {image_path}"}
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                fmt = img.format or "unknown"
                mode = img.mode
                analysis = {
                    "width": width,
                    "height": height,
                    "aspect_ratio": round(width / height, 4) if height else 0,
                    "mode": mode,
                }
            logger.info(f"analyze_image: {image_path} -> {width}x{height} {fmt}")
            return {
                "status": "success",
                "message": f"Analyzed image: {width}x{height} {fmt}",
                "dimensions": {"width": width, "height": height},
                "format": fmt.lower(),
                "analysis": analysis,
            }
        except Exception as e:
            logger.error(f"analyze_image failed for {image_path}: {e}")
            return {"status": "error", "message": f"Failed to analyze image: {e}"}

    def detect_objects(self, image_path: str) -> Dict[str, Any]:
        """Detect objects in image (placeholder — no object detection model loaded)."""
        if not image_path:
            return {"status": "error", "message": "No image path provided"}
        if not os.path.isfile(image_path):
            return {"status": "error", "message": f"Image not found: {image_path}"}
        logger.info(f"detect_objects: {image_path}")
        return {
            "status": "unavailable",
            "message": "Object detection model not loaded; install torchvision or YOLO",
            "objects": [],
        }

    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Extract text from image using Tesseract OCR."""
        if not image_path:
            return {"status": "error", "message": "No image path provided"}
        if not os.path.isfile(image_path):
            return {"status": "error", "message": f"Image not found: {image_path}"}
        if not PYTESSERACT_AVAILABLE:
            return {"status": "unavailable", "message": "pytesseract not installed"}
        try:
            with Image.open(image_path) as img:
                text = pytesseract.image_to_string(img)
            logger.info(f"extract_text: {image_path} -> {len(text)} chars")
            return {
                "status": "success",
                "message": f"Extracted {len(text)} characters from image",
                "extracted_text": text.strip(),
                "char_count": len(text),
            }
        except Exception as e:
            logger.error(f"extract_text failed for {image_path}: {e}")
            return {"status": "error", "message": f"OCR failed: {e}"}
