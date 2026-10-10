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
from services.agent_workspace.agent import AgentWorkspace, EdaWorkspaceAdapter
from services.agent_workspace.app_session import (
    ActionSpec,
    AppAdapter,
    AppSessionManager,
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


class FakeEdaAgent:
    agent_id = "eda_agent"
    capabilities = [{"name": "ai_card_reference", "version": "0.1.0"}]

    def get_status(self) -> Dict[str, Any]:
        return {"enabled": True, "learning_episodes": {"coordinator_wired": True}}

    async def probe_tools(self, **_: Any) -> Dict[str, Any]:
        return {"status": "ok", "tools": {"ngspice": {"available": True}}}

    async def run_ai_card_reference_experiment(self) -> Dict[str, Any]:
        return {"status": "reference_verified_acceptance_check_pending"}

    def get_ai_card_interface_packet(self) -> Dict[str, Any]:
        return {
            "ok": True,
            "packet": {
                "status": "decision_verification_pending",
                "pending_decisions": [{"id": "die_l1_interface"}],
            },
        }

    def get_hardware_standards(self, query: str = "") -> Dict[str, Any]:
        return {"status": "ok", "query": query, "count": 1, "standards": []}


def _make_manager(tmp_path: Path) -> AppSessionManager:
    return AppSessionManager(
        adapters={"fake": FakeAdapter()},
        log_path=tmp_path / "learning_log.jsonl",
    )


# ---------- ContextTree ----------


def _sample_tree() -> ContextTree:
    leaf_a = ContextNode(id="a1", label="節點A1", kind="item", summary="摘要A1")
    leaf_b = ContextNode(id="b1", label="節點B1", kind="item", commands=["poke"], readonly=False)
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


@pytest.mark.asyncio
async def test_eda_adapter_resolves_existing_agent_lazily(tmp_path: Path) -> None:
    state: Dict[str, Any] = {"agent": None}
    ws = AgentWorkspace(
        session_manager=AppSessionManager(
            adapters={"eda": EdaWorkspaceAdapter(lambda: state["agent"])},
            log_path=tmp_path / "learning_log.jsonl",
        )
    )

    unavailable = await ws.read_app("eda")
    assert unavailable["ok"] is False

    state["agent"] = FakeEdaAgent()
    opened = await ws.open_app("eda", purpose="AI 計算卡 reference")
    assert opened["commands"] == [
        "probe_tools",
        "run_ai_card_reference",
        "read_interface_packet",
        "search_hardware_standards",
    ]

    state_result = await ws.read_app("eda")
    assert state_result["ok"] is True
    assert state_result["state"]["agent_id"] == "eda_agent"

    result = await ws.act("eda", "run_ai_card_reference")
    assert result["ok"] is True
    assert result["result"]["result"]["status"].startswith("reference_verified")

    packet_result = await ws.act("eda", "read_interface_packet")
    assert packet_result["ok"] is True
    assert packet_result["result"]["result"]["packet"]["status"] == (
        "decision_verification_pending"
    )

    standards_result = await ws.act("eda", "search_hardware_standards", {"query": "AXI"})
    assert standards_result["ok"] is True
    assert standards_result["result"]["result"]["query"] == "AXI"


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


class _StubAgentAdapter:
    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_status": {"enabled": True},
            "available_methods": ["probe_tools", "run_ai_card_reference_experiment"],
        }


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


def test_global_overview_exposes_registered_eda_agent() -> None:
    agent_manager = type("AgentManager", (), {})()
    agent_manager.agents = {"eda_agent": _StubAgentAdapter()}
    agent_manager.collaborations = {}
    tree = GlobalContextTree(providers=GlobalContextProviders(agent_manager=agent_manager))

    overview = tree.overview()
    assert "代理 eda_agent" in overview["text"]
    focused = tree.focus("ctx:agent:eda_agent")
    assert focused["node_id"] == "ctx:agent:eda_agent"
    assert "run_ai_card_reference_experiment" in focused["text"]


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


def test_facade_without_providers_still_shows_apps(tmp_path: Path) -> None:
    """回歸：lifespan 組裝方式 UnifiedWorkspace(ws, GlobalContextTree())
    下，樹必須仍能看到應用會話分支（否則 focus('apps') 404）。"""
    unified = UnifiedWorkspace(
        _make_workspace(tmp_path), GlobalContextTree()  # 樹無 providers 注入
    )
    view = unified.focus("apps")
    assert view.get("error") is None
    assert "應用程式" in view["text"]
    assert "假應用" in view["text"]


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


# ---------- 上下文體積治理（100 行上限＋內容採樣） ----------


def test_overview_never_exceeds_100_lines() -> None:
    # 200 個子節點、放寬 children_limit，強迫原始輸出遠超 100 行
    kids = [
        ContextNode(id=f"k{i}", label=f"子節點{i}", kind="item", summary="短摘要")
        for i in range(200)
    ]
    root = ContextNode(id="root", label="根", kind="workspace", children=kids)
    view = ContextTree(root=root, children_limit=300).overview()
    assert view["lines"] <= 102  # 上限＋標記行
    assert "行上限" in view["text"]
    assert view["truncated"] is True


