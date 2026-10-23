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

**及格線從外部基準算出來，不是自己定**（避免自問自答）。每條線都掛一個公開
基準與一條統一規則：

| 規則 | 內容 |
| --- | --- |
| R1 隨機地板 | 及格 ≥ **隨機基線 + 20 個百分點**（MMLU 論文用「比隨機高近 20pp」描述 GPT-3 的顯著進步） |
| R2 人類相對 | 及格 ≥ **0.5 × 人類上限**（該基準若有公布） |
| R3 無人類基線 | 及格 = **0.7 × 已發表強基線／SOTA** |

及格線 = 對該題型適用的規則取**大者**。完整推導與引用見
`docs/06-project-management/INTELLIGENCE_PASS_CRITERIA.md`；
`check_intelligence_definition.py` 會重算，任何人手改門檻都会被擋下。
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
# The external anchors (the pass lines are derived, never hand-written)
# --------------------------------------------------------------------------- #
CHANCE_MARGIN = 0.20
HUMAN_FRACTION = 0.50
BASELINE_FRACTION = 0.70


@dataclass(frozen=True)
class Anchor:
    """A published benchmark the pass line is derived from.

    ``protocol`` says how close our internal measurement is to that benchmark:
    ``same`` = the actual benchmark, ``analogous`` = the same task family on
    our own items (the number is comparable in kind, not in items).
    """

    benchmark: str
    source: str
    url: str
    protocol: str
    #: Chance level of the benchmark (0 when free-form).
    chance: float = 0.0
    #: Published human ceiling (experts), if any.
    human_expert: Optional[float] = None
    #: Published non-expert human baseline, if any.
    human_nonexpert: Optional[float] = None
    #: Published strong baseline / SOTA, used when no human ceiling exists.
    published_baseline: Optional[float] = None
    #: One-line note about caveats (e.g. contamination).
    caveat: str = ""


def pass_line(anchor: Anchor) -> Tuple[float, str]:
    """Derive the pass line from the external anchors (never hand-written).

    Returns ``(value, derivation)`` where the derivation names the rule and the
    numbers it used, so a reader can recompute it.
    """
    candidates: List[Tuple[float, str]] = []
    if anchor.chance:
        candidates.append(
            (
                anchor.chance + CHANCE_MARGIN,
                f"R1 隨機 {anchor.chance:.1%} + {CHANCE_MARGIN:.0%}pp = "
                f"{(anchor.chance + CHANCE_MARGIN):.1%}",
            )
        )
    if anchor.human_expert is not None:
        candidates.append(
            (
                HUMAN_FRACTION * anchor.human_expert,
                f"R2 {HUMAN_FRACTION:.0%} × 人類上限 {anchor.human_expert:.1%} = "
                f"{(HUMAN_FRACTION * anchor.human_expert):.1%}",
            )
        )
    if candidates:
        value, derivation = max(candidates, key=lambda item: item[0])
        return round(value, 4), derivation
    if anchor.published_baseline is not None:
        return (
            round(BASELINE_FRACTION * anchor.published_baseline, 4),
            f"R3 {BASELINE_FRACTION:.0%} × 已發表基線 {anchor.published_baseline:.1%} = "
            f"{(BASELINE_FRACTION * anchor.published_baseline):.1%}",
        )
    raise ValueError(f"{anchor.benchmark}: no chance, human ceiling or baseline to derive from")


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
    #: The external benchmark the pass line is derived from.
    anchor: Optional[Anchor] = None
    #: What the dimension must show to be complete.
    exit_criterion: str = ""
    #: Why the dimension is hard / what its current blocker is.
    note: str = ""

    @property
    def threshold(self) -> float:
        """The pass line — **derived from the external anchor**, never hand-written."""
        return pass_line(self.anchor)[0] if self.anchor else 0.0

    @property
    def threshold_derivation(self) -> str:
        return pass_line(self.anchor)[1] if self.anchor else "（未掛外部基準）"


