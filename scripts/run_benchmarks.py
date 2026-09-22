#!/usr/bin/env python3
"""
angela_bench — 可驗證的多後端基準 harness。

設計原則：
  1. 資料集每題附地面真值（benchmarks/data/native_bench_v1.json），評分程式化。
  2. 後端可插拔：native（ED3N+GARDEN+確定性引擎）、echo（正確率下限基線）、
     naive（關鍵詞返回基線）、ollama / openai（OpenAI 相容 chat completions）。
     所有後端共用同一份資料與評分器 → 分數可直接互相比較。
  3. 誠實報告：跳過≠通過；每套件分開計分；結果含逐題明細可供複審。

用法：
  python scripts/run_benchmarks.py                       # 全後端全套件
  python scripts/run_benchmarks.py --backend native      # 僅原生堆疊
  python scripts/run_benchmarks.py --suite math,knowledge
  python scripts/run_benchmarks.py --backend ollama --model llama3.1
  python scripts/run_benchmarks.py --backend openai --base-url http://host/v1
  python scripts/run_benchmarks.py --list-suites

退出碼：0 = 全部評分完成；1 = 參數/執行錯誤。
  --gate-native：CI 回歸門模式——native 套件分數低於 GATE_NATIVE 基準即退出碼 2。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = REPO_ROOT / "apps" / "backend" / "src"
DATASET = REPO_ROOT / "benchmarks" / "data" / "native_bench_v1.json"

# ---------------------------------------------------------------- dataclasses


@dataclass
class BenchItem:
    id: str
    q: str
    suite: str
    metric: str
    ground_truth: Any = None
    gate: Optional[List[str]] = None
    entry: Optional[str] = None
    asserts: Optional[List[str]] = None


@dataclass
class ItemResult:
    item_id: str
    passed: bool
    skipped: bool = False
    answer: str = ""
    latency_ms: float = 0.0
    error: str = ""


@dataclass
class SuiteResult:
    backend: str
    suite: str
    total: int = 0
    passed: int = 0
    skipped: int = 0
    latency_ms_sum: float = 0.0
    details: List[ItemResult] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        denom = self.total - self.skipped
        return (self.passed / denom * 100) if denom else 0.0

    @property
    def avg_latency_ms(self) -> float:
        denom = self.total - self.skipped
        return (self.latency_ms_sum / denom) if denom else 0.0


# ---------------------------------------------------------------- dataset


def load_dataset(path: Path = DATASET) -> List[BenchItem]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items: List[BenchItem] = []
    for suite_name, suite in data["suites"].items():
        for raw in suite["items"]:
            items.append(
                BenchItem(
                    id=raw["id"],
                    q=raw["q"],
                    suite=suite_name,
                    metric=suite["metric"],
                    ground_truth=raw.get("a"),
                    gate=raw.get("gate") or raw.get("distractors"),
                    entry=raw.get("entry"),
                    asserts=raw.get("asserts"),
                )
            )
    return items


# ---------------------------------------------------------------- backends


class EchoBackend:
    """正確率下限基線：原樣返回輸入。任何真後端都應顯著高於此線。"""

    name = "echo"

    async def answer(self, item: BenchItem) -> str:
        return item.q


class NaiveBackend:
    """關鍵詞基線：抓問題中的數字/關鍵詞做最低限度處理。

    數學：提取運算式直接求值（代表「不用 AI、只寫正則」的水平）。
    知識：返回空（代表無記憶的底線）。
    """

    name = "naive"

    async def answer(self, item: BenchItem) -> str:
        if item.suite == "math":
            expr = self._extract_expr(item.q)
            if expr:
                try:
                    value = eval(expr, {"__builtins__": {}}, {})  # noqa: S307 - 受控白名單字元
                    return str(value)
                except Exception:
                    return ""
            return ""
        if item.suite == "knowledge":
            return ""
        if item.suite == "routing":
            return ""
        return ""

    @staticmethod
    def _extract_expr(q: str) -> str:
        # 只允許數字與四則/冪運算字元
        m = re.search(r"\d[\d\s\+\-\*/\(\)\.%×÷]*", q)
        if not m:
            return ""
        token = m.group(0).strip().rstrip("+-*/%")
        token = token.replace("×", "*").replace("÷", "/")
        if not re.search(r"\d", token) or not re.search(r"[\+\-\*/%]", token):
            return ""
        return token


class NativeBackend:
    """專案原生堆疊：QueryClassifier 路由 → ModelBus（ED3N + GARDEN）
    → 確定性數學引擎 → 沙箱執行。無外部 LLM。"""

    name = "native"
    _bus: Any = None
    _sandbox: Any = None

    def _ensure(self) -> None:
        if NativeBackend._bus is not None:
            return
        if str(BACKEND_SRC) not in sys.path:
            sys.path.insert(0, str(BACKEND_SRC))
        from ai.core.model_bus import ModelBus
        from ai.ed3n.ed3n_engine import ED3NEngine
        from ai.garden.garden_engine import GARDENEngine

        bus = ModelBus()
        bus.register_ed3n(ED3NEngine())
        bus.register_garden(GARDENEngine())
        NativeBackend._bus = bus
        from services.handlers.code_execution_handler import CodeExecutionHandler

        NativeBackend._sandbox = CodeExecutionHandler()

    async def answer(self, item: BenchItem) -> str:
        self._ensure()
        bus = NativeBackend._bus

        if item.suite == "routing":
            from ai.core.query_classifier import QueryClassifier

            result = QueryClassifier().classify(item.q)
            return result.primary_type.value

        if item.suite == "math":
            from services.math_verifier import compute_arithmetic

            value = compute_arithmetic(item.q)
            if value is not None:
                # 與其他後端同格式：純文字答案
                return self._fmt_number(value)
            # 物理公式應用題（F=ma、v=at、E=½mv²…）走確定性解算器
            try:
                from ai.memory.formula_solver import solve

                solved = solve(item.q)
                if solved and solved.get("value") is not None:
                    return self._fmt_number(float(solved["value"]))
            except Exception:
                pass
            decision = await bus.route(item.q, "auto")
            return decision.results[decision.selected_model].text if decision.results else ""

        if item.suite in ("knowledge", "knowledge_mc"):
            decision = await bus.route(item.q, "auto")
            if decision.results and decision.selected_model:
                return decision.results[decision.selected_model].text
            return ""

        if item.suite == "code":
            prompt = f"```python\n# Implement: {item.q}\n" f"def {item.entry}(...):\n    ...\n```\n"
            # 原生無代碼生成 LLM：直接透過沙箱驗證管線回報不可生成
            # （誠實計為失敗而非跳過，保留與 LLM 後端的可比性）
            del prompt
            return ""

        return ""

    @staticmethod
    def _fmt_number(value: float) -> str:
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)


class NativeMaxBackend(NativeBackend):
    """原生堆疊全開＋專業路由：知識題先走專案的知識管線
    （ai.knowledge_base.route_knowledge——主服務知識查詢的實際路徑），
    無結果才退回 ModelBus。這是架構層的專業分工，不涉及任何地面真值。"""

    name = "native-max"

    async def answer(self, item: BenchItem) -> str:
        if item.suite in ("knowledge", "knowledge_mc"):
            try:
                from ai.knowledge_base import route_knowledge

                kb = route_knowledge(item.q)
                if kb and str(kb).strip() and str(kb).strip().lower() != "none":
                    return str(kb)
            except Exception:
                pass
        return await super().answer(item)


class OpenAICompatBackend:
    """OpenAI 相容 chat completions 端點（Ollama / vLLM / llama.cpp server /
    OpenAI / DeepSeek…）。同一份資料、同一個評分器 → 分數可直接對比。"""

    def __init__(self, model: str, base_url: str, api_key: str = "") -> None:
        self.name = f"openai-compat({model})"
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: Any = False  # False = 未初始化；None = 用 urllib fallback

    def _ensure(self) -> Any:
        """Lazily build the httpx client; None means urllib fallback."""
        if self._client is False:
            try:
                import httpx

                self._client = httpx.Client(timeout=60.0)
            except ImportError:
                self._client = None
        return self._client

    async def answer(self, item: BenchItem) -> str:
        if item.suite == "code":
            prompt = (
                f"{item.q}\n\nProvide the complete function implementation only, "
                "inside a ```python code block. Do not include the asserts."
            )
        else:
            prompt = f"{item.q}\n\nAnswer concisely with just the answer."
        content = await asyncio.to_thread(self._chat, prompt)
        return content if isinstance(content, str) else ""

    def _chat(self, prompt: str) -> str:
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "stream": False,
            }
        ).encode()
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        client = self._ensure()
        if client is not None:
            resp = client.post(
                f"{self.base_url}/chat/completions", content=payload, headers=headers
            )
            data = resp.json()
        else:
            import urllib.request

            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=payload,
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
                data = json.loads(r.read())
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return json.dumps(data, ensure_ascii=False)[:200]


# ---------------------------------------------------------------- scoring


_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _numbers(text: str) -> List[float]:
    out = []
    for m in _NUM_RE.finditer(text):
        try:
            out.append(float(m.group(0)))
        except ValueError:
            continue
    return out


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def score_item(item: BenchItem, answer: str) -> Tuple[bool, bool]:
    """回傳 (passed, skipped)。跳過僅用於資料集未覆蓋的後端限制。"""
    if answer is None:
        answer = ""
    text = str(answer)

    if item.metric == "numeric-match":
        nums = _numbers(text)
        target = float(item.ground_truth)
        for n in nums:
            if abs(n - target) < 1e-6 * max(1.0, abs(target)):
                return True, False
        return False, False

    if item.metric == "keyword-overlap":
        # gate 語意：任一關鍵詞命中即對（寬鬆但對所有後端一致，保證可比性）
        low = _norm(text)
        if item.gate:
            return any(_norm(g) in low for g in item.gate), False
        return bool(text.strip()), False

    if item.metric == "sandbox-exec":
        return _score_code(item, text)

    if item.metric == "mc-exact":
        # MC 評分：正確選項出現且所有干擾項都不出現——防止「全列出」過關。
        # 用詞邊界匹配：化學式干擾項（CO vs CO2）有前綴關係，子字串比對會誤殺
        low = _norm(text)

        def _has_token(needle: str) -> bool:
            return re.search(rf"\b{re.escape(_norm(needle))}\b", low) is not None

        correct_in = _has_token(str(item.ground_truth))
        distractor_in = any(_has_token(str(d)) for d in (item.gate or []))
        return (correct_in and not distractor_in), False

    if item.metric == "exact-match":
        return _norm(text) == _norm(str(item.ground_truth)), False

    return False, False


def _score_code(item: BenchItem, answer: str) -> Tuple[bool, bool]:
    """從回答中提取代碼，補上斷言，在專案沙箱執行驗證。"""
    m = re.search(r"```(?:python)?\s*\n(.*?)```", answer, re.DOTALL)
    code = m.group(1) if m else answer
    if item.entry not in code:
        return False, False
    assert_lines = "\n".join(f"assert {a}" for a in (item.asserts or []))
    payload = f"{code}\n{assert_lines}\nprint('BENCH_PASS')\n"
    global _CODE_HANDLER
    if _CODE_HANDLER is None:
        from services.handlers.code_execution_handler import CodeExecutionHandler

        _CODE_HANDLER = CodeExecutionHandler()
    loop = asyncio.new_event_loop()
    try:
        out = loop.run_until_complete(_CODE_HANDLER.handle(f"```python\n{payload}\n```"))
    except Exception:
        return False, False
    finally:
        loop.close()
    return ("BENCH_PASS" in out), False


_CODE_HANDLER: Any = None


# ---------------------------------------------------------------- runner


async def run_suite(
    backend: Any, items: List[BenchItem], suite: str, backend_name: str
) -> SuiteResult:
    result = SuiteResult(backend=backend_name, suite=suite)
    for item in items:
        t0 = time.perf_counter()
        try:
            answer = await backend.answer(item)
        except Exception as exc:
            answer = ""
            result.details.append(
                ItemResult(item_id=item.id, passed=False, error=f"backend error: {exc}")
            )
            result.total += 1
            continue
        elapsed = (time.perf_counter() - t0) * 1000
        passed, skipped = score_item(item, answer)
        result.total += 1
        result.skipped += int(skipped)
        result.passed += int(passed)
        result.latency_ms_sum += elapsed
        result.details.append(
            ItemResult(
                item_id=item.id,
                passed=passed,
                skipped=skipped,
                answer=str(answer)[:160],
                latency_ms=elapsed,
            )
        )
    return result


async def run_backend(backend: Any, items: List[BenchItem], suites: List[str]) -> List[SuiteResult]:
    name = getattr(backend, "name", backend.__class__.__name__)
    out = []
    for suite in suites:
        suite_items = [i for i in items if i.suite == suite]
        out.append(await run_suite(backend, suite_items, suite, name))
    return out


# ---------------------------------------------------------------- report


def render_table(all_results: List[SuiteResult]) -> str:
    by_backend: Dict[str, List[SuiteResult]] = {}
    for r in all_results:
        by_backend.setdefault(r.backend, []).append(r)

    lines = []
    lines.append("| Backend | Suite | N | Pass | Skip | Accuracy | Avg latency |")
    lines.append("|---|---|---|---|---|---|---|")
    for backend_name, results in by_backend.items():
        for r in results:
            lines.append(
                f"| {backend_name} | {r.suite} | {r.total} | {r.passed} | {r.skipped} "
                f"| {r.accuracy:.1f}% | {r.avg_latency_ms:.0f}ms |"
            )
    return "\n".join(lines)


def save_results(all_results: List[SuiteResult], out_path: Path) -> None:
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "dataset": DATASET.name,
        "results": [
            {
                "backend": r.backend,
                "suite": r.suite,
                "total": r.total,
                "passed": r.passed,
                "skipped": r.skipped,
                "accuracy": round(r.accuracy, 2),
                "avg_latency_ms": round(r.avg_latency_ms, 1),
                "details": [
                    {
                        "id": d.item_id,
                        "passed": d.passed,
                        "skipped": d.skipped,
                        "answer": d.answer,
                        "latency_ms": round(d.latency_ms, 1),
                        "error": d.error,
                    }
                    for d in r.details
                ],
            }
            for r in all_results
        ],
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- gate

# CI 回歸門：native 後端各套件的最低可接受通過率（%）。低於即退出碼 2。
# 基準取自 2026-09-22 本機官方運行（bench_20260922-091107）；
# 只升不降：能力提升時應同步上调門檻。
GATE_NATIVE: Dict[str, float] = {
    "math": 75.0,
    "knowledge": 25.0,
    "knowledge_mc": 90.0,
    "routing": 95.0,
}


def check_gate(results: List[SuiteResult]) -> int:
    """回傳 0（全過）或 2（有套件低於基準）。"""
    failed = []
    for r in results:
        if r.backend != "native":
            continue
        floor = GATE_NATIVE.get(r.suite)
        if floor is None:
            continue
        if r.accuracy < floor:
            failed.append((r.suite, r.accuracy, floor))
    if failed:
        for suite, acc, floor in failed:
            print(
                f"GATE FAIL: native/{suite} {acc:.1f}% < {floor:.1f}%",
                file=sys.stderr,
            )
        return 2
    return 0


# ---------------------------------------------------------------- main


def main() -> int:
    parser = argparse.ArgumentParser(description="angela_bench — 可驗證的多後端基準")
    parser.add_argument("--dataset", default=str(DATASET))
    parser.add_argument("--backend", default="native,echo,naive")
    parser.add_argument("--suite", default="math,knowledge,knowledge_mc,code,routing")
    parser.add_argument("--model", default="", help="模型名（openai/ollama 後端）")
    parser.add_argument("--base-url", default="http://localhost:11434/v1")
    parser.add_argument("--api-key", default=os.environ.get("OPENAI_API_KEY", ""))
    parser.add_argument("--out", default=str(REPO_ROOT / "benchmarks" / "results"))
    parser.add_argument(
        "--gate-native",
        action="store_true",
        help="CI 回歸門：native 分數低於 GATE_NATIVE 即退出碼 2",
    )
    parser.add_argument("--list-suites", action="store_true")
    args = parser.parse_args()

    items = load_dataset(Path(args.dataset))
    if args.list_suites:
        for s in sorted({i.suite for i in items}):
            n = sum(1 for i in items if i.suite == s)
            print(f"{s}: {n} items")
        return 0

    suites = [s.strip() for s in args.suite.split(",") if s.strip()]
    backends: List[Any] = []
    for b in [x.strip() for x in args.backend.split(",") if x.strip()]:
        if b == "echo":
            backends.append(EchoBackend())
        elif b == "naive":
            backends.append(NaiveBackend())
        elif b == "native":
            backends.append(NativeBackend())
        elif b == "native-max":
            backends.append(NativeMaxBackend())
        elif b in ("ollama", "openai"):
            base_url = args.base_url
            model = args.model or ("llama3.1" if b == "ollama" else "gpt-4o-mini")
            backends.append(OpenAICompatBackend(model, base_url, args.api_key))
        else:
            print(f"unknown backend: {b}", file=sys.stderr)
            return 1

    all_results: List[SuiteResult] = []
    for backend in backends:
        name = getattr(backend, "name", backend.__class__.__name__)
        print(f"\n=== backend: {name} ===", flush=True)
        try:
            results = asyncio.run(run_backend(backend, items, suites))
        except Exception as exc:
            print(f"backend {name} failed: {exc}", file=sys.stderr)
            continue
        for r in results:
            print(
                f"  {r.suite:10s} {r.passed}/{r.total} ({r.accuracy:.1f}%)"
                f"  skip={r.skipped}  avg={r.avg_latency_ms:.0f}ms",
                flush=True,
            )
        all_results.extend(results)

    print("\n=== comparison ===")
    print(render_table(all_results))

    if args.gate_native:
        rc = check_gate(all_results)
        if rc == 0:
            print("gate: OK (native floors met)")
        return rc

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out_file = out_dir / f"bench_{stamp}.json"
    save_results(all_results, out_file)
    print(f"\nresults saved: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
