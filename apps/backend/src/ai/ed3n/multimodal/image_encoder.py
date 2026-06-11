# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L2-L4]
# =============================================================================

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ImageEncoder:
    """
    Converts image data to abstract dictionary keys.
    Wraps existing VisionService and converts results to ED3N entries.
    """

    def __init__(self, dictionary_layer=None):
        self.dictionary = dictionary_layer
        self._vision_service = None

    @property
    def vision_service(self):
        if self._vision_service is not None:
            return self._vision_service
        try:
            from apps.backend.src.services.vision_service import VisionService
            self._vision_service = VisionService()
        except ImportError:
            try:
                from services.vision_service import VisionService
                self._vision_service = VisionService()
            except ImportError:
                logger.warning("VisionService not available")
                self._vision_service = None
        except (ImportError, RuntimeError, AttributeError) as e:
            logger.warning("VisionService error: %s", e)
            self._vision_service = None
        return self._vision_service

    def encode(self, image_data: bytes, context: Optional[Dict] = None) -> List[str]:
        if not image_data:
            return []
        vs = self.vision_service
        if vs is not None:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    analysis = loop.run_until_complete(
                        vs.analyze_image(image_data, context=context or {})
                    )
                finally:
                    loop.close()
                if "error" in analysis:
                    logger.warning("VisionService error: %s", analysis["error"])
                    return self._fallback_encode(image_data)
                return self._analyze_to_entries(analysis)
            except (ConnectionError, TimeoutError, ValueError, RuntimeError) as e:
                logger.warning("VisionService analysis failed: %s", e)
                return self._fallback_encode(image_data)
        return self._fallback_encode(image_data)

    def _analyze_to_entries(self, analysis: Dict) -> List[str]:
        keys: List[str] = []
        if "objects" in analysis:
            for obj in analysis["objects"]:
                name = obj.get("label") or obj.get("name") or str(obj)
                keys.append(self._key_for_concept(name, "object"))
        if "scene" in analysis:
            scene = analysis["scene"]
            if isinstance(scene, dict):
                scene_label = scene.get("label") or scene.get("scene_type") or str(scene)
            else:
                scene_label = str(scene)
            keys.append(self._key_for_concept(scene_label, "scene"))
        if "colors" in analysis:
            colors = analysis["colors"]
            if isinstance(colors, list):
                for c in colors:
                    color_name = c.get("name") or c.get("color") or str(c)
                    keys.append(self._key_for_concept(color_name, "color"))
            elif isinstance(colors, dict):
                for k, v in colors.items():
                    keys.append(self._key_for_concept(str(v), "color"))
        if "emotions" in analysis:
            emotions = analysis["emotions"]
            if isinstance(emotions, list):
                for em in emotions:
                    em_name = em.get("emotion") or em.get("label") or str(em)
                    keys.append(self._key_for_concept(em_name, "emotion"))
        if "caption" in analysis:
            caption = analysis["caption"]
            if isinstance(caption, dict):
                caption_text = caption.get("text") or caption.get("caption") or str(caption)
            else:
                caption_text = str(caption)
            keys.append(self._key_for_concept(caption_text, "caption"))
        if "ocr_text" in analysis:
            ocr = analysis["ocr_text"]
            if isinstance(ocr, list):
                for item in ocr:
                    text = item.get("text") or str(item)
                    keys.append(self._key_for_concept(text, "ocr"))
            elif isinstance(ocr, str):
                keys.append(self._key_for_concept(ocr, "ocr"))
        return keys

    def _key_for_concept(self, concept: str, category: str) -> str:
        concept_str = str(concept).lower().strip()
        if not concept_str:
            return ""
        if self.dictionary is not None:
            existing = self.dictionary.encode(concept_str)
            if existing:
                return existing[0]
            key = f"img_{category}_{abs(hash(concept_str)) % 10000}"
            self.dictionary.add_entry(
                key=key,
                surface_forms={"en": concept_str},
                contexts=[{"modality": "image", "category": category}],
                confidence=0.7,
            )
            return key
        return f"img_{category}_{abs(hash(concept_str)) % 10000}"

    def _fallback_encode(self, image_data: bytes) -> List[str]:
        keys: List[str] = []
        try:
            from io import BytesIO
            from PIL import Image
            img = Image.open(BytesIO(image_data))
            fmt = img.format or "unknown"
            size = f"{img.size[0]}x{img.size[1]}"
            keys.append(self._key_for_concept(fmt.lower(), "format"))
            keys.append(self._key_for_concept(size, "size"))
            if img.mode == "RGB" or img.mode == "RGBA":
                try:
                    colors = img.convert("RGB").resize((64, 64)).getcolors(4096)
                    if colors:
                        colors.sort(reverse=True)
                        dominant = colors[0][1]
                        r, g, b = dominant
                        if r > 200 and g > 200 and b > 200:
                            keys.append(self._key_for_concept("bright", "color"))
                        elif r < 60 and g < 60 and b < 60:
                            keys.append(self._key_for_concept("dark", "color"))
                        else:
                            keys.append(self._key_for_concept(f"rgb_{r}_{g}_{b}", "color"))
                except (ValueError, OSError, TypeError):
                    logger.debug("PIL color quantization failed")
        except (IOError, ValueError, TypeError, AttributeError) as e:
            logger.debug("PIL fallback failed: %s", e)
            keys.append(self._key_for_concept("unrecognized", "format"))
        return keys

    def is_available(self) -> bool:
        return self.vision_service is not None
