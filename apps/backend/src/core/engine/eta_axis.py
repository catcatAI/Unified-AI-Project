"""
η (Eta) Axis — Execution/Operation Layer
========================================

η is the 7th axis (after αβγδεθ) that handles execution/operation,
contrasting θ's cognitive/evaluation role.

Layer 0 — Atomic Modules: LogicGate, ArithmeticOp, Aggregator, Router
Layer 1 — Composed Modules: Built from atoms
Layer 2 — Adjusted Modules: Parameter-adjusted versions

Trigger Curve:
  modules_to_call = floor(min(12, 3 × sigmoid(complexity × axis_count / 6)))
  adjustment_magnitude = min(0.2, 0.15 × sigmoid(complexity - 0.5))

Author: Angela AI v6.2.1
Version: 6.2.1
Date: 2026-05-15
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime
import math
import logging

logger = logging.getLogger(__name__)


def sigmoid(x: float) -> float:
    """Sigmoid function with clipping for numerical stability."""
    if x > 20:
        return 1.0
    if x < -20:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


# =============================================================================
# Layer 0 — Atomic Modules
# =============================================================================

class AtomicModuleType(Enum):
    LOGIC_GATE = auto()
    ARITHMETIC_OP = auto()
    AGGREGATOR = auto()
    ROUTER = auto()


class LogicGateType(Enum):
    AND = auto()
    OR = auto()
    NOT = auto()
    XOR = auto()
    THRESHOLD = auto()


class ArithmeticOpType(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    CUSTOM_EXPR = auto()


class AggregatorType(Enum):
    SUM = auto()
    MEAN = auto()
    MAX = auto()
    MIN = auto()
    WEIGHTED_AVG = auto()


class RouterType(Enum):
    DIRECT = auto()
    FANOUT = auto()
    MERGE = auto()
    SPLIT = auto()


@dataclass
class ModuleConfig:
    """Configuration for a single atomic module."""
    name: str
    module_type: AtomicModuleType
    sub_type: Any
    parameters: Dict[str, Any]
    tags: List[str] = field(default_factory=list)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    adjusted_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "module_type": self.module_type.name,
            "sub_type": self.sub_type.name if hasattr(self.sub_type, 'name') else str(self.sub_type),
            "parameters": self.parameters,
            "tags": self.tags,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "adjusted_count": self.adjusted_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModuleConfig:
        mt = AtomicModuleType[data.get("module_type", "LOGIC_GATE")]
        st = data.get("sub_type", "AND")
        if mt == AtomicModuleType.LOGIC_GATE:
            st = LogicGateType[st] if isinstance(st, str) else st
        elif mt == AtomicModuleType.ARITHMETIC_OP:
            st = ArithmeticOpType[st] if isinstance(st, str) else st
        elif mt == AtomicModuleType.AGGREGATOR:
            st = AggregatorType[st] if isinstance(st, str) else st
        elif mt == AtomicModuleType.ROUTER:
            st = RouterType[st] if isinstance(st, str) else st
        return cls(
            name=data["name"],
            module_type=mt,
            sub_type=st,
            parameters=data.get("parameters", {}),
            tags=data.get("tags", []),
            version=data.get("version", 1),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            adjusted_count=data.get("adjusted_count", 0),
        )


@dataclass
class AtomicModule:
    """Layer 0: Atomic module that cannot be split further."""
    config: ModuleConfig

    def execute(self, inputs: Dict[str, Any]) -> Any:
        """Execute the atomic module with given inputs."""
        if self.config.module_type == AtomicModuleType.LOGIC_GATE:
            return self._execute_logic_gate(inputs)
        elif self.config.module_type == AtomicModuleType.ARITHMETIC_OP:
            return self._execute_arithmetic_op(inputs)
        elif self.config.module_type == AtomicModuleType.AGGREGATOR:
            return self._execute_aggregator(inputs)
        elif self.config.module_type == AtomicModuleType.ROUTER:
            return self._execute_router(inputs)
        return None

    def _execute_logic_gate(self, inputs: Dict[str, Any]) -> bool:
        gate_type = self.config.sub_type
        params = self.config.parameters

        if gate_type == LogicGateType.AND:
            values = inputs.get("values", [])
            return all(v > 0 for v in values)

        elif gate_type == LogicGateType.OR:
            values = inputs.get("values", [])
            return any(v > 0 for v in values)

        elif gate_type == LogicGateType.NOT:
            value = inputs.get("value", 0)
            return value <= 0

        elif gate_type == LogicGateType.XOR:
            values = inputs.get("values", [])
            return sum(1 for v in values if v > 0) == 1

        elif gate_type == LogicGateType.THRESHOLD:
            value = inputs.get("value", 0)
            threshold = params.get("threshold", 0.5)
            operator = params.get("operator", ">")
            if operator == ">":
                return value > threshold
            elif operator == ">=":
                return value >= threshold
            elif operator == "<":
                return value < threshold
            elif operator == "<=":
                return value <= threshold
            elif operator == "==":
                return abs(value - threshold) < 1e-9
            return False

        return False

    def _execute_arithmetic_op(self, inputs: Dict[str, Any]) -> float:
        op_type = self.config.sub_type
        params = self.config.parameters

        if op_type == ArithmeticOpType.ADD:
            values = inputs.get("values", [])
            return sum(values)

        elif op_type == ArithmeticOpType.SUB:
            a = inputs.get("a", 0)
            b = inputs.get("b", 0)
            return a - b

        elif op_type == ArithmeticOpType.MUL:
            values = inputs.get("values", [1])
            result = 1.0
            for v in values:
                result *= v
            return result

        elif op_type == ArithmeticOpType.DIV:
            a = inputs.get("a", 0)
            b = inputs.get("b", 1)
            return a / b if b != 0 else 0.0

        elif op_type == ArithmeticOpType.CUSTOM_EXPR:
            expr = params.get("expr", "")
            try:
                local_vars = dict(inputs)
                import re
                safe = re.sub(r"[^0-9+\-*/().%\s_a-zA-Z]", "", expr)
                return eval(safe, {"__builtins__": {}}, local_vars)
            except Exception:
                return 0.0

        return 0.0

    def _execute_aggregator(self, inputs: Dict[str, Any]) -> float:
        agg_type = self.config.sub_type
        params = self.config.parameters
        values = inputs.get("values", [])

        if not values:
            return 0.0

        if agg_type == AggregatorType.SUM:
            return sum(values)

        elif agg_type == AggregatorType.MEAN:
            return sum(values) / len(values)

        elif agg_type == AggregatorType.MAX:
            return max(values)

        elif agg_type == AggregatorType.MIN:
            return min(values)

        elif agg_type == AggregatorType.WEIGHTED_AVG:
            weights = params.get("weights", [1.0] * len(values))
            total_weight = sum(weights)
            if total_weight == 0:
                return 0.0
            return sum(v * w for v, w in zip(values, weights)) / total_weight

        return 0.0

    def _execute_router(self, inputs: Dict[str, Any]) -> List[str]:
        router_type = self.config.sub_type
        params = self.config.parameters
        targets = params.get("targets", [])

        if router_type == RouterType.DIRECT:
            return [targets[0]] if targets else []

        elif router_type == RouterType.FANOUT:
            return targets

        elif router_type == RouterType.MERGE:
            return [params.get("output", "merged")]

        elif router_type == RouterType.SPLIT:
            value = inputs.get("value", 0)
            threshold = params.get("threshold", 0.5)
            if value > threshold:
                return [targets[0]] if targets else []
            return targets

        return targets


# =============================================================================
# Layer 1 — Composed Modules
# =============================================================================

@dataclass
class ComposedModule:
    """Layer 1: Composed module built from atomic modules."""
    name: str
    atoms: List[AtomicModule]
    composition: Dict[str, Any]
    output_mapping: Dict[str, List[str]]
    version: int = 1

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all atoms in composition order."""
        context = dict(inputs)
        for atom in self.atoms:
            result = atom.execute(context)
            context[atom.config.name] = result
        return context

    def adjust(self, **params) -> ComposedModule:
        """Return adjusted version with new parameters."""
        new_atoms = []
        for atom in self.atoms:
            new_config = ModuleConfig(
                name=atom.config.name,
                module_type=atom.config.module_type,
                sub_type=atom.config.sub_type,
                parameters={**atom.config.parameters, **params},
                tags=list(atom.config.tags),
                version=atom.config.version + 1,
                adjusted_count=atom.config.adjusted_count + 1,
            )
            new_atoms.append(AtomicModule(new_config))
        return ComposedModule(
            name=self.name,
            atoms=new_atoms,
            composition=dict(self.composition),
            output_mapping=dict(self.output_mapping),
            version=self.version + 1,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "atoms": [a.config.to_dict() for a in self.atoms],
            "composition": self.composition,
            "output_mapping": self.output_mapping,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ComposedModule:
        atoms = [AtomicModule(ModuleConfig.from_dict(a)) for a in data.get("atoms", [])]
        return cls(
            name=data["name"],
            atoms=atoms,
            composition=data.get("composition", {}),
            output_mapping=data.get("output_mapping", {}),
            version=data.get("version", 1),
        )


# =============================================================================
# Trigger Curve
# =============================================================================

class TriggerCurve:
    """
    Sigmoid-based trigger curve for module invocation.

    Formula:
      modules = floor(min(CAP, BASE × sigmoid(complexity × axis_count / 6)))
      delta = min(MAX_DELTA, BASE_DELTA × sigmoid(complexity - 0.5))
    """

    BASE: float = 3.0
    CAP: float = 12.0
    AXIS_COUNT_REF: float = 6.0
    MAX_DELTA: float = 0.2
    BASE_DELTA: float = 0.15

    def __init__(self, base: float = None, cap: float = None, max_delta: float = None, base_delta: float = None):
        self.BASE = base if base is not None else 3.0
        self.CAP = cap if cap is not None else 12.0
        self.MAX_DELTA = max_delta if max_delta is not None else 0.2
        self.BASE_DELTA = base_delta if base_delta is not None else 0.15

    def compute_modules(self, complexity: float, axis_count: int) -> int:
        """
        Compute number of modules to invoke based on complexity and axis count.

        Args:
            complexity: Signal intensity (0-1)
            axis_count: Number of axes in system

        Returns:
            Number of modules to invoke (capped at CAP)
        """
        x = complexity * axis_count / self.AXIS_COUNT_REF
        result = self.BASE * sigmoid(x)
        return min(int(self.CAP), max(1, int(result)))

    def compute_delta(self, complexity: float) -> float:
        """
        Compute parameter adjustment magnitude.

        Args:
            complexity: Signal intensity (0-1)

        Returns:
            Adjustment magnitude (0-MAX_DELTA)
        """
        x = complexity - 0.5
        return min(self.MAX_DELTA, self.BASE_DELTA * sigmoid(x))

    def compute_trigger_threshold(self, actual_rate: float, target_rate: float, current: float = 0.5) -> float:
        """
        Adaptively adjust trigger threshold based on actual vs target rate.

        Args:
            actual_rate: Actual trigger rate
            target_rate: Desired trigger rate
            current: Current threshold

        Returns:
            Adjusted threshold
        """
        alpha = 0.1
        adjustment = alpha * (target_rate - actual_rate)
        return max(0.1, min(0.9, current + adjustment))


# =============================================================================
# Eta Axis State
# =============================================================================

@dataclass
class UpdateOp:
    """Pending parameter update operation."""
    module_name: str
    parameter: str
    old_value: Any
    new_value: Any
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "parameter": self.parameter,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


class EtaAxisState:
    """
    η (Eta) Axis State — Execution/Operation Layer.

    Fields:
      module_registry: Dict[str, ModuleConfig] — All modules index
      active_modules: List[str] — Currently active module names
      execution_count: int — Total execution count
      success_rate: float — Routing success rate (0-1)
      parameter_tuning: Dict[str, float] — Adjustment magnitude per module
      structural_drift: float — Structural drift (0-1)
      module_composition: Dict[str, Any] — Current topology snapshot
      pending_updates: List[UpdateOp] — Pending parameter updates
    """

    def __init__(self):
        self.module_registry: Dict[str, ModuleConfig] = {}
        self.active_modules: List[str] = []
        self.execution_count: int = 0
        self.success_rate: float = 1.0
        self.parameter_tuning: Dict[str, float] = {}
        self.structural_drift: float = 0.0
        self.module_composition: Dict[str, Any] = {}
        self.pending_updates: List[UpdateOp] = []
        self._trigger_curve = TriggerCurve()
        self._last_trigger_time = datetime.now()
        self._trigger_count = 0
        self._no_trigger_count = 0
        self._trigger_threshold = 0.5

    @property
    def axis_count(self) -> int:
        """Get current axis count from module composition."""
        return len(self.module_composition.get("axes", ["alpha", "beta", "gamma", "delta", "epsilon", "theta"]))

    def register_module(self, config: ModuleConfig) -> None:
        """Register a new module."""
        self.module_registry[config.name] = config
        if config.name not in self.active_modules:
            self.active_modules.append(config.name)

    def unregister_module(self, name: str) -> None:
        """Unregister a module."""
        if name in self.module_registry:
            del self.module_registry[name]
        if name in self.active_modules:
            self.active_modules.remove(name)

    def get_module(self, name: str) -> Optional[ModuleConfig]:
        """Get module configuration by name."""
        return self.module_registry.get(name)

    def activate_module(self, name: str) -> bool:
        """Activate a module."""
        if name in self.module_registry and name not in self.active_modules:
            self.active_modules.append(name)
            return True
        return False

    def deactivate_module(self, name: str) -> bool:
        """Deactivate a module."""
        if name in self.active_modules:
            self.active_modules.remove(name)
            return True
        return False

    def execute(self, module_name: str, inputs: Dict[str, Any]) -> Any:
        """Execute a registered module."""
        config = self.module_registry.get(module_name)
        if not config:
            return None

        atom = AtomicModule(config)
        result = atom.execute(inputs)
        self.execution_count += 1
        return result

    def execute_active_modules(self, inputs: Dict[str, Any]) -> List[Tuple[str, Any]]:
        """Execute all active modules in sequence."""
        results = []
        for name in self.active_modules:
            config = self.module_registry.get(name)
            if config:
                atom = AtomicModule(config)
                result = atom.execute(inputs)
                results.append((name, result))
        self.execution_count += len(results)
        return results

    def compute_invocation_count(self, complexity: float) -> int:
        """Compute how many modules to invoke based on trigger curve."""
        return self._trigger_curve.compute_modules(complexity, self.axis_count)

    def apply_theta_signals(self, signals: Dict[str, float]) -> Dict[str, Any]:
        """
        Apply θ signals to compute module invocation.

        Args:
            signals: Dict with keys: update_frequency, complexity_delta,
                     novelty_peak, misallocation_rate, buffer_pressure

        Returns:
            Dict with modules_to_call, delta, triggered, threshold
        """
        complexity = signals.get("complexity_delta", 0.5)
        modules_to_call = self.compute_invocation_count(complexity)
        delta = self._trigger_curve.compute_delta(complexity)

        signal_strength = self._compute_signal_strength(signals)
        triggered = signal_strength > self._trigger_threshold

        now = datetime.now()
        if triggered:
            self._trigger_count += 1
            self._no_trigger_count = 0
            self._last_trigger_time = now
        else:
            self._no_trigger_count += 1
            if self._no_trigger_count > 10:
                self._trigger_threshold = self._trigger_curve.compute_trigger_threshold(
                    actual_rate=self._trigger_count / max(1, self._trigger_count + self._no_trigger_count),
                    target_rate=0.3,
                    current=self._trigger_threshold,
                )
                self._no_trigger_count = 0

        return {
            "modules_to_call": min(modules_to_call, len(self.active_modules)),
            "delta": delta,
            "triggered": triggered,
            "threshold": self._trigger_threshold,
            "signal_strength": signal_strength,
        }

    def _compute_signal_strength(self, signals: Dict[str, float]) -> float:
        """Compute overall signal strength from individual signals."""
        weights = {
            "update_frequency": 0.2,
            "complexity_delta": 0.3,
            "novelty_peak": 0.2,
            "misallocation_rate": 0.2,
            "buffer_pressure": 0.1,
        }
        total = 0.0
        weight_sum = 0.0
        for key, weight in weights.items():
            if key in signals:
                total += signals[key] * weight
                weight_sum += weight
        return total / weight_sum if weight_sum > 0 else 0.0

    def adjust_parameter(self, module_name: str, param: str, delta: float) -> None:
        """Adjust a module parameter by delta."""
        config = self.module_registry.get(module_name)
        if config and param in config.parameters:
            old_value = config.parameters[param]
            new_value = max(0.0, min(1.0, old_value + delta))
            config.parameters[param] = new_value
            config.adjusted_count += 1

            self.pending_updates.append(UpdateOp(
                module_name=module_name,
                parameter=param,
                old_value=old_value,
                new_value=new_value,
                reason=f"delta={delta}",
            ))

            self.parameter_tuning[module_name] = self.parameter_tuning.get(module_name, 0.0) + abs(delta)

    def apply_parameter_delta(self, delta: float) -> int:
        """Apply delta to all active modules."""
        count = 0
        for name in self.active_modules:
            config = self.module_registry.get(name)
            if config and config.parameters:
                for param in list(config.parameters.keys()):
                    if isinstance(config.parameters[param], (int, float)):
                        self.adjust_parameter(name, param, delta)
                        count += 1
        return count

    def update_composition(self) -> None:
        """Update module composition snapshot."""
        self.module_composition = {
            "total_modules": len(self.module_registry),
            "active_modules": len(self.active_modules),
            "execution_count": self.execution_count,
            "success_rate": self.success_rate,
            "structural_drift": self.structural_drift,
            "axes": ["alpha", "beta", "gamma", "delta", "epsilon", "theta"],
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "module_registry": {k: v.to_dict() for k, v in self.module_registry.items()},
            "active_modules": list(self.active_modules),
            "execution_count": self.execution_count,
            "success_rate": self.success_rate,
            "parameter_tuning": dict(self.parameter_tuning),
            "structural_drift": self.structural_drift,
            "module_composition": dict(self.module_composition),
            "pending_updates": [u.to_dict() for u in self.pending_updates[-50:]],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EtaAxisState:
        """Deserialize from dictionary."""
        state = cls()
        state.module_registry = {k: ModuleConfig.from_dict(v) for k, v in data.get("module_registry", {}).items()}
        state.active_modules = list(data.get("active_modules", []))
        state.execution_count = data.get("execution_count", 0)
        state.success_rate = data.get("success_rate", 1.0)
        state.parameter_tuning = data.get("parameter_tuning", {})
        state.structural_drift = data.get("structural_drift", 0.0)
        state.module_composition = data.get("module_composition", {})
        state.pending_updates = [
            UpdateOp(
                module_name=u["module_name"],
                parameter=u["parameter"],
                old_value=u["old_value"],
                new_value=u["new_value"],
                reason=u["reason"],
                timestamp=datetime.fromisoformat(u["timestamp"]) if "timestamp" in u else datetime.now(),
            )
            for u in data.get("pending_updates", [])
        ]
        return state


# =============================================================================
# Default Modules Factory
# =============================================================================

def create_default_modules() -> Dict[str, ModuleConfig]:
    """Create default module registry with common patterns."""
    return {
        "logic_AND": ModuleConfig(
            name="logic_AND",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={},
            tags=["logic", "gate", "and"],
        ),
        "logic_OR": ModuleConfig(
            name="logic_OR",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.OR,
            parameters={},
            tags=["logic", "gate", "or"],
        ),
        "logic_NOT": ModuleConfig(
            name="logic_NOT",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.NOT,
            parameters={},
            tags=["logic", "gate", "not"],
        ),
        "logic_XOR": ModuleConfig(
            name="logic_XOR",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.XOR,
            parameters={},
            tags=["logic", "gate", "xor"],
        ),
        "logic_threshold_7": ModuleConfig(
            name="logic_threshold_7",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.THRESHOLD,
            parameters={"threshold": 0.7, "operator": ">"},
            tags=["logic", "threshold", "high"],
        ),
        "logic_threshold_5": ModuleConfig(
            name="logic_threshold_5",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.THRESHOLD,
            parameters={"threshold": 0.5, "operator": ">"},
            tags=["logic", "threshold", "medium"],
        ),
        "logic_threshold_3": ModuleConfig(
            name="logic_threshold_3",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.THRESHOLD,
            parameters={"threshold": 0.3, "operator": ">"},
            tags=["logic", "threshold", "low"],
        ),
        "arith_ADD": ModuleConfig(
            name="arith_ADD",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.ADD,
            parameters={},
            tags=["arithmetic", "add", "sum"],
        ),
        "arith_SUB": ModuleConfig(
            name="arith_SUB",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.SUB,
            parameters={},
            tags=["arithmetic", "subtract"],
        ),
        "arith_MUL": ModuleConfig(
            name="arith_MUL",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.MUL,
            parameters={},
            tags=["arithmetic", "multiply"],
        ),
        "arith_DIV": ModuleConfig(
            name="arith_DIV",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.DIV,
            parameters={},
            tags=["arithmetic", "divide"],
        ),
        "arith_error_rate": ModuleConfig(
            name="arith_error_rate",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.CUSTOM_EXPR,
            parameters={"expr": "bugs/total*100"},
            tags=["arithmetic", "custom", "error_rate"],
        ),
        "agg_SUM": ModuleConfig(
            name="agg_SUM",
            module_type=AtomicModuleType.AGGREGATOR,
            sub_type=AggregatorType.SUM,
            parameters={},
            tags=["aggregator", "sum"],
        ),
        "agg_MEAN": ModuleConfig(
            name="agg_MEAN",
            module_type=AtomicModuleType.AGGREGATOR,
            sub_type=AggregatorType.MEAN,
            parameters={},
            tags=["aggregator", "mean", "average"],
        ),
        "agg_MAX": ModuleConfig(
            name="agg_MAX",
            module_type=AtomicModuleType.AGGREGATOR,
            sub_type=AggregatorType.MAX,
            parameters={},
            tags=["aggregator", "max"],
        ),
        "agg_MIN": ModuleConfig(
            name="agg_MIN",
            module_type=AtomicModuleType.AGGREGATOR,
            sub_type=AggregatorType.MIN,
            parameters={},
            tags=["aggregator", "min"],
        ),
        "agg_weighted_avg_6040": ModuleConfig(
            name="agg_weighted_avg_6040",
            module_type=AtomicModuleType.AGGREGATOR,
            sub_type=AggregatorType.WEIGHTED_AVG,
            parameters={"weights": [0.6, 0.4]},
            tags=["aggregator", "weighted", "60-40"],
        ),
        "router_DIRECT": ModuleConfig(
            name="router_DIRECT",
            module_type=AtomicModuleType.ROUTER,
            sub_type=RouterType.DIRECT,
            parameters={"targets": ["default"]},
            tags=["router", "direct"],
        ),
        "router_FANOUT": ModuleConfig(
            name="router_FANOUT",
            module_type=AtomicModuleType.ROUTER,
            sub_type=RouterType.FANOUT,
            parameters={"targets": ["alpha", "beta", "gamma"]},
            tags=["router", "fanout", "broadcast"],
        ),
        "router_MERGE": ModuleConfig(
            name="router_MERGE",
            module_type=AtomicModuleType.ROUTER,
            sub_type=RouterType.MERGE,
            parameters={"output": "merged"},
            tags=["router", "merge"],
        ),
        "router_SPLIT": ModuleConfig(
            name="router_SPLIT",
            module_type=AtomicModuleType.ROUTER,
            sub_type=RouterType.SPLIT,
            parameters={"threshold": 0.5, "targets": ["high", "low"]},
            tags=["router", "split", "conditional"],
        ),
    }