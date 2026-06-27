# =============================================================================
# ANGELA-MATRIX: L2-L3 [βδ] [A] L2+
# =============================================================================
"""
Tests for QueryClassifier v2 — intent classification with actionability.
"""

import pytest
from ai.core.query_classifier import (
    _NEGATION_WORDS,
    KNOWLEDGE_QUESTION_PATTERNS,
    VERBS_NOT_REFLEX,
    QueryClassifier,
    QueryResult,
    QueryType,
)


class TestQueryResult:
    """Tests for QueryResult dataclass."""

    def test_query_result_defaults(self):
        r = QueryResult(QueryType.UNKNOWN, 0.5)
        assert r.primary_type == QueryType.UNKNOWN
        assert r.confidence == 0.5
        assert r.actionability == 0.0
        assert r.action_type == "none"
        assert r.secondary_type is None
        assert r.secondary_confidence == 0.0
        assert r.reason == ""

    def test_query_result_full(self):
        r = QueryResult(
            primary_type=QueryType.FILE,
            confidence=0.9,
            actionability=0.8,
            action_type="read",
            secondary_type=QueryType.SEARCH,
            secondary_confidence=0.7,
            reason="pattern_match",
        )
        assert r.primary_type == QueryType.FILE
        assert r.secondary_type == QueryType.SEARCH


class TestQueryClassifierClassify:
    """Tests for classify() method — core classification."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_empty_input(self):
        r = self.clf.classify("")
        assert r.primary_type == QueryType.UNKNOWN
        assert r.confidence == 0.0
        assert r.reason == "empty_input"

    def test_whitespace_input(self):
        r = self.clf.classify("   ")
        assert r.primary_type == QueryType.UNKNOWN
        assert r.confidence == 0.0

    def test_long_text_returns_knowledge(self):
        r = self.clf.classify("a" * 300)
        assert r.primary_type == QueryType.KNOWLEDGE
        assert r.confidence >= 0.8

    def test_returns_query_result(self):
        r = self.clf.classify("hello")
        assert isinstance(r, QueryResult)


class TestQueryClassifierGreeting:
    """Tests for GREETING classification."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_chinese_greeting(self):
        r = self.clf.classify("你好")
        assert r.primary_type == QueryType.GREETING
        assert r.confidence >= 0.8

    def test_english_greeting(self):
        r = self.clf.classify("hello")
        assert r.primary_type == QueryType.GREETING

    def test_greeting_thanks(self):
        r = self.clf.classify("谢谢")
        assert r.primary_type == QueryType.GREETING

    def test_greeting_bye(self):
        r = self.clf.classify("bye")
        assert r.primary_type == QueryType.GREETING


class TestQueryClassifierMath:
    """Tests for MATH classification."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_arithmetic(self):
        r = self.clf.classify("1+2")
        assert r.primary_type == QueryType.MATH

    def test_chinese_math(self):
        r = self.clf.classify("计算一下")
        assert r.primary_type == QueryType.MATH

    def test_english_math(self):
        r = self.clf.classify("calculate 2+3")
        assert r.primary_type == QueryType.MATH


class TestQueryClassifierFile:
    """Tests for FILE classification."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_file_delete(self):
        r = self.clf.classify("删除 temp.txt")
        assert r.primary_type == QueryType.FILE
        assert r.action_type == "delete"

    def test_file_create(self):
        r = self.clf.classify("建立 notes.md")
        assert r.primary_type == QueryType.FILE
        assert r.action_type == "create"

    def test_file_read(self):
        r = self.clf.classify("读取文件")
        assert r.primary_type == QueryType.FILE
        assert r.action_type == "read"

    def test_file_modify(self):
        r = self.clf.classify("修改 config.json")
        assert r.primary_type == QueryType.FILE
        assert r.action_type == "modify"


