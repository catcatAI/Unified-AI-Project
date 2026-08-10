# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""統一的數據集入口 registry（主幹線後續計畫 §5）。

將遊戲卡片 JSON / 外部字典 JSON 等資料來源，登記為可列出、可載入的
資料集，作為 backbone 查詢/訓練的供給來源。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


class Dataset:
    """單一資料集的結構化描述。

    載入可在建例時（records 給出）或惰性（loader callable）完成。
    """

    def __init__(
        self,
        name: str,
        *,
        path: Optional[str] = None,
        records: Optional[Iterable[Any]] = None,
        loader: Optional[Callable[[], Iterable[Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.path = path
        self.metadata = dict(metadata or {})
        self._records = list(records) if records is not None else None
        self._loader = loader
        self._loaded = records is not None
        if self._records is None:
            self._records = []

    # ------------------------------------------------------------------
    def ensure_loaded(self) -> List[Any]:
        """確保 records 已載入（惰性 loader 觸發），回傳 records。"""
        if not self._loaded:
            if self._loader is None:
                logger.warning("Dataset '%s' has no loader and no records", self.name)
                return []
            self._records = list(self._loader())
            self._loaded = True
            logger.debug("Dataset '%s' loaded (%d records)", self.name, len(self._records))
        return self._records

    @property
    def size(self) -> int:
        return len(self._records)

    @property
    def loaded(self) -> bool:
        return self._loaded

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "size": self.size,
            "loaded": self.loaded,
            "metadata": self.metadata,
        }


class DatasetRegistry:
    """資料集註冊表：列出、載入、依名稱取得。"""

    def __init__(self) -> None:
        self._datasets: Dict[str, Dataset] = {}

    def register(self, name: str, dataset: Dataset) -> None:
        self._datasets[name] = dataset

    def register_records(
        self,
        name: str,
        records: Iterable[Any],
        *,
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dataset:
        dataset = Dataset(name, path=path, records=records, metadata=metadata)
        self.register(name, dataset)
        return dataset

    def register_loader(
        self,
        name: str,
        loader: Callable[[], Iterable[Any]],
        *,
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dataset:
        dataset = Dataset(name, path=path, loader=loader, metadata=metadata)
        self.register(name, dataset)
        return dataset

    # ------------------------------------------------------------------
    def get(self, name: str, default: Any = None) -> Any:
        return self._datasets.get(name, default)

    def names(self) -> List[str]:
        return list(self._datasets.keys())

    def list(self) -> List[Dict[str, Any]]:
        return [d.to_dict() for d in self._datasets.values()]

    def load(self, name: str) -> List[Any]:
        """載入並回傳指定資料集 records；不存在回傳 []。"""
        dataset = self._datasets.get(name)
        if dataset is None:
            return []
        return dataset.ensure_loaded()

    def __contains__(self, name: object) -> bool:
        return name in self._datasets

    def __len__(self) -> int:
        return len(self._datasets)


def load_json_records(
    path: str,
    *,
    records_key: str = "cards",
    name_key: str = "card_id",
    text_keys: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """載入 JSON 檔並正規化為 [{key, text, meta}] records。

    遊戲卡片 JSON（`apps/game-rpg/data/game_cards.json`）預設 key 為
    ``cards``，每張卡以 ``card_id`` 為 id、``name``/``description`` 為
    可檢索文字。
    """
    path_obj = Path(path)
    if not path_obj.is_file():
        logger.warning("Dataset file not found: %s", path)
        return []
    try:
        data = json.loads(path_obj.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("Dataset load failed for %s: %s", path, exc)
        return []
    raw_records = data.get(records_key, []) if isinstance(data, dict) else data
    if not isinstance(raw_records, list):
        return []
    text_keys = text_keys or ["name", "description"]
    records = []
    for raw in raw_records:
        if not isinstance(raw, dict):
            continue
        key = str(raw.get(name_key) or raw.get("name") or "")
        if not key:
            continue
        texts = [str(raw.get(k, "")) for k in text_keys if raw.get(k)]
        meta = dict(raw)
        records.append({"key": key, "text": " ".join(texts).strip(), "meta": meta})
    return records


def register_game_cards(
    registry: DatasetRegistry,
    *,
    path: str = "apps/game-rpg/data/game_cards.json",
    name: str = "game_cards",
) -> Dataset:
    """註冊遊戲卡片資料集（§5 指定）。回傳註冊的 Dataset。"""
    loader = lambda: load_json_records(path)
    return registry.register_loader(name, loader, path=path, metadata={"source": "game-rpg"})


__all__ = ["Dataset", "DatasetRegistry", "load_json_records", "register_game_cards"]
