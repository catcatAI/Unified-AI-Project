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

    def test_numeric_intermediate_does_not_pass(self):
        """13 appeared on the way, but the stated final answer is 12 → wrong."""
        ok, _ = tool.score_item(self._item(ground_truth=13), "3 + 10 = 13, so 12.")
        assert not ok

    def test_numeric_marked_answer_wins(self):
        ok, _ = tool.score_item(self._item(ground_truth=12), "3 + 10 = 13. Final answer: 12")
        assert ok

    def test_numeric_marker_ignores_trailing_work(self):
        ok, _ = tool.score_item(self._item(ground_truth=13), "Final answer: 13. Check: 13 - 10 = 3")
        assert ok

    def test_numeric_loose_keeps_old_rule(self):
        ok, _ = tool.score_item(self._item(ground_truth=13), "3 + 10 = 13, so 12.", "loose")
        assert ok

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

    def test_keyword_related_is_not_correct(self):
        """只沾到一個關鍵詞的句子不算答對（舊規則 any() 會放行）。"""
        item = self._item(
            metric="keyword-overlap",
            ground_truth="organ",
            gate=["organ", "pumps", "blood"],
        )
        ok, _ = tool.score_item(item, "Organ failure is a condition of the human body.")
        assert not ok

    def test_keyword_partial_concepts_is_not_correct(self):
        item = self._item(
            metric="keyword-overlap", ground_truth="carbon dioxide", gate=["carbon", "dioxide"]
        )
        ok, _ = tool.score_item(item, "Carbon is an element.")
        assert not ok

    def test_keyword_loose_mode_is_the_legacy_rule(self):
        item = self._item(
            metric="keyword-overlap",
            ground_truth="organ",
            gate=["organ", "pumps", "blood"],
        )
        assert tool.score_item(item, "Organ failure.", mode="loose")[0]
        assert not tool.score_item(item, "Organ failure.", mode="strict")[0]

    def test_keyword_gold_phrase_required(self):
        item = self._item(
            metric="keyword-overlap", ground_truth="carbon dioxide", gate=["carbon", "dioxide"]
        )
        ok, _ = tool.score_item(item, "Plants take in carbon and release dioxide.")
        assert ok

    def test_keyword_unit_label_not_required(self):
        """'100 degrees' 與 '100' 是同一答案，單位已在問句裡。"""
        item = self._item(metric="keyword-overlap", ground_truth="100 degrees", gate=["100"])
        assert tool.score_item(item, "100")[0]
        assert tool.score_item(item, "100 degrees Celsius")[0]
        assert not tool.score_item(item, "90 degrees Celsius")[0]

    def test_keyword_number_word(self):
        item = self._item(metric="keyword-overlap", ground_truth="8", gate=["8", "eight"])
        assert tool.score_item(item, "eight")[0]
        assert not tool.score_item(item, "six")[0]

    def test_exact_match(self):
        item = self._item(metric="exact-match", ground_truth="math")
        assert tool.score_item(item, "MATH")[0]
        assert not tool.score_item(item, "maths")[0]

    def test_ampersand_and_and_are_the_same_word(self):
        """'Energy & Climate' 與 'Energy and Climate' 是同一個答案。"""
        item = self._item(
            metric="keyword-overlap",
            ground_truth="Department of Energy and Climate Change",
            gate=["department", "energy", "climate"],
        )
        ok, _ = tool.score_item(
            item, "The Department of Energy & Climate Change (DECC) was a department."
        )
        assert ok


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

    @pytest.mark.asyncio
    async def test_native_knowledge_abstains_instead_of_asking_the_bus(self, monkeypatch):
        """知識層沒有答案時，benchmark 必須量到生產路徑的誠實棄權。

        以前它會退到 SNN bus 生成一段無關文字——那不是使用者會看到的回覆，
        而且讓「答錯」看起來像知識層的錯。
        """
        import ai.knowledge_base as kb_module

        monkeypatch.setattr(kb_module, "route_knowledge", lambda _q: None)
        backend = tool.NativeBackend()
        backend._ensure()

        class _ExplodingBus:
            async def route(self, *a, **kw):  # pragma: no cover - must not run
                raise AssertionError("knowledge suite must not fall back to the bus")

        monkeypatch.setattr(tool.NativeBackend, "_bus", _ExplodingBus())
        item = tool.BenchItem(
            id="t",
            q="What gas do plants absorb from the air for photosynthesis?",
            suite="knowledge",
            metric="keyword-overlap",
            ground_truth="carbon dioxide",
            gate=["carbon", "dioxide"],
        )
        assert await backend.answer(item) == ""

    @pytest.mark.asyncio
    async def test_native_bus_injects_query_type_resolver(self):
        """ModelBus.route("auto") refuses to build its own QueryClassifier, so the
        harness must inject the same owner production uses
        (services/llm/router.py::_resolve_query_type_for_bus).

        Without it every route() call raises and the knowledge suites silently
        degrade to 0% — which the CI --gate-native step then reports as a
        capability collapse rather than a wiring bug.
        """
        backend = tool.NativeBackend()
        backend._ensure()
        item = tool.BenchItem(
            id="t",
            q="What is the capital of France?",
            suite="knowledge_mc",
            metric="exact-match",
            ground_truth="Paris",
        )
        answer = await backend.answer(item)
        assert answer.strip(), "native knowledge path returned nothing"
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


