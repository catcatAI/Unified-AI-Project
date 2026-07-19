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
import re
from typing import Any, Dict, List, Optional

from ai.core.unicode_utils import is_english_dominant
from core.system.config.magic_numbers import (
    cache_value,
    confidence_value,
    learning_rate,
    limit_value,
    threshold_value,
)
from core.utils import any_keyword

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
        max_cache = (
            max_cache if max_cache is not None else cache_value("ai.garden.reflex.max_cache", 256)
        )
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
    anchors = input_keys[: limit_value("ai.garden.decode.anchor_keys", 3)]

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
        compatibility_mode: bool = False,
    ):
        top_k = top_k if top_k is not None else limit_value("ai.garden.engine.top_k", 8)
        similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else threshold_value("ai.garden.engine.similarity_threshold", 0.30)
        )
        snn_timesteps = (
            snn_timesteps
            if snn_timesteps is not None
            else limit_value("ai.garden.engine.snn_timesteps", 6)
        )
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
        self._learning_enabled = True
        self._last_confidence = 0.0

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
        if self._presets_loaded:
            return
        self.dictionary.load_presets()

        # Also load from config JSON files
        config_dir = os.path.join(os.path.dirname(__file__), "config")
        if os.path.isdir(config_dir):
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
                                confidence=entry_data.get(
                                    "confidence",
                                    confidence_value("ai.garden.engine.preset_confidence", 0.9),
                                ),
                            )
                            loaded_from_config += 1
                except Exception as e:
                    logger.warning("GARDEN: failed to load config %s: %s", fname, e)
            if loaded_from_config > 0:
                logger.info(
                    "GARDEN: loaded %d additional concepts from config/", loaded_from_config
                )

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
            self._last_confidence = 0.0
            return ""

        self._query_count += 1

        # Stage 0: Emotion detection + hormonal modulation
        emotion = self._detect_emotion(text)
        self._adjust_hormones(emotion)

        # Stage 1: High-precision structural answers (math + symbolic reasoning).
        # These run BEFORE the reflex stage so that structurally-answerable
        # questions (e.g. "Which is heavier: 1kg of feathers or 1kg of steel?")
        # are not hijacked by an over-broad reflexive greeting pattern.
        math_result = self._try_math_eval(text)
        if math_result is not None:
            self._last_confidence = 0.85
            return math_result

        reasoning_result = self._try_reasoning(text)
        if reasoning_result is not None:
            self._last_confidence = 0.85
            return reasoning_result

        # Stage 1.6b: Relational-chain reasoning (offline graph derivation).
        # Catches relational comparison questions the symbolic reasoner's regex
        # patterns miss (novel comparators / longer chains / paraphrases) by
        # building a transient directed graph from the stated comparisons and
        # resolving it via transitive closure. No LLM or torch dependency.
        chain_result = self._try_chain_reasoning(text)
        if chain_result is not None:
            self._last_confidence = 0.85
            return chain_result

        # Stage 2: Reflex (fast pattern match) — greetings / canned replies.
        reflex_hit = self.reflex.match(text)
        if reflex_hit is not None:
            self._last_confidence = 0.95
            return reflex_hit

        # Stage 3: Knowledge retrieval (deterministic KB, like math)
        kb_result = self._try_knowledge(text)
        if kb_result is not None:
            self._last_confidence = 0.80
            return kb_result

        # Stage 4: Multi-step detection
        if self._is_multi_step(text):
            self._last_confidence = 0.70
            return self._process_multi_step(text, context)

        # Stage 5: Vector encode
        if not self._presets_loaded:
            self.load_presets()

        input_keys = self.dictionary.encode(text)

        if not input_keys:
            self._last_confidence = 0.0
            return self._fallback_str(text)

        # Stage 6: SNN forward
        network_output = self.snn.forward(input_keys, context=context)

        # Stage 7: Anchored decode
        response = _anchored_decode(network_output, input_keys, self.dictionary)

        if not response:
            # Fallback: decode input keys directly
            response = self.dictionary.decode(
                input_keys[: limit_value("ai.garden.engine.fallback_decode_keys", 4)]
            )

        if not response:
            self._last_confidence = 0.0
            return self._fallback_str(text)

        # Stage 6: Cycling — iterative refinement if response is weak
        MAX_CYCLES = getattr(self, "max_cycles", 3)
        MIN_RESPONSE_LEN = 5
        current_output = response
        cycles_used = 0

        for cycle in range(MAX_CYCLES):
            if len(current_output) >= MIN_RESPONSE_LEN:
                break
            cycles_used += 1

            # Re-run with previous output as context
            cycle_context = dict(context) if context else {}
            cycle_context["previous_output"] = current_output
            cycle_context["cycle"] = cycle + 1

            cycle_network = self.snn.forward(input_keys, context=cycle_context)
            cycle_response = _anchored_decode(cycle_network, input_keys, self.dictionary)

            if cycle_response and len(cycle_response) > len(current_output):
                current_output = cycle_response

        # Compute confidence: key coverage × response quality × cycle penalty
        key_ratio = min(1.0, len(input_keys) / limit_value("ai.garden.engine.top_k", 8))
        resp_quality = min(1.0, len(current_output) / 50.0)
        cycle_penalty = 1.0 - (cycles_used * 0.1)
        self._last_confidence = round(
            max(0.0, key_ratio * 0.5 + resp_quality * 0.3 + 0.2 * cycle_penalty), 3
        )

        return current_output

    # ------------------------------------------------------------------
    # Multi-step reasoning (Phase 4.3)
    # ------------------------------------------------------------------

    _MULTI_STEP_MARKERS = [
        "然后",
        "然後",
        "接著",
        "接着",
        "之後",
        "之后",
        "然后再",
        "然後再",
        "and then",
        "after that",
    ]

    def _is_multi_step(self, text: str) -> bool:
        """Detect if the input contains multiple sequential steps."""
        lower = text.lower()
        return any_keyword(lower, tuple(self._MULTI_STEP_MARKERS))

    def _process_multi_step(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Split multi-step input and process each step sequentially."""
        sorted_markers = sorted(self._MULTI_STEP_MARKERS, key=len, reverse=True)
        pattern = "|".join(re.escape(m) for m in sorted_markers)
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
        return "\n".join(results) if results else self._fallback_str(text)

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
            response = self.dictionary.decode(
                input_keys[: limit_value("ai.garden.engine.fallback_decode_keys", 4)]
            )

        return response or ""

    # ------------------------------------------------------------------
    # Emotion detection + hormonal modulation (Phase 4.4)
    # ------------------------------------------------------------------

    _EMOTION_KEYWORDS: Dict[str, List[str]] = {
        "happy": [
            "开心",
            "高兴",
            "太好了",
            "happy",
            "great",
            "好开心",
            "好高兴",
            "開心",
            "高興",
            "好開心",
            "好高興",
        ],
        "sad": [
            "难过",
            "伤心",
            "糟糕",
            "sad",
            "bad",
            "好难过",
            "好伤心",
            "難過",
            "傷心",
            "好難過",
            "好傷心",
        ],
        "angry": ["生气", "气死", "烦", "angry", "mad", "好生气", "生氣", "氣死", "好生氣"],
        "anxious": [
            "担心",
            "紧张",
            "害怕",
            "worried",
            "anxious",
            "好担心",
            "擔心",
            "緊張",
            "害怕",
            "好擔心",
        ],
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
            if any_keyword(lower, tuple(keywords)):
                return emotion
        return "neutral"

    def _adjust_hormones(self, emotion: str) -> None:
        """Adjust hormone levels based on detected emotion."""
        adjustments = self._HORMONE_ADJUSTMENTS.get(emotion, {})
        for hormone, level in adjustments.items():
            self.set_hormone(hormone, level)

    def _try_math_eval(self, text: str) -> Optional[str]:
        """Evaluate math via the dictionary-layer compute-routing hook.

        Math is delegated to MathVerifier (single source of truth) through
        VectorDictionary.route_math — GARDEN no longer computes arithmetic itself.
        """
        try:
            from ai.garden.dictionary import VectorDictionary

            return VectorDictionary.route_math(text)
        except Exception as e:
            logger.debug("GARDEN: math routing failed for %r: %s", text, e)
            return None

    def _try_knowledge(self, text: str) -> Optional[str]:
        """Answer simple factual questions via the curated knowledge base.

        Mirrors the math-routing design: trivial, high-certainty factual recall
        is delegated to ``ai.knowledge_base.route_knowledge`` instead of being
        squeezed through the vector/SNN pipeline (which would hallucinate).
        """
        try:
            from ai.knowledge_base import route_knowledge

            return route_knowledge(text)
        except Exception as e:
            logger.debug("GARDEN: knowledge routing failed for %r: %s", text, e)
            return None

    def _try_reasoning(self, text: str) -> Optional[str]:
        """Apply deterministic symbolic reasoning to structured questions.

        Delegates transitive / syllogism / calendar / quantity / mass-trick
        reasoning to ``ai.symbolic_reasoner.route_reasoning`` — a real,
        high-certainty capability (valid inference over stated premises).
        """
        try:
            from ai.symbolic_reasoner import route_reasoning

            return route_reasoning(text)
        except Exception as e:
            logger.debug("GARDEN: symbolic reasoning failed for %r: %s", text, e)
            return None

    def _try_chain_reasoning(self, text: str) -> Optional[str]:
        """Offline relational-chain reasoning via transitive closure.

        Delegates to the shared ``ai.reasoning.relational_chain`` resolver. It
        parses explicit comparison statements in the query, builds directed
        "greater-than" edges, and resolves the dominant/least entity. This
        complements the regex-based symbolic reasoner by handling novel
        comparators and paraphrases that the fixed patterns do not match.
        """
        try:
            from ai.reasoning.relational_chain import (
                parse_and_resolve_relational_chain,
                resolve_relational_chain,
            )

            return parse_and_resolve_relational_chain(text, resolver=resolve_relational_chain)
        except Exception as e:
            logger.debug("GARDEN: chain reasoning failed for %r: %s", text, e)
            return None

    # ------------------------------------------------------------------
    # VectorDecoder (iterative generation)
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_str(text: str) -> str:
        """Return language-appropriate fallback message."""
        if is_english_dominant(text):
            return "Sorry, I couldn't understand what you meant."
        return "抱歉，我暂时无法理解你的意思。"

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
        1. Detect and grow new concepts in the dictionary (from both user and response text)
        2. Run Hebbian weight update in SNN between input and response keys
        Returns a summary dict.
        """
        if not self._learning_enabled:
            return {
                "interaction": self._learn_count,
                "new_concepts": [],
                "input_keys": [],
                "output_keys": [],
                "hebbian_delta": 0.0,
            }

        confidence = (
            confidence
            if confidence is not None
            else confidence_value("ai.garden.engine.learn_confidence", 0.7)
        )
        if not self._presets_loaded:
            self.load_presets()

        self._learn_count += 1

        new_keys: List[str] = []

        # Grow dictionary with novel concepts from user text
        all_tokens = []
        for text in [user_text, response_text]:
            tokens = [
                t
                for t in text.lower().split()
                if len(t) >= limit_value("ai.garden.engine.min_token_length", 3)
            ]
            all_tokens.extend(tokens)

        # Clean punctuation from tokens
        import string

        cleaned_tokens = []
        for token in all_tokens:
            cleaned = token.strip(string.punctuation)
            if cleaned and len(cleaned) >= limit_value("ai.garden.engine.min_token_length", 3):
                cleaned_tokens.append(cleaned)

        # Batch grow - don't rebuild index until all tokens processed
        for token in cleaned_tokens:
            existing = self.dictionary._find_similar_key(
                token, threshold=threshold_value("ai.garden.engine.dedup_similarity", 0.90)
            )
            if not existing and confidence >= self.dictionary.growth_threshold:
                new_key = self.dictionary.grow(token, token, confidence=confidence)
                if new_key:
                    self.snn._register_key(new_key)
                    new_keys.append(new_key)

        # Only rebuild index ONCE after all grows, not per token
        if new_keys and self.dictionary._dirty:
            self.dictionary._rebuild_index()

        # Compute input/output keys
        input_keys = self.dictionary.encode(user_text)
        output_keys = self.dictionary.encode(response_text)

        # Hebbian update
        delta = 0.0
        if input_keys and output_keys:
            delta = self.snn.hebbian_update(
                input_keys,
                output_keys,
                lr=learning_rate("ai.garden.engine.hebbian_lr", 0.05),
                target_strength=confidence_value("ai.garden.engine.hebbian_target_strength", 0.7),
            )

        return {
            "interaction": self._learn_count,
            "new_concepts": new_keys,
            "input_keys": input_keys,
            "output_keys": output_keys,
            "hebbian_delta": round(delta, 6),
        }

    def learn_batch(
        self,
        samples: List[Dict[str, str]],
        confidence: Optional[float] = None,
        train_associations: bool = True,
    ) -> Dict[str, Any]:
        """
        Batch learning from multiple interactions.
        Grows all new concepts first, rebuilds index ONCE, then runs Hebbian updates.
        Much faster than calling learn_from_interaction() in a loop.

        Architectural rule: the SNN learns ASSOCIATIONS (relations between
        concepts), not KNOWLEDGE FACTS. When ``train_associations=False`` the
        Hebbian input->output mirror is skipped, so knowledge facts are stored
        in the dictionary only and are NOT baked into the neural weights (which
        would make the SNN a memorizing AI no different from a normal one).
        """
        if not self._learning_enabled or not samples:
            return {"interaction": self._learn_count, "new_concepts": 0, "samples_processed": 0}

        confidence = (
            confidence
            if confidence is not None
            else confidence_value("ai.garden.engine.learn_confidence", 0.7)
        )
        if not self._presets_loaded:
            self.load_presets()

        all_new_keys: List[str] = []
        all_tokens: List[str] = []

        # Stage 1: Collect all tokens from all samples
        import string

        for s in samples:
            user_text = s.get("input", "")
            response_text = s.get("output", "")
            for text in [user_text, response_text]:
                tokens = [
                    t
                    for t in text.lower().split()
                    if len(t) >= limit_value("ai.garden.engine.min_token_length", 3)
                ]
                all_tokens.extend(tokens)

        # Clean punctuation from tokens
        cleaned_tokens = []
        for token in all_tokens:
            cleaned = token.strip(string.punctuation)
            if cleaned and len(cleaned) >= limit_value("ai.garden.engine.min_token_length", 3):
                cleaned_tokens.append(cleaned)

        # Stage 2: Batch grow - don't rebuild index until all tokens processed
        for token in cleaned_tokens:
            existing = self.dictionary._find_similar_key(
                token, threshold=threshold_value("ai.garden.engine.dedup_similarity", 0.90)
            )
            if not existing and confidence >= self.dictionary.growth_threshold:
                new_key = self.dictionary.grow(token, token, confidence=confidence)
                if new_key:
                    self.snn._register_key(new_key)
                    all_new_keys.append(new_key)

        # Stage 3: Rebuild index ONCE after all grows
        if all_new_keys and self.dictionary._dirty:
            self.dictionary._rebuild_index()

        # Stage 4: Hebbian updates for each sample.
        # Skipped when train_associations=False (knowledge-only ingestion: the
        # fact lives in the dictionary, the SNN only ever learns associations).
        hebbian_delta = 0.0
        if train_associations:
            for s in samples:
                user_text = s.get("input", "")
                response_text = s.get("output", "")
                input_keys = self.dictionary.encode(user_text)
                output_keys = self.dictionary.encode(response_text)
                if input_keys and output_keys:
                    delta = self.snn.hebbian_update(
                        input_keys,
                        output_keys,
                        lr=learning_rate("ai.garden.engine.hebbian_lr", 0.05),
                        target_strength=confidence_value(
                            "ai.garden.engine.hebbian_target_strength", 0.7
                        ),
                    )
                    hebbian_delta += delta

        self._learn_count += len(samples)

        return {
            "interaction": self._learn_count,
            "new_concepts": len(all_new_keys),
            "samples_processed": len(samples),
            "hebbian_delta": round(hebbian_delta, 6),
            "associations_trained": train_associations,
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
        snn_stats = self.snn.get_stats()
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
        snn_path = os.path.join(directory, "snn.pt")
        meta_path = os.path.join(directory, "engine_meta.json")

        if os.path.exists(dict_path):
            self.dictionary.import_from_json(dict_path)
        if os.path.exists(snn_path) or os.path.exists(snn_path + ".npy"):
            self.snn.load(snn_path)
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self._query_count = meta.get("query_count", 0)
            self._learn_count = meta.get("learn_count", 0)
        self._presets_loaded = True
        logger.info("GARDEN: engine loaded from %s", directory)
