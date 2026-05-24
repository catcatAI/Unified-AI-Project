import pytest
from ai.lis.err_introspector import ERRIntrospector


@pytest.fixture
def introspector():
    return ERRIntrospector()


def test_err_introspector_imports():
    from ai.lis.err_introspector import ERRIntrospector
    assert ERRIntrospector is not None


def test_introspector_init_defaults(introspector):
    assert introspector.output_history == []
    assert introspector.max_history == 15


def test_vectorize_simple(introspector):
    vector = introspector._vectorize("hello world")
    assert "hello" in vector
    assert "world" in vector


def test_vectorize_short_words_ignored(introspector):
    vector = introspector._vectorize("a an is it")
    assert vector == {}


def test_cosine_similarity_identical(introspector):
    vec = {"hello": 0.5, "world": 0.5}
    sim = introspector._cosine_similarity(vec, vec)
    assert sim == pytest.approx(0.5)


def test_cosine_similarity_disjoint(introspector):
    vec1 = {"hello": 0.6, "world": 0.8}
    vec2 = {"foo": 1.0}
    sim = introspector._cosine_similarity(vec1, vec2)
    assert sim == 0.0


def test_detect_ethical_divergence_safe(introspector):
    result = introspector._detect_ethical_divergence("Have a great day")
    assert result is None


def test_detect_ethical_divergence_restricted(introspector):
    result = introspector._detect_ethical_divergence("This contains malware")
    assert result is not None
    assert result["anomaly_type"] == "ETHICAL_DIVERGENCE"
    assert result["severity_score"] > 0.5
async def test_analyze_output_clean(introspector):
    events = await introspector.analyze_output("Have a wonderful day", {})
    assert isinstance(events, list)
    assert len(events) == 0
async def test_analyze_output_ethical_violation(introspector):
    events = await introspector.analyze_output("This is illegal and harmful", {})
    assert len(events) >= 1
    types = [e["anomaly_type"] for e in events]
    assert "ETHICAL_DIVERGENCE" in types