# ---------------------------------------------------------------- anchor


class TestGateAnchor:
    """LOST_CORRECT 回歸錨契約：錨題本次答錯 → 退出碼 2；錨只增不減。"""

    @staticmethod
    def _native_math(details, passed: int, total: int):
        r = tool.SuiteResult(backend="native", suite="math", total=total, passed=passed)
        r.details.extend(details)
        return r

    def test_missing_anchor_returns_empty(self, tmp_path):
        assert tool.load_anchor(tmp_path / "nope.json") == {}

    def test_corrupt_anchor_returns_empty(self, tmp_path):
        p = tmp_path / "a.json"
        p.write_text("{broken", encoding="utf-8")
        assert tool.load_anchor(p) == {}

    def test_update_anchor_is_monotone(self, tmp_path):
        p = tmp_path / "anchor.json"
        anchor: dict = {}
        r1 = self._native_math(
            [
                tool.ItemResult(item_id="m1", passed=True),
                tool.ItemResult(item_id="m2", passed=True),
            ],
            passed=2,
            total=2,
        )
        assert tool.update_anchor([r1], anchor, p) == 2
        r2 = self._native_math(
            [
                tool.ItemResult(item_id="m1", passed=True),
                tool.ItemResult(item_id="m2", passed=False),
            ],
            passed=1,
            total=2,
        )
        assert tool.update_anchor([r2], anchor, p) == 0
        assert set(tool.load_anchor(p)["native/math"]) == {"m1", "m2"}

    def test_update_anchor_ignores_non_native(self, tmp_path):
        p = tmp_path / "anchor.json"
        anchor: dict = {}
        r = tool.SuiteResult(backend="echo", suite="math", total=1, passed=1)
        r.details.append(tool.ItemResult(item_id="m1", passed=True))
        assert tool.update_anchor([r], anchor, p) == 0
        assert not p.exists()

    def test_anchor_keeps_the_scoring_marker(self, tmp_path):
        """Losing _scoring on rewrite would silently disable the mismatch guard.

        load_anchor used to drop non-list keys, so the very first update
        rewrote the file without the marker and ANCHOR-SCORING MISMATCH
        could never fire again.
        """
        p = tmp_path / "anchor.json"
        anchor: dict = {}
        first = self._native_math([tool.ItemResult(item_id="m1", passed=True)], passed=1, total=1)
        assert tool.update_anchor([first], anchor, p) == 1
        loaded = tool.load_anchor(p)
        assert loaded["_scoring"] == tool.SCORING_MODE
        second = self._native_math(
            [
                tool.ItemResult(item_id="m1", passed=True),
                tool.ItemResult(item_id="m2", passed=True),
            ],
            passed=2,
            total=2,
        )
        assert tool.update_anchor([second], loaded, p) == 1
        assert tool.load_anchor(p)["_scoring"] == tool.SCORING_MODE
        assert set(tool.load_anchor(p)["native/math"]) == {"m1", "m2"}

    def test_scoring_mismatch_is_reported(self, capsys):
        anchor = {"native/math": ["m1"], "_scoring": "loose"}
        r = self._native_math([tool.ItemResult(item_id="m1", passed=True)], passed=1, total=1)
        assert tool.check_gate([r], anchor) == 0
        assert "ANCHOR-SCORING MISMATCH" in capsys.readouterr().err

    def test_lost_correct_fails_gate(self, capsys):
        anchor = {"native/math": ["m1", "m2"]}
        r = self._native_math(
            [
                tool.ItemResult(item_id="m1", passed=True),
                tool.ItemResult(item_id="m2", passed=False),
            ],
            passed=6,
            total=8,
        )
        assert tool.check_gate([r], anchor) == 2
        assert "LOST_CORRECT" in capsys.readouterr().err

    def test_anchor_item_not_run_is_not_charged(self):
        anchor = {"native/math": ["m9"]}
        r = self._native_math([tool.ItemResult(item_id="m1", passed=True)], passed=9, total=9)
        assert tool.check_gate([r], anchor) == 0

    def test_skipped_anchor_item_not_charged(self):
        anchor = {"native/math": ["m2"]}
        r = self._native_math(
            [tool.ItemResult(item_id="m2", passed=False, skipped=True)], passed=9, total=9
        )
        assert tool.check_gate([r], anchor) == 0
