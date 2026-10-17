# -*- coding: utf-8 -*-
"""萬物皆軸引擎 M1 測試（計畫 §6.3 M1 驗收）。

- AxisSpec/AxisGroup/SignalSpec/GroupContract 建構即驗證（非法 raise）
- 契約缺訊號 startup 即 raise MissingSignalError
- 空間(space)+戰鬥(combat) 兩群組：組間訊號下一 tick 可見、同 tick 不可見
- emit 型別/精度契約強制；註冊序/重名/啟動後禁註冊
"""

from __future__ import annotations

import pytest
from engine import (
    AxisGroup,
    AxisSpec,
    ContractError,
    EnginePipeline,
    Entity,
    GroupContract,
    MissingSignalError,
    SignalSpec,
    TickContext,
)

# ---------------------------------------------------------------------------
# 共用夾具：空間 + 戰鬥兩群組（§6.3 M1）
# ---------------------------------------------------------------------------


def make_space(requires=()) -> AxisGroup:
    return AxisGroup(
        name="space",
        tick_rate=30.0,
        axes={
            "pos_x": AxisSpec("pos_x", "continuous", lo=-1000.0, hi=1000.0),
            "pos_y": AxisSpec("pos_y", "continuous", lo=-1000.0, hi=1000.0),
        },
        contract=GroupContract(
            group="space",
            provides=(
                SignalSpec("pos_x"),
                SignalSpec("pos_y"),
                SignalSpec("in_combat", "bool", 0),
            ),
            requires=tuple(requires),
        ),
    )


def make_combat(requires=("space.pos_x",)) -> AxisGroup:
    return AxisGroup(
        name="combat",
        tick_rate=60.0,
        axes={
            "hp": AxisSpec("hp", "discrete", lo=0.0, hi=999.0, step=1.0),
            "phase": AxisSpec("phase", "fsm", states=("idle", "fight", "flee")),
        },
        contract=GroupContract(
            group="combat",
            provides=(
                SignalSpec("damage"),
                SignalSpec("target_hp", "int", 0),
                SignalSpec("phase", "str", 0),
            ),
            requires=tuple(requires),
        ),
    )


def build_pair(combat_requires=("space.pos_x",), space_hook=None, combat_hook=None):
    """註冊 space/combat；hook(ctx) 缺省時 space 每 tick emit pos_x=7.5。"""
    pipe = EnginePipeline()

    def space_handler(ctx: TickContext) -> None:
        if space_hook is not None:
            space_hook(ctx)
        else:
            ctx.emit("pos_x", 7.5)

    def combat_handler(ctx: TickContext) -> None:
        if combat_hook is not None:
            combat_hook(ctx)

    pipe.register_group(make_space(), space_handler)
    pipe.register_group(make_combat(combat_requires), combat_handler)
    return pipe


# ---------------------------------------------------------------------------
# AxisSpec / AxisGroup / Entity
# ---------------------------------------------------------------------------


class TestAxisSpec:
    def test_continuous_with_range_ok(self):
        spec = AxisSpec("x", "continuous", lo=-1.0, hi=1.0)
        assert spec.contains(0.5) and not spec.contains(2.0)

    def test_discrete_requires_positive_step(self):
        with pytest.raises(ValueError):
            AxisSpec("n", "discrete", step=0.0)
        assert AxisSpec("n", "discrete", step=0.25).step == 0.25

    def test_fsm_requires_states(self):
        with pytest.raises(ValueError):
            AxisSpec("phase", "fsm")
        spec = AxisSpec("phase", "fsm", states=("a", "b"))
        assert spec.contains("a") and not spec.contains("c")

    def test_states_rejected_on_non_fsm(self):
        with pytest.raises(ValueError):
            AxisSpec("x", "continuous", states=("a",))

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"name": "", "kind": "continuous"},
            {"name": "x", "kind": "nope"},
            {"name": "x", "kind": "continuous", "step": -1.0},
            {"name": "x", "kind": "continuous", "lo": 5.0, "hi": 1.0},
        ],
    )
    def test_invalid_specs_raise(self, kwargs):
        with pytest.raises(ValueError):
            AxisSpec(**kwargs)

    def test_contains_rejects_non_number_on_numeric_axis(self):
        spec = AxisSpec("x", "continuous")
        assert not spec.contains("abc") and not spec.contains(True)


