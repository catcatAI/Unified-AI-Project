# =============================================================================
# ANGELA-MATRIX: [L3] [αβ] [B] [L2]
# =============================================================================
"""
GARDEN VectorDictionary — Semantic encoding layer using PyTorch tensor embeddings.

Replaces ED3N's character-exact matching (Trie/regex) with dense vector nearest-neighbour
search. Any text input is mapped to abstract Concept Keys via cosine similarity.

Encoder fallback chain:
  1. SentenceTransformer (if available) — best quality semantic encoding
  2. ChromaDB (if available) — good quality with built-in HNSW index
  3. TF-IDF (always available) — lightweight, no external dependencies
  4. CharBag (always available) — deterministic fallback for empty vocabularies
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import zlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.system.config.magic_numbers import confidence_value, threshold_value

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy torch import (compatible with Python 3.14 where torch may be absent)
# ---------------------------------------------------------------------------

_torch = None

def _lazy_torch():
    global _torch
    if _torch is None:
        import torch
        import torch.nn.functional as F
        _torch = (torch, F)
    return _torch

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ConceptEntry:
    """One entry in the GARDEN vector dictionary."""
    key: str                          # e.g. "g1"
    surface_forms: Dict[str, str]     # {"zh": "你好", "en": "hello"}
    relations: Dict[str, List[str]] = field(default_factory=dict)
    confidence: float = 1.0
    # Vector embedding (set after encoding)
    embedding: Optional[torch.Tensor] = field(default=None, repr=False)


# ---------------------------------------------------------------------------
# Encoder backend (sentence-transformers or fallback)
# ---------------------------------------------------------------------------

class _TfidfEncoder:
    """
    Pure-Python TF-IDF encoder with zero external dependencies.
    Tokenizes English words + Chinese unigrams/bigrams into a sparse vocab,
    then produces dense TF-IDF vectors normalized to unit length.

    Fits vocabulary on first encode() call.  Re-fit by calling fit() again.
    """

    def __init__(self):
        self.vocab: Dict[str, int] = {}
        self.idf: Optional[torch.Tensor] = None
        self.N: int = 0
        self._fitted = False

    # ------------------------------------------------------------------
    # Tokenisation (English words + Chinese chars/bigrams)
    # ------------------------------------------------------------------

    def _tokenize(self, text: str) -> List[str]:
        tokens: List[str] = []
        lower = text.lower().strip()
        if not lower:
            return tokens
        # English words (split on whitespace)
        for word in lower.split():
            cleaned = word.strip(",.!?;:\"'()[]{}")
            if cleaned and all(c.isalpha() or c in "'-" for c in cleaned):
                tokens.append(cleaned)
        # Chinese unigrams
        cjk_chars: List[str] = []
        for ch in lower:
            if '\u4e00' <= ch <= '\u9fff' or '\u3040' <= ch <= '\u30ff':
                tokens.append(ch)
                cjk_chars.append(ch)
        # Chinese bigrams
        for i in range(len(cjk_chars) - 1):
            tokens.append(cjk_chars[i] + cjk_chars[i + 1])
        return tokens

    # ------------------------------------------------------------------
    # Fit / build vocabulary
    # ------------------------------------------------------------------

    def fit(self, texts: List[str]) -> None:
        torch, _ = _lazy_torch()
        # Build vocabulary from corpus
        vocab_set: set = set()
        doc_freq: Dict[str, int] = {}
        for text in texts:
            toks = self._tokenize(text)
            seen = set()
            for t in toks:
                vocab_set.add(t)
                if t not in seen:
                    seen.add(t)
                    doc_freq[t] = doc_freq.get(t, 0) + 1
        self.vocab = {t: i for i, t in enumerate(sorted(vocab_set))}
        self.N = len(texts)
        V = len(self.vocab)
        # IDF: log(N / df) + 1  (smooth)
        idf_list = [0.0] * V
        for token, idx in self.vocab.items():
            df = doc_freq.get(token, 1)
            idf_list[idx] = math.log(self.N / df) + 1.0 if self.N > 0 else 1.0
        self.idf = torch.tensor(idf_list, dtype=torch.float32)
        self._fitted = True
        logger.info(
            "GARDEN TF-IDF: fitted on %d documents, vocab=%d",
            self.N, V,
        )

    # ------------------------------------------------------------------
    # Encode
    # ------------------------------------------------------------------

    def encode(self, texts: List[str]) -> torch.Tensor:
        torch, _ = _lazy_torch()
        if not self._fitted:
            self.fit(texts)
        V = len(self.vocab)
        if V == 0:
            return torch.zeros(len(texts), 1)
        N = len(texts)
        # Build TF-IDF matrix [N, V]
        matrix = torch.zeros(N, V, dtype=torch.float32)
        for i, text in enumerate(texts):
            toks = self._tokenize(text)
            for t in toks:
                idx = self.vocab.get(t)
                if idx is not None:
                    matrix[i, idx] += 1.0  # raw TF (will be weighted by IDF)
            # Apply IDF weights
            if self.idf is not None:
                matrix[i] *= self.idf
        # L2 normalize
        norms = matrix.norm(dim=1, keepdim=True)
        norms[norms == 0] = 1.0
        matrix = matrix / norms
        return matrix


class _CharBagEncoder:
    """
    CPU-only fallback encoder that produces a deterministic dense vector from text
    using character n-gram hashing into a fixed-dim space.  No internet required.
    Kept as fallback when TF-IDF vocabulary is empty.
    """
    DIM = 256

    def encode(self, texts: List[str]) -> torch.Tensor:
        torch, _ = _lazy_torch()
        vecs = []
        for text in texts:
            v = torch.zeros(self.DIM)
            lower = text.lower()
            for i, ch in enumerate(lower):
                idx = (ord(ch) * 31 + i) % self.DIM
                v[idx] += 1.0
            for i in range(len(lower) - 1):
                bigram = lower[i:i+2]
                idx = (zlib.adler32(bigram.encode()) & 0x7FFFFFFF) % self.DIM
                v[idx] += 0.5
            norm = v.norm()
            if norm > 0:
                v = v / norm
            vecs.append(v)
        return torch.stack(vecs) if vecs else torch.zeros(0, self.DIM)


class _STEncoder:
    """Wraps sentence-transformers SentenceTransformer for semantic encoding."""

    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name)
        logger.info("GARDEN: loaded SentenceTransformer model '%s'", model_name)

    def encode(self, texts: List[str]) -> torch.Tensor:
        embeddings = self._model.encode(texts, convert_to_tensor=True, normalize_embeddings=True)
        return embeddings.cpu()


class _ChromaEncoder:
    """
    ChromaDB-based semantic encoder for GARDEN.

    Uses ChromaDB's built-in embedding function (default: all-MiniLM-L6-v2)
    to encode text into dense vectors. Falls back gracefully if ChromaDB is
    unavailable or fails to initialize.

    The encoder maintains an in-memory ChromaDB collection. On encode(), texts
    are added to the collection and queried to retrieve embeddings. This allows
    the encoder to work with dynamic concept entries without requiring a fit()
    step.
    """

    EMBEDDING_DIM: int = 384

    def __init__(self):
        import chromadb
        import uuid
        self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(
            name=f"garden_concepts_{uuid.uuid4().hex[:8]}",
            metadata={"hnsw:space": "cosine"},
        )
        self._id_counter = 0
        self._text_to_id: Dict[str, str] = {}
        logger.info("GARDEN: ChromaDB encoder initialized (collection=%s)", self._collection.name)

    def fit(self, texts: List[str]) -> None:
        """No-op: ChromaDB indexes documents automatically on add()."""
        pass

    def encode(self, texts: List[str]) -> torch.Tensor:
        torch, _ = _lazy_torch()
        if not texts:
            return torch.zeros(0, self.EMBEDDING_DIM)

        # Add texts to collection (deduplicate by text content)
        ids_to_add = []
        docs_to_add = []
        for text in texts:
            if text not in self._text_to_id:
                doc_id = f"doc_{self._id_counter}"
                self._id_counter += 1
                self._text_to_id[text] = doc_id
                ids_to_add.append(doc_id)
                docs_to_add.append(text)

        if ids_to_add:
            self._collection.add(documents=docs_to_add, ids=ids_to_add)

        # Query each text to get its embedding from ChromaDB
        embeddings = []
        for text in texts:
            doc_id = self._text_to_id.get(text)
            if doc_id:
                try:
                    result = self._collection.get(
                        ids=[doc_id],
                        include=["embeddings"],
                    )
                    if result and result.get("embeddings") and len(result["embeddings"]) > 0:
                        emb = result["embeddings"][0]
                        if emb is not None and len(emb) > 0:
                            embeddings.append(emb)
                        else:
                            logger.warning("GARDEN: ChromaDB returned empty embedding for text '%s'", text[:50])
                            embeddings.append([0.0] * self.EMBEDDING_DIM)
                    else:
                        logger.warning("GARDEN: ChromaDB get() returned no embeddings for text '%s'", text[:50])
                        embeddings.append([0.0] * self.EMBEDDING_DIM)
                except Exception as e:
                    logger.warning("GARDEN: ChromaDB get() failed for text '%s': %s", text[:50], e)
                    embeddings.append([0.0] * self.EMBEDDING_DIM)
            else:
                logger.warning("GARDEN: text '%s' not found in ChromaDB text_to_id map", text[:50])
                embeddings.append([0.0] * self.EMBEDDING_DIM)

        if not embeddings:
            return torch.zeros(0, self.EMBEDDING_DIM)

        return torch.tensor(embeddings, dtype=torch.float32).cpu()

    def query_embedding(self, text: str) -> Optional[List[float]]:
        """Get the embedding for a single text without adding it to the collection."""
        try:
            result = self._collection.query(
                query_texts=[text],
                n_results=1,
                include=["embeddings"],
            )
            if result and result.get("embeddings"):
                embs = result["embeddings"]
                if len(embs) > 0 and len(embs[0]) > 0:
                    return embs[0][0].tolist() if hasattr(embs[0][0], 'tolist') else list(embs[0][0])
        except Exception as e:
            logger.debug("GARDEN: ChromaDB query_embedding failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# VectorDictionary
# ---------------------------------------------------------------------------

class VectorDictionary:
    """
    GARDEN vector dictionary.

    Maintains a set of ConceptEntry objects each with a dense embedding.
    Encodes arbitrary text inputs to a ranked list of Concept Keys via
    cosine similarity nearest-neighbour search.

    Usage:
        d = VectorDictionary()
        d.load_presets()
        keys = d.encode("你好今天天氣很好")   # -> ["g1", "c3", ...]
        surface = d.decode(["g1", "e1"])      # -> "你好 开心"
    """

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        top_k: int = 8,
        similarity_threshold: Optional[float] = None,
        device: str = "cpu",
        compatibility_mode: bool = False,
    ):
        similarity_threshold = similarity_threshold if similarity_threshold is not None else threshold_value("ai.garden.dictionary.similarity_threshold", 0.30)
        self.model_name = model_name
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.device = device
        self.compatibility_mode = compatibility_mode

        self.entries: Dict[str, ConceptEntry] = {}
        self._encoder = self._build_encoder(model_name)
        self._matrix: Optional[torch.Tensor] = None   # shape [N, D]
        self._key_order: List[str] = []               # maps row index -> key
        self._dirty = True                             # re-index flag
        self._presets_loaded = False
        self.growth_threshold = threshold_value("ai.garden.dictionary.growth_threshold", 0.6)

    # ------------------------------------------------------------------
    # Encoder setup
    # ------------------------------------------------------------------

    def _build_encoder(self, model_name: str):
        if self.compatibility_mode:
            logger.info("GARDEN: using TF-IDF encoder (compatibility mode)")
            return _TfidfEncoder()
        try:
            enc = _STEncoder(model_name)
            logger.info("GARDEN: using SentenceTransformer encoder (semantic mode)")
            return enc
        except Exception as e:
            logger.warning("GARDEN: SentenceTransformer not available (%s); trying ChromaDB", e)
        try:
            enc = _ChromaEncoder()
            logger.info("GARDEN: using ChromaDB encoder (semantic mode)")
            return enc
        except Exception as e:
            logger.warning("GARDEN: ChromaDB not available (%s); using TF-IDF fallback", e)
        return _TfidfEncoder()

    # ------------------------------------------------------------------
    # Entry management
    # ------------------------------------------------------------------

    def add_entry(
        self,
        key: str,
        surface_forms: Dict[str, str],
        relations: Optional[Dict[str, List[str]]] = None,
        confidence: Optional[float] = None,
    ) -> ConceptEntry:
        confidence = confidence if confidence is not None else confidence_value("ai.garden.dictionary.add_confidence", 1.0)
        entry = ConceptEntry(
            key=key,
            surface_forms=surface_forms,
            relations=relations or {},
            confidence=confidence,
        )
        self.entries[key] = entry
        self._dirty = True
        return entry

    def grow(self, text: str, surface_form: str, confidence: Optional[float] = None) -> str:
        """Add a new entry learned from conversation."""
        confidence = confidence if confidence is not None else confidence_value("ai.garden.dictionary.grow_confidence", 0.6)
        existing = self._find_similar_key(text, threshold=threshold_value("ai.garden.dictionary.grow_dedup_threshold", 0.85))
        if existing:
            return existing
        idx = len(self.entries) + 1
        key = f"l{idx}"
        self.add_entry(key, {"en": text, "zh": surface_form or text}, confidence=confidence)
        logger.info("GARDEN: grew new concept key=%s surface=%s", key, surface_form)
        return key

    def _find_similar_key(self, text: str, threshold: Optional[float] = None) -> Optional[str]:
        """Return existing key if text is very similar to an existing surface form."""
        threshold = threshold if threshold is not None else threshold_value("ai.garden.dictionary.find_similar_threshold", 0.85)
        lower = text.lower().strip()
        for key, entry in self.entries.items():
            for sf in entry.surface_forms.values():
                if sf.lower().strip() == lower:
                    return key
        return None

    # ------------------------------------------------------------------
    # Index building (lazy)
    # ------------------------------------------------------------------

    def _rebuild_index(self) -> None:
        _, F = _lazy_torch()
        if not self.entries:
            self._matrix = None
            self._key_order = []
            self._dirty = False
            return

        self._key_order = list(self.entries.keys())
        texts = []
        for key in self._key_order:
            entry = self.entries[key]
            forms = list(entry.surface_forms.values())
            texts.append(" ".join(forms))

        if hasattr(self._encoder, 'fit'):
            self._encoder.fit(texts)
        embeddings = self._encoder.encode(texts)  # [N, D]

        for i, key in enumerate(self._key_order):
            self.entries[key].embedding = embeddings[i]

        self._matrix = F.normalize(embeddings, dim=-1)  # [N, D]
        self._dirty = False
        logger.debug("GARDEN: index rebuilt with %d entries, dim=%d", len(self._key_order), self._matrix.shape[1])

    # ------------------------------------------------------------------
    # Core encode / decode
    # ------------------------------------------------------------------

    def encode(self, text: str) -> List[str]:
        """Map text to a ranked list of concept keys via cosine similarity."""
        if not text or not isinstance(text, str):
            return []
        if self._dirty or self._matrix is None:
            self._rebuild_index()
        if self._matrix is None or len(self._key_order) == 0:
            return []

        _, F = _lazy_torch()
        query_vec = self._encoder.encode([text])          # [1, D]
        query_vec = F.normalize(query_vec, dim=-1)        # [1, D]
        scores = (self._matrix @ query_vec.T).squeeze(-1) # [N]

        k = min(self.top_k, scores.shape[0])
        top_scores, top_indices = scores.topk(k)

        results = []
        for score, idx in zip(top_scores.tolist(), top_indices.tolist()):
            if score >= self.similarity_threshold:
                results.append(self._key_order[idx])
        return results

    def decode(self, keys: List[str]) -> str:
        """Turn a list of concept keys back into a human-readable string."""
        parts = []
        for key in keys:
            entry = self.entries.get(key)
            if entry is None:
                continue
            # Prefer Chinese, then English
            surface = entry.surface_forms.get("zh") or entry.surface_forms.get("en") or key
            parts.append(surface)
        return " ".join(parts)

    def get_synonyms(self, key: str) -> List[str]:
        entry = self.entries.get(key)
        if not entry:
            return []
        return list(entry.relations.get("synonym", []))

    def get_related(self, key: str, relation_type: Optional[str] = None) -> List[str]:
        entry = self.entries.get(key)
        if not entry:
            return []
        if relation_type:
            return list(entry.relations.get(relation_type, []))
        result: List[str] = []
        seen = set()
        for rels in entry.relations.values():
            for r in rels:
                if r not in seen:
                    seen.add(r)
                    result.append(r)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {
            "entry_count": len(self.entries),
            "encoder_type": type(self._encoder).__name__,
            "model_name": self.model_name,
            "index_built": not self._dirty and self._matrix is not None,
            "embedding_dim": self._matrix.shape[1] if self._matrix is not None else 0,
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def export_to_json(self, path: str) -> None:
        data = {
            "version": "garden-1.0",
            "entries": [
                {
                    "key": e.key,
                    "surface_forms": e.surface_forms,
                    "relations": e.relations,
                    "confidence": e.confidence,
                }
                for e in self.entries.values()
            ],
        }
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("GARDEN: dictionary exported to %s", path)

    def import_from_json(self, path: str) -> int:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = 0
        for item in data.get("entries", []):
            if item["key"] not in self.entries:
                self.add_entry(
                    key=item["key"],
                    surface_forms=item["surface_forms"],
                    relations=item.get("relations"),
                    confidence=item.get("confidence", 1.0),
                )
                count += 1
        logger.info("GARDEN: imported %d entries from %s", count, path)
        return count

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------

    def load_presets(self) -> None:
        """Load built-in concept presets covering greetings, emotions, logic, math."""
        if self._presets_loaded:
            return
        for p in self._build_presets():
            self.add_entry(**p)
        self._dirty = True
        self._presets_loaded = True
        logger.info("GARDEN: loaded %d preset entries", len(self.entries))

    def _build_presets(self) -> List[Dict[str, Any]]:
        return [
            # --- Greetings ---
            {"key": "g1", "surface_forms": {"zh": "你好", "en": "hello"},
             "relations": {"synonym": ["g2", "g3", "g5"]}},
            {"key": "g2", "surface_forms": {"zh": "早上好", "en": "good morning"},
             "relations": {"synonym": ["g1"], "mapping": ["g5"]}},
            {"key": "g3", "surface_forms": {"zh": "晚上好", "en": "good evening"},
             "relations": {"synonym": ["g1"]}},
            {"key": "g4", "surface_forms": {"zh": "欢迎", "en": "welcome"},
             "relations": {"synonym": ["g1"]}},
            {"key": "g5", "surface_forms": {"zh": "嗨", "en": "hi"},
             "relations": {"synonym": ["g1", "g6"]}},
            {"key": "g6", "surface_forms": {"zh": "哈喽", "en": "hey"},
             "relations": {"synonym": ["g1", "g5"]}},
            # --- Farewells ---
            {"key": "f1", "surface_forms": {"zh": "再见", "en": "goodbye"},
             "relations": {"synonym": ["f2"]}},
            {"key": "f2", "surface_forms": {"zh": "明天见", "en": "see you tomorrow"},
             "relations": {"synonym": ["f1"]}},
            # --- Politeness ---
            {"key": "p1", "surface_forms": {"zh": "谢谢", "en": "thank you"},
             "relations": {"synonym": ["p4"], "mapping": ["e1", "r1"]}},
            {"key": "p2", "surface_forms": {"zh": "对不起", "en": "sorry"},
             "relations": {"synonym": ["r2"]}},
            {"key": "p3", "surface_forms": {"zh": "没关系", "en": "no problem"},
             "relations": {"synonym": ["r3"]}},
            {"key": "p4", "surface_forms": {"zh": "请", "en": "please"},
             "relations": {"mapping": ["g1", "p1"]}},
            # --- Emotions ---
            {"key": "e1", "surface_forms": {"zh": "开心", "en": "happy"},
             "relations": {"synonym": ["e5"], "mapping": ["c2"]}},
            {"key": "e2", "surface_forms": {"zh": "难过", "en": "sad"},
             "relations": {"mapping": ["p2", "c2"]}},
            {"key": "e3", "surface_forms": {"zh": "烦恼", "en": "annoyed"},
             "relations": {"mapping": ["e2", "c2"]}},
            {"key": "e4", "surface_forms": {"zh": "无聊", "en": "bored"},
             "relations": {"mapping": ["e2", "c1"]}},
            {"key": "e5", "surface_forms": {"zh": "兴奋", "en": "excited"},
             "relations": {"synonym": ["e1"], "mapping": ["c2"]}},
            # --- Common patterns ---
            {"key": "c1", "surface_forms": {"zh": "在忙吗", "en": "are you busy"},
             "relations": {"mapping": ["e5", "r1"]}},
            {"key": "c2", "surface_forms": {"zh": "心情", "en": "mood"},
             "relations": {"mapping": ["e1", "e2", "e3", "e5"]}},
            {"key": "c3", "surface_forms": {"zh": "今天", "en": "today"},
             "relations": {"mapping": ["g2", "g3", "c1"]}},
            {"key": "c4", "surface_forms": {"zh": "名字", "en": "name"},
             "relations": {"mapping": ["g1"]}},
            {"key": "c5", "surface_forms": {"zh": "做什么", "en": "what are you doing"},
             "relations": {"mapping": ["c1", "e5"]}},
            # --- Responses ---
            {"key": "r1", "surface_forms": {"zh": "嗯", "en": "uh-huh"},
             "relations": {"synonym": ["r2", "r3"]}},
            {"key": "r2", "surface_forms": {"zh": "好的", "en": "okay"},
             "relations": {"synonym": ["r1", "r3", "r4"]}},
            {"key": "r3", "surface_forms": {"zh": "明白", "en": "understood"},
             "relations": {"synonym": ["r1", "r2", "r4"]}},
            {"key": "r4", "surface_forms": {"zh": "可以", "en": "sure"},
             "relations": {"synonym": ["r2"]}},
            # --- Logic ---
            {"key": "b1", "surface_forms": {"zh": "真", "en": "true"},
             "relations": {"antonym": ["b2"]}},
            {"key": "b2", "surface_forms": {"zh": "假", "en": "false"},
             "relations": {"antonym": ["b1"]}},
            {"key": "b3", "surface_forms": {"zh": "且", "en": "and"}, "relations": {}},
            {"key": "b4", "surface_forms": {"zh": "或", "en": "or"}, "relations": {}},
            {"key": "b5", "surface_forms": {"zh": "非", "en": "not"}, "relations": {}},
            # --- Math numbers 0-9 ---
            {"key": "m0", "surface_forms": {"zh": "零", "en": "zero"}, "relations": {}},
            {"key": "m1", "surface_forms": {"zh": "一", "en": "one"}, "relations": {}},
            {"key": "m2", "surface_forms": {"zh": "二", "en": "two"}, "relations": {}},
            {"key": "m3", "surface_forms": {"zh": "三", "en": "three"}, "relations": {}},
            {"key": "m4", "surface_forms": {"zh": "四", "en": "four"}, "relations": {}},
            {"key": "m5", "surface_forms": {"zh": "五", "en": "five"}, "relations": {}},
            {"key": "m6", "surface_forms": {"zh": "六", "en": "six"}, "relations": {}},
            {"key": "m7", "surface_forms": {"zh": "七", "en": "seven"}, "relations": {}},
            {"key": "m8", "surface_forms": {"zh": "八", "en": "eight"}, "relations": {}},
            {"key": "m9", "surface_forms": {"zh": "九", "en": "nine"}, "relations": {}},
            # --- Math operators ---
            {"key": "op1", "surface_forms": {"zh": "加", "en": "plus"}, "relations": {"antonym": ["op2"]}},
            {"key": "op2", "surface_forms": {"zh": "减", "en": "minus"}, "relations": {"antonym": ["op1"]}},
            {"key": "op3", "surface_forms": {"zh": "乘", "en": "multiply"}, "relations": {}},
            {"key": "op4", "surface_forms": {"zh": "除", "en": "divide"}, "relations": {}},
            {"key": "op5", "surface_forms": {"zh": "等于", "en": "equals"}, "relations": {}},
            # --- Angela identity ---
            {"key": "id1", "surface_forms": {"zh": "Angela", "en": "angela"},
             "relations": {"mapping": ["id2"]}},
            {"key": "id2", "surface_forms": {"zh": "AI助手", "en": "AI assistant"},
             "relations": {"mapping": ["id1"]}},
            # --- Questions ---
            {"key": "q1", "surface_forms": {"zh": "什么", "en": "what"}, "relations": {}},
            {"key": "q2", "surface_forms": {"zh": "为什么", "en": "why"}, "relations": {}},
            {"key": "q3", "surface_forms": {"zh": "怎么", "en": "how"}, "relations": {}},
            {"key": "q4", "surface_forms": {"zh": "哪里", "en": "where"}, "relations": {}},
            {"key": "q5", "surface_forms": {"zh": "谁", "en": "who"}, "relations": {}},
        ]
