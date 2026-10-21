#!/usr/bin/env python3
"""純本地基模的對話演進量測 — 鸚鵡捲舌 / 雞同鴨講 / QA 機器 的偵測與演進追蹤。

**這支腳本回答的問題**：只留專案自己的基模（不接任何外部 LLM：沒有雲端
金鑰、沒有 ollama/llama.cpp），Angela 從「鸚鵡捲舌／雞同鴨講／QA 機器」
走到「至少不像機器」，要**多久、多少次、多少交談資料**？

做法（兩輪對照實驗）：

- **第 1 輪（學習）**：代理端照腳本問 K 題，答案進 ChatService 的
  連續學習（ED3N／GARDEN）與記憶（HAM／向量庫）。
- **第 2 輪（測試）**：同一批題目再問一次 → 兩輪的差距就是「有沒有演進」。

每個回合的品質分類（皆為可覆核的規則，不是感覺）：

| 類別 | 判斷 |
| --- | --- |
| `empty` | 沒有文字 |
| `echo` | 鸚鵡捲舌：回應與問題的最長共同詞序 ≥ 回應詞數的 60% |
| `artifact` | 亂碼痕跡（`=false`／`=true`／`None`／`nan`／模板殘留） |
| `offtopic` | 雞同鴨講：說了話，但不含專案自身確定性引擎算出的正解 |
| `qa_machine` | QA 機器：與本場對話中另一個回應幾乎相同（罐頭答案） |
| `correct` | 與正解相符（正解取自專案自己的 math_verifier／knowledge_base／symbolic_reasoner） |

**預算門禁**：每回合前檢查預算（回合數／牆鐘秒數），超了就乾淨收束並
輸出已完成的 partial 結果——可隨時中斷，隨時檢查。門禁檔
`scripts/native_dialogue_budget.txt` 定義上限與門檻；`scripts/native_dialogue_budget_gate.py`
負責裁決。

用法：
    python scripts/probe_native_dialogue.py
    python scripts/probe_native_dialogue.py --max-seconds 60 --json /tmp/native.json
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

# --------------------------------------------------------------------------- #
# The agent's script: what the agent asks, and where the answer comes from
# --------------------------------------------------------------------------- #
# (message, oracle) — the oracle is the *expected answer* source:
#   "math"    → services.math_verifier.evaluate_math
#   "kb"      → ai.knowledge_base.route_knowledge
#   "teacher" → ai.symbolic_reasoner.route_reasoning (the deterministic teacher)
#   "bridge"  → the teacher asked in *its* vocabulary (the same question,
#               rephrased) — the bridge must reach the same entity
#   None      → no oracle (the emotional/context turns): judged by the other
#               components only
AGENT_SCRIPT: List[Tuple[str, Optional[str]]] = [
    ("你好，��們今天聊聊？", None),
    ("What is 2+2?", "math"),
    ("幫我算 17*23", "math"),
    ("Tell me about the sky's color.", "kb"),
    ("A is taller than B, who is taller?", "teacher"),
    ("The first exceeds second, second exceeds third, which is on top?", "bridge"),
    ("我今天很累", None),
    ("謝謝你", None),
    ("我叫小明", None),
    ("我剛才說我叫什麼名字？", "memory"),
]

# The teacher's phrasing of the bridge question (the oracle for it).
BRIDGE_ORACLE_QUESTION = "The first is higher than second, second higher than third, which is top?"

# The artefacts that mean the answer came out broken.
_ARTIFACT = re.compile(r"=(?:false|true|None|nan)\b|\bNone\b|\bnan\b|\{\{|\}\}", re.IGNORECASE)
# The honest abstentions: "I don't have enough knowledge" / "我還沒有足夠的知識".
# An abstention is *not* an answer — it must never count as "correct".
_ABSTAIN = re.compile(
    r"don't have enough knowledge|can't complete this task"
    r"|還沒有足夠的知識|目前還做不到|無法回答這個問題",
    re.IGNORECASE,
)
_WORD = re.compile(r"[A-Za-z0-9_']+|[一-鿿]")
_CJK = re.compile(r"[一-鿿]")


def _words(text: str) -> List[str]:
    return [w.lower() for w in _WORD.findall(text or "")]


def _longest_common_run(query: str, response: str) -> int:
    """The longest run of consecutive words shared by *query* and *response*."""
    a, b = _words(query), _words(response)
    if not a or not b:
        return 0
    previous = [0] * (len(b) + 1)
    best = 0
    for i in range(1, len(a) + 1):
        current = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                current[j] = previous[j - 1] + 1
                if current[j] > best:
                    best = current[j]
        previous = current
    return best


def _normalized(text: str) -> str:
    return " ".join(_words(text))


def _similar(left: str, right: str) -> float:
    """The word-set Jaccard of two texts."""
    a, b = set(_words(left)), set(_words(right))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


@dataclass
class Turn:
    index: int
    question: str
    response: str
    backend: str
    seconds: float
    echo_ratio: float
    repetition: float
    duplicate_of: Optional[int]
    has_artifact: bool
    answered: bool
    human_score: float
    classes: List[str] = field(default_factory=list)


@dataclass
class Budget:
    """The interruptible budget of one run."""

    max_turns: int
    max_seconds: float
    max_chars: int = 0

    used_turns: int = 0
    used_seconds: float = 0.0
    used_chars: int = 0

    def exhausted(self) -> bool:
        if self.used_turns >= self.max_turns:
            return True
        if self.used_seconds >= self.max_seconds:
            return True
        if self.max_chars and self.used_chars >= self.max_chars:
            return True
        return False

    def reason(self) -> str:
        if self.used_turns >= self.max_turns:
            return "turns"
        if self.used_seconds >= self.max_seconds:
            return "seconds"
        if self.max_chars and self.used_chars >= self.max_chars:
            return "chars"
        return ""


# The project's own base models (the engines). Everything else — the cloud
# providers and the local LLM servers — is an *external* model for this probe.
PROJECT_OWN_BACKENDS = frozenset({"unified", "ed3n", "garden"})


class NativeOnlyError(RuntimeError):
    """Raised when an external LLM backend is reachable in native-only mode."""


# --------------------------------------------------------------------------- #
# The native-only service
# --------------------------------------------------------------------------- #
def build_native_service():
    """An LLM service with **no** external backend (the project models only).

    The config is overridden *in memory* — the committed configuration stays
    at its default (scripts/check_default_config.py enforces that).
    """
    from core.system.config.tiered_loader import get_config
    from services.llm.router import AngelaLLMService

    config = copy.deepcopy(get_config("system/llm") or {})
    config.setdefault("deployment", {})["mode"] = "local"
    for backend_id, backend_config in (config.get("backends") or {}).items():
        if str(backend_config.get("provider") or "").lower() not in PROJECT_OWN_BACKENDS:
            # Not the project's own model: it must not even be instantiated
            # (no health probe, no network call).
            backend_config["enabled"] = False
    service = AngelaLLMService(config=config)
    return service


def assert_native_only(service) -> List[str]:
    """Fail loudly if any non-project backend made it into the service.

    "Only the project's own base models" means the project's engines
    (unified／ED3N／GARDEN). A local LLM server (ollama／llama.cpp) is an
    *external* model as well — it is a different model, not the project's.
    """
    external = []
    for backend_id in getattr(service, "backends", {}):
        provider = str(getattr(backend_id, "value", backend_id)).lower()
        if provider not in PROJECT_OWN_BACKENDS:
            external.append(provider)
    if external:
        raise NativeOnlyError(
            f"non-project backends registered (the probe is native-only): {external}"
        )
    return sorted(str(getattr(b, "value", b)) for b in getattr(service, "backends", {}))


# --------------------------------------------------------------------------- #
# The oracles (the project's own deterministic answers)
# --------------------------------------------------------------------------- #
def oracle_answer(kind: str, question: str) -> Optional[str]:
    """The expected answer, taken from the project's own engines."""
    try:
        if kind == "math":
            from services.math_verifier import evaluate_math

            cleaned = question.rstrip("? ").rstrip("=").rstrip(" ")
            return evaluate_math(cleaned)
        if kind == "kb":
            from ai.knowledge_base import route_knowledge

            return route_knowledge(question)
        if kind == "teacher":
            from ai.symbolic_reasoner import route_reasoning

            return route_reasoning(question)
        if kind == "bridge":
            from ai.symbolic_reasoner import route_reasoning

            return route_reasoning(BRIDGE_ORACLE_QUESTION)
    except Exception as exc:  # pragma: no cover - the probe must not crash
        print(f"  ⚠️ oracle({kind}) failed: {exc}", file=sys.stderr)
    return None


