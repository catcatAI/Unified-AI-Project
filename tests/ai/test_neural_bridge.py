"""Tests for the intermediate layer (neural bridge).

The layer sits between the neural model and the deterministic teacher:
contact (semantic matching) → alignment (teacher feedback) → composition.
"""

from __future__ import annotations

import pytest
from ai.reasoning.neural_bridge import (
    ANY_DIMENSION,
    CONCEPT_SEEDS,
    DIMENSION_SEEDS,
    DIRECTION_SEEDS,
    GREATER,
    GREATEST,
    LEAST,
    LESSER,
    SUPERLATIVE_SEEDS,
    NeuralBridge,
    RelationMatcher,
    extract_aggregation_span,
    extract_relation_spans,
)


@pytest.fixture(scope="module")
def bridge() -> NeuralBridge:
    return NeuralBridge()


# --------------------------------------------------------------------------- #
# The seeds must be the teacher's vocabulary (otherwise the claim is false)
# --------------------------------------------------------------------------- #
def test_relation_seeds_come_from_the_teacher_vocabulary() -> None:
    from ai.symbolic_reasoner import _EXTRA_GREATER, _EXTRA_LESSER, _GREATER, _LESSER

    teacher = set(_GREATER) | set(_LESSER) | set(_EXTRA_GREATER) | set(_EXTRA_LESSER)
    for (dimension, direction), words in CONCEPT_SEEDS.items():
        for word in words:
            assert (
                word in teacher
            ), f"{word!r} ({dimension}/{direction}) is not in the teacher's vocabulary"


def test_direction_seeds_come_from_the_teacher_superlatives() -> None:
    """Every direction seed is a teacher superlative (or its Chinese form)."""
    from ai.symbolic_reasoner import _superlative

    teacher_words = set()
    for (dimension, relation), words in CONCEPT_SEEDS.items():
        for word in words:
            for least in (False, True):
                phrase = _superlative(word, least=least).lower()
                teacher_words.add(phrase)
                teacher_words.add(phrase[4:] if phrase.startswith("the ") else phrase)
    # The Chinese superlatives are derived from the teacher's Chinese words.
    teacher_cn = {w for words in CONCEPT_SEEDS.values() for w in words if not w.isascii()}
    derived_cn = {f"最{w}" for w in teacher_cn}
    for direction, words in DIRECTION_SEEDS.items():
        for word in words:
            assert (
                word.lower() in teacher_words or word in derived_cn
            ), f"{word!r} ({direction}) is not a teacher superlative"


def test_the_superlative_seeds_follow_the_teacher_table() -> None:
    from ai.symbolic_reasoner import _superlative

    for (dimension, relation), words in CONCEPT_SEEDS.items():
        direction = "greatest" if relation == "greater" else "least"
        least = direction == "least"
        expected = {_superlative(word, least=least).lower() for word in words}
        expected |= {phrase[4:] for phrase in expected if phrase.startswith("the ")}
        assert set(SUPERLATIVE_SEEDS[(dimension, direction)]) >= expected


def test_dimension_seeds_are_derived_from_the_concepts() -> None:
    for dimension, words in DIMENSION_SEEDS.items():
        expected = {
            w for (dim, _d), seeds in CONCEPT_SEEDS.items() if dim == dimension for w in seeds
        }
        assert set(words) == expected


# --------------------------------------------------------------------------- #
# The contact step
# --------------------------------------------------------------------------- #
def test_contact_places_a_teacher_word(bridge: NeuralBridge) -> None:
    match = bridge.matcher.classify("taller", kind="relation")
    assert match is not None
    assert match[0] == ("size", GREATER)


def test_contact_places_an_unseen_paraphrase(bridge: NeuralBridge) -> None:
    """The teacher has no "exceeds"; the encoder places it near "bigger"."""
    match = bridge.matcher.classify("exceeds", kind="relation")
    assert match is not None
    assert match[0][0] == "size"


def test_a_question_word_is_never_used_as_a_relation(bridge: NeuralBridge) -> None:
    """The structural rules keep the question words out of the relations."""
    assert bridge.answer("Who is the tallest?") is None
    assert bridge.answer("Which one is bigger?") is None


def test_dimension_and_direction_are_matched_separately(bridge: NeuralBridge) -> None:
    dimension = bridge.matcher.classify_dimension("the coldest")
    direction = bridge.matcher.classify_direction("the coldest")
    assert dimension is not None and dimension[0] == "temperature"
    assert direction is not None and direction[0] == LEAST
    assert bridge.matcher.classify_direction("the tallest")[0] == GREATEST  # type: ignore[index]


