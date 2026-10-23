"""Contract tests for dialogue-taught facts (invented entities, no corpus)."""

import json

import pytest

from ai.memory.taught_facts import TaughtFacts, get_taught_facts, reset_taught_facts


@pytest.fixture
def store(tmp_path):
    return TaughtFacts(path=tmp_path / "taught_facts.json")


def test_extracts_chinese_triple(store):
    store.learn_from_turn("Zorblax 的首都是 Quuxville。")
    facts = store.facts()
    assert len(facts) == 1
    assert (facts[0].subject, facts[0].relation, facts[0].object) == (
        "Zorblax",
        "首都",
        "Quuxville",
    )


def test_extracts_english_triple(store):
    store.learn_from_turn("the capital of Vexmoor is Driftmoor.")
    assert store.lookup("What is the capital of Vexmoor?") == (
        "The capital of Vexmoor is Driftmoor."
    )


def test_question_is_never_stored(store):
    store.learn_from_turn("Zorblax 的首都是哪裡？")
    store.learn_from_turn("What is the capital of Vexmoor?")
    assert store.facts() == []


def test_wh_value_is_never_stored(store):
    # Not a question by punctuation, but the value is a question word.
    store.learn_from_turn("我想知道 Zorblax 的首都是什麼")
    assert store.facts() == []


def test_correction_replaces_the_old_object(store):
    store.learn_from_turn("Zorblax 的首都是 Quuxville。")
    store.learn_from_turn("更正：Zorblax 的首都不是 Quuxville，是 Brindleford。")
    facts = store.facts()
    assert len(facts) == 1
    assert facts[0].object == "Brindleford"
    assert facts[0].revision == 2
    assert "Quuxville" not in store.lookup("Zorblax 的首都是哪裡？")


def test_alias_is_taught_once_and_applies_to_a_new_subject(store):
    store.learn_from_turn("在這裡，首府和首都指的是同一件事。")
    store.learn_from_turn("Zorblax 的首都是 Quuxville。")
    assert store.lookup("Zorblax 的首府在哪裡？") == "Zorblax的首都是 Quuxville。"


def test_postposed_question_form(store):
    store.learn_from_turn("口語上，「誰創辦的」和「創辦人是誰」是同一個問題。")
    store.learn_from_turn("Pellucid 的創辦人是 Mira Voss。")
    assert store.lookup("Pellucid 是誰創辦的？") == "Pellucid的創辦人是 Mira Voss。"


def test_abstains_on_unrelated_relation(store):
    store.learn_from_turn("the capital of Vexmoor is Driftmoor.")
    assert store.lookup("What is the population of Vexmoor?") is None


def test_abstains_on_unknown_subject(store):
    store.learn_from_turn("Zorblax 的首都是 Quuxville。")
    assert store.lookup("Nolvane 的首都是哪裡？") is None


def test_composition_follows_question_order(store):
    store.learn_from_turn("Vexmoor 的首都是 Driftmoor。")
    store.learn_from_turn("Zorblax 的首都是 Quuxville。")
    answer = store.lookup("Vexmoor 和 Zorblax 的首都分別是什麼？")
    assert answer == "Vexmoor的首都是 Driftmoor；Zorblax的首都是 Quuxville。"


def test_persists_and_reloads(tmp_path):
    path = tmp_path / "facts.json"
    first = TaughtFacts(path=path)
    first.learn_from_turn("Zorblax 的首都是 Quuxville。")
    first.learn_from_turn("首府和首都指的是同一件事。")
    reloaded = TaughtFacts(path=path)
    assert reloaded.lookup("Zorblax 的首府在哪裡？") == "Zorblax的首都是 Quuxville。"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["facts"][0]["subject"] == "Zorblax"
    assert any("首府" in group for group in payload["aliases"])


def test_singleton_honours_the_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("ANGELA_TAUGHT_FACTS", str(tmp_path / "env.json"))
    reset_taught_facts()
    try:
        get_taught_facts().learn_from_turn("Zorblax 的首都是 Quuxville。")
        assert (tmp_path / "env.json").is_file()
    finally:
        reset_taught_facts()


def test_chat_shortcircuit_answers_from_taught_facts(tmp_path, monkeypatch):
    from api.routes.chat_routes import _try_taught_facts

    monkeypatch.setenv("ANGELA_TAUGHT_FACTS", str(tmp_path / "chat.json"))
    reset_taught_facts()
    try:
        get_taught_facts().learn_from_turn("Zorblax 的首都是 Quuxville。")
        result = _try_taught_facts("Zorblax 的首都是哪裡？", "test-session")
        assert result is not None
        assert result["source"] == "memory"
        assert result["response"].startswith("你教過我：")
        assert "Quuxville" in result["response"]
        assert _try_taught_facts("Nolvane 的首都是哪裡？", "test-session") is None
    finally:
        reset_taught_facts()
