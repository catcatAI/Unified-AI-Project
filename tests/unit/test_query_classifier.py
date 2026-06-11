"""Tests for ai.core.query_classifier"""
import pytest


class TestQueryClassifier:
    def test_import(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        assert QueryClassifier is not None
        assert QueryType is not None

    def test_classify_empty_string(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("")
        assert qtype == QueryType.UNKNOWN
        assert conf == 0.0

    def test_classify_reflex_short_word(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("哦")
        assert qtype == QueryType.REFLEX
        assert conf == 0.95

    def test_classify_reflex_english(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("ok")
        assert qtype == QueryType.REFLEX

    def test_classify_greeting_chinese(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("你好")
        assert qtype == QueryType.GREETING
        assert conf == 0.9

    def test_classify_greeting_english(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("hello")
        assert qtype == QueryType.GREETING

    def test_classify_math(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("1+1等于多少")
        assert qtype == QueryType.MATH

    def test_classify_knowledge(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("什么是人工智能")
        assert qtype == QueryType.KNOWLEDGE

    def test_classify_knowledge_english(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("what is AI")
        assert qtype == QueryType.KNOWLEDGE

    def test_classify_creative(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("写一首诗")
        assert qtype == QueryType.CREATIVE

    def test_classify_creative_english(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("write a story")
        assert qtype == QueryType.CREATIVE

    def test_classify_command(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("打开浏览器")
        assert qtype == QueryType.COMMAND

    def test_classify_long_text_defaults_to_knowledge(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("a" * 300)
        assert qtype == QueryType.KNOWLEDGE
        assert conf == 0.85

    def test_classify_question_ending_fallback(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("really?")
        assert qtype == QueryType.KNOWLEDGE
        assert conf == 0.65

    def test_classify_unknown(self):
        from ai.core.query_classifier import QueryClassifier, QueryType

        classifier = QueryClassifier()
        qtype, conf = classifier.classify("xyzabc")
        assert qtype == QueryType.UNKNOWN
        assert conf == 0.3
