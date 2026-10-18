# ANGELA-MATRIX: [L3] [β] [B] [L2]

"""Unit tests for ai.rules.solution_rules: verification gate + rule store."""

from __future__ import annotations

import os

import pytest
from ai.rules import solution_rules as sr
from ai.rules.solution_rules import (
    RuleStore,
    canonical_key,
    is_dynamic_query,
    verify_solution,
)


class TestCanonicalKey:
    def test_trailing_punctuation_and_case_trimmed(self) -> None:
        assert canonical_key("3+5=8??") == canonical_key("3+5=8")
        assert canonical_key("  HELLO  ") == "hello"

    def test_fullwidth_normalizes_to_same_key(self) -> None:
        assert canonical_key("3+5=8") == canonical_key("３＋５＝８")

    def test_numbers_preserve_identity(self) -> None:
        assert canonical_key("3+5=8") != canonical_key("3+5=9")

    def test_interior_spacing_kept_as_distinct_identity(self) -> None:
        assert canonical_key("3 + 5 = 8") != canonical_key("3+5=8")

    def test_empty_and_none_safe(self) -> None:
        assert canonical_key("") == ""
        assert canonical_key(None) == ""  # type: ignore[arg-type]


class TestIsDynamicQuery:
    @pytest.mark.parametrize(
        "query",
        ["今天幾號", "現在幾點", "明天星期幾", "明天天氣如何", "今日運勢", "請問天氣"],
    )
    def test_dynamic_queries_detected(self, query: str) -> None:
        assert is_dynamic_query(query) is True

    @pytest.mark.parametrize(
        "query",
        ["2026年10月18日是星期幾", "小明有3個蘋果，給了弟弟1個", "水的沸點是多少度"],
    )
    def test_static_queries_not_flagged(self, query: str) -> None:
        assert is_dynamic_query(query) is False


class TestVerifySolution:
    def test_word_problem_with_verified_steps(self) -> None:
        ok, kind, reason = verify_solution(
            "小明有3個蘋果，給了弟弟1個，還剩幾個？", "3-1=2，所以還剩2個"
        )
        assert ok is True
        assert kind == "math"
        assert reason == "arithmetic_verified"

    def test_paren_expression_verified(self) -> None:
        ok, kind, _ = verify_solution("請計算(3+5)*2", "先算括號：(3+5)*2=16，答案是16")
        assert ok is True
        assert kind == "math"

    def test_fullwidth_operators_verified(self) -> None:
        ok, _, reason = verify_solution("請計算 3×5+5", "3×5+5＝20，答案是20")
        assert ok is True
        assert reason == "arithmetic_verified"

    def test_arithmetic_mismatch_rejected(self) -> None:
        ok, _, reason = verify_solution("請計算 3加5", "3+5=9")
        assert ok is False
        assert reason == "arithmetic_mismatch"

    def test_final_claim_mismatch_rejected(self) -> None:
        ok, _, reason = verify_solution("請計算 3加5", "3+5=8，答案是9")
        assert ok is False
        assert reason == "final_claim_mismatch"

    def test_unverifiable_answer_rejected(self) -> None:
        ok, _, reason = verify_solution("請計算 12減3乘2", "答案取決於很多因素")
        assert ok is False
        assert reason == "no_equation"

    def test_echo_of_query_rejected(self) -> None:
        query = "請問3加5等於多少呀請問3加5等於多少呀"
        ok, _, reason = verify_solution(query, query)
        assert ok is False
        assert reason == "echo_of_query"

    def test_dynamic_query_rejected(self) -> None:
        ok, _, reason = verify_solution("今天幾號", "3+5=8，答案是8")
        assert ok is False
        assert reason == "dynamic_query"

    @pytest.mark.parametrize(
        ("query", "answer", "expected"),
        [
            ("x", "3+5=8", "empty_query"),
            ("請計算 3+5", "好", "answer_too_short"),
            ("請計算 3+5", "1+1=2 " * 120, "answer_too_long"),
            ("", "3+5=8，答案是8", "empty_query"),
        ],
    )
    def test_bounds_rejected(self, query: str, answer: str, expected: str) -> None:
        ok, _, reason = verify_solution(query, answer)
        assert ok is False
        assert reason == expected

    def test_symbolic_assignment_not_treated_as_verifiable(self) -> None:
        ok, _, reason = verify_solution("解方程", "設x=5，代入即可")
        assert ok is False
        assert reason == "no_equation"


def _word_problem_query() -> str:
    return "小明有3個蘋果，給了弟弟1個，還剩幾個？"


def _word_problem_answer() -> str:
    return "3-1=2，所以還剩2個"


@pytest.fixture()
def store(tmp_path) -> RuleStore:
    return RuleStore(path=str(tmp_path / "rules.json"))


