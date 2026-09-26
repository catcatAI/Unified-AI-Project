"""
The three previously-unreachable specialized agents, end to end.

WHY this file exists
--------------------
fantasy_dm_agent, web_search_agent and vision_processing_agent were registered
and fully implemented, but no intent mapped to them, so no chat message could
select them and the capability catalog reported them as not dispatchable. Adding
the intents was only half the job: the router hands every agent the raw user
message under generic keys (message/query/prompt/text), while these three classes
take domain parameters (`setting`, `url`, `image_path`). The first end-to-end run
therefore reached fantasy_dm_agent and got back "No setting provided" — reachable
and useless at the same time.

So these tests pin three separate things, because all three broke independently:
1. the intent is recognised, and existing intents are not stolen;
2. the gate has a verdict for the new intents (no entry = silent reject);
3. the agent actually produces a result, through the real adapter.

ANGELA-MATRIX: [L3] [α] [A] [L4]
"""

import asyncio
from pathlib import Path

import pytest
from ai.agents.agent_orchestrator import (
    _INTENT_AGENTS,
    AgentOrchestrator,
    dispatchable_agent_ids,
)
from ai.agents.specialized.fantasy_dm_agent import FantasyDMAgent
from ai.agents.specialized.vision_processing_agent import VisionProcessingAgent
from ai.agents.specialized.web_search_agent import WebSearchAgent

NEW_AGENTS = ("fantasy_dm_agent", "web_search_agent", "vision_processing_agent")


@pytest.fixture(scope="module")
def orchestrator():
    return AgentOrchestrator()


@pytest.fixture(scope="module")
def agent_manager():
    from ai.agents.agent_adapter import register_specialized_agents
    from ai.agents.agent_manager import AgentManager

    manager = AgentManager(enable_process_agents=False, enable_router=False)
    assert register_specialized_agents(manager) >= 11
    return manager


def _route(message, agent_manager):
    orch = AgentOrchestrator(agent_manager=agent_manager)
    result = asyncio.run(orch.route_task(message, {"conversation_path": "http"}))
    return (result.get("results") or [{}])[0]


def _inner(primary):
    return primary["result"]["result"]


# --------------------------------------------------------------------------- #
# 1. classification
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "message",
    [
        "幫我跑一個跑團，設定是黑暗森林，等級3",
        "我要玩 D&D，幫我創一個角色：精靈法師",
        "start a D&D campaign in a haunted keep",
        "roll initiative, the rogue attacks the dragon",
        "幫我建立一個 TRPG 角色卡",
    ],
)
def test_roleplay_is_recognised(orchestrator, message):
    assert orchestrator.classify_intent(message) == "roleplay"


@pytest.mark.parametrize(
    "message",
    [
        "請問 https://example.com 這個網址的內容講什麼？",
        "scrape this page and summarize it",
        "抓取這個網頁的內容",
        "fetch the url please",
    ],
)
def test_web_research_is_recognised(orchestrator, message):
    assert orchestrator.classify_intent(message) == "web_research"


@pytest.mark.parametrize(
    "message",
    [
        "這張圖片裡的文字是什麼？",
        "ocr 這張照片",
        "照片裡有什麼東西？",
        "extract text from the image /tmp/shot.png",
    ],
)
def test_image_detail_is_recognised(orchestrator, message):
    assert orchestrator.classify_intent(message) == "image_detail"


@pytest.mark.parametrize(
    "message,expected",
    [
        # The three new branches sit before the generic ones, so each of these
        # used to be the answer and must stay that way.
        ("幫我寫一首詩", "creative_write"),
        ("寫一個關於春天的故事", "creative_write"),
        ("搜尋 python 3.13 的新功能", "web_search"),
        ("google 一下 electron 的版本", "web_search"),
        ("分析這張圖片", "vision"),
        ("描述這張圖片", "vision"),
        ("幫我規劃下週的行程", "plan_create"),
        ("讀取 /tmp/a.txt", "file_read"),
        ("刪除這個檔案", "file_delete"),
        ("執行這段程式碼", "code_execute"),
        ("解釋這段 python 程式碼", "code_understand"),
        ("查詢知識圖譜", "knowledge_query"),
        ("分析數據", "data_analysis"),
        ("轉錄這段音訊", "audio"),
        ("情緒分析", "nlp"),
    ],
)
def test_new_intents_do_not_steal_existing_traffic(orchestrator, message, expected):
    assert orchestrator.classify_intent(message) == expected


def test_plain_photo_request_still_falls_through_to_the_llm(orchestrator):
    """Pre-existing gap, pinned rather than silently changed.

    「照片」 is absent from the vision pattern (which lists 圖片/影像), so a plain
    「看看這張照片」 classifies as `general` and is answered by the LLM. Adding it
    would be a one-word fix, but it moves benchmark routing (angela_bench holds a
    95% routing floor), so it is recorded here instead of bundled into this
    change. The new image_detail branch deliberately claims only the phrasings it
    can actually serve — OCR and object listing.
    """
    assert orchestrator.classify_intent("看看這張照片") == "general"