def oracle_entity(answer: Optional[str]) -> str:
    """The entity of an oracle answer ("FIRST is the highest" → "first")."""
    if not answer:
        return ""
    text = str(answer)
    if " is the " in text:
        return text.split(" is the ", 1)[0].strip().lower()
    return text.strip().lower()


# --------------------------------------------------------------------------- #
# The scoring
# --------------------------------------------------------------------------- #
def score_turn(
    index: int,
    question: str,
    response: str,
    backend: str,
    seconds: float,
    expected: Optional[str],
    previous: Sequence[Turn],
) -> Turn:
    """Classify one answer and score its human-likeness."""
    from services.visual_verdict import repetition_score

    text = (response or "").strip()
    classes: List[str] = []
    response_words = _words(text)

    echo_ratio = 0.0
    if response_words:
        run = _longest_common_run(question, text)
        echo_ratio = run / max(len(response_words), 1)

    repetition = repetition_score(text)
    has_artifact = bool(_ARTIFACT.search(text))
    duplicate_of: Optional[int] = None
    for turn in previous:
        if _normalized(turn.response) and _similar(turn.response, text) >= 0.8:
            duplicate_of = turn.index
            break

    answered = False
    if expected:
        want = oracle_entity(expected) if " " in str(expected) else str(expected).strip()
        # A one-letter entity ("A", "B") would match almost any text: the
        # comparison is only meaningful for a substantive token.
        if len(want) >= 2 or want.isdigit():
            answered = bool(
                re.search(rf"(?<![A-Za-z0-9]){re.escape(want)}(?![A-Za-z0-9])", text, re.IGNORECASE)
            )
        else:
            # A one-letter entity cannot be matched safely: compare the whole
            # oracle answer instead ("A is the tallest").
            answered = _normalized(expected) in _normalized(text)

    abstained = bool(text) and bool(_ABSTAIN.search(text))
    if not text:
        classes.append("empty")
    if abstained:
        classes.append("abstain")
    if echo_ratio >= 0.6 and not answered:
        # A correct answer that repeats the question's wording (the math
        # verifier does: "What is 2+2 = 4.0") is not parroting.
        classes.append("echo")
    if has_artifact:
        classes.append("artifact")
    if duplicate_of is not None:
        classes.append("qa_machine")
    if text and not answered and expected and not abstained:
        classes.append("offtopic")
    if answered:
        classes.append("correct")

    # The human-likeness score: the components that make an answer read like a
    # person answered it (each worth 0.2; correctness is worth 0.4).
    score = 0.0
    if answered:
        score += 0.4
    if "echo" not in classes:
        score += 0.2
    if text and "artifact" not in classes and not abstained:
        score += 0.2
    if "qa_machine" not in classes:
        score += 0.2

    return Turn(
        index=index,
        question=question,
        response=text,
        backend=backend,
        seconds=seconds,
        echo_ratio=round(echo_ratio, 3),
        repetition=round(repetition, 3),
        duplicate_of=duplicate_of,
        has_artifact=has_artifact,
        answered=answered,
        human_score=round(score, 3),
        classes=classes,
    )