class TestAxisGroupEntity:
    def test_tick_rate_must_be_positive(self):
        with pytest.raises(ValueError):
            AxisGroup(
                name="g",
                tick_rate=0.0,
                axes={"a": AxisSpec("a", "continuous")},
                contract=GroupContract(group="g"),
            )

    def test_empty_axes_raise(self):
        with pytest.raises(ValueError):
            AxisGroup(name="g", tick_rate=1.0, axes={}, contract=GroupContract(group="g"))

    def test_axes_key_spec_name_mismatch_raises(self):
        with pytest.raises(ValueError):
            AxisGroup(
                name="g",
                tick_rate=1.0,
                axes={"wrong": AxisSpec("a", "continuous")},
                contract=GroupContract(group="g"),
            )

    def test_contract_group_mismatch_raises(self):
        with pytest.raises(ValueError):
            AxisGroup(
                name="g",
                tick_rate=1.0,
                axes={"a": AxisSpec("a", "continuous")},
                contract=GroupContract(group="other"),
            )

    def test_entity_defaults(self):
        e = Entity(eid=1)
        assert e.groups == {} and e.parent is None and e.local_offset is None


# ---------------------------------------------------------------------------
# SignalSpec / GroupContract
# ---------------------------------------------------------------------------


class TestSignalSpec:
    @pytest.mark.parametrize(
        "kwargs",
        [
            {"name": ""},
            {"name": "a.b"},
            {"name": "x", "dtype": "nope"},
            {"name": "x", "precision": -1},
            {"name": "x", "dtype": "int", "precision": 2},
            {"name": "x", "dtype": "str", "precision": 1},
        ],
    )
    def test_invalid_signal_raises(self, kwargs):
        with pytest.raises(ContractError):
            SignalSpec(**kwargs)

    def test_float_coerce_rounds_to_precision(self):
        assert SignalSpec("f", "float", 3).coerce(1.23456) == 1.235

    def test_float_coerce_rejects_bool_and_str(self):
        spec = SignalSpec("f", "float", 3)
        with pytest.raises(ContractError):
            spec.coerce(True)
        with pytest.raises(ContractError):
            spec.coerce("1.0")

    def test_int_coerce_rejects_float_and_bool(self):
        spec = SignalSpec("n", "int", 0)
        assert spec.coerce(7) == 7
        with pytest.raises(ContractError):
            spec.coerce(1.5)
        with pytest.raises(ContractError):
            spec.coerce(True)

    def test_bool_and_str_coerce(self):
        assert SignalSpec("b", "bool", 0).coerce(True) is True
        assert SignalSpec("s", "str", 0).coerce("ok") == "ok"
        with pytest.raises(ContractError):
            SignalSpec("s", "str", 0).coerce(5)


class TestGroupContract:
    def test_duplicate_provides_raise(self):
        with pytest.raises(ContractError):
            GroupContract(group="g", provides=(SignalSpec("a"), SignalSpec("a")))

    @pytest.mark.parametrize("ref", ["pos", "group.", ".sig", "a.b.c"])
    def test_requires_must_be_group_signal(self, ref):
        with pytest.raises(ContractError):
            GroupContract(group="g", requires=(ref,))

    def test_provide_names_and_spec_of(self):
        c = GroupContract(group="g", provides=(SignalSpec("a"), SignalSpec("b", "int", 0)))
        assert c.provide_names() == ("a", "b")
        assert c.spec_of("b").dtype == "int"
        with pytest.raises(ContractError):
            c.spec_of("missing")


# ---------------------------------------------------------------------------
# EnginePipeline — M1 驗收
# ---------------------------------------------------------------------------