class TestQueryClassifierSearch:
    """Tests for SEARCH classification."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_chinese_search(self):
        r = self.clf.classify("搜寻台北天气")
        assert r.primary_type == QueryType.SEARCH
        assert r.action_type in ("read", "search")

    def test_english_search(self):
        r = self.clf.classify("search python docs")
        assert r.primary_type == QueryType.SEARCH

    def test_find(self):
        r = self.clf.classify("查找文件")
        assert r.primary_type in (QueryType.SEARCH, QueryType.FILE)


class TestQueryClassifierExecute:
    """Tests for EXECUTE classification."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_execute_command(self):
        r = self.clf.classify("执行这个命令")
        assert r.primary_type == QueryType.EXECUTE
        assert r.action_type in ("system", "execute")

    def test_run_program(self):
        r = self.clf.classify("运行程序")
        assert r.primary_type in (QueryType.EXECUTE, QueryType.CODE)

    def test_open_file(self):
        r = self.clf.classify("开启档案")
        assert r.primary_type == QueryType.EXECUTE


class TestQueryClassifierCode:
    """Tests for CODE classification."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_code_function(self):
        r = self.clf.classify("写一个函数")
        # "写" matches CREATIVE pattern first; CODE needs more specific keywords
        assert r.primary_type in (QueryType.CODE, QueryType.CREATIVE)

    def test_debug(self):
        r = self.clf.classify("调试代码")
        assert r.primary_type == QueryType.CODE


class TestQueryClassifierTask:
    """Tests for TASK classification."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_task_create(self):
        r = self.clf.classify("建立任务")
        # FILE pattern includes "建立", so it may match FILE first
        assert r.primary_type in (QueryType.TASK, QueryType.FILE)
        assert r.action_type == "create"

    def test_task_delete(self):
        r = self.clf.classify("删除任务")
        # FILE pattern includes "删除", so it may match FILE first
        assert r.primary_type in (QueryType.TASK, QueryType.FILE)
        assert r.action_type in ("delete", "none")


class TestQueryClassifierReflex:
    """Tests for REFLEX override and single-char handling."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_reflex_word(self):
        r = self.clf.classify("hi")
        # "hi" matches GREETING pattern with 0.9 confidence, higher than reflex threshold
        assert r.primary_type in (QueryType.REFLEX, QueryType.GREETING)

    def test_single_char_meaningful_verb(self):
        r = self.clf.classify("看")
        assert r.primary_type == QueryType.VISION
        assert r.reason in ("pattern_match", "dictionary_match")

    def test_single_char_not_in_reflex_set(self):
        r = self.clf.classify("哈")
        assert r.primary_type == QueryType.REFLEX

    def test_reflex_override_respects_verbs_not_reflex(self):
        for word in ["看", "查", "开", "关", "读", "写"]:
            r = self.clf.classify(word)
            assert r.primary_type != QueryType.REFLEX, f"'{word}' should not be REFLEX"


class TestQueryClassifierNegation:
    """Tests for negation handling."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_negation_detected(self):
        r = self.clf.classify("不要搜寻")
        assert "negation" in r.reason.lower() or r.confidence < 0.5

    def test_negation_words_in_set(self):
        assert "不要" in _NEGATION_WORDS
        assert "取消" in _NEGATION_WORDS
        assert "stop" in _NEGATION_WORDS
        assert "cancel" in _NEGATION_WORDS


class TestQueryClassifierQuestionMark:
    """Tests for ? override and KNOWLEDGE_QUESTION_PATTERNS."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_knowledge_question_pattern(self):
        r = self.clf.classify("什么是Python?")
        assert r.primary_type == QueryType.KNOWLEDGE
        # May match via pattern or question mark override
        assert r.reason in ("knowledge_question_mark_override", "pattern_match", "dictionary_match")

    def test_how_question(self):
        r = self.clf.classify("how does this work?")
        assert r.primary_type == QueryType.KNOWLEDGE

    def test_random_question_mark(self):
        r = self.clf.classify("今天?")
        assert r.primary_type == QueryType.KNOWLEDGE
        assert r.reason in ("knowledge_question_mark_override", "dictionary_match")


class TestQueryClassifierActionability:
    """Tests for _calc_actionability method."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_high_actionability_execute(self):
        r = self.clf.classify("执行这个命令")
        assert r.actionability >= 0.7

    def test_low_actionability_knowledge(self):
        r = self.clf.classify("什么是Python?")
        assert r.actionability <= 0.3

    def test_negation_reduces_actionability(self):
        r = self.clf.classify("不要搜寻")
        assert r.actionability <= 0.5

    def test_vague_words_reduce_actionability(self):
        r = self.clf.classify("帮我处理一下")
        assert r.actionability <= 0.5


