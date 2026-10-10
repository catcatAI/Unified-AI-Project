# ANGELA-MATRIX: [L3] [β] [B] [L2]
"""TaskSplitter: capability split, envelope fit, mount derivation."""

import pytest
from services.task_splitter import TaskSplitter


def test_compound_unity_splits_with_verb_propagation():
    plan = TaskSplitter().split("建車身Cube、車頂、四輪")
    kinds = [p.kind for p in plan.pieces]
    assert kinds.count("micro-act") == 3
    assert kinds[-1] == "verify"
    assert plan.mounts_needed == ["shell", "files"]
    prompts = " ".join(p.prompt for p in plan.pieces)
    assert "建車頂" in prompts and "建四輪" in prompts


def test_single_write_goes_executor_plus_verify():
    plan = TaskSplitter().split("寫一個python函數算總和")
    assert [p.kind for p in plan.pieces] == ["micro-act", "verify"]
    assert plan.pieces[0].capability == "executor"
    assert plan.pieces[1].depends_on == ["p1"]


def test_generic_task_goes_thinker():
    plan = TaskSplitter().split("分析一下系統為什麼慢")
    assert plan.pieces[0].kind == "think"
    assert plan.pieces[0].capability == "thinker"


def test_non_task_stays_whole():
    assert len(TaskSplitter().split("漢堡和可樂").pieces) == 2  # think+verify, no split
    kinds = [p.kind for p in TaskSplitter().split("漢堡和可樂").pieces]
    assert "micro-act" not in kinds


def test_empty_and_brief():
    plan = TaskSplitter().split("")
    assert plan.pieces == []
    plan2 = TaskSplitter().split("寫腳本", context={"decisions": ["用batch模式"]})
    assert "batch模式" in plan2.brief
    assert "無前言" in plan2.pieces[0].prompt


def test_ready_pieces_respect_dependencies():
    plan = TaskSplitter().split("建車身Cube、建車頂Cube")
    assert {p.piece_id for p in plan.ready_pieces(set())} == {"p1", "p2"}
    assert {p.piece_id for p in plan.ready_pieces({"p1", "p2"})} == {"p1", "p2", "verify"}


def test_preset_loader_reads_pack_and_falls_back():
    from services.preset_loader import framing_for, kind_params, load_preset

    assert load_preset("no-such-preset") == {}
    micro = framing_for("micro_act")
    assert "code_shape" in micro and "{part}" in micro["code_shape"]
    think_params = kind_params("think")
    assert think_params.get("slot") == "thinker"
    assert kind_params("nope") == {}


def test_bare_build_without_code_context_stays_whole():
    """建車身、建車頂 (no code nouns) is not a code task — stays think+verify."""
    kinds = [p.kind for p in TaskSplitter().split("建車身、建車頂").pieces]
    assert "micro-act" not in kinds


@pytest.mark.asyncio
async def test_runner_dispatches_by_kind_in_order():
    from services.task_splitter import SplitRunner, TaskSplitter

    plan = TaskSplitter().split("建車身Cube、建車頂Cube")
    calls = []

    async def act_fn(prompt):
        calls.append(("act", prompt[:20]))
        return "code-piece"

    async def verify_fn(prompt, results):
        calls.append(("verify", sorted(results)))
        return "通過" if len(results) == 2 else "缺件"

    out = await SplitRunner().run(plan, act_fn=act_fn, verify_fn=verify_fn)
    assert out["ok"] is True
    assert set(out["results"]) == {"p1", "p2", "verify"}
    assert calls[0][0] == "act" and calls[-1][0] == "verify"
    assert "code-piece" in out["results"]["p1"]


@pytest.mark.asyncio
async def test_runner_records_failure_and_continues():
    from services.task_splitter import SplitRunner, TaskSplitter

    async def boom(prompt):
        raise RuntimeError("down")

    plan = TaskSplitter().split("寫一個python函數算總和")
    out = await SplitRunner().run(plan, act_fn=boom)
    assert "[failed:p1" in out["results"]["p1"]
    assert out["results"]["verify"].startswith("[skipped")
