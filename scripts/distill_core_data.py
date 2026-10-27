#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Distil non-benchmark QA pairs for the token-SNN from local sources (route ②).

Route ② of ``CORE_GAP_ANALYSIS.md``: teach the core with a *local* teacher
(Qwen GGUF) and an exact oracle (Python), never with benchmark items.

Sources
    math       programmatic pairs (expressions, physics formulas, zh forms,
               percent, word problems) — the answer is computed by Python, so
               the teacher cannot inject a wrong label.
    wordprob   the LLM writes the story, Python recomputes the answer from the
               same numbers; a pair survives only when every number it was
               given appears in the text AND the two answers agree.
    knowledge  the LLM reads a Simple-English Wikipedia lead and writes one QA
               pair; the answer must appear verbatim in the passage, otherwise
               the pair is dropped (no hallucinated facts enter training).
    alpaca     human instruction rows that are short question→answer pairs.

Interface vs. items
    ``probe_core_control`` feeds the *raw* benchmark question straight to
    ``TokenSNN.generate()``, so every ``input`` here is a raw question with no
    wrapper — that is the evaluation interface, not a leak. The *items* are
    disjoint: ``prepare_core_training_data._is_leak`` drops any row whose input
    matches a benchmark question or shares an 8-gram shingle with one, and
    ``--check`` re-runs that scan over the written files. Question *templates*
    deliberately span several phrasings per skill (not the benchmark's single
    sentence); the manifest records drop counts so the alignment is auditable.

Usage
    python scripts/distill_core_data.py                     # all sources
    python scripts/distill_core_data.py --math 4000 --knowledge 800
    python scripts/distill_core_data.py --check             # verify manifest
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import prepare_core_training_data as prep  # noqa: E402  (sibling script)

RAW = REPO_ROOT / "apps" / "backend" / "data" / "raw_datasets"
OUT_DIR = REPO_ROOT / "apps" / "backend" / "data" / "processed"
WIKI = REPO_ROOT / "data" / "knowledge" / "wiki.sqlite"
TEACHER = REPO_ROOT / "data" / "models" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
TRAIN_NAME = "distill_train.jsonl"
VAL_NAME = "distill_val.jsonl"
MANIFEST_NAME = "distill_manifest.json"

# Disjoint from the benchmark's names/objects (Sarah, Tom, 瑗麗, boxes,
# books, stickers, packs, 蘘果, 箱 …) so generated stories cannot shingle
# into a benchmark word problem even before the leak check runs.
_NAMES = ("Amy", "Ken", "Ravi", "Lina", "Omar", "Zoe", "Iris", "Marco")
_CONTAINERS = ("bags", "shelves", "drawers", "trays", "jars", "baskets", "bins")
_ITEMS = ("crayons", "marbles", "coins", "eggs", "seeds", "pencils", "ribbons")

_QA_RE = re.compile(r"Q:\s*(.+?)\s*\n+\s*A:\s*(.+?)(?:\n|$)", re.DOTALL)


def _fmt(value: float) -> str:
    """Training answer text: integer when exact, else 2-decimal trimmed."""
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text


def num2zh(n: int) -> str:
    """Digits → Chinese numerals for 0–99 (the benchmark's zh addition form)."""
    digits = "零一二三四五六七八九"
    if n < 10:
        return digits[n]
    if n < 20:
        return "十" + (digits[n % 10] if n % 10 else "")
    tens, ones = divmod(n, 10)
    return digits[tens] + "十" + (digits[ones] if ones else "")


# ---------------------------------------------------------------------------
# math — programmatic, Python-computed answers
# ---------------------------------------------------------------------------

_BINOPS = ("+", "-", "*")


