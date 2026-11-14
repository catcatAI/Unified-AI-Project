#!/usr/bin/env python3
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# LAYER: learning
"""The pantry-ecosystem corpus, v2: four chains, and no turn gives the answer.

Why v1 was not enough
---------------------
v1 had one investigation shape: the janitor sees the culprit leave the pantry,
and that sentence contains the culprit's name. A model that learns "read the
sentence with 清潔阿姨" scores 1.0 without reasoning about the timeline or the
roster. The corpus was *extractive*: one turn held the answer and the rest was
decoration.

v2 removes the extractive path structurally rather than statistically:

1. **A turn that names people names everybody.** Every naming turn is a roll
   call or a roster; every evidence turn describes a *value* (a colour, a badge
   id) and names nobody. So "take the name out of the evidence turn" has
   nothing to take, and "the first / last / Nth name" is uniform over the roster.
   ``_validate_name_balance`` is a gate, not a hope.
2. **Every chain is value -> roster -> person, under a time filter.** Four types
   are drawn at random, and the filter is what makes the evidence selective:

   ========== ========================== ==================================
   chain      evidence value             filter that selects it
   ========== ========================== ==================================
   ``apron``  apron colour               none (the sighting is at theft time)
   ``badge``  badge id on a door entry   that entry's time is inside the window
   ``ledger`` badge id on a checkout row item is the target **and** time inside
   ``window`` badge id on a floor pass   the pass interval covers the window
   ========== ========================== ==================================

   Decoys are structurally identical (a second entry at another time, a row for
   another item, a pass that only overlaps the wide window), so filtering needs
   the bounds *and* the roster.
3. **The deduction is verified, not asserted.** Each turn carries machine
   readable ``asserts`` generated from the same hidden plan as its prose, and
   ``_validate_necessity`` runs a solver: the full set must yield exactly the
   oracle's culprit, and dropping any *load-bearing* turn must not still yield
   exactly the culprit. If one turn were sufficient, the gate fails.
4. **Non-monotonic by construction.** One evidence value is wrong and a later
   turn retracts it while asserting the right one. Honouring both without
   retraction yields two candidates, so a state that accumulates instead of
   overwriting cannot answer. ``_validate_retraction`` computes exactly that.
5. **The statistical check is a confirmation.** ``_validate_shortcuts`` runs
   surface baselines (first / last / most-mentioned actor, "the actor named in
   the turn containing 主管") and requires each one's 95% Wilson upper bound to
   stay within ``chance + 0.10``. Rule 1 makes them chance by construction.

Usage::

    ./.venv/bin/python scripts/gen_pantry_ecosystem.py --sessions 200
    ./.venv/bin/python scripts/gen_pantry_ecosystem.py --check

The dataset is data, not a score. Nothing here measures a model, and the
trainer that consumes it (with its own pre-registration) is a separate round.

Deviations from the spec as handed in (recorded, not silent)
-----------------------------------------------------------
1. **Names recur across sessions.** A twelve-name pool cannot be disjoint while
   still training a binding. The gate is on the *answer tuple* (chain, culprit,
   target, window, evidence value) and on the session id, both disjoint. Every
   name appears as culprit and as innocent on both sides, and no evidence turn
   names anyone, so a name cannot be the answer.
2. **Verbatim text repeats across splits.** With a fixed template family at 200
   sessions, disjoint sentences would shrink the corpus to a few dozen. This is
   *intended* for the two-stage plan: the text stage learns the language
   (shared), the pantry stage measures reasoning on answer tuples it has never
   seen. The gate therefore reports text overlap and gates on the answer tuple.
3. **``dt_s`` is consistent with a real turn timeline**: the conversation clock
   advances by exactly the drawn gap.
4. **Three extra top-level keys** (``schema_version``, ``session_meta``,
   per-turn ``asserts``) plus a sidecar manifest, so a corpus can be regenerated
   and audited.
5. **The oracle tag never appears in the prose.** It is a composite
   (``chain=...|value=...|t=...``); a gate fails if it occurs verbatim.
6. **The four chains share the value/roster shape.** That is the point: the
   difference is the *filter*, not a new puzzle. A corpus of four unrelated
   puzzles would measure transfer between puzzles; this measures whether one
   rule ("select by time, then look up") is applied to four filters.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_VERSION = "pantry-ecosystem-v2"
DEFAULT_OUT = "data/pantry_ecosystem/sessions.jsonl"
DEFAULT_SEED = 20261113
DEFAULT_SESSIONS = 200
DEFAULT_HELDOUT_FRACTION = 0.2

CHAINS = ("apron", "badge", "ledger", "window")

ACTORS = (
    "Alex",
    "Betty",
    "Chris",
    "David",
    "Elena",
    "Frank",
    "Grace",
    "Hana",
    "Ivan",
    "Judy",
    "Kevin",
    "Lena",
)

# ``key`` is the oracle/tag name; the value is what the testimony calls it.
ITEMS = {
    "pepperoni_pizza": ("雙倍起司披薩", "塊"),
    "matcha_mochi": ("抹茶大福", "顆"),
    "soy_milk": ("豆漿", "瓶"),
    "cold_brew": ("冷萃咖啡", "杯"),
    "egg_tart": ("蛋塔", "個"),
    "yogurt": ("優格", "杯"),
    "bubble_tea": ("珍珠奶茶", "杯"),
    "sandwich": ("三明治", "份"),
}

COLOURS = {
    "red": "紅色",
    "blue": "藍色",
    "green": "綠色",
    "grey": "灰色",
    "black": "黑色",
    "white": "白色",
    "orange": "橘色",
    "purple": "紫色",
}

# People who are not on the roll call. They carry observations, never names of
# suspects, so the marker they introduce cannot point at an actor.
WITNESSES = ("清潔阿姨", "警衛", "送貨員", "實習生", "櫃檯人員")

# (weight, low seconds, high seconds), log-uniform inside the band.
DT_BANDS: Tuple[Tuple[float, float, float], ...] = (
    (0.40, 10.0, 60.0),
    (0.40, 300.0, 1800.0),
    (0.20, 3600.0, 14400.0),
)

MAX_SLOTS = 16
CHANCE_MARGIN = 0.10  # a shortcut may not exceed chance by more than this
POWER_MIN = 100  # answered sessions before the Wilson bound is used as a gate
# Markers that actually occur, so the audit tests real shortcuts instead of
# silently reporting "answered: 0". Each one introduces a turn; the guess is
# "the first actor named in that turn".
SHORTCUT_MARKERS = ("主管", "值班表", "卡號", "登記簿", "更正")

VERDICT_MARKERS = (
    "兇手",
    "犯人",
    "就是他",
    "是她吃的",
    "是他吃的",
    "確定是",
    "the culprit is",
    "ate it",
)


def _fmt(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _parse(stamp: str) -> int:
    hour, minute = stamp.split(":")
    return int(hour) * 60 + int(minute)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _band_for(seconds: float) -> str:
    if seconds < 300.0:
        return "short"
    if seconds < 3600.0:
        return "mid"
    return "long"


def _sample_dt(rng: random.Random) -> float:
    roll = rng.random()
    cumulative = 0.0
    for weight, low, high in DT_BANDS:
        cumulative += weight
        if roll <= cumulative:
            lo, hi = math.log10(low), math.log10(high)
            return round(10.0 ** rng.uniform(lo, hi), 1)
    lo, hi = math.log10(DT_BANDS[-1][1]), math.log10(DT_BANDS[-1][2])
    return round(10.0 ** rng.uniform(lo, hi), 1)


# --------------------------------------------------------------------------- #
# the solver: what a reader can conclude from a set of turns
# --------------------------------------------------------------------------- #
def derive(
    asserts: Sequence[Tuple[int, Dict[str, Any]]],
    actors: Sequence[str],
    *,
    honour_retract: bool = True,
) -> List[str]:
    """Candidates still consistent with ``asserts``.

    ``asserts`` is ``(turn_index, assert)`` so a retraction can remove exactly
    the turn it names. These are the rules an investigator would use, and no
    rule reads a name out of the prose:

    * ``window`` narrows the theft interval (intersection);
    * ``seen`` / ``entry`` / ``checkout`` / ``access`` contribute an evidence
      *value* (a colour key or a badge id) when their own filter lets them in;
    * ``roster`` maps a value to a person;
    * ``retract`` drops the asserts of the turn it names.

    ``honour_retract=False`` answers "what would a reader believe who never
    throws anything away?" - the control used to prove the corpus is
    non-monotonic.
    """
    retractions = [
        (item["target"], set(item.get("kinds") or ()))
        for _, item in asserts
        if item["kind"] == "retract"
    ]

    def is_retracted(turn: int, item: Dict[str, Any]) -> bool:
        if not honour_retract:
            return False
        for target, kinds in retractions:
            if target == turn and (not kinds or item["kind"] in kinds):
                return True
        return False

    live = [(turn, item) for turn, item in asserts if not is_retracted(turn, item)]

    window: Tuple[int, int] | None = None
    roster: Dict[str, str] = {}
    pending: List[Dict[str, Any]] = []
    for _, item in live:
        kind = item["kind"]
        if kind == "window":
            lo, hi = _parse(item["lo"]), _parse(item["hi"])
            window = (lo, hi) if window is None else (max(window[0], lo), min(window[1], hi))
        elif kind == "roster":
            roster.update(item["value"])
        elif kind in {"seen", "entry", "checkout", "access"}:
            pending.append(item)

    values: List[str] = []
    for item in pending:
        kind = item["kind"]
        if kind == "seen":
            stamp = item.get("t")
            if stamp is None or window is None or window[0] <= _parse(stamp) <= window[1]:
                values.append(item["value"])
        elif kind == "entry":
            stamp = item.get("t")
            if stamp is not None and window is not None:
                if not (window[0] <= _parse(stamp) <= window[1]):
                    continue
            values.append(item["id"])
        elif kind == "checkout":
            if item["item"] != item["target"]:
                continue
            if window is not None and not (window[0] <= _parse(item["t"]) <= window[1]):
                continue
            values.append(item["id"])
        else:  # access
            lo, hi = _parse(item["lo"]), _parse(item["hi"])
            if window is not None and not (lo <= window[1] and hi >= window[0]):
                continue
            values.append(item["id"])

    candidates = set(actors)
    # Several rows can carry the same kind of evidence (the ledger lists several
    # checkouts); they are alternatives, so the candidate set is their *union*.
    # An unmapped value is no information at all, which is what makes the
    # roster turn necessary.
    mapped = {roster[value] for value in values if value in roster}
    if mapped:
        candidates &= mapped
    return sorted(candidates)


def _all_asserts(session: Dict[str, Any]) -> List[Tuple[int, Dict[str, Any]]]:
    return [
        (turn["turn_id"], item) for turn in session["turns"] for item in turn.get("asserts", [])
    ]


def _validate_necessity(session: Dict[str, Any]) -> List[str]:
    """The full testimony identifies one person, and every load-bearing turn is needed."""
    actors = session["environment"]["actors"]
    culprit = session["ground_truth_oracle"]["culprit"]
    chain_turns = session["session_meta"].get("chain_turns")
    sid = session["session_id"]

    if not chain_turns:
        return [f"{sid}: no chain_turns recorded"]

    full = derive(_all_asserts(session), actors)
    if full != [culprit]:
        return [f"{sid}: testimony derives {full}, not [{culprit}]"]

    out: List[str] = []
    for turn_id in chain_turns:
        reduced = [(index, item) for index, item in _all_asserts(session) if index != turn_id]
        candidates = derive(reduced, actors)
        if candidates == [culprit]:
            out.append(
                f"{sid}: chain turn {turn_id} can be dropped and the answer is unchanged; "
                "it is decoration, not evidence"
            )
    return out


def _validate_retraction(session: Dict[str, Any]) -> List[str]:
    """A reader who never retracts must not get the right answer.

    That is the operational meaning of "non-monotonic": the winning state is not
    the union of everything that was said.
    """
    sid = session["session_id"]
    actors = session["environment"]["actors"]
    culprit = session["ground_truth_oracle"]["culprit"]
    turns = session["turns"]

    retracted = [
        turn["turn_id"] for turn in turns if "retract" in {i["kind"] for i in turn["asserts"]}
    ]
    if not retracted:
        return [f"{sid}: no retraction; the session is monotonic and cannot test overwriting"]

    naive = derive(_all_asserts(session), actors, honour_retract=False)
    if naive == [culprit]:
        return [
            f"{sid}: ignoring the retraction still gives [{culprit}]; "
            "retracting nothing is not a mistake here"
        ]
    return []


def _named(text: str, actors: Sequence[str]) -> List[str]:
    return [name for name in actors if name in text]


def _validate_name_balance(session: Dict[str, Any]) -> List[str]:
    """Every turn must name *nobody* or *everybody*.

    Naming a subset (even two of seven) leaves a positional cue: "the first name
    in the turn that mentions 主管" is then right more often than chance. Only a
    turn that names nobody (it carries a value) or the whole floor can carry the
    deduction, and the deduction reads the value, not the name.
    """
    sid = session["session_id"]
    actors = session["environment"]["actors"]
    out = []
    for turn in session["turns"]:
        named = _named(turn["user_input"], actors)
        if named and len(named) != len(actors):
            out.append(
                f"{sid}: turn {turn['turn_id']} names {len(named)} of {len(actors)} "
                f"actors ({', '.join(named)}); a reader could use a positional cue"
            )
    return out


def _shortcut_guesses(session: Dict[str, Any]) -> Dict[str, str | None]:
    """Surface baselines a pattern-matching model could actually use."""
    actors = session["environment"]["actors"]
    flat = [(turn["turn_id"], turn["user_input"]) for turn in session["turns"]]
    text = "".join(payload for _, payload in flat)

    positions = sorted((text.find(name), name) for name in actors if name in text)
    guesses: Dict[str, str | None] = {
        "first_named": positions[0][1] if positions else None,
        "last_named": positions[-1][1] if positions else None,
    }

    counts = {name: text.count(name) for name in actors}
    best = max(counts.values())
    guesses["most_mentioned"] = next((name for name in actors if counts[name] == best), None)

    for marker in SHORTCUT_MARKERS:
        found = None
        for _, payload in flat:
            if marker in payload:
                named = _named(payload, actors)
                found = named[0] if named else None
                break
        guesses[f"turn_with:{marker}"] = found
    return guesses


def _wilson_upper(successes: int, total: int, z: float = 1.96) -> float:
    if total <= 0:
        return 1.0
    p = successes / total
    denominator = 1.0 + z * z / total
    centre = p + z * z / (2.0 * total)
    spread = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total))
    return (centre + spread) / denominator


def shortcut_audit(sessions: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Per-baseline accuracy with a 95% upper bound against per-session chance."""
    tallies: Dict[str, Dict[str, float]] = {}
    for session in sessions:
        culprit = session["ground_truth_oracle"]["culprit"]
        chance = 1.0 / len(session["environment"]["actors"])
        for name, guess in _shortcut_guesses(session).items():
            row = tallies.setdefault(name, {"answered": 0, "correct": 0, "chance": 0.0})
            if guess is None:
                continue
            row["answered"] += 1
            row["correct"] += int(guess == culprit)
            row["chance"] += chance
    report = {}
    for name, row in sorted(tallies.items()):
        answered = int(row["answered"])
        correct = int(row["correct"])
        report[name] = {
            "answered": answered,
            "accuracy": round(correct / answered, 4) if answered else None,
            "chance": round(row["chance"] / answered, 4) if answered else None,
            "upper95": round(_wilson_upper(correct, answered), 4) if answered else None,
            "powered": answered >= POWER_MIN,
        }
    return report