class TestRuleStore:
    def test_admit_and_recall_verbatim(self, store: RuleStore) -> None:
        admitted = store.remember(_word_problem_query(), _word_problem_answer())
        assert admitted is not None
        hit = store.recall(_word_problem_query())
        assert hit is not None
        assert hit.answer == _word_problem_answer()
        assert hit.serves == 1

    def test_recall_tolerates_trailing_punctuation(self, store: RuleStore) -> None:
        store.remember(_word_problem_query(), _word_problem_answer())
        hit = store.recall(_word_problem_query().rstrip("？") + "?")
        assert hit is not None

    def test_unverifiable_never_admitted(self, store: RuleStore) -> None:
        assert store.remember("這是什麼意思呢", "這取決於脈絡與語境") is None
        assert store.recall("這是什麼意思呢") is None

    def test_duplicate_key_keeps_first_rule(self, store: RuleStore) -> None:
        first = store.remember(_word_problem_query(), _word_problem_answer())
        second = store.remember(_word_problem_query(), _word_problem_answer())
        assert first is not None and second is not None
        assert first.id == second.id

    def test_different_numbers_are_different_rules(self, store: RuleStore) -> None:
        q2 = "小明有3個蘋果，給了弟弟2個，還剩幾個？"
        a2 = "3-2=1，所以還剩1個"
        r1 = store.remember(_word_problem_query(), _word_problem_answer())
        r2 = store.remember(q2, a2)
        assert r1 is not None and r2 is not None
        assert r1.key != r2.key
        hit = store.recall(q2)
        assert hit is not None
        assert hit.answer == a2

    def test_two_failures_drop_below_gate(self, store: RuleStore) -> None:
        rule = store.remember(_word_problem_query(), _word_problem_answer())
        assert rule is not None
        assert store.record_outcome(rule.id, False) is True
        assert store.record_outcome(rule.id, False) is True
        assert rule.confidence < 0.5
        assert store.recall(_word_problem_query()) is None

    def test_single_failure_still_serves(self, store: RuleStore) -> None:
        rule = store.remember(_word_problem_query(), _word_problem_answer())
        assert rule is not None
        store.record_outcome(rule.id, False)
        assert rule.confidence >= 0.5
        assert store.recall(_word_problem_query()) is not None

    def test_success_feedback_raises_confidence(self, store: RuleStore) -> None:
        rule = store.remember(_word_problem_query(), _word_problem_answer())
        assert rule is not None
        baseline = rule.confidence
        store.record_outcome(rule.id, True)
        store.record_outcome(rule.id, True)
        assert rule.confidence > baseline

    def test_record_outcome_unknown_id(self, store: RuleStore) -> None:
        assert store.record_outcome("missing-id", True) is False

    def test_persistence_roundtrip(self, tmp_path) -> None:
        path = str(tmp_path / "rules.json")
        first = RuleStore(path=path)
        rule = first.remember(_word_problem_query(), _word_problem_answer())
        assert rule is not None
        reloaded = RuleStore(path=path)
        hit = reloaded.recall(_word_problem_query())
        assert hit is not None
        assert hit.answer == _word_problem_answer()
        assert hit.id == rule.id

    def test_corrupt_file_tolerated(self, tmp_path) -> None:
        path = str(tmp_path / "rules.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{not json")
        store = RuleStore(path=path)
        assert store.recall(_word_problem_query()) is None
        assert store.remember(_word_problem_query(), _word_problem_answer()) is not None

    def test_eviction_caps_store_at_max_rules(self, store_factory) -> None:
        store = store_factory(max_rules=2)
        r1 = store.remember(_word_problem_query(), _word_problem_answer())
        r2 = store.remember("請計算 12減3乘2", "12-3*2=6，答案是6")
        r3 = store.remember("請計算 7加8", "7+8=15，答案是15")
        assert r1 is not None and r2 is not None and r3 is not None
        assert store.stats()["total"] == 2
        assert store.recall(_word_problem_query()) is None
        assert store.recall("請計算 7加8") is not None

    def test_recall_drops_rule_when_reverify_fails(
        self, store: RuleStore, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        rule = store.remember(_word_problem_query(), _word_problem_answer())
        assert rule is not None
        monkeypatch.setattr(sr, "verify_solution", lambda q, a: (False, "", "forced_failure"))
        assert store.recall(_word_problem_query()) is None
        monkeypatch.undo()
        assert store.recall(_word_problem_query()) is None

    def test_stats_shape(self, store: RuleStore) -> None:
        empty = store.stats()
        assert empty["total"] == 0
        assert empty["by_kind"] == {}
        rule = store.remember(_word_problem_query(), _word_problem_answer())
        assert rule is not None
        store.recall(_word_problem_query())
        store.record_outcome(rule.id, True)
        stats = store.stats()
        assert stats["total"] == 1
        assert stats["serves"] == 1
        assert stats["feedback"] == 1
        assert stats["by_kind"] == {"math": 1}
        assert 0.0 < stats["avg_confidence"] <= 1.0

    def test_remember_rejects_dynamic_query(self, store: RuleStore) -> None:
        assert store.remember("今天幾號", "3+5=8，答案是8") is None


@pytest.fixture()
def store_factory(tmp_path):
    def factory(max_rules: int = 500) -> RuleStore:
        return RuleStore(path=str(tmp_path / f"rules_{max_rules}.json"), max_rules=max_rules)

    return factory


class TestGetRuleStoreSingleton:
    def test_same_instance_and_env_path_override(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        monkeypatch.setattr(sr, "_STORE", None)
        env_path = str(tmp_path / "env_rules.json")
        monkeypatch.setenv("ANGELA_SOLUTION_RULES_PATH", env_path)
        first = sr.get_rule_store()
        second = sr.get_rule_store()
        assert first is second
        rule = first.remember(_word_problem_query(), _word_problem_answer())
        assert rule is not None
        assert os.path.exists(env_path)
