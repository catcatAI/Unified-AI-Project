# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [A] [L3+]
# =============================================================================
"""
Backbone — 統一註冊、路由、配置、生命週期管理。

取代 ~130 個散落的 get_* 工廠函數，提供統一的元件存取入口。

使用方式:
    from core.backbone import get_backbone
    bb = get_backbone()
    bb.initialize()

    # 統一存取
    intent = bb.engine("intent")
    memory = bb.memory()
    emotion = bb.emotion()
    state = bb.state_matrix()

    # 配置
    enabled = bb.config_bool("semantic_visual", default=False)

    # 硬體自適應
    backend = bb.auto_select("neural_backend")
"""

import logging
import os
import threading
import types
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class _NamesView:
    """輕量 names() 視圖（供 external / datasets 等結構探查）。"""

    def __init__(self, names: list) -> None:
        self._names = list(names)

    def names(self) -> list:
        return list(self._names)

    def __iter__(self):
        return iter(self._names)


class Backbone:
    """統一元件登錄與生命週期管理。

    取代 lifespan.py 中的 ~130 個 _get_* 工廠函數。
    所有引擎透過此處存取，確保單例一致性。
    """

    def __init__(self, config_path: Optional[str] = None):
        self._engines: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._config_path = config_path or self._default_config_path()
        self._config: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._initialized = False
        # 組合式子系統（core/backbone/* mixin 元件）— 惰性實例化
        self._registries: Optional[Any] = None
        self._pairs: Optional[Any] = None
        self._io: Optional[Any] = None
        self._state: Optional[Any] = None
        self._config_obj: Optional[Any] = None
        self._memory_registry: Optional[Any] = None
        self._translator: Optional[Any] = None
        self._learning: Optional[Any] = None
        self._mounts: Optional[Any] = None
        self._external: Optional[Any] = None
        self._theta: Optional[Any] = None
        self._response: Optional[Any] = None
        self._state_sync: Optional[Any] = None
        self._io_pairs: Optional[Any] = None
        self._axes_registries: Dict[str, Any] = {}
        self._free_matrices: Dict[str, Any] = {}
        self._dataset_registry: Any = None

    @staticmethod
    def _default_config_path() -> str:
        base = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "..", "configs", "standard"
        )
        return os.path.abspath(base)

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self):
        """初始化 Backbone — 載入配置並設定預設引擎。"""
        with self._lock:
            if self._initialized:
                return
            self._load_config()
            self._initialized = True
            logger.info("Backbone initialized")

    def _load_config(self):
        """載入骨幹配置。"""
        import yaml

        config_file = os.path.join(self._config_path, "backbone.default.yaml")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    self._config = yaml.safe_load(f) or {}
                logger.info("Backbone config loaded from %s", config_file)
            except Exception as e:
                logger.warning("Failed to load backbone config: %s", e)
                self._config = {}
        else:
            logger.info("No backbone config file found, using defaults")
            self._config = self._default_config()

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        return {
            "engines": {
                "intent": "query_classifier",
                "neural": "auto",
                "knowledge": "hybrid",
                "emotion": "pad",
                "memory": "ham",
                "planning": "default",
            },
            "singletons": ["memory", "state_matrix", "emotion"],
        }

    def engine(self, name: str) -> Optional[Any]:
        """取得指定引擎（懒加載）。"""
        with self._lock:
            if name in self._engines:
                return self._engines[name]
            engine = self._create_engine(name)
            if engine:
                self._engines[name] = engine
            return engine

    def _create_engine(self, name: str) -> Optional[Any]:
        """根據名稱創建引擎實例。"""
        engine_map = {
            "intent": self._create_intent_engine,
            "knowledge": self._create_knowledge_engine,
            "emotion": self._create_emotion_engine,
            "planning": self._create_planning_engine,
        }
        factory = engine_map.get(name)
        if factory:
            try:
                return factory()
            except Exception as e:
                logger.warning("Failed to create engine '%s': %s", name, e)
        return None

    @staticmethod
    def _create_intent_engine():
        from ai.core.query_classifier import QueryClassifier

        return QueryClassifier()

    @staticmethod
    def _create_knowledge_engine():
        from ai.meta.knowledge_pipeline import KnowledgePipeline

        return KnowledgePipeline()

    @staticmethod
    def _create_emotion_engine():
        from ai.alignment.emotion_system import EmotionSystem

        return EmotionSystem()

    @staticmethod
    def _create_planning_engine():
        from ai.reasoning.planning_engine import PlanningEngine

        return PlanningEngine()

    def memory(self, key: str = "memory", default: Any = None) -> Any:
        """取得記憶（統一單例 / 註冊表查找）。"""
        return self.memories.get(key)

    def state_matrix(self) -> Optional[Any]:
        """取得 StateMatrix 單例。"""
        return self._get_singleton("state_matrix", self._create_state_matrix)

    def emotion(self) -> Optional[Any]:
        """取得情緒系統單例。"""
        return self._get_singleton("emotion", self._create_emotion_singleton)

    def _get_singleton(self, name: str, factory) -> Optional[Any]:
        if name in self._singletons:
            return self._singletons[name]
        with self._lock:
            if name in self._singletons:
                return self._singletons[name]
            try:
                instance = factory()
                self._singletons[name] = instance
                return instance
            except Exception as e:
                logger.warning("Failed to create singleton '%s': %s", name, e)
                return None

    @staticmethod
    def _create_memory():
        from ai.memory.ham_memory.ham_manager import HAMMemoryManager

        return HAMMemoryManager()

    @staticmethod
    def _create_state_matrix():
        from core.engine.state_matrix import StateMatrix4D

        return StateMatrix4D()

    @staticmethod
    def _create_emotion_singleton():
        from ai.alignment.emotion_system import EmotionSystem

        return EmotionSystem()

    @property
    def config(self) -> Any:
        """配置門面（BackboneConfig）。"""
        if self._config_obj is None:
            from core.backbone.config import BackboneConfig

            self._config_obj = BackboneConfig()
        return self._config_obj

    def config_bool(self, section: str, default: bool = False) -> bool:
        return bool(self.config.compute_bool(section, default))

    def config_int(self, feature: str, key: str, default: int = 0) -> int:
        return int(self.config.compute_int(feature, key, default))

    def config_float(self, feature: str, key: str, default: float = 0.0) -> float:
        return float(self.config.compute_float(feature, key, default))

    def config_mode(self, key: str, default: str = "auto") -> str:
        return self.config.compute_mode(key, default)

    def auto_select(self, key: str) -> str:
        """硬體自適應元件選擇。

        根據硬體配置自動選擇最適合的元件實作。
        """
        hw_tier = self._config.get("hardware_tier", "balanced")

        selection_map = {
            "neural_backend": {
                "low": "cpu",
                "balanced": "cpu",
                "high": "gpu",
            },
            "precision": {
                "low": "fp32",
                "balanced": "fp16",
                "high": "fp16",
            },
            "batch_strategy": {
                "low": "sequential",
                "balanced": "dynamic",
                "high": "parallel",
            },
        }

        if key in selection_map:
            return selection_map[key].get(hw_tier, "balanced")
        return "default"

    def get_stats(self) -> Dict[str, Any]:
        """取得 Backbone 統計資訊。"""
        return {
            "engines_loaded": len(self._engines),
            "singletons": len(self._singletons),
            "initialized": self._initialized,
            "config_loaded": bool(self._config),
        }

    def summary(self) -> Dict[str, Any]:
        """取得骨幹摘要。"""
        regs = self.registries
        return {
            "matrices": regs.matrices.count(),
            "axes": regs.axes.count(),
            "modules": regs.modules.count(),
            "dictionaries": regs.dictionaries.count(),
            "translators": regs.translators.count(),
            "mountables": len(regs.dictionaries._mountables),
            "pairs": len(self.pairs.pending()) if self._pairs is not None else 0,
            "io_pairs_domain_bound": (
                len(self._io._down_handlers) if self._io is not None else 0
            ),
        }

    def structure(self) -> Dict[str, Any]:
        """取得主幹線結構盤點（各層 section）。"""
        from core.backbone.structure import BackboneStructure

        return BackboneStructure(self).build()

    def inventory(self) -> Dict[str, Any]:
        """取得主幹線結構字典（外部審查用）。"""
        from core.backbone.structure import inventory

        return inventory(self)

    def dump(self, title: str = "BACKBONE", detailed: bool = True) -> str:
        """列印主幹線結構樹文字。"""
        from core.backbone.structure import dump as _dump

        return _dump(self, title=title, detailed=detailed)

    # ------------------------------------------------------------------
    # 組合式子系統：註冊與生命週期（core/backbone/* mixin 元件）
    # ------------------------------------------------------------------
    @property
    def registries(self) -> Any:
        """統一註冊中心（matrix/axis/module/dictionary/translator）。"""
        if self._registries is None:
            from core.backbone.registry import BackboneRegistries

            regs = BackboneRegistries()
            # 預設轉譯器（神經橋 / 語意鍵映射）
            try:
                from core.backbone.translators import (
                    NeuralBridgeTranslator,
                    SemanticKeyMapperTranslator,
                )

                regs.translators.register_rule(
                    "neural_bridge", NeuralBridgeTranslator()
                )
                regs.translators.register_rule(
                    "semantic_key_mapper", SemanticKeyMapperTranslator()
                )
            except Exception as e:
                logger.debug(f"Backbone registries init failed: {e}", exc_info=True)
            self._registries = regs
        return self._registries

    @property
    def pairs(self) -> Any:
        """成對排程器（§5.0 Stability Core）。"""
        if self._pairs is None:
            from core.backbone.pairs import PairScheduler

            self._pairs = PairScheduler()
        return self._pairs

    @property
    def state(self) -> Any:
        """統一狀態讀寫門面（BackboneState）。"""
        if self._state is None:
            from core.backbone.state import BackboneState

            self._state = BackboneState(
                matrix_registry=self.registries.matrices,
                axis_registry=self.registries.axes,
            )
        return self._state

    @property
    def io(self) -> Any:
        """信封路由 + 成對入口（BackboneIO）。"""
        if self._io is None:
            from core.backbone.io import BackboneIO

            self._io = BackboneIO(
                pair_scheduler=self.pairs,
                registries=self.registries,
                state=self.state,
            )
        return self._io

    @property
    def memories(self) -> Any:
        """記憶登錄器（MemoryRegistry）。"""
        if self._memory_registry is None:
            from core.backbone.memory import MemoryRegistry

            self._memory_registry = MemoryRegistry()
        return self._memory_registry

    @property
    def translator(self) -> Any:
        """轉譯器門面（BackboneTranslator）。"""
        if self._translator is None:
            from core.backbone.translate import BackboneTranslator

            self._translator = BackboneTranslator(registry=self.registries.translators)
        return self._translator

    @property
    def learning(self) -> Any:
        """學習協調器（LearningCoordinator）。"""
        if self._learning is None:
            from core.backbone.learning import LearningCoordinator

            self._learning = LearningCoordinator(pair_scheduler=self.pairs)
        return self._learning

    @property
    def mounts(self) -> Any:
        """掛載管理器（MountManager）。"""
        if self._mounts is None:
            from core.backbone.mountable import MountManager

            self._mounts = MountManager()
            # 預設掛載 shared_latent_space 全域 singleton
            try:
                from ai.multimodal.shared_latent_space import get_shared_latent_space

                if not self._mounts.has("shared_latent_space"):
                    self._mounts.register("shared_latent_space", get_shared_latent_space())
            except Exception as e:
                logger.debug(f"Backbone mounts shared_latent_space failed: {e}", exc_info=True)
        return self._mounts

    @property
    def axes_registries(self) -> Dict[str, Any]:
        return self._axes_registries

    @property
    def external(self) -> Any:
        """外部閘道（ExternalGateway）。"""
        if self._external is None:
            from core.backbone.external import ExternalGateway

            self._external = ExternalGateway(pair_scheduler=self.pairs, io=self.io)
        return self._external

    @property
    def theta(self) -> Any:
        """θ 元認知路由橋接（ThetaBridge）。"""
        if self._theta is None:
            from core.backbone.theta import ThetaBridge

            self._theta = ThetaBridge(primary_matrix=self.primary_matrix())
        return self._theta

    @property
    def response(self) -> Any:
        """響應模式選取器（ResponseModeSelector）。"""
        if self._response is None:
            from core.backbone.response import ResponseModeSelector

            self._response = ResponseModeSelector()
        return self._response

    @property
    def state_sync(self) -> Any:
        """CNS domain 訂閱同步器（CNSDomainSync）。"""
        if self._state_sync is None:
            from core.backbone.subscriptions import CNSDomainSync

            self._state_sync = CNSDomainSync(
                state=self.state, matrix=self.primary_matrix()
            )
        return self._state_sync

    @property
    def io_pairs(self) -> Any:
        """成對排程狀態外觀（PairState）。"""
        if self._io_pairs is None:
            from core.backbone.pairs import PairState

            self._io_pairs = PairState(self.pairs)
        return self._io_pairs

    # 矩陣
    def register_matrix(self, name: str, matrix: Any) -> None:
        self.registries.matrices.register(name, matrix)

    def primary_matrix(self) -> Any:
        return self.registries.matrices.primary()

    # 軸
    def register_axis(self, name: str, axis: Any) -> None:
        self.registries.axes.register(name, axis)

    def unregister_axis(self, name: str, axis: Any = None) -> bool:
        return self.registries.axes.unregister(name)

    def get_axis(self, name: str) -> Any:
        return self.registries.axes.get(name)

    def register_axes_registry(self, name: str, registry: Any) -> None:
        self._axes_registries[name] = registry

    def axes_registry(self, name: str = "default", default: Any = None) -> Any:
        if name in self._axes_registries:
            return self._axes_registries[name]
        if name == "default":
            from core.backbone.axes import get_axes_registry

            reg = get_axes_registry("default")
            self._axes_registries["default"] = reg
            return reg
        return default

    # 模組
    def register_module(self, key: str, item: Any, **kwargs: Any) -> None:
        self.registries.modules.register(key, item, **kwargs)

    def unregister_module(self, key: str) -> bool:
        return self.registries.modules.unregister(key)

    def get_module(self, key: str) -> Any:
        return self.registries.modules.get(key)

    def mount_module(self, key: str) -> bool:
        return self.registries.modules.mount(key)

    def unmount_module(self, key: str) -> bool:
        return self.registries.modules.unmount(key)

    # 字典
    def register_dictionary(self, name: str, dic: Any) -> None:
        self.registries.dictionaries.register(name, dic)

    def get_dictionary(self, name: str) -> Any:
        return self.registries.dictionaries.get(name)

    def register_mountable(self, name: str, resource: Any, idle_timeout: float = 300.0) -> None:
        # 包裝為 MountableWrapper 供 dictionary_sources 標記 modality / mountable
        from core.backbone.mountable import MountableWrapper

        wrapped = MountableWrapper(resource, idle_timeout=idle_timeout)
        self.registries.dictionaries.register_mountable(name, wrapped)
        # 與統一掛載管理器（供 mount/access/unmount）
        self.mounts.register(name, resource, idle_timeout=idle_timeout)

    def dictionary_sources(self) -> list:
        return self.registries.dictionaries.sources()

    # 外部閘道
    def register_external(self, name: str, provider: Any) -> None:
        self.external.register(name, provider)

    def unregister_external(self, name: str) -> bool:
        return self.external.unregister(name)

    def external_names(self) -> list:
        return self.external.names()

    async def call_external(self, name: str, method: str, **kwargs: Any) -> Any:
        return await self.external.call_external(name, method, **kwargs)

    # 字典查詢聚合
    def query_dictionary(self, theme: str, input_data: Any = None, top_k: int = 5, **kwargs: Any) -> list:
        if input_data is None:
            input_data = theme
        return self.registries.dictionaries.query(theme, input_data, top_k=top_k, **kwargs)

    def encode_dictionaries(self, theme: str, input_data: Any = None, **kwargs: Any) -> Dict[str, list]:
        if input_data is None:
            input_data = theme
        return self.registries.dictionaries.encode_all(theme, input_data, **kwargs)

    # 成對排程端點
    def submit(self, envelope: Any, timeout: float = 8.0) -> str:
        return self.io.submit(envelope, timeout=timeout)

    def resolve(self, pair_id: str, envelope: Any) -> None:
        return self.io.resolve(pair_id, envelope)

    # 記憶
    def register_memory(self, name: str, backend: Any) -> Any:
        return self.memories.register(name, backend)

    # 學習
    def register_learning(self, name: str, learner: Any) -> None:
        self.learning.register_learning(name, learner)
        self.registries.modules.register("learning:" + name, learner)

    async def trigger_learning(self, user_message: Any, response: Any, context: Any = None) -> Any:
        return await self.learning.trigger(user_message, response, context)

    def subscribe_learning(self, state_store: Any = None) -> bool:
        return self.learning.subscribe(state_store)

    # 訓練
    def register_training(self, name: str, trainer: Any) -> None:
        self.registries.modules.register("training:" + name, trainer)

    def register_training_mount(
        self,
        name: str,
        factory: Any,
        save_func: Any = None,
        load_func: Any = None,
        persistence_path: str = "",
    ) -> None:
        from core.backbone.training import TrainingMount

        mount = TrainingMount(
            name=name,
            factory=factory,
            save_func=save_func,
            load_func=load_func,
            persistence_path=persistence_path,
        )
        self.mounts.register("training:" + name, mount)

    def training_info(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for key, wrapper in self.mounts._resources.items():
            if not key.startswith("training:"):
                continue
            res = wrapper.resource
            if hasattr(res, "info"):
                try:
                    out[key] = res.info()
                    continue
                except Exception:
                    pass
            out[key] = {"mounted": wrapper.is_mounted()}
        return out

    # 轉譯器
    def register_translator(self, name: str, rule: Any) -> None:
        self.registries.translators.register_rule(name, rule)

    def unregister_translator(self, name: str) -> None:
        self.registries.translators.unregister(name)

    def translate(
        self,
        source: str,
        target: str,
        data: Any,
        direction: str = "down",
        **ctx: Any,
    ) -> Any:
        return self.translator.translate(
            source, target, data, direction=direction, **ctx
        )

    # 自由矩陣（theta/SNN/共振/語意/代理/因果/外部）
    def register_free_matrix(self, name: str, matrix: Any) -> None:
        self._free_matrices[name] = matrix
        try:
            self.mounts.register(name, matrix)
        except Exception as e:
            logger.debug(f"Backbone mount {name} failed: {e}", exc_info=True)

    def _free_matrix_entry(self, key: str, matrix: Any) -> Dict[str, Any]:
        raw = (
            getattr(matrix, "registered_modalities", None)
            or getattr(matrix, "modalities", None)
            or getattr(matrix, "_modalities", None)
        )
        if callable(raw):
            try:
                raw = raw()
            except Exception:
                raw = None
        if isinstance(raw, dict):
            mods = list(raw.keys())
        elif isinstance(raw, (list, set, tuple)):
            mods = list(raw)
        else:
            mods = []
        return {
            "key": key,
            "is_free_matrix": True,
            "version": getattr(matrix, "version", None),
            "modalities": mods,
            "latent_dim": getattr(matrix, "_latent_dim", None)
            or getattr(matrix, "latent_dim", None),
        }

    def free_matrices(self) -> list:
        # 確保預設 shared_latent_space 已註冊
        if "shared_latent_space" not in self._free_matrices:
            try:
                from ai.multimodal.shared_latent_space import get_shared_latent_space

                space = get_shared_latent_space()
                self._free_matrices["shared_latent_space"] = space
                try:
                    self.mounts.register("shared_latent_space", space)
                except Exception as e:
                    logger.debug(f"Backbone free_matrices mount failed: {e}", exc_info=True)
            except Exception as e:
                logger.debug(f"Backbone shared_latent_space get failed: {e}", exc_info=True)
        return [self._free_matrix_entry(k, m) for k, m in self._free_matrices.items()]

    def get_free_matrix(self, name: str) -> Optional[Any]:
        return self._free_matrices.get(name)

    def add_free_matrix(self, name: str, matrix: Any) -> None:
        self._free_matrices[name] = matrix

    def list_free_matrices(self) -> list:
        return list(self._free_matrices.keys())

    def remove_free_matrix(self, name: str) -> None:
        self._free_matrices.pop(name, None)

    # 掛載（自由矩陣 / 訓練掛載統一入口）
    def mount(self, key: str) -> bool:
        return bool(self.mounts.mount(key))

    def unmount(self, key: str) -> bool:
        return bool(self.mounts.unmount(key))

    def mounted(self) -> Dict[str, bool]:
        return self.mounts.mounted()

    def access(self, key: str, *args: Any, **kwargs: Any) -> Any:
        wrapper = self.mounts.get(key)
        if wrapper is None:
            return None
        res = wrapper.access(*args, **kwargs)
        if res is not None and hasattr(res, "access"):
            try:
                return res.access(*args, **kwargs)
            except Exception:
                return res
        return res

    # 信封路由
    def send_down(self, envelope: Any, **kwargs: Any) -> Any:
        return self.io.send_down(envelope, **kwargs)

    def send_up(self, envelope: Any, **kwargs: Any) -> Any:
        return self.io.send_up(envelope, **kwargs)

    async def respond(self, user_message: Any, context: Any = None, mode: str = "1:1", **kwargs: Any) -> Any:
        return await self.response.respond(user_message, context=context, mode=mode, **kwargs)

    # 其它骨架掛載點
    def register_pair(self, name: str, pair: Any) -> None:
        self.registries.modules.register("pair:" + name, pair)

    def register_dataset(self, name: str, ds: Any) -> None:
        self.registries.modules.register("dataset:" + name, ds)

    @property
    def datasets(self) -> Any:
        """統一數據集 registry（後續計畫 §5）。"""
        if self._dataset_registry is None:
            from core.backbone.datasets import DatasetRegistry

            self._dataset_registry = DatasetRegistry()
        return self._dataset_registry

    def register_dataset_records(self, name: str, records: Any) -> None:
        self.datasets.register_records(name, records)

    def register_dataset_loader(self, name: str, loader: Any) -> None:
        self.datasets.register_loader(name, loader)

    def load_dataset(self, name: str) -> Any:
        return self.datasets.load(name)

    def datasets_list(self) -> list:
        return [{"name": n} for n in self.datasets.names()]

    def register_security(self, name: str, sec: Any) -> None:
        self.registries.modules.register("security:" + name, sec)

    def register_subscription(self, name: str, sub: Any) -> None:
        self.registries.modules.register("subscription:" + name, sub)

    def register_response(self, name: str, resp: Any) -> None:
        self.registries.modules.register("response:" + name, resp)

    def register_theta(self, name: str, theta: Any) -> None:
        self.registries.modules.register("theta:" + name, theta)

    def bind_state_store(self, store: Any) -> Any:
        """綁定全域狀態庫並重建 CNS domain 同步器。"""
        from core.backbone.state import BackboneState
        from core.backbone.subscriptions import CNSDomainSync

        st = BackboneState(
            state_store=store,
            matrix_registry=self.registries.matrices,
            axis_registry=self.registries.axes,
        )
        self._state_sync = CNSDomainSync(state=st, matrix=self.primary_matrix())
        return self._state_sync

    # ------------------------------------------------------------------
    # 重置
    # ------------------------------------------------------------------
    def clear(self) -> None:
        """重置所有註冊與快取（測試 / 重新初始化用）。"""
        if self._registries is not None:
            self._registries.clear_all()
            self._registries.dictionaries._mountables.clear()
        self._engines.clear()
        self._singletons.clear()
        self._axes_registries.clear()
        self._free_matrices.clear()
        if self._mounts is not None:
            try:
                self._mounts.clear()
            except Exception:
                pass
        if self._pairs is not None:
            try:
                self._pairs.clear()
            except Exception:
                pass
        self._config_obj = None
        self._memory_registry = None
        self._translator = None
        self._learning = None
        self._state = None
        self._io = None
        self._external = None
        self._theta = None
        self._response = None
        self._state_sync = None
        self._io_pairs = None
        if self._dataset_registry is not None:
            try:
                self._dataset_registry = None
            except Exception:
                pass


# 全域單例
_instance = None
_instance_lock = threading.Lock()


def get_backbone() -> Backbone:
    """取得全域 Backbone 單例。"""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = Backbone()
    return _instance


def reset_backbone() -> None:
    """重置全域 Backbone（測試用）。"""
    global _instance
    _instance = None