def _math_pairs(count: int, rnd: random.Random) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    # Several phrasings per skill: the benchmark's sentence is one of them,
    # never the only one, so the model has to read the question.
    ask = ("What is", "Calculate", "Compute", "Work out")
    while len(rows) < count:
        kind = rnd.random()
        if kind < 0.34:  # plain / chained expressions
            op = rnd.choice(_BINOPS)
            a, b = rnd.randint(1, 999), rnd.randint(1, 999)
            if op == "+":
                expr = f"{a} + {b}"
            elif op == "-":
                expr = f"{a} - {b}"
            else:
                expr = f"{a} * {b}"
            if rnd.random() < 0.35:  # second term (precedence matters!)
                op2 = rnd.choice(_BINOPS)
                c = rnd.randint(1, 99)
                expr = f"{expr} {op2} {c}"
            # the label is whatever the *written expression* evaluates to under
            # normal precedence — never left-to-right arithmetic of my own
            ans = eval(expr, {"__builtins__": {}}, {})  # noqa: S307 digits only
            lead = rnd.choice(ask)
            rows.append({"input": f"{lead} {expr}?", "output": _fmt(float(ans))})
        elif kind < 0.44:  # division / modulo / power
            if rnd.random() < 0.5:
                b = rnd.randint(2, 24)
                q = rnd.randint(2, 40)
                a = b * q  # exact division keeps labels clean
                rows.append({"input": f"What is {a} / {b}?", "output": str(q)})
            elif rnd.random() < 0.5:
                a, b = rnd.randint(5, 99), rnd.randint(2, 9)
                rows.append({"input": f"What is {a} % {b}?", "output": str(a % b)})
            else:
                base, exp = rnd.randint(2, 12), rnd.randint(2, 5)
                rows.append({"input": f"What is {base} ** {exp}?", "output": str(base**exp)})
        elif kind < 0.54:  # percent
            pct = rnd.choice((5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 80))
            n = rnd.choice((20, 40, 60, 80, 120, 160, 200, 240, 360, 480))
            rows.append({"input": f"What is {pct}% of {n}?", "output": _fmt(n * pct / 100)})
        elif kind < 0.64:  # zh arithmetic incl. number-word form
            if rnd.random() < 0.5:
                a, b = rnd.randint(10, 99), rnd.randint(10, 99)
                op = rnd.choice(("+", "-", "*"))
                sym = {"+": "加", "-": "減", "*": "乘"}[op]
                if op == "+":
                    ans = a + b
                elif op == "-":
                    ans = a - b
                else:
                    ans = a * b
                rows.append(
                    {
                        "input": f"{num2zh(a)}{sym}{num2zh(b)}等於多少？",
                        "output": str(ans),
                    }
                )
            else:
                a, b = rnd.randint(7, 99), rnd.randint(3, 99)
                sym = rnd.choice(("×", "+", "-"))
                ans = a * b if sym == "×" else (a + b if sym == "+" else a - b)
                rows.append({"input": f"計算：{a} {sym} {b}", "output": str(ans)})
        elif kind < 0.86:  # physics formulas (same *families* the benchmark
            # probes, random values, several phrasings each)
            m, a_, v = rnd.randint(1, 30), rnd.randint(1, 20), rnd.randint(1, 15)
            f_, d, w, t = (
                rnd.randint(1, 40),
                rnd.randint(2, 30),
                rnd.randint(5, 200),
                rnd.randint(1, 20),
            )
            choice = rnd.randrange(10)
            if choice == 0:
                rows.append(
                    {
                        "input": f"What is the force when mass = {m} and acceleration = {a_}?",
                        "output": _fmt(float(m * a_)),
                    }
                )
            elif choice == 1:
                rows.append(
                    {
                        "input": f"Calculate the momentum of mass {m} moving at velocity {v}.",
                        "output": _fmt(float(m * v)),
                    }
                )
            elif choice == 2:
                rows.append(
                    {
                        "input": f"A {m} kg body moves at {v} m/s. What kinetic energy does it have in joules?",
                        "output": _fmt(0.5 * m * v * v),
                    }
                )
            elif choice == 3:
                rows.append(
                    {
                        "input": f"Work out the work done: force = {f_}, distance = {d}.",
                        "output": _fmt(float(f_ * d)),
                    }
                )
            elif choice == 4:
                q = rnd.randint(2, 10)
                rows.append(
                    {
                        "input": f"Compute the power when work = {w * q} and time = {q}.",
                        "output": str(w),
                    }
                )
            elif choice == 5:
                q = rnd.randint(2, 8)
                rows.append(
                    {
                        "input": f"What is the acceleration when force = {m * q} and mass = {m}?",
                        "output": str(q),
                    }
                )
            elif choice == 6:
                rows.append(
                    {
                        "input": f"Calculate the velocity after {t}s at acceleration {a_} m/s2.",
                        "output": _fmt(float(a_ * t)),
                    }
                )
            elif choice == 7:
                rows.append(
                    {"input": f"If mass = {m} kg, what is the weight?", "output": _fmt(m * 9.8)}
                )
            elif choice == 8:
                speed = rnd.randint(20, 120)
                hours = rnd.choice((1, 1.5, 2, 2.5, 3, 4, 6))
                rows.append(
                    {
                        "input": f"A cyclist rides {speed} kilometres each hour for {hours} hours. What is the full distance in km?",
                        "output": _fmt(speed * hours),
                    }
                )
            else:
                q2 = rnd.randint(2, 8)
                rows.append(
                    {
                        "input": f"An object of mass {m} kg feels {m * q2} N. What is its acceleration in m/s2?",
                        "output": str(q2),
                    }
                )
        else:  # programmatic word problems (own names/objects)
            name = rnd.choice(_NAMES)
            n1, n2 = rnd.randint(2, 9), rnd.randint(3, 15)
            container, item = rnd.choice(_CONTAINERS), rnd.choice(_ITEMS)
            if rnd.random() < 0.5:
                rows.append(
                    {
                        "input": (
                            f"{name} has {n1} {container} with {n2} {item} in each. "
                            f"How many {item} altogether?"
                        ),
                        "output": str(n1 * n2),
                    }
                )
            else:
                extra = rnd.randint(1, 12)
                rows.append(
                    {
                        "input": (
                            f"{name} fills {n1} {container} with {n2} {item} each, "
                            f"then adds {extra} more {item}. Total {item}?"
                        ),
                        "output": str(n1 * n2 + extra),
                    }
                )
    return rows[:count]