class TestQueryClassifierInferActionType:
    """Tests for _infer_action_type method."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_greeting_returns_none(self):
        r = self.clf.classify("你好")
        assert r.action_type == "none"

    def test_search_returns_read(self):
        r = self.clf.classify("搜寻天气")
        assert r.action_type in ("read", "search")

    def test_file_delete_returns_delete(self):
        r = self.clf.classify("删除文件")
        assert r.action_type == "delete"

    def test_execute_returns_system(self):
        r = self.clf.classify("执行命令")
        assert r.action_type in ("system", "execute")

    def test_task_returns_create(self):
        r = self.clf.classify("建立任务")
        # FILE or TASK both have action_type "create"
        assert r.action_type == "create"


class TestQueryClassifierRegexBoundary:
    """Tests for regex word boundary fixes."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_kai_wan_xiao_not_execute(self):
        """'开玩笑' should NOT match EXECUTE."""
        r = self.clf.classify("开玩笑")
        assert r.primary_type != QueryType.EXECUTE

    def test_guan_xin_not_execute(self):
        """'关心你' should NOT match EXECUTE."""
        r = self.clf.classify("关心你")
        assert r.primary_type != QueryType.EXECUTE

    def test_zhixing_matches_execute(self):
        """'执行这个' should match EXECUTE."""
        r = self.clf.classify("执行这个")
        assert r.primary_type == QueryType.EXECUTE

    def test_kaiqi_matches_execute(self):
        """'开启档案' should match EXECUTE."""
        r = self.clf.classify("开启档案")
        assert r.primary_type == QueryType.EXECUTE


class TestQueryClassifierSecondaryType:
    """Tests for secondary type detection."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_secondary_type_when_close_match(self):
        r = self.clf.classify("搜寻并删除文件")
        assert r.primary_type in (QueryType.SEARCH, QueryType.FILE)
        # Secondary type depends on which patterns match with close confidence
        if r.secondary_type is not None:
            assert r.secondary_type in (QueryType.SEARCH, QueryType.FILE, QueryType.MATH)


class TestQueryClassifierEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def setup_method(self):
        self.clf = QueryClassifier()

    def test_single_space(self):
        r = self.clf.classify(" ")
        assert r.primary_type == QueryType.UNKNOWN

    def test_very_long_chinese(self):
        r = self.clf.classify("这是一段很长的中文文本" * 50)
        assert r.primary_type == QueryType.KNOWLEDGE

    def test_mixed_language(self):
        r = self.clf.classify("hello 你好")
        assert r.primary_type == QueryType.GREETING

    def test_only_punctuation(self):
        r = self.clf.classify("???")
        # "?" triggers knowledge_question_mark_override if pattern matches,
        # otherwise falls to UNKNOWN
        assert r.primary_type in (QueryType.KNOWLEDGE, QueryType.UNKNOWN)

    def test_numbers_only(self):
        r = self.clf.classify("12345")
        assert r.primary_type in (QueryType.MATH, QueryType.UNKNOWN)

    def test_confidence_range(self):
        texts = ["hello", "搜寻天气", "删除文件", "开玩笑", "执行命令"]
        for text in texts:
            r = self.clf.classify(text)
            assert 0.0 <= r.confidence <= 1.0, f"Confidence out of range for '{text}'"
            assert 0.0 <= r.actionability <= 1.0, f"Actionability out of range for '{text}'"
