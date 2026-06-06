# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [C] [L2]
# =============================================================================

import copy
import logging
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from apps.backend.src.ai.ed3n.core_network import CoreNetwork
from apps.backend.src.ai.ed3n.dictionary_layer import DictionaryLayer
from apps.backend.src.ai.ed3n.multimodal.audio_encoder import AudioEncoder
from apps.backend.src.ai.ed3n.multimodal.cross_modal_trainer import CrossModalTrainer
from apps.backend.src.ai.ed3n.multimodal.image_encoder import ImageEncoder
from apps.backend.src.ai.ed3n.output_anchor import anchored_decode, ResponseAnchorValidator
from apps.backend.src.ai.ed3n.relation_classifier import RelationClassifier
from apps.backend.src.ai.ed3n.snn.snn_core import SNNCore
from apps.backend.src.ai.ed3n.snn.hormonal_modulator import HormonalModulator

logger = logging.getLogger(__name__)


class ReflexLayer:
    def __init__(self, max_cache: int = 128):
        self.patterns: Dict[str, str] = OrderedDict()
        self.lru_cache: OrderedDict[str, str] = OrderedDict()
        self.max_cache = max_cache

    def process(self, input_text: str) -> Optional[str]:
        normalized = input_text.strip().lower()

        if normalized in self.lru_cache:
            result = self.lru_cache.pop(normalized)
            self.lru_cache[normalized] = result
            return result

        for pattern, response in self.patterns.items():
            if pattern in normalized:
                self._add_to_cache(normalized, response)
                return response

        return None

    def add_pattern(self, pattern: str, response: str) -> None:
        self.patterns[pattern.lower().strip()] = response

    def load_presets(self) -> None:
        presets = self._build_presets()
        for pattern, response in presets.items():
            self.add_pattern(pattern, response)
        logger.info("Loaded %d reflex patterns.", len(presets))

    def _add_to_cache(self, key: str, value: str) -> None:
        if key in self.lru_cache:
            self.lru_cache.move_to_end(key)
        self.lru_cache[key] = value
        if len(self.lru_cache) > self.max_cache:
            self.lru_cache.popitem(last=False)

    @staticmethod
    def _build_presets() -> Dict[str, str]:
        return {
            "你好": "你好！很高兴见到你！",
            "早上好": "早上好！祝你今天愉快！",
            "晚上好": "晚上好！祝你今晚愉快！",
            "欢迎": "欢迎！很高兴你能来！",
            "再见": "再见！期待下次见面！",
            "明天见": "明天见！到时候聊！",
            "谢谢": "不客气！很高兴能帮到你！",
            "对不起": "没关系，别放在心上。",
            "没关系": "嗯，谢谢你理解！",
            "请": "请说，我在听。",
            "在忙吗": "不忙，随时为你服务！",
            "心情": "我心情不错！希望你也开心！",
            "今天": "今天是个好日子！",
            "名字": "我是Angela AI，很高兴认识你！",
            "做什么": "我在这里帮助你完成各种任务！",
            "开心": "开心真好！希望你一直保持好心情！",
            "难过": "别难过，我在这里陪着你。",
            "烦恼": "别烦恼了，我们一起想办法。",
            "无聊": "无聊的话，我们可以聊聊天！",
            "兴奋": "太棒了！你的热情感染了我！",
            "嗯": "嗯嗯，在听。",
            "好的": "好的，马上处理！",
            "明白": "明白，交给我吧。",
            "可以": "可以，没问题！",
            "help": "I'm here to help! How can I assist you?",
            "hello": "Hello! Nice to meet you!",
            "hi": "Hi there! How can I help you today?",
            "good morning": "Good morning! Hope you have a great day!",
            "goodbye": "Goodbye! Take care!",
            "thank you": "You're welcome! Happy to help!",
        }


