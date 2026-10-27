"""
η (Eta) Axis — Execution/Operation Layer
"""

from __future__ import annotations

import enum
import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from core.security.secure_eval import safe_eval

logger = logging.getLogger(__name__)


def sigmoid(x: float) -> float:
    if x >= 50:
        return 1.0
    if x <= -50:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


class AtomicModuleType(enum.Enum):
    LOGIC_GATE = "logic_gate"
    ARITHMETIC_OP = "arithmetic_op"
    AGGREGATOR = "aggregator"
    ROUTER = "router"


class LogicGateType(enum.Enum):
    AND = "and"
    OR = "or"
    NOT = "not"
    XOR = "xor"
    THRESHOLD = "threshold"
    NAND = "nand"
    NOR = "nor"


class ArithmeticOpType(enum.Enum):
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    CUSTOM_EXPR = "custom_expr"


class AggregatorType(enum.Enum):
    SUM = "sum"
    MEAN = "mean"
    MAX = "max"
    MIN = "min"
    WEIGHTED_AVG = "weighted_avg"


class RouterType(enum.Enum):
    DIRECT = "direct"
    FANOUT = "fanout"
    SPLIT = "split"
    ROUND_ROBIN = "round_robin"


@dataclass
class ModuleConfig:
    name: str
    module_type: AtomicModuleType
    sub_type: Union[LogicGateType, ArithmeticOpType, AggregatorType, RouterType]
    parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "module_type": self.module_type.value,
            "sub_type": self.sub_type.value,
            "parameters": dict(self.parameters),
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ModuleConfig:
        mt = AtomicModuleType(data["module_type"])
        st = _resolve_sub_type(mt, data["sub_type"])
        return cls(
            name=data["name"],
            module_type=mt,
            sub_type=st,
            parameters=data.get("parameters", {}),
            tags=data.get("tags", []),
        )


def _resolve_sub_type(
    mt: AtomicModuleType, value: str
) -> Union[LogicGateType, ArithmeticOpType, AggregatorType, RouterType]:
    mapping: Dict[AtomicModuleType, type] = {
        AtomicModuleType.LOGIC_GATE: LogicGateType,
        AtomicModuleType.ARITHMETIC_OP: ArithmeticOpType,
        AtomicModuleType.AGGREGATOR: AggregatorType,
        AtomicModuleType.ROUTER: RouterType,
    }
    enum_cls = mapping.get(mt)
    if enum_cls is None:
        raise ValueError(f"Unknown module type: {mt}")
    # enum_cls is a type (e.g., LogicGateType), iterate over its members
    for member in enum_cls:  # type: ignore[attr-defined]
        if member.value == value:
            return cast(Union[LogicGateType, ArithmeticOpType, AggregatorType, RouterType], member)
    raise ValueError(f"Unknown sub_type {value} for {mt}")


