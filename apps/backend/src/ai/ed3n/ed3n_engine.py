# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [C] [L2]
# =============================================================================

import json
import logging
import os
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from ai.core.unicode_utils import normalize_text, is_english_dominant

from .input_enricher import InputEnricher
from .telemetry import TelemetryCollector

from core.system.config.magic_numbers import (
    batch_value,
    learning_rate,
    limit_value,
)

from .core_network import CoreNetwork
from .dictionary_layer import DictionaryLayer
from .multimodal.audio_encoder import AudioEncoder
from .multimodal.cross_modal_trainer import CrossModalTrainer
from .multimodal.image_encoder import ImageEncoder
from .output_anchor import anchored_decode, ResponseAnchorValidator
from .relation_classifier import RelationClassifier
from .snn.snn_core import SNNCore
from .snn.hormonal_modulator import HormonalModulator
from .step_decoder import StepDecoder

logger = logging.getLogger(__name__)


class ReflexLayer:
    def __init__(self, max_cache: int = 128, threshold: float = 0.5, min_pattern_len: int = 2):
        self.patterns: Dict[str, str] = OrderedDict()
        self.lru_cache: OrderedDict[str, str] = OrderedDict()
        self.max_cache = max_cache
        self.threshold = threshold
        self.min_pattern_len = min_pattern_len
        self._lock = threading.RLock()

    def process(self, input_text: str) -> Optional[str]:
        with self._lock:
            normalized = normalize_text(input_text).lower()

            if normalized in self.lru_cache:
                result = self.lru_cache.pop(normalized)
                self.lru_cache[normalized] = result
                return result

            for pattern, response in self.patterns.items():
                if len(pattern) < self.min_pattern_len:
                    continue
                if pattern in normalized:
                    if self.min_pattern_len >= limit_value("ai.ed3n_engine.reflex_min_match_len", 3) or len(pattern) >= limit_value("ai.ed3n_engine.reflex_min_match_len", 3):
                        self._add_to_cache(normalized, response)
                        return response
                    if self._is_word_boundary_match(normalized, pattern):
                        self._add_to_cache(normalized, response)
                        return response

        return None

    @staticmethod
    def _is_word_boundary_match(text: str, pattern: str) -> bool:
        idx = text.find(pattern)
        if idx == -1:
            return False
        before = idx == 0 or not text[idx - 1].isalnum()
        after = idx + len(pattern) >= len(text) or not text[idx + len(pattern)].isalnum()
        return before and after

    def add_pattern(self, pattern: str, response: str) -> None:
        with self._lock:
            self.patterns[normalize_text(pattern).lower().strip()] = response

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
        auto_load_presets: bool = True,
        auto_load_dictionaries: bool = False,
        telemetry: Optional[TelemetryCollector] = None,
        continuous_learning: Optional[Any] = None,
    ):
        self.reflex = reflex or ReflexLayer()
        self.telemetry = telemetry or TelemetryCollector()
        self.input_enricher = InputEnricher()
        self.dictionary = dictionary or DictionaryLayer()
        self.classifier = classifier or RelationClassifier(dictionary=self.dictionary)
        self.network = network or CoreNetwork(classifier=self.classifier)
        self._snn_network = snn_network
        self.modulator = modulator or HormonalModulator()
        self.snn_mode = snn_mode
        self._process_lock = threading.RLock()
        self._validator: Optional[ResponseAnchorValidator] = None
        self._step_decoder: Optional[StepDecoder] = None
        self.image_encoder: Optional[ImageEncoder] = None
        self.audio_encoder: Optional[AudioEncoder] = None
        self.cross_modal_trainer: Optional[CrossModalTrainer] = None
        self.multimodal_adapter: Optional[Any] = None
        self._continuous_learning = continuous_learning
        self._external_dicts_loaded = False
        self._last_confidence = 0.0
        self.enable_multimodal()
        if auto_load_presets:
            self.load_presets()
        if auto_load_dictionaries:
            self.load_external_dictionaries()
            self._external_dicts_loaded = True

    _shared_instance: Optional["ED3NEngine"] = None
    _shared_lock = threading.Lock()

    @classmethod
    def get_shared(cls) -> "ED3NEngine":
        """Get the process-wide shared ED3NEngine instance with presets loaded."""
        if cls._shared_instance is None:
            with cls._shared_lock:
                if cls._shared_instance is None:
                    cls._shared_instance = cls()
        return cls._shared_instance

    @property
    def validator(self) -> ResponseAnchorValidator:
        if self._validator is None:
            self._validator = ResponseAnchorValidator(dictionary=self.dictionary)
        return self._validator

    def process(
        self, input_text: str, context: Optional[Dict[str, Any]] = None, depth: str = "auto"
    ) -> str:
        # Lazy-load external dictionaries on first query if not already loaded
        if not self._external_dicts_loaded and self.dictionary is not None and len(self.dictionary.entries) < 100:
            try:
                count = self.load_external_dictionaries()
                if count > 0:
                    self._external_dicts_loaded = True
                    logger.info("Lazy-loaded %d external dictionary entries on first query", count)
            except Exception as e:
                logger.debug("Lazy dictionary load failed (non-critical): %s", e)

        with self._process_lock:
            output = self._process_unlocked(input_text, context, depth)
        self._maybe_learn(input_text, output, context or {})
        return output

    def warm_up(self) -> int:
        """Pre-load external dictionaries to avoid cold-start latency on first query.

        Can be called at application startup (e.g. lifespan, background task).
        Returns the number of entries loaded.
        """
        if self._external_dicts_loaded:
            return 0
        count = 0
        try:
            count = self.load_external_dictionaries()
            if count > 0:
                self._external_dicts_loaded = True
                logger.info("Warm-up: loaded %d external dictionary entries", count)
        except Exception as e:
            logger.debug("Warm-up dictionary load failed (non-critical): %s", e)
        return count

    def _maybe_learn(self, input_text: str, output_text: str, context: Dict[str, Any]) -> None:
        if self._continuous_learning is not None and output_text:
            self._continuous_learning.process_interaction(input_text, output_text, context)

    def _reflex_match(self, input_text: str) -> Optional[str]:
        return self.process_reflex(input_text)

    def _try_math_eval(self, text: str) -> Optional[str]:
        """Evaluate math expression using MathRippleEngine."""
        try:
            from ai.memory.math_ripple_engine import MathRippleEngine
            engine = MathRippleEngine()
            converted = engine.convert_chinese_math(text)
            if not converted:
                return None
            result, ripples = engine.compute(text)
            if result is None:
                return None
            # Format result
            if result == int(result):
                return f"{text.rstrip('？?！!。.')} = {int(result)}"
            return f"{text.rstrip('？?！!。.')} = {result:.2f}"
        except Exception:
            return None

    def _perform_encode(self, input_text: str) -> Tuple[List[str], bool]:
        _cache_key = (input_text.lower().strip(), self.dictionary._index_version)
        cache_hit = _cache_key in self.dictionary._encode_cache
        keys = self.dictionary.encode(input_text)
        return keys, cache_hit

    def _snn_process(self, keys: List[str], context: Optional[Dict[str, Any]], depth: str) -> object:
        if depth == "snn":
            was_snn = self.snn_mode
            self.snn_mode = True
            try:
                network_output = self.snn_network.forward(keys, context=context)
            finally:
                self.snn_mode = was_snn
        else:
            network_output = self.network.forward(keys, context=context)
        return network_output

    def _output_anchor_decode(self, network_output: object, keys: List[str], enriched=None) -> str:
        return anchored_decode(
            network_output=network_output,
            original_input_keys=keys,
            dictionary=self.dictionary,
            top_k_anchors=batch_value("ai.ed3n_engine.top_k_anchors", 3),
            top_k_network=batch_value("ai.ed3n_engine.top_k_network", 5),
            enriched=enriched,
        )

    def _process_unlocked(
        self, input_text: str, context: Optional[Dict[str, Any]] = None, depth: str = "auto"
    ) -> str:
        if not input_text or not isinstance(input_text, str):
            self._last_confidence = 0.0
            return ""

        query_id = f"{id(input_text)}_{time.time_ns()}"
        stages: Dict[str, float] = {}

        # Stage 1: Reflex
        t0 = time.perf_counter()
        reflex_result = self._reflex_match(input_text)
        stages["reflex"] = (time.perf_counter() - t0) * 1000

        if reflex_result is not None:
            self.telemetry.record_query(
                query_id=query_id,
                input_text=input_text,
                stages=stages,
                reflex_match=reflex_result,
                cache_hit=False,
                matched_keys=[],
                output_text=reflex_result,
                confidence=1.0,
                is_fallback=False,
            )
            self._last_confidence = 1.0
            return reflex_result

        if depth == "reflex":
            self.telemetry.record_query(
                query_id=query_id,
                input_text=input_text,
                stages=stages,
                reflex_match=None,
                cache_hit=False,
                matched_keys=[],
                output_text="",
                confidence=0.0,
                is_fallback=False,
            )
            self._last_confidence = 0.0
            return ""

        # Stage 1.5: Math evaluation
        t_math = time.perf_counter()
        math_result = self._try_math_eval(input_text)
        stages["math"] = (time.perf_counter() - t_math) * 1000
        if math_result is not None:
            self.telemetry.record_query(
                query_id=query_id,
                input_text=input_text,
                stages=stages,
                reflex_match=None,
                cache_hit=False,
                matched_keys=[],
                output_text=math_result,
                confidence=1.0,
                is_fallback=False,
            )
            self._last_confidence = 1.0
            return math_result

        # Stage 2: Encode
        FALLBACK_STR = self._fallback_str(input_text)
        t1 = time.perf_counter()
        keys, cache_hit = self._perform_encode(input_text)
        stages["encode"] = (time.perf_counter() - t1) * 1000

        if not keys:
            self.telemetry.record_query(
                query_id=query_id,
                input_text=input_text,
                stages=stages,
                reflex_match=None,
                cache_hit=cache_hit,
                matched_keys=[],
                output_text=FALLBACK_STR,
                confidence=0.0,
                is_fallback=True,
            )
            self._last_confidence = 0.0
            return FALLBACK_STR

        # Stage 2.5: Enrichment — algorithmic scoring of matched keys
        t_enr = time.perf_counter()
        enriched = self.input_enricher.enrich(input_text, keys, self.dictionary)
        stages["enrichment"] = (time.perf_counter() - t_enr) * 1000

        confidence = self._compute_confidence(keys)

        if depth == "shallow" or (depth == "auto" and not context):
            # Stage 3: Decode (shallow)
            t3 = time.perf_counter()
            decoded = self.dictionary.decode(keys, context)
            stages["decode"] = (time.perf_counter() - t3) * 1000
            output = decoded if decoded else FALLBACK_STR
            self.telemetry.record_query(
                query_id=query_id,
                input_text=input_text,
                stages=stages,
                reflex_match=None,
                cache_hit=cache_hit,
                matched_keys=keys,
                output_text=output,
                confidence=confidence,
                is_fallback=(not decoded),
            )
            self._last_confidence = confidence
            return output

        # Stage 3: Network forward
        t3 = time.perf_counter()
        network_output = self._snn_process(keys, context, depth)
        stages["network_forward"] = (time.perf_counter() - t3) * 1000

        # Override confidence with enriched score for deep path decisions
        enriched_conf = enriched.confidence

        # Stage 4: Decode (anchored)
        t4 = time.perf_counter()
        response = self._output_anchor_decode(network_output, keys, enriched=enriched)
        stages["decode"] = (time.perf_counter() - t4) * 1000

        if not response:
            fallback = self.dictionary.decode(keys, context) or FALLBACK_STR
            self.telemetry.record_query(
                query_id=query_id,
                input_text=input_text,
                stages=stages,
                reflex_match=None,
                cache_hit=cache_hit,
                matched_keys=keys,
                output_text=fallback,
                confidence=enriched_conf,
                is_fallback=True,
            )
            self._last_confidence = enriched_conf
            return fallback

        # Stage 5: Validate
        t5 = time.perf_counter()
        valid = self.validator.validate(response, anchored_keys=keys)
        stages["validate"] = (time.perf_counter() - t5) * 1000

        if not valid:
            fallback = self.dictionary.decode(keys, context)
            output = fallback or response
            self.telemetry.record_query(
                query_id=query_id,
                input_text=input_text,
                stages=stages,
                reflex_match=None,
                cache_hit=cache_hit,
                matched_keys=keys,
                output_text=output,
                confidence=enriched_conf,
                is_fallback=True,
            )
            self._last_confidence = enriched_conf
            return output

        # Stage 6: Cycling — iterative refinement if confidence is low
        MAX_CYCLES = 3
        CONFIDENCE_THRESHOLD = 0.7
        current_output = response
        current_confidence = enriched_conf

        for cycle in range(MAX_CYCLES):
            if current_confidence >= CONFIDENCE_THRESHOLD:
                break

            # Re-encode with previous output as additional context
            cycle_context = dict(context) if context else {}
            cycle_context["previous_output"] = current_output
            cycle_context["cycle"] = cycle + 1

            # Re-run network forward with enriched context
            cycle_network = self._snn_process(keys, cycle_context, depth)
            cycle_response = self._output_anchor_decode(cycle_network, keys, enriched=enriched)

            if cycle_response:
                cycle_valid = self.validator.validate(cycle_response, anchored_keys=keys)
                if cycle_valid:
                    cycle_enriched = self.input_enricher.enrich(input_text, keys, self.dictionary)
                    cycle_conf = cycle_enriched.confidence
                    if cycle_conf > current_confidence:
                        current_output = cycle_response
                        current_confidence = cycle_conf

        self.telemetry.record_query(
            query_id=query_id,
            input_text=input_text,
            stages=stages,
            reflex_match=None,
            cache_hit=cache_hit,
            matched_keys=keys,
            output_text=current_output,
            confidence=current_confidence,
            is_fallback=False,
        )
        self._last_confidence = current_confidence
        return current_output

    @staticmethod
    def _fallback_str(text: str) -> str:
        """Return language-appropriate fallback message."""
        if is_english_dominant(text):
            return "Sorry, I didn't understand what you meant."
        return "抱歉，我没理解你的意思。"

    def _compute_confidence(self, keys: List[str]) -> float:
        if not keys:
            return 0.0
        confidences = []
        for k in keys:
            entry = self.dictionary.entries.get(k)
            if entry is not None:
                confidences.append(entry.confidence)
        if not confidences:
            return 0.0
        return round(sum(confidences) / len(confidences), 4)

    def process_reflex(self, input_text: str) -> Optional[str]:
        return self.reflex.process(input_text)

    def process_shallow(
        self, input_text: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        if not input_text:
            return self._fallback_str(input_text)
        keys = self.dictionary.encode(input_text)
        if not keys:
            return self._fallback_str(input_text)
        decoded = self.dictionary.decode(keys, context)
        return decoded if decoded else self._fallback_str(input_text)

    @property
    def snn_network(self) -> SNNCore:
        if self._snn_network is None:
            self._snn_network = SNNCore(classifier=self.classifier)
            self._snn_network.connect_modulator(self.modulator)
        return self._snn_network

    def process_deep(
        self, input_text: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        if not input_text:
            return self._fallback_str(input_text)
        keys = self.dictionary.encode(input_text)
        if not keys:
            return self._fallback_str(input_text)

        if self.snn_mode:
            network_output = self.snn_network.forward(keys, context=context)
        else:
            network_output = self.network.forward(keys, context=context)

        response = anchored_decode(
            network_output=network_output,
            original_input_keys=keys,
            dictionary=self.dictionary,
            top_k_anchors=batch_value("ai.ed3n_engine.top_k_anchors", 3),
            top_k_network=batch_value("ai.ed3n_engine.top_k_network", 5),
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
        with self._process_lock:
            was_snn = self.snn_mode
            self.snn_mode = True
            try:
                return self.process_deep(input_text, context)
            finally:
                self.snn_mode = was_snn

    def enable_multimodal(self, enable_image=True, enable_audio=True) -> None:
        if not hasattr(self.dictionary, "modality_encoders"):
            logger.warning("Dictionary missing modality_encoders; cannot enable multimodal")
            return
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

    def set_multimodal_adapter(self, adapter: Any) -> None:
        self.multimodal_adapter = adapter
        logger.info("MultimodalED3NAdapter set on ED3NEngine")

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

        # Multimodal RAG: retrieve related entries via MultimodalED3NAdapter
        if self.multimodal_adapter is not None:
            try:
                rag_entries = []
                if image_data:
                    rag_entries = self.multimodal_adapter.retrieve_multimodal(
                        image_data=image_data, top_k=3
                    )
                elif audio_data:
                    rag_entries = self.multimodal_adapter.retrieve_multimodal(
                        audio_data=audio_data, top_k=3
                    )
                for entry in rag_entries:
                    key = entry.get("key", "")
                    if key and key not in combined_keys:
                        combined_keys.insert(0, key)
            except Exception as e:
                logger.debug("Multimodal RAG retrieval failed (non-critical): %s", e)

        if not combined_keys:
            return self._fallback_str(text or "")

        if self.cross_modal_trainer:
            for tk in text_keys or [""]:
                ik = image_keys[0] if image_keys else None
                ak = audio_keys[0] if audio_keys else None
                if tk:
                    self.cross_modal_trainer.record_co_occurrence(tk, ik, ak)

        if depth == "shallow" or (depth == "auto" and not context and not text):
            decoded = self.dictionary.decode(combined_keys, context)
            return decoded or self._fallback_str(text or "")

        if self.snn_mode:
            network_output = self.snn_network.forward(combined_keys, context=context)
        else:
            network_output = self.network.forward(combined_keys, context=context)

        response = anchored_decode(
            network_output=network_output,
            original_input_keys=combined_keys,
            dictionary=self.dictionary,
            top_k_anchors=batch_value("ai.ed3n_engine.top_k_anchors", 3),
            top_k_network=batch_value("ai.ed3n_engine.top_k_network", 5),
        )

        if not response:
            return self.dictionary.decode(combined_keys, context) or "抱歉，我没理解你的意思。"

        if not self.validator.validate(response, anchored_keys=combined_keys):
            fallback = self.dictionary.decode(combined_keys, context)
            return fallback or response

        return response

    @property
    def step_decoder(self) -> StepDecoder:
        if self._step_decoder is None:
            self._step_decoder = StepDecoder(
                dictionary=self.dictionary, network=self.network
            )
        return self._step_decoder

    def generate(
        self,
        input_text: str,
        temperature: Optional[float] = None,
        max_length: Optional[int] = None,
    ) -> str:
        with self._process_lock:
            if not input_text or not isinstance(input_text, str):
                return ""

            reflex_result = self.process_reflex(input_text)
            if reflex_result is not None:
                return reflex_result

            decoder = self.step_decoder
            if max_length is not None:
                old = decoder.max_length
                decoder.max_length = max_length
                try:
                    return decoder.generate_text(input_text, temperature)
                finally:
                    decoder.max_length = old
            return decoder.generate_text(input_text, temperature)

    def learn_reflex(self, pattern: str, response: str) -> None:
        self.reflex.add_pattern(pattern, response)

    def save(self, path: str) -> None:
        """Save full ED3N engine state."""
        import json
        import os

        state = {
            "snn_mode": self.snn_mode,
            "reflex_threshold": self.reflex.threshold,
            "reflex_patterns": list(self.reflex.patterns.items()),
            "network": self.network.to_dict(),
        }
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        dict_path = path.replace(".json", "_dictionary.json")
        self.dictionary.export_to_json(dict_path)
        if self._continuous_learning is not None:
            cl_path = path.replace(".json", "_continuous_learning.json")
            self._continuous_learning.save(cl_path)
        logger.info("ED3NEngine saved to %s", path)

    def load(self, path: str) -> None:
        """Load full ED3N engine state."""
        import json
        import os

        self.load_presets()
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error("ED3NEngine: failed to load checkpoint %s: %s", path, e)
            return
        self.snn_mode = state.get("snn_mode", False)
        if "reflex_threshold" in state:
            self.reflex.threshold = state["reflex_threshold"]
        if "reflex_patterns" in state:
            self.reflex.patterns.clear()
            for pattern, response in state["reflex_patterns"]:
                self.reflex.patterns[pattern] = response
            logger.info("Loaded %d reflex patterns from checkpoint.", len(state["reflex_patterns"]))
        if "network" in state:
            from ai.ed3n.core_network import CoreNetwork
            self.network = CoreNetwork.from_dict(state["network"], classifier=self.classifier)
            logger.info("Loaded CoreNetwork from checkpoint.")
        dict_path = path.replace(".json", "_dictionary.json")
        if os.path.exists(dict_path):
            self.dictionary.import_from_json(dict_path)
        if self._continuous_learning is not None:
            cl_path = path.replace(".json", "_continuous_learning.json")
            if os.path.exists(cl_path):
                self._continuous_learning = type(self._continuous_learning).load(
                    cl_path, self, None
                )
        logger.info("ED3NEngine loaded from %s", path)

    def train(
        self,
        examples: List[Any],
        epochs: int = batch_value("ai.ed3n_engine.train_epochs", 5),
        lr: float = learning_rate("ai.ed3n_engine.train_lr", 0.01),
        dictionary_epochs: int = batch_value("ai.ed3n_engine.dictionary_epochs", 3),
        network_epochs: int = batch_value("ai.ed3n_engine.network_epochs", 3),
    ) -> Any:
        """High-level training API. Accepts list of dicts with 'input', 'output', 'context'."""
        from .ed3n_trainer import ED3NTrainer
        from .training_types import (
            TrainingBatch,
            TrainingExample,
        )

        trainer = ED3NTrainer(self)
        training_examples = []
        for ex in examples:
            if isinstance(ex, dict):
                training_examples.append(
                    TrainingExample(
                        input_text=ex.get("input", ex.get("user_text", "")),
                        expected_output=ex.get("output", ex.get("response_text", "")),
                        input_keys=ex.get("input_keys", []),
                        output_keys=ex.get("output_keys", []),
                        relation_pairs=ex.get("relation_pairs", []),
                        confidence=ex.get("confidence", 0.8),
                        metadata=ex.get("context", ex.get("conversation_id", {})),
                    )
                )
            else:
                training_examples.append(ex)

        batch = TrainingBatch(
            examples=training_examples,
            batch_id=f"train_{int(__import__('time').time())}",
        )
        metrics = trainer.train_step(batch)
        return metrics

    def load_presets(self) -> None:
        self.reflex.load_presets()
        self.dictionary.load_preset_responses()
        self.network.sync_from_dictionary(self.dictionary)
        logger.info("ED3NEngine loaded all presets.")

    def load_presets_from_config(self, config_dir: Optional[str] = None) -> None:
        """Load all presets from JSON config files instead of hardcoded Python."""
        import json, os
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), "config")

        # Load reflex patterns from JSON
        reflex_patterns = {}
        for fname in os.listdir(config_dir):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(config_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "reflex_patterns" in data:
                for pattern, response in data["reflex_patterns"].items():
                    self.reflex.add_pattern(pattern, response)

        # Load dictionary entries from JSON
        loaded = self.dictionary.load_preset_responses_from_dir(config_dir)
        logger.info("ED3NEngine loaded %d entries and %d reflex patterns from config dir: %s",
                    loaded, len(self.reflex.patterns), config_dir)

    @staticmethod
    def _find_project_root() -> str:
        """Find project root by walking up until a unique marker file is found."""
        current = os.path.dirname(os.path.abspath(__file__))
        for _ in range(10):
            # .gitignore is the most reliable marker (unique to project root)
            if os.path.exists(os.path.join(current, ".gitignore")):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        # Fallback: look for pyproject.toml
        current = os.path.dirname(os.path.abspath(__file__))
        for _ in range(10):
            if os.path.exists(os.path.join(current, "pyproject.toml")):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return os.getcwd()

    def load_external_dictionaries(self, dict_dir: Optional[str] = None) -> int:
        """Load external dictionary entries (CEDICT/JMdict/WordNet) into DictionaryLayer.

        Uses ``bulk_add_entries`` for performance and calls
        ``_rebuild_index`` only once after all files are loaded.

        Args:
            dict_dir: Path to directory containing dictionary JSON files.
                      Defaults to ``data/dictionaries/`` relative to project root.

        Returns:
            Total number of imported entries.
        """
        if dict_dir is None:
            base = os.environ.get("PROJECT_ROOT", self._find_project_root())
            dict_dir = os.path.join(base, "data", "dictionaries")
        total = 0
        # Use orjson for ~3-5x faster JSON parsing when available
        try:
            import orjson as _fast_json
            def _load_json(fpath):
                with open(fpath, "rb") as f:
                    return _fast_json.loads(f.read())
        except ImportError:
            def _load_json(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    return json.load(f)
        for fname in ("cedict.json", "jmdict.json", "wordnet.json"):
            fpath = os.path.join(dict_dir, fname)
            if not os.path.exists(fpath):
                continue
            try:
                data = _load_json(fpath)
                entries_data = data.get("entries", [])
                count = self.dictionary.bulk_add_entries(entries_data)
                total += count
                logger.info("Loaded %d entries from %s", count, fpath)
            except Exception as e:
                logger.warning("Failed to load %s: %s", fpath, e)
        if total > 0:
            self.dictionary._rebuild_index()
            self.network.sync_from_dictionary(self.dictionary)
            self._external_dicts_loaded = True
        logger.info("ED3NEngine loaded %d external dictionary entries total.", total)
        return total

    def get_snn_stats(self) -> Dict[str, Any]:
        if self._snn_network is None:
            return {"snn_mode": self.snn_mode, "snn_initialized": False}
        return {
            "snn_mode": self.snn_mode,
            "snn_initialized": True,
            "sparsity": self._snn_network.get_sparsity_report(),
            "modulation": self.modulator.get_profile_summary(),
        }
