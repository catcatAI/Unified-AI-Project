# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""主幹線結構探查與打印 — structure() / dump()。

讓主幹線「打印一下就能知道直接連接著啥、透過啥、又接著啥、都是啥狀態」。

提供：
- ``BackboneStructure``：對 backbone 實例做完整盤點，回傳一棵結構化 dict 樹。
- ``dump(bb, ...)``：把該樹打印成可讀文字。

層次（有意義的分層，各層都有對應註冊資料）：
  1. 核心矩陣（StateMatrix4D）與座標軸
  2. 自由矩陣（SharedLatentSpace + Mountable 掛載狀態）
  3. 字典（MultimodalDictionary: ED3N/GARDEN/semantic/object/space/card）
  4. 模組（Router/ChatService/…）
  5. 轉譯器（Translator: neural_bridge/semantic_key_mapper）
  6. 外部閘道（LLM/weather/drive/…）
  7. 學習/訓練
  8. 記憶
  9. 狀態/CNS 訂閱
  10. 響應模式
  11. 資料集
  12. 成對排程（pairs）
  13. 安全層（掛載於 lifespan，非 backbone 內）
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _safe_len(obj: Any) -> int:
    try:
        return len(obj)
    except TypeError:
        return 0


class BackboneStructure:
    """對單一 backbone 實例做結構化盤點。"""

    def __init__(self, backbone: Any) -> None:
        self.bb = backbone

    # ------------------------------------------------------------------
    # 各層探查
    # ------------------------------------------------------------------
    def matrices(self) -> List[Dict[str, Any]]:
        out = []
        for key in self.bb.registries.matrices.keys():
            mat = self.bb.registries.matrices.get(key)
            row = {"key": key}
            row.update(_safe_matrix_info(mat))
            out.append(row)
        return out

    def axes(self) -> List[Dict[str, Any]]:
        out = []
        for key in self.bb.registries.axes.keys():
            obj = self.bb.registries.axes.get(key)
            out.append({"key": key, "type": type(obj).__name__})
        # 結構化 AxesRegistry（§3 後續計畫）
        for name, reg in getattr(self.bb, "axes_registries", {}).items():
            axes_names = reg.names() if hasattr(reg, "names") else []
            out.append({"key": f"registry:{name}", "axes": axes_names})
        return out

    def free_matrices(self) -> List[Dict[str, Any]]:
        return self.bb.free_matrices()

    def dictionaries(self) -> List[Dict[str, Any]]:
        return self.bb.dictionary_sources()

    def modules(self) -> List[Dict[str, Any]]:
        out = []
        for key in self.bb.registries.modules.keys():
            out.append({"key": key})
        return out

    # 知名內部接線屬性（「透過啥接著啥」的探測白名單）
    _WIRED_ATTRS = (
        "state_matrix",
        "modality_gateway",
        "memory_bridge",
        "ham_memory",
        "_ham_memory",
        "vector_store",
        "_vector_store",
        "garden_engine",
        "_garden_engine",
        "intent_manager",
        "action_executor",
        "biological_integrator",
        "model_bus",
        "_llm_service",
        "lifecycle",
        "emotion_system",
        "crisis_system",
        "training_coordinator",
    )

    def connections(self) -> List[Dict[str, Any]]:
        """探測已註冊模組的內部接線，生成{from, via, to_type}邊。"""
        edges: List[Dict[str, Any]] = []
        for key in self.bb.registries.modules.keys():
            obj = self.bb.registries.modules.get(key)
            if obj is None:
                continue
            for attr in self._WIRED_ATTRS:
                value = getattr(obj, attr, None)
                if value is None:
                    continue
                edges.append({"from": key, "via": attr, "to_type": type(value).__name__})
        return edges

    def translators(self) -> List[Dict[str, Any]]:
        out = []
        for key in self.bb.registries.translators.keys():
            out.append({"key": key})
        return out

    def externals(self) -> List[Dict[str, Any]]:
        return [{"name": n} for n in self.bb.external.names()]

    def learning(self) -> List[Dict[str, Any]]:
        return [{"name": n} for n in self.bb.learning.names()]

    def trainings(self) -> List[Dict[str, Any]]:
        try:
            return self.bb.training_info() or []
        except Exception as e:
            logger.debug(f"trainings failed: {e}", exc_info=True)
            return []

    def memories(self) -> List[Dict[str, Any]]:
        out = []
        for n in self.bb.memories.names():
            mem = self.bb.memories.get(n)
            row = {"name": n, "type": type(mem).__name__ if mem is not None else None}
            if mem is not None and hasattr(mem, "count"):
                try:
                    row["count"] = mem.count()
                except Exception:
                    row["count"] = None
            out.append(row)
        return out

    def datasets(self) -> List[Dict[str, Any]]:
        return self.bb.datasets_list()

    def state_store(self) -> Dict[str, Any]:
        ss = getattr(self.bb, "state_store", None)
        if ss is None:
            return {"bound": False}
        return {
            "bound": True,
            "domain_keys": self._domain_keys_from(ss),
        }

    def _domain_keys_from(self, ss: Any) -> List[str]:
        try:
            return list(ss.domain_keys() if callable(ss.domain_keys) else (ss.domain_keys or []))
        except Exception as e:
            logger.debug(f"_domain_keys_from failed: {e}", exc_info=True)
            return []

    def pairs(self) -> Dict[str, Any]:
        pairs = self.bb.pairs
        all_pairs = pairs.all()
        by_kind: Dict[str, int] = {}
        for p in all_pairs:
            kind = p.get("kind") if isinstance(p, dict) else getattr(p, "kind", "unknown")
            by_kind[kind] = by_kind.get(kind, 0) + 1
        return {
            "total": len(all_pairs),
            "pending": len(pairs.pending()),
            "orphans": len(pairs.orphans()),
            "by_kind": by_kind,
        }

    def io_bound(self) -> bool:
        return bool(getattr(self.bb, "_io_pairs_bound", False))

    def security(self) -> Dict[str, Any]:
        """安全層資訊（lifespan 掛載，主幹線只回報是否已啟用機制）。"""
        try:
            from core.backbone.security import build_security_layer

            layer = build_security_layer(enable_auth=False)
            return {
                "auth_configured": layer.auth is not None,
                "content_filter": layer.content_filter is not None,
                "enable_auth": False,
            }
        except Exception:
            return {"error": True}

    # ------------------------------------------------------------------
    # 樹形組裝
    # ------------------------------------------------------------------
    def build(self) -> Dict[str, Any]:
        return {
            "core_matrix": self.matrices(),
            "axes": self.axes(),
            "free_matrices": self.free_matrices(),
            "dictionaries": self.dictionaries(),
            "modules": self.modules(),
            "translators": self.translators(),
            "external": self.externals(),
            "learning": self.learning(),
            "training": self.trainings(),
            "memory": self.memories(),
            "state_store": self.state_store(),
            "response": {"mode": self._response_mode()},
            "datasets": self.datasets(),
            "pairs": self.pairs(),
            "io_bound": self.io_bound(),
            "security": self.security(),
            "connections": self.connections(),
        }

    def _response_mode(self) -> str:
        try:
            mode = getattr(self.bb.response, "current_mode", None)
            if callable(mode):
                return str(mode())
            return str(mode) if mode else "default"
        except Exception as e:
            logger.debug(f"_response_mode failed: {e}", exc_info=True)
            return "default"


