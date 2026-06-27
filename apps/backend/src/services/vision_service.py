# This module will handle image understanding, object detection, OCR, etc.
import asyncio
import hashlib
import io
import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core.perception.attention_controller import AttentionController
from core.perception.perceptual_memory import PerceptualMemory
from core.perception.visual_sampler import SamplingDistribution, VisualSampler
from core.sync.realtime_sync import SyncEvent, sync_manager
from core.system.cluster_manager import cluster_manager
from core.system.config.magic_numbers import timing_value
from integrations.os_bridge_adapter import OSBridgeAdapter

logger = logging.getLogger(__name__)

_MAX_PROCESSING_HISTORY = 500

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


class VisionService:
    """查看服務：提供圖像理解、物體檢測、OCR等多模態處理能力"""

    def __init__(self, config: Optional[Dict] = None) -> None:
        self.config = config or {}
        self.enabled = True
        self.peer_services: Dict[str, Any] = {}  # 其他多模態服務的引用
        self.processing_history: List[Dict[str, Any]] = []  # 處理歷史記錄

        # 2030 Standard: Hardware Bridge for OCR/Screen
        self.os_bridge = OSBridgeAdapter()
        
        # 初始化視覺組件
        self.sampler = VisualSampler(self.config.get("sampler_config"))
        self.memory = PerceptualMemory(capacity=self.config.get("memory_capacity", 1000))
        self.attention = AttentionController()

        # 初始化視覺模型 / API
        self.model_config = self.config.get(
            "model_config",
            {
                "detection_confidence_threshold": 0.5,
                "ocr_languages": ["en", "zh"],
                "max_objects_per_image": 20,
                "enable_face_recognition": False,
                "enable_scene_analysis": True,
            },
        )

        # 註冊同步事件監聽
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(self._init_sync_listener())
            self._init_task = task
            task.add_done_callback(
                lambda t: logger.warning("Task _init_sync_listener failed: %s", t.exception())
                if not t.cancelled() and t.exception() else None
            )
        except RuntimeError:
            # No running event loop, this is fine during import or sync tests
            logger.debug(
                "No running event loop, sync listener will not be initialized automatically"
            )

        logger.info("Vision Service initialized with enhanced capabilities")

    async def _init_sync_listener(self) -> None:
        """初始化同步監聽器"""
        try:
            await sync_manager.register_client("vision_service", self._handle_sync_event)
            logger.info("Vision Service registered to sync manager")
        except Exception as e:  # broad exception acceptable: sync registration should not crash
            logger.error(f"Failed to register Vision Service to sync manager: {e}", exc_info=True)

    async def _handle_sync_event(self, event: SyncEvent) -> None:
        """處理同步事件"""
        if event.type == "module_control":
            module = event.data.get("module")
            enabled = event.data.get("enabled")
            if module == "vision":
                self.enabled = enabled
                logger.info(f"Vision Service enabled status changed to: {enabled}")

    def set_peer_services(self, peer_services: Dict[str, Any]) -> None:
        """設置其他多模態服務的引用"""
        self.peer_services = peer_services
        logger.debug(f"Vision Service connected to peer services: {list(peer_services.keys())}")

    async def analyze_image(
        self,
        image_data: Optional[bytes] = None,
        features: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        分析圖像並提取指定特徵 (2030 Standard: Support Auto-Capture).
        """
        image_data, err = await self._auto_capture(image_data)
        if err:
            return err

        analysis_results, requested_features = self._setup_analysis(image_data, features, context)
        if not image_data:
            return {"error": "No image data provided", "processing_id": analysis_results.get("processing_id")}

        try:
            await self._extract_features(image_data, requested_features, analysis_results.get("context", {}), analysis_results)
            self._record_processing(analysis_results.get("processing_id"), requested_features, True)
            return analysis_results
        except Exception as e:
            logger.error(f"Error analyzing image {analysis_results.get('processing_id')}: {e}", exc_info=True)
            error_result = self._build_error_result(e, analysis_results.get("processing_id"))
            self._record_processing(analysis_results.get("processing_id"), requested_features, False, str(e))
            return error_result

    async def _auto_capture(self, image_data: Optional[bytes]) -> Tuple[Optional[bytes], Optional[Dict]]:
        """Auto-capture screen if no image data provided."""
        if image_data is not None:
            return image_data, None
        try:
            from io import BytesIO

            import pyautogui
            screenshot = pyautogui.screenshot()
            img_byte_arr = BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            logger.info("📸 [Vision] Environment captured: Automated screen snapshot.")
            return img_byte_arr.getvalue(), None
        except Exception as e:
            logger.error(f"Failed to auto-capture screen: {e}", exc_info=True)
            return None, {"error": "Vision capture failed"}

    def _setup_analysis(self, image_data: bytes, features: Optional[List[str]], context: Optional[Dict]) -> tuple:
        """Initialize analysis results dict and feature list."""
        processing_id = self._generate_processing_id(image_data)
        requested_features = features or ["captioning", "object_detection", "scene_analysis"]
        analysis_results: Dict[str, Any] = {
            "processing_id": processing_id,
            "image_size": len(image_data),
            "timestamp": datetime.now().isoformat(),
            "requested_features": requested_features,
            "context": context or {},
        }
        logger.info(f"Vision Service: Analyzing image (ID: {processing_id}) for features: {requested_features}")
        return analysis_results, requested_features

    async def _extract_features(self, image_data: bytes, requested_features: List[str], context: Dict, results: Dict) -> None:
        """Run requested feature extractors against the image."""
        if "captioning" in requested_features:
            results["caption"] = await self._generate_image_caption(image_data, context)
        if "object_detection" in requested_features:
            results["objects"] = await self._detect_objects(image_data)
        if "ocr" in requested_features:
            results["ocr_text"] = await self._extract_text_ocr(image_data)
        if "face_recognition" in requested_features and self.model_config.get("enable_face_recognition"):
            results["faces"] = await self._detect_faces(image_data)
        if "scene_analysis" in requested_features:
            results["scene"] = await self._analyze_scene(image_data)
        if "emotion_detection" in requested_features:
            results["emotions"] = await self._detect_emotions(image_data)
        if "color_analysis" in requested_features:
            results["colors"] = await self._analyze_colors(image_data)
        if context.get("text_context") or context.get("audio_context"):
            results["multimodal_insights"] = await self._perform_multimodal_analysis(results, context)

    def _record_processing(self, processing_id: str, features: List[str], success: bool, error_msg: str = "") -> None:
        """Record analysis to processing history, trimming if needed."""
        entry = {
            "processing_id": processing_id,
            "timestamp": datetime.now().isoformat(),
            "features": features,
            "success": success,
        }
        if error_msg:
            entry["error"] = error_msg
        self.processing_history.append(entry)
        if len(self.processing_history) > _MAX_PROCESSING_HISTORY:
            self.processing_history = self.processing_history[-_MAX_PROCESSING_HISTORY:]

    def _build_error_result(self, error: Exception, processing_id: str) -> Dict[str, Any]:
        return {
            "error": str(error),
            "processing_id": processing_id,
            "timestamp": datetime.now().isoformat(),
        }

    async def compare_images(
        self,
        image_data1: bytes,
        image_data2: bytes,
        comparison_type: str = "similarity",
    ) -> Dict[str, Any]:
        """
        比較兩張圖像並返回相似性分數和詳細分析。
        Uses PIL for pixel-level comparison when available.
        """
        if not image_data1 or not image_data2:
            return {"error": "One or both images are missing", "similarity_score": None}

        logger.info(
            f"Vision Service: Comparing images (sizes: {len(image_data1)}, {len(image_data2)}) using {comparison_type}"
        )

        try:
            comparison_result: Dict[str, Any] = {
                "comparison_type": comparison_type,
                "timestamp": datetime.now().isoformat(),
                "image1_size": len(image_data1),
                "image2_size": len(image_data2),
            }

            if comparison_type == "similarity":
                try:
                    from io import BytesIO

                    from PIL import Image
                    img1 = Image.open(BytesIO(image_data1)).convert("RGB").resize((32, 32))
                    img2 = Image.open(BytesIO(image_data2)).convert("RGB").resize((32, 32))
                    p1 = list(img1.getdata())
                    p2 = list(img2.getdata())
                    diffs = sum(abs(p1[i][j] - p2[i][j]) for i in range(len(p1)) for j in range(3))
                    max_diff = len(p1) * 3 * 255
                    similarity_score = 1.0 - (diffs / max_diff)
                except Exception:
                    size_factor = 1 - abs(len(image_data1) - len(image_data2)) / max(
                        len(image_data1), len(image_data2), 1
                    )
                    similarity_score = size_factor

                comparison_result["similarity_score"] = round(similarity_score, 3)
                comparison_result["confidence"] = round(0.5 + 0.5 * similarity_score, 3)

            elif comparison_type == "difference":
                try:
                    from io import BytesIO

                    import numpy as np
                    from PIL import Image
                    img1 = np.array(Image.open(BytesIO(image_data1)).convert("RGB").resize((64, 64)))
                    img2 = np.array(Image.open(BytesIO(image_data2)).convert("RGB").resize((64, 64)))
                    diff = np.abs(img1.astype(int) - img2.astype(int))
                    diff_score = float(np.mean(diff) / 255.0)
                    comparison_result["difference_score"] = round(diff_score, 3)
                except Exception:
                    comparison_result["difference_score"] = round(
                        1 - len(image_data1) / max(len(image_data2), 1), 3
                    )

            elif comparison_type == "feature_match":
                # Feature matching requires real CV libraries; use size-based heuristic
                size_ratio = min(len(image_data1), len(image_data2)) / max(len(image_data1), len(image_data2), 1)
                comparison_result["feature_similarity"] = round(size_ratio, 3)
                comparison_result["matched_features"] = {
                    "keypoints_matched": int(size_ratio * 50),
                    "total_keypoints_1": 50,
                    "total_keypoints_2": 50,
                    "match_quality": round(size_ratio * 0.8 + 0.1, 3),
                }

            return comparison_result

        except Exception as e:
            logger.error(f"Error comparing images: {e}", exc_info=True)
            return {"error": str(e), "similarity_score": None}

    async def process_video_frame(
        self,
        frame_data: bytes,
        frame_number: int,
        video_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """處理視頻幀片, 支持時序分析"""
        logger.debug(f"Processing video frame {frame_number}")

        # 重用圖像分析功能, 但添加視頻特定上下文
        video_context = video_context or {}
        video_context["frame_number"] = frame_number
        video_context["is_video_frame"] = True

        frame_analysis = await self.analyze_image(
            frame_data,
            features=["object_detection", "scene_analysis", "motion_detection"],
            context=video_context,
        )

        # 添加視頻特定資訊
        frame_analysis["frame_number"] = frame_number
        frame_analysis["motion_detected"] = random.choice([True, False])

        return frame_analysis

    async def get_sampling_analysis(
        self,
        center: Tuple[float, float] = (0.5, 0.5),
        scale: float = 1.0,
        deformation: float = 0.0,
        distribution: str = "GAUSSIAN",
        target_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        執行視覺採樣分析並獲取統計數據
        """
        dist_enum = SamplingDistribution[distribution.upper()]

        # 1. 更新注意力控制器位置
        self.attention.update_target(center, target_id=target_id)

        # 2. 生成粒子雲
        self.sampler.generate_cloud(center=center, distribution=dist_enum)

        # 3. 應用變換
        self.sampler.apply_transform(scale=scale, deformation=deformation)

        # 4. 獲取統計
        stats = self.sampler.get_attention_stats()

        logger.info(
            f"Visual sampling performed at {center} with scale {scale}, mode: {self.attention.mode.name}"
        )

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "sampling_stats": stats,
            "attention_mode": self.attention.mode.name,
            "target_id": self.attention.current_target_id,
        }

    async def perceive_and_focus(self, image_data: bytes) -> Dict[str, Any]:
        """
        模擬「發現-聚焦-記憶」的視覺鏈路：
        1. 在當前視場中發現物體 (模擬檢測)
        2. 將發現的物體存入感知記憶
        3. 根據注意力策略決定下一個焦點
        4. 如果有感興趣的物體，執行高精度聚焦採樣
        5. 將感興趣的物體建模到桌布 (新增加)
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "Vision system is currently disabled",
            }

        # 1. 基礎檢測 (模擬第一幀發現)
        detected = await self._detect_objects(image_data)

        # 2. 存入記憶
        perceived_objs = []
        for obj in detected:
            # 轉換為座標格式 (取中心點)
            bbox = obj["bounding_box"]  # [xmin, ymin, xmax, ymax]
            pos = ((bbox[0] + bbox[2]) / 200, (bbox[1] + bbox[3]) / 200)  # 假設 100x100

            p_obj = self.memory.add_or_update(
                {
                    "label": obj["label"],
                    "confidence": obj["confidence"],
                    "position": pos,
                    "bounds": tuple(bbox),
                }
            )
            perceived_objs.append(p_obj)

        # 3. 注意力決策：下一個焦點在哪？
        next_pos, target_id = self.attention.get_next_focus_point(perceived_objs)

        # 4. 執行聚焦採樣 (模擬下一幀聚焦)
        # 如果有目標 ID，切換到 FOCUS 模式
        is_focus_mode = target_id is not None
        sampling_results = await self.get_sampling_analysis(
            center=next_pos,
            distribution="GAUSSIAN" if is_focus_mode else "UNIFORM",
            scale=0.5 if is_focus_mode else 1.0,  # 聚焦時縮小範圍提高精度
            target_id=target_id,
        )

        # 5. 自動建模到桌布：如果置信度高且是感興趣的物體
        wallpaper_injections = []
        for obj in perceived_objs:
            if obj.get("confidence", 0) > 0.8:  # 高置信度閾值
                injection_data = {
                    "type": "wallpaper_object_injection",
                    "data": {
                        "name": obj["label"],
                        "position": {
                            "x": obj["position"][0],
                            "y": obj["position"][1],
                            "z": 0,
                        },
                        "scale": obj["confidence"],
                        "metadata": {
                            "source": "vision_service",
                            "detection_time": datetime.now().isoformat(),
                        },
                    },
                }
                wallpaper_injections.append(injection_data)

                # 觸發同步事件，將物體建模到桌布
                import uuid

                try:
                    await sync_manager.broadcast_event(
                        SyncEvent(
                            id=str(uuid.uuid4()),
                            event_type="wallpaper_object_injection",
                            data=injection_data["data"],
                            source="vision_service",
                        )
                    )
                    logger.info(f"Broadcasted wallpaper injection for: {obj['label']}")
                except Exception as e:  # broad exception acceptable: broadcast is optional, should not block
                    logger.error(f"Failed to broadcast wallpaper injection: {e}", exc_info=True)

        return {
            "status": "success",
            "perceived_objects_count": len(perceived_objs),
            "next_focus_point": next_pos,
            "target_id": target_id,
            "sampling_results": sampling_results,
            "wallpaper_injections": wallpaper_injections,
            "memory_stats": {"total_remembered": len(self.memory.objects)},
        }

    def _generate_processing_id(self, image_data: bytes) -> str:
        """生成唯一的處理ID"""
        hash_object = hashlib.md5(image_data)
        return f"vision_{hash_object.hexdigest()[:8]}_{datetime.now().strftime('%H%M%S')}"

    async def _generate_image_caption(self, image_data: bytes, context: Dict[str, Any]) -> str:
        """生成圖像描述 — uses PIL metadata, falls back to informative description"""
        await asyncio.sleep(timing_value("vision.processing_slow", 0.1))

        try:
            from io import BytesIO

            from PIL import Image
            img = Image.open(BytesIO(image_data))
            fmt = img.format or "unknown"
            size = f"{img.size[0]}x{img.size[1]}"
            mode = img.mode
            base_caption = f"Image in {fmt} format, {size} pixels, {mode} color mode"
            if context.get("text_context"):
                base_caption += f", related to: {context['text_context'][:50]}"
            return base_caption
        except Exception:
            base_caption = "An image (format could not be determined)"
            if context.get("text_context"):
                base_caption += f" related to {context['text_context'][:50]}"
            return base_caption

    async def _detect_objects(self, image_data: bytes) -> List[Dict[str, Any]]:
        """物體檢測 — returns PIL-based image properties as structured metadata"""
        await asyncio.sleep(timing_value("vision.processing_medium", 0.05))

        try:
            from io import BytesIO

            from PIL import Image
            img = Image.open(BytesIO(image_data))
            fmt = img.format or "unknown"
            w, h = img.size
            mode = img.mode
            # Provide image properties as structured output instead of random objects
            properties = [
                {"label": f"format_{fmt.lower()}", "confidence": 0.95, "property": "format"},
                {"label": f"resolution_{w}x{h}", "confidence": 0.95, "property": "resolution"},
                {"label": f"color_mode_{mode}", "confidence": 0.95, "property": "color_mode"},
            ]
            # Attempt cluster distribution with real image hash as feature vector
            try:
                feature_hash = [ord(c) / 255.0 for c in hashlib.md5(image_data).hexdigest()[:64]]
                await cluster_manager.distribute_task("Vision", feature_hash)
            except Exception:
                pass
            return properties
        except Exception:
            return [{"label": "unrecognized_image", "confidence": 0.5, "property": "format"}]

    async def initialize(self) -> bool:
        """Boot cognitive perception layers."""
        logger.info("[Vision] Realized Vision System Online.")
        return True

    async def shutdown(self) -> bool:
        logger.info("[Vision] Powered down.")
        return True

    async def _extract_text_ocr(self, image_data: bytes) -> Dict[str, Any]:
        """Extract text from image using pytesseract (when available).

        Falls back gracefully when pytesseract or the tesseract binary is
        not installed.
        """
        await asyncio.sleep(timing_value("vision.processing_ocr", 0.05))
        if not PYTESSERACT_AVAILABLE:
            return {"text": "", "language": "auto", "confidence": 0.0,
                    "status": "pytesseract not installed (pip install pytesseract)"}
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(img)
            lang = pytesseract.get_languages()
            return {
                "text": text.strip(),
                "language": lang[-1] if lang else "auto",
                "confidence": 0.85 if text.strip() else 0.0,
                "status": "success" if text.strip() else "no_text_found",
            }
        except Exception as e:
            logger.debug("pytesseract OCR failed: %s", e)
            return {"text": "", "language": "auto", "confidence": 0.0,
                    "status": f"ocr_failed: {e}"}

    async def _detect_faces(self, image_data: bytes) -> List[Dict[str, Any]]:
        """臉部檢測 — ML model required; returns image metadata when model unavailable"""
        await asyncio.sleep(timing_value("vision.processing_ocr", 0.06))

        # Face detection requires ML model (MTCNN, RetinaFace, etc.)
        # Without one, report availability info instead of random data
        try:
            from io import BytesIO

            from PIL import Image
            img = Image.open(BytesIO(image_data))
            w, h = img.size
            if w < 32 or h < 32:
                return []
        except Exception:
            pass
        return []

    async def _analyze_scene(self, image_data: bytes) -> Dict[str, Any]:
        """場景分析 — uses PIL for brightness/contrast/complexity estimation"""
        await asyncio.sleep(timing_value("vision.processing_caption", 0.04))

        try:
            import math
            from io import BytesIO

            from PIL import Image
            img = Image.open(BytesIO(image_data)).convert("RGB").resize((64, 64))
            pixels = list(img.getdata())
            total = len(pixels)
            r_avg = sum(p[0] for p in pixels) / total
            g_avg = sum(p[1] for p in pixels) / total
            b_avg = sum(p[2] for p in pixels) / total
            brightness = (r_avg + g_avg + b_avg) / 3.0
            variance = sum((p[0] - r_avg)**2 + (p[1] - g_avg)**2 + (p[2] - b_avg)**2 for p in pixels) / total
            contrast = math.sqrt(variance / 3.0)

            if brightness > 180:
                time_est = "daytime"
            elif brightness > 100:
                time_est = "afternoon"
            elif brightness > 50:
                time_est = "evening"
            else:
                time_est = "night"

            if contrast > 60:
                complexity = "high"
            elif contrast > 30:
                complexity = "moderate"
            else:
                complexity = "low"

            return {
                "scene_type": "digital_image",
                "brightness": round(brightness / 255.0, 3),
                "contrast": round(contrast / 255.0, 3),
                "estimated_lighting": time_est,
                "complexity": complexity,
                "confidence": 0.85,
            }
        except Exception:
            return {"scene_type": "unknown", "confidence": 0.3}

    async def _detect_emotions(self, image_data: bytes) -> Dict[str, Any]:
        """情緒檢測 — ML model required; returns neutral when model unavailable"""
        await asyncio.sleep(timing_value("vision.processing_classify", 0.03))

        # Emotion recognition from faces requires ML model (FER, DeepFace, etc.)
        return {
            "primary_emotion": "unknown",
            "emotion_scores": {"neutral": 0.5},
            "confidence": 0.3,
            "note": "Emotion detection requires ML model (FER/DeepFace) — not available",
        }

    async def _analyze_colors(self, image_data: bytes) -> Dict[str, Any]:
        """顏色分析 — uses PIL to extract dominant colors and brightness"""
        await asyncio.sleep(timing_value("vision.processing_fast", 0.02))

        try:
            from io import BytesIO

            from PIL import Image
            img = Image.open(BytesIO(image_data)).convert("RGB").resize((64, 64))
            pixels = list(img.getdata())
            total = len(pixels)
            r_total = sum(p[0] for p in pixels) / total
            g_total = sum(p[1] for p in pixels) / total
            b_total = sum(p[2] for p in pixels) / total
            brightness = (r_total + g_total + b_total) / 765.0
            dominant = self._extract_dominant_colors(img, total)
            return {
                "dominant_colors": [c["name"] for c in dominant[:4]],
                "color_distribution": {c["name"]: c["ratio"] for c in dominant},
                "brightness": round(brightness, 3),
                "avg_rgb": [round(r_total), round(g_total), round(b_total)],
            }
        except Exception:
            return {"dominant_colors": ["unknown"], "color_distribution": {}, "brightness": 0.5}

    def _extract_dominant_colors(self, img: Any, total: int) -> List[Dict[str, Any]]:
        colors = img.getcolors(4096)
        dominant: List[Dict[str, Any]] = []
        if colors:
            colors.sort(reverse=True)
            for count, (r, g, b) in colors[:5]:
                name = self._name_color(r, g, b)
                dominant.append({"name": name, "rgb": [r, g, b], "ratio": round(count / total, 3)})
        return dominant

    def _name_color(self, r: int, g: int, b: int) -> str:
        if r > 200 and g < 100 and b < 100:
            return "red"
        if g > 200 and r < 100 and b < 100:
            return "green"
        if b > 200 and r < 100 and g < 100:
            return "blue"
        if r > 200 and g > 200 and b < 100:
            return "yellow"
        if r > 200 and g > 150 and b > 150:
            return "pink"
        if r < 80 and g < 80 and b < 80:
            return "black"
        if r > 200 and g > 200 and b > 200:
            return "white"
        if r > 150 and g > 100 and b < 100:
            return "orange"
        if r > 100 and g < 50 and b > 100:
            return "purple"
        return f"rgb({r},{g},{b})"

    async def _perform_multimodal_analysis(
        self, visual_analysis: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """執行多模態分析, 結合視覺、文本和音頻上下文"""
        await asyncio.sleep(timing_value("vision.processing_medium", 0.05))
        insights: Dict[str, Any] = {}

        # 結合文本上下文
        if context.get("text_context"):
            text_context = context["text_context"]
            caption = visual_analysis.get("caption", "a scene")
            insights["context_enhanced_caption"] = f"Image shows {caption} related to: {text_context[:50]}"

        # 結合音頻上下文
        if context.get("audio_context"):
            if self.peer_services.get("audio"):
                insights["cross_modal_features"] = "Audio and visual data processed together"

        return insights

    async def _identify_differences(
        self, image_data1: bytes, image_data2: bytes
    ) -> List[Dict[str, Any]]:
        """識別兩張圖像之間的差異區域 — uses PIL pixel comparison"""
        await asyncio.sleep(timing_value("vision.processing_detect", 0.07))

        try:
            from io import BytesIO

            import numpy as np
            from PIL import Image
            img1 = np.array(Image.open(BytesIO(image_data1)).convert("RGB").resize((32, 32)))
            img2 = np.array(Image.open(BytesIO(image_data2)).convert("RGB").resize((32, 32)))
            diff = np.abs(img1.astype(int) - img2.astype(int))
            diff_mask = np.mean(diff, axis=2) > 30
            diff_coords = np.argwhere(diff_mask)
            if len(diff_coords) == 0:
                return []
            # Report up to 3 difference regions
            differences = []
            seen = set()
            for y, x in diff_coords[:100]:
                region_key = (x // 8, y // 8)
                if region_key not in seen:
                    seen.add(region_key)
                    differences.append({
                        "difference_id": f"diff_{len(differences) + 1}",
                        "type": "color_change",
                        "location": [int(x * 3.2), int(y * 3.2), 26, 26],
                        "confidence": 0.85,
                    })
                    if len(differences) >= 3:
                        break
            return differences
        except Exception:
            # Fallback: compare file sizes
            if len(image_data1) != len(image_data2):
                return [{"difference_id": "diff_1", "type": "size_change", "confidence": 0.6}]
            return []

    async def _match_image_features(self, image_data1: bytes, image_data2: bytes) -> Dict[str, Any]:
        """配對兩張圖像的特徵點 — uses PIL hash-based matching"""
        await asyncio.sleep(timing_value("vision.processing_ocr", 0.06))

        try:
            import hashlib
            from io import BytesIO

            from PIL import Image
            img1 = Image.open(BytesIO(image_data1)).convert("RGB").resize((16, 16))
            img2 = Image.open(BytesIO(image_data2)).convert("RGB").resize((16, 16))
            h1 = hashlib.md5(img1.tobytes()).hexdigest()
            h2 = hashlib.md5(img2.tobytes()).hexdigest()
            matching_bits = sum(c1 == c2 for c1, c2 in zip(h1, h2))
            similarity = matching_bits / len(h1)
            return {
                "keypoints_matched": int(similarity * 100),
                "total_keypoints_1": 100,
                "total_keypoints_2": 100,
                "match_quality": round(similarity, 3),
                "geometric_consistency": round(similarity * 0.9, 3),
            }
        except Exception:
            return {"keypoints_matched": 0, "total_keypoints_1": 0, "total_keypoints_2": 0,
                    "match_quality": 0.0, "geometric_consistency": 0.0}

    async def process(self, input_data: Any) -> Dict[str, Any]:
        """統一的處理方法, 用於統一控制中心調用"""
        if isinstance(input_data, dict):
            if "image_data" in input_data:
                return await self.analyze_image(
                    input_data["image_data"],
                    input_data.get("features"),
                    input_data.get("context"),
                )
            elif "compare_images" in input_data:
                return await self.compare_images(
                    input_data["image_data1"],
                    input_data["image_data2"],
                    input_data.get("comparison_type", "similarity"),
                )

        return {"error": "Invalid input format for vision processing"}

    async def encode_image(self, image_data: bytes) -> list:
        """Encode image into a feature vector using VisualEncoder (P15)."""
        if not image_data:
            return []
        try:
            from ai.multimodal.visual_encoder import VisualEncoder
            encoder = VisualEncoder()
            vec = encoder.encode(image_data)
            return vec.tolist()
        except Exception as e:
            logger.warning("VisualEncoder failed: %s", e)
            return []

    async def encode_with_pipeline(self, image_data: bytes) -> dict:
        """Encode image using the full VisionPipeline (P31).

        Returns the full pipeline result dict with latent, ssim, psnr, etc.
        Lazily initializes and caches the VisionPipeline instance.
        """
        try:
            from ai.vision.vision_pipeline import VisionPipeline
            if not hasattr(self, '_vision_pipeline') or self._vision_pipeline is None:
                self._vision_pipeline = VisionPipeline()
            import asyncio
            return await asyncio.to_thread(self._vision_pipeline.process, image_data)
        except Exception as e:
            logger.warning("VisionPipeline failed: %s", e)
            return {"error": str(e)}

    async def batch_encode(self, images: list) -> list:
        """Batch encode multiple images using VisionPipeline.

        Args:
            images: List of raw image bytes

        Returns:
            List of result dicts
        """
        results = []
        for img in images:
            result = await self.encode_with_pipeline(img)
            results.append(result)
        return results

    def clear_vision_pipeline_cache(self) -> None:
        """Clear the VisionPipeline LRU cache."""
        if hasattr(self, '_vision_pipeline') and self._vision_pipeline is not None:
            self._vision_pipeline.clear_cache()


if __name__ == "__main__":

    async def main() -> None:
        """Main entry point."""
        vision_config = {}  # Placeholder for actual config
        service = VisionService(config=vision_config)

        # Test image analysis (with dummy bytes)
        dummy_image = b"\x10\x11\x12\x13\x14\x15"
        analysis = await service.analyze_image(dummy_image, features=["captioning", "ocr"])
        logger.info(f"Image Analysis: {analysis}")

        analysis_default = await service.analyze_image(dummy_image)
        logger.info(f"Image Analysis (default features): {analysis_default}")

        # Test image comparison
        dummy_image2 = b"\x20\x21\x22\x23\x24\x25"
        similarity = await service.compare_images(dummy_image, dummy_image2)
        logger.info(f"Image Similarity: {similarity}")

        logger.info("Vision Service script finished.")

    asyncio.run(main())
