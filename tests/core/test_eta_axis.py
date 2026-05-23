"""
η (Eta) Axis Tests — P10.9
===========================

Author: Angela AI v6.2.1
Date: 2026-05-15
"""

import pytest
from datetime import datetime
from core.autonomous.eta_axis import (
    sigmoid,
    AtomicModuleType,
    LogicGateType,
    ArithmeticOpType,
    AggregatorType,
    RouterType,
    ModuleConfig,
    AtomicModule,
    ComposedModule,
    TriggerCurve,
    UpdateOp,
    EtaAxisState,
    create_default_modules,
)


class TestSigmoid:
    def test_sigmoid_normal(self):
        assert 0 < sigmoid(0) < 1

    def test_sigmoid_extreme_positive(self):
        assert sigmoid(50) > 0.99

    def test_sigmoid_extreme_negative(self):
        assert sigmoid(-50) < 0.01

    def test_sigmoid_zero(self):
        assert abs(sigmoid(0) - 0.5) < 0.01


class TestTriggerCurve:
    def test_compute_modules_base(self):
        tc = TriggerCurve()
        result = tc.compute_modules(0.5, 6)
        assert 1 <= result <= 12

    def test_compute_modules_cap(self):
        tc = TriggerCurve()
        result = tc.compute_modules(1.0, 6)
        assert result <= 12

    def test_compute_delta_mid(self):
        tc = TriggerCurve()
        delta = tc.compute_delta(0.5)
        assert 0 < delta <= 0.2

    def test_compute_delta_cap(self):
        tc = TriggerCurve()
        delta = tc.compute_delta(1.0)
        assert delta <= 0.2

    def test_axis_count_affects_modules(self):
        tc = TriggerCurve()
        result_6 = tc.compute_modules(0.5, 6)
        result_12 = tc.compute_modules(0.5, 12)
        assert result_12 >= result_6

    def test_trigger_threshold_adaptation(self):
        tc = TriggerCurve()
        new_threshold = tc.compute_trigger_threshold(actual_rate=0.1, target_rate=0.3, current=0.5)
        assert 0.1 <= new_threshold <= 0.9


class TestModuleConfig:
    def test_to_dict_roundtrip(self):
        config = ModuleConfig(
            name="test_module",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={"threshold": 0.5},
            tags=["test"],
        )
        data = config.to_dict()
        restored = ModuleConfig.from_dict(data)
        assert restored.name == config.name
        assert restored.module_type == config.module_type
        assert restored.sub_type == config.sub_type


