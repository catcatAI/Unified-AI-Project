"""統一的智能定義（Unified intelligence definition）— v1。

專案裡原本有**十一套**打分系統，講的都不是同一件事，於是「智能」這個詞在
文件、工具、門禁之間漂移。本模組是**唯一的定義來源**：

1. **能力（capability）**：它**能**做什麼（六個維度，每個 ×10）。每個維度必
   須標註**分數型別**（六型：架構／框架／預期／訓練／驗證／實際）——只有
   **驗證／實際**可以計入智能總分（架構分與框架分是準備度，不是能力）。
2. **來源（source）**：回答**由哪一層**產生（神經／模板／確定性／檢索）。這是
   「智能 vs 複製模板」的判準：能力再高，若全部來自模板，就不是智能。
3. **誠實度（integrity）**：量測本身可不可信（樣本有效性、少量 vs 標準量一致
   性、hold-out gap、非空轉）。**誠實度是門，不是分數**——量測無效時，智能
   總分是「未定義」，不是「低分」。

**階梯命名空間**（原本四套 L0 開頭的階梯互相撞名，現在各有名稱）：

| 命名空間 | 意義 | 出處 |
| --- | --- | --- |
| `L0..L3` | **智能階梯**（本定義） | `AI_CAPABILITY_LADDER.md` |
| `Q0..Q4` | 美術品質階梯（看多少定什麼） | `VISION_MAP_AND_QUALITY_LADDER.md` |
| `X0..X11` | 成熟度／經驗值 | `ANGELA_MATRIX_ANNOTATION_GUIDE.md` |
| `R1..R3` | 回應來源層級 | `docs/05-development/testing/timeout-strategy.md` |
| `claimed..production` | 工程成熟度 | `docs/status_matrix.yaml` |

**智能總分** = 六個能力維度的平均（0–10），**前提是誠實度全過**；來源分布
另外報告（不乘進總分——能力分本來就來自分層的量測）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# The score types (the project's existing discipline — INTELLIGENCE_ASSESSMENT §0)
# --------------------------------------------------------------------------- #
SCORE_TYPE_ARCHITECTURE = "架構分"
SCORE_TYPE_FRAMEWORK = "框架分"
SCORE_TYPE_EXPECTED = "預期分"
SCORE_TYPE_TRAINED = "訓練分"
SCORE_TYPE_VERIFIED = "驗證分"
SCORE_TYPE_ACTUAL = "實際分"

#: Only these two count toward the intelligence composite (the rest measure
#: readiness, not capability).
COUNTED_SCORE_TYPES = (SCORE_TYPE_VERIFIED, SCORE_TYPE_ACTUAL)

SCORE_TYPES: Tuple[str, ...] = (
    SCORE_TYPE_ARCHITECTURE,
    SCORE_TYPE_FRAMEWORK,
    SCORE_TYPE_EXPECTED,
    SCORE_TYPE_TRAINED,
    SCORE_TYPE_VERIFIED,
    SCORE_TYPE_ACTUAL,
)


# --------------------------------------------------------------------------- #
# The capability dimensions
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Dimension:
    """One capability dimension: what it measures and where the number comes."""

    id: str
    name: str
    #: The command that produces the measurement.
    command: str
    #: The score type the number carries.
    score_type: str
    #: The dimension's share of the composite (0 = not measured yet).
    weight: float = 0.0
    #: The floor the dimension must reach to count as "measured".
    threshold: float = 0.0
    #: What the dimension must show to be complete.
    exit_criterion: str = ""
    #: Why the dimension is hard / what its current blocker is.
    note: str = ""


DIMENSIONS: List[Dimension] = [
    Dimension(
        id="facts",
        name="事實與知識",
        command="python scripts/run_benchmarks.py --backend native --suite knowledge,knowledge_mc --gate-native",
        score_type=SCORE_TYPE_VERIFIED,
        weight=1.0,
        threshold=0.25,
        exit_criterion="native knowledge ≥25% 且 knowledge_mc ≥90%（不含 RAG）",
        note="確定性知識庫＋SNN 語意層；跨 AI 可比分數另計（不計入本表）",
    ),
    Dimension(
        id="math",
        name="数理與邏輯",
        command="python scripts/run_benchmarks.py --backend native --suite math --gate-native",
        score_type=SCORE_TYPE_VERIFIED,
        weight=1.0,
        threshold=0.75,
        exit_criterion="native math ≥75%（確定性引擎）",
        note="確定性引擎的正確率；不是神經的泛化",
    ),
    Dimension(
        id="paraphrase",
        name="語意理解／改述泛化（L1 關鍵）",
        command="python scripts/probe_reasoning_unseen.py",
        score_type=SCORE_TYPE_ACTUAL,
        weight=1.0,
        threshold=0.40,
        exit_criterion="純神經（SNN-only）改述／CJK 召回 ≥40%；橋接可補足但要分開報",
        note="階梯 L1 的關鍵度量；目前純神經 0%＝這一級還沒到",
    ),
    Dimension(
        id="dialogue",
        name="對話與記憶（L2 關鍵）",
        command="python scripts/probe_native_dialogue.py",
        score_type=SCORE_TYPE_ACTUAL,
        weight=1.0,
        threshold=0.60,
        exit_criterion="純本地對話：人話標準 ≥60% 且學習效應 ≥0.20 且神經層佔比 ≥20%",
        note="只留專案自己的基模（不接雲端金鑰／本地 LLM）",
    ),
    Dimension(
        id="boundary",
        name="推理與例外（最正確）",
        command="python scripts/probe_native_dialogue.py",
        score_type=SCORE_TYPE_ACTUAL,
        weight=1.0,
        threshold=0.30,
        exit_criterion="帶邊界條件的題（斷言）通過率 ≥30%：要帶條件＋例外，不只是近似",
        note="題庫覆蓋率＝知識缺口；機制（斷言推理）另計",
    ),
    Dimension(
        id="tools",
        name="工具與行動",
        command="python scripts/run_benchmarks.py --backend native --suite code,routing --gate-native",
        score_type=SCORE_TYPE_VERIFIED,
        weight=1.0,
        threshold=0.85,
        exit_criterion="native code＋routing 皆 ≥85%（工具選擇與執行）",
        note="code＝沙箱執行程式、routing＝工具/路徑選擇；取兩者最弱者",
    ),
]

DIMENSION_BY_ID: Dict[str, Dimension] = {d.id: d for d in DIMENSIONS}

# --------------------------------------------------------------------------- #
# The ladder (the project's existing bands — kept, now the only intelligence
# ladder)
# --------------------------------------------------------------------------- #
LADDER_BANDS: List[Tuple[int, int, str, str]] = [
    (0, 2, "L0 確定性＋反射＋字典", "能算、能查、能回罐頭，但不會「想」"),
    (2, 4, "L1 本地可理解", "能把未見過的問法對上已知概念，改述召回穩定"),
    (4, 6, "L2 本地可用", "多輪對話不跑題，記憶／推理／多模態能串起來當助手用"),
    (6, 10, "L3 LLM 編排", "自然對話、工具調用、多智能體協作"),
]

#: 要「達到」某一階，該階的關鍵維度必須**全部**過門檻。平均分落在某個帶
#: 不代表那一階達成了——例如平均 4.4 落在 L2 帶，但 L1 的關鍵度量（改述泛化）
#: 是 0，那就只達成 L0。這是「平均」與「門檻」的分離，避免用平均值掩蓋缺口。
LEVEL_REQUIREMENTS: Dict[str, Tuple[str, ...]] = {
    "L1": ("paraphrase",),
    "L2": ("dialogue", "boundary"),
    "L3": ("facts", "math", "tools"),
}

#: The other ladders, with their namespaces (so L0 stops meaning five things).
LADDER_NAMESPACES: Dict[str, str] = {
    "L0..L3": "智能階梯（本定義；AI_CAPABILITY_LADDER.md）",
    "Q0..Q4": "美術品質階梯（看多少定什麼；VISION_MAP_AND_QUALITY_LADDER.md）",
    "X0..X11": "成熟度／經驗值（ANGELA_MATRIX_ANNOTATION_GUIDE.md）",
    "R1..R3": "回應來源層級（docs/05-development/testing/timeout-strategy.md）",
    "claimed..production": "工程成熟度（docs/status_matrix.yaml）",
}

# --------------------------------------------------------------------------- #
# The answer sources (the anti-fossilization axis)
# --------------------------------------------------------------------------- #
SOURCE_NEURAL = "neural"
SOURCE_TEMPLATE = "template"
SOURCE_DETERMINISTIC = "deterministic"
SOURCE_RETRIEVAL = "retrieval"
SOURCE_OTHER = "other"

#: The intelligence composite requires the learned models to carry a real share
#: of the answers — otherwise the capability is template copying.
MIN_NEURAL_SHARE = 0.20


@dataclass
class Integrity:
    """The measurement's trustworthiness (a gate, not a score)."""

    sample_valid: bool = True
    consistent: bool = True
    holdout_gap: Optional[float] = None
    non_vacuous: bool = True
    problems: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.sample_valid and self.consistent and self.non_vacuous

    def describe(self) -> str:
        if self.ok:
            return "量測有效（樣本有效性 ✅／少量-標準量一致性 ✅／非空轉 ✅）"
        return "量測無效：" + "；".join(self.problems)