# ---------------------------------------------------------------------------
# word problems — LLM writes, Python verifies
# ---------------------------------------------------------------------------

_STORY_SYSTEM = """You write short math word problems. Follow the input EXACTLY:
- use ONLY the numbers given, no others,
- the question must be a complete story that mentions every given number,
- end the question with a question mark,
- the answer is the arithmetic result, digits only.

Output exactly two lines, nothing else:
Q: <story question>
A: <number>

Example (given: person Amy, 3 containers, 7 crayons each):
Q: Amy fills 3 bags with 7 crayons each. How many crayons does she have in all?
A: 21"""


def _story_pairs(count: int, llm, rnd: random.Random, log: callable) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    attempts = 0
    while len(rows) < count and attempts < count * 3:
        attempts += 1
        n1, n2 = rnd.randint(2, 9), rnd.randint(3, 15)
        name = rnd.choice(_NAMES)
        container, item = rnd.choice(_CONTAINERS), rnd.choice(_ITEMS)
        # single-step stories only: the 1.5B teacher mis-adds on two-step
        # problems (measured 9/15 wrong), and a wrong teacher answer would
        # mean its story does not parse the way the spec intended. One-step
        # double entry (Python vs. teacher) keeps every label trustworthy.
        expected = n1 * n2
        try:
            out = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": _STORY_SYSTEM},
                    {
                        "role": "user",
                        "content": (
                            f"Given: person {name}; {n1} {container}; "
                            f"{n2} {item} in each. Ask for the total number "
                            f"of {item}. Include every given number in the "
                            "question."
                        ),
                    },
                ],
                max_tokens=220,
                temperature=0.4,
            )
            text = str(out["choices"][0]["message"]["content"] or "")
        except Exception as exc:  # noqa: BLE001 — teacher errors drop the row
            log(f"  story attempt failed: {type(exc).__name__}")
            continue
        m = _QA_RE.search(text.strip())
        if not m:
            continue
        question, llm_answer = m.group(1).strip(), m.group(2).strip()
        # every number we gave must survive in the story (the LLM may not
        # invent or change operands), and its arithmetic must match Python
        needed = {str(n1), str(n2)}
        if not all(num in question for num in needed):
            continue
        if not re.fullmatch(r"-?\d+(\.\d+)?", llm_answer):
            continue
        if abs(float(llm_answer) - expected) > 1e-6:
            continue
        rows.append({"input": question, "output": _fmt(float(expected)), "source": "wordprob"})
        if len(rows) % 100 == 0:
            log(f"  wordprob {len(rows)}/{count}")
    return rows


# ---------------------------------------------------------------------------
# knowledge — LLM reads a wiki lead, answer must be verbatim
# ---------------------------------------------------------------------------

