"""Turn observation: structure only, off by default, and no conversation in the log.

WHY: the AL state-channel question (docs/06-project-management/
HIERARCHICAL_PLAN_FILL_GENERATION.md §6.1) needs (state, answer-structure) pairs
and the repository has none. The writer must therefore (a) do nothing unless
explicitly enabled, and (b) never store the text, because the metric only needs
length and skeleton and a leaked log must not reconstruct a conversation.
"""

import json
from datetime import datetime

import pytest
from ai.lifecycle import turn_observation as obs


@pytest.fixture(autouse=True)
def _observation_off(monkeypatch):
    """Every test starts from the shipped default: off, and pointed at a tmp dir."""
    monkeypatch.delenv("ANGELA_TURN_OBSERVATION", raising=False)
    monkeypatch.delenv("ANGELA_TURN_OBSERVATION_DIR", raising=False)


def _write(target, *, session="s-1", user="你好", reply="你好呀！", source="template", when=None):
    return obs.record_turn(
        session_id=session,
        user_message=user,
        response_text=reply,
        source=source,
        state={"health": None},
        path=target,
        now=when,
    )


def test_disabled_by_default_writes_nothing(tmp_path):
    target = tmp_path / "turns.jsonl"
    assert obs.observation_enabled() is False
    assert _write(target) is None
    assert not target.exists()


def test_enabling_requires_an_explicit_truthy_value():
    assert obs.observation_enabled({"ANGELA_TURN_OBSERVATION": "1"}) is True
    assert obs.observation_enabled({"ANGELA_TURN_OBSERVATION": "on"}) is True
    assert obs.observation_enabled({"ANGELA_TURN_OBSERVATION": "true"}) is True
    assert obs.observation_enabled({"ANGELA_TURN_OBSERVATION": "0"}) is False
    assert obs.observation_enabled({"ANGELA_TURN_OBSERVATION": ""}) is False
    assert obs.observation_enabled({}) is False


def test_disabled_does_not_create_the_configured_directory(tmp_path, monkeypatch):
    directory = tmp_path / "observations"
    monkeypatch.setenv("ANGELA_TURN_OBSERVATION_DIR", str(directory))
    assert (
        obs.record_turn(session_id="s", user_message="hi", response_text="hello", source="template")
        is None
    )
    assert not directory.exists()


def test_one_line_per_turn_with_a_stable_session_key(tmp_path, monkeypatch):
    monkeypatch.setenv("ANGELA_TURN_OBSERVATION", "1")
    target = tmp_path / "turns.jsonl"
    when = datetime(2026, 11, 11, 12, 0, 0)
    _write(target, when=when)
    _write(target, when=when, reply="第二句。")

    records = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 2
    assert records[0]["turn_id"] != records[1]["turn_id"]
    assert records[0]["session"] == records[1]["session"] == obs._session_hash("s-1")
    assert records[0]["day"] == "2026-11-11"
    assert records[0]["v"] == obs.VERSION


def test_the_log_contains_no_conversation_text(tmp_path, monkeypatch):
    monkeypatch.setenv("ANGELA_TURN_OBSERVATION", "1")
    target = tmp_path / "turns.jsonl"
    _write(
        target,
        user="我的生日是 1990-05-04",
        reply="記住囉，你的生日是 1990-05-04。",
    )
    raw = target.read_text(encoding="utf-8")
    for fragment in ("生日", "1990-05-04", "記住囉", "user_message", "response_text"):
        assert fragment not in raw
    record = json.loads(raw.strip())
    assert record["out_len"] == len("記住囉，你的生日是 1990-05-04。")