class AtomicModule:
    def __init__(self, config: ModuleConfig):
        self.config = config

    def execute(self, kwargs: Dict[str, Any]) -> Any:
        mt = self.config.module_type
        st = self.config.sub_type
        params = self.config.parameters
        if mt == AtomicModuleType.LOGIC_GATE:
            return self._exec_logic(st, kwargs, params)  # type: ignore[arg-type]
        if mt == AtomicModuleType.ARITHMETIC_OP:
            return self._exec_arithmetic(st, kwargs, params)  # type: ignore[arg-type]
        if mt == AtomicModuleType.AGGREGATOR:
            return self._exec_aggregator(st, kwargs, params)  # type: ignore[arg-type]
        if mt == AtomicModuleType.ROUTER:
            return self._exec_router(st, kwargs, params)  # type: ignore[arg-type]
        raise ValueError(f"Unknown module type: {mt}")

    def _exec_logic(self, st: LogicGateType, kwargs: Dict, params: Dict) -> bool:
        if st == LogicGateType.AND:
            vals = kwargs.get("values", [])
            return bool(all(v > 0 for v in vals))
        if st == LogicGateType.OR:
            vals = kwargs.get("values", [])
            return bool(any(v > 0 for v in vals))
        if st == LogicGateType.NOT:
            val = float(kwargs.get("value", 0.0))
            return val <= 0
        if st == LogicGateType.XOR:
            vals = kwargs.get("values", [])
            return bool(sum(1 for v in vals if v > 0) % 2 == 1)
        if st == LogicGateType.THRESHOLD:
            val = float(kwargs.get("value", 0.0))
            threshold = float(params.get("threshold", 0.5))
            operator = str(params.get("operator", ">"))
            if operator == ">":
                return val > threshold
            return val >= threshold
        return False

    @staticmethod
    def _arithmetic_div(kwargs: Dict) -> float:
        """DIV with zero-guard (returns 0.0 on b == 0)."""
        a = float(kwargs.get("a", 0.0))
        b = float(kwargs.get("b", 1.0))
        if b == 0.0:
            return 0.0
        return a / b

    @staticmethod
    def _arithmetic_custom_expr(kwargs: Dict, params: Dict) -> float:
        """CUSTOM_EXPR via safe_eval; failure/non-convertible → 0.0."""
        expr = params.get("expr", "0")
        local_vars = {k: float(v) for k, v in kwargs.items()}
        eval_result = safe_eval(expr, context=local_vars)
        if eval_result.success and eval_result.result is not None:
            try:
                return float(eval_result.result)
            except (TypeError, ValueError):
                logger.debug(
                    "Custom expression result not convertible to float: %s", eval_result.result
                )
                return 0.0
        logger.debug("Custom expression eval failed (%s): %s", expr, eval_result.error)
        return 0.0

    def _exec_arithmetic(self, st: ArithmeticOpType, kwargs: Dict, params: Dict) -> float:
        if st == ArithmeticOpType.ADD:
            vals = kwargs.get("values", [])
            return float(sum(vals))
        if st == ArithmeticOpType.SUB:
            a = float(kwargs.get("a", 0.0))
            b = float(kwargs.get("b", 0.0))
            return a - b
        if st == ArithmeticOpType.MUL:
            vals = kwargs.get("values", [])
            result = 1.0
            for v in vals:
                result *= float(v)
            return result
        if st == ArithmeticOpType.DIV:
            return self._arithmetic_div(kwargs)
        if st == ArithmeticOpType.CUSTOM_EXPR:
            return self._arithmetic_custom_expr(kwargs, params)
        return 0.0

    def _exec_aggregator(self, st: AggregatorType, kwargs: Dict, params: Dict) -> float:
        vals = [float(v) for v in kwargs.get("values", [])]
        if not vals:
            return 0.0
        if st == AggregatorType.SUM:
            return float(sum(vals))
        if st == AggregatorType.MEAN:
            return float(sum(vals) / len(vals))
        if st == AggregatorType.MAX:
            return float(max(vals))
        if st == AggregatorType.MIN:
            return float(min(vals))
        if st == AggregatorType.WEIGHTED_AVG:
            weights = params.get("weights", [1.0 / len(vals)] * len(vals))
            return float(sum(v * w for v, w in zip(vals, weights)))
        return 0.0

    def _exec_router(self, st: RouterType, kwargs: Dict, params: Dict) -> List[Any]:
        targets = params.get("targets", [])
        if st == RouterType.DIRECT:
            return [targets[0]] if targets else []
        if st == RouterType.FANOUT:
            return list(targets)
        if st == RouterType.SPLIT:
            value = kwargs.get("value", 0.0)
            threshold = params.get("threshold", 0.5)
            if value >= threshold:
                return [targets[0]] if targets else []
            return list(targets)
        return []


