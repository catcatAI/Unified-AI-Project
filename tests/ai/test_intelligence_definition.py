"""統一定義的合約測試：一個定義、一個數字、一個地方。

專案原本有十一套自稱 intelligence 的評分系統（能力階梯、×10 公式、
4.3/10 加權綜合、人話 rubric、neural_share、成熟度階級、美術品質階梯…），
同一個詞在不同檔案裡指不同的量尺。這些測試守住統一定義的三件事：

1. **能力**只認「驗證／實際」分——架構分與框架分是準備度，不是能力。
2. **誠實度**是門：量測無效時總分必須是「未定義」，不可以給數字。
3. **階梯**只有一個智能階梯，其餘四套各有命名空間（不再共用 L0）。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFINITION = REPO_ROOT / "apps" / "backend" / "src" / "ai" / "meta" / "intelligence.py"
SCRIPTS = REPO_ROOT / "scripts"


def _load_definition():
    spec = importlib.util.spec_from_file_location("intelligence_definition_test", DEFINITION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["intelligence_definition_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def definition():
    return _load_definition()


# --------------------------------------------------------------------------- #
# The dimensions
# --------------------------------------------------------------------------- #
def test_every_dimension_has_a_counted_or_explicit_score_type(definition) -> None:
    assert definition.DIMENSIONS, "the definition must declare the dimensions"
    for dimension in definition.DIMENSIONS:
        assert dimension.score_type in definition.SCORE_TYPES
        assert dimension.weight > 0
        assert dimension.threshold >= 0


def test_at_least_one_dimension_carries_a_counted_score(definition) -> None:
    counted = [d for d in definition.DIMENSIONS if d.score_type in definition.COUNTED_SCORE_TYPES]
    assert counted, "readiness scores alone must never produce an intelligence score"


def test_every_measurement_command_points_at_an_existing_script(definition) -> None:
    for dimension in definition.DIMENSIONS:
        parts = dimension.command.split()
        script = next(
            (
                p
                for i, p in enumerate(parts)
                if i and "python" in parts[i - 1] and p.endswith(".py")
            ),
            "",
        )
        assert script, f"{dimension.id}: no script in {dimension.command!r}"
        assert (REPO_ROOT / script).is_file(), f"{dimension.id}: missing {script}"


# --------------------------------------------------------------------------- #
# The composite
# --------------------------------------------------------------------------- #
def test_composite_ignores_readiness_scores(definition) -> None:
    """A dimension whose score type is readiness must not be folded in."""
    architecture = definition.Dimension(
        id="readiness",
        name="readiness",
        command="python scripts/report_intelligence.py",
        score_type=definition.SCORE_TYPE_ARCHITECTURE,
        weight=1.0,
    )
    original = definition.DIMENSIONS
    try:
        definition.DIMENSIONS = [architecture]
        result = definition.composite({"readiness": 1.0}, definition.Integrity())
    finally:
        definition.DIMENSIONS = original
    assert result["status"] == "undefined"
    assert result["score"] is None


def test_composite_is_undefined_when_the_measurement_is_not_trustworthy(definition) -> None:
    integrity = definition.Integrity(
        sample_valid=False, problems=["the sample is too small (3 turns < 30)"]
    )
    result = definition.composite({"math": 0.9}, integrity)
    assert result["status"] == "undefined"
    assert result["score"] is None
    assert "too small" in result["reason"]


def test_composite_measures_the_counted_dimensions(definition) -> None:
    result = definition.composite({"math": 0.8, "facts": 0.4}, definition.Integrity())
    assert result["status"] == "measured"
    assert result["score"] == pytest.approx(6.0, abs=0.01)
    assert result["band"].startswith("L3")


def test_composite_clamps_out_of_range_values(definition) -> None:
    result = definition.composite({"math": 2.5}, definition.Integrity())
    assert result["score"] == pytest.approx(10.0, abs=0.01)


@pytest.mark.parametrize(
    "score,prefix",
    [
        (0.0, "L0"),
        (1.9, "L0"),
        (2.0, "L1"),
        (3.9, "L1"),
        (4.0, "L2"),
        (5.9, "L2"),
        (6.0, "L3"),
        (9.9, "L3"),
    ],
)
def test_band_boundaries(definition, score, prefix) -> None:
    name, _summary = definition.band_for(score)
    assert name.startswith(prefix)


def test_the_average_band_and_the_attained_level_are_different_things(definition) -> None:
    """平均落在 L2 帶，不代表 L2 達成——關鍵維度沒過門檻就停在低階。"""
    scores = {"facts": 0.9, "math": 0.9, "dialogue": 0.9, "boundary": 0.9, "paraphrase": 0.0}
    result = definition.composite(scores, definition.Integrity())
    assert result["band"].startswith("L2") or result["band"].startswith("L3")
    assert result["attained_level"] == "L0"
    assert any("paraphrase" in item for item in result["level_missing"])


def test_attained_level_reaches_l2_when_the_key_dimensions_pass(definition) -> None:
    level, missing = definition.attained_level(
        {"paraphrase": 0.5, "dialogue": 0.7, "boundary": 0.4}
    )
    assert level == "L2"
    # ``missing`` belongs to the first level NOT reached (here L3: facts/math/tools).
    assert any(item.startswith("facts") for item in missing)


def test_attained_level_stops_at_the_first_unmet_requirement(definition) -> None:
    level, missing = definition.attained_level({"paraphrase": 0.5, "dialogue": 0.1})
    assert level == "L1"
    assert any("dialogue" in item for item in missing)


def test_failed_dimensions_are_reported_not_hidden(definition) -> None:
    result = definition.composite({"math": 0.8, "facts": 0.01}, definition.Integrity())
    assert result["status"] == "measured"
    assert any(item.startswith("facts") for item in result["failed_dimensions"])


# --------------------------------------------------------------------------- #
# The ladders
# --------------------------------------------------------------------------- #
def test_exactly_one_intelligence_ladder(definition) -> None:
    intelligence = {n: t for n, t in definition.LADDER_NAMESPACES.items() if "智能" in t}
    assert list(intelligence) == ["L0..L3"]


def test_ladder_meanings_are_unique(definition) -> None:
    meanings = list(definition.LADDER_NAMESPACES.values())
    assert len(meanings) == len(set(meanings)), "two ladders share the same meaning"


def test_the_five_namespaces_are_present(definition) -> None:
    assert set(definition.LADDER_NAMESPACES) == {
        "L0..L3",
        "Q0..Q4",
        "X0..X11",
        "R1..R3",
        "claimed..production",
    }


def test_ladder_bands_cover_0_to_10(definition) -> None:
    bands = definition.LADDER_BANDS
    assert bands[0][0] == 0
    assert bands[-1][1] == 10
    for (low, high, _n, _s), (next_low, _nh, _nn, _ns) in zip(bands, bands[1:]):
        assert high == next_low, "the bands must not leave a gap"


# --------------------------------------------------------------------------- #
# The gate
# --------------------------------------------------------------------------- #
def test_the_gate_passes_on_the_current_repository() -> None:
    spec = importlib.util.spec_from_file_location(
        "intelligence_definition_gate_test", SCRIPTS / "check_intelligence_definition.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["intelligence_definition_gate_test"] = module
    spec.loader.exec_module(module)
    assert module.check() == []


def test_the_gate_ships_the_committed_report() -> None:
    """The report is the artifact the docs cite — it must be committed."""
    report = REPO_ROOT / "docs" / "06-project-management" / "intelligence_report.json"
    assert report.is_file(), "the unified intelligence report must be committed"
