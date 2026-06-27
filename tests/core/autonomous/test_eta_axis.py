"""
Smoke tests for η (Eta) Axis — Execution/Operation Layer.

Covers:
  - EtaAxisState instantiation and property defaults
  - Module registration / unregistration
  - Module execution (LogicGate, ArithmeticOp, Aggregator, Router)
  - Default module factory
  - Trigger curve computation
  - Serialization round-trip
"""

import pytest


@pytest.fixture
def eta():
    """Fresh EtaAxisState for each test."""
    from core.engine.eta_axis import EtaAxisState

    return EtaAxisState()


class TestInitialState:
    """Default state values after construction."""

    def test_module_registry_empty(self, eta):
        assert eta.module_registry == {}

    def test_active_modules_empty(self, eta):
        assert eta.active_modules == []

    def test_execution_count_zero(self, eta):
        assert eta.execution_count == 0

    def test_success_rate_one(self, eta):
        assert eta.success_rate == 1.0

    def test_structural_drift_zero(self, eta):
        assert eta.structural_drift == 0.0


class TestModuleRegistration:
    """Register, unregister, activate, deactivate modules."""

    def test_register_adds_to_registry_and_active(self, eta):
        from core.engine.eta_axis import (
            AtomicModuleType,
            LogicGateType,
            ModuleConfig,
        )

        config = ModuleConfig(
            name="test_and",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={},
        )
        eta.register_module(config)
        assert "test_and" in eta.module_registry
        assert "test_and" in eta.active_modules

    def test_unregister_removes_from_both(self, eta):
        from core.engine.eta_axis import (
            AtomicModuleType,
            LogicGateType,
            ModuleConfig,
        )

        config = ModuleConfig(
            name="test_and",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={},
        )
        eta.register_module(config)
        eta.unregister_module("test_and")
        assert "test_and" not in eta.module_registry
        assert "test_and" not in eta.active_modules

    def test_activate_and_deactivate(self, eta):
        from core.engine.eta_axis import (
            AtomicModuleType,
            LogicGateType,
            ModuleConfig,
        )

        config = ModuleConfig(
            name="test_mod",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={},
        )
        eta.register_module(config)
        assert eta.deactivate_module("test_mod") is True
        assert "test_mod" not in eta.active_modules
        assert eta.activate_module("test_mod") is True
        assert "test_mod" in eta.active_modules


class TestModuleExecution:
    """Execute atomic modules of each type."""

    def test_logic_gate_and(self, eta):
        from core.engine.eta_axis import (
            AtomicModuleType,
            LogicGateType,
            ModuleConfig,
        )

        eta.register_module(ModuleConfig(
            name="and_gate",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={},
        ))
        assert eta.execute("and_gate", {"values": [1, 2, 3]}) is True
        assert eta.execute("and_gate", {"values": [0, 1, 2]}) is False

    def test_arithmetic_add(self, eta):
        from core.engine.eta_axis import (
            ArithmeticOpType,
            AtomicModuleType,
            ModuleConfig,
        )

        eta.register_module(ModuleConfig(
            name="add_op",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.ADD,
            parameters={},
        ))
        assert eta.execute("add_op", {"values": [1.0, 2.0, 3.0]}) == 6.0

    def test_aggregator_mean(self, eta):
        from core.engine.eta_axis import (
            AggregatorType,
            AtomicModuleType,
            ModuleConfig,
        )

        eta.register_module(ModuleConfig(
            name="mean_agg",
            module_type=AtomicModuleType.AGGREGATOR,
            sub_type=AggregatorType.MEAN,
            parameters={},
        ))
        assert eta.execute("mean_agg", {"values": [2.0, 4.0, 6.0]}) == 4.0

    def test_router_direct(self, eta):
        from core.engine.eta_axis import (
            AtomicModuleType,
            ModuleConfig,
            RouterType,
        )

        eta.register_module(ModuleConfig(
            name="direct_router",
            module_type=AtomicModuleType.ROUTER,
            sub_type=RouterType.DIRECT,
            parameters={"targets": ["alpha"]},
        ))
        assert eta.execute("direct_router", {}) == ["alpha"]


class TestDefaultModules:
    """Factory function creates the standard module set."""

    def test_create_default_modules_returns_all_types(self):
        from core.engine.eta_axis import AtomicModuleType, create_default_modules

        modules = create_default_modules()
        assert len(modules) > 0

        types_found = set()
        for cfg in modules.values():
            types_found.add(cfg.module_type)
        assert AtomicModuleType.LOGIC_GATE in types_found
        assert AtomicModuleType.ARITHMETIC_OP in types_found
        assert AtomicModuleType.AGGREGATOR in types_found
        assert AtomicModuleType.ROUTER in types_found

    def test_default_modules_can_be_registered(self, eta):
        from core.engine.eta_axis import create_default_modules

        for name, config in create_default_modules().items():
            eta.register_module(config)

        assert len(eta.module_registry) >= 21  # known default count


class TestTriggerCurve:
    """Sigmoid-based trigger curve logic."""

    def test_compute_modules_basic(self):
        from core.engine.eta_axis import TriggerCurve

        tc = TriggerCurve()
        count = tc.compute_modules(complexity=0.5, axis_count=6)
        assert 1 <= count <= 12

    def test_compute_delta_basic(self):
        from core.engine.eta_axis import TriggerCurve

        tc = TriggerCurve()
        delta = tc.compute_delta(complexity=0.5)
        assert 0.0 <= delta <= 0.2

    def test_compute_trigger_threshold(self):
        from core.engine.eta_axis import TriggerCurve

        tc = TriggerCurve()
        new_th = tc.compute_trigger_threshold(
            actual_rate=0.5, target_rate=0.3, current=0.5
        )
        assert 0.1 <= new_th <= 0.9


class TestSerialization:
    """to_dict / from_dict round-trip."""

    def test_roundtrip_preserves_state(self, eta):
        from core.engine.eta_axis import EtaAxisState, create_default_modules

        for name, config in create_default_modules().items():
            eta.register_module(config)

        eta.execution_count = 42
        eta.success_rate = 0.85
        eta.structural_drift = 0.1

        data = eta.to_dict()
        restored = EtaAxisState.from_dict(data)

        assert restored.execution_count == 42
        assert restored.success_rate == 0.85
        assert restored.structural_drift == 0.1
        assert len(restored.module_registry) == len(eta.module_registry)
        assert restored.active_modules == eta.active_modules
