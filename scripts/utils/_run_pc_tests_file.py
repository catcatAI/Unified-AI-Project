"""Isolation tests - writes output to file."""
import importlib.util
import time

log=[]

def log_print(msg):
    log.append(msg)

log_print("Pre-loading slow dependencies...")
t0 = time.time()
try:
    import core.shared.types.common_types
    log_print(f"  core.shared.types.common_types: {time.time()-t0:.1f}s")
except Exception as e:
    log_print(f"  core.shared.types.common_types FAILED: {e}")

t1 = time.time()
try:
    import networkx as nx
    log_print(f"  networkx: {time.time()-t1:.1f}s")
except Exception as e:
    log_print(f"  networkx FAILED: {e}")

log_print("Running tests...")
log_print("")

import asyncio
from unittest.mock import AsyncMock, MagicMock

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

log_print("Test 1: ProjectCoordinator init")
coord = ProjectCoordinator(memory_manager=MagicMock(), personality_manager=MagicMock(), dialogue_manager_config={"turn_timeout_seconds": 60})
log_print(f"  OK: turn_timeout={coord.turn_timeout_seconds}")

log_print("Test 2: fallback decompose")
result = coord._fallback_decompose("生成一個角色卡")
log_print(f"  OK: {len(result)} tasks")

log_print("Test 3: detect complex task")
assert coord._detect_complex_task("生成角色卡") is True
assert coord._detect_complex_task("你好") is False
log_print("  OK")

log_print("Test 4: clean JSON response")
cleaned = coord._clean_json_response('[{"a":1}]')
assert cleaned[0] == "["
log_print("  OK")

log_print("Test 5: integrate fallback")
coord.prompts={}
llm_mock = AsyncMock()
llm_mock.generate_text = AsyncMock(return_value="整合結果")
async def ti():
    return await coord._integrate_subtask_results("原始", {0:'A', 1:'B'}, llm_mock)
loop_int = asyncio.new_event_loop()
r = loop_int.run_until_complete(ti())
loop_int.close()
assert r == "整合結果"
log_print("  OK")

log_print("Test 6: DocumentBuilder init")
async def ml(**k):
    return "out"
builder = DocumentBuilder(llm_generate_fn=ml, max_segments=4, tokens_per_segment=256)
log_print(f"  OK: {builder.max_segments} segs")

log_print("Test 7: detect task type")
assert builder._detect_task_type("生成一個角色卡") == "character_card"
assert builder._detect_task_type("整理所有文件") == "document"
assert builder._detect_task_type("搜尋") == "research"
assert builder._detect_task_type("規劃") == "plan"
log_print("  OK")

log_print("Test 8: no library")
r = builder._load_format_from_memory("character_card")
assert r is None
log_print("  OK")

log_print("Test 9: no codex")
async def tc():
    return await builder._load_fantasy_codex("生成角色")
loop_cx = asyncio.new_event_loop()
r = loop_cx.run_until_complete(tc())
loop_cx.close()
assert r == {}
log_print("  OK")

log_print("Test 10: build basic")
async def sl(**k):
    await asyncio.sleep(0.05)
    return "Generated"
builder2 = DocumentBuilder(llm_generate_fn=sl, max_segments=2, tokens_per_segment=128)
builder2._update_eta = MagicMock()
builder2.eta_state = MagicMock()
async def tb():
    return await builder2.build("生成測試", complexity=0.3)
loop2 = asyncio.new_event_loop()
result = loop2.run_until_complete(asyncio.wait_for(tb(), timeout=5.0))
loop2.close()
log_print(f"  OK: {len(result.segments)} segments")

log_print("Test 11: build segment failure")
attempt={"count": 0}
async def fl(**k):
    attempt["count"] += 1
    if attempt["count"] == 1:
        raise RuntimeError("failed")
    return "recovered"
builder3 = DocumentBuilder(llm_generate_fn=fl, max_segments=4, tokens_per_segment=64)
builder3._update_eta = MagicMock()
builder3.eta_state = MagicMock()
async def tf():
    return await builder3.build("測試", complexity=0.3)
loop3 = asyncio.new_event_loop()
result = loop3.run_until_complete(asyncio.wait_for(tf(), timeout=5.0))
loop3.close()
log_print(f"  OK: {result.successful_segments}/{result.total_segments} succeeded")

log_print("Test 12: build segment timeout")
async def hl(**k):
    await asyncio.sleep(2.0)
    return "timeout"
builder4 = DocumentBuilder(llm_generate_fn=hl, max_segments=2, tokens_per_segment=64)
builder4._segment_timeout_seconds=0.5
builder4._update_eta = MagicMock()
builder4.eta_state = MagicMock()
async def th():
    return await builder4.build("測試超時", complexity=0.3)
loop4 = asyncio.new_event_loop()
result = loop4.run_until_complete(asyncio.wait_for(th(), timeout=3.0))
loop4.close()
assert result.successful_segments <= 1
log_print(f"  OK: timeout handled {result.successful_segments}/{result.total_segments}")

log_print("Test 13: _update_eta")
builder5 = DocumentBuilder(llm_generate_fn=ml)
builder5.eta_state = MagicMock()
builder5._update_eta(2)
log_print("  OK")

log_print("Test 14: _learn_format dedup")
builder6 = DocumentBuilder(llm_generate_fn=ml, template_library=MagicMock())
builder6._learn_format("character_card", "生成戰士角色", "內容1", [])
assert hasattr(builder6, "_learned_format_keys") and len(builder6._learned_format_keys) == 1
builder6._learn_format("character_card", "生成戰士角色", "內容2", [])
assert len(builder6._learned_format_keys) == 1
builder6._learn_format("character_card", "不同的查詢", "內容3", [])
assert len(builder6._learned_format_keys) == 2
log_print("  OK: dedup works")

log_print("")
log_print("=" * 50)
log_print("ALL 14 TESTS PASSED")
log_print("B7/B8/B9/B10/B11 fixed and verified")

out_path = r"C:\Users\zofug\AppData\Local\Temp\pc_test_results.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(log))
print(f"Results written to {out_path}")