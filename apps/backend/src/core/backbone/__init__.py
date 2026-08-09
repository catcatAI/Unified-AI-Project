# =============================================================================
# ANGELA-MATRIX: L1-L6[全层] αβγδεθζη [A] L2+
# =============================================================================
#
# 職責: 主幹線套件匯出 — get_backbone() 單例（步驟 A #4，仿 get_shared_latent_space）
# 維度: ζ 連通維度（跨模組統一入口）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸主幹線概念
#
# =============================================================================

"""主幹線套件（§6 core/backbone/）。

對外公開：
- `get_backbone()`：進程級主幹線單例（延遲建立）。
- `Backbone`：主幹線類。
- 協定/結構：`Envelope`、`IOPair`、`PairStatus`、`PairPattern`、`Mountable`。
"""

from __future__ import annotations

from typing import Optional

from core.backbone.backbone import Backbone
from core.backbone.contracts import (
    Envelope,
    EnvelopeKind,
    IOPair,
    Mountable,
    PairPattern,
    PairStatus,
    TranslationRule,
)
from core.backbone.external import ExternalBackend, ExternalGateway
from core.backbone.pairs import (
    PairConflictError,
    PairScheduler,
    PairState,
    get_pair_scheduler,
    reset_pair_scheduler,
)

__all__ = [
    "Backbone",
    "Envelope",
    "EnvelopeKind",
    "ExternalBackend",
    "ExternalGateway",
    "IOPair",
    "Mountable",
    "PairConflictError",
    "PairPattern",
    "PairScheduler",
    "PairState",
    "PairStatus",
    "TranslationRule",
    "get_backbone",
    "get_pair_scheduler",
    "reset_backbone",
    "reset_pair_scheduler",
]

_backbone_instance: Optional[Backbone] = None


def get_backbone() -> Backbone:
    """取得進程級主幹線單例（延遲建立）。

    仿 `get_shared_latent_space` 模式：所有元件（chat_routes、router、
    neural_bridge、lifecycle…）都應經此取得主幹線，而非自行實例化。
    """
    global _backbone_instance
    if _backbone_instance is None:
        _backbone_instance = Backbone()
    return _backbone_instance


def reset_backbone() -> None:
    """測試隔離用：重置主幹線單例。"""
    global _backbone_instance
    _backbone_instance = None
