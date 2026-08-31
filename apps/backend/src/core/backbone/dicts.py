# =============================================================================
# ANGELA-MATRIX: L1-L6[全層] αβγδεθζη [A] L2+
# =============================================================================
#
# 職責: MultimodalDictionary 協定（步驟 C2）的實作 — 跨模態字典統一介面
#       （ED3N DictionaryLayer / GARDEN VectorDictionary / 記憶體示範字典）
# 維度: ζ 連通維度（跨模組字典耦合）+ η 執行維度（字典掛載）
# 安全: Key A (後端控制)
#
# =============================================================================

"""多模態字典統一協定實作（§3.5 / 步驟 C2）。

把既有字典（ED3N `DictionaryLayer`、GARDEN `VectorDictionary`）以薄適配層
包裝成 `MultimodalDictionary` 協定，讓主幹線 `backbone.query_dictionary()`
/ `encode_dictionaries()` 可以一致地查詢任何字典，並支援 mountable 字典。

提供：
- `Ed3nDictionaryAdapter`：包 ED3N DictionaryLayer（text 模態）。
- `GardenDictionaryAdapter`：包 GARDEN VectorDictionary（text 模態）。
- `InMemoryDictionary`：輕量示範字典（任何模態，兼作單元測試標竿）。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# 統一 query 回傳統一定義: (key, score, payload) tuple
Hit = tuple


class _BaseDictionaryAdapter:
    """MultimodalDictionary 協定基底。

    提供統一的 `modality`、`size`、`register_entry`、`query` 骨架，
    子類別實作 `encode` 與 `_persist_state`（save/load）。
    """

    modality_name = "text"

    def modality(self) -> str:
        return self.modality_name

    def size(self) -> int:
        raw = self._inner_size()
        return int(raw or 0)

    def _inner_size(self) -> Any:
        return None

    def register_entry(self, key: str, payload: Any = None, **kwargs: Any) -> bool:
        return bool(self._register(key, payload, **kwargs))

    def _register(self, key: str, payload: Any, **kwargs: Any) -> bool:
        return False

    def query(self, input_data: Any, top_k: int = 5, **kwargs: Any) -> List[Hit]:
        """相似性查詢：由 encode 給分 + 取前 top_k。回傳 (key, score, payload)。"""
        scored = self._query_scored(input_data, **kwargs)
        if not scored:
            return []
        scored = sorted(scored, key=lambda x: x[1], reverse=True)[:top_k]
        return [(k, s, self._payload(k)) for k, s in scored]

    def _query_scored(self, input_data: Any, **kwargs: Any) -> List[Any]:
        return []

    def _payload(self, key: str) -> Any:
        return None

    def save(self, path: str) -> bool:
        return self._save(path)

    def load(self, path: str) -> bool:
        return self._load(path)

    def _save(self, path: str) -> bool:
        return False

    def _load(self, path: str) -> bool:
        return False


class Ed3nDictionaryAdapter(_BaseDictionaryAdapter):
    """包裝 ED3N `DictionaryLayer` 的協定適配層。

    - `encode(text)`：delegate 到 inner.encode（回傳候選鍵）。
    - `register_entry(key, text)`：呼叫 add_entry。
    - `query(text, top_k)`：以 encode + lookup 給分。
    """

    def __init__(self, inner: Any) -> None:
        self.inner = inner

    def _inner_size(self) -> int:
        entries = getattr(self.inner, "entries", None)
        return len(entries) if entries else 0

    def encode(self, input_data: Any, **kwargs: Any) -> List[str]:
        fn = getattr(self.inner, "encode", None)
        if callable(fn):
            out = fn(input_data, **kwargs)
            if isinstance(out, list):
                return out
            if isinstance(out, dict):
                return list(out.keys())
        return []

    def _register(self, key: str, payload: Any, **kwargs: Any) -> bool:
        fn = getattr(self.inner, "add_entry", None)
        if not callable(fn):
            return False
        try:
            if isinstance(payload, dict):
                surface_forms = payload
            elif isinstance(payload, str):
                surface_forms = {"en": payload}
            else:
                surface_forms = kwargs.get("surface_forms") or {"en": str(payload or key)}
            fn(key, surface_forms=surface_forms)
            return True
        except Exception as exc:
            logger.debug("Ed3nDictionaryAdapter register failed: %s", exc, exc_info=True)
            return False

    def _query_scored(self, input_data: Any, **kwargs: Any) -> List[Any]:
        keys = self.encode(input_data, **kwargs)
        if not keys:
            return []
        lookup = getattr(self.inner, "lookup", None)
        entry_map = {}
        if callable(lookup):
            try:
                entry_map = lookup(keys) or {}
            except Exception:
                entry_map = {}
        out: List[Any] = []
        for key in keys:
            entry = entry_map.get(key)
            conf = 1.0
            if entry is not None:
                conf = float(getattr(entry, "confidence", 1.0) or 1.0)
            out.append((key, conf))
        return out


class GardenDictionaryAdapter(_BaseDictionaryAdapter):
    """包裝 GARDEN `VectorDictionary` 的協定適配層。

    - `encode(text)`：delegate 到 inner.encode（Dict[str, float] → keys）。
    - `query(text, top_k)`：以 encode 的分數排序。
    """

    def __init__(self, inner: Any) -> None:
        self.inner = inner

    def _inner_size(self) -> int:
        entries = getattr(self.inner, "entries", None)
        return len(entries) if entries else 0

    def encode(self, input_data: Any, **kwargs: Any) -> List[str]:
        fn = getattr(self.inner, "encode", None)
        if callable(fn):
            out = fn(input_data, **kwargs)
            if hasattr(out, "keys"):
                return list(out.keys())
            if isinstance(out, list):
                return out
        return []

    def _register(self, key: str, payload: Any, **kwargs: Any) -> bool:
        fn = getattr(self.inner, "add_entry", None)
        if not callable(fn):
            return False
        try:
            if isinstance(payload, dict):
                surface_forms = payload
            elif isinstance(payload, str):
                surface_forms = {"en": payload}
            else:
                surface_forms = kwargs.get("surface_forms") or {"en": str(payload or key)}
            fn(key, surface_forms=surface_forms)
            return True
        except Exception as exc:
            logger.debug("GardenDictionaryAdapter register failed: %s", exc, exc_info=True)
            return False

    def _query_scored(self, input_data: Any, **kwargs: Any) -> List[Any]:
        fn = getattr(self.inner, "encode", None)
        if callable(fn):
            try:
                out = fn(input_data, **kwargs)
            except Exception as e:
                logger.debug(f"dict _query_scored failed: {e}", exc_info=True)
                return []
        scored = []
        if hasattr(out, "items"):
            scored = [(k, float(v or 0.0)) for k, v in out.items()]
        return scored


class InMemoryDictionary(_BaseDictionaryAdapter):
    """輕量記憶體字典（任何模態）。

    純 Python dict 儲存辭條 → payload 對映，兼作協定標竿與空間字典示範
    （例如 `modality="space"` 的「場景/物品→描述」字典）。
    """

    def __init__(self, modality: str = "text") -> None:
        self.modality_name = modality
        self._data: Dict[str, Any] = {}
        self._meta: Dict[str, Any] = {}

    def _inner_size(self) -> int:
        return len(self._data)

    def encode(self, input_data: Any, **kwargs: Any) -> List[str]:
        text = str(input_data).strip().lower()
        if not text:
            return []
        matched = []
        for k, payload in self._data.items():
            haystack = str(k).lower()
            if isinstance(payload, (list, tuple, set)):
                haystack += " " + " ".join(str(p).lower() for p in payload)
            elif payload is not None:
                haystack += " " + str(payload).lower()
            # 命中條件：查詢串包含字典辭條 term，或字典辭條 term 包含於查詢串
            terms = haystack.split()
            if text in haystack or any(t in text for t in terms if t):
                matched.append(k)
        return matched

    def _register(self, key: str, payload: Any, **kwargs: Any) -> bool:
        self._data[key] = payload
        for meta_k, meta_v in kwargs.items():
            if meta_k in ("text", "surface"):
                continue
            self._meta.setdefault(key, {})[meta_k] = meta_v
        return True

    def _query_scored(self, input_data: Any, **kwargs: Any) -> List[Any]:
        keys = self.encode(input_data, **kwargs)
        return [(k, 1.0) for k in keys]

    def _payload(self, key: str) -> Any:
        return self._data.get(key)

    def _save(self, path: str) -> bool:
        try:
            import json

            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    {"modality": self.modality_name, "data": self._data}, f, ensure_ascii=False
                )
            return True
        except Exception as exc:
            logger.warning("InMemoryDictionary save failed: %s", exc, exc_info=True)
            return False

    def _load(self, path: str) -> bool:
        try:
            import json

            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self.modality_name = payload.get("modality", self.modality_name)
            self._data = payload.get("data", {})
            return True
        except Exception as exc:
            logger.warning("InMemoryDictionary load failed: %s", exc, exc_info=True)
            return False


class KeyValueDictionary(_BaseDictionaryAdapter):
    """通用模態鍵值字典（步驟 C4：物件 / 空間字典標籤）。

    `modality` 以標籤指定（"object"/"space"/"audio"/"image"...），辭條為
    key → 任意 payload（描述、嵌入、屬性 dict）。查詢以 substring/term 比對。
    """

    def __init__(self, modality: str = "object") -> None:
        self.modality_name = modality
        self._data: Dict[str, Any] = {}

    def _inner_size(self) -> int:
        return len(self._data)

    def encode(self, input_data: Any, **kwargs: Any) -> List[str]:
        text = str(input_data).strip().lower()
        if not text:
            return []
        matched = []
        for k, payload in self._data.items():
            haystack = str(k).lower()
            if isinstance(payload, dict):
                haystack += " " + " ".join(str(v).lower() for v in payload.values())
            elif isinstance(payload, (list, tuple, set)):
                haystack += " " + " ".join(str(p).lower() for p in payload)
            elif payload is not None:
                haystack += " " + str(payload).lower()
            terms = haystack.split()
            if text in haystack or any(t in text for t in terms if t):
                matched.append(k)
        return matched

    def _register(self, key: str, payload: Any, **kwargs: Any) -> bool:
        self._data[key] = payload
        return True

    def _query_scored(self, input_data: Any, **kwargs: Any) -> List[Any]:
        keys = self.encode(input_data, **kwargs)
        return [(k, 1.0) for k in keys]

    def _payload(self, key: str) -> Any:
        return self._data.get(key)


class SemanticKeyMapperAdapter(_BaseDictionaryAdapter):
    """包 `SemanticKeyMapper` 的多模態語義字典（步驟 C4）。

    `SemanticKeyMapper` 把 latent 向量（64-dim / raw CLIP/Whisper 512/384-dim）
    對映到 ED3N 概念鍵。此適配層以 `query(latent, top_k)` 提供 cosine 相似度
    查詢，回傳 `[{key, score}, ...]`（符合協定）。
    """

    modality_name = "semantic"

    def __init__(self, inner: Any) -> None:
        self.inner = inner

    def _inner_size(self) -> int:
        count = getattr(self.inner, "count", None)
        if count is not None:
            return int(count() if callable(count) else count)
        return 0

    def encode(self, input_data: Any, **kwargs: Any) -> List[str]:
        # 語義字典以 latent 查詢為準；encode 視為 top-K 命中的鍵
        scored = self._query_scored(input_data, **kwargs)
        return [k for k, _s in scored]

    def _register(self, key: str, payload: Any, **kwargs: Any) -> bool:
        fn = getattr(self.inner, "index_key", None)
        if not callable(fn):
            return False
        try:
            latents = payload if isinstance(payload, dict) else kwargs
            fn(
                key,
                structural_latent=latents.get("structural_latent", latents.get("structural")),
                semantic_latent=latents.get("semantic_latent", latents.get("semantic")),
                combined_latent=latents.get("combined_latent", latents.get("combined")),
                raw_semantic=latents.get("raw_semantic", latents.get("raw")),
            )
            return True
        except Exception as exc:
            logger.debug("SemanticKeyMapperAdapter register failed: %s", exc, exc_info=True)
            return False

    def _query_scored(self, input_data: Any, **kwargs: Any) -> List[Any]:
        import numpy as np

        q = input_data
        if isinstance(q, (list, tuple)):
            try:
                q = np.asarray(q, dtype=np.float32)
            except Exception as e:
                logger.debug(f"dict q convert failed: {e}", exc_info=True)
                return []
        if not isinstance(q, np.ndarray):
            return []
        fn = getattr(self.inner, "map_latent_to_keys", None)
        if not callable(fn):
            return []
        try:
            hits = fn(q, top_k=kwargs.get("top_k", 5), mode=kwargs.get("mode", "auto"))
        except Exception as e:
            logger.debug(f"dict map_latent_to_keys failed: {e}", exc_info=True)
            return []
        out: List[Any] = []
        for h in hits or []:
            if isinstance(h, dict):
                out.append((h.get("key"), float(h.get("score", 0.0) or 0.0)))
            elif isinstance(h, (tuple, list)) and len(h) >= 2:
                out.append((h[0], float(h[1] or 0.0)))
        return out


__all__ = [
    "Ed3nDictionaryAdapter",
    "GardenDictionaryAdapter",
    "InMemoryDictionary",
    "KeyValueDictionary",
    "SemanticKeyMapperAdapter",
    "Hit",
]
