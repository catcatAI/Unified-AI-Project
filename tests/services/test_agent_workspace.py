"""代理工作區測試：樹狀上下文雙視圖＋會話閉環＋確認門＋學習日誌。

涵蓋：
- ContextTree：全貌唯讀／預算截斷／子節點摺疊／執行器分層與指令白名單
- AppSessionManager：open→read→act→save→close 狀態機、確認門、學習日誌
- AgentWorkspace：樹隨會話狀態刷新
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from services.agent_workspace.agent import AgentWorkspace
from services.agent_workspace.app_session import (
    AppAdapter,
    AppSessionManager,
    ActionSpec,
)
from services.agent_workspace.context_tree import ContextNode, ContextTree
from services.agent_workspace.global_tree import (
    GlobalContextProviders,
    GlobalContextTree,
    UnifiedWorkspace,
)


class FakeAdapter(AppAdapter):
    """假應用：一個安全指令＋一個危險指令。"""

    app_id = "fake"
    label = "假應用"

    def __init__(self) -> None:
        super().__init__()
        self.register(ActionSpec("poke", "安全指令"), self._poke)
        self.register(ActionSpec("nuke", "危險指令", dangerous=True), self._nuke)

    async def _poke(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": True, "poked": True}

    async def _nuke(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return {"ok": True, "nuked": True}


def _make_manager(tmp_path: Path) -> AppSessionManager:
    return AppSessionManager(
        adapters={"fake": FakeAdapter()},
        log_path=tmp_path / "learning_log.jsonl",
    )


# ---------- ContextTree ----------


def _sample_tree() -> ContextTree:
    leaf_a = ContextNode(id="a1", label="節點A1", kind="item", summary="摘要A1")
    leaf_b = ContextNode(
        id="b1", label="節點B1", kind="item", commands=["poke"], readonly=False
    )
    group = ContextNode(id="grp", label="群組", kind="app", children=[leaf_a, leaf_b])
    root = ContextNode(id="root", label="根", kind="workspace", children=[group])
    return ContextTree(root=root, view_budget=4000, children_limit=12)


def test_overview_is_readonly_and_flags_nodes() -> None:
    view = _sample_tree().overview()
    assert view["readonly"] is True
    assert "🔒" in view["text"]  # 唯讀節點旗標
    assert "🔧" in view["text"]  # 有指令的節點旗標


def test_overview_collapses_extra_children() -> None:
    kids = [ContextNode(id=f"k{i}", label=f"子{i}", kind="item") for i in range(15)]
    root = ContextNode(id="root", label="根", kind="workspace", children=kids)
    view = ContextTree(root=root, children_limit=10).overview()
    assert "…還有 5 個子節點" in view["text"]
    assert view["truncated"] is True


def test_overview_respects_budget() -> None:
    kids = [
        ContextNode(id=f"k{i}", label=f"子節點{i}", kind="item", summary="x" * 60)
        for i in range(50)
    ]
    root = ContextNode(id="root", label="根", kind="workspace", children=kids)
    view = ContextTree(root=root, view_budget=800, children_limit=50).overview()
    assert len(view["text"]) <= 900
    assert "超過上下文預算" in view["text"]


def test_focus_shows_path_and_whitelist() -> None:
    view = _sample_tree().focus("b1")
    assert view["view"] == "focus"
    assert view["commands"] == ["poke"]
    assert "根[root]" in view["text"] and "節點B1[b1]" in view["text"]


def test_focus_readonly_layer_has_no_commands() -> None:
    view = _sample_tree().focus("a1")
    assert view["commands"] == []
    assert "唯讀層" in view["text"]


def test_focus_unknown_node_returns_error() -> None:
    view = _sample_tree().focus("nope")
    assert "error" in view


# ---------- AppSessionManager 生命週期 ----------


@pytest.mark.asyncio
async def test_full_lifecycle_open_act_save_close(tmp_path: Path) -> None:
    mgr = _make_manager(tmp_path)
    opened = await mgr.open_app("fake", purpose="教學演示")
    assert opened["ok"] is True
    assert opened["commands"] == ["poke", "nuke"]

    acted = await mgr.act("fake", "poke")
    assert acted["ok"] is True
    assert acted["session"]["dirty"] is True

    saved = await mgr.save_app("fake")
    assert saved["ok"] is True
    assert saved["session"]["dirty"] is False

    closed = await mgr.close_app("fake")
    assert closed["ok"] is True
    assert mgr.get_session("fake") is None


@pytest.mark.asyncio
async def test_open_unknown_and_duplicate_app(tmp_path: Path) -> None:
    mgr = _make_manager(tmp_path)
    assert (await mgr.open_app("ghost"))["ok"] is False
    assert (await mgr.open_app("fake"))["ok"] is True
    assert (await mgr.open_app("fake"))["ok"] is False


@pytest.mark.asyncio
async def test_act_requires_open_session_and_whitelist(tmp_path: Path) -> None:
    mgr = _make_manager(tmp_path)
    assert (await mgr.act("fake", "poke"))["ok"] is False  # 未開啟
    await mgr.open_app("fake")
    result = await mgr.act("fake", "hack")
    assert result["ok"] is False
    assert "白名單" in result["error"] or "無指令" in result["error"]


@pytest.mark.asyncio
async def test_confirm_gate_blocks_dangerous_action(tmp_path: Path) -> None:
    mgr = _make_manager(tmp_path)
    await mgr.open_app("fake")
    first = await mgr.act("fake", "nuke")
    assert first["status"] == "pending_confirmation"
    assert first["confirm_required"] is True
    second = await mgr.act("fake", "nuke", confirm=True)
    assert second["ok"] is True


@pytest.mark.asyncio
async def test_close_with_dirty_requires_confirm(tmp_path: Path) -> None:
    mgr = _make_manager(tmp_path)
    await mgr.open_app("fake")
    await mgr.act("fake", "poke")
    blocked = await mgr.close_app("fake")
    assert blocked["status"] == "pending_confirmation"
    assert mgr.get_session("fake") is not None  # 仍在
    saved = await mgr.save_app("fake")
    assert saved["ok"] is True
    closed = await mgr.close_app("fake")
    assert closed["ok"] is True


# ---------- 學習日誌 ----------


@pytest.mark.asyncio
async def test_learning_log_records_teaching_and_failures(tmp_path: Path) -> None:
    mgr = _make_manager(tmp_path)
    await mgr.open_app("fake", purpose="教學", source="teaching")
    await mgr.act("fake", "hack")  # 白名單外 → 失敗也是學習資料
    await mgr.act("fake", "poke", source="exploration")  # 自主探索
    entries = mgr.learning_tail()
    actions = [e["action"] for e in entries]
    assert "open" in actions
    assert "act:hack" in actions
    assert "act:poke" in actions
    outcomes = {e["action"]: e["outcome"] for e in entries}
    assert outcomes["open"] == "ok"
    assert outcomes["act:hack"] == "failed"
    by_source = {e["action"]: e["source"] for e in entries}
    assert by_source["act:poke"] == "exploration"
    assert (tmp_path / "learning_log.jsonl").exists()


@pytest.mark.asyncio
async def test_learning_tail_empty_when_no_log(tmp_path: Path) -> None:
    mgr = _make_manager(tmp_path)
    assert mgr.learning_tail() == []


# ---------- AgentWorkspace 整合 ----------


def _make_workspace(tmp_path: Path) -> AgentWorkspace:
    return AgentWorkspace(session_manager=_make_manager(tmp_path))


@pytest.mark.asyncio
async def test_workspace_overview_reflects_sessions(tmp_path: Path) -> None:
    ws = _make_workspace(tmp_path)
    before = ws.overview()
    assert "假應用" in before["text"]
    assert "會話" not in before["text"]
    await ws.open_app("fake")
    after = ws.overview()
    assert "會話" in after["text"]


@pytest.mark.asyncio
async def test_workspace_focus_session_shows_full_whitelist(tmp_path: Path) -> None:
    ws = _make_workspace(tmp_path)
    await ws.open_app("fake")
    app_view = ws.focus("app:fake")
    assert app_view["commands"] == ["open"]  # 未開啟的應用層只有 open
    session_view = ws.focus("session:fake")
    assert session_view["commands"] == ["poke", "nuke", "save", "close"]


@pytest.mark.asyncio
async def test_workspace_act_updates_tree_dirty_state(tmp_path: Path) -> None:
    ws = _make_workspace(tmp_path)
    await ws.open_app("fake")
    result = await ws.act("fake", "poke")
    assert result["ok"] is True
    overview_text = ws.overview()["text"]
    assert "dirty" in overview_text


# ---------- 全域上下文樹（五類上下文統一治理） ----------


class _StubMem:
    def __init__(self, content: str, memory_type: str) -> None:
        self.content = content
        self.memory_type = memory_type


class _StubConv:
    def __init__(self, messages: int, key_points: int) -> None:
        self.messages = [object()] * messages
        self.context_summary = type("S", (), {"key_points": ["p"] * key_points})()


class _StubTool:
    def __init__(self, name: str) -> None:
        self.name = name


def _global_providers(tmp_path: Path) -> GlobalContextProviders:
    ws = _make_workspace(tmp_path)
    tm = type("TM", (), {})()
    tm.categories = {"cat1": type("C", (), {"name": "程式工具", "tools": []})()}
    tm.tools = {"t1": _StubTool("程式產生器")}
    mm = type("MM", (), {})()
    mm.memories = {
        "m1": _StubMem("使用者喜歡繁體中文", "short_term"),
        "m2": _StubMem("專案採 monorepo 架構", "long_term"),
    }
    dm = type("DM", (), {})()
    dm.conversations = {"conv_001": _StubConv(messages=12, key_points=3)}
    return GlobalContextProviders(
        tool_manager=tm,
        memory_manager=mm,
        dialogue_manager=dm,
        workspace=ws,
    )


def test_global_overview_covers_all_context_kinds(tmp_path: Path) -> None:
    tree = GlobalContextTree(providers=_global_providers(tmp_path))
    view = tree.overview()
    assert view["readonly"] is True
    text = view["text"]
    assert "AI 系統上下文" in text
    assert "工具上下文" in text
    assert "記憶上下文" in text
    assert "對話上下文" in text
    assert "應用程式" in text  # 代理工作區會話掛同一棵樹


def test_global_overview_absent_sections_degrade(tmp_path: Path) -> None:
    providers = GlobalContextProviders(workspace=_make_workspace(tmp_path))
    tree = GlobalContextTree(providers=providers)
    text = tree.overview()["text"]
    assert "工具上下文" not in text
    assert "應用程式" in text


def test_global_focus_dialogue_layer(tmp_path: Path) -> None:
    tree = GlobalContextTree(providers=_global_providers(tmp_path))
    view = tree.focus("ctx:dialogue")
    assert "對話 conv_001" in view["text"]
    conv_view = tree.focus("ctx:conv:conv_001")
    assert "12 則訊息" in conv_view["text"]


def test_global_search_across_contexts(tmp_path: Path) -> None:
    tree = GlobalContextTree(providers=_global_providers(tmp_path))
    result = tree.search("繁體中文")
    assert result["ok"] is True
    types = {r["type"] for r in result["results"]}
    assert "memory" in types
    tool_result = tree.search("程式")
    assert any(r["type"] == "tool" for r in tool_result["results"])


def test_unified_facade_delegates(tmp_path: Path) -> None:
    providers = _global_providers(tmp_path)
    unified = UnifiedWorkspace(providers.workspace, GlobalContextTree(providers=providers))
    assert "AI 系統上下文" in unified.overview()["text"]
    assert unified.search("繁體中文")["ok"] is True


@pytest.mark.asyncio
async def test_unified_facade_session_loop(tmp_path: Path) -> None:
    providers = _global_providers(tmp_path)
    unified = UnifiedWorkspace(providers.workspace, GlobalContextTree(providers=providers))
    opened = await unified.open_app("fake")
    assert opened["ok"] is True
    # 開啟會話後，全域樹也看得到（同一份狀態）
    assert "會話" in unified.overview()["text"]
    assert (await unified.act("fake", "nuke"))["status"] == "pending_confirmation"
    assert (await unified.save_app("fake"))["ok"] is True
    assert (await unified.close_app("fake"))["ok"] is True