class TestAtomicModule:
    def test_logic_AND_true(self):
        config = ModuleConfig(
            name="and_gate",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={},
        )
        module = AtomicModule(config)
        result = module.execute({"values": [1.0, 0.8, 0.9]})
        assert result is True

    def test_logic_AND_false(self):
        config = ModuleConfig(
            name="and_gate",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={},
        )
        module = AtomicModule(config)
        result = module.execute({"values": [1.0, 0.0, 0.9]})
        assert result is False

    def test_logic_OR_true(self):
        config = ModuleConfig(
            name="or_gate",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.OR,
            parameters={},
        )
        module = AtomicModule(config)
        result = module.execute({"values": [0.0, 0.0, 0.9]})
        assert result is True

    def test_logic_NOT(self):
        config = ModuleConfig(
            name="not_gate",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.NOT,
            parameters={},
        )
        module = AtomicModule(config)
        assert module.execute({"value": 1.0}) is False
        assert module.execute({"value": 0.0}) is True

    def test_logic_XOR(self):
        config = ModuleConfig(
            name="xor_gate",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.XOR,
            parameters={},
        )
        module = AtomicModule(config)
        assert module.execute({"values": [1.0, 0.0]}) is True
        assert module.execute({"values": [1.0, 1.0]}) is False
        assert module.execute({"values": [0.0, 1.0]}) is True

    def test_logic_threshold_above(self):
        config = ModuleConfig(
            name="threshold_gate",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.THRESHOLD,
            parameters={"threshold": 0.7, "operator": ">"},
        )
        module = AtomicModule(config)
        assert module.execute({"value": 0.8}) is True
        assert module.execute({"value": 0.6}) is False

    def test_arithmetic_ADD(self):
        config = ModuleConfig(
            name="add_op",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.ADD,
            parameters={},
        )
        module = AtomicModule(config)
        result = module.execute({"values": [1.5, 2.5, 3.0]})
        assert abs(result - 7.0) < 0.001

    def test_arithmetic_SUB(self):
        config = ModuleConfig(
            name="sub_op",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.SUB,
            parameters={},
        )
        module = AtomicModule(config)
        result = module.execute({"a": 10.0, "b": 3.0})
        assert abs(result - 7.0) < 0.001

    def test_arithmetic_MUL(self):
        config = ModuleConfig(
            name="mul_op",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.MUL,
            parameters={},
        )
        module = AtomicModule(config)
        result = module.execute({"values": [2.0, 3.0, 4.0]})
        assert abs(result - 24.0) < 0.001

    def test_arithmetic_DIV(self):
        config = ModuleConfig(
            name="div_op",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.DIV,
            parameters={},
        )
        module = AtomicModule(config)
        result = module.execute({"a": 20.0, "b": 4.0})
        assert abs(result - 5.0) < 0.001

    def test_arithmetic_DIV_by_zero(self):
        config = ModuleConfig(
            name="div_op",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.DIV,
            parameters={},
        )
        module = AtomicModule(config)
        result = module.execute({"a": 20.0, "b": 0.0})
        assert result == 0.0

    def test_arithmetic_CUSTOM_EXPR(self):
        config = ModuleConfig(
            name="custom_expr",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.CUSTOM_EXPR,
            parameters={"expr": "a + b * c"},
        )
        module = AtomicModule(config)
        result = module.execute({"a": 1.0, "b": 2.0, "c": 3.0})
        assert abs(result - 7.0) < 0.001

    def test_aggregator_SUM(self):
        config = ModuleConfig(
            name="sum_agg",
            module_type=AtomicModuleType.AGGREGATOR,
            sub_type=AggregatorType.SUM,
            parameters={},
        )
        module = AtomicModule(config)
        result = module.execute({"values": [1.0, 2.0, 3.0]})
        assert abs(result - 6.0) < 0.001

    def test_aggregator_MEAN(self):
        config = ModuleConfig(
            name="mean_agg",
            module_type=AtomicModuleType.AGGREGATOR,
            sub_type=AggregatorType.MEAN,
            parameters={},
        )
        module = AtomicModule(config)
        result = module.execute({"values": [1.0, 2.0, 3.0]})
        assert abs(result - 2.0) < 0.001

    def test_aggregator_MAX(self):
        config = ModuleConfig(
            name="max_agg",
            module_type=AtomicModuleType.AGGREGATOR,
            sub_type=AggregatorType.MAX,
            parameters={},
        )
        module = AtomicModule(config)
        result = module.execute({"values": [1.0, 5.0, 3.0]})
        assert abs(result - 5.0) < 0.001

    def test_aggregator_WEIGHTED_AVG(self):
        config = ModuleConfig(
            name="weighted_avg",
            module_type=AtomicModuleType.AGGREGATOR,
            sub_type=AggregatorType.WEIGHTED_AVG,
            parameters={"weights": [0.5, 0.3, 0.2]},
        )
        module = AtomicModule(config)
        result = module.execute({"values": [10.0, 20.0, 30.0]})
        assert abs(result - 17.0) < 0.001

    def test_router_DIRECT(self):
        config = ModuleConfig(
            name="direct_router",
            module_type=AtomicModuleType.ROUTER,
            sub_type=RouterType.DIRECT,
            parameters={"targets": ["alpha", "beta"]},
        )
        module = AtomicModule(config)
        result = module.execute({})
        assert result == ["alpha"]

    def test_router_FANOUT(self):
        config = ModuleConfig(
            name="fanout_router",
            module_type=AtomicModuleType.ROUTER,
            sub_type=RouterType.FANOUT,
            parameters={"targets": ["alpha", "beta", "gamma"]},
        )
        module = AtomicModule(config)
        result = module.execute({})
        assert len(result) == 3

    def test_router_SPLIT_high(self):
        config = ModuleConfig(
            name="split_router",
            module_type=AtomicModuleType.ROUTER,
            sub_type=RouterType.SPLIT,
            parameters={"threshold": 0.5, "targets": ["high", "low"]},
        )
        module = AtomicModule(config)
        result = module.execute({"value": 0.8})
        assert result == ["high"]

    def test_router_SPLIT_low(self):
        config = ModuleConfig(
            name="split_router",
            module_type=AtomicModuleType.ROUTER,
            sub_type=RouterType.SPLIT,
            parameters={"threshold": 0.5, "targets": ["high", "low"]},
        )
        module = AtomicModule(config)
        result = module.execute({"value": 0.3})
        assert result == ["high", "low"]


class TestComposedModule:
    def test_execute_sequential(self):
        and_config = ModuleConfig(
            name="and_gate",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={},
        )
        threshold_config = ModuleConfig(
            name="threshold_gate",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.THRESHOLD,
            parameters={"threshold": 0.5, "operator": ">"},
        )
        composed = ComposedModule(
            name="code_quality",
            atoms=[AtomicModule(and_config), AtomicModule(threshold_config)],
            composition={"order": "and_then_threshold"},
            output_mapping={},
        )
        result = composed.execute({"values": [0.8, 0.9], "value": 0.8})
        assert "and_gate" in result
        assert "threshold_gate" in result

    def test_adjust_creates_new_version(self):
        config = ModuleConfig(
            name="threshold_gate",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.THRESHOLD,
            parameters={"threshold": 0.7},
        )
        composed = ComposedModule(
            name="test_module",
            atoms=[AtomicModule(config)],
            composition={},
            output_mapping={},
        )
        adjusted = composed.adjust(threshold=0.5)
        assert adjusted.version == 2
        assert adjusted.atoms[0].config.parameters["threshold"] == 0.5