def test_focus_memory_group_shows_content_preview(tmp_path: Path) -> None:
    tree = GlobalContextTree(providers=_global_providers(tmp_path))
    view = tree.focus("ctx:memory:short_term")
    assert "內容採樣" in view["text"]
    assert "使用者喜歡繁體中文" in view["text"]


def test_view_reports_line_count(tmp_path: Path) -> None:
    tree = GlobalContextTree(providers=_global_providers(tmp_path))
    ov = tree.overview()
    assert ov["lines"] == len(ov["text"].splitlines())
    assert ov["lines"] <= 100


# ---------- 動態掛載（主 AI 按需掛應用） ----------


def _make_mount_manager(tmp_path: Path) -> AppSessionManager:
    return AppSessionManager(
        adapters={"fake": FakeAdapter()},
        log_path=tmp_path / "learning_log.jsonl",
        protected_ids={"fake"},
    )


async def test_mount_and_unmount_lifecycle(tmp_path: Path) -> None:
    from services.agent_workspace.agent import FilesAdapter, ShellAdapter

    mgr = _make_mount_manager(tmp_path)
    assert [a["app_id"] for a in mgr.available_apps()] == ["fake"]
    r = mgr.mount_adapter(ShellAdapter(), source="test")
    assert r["ok"] is True and r["app_id"] == "shell"
    assert r["commands"] == ["run"]
    # 重複掛載拒絕（活會話 adapter 不可被替換）
    dup = mgr.mount_adapter(ShellAdapter(), source="test")
    assert dup["ok"] is False
    # 非 adapter 拒絕
    assert mgr.mount_adapter(object(), source="test")["ok"] is False  # type: ignore[arg-type]
    # 開啟中會話擋卸載
    await mgr.open_app("shell")
    assert mgr.unmount_adapter("shell")["ok"] is False
    await mgr.close_app("shell", confirm=True)
    assert mgr.unmount_adapter("shell")["ok"] is True
    # 內建受保護
    assert mgr.unmount_adapter("fake")["ok"] is False
    # 未知應用
    assert mgr.unmount_adapter("ghost")["ok"] is False
    assert mgr.mount_adapter(FilesAdapter(), source="test")["ok"] is True


async def test_files_adapter_jail_and_roundtrip(tmp_path: Path) -> None:
    from services.agent_workspace.agent import FilesAdapter

    mgr = _make_mount_manager(tmp_path)
    mgr.mount_adapter(FilesAdapter(), source="test")
    await mgr.open_app("files")
    target = tmp_path / "note.txt"
    w = await mgr.act("files", "write", {"path": str(target), "content": "hi"}, confirm=True)
    assert w["ok"] is True
    # 危險寫入需確認
    assert (await mgr.act("files", "write", {"path": str(target), "content": "x"}))["ok"] is False
    r = await mgr.act("files", "read", {"path": str(target)})
    assert r["result"]["content"] == "hi"
    # 越界拒絕（讀 /etc 不得成功）
    bad = await mgr.act("files", "read", {"path": "/etc/hostname"})
    assert bad["ok"] is False or bad["result"].get("ok") is False
    # 白名單外拒絕
    assert (await mgr.act("files", "delete", {}))["ok"] is False


async def test_shell_adapter_run_and_deny(tmp_path: Path) -> None:
    from services.agent_workspace.agent import ShellAdapter

    mgr = _make_mount_manager(tmp_path)
    mgr.mount_adapter(ShellAdapter(workdir=str(tmp_path)), source="test")
    await mgr.open_app("shell")
    # 未確認不執行
    assert (await mgr.act("shell", "run", {"cmd": "echo hi"}))["ok"] is False
    ok = await mgr.act("shell", "run", {"cmd": "echo hi"}, confirm=True)
    assert ok["ok"] is True
    assert "hi" in ok["result"]["stdout"]
    # 拒絕明顯破壞性指令（adapter 層拒絕，原樣回傳）
    deny = await mgr.act("shell", "run", {"cmd": "rm -rf / tmp"}, confirm=True)
    assert deny["ok"] is False
    assert "拒絕" in deny.get("error", "")
    # cwd 越界拒絕（失敗原樣回傳，無 result 包裝）
    jail = await mgr.act("shell", "run", {"cmd": "echo hi", "cwd": "/proc"}, confirm=True)
    assert jail["ok"] is False
    assert "越界" in jail.get("error", "")
    # 缺省工作目錄不存在時回落進程 cwd（.env ANGELA_WORKSPACE=./workspace 未建）
    from services.agent_workspace.agent import ShellAdapter as _Shell

    mgr2 = _make_mount_manager(tmp_path)
    mgr2.mount_adapter(_Shell(workdir=str(tmp_path / "no-such-dir")), source="test")
    await mgr2.open_app("shell")
    fb = await mgr2.act("shell", "run", {"cmd": "echo fallback-ok"}, confirm=True)
    assert fb["ok"] is True
    assert "fallback-ok" in fb["result"]["stdout"]
    # 顯式 cwd 不存在則明確報錯
    missing = await mgr2.act(
        "shell", "run", {"cmd": "echo hi", "cwd": "/tmp/no-such-dir-xyz"}, confirm=True
    )
    assert missing["ok"] is False
    assert "不存在" in missing.get("error", "")


