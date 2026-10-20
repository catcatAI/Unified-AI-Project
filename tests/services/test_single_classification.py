"""
ANGELA-MATRIX: [L3] [β] [B] [L2]
One message, one classification.

The pipeline, the router and the MSBA pipeline each classified the same
message on their own. The status matrix records that duplicate-classification
debt as the project's top architectural gap: two classifiers can disagree
about what a message *is*, and the same message then takes two different
routes.

The decision is now published on the request context
(``_classify_result_type`` / ``_preprocessing_plan.query_type``) and read by
every consumer.
"""

import pytest
from services.llm.router import AngelaLLMService


class _CountingClassifier:
    """A classifier that counts how often it was asked."""

    def __init__(self):
        self.calls = 0

    def classify(self, text):
        self.calls += 1

        class _Result:
            primary_type = type("T", (), {"value": "chitchat"})()
            secondary_type = None
            secondary_confidence = 0.0
            confidence = 0.9
            action_type = "chat"
            actionability = 0.0
            route_hint = "balanced"
            reason = "test"

        return _Result()


def test_the_query_type_is_read_from_the_request():
    service = object.__new__(AngelaLLMService)
    context = {"_classify_result_type": "math"}
    assert AngelaLLMService._query_type("1+1 是多少", context) == "math"


def test_the_preprocessing_plan_is_used_when_there_is_no_cached_type():
    service = object.__new__(AngelaLLMService)
    context = {"_preprocessing_plan": {"query_type": "code"}}
    assert AngelaLLMService._query_type("寫一個函式", context) == "code"


def test_the_classifier_runs_only_when_nobody_classified_yet(monkeypatch):
    """With a cached decision, the classifier is not consulted at all."""
    classifier = _CountingClassifier()
    monkeypatch.setattr("ai.core.query_classifier.QueryClassifier", lambda *a, **k: classifier)
    context = {"_classify_result_type": "knowledge"}
    assert AngelaLLMService._query_type("什麼是光合作用", context) == "knowledge"
    assert classifier.calls == 0


def test_the_math_and_code_guards_use_the_shared_decision(monkeypatch):
    """A cached "math" decision must stop the memory recall, without a
    second classification."""
    classifier = _CountingClassifier()
    monkeypatch.setattr("ai.core.query_classifier.QueryClassifier", lambda *a, **k: classifier)
    service = object.__new__(AngelaLLMService)
    context = {"_classify_result_type": "math"}
    assert service._recall_math_guard("一百加二十是多少", context) is True
    assert service._recall_code_guard("一百加二十是多少", context) is False
    assert classifier.calls == 0


def test_the_factual_query_guard_uses_the_shared_decision(monkeypatch):
    classifier = _CountingClassifier()
    monkeypatch.setattr("ai.core.query_classifier.QueryClassifier", lambda *a, **k: classifier)
    context = {"_classify_result_type": "math"}
    assert AngelaLLMService._is_factual_query("1+1", context) is True
    assert classifier.calls == 0
