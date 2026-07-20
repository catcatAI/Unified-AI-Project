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

from core.system.config.hardware_profile import HardwareProfile
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
                    "constraint_type": "hard",
                    "is_critical": True,
                },
                "target_throughput": {
                    "name": "target_throughput",
                    "value": 1000.0,
                    "min_value": 100.0,
                    "max_value": 10000.0,
                    "default_value": 1000.0,
                    "adaptation_rate": 0.08,
                    "constraint_type": "soft",
                    "is_critical": False,
                },
                "max_memory_usage": {
                    "name": "max_memory_usage",
                    "value": 0.8,
                    "min_value": 0.3,
                    "max_value": 0.95,
                    "default_value": 0.8,
                    "adaptation_rate": 0.06,
                    "constraint_type": "hard",
                    "is_critical": True,
                },
            },
            # 自适应配置
            "adaptation": {
                "learning_rate": 0.01,
                "momentum": 0.9,
                "Exploration_factor": 0.1,
                "reward_decay": 0.95,
                "min_adaptation_interval_ms": 100,
                "max_adaptation_frequency_per_minute": 10,
            },
            # 硬件配置
            "hardware": {
                "enable_hardware_awareness": True,
                "auto_detect_profile": True,
                "apply_hardware_constraints": True,
            },
            # 集成配置
            "integration": {
                "enable_feedback_aggregation": True,
                "enable_prediction_engine": True,
                "integration_timeout_ms": 500,
            },
            # 日志记录配置
            "logging": {
                "enable_adaptation_logging": True,
                "enable_performance_logging": True,
                "adaptation_log_level": "INFO",
            },
        }

    def _initialize_system(self) -> None:
        """初始化系统"""
        try:
            # 初始化硬件配置
            if self.config["hardware"]["enable_hardware_awareness"]:
                self.hardware_profile = HardwareProfile()
                self._load_hardware_constraints()

            # 初始化阈值配置
            self.thresholds = {
                key: ThresholdConfiguration(**config)
                for key, config in self.config["thresholds"].items()
            }

            # 初始化性能阈值配置
            self.performance_thresholds = {
                key: ThresholdConfiguration(**config)
                for key, config in self.config["performance_thresholds"].items()
            }

            # 初始化自适应规则
            self._initialize_adaptation_rules()

            # 加载默认性能目标
            self._load_default_performance_targets()

            # 初始化反馈聚合器和预测引擎
            if self.config["integration"]["enable_feedback_aggregation"]:
                self._initialize_feedback_aggregator()

            if self.config["integration"]["enable_prediction_engine"]:
                self._initialize_prediction_engine()

            logger.info("DynamicThresholdManager initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing DynamicThresholdManager: {e}", exc_info=True)
            raise

    def _load_hardware_constraints(self) -> None:
        """加载硬件约束"""
        try:
            if not self.hardware_profile:
                return

            profile_name = self.hardware_profile.get_profile_name()

            # 根据硬件配置加载约束
            hardware_configs = {
                "high_performance_desktop": HardwareConstraint(
                    hardware_profile="high_performance_desktop",
                    max_threshold=1.0,
                    optimal_range=(0.7, 0.95),
                    memory_limit=0.9,
                    cpu_limit=1.0,
                    gpu_limit=1.0,
                    thermal_limit=0.85,
                ),
                "laptop_normal": HardwareConstraint(
                    hardware_profile="laptop_normal",
                    max_threshold=0.85,
                    optimal_range=(0.6, 0.85),
                    memory_limit=0.8,
                    cpu_limit=0.8,
                    gpu_limit=0.7,
                    thermal_limit=0.75,
                ),
                "laptop_power_saver": HardwareConstraint(
                    hardware_profile="laptop_power_saver",
                    max_threshold=0.7,
                    optimal_range=(0.5, 0.7),
                    memory_limit=0.7,
                    cpu_limit=0.7,
                    gpu_limit=0.5,
                    thermal_limit=0.65,
                ),
                "low_power_device": HardwareConstraint(
                    hardware_profile="low_power_device",
                    max_threshold=0.6,
                    optimal_range=(0.4, 0.6),
                    memory_limit=0.6,
                    cpu_limit=0.6,
                    gpu_limit=0.4,
                    thermal_limit=0.55,
                ),
                "server_cloud": HardwareConstraint(
                    hardware_profile="server_cloud",
                    max_threshold=1.0,
                    optimal_range=(0.8, 1.0),
                    memory_limit=0.95,
                    cpu_limit=1.0,
                    gpu_limit=1.0,
                    thermal_limit=0.9,
                ),
            }

            self.hardware_constraints = {
                profile: config
                for config_name, config in hardware_configs.items()
                if config_name in self.hardware_profile.get_hardware_profile()
            }

            logger.debug(f"Loaded {len(self.hardware_constraints)} hardware constraint sets")

        except Exception as e:
            logger.error(f"Error loading hardware constraints: {e}", exc_info=True)

    def _initialize_adaptation_rules(self) -> None:
        """初始化自适应规则"""
        self.adaptation_rules = [
            {
                "name": "performance_degradation",
                "condition": lambda m, p, h: p["latency"] > self.performance_thresholds["max_latency_ms"].value * 1.5,
                "action": "increase_threshold",
                "target_metric": "max_latency_ms",
                "adjustment_factor": 1.2,
            },
            {
                "name": "accuracy_drop",
                "condition": lambda m, p, h: p["accuracy"] < self.performance_thresholds["min_accuracy"].value * 0.9,
                "action": "decrease_threshold",
                "target_metric": "confidence_threshold",
                "adjustment_factor": 0.9,
            },
            {
                "name": "resource_pressure",
                "condition": lambda m, p, h: p["resource_usage"] > 0.8 or p["memory_usage"] > 0.8,
                "action": "reduce_thresholds",
                "target_metrics": ["confidence_threshold", "learning_rate_threshold"],
                "adjustment_factor": 0.8,
            },
            {
                "name": "hardware_constraint",
                "condition": lambda m, p, h: h["profile"] != "high_performance_desktop" and m["overall_score"] > 0.9,
                "action": "apply_hardware_limits",
                "target_metrics": ["confidence_threshold", "temperature_threshold"],
                "adjustment_factor": 0.9,
            },
            {
                "name": "adaptation_success",
                "condition": lambda m, p, h: m.get("improvement", 0) > 0.1,
                "action": "increase_learning_rate",
                "target_metric": "learning_rate",
                "adjustment_factor": 1.1,
            },
        ]

    def _load_default_performance_targets(self) -> None:
        """加载默认性能目标"""
        self.performance_target = {
            "accuracy": 0.9,
            "latency": 100.0,
            "throughput": 1000.0,
            "error_rate": 0.05,
            "resource_usage": 0.7,
            "memory_usage": 0.8,
        }

        self.optimization_goals = {
            "confidence_threshold": 0.8,
            "temperature_threshold": 0.8,
            "pressure_threshold": 0.7,
            "learning_rate_threshold": 0.4,
            "diversity_threshold": 0.6,
            "max_latency_ms": 50.0,
            "min_accuracy": 0.95,
            "target_throughput": 2000.0,
            "max_memory_usage": 0.9,
        }

    def _initialize_feedback_aggregator(self) -> None:
        """初始化反馈聚合器"""
        try:
            from services.llm.llm_decision_loop import LLMDecisionLoop

            self.feedback_aggregator = LLMDecisionLoop()
            logger.debug("Feedback aggregator initialized")

        except ImportError:
            logger.warning("LLM DecisionLoop not available, skipping feedback aggregator initialization")
        except Exception as e:
            logger.error(f"Error initializing feedback aggregator: {e}", exc_info=True)

    def _initialize_prediction_engine(self) -> None:
        """初始化预测引擎"""
        try:
            from ai.garden.garden_engine import GARDENEngine

            self.prediction_engine = GARDENEngine()
            logger.debug("Prediction engine initialized")

        except ImportError:
            logger.warning("GARDENEngine not available, skipping prediction engine initialization")
        except Exception as e:
            logger.error(f"Error initializing prediction engine: {e}", exc_info=True)

    def evaluate_system_state(
        self,
        metrics: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        评估系统状态并确定是否需要自适应

        Args:
            metrics: 性能指标
            context: 上下文信息

        Returns:
            Dict: 评估结果
        """
        try:
            # 收集系统信息
            system_info = self._collect_system_info()

            # 评估需要自适应
            needs_adaptation = self._check_adaptation_needs(metrics, system_info, context or {})

            result = {
                "timestamp": time.time(),
                "needs_adaptation": needs_adaptation,
                "metrics": metrics,
                "system_info": system_info,
                "adaptation_recommendations": [],
                "urgency_level": "low",
            }

            if needs_adaptation:
                recommendations = self._generate_adaptation_recommendations(
                    metrics, system_info, context or {}
                )
                result["adaptation_recommendations"] = recommendations
                result["urgency_level"] = self._calculate_urgency_level(metrics, system_info)

            return result

        except Exception as e:
            logger.error(f"Error evaluating system state: {e}", exc_info=True)
            return {
                "timestamp": time.time(),
                "needs_adaptation": False,
                "metrics": metrics,
                "system_info": {},
                "adaptation_recommendations": [],
                "urgency_level": "error",
                "error": str(e),
            }

    def adapt_thresholds(
        self,
        metrics: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        force_adaptation: bool = False,
    ) -> Dict[str, Any]:
        """
        执行自适应操作

        Args:
            metrics: 性能指标
            context: 上下文信息
            force_adaptation: 是否强制自适应

        Returns:
            Dict: 自适应结果
        """
        try:
            # 检查是否需要自适应
            state_result = self.evaluate_system_state(metrics, context)

            if not state_result["needs_adaptation"] and not force_adaptation:
                return {
                    "timestamp": time.time(),
                    "adapted": False,
                    "reason": "No adaptation needed",
                    "metrics": metrics,
                    "before": {},
                    "after": {},
                    "improvements": {},
                }

            # 收集当前阈值
            before_thresholds = self._collect_current_thresholds()

            # 执行自适应
            adaptations = self._execute_adaptations(metrics, context or {}, state_result["urgency_level"])

            # 获取适应后的阈值
            after_thresholds = self._collect_current_thresholds()

            # 计算改进
            improvements = {}
            for key in after_thresholds:
                if key in before_thresholds:
                    improvement = (after_thresholds[key] - before_thresholds[key]) / before_thresholds[key]
                    improvements[key] = improvement

            # 记录自适应
            adaptation_record = {
                "timestamp": time.time(),
                "metrics": metrics,
                "context": context,
                "urgency_level": state_result["urgency_level"],
                "before": before_thresholds,
                "after": after_thresholds,
                "improvements": improvements,
                "adaptations": adaptations,
                "success": sum(1 for imp in improvements.values() if abs(imp) > 0.01) > 0,
            }

            self.optimization_cycles.append(adaptation_record)

            # 触发事件
            if adaptations:
                state_store.emit_event(
                    "threshold.adapted",
                    {
                        "timestamp": time.time(),
                        "adaptations": adaptations,
                        "improvements": improvements,
                        "urgency_level": state_result["urgency_level"],
                        "success": adaptation_record["success"],
                    },
                )

            logger.debug(
                f"Threshold adaptation completed - adaptations: {len(adaptations)}, success: {adaptation_record['success']}"
            )

            return {
                "timestamp": time.time(),
                "adapted": True,
                "reason": "Adaptation completed",
                "urgency_level": state_result["urgency_level"],
                "metrics": metrics,
                "before": before_thresholds,
                "after": after_thresholds,
                "improvements": improvements,
                "adaptations": adaptations,
                "success": adaptation_record["success"],
            }

        except Exception as e:
            logger.error(f"Error adapting thresholds: {e}", exc_info=True)
            return {
                "timestamp": time.time(),
                "adapted": False,
                "reason": f"Error: {e}",
                "urgency_level": "error",
                "metrics": metrics,
                "before": {},
                "after": {},
                "improvements": {},
                "adaptations": {},
                "success": False,
                "error": str(e),
            }

    def get_optimized_thresholds(
        self,
        system_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        获取优化后的阈值

        Args:
            system_state: 系统状态信息

        Returns:
            Dict: 优化后的阈值
        """
        try:
            thresholds = {}

            for name, config in self.thresholds.items():
                optimized_value = self._calculate_optimized_threshold(
                    name, config, system_state
                )
                thresholds[name] = {
                    "name": name,
                    "value": optimized_value,
                    "is_critical": config.is_critical,
                    "constraint_type": config.constraint_type,
                    "adaptation_rate": config.adaptation_rate,
                    "optimized": True,
                }

            for name, config in self.performance_thresholds.items():
                optimized_value = self._calculate_optimized_threshold(
                    name, config, system_state
                )
                thresholds[name] = {
                    "name": name,
                    "value": optimized_value,
                    "is_critical": config.is_critical,
                    "constraint_type": config.constraint_type,
                    "adaptation_rate": config.adaptation_rate,
                    "optimized": True,
                }

            return {
                "timestamp": time.time(),
                "thresholds": thresholds,
                "optimization_source": "dynamic",
                "adaptation_mode": self.current_adaptation_mode.value,
                "confidence": self._calculate_optimization_confidence(),
                "hardware_aware": self.config["hardware"]["enable_hardware_awareness"],
            }

        except Exception as e:
            logger.error(f"Error getting optimized thresholds: {e}", exc_info=True)
            return self._get_default_thresholds()

    def record_performance_metrics(
        self,
        metrics: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录性能指标

        Args:
            metrics: 性能指标
            context: 上下文信息
        """
        try:
            # 创建性能指标记录
            metric_record = PerformanceMetrics(
                timestamp=time.time(),
                accuracy=metrics.get("accuracy", 0.0),
                latency=metrics.get("latency", 0.0),
                throughput=metrics.get("throughput", 0.0),
                error_rate=metrics.get("error_rate", 0.0),
                resource_usage=metrics.get("resource_usage", 0.0),
                memory_usage=metrics.get("memory_usage", 0.0),
            )

            self.performance_history.append(metric_record)

            # 记录资源使用情况
            if "resource_usage" in metrics:
                self.resource_usage_history.append(
                    {"timestamp": time.time(), "usage": metrics["resource_usage"]}
                )

            # 检查是否需要自适应
            if len(self.performance_history) >= 10:
                self._check_and_adapt_if_needed(context)

            logger.debug(f"Performance metrics recorded - accuracy: {metrics.get('accuracy', 0.0):.2f}, latency: {metrics.get('latency', 0.0):.2f}ms")

        except Exception as e:
            logger.error(f"Error recording performance metrics: {e}", exc_info=True)

    def get_adaptation_analytics(
        self,
        time_window_minutes: int = 60,
    ) -> Dict[str, Any]:
        """
        获取自适应分析数据

        Args:
            time_window_minutes: 时间窗口（分钟）

        Returns:
            Dict: 自适应分析结果
        """
        try:
            # 过滤历史记录
            end_time = time.time()
            start_time = end_time - (time_window_minutes * 60.0)

            # 计算自适应统计
            adaptation_stats = self._calculate_adaptation_statistics(start_time, end_time)
            threshold_stats = self._calculate_threshold_statistics(start_time, end_time)
            performance_trends = self._calculate_performance_trends(start_time, end_time)

            return {
                "timestamp": time.time(),
                "time_window_minutes": time_window_minutes,
                "adaptation_stats": adaptation_stats,
                "threshold_stats": threshold_stats,
                "performance_trends": performance_trends,
                "current_adaptation_mode": self.current_adaptation_mode.value,
                "adaptation_efficiency": self._calculate_adaptation_efficiency(),
                "optimization_effectiveness": self._calculate_optimization_effectiveness(),
            }

        except Exception as e:
            logger.error(f"Error getting adaptation analytics: {e}", exc_info=True)
            return {
                "timestamp": time.time(),
                "error": str(e),
            }

    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统信息"""
        try:
            system_info = {}

            # 硬件信息
            if self.hardware_profile:
                profile_name = self.hardware_profile.get_profile_name()
                system_info["hardware_profile"] = profile_name
                system_info["hardware_constraints"] = self.hardware_constraints.get(profile_name, {})

            # 适应模式
            system_info["adaptation_mode"] = self.current_adaptation_mode.value
            system_info["adaptation_rules_count"] = len(self.adaptation_rules)

            # 性能目标
            system_info["performance_targets"] = self.performance_target
            system_info["optimization_goals"] = self.optimization_goals

            return system_info

        except Exception as e:
            logger.error(f"Error collecting system info: {e}", exc_info=True)
            return {}

    def _check_adaptation_needs(
        self,
        metrics: Dict[str, Any],
        system_info: Dict[str, Any],
        context: Dict[str, Any],
    ) -> bool:
        """检查是否需要自适应"""
        try:
            # 检查紧急情况
            if context.get("emergency_mode", False):
                return True

            # 检查阈值违规
            threshold_violations = self._check_threshold_violations(metrics, system_info)
            if threshold_violations:
                return True

            # 检查性能目标
            performance_issues = self._check_performance_issues(metrics, system_info)
            if performance_issues:
                return True

            # 检查自适应机会
            adaptation_opportunities = self._check_adaptation_opportunities(metrics, system_info)
            if adaptation_opportunities:
                return True

            # 检查硬件约束
            hardware_issues = self._check_hardware_constraints(system_info)
            if hardware_issues:
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking adaptation needs: {e}", exc_info=True)
            return False

    def _check_threshold_violations(
        self,
        metrics: Dict[str, Any],
        system_info: Dict[str, Any],
    ) -> List[str]:
        """检查阈值违规"""
        violations = []

        # 检查关键性能指标
        if metrics.get("latency", 0) > self.performance_thresholds["max_latency_ms"].value:
            violations.append("latency_exceeded")

        if metrics.get("accuracy", 0) < self.performance_thresholds["min_accuracy"].value:
            violations.append("accuracy_below_threshold")

        if metrics.get("memory_usage", 0) > self.performance_thresholds["max_memory_usage"].value:
            violations.append("memory_usage_exceeded")

        # 检查硬件约束
        if "hardware_constraints" in system_info:
            constraints = system_info["hardware_constraints"]
            if metrics.get("resource_usage", 0) > constraints.get("cpu_limit", 1.0):
                violations.append("cpu_usage_exceeded")
            if metrics.get("memory_usage", 0) > constraints.get("memory_limit", 1.0):
                violations.append("memory_usage_exceeded")
            if metrics.get("resource_usage", 0) > constraints.get("thermal_limit", 1.0):
                violations.append("thermal_limit_exceeded")

        return violations

    def _check_performance_issues(
        self,
        metrics: Dict[str, Any],
        system_info: Dict[str, Any],
    ) -> List[str]:
        """检查性能问题"""
        issues = []

        # 检查延迟是否太高
        if metrics.get("latency", 0) > self.performance_thresholds["max_latency_ms"].value * 2:
            issues.append("high_latency")

        # 检查准确率是否太低
        if metrics.get("accuracy", 0) < self.performance_thresholds["min_accuracy"].value * 0.9:
            issues.append("low_accuracy")

        # 检查错误率是否太高
        if metrics.get("error_rate", 0) > 0.1:
            issues.append("high_error_rate")

        return issues

    def _check_adaptation_opportunities(
        self,
        metrics: Dict[str, Any],
        system_info: Dict[str, Any],
    ) -> List[str]:
        """检查自适应机会"""
        opportunities = []

        # 检查是否有性能改进空间
        if metrics.get("latency", 0) > 100.0:
            opportunities.append("latency_optimization")

        if metrics.get("accuracy", 0) < 0.9:
            opportunities.append("accuracy_optimization")

        # 检查是否有资源利用不足
        if metrics.get("resource_usage", 0) < 0.5:
            opportunities.append("resource_reallocation")

        return opportunities

    def _check_hardware_constraints(
        self,
        system_info: Dict[str, Any],
    ) -> bool:
        """检查硬件约束问题"""
        if "hardware_constraints" not in system_info:
            return False

        constraints = system_info["hardware_constraints"]
        return constraints.get("cpu_limit", 1.0) < 0.8 or constraints.get("memory_limit", 1.0) < 0.8

    def _generate_adaptation_recommendations(
        self,
        metrics: Dict[str, Any],
        system_info: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[str]:
        """生成自适应建议"""
        recommendations = []

        # 根据不同情况生成建议
        if metrics.get("latency", 0) > self.performance_thresholds["max_latency_ms"].value * 1.5:
            recommendations.append("优先优化延迟")

        if metrics.get("accuracy", 0) < self.performance_thresholds["min_accuracy"].value:
            recommendations.append("优化模型准确率")

        if metrics.get("memory_usage", 0) > self.performance_thresholds["max_memory_usage"].value:
            recommendations.append("优化内存使用")

        if system_info.get("hardware_profile") == "low_power_device":
            recommendations.append("启用节电模式")

        if context.get("load_level") == "high":
            recommendations.append("降低处理频率，保持服务稳定性")

        return recommendations

    def _calculate_urgency_level(
        self,
        metrics: Dict[str, Any],
        system_info: Dict[str, Any],
    ) -> str:
        """计算紧急程度"""
        urgency = "low"

        # 检查紧急情况
        if metrics.get("latency", 0) > self.performance_thresholds["max_latency_ms"].value * 3:
            urgency = "high"
        elif metrics.get("latency", 0) > self.performance_thresholds["max_latency_ms"].value * 2:
            urgency = "medium"

        if metrics.get("accuracy", 0) < self.performance_thresholds["min_accuracy"].value * 0.8:
            urgency = max(urgency, "medium")

        if metrics.get("error_rate", 0) > 0.2:
            urgency = max(urgency, "high")

        return urgency

    def _execute_adaptations(
        self,
        metrics: Dict[str, Any],
        context: Dict[str, Any],
        urgency_level: str,
    ) -> List[Dict[str, Any]]:
        """执行自适应操作"""
        adaptations = []

        # 根据紧急程度执行不同的自适应策略
        if urgency_level == "high":
            # 紧急情况：快速执行自适应
            adaptations.extend(self._apply_fast_adaptations(metrics, context))
        elif urgency_level == "medium":
            # 中等紧急情况：平衡执行自适应
            adaptations.extend(self._apply_balanced_adaptations(metrics, context))
        else:
            # 低紧急情况：执行常规自适应
            adaptations.extend(self._apply_conservative_adaptations(metrics, context))

        # 应用硬件约束
        adaptations.extend(self._apply_hardware_constraints_adaptations(context))

        # 记录自适应
        for adaptation in adaptations:
            self.adaptation_history.append(AdaptationHistory(
                timestamp=time.time(),
                optimization_type=OptimizationType(adaptation["type"]),
                before_value=adaptation["before"],
                after_value=adaptation["after"],
                improvement=adaptation.get("improvement", 0.0),
                performance_gain=adaptation.get("performance_gain", 0.0),
                feedback=adaptation.get("feedback", ""),
                context=context,
            ))

        return adaptations

    def _apply_fast_adaptations(
        self,
        metrics: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """应用快速自适应"""
        adaptations = []

        # 快速调整延迟相关的阈值
        if metrics.get("latency", 0) > self.performance_thresholds["max_latency_ms"].value:
            latency_improvement = min(
                0.5,
                (metrics.get("latency", 0) - self.performance_thresholds["max_latency_ms"].value)
                / self.performance_thresholds["max_latency_ms"].value,
            )

            adaptations.append({
                "type": "threshold",
                "target": "max_latency_ms",
                "before": self.performance_thresholds["max_latency_ms"].value,
                "after": self.performance_thresholds["max_latency_ms"].value * (1.0 - latency_improvement * 0.3),
                "improvement": latency_improvement * 0.3,
                "performance_gain": min(0.5, latency_improvement * 0.5),
                "feedback": "High latency, aggressive threshold adjustment",
            })

        # 快速调整准确率相关的阈值
        if metrics.get("accuracy", 0) < self.performance_thresholds["min_accuracy"].value:
            accuracy_improvement = min(
                0.3,
                (self.performance_thresholds["min_accuracy"].value - metrics.get("accuracy", 0))
                / self.performance_thresholds["min_accuracy"].value,
            )

            adaptations.append({
                "type": "threshold",
                "target": "confidence_threshold",
                "before": self.thresholds["confidence_threshold"].value,
                "after": self.thresholds["confidence_threshold"].value * (1.0 + accuracy_improvement * 0.2),
                "improvement": accuracy_improvement * 0.2,
                "performance_gain": accuracy_improvement * 0.4,
                "feedback": "Low accuracy, confidence threshold adjustment",
            })

        return adaptations

    def _apply_balanced_adaptations(
        self,
        metrics: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """应用平衡自适应"""
        adaptations = []

        # 平衡调整多个阈值
        if metrics.get("latency", 0) > self.performance_thresholds["max_latency_ms"].value * 1.2:
            adaptations.append({
                "type": "threshold",
                "target": "max_latency_ms",
                "before": self.performance_thresholds["max_latency_ms"].value,
                "after": self.performance_thresholds["max_latency_ms"].value * 0.95,
                "improvement": 0.05,
                "performance_gain": 0.08,
                "feedback": "Moderate latency increase, balanced adjustment",
            })

        if metrics.get("accuracy", 0) < self.performance_thresholds["min_accuracy"].value * 0.95:
            adaptations.append({
                "type": "threshold",
                "target": "temperature_threshold",
                "before": self.thresholds["temperature_threshold"].value,
                "after": self.thresholds["temperature_threshold"].value * 1.05,
                "improvement": 0.05,
                "performance_gain": 0.06,
                "feedback": "Slight accuracy decrease, temperature threshold adjustment",
            })

        return adaptations

    def _apply_conservative_adaptations(
        self,
        metrics: Dict[str, Any],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """应用保守自适应"""
        adaptations = []

        # 保守调整阈值
        if metrics.get("latency", 0) > self.performance_thresholds["max_latency_ms"].value:
            adaptations.append({
                "type": "threshold",
                "target": "max_latency_ms",
                "before": self.performance_thresholds["max_latency_ms"].value,
                "after": self.performance_thresholds["max_latency_ms"].value * 0.98,
                "improvement": 0.02,
                "performance_gain": 0.03,
                "feedback": "Conservative adaptation for stability",
            })

        return adaptations

    def _apply_hardware_constraints_adaptations(
        self,
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """应用硬件约束自适应"""
        adaptations = []

        # 获取当前硬件配置
        profile_name = self.hardware_profile.get_profile_name()
        constraints = self.hardware_constraints.get(profile_name, {})

        if not constraints:
            return adaptations

        # 根据硬件约束调整阈值
        if constraints.get("cpu_limit", 1.0) < 0.8:
            adaptations.append({
                "type": "hardware",
                "target": "temperature_threshold",
                "before": self.thresholds["temperature_threshold"].value,
                "after": self.thresholds["temperature_threshold"].value * constraints.get("cpu_limit", 0.8),
                "improvement": constraints.get("cpu_limit", 0.8) - self.thresholds["temperature_threshold"].value,
                "performance_gain": 0.0,
                "feedback": f"Hardware constraint: CPU limit {constraints.get('cpu_limit', 0.8)}",
            })

        if constraints.get("memory_limit", 1.0) < 0.8:
            adaptations.append({
                "type": "hardware",
                "target": "confidence_threshold",
                "before": self.thresholds["confidence_threshold"].value,
                "after": self.thresholds["confidence_threshold"].value * constraints.get("memory_limit", 0.8),
                "improvement": constraints.get("memory_limit", 0.8) - self.thresholds["confidence_threshold"].value,
                "performance_gain": 0.0,
                "feedback": f"Hardware constraint: Memory limit {constraints.get('memory_limit', 0.8)}",
            })

        return adaptations

    def _check_and_adapt_if_needed(
        self,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """检查并执行自适应"""
        if len(self.performance_history) < 10:
            return

        # 获取最近的性能指标
        recent_metrics = self._get_recent_metrics()

        # 评估系统状态
        state_result = self.evaluate_system_state(recent_metrics, context or {})

        # 如果需要自适应，执行自适应
        if state_result["needs_adaptation"]:
            self.adapt_thresholds(recent_metrics, context, force_adaptation=False)

    def _get_recent_metrics(self) -> Dict[str, Any]:
        """获取最近的性能指标"""
        if not self.performance_history:
            return {}

        # 获取最近10个性能记录
        recent_metrics = []
        for metric_record in list(self.performance_history)[-10:]:
            recent_metrics.append({
                "accuracy": metric_record.accuracy,
                "latency": metric_record.latency,
                "throughput": metric_record.throughput,
                "error_rate": metric_record.error_rate,
                "resource_usage": metric_record.resource_usage,
                "memory_usage": metric_record.memory_usage,
            })

        # 计算平均值
        if not recent_metrics:
            return {}

        averaged_metrics = {}
        for key in recent_metrics[0].keys():
            averaged_metrics[key] = sum(m[key] for m in recent_metrics) / len(recent_metrics)

        return averaged_metrics

    def _calculate_adaptation_statistics(
        self,
        start_time: float,
        end_time: float,
    ) -> Dict[str, Any]:
        """计算自适应统计"""
        try:
            adaptations_in_window = [
                cycle for cycle in self.optimization_cycles
                if start_time <= cycle["timestamp"] <= end_time
            ]

            if not adaptations_in_window:
                return {
                    "total_adaptations": 0,
                    "success_rate": 0.0,
                    "average_improvement": 0.0,
                    "total_performance_gain": 0.0,
                }

            total_adaptations = len(adaptations_in_window)
            success_count = sum(1 for cycle in adaptations_in_window if cycle.get("success", False))

            average_improvement = sum(
                sum(abs(imp) for imp in cycle.get("improvements", {}).values())
                for cycle in adaptations_in_window
            ) / max(1, total_adaptations)

            total_performance_gain = sum(
                cycle.get("improvements", {}).get("max_latency_ms", 0.0)
                for cycle in adaptations_in_window
            )

            return {
                "total_adaptations": total_adaptations,
                "success_rate": success_count / max(1, total_adaptations),
                "average_improvement": average_improvement,
                "total_performance_gain": total_performance_gain,
                "urgency_distribution": self._calculate_urgency_distribution(adaptations_in_window),
            }

        except Exception as e:
            logger.error(f"Error calculating adaptation statistics: {e}", exc_info=True)
            return {"error": str(e)}

    def _calculate_threshold_statistics(
        self,
        start_time: float,
        end_time: float,
    ) -> Dict[str, Any]:
        """计算阈值统计"""
        try:
            thresholds_in_window = []
            for cycle in self.optimization_cycles:
                if start_time <= cycle["timestamp"] <= end_time:
                    thresholds_in_window.extend([
                        (name, after_value)
                        for name, after_value in cycle.get("after", {}).items()
                    ])

            if not thresholds_in_window:
                return {
                    "threshold_names": [],
                    "value_distributions": {},
                    "adaptation_frequency": {},
                }

            # 按阈值名称分组
            threshold_distributions = {}
            adaptation_frequency = {}

            for name, value in thresholds_in_window:
                if name not in threshold_distributions:
                    threshold_distributions[name] = []
                threshold_distributions[name].append(value)

                if name not in adaptation_frequency:
                    adaptation_frequency[name] = 0
                adaptation_frequency[name] += 1

            # 计算统计值
            threshold_stats = {}
            for name, values in threshold_distributions.items():
                threshold_stats[name] = {
                    "count": len(values),
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "std": (sum((v - sum(values) / len(values)) ** 2 for v in values) / len(values)) ** 0.5,
                }

            return {
                "threshold_names": list(threshold_distributions.keys()),
                "value_distributions": threshold_stats,
                "adaptation_frequency": adaptation_frequency,
            }

        except Exception as e:
            logger.error(f"Error calculating threshold statistics: {e}", exc_info=True)
            return {"error": str(e)}

    def _calculate_performance_trends(
        self,
        start_time: float,
        end_time: float,
    ) -> Dict[str, Any]:
        """计算性能趋势"""
        try:
            if not self.performance_history:
                return {"accuracy_trend": 0.0, "latency_trend": 0.0}

            # 获取窗口内性能记录
            metrics_in_window = []
            for metric_record in self.performance_history:
                if start_time <= metric_record.timestamp <= end_time:
                    metrics_in_window.append(metric_record)

            if len(metrics_in_window) < 2:
                return {"accuracy_trend": 0.0, "latency_trend": 0.0}

            # 计算趋势
            accuracy_trend = sum(
                (metric.accuracy - metrics_in_window[0].accuracy)
                for metric in metrics_in_window[1:]
            ) / (len(metrics_in_window) - 1)

            latency_trend = sum(
                (metrics_in_window[0].latency - metric.latency)
                for metric in metrics_in_window[1:]
            ) / (len(metrics_in_window) - 1)

            return {
                "accuracy_trend": accuracy_trend,
                "latency_trend": latency_trend,
                "sample_count": len(metrics_in_window),
            }

        except Exception as e:
            logger.error(f"Error calculating performance trends: {e}", exc_info=True)
            return {"error": str(e)}

    def _calculate_urgency_distribution(
        self,
        adaptations: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """计算紧急程度分布"""
        distribution = {"low": 0, "medium": 0, "high": 0, "error": 0}

        for adaptation in adaptations:
            urgency = adaptation.get("urgency_level", "low")
            if urgency in distribution:
                distribution[urgency] += 1

        return distribution

    def _check_adaptation_success(
        self,
        metrics: Dict[str, Any],
        before_metrics: Dict[str, Any],
    ) -> bool:
        """检查自适应是否成功"""
        if not before_metrics:
            return True

        # 检查延迟改进
        latency_improved = metrics.get("latency", 0) < before_metrics.get("latency", 0)

        # 检查准确率改进
        accuracy_improved = metrics.get("accuracy", 0) > before_metrics.get("accuracy", 0)

        # 检查错误率改进
        error_rate_improved = metrics.get("error_rate", 0) < before_metrics.get("error_rate", 0)

        return (latency_improved and accuracy_improved) or error_rate_improved or not any([
            metrics.get("latency", 0) > before_metrics.get("latency", 0) * 1.5,
            metrics.get("accuracy", 0) < before_metrics.get("accuracy", 0) * 0.9,
            metrics.get("error_rate", 0) > before_metrics.get("error_rate", 0) * 1.5,
        ])

    def _get_performance_target_key_from_metric(
        self,
        metric_name: str,
    ) -> Optional[str]:
        """根据指标名称获取性能目标键"""
        mapping = {
            "latency": "max_latency_ms",
            "accuracy": "min_accuracy",
            "throughput": "target_throughput",
            "error_rate": "min_accuracy",
            "resource_usage": "max_memory_usage",
            "memory_usage": "max_memory_usage",
        }
        return mapping.get(metric_name)

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "timestamp": time.time(),
            "is_initialized": True,
            "adaptation_mode": self.current_adaptation_mode.value,
            "performance_history_size": len(self.performance_history),
            "adaptation_history_size": len(self.adaptation_history),
            "thresholds_count": len(self.thresholds) + len(self.performance_thresholds),
            "hardware_profile": self.hardware_profile.get_profile_name() if self.hardware_profile else "unknown",
            "adaptation_efficiency": self._calculate_adaptation_efficiency(),
            "optimization_effectiveness": self._calculate_optimization_effectiveness(),
        }

    def reset_system(self) -> None:
        """重置系统"""
        try:
            # 清除历史记录
            self.performance_history.clear()
            self.resource_usage_history.clear()
            self.adaptation_history.clear()
            self.optimization_cycles.clear()

            # 重置阈值到默认值
            for name, config in self.thresholds.items():
                config.value = config.default_value

            for name, config in self.performance_thresholds.items():
                config.value = config.default_value

            # 重置适应模式
            self.current_adaptation_mode = AdaptationMode.BALANCED

            logger.info("DynamicThresholdManager system reset completed")

        except Exception as e:
            logger.error(f"Error resetting system: {e}", exc_info=True)

    def __str__(self) -> str:
        return f"DynamicThresholdManager(adaptation_mode={self.current_adaptation_mode.value}, thresholds={len(self.thresholds)}, performance_thresholds={len(self.performance_thresholds)})"

    def __repr__(self) -> str:
        return self.__str__()