def inventory(backbone: Any) -> Dict[str, Any]:
    """回傳 backbone 結構字典（供外部審查工具使用）。"""
    return BackboneStructure(backbone).build()


def _safe_matrix_info(mat: Any) -> Dict[str, Any]:
    info: Dict[str, Any] = {"type": type(mat).__name__}
    for attr in ("dimensions", "version", "matrix_version"):
        if hasattr(mat, attr):
            val = getattr(mat, attr)
            if callable(val):
                try:
                    val = val()
                except Exception:
                    val = None
            info[attr] = val
    return info


_DISPLAY = {
    "core_matrix": "核心矩陣",
    "axes": "座標軸",
    "free_matrices": "自由矩陣",
    "dictionaries": "字典",
    "modules": "模組",
    "translators": "轉譯器",
    "external": "外部閘道",
    "learning": "學習",
    "training": "訓練",
    "memory": "記憶",
    "state_store": "狀態庫",
    "response": "響應模式",
    "datasets": "數據集",
    "pairs": "成對排程",
    "io_bound": "IO 排程綁定",
    "security": "安全層",
    "connections": "連接線（透過啥接著啥）",
}


def dump(backbone: Any, *, title: str = "BACKBONE", detailed: bool = True) -> str:
    """把 backbone 打印成可讀結構樹文字。

    Args:
        backbone: Backbone 實例。
        title: 標題。
        detailed: True 時列出每個 item 明細，False 只給數量。
    """
    data = inventory(backbone)
    lines: List[str] = []
    width = 74
    lines.append("═" * width)
    lines.append(f"  {title} — 主幹線全覽")
    lines.append("═" * width)

    def _fmt_item(it: Dict[str, Any], label_key: str) -> str:
        rest = {k: v for k, v in it.items() if k != label_key and v is not None and v != ""}
        if not rest:
            return str(it.get(label_key, ""))
        parts = [str(it.get(label_key, ""))]
        for k, v in rest.items():
            parts.append(f"{k}={v}")
        return " ".join(parts)

    for section_key, label in _DISPLAY.items():
        info = data.get(section_key)
        if section_key == "connections":
            if not info:
                lines.append(f"▶ {label}: (無 mod，無邊)")
                continue
            lines.append(f"▶ {label}: {len(info)} 條")
            for edge in info[:40]:
                lines.append(f"    - {edge['from']} ─[{edge['via']}]→ {edge['to_type']}")
            continue
        if isinstance(info, dict):
            meta = ", ".join(f"{k}={v}" for k, v in info.items() if k != "by_kind")
            lines.append(f"▶ {label}: {meta or '(none)'}")
            if isinstance(info.get("by_kind"), dict):
                kinds = ", ".join(f"{k}:{v}" for k, v in info["by_kind"].items())
                lines.append(f"    kinds: {kinds}")
            continue
        if isinstance(info, list):
            count = len(info)
            lines.append(f"▶ {label}: {count} 項")
            if detailed and count:
                label_key = (
                    "name"
                    if section_key in ("external", "learning", "memory", "datasets")
                    else "key"
                )
                for item in info[:40]:
                    lines.append(f"    - {_fmt_item(item, label_key)}")
                if count > 40:
                    lines.append(f"    … (共 {count} 項，只顯示前 40)")
            continue
        lines.append(f"▶ {label}: {info}")

    lines.append("─" * width)
    lines.append("安全層註記: 由 lifespan setup_middleware 掛載（HTTP 下層入口）")
    lines.append(f"IO 排程綁定: {data['io_bound']}")
    lines.append("═" * width)
    return "\n".join(lines)


__all__ = ["BackboneStructure", "inventory", "dump"]
