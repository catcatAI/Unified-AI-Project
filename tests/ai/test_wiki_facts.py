# =============================================================================
# ANGELA-MATRIX: [L1] [β] [A] [L4]
# =============================================================================
"""Contract tests for the offline encyclopedia layer (``ai.knowledge.wiki_facts``).

These run against a tiny temporary FTS5 index, not the 200 MB production index:
the point is the *behaviour* (retrieve, extract, abstain, convert units), which
must not depend on the exact corpus. Questions here are deliberately unrelated
to the evaluation suite so a passing answer cannot come from tuning to it.
"""

from __future__ import annotations

import sqlite3

import pytest

from ai.knowledge import wiki_facts
from ai.knowledge.wiki_facts import WikiFacts, looks_factual, route_general_knowledge

ARTICLES = {
    "Mars": (
        "Mars is the fourth planet from the Sun and the second-smallest planet "
        "in the Solar System, nicknamed The Red Planet. Mars is a terrestrial "
        "planet with caps of water and carbon dioxide."
    ),
    "Speed of light": (
        "The speed of light in a vacuum is exactly 299792458 metres per second. "
        "It is a physical constant important in many areas of physics."
    ),
    "Spiders": (
        "Spiders are air-breathing arthropods. They have eight legs and "
        "mouthparts that inject venom into their prey."
    ),
    "Lighthouse": (
        "A lighthouse is a tower with a bright light at the top. It is built "
        "near the sea to warn ships about rocks."
    ),
    "Nitrogen": (
        "Nitrogen is a nonmetal chemical element. It is a colourless gas that "
        "makes up most of the atmosphere of the Earth."
    ),
    "Silver": (
        "Silver conducts electricity better than any other element. "
        "It is used in electronics and jewellery."
    ),
}


@pytest.fixture()
def facts(tmp_path) -> WikiFacts:
    path = tmp_path / "wiki.sqlite"
    connection = sqlite3.connect(path)
    connection.execute("CREATE VIRTUAL TABLE pages USING fts5(title, body)")
    connection.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT)")
    connection.executemany("INSERT INTO pages(title, body) VALUES (?, ?)", list(ARTICLES.items()))
    connection.commit()
    connection.close()
    return WikiFacts(db_path=path)


def test_available_and_abstains_without_index(tmp_path):
    missing = WikiFacts(db_path=tmp_path / "nope.sqlite")
    assert missing.available() is False
    assert missing.answer("What is the capital of France?") is None


def test_entity_definition_is_returned(facts: WikiFacts):
    answer = facts.answer("What planet is known as the Red Planet?")
    assert answer is not None
    assert "Mars" in answer


def test_retrieves_a_sentence_for_a_descriptive_question(facts: WikiFacts):
    answer = facts.answer("What kind of tower warns ships about rocks?")
    assert answer is not None
    assert "lighthouse" in answer.lower()


def test_converts_units_when_the_question_asks_for_them(facts: WikiFacts):
    answer = facts.answer("What is the speed of light in km/s?")
    assert answer is not None
    assert "299,792" in answer


def test_abstains_when_nothing_overlaps(facts: WikiFacts):
    assert facts.answer("Who painted the Sistine Chapel ceiling?") is None


def test_short_questions_abstain(facts: WikiFacts):
    assert facts.answer("") is None
    assert facts.answer("what") is None


def test_answer_need_not_repeat_the_type_word(facts: WikiFacts):
    """For the question 'What METAL conducts electricity?' the answer
    sentence ('Silver conducts electricity ...') never says 'metal'.
    Requiring the question's type word inside the window discarded real
    answers while letting topically-typed fillers through; only the
    definition-shaped entity path still requires it (_defines). Before this
    fix this question abstained.
    """
    answer = facts.answer("What metal conducts electricity?")
    assert answer is not None
    assert "Silver" in answer


@pytest.mark.parametrize(
    "text, expected",
    [
        ("What gas do beans make?", True),
        ("Why is the sea salty?", True),
        ("hello", False),
        ("how are you?", False),
        ("tell me a story", False),
    ],
)
def test_looks_factual_shape(text: str, expected: bool):
    assert looks_factual(text) is expected


def test_general_route_abstains_on_chat(monkeypatch, facts: WikiFacts):
    monkeypatch.setattr(wiki_facts, "_INSTANCE", facts)
    assert route_general_knowledge("how are you?") is None


def test_general_route_answers_a_factual_question(monkeypatch, facts: WikiFacts):
    monkeypatch.setattr(wiki_facts, "_INSTANCE", facts)
    answer = route_general_knowledge("What planet is known as the Red Planet?")
    assert answer is not None and "Mars" in answer


def test_general_route_can_be_disabled(monkeypatch, facts: WikiFacts):
    monkeypatch.setattr(wiki_facts, "_INSTANCE", facts)
    monkeypatch.setenv("ANGELA_WIKI_FACTS", "0")
    assert route_general_knowledge("What planet is known as the Red Planet?") is None