class TestStartupContractValidation:
    def test_missing_signal_raises_at_startup(self):
        # M1 驗收：契約缺訊號啟動即 raise（combat 依賴 space.hp，space 未提供）
        pipe = EnginePipeline()
        pipe.register_group(make_space(), lambda ctx: None)
        pipe.register_group(make_combat(requires=("space.hp",)), lambda ctx: None)
        with pytest.raises(MissingSignalError, match="does not provide signal 'hp'"):
            pipe.startup()
        assert not pipe.started

    def test_requires_unregistered_group_raises(self):
        pipe = EnginePipeline()
        pipe.register_group(make_space(requires=("mind.focus",)), lambda ctx: None)
        with pytest.raises(MissingSignalError, match="not registered"):
            pipe.startup()

    def test_duplicate_group_register_raises(self):
        pipe = EnginePipeline()
        pipe.register_group(make_space(), lambda ctx: None)
        with pytest.raises(ContractError, match="already registered"):
            pipe.register_group(make_space(), lambda ctx: None)

    def test_startup_idempotent(self):
        pipe = build_pair()
        pipe.startup()
        pipe.startup()
        assert pipe.started and pipe.group_names() == ["space", "combat"]

    def test_register_after_startup_raises(self):
        pipe = build_pair()
        pipe.startup()
        with pytest.raises(ContractError):
            pipe.register_group(make_space(), lambda ctx: None)


class TestNextTickVisibility:
    def test_cross_group_signal_visible_next_tick(self):
        # M1 驗收：組間訊號下一 tick 可見
        seen = []
        pipe = build_pair(combat_hook=lambda ctx: seen.append(ctx.read("space.pos_x", None)))
        pipe.startup()

        pipe.tick()
        assert seen == [None]  # 同 tick 內（首輪）尚不可見
        assert pipe.signal("space.pos_x") == 7.5

        pipe.tick()
        assert seen == [None, 7.5]  # 下一 tick 可見
        assert pipe.ticks == 2

    def test_own_group_emit_not_readable_same_tick(self):
        reads = []
        pipe = EnginePipeline()

        def handler(ctx: TickContext) -> None:
            ctx.emit("pos_x", 1.0)
            reads.append(ctx.read("space.pos_x", None))

        pipe.register_group(make_space(), handler)
        pipe.startup()
        pipe.tick()
        assert reads == [None]  # 同 tick 寫入不可自讀
        pipe.tick()
        assert reads == [None, 1.0]

    def test_tick_before_startup_raises(self):
        pipe = build_pair()
        with pytest.raises(ContractError, match="not started"):
            pipe.tick()


class TestEmitContracts:
    def test_emit_signal_not_in_contract_raises(self):
        pipe = build_pair()
        pipe.startup()
        with pytest.raises(ContractError, match="does not provide signal"):
            EnginePipeline._emit(pipe, "space", "nope", 1.0)

    def test_emit_wrong_dtype_raises(self):
        errors = []

        def space_hook(ctx: TickContext) -> None:
            try:
                ctx.emit("pos_x", "not-a-number")
            except ContractError as exc:
                errors.append(exc)
                ctx.emit("pos_x", 7.5)

        pipe = build_pair(space_hook=space_hook)
        pipe.startup()
        pipe.tick()
        assert errors and "expects float" in str(errors[0])
        assert pipe.signal("space.pos_x") == 7.5

    def test_emit_float_precision_applied(self):
        got = []

        def space_hook(ctx: TickContext) -> None:
            ctx.emit("pos_x", 1.23456)
            got.append(ctx.read("space.pos_x", None))

        pipe = build_pair(space_hook=space_hook)
        pipe.startup()
        pipe.tick()
        pipe.tick()
        assert got[-1] == 1.235  # 上一 tick 快照已按 precision 捨入

    def test_read_bad_ref_format_raises(self):
        pipe = build_pair()
        pipe.startup()
        with pytest.raises(ContractError, match="group.signal"):
            pipe.signal("nodot")

    def test_contract_of_unknown_group_raises(self):
        pipe = build_pair()
        with pytest.raises(ContractError, match="unknown group"):
            pipe.contract_of("mind")