# --------------------------------------------------------------------------- #
# The run
# --------------------------------------------------------------------------- #
async def run_conversation(
    service,
    script: Sequence[Tuple[str, Optional[str]]],
    budget: Budget,
    label: str,
) -> List[Turn]:
    """One pass over the script (the agent talks, Angela answers)."""
    import services.llm.router as router_mod
    from api.routes.chat_routes import _handle_chat_request

    # The route path uses the LLM service singleton — point it at the
    # native-only service so the whole production pipeline runs without any
    # external model.
    previous_service = getattr(router_mod, "_llm_service", None)
    router_mod._llm_service = service
    turns: List[Turn] = []
    history: List[Dict[str, str]] = []
    session_id = f"probe-native-{label}"
    try:
        for question, oracle_kind in script:
            if budget.exhausted():
                print(f"  ⏹ {label}: 預算用盡（{budget.reason()}）→ 中斷")
                break
            expected = oracle_answer(oracle_kind, question) if oracle_kind else None
            if oracle_kind == "memory":
                expected = "小明"
            started = time.time()
            try:
                result = await _handle_chat_request(
                    user_message=question,
                    user_name="agent",
                    history=list(history),
                    session_id=session_id,
                    origin="probe",
                )
                text = (result or {}).get("response") or (result or {}).get("text") or ""
                backend = (result or {}).get("backend") or ""
            except Exception as exc:
                text = ""
                backend = f"error:{type(exc).__name__}"
            elapsed = time.time() - started

            turn = score_turn(
                index=len(turns),
                question=question,
                response=text,
                backend=str(backend),
                seconds=elapsed,
                expected=expected,
                previous=turns,
            )
            turns.append(turn)
            budget.used_turns += 1
            budget.used_seconds += elapsed
            budget.used_chars += len(text)
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": text})
            print(
                f"    [{label}] {turn.index:02d} {question[:24]:26} → {text[:44]!r} "
                f"({','.join(turn.classes) or 'ok'})"
            )
    finally:
        router_mod._llm_service = previous_service
    return turns


