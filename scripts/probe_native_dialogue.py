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
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

# The probe is a sandbox: its conversations must not land in the user's real
# memory (HAM／vector store). ANGELA_DATA_DIR redirects the data dir
# (path_config.DATA_DIR) — it is set in main(), *before* any backend module is
# imported (importing this module must not change the process environment).
SANDBOX_DATA_DIR = Path(
    os.environ.get("ANGELA_PROBE_DATA_DIR") or (REPO_ROOT / "data" / "probe_native_dialogue")
)


def isolate_data_dir() -> Path:
    """Point the data dir at the sandbox (call before the backend imports)."""
    os.environ["ANGELA_DATA_DIR"] = str(SANDBOX_DATA_DIR)
    return SANDBOX_DATA_DIR


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
# --------------------------------------------------------------------------- #
# The sample: a battery, not a handful of questions
# --------------------------------------------------------------------------- #
# **為什麼要這麼多題**：樣本太少時，鸚鵡捲舌（輸出恆等於輸入）與學習（輸出
# 隨對話改變）在量測上分不開——兩者看起來都是「一致��輸出」。所以探針必須同時
# 具備三件事：① 夠多的回合（各類缺陷率有意義）；② 足夠多組「教→問」對
# （學習效應是平均值，不是單一問答的巧合）；③ **有效性檢查**：輸出若全是一樣
# 的，這次量測就分不出形狀，必須自己說出來（見 _sample_validity）。
QUALITY_QUESTIONS: List[Tuple[str, Optional[str]]] = [
    ("你好，我們今天聊聊？", None),
    ("What is 2+2?", "math"),
    ("幫我算 17*23", "math"),
    ("Tell me about the sky's color.", "kb"),
    ("A is taller than B, who is taller?", "teacher"),
    ("The first exceeds second, second exceeds third, which is on top?", "bridge"),
    ("我今天很累", None),
    ("謝謝你", None),
    ("What is 12 * 12?", "math"),
    ("How many days in a week?", "kb"),
    ("B is shorter than C, C shorter than D, who is shortest?", "teacher"),
    ("The cat sits on the mat. What does the cat sit on?", "kb"),
    ("我最近有點焦慮", None),
    ("晚安", None),
    ("What is 100 - 58?", "math"),
    ("Who is taller, Anna or Ben?", "teacher"),
    ("Nina outweighs Otto, Otto outweighs Pia, who is the heaviest?", "bridge"),
    ("Tell me about the color of grass.", "kb"),
    ("我昨天加班到很晚", None),
    ("謝謝你陪我聊", None),
]

# The learning battery: each entry is (the teaching turn, the question, the
# expected answer). The question is asked BEFORE the teaching (cold) and
# AFTER it (warm) — the difference is the learning effect.
LEARNING_BATTERY: List[Tuple[str, str, str]] = [
    ("我叫小明", "我剛才說我叫什麼名字？", "小明"),
    ("我住在台北", "我剛才說我住哪裡？", "台北"),
    ("我的貓叫小花", "我剛才說我的貓叫什麼？", "小花"),
    ("我喜歡喝拿鐵", "我剛才說我喜歡喝什麼？", "拿鐵"),
    ("我今天用紅色背包", "我剛才說我今天用什麼顏色的背包？", "紅色"),
    ("我在圖書館工作", "我剛才說我在哪裡工作？", "圖書館"),
    ("我養了一隻叫豆豆的狗", "我剛才說我的狗叫什麼？", "豆豆"),
    ("我下午三點開會", "我剛才說我幾點開會？", "三點"),
    ("我最愛吃的口味是芒果", "我剛才說我最愛吃什麼口味？", "芒果"),
    ("我的生日是九月十號", "我剛才說我的生日是哪天？", "九月十號"),
    ("我上班搭捷運", "我剛才說我上班怎麼去？", "捷運"),
    ("我最近在學鋼琴", "我剛才說我最近在學什麼？", "鋼琴"),
    ("我的手機是藍色的", "我剛才說我的手機是什麼顏色？", "藍色"),
    ("我喜歡的球類是籃球", "我剛才說我喜歡哪種球類？", "籃球"),
    ("我家的狗叫旺財", "我剛才說我家的狗叫什麼？", "旺財"),
    ("我下週要去墾丁", "我剛才說我下週要去哪裡？", "墾丁"),
]


# The classes the probe scores.
CLASSES = (
    "correct",
    "echo",
    "artifact",
    "qa_machine",
    "offtopic",
    "abstain",
    "empty",
    "ramble",
    "stale_fact",
)