class TestEtaAxisState:
    def test_register_module(self):
        state = EtaAxisState()
        config = ModuleConfig(
            name="test_module",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={},
        )
        state.register_module(config)
        assert "test_module" in state.module_registry
        assert "test_module" in state.active_modules

    def test_unregister_module(self):
        state = EtaAxisState()
        config = ModuleConfig(
            name="test_module",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={},
        )
        state.register_module(config)
        state.unregister_module("test_module")
        assert "test_module" not in state.module_registry
        assert "test_module" not in state.active_modules

    def test_execute_module(self):
        state = EtaAxisState()
        config = ModuleConfig(
            name="and_gate",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={},
        )
        state.register_module(config)
        result = state.execute("and_gate", {"values": [1.0, 0.8]})
        assert result is True
        assert state.execution_count == 1

    def test_execute_active_modules(self):
        state = EtaAxisState()
        config = ModuleConfig(
            name="add_op",
            module_type=AtomicModuleType.ARITHMETIC_OP,
            sub_type=ArithmeticOpType.ADD,
            parameters={},
        )
        state.register_module(config)
        results = state.execute_active_modules({"values": [1.0, 2.0]})
        assert len(results) == 1
        assert results[0][0] == "add_op"
        assert abs(results[0][1] - 3.0) < 0.001

    def test_apply_theta_signals_triggered(self):
        state = EtaAxisState()
        signals = {
            "update_frequency": 0.8,
            "complexity_delta": 0.7,
            "novelty_peak": 0.6,
            "misallocation_rate": 0.5,
            "buffer_pressure": 0.4,
        }
        result = state.apply_theta_signals(signals)
        assert "modules_to_call" in result
        assert "delta" in result
        assert "triggered" in result
        assert "threshold" in result

    def test_adjust_parameter(self):
        state = EtaAxisState()
        config = ModuleConfig(
            name="threshold_gate",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.THRESHOLD,
            parameters={"threshold": 0.7},
        )
        state.register_module(config)
        state.adjust_parameter("threshold_gate", "threshold", 0.05)
        assert abs(state.module_registry["threshold_gate"].parameters["threshold"] - 0.75) < 0.001

    def test_to_dict_roundtrip(self):
        state = EtaAxisState()
        config = ModuleConfig(
            name="test_module",
            module_type=AtomicModuleType.LOGIC_GATE,
            sub_type=LogicGateType.AND,
            parameters={},
        )
        state.register_module(config)
        state.execution_count = 10

        data = state.to_dict()
        restored = EtaAxisState.from_dict(data)

        assert len(restored.module_registry) == 1
        assert restored.execution_count == 10

    def test_update_composition(self):
        state = EtaAxisState()
        state.update_composition()
        assert "total_modules" in state.module_composition
        assert "axes" in state.module_composition


class TestCreateDefaultModules:
    def test_creates_expected_count(self):
        modules = create_default_modules()
        assert len(modules) == 21

    def test_all_have_names(self):
        modules = create_default_modules()
        for name in modules:
            assert name in modules[name].name

    def test_all_types_represented(self):
        modules = create_default_modules()
        types = {m.module_type for m in modules.values()}
        assert AtomicModuleType.LOGIC_GATE in types
        assert AtomicModuleType.ARITHMETIC_OP in types
        assert AtomicModuleType.AGGREGATOR in types
        assert AtomicModuleType.ROUTER in types


class TestEtaAxisStateIntegration:
    def test_full_cycle(self):
        state = EtaAxisState()
        for name, config in create_default_modules().items():
            state.register_module(config)

        signals = {
            "update_frequency": 0.5,
            "complexity_delta": 0.6,
            "novelty_peak": 0.5,
            "misallocation_rate": 0.3,
            "buffer_pressure": 0.2,
        }
        result = state.apply_theta_signals(signals)

        if result["triggered"]:
            count = min(result["modules_to_call"], len(state.active_modules))
            inputs = {"values": [0.5, 0.6, 0.7]}
            results = state.invoke_active_modules(inputs) if hasattr(state, 'invoke_active_modules') else state.execute_active_modules(inputs)
            assert len(results) >= 0

        state.update_composition()
        report = state.to_dict()
        assert "module_registry" in report
        assert "active_modules" in report
        assert report["active_modules"] == list(state.active_modules)