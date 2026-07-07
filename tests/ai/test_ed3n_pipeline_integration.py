"""
Test: Can the system retrieve content from conversation history?
Tests ED3N dictionary-based retrieval and context matching.
"""
import sys

import pytest

sys.path.insert(0, "apps/backend/src")


def test_ed3n_retrieval():
    """Test ED3N dictionary encode/decode for context retrieval."""
    from ai.ed3n.ed3n_engine import ED3NEngine

    engine = ED3NEngine()
    engine.load_presets()

    history = [
        {"role": "user", "content": "Angela 是什麼？"},
        {"role": "assistant", "content": "Angela 是一個 AI 數字生命，具有情緒和記憶能力。"},
        {"role": "user", "content": "幫我搜尋台北天氣"},
        {"role": "assistant", "content": "台北今天晴朗，氣溫 28°C。"},
        {"role": "user", "content": "刪除 temp.txt"},
        {"role": "assistant", "content": "刪除操作不可逆，我無法直接執行。你確定要刪除嗎？"},
    ]

    query = "Angela 有什麼能力？"
    query_keys = set(engine.dictionary.encode(query))
    print(f"Query: '{query}'")
    print(f"Query keys: {query_keys}")

    retrieved = []
    for entry in history:
        content = entry.get("content", "")
        if not content:
            continue
        entry_keys = set(engine.dictionary.encode(content))
        overlap = len(query_keys & entry_keys)
        if overlap > 0:
            retrieved.append({**entry, "relevance": float(overlap)})

    retrieved.sort(key=lambda x: x["relevance"], reverse=True)

    print(f"\nRetrieved {len(retrieved)} relevant entries:")
    for r in retrieved:
        print(f"  [{r['role']}] {r['content'][:50]}... (relevance: {r['relevance']})")

    assert len(retrieved) > 0, "Should retrieve at least 1 relevant entry"
    assert retrieved[0]["relevance"] > 0, "Top entry should have positive relevance"
    print("\nED3N retrieval test PASSED")


def test_query_classifier_classification():
    """Test that queries are correctly classified."""
    from ai.core.query_classifier import QueryClassifier, QueryType

    clf = QueryClassifier()

    test_cases = [
        ("Angela 是什麼？", QueryType.KNOWLEDGE),
        ("搜尋台北天氣", QueryType.SEARCH),
        ("刪除 temp.txt", QueryType.FILE),
        (" 幫我建立文件", QueryType.FILE),
        ("執行這個命令", QueryType.EXECUTE),
        ("你好", QueryType.GREETING),
        ("1+2", QueryType.MATH),
    ]

    print("\nQuery Classification Tests:")
    all_pass = True
    for text, expected in test_cases:
        r = clf.classify(text)
        status = "PASS" if r.primary_type == expected else "FAIL"
        if r.primary_type != expected:
            all_pass = False
        print(f"  {status} '{text}' -> {r.primary_type.value} (expected {expected.value})")

    assert all_pass, "Some classification tests failed"
    print("\nClassification test PASSED")


def test_execution_gate_decisions():
    """Test that execution gate makes correct decisions."""
    from ai.core.execution_gate import ExecutionGate
    from ai.core.query_classifier import QueryClassifier

    clf = QueryClassifier()
    gate = ExecutionGate()

    test_cases = [
        ("搜尋台北天氣", "auto_execute"),
        ("讀取 temp.txt", "auto_execute"),
        ("刪除 temp.txt", "reject"),
        ("不要搜尋", "reject"),
        ("執行這個命令", "reject"),
    ]

    print("\nExecution Gate Tests:")
    all_pass = True
    for text, expected in test_cases:
        r = clf.classify(text)
        d = gate.decide(r.primary_type.value, r.action_type, text, r.confidence, {})
        status = "PASS" if d.action == expected else "FAIL"
        if d.action != expected:
            all_pass = False
        print(f"  {status} '{text}' -> {d.action} (expected {expected}) score={d.score:.3f}")

    assert all_pass, "Some execution gate tests failed"
    print("\nExecution gate test PASSED")


def test_prompt_builder_injection():
    """Test that execution results are injected into prompts."""
    from services.llm.prompt_builder import construct_angela_prompt

    context = {
        "user_name": "Test User",
        "last_action_result": {
            "type": "web_search",
            "success": True,
            "result": "Search result: Taipei today is sunny, 28C",
            "error": None,
        },
    }

    messages = construct_angela_prompt("台北天氣如何？", context)

    system_content = messages[0]["content"]
    assert "Execution Result" in system_content, "System prompt should contain execution result block"
    assert "web_search" in system_content, "Should contain handler type"
    assert "是" in system_content, "Should contain success status"
    assert "Search result" in system_content, "Should contain result text"

    print("\nPrompt builder injection test PASSED")


def test_retrieval_from_txt_file():
    """Test retrieving content from a text file."""
    import os
    if not os.path.exists("test_retrieval.txt"):
        pytest.skip("test_retrieval.txt not found")
    with open("test_retrieval.txt", "r", encoding="utf-8") as f:
        content = f.read()

    print(f"\nFile content ({len(content)} chars):")
    print(content[:200] + "...")

    key_terms = ["Angela", "數據之海", "二進位", "符號", "沙灘"]
    found = []
    for term in key_terms:
        if term in content:
            found.append(term)

    print(f"\nFound {len(found)}/{len(key_terms)} key terms: {found}")
    assert len(found) == len(key_terms), f"Missing terms: {set(key_terms) - set(found)}"
    print("File content retrieval test PASSED")


def test_ed3n_classifier_integration():
    """Test that ED3N engine can be passed to QueryClassifier."""
    from ai.core.query_classifier import QueryClassifier

    # Test with no ed3n (backward compatible)
    clf_no_ed3n = QueryClassifier()
    assert clf_no_ed3n._ed3n is None
    r = clf_no_ed3n.classify("搜尋天氣")
    assert r.primary_type.value == "search"

    # Test with ed3n engine
    from ai.ed3n.ed3n_engine import ED3NEngine
    engine = ED3NEngine()
    engine.load_presets()

    clf_with_ed3n = QueryClassifier(ed3n_engine=engine)
    assert clf_with_ed3n._ed3n is engine
    r = clf_with_ed3n.classify("搜尋天氣")
    assert r.primary_type.value == "search"

    print("\nED3N classifier integration test PASSED")


if __name__ == "__main__":
    print("=" * 60)
    print("Angela v2 Integration Tests")
    print("=" * 60)

    test_retrieval_from_txt_file()
    test_ed3n_retrieval()
    test_query_classifier_classification()
    test_execution_gate_decisions()
    test_prompt_builder_injection()
    test_ed3n_classifier_integration()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
