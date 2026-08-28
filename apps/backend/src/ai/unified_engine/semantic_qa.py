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
_DEFAULT_THRESHOLD = 0.75  # lowered 0.80->0.75 for open-domain recall (ONNX 384-dim
# now handles CJK, so lower threshold trades 5% precision for ~25% recall)
# Config-driven via threshold_value("semantic_qa.threshold") for hardware-aware tuning.


_CACHED_THRESHOLD: Optional[float] = None


def _emotion_threshold_adjustment() -> float:
    """情緒→閾值的自調整增量 (AI 自調, 閉環).

    優先讀 _EMOTION_ADJ (由 chat_routes 每輪注入), 其次回退到 state_store 探測.
    狀態(αβγ)經 EmotionSystem 映射為 PAD，再映射為反應風格:
    - JOY/TRUST/高 arousal → 更探索 → 閾值 -0.05 (更願意回答, 提高召回)
    - FEAR/SADNESS/低 valence 或 sustained_negative≥3 → 更保守 → 閾值 +0.08
    - 中性 → 0
    增量限幅 ±0.10，最終閾值限幅 [0.60, 0.85] 防幻覺/過度沉默.
    """
    # Path 0: 直接注入 (最可靠, 無循環 import, 無 state_store 依賴)
    if _EMOTION_ADJ != 0.0:
        return max(-0.10, min(0.10, _EMOTION_ADJ))
    adj = 0.0
    # Path 1: state_store 上的 emotion 事件 (chat_routes 每輪 emit)
    try:
        from core.system.state_store.global_store import state_store  # type: ignore

        emo = None
        for key in ("emotion.behavioral_adjustment", "emotion.current", "angela_emotion"):
            try:
                emo = state_store.get(key, None)  # type: ignore[attr-defined]
                if emo:
                    break
            except Exception:
                continue
        if isinstance(emo, dict):
            routing = emo.get("routing_mode", "")
            valence = float(emo.get("valence", 0.0) or 0.0)
            arousal = float(emo.get("arousal", 0.5) or 0.5)
            sustained = int(emo.get("sustained_negative_counter", 0) or 0)
            if routing in ("exploratory",):
                adj -= 0.05
            if routing in ("conservative",):
                adj += 0.05
            if valence > 0.3 and arousal > 0.5:
                adj -= 0.03
            if valence < -0.3:
                adj += 0.03
            if sustained >= 3:
                adj += 0.08
    except Exception:
        pass
    if adj == 0.0:
        try:
            import importlib

            mod = importlib.import_module("api.lifespan")
            get_es = getattr(mod, "get_emotion_system", None) or getattr(mod, "_get_emotion_system", None)
            if get_es is not None:
                try:
                    es = get_es()
                except Exception:
                    es = None
                if es is not None and hasattr(es, "get_emotion_summary"):
                    summary = es.get_emotion_summary()
                    dom = summary.get("dominant_emotion", "neutral")
                    if dom in ("joy", "trust", "surprise", "anticipation"):
                        adj -= 0.04
                    if dom in ("fear", "sadness", "anger", "disgust"):
                        adj += 0.05
        except Exception:
            pass
    return max(-0.10, min(0.10, adj))


def _threshold() -> float:
    global _CACHED_THRESHOLD
    if _CACHED_THRESHOLD is None:
        try:
            from core.system.config.magic_numbers import threshold_value

            _CACHED_THRESHOLD = threshold_value("semantic_qa.threshold", _DEFAULT_THRESHOLD)
        except Exception:
            _CACHED_THRESHOLD = _DEFAULT_THRESHOLD
    base = float(_CACHED_THRESHOLD)  # type: ignore[arg-type]
    adj = _emotion_threshold_adjustment()
    # 最終限幅 [0.60, 0.85] — 既防幻覺 (>0.85 過嚴) 也防過度沉默 (<0.60 過松)
    return max(0.60, min(0.85, base + adj))


