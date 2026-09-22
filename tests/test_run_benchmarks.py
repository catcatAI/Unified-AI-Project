# -*- coding: utf-8 -*-
"""run_benchmarks.py 測試 — 資料集完整性、評分器正確性、後端行為與可比性契約。"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = REPO_ROOT / "scripts" / "run_benchmarks.py"
DATASET = REPO_ROOT / "benchmarks" / "data" / "native_bench_v1.json"


def load_tool():
    spec = importlib.util.spec_from_file_location("run_benchmarks", TOOL_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclasses 需要 __module__ 可解析
    spec.loader.exec_module(mod)
    return mod


tool = load_tool()


# ---------------------------------------------------------------- dataset


class TestDataset:
    def test_loads(self):
        items = tool.load_dataset()
        assert len(items) >= 60

    def test_every_item_has_ground_truth(self):
        for item in tool.load_dataset():
            if item.metric == "sandbox-exec":
                assert item.entry and item.asserts, item.id
            else:
                assert item.ground_truth is not None, item.id
            if item.metric == "keyword-overlap":
                assert item.gate, f"{item.id} missing gate keywords"

    def test_all_backends_supported(self):
        items = tool.load_dataset()
        assert {i.suite for i in items} == {
            "math",
            "knowledge",
            "knowledge_mc",
            "code",
            "routing",
        }


# ---------------------------------------------------------------- scoring


class TestScoring:
    def _item(self, **kw):
        defaults = dict(id="t", q="q", suite="s", metric="numeric-match", ground_truth=42)
        defaults.update(kw)
        return tool.BenchItem(**defaults)

    def test_numeric_exact(self):
        ok, _ = tool.score_item(self._item(), "The answer is 42.")
        assert ok

    def test_numeric_tolerance(self):
        ok, _ = tool.score_item(self._item(ground_truth=0.1), "0.10000001")
        assert ok

    def test_numeric_wrong(self):
        ok, _ = tool.score_item(self._item(), "43")
        assert not ok

    def test_numeric_no_substring(self):
        """142 不應該算成 42 對。"""
        ok, _ = tool.score_item(self._item(), "142")
        assert not ok

    def test_keyword_gate(self):
        item = self._item(
            metric="keyword-overlap", ground_truth="carbon dioxide", gate=["carbon", "dioxide"]
        )
        ok, _ = tool.score_item(item, "Plants absorb carbon dioxide.")
        assert ok

    def test_keyword_miss(self):
        item = self._item(
            metric="keyword-overlap", ground_truth="carbon dioxide", gate=["carbon", "dioxide"]
        )
        ok, _ = tool.score_item(item, "oxygen")
        assert not ok

    def test_exact_match(self):
        item = self._item(metric="exact-match", ground_truth="math")
        assert tool.score_item(item, "MATH")[0]
        assert not tool.score_item(item, "maths")[0]


# ---------------------------------------------------------------- backends


class TestBackends:
    @pytest.mark.asyncio
    async def test_echo_baseline_fails_math(self):
        item = tool.BenchItem(
            id="t", q="What is 2+2?", suite="math", metric="numeric-match", ground_truth=4
        )
        ok, _ = tool.score_item(item, await tool.EchoBackend().answer(item))
        assert not ok

    @pytest.mark.asyncio
    async def test_naive_evals_pure_expr(self):
        item = tool.BenchItem(
            id="t", q="What is 2 ** 10?", suite="math", metric="numeric-match", ground_truth=1024
        )
        answer = await tool.NaiveBackend().answer(item)
        ok, _ = tool.score_item(item, answer)
        assert ok

    @pytest.mark.asyncio
    async def test_native_answers_math_deterministically(self):
        backend = tool.NativeBackend()
        backend._ensure()
        item = tool.BenchItem(
            id="t",
            q="What is 123 * 456 - 1000?",
            suite="math",
            metric="numeric-match",
            ground_truth=55088,
        )
        answer = await backend.answer(item)
        ok, _ = tool.score_item(item, answer)
        assert ok

    @pytest.mark.asyncio
    async def test_native_routing_uses_classifier(self):
        backend = tool.NativeBackend()
        backend._ensure()
        item = tool.BenchItem(
            id="t", q="嗨，早安！", suite="routing", metric="exact-match", ground_truth="greeting"
        )
        answer = await backend.answer(item)
        ok, _ = tool.score_item(item, answer)
        assert ok


# ---------------------------------------------------------------- code scoring


class TestCodeScoring:
    def test_correct_implementation_passes(self):
        item = tool.BenchItem(
            id="t",
            q="q",
            suite="code",
            metric="sandbox-exec",
            entry="add",
            asserts=["add(1, 2) == 3", "add(-1, 1) == 0"],
        )
        answer = "```python\ndef add(a, b):\n    return a + b\n```"
        ok, _ = tool._score_code(item, answer)
        assert ok

    def test_wrong_implementation_fails(self):
        item = tool.BenchItem(
            id="t",
            q="q",
            suite="code",
            metric="sandbox-exec",
            entry="add",
            asserts=["add(1, 2) == 3"],
        )
        answer = "```python\ndef add(a, b):\n    return a - b\n```"
        ok, _ = tool._score_code(item, answer)
        assert not ok

    def test_missing_entry_fails(self):
        item = tool.BenchItem(
            id="t",
            q="q",
            suite="code",
            metric="sandbox-exec",
            entry="add",
            asserts=["add(1, 2) == 3"],
        )
        ok, _ = tool._score_code(item, "```python\nprint('hi')\n```")
        assert not ok


# ---------------------------------------------------------------- comparability


class TestComparability:
    def test_all_backends_share_scorer(self):
        """同一題、同一回答，任何後端都必須得到同一判定。"""
        items = {i.id: i for i in tool.load_dataset()}
        item = items["math-010"]  # 17 * 24 = 408
        for backend_cls in (tool.EchoBackend, tool.NaiveBackend):
            b = backend_cls()
            del b
            ok, skipped = tool.score_item(item, "408")
            assert ok and not skipped

    def test_report_table_renders(self):
        r = tool.SuiteResult(backend="b", suite="math", total=2, passed=1)
        r.details.append(tool.ItemResult(item_id="a", passed=True))
        r.details.append(tool.ItemResult(item_id="b", passed=False))
        table = tool.render_table([r])
        assert "| b | math | 2 | 1 | 0 |" in table

    def test_results_json_roundtrip(self, tmp_path):
        r = tool.SuiteResult(backend="b", suite="math", total=1, passed=1)
        r.details.append(tool.ItemResult(item_id="a", passed=True, answer="x"))
        out = tmp_path / "r.json"
        tool.save_results([r], out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["results"][0]["accuracy"] == 100.0


# ---------------------------------------------------------------- gate


class TestGate:
    """--gate-native CI 回歸門契約：低於 GATE_NATIVE 基準 → 退出碼 2。"""

    def test_below_floor_fails(self):
        r = tool.SuiteResult(backend="native", suite="math", total=10, passed=0)
        assert tool.check_gate([r]) == 2

    def test_above_floor_passes(self):
        r = tool.SuiteResult(backend="native", suite="math", total=10, passed=9)
        assert tool.check_gate([r]) == 0

    def test_only_native_is_gated(self):
        r = tool.SuiteResult(backend="echo", suite="math", total=10, passed=0)
        assert tool.check_gate([r]) == 0

    def test_unknown_suite_not_gated(self):
        r = tool.SuiteResult(backend="native", suite="code", total=10, passed=0)
        assert tool.check_gate([r]) == 0

    def test_gate_floors_are_monotone_baseline(self):
        # 門檻只升不降：正式運行基準（2026-09-22）是下限
        assert tool.GATE_NATIVE["math"] >= 75.0
        assert tool.GATE_NATIVE["knowledge_mc"] >= 90.0
        assert tool.GATE_NATIVE["routing"] >= 95.0
        assert tool.GATE_NATIVE["knowledge"] >= 25.0