# The small sample: the first N turns of a pass. The standard sample is the
# whole pass. Both are measured; if they disagree, the standard size is not
# yet a stable measurement (an 11-turn sample said 0% offtopic where 44
# turns said 30% — the conclusion flipped with the sample size).
SMALL_SAMPLE_TURNS = 20


def _build_units() -> List[List[Tuple[str, Optional[str]]]]:
    """The sample as *units* (a unit is a whole teach→ask pair or a question).

    The units matter for the small sample: a systematic sample of the units
    keeps the pairs intact, so the small sample's learning effect is
    measurable (a sample of turns would break the pairs and report 0).
    """
    units: List[List[Tuple[str, Optional[str]]]] = []
    for teaching, question, expected in LEARNING_BATTERY:
        units.append(
            [
                (question, ("memory", expected)),  # 冷：還沒被教過
                (teaching, "not_contains"),  # 教：使用者自報
                (question, ("memory", expected)),  # 熱：教完再問
            ]
        )
    for question, oracle in QUALITY_QUESTIONS:
        units.append([(question, oracle)])
    return units


AGENT_UNITS: List[List[Tuple[str, Optional[str]]]] = _build_units()
AGENT_SCRIPT: List[Tuple[str, Optional[str]]] = [turn for unit in AGENT_UNITS for turn in unit]

# The teacher's phrasing of the bridge question (the oracle for it).
BRIDGE_ORACLE_QUESTION = "The first is higher than second, second higher than third, which is top?"

# A glued-together answer (several unrelated template fragments in one
# breath) — the "ramble" shape.
_SENTENCE_END = re.compile(r"[。！？!?…~]|\.\s")


def _is_ramble(text: str) -> bool:
    """True when the answer glues several fragments together.

    Three sentences is a reply; four or more is a ramble (it reads
    machine-made at the first glance).
    """
    return len(_SENTENCE_END.findall(text or "")) >= 4