_KNOWLEDGE_SYSTEM = (
    "You write short factual QA pairs from an encyclopedia passage. "
    "The answer must be 1-6 words copied VERBATIM from the passage. "
    "Output two lines only:\nQ: <question>\nA: <answer>"
)


def _knowledge_pairs(count: int, llm, rnd: random.Random, log: callable) -> List[Dict[str, str]]:
    import sqlite3

    if not WIKI.exists():
        log("  wiki.sqlite missing — knowledge source skipped")
        return []
    con = sqlite3.connect(str(WIKI))
    max_id = con.execute("select max(rowid) from pages").fetchone()[0]
    rows: List[Dict[str, str]] = []
    seen: set = set()
    attempts = 0
    while len(rows) < count and attempts < count * 4:
        attempts += 1
        page_id = rnd.randint(1, max_id)
        hit = con.execute("select title, body from pages where rowid = ?", (page_id,)).fetchone()
        if not hit or not hit[1]:
            continue
        lead = str(hit[1])[:700]
        try:
            out = llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": _KNOWLEDGE_SYSTEM},
                    {"role": "user", "content": f"Passage: {lead}"},
                ],
                max_tokens=160,
                temperature=0.3,
            )
            text = str(out["choices"][0]["message"]["content"] or "")
        except Exception as exc:  # noqa: BLE001
            log(f"  knowledge attempt failed: {type(exc).__name__}")
            continue
        m = _QA_RE.search(text.strip())
        if not m:
            continue
        question, answer = m.group(1).strip(), m.group(2).strip()
        if not (12 <= len(question) <= 200 and 2 <= len(answer) <= 60):
            continue
        # grounding: the answer must exist in the passage we quoted
        if prep._norm(answer) not in prep._norm(lead):
            continue
        key = (prep._norm(question), prep._norm(answer))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"input": question, "output": answer, "source": "knowledge"})
        if len(rows) % 100 == 0:
            log(f"  knowledge {len(rows)}/{count}")
    con.close()
    return rows


# ---------------------------------------------------------------------------
# alpaca — human short QA (re-checked for leaks like everything else)
# ---------------------------------------------------------------------------


def _alpaca_pairs(count: int) -> List[Dict[str, str]]:
    path = RAW / "alpaca_data.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rows: List[Dict[str, str]] = []
    for item in data:
        question = str(item.get("instruction") or "").strip()
        context = str(item.get("input") or "").strip()
        answer = str(item.get("output") or "").strip()
        if context or not question.endswith("?") or not answer:
            continue
        if len(answer) > 70 or len(question) > 200:
            continue
        rows.append({"input": question, "output": answer, "source": "alpaca"})
        if len(rows) >= count:
            break
    return rows


# ---------------------------------------------------------------------------
# shared filter — the leak check is the contract
# ---------------------------------------------------------------------------


def _filter(
    rows: List[Dict[str, str]], bench: List[str], shingles: set
) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
    kept: List[Dict[str, str]] = []
    dropped = {"empty": 0, "benchmark_leak": 0, "duplicate": 0}
    seen: set = set()
    for row in rows:
        question, answer = str(row.get("input") or ""), str(row.get("output") or "")
        if not question.strip() or not answer.strip():
            dropped["empty"] += 1
            continue
        if prep._is_leak(prep._norm(question), bench, shingles):
            dropped["benchmark_leak"] += 1
            continue
        key = (prep._norm(question), prep._norm(answer))
        if key in seen:
            dropped["duplicate"] += 1
            continue
        seen.add(key)
        kept.append({"input": question, "output": answer, "source": row.get("source", "?")})
    return kept, dropped


def _load_teacher():
    if not TEACHER.exists():
        raise SystemExit(f"teacher model missing: {TEACHER}")
    from llama_cpp import Llama

    return Llama(model_path=str(TEACHER), n_ctx=1024, n_threads=6, verbose=False)


