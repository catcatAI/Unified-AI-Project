# =============================================================================
# ANGELA-MATRIX: L1-L6[全层] αβγδεθζη [A] L2+
# =============================================================================
#
# 職責: Backbone 主幹線類 — 註冊表 + 路由 + 信封 + 成對排程聚合（§6 backbone.py）
# 維度: ζ 連通維度（跨模組統一入口）；η 執行維度（資源效率）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸主幹線概念
#
# =============================================================================

"""Backbone 主幹線類（§6 backbone.py）。

主幹線是「薄註冊表 + 路由」：不持有業務邏輯，只統一收斂既有元件（狀態矩陣、
潛空間、字典、模組、轉譯器、成對排程）的**對外接線**。

聚合：
- `BackboneRegistries`（五個註冊表：matrix/axis/module/dictionary/translator）
- `PairScheduler` + `PairState`（§5.0 Stability Core）
- `MountManager`（§4 掛載/釋放）
- `BackboneState`（§6 state.py）
- `BackboneIO`（§6 io.py，含 backbone.io 成對入口）
- `BackboneTranslator`（§5.3）
- `BackboneConfig`（§6 config.py）
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from core.backbone.config import BackboneConfig
from core.backbone.contracts import Envelope, IOPair, PairStatus, TranslationRule
from core.backbone.io import BackboneIO
from core.backbone.mountable import MountManager
from core.backbone.pairs import PairScheduler, PairState
from core.backbone.registry import BackboneRegistries
from core.backbone.state import BackboneState
from core.backbone.translate import BackboneTranslator

logger = logging.getLogger("angela_backbone")


class Backbone:
    """主幹線（薄註冊表 + 路由 + 信封 + 成對排程）。"""

    def __init__(self) -> None:
        self.registries = BackboneRegistries()
        self.state_store: Any = None

        self.pairs = PairScheduler(state_store=None)
        self.pair_state = PairState(self.pairs)

        self.mounts = MountManager()
        self.state = BackboneState(
            state_store=None,
            matrix_registry=self.registries.matrices,
            axis_registry=self.registries.axes,
        )
        self.io = BackboneIO(
            pair_scheduler=self.pairs, registries=self.registries, state=self.state
        )
        self.translator = BackboneTranslator(self.registries.translators)
        self.config = BackboneConfig()

        self._io_pairs_bound = False

    # ==================================================================
    # 單例註冊（步驟 A #2）
    # ==================================================================
    def bind_state_store(self, state_store: Any) -> None:
        """綁定 CNS 全域狀態庫（GlobalStateStore），並啟用 io_pairs 持久化。"""
        self.state_store = state_store
        self.state = BackboneState(
            state_store=state_store,
            matrix_registry=self.registries.matrices,
            axis_registry=self.registries.axes,
        )
        self.io.state = self.state
        if not self._io_pairs_bound:
            try:
                state_store.update_state("io_pairs", {}, notify=False)
                self.pairs._state_store = state_store
                self._io_pairs_bound = True
            except Exception as exc:
                logger.warning("failed to bind io_pairs domain: %s", exc)

    # ------------------------------------------------------------------
    # 矩陣 / 座標軸
    # ------------------------------------------------------------------
    def register_matrix(self, key: str, matrix: Any) -> None:
        """註冊狀態矩陣實例（如 `StateMatrix4D`）。"""
        self.registries.matrices.register(key, matrix)

    def register_axis(self, axis: str, obj: Any) -> None:
        """註冊座標軸物件。"""
        self.registries.axes.register(axis, obj)

    def primary_matrix(self) -> Any:
        return self.registries.matrices.primary()

    # ------------------------------------------------------------------
    # 模組 / 字典
    # ------------------------------------------------------------------
    def register_module(
        self,
        key: str,
        module: Any,
        on_mount: Optional[Callable[[], None]] = None,
        on_unmount: Optional[Callable[[], None]] = None,
    ) -> None:
        """註冊元件/模組（Router、ChatService、ED3NEngine…）。"""
        self.registries.modules.register(key, module, on_mount, on_unmount)

    def get_module(self, key: str, default: Any = None) -> Any:
        return self.registries.modules.get(key, default)

    def register_dictionary(self, key: str, dictionary: Any) -> None:
        """註冊字典（DictionaryLayer / VectorDictionary）。"""
        self.registries.dictionaries.register(key, dictionary)

    def get_dictionary(self, key: str, default: Any = None) -> Any:
        return self.registries.dictionaries.get(key, default)

    # ------------------------------------------------------------------
    # 掛載 / 釋放（§4.2）
    # ------------------------------------------------------------------
    def register_mountable(self, key: str, resource: Any, idle_timeout: float = 300.0) -> None:
        """註冊可掛載資源（自動 lazy mount + idle timeout 釋放）。"""
        wrapper = self.mounts.register(key, resource, idle_timeout=idle_timeout)
        self.registries.dictionaries.register_mountable(key, wrapper)

    def mount(self, key: str) -> bool:
        """掛載資源（從磁碟載入 → 記憶體）。"""
        return self.mounts.mount(key)

    def unmount(self, key: str) -> bool:
        """釋放資源（記憶體 → 磁碟 flush，釋放 RAM）。"""
        return self.mounts.unmount(key)

    def access(self, key: str) -> Any:
        """統一入口：回傳已掛載資源（未掛載則 lazy mount）。"""
        return self.mounts.access(key)

    def mounted(self) -> Dict[str, bool]:
        """查詢全部掛載狀態。"""
        return self.mounts.mounted()

    def sweep(self) -> int:
        """掃描閒置逾時資源並自動釋放。"""
        return self.mounts.sweep()

    # ------------------------------------------------------------------
    # 轉譯器（§5.3）
    # ------------------------------------------------------------------
    def register_translator(self, name: str, rule: Any) -> None:
        self.translator.register(name, rule)

    def translate(
        self, source: str, target: str, data: Any, direction: str = "down", **kwargs: Any
    ) -> Any:
        return self.translator.translate(source, target, data, direction=direction, **kwargs)

    # ------------------------------------------------------------------
    # 配置（§6 config.py）
    # ------------------------------------------------------------------
    def config_bool(self, feature: str, default: bool = True) -> bool:
        return self.config.compute_bool(feature, default)

    def config_int(self, feature: str, key: str, default: int = 0) -> int:
        return self.config.compute_int(feature, key, default)

    def config_mode(self, feature: str, default: str = "auto") -> str:
        return self.config.compute_mode(feature, default)

    # ------------------------------------------------------------------
    # 成對排程 / 配對狀態（§5.0）
    # ------------------------------------------------------------------
    @property
    def io_pairs(self) -> PairState:
        """配對狀態查詢門面（§5.0.3）。"""
        return self.pair_state

    def submit(self, envelope: Envelope, timeout: float = 8.0) -> str:
        """提交輸入信封 → 建立 IOPair（§5.0.2）。"""
        return self.pairs.submit(envelope, timeout=timeout)

    def resolve(self, pair_id: str, output_envelope: Envelope) -> None:
        """配對輸出信封 → PAIRED。"""
        self.pairs.resolve(pair_id, output_envelope)

    def send_down(self, envelope: Envelope, **kwargs: Any) -> Any:
        """send_down：下層→中層→上層（使用者請求進入，自動建立 IOPair）。"""
        return self.io.send_down(envelope, **kwargs)

    def send_up(self, envelope: Envelope, **kwargs: Any) -> Any:
        """send_up：下層→中層→上層（回應輸出返回）。"""
        return self.io.send_up(envelope, **kwargs)

    # ------------------------------------------------------------------
    # 學習 / 訓練（§6 learning.py / training.py 預留接線）
    # ------------------------------------------------------------------
    def register_learning(self, name: str, coroutine_factory: Callable) -> None:
        """註冊中層學習協調器（CNS 事件驅動，§6 learning.py）。"""
        self.registries.modules.register(f"learning:{name}", coroutine_factory)

    def register_training(self, name: str, workflow: Callable) -> None:
        """註冊上層訓練工作流（掛載/釋放，§6 training.py）。"""
        self.registries.modules.register(f"training:{name}", workflow)

    # ------------------------------------------------------------------
    # 查詢 / 診斷
    # ------------------------------------------------------------------
    def summary(self) -> Dict[str, Any]:
        """主幹線狀態摘要（診斷用）。"""
        return {
            "matrices": self.registries.matrices.count(),
            "axes": self.registries.axes.count(),
            "modules": self.registries.modules.count(),
            "dictionaries": self.registries.dictionaries.count(),
            "translators": self.registries.translators.count(),
            "mountables": len(self.mounts.mounted()),
            "pairs": {
                "total": len(self.pairs.all()),
                "pending": len(self.pairs.pending()),
                "orphans": len(self.pairs.orphans()),
            },
            "io_pairs_domain_bound": self._io_pairs_bound,
        }

    def clear(self) -> None:
        """清除全部註冊（測試隔離用）。"""
        self.registries.clear_all()
        self.pairs.clear()
        self.mounts.clear()
