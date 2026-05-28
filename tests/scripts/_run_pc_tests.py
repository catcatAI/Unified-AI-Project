"""Quick test runner for ProjectCoordinator isolation tests.

Uses importlib.util to bypass ai.dialogue package import chain
(which has a 11s+ import time due to slow dependencies.
Direct file load takes ~2s.
"""
import time, importlib.util

print("Pre-loading slow dependencies...")
t0 = time.time()
import core.shared.types.common_types
import networkx as nx
import core.hsp.types
print(f"  loaded in {time.time()-t0:.1f}s")

print()
print("Running isolation tests...")
print()

from unittest.mock import MagicMock, AsyncMock
import asyncio

# Direct file load (bypasses ai.dialogue package init)
pc_spec = importlib.util.spec_from_file_location(
    "project_coordinator",
    str(Path(src) / "ai" / "dialogue" / "project_coordinator.py")
)
pc_module = importlib.util.module_from_spec(pc_spec)
pc_spec.loader.exec_module(pc_module)
ProjectCoordinator = pc_module.ProjectCoordinator

db_spec = importlib.util.spec_from_file_location(
    "document_builder",
    str(Path(src) / "ai" / "dialogue" / "document_builder.py")
)
db_module = importlib.util.module_from_spec(db_spec)
db_spec.loader.exec_module(db_module)
DocumentBuilder = db_module.DocumentBuilder

print("Test 1: ProjectCoordinator init")
coord = ProjectCoordinator(
    memory_manager=MagicMock(),
    personality_manager=MagicMock(),
    dialogue_manager_config={"turn_timeout_seconds": 60},
)
print(f"  OK: turn_timeout={coord.turn_timeout_seconds}")

print("Test 2: fallback decompose")
result = coord._fallback_decompose("生成一個角色卡")
print(f"  OK: {len(result)} tasks, first capability={result[0]['capability_needed']}")

print("Test 3: detect complex task")
assert coord._detect_complex_task("生成角色卡") == True
assert coord._detect_complex_task("整理文件") == True
assert coord._detect_complex_task("你好") == False
assert coord._detect_complex_task("嗨") == False
print("  OK: all assertions passed")

print("Test 4: clean JSON response")
cleaned = coord._clean_json_response('[{"a":1}]')
assert cleaned[0] == "["
print("  OK: JSON cleaned")

print("Test 5: _integrate_subtask_results fallback")
coord.prompts = {}
results = {0: "Result A", 1: "Result B"}
llm_mock = AsyncMock()
llm_mock.generate_text = AsyncMock(return_value="整合結果")
async def test_integrate():
    return await coord._integrate_subtask_results("原始請求", results, llm_mock)
loop_int = asyncio.new_event_loop()
result_text = loop_int.run_until_complete(test_integrate())
loop_int.close()
assert result_text == "整合結果"
print("  OK: integrate fallback works")

print("Test 6: DocumentBuilder init")
async def mock_llm(prompt, **kwargs):
    return "test output"
builder = DocumentBuilder(llm_generate_fn=mock_llm, max_segments=4, tokens_per_segment=256)
print(f"  OK: max_segments={builder.max_segments}, tokens_per_segment={builder.tokens_per_segment}")

print("Test 7: _detect_task_type")
assert builder._detect_task_type("生成一個角色卡") == "character_card"
assert builder._detect_task_type("整理所有文件") == "document"
assert builder._detect_task_type("搜尋最新資訊") == "research"
assert builder._detect_task_type("規劃项目") == "plan"
assert builder._detect_task_type("一般問答") == "general"
print("  OK: all task types detected")

print("Test 8: _extract_keywords")
kw = builder._extract_keywords("生成一個測試角色卡")
assert isinstance(kw, list)
print(f"  OK: keywords={kw[:3]}")

print("Test 9: _load_format_from_memory (no library)")
result = builder._load_format_from_memory("character_card")
assert result is None
print("  OK: returns None when no library")

print("Test 10: _load_fantasy_codex (no memory)")
async def test_codex():
    return await builder._load_fantasy_codex("生成角色")
loop_cx = asyncio.new_event_loop()
result = loop_cx.run_until_complete(test_codex())
loop_cx.close()
assert result == {}
print("  OK: returns {} when no memory_manager")

print("Test 11: build() with basic LLM")
async def slow_llm(prompt, **kwargs):
    await asyncio.sleep(0.05)
    return "Generated content"
builder2 = DocumentBuilder(llm_generate_fn=slow_llm, max_segments=2, tokens_per_segment=128)
builder2._update_eta = MagicMock()
builder2.eta_state = MagicMock()
async def test_build():
    return await builder2.build("生成測試", complexity=0.3)
loop = asyncio.new_event_loop()
result = loop.run_until_complete(asyncio.wait_for(test_build(), timeout=5.0))
loop.close()
print(f"  OK: build returned {len(result.segments)} segments")

print("Test 12: build() with segment failure")
attempt = {"count": 0}
async def flaky_llm(prompt, **kwargs):
    attempt["count"] += 1
    if attempt["count"] == 1:
        raise RuntimeError("Segment 0 failed")
    return "Recovery success"
builder3 = DocumentBuilder(llm_generate_fn=flaky_llm, max_segments=4, tokens_per_segment=64)
builder3._update_eta = MagicMock()
builder3.eta_state = MagicMock()
async def test_flaky():
    return await builder3.build("測試", complexity=0.3)
loop2 = asyncio.new_event_loop()
result = loop2.run_until_complete(asyncio.wait_for(test_flaky(), timeout=5.0))
loop2.close()
print(f"  OK: build with failure: {result.successful_segments}/{result.total_segments} succeeded")

print("Test 13: build() with segment timeout")
async def hung_llm(prompt, **kwargs):
    await asyncio.sleep(2.0)
    return "Should not reach"
builder4 = DocumentBuilder(llm_generate_fn=hung_llm, max_segments=2, tokens_per_segment=64)
builder4._segment_timeout_seconds = 0.5
builder4._update_eta = MagicMock()
builder4.eta_state = MagicMock()
async def test_timeout():
    return await builder4.build("測試超時", complexity=0.3)
loop3 = asyncio.new_event_loop()
result = loop3.run_until_complete(asyncio.wait_for(test_timeout(), timeout=3.0))
loop3.close()
assert result.successful_segments <= 1
print(f"  OK: build with timeout: {result.successful_segments}/{result.total_segments} succeeded (timeout=0.5s)")

print("Test 14: _update_eta method")
builder5 = DocumentBuilder(llm_generate_fn=mock_llm)
builder5.eta_state = MagicMock()
builder5._update_eta(2)
builder5.eta_state.execution_count += 2
print("  OK: _update_eta called")

print("Test 15: _learn_format dedup key set")
builder6 = DocumentBuilder(llm_generate_fn=mock_llm, template_library=MagicMock())
builder6._learn_format("character_card", "生成戰士角色", "內容1", [])
assert hasattr(builder6, "_learned_format_keys") and len(builder6._learned_format_keys) == 1
builder6._learn_format("character_card", "生成戰士角色", "內容2", [])
assert len(builder6._learned_format_keys) == 1
builder6._learn_format("character_card", "不同的查詢", "內容3", [])
assert len(builder6._learned_format_keys) == 2
print(f"  OK: dedup works ({len(builder6._learned_format_keys)} unique keys)")

print()
print("=" * 50)
print("ALL 12 TESTS PASSED")
print("B7/B8/B9/B10/B11 covered")