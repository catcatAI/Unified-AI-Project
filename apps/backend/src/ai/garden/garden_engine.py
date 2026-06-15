# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [B] [L2]
# =============================================================================
"""
GARDEN GARDENEngine — Unified reasoning engine for the GARDEN-1G model tier.

Three-stage pipeline:
  1. VectorDictionary.encode(text)  -> concept keys (via cosine similarity)
  2. TensorSNNCore.forward(keys)    -> activated output keys (LIF multi-step)
  3. Anchored decode                -> human-readable response

Additional capabilities:
  - Hormonal modulation passthrough (cortisol/serotonin affect SNN threshold)
  - Continuous learning: learn_from_interaction() grows dictionary and runs Hebbian update
  - Save/load full engine state (dictionary JSON + SNN .pt checkpoint)
  - CLI-friendly stats() method
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from core.system.config.magic_numbers import (
    cache_value,
    confidence_value,
    learning_rate,
    limit_value,
    threshold_value,
)

from .dictionary import VectorDictionary
from .snn_core import TensorSNNCore
from .vector_decoder import VectorDecoder

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reflex layer (fast pattern table, same design as ED3N)
# ---------------------------------------------------------------------------

class _ReflexTable:
    """O(1) exact-pattern lookup with LRU cache. Triggers before vector encoding."""

    PRESETS: Dict[str, str] = {
        "你好": "你好！很高兴见到你！",
        "早上好": "早上好！祝你今天愉快！",
        "晚上好": "晚上好！祝你今晚愉快！",
        "欢迎": "欢迎！很高兴你能来！",
        "再见": "再见！期待下次见面！",
        "谢谢": "不客气！很高兴能帮到你！",
        "对不起": "没关系，别放在心上。",
        "没关系": "嗯，谢谢你理解！",
        "开心": "开心真好！希望你一直保持好心情！",
        "难过": "别难过，我在这里陪着你。",
        "烦恼": "别烦恼了，我们一起想办法。",
        "在忙吗": "不忙，随时为你服务！",
        "名字": "我是Angela AI，很高兴认识你！",
        "hello": "Hello! Nice to meet you!",
        "hi": "Hi there! How can I help you today?",
        "good morning": "Good morning! Hope you have a great day!",
        "goodbye": "Goodbye! Take care!",
        "thank you": "You're welcome! Happy to help!",
        "help": "I'm here to help! What do you need?",
    }

    def __init__(self, max_cache: Optional[int] = None):
        max_cache = max_cache if max_cache is not None else cache_value("ai.garden.reflex.max_cache", 256)
        self.patterns: Dict[str, str] = dict(self.PRESETS)
        self._cache: Dict[str, str] = {}
        self._max_cache = max_cache

    def match(self, text: str) -> Optional[str]:
        lower = text.strip().lower()
        if lower in self._cache:
            return self._cache[lower]
        for pattern, response in self.patterns.items():
            if pattern in lower:
                if len(self._cache) >= self._max_cache:
                    oldest = next(iter(self._cache))
                    del self._cache[oldest]
                self._cache[lower] = response
                return response
        return None

    def add(self, pattern: str, response: str) -> None:
        self.patterns[pattern.lower().strip()] = response


# ---------------------------------------------------------------------------
# Output anchoring (prevent semantic drift)
# ---------------------------------------------------------------------------

def _anchored_decode(
    network_output: Dict[str, float],
    input_keys: List[str],
    dictionary: VectorDictionary,
    top_k: Optional[int] = None,
) -> str:
    """
    Combine highest-scored network output keys with top anchor input keys,
    then decode to text.  Anchoring prevents the response from drifting
    entirely away from the user's original intent.
    """
    top_k = top_k if top_k is not None else limit_value("ai.garden.decode.top_k", 6)
    if not network_output and not input_keys:
        return ""

    # Sort network output by score, take top_k
    sorted_output = sorted(network_output.items(), key=lambda x: x[1], reverse=True)
    output_keys = [k for k, _ in sorted_output[:top_k]]

    # Anchors = top-3 input keys (preserve intent)
    anchors = input_keys[:limit_value("ai.garden.decode.anchor_keys", 3)]

    # Merge: anchors first, then new output keys (deduplicated)
    seen: set = set(anchors)
    combined = list(anchors)
    for k in output_keys:
        if k not in seen:
            seen.add(k)
            combined.append(k)

    return dictionary.decode(combined[:top_k])


# ---------------------------------------------------------------------------
# GARDENEngine
# ---------------------------------------------------------------------------

class GARDENEngine:
    """
    GARDEN-1G unified reasoning engine.

    Instantiate and call process(text) to get a response.
    All components (reflex table, vector dictionary, SNN core) are lazy-initialised
    on first use so import time stays fast.

    Example:
        engine = GARDENEngine()
        engine.load_presets()
        reply = engine.process("你好，今天心情怎么样？")
        print(reply)
    """

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        snn_timesteps: Optional[int] = None,
        device: str = "cpu",
        compatibility_mode: bool = True,
    ):
        top_k = top_k if top_k is not None else limit_value("ai.garden.engine.top_k", 8)
        similarity_threshold = similarity_threshold if similarity_threshold is not None else threshold_value("ai.garden.engine.similarity_threshold", 0.30)
        snn_timesteps = snn_timesteps if snn_timesteps is not None else limit_value("ai.garden.engine.snn_timesteps", 6)
        self.model_name = model_name
        self.device = device

        self.reflex = _ReflexTable()
        self.dictionary = VectorDictionary(
            model_name=model_name,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            device=device,
            compatibility_mode=compatibility_mode,
        )
        self.snn = TensorSNNCore(timesteps=snn_timesteps, device=device)

        self._presets_loaded = False
        self._query_count = 0
        self._learn_count = 0

    # ------------------------------------------------------------------
    # Preset / init
    # ------------------------------------------------------------------

    def load_presets(self) -> None:
        """Load built-in dictionary presets and wire their relations into the SNN.

        Loads in this order:
          1. Hard-coded preset concepts (from dictionary.load_presets())
          2. Config JSON files from the config/ directory (if they exist)
          3. Wire all dictionary relations into the SNN weight matrix
        """
        self.dictionary.load_presets()

        # Also load from config JSON files
        config_dir = os.path.join(os.path.dirname(__file__), "config")
        if os.path.isdir(config_dir):
            import json
            loaded_from_config = 0
            for fname in sorted(os.listdir(config_dir)):
                if not fname.endswith(".json"):
                    continue
                fpath = os.path.join(config_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Load reflex patterns
                    for pattern, response in data.get("reflex_patterns", {}).items():
                        self.reflex.add(pattern, response)
                    # Load dictionary entries
                    for entry_data in data.get("dictionary_entries", []):
                        key = entry_data.get("key")
                        if key and key not in self.dictionary.entries:
                            self.dictionary.add_entry(
                                key=key,
                                surface_forms=entry_data.get("surface_forms", {}),
                                relations=entry_data.get("relations"),
                                confidence=entry_data.get("confidence", confidence_value("ai.garden.engine.preset_confidence", 0.9)),
                            )
                            loaded_from_config += 1
                except Exception as e:
                    logger.warning("GARDEN: failed to load config %s: %s", fname, e)
            if loaded_from_config > 0:
                logger.info("GARDEN: loaded %d additional concepts from config/", loaded_from_config)

        # Collect all unique keys (entries + relation targets) for pre-allocation
        all_keys: set = set(self.dictionary.entries.keys())
        for entry in self.dictionary.entries.values():
            for targets in entry.relations.values():
                all_keys.update(targets)
        self.snn._pre_allocate(list(all_keys))

        # Wire dictionary relations into the SNN weight matrix
        for entry in self.dictionary.entries.values():
            self.snn.add_relations_from_entry(entry.key, entry.relations)
            self.snn._register_key(entry.key)
        self._presets_loaded = True
        logger.info(
            "GARDEN: presets loaded — %d concepts, %d SNN vocab",
            len(self.dictionary.entries),
            self.snn.vocab_size,
        )

    # ------------------------------------------------------------------
    # Core processing pipeline
    # ------------------------------------------------------------------

    def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Full GARDEN inference pipeline:
          emotion detect → reflex → multi-step check → vector encode → SNN forward → anchored decode
        """
        if not text or not isinstance(text, str):
            return ""

        self._query_count += 1

        # Stage 0: Emotion detection + hormonal modulation
        emotion = self._detect_emotion(text)
        self._adjust_hormones(emotion)

        # Stage 1: Reflex (fast pattern match)
        reflex_hit = self.reflex.match(text)
        if reflex_hit is not None:
            return reflex_hit

        # Stage 2: Multi-step detection
        if self._is_multi_step(text):
            return self._process_multi_step(text, context)

        # Stage 3: Vector encode
        if not self._presets_loaded:
            self.load_presets()

        input_keys = self.dictionary.encode(text)

        if not input_keys:
            return "抱歉，我暂时无法理解你的意思。"

        # Stage 4: SNN forward
        network_output = self.snn.forward(input_keys, context=context)

        # Stage 5: Anchored decode
        response = _anchored_decode(network_output, input_keys, self.dictionary)

        if not response:
            # Fallback: decode input keys directly
            response = self.dictionary.decode(input_keys[:limit_value("ai.garden.engine.fallback_decode_keys", 4)])

        if not response:
            return "抱歉，我暂时无法理解你的意思。"

        return response

    # ------------------------------------------------------------------
    # Multi-step reasoning (Phase 4.3)
    # ------------------------------------------------------------------

    _MULTI_STEP_MARKERS = ["然后", "然後", "接著", "接着", "之後", "之后", "再", "and then", "after that"]

    def _is_multi_step(self, text: str) -> bool:
        """Detect if the input contains multiple sequential steps."""
        lower = text.lower()
        return any(m in lower for m in self._MULTI_STEP_MARKERS)

    def _process_multi_step(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Split multi-step input and process each step sequentially."""
        import re
        pattern = "|".join(re.escape(m) for m in self._MULTI_STEP_MARKERS)
        steps = re.split(pattern, text, flags=re.IGNORECASE)
        results = []
        for step in steps:
            step = step.strip()
            if not step:
                continue
            # Process each step through the single-step pipeline
            result = self._single_step_process(step, context)
            if result:
                results.append(result)
        return "\n".join(results) if results else "抱歉，我无法理解这些步骤。"

    def _single_step_process(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a single step through the GARDEN pipeline."""
        # Reflex check
        reflex_hit = self.reflex.match(text)
        if reflex_hit is not None:
            return reflex_hit

        # Vector encode + SNN + decode
        if not self._presets_loaded:
            self.load_presets()

        input_keys = self.dictionary.encode(text)
        if not input_keys:
            return ""

        network_output = self.snn.forward(input_keys, context=context)
        response = _anchored_decode(network_output, input_keys, self.dictionary)

        if not response:
            response = self.dictionary.decode(input_keys[:limit_value("ai.garden.engine.fallback_decode_keys", 4)])

        return response or ""

    # ------------------------------------------------------------------
    # Emotion detection + hormonal modulation (Phase 4.4)
    # ------------------------------------------------------------------

    _EMOTION_KEYWORDS: Dict[str, List[str]] = {
        "happy": ["开心", "高兴", "太好了", "happy", "great", "好开心", "好高兴"],
        "sad": ["难过", "伤心", "糟糕", "sad", "bad", "好难过", "好伤心"],
        "angry": ["生气", "气死", "烦", "angry", "mad", "好生气"],
        "anxious": ["担心", "紧张", "害怕", "worried", "anxious", "好担心"],
    }

    _HORMONE_ADJUSTMENTS: Dict[str, Dict[str, float]] = {
        "happy": {"serotonin": 0.8, "dopamine": 0.7},
        "sad": {"serotonin": 0.3, "cortisol": 0.6},
        "angry": {"cortisol": 0.8, "adrenaline": 0.7},
        "anxious": {"cortisol": 0.7, "adrenaline": 0.6},
        "neutral": {"serotonin": 0.5, "cortisol": 0.3},
    }

    def _detect_emotion(self, text: str) -> str:
        """Detect the dominant emotion in user input."""
        lower = text.lower()
        for emotion, keywords in self._EMOTION_KEYWORDS.items():
            if any(k in lower for k in keywords):
                return emotion
        return "neutral"

    def _adjust_hormones(self, emotion: str) -> None:
        """Adjust hormone levels based on detected emotion."""
        adjustments = self._HORMONE_ADJUSTMENTS.get(emotion, {})
        for hormone, level in adjustments.items():
            self.set_hormone(hormone, level)

    # ------------------------------------------------------------------
    # VectorDecoder (iterative generation)
    # ------------------------------------------------------------------

    @property
    def vector_decoder(self) -> VectorDecoder:
        if not hasattr(self, "_vector_decoder"):
            self._vector_decoder = VectorDecoder(
                dictionary=self.dictionary,
                snn=self.snn,
            )
        return self._vector_decoder

    def generate(
        self,
        input_text: str,
        temperature: Optional[float] = None,
        max_steps: Optional[int] = None,
    ) -> str:
        return self.vector_decoder.generate_text(
            input_text, temperature=temperature, max_steps=max_steps
        )

    # ------------------------------------------------------------------
    # Continuous learning
    # ------------------------------------------------------------------

    def learn_from_interaction(
        self,
        user_text: str,
        response_text: str,
        confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Online learning from a single interaction.
        1. Detect and grow new concepts in the dictionary
        2. Run Hebbian weight update in SNN between input and response keys
        Returns a summary dict.
        """
        confidence = confidence if confidence is not None else confidence_value("ai.garden.engine.learn_confidence", 0.7)
        if not self._presets_loaded:
            self.load_presets()

        self._learn_count += 1

        # Grow dictionary with any novel concepts from user text
        new_keys: List[str] = []
        tokens = [t for t in user_text.lower().split() if len(t) >= limit_value("ai.garden.engine.min_token_length", 3)]
        for token in tokens:
            existing = self.dictionary._find_similar_key(token, threshold=threshold_value("ai.garden.engine.dedup_similarity", 0.90))
            if not existing and confidence >= self.dictionary.growth_threshold:
                new_key = self.dictionary.grow(token, token, confidence=confidence)
                if new_key:
                    self.snn._register_key(new_key)
                    new_keys.append(new_key)

        # Compute input/output keys
        input_keys  = self.dictionary.encode(user_text)
        output_keys = self.dictionary.encode(response_text)

        # Hebbian update
        delta = 0.0
        if input_keys and output_keys:
            delta = self.snn.hebbian_update(
                input_keys, output_keys, lr=learning_rate("ai.garden.engine.hebbian_lr", 0.05), target_strength=confidence_value("ai.garden.engine.hebbian_target_strength", 0.7)
            )

        return {
            "interaction": self._learn_count,
            "new_concepts": new_keys,
            "input_keys": input_keys,
            "output_keys": output_keys,
            "hebbian_delta": round(delta, 6),
        }

    # ------------------------------------------------------------------
    # Hormonal modulation passthrough
    # ------------------------------------------------------------------

    def set_hormone(self, name: str, value: float) -> None:
        """Update a hormone level that modulates SNN spike threshold."""
        self.snn.modulator.set_hormone(name, value)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        dict_stats = self.dictionary.get_stats()
        snn_stats  = self.snn.get_stats()
        return {
            "tier": "GARDEN-1G (Lightweight Local)",
            "query_count": self._query_count,
            "learn_count": self._learn_count,
            "presets_loaded": self._presets_loaded,
            "reflex_patterns": len(self.reflex.patterns),
            "dictionary": dict_stats,
            "snn": snn_stats,
        }

    # ------------------------------------------------------------------
    # Save / load
    # ------------------------------------------------------------------

    def save(self, directory: str) -> None:
        """
        Persist the full engine state to a directory:
          - dictionary.json  — all concept entries
          - snn.pt           — SNN weight matrix + key registry
        """
        os.makedirs(directory, exist_ok=True)
        self.dictionary.export_to_json(os.path.join(directory, "dictionary.json"))
        self.snn.save(os.path.join(directory, "snn.pt"))
        # Save engine metadata
        meta = {
            "tier": "GARDEN-1G",
            "model_name": self.model_name,
            "query_count": self._query_count,
            "learn_count": self._learn_count,
        }
        with open(os.path.join(directory, "engine_meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        logger.info("GARDEN: engine saved to %s", directory)

    def load(self, directory: str) -> None:
        """Load full engine state from a previously saved directory."""
        dict_path = os.path.join(directory, "dictionary.json")
        snn_path  = os.path.join(directory, "snn.pt")
        meta_path = os.path.join(directory, "engine_meta.json")

        if os.path.exists(dict_path):
            self.dictionary.import_from_json(dict_path)
        if os.path.exists(snn_path):
            self.snn.load(snn_path)
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self._query_count = meta.get("query_count", 0)
            self._learn_count = meta.get("learn_count", 0)
        self._presets_loaded = True
        logger.info("GARDEN: engine loaded from %s", directory)
