#!/usr/bin/env python3
"""Build the paraphrase benchmark (`benchmarks/data/paraphrase_v1.json`).

The benchmark measures **改述泛化**: a comparison chain is stated in words the
deterministic teacher may not know, and the system must still answer the
superlative. The splits are frozen here so the measurement is reproducible:

- ``heldout_dimensions`` — the taught relation words on dimensions the
  curriculum never teaches (the *development* split: it was used while fixing
  parser bugs, so it is optimistic).
- ``unseen_surfaces`` — relation words the curriculum never teaches at all
  (a development diagnostic: it drove which general synonyms were added).
- ``test`` — taught words on a frozen split with its own seed, entities and
  question phrasings (application, not generalisation).
- ``heldout_final`` — words that appear in no curriculum entry and were not
  used while tuning. This is the dimension's score.

Usage:
    python scripts/build_paraphrase_benchmark.py            # write the file
    python scripts/build_paraphrase_benchmark.py --check    # verify it matches
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT = REPO_ROOT / "benchmarks" / "data" / "paraphrase_v1.json"

# dimension -> (greater comparative, lesser comparative, base adjective,
#               greatest superlatives, least superlatives)
DIMENSIONS: Dict[str, Tuple[str, str, str, List[str], List[str]]] = {
    "size": ("taller", "shorter", "tall", ["tallest", "highest", "top"], ["shortest", "bottom"]),
    "age": ("older", "younger", "old", ["oldest"], ["youngest"]),
    "temperature": ("hotter", "colder", "hot", ["hottest"], ["coldest"]),
    "speed": ("faster", "slower", "fast", ["fastest", "quickest"], ["slowest"]),
    "weight": ("heavier", "lighter", "heavy", ["heaviest"], ["lightest"]),
    "strength": ("stronger", "weaker", "strong", ["strongest"], ["weakest"]),
    "wealth": ("richer", "poorer", "rich", ["richest"], ["poorest"]),
}
#: The dimensions the curriculum teaches; the others are held out.
TAUGHT_DIMENSIONS = ("size", "age", "temperature")
HELDOUT_DIMENSIONS = tuple(d for d in DIMENSIONS if d not in TAUGHT_DIMENSIONS)

# (relation template, direction). The curriculum teaches all of these.
# ``inflected`` surfaces take the dimension's own comparative ("is faster
# than"), which the deterministic teacher already knows; ``lexical`` surfaces
# are fixed relation words, and every one of them must be in the curriculum.
TAUGHT_SURFACES: List[Tuple[str, str]] = [
    ("{A} is {g} than {B}", "greater"),
    ("{A} is {l} than {B}", "lesser"),
    ("{A} exceeds {B}", "greater"),
    ("{A} surpasses {B}", "greater"),
    ("{A} is superior to {B}", "greater"),
    ("{A} dominates {B}", "greater"),
    ("{A} is exceeded by {B}", "lesser"),
    ("{A} is inferior to {B}", "lesser"),
    ("{A} is outclassed by {B}", "lesser"),
]
# The relation words the *evaluation* uses that the curriculum never teaches.
# This split is used to *design* the curriculum (which general synonyms to
# teach), so it is a development split. Its numbers are optimistic.
UNSEEN_SURFACES: List[Tuple[str, str]] = [
    ("{A} outpaces {B}", "greater"),
    ("{A} has the edge over {B}", "greater"),
    ("{A} lags behind {B}", "lesser"),
    ("{A} is beneath {B}", "lesser"),
    # Rotated out of ``heldout_final`` on 2026-10-23: the first four were
    # used to design the passive-inversion and "an unseen word carries no
    # dimension" rules; the second four were used to find the window/subject
    # segmentation bug. They are development surfaces now, not a holdout.
    ("{A} outshines {B}", "greater"),
    ("{A} runs rings around {B}", "greater"),
    ("{A} is dwarfed by {B}", "lesser"),
    ("{A} is beaten by {B}", "lesser"),
    ("{A} towers over {B}", "greater"),
    ("{A} is a cut above {B}", "greater"),
    ("{A} is left behind by {B}", "lesser"),
    ("{A} pales in comparison to {B}", "lesser"),
    # Third rotation: these four found the "ahead of" preposition guard.
    ("{A} outperforms {B}", "greater"),
    ("{A} is far ahead of {B}", "greater"),
    ("{A} is bested by {B}", "lesser"),
    ("{A} is outdone by {B}", "lesser"),
]
# The final holdout: words that appear in no curriculum entry and were not
# used while tuning. This split is the dimension's score.
# Authored after the 2026-10-23 rules were fixed, and run once. They are not
# in the curriculum and were not used to tune anything.
FINAL_SURFACES: List[Tuple[str, str]] = [
    ("{A} outranks {B}", "greater"),
    ("{A} is well ahead of {B}", "greater"),
    ("{A} is outshone by {B}", "lesser"),
    ("{A} is a step behind {B}", "lesser"),
]

#: Function words that may appear in a held-out surface without teaching it.
#: Content words (the verbs and particles that carry the relation) are not
#: here: those are what the split holds out.
FUNCTION_WORDS = frozenset(
    """
    a an the is are was were be been being am
    by to of in on at with from into over under above below behind ahead
    for as than and or not its it
    """.split()
)


def heldout_word_leaks(curriculum_text: str, payload: Dict[str, Any]) -> List[str]:
    """The content words of the held-out splits that appear in the curriculum.

    Word-boundary matching, not substring: "in" is inside "training", and a
    substring test would report a leak for every function word.
    """
    lowered = (curriculum_text or "").lower()
    problems: List[str] = []
    for name in ("unseen_surfaces", "heldout_final"):
        for item in (payload.get("splits") or {}).get(name) or []:
            surface = (item.get("surface") or "").replace("{A}", "").replace("{B}", "")
            for word in re.split(r"[^A-Za-z']+", surface.lower()):
                if not word or word in FUNCTION_WORDS:
                    continue
                if re.search(rf"\b{re.escape(word)}\b", lowered):
                    problems.append(f"{name}: held-out word {word!r} is in the curriculum")
    return problems


ENTITIES = [
    "Alice",
    "Bob",
    "Carol",
    "Dan",
    "Eve",
    "Finn",
    "Gina",
    "Hugo",
    "Iris",
    "Jack",
    "Nina",
    "Otto",
    "Pia",
    "Quinn",
    "Rosa",
    "Sam",
    "the oak",
    "the pine",
    "the birch",
    "the sedan",
    "the van",
    "the truck",
    "the ruby",
    "the sapphire",
    "the pearl",
    "the brick",
    "the stone",
    "the feather",
]

# (question phrasing, direction)
QUESTION_TEMPLATES: List[Tuple[str, str]] = [
    ("who is the {sup}?", "greatest"),
    ("which one is the {sup}?", "greatest"),
    ("who ends up being the {sup}?", "greatest"),
    ("who is the {sup}?", "least"),
    ("which one is the {sup}?", "least"),
    ("who ends up being the {sup}?", "least"),
]


def _question_phrasings(question_pool: List[Tuple[str, str]], direction: str) -> List[str]:
    phrasings = [text for text, want in question_pool if want == direction]
    return phrasings or ["who is the {sup}?"]


def _build(
    dimensions: Tuple[str, ...],
    surfaces: List[Tuple[str, str]],
    seed: int,
    question_pool: List[Tuple[str, str]] = QUESTION_TEMPLATES,
) -> List[Dict[str, str]]:
    rng = random.Random(seed)
    items: List[Dict[str, str]] = []
    for dimension in dimensions:
        greater, lesser, base, superlatives_g, superlatives_l = DIMENSIONS[dimension]
        for template, direction in surfaces:
            for question_direction in ("greatest", "least"):
                first, second, third = rng.sample(ENTITIES, 3)
                if direction == "greater":
                    pairs = ((first, second), (second, third))
                else:
                    pairs = ((second, first), (third, second))
                clauses = [
                    template.format(A=a, B=b, g=greater, l=lesser, base=base) for a, b in pairs
                ]
                superlatives = (
                    superlatives_g if question_direction == "greatest" else superlatives_l
                )
                phrasing = rng.choice(_question_phrasings(question_pool, question_direction))
                question = ", ".join(clauses) + ", " + phrasing.format(sup=rng.choice(superlatives))
                items.append(
                    {
                        "id": f"{dimension}-{len(items):03d}",
                        "q": question,
                        "expected": first if question_direction == "greatest" else third,
                        "dimension": dimension,
                        "surface": template,
                        "surface_kind": (
                            "inflected"
                            if ("{g}" in template or "{l}" in template or "{base}" in template)
                            else "lexical"
                        ),
                        "direction": direction,
                        "question_direction": question_direction,
                    }
                )
    rng.shuffle(items)
    return items


def build() -> Dict[str, Any]:
    return {
        "name": "paraphrase_v2",
        "description": (
            "改述泛化：同一個比較鏈用不同的說法敘述，問最高級。heldout_dimensions "
            "是開發集（修 parser 時看過，偏樂觀）；unseen_surfaces 是開發用嚴格"
            "診斷（課程沒教那些詞，但用來決定要補哪些同義詞）；test 是教過的詞在"
            "新句子上的套用確認集；heldout_final 是從未教過、也沒用來調參的詞，"
            "這一格才是分數。2026-10-23 換過兩次：第一批（outshines／is dwarfed "
            "by…）用來設計被動反轉與「未見詞不帶維度」兩條規則，第二批（towers "
            "over／is a cut above…）用來找出關係窗與主詞切分的 bug；兩批都已降級"
            "為開發集；第三批（outperforms／is far ahead of…）找出「ahead of」"
            "的介系詞守門 bug。現在這批是機制凍結後才寫、只跑一次。"
        ),
        "provenance": {
            "generated_by": "scripts/build_paraphrase_benchmark.py",
            "curriculum": ("apps/backend/configs/standard/reasoning/paraphrase_curriculum.yaml"),
            "taught_dimensions": list(TAUGHT_DIMENSIONS),
            "heldout_dimensions": list(HELDOUT_DIMENSIONS),
            "seeds": {
                "heldout_dimensions": 11,
                "unseen_surfaces": 23,
                "test": 37,
                "heldout_final": 53,
            },
        },
        "splits": {
            # The taught word set on dimensions the curriculum never teaches.
            "heldout_dimensions": _build(HELDOUT_DIMENSIONS, TAUGHT_SURFACES, 11),
            # Words the curriculum never teaches, on every dimension.
            "unseen_surfaces": _build(tuple(DIMENSIONS), UNSEEN_SURFACES, 23),
            # The frozen confirmation split: fresh entities and phrasings.
            "test": _build(tuple(DIMENSIONS), TAUGHT_SURFACES, 37),
            # Never-taught words, never used while tuning: the score.
            "heldout_final": _build(tuple(DIMENSIONS), FINAL_SURFACES, 53),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the committed file")
    args = parser.parse_args()

    payload = build()
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUTPUT.is_file():
            print(f"missing: {OUTPUT.relative_to(REPO_ROOT)}")
            return 1
        if OUTPUT.read_text(encoding="utf-8") != text:
            print("the committed benchmark does not match the generator")
            return 1
        for name, split in payload["splits"].items():
            print(f"  {name}: {len(split)} items")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(text, encoding="utf-8")
    for name, split in payload["splits"].items():
        print(f"  {name}: {len(split)} items")
    print(f"寫入 {OUTPUT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
