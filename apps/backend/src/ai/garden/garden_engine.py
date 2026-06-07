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
import time
from typing import Any, Dict, List, Optional

from .dictionary import VectorDictionary
from .snn_core import TensorSNNCore

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

    def __init__(self, max_cache: int = 256):
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
    top_k: int = 6,
) -> str:
    """
    Combine highest-scored network output keys with top anchor input keys,
    then decode to text.  Anchoring prevents the response from drifting
    entirely away from the user's original intent.
    """
    if not network_output and not input_keys:
        return ""

    # Sort network output by score, take top_k
    sorted_output = sorted(network_output.items(), key=lambda x: x[1], reverse=True)
    output_keys = [k for k, _ in sorted_output[:top_k]]

    # Anchors = top-3 input keys (preserve intent)
    anchors = input_keys[:3]

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
        top_k: int = 8,
        similarity_threshold: float = 0.30,
        snn_timesteps: int = 6,
        device: str = "cpu",
    ):
        self.model_name = model_name
        self.device = device

        self.reflex = _ReflexTable()
        self.dictionary = VectorDictionary(
            model_name=model_name,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            device=device,
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
                                confidence=entry_data.get("confidence", 0.9),
                            )
                            loaded_from_config += 1
                except Exception as e:
                    logger.warning("GARDEN: failed to load config %s: %s", fname, e)
            if loaded_from_config > 0:
                logger.info("GARDEN: loaded %d additional concepts from config/", loaded_from_config)

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
          reflex → vector encode → SNN forward → anchored decode
        """
        if not text or not isinstance(text, str):
            return ""

        self._query_count += 1

        # Stage 1: Reflex (fast pattern match)
        reflex_hit = self.reflex.match(text)
        if reflex_hit is not None:
            return reflex_hit

        # Stage 2: Vector encode
        if not self._presets_loaded:
            self.load_presets()

        input_keys = self.dictionary.encode(text)

        if not input_keys:
            return "抱歉，我暂时无法理解你的意思。"

        # Stage 3: SNN forward
        network_output = self.snn.forward(input_keys, context=context)

        # Stage 4: Anchored decode
        response = _anchored_decode(network_output, input_keys, self.dictionary)

        if not response:
            # Fallback: decode input keys directly
            response = self.dictionary.decode(input_keys[:4])

        if not response:
            return "抱歉，我暂时无法理解你的意思。"

        return response

    # ------------------------------------------------------------------
    # Continuous learning
    # ------------------------------------------------------------------

    def learn_from_interaction(
        self,
        user_text: str,
        response_text: str,
        confidence: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Online learning from a single interaction.
        1. Detect and grow new concepts in the dictionary
        2. Run Hebbian weight update in SNN between input and response keys
        Returns a summary dict.
        """
        if not self._presets_loaded:
            self.load_presets()

        self._learn_count += 1

        # Grow dictionary with any novel concepts from user text
        new_keys: List[str] = []
        tokens = [t for t in user_text.lower().split() if len(t) >= 3]
        for token in tokens:
            existing = self.dictionary._find_similar_key(token, threshold=0.90)
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
                input_keys, output_keys, lr=0.05, target_strength=0.7
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
