# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L3]
# =============================================================================
"""
Semantic QA layer for the unified engine.

Backed by SharedLatentSpace (true gradient-trained projection): question
strings are hashed into fixed-dim features, contrastively trained so that
paraphrases of the same topic land near each other, and answers retrieved
by cosine similarity. This gives the engine *factual* open-QA ability the
byte-statistical core cannot represent ("capital of France" -> Paris).

Design:
  - learn(qa_pairs): trains the SLS projection on question->answer pairs
    (question augmented with its answer words as positives).
  - answer(query): returns (answer_text, similarity) for the nearest known
    QA pair, or None when similarity is below threshold.
  - Persistence: weights saved via SharedLatentSpace.save_weights.

This is a REAL learned component (gradient descent), complementing the
deterministic math/logic layers and the byte-statistical core.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_DIM = 512
_MODALITY = "unified_qa"
_THRESHOLD = 0.75  # below this we admit "don't know" instead of guessing


def _tokens(s: str) -> List[str]:
    stop = {"what", "is", "the", "of", "are", "there", "a", "an", "to", "in", "on"}
    return [w for w in re.findall(r"[a-z]+", s.lower()) if w not in stop]


def _features(s: str, dim: int = _DIM) -> np.ndarray:
    v = np.zeros(dim, dtype=np.float32)
    ws = _tokens(s)
    for w in ws:
        v[hash(w) % dim] += 1.5
    for w in ws:
        for i in range(len(w) - 2):
            v[hash(w[i : i + 3]) % dim] += 0.6
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


class SemanticQA:
    """Contrastive QA retrieval over SharedLatentSpace."""

    def __init__(self) -> None:
        from ai.multimodal.shared_latent_space import get_shared_latent_space

        self._sls = get_shared_latent_space()
        self._questions: List[str] = []
        self._answers: List[str] = []
        self._embs: Optional[np.ndarray] = None

    def learn(self, qa_pairs: List[Tuple[str, str]], epochs: int = 60) -> Dict[str, float]:
        self._sls.reset()
        self._sls.register_modality(_MODALITY, _DIM)
        self._questions = [q for q, _ in qa_pairs]
        self._answers = [a for _, a in qa_pairs]
        qs = [_features(q) for q in self._questions]
        # positive pairs: question with its own answer words appended (teaches
        # the projection that question-topic and answer-token contexts agree)
        pos = [(qs[i], _features(f"{q} {a.lower()}")) for i, (q, a) in enumerate(qa_pairs)]
        neg: List[Tuple[np.ndarray, np.ndarray]] = []
        step = max(1, len(qs) // 3)
        for i in range(len(qs)):
            j = (i + step) % len(qs)
            if i != j:
                neg.append((qs[i], qs[j]))
        result = self._sls.semantic_contrastive_train(
            pos, neg, modality=_MODALITY, epochs=epochs, lr=0.03, margin=0.4
        )
        embs = np.stack([self._sls.project(_MODALITY, q) for q in qs])
        self._embs = embs / (np.linalg.norm(embs, axis=1, keepdims=True) + 1e-9)
        return {
            "pairs": len(qa_pairs),
            "final_loss": float(result.get("final_loss", -1.0)),
        }

    def answer(self, query: str) -> Optional[Tuple[str, float]]:
        if self._embs is None or not self._questions:
            return None
        qv = self._sls.project(_MODALITY, _features(query))
        nv = np.linalg.norm(qv)
        if nv < 1e-9:
            return None
        sims = self._embs @ (qv / nv)
        best = int(np.argmax(sims))
        sim = float(sims[best])
        if sim < _THRESHOLD:
            return None
        return self._answers[best], sim

    @property
    def size(self) -> int:
        return len(self._questions)

    def to_dict(self) -> Dict:
        return {
            "format": "semantic_qa/1",
            "questions": self._questions,
            "answers": self._answers,
        }

    def load_dict(self, d: Dict) -> bool:
        if d.get("format") != "semantic_qa/1":
            return False
        pairs = list(zip(d.get("questions", []), d.get("answers", [])))
        if not pairs:
            return False
        self.learn(pairs, epochs=10)  # short refresh on load
        return True