def test_latin_roleplay_keywords_are_lowercase_in_the_pattern(orchestrator):
    """`classify_intent` matches against an already-lowercased string.

    The pattern was first written with 「TRPG」/「\\bRPG\\b」/「\\bDM\\b」, which can
    never match, so every Latin roleplay request fell through to the LLM.
    """
    assert orchestrator.classify_intent("start an rpg campaign") == "roleplay"
    assert orchestrator.classify_intent("be our dm for tonight") == "roleplay"


# --------------------------------------------------------------------------- #
# 2. dispatch table + gate verdict
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "intent,agent",
    [
        ("roleplay", "fantasy_dm_agent"),
        ("web_research", "web_search_agent"),
        ("image_detail", "vision_processing_agent"),
    ],
)
def test_intent_maps_to_agent(intent, agent):
    assert _INTENT_AGENTS[intent] == agent
    assert agent in dispatchable_agent_ids()


@pytest.mark.parametrize("intent", ["roleplay", "web_research", "image_detail"])
def test_gate_has_a_verdict_for_every_new_intent(intent):
    """An intent with no action class is rejected before reaching its agent."""
    from ai.core.execution_gate import _AGENT_INTENT_ACTIONS

    assert (
        intent in _AGENT_INTENT_ACTIONS
    ), f"{intent} would be silently rejected: ExecutionGate has no action class"


def test_every_agent_intent_has_a_gate_verdict():
    """Guards the whole table, including intents added later."""
    from ai.core.execution_gate import _AGENT_INTENT_ACTIONS

    missing = sorted(set(_INTENT_AGENTS) - set(_AGENT_INTENT_ACTIONS))
    assert not missing, f"intents with no ExecutionGate action class: {missing}"


def test_capability_catalog_marks_them_dispatchable(agent_manager, monkeypatch):
    """The catalog reads the lifespan singleton, so register into it as startup does."""
    import api.lifespan as lifespan
    from services.llm.capability_catalog import build_capability_snapshot

    monkeypatch.setattr(lifespan, "get_agent_manager", lambda: agent_manager)
    snapshot = build_capability_snapshot()
    by_id = {entry["id"]: entry for entry in snapshot["agents"]}
    for agent in NEW_AGENTS:
        assert agent in by_id, f"{agent} is not even registered in the catalog"
        assert by_id[agent]["dispatchable"] is True, f"{agent} is still unreachable"


# --------------------------------------------------------------------------- #
# 3. the agents actually run (real classes, real adapter, no mocks)
# --------------------------------------------------------------------------- #
def test_roleplay_produces_a_scenario(agent_manager):
    primary = _route("幫我跑一個跑團，設定是黑暗森林，等級3", agent_manager)
    assert primary["agent"] == "fantasy_dm_agent"
    assert primary["intent"] == "roleplay"
    inner = _inner(primary)
    assert inner["status"] == "success"
    assert inner["setting"] == "黑暗森林"
    assert inner["player_level"] == 3
    assert inner["difficulty"] == "medium"


def test_roleplay_builds_a_character_sheet(agent_manager):
    primary = _route("我要玩 D&D，幫我創一個角色：精靈法師", agent_manager)
    inner = _inner(primary)
    assert inner["status"] == "success"
    assert inner["character_class"] == "mage"
    assert inner["race"] == "elf"
    # the mage bonus must actually land in the stat block
    assert inner["stats"]["intelligence"] == 13
    assert inner["stats"]["wisdom"] == 11


def test_image_detail_reports_a_missing_file_instead_of_pretending(agent_manager, tmp_path):
    """Honest failure matters more than a fabricated analysis."""
    primary = _route(f"ocr {tmp_path / 'definitely-not-here.png'}", agent_manager)
    assert primary["agent"] == "vision_processing_agent"
    inner = _inner(primary)
    assert inner["status"] == "error"
    assert "not found" in inner["message"].lower()


def test_image_detail_opens_the_real_file(agent_manager, tmp_path):
    """The named file must reach the pipeline, and the result must be honest.

    Object detection needs torchvision/YOLO and OCR needs pytesseract, so the deep
    result depends on the environment. What must hold everywhere: the real agent is
    selected, the extracted path is the file the user named, and a missing model is
    reported as `unavailable` with the reason — never as a fabricated analysis.
    """
    pytest.importorskip("PIL")
    from PIL import Image

    path = tmp_path / "solid.png"
    Image.new("RGB", (8, 8), (10, 120, 200)).save(path)

    seen = {}
    original = VisionProcessingAgent.detect_objects

    def spy(self, image_path):
        seen["path"] = image_path
        seen["exists"] = Path(image_path).is_file()
        return original(self, image_path)

    VisionProcessingAgent.detect_objects = spy
    try:
        primary = _route(f"這張圖片裡有什麼？ {path}", agent_manager)
    finally:
        VisionProcessingAgent.detect_objects = original

    assert primary["agent"] == "vision_processing_agent"
    assert seen["path"] == str(path)
    assert seen["exists"] is True

    inner = _inner(primary)
    assert inner["status"] in {"success", "unavailable"}, inner
    if inner["status"] == "unavailable":
        assert inner["message"], "an unavailable result must say what is missing"