# --------------------------------------------------------------------------- #
# The composition step
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "question,expected",
    [
        ("The first is higher than second, second higher than third, which is top?", "first"),
        ("X is colder than Y, Y colder than Z, who coldest?", "X"),
        ("Tom is younger than Jerry, Jerry younger than Spike, who youngest?", "Tom"),
        ("A is not as short as B, B not as short as C, who shortest?", "C"),
        ("若甲比乙高，乙比丙高，誰最高？", "甲"),
    ],
)
def test_the_bridge_answers_the_teacher_vocabulary(
    bridge: NeuralBridge, question: str, expected: str
) -> None:
    answer = bridge.answer(question)
    assert answer is not None
    assert expected.lower() in answer.lower()


@pytest.mark.parametrize(
    "question,expected",
    [
        ("The first exceeds second, second exceeds third, which is on top?", "first"),
        ("X is cooler than Y, Y cooler than Z, who is the coolest?", "X"),
        ("Tom is junior to Jerry, Jerry junior to Spike, who is the youngest?", "Tom"),
    ],
)
def test_the_bridge_generalises_beyond_the_teacher(
    bridge: NeuralBridge, question: str, expected: str
) -> None:
    from ai.symbolic_reasoner import route_reasoning

    assert route_reasoning(question) is None, "the teacher is expected to fail this one"
    answer = bridge.answer(question)
    assert answer is not None
    assert expected.lower() in answer.lower()


def test_the_bridge_refuses_a_question_of_another_dimension(bridge: NeuralBridge) -> None:
    """A size chain cannot answer "who is the coldest"."""
    assert (
        bridge.answer("The box is bigger than the bag, the bag bigger than the cup, who coldest?")
        is None
    )


def test_the_bridge_refuses_an_empty_question(bridge: NeuralBridge) -> None:
    assert bridge.answer("") is None
    assert bridge.answer("   ") is None


def test_the_bridge_answers_a_yes_no_question(bridge: NeuralBridge) -> None:
    answer = bridge.answer(
        "If Tom is older than Jerry, Jerry older than Spike, is Tom older than Spike? yes/no"
    )
    assert answer == "yes"


# --------------------------------------------------------------------------- #
# The alignment step
# --------------------------------------------------------------------------- #
def test_alignment_moves_the_prototype_toward_the_phrase() -> None:
    matcher = RelationMatcher()
    concept = ("size", GREATER)
    before = matcher.classify("outranks", kind="relation")
    stats = matcher.align("outranks", concept, kind="relation")
    assert stats > 0.0, "the alignment must increase the similarity"
    after = matcher.classify("outranks", kind="relation")
    assert after is not None and before is not None
    assert after[1] > before[1]


def test_alignment_places_an_ambiguous_word() -> None:
    """With the teacher's verdict the ambiguous word lands in the right concept."""
    matcher = RelationMatcher()
    matcher.align("outranks", ("size", GREATER), kind="relation")
    match = matcher.classify("outranks", kind="relation")
    assert match is not None
    assert match[0] == ("size", GREATER)


def test_the_bridge_aligns_from_a_teacher_verdict() -> None:
    bridge = NeuralBridge()
    stats = bridge.align_phrase("cooler", ("temperature", LESSER))
    assert stats["aligned"] == 1.0
    assert stats["delta"] > 0.0


def test_the_bridge_aligns_a_direction() -> None:
    bridge = NeuralBridge()
    stats = bridge.align_phrase("the lightest", LEAST)
    assert stats["delta"] > 0.0


def test_the_alignment_never_stores_the_question() -> None:
    """The alignment only moves prototypes: the state stays small."""
    bridge = NeuralBridge()
    before = bridge.matcher.stats()
    bridge.align_from_feedback(
        "A mysterious sentence the teacher cannot answer?",
        expected="X",
        teacher_concept=("size", GREATER),
    )
    assert bridge.matcher.stats() == before


# --------------------------------------------------------------------------- #
# The extraction helpers
# --------------------------------------------------------------------------- #
def test_extract_relation_spans_finds_the_structural_shapes() -> None:
    spans = extract_relation_spans("若甲比乙高")
    assert spans and spans[0][0] == "甲" and spans[0][2] == "乙"
    symbolic = extract_relation_spans("A > B")
    assert symbolic and symbolic[0][1] == "greater"


def test_extract_aggregation_span_takes_the_question_tail() -> None:
    assert extract_aggregation_span("who coldest?") == "who coldest"
    assert extract_aggregation_span("誰最高？") == "誰最高"


def test_the_matcher_reports_its_concepts() -> None:
    matcher = RelationMatcher()
    stats = matcher.stats()
    assert stats["relation_concepts"] == len(CONCEPT_SEEDS)
    assert stats["dimension_concepts"] == len(DIMENSION_SEEDS)
    # The direction seeds: the global ones plus the per-dimension ones.
    assert stats["direction_concepts"] == len(DIRECTION_SEEDS) + len(SUPERLATIVE_SEEDS)


def test_the_any_dimension_is_not_a_real_dimension() -> None:
    assert ANY_DIMENSION not in DIMENSION_SEEDS