def test_unobserved_state_stays_null_and_derived_fields_are_dropped(monkeypatch):
    class _Snapshot:
        def as_dict(self):
            return {
                "version": 2,
                "taken_at": 1.0,
                "effective": None,
                "components": {},
                "weights": {"health": 0.5},
                "source": {},
                "born_at": 1793100290.5,
                "ticks": 3,
                "life_phase": "adult",
                "life_cycle_state": None,
                "health": None,
                "intensity": 0.4,
                "emotion": None,
                "tendency": {"openness": 0.5},
                "drift": {"drift": 0.1},
                "rhythm": None,
            }

    monkeypatch.setattr("core.life.al_state.get_al_state", lambda: _Snapshot())
    record = obs.build_record(
        session_id="s", user_message="hi", response_text="hello", source="template"
    )
    state = record["state"]
    assert state["health"] is None  # never 0.0 — an unobserved field is not zero
    assert state["life_cycle_state"] is None
    assert state["ticks"] == 3
    assert state["life_phase"] == "adult"
    assert "drift" not in state
    assert "born_at" not in state


def test_unreadable_state_is_a_missing_observation_not_a_crash(monkeypatch):
    def _boom():
        raise RuntimeError("state providers not registered")

    monkeypatch.setattr("core.life.al_state.get_al_state", _boom)
    assert obs.state_vector() is None
    record = obs.build_record(
        session_id="s", user_message="hi", response_text="hello", source="knowledge"
    )
    assert record["state"] is None


@pytest.mark.parametrize(
    "text,expected",
    [
        ("", "0"),
        ("好", "1"),
        ("你好呀", "2-4"),
        ("你好呀！", "2-4"),
        ("一二三四五", "5-8"),
        ("一二三四五六七八九", "9-16"),
        ("一二三四五六七八九十一二三四五六七", "17+"),
    ],
)
def test_length_buckets(text, expected):
    assert obs.structure_signature(text)["bucket"] == expected


@pytest.mark.parametrize(
    "text,skeleton",
    [
        ("- 一\n- 二", {"lines": 2, "bullets": True}),
        ("1. 一\n2. 二", {"lines": 2, "numbered": True}),
        ("```\ncode\n```", {"code_fence": True}),
        ("第一句。第二句！第三句？", {"sentences": 3}),
        ("甲\n\n乙", {"paragraphs": 2}),
        ("是嗎？", {"question": True}),
    ],
)
def test_skeleton_flags(text, skeleton):
    detected = obs.structure_signature(text)["skeleton"]
    for key, value in skeleton.items():
        assert detected[key] == value


def test_signature_depends_on_structure_only():
    first = obs.structure_signature("你好")
    second = obs.structure_signature("再見")
    assert len(first["signature"]) == 12
    assert first["signature"] == second["signature"]
    assert first["signature"] != obs.structure_signature("- 你好")["signature"]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("水的沸點是多少?", "question"),
        ("為什麼天空是藍的", "question"),
        ("你好", "statement"),
        ("我今天很累", "statement"),
        ("   ", "empty"),
        ("我是說台北不是台中", "repair"),
        ("That's wrong", "repair"),
        ("幫我查一下", "request"),
    ],
)
def test_user_move_labels(text, expected):
    assert obs.classify_user_move(text) == expected


def test_unknown_source_is_labelled_not_guessed():
    record = obs.build_record(
        session_id="s", user_message="hi", response_text="hello", source="", state={}
    )
    assert record["source"] == "unknown"


def test_chat_response_records_the_route_that_answered(tmp_path, monkeypatch):
    """The wiring point: _format_chat_response must log the derived route."""
    monkeypatch.setenv("ANGELA_TURN_OBSERVATION", "1")
    monkeypatch.setenv("ANGELA_TURN_OBSERVATION_DIR", str(tmp_path))

    from api.routes.chat_routes import _format_chat_response

    result = _format_chat_response(
        "2 + 3 = 5.0",
        {"backend": "deterministic-math"},
        None,
        "v1",
        "",
        "2加3等於多少",
        4096,
        "session-abc",
    )
    assert result["route"] == "computed"

    written = list(tmp_path.glob("turns-*.jsonl"))
    assert len(written) == 1
    record = json.loads(written[0].read_text(encoding="utf-8").strip())
    assert record["source"] == "computed"
    assert record["user_move"] == "question"
    assert record["session"] == obs._session_hash("session-abc")
    assert record["out_len"] == len("2 + 3 = 5.0")