def _validate_shortcuts(sessions: Sequence[Dict[str, Any]]) -> List[str]:
    """Gate a baseline only where the corpus can distinguish chance from chance+0.10.

    With 5-8 actors, chance is 0.125-0.20, so ``chance + 0.10`` is roughly two
    standard errors wide at n=100 and wider than that below it. Gating an
    underpowered baseline would reject a correct corpus on sampling noise (at 40
    sessions the apron roster marker answers 10 times, and 3/10 is exactly what
    chance looks like). So:

    * ``answered >= POWER_MIN`` -> the 95% Wilson upper bound must stay under
      ``chance + CHANCE_MARGIN``;
    * below that, the baseline is reported with ``powered: false`` and is *not*
      a gate. The structural rule (``_validate_name_balance``) still runs on
      every session at any corpus size, so a turn that names a subset fails
      regardless of statistics.
    """
    out: List[str] = []
    for name, row in shortcut_audit(sessions).items():
        if not row["answered"] or row["chance"] is None:
            continue
        if row["answered"] < POWER_MIN:
            continue
        line = row["chance"] + CHANCE_MARGIN
        if row["upper95"] > line:
            out.append(
                f"shortcut {name!r} reaches {row['accuracy']:.3f} "
                f"(upper 95% {row['upper95']:.3f}, n={row['answered']}) "
                f"vs chance {row['chance']:.3f}"
            )
    return out