def band_for(score: float) -> Tuple[str, str]:
    """The ladder band of a composite score."""
    for low, high, name, summary in LADDER_BANDS:
        if score < high:
            return name, summary
    return LADDER_BANDS[-1][2], LADDER_BANDS[-1][3]


def attained_level(dimension_scores: Dict[str, float]) -> Tuple[str, List[str]]:
    """The highest ladder level whose key dimensions ALL meet their floors.

    Returns ``(level, missing)`` where ``missing`` lists the unmet requirements
    of the first level that was not reached.
    """
    level = "L0"
    for name in ("L1", "L2", "L3"):
        missing = [
            f"{dimension} {dimension_scores.get(dimension, 0.0) * 10:.1f}/10 "
            f"< {DIMENSION_BY_ID[dimension].threshold * 10:.1f}/10"
            for dimension in LEVEL_REQUIREMENTS[name]
            if dimension_scores.get(dimension, 0.0) < DIMENSION_BY_ID[dimension].threshold
        ]
        if missing:
            return level, missing
        level = name
    return level, []


def composite(dimension_scores: Dict[str, float], integrity: Integrity) -> Dict[str, object]:
    """The intelligence composite (0-10) — undefined when the measurement is not
    trustworthy.

    ``dimension_scores`` maps a dimension id to its 0-1 measured value. Only
    dimensions that are *measured* (their score type counts) and that have a
    weight contribute.
    """
    counted: List[Tuple[str, float, float]] = []
    skipped: List[str] = []
    for dimension in DIMENSIONS:
        if dimension.score_type not in COUNTED_SCORE_TYPES:
            skipped.append(f"{dimension.id}({dimension.score_type})")
            continue
        value = dimension_scores.get(dimension.id)
        if value is None:
            skipped.append(f"{dimension.id}(未量)")
            continue
        counted.append((dimension.id, min(max(value, 0.0), 1.0), dimension.weight))
    if not counted:
        return {
            "score": None,
            "status": "undefined",
            "reason": "no dimension carries a verified/actual score yet",
            "counted": [],
            "skipped": skipped,
            "integrity": integrity.describe(),
        }
    total_weight = sum(weight for _id, _v, weight in counted)
    weighted = sum(value * weight for _id, value, weight in counted) / (total_weight or 1.0)
    score = round(weighted * 10, 2)
    if not integrity.ok:
        return {
            "score": None,
            "status": "undefined",
            "reason": integrity.describe(),
            "counted": [(i, round(v, 4)) for i, v, _w in counted],
            "skipped": skipped,
            "integrity": integrity.describe(),
        }
    name, summary = band_for(score)
    failed = [
        f"{i} {v * 10:.1f}/10 < {DIMENSION_BY_ID[i].threshold * 10:.1f}/10"
        for i, v, _w in counted
        if v < DIMENSION_BY_ID[i].threshold
    ]
    level, missing = attained_level(dimension_scores)
    return {
        "score": score,
        "status": "measured",
        "band": name,
        "band_summary": summary,
        "attained_level": level,
        "level_missing": missing,
        "failed_dimensions": failed,
        "counted": [(i, round(v, 4)) for i, v, _w in counted],
        "skipped": skipped,
        "integrity": integrity.describe(),
    }


__all__ = [
    "COUNTED_SCORE_TYPES",
    "DIMENSIONS",
    "DIMENSION_BY_ID",
    "Dimension",
    "Integrity",
    "LADDER_BANDS",
    "LADDER_NAMESPACES",
    "LEVEL_REQUIREMENTS",
    "MIN_NEURAL_SHARE",
    "SCORE_TYPES",
    "attained_level",
    "band_for",
    "composite",
]