# The artefacts that mean the answer came out broken.
_ARTIFACT = re.compile(r"=(?:false|true|None|nan)\b|\bNone\b|\bnan\b|\{\{|\}\}", re.IGNORECASE)
# The honest abstentions: "I don't have enough knowledge" / "我還沒有足夠的知識".
# An abstention is *not* an answer — it must never count as "correct".
_ABSTAIN = re.compile(
    r"don't have enough knowledge|can't complete this task|no language model is available"
    r"|還沒有足夠的知識|目前還做不到|目前做不到|無法回答這個問題|沒有可用的語言模型",
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


# The social turns: a canned answer is *appropriate* for them.
_SOCIAL_TURN = re.compile(
    r"你好|您好|早安|晚安|謝謝|谢谢|再見|再见|哈囉|hello|hi\b|thanks|thank you|bye|goodbye|morning",
    re.IGNORECASE,
)
# The canned answers the project serves from its presets/templates.
_CANNED_ANSWERS: Optional[set] = None


def _canned_answers() -> set:
    """The preset/template answers of the project (the QA-machine shapes)."""
    global _CANNED_ANSWERS
    if _CANNED_ANSWERS is not None:
        return _CANNED_ANSWERS
    answers = set()
    try:
        from ai.data_eng.presets import REFLEX_PRESETS

        for value in REFLEX_PRESETS.values():
            answers.add(_normalized(str(value)))
    except Exception:
        pass
    try:
        from ai.memory.template_library import get_template_library

        library = get_template_library()
        for template in getattr(library, "_templates", {}).values():
            content = getattr(template, "content", None)
            if content:
                answers.add(_normalized(str(content)))
    except Exception:
        pass
    _CANNED_ANSWERS = {a for a in answers if a}
    return _CANNED_ANSWERS


def _canned_mismatch(question: str, text: str) -> bool:
    """True when a canned answer ignored what the user actually said.

    A *context-matched* template (an emotional template whose keywords are
    in the user's words) is a legitimate answer. A canned line that was
    triggered by a keyword inside the sentence ("我今天很累" → "今天") is the
    QA-machine shape.
    """
    normalized = _normalized(text)
    if normalized not in _canned_answers():
        return False
    user_chars = set(_words(question))
    try:
        from ai.memory.template_library import get_template_library

        library = get_template_library()
        for template in getattr(library, "_templates", {}).values():
            if _normalized(str(getattr(template, "content", ""))) != normalized:
                continue
            keywords = set()
            for kw in getattr(template, "keywords", []) or []:
                keywords.update(_words(str(kw)))
            if keywords & user_chars:
                return False  # the template matched the user's own words
            return True
    except Exception:
        pass
    # The reflex presets: the key must be the whole message.
    try:
        from ai.data_eng.presets import REFLEX_PRESETS

        normalized_q = _normalized(question)
        for key, value in REFLEX_PRESETS.items():
            if _normalized(str(value)) == normalized and _normalized(str(key)) != normalized_q:
                return True
    except Exception:
        pass
    return False


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
def oracle_answer(kind, question: str) -> Optional[str]:
    """The expected answer, taken from the project's own engines.

    ``kind`` may be a plain kind ("math"/"kb"/"teacher"/"bridge") or a tuple
    ("memory", expected_value) for the learning battery.
    """
    if isinstance(kind, tuple):
        kind, expected = kind[0], kind[1]
        if kind == "memory":
            return str(expected)
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
# What a statement turn must NOT bring back (a stale remembered fact).
_FORBIDDEN_IN_STATEMENT = ("小花", "貓", "鮪魚", "fox")


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
        if turn.question == question:
            # The same question asked twice may legitimately get the same
            # answer; the QA-machine shape is one answer for *different*
            # questions.
            continue
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
    if text and _is_ramble(text):
        classes.append("ramble")
    if duplicate_of is not None:
        classes.append("qa_machine")
    elif text and not _SOCIAL_TURN.search(question) and _canned_mismatch(question, text):
        # A canned answer to a substantive turn, and the canned line did not
        # match what the user said: the QA-machine shape.
        classes.append("qa_machine")
    if text and not answered and expected and not abstained:
        classes.append("offtopic")
    if expected == "not_contains":
        # A statement turn must not drag an unrelated remembered fact back in.
        if any(word in text for word in _FORBIDDEN_IN_STATEMENT):
            classes.append("stale_fact")
        answered = True  # the turn has no positive oracle
    if answered:
        classes.append("correct")

    # The human-likeness score: the components that make an answer read like a
    # person answered it (each worth 0.2; correctness is worth 0.4).
    score = 0.0
    if answered:
        score += 0.4
    if "echo" not in classes:
        score += 0.2
    if text and "artifact" not in classes and not abstained and "ramble" not in classes:
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


def _wilson(successes: int, total: int, z: float = 1.96) -> Tuple[float, float]:
    """The Wilson score interval of a rate (0/10 is NOT "0%")."""
    if total <= 0:
        return (0.0, 0.0)
    phat = successes / total
    denominator = 1 + z * z / total
    center = (phat + z * z / (2 * total)) / denominator
    margin = z * ((phat * (1 - phat) / total + z * z / (4 * total * total)) ** 0.5) / denominator
    return (round(max(0.0, center - margin), 4), round(min(1.0, center + margin), 4))


def _sample_validity(turns: Sequence[Turn]) -> Dict[str, object]:
    """Is this sample able to tell the shapes apart?

    **樣本太少或輸出全一樣時，量測是無效的**：鸚鵡捲舌（輸出恆等於輸入）
    與學習（輸出隨對話改變）在統計上分不開——兩者都是「一致的輸出」。所以量測
    工具自己必須先回答三個問題：① 回合數夠嗎？② 不同輸出有幾種？③ 有沒有
    任何一個回合的輸出跟別人不同（不變的樣本＝分不出形狀）？
    """
    total = len(turns)
    responses = [_normalized(t.response) for t in turns if t.response]
    distinct = len(set(responses))
    distinct_ratio = round(distinct / max(total, 1), 4)
    learning_pairs = 0
    seen: Dict[str, int] = {}
    for turn in turns:
        seen[turn.question] = seen.get(turn.question, 0) + 1
    learning_pairs = sum(1 for count in seen.values() if count > 1)
    problems: List[str] = []
    if total < 30:
        problems.append(f"the sample is too small ({total} turns < 30)")
    if distinct_ratio < 0.30:
        problems.append(
            f"the outputs are nearly constant ({distinct} distinct / {total} turns) — "
            "parroting and learning cannot be told apart"
        )
    if learning_pairs < 5:
        problems.append(
            f"too few teach→ask pairs ({learning_pairs} < 5) to measure the learning effect"
        )
    return {
        "turns": total,
        "distinct_responses": distinct,
        "distinct_ratio": distinct_ratio,
        "learning_pairs": learning_pairs,
        "valid": not problems,
        "problems": problems,
    }


def _rate_with_interval(turns: Sequence[Turn], klass: str) -> Dict[str, object]:
    """The rate of a class + its Wilson interval (never a bare percentage)."""
    total = len(turns)
    hits = sum(1 for t in turns if klass in t.classes)
    low, high = _wilson(hits, total)
    return {
        "rate": round(hits / total, 4) if total else 0.0,
        "hits": hits,
        "total": total,
        "ci95": [low, high],
    }


def _systematic_sample(turns: Sequence[Turn], size: int) -> List[Turn]:
    """A representative subsample of the *units* (the pairs stay intact).

    A *prefix* would be biased (the learning pairs come first, so the prefix
    would be all learning questions) and a sample of *turns* would break the
    teach→ask pairs (the learning effect would read 0). Both would make the
    small sample "disagree" with the standard one for the wrong reason.
    """
    if size <= 0 or len(turns) <= size:
        return list(turns)
    # The unit boundaries come from the script (the teaching turn sits
    # *between* the cold and the warm ask, so adjacency does not define a
    # unit).
    ranges = _script_unit_ranges()
    keep = max(1, round(len(ranges) * size / len(turns)))
    step = len(ranges) / keep
    picked_indexes = set()
    for i in range(keep):
        start, end = ranges[min(len(ranges) - 1, int(i * step))]
        picked_indexes.update(range(start, end))
    return [turn for turn in turns if turn.index in picked_indexes]


def _script_unit_ranges() -> List[Tuple[int, int]]:
    """The (start, end) script index range of every unit."""
    ranges: List[Tuple[int, int]] = []
    cursor = 0
    for unit in AGENT_UNITS:
        ranges.append((cursor, cursor + len(unit)))
        cursor += len(unit)
    return ranges


def _subset_metrics(turns: Sequence[Turn], label: str) -> Dict[str, object]:
    """The metrics of a subset of the turns (the small / the standard sample)."""
    return {
        "label": label,
        "turns": len(turns),
        "human_score": _mean([t.human_score for t in turns]),
        "progress": _learning_delta(turns),
        "rates": {k: _rate_with_interval(turns, k) for k in CLASSES},
    }


def _consistency(small: Dict[str, object], standard: Dict[str, object]) -> Dict[str, object]:
    """Do the small and the standard sample agree?

    **不一致就代表標準量還不夠**（或抽樣有偏）：結論會隨著樣本大小翻轉——
    那正是 11 題的樣本給過的教訓（0% 雞同鴨講 vs 44 題的 30%）。
    """
    tolerance = 0.15
    disagreements: List[str] = []
    for key in ("human_score", "progress"):
        delta = abs(float(small[key]) - float(standard[key]))
        if delta > tolerance:
            disagreements.append(
                f"{key}: 少量 {small[key]} vs 標準 {standard[key]}（差 {delta:.2f} > {tolerance}）"
            )
    for klass in CLASSES:
        small_rate = float(small["rates"][klass]["rate"])  # type: ignore[index]
        standard_rate = float(standard["rates"][klass]["rate"])  # type: ignore[index]
        if abs(small_rate - standard_rate) > tolerance:
            disagreements.append(f"{klass}: 少量 {small_rate:.0%} vs 標準 {standard_rate:.0%}")
    return {
        "consistent": not disagreements,
        "tolerance": tolerance,
        "disagreements": disagreements,
    }


def _learning_delta(turns: Sequence[Turn]) -> float:
    """The learning effect: the same question, before and after the teaching.

    A question asked twice in one pass (cold → warm) is the experiment: the
    delta is what the conversation actually taught the AI — that is the
    "要多少交談資料才學會" number.
    """
    seen: Dict[str, List[float]] = {}
    for turn in turns:
        seen.setdefault(turn.question, []).append(turn.human_score)
    deltas = [scores[-1] - scores[0] for scores in seen.values() if len(scores) > 1]
    return round(sum(deltas) / len(deltas), 4) if deltas else 0.0


def _learning_deltas(turns: Sequence[Turn]) -> List[float]:
    """The cold→warm delta of every repeated question (the per-pair detail)."""
    seen: Dict[str, List[float]] = {}
    for turn in turns:
        seen.setdefault(turn.question, []).append(turn.human_score)
    return [scores[-1] - scores[0] for scores in seen.values() if len(scores) > 1]


def _rate(turns: Sequence[Turn], klass: str) -> float:
    if not turns:
        return 0.0
    return round(sum(1 for t in turns if klass in t.classes) / len(turns), 4)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-turns",
        type=int,
        default=200,
        help="the turn budget (both passes; the standard sample is 136)",
    )
    parser.add_argument("--max-seconds", type=float, default=600.0, help="the wall-clock budget")
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

    # The sandbox must be set before the backend modules are imported, and it
    # must start EMPTY: a sandbox that keeps the previous run's memory would
    # make the "cold" question warm (the measurement would not reproduce).
    isolate_data_dir()
    if SANDBOX_DATA_DIR.exists():
        shutil.rmtree(SANDBOX_DATA_DIR, ignore_errors=True)

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
    stability = round(second_score - first_score, 4)
    progress = _learning_delta(first)

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
                k: _rate_with_interval(first, k)
                for k in (
                    "correct",
                    "echo",
                    "artifact",
                    "qa_machine",
                    "offtopic",
                    "abstain",
                    "empty",
                    "ramble",
                    "stale_fact",
                )
            },
        },
        "pass2": {
            "turns": len(second),
            "human_score": second_score,
            "rates": {
                k: _rate_with_interval(second, k)
                for k in (
                    "correct",
                    "echo",
                    "artifact",
                    "qa_machine",
                    "offtopic",
                    "abstain",
                    "empty",
                    "ramble",
                    "stale_fact",
                )
            },
        },
        "progress": progress,
        "stability": stability,
        "validity": _sample_validity(all_turns),
        "learning_deltas": _learning_deltas(first),
        "small_sample": _subset_metrics(_systematic_sample(second, SMALL_SAMPLE_TURNS), "small"),
        "standard_sample": _subset_metrics(second, "standard"),
        "consistency": _consistency(
            _subset_metrics(_systematic_sample(second, SMALL_SAMPLE_TURNS), "small"),
            _subset_metrics(second, "standard"),
        ),
        "data": {"pairs": data_pairs, "chars": data_chars},
        "elapsed_sec": round(time.time() - started, 2),
        "turn_details": [t.__dict__ for t in all_turns],
    }

    print("  ── 結果 ──")
    print(
        f"  回合數：{len(all_turns)}（預算 {budget.max_turns} 回合／{budget.max_seconds:.0f} 秒）"
    )
    print(
        f"  第 1 輪人味分數：{first_score:.3f}　第 2 輪：{second_score:.3f}　"
        f"學習效應（冷→熱）：{progress:+.3f}　穩定度（兩輪差）：{stability:+.3f}"
    )
    for label, block in (("第 1 輪", result["pass1"]), ("第 2 輪", result["pass2"])):
        rates = block["rates"]
        print(
            f"  {label}（n={block['turns']}）: 答對 {rates['correct']['rate']:.0%}"
            f"｜鸚鵡 {rates['echo']['rate']:.0%}｜"
            f"亂碼 {rates['artifact']['rate']:.0%}｜QA 機器 {rates['qa_machine']['rate']:.0%}｜"
            f"雞同鴨講 {rates['offtopic']['rate']:.0%}｜棄權 {rates['abstain']['rate']:.0%}｜"
            f"碎念 {rates['ramble']['rate']:.0%}｜舊事實 {rates['stale_fact']['rate']:.0%}｜"
            f"空白 {rates['empty']['rate']:.0%}"
        )
        # 誠實：0/12 不是「0%」——把區間一起印出來。
        worst = rates["echo"]
        print(
            f"    95% 區間（以鸚鵡捲舌為例）：{worst['hits']}/{worst['total']} → "
            f"{worst['ci95'][0]:.0%}–{worst['ci95'][1]:.0%}"
        )
    small = result["small_sample"]
    standard = result["standard_sample"]
    consistency = result["consistency"]
    print(
        f"  少量（n={small['turns']}）vs 標準（n={standard['turns']}）: "
        f"人味 {small['human_score']:.3f} vs {standard['human_score']:.3f}｜"
        f"學習效應 {small['progress']:+.3f} vs {standard['progress']:+.3f}"
    )
    if consistency["consistent"]:
        print("  一致性：✅ 少量與標準量的結論一致（標準量可用）")
    else:
        print("  一致性：❌ 少量與標準量不一致 → **標準量需要重調整**（結論會隨樣本大小翻轉）：")
        for item in consistency["disagreements"]:
            print(f"    - {item}")

    validity = result["validity"]
    if validity["valid"]:
        print(
            f"  樣本有效性：✅ 回合 {validity['turns']}、不同輸出 {validity['distinct_responses']} 種"
            f"（{validity['distinct_ratio']:.0%}）、教→問 {validity['learning_pairs']} 組"
        )
    else:
        print("  樣本有效性：❌ 這次量測分不出形狀，數字不可信：")
        for problem in validity["problems"]:
            print(f"    - {problem}")
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
