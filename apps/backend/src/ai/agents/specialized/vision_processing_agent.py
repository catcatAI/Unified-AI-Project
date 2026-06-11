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
            text = pytesseract.image_to_string(Image.open(image_path))
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