class ED3NEngine:
    def __init__(
        self,
        dictionary: Optional[DictionaryLayer] = None,
        classifier: Optional[RelationClassifier] = None,
        network: Optional[CoreNetwork] = None,
        reflex: Optional[ReflexLayer] = None,
        snn_network: Optional[SNNCore] = None,
        modulator: Optional[HormonalModulator] = None,
        snn_mode: bool = False,
    ):
        self.reflex = reflex or ReflexLayer()
        self.dictionary = dictionary or DictionaryLayer()
        self.classifier = classifier or RelationClassifier(dictionary=self.dictionary)
        self.network = network or CoreNetwork(classifier=self.classifier)
        self._snn_network = snn_network
        self.modulator = modulator or HormonalModulator()
        self.snn_mode = snn_mode
        self._validator: Optional[ResponseAnchorValidator] = None
        self.image_encoder: Optional[ImageEncoder] = None
        self.audio_encoder: Optional[AudioEncoder] = None
        self.cross_modal_trainer: Optional[CrossModalTrainer] = None

    @property
    def validator(self) -> ResponseAnchorValidator:
        if self._validator is None:
            self._validator = ResponseAnchorValidator(dictionary=self.dictionary)
        return self._validator

    def process(
        self, input_text: str, context: Optional[Dict[str, Any]] = None, depth: str = "auto"
    ) -> str:
        reflex_result = self.process_reflex(input_text)
        if reflex_result is not None:
            return reflex_result

        if depth == "reflex":
            return reflex_result or ""

        if depth == "shallow" or (depth == "auto" and not context):
            return self.process_shallow(input_text, context)

        if depth == "snn":
            return self.process_snn(input_text, context)

        return self.process_deep(input_text, context)

    def process_reflex(self, input_text: str) -> Optional[str]:
        return self.reflex.process(input_text)

    def process_shallow(
        self, input_text: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        keys = self.dictionary.encode(input_text)
        if not keys:
            return "抱歉，我没理解你的意思。"
        decoded = self.dictionary.decode(keys, context)
        return decoded if decoded else "抱歉，我没理解你的意思。"

    @property
    def snn_network(self) -> SNNCore:
        if self._snn_network is None:
            self._snn_network = SNNCore(classifier=self.classifier)
            self._snn_network.connect_modulator(self.modulator)
        return self._snn_network

    def process_deep(
        self, input_text: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        keys = self.dictionary.encode(input_text)
        if not keys:
            return "抱歉，我没理解你的意思。"

        if self.snn_mode:
            network_output = self.snn_network.forward(keys, context=context)
        else:
            network_output = self.network.forward(keys, context=context)

        response = anchored_decode(
            network_output=network_output,
            original_input_keys=keys,
            dictionary=self.dictionary,
            top_k_anchors=3,
            top_k_network=5,
        )

        if not response:
            return self.dictionary.decode(keys, context) or "抱歉，我没理解你的意思。"

        if not self.validator.validate(response, anchored_keys=keys):
            fallback = self.dictionary.decode(keys, context)
            return fallback or response

        return response

    def process_snn(
        self, input_text: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Deep processing with SNN core (regardless of self.snn_mode)."""
        was_snn = self.snn_mode
        self.snn_mode = True
        try:
            return self.process_deep(input_text, context)
        finally:
            self.snn_mode = was_snn

    def enable_multimodal(self, enable_image=True, enable_audio=True) -> None:
        if enable_image:
            self.image_encoder = ImageEncoder(dictionary_layer=self.dictionary)
            self.dictionary.modality_encoders["image"] = self.image_encoder
        if enable_audio:
            self.audio_encoder = AudioEncoder(dictionary_layer=self.dictionary)
            self.dictionary.modality_encoders["audio"] = self.audio_encoder
        self.cross_modal_trainer = CrossModalTrainer(
            dictionary_layer=self.dictionary,
            core_network=self.network,
        )
        logger.info("ED3N multimodal enabled (image=%s, audio=%s)", enable_image, enable_audio)

    def _process_image_input(self, image_data) -> List[str]:
        if self.image_encoder is None:
            return []
        return self.image_encoder.encode(image_data)

    def _process_audio_input(self, audio_data) -> List[str]:
        if self.audio_encoder is None:
            return []
        return self.audio_encoder.encode(audio_data)

    def is_multimodal_available(self) -> bool:
        return self.image_encoder is not None or self.audio_encoder is not None

    def process_multimodal(
        self,
        text: Optional[str] = None,
        image_data: Optional[Any] = None,
        audio_data: Optional[Any] = None,
        context: Optional[Dict] = None,
        depth: str = "auto",
    ) -> str:
        text_keys: List[str] = []
        image_keys: List[str] = []
        audio_keys: List[str] = []

        if text:
            text_keys = self.dictionary.encode(text)

        if image_data:
            image_keys = self._process_image_input(image_data)

        if audio_data:
            audio_keys = self._process_audio_input(audio_data)

        combined_keys = list(set(text_keys + image_keys + audio_keys))

        if not combined_keys:
            return "抱歉，我没理解你的意思。"

        if self.cross_modal_trainer:
            for tk in text_keys or [""]:
                ik = image_keys[0] if image_keys else None
                ak = audio_keys[0] if audio_keys else None
                if tk:
                    self.cross_modal_trainer.record_co_occurrence(tk, ik, ak)

        if depth == "shallow" or (depth == "auto" and not context and not text):
            decoded = self.dictionary.decode(combined_keys, context)
            return decoded or "抱歉，我没理解你的意思。"

        if self.snn_mode:
            network_output = self.snn_network.forward(combined_keys, context=context)
        else:
            network_output = self.network.forward(combined_keys, context=context)

        response = anchored_decode(
            network_output=network_output,
            original_input_keys=combined_keys,
            dictionary=self.dictionary,
            top_k_anchors=3,
            top_k_network=5,
        )

        if not response:
            return self.dictionary.decode(combined_keys, context) or "抱歉，我没理解你的意思。"

        if not self.validator.validate(response, anchored_keys=combined_keys):
            fallback = self.dictionary.decode(combined_keys, context)
            return fallback or response

        return response

    def load_presets(self) -> None:
        self.reflex.load_presets()
        self.dictionary.load_preset_responses()
        logger.info("ED3NEngine loaded all presets.")

    def get_snn_stats(self) -> Dict[str, Any]:
        if self._snn_network is None:
            return {"snn_mode": self.snn_mode, "snn_initialized": False}
        return {
            "snn_mode": self.snn_mode,
            "snn_initialized": True,
            "sparsity": self._snn_network.get_sparsity_report(),
            "modulation": self.modulator.get_profile_summary(),
        }