def test_ocr_phrasing_selects_text_extraction(agent_manager, tmp_path, monkeypatch):
    """「裡的文字」 must choose extract_text, not object detection."""
    calls = []
    monkeypatch.setattr(
        VisionProcessingAgent,
        "extract_text",
        lambda self, p: calls.append(("ocr", p)) or {"status": "ok"},
    )
    monkeypatch.setattr(
        VisionProcessingAgent,
        "detect_objects",
        lambda self, p: calls.append(("objects", p)) or {"status": "ok"},
    )
    _route(f"這張圖片裡的文字是什麼？ {tmp_path / 'x.png'}", agent_manager)
    assert [kind for kind, _ in calls] == ["ocr"]


def test_listing_phrasing_selects_object_detection(agent_manager, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(
        VisionProcessingAgent,
        "extract_text",
        lambda self, p: calls.append("ocr") or {"status": "ok"},
    )
    monkeypatch.setattr(
        VisionProcessingAgent,
        "detect_objects",
        lambda self, p: calls.append("objects") or {"status": "ok"},
    )
    _route(f"照片裡有什麼東西？ {tmp_path / 'y.png'}", agent_manager)
    assert calls == ["objects"]


def test_web_research_fetches_the_named_url(agent_manager, monkeypatch):
    """The URL branch is exercised without touching the network."""
    seen = {}

    def fake_fetch(self, url):
        seen["url"] = url
        return {"status": "success", "message": f"Fetched {url}", "content_summary": "hi"}

    monkeypatch.setattr(WebSearchAgent, "fetch_content", fake_fetch)
    primary = _route("請問 https://example.com 這個網址講什麼？", agent_manager)
    assert primary["agent"] == "web_search_agent"
    assert seen["url"] == "https://example.com"
    assert _inner(primary)["status"] == "success"


def test_web_research_searches_when_no_url_is_given(agent_manager, monkeypatch):
    """web_research claims fetch-flavoured phrasing; a bare URL-less request searches."""
    seen = {}

    def fake_search(self, query, num_results=5):
        seen["query"] = query
        return {"status": "success", "message": "searched", "results": []}

    monkeypatch.setattr(WebSearchAgent, "search", fake_search)
    primary = _route("抓取這個網頁的內容，關於 electron", agent_manager)
    assert primary["agent"] == "web_search_agent"
    assert "electron" in seen["query"]


# --------------------------------------------------------------------------- #
# 4. argument adapters themselves
# --------------------------------------------------------------------------- #
def test_vision_and_handler_agree_on_image_paths():
    """The agent duplicates VisionHandler's path conventions; pin the fork.

    Two copies of the same regex will drift. This asserts they currently agree on
    all three conventions, so a change to one has to be made in the other.
    """
    from services.handlers.vision_handler import VisionHandler

    agent = VisionProcessingAgent()
    handler = VisionHandler()
    for text in (
        "`/tmp/a.png`",
        "look at /tmp/nested/dir/b.jpg please",
        "```\n/tmp/c.gif\n```",
    ):
        assert agent.extract_image_path(text) == handler._extract_image_path(text), text


def test_vision_extracts_nothing_when_there_is_no_path():
    result = VisionProcessingAgent().handle_request("這張圖片裡有什麼？")
    assert result["status"] == "error"
    assert "no image path" in result["message"].lower()


@pytest.mark.parametrize(
    "text,expected",
    [
        ("請問 https://example.com 這個網址講什麼？", "https://example.com"),
        ("see http://a.b/c?d=1 for details", "http://a.b/c?d=1"),
        ("no url here", None),
    ],
)
def test_web_agent_url_extraction(text, expected):
    assert WebSearchAgent().extract_url(text) == expected


@pytest.mark.parametrize(
    "text,setting,level",
    [
        ("設定是黑暗森林，等級3", "黑暗森林", 3),
        ("setting is 火星殖民地 level 7", "火星殖民地", 7),
        ("場景：海底古城", "海底古城", 1),
    ],
)
def test_fantasy_setting_and_level_parsing(text, setting, level):
    result = FantasyDMAgent().handle_request(text)
    assert result["setting"] == setting
    assert result["player_level"] == level


def test_fantasy_level_is_clamped_to_the_dice_range():
    agent = FantasyDMAgent()
    assert agent.handle_request("設定是 x，等級 999")["player_level"] == 20
    assert agent.handle_request("設定是 x，等級 0")["player_level"] == 1