# --------------------------------------------------------------------------- #
# the generator
# --------------------------------------------------------------------------- #
class PantryEcosystemSynthesizer:
    """Deterministic generator of multi-chain pantry investigations.

    A session's randomness is derived from ``f"{seed}:{index}:{salt}"``, so
    session *i* is identical whether the corpus has 10 lines or 10,000. The only
    corpus-level state is the set of answer tuples already used, needed to keep
    the splits disjoint, and it is applied in index order (also deterministic).
    """

    def __init__(
        self,
        *,
        seed: int = DEFAULT_SEED,
        sessions: int = DEFAULT_SESSIONS,
        heldout_fraction: float = DEFAULT_HELDOUT_FRACTION,
        actors: Sequence[str] = ACTORS,
        items: Dict[str, Tuple[str, str]] = ITEMS,
    ) -> None:
        if sessions <= 0:
            raise ValueError("sessions must be > 0")
        if not 0.0 < heldout_fraction < 1.0:
            raise ValueError("heldout_fraction must be in (0, 1)")
        if len(actors) < 8:
            raise ValueError("need at least 8 actors for a 5-8 person session")
        if len(items) < 4:
            raise ValueError("need at least 4 items for 1 target + 3 distractors")

        self.seed = int(seed)
        self.sessions = int(sessions)
        self.heldout_fraction = float(heldout_fraction)
        self.actors = tuple(actors)
        self.items = dict(items)
        self._period = max(2, int(round(1.0 / self.heldout_fraction)))

    # -- public -------------------------------------------------------------

    def split_of(self, index: int) -> str:
        return "heldout" if index % self._period == 0 else "train"

    def is_heldout(self, index: int) -> bool:
        """Interleaved, so both sides see the same range of session structures."""
        return index % self._period == 0

    def generate(self) -> Dict[str, List[Dict[str, Any]]]:
        used: Dict[str, set] = {"answer": set()}
        train: List[Dict[str, Any]] = []
        heldout: List[Dict[str, Any]] = []
        for index in range(self.sessions):
            session = self._session(index, used)
            (heldout if self.is_heldout(index) else train).append(session)
        if not train or not heldout:
            raise ValueError(
                "heldout_fraction produced an empty split; use --sessions >= " f"{self._period + 1}"
            )
        return {"train": train, "heldout": heldout}

    # -- one session --------------------------------------------------------

    def _session(self, index: int, used: Dict[str, set]) -> Dict[str, Any]:
        for salt in range(128):
            rng = random.Random(f"{self.seed}:{index}:{salt}")
            session = self._render(index, rng)
            key = self._answer_key(session)
            if key in used["answer"]:
                continue
            used["answer"].add(key)
            return session
        raise RuntimeError(f"could not make session {index} unique after 128 attempts")

    @staticmethod
    def _answer_key(session: Dict[str, Any]) -> str:
        oracle = session["ground_truth_oracle"]
        return "|".join(
            str(oracle[name])
            for name in ("chain", "culprit", "target_item", "window", "evidence_tag")
        )

    def _render(self, index: int, rng: random.Random) -> Dict[str, Any]:
        size = rng.randint(5, 8)
        actors = rng.sample(self.actors, size)
        target_key = rng.choice(sorted(self.items))
        distractors = rng.sample(
            [key for key in sorted(self.items) if key != target_key], rng.randint(2, 3)
        )
        chain = rng.choice(CHAINS)
        culprit, trap_actor, herring = rng.sample(actors, 3)
        target_zh, unit = self.items[target_key]
        decoy_item_zh = self.items[distractors[0]][0]
        other_item_zh = self.items[distractors[-1]][0]

        action = rng.randint(17 * 60 + 30, 19 * 60)
        opening = action - rng.randint(55, 70)
        now = action + rng.randint(30, 50)
        impossible = opening - rng.randint(5, 25)
        window_lo = action - rng.randint(6, 12)
        window_hi = action + rng.randint(6, 12)
        # Bounds wide enough to leave room for a decoy on either side: dropping
        # either bound must admit exactly one more person, or the bounds are not
        # doing any work.
        # Keep at least five minutes between a decoy and the bound it misses:
        # a one-minute gap is a coin flip on tokenisation, not a reasoning test.
        bound_lo = opening + rng.randint(12, max(12, window_lo - opening - 1))
        bound_hi = window_hi + rng.randint(6, max(6, (now - window_hi) // 2))
        missing = rng.randint(2, 4)
        witness_a, witness_b = rng.sample(WITNESSES, 2)

        badges = {name: f"{rng.randint(100, 999)}" for name in actors}
        while len(set(badges.values())) != len(badges):
            badges = {name: f"{rng.randint(100, 999)}" for name in actors}

        turns: List[Dict[str, Any]] = []
        chain_turns: List[int] = []

        def add(
            text: str,
            asserts: Sequence[Dict[str, Any]] = (),
            tags: Sequence[str] = (),
            required: bool = False,
        ) -> int:
            turn_id = len(turns)
            turns.append(
                {
                    "turn_id": turn_id,
                    "dt_s": 0.0,
                    "user_input": text,
                    "asserts": [dict(item, turn=turn_id) for item in asserts],
                    "expected_internal_focus": list(tags) or ["no_focus"],
                }
            )
            if required:
                chain_turns.append(turn_id)
            return turn_id

        # turn 0: the crime exists (nobody named)
        add(
            f"下午 {_fmt(opening)} 點了{target_zh}放茶水間，順便冰了{decoy_item_zh}。"
            f"現在 {_fmt(now)}，{target_zh}少了 {missing} {unit}，"
            f"{other_item_zh}好像也被動過。",
            tags=[f"{target_key}_missing_{missing}", f"{distractors[0]}_checked"],
        )

        # The roll call is the first turn that names anyone, and it names
        # everyone. It also carries every shortcut marker, so each marker
        # baseline is answered by the whole corpus rather than by one chain out
        # of four - otherwise the audit has no power on the rarer chains.
        add(
            "主管盤點今天下午在這一層的人，值班表、門禁卡號、登記簿和更正紀錄都攤在桌上："
            + "、".join(rng.sample(list(actors), len(actors)))
            + "，名單上就這幾個。",
            tags=["roll_call"],
        )

        # turn 2-3: the two bounds (nobody named)
        add(
            f"{witness_a} 說 {_fmt(bound_lo)} 經過茶水間時，{target_zh}還在架上而且沒開過。",
            [{"kind": "window", "lo": _fmt(bound_lo), "hi": _fmt(now)}],
            ["window_lower_bound"],
            required=chain != "apron",
        )
        add(
            f"{witness_b} 說 {_fmt(bound_hi)} 再看，裝{target_zh}的盒子已經空了。",
            [{"kind": "window", "lo": _fmt(opening), "hi": _fmt(bound_hi)}],
            ["window_upper_bound"],
            required=chain != "apron",
        )

        # a claim that the timeline itself rules out: before the food arrived
        add(
            f"{rng.choice(WITNESSES)} 說 {_fmt(impossible)} 聽到茶水間有人在講話，"
            f"但那個時間{target_zh}還沒送到。",
            tags=["time_confusion_rejected"],
        )

        # -- the chain: a wrong value first, the right one in the correction --
        evidence_value = ""
        trap_text = ""
        trap_asserts: List[Dict[str, Any]] = []
        truth_text = ""
        truth_asserts: List[Dict[str, Any]] = []
        roster_text = ""
        roster_assert: Dict[str, Any]

        if chain == "apron":
            colours = rng.sample(sorted(COLOURS), len(actors))
            mapping = {colours[0]: trap_actor, colours[1]: culprit}
            for colour, actor in zip(
                colours[2:], [a for a in actors if a not in (trap_actor, culprit)]
            ):
                mapping[colour] = actor
            evidence_value = COLOURS[colours[1]]
            trap_text = (
                f"{witness_a} 說 {_fmt(action)} 看到一個人從茶水間出來，"
                f"穿著{COLOURS[colours[0]]}的圍裙，手裡拿著紙巾擦嘴。"
            )
            trap_asserts = [{"kind": "seen", "value": colours[0], "t": _fmt(action)}]
            truth_text = (
                f"更正：監視器畫面裡那件圍裙是{COLOURS[colours[1]]}，不是"
                f"{COLOURS[colours[0]]}；剛才看錯了。"
            )
            truth_asserts = [{"kind": "seen", "value": colours[1], "t": _fmt(action)}]
            roster_text = (
                "今天值班表上寫著："
                + "、".join(f"{COLOURS[key]}是 {actor}" for key, actor in mapping.items())
                + "。"
            )
            roster_assert = {"kind": "roster", "value": mapping}
        elif chain == "badge":
            mapping = {badges[name]: name for name in actors}
            evidence_value = badges[culprit]
            early, late = [a for a in actors if a not in (culprit, trap_actor)][:2]
            early_time = bound_lo - rng.randint(5, 10)
            late_time = bound_hi + rng.randint(5, 8)
            trap_text = (
                f"門口感應紀錄顯示茶水間的門今天下午被刷過三次："
                f"{_fmt(early_time)} 卡號 {badges[early]}、{_fmt(action)} 卡號 "
                f"{badges[trap_actor]}、{_fmt(late_time)} 卡號 {badges[late]}。"
            )
            trap_asserts = [
                {"kind": "entry", "id": badges[early], "t": _fmt(early_time)},
                {"kind": "entry", "id": badges[trap_actor], "t": _fmt(action)},
                {"kind": "entry", "id": badges[late], "t": _fmt(late_time)},
            ]
            truth_text = (
                f"更正：{_fmt(action)} 那筆 {badges[trap_actor]} 是隔壁辦公室的門，"
                f"不是茶水間；茶水間那個時間的紀錄是 {badges[culprit]}。"
            )
            truth_asserts = [
                {"kind": "entry", "id": badges[early], "t": _fmt(early_time)},
                {"kind": "entry", "id": badges[culprit], "t": _fmt(action)},
                {"kind": "entry", "id": badges[late], "t": _fmt(late_time)},
            ]
            roster_text = (
                "人事那邊的卡號對照："
                + "、".join(f"{value} 是 {name}" for value, name in mapping.items())
                + "。"
            )
            roster_assert = {"kind": "roster", "value": mapping}
        elif chain == "ledger":
            mapping = {badges[name]: name for name in actors}
            evidence_value = badges[culprit]
            early, late = [a for a in actors if a not in (culprit, trap_actor)][:2]
            early_time = bound_lo - rng.randint(5, 10)
            late_time = bound_hi + rng.randint(5, 8)
            trap_time = action
            truth_time = bound_lo - rng.randint(5, 8)

            def ledger_rows(trap_stamp: int) -> List[Tuple[int, str, str, str]]:
                rows = [
                    (action, badges[culprit], target_key, target_zh),
                    (early_time, badges[early], target_key, target_zh),
                    (late_time, badges[late], target_key, target_zh),
                    (trap_stamp, badges[trap_actor], target_key, target_zh),
                    (action, badges[herring], distractors[0], decoy_item_zh),
                ]
                rng.shuffle(rows)
                return rows

            trap_rows = ledger_rows(trap_time)
            truth_rows = ledger_rows(truth_time)
            trap_text = (
                "冰箱的取用登記簿有這幾筆："
                + "；".join(
                    f"{_fmt(stamp)} {badge} 取了{item_zh}" for stamp, badge, _, item_zh in trap_rows
                )
                + "。"
            )
            trap_asserts = [
                {
                    "kind": "checkout",
                    "id": badge,
                    "item": item_key,
                    "target": target_key,
                    "t": _fmt(stamp),
                }
                for stamp, badge, item_key, _ in trap_rows
            ]
            truth_text = (
                f"更正：登記簿上 {_fmt(trap_time)} 那筆時間寫錯了，"
                f"其實是 {_fmt(truth_time)}，跟失竊無關。"
            )
            truth_asserts = [
                {
                    "kind": "checkout",
                    "id": badge,
                    "item": item_key,
                    "target": target_key,
                    "t": _fmt(stamp),
                }
                for stamp, badge, item_key, _ in truth_rows
            ]
            roster_text = (
                "登記簿上的編號對照："
                + "、".join(f"{value} 是 {name}" for value, name in mapping.items())
                + "。"
            )
            roster_assert = {"kind": "roster", "value": mapping}
        else:  # window
            mapping = {badges[name]: name for name in actors}
            evidence_value = badges[culprit]
            others = [a for a in actors if a not in (culprit, trap_actor)]
            early, late = others[0], others[1]
            # the culprit is on the floor for the whole window; the two decoys
            # only overlap the *wide* window, so dropping one bound admits them
            trap_text = (
                "訪客系統匯出的時段（卡號）："
                f"{badges[culprit]} {_fmt(bound_lo - 2)}-{_fmt(bound_hi + 2)}、"
                f"{badges[early]} {_fmt(opening + 1)}-{_fmt(bound_lo - 1)}、"
                f"{badges[late]} {_fmt(bound_hi + 1)}-{_fmt(now - 1)}、"
                f"{badges[trap_actor]} {_fmt(window_lo - 1)}-{_fmt(window_hi + 1)}。"
            )
            trap_asserts = [
                {
                    "kind": "access",
                    "id": badges[culprit],
                    "lo": _fmt(bound_lo - 2),
                    "hi": _fmt(bound_hi + 2),
                },
                {
                    "kind": "access",
                    "id": badges[early],
                    "lo": _fmt(opening + 1),
                    "hi": _fmt(bound_lo - 1),
                },
                {
                    "kind": "access",
                    "id": badges[late],
                    "lo": _fmt(bound_hi + 1),
                    "hi": _fmt(now - 1),
                },
                {
                    "kind": "access",
                    "id": badges[trap_actor],
                    "lo": _fmt(window_lo - 1),
                    "hi": _fmt(window_hi + 1),
                },
            ]
            truth_text = (
                f"更正：訪客系統把 {badges[trap_actor]} 的時段接錯了，"
                f"那個區間其實是 {_fmt(opening - 25)}-{_fmt(opening - 5)}，人不在場。"
            )
            truth_asserts = [
                {
                    "kind": "access",
                    "id": badges[culprit],
                    "lo": _fmt(bound_lo - 2),
                    "hi": _fmt(bound_hi + 2),
                },
                {
                    "kind": "access",
                    "id": badges[early],
                    "lo": _fmt(opening + 1),
                    "hi": _fmt(bound_lo - 1),
                },
                {
                    "kind": "access",
                    "id": badges[late],
                    "lo": _fmt(bound_hi + 1),
                    "hi": _fmt(now - 1),
                },
                {
                    "kind": "access",
                    "id": badges[trap_actor],
                    "lo": _fmt(opening - 25),
                    "hi": _fmt(opening - 5),
                },
            ]
            roster_text = (
                "訪客系統的卡號對照："
                + "、".join(f"{value} 是 {name}" for value, name in mapping.items())
                + "。"
            )
            roster_assert = {"kind": "roster", "value": mapping}

        trap_turn = add(trap_text, trap_asserts, [f"{chain}_evidence", "wrong_value"])
        roster_turn = add(roster_text, [roster_assert], ["roster_lookup"], required=True)
        correction_turn = add(
            truth_text,
            [{"kind": "retract", "target": trap_turn}] + truth_asserts,
            ["claim_corrected", "non_monotonic_update"],
            required=True,
        )

        # everyone's own account: names nobody, keeps mention counts balanced
        add(
            "問了一輪，每個人都說自己整個下午都在座位上，沒有人記得去過茶水間。",
            tags=["statement_roundup"],
        )

        # a red herring with the same shape as the evidence, outside the window
        add(
            f"登記簿上還有一筆 {_fmt(action - rng.randint(20, 45))} 有人拿了{decoy_item_zh}，"
            f"但那是下午茶時間，跟{target_zh}無關。",
            tags=["red_herring", "decoy_time_window"],
        )

        # final question
        add(
            "好，根據目前的口供和時間線交叉比對，"
            f"你認為誰是吃掉{target_zh}的人？請給出你的最終推論。",
            tags=["final_deduction"],
        )
        turns[-1]["expected_final_deduction"] = culprit

        for position, turn in enumerate(turns):
            turn["dt_s"] = 0.0 if position == 0 else _sample_dt(rng)

        return {
            "session_id": f"ecosystem_pantry_{index:03d}",
            "schema_version": SCHEMA_VERSION,
            "session_meta": {
                "seed": self.seed,
                "index": index,
                "split": self.split_of(index),
                "chain": chain,
                "chain_turns": sorted(set(chain_turns)),
                "evidence_turn": trap_turn,
                "roster_turn": roster_turn,
                "correction_turn": correction_turn,
                "slots": len(actors) + len(distractors) + 1 + 3,
                "timeline": {
                    "impossible_claim": _fmt(impossible),
                    "opening": _fmt(opening),
                    "window_lo": _fmt(window_lo),
                    "window_hi": _fmt(window_hi),
                    "action": _fmt(action),
                    "now": _fmt(now),
                },
            },
            "environment": {
                "actors": list(actors),
                "items": [target_key] + list(distractors),
                "badges": dict(badges),
            },
            "ground_truth_oracle": {
                "chain": chain,
                "target_item": target_key,
                "culprit": culprit,
                "action_time": _fmt(action),
                "window": f"{_fmt(window_lo)}-{_fmt(window_hi)}",
                "window_bounds": f"{_fmt(bound_lo)}-{_fmt(bound_hi)}",
                "evidence_tag": f"chain={chain}|value={evidence_value}|t={_fmt(action)}",
            },
            "turns": turns,
        }

    # -- gates --------------------------------------------------------------

    @staticmethod
    def validate(splits: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Every data-side gate, as a list of violations a reader can act on."""
        problems: List[str] = []
        for split, sessions in splits.items():
            for session in sessions:
                problems.extend(_validate_session(session, split))

        train = splits.get("train", [])
        heldout = splits.get("heldout", [])
        if train and heldout:
            problems.extend(_validate_split(train, heldout))
        everything = list(train) + list(heldout)
        if everything:
            problems.extend(_validate_shortcuts(everything))
        return problems


# --------------------------------------------------------------------------- #
# §61: counterfactual twins
# --------------------------------------------------------------------------- #
COUNTERFACTUAL_SUFFIX = "_cf"
COUNTERFACTUAL_INDEX_OFFSET = 10_000
COUNTERFACTUAL_STRUCTURES = 200


def _roster_item(session: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """The roster turn and its assert; every chain has exactly one."""
    turn_id = int(session["session_meta"]["roster_turn"])
    for item in session["turns"][turn_id]["asserts"]:
        if item["kind"] == "roster":
            return turn_id, item
    raise ValueError(f"{session['session_id']}: roster turn has no roster assert")


def _roster_text(chain: str, mapping: Dict[str, str]) -> str:
    """Render the roster turn from a value -> name mapping.

    Rebuilding (instead of patching two names in the old string) keeps the
    insertion order and the separators identical to the generator's own
    rendering, so a twin's roster line differs only in the two swapped names.
    """
    if chain == "apron":
        body = "、".join(f"{COLOURS[key]}是 {actor}" for key, actor in mapping.items())
        return "今天值班表上寫著：" + body + "。"
    prefix = {
        "badge": "人事那邊的卡號對照：",
        "ledger": "登記簿上的編號對照：",
        "window": "訪客系統的卡號對照：",
    }[chain]
    return prefix + "、".join(f"{value} 是 {name}" for value, name in mapping.items()) + "。"


def _pre_correction(session: Dict[str, Any]) -> List[Tuple[int, Dict[str, Any]]]:
    """Every assert a reader has before the correction turn."""
    limit = int(session["session_meta"]["correction_turn"])
    return [
        (turn["turn_id"], item)
        for turn in session["turns"]
        if int(turn["turn_id"]) < limit
        for item in turn["asserts"]
    ]


def counterfactual_twin(
    session: Dict[str, Any],
    partner: str | None = None,
    *,
    forbidden_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """§61: the same structure with the roster's value -> name map swapped.

    Everything except the roster turn, the oracle culprit and the final expected
    deduction is copied verbatim. The culprit's live evidence value and a
    *non-live* actor's value exchange the people they name, so the surviving
    evidence now identifies the partner while the text the model reads (witness
    accounts, badge ids, times) is byte-identical. That is the point: session
    identity is no longer a sufficient statistic for the answer, because two
    items with the same non-roster text have different answers.

    A twin is only accepted if the solver agrees with it (full testimony ->
    partner), the pre-correction candidate set is unchanged (the trap stays the
    trap), every data gate passes, and its answer tuple is free. If no actor
    works, this raises instead of silently skipping: a skipped structure would
    quietly change the registered corpus.
    """
    actors = list(session["environment"]["actors"])
    culprit = session["ground_truth_oracle"]["culprit"]
    chain = session["ground_truth_oracle"]["chain"]
    roster_turn, roster_assert = _roster_item(session)
    mapping = dict(roster_assert["value"])
    value_of = {name: value for value, name in mapping.items()}
    if culprit not in value_of:
        raise ValueError(f"{session['session_id']}: the culprit has no roster value")

    pre_original = derive(_pre_correction(session), actors)
    if partner is not None:
        candidates = [partner]
    else:
        # A position-ordered scan would make the first actor the twin culprit
        # far too often, and the corpus's "most mentioned" shortcut baseline
        # tie-breaks on that same position - a surface cue the original corpus
        # is gated against. Shuffle deterministically from the session id so the
        # partner is uniform over the roster and independent of turn order.
        candidates = [a for a in actors if a != culprit]
        random.Random(f"{session['session_id']}:counterfactual").shuffle(candidates)
    tried: List[Tuple[str, str]] = []
    forbidden = set(forbidden_keys)

    for candidate in candidates:
        if candidate == culprit:
            continue
        if candidate not in value_of:
            tried.append((candidate, "not on the roster"))
            continue
        live_value = value_of[culprit]
        partner_value = value_of[candidate]
        new_mapping = dict(mapping)
        new_mapping[live_value] = candidate
        new_mapping[partner_value] = culprit

        twin = copy.deepcopy(session)
        twin["session_id"] = session["session_id"] + COUNTERFACTUAL_SUFFIX
        twin["session_meta"]["index"] = (
            int(session["session_meta"]["index"]) + COUNTERFACTUAL_INDEX_OFFSET
        )
        twin["session_meta"]["split"] = "train"
        twin["session_meta"]["counterfactual_of"] = session["session_id"]
        twin["ground_truth_oracle"]["culprit"] = candidate
        twin["turns"][-1]["expected_final_deduction"] = candidate
        for item in twin["turns"][roster_turn]["asserts"]:
            if item["kind"] == "roster":
                item["value"] = dict(new_mapping)
        twin["turns"][roster_turn]["user_input"] = _roster_text(chain, new_mapping)

        # the solver must agree, and the correction must still be the pivot
        if derive(_all_asserts(twin), actors) != [candidate]:
            tried.append((candidate, "derive does not yield the partner"))
            continue
        if derive(_pre_correction(twin), actors) != pre_original:
            tried.append((candidate, "the pre-correction answer changed"))
            continue
        problems = (
            _validate_necessity(twin)
            + _validate_retraction(twin)
            + _validate_name_balance(twin)
            + _validate_session(twin, "train")
        )
        if problems:
            tried.append((candidate, problems[0]))
            continue
        key = PantryEcosystemSynthesizer._answer_key(twin)
        if key in forbidden:
            tried.append((candidate, "answer tuple collides"))
            continue

        # the claim this experiment rests on: only the roster turn differs
        for left, right in zip(session["turns"], twin["turns"]):
            if int(left["turn_id"]) != roster_turn and left["user_input"] != right["user_input"]:
                raise AssertionError(
                    f"{twin['session_id']}: twin changed a non-roster turn " f"({left['turn_id']})"
                )
        return twin

    head = "; ".join(f"{name}: {why}" for name, why in tried[:4])
    raise RuntimeError(
        f"{session['session_id']}: no counterfactual partner works ({len(tried)} tried; {head})"
    )


def build_counterfactual(
    splits: Dict[str, List[Dict[str, Any]]],
    *,
    structures: int = COUNTERFACTUAL_STRUCTURES,
) -> Dict[str, List[Dict[str, Any]]]:
    """Interleave the first ``structures`` train items with their twins.

    The result is ``[o0, t0, o1, t1, ...] + train[structures:]``, so a
    ``--train-sessions 2*structures`` arm gets exactly the pairs while the
    original 800-session corpus stays in place behind them.
    """
    train = list(splits["train"])
    heldout = list(splits["heldout"])
    if structures <= 0 or structures > len(train):
        raise ValueError(f"structures={structures} is outside 1..{len(train)}")

    used = {PantryEcosystemSynthesizer._answer_key(session) for session in heldout}
    used |= {session["session_id"] for session in heldout}
    twins: List[Dict[str, Any]] = []
    for session in train[:structures]:
        twin = counterfactual_twin(session, forbidden_keys=sorted(used))
        used.add(PantryEcosystemSynthesizer._answer_key(twin))
        used.add(twin["session_id"])
        twins.append(twin)

    interleaved: List[Dict[str, Any]] = []
    for original, twin in zip(train[:structures], twins):
        interleaved.extend([original, twin])
    interleaved.extend(train[structures:])
    return {"train": interleaved, "heldout": heldout}


def validate_counterfactual(
    splits: Dict[str, List[Dict[str, Any]]],
    *,
    structures: int = COUNTERFACTUAL_STRUCTURES,
) -> List[str]:
    """Every §61 invariant, as violations a reader can act on."""
    problems: List[str] = []
    train = list(splits.get("train") or [])
    heldout = list(splits.get("heldout") or [])
    originals: Dict[str, Dict[str, Any]] = {}
    twins: List[Dict[str, Any]] = []
    for session in train:
        if session["session_meta"].get("counterfactual_of"):
            twins.append(session)
        else:
            originals[session["session_id"]] = session

    if len(twins) != structures:
        problems.append(f"expected {structures} twins, found {len(twins)}")
    ids = [session["session_id"] for session in train + heldout]
    if len(ids) != len(set(ids)):
        problems.append("session ids are not unique")
    keys = [PantryEcosystemSynthesizer._answer_key(session) for session in train + heldout]
    if len(keys) != len(set(keys)):
        problems.append("answer tuples are not unique across the counterfactual corpus")
    heldout_keys = {PantryEcosystemSynthesizer._answer_key(session) for session in heldout}

    seen: set = set()
    for twin in twins:
        sid = twin["session_id"]
        if not sid.endswith(COUNTERFACTUAL_SUFFIX):
            problems.append(f"{sid}: twin id does not end in {COUNTERFACTUAL_SUFFIX}")
        original = originals.get(twin["session_meta"].get("counterfactual_of"))
        if original is None:
            problems.append(f"{sid}: counterfactual_of does not name a train structure")
            continue
        if twin["ground_truth_oracle"]["culprit"] == original["ground_truth_oracle"]["culprit"]:
            problems.append(f"{sid}: the twin did not change the culprit")
        if PantryEcosystemSynthesizer._answer_key(twin) in heldout_keys:
            problems.append(f"{sid}: the twin's answer tuple is in the held-out split")
        if twin["session_meta"].get("counterfactual_of") in seen:
            problems.append(f"{sid}: structure has more than one twin")
        seen.add(twin["session_meta"].get("counterfactual_of"))

        for field in ("actors", "items"):
            if twin["environment"][field] != original["environment"][field]:
                problems.append(f"{sid}: environment.{field} differs from its structure")
        if twin["ground_truth_oracle"]["chain"] != original["ground_truth_oracle"]["chain"]:
            problems.append(f"{sid}: chain differs from its structure")
        if twin["session_meta"].get("timeline") != original["session_meta"].get("timeline"):
            problems.append(f"{sid}: timeline differs from its structure")
        if len(twin["turns"]) != len(original["turns"]):
            problems.append(f"{sid}: turn count differs from its structure")
            continue
        roster_turn = int(twin["session_meta"]["roster_turn"])
        for left, right in zip(original["turns"], twin["turns"]):
            if int(left["turn_id"]) != roster_turn and left["user_input"] != right["user_input"]:
                problems.append(f"{sid}: non-roster turn {left['turn_id']} differs")
        _, old_roster = _roster_item(original)
        _, new_roster = _roster_item(twin)
        old_map, new_map = dict(old_roster["value"]), dict(new_roster["value"])
        if set(old_map) != set(new_map):
            problems.append(f"{sid}: roster value set changed")
        if set(old_map.values()) != set(new_map.values()):
            problems.append(f"{sid}: roster name set changed")
        changed = [value for value in old_map if old_map[value] != new_map.get(value)]
        if len(changed) != 2:
            problems.append(f"{sid}: roster changed {len(changed)} entries, expected 2")
        old_culprit = original["ground_truth_oracle"]["culprit"]
        new_culprit = twin["ground_truth_oracle"]["culprit"]
        live_value = next(v for v, name in old_map.items() if name == old_culprit)
        partner_value = next(v for v, name in old_map.items() if name == new_culprit)
        if new_map.get(live_value) != new_culprit or new_map.get(partner_value) != old_culprit:
            problems.append(f"{sid}: the roster swap is not the registered one")
        if twin["turns"][-1].get("expected_final_deduction") != new_culprit:
            problems.append(f"{sid}: final deduction does not match the twin culprit")
        if derive(_all_asserts(twin), twin["environment"]["actors"]) != [new_culprit]:
            problems.append(f"{sid}: testimony does not derive the twin culprit")
        problems.extend(_validate_session(twin, "train"))

    # the first 2*structures items must be the interleaved pairs
    head = train[: 2 * structures]
    if len(head) == 2 * structures:
        for position in range(0, len(head), 2):
            original, twin = head[position], head[position + 1]
            if twin["session_meta"].get("counterfactual_of") != original["session_id"]:
                problems.append(f"train[{position + 1}] is not the twin of train[{position}]")
    else:
        problems.append(
            f"the train split has {len(train)} items, fewer than the {2 * structures} pair head"
        )
    return problems


# --------------------------------------------------------------------------- #
# §62: the minimal binding corpus - two people, one live value
# --------------------------------------------------------------------------- #
MINIMAL_ROSTER_SIZE = 2
# §65: the capacity curve runs the same corpus at 2/3/4/5 names. The default stays
# 2 so every §62-§64 digest is unchanged.
MINIMAL_ROSTER_SIZES = (2, 3, 4, 5)
MINIMAL_TRAIN_STRUCTURES = 200
MINIMAL_HELDOUT_STRUCTURES = 200
MINIMAL_INDEX_OFFSET = 10_000
MINIMAL_SUFFIX = "_cf"
# §64: an order twin is the same session with the roster's two entries listed in
# the opposite order; the value -> person mapping and the culprit do not change.
MINIMAL_ORDER_INDEX_OFFSET = 20_000
MINIMAL_ORDER_SUFFIX = "_ro"


def _minimal_session(
    index: int,
    rng: random.Random,
    seed: int,
    split: str,
    roster_order: str = "balanced",
    roster_size: int = MINIMAL_ROSTER_SIZE,
) -> Dict[str, Any]:
    """Four turns: the crime, a two-name roster, one live value, the question.

    No trap, no correction, no time filter. The only thing that can turn the
    evidence value into a person is the roster line - which is exactly the
    binding §61 showed the carrier only does for part of its pairs. The
    dead value never appears in the testimony; it exists so the roster is a real
    choice of two rather than a one-entry lookup.

    ``roster_order`` exists because §62's first version wrote the dead value
    first and the live value second every time, so the culprit was always the
    second roster entry; a trained arm answered that position and scored 1.0000
    without reading the mapping (§62.10). ``balanced`` alternates the live
    value's position with the session index, so the two positions hold the
    culprit equally often and the position cannot stand in for the answer.
    ``culprit_second`` reproduces the §62 corpus byte for byte so that report
    stays checkable.

    ``roster_size`` (§65) is the capacity curve's knob: k actors sampled in the
    same order and k values, one of which is the live value. The live entry is
    rotated through the k slots with ``index % k``, so each slot holds the
    culprit about ``n / k`` times and a fixed-slot rule caps at ``1 / k``. The
    default of 2 reproduces every earlier corpus byte for byte.
    """
    if roster_order not in {"balanced", "culprit_second"}:
        raise ValueError(f"unknown roster_order {roster_order!r}")
    if roster_size < 2 or roster_size > len(ACTORS) or roster_size > len(COLOURS):
        raise ValueError(f"roster_size {roster_size} is out of range")
    if roster_order == "culprit_second" and roster_size != 2:
        raise ValueError("culprit_second reproduces §62 and is only defined for two names")
    actors = rng.sample(ACTORS, roster_size)
    culprit = actors[0]
    others = actors[1:]
    target_key = rng.choice(sorted(ITEMS))
    target_zh, unit = ITEMS[target_key]
    decoy_key = rng.choice([key for key in sorted(ITEMS) if key != target_key])
    decoy_zh = ITEMS[decoy_key][0]
    values = rng.sample(sorted(COLOURS), roster_size)
    live_value = values[0]
    dead_values = values[1:]
    if roster_order == "culprit_second":
        mapping = {dead_values[0]: others[0], live_value: culprit}
    elif roster_size == 2 and index % 2:
        mapping = {dead_values[0]: others[0], live_value: culprit}
    else:
        slot = index % roster_size
        ordered: List[Tuple[str, str]] = []
        dead_iter = iter(zip(dead_values, others))
        for position in range(roster_size):
            ordered.append((live_value, culprit) if position == slot else next(dead_iter))
        mapping = dict(ordered)
    action = rng.randint(17 * 60 + 30, 19 * 60)
    opening = action - rng.randint(55, 70)
    now = action + rng.randint(30, 50)
    missing = rng.randint(2, 4)
    witness = rng.choice(WITNESSES)

    turns: List[Dict[str, Any]] = []

    def add(
        text: str,
        asserts: Sequence[Dict[str, Any]] = (),
        tags: Sequence[str] = (),
    ) -> int:
        turn_id = len(turns)
        turns.append(
            {
                "turn_id": turn_id,
                "dt_s": 0.0,
                "user_input": text,
                "asserts": [dict(item, turn=turn_id) for item in asserts],
                "expected_internal_focus": list(tags) or ["no_focus"],
            }
        )
        return turn_id

    add(
        f"下午 {_fmt(opening)} 點{target_zh}放茶水間，順便冰了{decoy_zh}。"
        f"現在 {_fmt(now)}，{target_zh}少了 {missing} {unit}。",
        tags=[f"{target_key}_missing_{missing}"],
    )
    roster_turn = add(
        _roster_text("apron", mapping),
        [{"kind": "roster", "value": mapping}],
        ["roster_lookup"],
    )
    evidence_turn = add(
        f"{witness} 說 {_fmt(action)} 看到一個人從茶水間出來，"
        f"穿著{COLOURS[live_value]}的圍裙，手裡拿著紙巾擦嘴。",
        [{"kind": "seen", "value": live_value, "t": _fmt(action)}],
        ["apron_evidence"],
    )
    question_turn = add(
        "好，根據目前的口供和時間線交叉比對，"
        f"你認為誰是吃掉{target_zh}的人？請給出你的最終推論。",
        tags=["final_deduction"],
    )
    turns[question_turn]["expected_final_deduction"] = culprit
    for position, turn in enumerate(turns):
        turn["dt_s"] = 0.0 if position == 0 else _sample_dt(rng)

    return {
        "session_id": f"minimal_pantry_{index:03d}",
        "schema_version": SCHEMA_VERSION,
        "session_meta": {
            "seed": seed,
            "index": index,
            "split": split,
            "chain": "apron",
            "chain_turns": sorted({roster_turn, evidence_turn}),
            "evidence_turn": evidence_turn,
            "roster_turn": roster_turn,
            # the live value is stated once; dropping that turn removes the only
            # evidence, which is what the no_correction variant means here
            "correction_turn": evidence_turn,
            "slots": len(actors) + 3,
            "minimal_binding": True,
            "timeline": {
                "opening": _fmt(opening),
                "action": _fmt(action),
                "now": _fmt(now),
            },
        },
        "environment": {
            "actors": list(actors),
            "items": [target_key, decoy_key],
            "badges": {},
        },
        "ground_truth_oracle": {
            "chain": "apron",
            "target_item": target_key,
            "culprit": culprit,
            "action_time": _fmt(action),
            "window": f"{_fmt(opening)}-{_fmt(now)}",
            "window_bounds": f"{_fmt(opening)}-{_fmt(now)}",
            "evidence_tag": f"chain=apron|value={live_value}|t={_fmt(action)}",
        },
        "turns": turns,
    }


def minimal_twin(session: Dict[str, Any]) -> Dict[str, Any]:
    """Swap the culprit's name on the roster; everything else is byte-identical.

    The value the witness saw stays the same, so after the swap it names another
    person. That is the smallest possible counterfactual: one roster line with
    two names exchanged, and a different answer.
    """
    twin = copy.deepcopy(session)
    roster_turn, roster_assert = _roster_item(twin)
    mapping = dict(roster_assert["value"])
    if len(mapping) < 2:
        raise ValueError(f"{session['session_id']}: expected a roster of at least two entries")
    names = list(mapping.values())
    culprit = session["ground_truth_oracle"]["culprit"]
    # Swap the culprit's name with the first entry that is not the culprit, so the
    # answer always changes. With two names this is exactly names[0] <-> names[1];
    # §65's wider rosters need the general form or the twin would sometimes keep
    # the same answer.
    other = next(name for name in names if name != culprit)
    swapped = {
        value: (other if name == culprit else culprit if name == other else name)
        for value, name in mapping.items()
    }
    acting_value = next(value for value, name in mapping.items() if name == culprit)
    twin["session_id"] = session["session_id"] + MINIMAL_SUFFIX
    twin["session_meta"]["index"] = int(session["session_meta"]["index"]) + MINIMAL_INDEX_OFFSET
    twin["session_meta"]["split"] = "train"
    twin["session_meta"]["counterfactual_of"] = session["session_id"]
    twin["ground_truth_oracle"]["culprit"] = swapped[acting_value]
    twin["turns"][-1]["expected_final_deduction"] = twin["ground_truth_oracle"]["culprit"]
    for item in twin["turns"][roster_turn]["asserts"]:
        if item["kind"] == "roster":
            item["value"] = dict(swapped)
    twin["turns"][roster_turn]["user_input"] = _roster_text("apron", swapped)
    return twin


def minimal_order_twin(session: Dict[str, Any]) -> Dict[str, Any]:
    """§64: the same session with the roster's entries in the opposite order.

    The mapping is unchanged, so ``derive()`` still names the same culprit; only
    the entries' positions in the roster line change. This is the training
    counterpart of §63's M5 control: a model that reads the mapping answers both
    copies the same way, a model that reads a position answers them differently.
    """
    twin = copy.deepcopy(session)
    roster_turn, roster_assert = _roster_item(twin)
    mapping = dict(roster_assert["value"])
    if len(mapping) < 2:
        raise ValueError(f"{session['session_id']}: expected a roster of at least two entries")
    flipped = dict(reversed(list(mapping.items())))
    twin["session_id"] = session["session_id"] + MINIMAL_ORDER_SUFFIX
    twin["session_meta"]["index"] = (
        int(session["session_meta"]["index"]) + MINIMAL_ORDER_INDEX_OFFSET
    )
    twin["session_meta"]["split"] = "train"
    twin["session_meta"]["order_augmented_of"] = session["session_id"]
    for item in twin["turns"][roster_turn]["asserts"]:
        if item["kind"] == "roster":
            item["value"] = dict(flipped)
    twin["turns"][roster_turn]["user_input"] = _roster_text("apron", flipped)
    return twin


def build_minimal_binding(
    *,
    structures: int = MINIMAL_TRAIN_STRUCTURES,
    heldout: int = MINIMAL_HELDOUT_STRUCTURES,
    seed: int = DEFAULT_SEED,
    roster_order: str = "balanced",
    order_augmented: bool = False,
    roster_size: int = MINIMAL_ROSTER_SIZE,
) -> Dict[str, List[Dict[str, Any]]]:
    """``[o0, t0, o1, t1, ...]`` for train, plain structures for held-out.

    ``order_augmented`` (§64) replaces each structure's name-swapped twin with
    its *order* twin: the same 200 structures, each seen once in each roster
    order, still 400 training items. The held-out split is unchanged.
    """
    if roster_size not in MINIMAL_ROSTER_SIZES:
        raise ValueError(f"roster_size {roster_size} is not one of {MINIMAL_ROSTER_SIZES}")
    used: set = set()

    def make(index: int, split: str) -> Dict[str, Any]:
        for salt in range(128):
            rng = random.Random(f"{seed}:minimal:{index}:{salt}")
            session = _minimal_session(index, rng, seed, split, roster_order, roster_size)
            key = PantryEcosystemSynthesizer._answer_key(session)
            if key in used:
                continue
            used.add(key)
            return session
        raise RuntimeError(f"could not make minimal session {index} unique after 128 attempts")

    train_structures = [make(index, "train") for index in range(structures)]
    heldout_structures = [make(structures + index, "heldout") for index in range(heldout)]

    train_twins: List[Dict[str, Any]] = []
    for session in train_structures:
        if order_augmented:
            # the order twin's answer tuple is the original's by construction
            twin = minimal_order_twin(session)
        else:
            twin = minimal_twin(session)
            key = PantryEcosystemSynthesizer._answer_key(twin)
            if key in used:
                raise RuntimeError(f"{session['session_id']}: its twin's answer tuple collides")
            used.add(key)
        train_twins.append(twin)

    interleaved: List[Dict[str, Any]] = []
    for original, twin in zip(train_structures, train_twins):
        interleaved.extend([original, twin])

    heldout_twins = [minimal_twin(session) for session in heldout_structures]
    return {
        "train": interleaved,
        "heldout": heldout_structures,
        "heldout_twins": heldout_twins,
    }


def validate_minimal_binding(
    splits: Dict[str, List[Dict[str, Any]]],
    *,
    structures: int = MINIMAL_TRAIN_STRUCTURES,
    heldout: int = MINIMAL_HELDOUT_STRUCTURES,
    roster_order: str = "balanced",
    order_augmented: bool = False,
    roster_size: int = MINIMAL_ROSTER_SIZE,
) -> List[str]:
    """Every §62/§64 invariant, as violations a reader can act on."""
    problems: List[str] = []
    train = list(splits.get("train") or [])
    heldout_sessions = list(splits.get("heldout") or [])
    heldout_twins = list(splits.get("heldout_twins") or [])

    if len(train) != 2 * structures:
        problems.append(f"expected {2 * structures} train items, found {len(train)}")
    if len(heldout_sessions) != heldout:
        problems.append(f"expected {heldout} held-out structures, found {len(heldout_sessions)}")
    if len(heldout_twins) != heldout:
        problems.append(f"expected {heldout} held-out twins, found {len(heldout_twins)}")

    structures_of: Dict[str, Dict[str, Any]] = {}
    twins: List[Dict[str, Any]] = []
    order_twins: List[Dict[str, Any]] = []
    link_key = "order_augmented_of" if order_augmented else "counterfactual_of"
    for position, session in enumerate(train):
        if session["session_meta"].get("counterfactual_of"):
            twins.append(session)
        elif session["session_meta"].get("order_augmented_of"):
            order_twins.append(session)
        else:
            structures_of[session["session_id"]] = session
    if order_augmented:
        if twins:
            problems.append(f"order-augmented train carries {len(twins)} counterfactual twins")
        if len(order_twins) != structures:
            problems.append(f"expected {structures} order twins, found {len(order_twins)}")
    elif len(twins) != structures:
        problems.append(f"expected {structures} twins, found {len(twins)}")
    for position in range(0, len(train) - 1, 2):
        original, twin = train[position], train[position + 1]
        if twin["session_meta"].get(link_key) != original["session_id"]:
            problems.append(f"train[{position + 1}] is not the twin of train[{position}]")

    # an order twin's answer tuple is its structure's by construction, so only
    # the structures and the held-out split must be pairwise unique
    unique_rows = [session for session in train if not session["session_meta"].get(link_key)]
    keys = [
        PantryEcosystemSynthesizer._answer_key(session)
        for session in unique_rows + heldout_sessions
    ]
    if len(keys) != len(set(keys)):
        problems.append("answer tuples are not unique across the minimal corpus")

    def check_structure(session: Dict[str, Any], label: str) -> None:
        sid = session["session_id"]
        actors = list(session["environment"]["actors"])
        oracle = session["ground_truth_oracle"]
        if len(actors) != roster_size:
            problems.append(f"{label}/{sid}: {len(actors)} actors, expected {roster_size}")
            return
        roster_turn, roster_assert = _roster_item(session)
        mapping = dict(roster_assert["value"])
        if len(mapping) != roster_size:
            problems.append(f"{label}/{sid}: roster has {len(mapping)} entries")
            return
        rendered = session["turns"][roster_turn]["user_input"]
        if rendered != _roster_text(session["session_meta"]["chain"], mapping):
            problems.append(
                f"{label}/{sid}: the roster line does not match the roster mapping, so the "
                "text and the asserts disagree"
            )
        if set(mapping.values()) != set(actors):
            problems.append(f"{label}/{sid}: the roster does not name both actors")
        evidence = [
            item
            for turn in session["turns"]
            for item in turn.get("asserts", [])
            if item["kind"] in {"seen", "entry", "checkout", "access"}
        ]
        if len(evidence) != 1:
            problems.append(f"{label}/{sid}: {len(evidence)} evidence values, expected 1")
        else:
            if evidence[0]["kind"] != "seen":
                problems.append(f"{label}/{sid}: the live value is not a seen assert")
            live = evidence[0].get("value")
            if live not in mapping:
                problems.append(f"{label}/{sid}: the live value is not on the roster")
            dead = [value for value in mapping if value != live]
            if any(value in str(item.get("id")) for value in dead for item in evidence):
                problems.append(f"{label}/{sid}: a dead value appears as evidence")
        if derive(_all_asserts(session), actors) != [oracle["culprit"]]:
            problems.append(f"{label}/{sid}: the testimony does not derive the culprit")
        before = [
            (turn["turn_id"], item)
            for turn in session["turns"]
            if int(turn["turn_id"]) < roster_turn
            for item in turn.get("asserts", [])
        ]
        roster_only = [
            (turn["turn_id"], item)
            for turn in session["turns"]
            if int(turn["turn_id"]) <= roster_turn
            for item in turn.get("asserts", [])
        ]
        if derive(roster_only, actors) != sorted(actors):
            problems.append(f"{label}/{sid}: the roster alone already answers the question")
        if before and derive(before, actors) != sorted(actors):
            problems.append(f"{label}/{sid}: the crime alone already narrows the roster")
        if session["turns"][-1].get("expected_final_deduction") != oracle["culprit"]:
            problems.append(f"{label}/{sid}: the final deduction is not the culprit")
        text = "\n".join(turn["user_input"] for turn in session["turns"])
        for name in actors:
            if text.count(name) != 1:
                problems.append(f"{label}/{sid}: {name} is named {text.count(name)} times")
            if name in session["turns"][-1]["user_input"]:
                problems.append(f"{label}/{sid}: {name} appears in the question")
        if oracle["evidence_tag"] in text:
            problems.append(f"{label}/{sid}: the oracle tag appears in the text")

    for session in train:
        if not session["session_meta"].get("counterfactual_of") and not session["session_meta"].get(
            "order_augmented_of"
        ):
            check_structure(session, "train")
    for session in heldout_sessions:
        check_structure(session, "heldout")
    for session, twin in zip(heldout_sessions, heldout_twins):
        if twin["session_meta"].get("counterfactual_of") != session["session_id"]:
            problems.append(f"{twin['session_id']}: held-out twin is not linked")

    if roster_order == "balanced":
        # §62.10: the first corpus wrote the live value second every time, so the
        # culprit was always the second roster entry. An arm trained on it read
        # the position and scored 1.0000 without ever matching the evidence value
        # through the roster. The answer must not be recoverable from where the
        # entry sits.
        def culprit_position(session: Dict[str, Any]) -> Optional[int]:
            _, roster_assert = _roster_item(session)
            mapping = dict(roster_assert["value"])
            culprit = session["ground_truth_oracle"]["culprit"]
            names = list(mapping.values())
            return names.index(culprit) if culprit in names else None

        train_structures = [
            session
            for session in train
            if not session["session_meta"].get("counterfactual_of")
            and not session["session_meta"].get("order_augmented_of")
        ]
        train_twins = [twin for twin in train if twin["session_meta"].get(link_key)]
        # A "second entry" reader is right on a structure exactly when the culprit
        # sits second, and the twin keeps the live value's key (only the name
        # changes), so the twin's culprit sits in the same slot. Both splits must
        # therefore be balanced, or such a reader gets a free half of the corpus.
        for label, rows in (
            ("train structures", train_structures),
            ("train twins", train_twins),
            ("heldout", heldout_sessions),
            ("heldout twins", heldout_twins),
        ):
            positions = [culprit_position(session) for session in rows]
            counts = [positions.count(slot) for slot in range(roster_size)]
            if sum(counts) != len(positions) or max(counts) - min(counts) > 1:
                problems.append(
                    f"{label}: the culprit's roster slot counts are {counts} over "
                    f"{len(positions)} items; a positional shortcut would be free"
                )

    if order_augmented:
        heldout_ids = {session["session_id"] for session in heldout_sessions}
        for twin in order_twins:
            sid = twin["session_id"]
            if not sid.endswith(MINIMAL_ORDER_SUFFIX):
                problems.append(f"{sid}: order twin id does not end in {MINIMAL_ORDER_SUFFIX}")
            original = structures_of.get(twin["session_meta"].get("order_augmented_of"))
            if original is None:
                problems.append(f"{sid}: order_augmented_of does not name a structure")
                continue
            if twin["ground_truth_oracle"]["culprit"] != original["ground_truth_oracle"]["culprit"]:
                problems.append(f"{sid}: the order twin changed the culprit")
            if derive(_all_asserts(twin), twin["environment"]["actors"]) != [
                twin["ground_truth_oracle"]["culprit"]
            ]:
                problems.append(f"{sid}: the order twin's testimony no longer derives the culprit")
            old_map = dict(_roster_item(original)[1]["value"])
            new_map = dict(_roster_item(twin)[1]["value"])
            if old_map != new_map:
                problems.append(f"{sid}: the order twin changed the roster mapping")
            if list(old_map) == list(new_map):
                problems.append(f"{sid}: the order twin did not reverse the roster entries")
            twin_turn = int(twin["session_meta"]["roster_turn"])
            if twin["turns"][twin_turn]["user_input"] != _roster_text(
                twin["session_meta"]["chain"], new_map
            ):
                problems.append(f"{sid}: the order twin's roster line does not match its mapping")
            roster_turn = int(original["session_meta"]["roster_turn"])
            for left, right in zip(original["turns"], twin["turns"]):
                if (
                    int(left["turn_id"]) != roster_turn
                    and left["user_input"] != right["user_input"]
                ):
                    problems.append(f"{sid}: non-roster turn {left['turn_id']} differs")
        return problems

    heldout_ids = {session["session_id"] for session in heldout_sessions}
    for twin in twins + heldout_twins:
        sid = twin["session_id"]
        if not sid.endswith(MINIMAL_SUFFIX):
            problems.append(f"{sid}: twin id does not end in {MINIMAL_SUFFIX}")
        original = structures_of.get(twin["session_meta"].get("counterfactual_of"))
        if original is None and twin["session_meta"].get("counterfactual_of") in heldout_ids:
            original = next(
                session
                for session in heldout_sessions
                if session["session_id"] == twin["session_meta"]["counterfactual_of"]
            )
        if original is None:
            problems.append(f"{sid}: counterfactual_of does not name a structure")
            continue
        if twin["ground_truth_oracle"]["culprit"] == original["ground_truth_oracle"]["culprit"]:
            problems.append(f"{sid}: the twin did not change the culprit")
        roster_turn = int(original["session_meta"]["roster_turn"])
        if len(twin["turns"]) != len(original["turns"]):
            problems.append(f"{sid}: turn count differs from its structure")
            continue
        for left, right in zip(original["turns"], twin["turns"]):
            if int(left["turn_id"]) != roster_turn and left["user_input"] != right["user_input"]:
                problems.append(f"{sid}: non-roster turn {left['turn_id']} differs")
        if derive(_all_asserts(twin), twin["environment"]["actors"]) != [
            twin["ground_truth_oracle"]["culprit"]
        ]:
            problems.append(f"{sid}: the testimony does not derive the twin culprit")
    return problems


def _validate_timeline(
    meta: Dict[str, Any], oracle: Dict[str, Any], split: str, sid: str
) -> List[str]:
    """The stated times must describe one consistent afternoon."""
    timeline = meta.get("timeline") or {}
    names = ("impossible_claim", "opening", "window_lo", "window_hi", "action", "now")
    missing = [name for name in names if name not in timeline]
    if missing:
        return [f"{split}/{sid}: timeline is missing {missing}"]
    try:
        values = [_parse(timeline[name]) for name in names]
    except (AttributeError, ValueError):
        return [f"{split}/{sid}: timeline is not HH:MM"]

    impossible, opening, window_lo, window_hi, action, now = values
    out: List[str] = []
    if timeline["action"] != oracle["action_time"]:
        out.append(f"{split}/{sid}: timeline action != oracle action_time")
    if not impossible < opening:
        out.append(f"{split}/{sid}: the 'impossible' claim is not before delivery")
    if not opening <= window_lo:
        out.append(f"{split}/{sid}: the window opens before the food arrives")
    if not window_lo <= action <= window_hi:
        out.append(f"{split}/{sid}: the theft is outside its own window")
    if not window_hi <= now:
        out.append(f"{split}/{sid}: the window ends after the conversation starts")
    if oracle["window"] != f"{_fmt(window_lo)}-{_fmt(window_hi)}":
        out.append(f"{split}/{sid}: oracle window != timeline window")
    bounds = oracle.get("window_bounds") or ""
    if not bounds:
        out.append(f"{split}/{sid}: oracle has no window_bounds")
    else:
        bound_lo, bound_hi = (_parse(part) for part in bounds.split("-"))
        if not opening < bound_lo < window_lo:
            out.append(f"{split}/{sid}: the lower bound is not between delivery and the window")
        if not window_hi < bound_hi < now:
            out.append(f"{split}/{sid}: the upper bound is not between the window and now")
    return out


def _validate_session(session: Dict[str, Any], split: str) -> List[str]:
    out: List[str] = []
    sid = session.get("session_id", "<missing>")
    required = {
        "session_id",
        "schema_version",
        "session_meta",
        "environment",
        "ground_truth_oracle",
        "turns",
    }
    missing = required.difference(session)
    if missing:
        return [f"{split}/{sid}: missing keys {sorted(missing)}"]

    meta = session["session_meta"]
    environment = session["environment"]
    oracle = session["ground_truth_oracle"]
    turns = session["turns"]

    if meta.get("split") != split:
        out.append(f"{split}/{sid}: meta.split={meta.get('split')!r}")
    if not 5 <= len(environment["actors"]) <= 8:
        out.append(f"{split}/{sid}: actor count {len(environment['actors'])}")
    if not 3 <= len(environment["items"]) <= 4:
        out.append(f"{split}/{sid}: item count {len(environment['items'])}")
    if oracle["culprit"] not in environment["actors"]:
        out.append(f"{split}/{sid}: culprit is not an actor")
    if oracle["target_item"] not in environment["items"]:
        out.append(f"{split}/{sid}: target is not an item")
    if environment["items"][0] != oracle["target_item"]:
        out.append(f"{split}/{sid}: target is not the first item")
    if oracle["chain"] not in CHAINS:
        out.append(f"{split}/{sid}: unknown chain {oracle['chain']!r}")
    if meta.get("chain") != oracle["chain"]:
        out.append(f"{split}/{sid}: meta.chain != oracle.chain")

    slots = meta.get("slots")
    if not isinstance(slots, int) or slots > MAX_SLOTS:
        out.append(f"{split}/{sid}: slots {slots} > {MAX_SLOTS}")

    out.extend(_validate_timeline(meta, oracle, split, sid))

    if len(turns) < 6:
        out.append(f"{split}/{sid}: {len(turns)} turns is too few")
        return out
    for position, turn in enumerate(turns):
        if turn.get("turn_id") != position:
            out.append(f"{split}/{sid}: turn_id {turn.get('turn_id')} at {position}")
        dt = turn.get("dt_s")
        if not isinstance(dt, (int, float)) or dt < 0:
            out.append(f"{split}/{sid}: turn {position} dt_s {dt!r}")
        if position == 0 and dt != 0.0:
            out.append(f"{split}/{sid}: first turn dt_s is not 0.0")
        text = turn.get("user_input") or ""
        if not text:
            out.append(f"{split}/{sid}: turn {position} has no text")
        tag = oracle["evidence_tag"]
        if tag in text or "surveillance" in text.lower():
            out.append(f"{split}/{sid}: turn {position} leaks the oracle tag")
        lowered = text.lower()
        for marker in VERDICT_MARKERS:
            if marker.lower() in lowered:
                out.append(f"{split}/{sid}: turn {position} contains verdict marker {marker!r}")
        for item in turn.get("asserts", []):
            if item.get("turn") != position:
                out.append(
                    f"{split}/{sid}: turn {position} carries an assert owned by {item.get('turn')}"
                )
            if item["kind"] == "retract" and not 0 <= item["target"] < position:
                out.append(
                    f"{split}/{sid}: turn {position} retracts {item['target']}, which is not earlier"
                )

    final = turns[-1]
    if final.get("expected_final_deduction") != oracle["culprit"]:
        out.append(f"{split}/{sid}: final deduction does not match the oracle")
    for turn in turns[:-1]:
        if "expected_final_deduction" in turn:
            out.append(f"{split}/{sid}: turn {turn.get('turn_id')} has a final deduction")
        if not turn.get("expected_internal_focus"):
            out.append(f"{split}/{sid}: turn {turn.get('turn_id')} has no focus tags")

    out.extend(_validate_name_balance(session))
    out.extend(_validate_necessity(session))
    out.extend(_validate_retraction(session))
    return out


def _validate_split(
    train: Sequence[Dict[str, Any]], heldout: Sequence[Dict[str, Any]]
) -> List[str]:
    out: List[str] = []
    train_ids = {session["session_id"] for session in train}
    heldout_ids = {session["session_id"] for session in heldout}
    shared = train_ids.intersection(heldout_ids)
    if shared:
        out.append(f"session ids appear in both splits: {sorted(shared)[:3]}")

    def answers(sessions: Sequence[Dict[str, Any]]) -> set:
        return {PantryEcosystemSynthesizer._answer_key(session) for session in sessions}

    shared_answers = answers(train).intersection(answers(heldout))
    if shared_answers:
        out.append(f"answer tuples appear in both splits: {sorted(shared_answers)[:2]}")
    return out


def summarise(
    splits: Dict[str, List[Dict[str, Any]]], payload: str, seed: int, fraction: float
) -> Dict[str, Any]:
    bands = {"short": 0, "mid": 0, "long": 0}
    chains: Dict[str, int] = {name: 0 for name in CHAINS}
    turns = 0
    for sessions in splits.values():
        for session in sessions:
            chains[session["session_meta"]["chain"]] += 1
            for turn in session["turns"]:
                turns += 1
                bands[_band_for(float(turn["dt_s"]))] += 1
    everything = list(splits["train"]) + list(splits["heldout"])
    return {
        "schema_version": SCHEMA_VERSION,
        "generator": "scripts/gen_pantry_ecosystem.py",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seed": seed,
        "heldout_fraction": fraction,
        "counts": {name: len(sessions) for name, sessions in splits.items()},
        "turns": turns,
        "dt_bands": bands,
        "chains": chains,
        "shortcuts": shortcut_audit(everything) if everything else {},
        "max_slots": MAX_SLOTS,
        "file_sha256": _digest(payload),
        "split_sha256": {
            name: _digest("\n".join(s["session_id"] for s in sessions))
            for name, sessions in splits.items()
        },
    }


def _payload(splits: Dict[str, List[Dict[str, Any]]]) -> str:
    lines = [json.dumps(session, ensure_ascii=False) for session in splits["train"]]
    lines += [json.dumps(session, ensure_ascii=False) for session in splits["heldout"]]
    return "\n".join(lines) + "\n"


def write_corpus(path: Path, seed: int, sessions: int, fraction: float) -> Dict[str, Any]:
    synth = PantryEcosystemSynthesizer(seed=seed, sessions=sessions, heldout_fraction=fraction)
    splits = synth.generate()
    problems = synth.validate(splits)
    if problems:
        raise SystemExit("generated corpus violates its own gates:\n  " + "\n  ".join(problems))
    payload = _payload(splits)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    manifest = summarise(splits, payload, seed, fraction)
    path.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def check_corpus(path: Path) -> List[str]:
    """Re-derive and re-validate; any drift is a failure, not a warning."""
    problems: List[str] = []
    manifest_path = path.with_suffix(".manifest.json")
    if not path.exists():
        return [f"{path} does not exist"]
    if not manifest_path.exists():
        return [f"{manifest_path} does not exist"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload = path.read_text(encoding="utf-8")

    if _digest(payload) != manifest.get("file_sha256"):
        problems.append("the file no longer matches its manifest digest (was it edited?)")
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != manifest.get("generator_sha256"):
        problems.append("the generator changed since the corpus was written; regenerate it")

    sessions = [json.loads(line) for line in payload.splitlines() if line.strip()]
    splits = {
        "train": [s for s in sessions if s.get("session_meta", {}).get("split") == "train"],
        "heldout": [s for s in sessions if s.get("session_meta", {}).get("split") == "heldout"],
    }
    problems.extend(PantryEcosystemSynthesizer.validate(splits))

    rebuilt = PantryEcosystemSynthesizer(
        seed=manifest["seed"],
        sessions=sum(len(v) for v in splits.values()),
        heldout_fraction=manifest["heldout_fraction"],
    ).generate()
    if _payload(rebuilt) != payload:
        problems.append("regenerating from the recorded seed does not reproduce the file")
    return problems


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pantry-ecosystem session corpus")
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--sessions", type=int, default=DEFAULT_SESSIONS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--heldout-fraction", type=float, default=DEFAULT_HELDOUT_FRACTION)
    parser.add_argument(
        "--check", action="store_true", help="verify an existing corpus instead of writing one"
    )
    args = parser.parse_args(argv)

    out = Path(args.out)
    if not out.is_absolute():
        out = REPO_ROOT / out

    if args.check:
        problems = check_corpus(out)
        if problems:
            print(f"FAIL {out}")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        manifest = json.loads(out.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        print(
            f"OK {out}  train={manifest['counts']['train']} "
            f"heldout={manifest['counts']['heldout']} turns={manifest['turns']} "
            f"chains={manifest['chains']} bands={manifest['dt_bands']}"
        )
        return 0

    manifest = write_corpus(out, args.seed, args.sessions, args.heldout_fraction)
    print(
        f"wrote {out}\n"
        f"  sessions  : {manifest['counts']['train']} train / "
        f"{manifest['counts']['heldout']} held-out\n"
        f"  turns     : {manifest['turns']}\n"
        f"  chains    : {manifest['chains']}\n"
        f"  dt bands  : {manifest['dt_bands']}\n"
        f"  digest    : {manifest['file_sha256'][:16]}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
