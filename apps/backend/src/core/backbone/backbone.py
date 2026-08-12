# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [A] [L3+]
# =============================================================================
"""
Backbone — 統一註冊、路由、配置、生命週期管理。

取代 ~130 個散落的 get_* 工廠函數，提供統一的元件存取入口。

使用方式:
    from core.backbone import get_backbone
    bb = get_backbone()
    
    # 統一存取
    intent = bb.engine("intent")
    memory = bb.memory()
    emotion = bb.emotion()
    state = bb.state_matrix()
    
    # 配置
    config = bb.config("engines.intent")
    
    # 硬體自適應
    backend = bb.auto_select("neural_backend")
"""

import logging
import os
import threading
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


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

    @staticmethod
    def _default_config_path() -> str:
        base = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "configs", "standard")
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
        if name in self._engines:
            return self._engines[self._init_lock(name)]

        with self._lock:
            if name in self._engines:
                return self._engines[name]
            engine = self._create_engine(name)
            if engine:
                self._engines[name] = engine
            return engine

    def _init_lock(self, name: str):
        return self._lock

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

    def memory(self) -> Optional[Any]:
        """取得 HAM 記憶單例。"""
        return self._get_singleton("memory", self._create_memory)

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

    def config(self, section: str) -> Any:
        """取得配置值（支援點號路徑）。"""
        keys = section.split(".")
        val = self._config
        for key in keys:
            if isinstance(val, dict):
                val = val.get(key)
            else:
                return None
        return val

    def auto_select(self, key: str) -> str:
        """根據硬體自動選擇最佳實現。"""
        from core.backbone.hardware import HardwareProfile
        hw = HardwareProfile.detect()
        
        if key == "neural_backend":
            if hw.get("gpu_memory_gb", 0) >= 4 and hw.get("torch_available"):
                return "torch"
            elif hw.get("cpu_cores", 1) >= 8:
                return "numpy_fast"
            return "numpy"
        
        if key == "knowledge_backend":
            if hw.get("ram_gb", 0) >= 8:
                return "hybrid"
            return "symbolic"
        
        if key == "memory_backend":
            if hw.get("ram_gb", 0) >= 4:
                return "ham"
            return "minimal"
        
        return "default"

    def get_stats(self) -> Dict[str, Any]:
        return {
            "engines_loaded": list(self._engines.keys()),
            "singletons_loaded": list(self._singletons.keys()),
            "config_loaded": bool(self._config),
        }


_instance: Optional[Backbone] = None


def get_backbone(config_path: Optional[str] = None) -> Backbone:
    """取得 Backbone 單例。"""
    global _instance
    if _instance is None:
        _instance = Backbone(config_path=config_path)
    return _instance


__all__ = ["Backbone", "get_backbone"]