DIMENSIONS: List[Dimension] = [
    Dimension(
        id="facts",
        name="事實與知識",
        command="python scripts/run_benchmarks.py --backend native --suite knowledge,knowledge_mc --gate-native",
        score_type=SCORE_TYPE_VERIFIED,
        weight=1.0,
        anchor=Anchor(
            benchmark="MMLU",
            source="Hendrycks et al., 2020, arXiv:2009.03300",
            url="https://arxiv.org/abs/2009.03300",
            protocol="analogous",
            chance=0.25,
            human_expert=0.898,
            human_nonexpert=0.345,
            caveat="MMLU 為 4 選項；內部 knowledge 為自由作答、knowledge_mc 為 4 選項（協定相近但題目不重合）",
        ),
        exit_criterion="facts ≥ 45%（MMLU 規則：隨機 25% + 20pp）",
        note="確定性知識庫＋SNN 語意層；跨 AI 可比分數另計（不計入本表）",
    ),
    Dimension(
        id="math",
        name="数理與邏輯",
        command="python scripts/run_benchmarks.py --backend native --suite math --gate-native",
        score_type=SCORE_TYPE_VERIFIED,
        weight=1.0,
        anchor=Anchor(
            benchmark="GSM8K",
            source="Cobbe et al., 2021（arXiv:2110.14168）；GPT-4 TR 2023 Table 2",
            url="https://arxiv.org/abs/2110.14168",
            protocol="analogous",
            published_baseline=0.873,
            caveat="87.3% 為 Chinchilla+SFT+ORM-RL 微調後 SOTA；GPT-4 92.0% 含訓練集污染註記 → 不採信為上限",
        ),
        exit_criterion="math ≥ 61%（無人類基線 → 0.7 × 已發表強基線 87.3%）",
        note="確定性引擎的正確率；不是神經的泛化",
    ),
    Dimension(
        id="paraphrase",
        name="語意理解／改述泛化（L1 關鍵）",
        command="python scripts/probe_paraphrase.py",
        score_type=SCORE_TYPE_ACTUAL,
        weight=1.0,
        anchor=Anchor(
            benchmark="PAWS",
            source="Zhang et al., 2019, NAACL（aclanthology.org/N19-1131）",
            url="https://aclanthology.org/N19-1131/",
            protocol="analogous",
            chance=0.50,
            human_expert=0.920,
            published_baseline=0.85,
            caveat="PAWS 是成對改述判定（人類一致度 QQP 92.0%／Wiki 94.7%）；內部探針是改述問答正確率（同為「看穿改述」，題型不同）",
        ),
        exit_criterion="paraphrase ≥ 70%（PAWS 規則：二元隨機 50% + 20pp）",
        note=(
            "量生產路徑（老師→中間層）在凍結改述集上的正確率；課程沒教過的詞"
            "（unseen_surfaces）另報為嚴格診斷，不混進分數"
        ),
    ),
    Dimension(
        id="dialogue",
        name="對話與記憶（L2 關鍵）",
        command="python scripts/probe_native_dialogue.py",
        score_type=SCORE_TYPE_ACTUAL,
        weight=1.0,
        anchor=Anchor(
            benchmark="LoCoMo",
            source="Maharana et al., ACL 2024（aclanthology.org/2024.acl-long.747）",
            url="https://aclanthology.org/2024.acl-long.747/",
            protocol="analogous",
            human_expert=0.879,
            caveat="LoCoMo 人類 87.9 為長對話 QA 的 F1；內部是人話標準通過率（同為多輪對話能力，計分方式不同）",
        ),
        exit_criterion="dialogue ≥ 44%（LoCoMo 規則：0.5 × 人類 87.9%＝44.0%，高於隨機地板 20%）",
        note="只留專案自己的基模（不接雲端金鑰／本地 LLM）",
    ),
    Dimension(
        id="boundary",
        name="推理與例外（最正確）",
        command="python scripts/probe_native_dialogue.py",
        score_type=SCORE_TYPE_ACTUAL,
        weight=1.0,
        anchor=Anchor(
            benchmark="FOLIO",
            source="Han et al., EMNLP 2024（aclanthology.org/2024.emnlp-main.1229）",
            url="https://aclanthology.org/2024.emnlp-main.1229/",
            protocol="analogous",
            chance=1.0 / 3.0,
            human_expert=0.9598,
            human_nonexpert=0.6182,
            caveat="FOLIO 為三值（真／假／未知）一階邏輯推理；內部是「事實＋條件＋例外」的斷言題（同為例外推理）",
        ),
        exit_criterion="boundary ≥ 53%（FOLIO 規則：隨機 33.3% + 20pp）",
        note="題庫覆蓋率＝知識缺口；機制（斷言推理）另計",
    ),
    Dimension(
        id="tools",
        name="工具與行動",
        command="python scripts/run_benchmarks.py --backend native --suite code,routing --gate-native",
        score_type=SCORE_TYPE_VERIFIED,
        weight=1.0,
        anchor=Anchor(
            benchmark="BFCL V4",
            source="Patil et al., ICML 2025（gorilla.cs.berkeley.edu/leaderboard，2026-10-22）",
            url="https://gorilla.cs.berkeley.edu/leaderboard",
            protocol="analogous",
            published_baseline=0.775,
            caveat="BFCL Overall SOTA 77.5%（Claude Opus 4.5, 2026-10-22）；內部為 code（沙箱執行）與 routing（工具/路徑選擇）兩套小型測試",
        ),
        exit_criterion="tools ≥ 54%（無人類基線 → 0.7 × SOTA 77.5%）",
        note="取 code 與 routing 的最弱者（工具要選對也要執行對）",
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

# --------------------------------------------------------------------------- #
# Core vs performance layer (the one boundary)
# --------------------------------------------------------------------------- #
# Pure intelligence is not directly observable. An SNN's weights carry no
# readable claim; the only way to know whether the core "thinks" is to let it
# produce the content and look at the result. That measurement necessarily
# passes *through* the performance layer (rendering, routing, memory), so the
# two layers must be kept apart: the performance layer can answer correctly
# with zero core involvement, and when it is allowed to answer first, a
# template score gets read as intelligence (this project did exactly that).
#
# Rule: an answer the core produced is *core intelligence*; an answer produced
# by routing / templates / memory / retrieval / rules is *performance* — zero
# intelligence even when correct. Only the entries below are the core. Note
# that an encoder used as a feature extractor ("semantic-qa", "neural-bridge",
# "unified") is *not* the core: it retrieves or composes around a similarity
# score, and counting it as core was the same mistake as counting lookups.
CORE_BACKENDS: Tuple[str, ...] = (
    "snn",
    "ed3n",
    "garden",
    "llm",
    "qwen",
    "llama",
    "gpt",
    "claude",
    "token-snn",
)
CORE_LAYER = "core"
PERFORMANCE_LAYER = "performance"


def is_core_backend(backend: str) -> bool:
    """True only for the thinking core (SNN family or an LLM)."""
    name = str(backend or "").lower()
    return any(key in name for key in CORE_BACKENDS)


def layer_of(backend: str) -> str:
    """``core`` or ``performance`` — never inferred from the word "neural"."""
    return CORE_LAYER if is_core_backend(backend) else PERFORMANCE_LAYER


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
    "CORE_BACKENDS",
    "CORE_LAYER",
    "COUNTED_SCORE_TYPES",
    "PERFORMANCE_LAYER",
    "is_core_backend",
    "layer_of",
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