# Emotion-driven threshold adjustment (AI 自調, 閉環).
# chat_routes 每輪 _inject_emotion_behavioral_context 後調用 set_emotion_threshold_adjustment()
# 把當前 PAD 推導的 routing/style 轉為閾值增量，下一輪 semantic_qa.answer() 即生效.
# 狀態(6D) -> 情緒(PAD) -> 閾值 -> 反應(文本) -> 回饋 -> 情緒，完成閉環.
_EMOTION_ADJ: float = 0.0


def set_emotion_threshold_adjustment(adj: float) -> None:
    """由 chat_routes 注入當前情緒推導的閾值增量 (AI 自調, 執行緒安全)."""
    global _EMOTION_ADJ
    # 限幅 ±0.10
    _EMOTION_ADJ = max(-0.10, min(0.10, float(adj)))


# ONNX int8 encoder (reuses garden/dictionary export, 2.1x CPU, multilingual).
# Lazy singleton: None = not probed, False = unavailable (fallback to hash).
_ONNX_ENCODER: Optional[object] = None
_ONNX_TRIED = False


def _get_onnx_encoder():
    global _ONNX_ENCODER, _ONNX_TRIED
    if _ONNX_TRIED:
        return _ONNX_ENCODER
    _ONNX_TRIED = True
    try:
        from ai.garden.dictionary import _OnnxEncoder, _onnx_model_path

        path = _onnx_model_path("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        if path is None:
            path = _onnx_model_path("paraphrase-multilingual-MiniLM-L12-v2")
        if path is not None:
            _ONNX_ENCODER = _OnnxEncoder(path, max_length=32)
            logger.info("SemanticQA: ONNX encoder active (%s)", path)
            return _ONNX_ENCODER
    except Exception as e:
        logger.debug("SemanticQA ONNX unavailable, using hash fallback: %s", e)
    _ONNX_ENCODER = False  # type: ignore[assignment]
    return None


def _tokens(s: str) -> List[str]:
    stop = {"what", "is", "the", "of", "are", "there", "a", "an", "to", "in", "on"}
    return [w for w in re.findall(r"[a-z]+", s.lower()) if w not in stop]


def _features(s: str, dim: int = _DIM) -> np.ndarray:
    # Prefer ONNX multilingual embedding (int8, 2.1x CPU, handles CJK) when
    # the quantized model is present; otherwise hash fallback (zero extra deps).
    enc = _get_onnx_encoder()
    if enc is not None:
        try:
            # _OnnxEncoder.encode returns L2-normalized [1, H]; squeeze to [H]
            arr = enc.encode([s])
            if arr is not None and arr.shape[0] > 0:
                return arr[0].astype(np.float32)
        except Exception:
            pass
    v = np.zeros(dim, dtype=np.float32)
    ws = _tokens(s)
    for w in ws:
        v[hash(w) % dim] += 1.5
    for w in ws:
        for i in range(len(w) - 2):
            v[hash(w[i : i + 3]) % dim] += 0.6
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


def _embedding_dim() -> int:
    enc = _get_onnx_encoder()
    if enc is not None:
        try:
            # probe output dim without allocating large batch
            probe = enc.encode(["hello"])
            if probe is not None and probe.ndim == 2:
                return int(probe.shape[1])
        except Exception:
            pass
    return _DIM


class SemanticQA:
    """Contrastive QA retrieval over SharedLatentSpace."""

    def __init__(self) -> None:
        from ai.multimodal.shared_latent_space import get_shared_latent_space

        self._sls = get_shared_latent_space()
        self._questions: List[str] = []
        self._answers: List[str] = []
        self._embs: Optional[np.ndarray] = None

    def learn(self, qa_pairs: List[Tuple[str, str]], epochs: int = 60) -> Dict[str, float]:
        dim = _embedding_dim()
        self._sls.reset()
        self._sls.register_modality(_MODALITY, dim)
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
        if sim < _threshold():
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