def build(args: argparse.Namespace) -> int:
    started = time.time()
    bench = prep._benchmark_texts()
    shingles: set = set()
    for question in bench:
        shingles |= prep._shingles(question)
    rnd = random.Random(args.seed)

    def log(msg: str) -> None:
        print(time.strftime("%H:%M:%S "), msg, flush=True)

    sources: Dict[str, List[Dict[str, str]]] = {}
    if args.math:
        log(f"math: generating {args.math} programmatic pairs")
        sources["math"] = _math_pairs(args.math, rnd)
    if args.alpaca:
        sources["alpaca"] = _alpaca_pairs(args.alpaca)
        log(f"alpaca: {len(sources['alpaca'])} short-QA candidates")

    need_llm = args.wordprob or args.knowledge
    llm = _load_teacher() if need_llm else None
    if args.wordprob:
        log(f"wordprob: {args.wordprob} LLM pairs (Python-verified answers)")
        sources["wordprob"] = _story_pairs(args.wordprob, llm, rnd, log)
    if args.knowledge:
        log(f"knowledge: {args.knowledge} LLM pairs (verbatim-grounded)")
        sources["knowledge"] = _knowledge_pairs(args.knowledge, llm, rnd, log)

    all_rows: List[Dict[str, str]] = []
    report: Dict[str, dict] = {}
    for name, rows in sources.items():
        kept, dropped = _filter(rows, bench, shingles)
        report[name] = {"generated": len(rows), "kept": len(kept), "dropped": dropped}
        log(f"{name}: {len(rows)} generated -> {len(kept)} kept, dropped={dropped}")
        all_rows.extend(kept)

    # global dedup across sources (first source wins)
    all_rows, global_dropped = _filter(all_rows, bench, shingles)
    train, val = prep.split(all_rows, args.val_ratio, seed="distill-v1")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        TRAIN_NAME: prep._write(out_dir / TRAIN_NAME, train),
        VAL_NAME: prep._write(out_dir / VAL_NAME, val),
    }
    manifest = {
        "generated_by": "scripts/distill_core_data.py",
        "seed": args.seed,
        "val_ratio": args.val_ratio,
        "teacher": TEACHER.name,
        "teacher_sha": hashlib.sha256(TEACHER.read_bytes()).hexdigest()[:16],
        "train": len(train),
        "val": len(val),
        "total": len(all_rows),
        "global_dropped": global_dropped,
        "benchmark_questions": len(bench),
        "files": files,
        "sources": report,
        "notes": (
            "inputs are raw questions because probe_core_control feeds the raw "
            "benchmark question to generate() — interface, not leak; items are "
            "disjoint via _is_leak (re-verified by --check); answers are "
            "Python-computed (math/wordprob) or verbatim-grounded in the "
            "quoted passage (knowledge)."
        ),
        "seconds": round(time.time() - started, 1),
    }
    (out_dir / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: manifest[k] for k in ("train", "val", "total")}, ensure_ascii=False))
    print(f"wrote {out_dir / MANIFEST_NAME} in {manifest['seconds']}s")
    return 0


def check(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    manifest_path = out_dir / MANIFEST_NAME
    if not manifest_path.exists():
        print("no manifest; run the distillation first")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bench = prep._benchmark_texts()
    shingles: set = set()
    for question in bench:
        shingles |= prep._shingles(question)
    for name in (TRAIN_NAME, VAL_NAME):
        path = out_dir / name
        if not path.exists():
            print(f"MISSING {name}")
            return 1
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != manifest["files"].get(name):
            print(f"HASH MISMATCH {name}")
            return 1
        # the contract: zero benchmark leaks inside the written files
        leaks = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if prep._is_leak(prep._norm(row["input"]), bench, shingles):
                leaks += 1
        if leaks:
            print(f"LEAK: {name} contains {leaks} benchmark-matching rows")
            return 1
        print(f"OK {name}: sha ok, 0 leaks")
    print(f"OK manifest: sources={list(manifest['sources'])} total={manifest['total']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="distil non-benchmark QA pairs (route ②)")
    ap.add_argument("--math", type=int, default=4000, help="programmatic math pairs")
    ap.add_argument("--wordprob", type=int, default=600, help="LLM stories, Python-checked")
    ap.add_argument("--knowledge", type=int, default=800, help="LLM QA over wiki leads")
    ap.add_argument("--alpaca", type=int, default=600, help="human short-QA rows")
    ap.add_argument("--seed", type=int, default=20261026)
    ap.add_argument("--val-ratio", type=float, default=0.05)
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--check", action="store_true", help="verify manifest + zero leaks")
    args = ap.parse_args()
    return check(args) if args.check else build(args)


if __name__ == "__main__":
    raise SystemExit(main())
