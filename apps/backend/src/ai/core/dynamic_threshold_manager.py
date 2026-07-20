# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [A] [L3]
# =============================================================================
#
# 职责: 自适应阈值管理和优化
# 维度: 涉及认知维度 (β) 的自适应性和学习曲线
# 安全: 使用 Key A (后端控制) 进行自适应性和安全约束
# 成熟度: L3 等级可以理解和实施自适应性阈值管理
#
# 核心功能:
# - threshold_adaptation: 自适应性阈值调整
# - performance_optimization: 性能优化调整
# - hardware_awareness: 硬件感知优化
# - feedback_loop: 连续反馈循环
#
# =============================================================================

import asyncio
import json
import logging
import time
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from core.system.config.magic_numbers import (
    loop_sleep,
    retry_value,
    timeout_value,
    get_config,
)

from core.system.state_store.global_store import state_store

logger = logging.getLogger(__name__)


class AdaptationMode(Enum):
    """自适应模式"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    LEARNING = "learning"


class OptimizationType(Enum):
    """优化类型"""
    THRESHOLD = "threshold"
    PERFORMANCE = "performance"
    EFFICIENCY = "efficiency"
    ACCURACY = "accuracy"
    LATENCY = "latency"


@dataclass
class ThresholdConfiguration:
    """阈值配置"""
    name: str
    value: float
    min_value: float
    max_value: float
    default_value: float
    adaptation_rate: float
    constraint_type: str  # "hard", "soft", "adaptive"
    is_critical: bool = False


@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: float
    accuracy: float  # 0.0-1.0
    latency: float  # 毫秒
    throughput: float  # 请求/秒
    error_rate: float  # 0.0-1.0
    resource_usage: float  # CPU/GPU使用率 0.0-1.0
    memory_usage: float  # 内存使用率 0.0-1.0


@dataclass
class AdaptationHistory:
    """自适应历史"""
    timestamp: float
    optimization_type: OptimizationType
    before_value: float
    after_value: float
    improvement: float
    performance_gain: float
    feedback: str
    context: Dict[str, Any]


@dataclass
class HardwareConstraint:
    """硬件约束"""
    hardware_profile: str
    max_threshold: float
    optimal_range: Tuple[float, float]
    memory_limit: float
    cpu_limit: float
    gpu_limit: float
    thermal_limit: float


class DynamicThresholdManager:
    """
    自适应性阈值管理和优化系统

    职责: 实时自适应阈值，优化性能与质量的平衡
    维度: 涉及认知维度 (β) 的自适应性和学习曲线
    安全: 使用 Key A (后端控制) 进行自适应性和安全约束
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()

        # 初始化硬件感知
        self.hardware_profile: HardwareProfile = HardwareProfile()

        # 阈值配置
        self.thresholds: Dict[str, ThresholdConfiguration] = {}
        self.performance_thresholds: Dict[str, ThresholdConfiguration] = {}

        # 性能监控
        self.performance_history: deque = deque(maxlen=1000)
        self.resource_usage_history: deque = deque(maxlen=1000)

        # 自适应历史
        self.adaptation_history: deque = deque(maxlen=5000)
        self.optimization_cycles: deque = deque(maxlen=100)

        # 状态跟踪
        self.current_adaptation_mode: AdaptationMode = AdaptationMode.BALANCED
        self.performance_target: Dict[str, float] = {}
        self.optimization_goals: Dict[str, float] = {}

        # 集成组件
        self.hardware_constraints: Dict[str, HardwareConstraint] = {}
        self.feedback_aggregator: Optional[Any] = None
        self.prediction_engine: Optional[Any] = None

        # 控制逻辑
        self.adaptation_rules: List[Dict[str, Any]] = []
        self.constraint_violations: deque = deque(maxlen=100)
        self.emergency_bypass: Dict[str, bool] = {}

        # 初始化
        self._initialize_system()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            # 基础阈值配置
            "thresholds": {
                "confidence_threshold": {
                    "name": "confidence_threshold",
                    "value": 0.5,
                    "min_value": 0.1,
                    "max_value": 0.9,
                    "default_value": 0.5,
                    "adaptation_rate": 0.05,
                    "constraint_type": "adaptive",
                    "is_critical": True,
                },
                "temperature_threshold": {
                    "name": "temperature_threshold",
                    "value": 0.7,
                    "min_value": 0.3,
                    "max_value": 1.0,
                    "default_value": 0.7,
                    "adaptation_rate": 0.08,
                    "constraint_type": "hard",
                    "is_critical": True,
                },
                "pressure_threshold": {
                    "name": "pressure_threshold",
                    "value": 0.6,
                    "min_value": 0.2,
                    "max_value": 0.9,
                    "default_value": 0.6,
                    "adaptation_rate": 0.06,
                    "constraint_type": "soft",
                    "is_critical": False,
                },
                "learning_rate_threshold": {
                    "name": "learning_rate_threshold",
                    "value": 0.3,
                    "min_value": 0.05,
                    "max_value": 0.8,
                    "default_value": 0.3,
                    "adaptation_rate": 0.04,
                    "constraint_type": "adaptive",
                    "is_critical": False,
                },
                "diversity_threshold": {
                    "name": "diversity_threshold",
                    "value": 0.4,
                    "min_value": 0.1,
                    "max_value": 0.8,
                    "default_value": 0.4,
                    "adaptation_rate": 0.07,
                    "constraint_type": "soft",
                    "is_critical": False,
                },
            },
            # 性能阈值配置
            "performance_thresholds": {
                "max_latency_ms": {
                    "name": "max_latency_ms",
                    "value": 100.0,
                    "min_value": 10.0,
                    "max_value": 1000.0,
                    "default_value": 100.0,
                    "adaptation_rate": 0.1,
                    "constraint_type": "hard",
                    "is_critical": True,
                },
                "min_accuracy": {
                    "name": "min_accuracy",
                    "value": 0.85,
                    "min_value": 0.5,
                    "max_value": 0.99,
                    "default_value": 0.85,
                    "adaptation_rate": 0.05,
                    \"constraint_type\": \"hard\",
                    \"is_critical\": True,
                },
                \"target_throughput\": {
                    \"name\": \"target_throughput\",
                    \"value\": 1000.0,
                    \"min_value\": 100.0,
                    \"max_value\": 10000.0,
                    \"default_value\": 1000.0,
                    \"adaptation_rate\": 0.08,
                    \"constraint_type\": \"soft\",
                    \"is_critical\": False,
                },
                \"max_memory_usage\": {
                    \"name\": \"max_memory_usage\",
                    \"value\": 0.8,
                    \"min_value\": 0.3,
                    \"max_value\": 0.95,
                    \"default_value\": 0.8,
                    \"adaptation_rate\": 0.06,
                    \"constraint_type\": \"hard\",
                    \"is_critical\": True,
                },
            },
            # 自适应配置
            \"adaptation\": {
                \"learning_rate\": 0.01,
                \"momentum\": 0.9,
                \"Exploration_factor\": 0.1,
                \"reward_decay\": 0.95,
                \"min_adaptation_interval_ms\": 100,
                \"max_adaptation_frequency_per_minute\": 10,
            },
            # 硬件配置
            \"hardware\": {
                \"enable_hardware_awareness\": True,
                \"auto_detect_profile\": True,
                \"apply_hardware_constraints\": True,
            },
            # 集成配置
            \"integration\": {
                \"enable_feedback_aggregation\": True,
                \"enable_prediction_engine\": True,
                \"integration_timeout_ms\": 500,
            },
            # 日志记录配置
            \"logging\": {
                \"enable_adaptation_logging\": True,
                \"enable_performance_logging\": True,
                \"adaptation_log_level\": \"INFO\",
            },
        }

    def _initialize_system(self) -> None:
        \"\"\"初始化系统\"\"\"\n        try:\n            # 初始化硬件配置\n            if self.config[\"hardware\"][\"enable_hardware_awareness\"]:\n                self.hardware_profile = HardwareProfile()\n                self._load_hardware_constraints()\n\n            # 初始化阈值配置\n            self.thresholds = {\n                key: ThresholdConfiguration(**config)\n                for key, config in self.config[\"thresholds\"].items()\n            }\n\n            # 初始化性能阈值配置\n            self.performance_thresholds = {\n                key: ThresholdConfiguration(**config)\n                for key, config in self.config[\"performance_thresholds\"].items()\n            }\n\n            # 初始化自适应规则\n            self._initialize_adaptation_rules()\n\n            # 加载默认性能目标\n            self._load_default_performance_targets()\n\n            # 初始化反馈聚合器和预测引擎\n            if self.config[\"integration\"][\"enable_feedback_aggregation\"]:\n                self._initialize_feedback_aggregator()\n\n            if self.config[\"integration\"][\"enable_prediction_engine\"]:\n                self._initialize_prediction_engine()\n\n            logger.info(\"DynamicThresholdManager initialized successfully\")\n\n        except Exception as e:\n            logger.error(f\"Error initializing DynamicThresholdManager: {e}\", exc_info=True)\n            raise\n\n    def _load_hardware_constraints(self) -> None:\n        \"\"\"加载硬件约束\"\"\"\n        try:\n            if not self.hardware_profile:\n                return\n\n            profile_name = self.hardware_profile.get_profile_name()\n\n            # 根据硬件配置加载约束\n            hardware_configs = {\n                \"high_performance_desktop\": HardwareConstraint(\n                    hardware_profile=\"high_performance_desktop\",\n                    max_threshold=1.0,\n                    optimal_range=(0.7, 0.95),\n                    memory_limit=0.9,\n                    cpu_limit=1.0,\n                    gpu_limit=1.0,\n                    thermal_limit=0.85,\n                ),\n                \"laptop_normal\": HardwareConstraint(\n                    hardware_profile=\"laptop_normal\",\n                    max_threshold=0.85,\n                    optimal_range=(0.6, 0.85),\n                    memory_limit=0.8,\n                    cpu_limit=0.8,\n                    gpu_limit=0.7,\n                    thermal_limit=0.75,\n                ),\n                \"laptop_power_saver\": HardwareConstraint(\n                    hardware_profile=\"laptop_power_saver\",\n                    max_threshold=0.7,\n                    optimal_range=(0.5, 0.7),\n                    memory_limit=0.7,\n                    cpu_limit=0.7,\n                    gpu_limit=0.5,\n                    thermal_limit=0.65,\n                ),\n                \"low_power_device\": HardwareConstraint(\n                    hardware_profile=\"low_power_device\",\n                    max_threshold=0.6,\n                    optimal_range=(0.4, 0.6),\n                    memory_limit=0.6,\n                    cpu_limit=0.6,\n                    gpu_limit=0.4,\n                    thermal_limit=0.55,\n                ),\n                \"server_cloud\": HardwareConstraint(\n                    hardware_profile=\"server_cloud\",\n                    max_threshold=1.0,\n                    optimal_range=(0.8, 1.0),\n                    memory_limit=0.95,\n                    cpu_limit=1.0,\n                    gpu_limit=1.0,\n                    thermal_limit=0.9,\n                ),\n            }\n\n            self.hardware_constraints = {\n                profile: config\n                for config_name, config in hardware_configs.items()\n                if config_name in self.hardware_profile.get_hardware_profile()\n            }\n\n            logger.debug(f\"Loaded {len(self.hardware_constraints)} hardware constraint sets\")\n\n        except Exception as e:\n            logger.error(f\"Error loading hardware constraints: {e}\", exc_info=True)\n\n    def _initialize_adaptation_rules(self) -> None:\n        \"\"\"初始化自适应规则\"\"\"\n        self.adaptation_rules = [\n            {\n                \"name\": \"performance_degradation\",\n                \"condition\": lambda m, p, h: p[\"latency\"] > self.performance_thresholds[\"max_latency_ms\"].value * 1.5,\n                \"action\": \"increase_threshold\",\n                \"target_metric\": \"max_latency_ms\",\n                \"adjustment_factor\": 1.2,\n            },\n            {\n                \"name\": \"accuracy_drop\",\n                \"condition\": lambda m, p, h: p[\"accuracy\"] < self.performance_thresholds[\"min_accuracy\"].value * 0.9,\n                \"action\": \"decrease_threshold\",\n                \"target_metric\": \"confidence_threshold\",\n                \"adjustment_factor\": 0.9,\n            },\n            {\n                \"name\": \"resource_pressure\",\n                \"condition\": lambda m, p, h: p[\"resource_usage\"] > 0.8 or p[\"memory_usage\"] > 0.8,\n                \"action\": \"reduce_thresholds\",\n                \"target_metrics\": [\"confidence_threshold\", \"learning_rate_threshold\"],\n                \"adjustment_factor\": 0.8,\n            },\n            {\n                \"name\": \"hardware_constraint\",\n                \"condition\": lambda m, p, h: h[\"profile\"] != \"high_performance_desktop\" and m[\"overall_score\"] > 0.9,\n                \"action\": \"apply_hardware_limits\",\n                \"target_metrics\": [\"confidence_threshold\", \"temperature_threshold\"],\n                \"adjustment_factor\": 0.9,\n            },\n            {\n                \"name\": \"adaptation_success\",\n                \"condition\": lambda m, p, h: m.get(\"improvement\", 0) > 0.1,\n                \"action\": \"increase_learning_rate\",\n                \"target_metric\": \"learning_rate\",\n                \"adjustment_factor\": 1.1,\n            },\n        ]\n\n    def _load_default_performance_targets(self) -> None:\n        \"\"\"加载默认性能目标\"\"\"\n        self.performance_target = {\n            \"accuracy\": 0.9,\n            \"latency\": 100.0,\n            \"throughput\": 1000.0,\n            \"error_rate\": 0.05,\n            \"resource_usage\": 0.7,\n            \"memory_usage\": 0.8,\n        }\n\n        self.optimization_goals = {\n            \"confidence_threshold\": 0.8,\n            \"temperature_threshold\": 0.8,\n            \"pressure_threshold\": 0.7,\n            \"learning_rate_threshold\": 0.4,\n            \"diversity_threshold\": 0.6,\n            \"max_latency_ms\": 50.0,\n            \"min_accuracy\": 0.95,\n            \"target_throughput\": 2000.0,\n            \"max_memory_usage\": 0.9,\n        }\n\n    def _initialize_feedback_aggregator(self) -> None:\n        \"\"\"初始化反馈聚合器\"\"\"\n        try:\n            from services.llm.llm_decision_loop import LLMDecisionLoop\n\n            self.feedback_aggregator = LLMDecisionLoop()\n            logger.debug(\"Feedback aggregator initialized\")\n\n        except ImportError:\n            logger.warning(\"LLM DecisionLoop not available, skipping feedback aggregator initialization\")\n        except Exception as e:\n            logger.error(f\"Error initializing feedback aggregator: {e}\", exc_info=True)\n\n    def _initialize_prediction_engine(self) -> None:\n        \"\"\"初始化预测引擎\"\"\"\n        try:\n            from ai.garden.garden_engine import GARDENEngine\n\n            self.prediction_engine = GARDENEngine()\n            logger.debug(\"Prediction engine initialized\")\n\n        except ImportError:\n            logger.warning(\"GARDENEngine not available, skipping prediction engine initialization\")\n        except Exception as e:\n            logger.error(f\"Error initializing prediction engine: {e}\", exc_info=True)\n\n    def evaluate_system_state(\n        self,\n        metrics: Dict[str, Any],\n        context: Optional[Dict[str, Any]] = None,\n    ) -> Dict[str, Any]:\n        \"\"\"\n        评估系统状态并确定是否需要自适应\n\n        Args:\n            metrics: 性能指标\n            context: 上下文信息\n\n        Returns:\n            Dict: 评估结果\n        \"\"\"\n        try:\n            # 收集系统信息\n            system_info = self._collect_system_info()\n\n            # 评估需要自适应\n            needs_adaptation = self._check_adaptation_needs(metrics, system_info, context or {})\n\n            result = {\n                \"timestamp\": time.time(),\n                \"needs_adaptation\": needs_adaptation,\n                \"metrics\": metrics,\n                \"system_info\": system_info,\n                \"adaptation_recommendations\": [],\n                \"urgency_level\": \"low\",\n            }\n\n            if needs_adaptation:\n                recommendations = self._generate_adaptation_recommendations(\n                    metrics, system_info, context or {}\n                )\n                result[\"adaptation_recommendations\"] = recommendations\n                result[\"urgency_level\"] = self._calculate_urgency_level(metrics, system_info)\n\n            return result\n\n        except Exception as e:\n            logger.error(f\"Error evaluating system state: {e}\", exc_info=True)\n            return {\n                \"timestamp\": time.time(),\n                \"needs_adaptation\": False,\n                \"metrics\": metrics,\n                \"system_info\": {},\n                \"adaptation_recommendations\": [],\n                \"urgency_level\": \"error\",\n                \"error\": str(e),\n            }\n\n    def adapt_thresholds(\n        self,\n        metrics: Dict[str, Any],\n        context: Optional[Dict[str, Any]] = None,\n        force_adaptation: bool = False,\n    ) -> Dict[str, Any]:\n        \"\"\"\n        执行自适应操作\n\n        Args:\n            metrics: 性能指标\n            context: 上下文信息\n            force_adaptation: 是否强制自适应\n\n        Returns:\n            Dict: 自适应结果\n        \"\"\"\n        try:\n            # 检查是否需要自适应\n            state_result = self.evaluate_system_state(metrics, context)\n\n            if not state_result[\"needs_adaptation\"] and not force_adaptation:\n                return {\n                    \"timestamp\": time.time(),\n                    \"adapted\": False,\n                    \"reason\": \"No adaptation needed\",\n                    \"metrics\": metrics,\n                    \"before\": {},\n                    \"after\": {},\n                    \"improvements\": {},\n                }\n\n            # 收集当前阈值\n            before_thresholds = self._collect_current_thresholds()\n\n            # 执行自适应\n            adaptations = self._execute_adaptations(metrics, context or {}, state_result[\"urgency_level\"])\n\n            # 获取适应后的阈值\n            after_thresholds = self._collect_current_thresholds()\n\n            # 计算改进\n            improvements = {}\n            for key in after_thresholds:\n                if key in before_thresholds:\n                    improvement = (after_thresholds[key] - before_thresholds[key]) / before_thresholds[key]\n                    improvements[key] = improvement\n\n            # 记录自适应\n            adaptation_record = {\n                \"timestamp\": time.time(),\n                \"metrics\": metrics,\n                \"context\": context,\n                \"urgency_level\": state_result[\"urgency_level\"],\n                \"before\": before_thresholds,\n                \"after\": after_thresholds,\n                \"improvements\": improvements,\n                \"adaptations\": adaptations,\n                \"success\": sum(1 for imp in improvements.values() if abs(imp) > 0.01) > 0,\n            }\n\n            self.optimization_cycles.append(adaptation_record)\n\n            # 触发事件\n            if adaptations:\n                state_store.emit_event(\n                    \"threshold.adapted\",\n                    {\n                        \"timestamp\": time.time(),\n                        \"adaptations\": adaptations,\n                        \"improvements\": improvements,\n                        \"urgency_level\": state_result[\"urgency_level\"],\n                        \"success\": adaptation_record[\"success\"],\n                    },\n                )\n\n            logger.debug(\n                f\"Threshold adaptation completed - adaptations: {len(adaptations)}, success: {adaptation_record['success']}\"\n            )\n\n            return {\n                \"timestamp\": time.time(),\n                \"adapted\": True,\n                \"reason\": \"Adaptation completed\",\n                \"urgency_level\": state_result[\"urgency_level\"],\n                \"metrics\": metrics,\n                \"before\": before_thresholds,\n                \"after\": after_thresholds,\n                \"improvements\": improvements,\n                \"adaptations\": adaptations,\n                \"success\": adaptation_record[\"success\"],\n            }\n\n        except Exception as e:\n            logger.error(f\"Error adapting thresholds: {e}\", exc_info=True)\n            return {\n                \"timestamp\": time.time(),\n                \"adapted\": False,\n                \"reason\": f\"Error: {e}\",\n                \"urgency_level\": \"error\",\n                \"metrics\": metrics,\n                \"before\": {},\n                \"after\": {},\n                \"improvements\": {},\n                \"adaptations\": {},\n                \"success\": False,\n                \"error\": str(e),\n            }\n\n    def get_optimized_thresholds(\n        self,\n        system_state: Optional[Dict[str, Any]] = None,\n    ) -> Dict[str, Any]:\n        \"\"\"\n        获取优化后的阈值\n\n        Args:\n            system_state: 系统状态信息\n\n        Returns:\n            Dict: 优化后的阈值\n        \"\"\"\n        try:\n            thresholds = {}\n\n            for name, config in self.thresholds.items():\n                optimized_value = self._calculate_optimized_threshold(\n                    name, config, system_state\n                )\n                thresholds[name] = {\n                    \"name\": name,\n                    \"value\": optimized_value,\n                    \"is_critical\": config.is_critical,\n                    \"constraint_type\": config.constraint_type,\n                    \"adaptation_rate\": config.adaptation_rate,\n                    \"optimized\": True,\n                }\n\n            for name, config in self.performance_thresholds.items():\n                optimized_value = self._calculate_optimized_threshold(\n                    name, config, system_state\n                )\n                thresholds[name] = {\n                    \"name\": name,\n                    \"value\": optimized_value,\n                    \"is_critical\": config.is_critical,\n                    \"constraint_type\": config.constraint_type,\n                    \"adaptation_rate\": config.adaptation_rate,\n                    \"optimized\": True,\n                }\n\n            return {\n                \"timestamp\": time.time(),\n                \"thresholds\": thresholds,\n                \"optimization_source\": \"dynamic\",\n                \"adaptation_mode\": self.current_adaptation_mode.value,\n                \"confidence\": self._calculate_optimization_confidence(),\n                \"hardware_aware\": self.config[\"hardware\"][\"enable_hardware_awareness\"],\n            }\n\n        except Exception as e:\n            logger.error(f\"Error getting optimized thresholds: {e}\", exc_info=True)\n            return self._get_default_thresholds()\n\n    def get_optimized_thresholds(\n        self,\n        system_state: Optional[Dict[str, Any]] = None,\n    ) -> Dict[str, Any]:\n        \"\"\"\n        获取优化后的阈值\n\n        Args:\n            system_state: 系统状态信息\n\n        Returns:\n            Dict: 优化后的阈值\n        \"\"\"\n        try:\n            thresholds = {}\n\n            for name, config in self.thresholds.items():\n                optimized_value = self._calculate_optimized_threshold(\n                    name, config, system_state\n                )\n                thresholds[name] = {\n                    \"name\": name,\n                    \"value\": optimized_value,\n                    \"is_critical\": config.is_critical,\n                    \"constraint_type\": config.constraint_type,\n                    \"adaptation_rate\": config.adaptation_rate,\n                    \"optimized\": True,\n                }\n\n            for name, config in self.performance_thresholds.items():\n                optimized_value = self._calculate_optimized_threshold(\n                    name, config, system_state\n                )\n                thresholds[name] = {\n                    \"name\": name,\n                    \"value\": optimized_value,\n                    \"is_critical\": config.is_critical,\n                    \"constraint_type\": config.constraint_type,\n                    \"adaptation_rate\": config.adaptation_rate,\n                    \"optimized\": True,\n                }\n\n            return {\n                \"timestamp\": time.time(),\n                \"thresholds\": thresholds,\n                \"optimization_source\": \"dynamic\",\n                \"adaptation_mode\": self.current_adaptation_mode.value,\n                \"confidence\": self._calculate_optimization_confidence(),\n                \"hardware_aware\": self.config[\"hardware\"][\"enable_hardware_awareness\"],\n            }\n\n        except Exception as e:\n            logger.error(f\"Error getting optimized thresholds: {e}\", exc_info=True)\n            return self._get_default_thresholds()\n\n    def record_performance_metrics(\n        self,\n        metrics: Dict[str, Any],\n        context: Optional[Dict[str, Any]] = None,\n    ) -> None:\n        \"\"\"\n        记录性能指标\n\n        Args:\n            metrics: 性能指标\n            context: 上下文信息\n        \"\"\"\n        try:\n            # 创建性能指标记录\n            metric_record = PerformanceMetrics(\n                timestamp=time.time(),\n                accuracy=metrics.get(\"accuracy\", 0.0),\n                latency=metrics.get(\"latency\", 0.0),\n                throughput=metrics.get(\"throughput\", 0.0),\n                error_rate=metrics.get(\"error_rate\", 0.0),\n                resource_usage=metrics.get(\"resource_usage\", 0.0),\n                memory_usage=metrics.get(\"memory_usage\", 0.0),\n            )\n\n            self.performance_history.append(metric_record)\n\n            # 记录资源使用情况\n            if \"resource_usage\" in metrics:\n                self.resource_usage_history.append(\n                    {\"timestamp\": time.time(), \"usage\": metrics[\"resource_usage\"]}\n                )\n\n            # 检查是否需要自适应\n            if len(self.performance_history) >= 10:\n                self._check_and_adapt_if_needed(context)\n\n            logger.debug(f\"Performance metrics recorded - accuracy: {metrics.get('accuracy', 0.0):.2f}, latency: {metrics.get('latency', 0.0):.2f}ms\")\n\n        except Exception as e:\n            logger.error(f\"Error recording performance metrics: {e}\", exc_info=True)\n\n    def get_adaptation_analytics(\n        self,\n        time_window_minutes: int = 60,\n    ) -> Dict[str, Any]:\n        \"\"\"\n        获取自适应分析数据\n\n        Args:\n            time_window_minutes: 时间窗口（分钟）\n\n        Returns:\n            Dict: 自适应分析结果\n        \"\"\"\n        try:\n            # 过滤历史记录\n            end_time = time.time()\n            start_time = end_time - (time_window_minutes * 60.0)\n\n            # 计算自适应统计\n            adaptation_stats = self._calculate_adaptation_statistics(start_time, end_time)\n            threshold_stats = self._calculate_threshold_statistics(start_time, end_time)\n            performance_trends = self._calculate_performance_trends(start_time, end_time)\n\n            return {\n                \"timestamp\": time_time(),\n                \"time_window_minutes\": time_window_minutes,\n                \"adaptation_stats\": adaptation_stats,\n                \"threshold_stats\": threshold_stats,\n                \"performance_trends\": performance_trends,\n                \"current_adaptation_mode\": self.current_adaptation_mode.value,\n                \"adaptation_efficiency\": self._calculate_adaptation_efficiency(),\n                \"optimization_effectiveness\": self._calculate_optimization_effectiveness(),\n            }\n\n        except Exception as e:\n            logger.error(f\"Error getting adaptation analytics: {e}\", exc_info=True)\n            return {\n                \"timestamp\": time.time(),\n                \"error\": str(e),\n            }\n\n    def _collect_system_info(self) -> Dict[str, Any]:\n        \"\"\"收集系统信息\"\"\"\n        try:\n            system_info = {}\n\n            # 硬件信息\n            if self.hardware_profile:\n                profile_name = self.hardware_profile.get_profile_name()\n                system_info[\"hardware_profile\"] = profile_name\n                system_info[\"hardware_constraints\"] = self.hardware_constraints.get(profile_name, {})\n\n            # 适应模式\n            system_info[\"adaptation_mode\"] = self.current_adaptation_mode.value\n            system_info[\"adaptation_rules_count\"] = len(self.adaptation_rules)\n\n            # 性能目标\n            system_info[\"performance_targets\"] = self.performance_target\n            system_info[\"optimization_goals\"] = self.optimization_goals\n\n            return system_info\n\n        except Exception as e:\n            logger.error(f\"Error collecting system info: {e}\", exc_info=True)\n            return {}\n\n    def _check_adaptation_needs(\n        self,\n        metrics: Dict[str, Any],\n        system_info: Dict[str, Any],\n        context: Dict[str, Any],\n    ) -> bool:\n        \"\"\"检查是否需要自适应\"\"\"\n        try:\n            # 检查紧急情况\n            if context.get(\"emergency_mode\", False):\n                return True\n\n            # 检查阈值违规\n            threshold_violations = self._check_threshold_violations(metrics, system_info)\n            if threshold_violations:\n                return True\n\n            # 检查性能目标\n            performance_issues = self._check_performance_issues(metrics, system_info)\n            if performance_issues:\n                return True\n\n            # 检查自适应机会\n            adaptation_opportunities = self._check_adaptation_opportunities(metrics, system_info)\n            if adaptation_opportunities:\n                return True\n\n            # 检查硬件约束\n            hardware_issues = self._check_hardware_constraints(system_info)\n            if hardware_issues:\n                return True\n\n            return False\n\n        except Exception as e:\n            logger.error(f\"Error checking adaptation needs: {e}\", exc_info=True)\n            return False\n\n    def _check_threshold_violations(\n        self,\n        metrics: Dict[str, Any],\n        system_info: Dict[str, Any],\n    ) -> List[str]:\n        \"\"\"检查阈值违规\"\"\"\n        violations = []\n\n        # 检查关键性能指标\n        if metrics.get(\"latency\", 0) > self.performance_thresholds[\"max_latency_ms\"].value:\n            violations.append(\"latency_exceeded\")\n\n        if metrics.get(\"accuracy\", 0) < self.performance_thresholds[\"min_accuracy\"].value:\n            violations.append(\"accuracy_below_threshold\")\n\n        if metrics.get(\"memory_usage\", 0) > self.performance_thresholds[\"max_memory_usage\"].value:\n            violations.append(\"memory_usage_exceeded\")\n\n        # 检查硬件约束\n        if \"hardware_constraints\" in system_info:\n            constraints = system_info[\"hardware_constraints\"]\n            if metrics.get(\"resource_usage\", 0) > constraints.get(\"cpu_limit\", 1.0):\n                violations.append(\"cpu_usage_exceeded\")\n            if metrics.get(\"memory_usage\", 0) > constraints.get(\"memory_limit\", 1.0):\n                violations.append(\"memory_usage_exceeded\")\n            if metrics.get(\"resource_usage\", 0) > constraints.get(\"thermal_limit\", 1.0):\n                violations.append(\"thermal_limit_exceeded\")\n\n        return violations\n\n    def _check_performance_issues(\n        self,\n        metrics: Dict[str, Any],\n        system_info: Dict[str, Any],\n    ) -> List[str]:\n        \"\"\"检查性能问题\"\"\"\n        issues = []\n\n        # 检查延迟是否太高\n        if metrics.get(\"latency\", 0) > self.performance_thresholds[\"max_latency_ms\"].value * 2:\n            issues.append(\"high_latency\")\n\n        # 检查准确率是否太低\n        if metrics.get(\"accuracy\", 0) < self.performance_thresholds[\"min_accuracy\"].value * 0.9:\n            issues.append(\"low_accuracy\")\n\n        # 检查错误率是否太高\n        if metrics.get(\"error_rate\", 0) > 0.1:\n            issues.append(\"high_error_rate\")\n\n        return issues\n\n    def _check_adaptation_opportunities(\n        self,\n        metrics: Dict[str, Any],\n        system_info: Dict[str, Any],\n    ) -> List[str]:\n        \"\"\"检查自适应机会\"\"\"\n        opportunities = []\n\n        # 检查是否有性能改进空间\n        if metrics.get(\"latency\", 0) > 100.0:\n            opportunities.append(\"latency_optimization\")\n\n        if metrics.get(\"accuracy\", 0) < 0.9:\n            opportunities.append(\"accuracy_optimization\")\n\n        # 检查是否有资源利用不足\n        if metrics.get(\"resource_usage\", 0) < 0.5:\n            opportunities.append(\"resource_reallocation\")\n\n        return opportunities\n\n    def _check_hardware_constraints(\n        self,\n        system_info: Dict[str, Any],\n    ) -> bool:\n        \"\"\"检查硬件约束问题\"\"\"\n        if \"hardware_constraints\" not in system_info:\n            return False\n\n        constraints = system_info[\"hardware_constraints\"]\n        return constraints.get(\"cpu_limit\", 1.0) < 0.8 or constraints.get(\"memory_limit\", 1.0) < 0.8\n\n    def _generate_adaptation_recommendations(\n        self,\n        metrics: Dict[str, Any],\n        system_info: Dict[str, Any],\n        context: Dict[str, Any],\n    ) -> List[str]:\n        \"\"\"生成自适应建议\"\"\"\n        recommendations = []\n\n        # 根据不同情况生成建议\n        if metrics.get(\"latency\", 0) > self.performance_thresholds[\"max_latency_ms\"].value * 1.5:\n            recommendations.append(\"优先优化延迟\")\n\n        if metrics.get(\"accuracy\", 0) < self.performance_thresholds[\"min_accuracy\"].value:\n            recommendations.append(\"优化模型准确率\")\n\n        if metrics.get(\"memory_usage\", 0) > self.performance_thresholds[\"max_memory_usage\"].value:\n            recommendations.append(\"优化内存使用\")\n\n        if system_info.get(\"hardware_profile\") == \"low_power_device\":\n            recommendations.append(\"启用节电模式\")\n\n        if context.get(\"load_level\") == \"high\":\n            recommendations.append(\"降低处理频率，保持服务稳定性\")\n\n        return recommendations\n\n    def _calculate_urgency_level(\n        self,\n        metrics: Dict[str, Any],\n        system_info: Dict[str, Any],\n    ) -> str:\n        \"\"\"计算紧急程度\"\"\"\n        urgency = \"low\"\n\n        # 检查紧急情况\n        if metrics.get(\"latency\", 0) > self.performance_thresholds[\"max_latency_ms\"].value * 3:\n            urgency = \"high\"\n        elif metrics.get(\"latency\", 0) > self.performance_thresholds[\"max_latency_ms\"].value * 2:\n            urgency = \"medium\"\n\n        if metrics.get(\"accuracy\", 0) < self.performance_thresholds[\"min_accuracy\"].value * 0.8:\n            urgency = max(urgency, \"medium\")\n\n        if metrics.get(\"error_rate\", 0) > 0.2:\n            urgency = max(urgency, \"high\")\n\n        return urgency\n\n    def _execute_adaptations(\n        self,\n        metrics: Dict[str, Any],\n        context: Dict[str, Any],\n        urgency_level: str,\n    ) -> List[Dict[str, Any]]:\n        \"\"\"执行自适应操作\"\"\"\n        adaptations = []\n\n        # 根据紧急程度执行不同的自适应策略\n        if urgency_level == \"high\":\n            # 紧急情况：快速执行自适应\n            adaptations.extend(self._apply_fast_adaptations(metrics, context))\n        elif urgency_level == \"medium\":\n            # 中等紧急情况：平衡执行自适应\n            adaptations.extend(self._apply_balanced_adaptations(metrics, context))\n        else:\n            # 低紧急情况：执行常规自适应\n            adaptations.extend(self._apply_conservative_adaptations(metrics, context))\n\n        # 应用硬件约束\n        adaptations.extend(self._apply_hardware_constraints_adaptations(context))\n\n        # 记录自适应\n        for adaptation in adaptations:\n            self.adaptation_history.append(AdaptationHistory(\n                timestamp=time.time(),\n                optimization_type=AdaptationType(adaptation[\"type\"]),\n                before_value=adaptation[\"before\"],\n                after_value=adaptation[\"after\"],\n                improvement=adaptation.get(\"improvement\", 0.0),\n                performance_gain=adaptation.get(\"performance_gain\", 0.0),\n                feedback=adaptation.get(\"feedback\", \"\"),\n                context=context,\n            ))\n\n        return adaptations\n\n    def _apply_fast_adaptations(\n        self,\n        metrics: Dict[str, Any],\n        context: Dict[str, Any],\n    ) -> List[Dict[str, Any]]:\n        \"\"\"应用快速自适应\"\"\"\n        adaptations = []\n
        # 快速调整延迟相关的阈值\n        if metrics.get(\"latency\", 0) > self.performance_thresholds[\"max_latency_ms\"].value:\n            latency_improvement = min(\n                0.5,\n                (metrics.get(\"latency\", 0) - self.performance_thresholds[\"max_latency_ms\"].value)\n                / self.performance_thresholds[\"max_latency_ms\"].value,\n            )\n
            adaptations.append({\n                \"type\": \"threshold\",\n                \"target\": \"max_latency_ms\",\n                \"before\": self.performance_thresholds[\"max_latency_ms\"].value,\n                \"after\": self.performance_thresholds[\"max_latency_ms\"].value * (1.0 - latency_improvement * 0.3),\n                \"improvement\": latency_improvement * 0.3,\n                \"performance_gain\": min(0.5, latency_improvement * 0.5),\n                \"feedback\": \"High latency, aggressive threshold adjustment\",\n            })\n\n        # 快速调整准确率相关的阈值\n        if metrics.get(\"accuracy\", 0) < self.performance_thresholds[\"min_accuracy\"].value:\n            accuracy_improvement = min(\n                0.3,\n                (self.performance_thresholds[\"min_accuracy\"].value - metrics.get(\"accuracy\", 0))\n                / self.performance_thresholds[\"min_accuracy\"].value,\n            )\n\n            adaptations.append({\n                \"type\": \"threshold\",\n                \"target\": \"confidence_threshold\",\n                \"before\": self.thresholds[\"confidence_threshold\"].value,\n                \"after\": self.thresholds[\"confidence_threshold\"].value * (1.0 + accuracy_improvement * 0.2),\n                \"improvement\": accuracy_improvement * 0.2,\n                \"performance_gain\": accuracy_improvement * 0.4,\n                \"feedback\": \"Low accuracy, confidence threshold adjustment\",\n            })\n\n        return adaptations\n\n    def _apply_balanced_adaptations(\n        self,\n        metrics: Dict[str, Any],\n        context: Dict[str, Any],\n    ) -> List[Dict[str, Any]]:\n        \"\"\"应用平衡自适应\"\"\"\n        adaptations = []\n
        # 平衡调整多个阈值\n        if metrics.get(\"latency\", 0) > self.performance_thresholds[\"max_latency_ms\"].value * 1.2:\n            adaptations.append({\n                \"type\": \"threshold\",\n                \"target\": \"max_latency_ms\",\n                \"before\": self.performance_thresholds[\"max_latency_ms\"].value,\n                \"after\": self.performance_thresholds[\"max_latency_ms\"].value * 0.95,\n                \"improvement\": 0.05,\n                \"performance_gain\": 0.08,\n                \"feedback\": \"Moderate latency increase, balanced adjustment\",\n            })\n\n        if metrics.get(\"accuracy\", 0) < self.performance_thresholds[\"min_accuracy\"].value * 0.95:\n            adaptations.append({\n                \"type\": \"threshold\",\n                \"target\": \"temperature_threshold\",\n                \"before\": self.thresholds[\"temperature_threshold\"].value,\n                \"after\": self.thresholds[\"temperature_threshold\"].value * 1.05,\n                \"improvement\": 0.05,\n                \"performance_gain\": 0.06,\n                \"feedback\": \"Slight accuracy decrease, temperature threshold adjustment\",\n            })\n\n        return adaptations\n\n    def _apply_conservative_adaptations(\n        self,\n        metrics: Dict[str, Any],\n        context: Dict[str, Any],\n    ) -> List[Dict[str, Any]]:\n        \"\"\"应用保守自适应\"\"\"\n        adaptations = []\n\n        # 保守调整阈值\n        if metrics.get(\"latency\", 0) > self.performance_thresholds[\"max_latency_ms\"].value:\n            adaptations.append({\n                \"type\": \"threshold\",\n                \"target\": \"max_latency_ms\",\n                \"before\": self.performance_thresholds[\"max_latency_ms\"].value,\n                \"after\": self.performance_thresholds[\"max_latency_ms\"].value * 0.98,\n                \"improvement\": 0.02,\n                \"performance_gain\": 0.03,\n                \"feedback\": \"Conservative adaptation for stability\",\n            })\n\n        return adaptations\n\n    def _apply_hardware_constraints_adaptations(\n        self,\n        context: Dict[str, Any],\n    ) -> List[Dict[str, Any]]:\n        \"\"\"应用硬件约束自适应\"\"\"\n        adaptations = []\n
        # 获取当前硬件配置\n        profile_name = self.hardware_profile.get_profile_name()\n        constraints = self.hardware_constraints.get(profile_name, {})\n\n        if not constraints:\n            return adaptations\n\n        # 根据硬件约束调整阈值\n        if constraints.get(\"cpu_limit\", 1.0) < 0.8:\n            adaptations.append({\n                \"type\": \"hardware\",\n                \"target\": \"temperature_threshold\",\n                \"before\": self.thresholds[\"temperature_threshold\"].value,\n                \"after\": self.thresholds[\"temperature_threshold\"].value * constraints.get(\"cpu_limit\", 0.8),\n                \"improvement\": constraints.get(\"cpu_limit\", 0.8) - self.thresholds[\"temperature_threshold\"].value,\n                \"performance_gain\": 0.0,\n                \"feedback\": f\"Hardware constraint: CPU limit {constraints.get('cpu_limit', 0.8)}\",\n            })\n\n        if constraints.get(\"memory_limit\", 1.0) < 0.8:\n            adaptations.append({\n                \"type\": \"hardware\",\n                \"target\": \"confidence_threshold\",\n                \"before\": self.thresholds[\"confidence_threshold\"].value,\n                \"after\": self.thresholds[\"confidence_threshold\"].value * constraints.get(\"memory_limit\", 0.8),\n                \"improvement\": constraints.get(\"memory_limit\", 0.8) - self.thresholds[\"confidence_threshold\"].value,\n                \"performance_gain\": 0.0,\n                \"feedback\": f\"Hardware constraint: Memory limit {constraints.get('memory_limit', 0.8)}\",\n            })\n\n        return adaptations\n\n    def _check_and_adapt_if_needed(\n        self,\n        context: Optional[Dict[str, Any]] = None,\n    ) -> None:\n        \"\"\"检查并执行自适应\"\"\"\n        if len(self.performance_history) < 10:\n            return\n\n        # 获取最近的性能指标\n        recent_metrics = self._get_recent_metrics()\n\n        # 评估系统状态\n        state_result = self.evaluate_system_state(recent_metrics, context or {})\n\n        # 如果需要自适应，执行自适应\n        if state_result[\"needs_adaptation\"]:\n            self.adapt_thresholds(recent_metrics, context, force_adaptation=False)\n\n    def _get_recent_metrics(self) -> Dict[str, Any]:\n        \"\"\"获取最近的性能指标\"\"\"\n        if not self.performance_history:\n            return {}\n\n        # 获取最近10个性能记录\n        recent_metrics = []\n        for metric_record in list(self.performance_history)[-10:]:\n            recent_metrics.append({\n                \"accuracy\": metric_record.accuracy,\n                \"latency\": metric_record.latency,\n                \"throughput\": metric_record.throughput,\n                \"error_rate\": metric_record.error_rate,\n                \"resource_usage\": metric_record.resource_usage,\n                \"memory_usage\": metric_record.memory_usage,\n            })\n\n        # 计算平均值\n        if not recent_metrics:\n            return {}\n\n        averaged_metrics = {}\n        for key in recent_metrics[0].keys():\n            averaged_metrics[key] = sum(m[key] for m in recent_metrics) / len(recent_metrics)\n\n        return averaged_metrics\n\n    def _calculate_adaptation_statistics(\n        self,\n        start_time: float,\n        end_time: float,\n    ) -> Dict[str, Any]:\n        \"\"\"计算自适应统计\"\"\"\n        try:\n            adaptations_in_window = [\n                cycle for cycle in self.optimization_cycles\n                if start_time <= cycle[\"timestamp\"] <= end_time\n            ]\n\n            if not adaptations_in_window:\n                return {\n                    \"total_adaptations\": 0,\n                    \"success_rate\": 0.0,\n                    \"average_improvement\": 0.0,\n                    \"total_performance_gain\": 0.0,\n                }\n\n            total_adaptations = len(adaptations_in_window)\n            success_count = sum(1 for cycle in adaptations_in_window if cycle.get(\"success\", False))\n\n            average_improvement = sum(\n                sum(abs(imp) for imp in cycle.get(\"improvements\", {}).values())\n                for cycle in adaptations_in_window\n            ) / max(1, total_adaptations)\n\n            total_performance_gain = sum(\n                cycle.get(\"improvements\", {}).get(\"max_latency_ms\", 0.0)\n                for cycle in adaptations_in_window\n            )\n\n            return {\n                \"total_adaptations\": total_adaptations,\n                \"success_rate\": success_count / max(1, total_adaptations),\n                \"average_improvement\": average_improvement,\n                \"total_performance_gain\": total_performance_gain,\n                \"urgency_distribution\": self._calculate_urgency_distribution(adaptations_in_window),\n            }\n\n        except Exception as e:\n            logger.error(f\"Error calculating adaptation statistics: {e}\", exc_info=True)\n            return {\"error\": str(e)}\n\n    def _calculate_threshold_statistics(\n        self,\n        start_time: float,\n        end_time: float,\n    ) -> Dict[str, Any]:\n        \"\"\"计算阈值统计\"\"\"\n        try:\n            thresholds_in_window = []\n            for cycle in self.optimization_cycles:\n                if start_time <= cycle[\"timestamp\"] <= end_time:\n                    thresholds_in_window.extend([\n                        (name, after_value)\n                        for name, after_value in cycle.get(\"after\", {}).items()\n                    ])\n\n            if not thresholds_in_window:\n                return {\n                    \"threshold_names\": [],\n                    \"value_distributions\": {},\n                    \"adaptation_frequency\": {},\n                }\n\n            # 按阈值名称分组\n            threshold_distributions = {}\n            adaptation_frequency = {}\n\n            for name, value in thresholds_in_window:\n                if name not in threshold_distributions:\n                    threshold_distributions[name] = []\n                threshold_distributions[name].append(value)\n\n                if name not in adaptation_frequency:\n                    adaptation_frequency[name] = 0\n                adaptation_frequency[name] += 1\n\n            # 计算统计值\n            threshold_stats = {}\n            for name, values in threshold_distributions.items():\n                threshold_stats[name] = {\n                    \"count\": len(values),\n                    \"mean\": sum(values) / len(values),\n                    \"min\": min(values),\n                    \"max\": max(values),\n                    \"std\": (sum((v - sum(values) / len(values)) ** 2 for v in values) / len(values)) ** 0.5,\n                }\n\n            return {\n                \"threshold_names\": list(threshold_distributions.keys()),\n                \"value_distributions\": threshold_stats,\n                \"adaptation_frequency\": adaptation_frequency,\n            }\n\n        except Exception as e:\n            logger.error(f\"Error calculating threshold statistics: {e}\", exc_info=True)\n            return {\"error\": str(e)}\n\n    def _calculate_performance_trends(\n        self,\n        start_time: float,\n        end_time: float,\n    ) -> Dict[str, Any]:\n        \"\"\"计算性能趋势\"\"\"\n        try:\n            if not self.performance_history:\n                return {\"accuracy_trend\": 0.0, \"latency_trend\": 0.0}\n\n            # 获取窗口内性能记录\n            metrics_in_window = []\n            for metric_record in self.performance_history:\n                if start_time <= metric_record.timestamp <= end_time:\n                    metrics_in_window.append(metric_record)\n\n            if len(metrics_in_window) < 2:\n                return {\"accuracy_trend\": 0.0, \"latency_trend\": 0.0}\n\n            # 计算趋势\n            accuracy_trend = sum(\n                (metric.accuracy - metrics_in_window[0].accuracy)\n                for metric in metrics_in_window[1:]\n            ) / (len(metrics_in_window) - 1)\n\n            latency_trend = sum(\n                (metrics_in_window[0].latency - metric.latency)\n                for metric in metrics_in_window[1:]\n            ) / (len(metrics_in_window) - 1)\n\n            return {\n                \"accuracy_trend\": accuracy_trend,\n                \"latency_trend\": latency_trend,\n                \"sample_count\": len(metrics_in_window),\n            }\n\n        except Exception as e:\n            logger.error(f\"Error calculating performance trends: {e}\", exc_info=True)\n            return {\"error\": str(e)}\n\n    def _calculate_urgency_distribution(\n        self,\n        adaptations: List[Dict[str, Any]],\n    ) -> Dict[str, int]:\n        \"\"\"计算紧急程度分布\"\"\"\n        distribution = {\"low\": 0, \"medium\": 0, \"high\": 0, \"error\": 0}\n\n        for adaptation in adaptations:\n            urgency = adaptation.get(\"urgency_level\", \"low\")\n            if urgency in distribution:\n                distribution[urgency] += 1\n\n        return distribution\n\n    def _check_adaptation_success(\n        self,\n        metrics: Dict[str, Any],\n        before_metrics: Dict[str, Any],\n    ) -> bool:\n        \"\"\"检查自适应是否成功\"\"\"\n        if not before_metrics:\n            return True\n\n        # 检查延迟改进\n        latency_improved = metrics.get(\"latency\", 0) < before_metrics.get(\"latency\", 0)\n\n        # 检查准确率改进\n        accuracy_improved = metrics.get(\"accuracy\", 0) > before_metrics.get(\"accuracy\", 0)\n\n        # 检查错误率改进\n        error_rate_improved = metrics.get(\"error_rate\", 0) < before_metrics.get(\"error_rate\", 0)\n\n        return (latency_improved and accuracy_improved) or error_rate_improved or not any([\n            metrics.get(\"latency\", 0) > before_metrics.get(\"latency\", 0) * 1.5,\n            metrics.get(\"accuracy\", 0) < before_metrics.get(\"accuracy\", 0) * 0.9,\n            metrics.get(\"error_rate\", 0) > before_metrics.get(\"error_rate\", 0) * 1.5,\n        ])\n\n    def _get_performance_target_key_from_metric(\n        self,\n        metric_name: str,\n    ) -> Optional[str]:\n        \"\"\"根据指标名称获取性能目标键\"\"\"\n        mapping = {\n            \"latency\": \"max_latency_ms\",\n            \"accuracy\": \"min_accuracy\",\n            \"throughput\": \"target_throughput\",\n            \"error_rate\": \"min_accuracy\",\n            \"resource_usage\": \"max_memory_usage\",\n            \"memory_usage\": \"max_memory_usage\",\n        }\n        return mapping.get(metric_name)\n\n    def _initialize_feedback_aggregator(self) -> None:\n        \"\"\"初始化反馈聚合器\"\"\"\n        try:\n            # 尝试导入并初始化反馈聚合器\n            from services.llm.llm_decision_loop import LLMDecisionLoop\n\n            self.feedback_aggregator = LLMDecisionLoop()\n            logger.debug(\"Feedback aggregator initialized\")\n\n        except ImportError:\n            logger.warning(\"LLM DecisionLoop not available, skipping feedback aggregator initialization\")\n        except Exception as e:\n            logger.error(f\"Error initializing feedback aggregator: {e}\", exc_info=True)\n\n    def _initialize_prediction_engine(self) -> None:\n        \"\"\"初始化预测引擎\"\"\"\n        try:\n            # 尝试导入并初始化预测引擎\n            from ai.garden.garden_engine import GARDENEngine\n\n            self.prediction_engine = GARDENEngine()\n            logger.debug(\"Prediction engine initialized\")\n\n        except ImportError:\n            logger.warning(\"GARDENEngine not available, skipping prediction engine initialization\")\n        except Exception as e:\n            logger.error(f\"Error initializing prediction engine: {e}\", exc_info=True)\n\n    def get_system_status(self) -> Dict[str, Any]:\n        \"\"\"获取系统状态\"\"\"\n        return {\n            \"timestamp\": time.time(),\n            \"is_initialized\": True,\n            \"adaptation_mode\": self.current_adaptation_mode.value,\n            \"performance_history_size\": len(self.performance_history),\n            \"adaptation_history_size\": len(self.adaptation_history),\n            \"thresholds_count\": len(self.thresholds) + len(self.performance_thresholds),\n            \"hardware_profile\": self.hardware_profile.get_profile_name() if self.hardware_profile else \"unknown\",\n            \"adaptation_efficiency\": self._calculate_adaptation_efficiency(),\n            \"optimization_effectiveness\": self._calculate_optimization_effectiveness(),\n        }\n\n    def reset_system(self) -> None:\n        \"\"\"重置系统\"\"\"\n        try:\n            # 清除历史记录\n            self.performance_history.clear()\n            self.resource_usage_history.clear()\n            self.adaptation_history.clear()\n            self.optimization_cycles.clear()\n\n            # 重置阈值到默认值\n            for name, config in self.thresholds.items():\n                config.value = config.default_value\n\n            for name, config in self.performance_thresholds.items():\n                config.value = config.default_value\n\n            # 重置适应模式\n            self.current_adaptation_mode = AdaptationMode.BALANCED\n\n            logger.info(\"DynamicThresholdManager system reset completed\")\n\n        except Exception as e:\n            logger.error(f\"Error resetting system: {e}\", exc_info=True)\n\n    def __str__(self) -> str:\n        return f\"DynamicThresholdManager(adaptation_mode={self.current_adaptation_mode.value}, thresholds={len(self.thresholds)}, performance_thresholds={len(self.performance_thresholds)})\"\n\n    def __repr__(self) -> str:\n        return self.__str__()\n\n\ndef time_time() -> float:\n    \"\"\"替代 time.time，处理可能的导入问题\"\"\"\n    return time.time()