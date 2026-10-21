"""人話標準（rubric）與標準集的合約測試。

這組測試守的是**判準本身**：如果判準可以被輕易「調過」就會失去意義，
所以測試要同時守住兩面——嚴格的部分（帶邊界條件的題不該被算成通過）與
合理的部分（正確但重述問題的回答不算鸚鵡捲舌）。
"""

from __future__ import annotations

import pytest
from ai.response.human_speech import (
    ABSTAIN,
    APPROXIMATE,
    CORRECT,
    EXCEPTION_AWARE,
    FALSE,
    NON_COMPLIANT,
    PARROT,
    StandardItem,
    build_standard_set,
    classify_state,
    judge,
)


# --------------------------------------------------------------------------- #
# The state classification
# --------------------------------------------------------------------------- #
def test_a_factually_correct_answer_is_correct() -> None:
    item = StandardItem(
        kind="state",
        message="水的沸點是 100°C，這句話對嗎？",
        truth="在標準大氣壓下的純水沸點是 100°C",
        exception="高海拔低氣壓時不到 100°C 就沸騰",
        irrelevant="這杯冰水的溫度是 100°C",
    )
    assert classify_state(item, "在標準大氣壓下的純水沸點是 100°C。") == CORRECT
    assert classify_state(item, "高海拔時不到 100°C 就沸騰，加鹽則高於 100°C。") == EXCEPTION_AWARE
    assert classify_state(item, "這杯冰水的溫度是 100°C。") == NON_COMPLIANT


def test_an_answer_without_the_boundary_is_only_approximately_correct() -> None:
    """「最正確」與「近似正確」的差別：有没有把例外講出來。"""
    item = StandardItem(
        kind="state",
        message="水的沸點是 100°C，這句話對嗎？",
        truth="在標準大氣壓下的純水沸點是 100°C",
        exception="高海拔低氣壓時不到 100°C 就沸騰",
        irrelevant="這杯冰水的溫度是 100°C",
    )
    verdict = judge(item, "在標準大氣壓下的純水沸點是 100°C。")
    assert verdict["state"] in (CORRECT, APPROXIMATE)
    assert verdict["criteria"]["boundary_aware"] is False, "the exception was not mentioned"
    assert verdict["passed"] is False


def test_an_answer_with_the_boundary_is_the_most_correct() -> None:
    item = StandardItem(
        kind="state",
        message="水的沸點是 100°C，這句話對嗎？",
        truth="在標準大氣壓下的純水沸點是 100°C",
        exception="高海拔低氣壓時不到 100°C 就沸騰",
        irrelevant="這杯冰水的溫度是 100°C",
    )
    verdict = judge(
        item,
        "在標準大氣壓下的純水沸點是 100°C；但高海拔低氣壓時不到 100°C 就沸騰，加鹽則高於 100°C。",
    )
    assert verdict["state"] == EXCEPTION_AWARE
    assert verdict["criteria"]["boundary_aware"] is True
    assert verdict["passed"] is True


def test_an_abstention_is_honest_but_not_a_pass() -> None:
    item = StandardItem(kind="qa", message="What is 2+2?", expected="4")
    verdict = judge(item, "我目前還沒有足夠的知識能正確回答。")
    assert verdict["state"] == ABSTAIN
    assert verdict["passed"] is False


def test_an_echo_is_a_parrot() -> None:
    item = StandardItem(kind="qa", message="Who is taller, Anna or Ben?", expected="Anna")
    verdict = judge(item, "Who is taller, Anna or Ben=false")
    assert verdict["state"] == PARROT
    assert verdict["criteria"]["not_parrot"] is False
    assert verdict["passed"] is False


def test_a_correct_answer_that_restates_the_question_is_not_a_parrot() -> None:
    """ "What is 2+2 = 4.0" is a normal math answer, not parroting."""
    item = StandardItem(kind="qa", message="What is 2+2?", expected="4")
    verdict = judge(item, "What is 2+2 = 4.0")
    assert verdict["criteria"]["not_parrot"] is True
    assert verdict["passed"] is True


def test_a_broken_answer_never_passes() -> None:
    item = StandardItem(kind="qa", message="What is 2+2?", expected="4")
    assert judge(item, "What is 2+2 = 4.0？=false")["passed"] is False
    assert judge(item, "")["passed"] is False


# --------------------------------------------------------------------------- #
# The standard set
# --------------------------------------------------------------------------- #
def test_the_standard_set_has_more_than_a_thousand_items() -> None:
    """一千題以內的平均值無法證明會說人話（樣本可能受限於問答行為本身）。"""
    items = build_standard_set()
    assert len(items) >= 1000


def test_the_standard_set_contains_the_dialogue() -> None:
    """「是否是人話」要有對話實例，不只是問答。"""
    items = build_standard_set()
    kinds = {item.kind for item in items}
    assert "dialogue" in kinds
    assert "state" in kinds, "the boundary-condition questions must be in the set"
    assert "multi" in kinds, "the multi-fact scenarios must be in the set"
    dialogue = [i for i in items if i.kind == "dialogue"]
    assert len(dialogue) >= 100


def test_the_state_items_carry_the_ground_truth() -> None:
    """每個帶邊界條件的題都要有：事實、例外、不符合——否則無法裁決。"""
    for item in build_standard_set():
        if item.kind != "state":
            continue
        assert item.truth and item.exception and item.irrelevant


def test_the_multi_fact_items_carry_the_expected_fact() -> None:
    for item in build_standard_set():
        if item.kind == "multi" and item.expected:
            assert item.expected


@pytest.mark.parametrize("state_name", [CORRECT, APPROXIMATE, EXCEPTION_AWARE, FALSE])
def test_the_states_are_distinguishable(state_name: str) -> None:
    assert state_name in (CORRECT, APPROXIMATE, EXCEPTION_AWARE, FALSE)