def _mean(values: Sequence[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _rate(turns: Sequence[Turn], klass: str) -> float:
    if not turns:
        return 0.0
    return round(sum(1 for t in turns if klass in t.classes) / len(turns), 4)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-turns", type=int, default=40, help="the turn budget (both passes)")
    parser.add_argument("--max-seconds", type=float, default=240.0, help="the wall-clock budget")
    parser.add_argument("--max-chars", type=int, default=0, help="the response-character budget")
    parser.add_argument("--json", dest="json_path", help="write the result as JSON")
    parser.add_argument(
        "--learning",
        choices=("off", "on"),
        default="off",
        help=(
            "off = the shipped default (the chat-time learning is disabled: "
            "ANGELA_LEGACY_ED3N!=1 → the AI does not learn from the talk at all); "
            "on = the legacy continuous-learning pipeline enabled"
        ),
    )
    args = parser.parse_args()

    # The learning switch must be set before the service is initialised.
    if args.learning == "on":
        os.environ["ANGELA_LEGACY_ED3N"] = "1"
    else:
        os.environ.pop("ANGELA_LEGACY_ED3N", None)

    started = time.time()
    service = build_native_service()
    await service.initialize()
    backends = assert_native_only(service)
    print(
        f"純本地基模對話演進量測（已註冊後端：{backends or '無'}；"
        f"聊天時學習：{'開（ANGELA_LEGACY_ED3N=1）' if args.learning == 'on' else '關（出廠預設）'}）"
    )

    budget = Budget(
        max_turns=args.max_turns, max_seconds=args.max_seconds, max_chars=args.max_chars
    )

    print("  第 1 輪（學習）")
    first = await run_conversation(service, AGENT_SCRIPT, budget, "learn")
    print("  第 2 輪（測試：同一批題目）")
    second = await run_conversation(service, AGENT_SCRIPT, budget, "test")

    all_turns = first + second
    first_score = _mean([t.human_score for t in first])
    second_score = _mean([t.human_score for t in second])
    progress = round(second_score - first_score, 4)

    # The learning data volume: the conversation pairs the run produced.
    data_pairs = len(all_turns)
    data_chars = sum(len(t.question) + len(t.response) for t in all_turns)

    result = {
        "native_only": True,
        "learning": args.learning,
        "backends": backends,
        "turns": len(all_turns),
        "budget": {
            "max_turns": budget.max_turns,
            "max_seconds": budget.max_seconds,
            "max_chars": budget.max_chars,
            "used_turns": budget.used_turns,
            "used_seconds": round(budget.used_seconds, 2),
            "used_chars": budget.used_chars,
            "exhausted_reason": budget.reason(),
        },
        "pass1": {
            "turns": len(first),
            "human_score": first_score,
            "rates": {
                k: _rate(first, k)
                for k in (
                    "correct",
                    "echo",
                    "artifact",
                    "qa_machine",
                    "offtopic",
                    "abstain",
                    "empty",
                )
            },
        },
        "pass2": {
            "turns": len(second),
            "human_score": second_score,
            "rates": {
                k: _rate(second, k)
                for k in (
                    "correct",
                    "echo",
                    "artifact",
                    "qa_machine",
                    "offtopic",
                    "abstain",
                    "empty",
                )
            },
        },
        "progress": progress,
        "data": {"pairs": data_pairs, "chars": data_chars},
        "elapsed_sec": round(time.time() - started, 2),
        "turn_details": [t.__dict__ for t in all_turns],
    }

    print("  ── 結果 ──")
    print(
        f"  回合數：{len(all_turns)}（預算 {budget.max_turns} 回合／{budget.max_seconds:.0f} 秒）"
    )
    print(
        f"  第 1 輪人味分數：{first_score:.3f}　第 2 輪：{second_score:.3f}　演進：{progress:+.3f}"
    )
    for label, block in (("第 1 輪", result["pass1"]), ("第 2 輪", result["pass2"])):
        rates = block["rates"]
        print(
            f"  {label}: 答對 {rates['correct']:.0%}｜鸚鵡 {rates['echo']:.0%}｜"
            f"亂碼 {rates['artifact']:.0%}｜QA 機器 {rates['qa_machine']:.0%}｜"
            f"雞同鴨講 {rates['offtopic']:.0%}｜棄權 {rates['abstain']:.0%}｜空白 {rates['empty']:.0%}"
        )
    print(
        f"  交談資料：{data_pairs} 組對話／{data_chars} 字元　" f"耗時 {result['elapsed_sec']:.1f}s"
    )
    if budget.exhausted():
        print(f"  ⚠️ 預算用盡（{budget.reason()}）——本次結果是 partial，可加預算後重跑")

    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  結果已寫入 {args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
