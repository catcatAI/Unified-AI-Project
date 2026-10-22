# =============================================================================
# ANGELA-MATRIX: [L2] [γ] [B] [L4]
# =============================================================================
"""The paraphrase benchmark and the curriculum must not leak into each other.

The measurement is only honest if:

1. the benchmark is the generator's output (frozen, reproducible);
2. every *taught* relation word in the evaluation is actually taught;
3. the *held-out* words never appear in the curriculum (otherwise
   "generalisation" is just vocabulary recall);
4. no evaluation sentence appears in the curriculum;
5. no question appears in two splits.

These are data-level contracts, so the test is fast and does not need the
ONNX encoder.
"""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest
from ai.reasoning.paraphrase_curriculum import CURRICULUM_PATH, load_curriculum

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK = REPO_ROOT / "benchmarks" / "data" / "paraphrase_v1.json"
BUILDER = REPO_ROOT / "scripts" / "build_paraphrase_benchmark.py"

TAUGHT_SPLITS = ("heldout_dimensions", "test")
HELD_OUT_SPLITS = ("unseen_surfaces", "heldout_final")


def _payload() -> dict:
    return json.loads(BENCHMARK.read_text(encoding="utf-8"))


def _surface_text(item: dict) -> str:
    """The relation words of an item, without the entity placeholders."""
    return (item["surface"] or "").replace("{A}", "").replace("{B}", "").strip()


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[^A-Za-z']+", text.lower()) if w]


def test_benchmark_file_exists() -> None:
    assert BENCHMARK.is_file(), "run scripts/build_paraphrase_benchmark.py"


def test_benchmark_matches_generator() -> None:
    spec = importlib.util.spec_from_file_location("paraphrase_bench_builder", BUILDER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    generated = json.dumps(module.build(), ensure_ascii=False, indent=2) + "\n"
    assert BENCHMARK.read_text(encoding="utf-8") == generated


def test_all_splits_are_present_and_non_empty() -> None:
    splits = _payload()["splits"]
    assert set(splits) >= set(TAUGHT_SPLITS) | set(HELD_OUT_SPLITS)
    for name, items in splits.items():
        assert items, f"{name} is empty"


def test_question_is_not_in_two_splits() -> None:
    splits = _payload()["splits"]
    seen: dict[str, str] = {}
    for name, items in splits.items():
        for item in items:
            assert item["q"] not in seen, f"{item['q']} in {seen.get(item['q'])} and {name}"
            seen[item["q"]] = name


def test_expected_answer_is_one_of_the_chain_entities() -> None:
    for items in _payload()["splits"].values():
        for item in items:
            assert item["expected"] in item["q"]


def test_curriculum_loads_and_validates() -> None:
    entries = load_curriculum()
    assert len(entries) >= 13
    for entry in entries:
        assert entry["direction"] in ("greater", "lesser")
        assert entry["phrase"].strip()


def test_taught_lexical_surfaces_are_in_the_curriculum() -> None:
    text = CURRICULUM_PATH.read_text(encoding="utf-8")
    for name in TAUGHT_SPLITS:
        for item in _payload()["splits"][name]:
            if item["surface_kind"] != "lexical":
                continue
            surface = _surface_text(item)
            assert surface in text, f"taught surface {surface!r} missing from the curriculum"


def test_held_out_words_are_not_in_the_curriculum() -> None:
    text = CURRICULUM_PATH.read_text(encoding="utf-8").lower()
    for name in HELD_OUT_SPLITS:
        for item in _payload()["splits"][name]:
            if item["surface_kind"] != "lexical":
                continue
            for word in _words(_surface_text(item)):
                if word in {"a", "an", "the", "is", "by", "to", "over", "of", "behind", "around"}:
                    continue
                assert word not in text, f"held-out word {word!r} leaked into the curriculum"


@pytest.mark.parametrize("name", list(TAUGHT_SPLITS) + list(HELD_OUT_SPLITS))
def test_no_evaluation_sentence_is_in_the_curriculum(name: str) -> None:
    text = CURRICULUM_PATH.read_text(encoding="utf-8")
    for item in _payload()["splits"][name]:
        assert item["q"] not in text
