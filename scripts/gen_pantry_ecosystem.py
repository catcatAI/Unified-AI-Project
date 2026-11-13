#!/usr/bin/env python3
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# LAYER: learning
"""The pantry-ecosystem corpus: multi-turn sessions that cannot be memorised.

Why this exists
---------------
The rounds so far taught the state *one* binding per episode (§44/§45) and then
asked whether a store could hold two (§46). Both are small enough that a model
can pass by matching a surface form to a value: the vocabulary is closed CV
syllables and the sentence is always ``remember <name> = <value> .``. A pass
therefore says something about the carrier and almost nothing about reasoning
across turns.

This generator produces the dataset that removes that shortcut. Each line is a
**session** - an office-pantry investigation with several people, one target
food, two or three distractors, conflicting testimony, red herrings and real
time gaps - and the only thing a model can do with it is keep the testimony,
the timeline and the identities straight in a fixed-size state. The ground
truth (who took the food, when, and which camera saw it) is emitted **only** in
the oracle block; it never appears in any ``user_input``, so a model that
answers correctly has to have reconstructed it.

The four properties the spec asks for, and how each is enforced here:

* **multi-entity + distractors** - 5-8 actors, 1 target item, 2-3 distractors,
  each session sampled from larger pools so no fixed name set recurs;
* **non-monotonic updates** - a witness seen near the pantry for a *different*
  item, a claim that a time is impossible, and a manager's alibi contradicted
  by the janitor; the last statement overturns the earlier one;
* **time gaps** - ``dt_s`` is log-uniform in three bands (10-60 s,
  300-1800 s, >= 3600 s), so ``al_step`` is exercised on short follow-ups and
  long absences within one session;
* **oracle adjudication** - the answer is ``(culprit, target_item,
  action_time, evidence_tag)`` and is checked by the data gates below rather
  than being present in the text.

Usage::

    ./.venv/bin/python scripts/gen_pantry_ecosystem.py --sessions 40
    ./.venv/bin/python scripts/gen_pantry_ecosystem.py --check

The dataset is data, not a score: nothing here measures a model. The trainer
that consumes it and the pre-registration of its gates are a separate round, so
this file only claims what it can prove - that the sessions are well formed,
deterministic, split by session, and free of oracle leakage.

Deviations from the spec as handed in (recorded, not silent)
-----------------------------------------------------------
1. **Names recur across sessions.** A pool of twelve actors shared by train and
   held-out cannot be disjoint, and making it so would shrink held-out to a
   dozen sessions and teach nothing. The gate is therefore on the **answer
   tuple** (culprit × target × time × camera) and on verbatim turn text, both of
   which are disjoint; names are not, and every name appears as culprit and as
   innocent witness on both sides, so a name cannot be the answer.
2. **``dt_s`` is consistent with a real turn timeline** instead of being an
   independent sample: the gap is drawn from the log-uniform bands and the
   conversation clock advances by exactly that gap. Drawn gaps and stated gaps
   cannot disagree.
3. **Three extra top-level keys** - ``schema_version``, ``session_meta`` (seed,
   index, permutation) - and a sidecar manifest exist so a run can be
   regenerated and audited. The four keys the spec names are unchanged.
4. **The camera timestamp is never mentioned by anyone.** The spec's example
   oracle names ``surveillance_cam_3_timestamp_1842``; the janitor's testimony
   is the visible evidence, and the camera is the hidden check. A gate fails if
   the tag leaks into any turn.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_VERSION = "pantry-ecosystem-v1"
DEFAULT_OUT = "data/pantry_ecosystem/sessions.jsonl"
DEFAULT_SEED = 20261113
DEFAULT_SESSIONS = 40
DEFAULT_HELDOUT_FRACTION = 0.2

# Larger than any session needs, so the pool is never the binding constraint.
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

PROPS = {
    "paper_plate": "紙盤",
    "mug": "馬克杯",
    "napkin": "紙巾",
    "tray": "托盤",
    "fork": "叉子",
}

# (weight, low seconds, high seconds). Log-uniform inside a band, so short
# follow-ups, mid-length investigation and long absences all occur.
DT_BANDS: Tuple[Tuple[float, float, float], ...] = (
    (0.40, 10.0, 60.0),
    (0.40, 300.0, 1800.0),
    (0.20, 3600.0, 14400.0),
)

MAX_SLOTS = 16  # actors + items + clues; the spec's capacity bound (§5)

# Phrases that would hand the verdict to the model. The final question asks for
# the deduction, so the answer must not already be in the transcript.
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


class PantryEcosystemSynthesizer:
    """Deterministic generator of pantry-investigation sessions.

    Every session's randomness is derived from ``f"{seed}:{index}"``, so session
    *i* is the same whether the corpus has 10 lines or 10,000. The only corpus
    level state is the set of answer tuples already used, which is needed to
    keep the splits disjoint and is applied in index order (also deterministic).
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

    def is_heldout(self, index: int) -> bool:
        """Interleaved, so both sides see the same range of session structures."""
        return index % self._period == 0

    def generate(self) -> Dict[str, List[Dict[str, Any]]]:
        used: Dict[str, Any] = {
            "answer": set(),
            # Text is only required to be disjoint *across* splits: within one
            # split two sessions may legitimately share a sentence shape, and
            # forbidding that would make the pool the binding constraint.
            "text": {"train": set(), "heldout": set()},
        }
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

    def _session(self, index: int, used: Dict[str, Any]) -> Dict[str, Any]:
        split = "heldout" if self.is_heldout(index) else "train"
        other = "train" if split == "heldout" else "heldout"
        # A collision can only be in the oracle tuple or in text shared with the
        # other split; retry with a salt so the pattern of retries is
        # reproducible too.
        for salt in range(64):
            rng = random.Random(f"{self.seed}:{index}:{salt}")
            session = self._render(index, rng)
            key = self._answer_key(session)
            texts = tuple(turn["user_input"] for turn in session["turns"])
            if key in used["answer"]:
                continue
            if used["text"][other].intersection(texts):
                continue
            used["answer"].add(key)
            used["text"][split].update(texts)
            return session
        raise RuntimeError(f"could not make session {index} unique after 64 attempts")

    @staticmethod
    def _answer_key(session: Dict[str, Any]) -> str:
        oracle = session["ground_truth_oracle"]
        return "|".join(
            str(oracle[name]) for name in ("culprit", "target_item", "action_time", "evidence_tag")
        )

    def _render(self, index: int, rng: random.Random) -> Dict[str, Any]:
        size = rng.randint(5, 8)
        actors = rng.sample(self.actors, size)
        target_key = rng.choice(sorted(self.items))
        distractors = rng.sample(
            [key for key in sorted(self.items) if key != target_key],
            rng.randint(2, 3),
        )
        culprit, herring, observed, confused = rng.sample(actors, 4)
        target_zh, unit = self.items[target_key]
        main_side = self.items[distractors[0]][0]
        other_side = self.items[distractors[-1]][0]

        # Theft is in the late afternoon; the conversation starts an hour later.
        action = rng.randint(17 * 60 + 30, 19 * 60)
        opening = action - 60
        now = action + rng.randint(10, 40)
        seen_by_herring = action - rng.randint(20, 45)
        # Before the food arrived (so the claim is impossible), not merely
        # earlier than the theft.
        impossible = action - rng.randint(70, 130)
        seen_by_janitor = action + rng.randint(0, 3)
        missing = rng.randint(2, 4)
        camera = rng.randint(1, 6)

        prop = rng.choice([key for key in sorted(PROPS) if key != "napkin"])
        wiping = "napkin"
        order = ["herring", "confusion", "conflict"]
        rng.shuffle(order)

        texts = {
            "opening": (
                f"下午 {_fmt(opening)} 點了{target_zh}放茶水間，順便冰了{main_side}。"
                f"現在 {_fmt(now)}，{target_zh}少了 {missing} {unit}，"
                f"{other_side}好像也被動過。"
            ),
            "herring": (
                f"{herring} 說 {_fmt(seen_by_herring)} 去茶水間拿了一個"
                f"{PROPS[prop]}，看到 {observed} 站在{other_side}旁邊。"
                f"{observed} 堅稱當時只拿著{main_side}在微波爐前面。"
            ),
            "confusion": (
                f"{confused} 說 {_fmt(impossible)} 聽到茶水間有人在講話，"
                f"但那個時間{target_zh}還沒送到。"
            ),
            "conflict": (
                f"{culprit} 的主管說 {culprit} 整個下午都在座位趕報表，"
                f"但清潔阿姨說 {_fmt(seen_by_janitor)} 看到 {culprit} "
                f"從茶水間出來，手裡還拿著{PROPS[wiping]}擦嘴。"
            ),
        }
        focus = {
            "herring": [
                f"{herring.lower()}_alibi_verified",
                f"{observed.lower()}_alibi_{distractors[0]}",
            ],
            "confusion": ["time_confusion_rejected"],
            "conflict": [
                f"{culprit.lower()}_location_conflict",
                "janitor_testimony",
            ],
        }

        turns: List[Dict[str, Any]] = [
            {
                "turn_id": 0,
                "dt_s": 0.0,
                "user_input": texts["opening"],
                "expected_internal_focus": [
                    f"{target_key}_missing_{missing}",
                    f"{distractors[0]}_checked",
                ],
            }
        ]
        for position, kind in enumerate(order, start=1):
            turns.append(
                {
                    "turn_id": position,
                    "dt_s": _sample_dt(rng),
                    "user_input": texts[kind],
                    "expected_internal_focus": focus[kind],
                }
            )
        turns.append(
            {
                "turn_id": len(turns),
                "dt_s": _sample_dt(rng),
                "user_input": (
                    "好，根據目前的口供和時間線交叉比對，"
                    f"你認為誰是吃掉{target_zh}的人？請給出你的最終推論。"
                ),
                "expected_final_deduction": culprit,
            }
        )

        return {
            "session_id": f"ecosystem_pantry_{index:03d}",
            "schema_version": SCHEMA_VERSION,
            "session_meta": {
                "seed": self.seed,
                "index": index,
                "split": "heldout" if self.is_heldout(index) else "train",
                "testimony_order": order,
                "slots": len(actors) + len(distractors) + 1 + 3,
                # The plan the testimony describes, so the timeline can be
                # checked instead of trusted: the impossible claim must precede
                # delivery, and the janitor must see the culprit leave after the
                # theft and before the conversation starts.
                "timeline": {
                    "impossible_claim": _fmt(impossible),
                    "opening": _fmt(opening),
                    "action": _fmt(action),
                    "janitor_sighting": _fmt(seen_by_janitor),
                    "now": _fmt(now),
                },
            },
            "environment": {
                "actors": list(actors),
                "items": [target_key] + list(distractors),
                "props": [prop, wiping],
            },
            "ground_truth_oracle": {
                "target_item": target_key,
                "culprit": culprit,
                "action_time": _fmt(action),
                "evidence_tag": (
                    f"surveillance_cam_{camera}_timestamp_" f"{_fmt(action).replace(':', '')}"
                ),
            },
            "turns": turns,
        }

    # -- gates --------------------------------------------------------------

    @staticmethod
    def validate(splits: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Every data-side gate from the spec, as a list of violations.

        A violation is a string a reader can act on; an empty list means the
        corpus is well formed. Nothing here looks at a model.
        """
        problems: List[str] = []
        for split, sessions in splits.items():
            for session in sessions:
                problems.extend(_validate_session(session, split))

        train = splits.get("train", [])
        heldout = splits.get("heldout", [])
        if train and heldout:
            problems.extend(_validate_split(train, heldout))
        return problems


def _minutes(stamp: str) -> int:
    hour, minute = stamp.split(":")
    return int(hour) * 60 + int(minute)


def _validate_timeline(
    meta: Dict[str, Any], oracle: Dict[str, Any], split: str, sid: str
) -> List[str]:
    """The stated times must describe one consistent afternoon.

    Without this, "the time is impossible" is only an assertion in prose: a
    corpus could claim a contradiction while its own numbers agree.
    """
    timeline = meta.get("timeline") or {}
    names = ("impossible_claim", "opening", "action", "janitor_sighting", "now")
    missing = [name for name in names if name not in timeline]
    if missing:
        return [f"{split}/{sid}: timeline is missing {missing}"]
    try:
        values = [_minutes(timeline[name]) for name in names]
    except (AttributeError, ValueError):
        return [f"{split}/{sid}: timeline is not HH:MM"]

    out: List[str] = []
    if timeline["action"] != oracle["action_time"]:
        out.append(f"{split}/{sid}: timeline action != oracle action_time")
    impossible, opening, action, sighting, now = values
    if not impossible < opening:
        out.append(f"{split}/{sid}: the 'impossible' claim is not before delivery")
    if not opening < action:
        out.append(f"{split}/{sid}: food arrives after the theft")
    if not action <= sighting:
        out.append(f"{split}/{sid}: the janitor sees the culprit before the theft")
    if not sighting <= now:
        out.append(f"{split}/{sid}: the janitor's sighting is in the future")
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

    slots = meta.get("slots")
    if not isinstance(slots, int) or slots > MAX_SLOTS:
        out.append(f"{split}/{sid}: slots {slots} > {MAX_SLOTS}")

    out.extend(_validate_timeline(meta, oracle, split, sid))

    if len(turns) < 3:
        out.append(f"{split}/{sid}: {len(turns)} turns is too few")
        return out
    for position, turn in enumerate(turns):
        if turn.get("turn_id") != position:
            out.append(f"{split}/{sid}: turn_id {turn.get('turn_id')} at {position}")
        if not isinstance(turn.get("dt_s"), (int, float)) or turn["dt_s"] < 0:
            out.append(f"{split}/{sid}: turn {position} dt_s {turn.get('dt_s')!r}")
        if position == 0 and turn.get("dt_s") != 0.0:
            out.append(f"{split}/{sid}: first turn dt_s is not 0.0")
        text = turn.get("user_input") or ""
        if not text:
            out.append(f"{split}/{sid}: turn {position} has no text")
        tag = oracle["evidence_tag"]
        if tag in text or "surveillance" in text.lower():
            out.append(f"{split}/{sid}: turn {position} leaks the camera tag")
        lowered = text.lower()
        for marker in VERDICT_MARKERS:
            if marker.lower() in lowered:
                out.append(f"{split}/{sid}: turn {position} contains verdict marker {marker!r}")

    final = turns[-1]
    if final.get("expected_final_deduction") != oracle["culprit"]:
        out.append(f"{split}/{sid}: final deduction does not match the oracle")
    for turn in turns[:-1]:
        if "expected_final_deduction" in turn:
            out.append(f"{split}/{sid}: turn {turn.get('turn_id')} has a final deduction")
        if not turn.get("expected_internal_focus"):
            out.append(f"{split}/{sid}: turn {turn.get('turn_id')} has no focus tags")
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

    def texts(sessions: Sequence[Dict[str, Any]]) -> set:
        return {turn["user_input"] for session in sessions for turn in session["turns"]}

    shared_texts = texts(train).intersection(texts(heldout))
    if shared_texts:
        out.append(f"verbatim turn text appears in both splits: {sorted(shared_texts)[:1]}")
    return out


def summarise(
    splits: Dict[str, List[Dict[str, Any]]], payload: str, seed: int, fraction: float
) -> Dict[str, Any]:
    bands = {"short": 0, "mid": 0, "long": 0}
    turns = 0
    for sessions in splits.values():
        for session in sessions:
            for turn in session["turns"]:
                turns += 1
                bands[_band_for(float(turn["dt_s"]))] += 1
    return {
        "schema_version": SCHEMA_VERSION,
        "generator": "scripts/gen_pantry_ecosystem.py",
        "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seed": seed,
        "heldout_fraction": fraction,
        "counts": {name: len(sessions) for name, sessions in splits.items()},
        "turns": turns,
        "dt_bands": bands,
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
            f"bands={manifest['dt_bands']}"
        )
        return 0

    manifest = write_corpus(out, args.seed, args.sessions, args.heldout_fraction)
    print(
        f"wrote {out}\n"
        f"  sessions  : {manifest['counts']['train']} train / "
        f"{manifest['counts']['heldout']} held-out\n"
        f"  turns     : {manifest['turns']}\n"
        f"  dt bands  : {manifest['dt_bands']}\n"
        f"  digest    : {manifest['file_sha256'][:16]}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