async def test_workspace_mount_rebuilds_tree(tmp_path: Path) -> None:
    ws = AgentWorkspace(session_manager=_make_mount_manager(tmp_path))
    assert "shell" not in [a["app_id"] for a in ws.sessions.available_apps()]
    assert ws.mount_app("shell")["ok"] is True
    assert "shell" in [a["app_id"] for a in ws.sessions.available_apps()]
    assert ws.mount_app("not-a-kind")["ok"] is False
    assert ws.unmount_app("shell")["ok"] is True


async def test_mount_handler_parse_and_list() -> None:
    from services.handlers.workspace_mount_handler import WorkspaceMountHandler

    h = WorkspaceMountHandler()
    assert h._parse_action("把shell掛上") == ("mount", "shell")
    assert h._parse_action("掛載文件") == ("mount", "文件")
    assert h._parse_action("卸載shell") == ("unmount", "shell")
    assert h._parse_action("有哪些應用") == ("list", "")
    assert h._parse_action("代理狀態如何") == ("inspect", "")
    assert h._parse_action("會話開著嗎") == ("inspect", "")
    assert h._parse_action("系統狀態如何") is None
    assert h._parse_action("配置文件在哪") is None
    assert h._parse_action("怎麼掛載shell") is None
    assert h._parse_action("不要卸載shell") is None
    assert h._parse_action("把shell掛上嗎") == ("mount", "shell")
    assert h._parse_action("配置一個Unity代理") == ("configure", "Unity")
    assert h._parse_action("組裝chip代理") == ("configure", "chip")
    assert h._parse_action("你好") is None


def test_suggest_modules_maps_tasks() -> None:
    from services.agent_workspace.modules import suggest_modules

    assert "shell-unity" in suggest_modules("用Unity建模小車")
    assert "files-ro" in suggest_modules("看看chip目錄")
    assert suggest_modules("你好") == []


async def test_compose_agent_puzzle_assembly(tmp_path: Path) -> None:
    from services.agent_workspace.agent import AgentWorkspace
    from services.agent_workspace.modules import compose_agent

    adapter = compose_agent("unity-dev", ["shell-unity", "files-rw"], "Unity開發")
    assert adapter.app_id == "unity-dev"
    assert {s.name for s in adapter.specs()} == {"run", "list", "read", "write"}
    ws = AgentWorkspace(session_manager=_make_mount_manager(tmp_path))
    assert ws.sessions.mount_adapter(adapter, source="test")["ok"] is True
    await ws.open_app("unity-dev")
    # collision / unknown rejected
    with pytest.raises(ValueError):
        compose_agent("x", ["shell-exec", "shell-unity"])
    with pytest.raises(ValueError):
        compose_agent("x", ["nope"])


async def test_workspace_compose_mounts_and_runs(tmp_path: Path) -> None:
    ws = AgentWorkspace(session_manager=_make_mount_manager(tmp_path))
    result = ws.compose_app("chip-reader", ["files-ro"], "chip隻讀")
    assert result["ok"] is True
    assert result["modules"] == ["files-ro"]
    await ws.open_app("chip-reader")
    # read-only: no write action registered
    assert (await ws.act("chip-reader", "write", {}, confirm=True))["ok"] is False
    state = await ws.read_app("chip-reader")
    assert state["ok"] is True


async def test_mount_handler_inspect_reports_sessions(tmp_path: Path) -> None:
    from services.handlers.workspace_mount_handler import WorkspaceMountHandler

    h = WorkspaceMountHandler()
    ws = _make_workspace(tmp_path)
    text = h._inspect(ws)
    assert "可用應用" in text and "fake" in text and "未開啟" in text
    await ws.open_app("fake")
    text2 = h._inspect(ws)
    assert "開啟中" in text2


def test_mount_intent_detected_with_verb_bypass() -> None:
    """長句掛載請求：動詞繞過密度門檻（learning 0.18 案同構）。"""
    from core.intent_registry import IntentRegistry

    name, conf = IntentRegistry().detect(
        "請幫我把shell終端掛載到代理上好嗎謝謝", category="app_mount"
    )
    assert name == "app_mount"

    from ai.core.execution_gate import ExecutionGate

    decision = ExecutionGate(model_bus=None).decide_agent_execution(
        intent="app_mount", agent_name="workspace", user_message="掛載shell"
    )
    assert decision.action in ("auto_execute", "confirm_then_execute")
