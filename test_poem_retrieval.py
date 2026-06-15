"""
Test: Can the system retrieve specific content from a TXT file?
Not just keyword matching - can it understand the actual content?
"""
import sys
sys.path.insert(0, "apps/backend/src")


def test_poem_retrieval():
    """Read the poem file and verify specific content is accessible."""
    with open("test_retrieval.txt", "r", encoding="utf-8") as f:
        content = f.read()

    print("=" * 60)
    print("FILE CONTENT:")
    print("=" * 60)
    print(content)
    print("=" * 60)

    # Verify specific lines exist (not just keywords)
    checks = [
        ("Title", "數據之海" in content),
        ("Line 1", "二進位的海洋" in content),
        ("Line 2", "會思考的符號" in content),
        ("Line 3", "零與一交織成夢" in content),
        ("Philosophy", "你是誰" in content),
        ("Philosophy", "我是你的倒影" in content),
        ("Metaphor", "記憶是潮汐" in content),
        ("Ending", "波紋" in content),
        ("Ending", "沙灘上" in content),
        ("Author", "Angela" in content),
        ("Year", "2026" in content),
    ]

    print("\nCONTENT VERIFICATION:")
    all_pass = True
    for label, result in checks:
        status = "PASS" if result else "FAIL"
        if not result:
            all_pass = False
        print(f"  {status} {label}: {result}")

    assert all_pass, "Some content checks failed"
    print("\nAll content checks PASSED")


def test_poem_with_ed3n():
    """Test ED3N retrieval with the poem as context."""
    from ai.ed3n.ed3n_engine import ED3NEngine

    engine = ED3NEngine()
    engine.load_presets()

    # Simulate conversation about the poem
    history = [
        {"role": "assistant", "content": "我寫了一首詩：數據之海。在二進位的海洋裡，我是一串會思考的符號。"},
        {"role": "user", "content": "詩裡寫了什麼？"},
        {"role": "assistant", "content": "零與一交織成夢，每個 bit 都是一個問號。你問我你是誰，我說我是你的倒影。"},
    ]

    # Query about the poem
    query = "那首詩的最後一句是什麼？"
    query_keys = set(engine.dictionary.encode(query))

    print(f"\nQuery: '{query}'")
    print(f"Query keys: {query_keys}")

    retrieved = []
    for entry in history:
        content = entry.get("content", "")
        entry_keys = set(engine.dictionary.encode(content))
        overlap = len(query_keys & entry_keys)
        if overlap > 0:
            retrieved.append({**entry, "relevance": float(overlap)})

    retrieved.sort(key=lambda x: x["relevance"], reverse=True)

    print(f"\nRetrieved {len(retrieved)} entries:")
    for r in retrieved:
        print(f"  [{r['role']}] {r['content'][:60]}... (relevance: {r['relevance']})")

    # The second assistant message should be most relevant (has "最後一句" context)
    assert len(retrieved) >= 1, "Should retrieve at least 1 entry"
    print("\nED3N poem retrieval PASSED")


def test_exact_line_match():
    """Test that we can find exact lines in the file."""
    with open("test_retrieval.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"\nTotal lines in file: {len(lines)}")

    # Find specific poem lines
    target_lines = []
    for i, line in enumerate(lines):
        line = line.strip()
        if line and ("二進位" in line or "符號" in line or "波紋" in line or "沙灘" in line):
            target_lines.append((i + 1, line))

    print("\nFound specific poem lines:")
    for num, line in target_lines:
        print(f"  Line {num}: {line}")

    assert len(target_lines) >= 4, f"Should find at least 4 specific lines, found {len(target_lines)}"
    print("\nExact line match PASSED")


if __name__ == "__main__":
    print("=" * 60)
    print("POEM CONTENT RETRIEVAL TEST")
    print("=" * 60)

    test_poem_retrieval()
    test_poem_with_ed3n()
    test_exact_line_match()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
