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

        from core.backbone.external import ExternalGateway

        self.external = ExternalGateway(pair_scheduler=self.pairs, io=self.io)

        from core.backbone.learning import LearningCoordinator

        self.learning = LearningCoordinator(pair_scheduler=self.pairs)

        from core.backbone.response import ResponseModeSelector

        self.response = ResponseModeSelector(pair_scheduler=self.pairs)

        from core.backbone.memory import MemoryRegistry

        self.memories = MemoryRegistry()

        from core.backbone.datasets import DatasetRegistry

        self.datasets = DatasetRegistry()

        from core.backbone.axes import AxesRegistry

        self.axes_registries: Dict[str, AxesRegistry] = {"default": AxesRegistry("default")}

        from core.backbone.theta import ThetaBridge

        self.theta = ThetaBridge(matrix_provider=self.primary_matrix)

        from core.backbone.subscriptions import CNSDomainSync

        self.state_sync = CNSDomainSync(state=self.state, matrix=None)

        self._io_pairs_bound = False

        self.register_default_translators()

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
        self.state_sync.bind_state(self.state)
        self.state_sync.bind_matrix(self.primary_matrix())
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

    def register_axes_registry(self, name: str, axes_registry: Any) -> None:
        """註冊一個結構化 AxesRegistry（後續計畫 §3）。

        與 ``register_axis``（單軸物件）不同：AxesRegistry 是「多軸譜集合」，
        每軸含維度/位置語意。``name`` 例如 "game"（遊戲軸譜）。
        """
        self.axes_registries[name] = axes_registry

    def axes_registry(self, name: str = "default", default: Any = None) -> Any:
        """取得指定名稱的 AxesRegistry；不存在回傳 default（或 None）。"""
        return self.axes_registries.get(name, default)

    # ------------------------------------------------------------------
    # 數據集（後續計畫 §5）
    # ------------------------------------------------------------------
    def register_dataset_records(
        self,
        name: str,
        records: Any,
        *,
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """註冊一個帶 records 的資料集。"""
        return self.datasets.register_records(name, records, path=path, metadata=metadata)

    def register_dataset_loader(
        self,
        name: str,
        loader: Callable[[], Any],
        *,
        path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """註冊一個惰性載入資料集。"""
        return self.datasets.register_loader(name, loader, path=path, metadata=metadata)

    def load_dataset(self, name: str) -> list:
        """載入資料集 records；不存在回傳 []。"""
        return self.datasets.load(name)

    def datasets_list(self) -> list:
        """列出所有已註冊資料集（name/path/size/loaded/metadata）。"""
        return self.datasets.list()

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

    def query_dictionary(self, input_data: Any, top_k: int = 5, **kwargs: Any) -> list:
        """多模態字典統一相似性查詢（步驟 C2 / §3.5）。

        對所有已註冊字典（含未掛載的 mountable）查詢，合併排序後回傳
        [{name, key, score, payload}, ...]。
        """
        return self.registries.dictionaries.query("__all__", input_data, top_k=top_k, **kwargs)

    def encode_dictionaries(self, input_data: Any, **kwargs: Any) -> Dict[str, list]:
        """多模態字典統一編碼（步驟 C2），回傳 {name: [keys, ...]}。"""
        return self.registries.dictionaries.encode_all("__all__", input_data, **kwargs)

    # ------------------------------------------------------------------
    # 外部閘道（§5.5.1 步驟 B3/B4）
    # ------------------------------------------------------------------
    def register_external(self, name: str, provider: Any) -> None:
        """註冊外部服務後端（包裝為 ExternalBackend）。"""
        self.external.register(name, provider)

    def register_external_backend(self, name: str, backend: Any) -> None:
        """註冊已包裝的 ExternalBackend。"""
        self.external.register_backend(name, backend)

    def unregister_external(self, name: str) -> bool:
        return self.external.unregister(name)

    def external_names(self) -> list:
        return self.external.names()

    async def call_external(
        self,
        name: str,
        method: str,
        timeout: float = 8.0,
        retries: Optional[int] = None,
        **kwargs: Any,
    ) -> Any:
        """呼叫外部服務（§5.5.1）— 內建重試/熔斷/rate-limit + 成對追蹤。

        依步驟 B4，`call_external` 內部經 `backbone.io.submit/resolve`，
        每次呼叫獲得成對追蹤與 ORPHAN 診斷。
        """
        return await self.external.call_external(
            name, method, timeout=timeout, retries=retries, **kwargs
        )

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
        resource = self.mounts.access(key)
        # TrainingMount 為雙層包裝：穿透回傳底層工作流實例
        if resource is not None and hasattr(resource, "access") and hasattr(resource, "_instance"):
            return resource.access()
        return resource

    def mounted(self) -> Dict[str, bool]:
        """查詢全部掛載狀態。"""
        return self.mounts.mounted()

    def sweep(self) -> int:
        """掃描閒置逾時資源並自動釋放。"""
        return self.mounts.sweep()

    # ------------------------------------------------------------------
    # 自由矩陣（後續計畫 §1）
    # ------------------------------------------------------------------
    def register_free_matrix(self, key: str, matrix: Any, idle_timeout: float = 300.0) -> None:
        """註冊一個自由矩陣實例（SharedLatentSpace 或具 mount 協定者）。

        經 Mountable 掛載：惰性建例、idle timeout 釋放、backbone.access 讀取。
        與既有 `register_mountable` 相容，但語意聚焦「自由矩陣」。
        """
        self.register_mountable(key, matrix, idle_timeout=idle_timeout)

    def free_matrices(self) -> list:
        """列出所有已註冊自由矩陣的狀態與資訊（不觸發 lazy mount）。

        每一項：{key, mounted, version, latent_dim, modalities, created_at}。
        僅對存取後具 SharedLatentSpace 形狀的實例補全資訊。
        """
        out = []
        for key, is_mounted in self.mounts.mounted().items():
            try:
                instance = self.mounts.access(key)
                info: Dict[str, Any] = {"key": key, "mounted": is_mounted}
                if instance is not None and hasattr(instance, "registered_modalities"):
                    info["version"] = getattr(instance, "version", None)
                    info["latent_dim"] = getattr(instance, "_latent_dim", None)
                    info["modalities"] = instance.registered_modalities()
                    info["created_at"] = getattr(instance, "created_at", None)
                    info["is_free_matrix"] = True
                else:
                    info["is_free_matrix"] = False
                out.append(info)
            except Exception as exc:
                logger.debug("free_matrices skipped %s: %s", key, exc)
        return out

    # ------------------------------------------------------------------
    # 轉譯器（§5.3）
    # ------------------------------------------------------------------
    def register_translator(self, name: str, rule: Any) -> None:
        self.translator.register(name, rule)

    def register_default_translators(self) -> None:
        """註冊內建轉譯器（§5.3 步驟 B2）。

        惰性：`core/backbone/translators.py` 的 `register_default_translators`
        僅註冊規則（neural_bridge / semantic_key_mapper），不實例化重元件。
        """
        try:
            from core.backbone.translators import register_default_translators as _register

            _register(self)
        except Exception as exc:  # pragma: no cover - 轉譯器註冊永不中斷主幹線
            logger.warning("failed to register default translators: %s", exc)

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
        """註冊中層學習協調器（CNS 事件驅動，§6 learning.py）。

        委派給 `self.learning`（LearningCoordinator），
        統一經 CNS `routing.response_generated` 事件驅動。
        """
        self.learning.register_learning(name, coroutine_factory)
        self.registries.modules.register(f"learning:{name}", coroutine_factory)

    def subscribe_learning(self, state_store: Any = None) -> bool:
        """訂閱 CNS 事件驅動學習（§5.5.2）。"""
        return self.learning.subscribe(state_store)

    def trigger_learning(self, user_message: str, response: Any, context: Optional[dict] = None):
        """以 CNS 事件語意觸發所有 learners（fire-and-forget background task）。"""
        return self.learning.trigger(user_message, response, context)

    # ------------------------------------------------------------------
    # 響應模式（§5.6 response.py 選取器）
    # ------------------------------------------------------------------
    async def respond(
        self,
        user_message: str,
        context: Optional[dict] = None,
        mode: str = "1:1",
        **kwargs: Any,
    ):
        """統一響應入口：請求層級選模式（1:1 / layered / stream / layered_stream）。

        委派給 `self.response`（ResponseModeSelector）。
        """
        return await self.response.respond(user_message, context=context, mode=mode, **kwargs)

    # ------------------------------------------------------------------
    # 記憶統一（§11.3 #2 memory.py 登錄器）
    # ------------------------------------------------------------------
    def memory(self, name: str) -> Any:
        """取得統一記憶後端單例（`backbone.memory("ham")`）。

        取代各元件自行 `HAMMemoryManager()` 的分片實例。
        """
        return self.memories.get(name)

    def register_memory(self, name: str, backend: Any) -> bool:
        """註冊記憶後端（類別/實例/factory）。"""
        return self.memories.register(name, backend)

    def register_training(self, name: str, workflow: Callable) -> None:
        """註冊上層訓練工作流（掛載/釋放，§6 training.py）。"""
        self.registries.modules.register(f"training:{name}", workflow)

    def register_training_mount(
        self,
        name: str,
        factory: Callable,
        save_func: Optional[Callable] = None,
        load_func: Optional[Callable] = None,
        persistence_path: str = "",
        idle_timeout: float = 600.0,
    ) -> None:
        """註冊可掛載的訓練工作流（§5.5.3 步驟 C3）。

        包裝為 `TrainingMount`，註冊進 mounts（key `training:{name}`），
        可經 `backbone.mount("training:...")` 掛載 / `unmount` 釋放，
        `access` lazy 建立實例。
        """
        from core.backbone.training import TrainingMount

        mount = TrainingMount(
            name=name,
            factory=factory,
            save_func=save_func,
            load_func=load_func,
            persistence_path=persistence_path,
            idle_timeout=idle_timeout,
        )
        self.mounts.register(f"training:{name}", mount, idle_timeout=idle_timeout)
        self.registries.modules.register(f"training:{name}", lambda: mount.access())

    def training_info(self) -> Dict[str, Any]:
        """查詢全部已註冊訓練工作流的掛載狀態。"""
        out: Dict[str, Dict[str, Any]] = {}
        for key, wrapper in self.mounts._resources.items():
            if key.startswith("training:"):
                resource = getattr(wrapper, "resource", None)
                if resource is not None and hasattr(resource, "info"):
                    try:
                        out[key] = resource.info()
                        continue
                    except Exception:
                        pass
                out[key] = {"name": key, "mounted": wrapper.is_mounted()}
        return out

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