class ComposedModule:
    def __init__(
        self,
        name: str,
        atoms: List[AtomicModule],
        composition: Dict[str, Any],
        output_mapping: Dict[str, Any],
        version: int = 1,
    ):
        self.name = name
        self.atoms = atoms
        self.composition = composition
        self.output_mapping = output_mapping
        self.version = version

    def execute(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for atom in self.atoms:
            result[atom.config.name] = atom.execute(kwargs)
        return result

    def adjust(self, **overrides) -> ComposedModule:
        new_atoms = []
        for atom in self.atoms:
            cfg = atom.config
            new_params = dict(cfg.parameters)
            for k, v in overrides.items():
                if k in new_params:
                    new_params[k] = v
            new_config = ModuleConfig(
                name=cfg.name,
                module_type=cfg.module_type,
                sub_type=cfg.sub_type,
                parameters=new_params,
            )
            new_atoms.append(AtomicModule(new_config))
        return ComposedModule(
            name=self.name,
            atoms=new_atoms,
            composition=dict(self.composition),
            output_mapping=dict(self.output_mapping),
            version=self.version + 1,
        )


@dataclass
class ModuleWrapper:
    name: str
    module: Any
    enabled: bool = True


@dataclass
class HotplugDescriptor:
    name: str
    module_type: str
    status: str = "detached"


@dataclass
class HotplugResult:
    success: bool
    message: str = ""


class TriggerCurve:
    def compute_modules(self, complexity: float, axis_count: int) -> int:
        raw = 3 * sigmoid(complexity * axis_count / 6)
        return max(1, min(12, int(round(raw))))

    def compute_delta(self, complexity: float) -> float:
        return min(0.2, 0.15 * sigmoid(complexity - 0.5))

    def compute_trigger_threshold(
        self, actual_rate: float, target_rate: float, current: float
    ) -> float:
        delta = (target_rate - actual_rate) * 0.1
        return max(0.1, min(0.9, current + delta))


class EtaAxisState:
    def __init__(self):
        self.module_registry: Dict[str, ModuleConfig] = {}
        self.active_modules: List[str] = []
        self.execution_count: int = 0
        self.success_rate: float = 1.0
        self.structural_drift: float = 0.0
        # η.drift 觀測來源（three-core plan Phase 2 item 2）：structural_drift
        # 是「模組組成相對啟動基線的變化」的計算值，只在
        # mark_structural_baseline() 之後有意義。沒有基線 → 屬未觀測
        # （structural_drift_observed 為 False），展示端須扣住不顯示（D11）。
        self._structural_baseline: Optional[Tuple[frozenset, frozenset]] = None
        self.module_composition: Dict[str, Any] = field(
            default_factory=lambda: {"total_modules": 0, "axes": []}
        )

    def register_module(self, config: ModuleConfig) -> None:
        self.module_registry[config.name] = config
        if config.name not in self.active_modules:
            self.active_modules.append(config.name)
        self._recompute_structural_drift()

    def unregister_module(self, name: str) -> None:
        self.module_registry.pop(name, None)
        if name in self.active_modules:
            self.active_modules.remove(name)
        self._recompute_structural_drift()

    def activate_module(self, name: str) -> bool:
        if name in self.module_registry and name not in self.active_modules:
            self.active_modules.append(name)
            self._recompute_structural_drift()
            return True
        return name in self.module_registry

    def deactivate_module(self, name: str) -> bool:
        if name in self.active_modules:
            self.active_modules.remove(name)
            self._recompute_structural_drift()
            return True
        return False

    @property
    def structural_drift_observed(self) -> bool:
        """structural_drift 有無比較基線（= 有無觀測）。"""
        return self._structural_baseline is not None

    def mark_structural_baseline(self) -> None:
        """記下當前模組組成作為 η.drift 的比較基線（Phase 2 item 2）。

        three-core plan：`η.drift` 的觀測來源定義為「模組組成的變化」——
        工廠註冊完預設模組後呼叫一次；其後任何 register/unregister/
        activate/deactivate 都會把 ``structural_drift`` 重算成組成相對
        基線的對稱差比例（註冊集＋啟用集，除以聯集，∈ [0,1]）。基線屬本
        進程（不跨重啟持久化——跨重啟的組成回到底線）；``from_dict`` 還原
        的狀態沒有基線 → 未觀測，直到重新標記。
        """
        self._structural_baseline = (
            frozenset(self.module_registry),
            frozenset(self.active_modules),
        )
        self.structural_drift = 0.0

    def _recompute_structural_drift(self) -> None:
        """組成相對基線變了 → 重算 drift；未標基線就不算（D11）。"""
        if self._structural_baseline is None:
            return
        base_registry, base_active = self._structural_baseline
        current_registry = frozenset(self.module_registry)
        current_active = frozenset(self.active_modules)
        union = len(base_registry | current_registry) + len(base_active | current_active)
        if union == 0:
            self.structural_drift = 0.0
            return
        changed = len(base_registry ^ current_registry) + len(base_active ^ current_active)
        self.structural_drift = changed / union

    def execute(self, name: str, kwargs: Dict[str, Any]) -> Any:
        config = self.module_registry.get(name)
        if config is None:
            raise ValueError(f"Module '{name}' not found")
        module = AtomicModule(config)
        result = module.execute(kwargs)
        self.execution_count += 1
        return result

    def execute_active_modules(self, kwargs: Dict[str, Any]) -> List[Tuple[str, Any]]:
        results = []
        for name in self.active_modules:
            config = self.module_registry.get(name)
            if config is not None:
                module = AtomicModule(config)
                result = module.execute(kwargs)
                results.append((name, result))
                self.execution_count += 1
        return results

    def apply_theta_signals(self, signals: Dict[str, float]) -> Dict[str, Any]:
        complexity = signals.get("complexity_delta", 0.5)
        axis_count = len(self.active_modules) or 1
        count = int(round(3 * sigmoid(complexity * axis_count / 6)))
        count = max(1, min(12, count))
        delta = min(0.2, 0.15 * sigmoid(complexity - 0.5))
        return {
            "modules_to_call": count,
            "delta": delta,
            "triggered": count > 0,
            "threshold": 0.5,
        }

    def adjust_parameter(self, name: str, param: str, delta: float) -> None:
        config = self.module_registry.get(name)
        if config is not None:
            current = config.parameters.get(param, 0.0)
            config.parameters[param] = current + delta

    def update_composition(self) -> None:
        self.module_composition = {
            "total_modules": len(self.module_registry),
            "axes": list(self.active_modules),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_registry": {k: v.to_dict() for k, v in self.module_registry.items()},
            "active_modules": list(self.active_modules),
            "execution_count": self.execution_count,
            "success_rate": self.success_rate,
            "structural_drift": self.structural_drift,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EtaAxisState:
        state = cls()
        state.module_registry = {
            k: ModuleConfig.from_dict(v) for k, v in data.get("module_registry", {}).items()
        }
        state.active_modules = list(data.get("active_modules", []))
        state.execution_count = data.get("execution_count", 0)
        state.success_rate = data.get("success_rate", 1.0)
        # 数值照存（round-trip 兼容），但基線不隨狀態還原 —— 舊值描述的是一
        # 次本進程沒有的比較，因此 structural_drift_observed 仍為 False，
        # 展示端扣住，直到 mark_structural_baseline() 重新建立比較點。
        state.structural_drift = data.get("structural_drift", 0.0)
        return state


def create_default_modules() -> Dict[str, ModuleConfig]:
    modules = {}
    configs: List[
        Tuple[
            str,
            AtomicModuleType,
            Union[LogicGateType, ArithmeticOpType, AggregatorType, RouterType],
            Dict[str, Any],
        ]
    ] = [
        ("and_gate", AtomicModuleType.LOGIC_GATE, LogicGateType.AND, {}),
        ("or_gate", AtomicModuleType.LOGIC_GATE, LogicGateType.OR, {}),
        ("not_gate", AtomicModuleType.LOGIC_GATE, LogicGateType.NOT, {}),
        ("xor_gate", AtomicModuleType.LOGIC_GATE, LogicGateType.XOR, {}),
        (
            "threshold_gate",
            AtomicModuleType.LOGIC_GATE,
            LogicGateType.THRESHOLD,
            {"threshold": 0.5, "operator": ">"},
        ),
        ("nand_gate", AtomicModuleType.LOGIC_GATE, LogicGateType.NAND, {}),
        ("nor_gate", AtomicModuleType.LOGIC_GATE, LogicGateType.NOR, {}),
        ("add_op", AtomicModuleType.ARITHMETIC_OP, ArithmeticOpType.ADD, {}),
        ("sub_op", AtomicModuleType.ARITHMETIC_OP, ArithmeticOpType.SUB, {}),
        ("mul_op", AtomicModuleType.ARITHMETIC_OP, ArithmeticOpType.MUL, {}),
        ("div_op", AtomicModuleType.ARITHMETIC_OP, ArithmeticOpType.DIV, {}),
        (
            "custom_expr",
            AtomicModuleType.ARITHMETIC_OP,
            ArithmeticOpType.CUSTOM_EXPR,
            {"expr": "a + b"},
        ),
        ("sum_agg", AtomicModuleType.AGGREGATOR, AggregatorType.SUM, {}),
        ("mean_agg", AtomicModuleType.AGGREGATOR, AggregatorType.MEAN, {}),
        ("max_agg", AtomicModuleType.AGGREGATOR, AggregatorType.MAX, {}),
        ("min_agg", AtomicModuleType.AGGREGATOR, AggregatorType.MIN, {}),
        (
            "weighted_avg",
            AtomicModuleType.AGGREGATOR,
            AggregatorType.WEIGHTED_AVG,
            {"weights": [0.5, 0.3, 0.2]},
        ),
        ("direct_router", AtomicModuleType.ROUTER, RouterType.DIRECT, {"targets": ["alpha"]}),
        (
            "fanout_router",
            AtomicModuleType.ROUTER,
            RouterType.FANOUT,
            {"targets": ["alpha", "beta", "gamma"]},
        ),
        (
            "split_router",
            AtomicModuleType.ROUTER,
            RouterType.SPLIT,
            {"threshold": 0.5, "targets": ["high", "low"]},
        ),
        ("round_robin", AtomicModuleType.ROUTER, RouterType.ROUND_ROBIN, {"targets": ["a", "b"]}),
    ]
    for name, mt, st, params in configs:
        modules[name] = ModuleConfig(name=name, module_type=mt, sub_type=st, parameters=params)
    return modules


def measured_eta_metrics(state: Optional[EtaAxisState]) -> Dict[str, Any]:
    """The η numbers that have actually been observed, for prompt and context.

    ``None`` means "not measured" and is never reported as ``0.0``: a zero is
    read as a measurement, which is how the prompt came to say
    "Structural drift: 0.00" and the dashboard "success=100% drift=0.0000"
    while no module had ever run.

    - ``success_rate`` stays None until ``execution_count`` is above zero —
      production registers the default modules and never executes one, so the
      default 1.0 has no observation behind it.
    - ``structural_drift`` flips with the producer that landed in Phase 2
      item 2: it reports ``state.structural_drift`` only once
      ``structural_drift_observed`` is True (``mark_structural_baseline()``
      established the boot-time composition as the comparison point). A bare
      or restored state has no baseline → None. A marked state's ``0.0`` is
      a real comparison — composition unchanged since boot — and is shown.
    """
    if state is None:
        return {
            "module_count": 0,
            "execution_count": 0,
            "success_rate": None,
            "structural_drift": None,
        }
    observed_drift = (
        round(state.structural_drift, 4)
        if getattr(state, "structural_drift_observed", False)
        else None
    )
    return {
        "module_count": len(state.active_modules),
        "execution_count": state.execution_count,
        "success_rate": round(state.success_rate, 4) if state.execution_count > 0 else None,
        "structural_drift": observed_drift,
    }
