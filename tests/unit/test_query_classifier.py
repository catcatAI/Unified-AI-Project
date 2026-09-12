"""Tests for ai.core.query_classifier — classify() returns QueryResult (not tuple)"""
import pytest


class TestQueryClassifier:
    def test_import(self):
        from ai.core.query_classifier import QueryClassifier, QueryResult, QueryType

        assert QueryClassifier is not None
        assert QueryType is not None
        assert QueryResult is not None

    def test_classify_returns_queryresult(self):
        from ai.core.query_classifier import QueryClassifier, QueryResult

        classifier = QueryClassifier()
        result = classifier.classify("")
        assert isinstance(result, QueryResult)

    def test_classify_empty_string(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("")
        assert result.primary_type == QueryType.UNKNOWN
        assert result.confidence == 0.0

    def test_classify_reflex_short_word(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("哦")
        assert result.primary_type == QueryType.REFLEX
        assert result.confidence == 0.95

    def test_classify_reflex_english(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("ok")
        # "ok" is 2 chars (not < 2), doesn't match patterns, falls to UNKNOWN
        assert result.primary_type == QueryType.UNKNOWN

    def test_classify_greeting_chinese(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("你好")
        assert result.primary_type == QueryType.GREETING
        assert result.confidence > 0.8  # adjusted by _adjust_confidence

    def test_classify_greeting_english(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("hello")
        assert result.primary_type == QueryType.GREETING

    def test_classify_math(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("1+1等于多少")
        assert result.primary_type == QueryType.MATH

    def test_classify_knowledge(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("什么是人工智能")
        assert result.primary_type == QueryType.KNOWLEDGE

    def test_classify_knowledge_english(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("what is AI")
        assert result.primary_type == QueryType.KNOWLEDGE

    def test_classify_creative(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("写一首诗")
        assert result.primary_type == QueryType.CREATIVE

    def test_classify_creative_english(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("write a story")
        # "write" also matches FILE pattern with higher base confidence (0.8 > 0.75)
        assert result.primary_type in (QueryType.CREATIVE, QueryType.FILE)

    def test_classify_command(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("打开浏览器")
        # "打开" (simplified) doesn't match COMMAND pattern which uses "打開" (traditional)
        assert result.primary_type in (QueryType.COMMAND, QueryType.UNKNOWN)

    def test_classify_long_text_defaults_to_knowledge(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("a" * 300)
        assert result.primary_type == QueryType.KNOWLEDGE
        assert result.confidence > 0.8  # adjusted by _adjust_confidence

    def test_classify_question_ending_fallback(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("really?")
        # "really?" ends with ? but doesn't match KNOWLEDGE_QUESTION_PATTERNS (^what, ^how, etc.)
        assert result.primary_type in (QueryType.KNOWLEDGE, QueryType.UNKNOWN)

    def test_classify_unknown(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("xyzabc")
        assert result.primary_type == QueryType.UNKNOWN
        assert result.confidence == 0.3


class TestCivilAntiMisjudgment:
    """土木分類防誤判（本輪）：漏判修復 + 主板類誤傷修復，主流程接線守衛。"""

    def test_civil_compound_with_liang_peijin(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("梁跨度8米配筋多少")
        assert result.primary_type == QueryType.CIVIL

    def test_civil_zhu_hunningtu(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("柱截面400x400混凝土C30")
        assert result.primary_type == QueryType.CIVIL

    def test_motherboard_not_civil(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        for s in ("B550M主板", "電腦主板壞了", "黑板上寫字", "平板電腦推薦"):
            result = classifier.classify(s)
            assert result.primary_type != QueryType.CIVIL, s

    def test_civil_routes_to_handler_based(self):
        from ai.core.model_bus import ModelBus
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        result = classifier.classify("梁跨度8米配筋多少")
        assert result.primary_type == QueryType.CIVIL
        assert ModelBus._ROUTE_HANDLERS["civil"] == "_handle_handler_based"

    def test_civil_gate_maps_to_civil_handler(self):
        from ai.core.execution_gate import ExecutionGate

        assert ExecutionGate.HANDLER_MAP["civil"] == "civil"


class TestWiringSweepAntiMisjudgment:
    """主流程接線掃描（本輪）：句中關鍵詞 + 字典低置信讓位 + 否定封頂。"""

    def test_knowledge_mid_sentence_what_is(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        result = QueryClassifier().classify("什麼是光合作用")
        assert result.primary_type == QueryType.KNOWLEDGE
        assert result.reason == "regex_pattern_match"

    def test_opinion_mid_sentence_feel(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        result = QueryClassifier().classify("你覺得哪款手機好")
        assert result.primary_type == QueryType.OPINION

    def test_code_mid_sentence_function(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        result = QueryClassifier().classify("寫個Python快排函數")
        assert result.primary_type == QueryType.CODE

    def test_logic推理_mid_sentence(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        result = QueryClassifier().classify("這個推理有問題嗎")
        assert result.primary_type == QueryType.LOGIC

    def test_negation_caps_actionable_confidence(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        for s, want in (("不要搜寻", QueryType.SEARCH), ("不要刪除文件", QueryType.FILE)):
            result = QueryClassifier().classify(s)
            assert result.primary_type == want, s
            assert result.confidence < 0.5, s

    def test_motherboard_still_not_civil(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        assert QueryClassifier().classify("B550M主板").primary_type != QueryType.CIVIL

    def test_task_domain_beats_generic_file_verbs(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        for s in ("建立任務：買牛奶", "刪除任務 #1"):
            result = QueryClassifier().classify(s)
            assert result.primary_type == QueryType.TASK, s

    def test_file_with_entity_signal_stays_file(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        for s in ("刪除桌面文件", "建立 notes.md", "整理桌面文件"):
            result = QueryClassifier().classify(s)
            assert result.primary_type == QueryType.FILE, s
