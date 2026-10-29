#!/usr/bin/env python3
"""對話記憶量測 — 教過的事實，之後問得出來嗎？（**記憶層，不是學習**）

**這支腳本回答的問題**：只靠**交談**（陳述事實、更正、教一個同義詞），
系統能不能把這些紀錄歸屬到說話者、並在之後的問句裡回想起來：

1. `taught`   同一種問法 → 答對（回想）
2. `transfer` 沒教過的說法（首府／capital）→ 答對（泛化）
3. `compose`  兩個教過的事實放進同一題 → 兩個都答對（組合）
4. `correct`  被更正後（不是 A，是 B）→ 答 B 且不再答 A（錯誤修正）
5. `retain`   經過若干無關回合後 → 還記得（穩定）
6. `heldout`  以上全部換成**另一組實體與關係**（實作完成後才建立）→ 這是分數

**為什麼用發明的實體**：`Zorblax`／`Quuxville` 不存在於任何語料、索引或題庫，
所以答對只可能來自這次對話；答不出來就是答不出來，沒有巧合可撿。

**這不是「學習」**（見 docs/06-project-management/LAYER_SEPARATION.md）：
資料在 `ai/memory/taught_facts.py` 的字典型紀錄裡，刪掉紀錄就沒有能力；
「換句話問」能過，是因為對話中先教了同義詞，屬記憶層的同義詞比對。
真正的學習要看 `scripts/probe_neural_learning.py`（刪除來源後仍答得出來），
目前結果是 **fail**。這裡的 100% 只證明「記得、更正得動、說得出是誰說的」。

用法：
    python scripts/probe_dialogue_teaching.py                 # 量測（不修改程式碼）
    python scripts/probe_dialogue_teaching.py --json /tmp/teaching.json
    python scripts/probe_dialogue_teaching.py --keep-data     # 保留沙盒資料
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

SANDBOX = Path(
    os.environ.get("ANGELA_PROBE_DATA_DIR") or (REPO_ROOT / "data" / "probe_dialogue_teaching")
)

# --------------------------------------------------------------------------- #
# The items: invented entities, two disjoint sets
# --------------------------------------------------------------------------- #
# `dev`      : the set used while building the mechanism (visible).
# `heldout`  : written after the mechanism, never used to shape it (the score).
# Both use the same *shape* (subject, relation, object) but different words, so a
# mechanism that generalises answers both; one tuned to `dev` fails `heldout`.
DEV_ITEMS: List[Dict[str, Any]] = [
    {
        "subject": "Zorblax",
        "relation": "首都",
        "object": "Quuxville",
        "correction": "Brindleford",
        "teach": "Zorblax 的首都是 Quuxville。",
        "ask": "Zorblax 的首都是哪裡？",
        "transfer": "Zorblax 的首府在哪裡？",
        "ask_en": "What is the capital of Zorblax?",
    },
    {
        "subject": "Vexmoor",
        "relation": "首都",
        "object": "Driftmoor",
        "correction": "Hollowmere",
        "teach": "Vexmoor 的首都是 Driftmoor。",
        "ask": "Vexmoor 的首都是哪裡？",
        "transfer": "Vexmoor 的首府在哪裡？",
        "ask_en": "What is the capital of Vexmoor?",
    },
    {
        "subject": "Pellucid",
        "relation": "創辦人",
        "object": "Mira Voss",
        "correction": "Tomas Reed",
        "teach": "Pellucid 的創辦人是 Mira Voss。",
        "ask": "Pellucid 的創辦人是誰？",
        "transfer": "Pellucid 是誰創辦的？",
        "ask_en": "Who founded Pellucid?",
    },
]

HELDOUT_ITEMS: List[Dict[str, Any]] = [
    {
        "subject": "Ondrast",
        "relation": "語言",
        "object": "Vellish",
        "correction": "Kornish",
        "teach": "Ondrast 的語言是 Vellish。",
        "ask": "Ondrast 的語言是什麼？",
        "transfer": "Ondrast 說哪一種話？",
        "ask_en": "What language is spoken in Ondrast?",
    },
    {
        "subject": "Skerrow",
        "relation": "貨幣",
        "object": "Thistlemark",
        "correction": "Goldfern",
        "teach": "Skerrow 的貨幣是 Thistlemark。",
        "ask": "Skerrow 的貨幣是什麼？",
        "transfer": "Skerrow 用什麼錢？",
        "ask_en": "What currency does Skerrow use?",
    },
    {
        "subject": "Ulmarrow",
        "relation": "發明人",
        "object": "Nissa Quill",
        "correction": "Rook Mabry",
        "teach": "Ulmarrow 的發明人是 Nissa Quill。",
        "ask": "Ulmarrow 的發明人是誰？",
        "transfer": "Ulmarrow 是誰發明的？",
        "ask_en": "Who invented Ulmarrow?",
    },
    {
        "subject": "Morrowgate",
        "relation": "語言",
        "object": "Sabletongue",
        "correction": "Ferrow",
        "teach": "Morrowgate 的語言是 Sabletongue。",
        "ask": "Morrowgate 的語言是什麼？",
        "transfer": "Morrowgate 說哪一種話？",
        "ask_en": "What language is spoken in Morrowgate?",
    },
]

FILLER = [
    "你好，我們隨便聊聊。",
    "今天過得還行。",
    "你覺得天空是什麼顏色？",
    "謝謝你陪我說話。",
    "我們等一下再聊別的。",
    "現在幾點了呢？",
    "說個笑話吧。",
    "我覺得有點累。",
    "你喜歡什麼音樂？",
    "晚安，早點休息。",
]


# --------------------------------------------------------------------------- #
# Sandbox + service (identical to the native-dialogue probe)
# --------------------------------------------------------------------------- #
def isolate_data_dir(keep: bool = False) -> Path:
    """Fresh sandbox per run -- stale memory would fake (or hide) learning."""
    if not keep:
        shutil.rmtree(SANDBOX, ignore_errors=True)
    os.environ["ANGELA_DATA_DIR"] = str(SANDBOX)
    os.environ["VECTOR_STORE_PATH"] = str(SANDBOX / "vector_store")
    os.environ["ANGELA_TAUGHT_FACTS"] = str(SANDBOX / "taught_facts.json")
    return SANDBOX


def build_native_service():
    import copy

    from core.system.config.tiered_loader import get_config
    from services.llm.router import AngelaLLMService

    config = copy.deepcopy(get_config("system/llm") or {})
    config.setdefault("deployment", {})["mode"] = "local"
    for _, backend in (config.get("backends") or {}).items():
        if str(backend.get("provider") or "").lower() not in {"unified", "ed3n", "garden"}:
            backend["enabled"] = False
    return AngelaLLMService(config=config)


# --------------------------------------------------------------------------- #
# Scoring (mechanical, auditable)
# --------------------------------------------------------------------------- #
def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def contains(text: str, needle: str) -> bool:
    return _norm(needle) in _norm(text)


def classify(response: str, expected: str, wrong: str = "") -> str:
    if not (response or "").strip():
        return "empty"
    if contains(response, expected):
        return "correct"
    if wrong and contains(response, wrong):
        return "stale"
    if re.search(r"不知道|不確定|沒有足夠|無法回答|還沒有|don't know|not sure", response, re.I):
        return "abstain"
    return "wrong"


def _git_state() -> Dict[str, Any]:
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True
            ).stdout.strip()
        )
        return {"head": head, "dirty_worktree": dirty, "code_changed_by_probe": False}
    except Exception:
        return {"head": "", "dirty_worktree": None, "code_changed_by_probe": False}


# --------------------------------------------------------------------------- #
# One conversation
# --------------------------------------------------------------------------- #
class Recorder:
    def __init__(self) -> None:
        self.turns: List[Dict[str, Any]] = []

    async def say(self, service, session: str, history: List[Dict[str, str]], message: str) -> str:
        import services.llm.router as router_mod
        from api.routes.chat_routes import _handle_chat_request

        router_mod._llm_service = service
        started = time.time()
        try:
            result = await _handle_chat_request(
                user_message=message,
                user_name="teacher",
                history=list(history),
                session_id=session,
                origin="probe",
            )
            text = (result or {}).get("response") or (result or {}).get("text") or ""
            route = str((result or {}).get("route") or (result or {}).get("backend") or "")
        except Exception as exc:  # pragma: no cover - a broken pipeline is data
            text = ""
            route = f"error:{type(exc).__name__}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": text})
        self.turns.append(
            {
                "message": message,
                "response": text,
                "route": route,
                "seconds": round(time.time() - started, 3),
            }
        )
        return text

    def last_route(self) -> str:
        return self.turns[-1]["route"] if self.turns else ""


async def run_item(
    service, session: str, history, item: Dict[str, Any], rec: Recorder
) -> Dict[str, Any]:
    """cold → teach → taught → transfer → (correction) → retention."""
    result: Dict[str, Any] = {"subject": item["subject"], "relation": item["relation"]}

    cold = await rec.say(service, session, history, item["ask"])
    result["cold"] = classify(cold, item["object"])
    result["cold_text"] = cold[:160]

    await rec.say(service, session, history, item["teach"])
    taught = await rec.say(service, session, history, item["ask"])
    result["taught"] = classify(taught, item["object"])
    result["taught_text"] = taught[:160]
    result["taught_route"] = rec.last_route()

    taught_en = await rec.say(service, session, history, item["ask_en"])
    result["taught_en"] = classify(taught_en, item["object"])
    result["taught_en_text"] = taught_en[:160]

    transfer = await rec.say(service, session, history, item["transfer"])
    result["transfer"] = classify(transfer, item["object"])
    result["transfer_text"] = transfer[:160]
    result["transfer_route"] = rec.last_route()

    # A third exposure (dose-response): does more teaching help more?
    await rec.say(service, session, history, item["teach"])
    result["taught_2"] = classify(
        await rec.say(service, session, history, item["ask"]), item["object"]
    )

    correction = (
        f"更正：{item['subject']} 的{item['relation']}不是 {item['object']}，"
        f"是 {item['correction']}。"
    )
    await rec.say(service, session, history, correction)
    fixed = await rec.say(service, session, history, item["ask"])
    result["correct"] = classify(fixed, item["correction"], wrong=item["object"])
    result["correct_text"] = fixed[:160]
    return result


DEV_ALIASES = [
    "在這裡，首府和首都指的是同一件事。",
    "口語上，「誰創辦的」和「創辦人是誰」是同一個問題。",
    "capital 和 首都 指的是同一件事。",
    "founder 和 創辦人 指的是同一件事。",
]
HELDOUT_ALIASES = [
    "「說哪一種話」和「語言」指的是同一件事。",
    "「用什麼錢」和「貨幣」指的是同一件事。",
    "「是誰發明的」和「發明人」是同一個問題。",
    "language 和 語言 指的是同一件事。",
    "currency 和 貨幣 指的是同一件事。",
    "inventor 和 發明人 指的是同一件事。",
]


def current(item: Dict[str, Any]) -> str:
    """The value that is true *now* (the correction was taught during the run)."""
    return item.get("correction") or item["object"]


async def run_set(
    service, session: str, items: Sequence[Dict[str, Any]], rec: Recorder, aliases: Sequence[str]
) -> Dict[str, Any]:
    history: List[Dict[str, str]] = []
    # The relation synonyms are *taught*, not assumed: one sentence each, then
    # the mechanism must apply them to every subject on its own (that is the
    # transfer marker -- the synonym is never repeated per item).
    for alias in aliases:
        await rec.say(service, session, history, alias)

    results = []
    for item in items:
        results.append(await run_item(service, session, history, item, rec))

    # Composition: two taught facts in one question (no extra teaching). The
    # pair must share a relation, otherwise the question is unanswerable.
    pair = next(
        ((a, b) for a in items for b in items if a is not b and a["relation"] == b["relation"]),
        None,
    )
    if pair:
        first, second = pair
        combo = f"{first['subject']} 和 {second['subject']} 的{first['relation']}分別是什麼？"
        text = await rec.say(service, session, history, combo)
        composition = {
            "question": combo,
            "first": contains(text, current(first)),
            "second": contains(text, current(second)),
            "response": text[:200],
            "route": rec.last_route(),
        }
    else:  # pragma: no cover - sets always have >= 2
        composition = {"first": False, "second": False, "response": ""}

    # Retention: filler turns, then ask the first item again.
    for filler in FILLER:
        await rec.say(service, session, history, filler)
    retention_text = await rec.say(service, session, history, items[0]["ask"])
    retention = classify(retention_text, current(items[0]))

    return {"items": results, "composition": composition, "retention": retention}


def _rate(rows: Sequence[Dict[str, Any]], key: str) -> float:
    rows = [r for r in rows if key in r]
    if not rows:
        return 0.0
    return round(sum(1 for r in rows if r[key] == "correct") / len(rows), 4)


def summarise(rows: Sequence[Dict[str, Any]], extra: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "n": len(rows),
        "cold": _rate(rows, "cold"),
        "taught": _rate(rows, "taught"),
        "taught_en": _rate(rows, "taught_en"),
        "taught_2": _rate(rows, "taught_2"),
        "transfer": _rate(rows, "transfer"),
        "correct": _rate(rows, "correct"),
        "retention": extra.get("retention", 0.0),
        "composition_both": bool(
            extra.get("composition", {}).get("first") and extra.get("composition", {}).get("second")
        ),
        "stale_after_correction": sum(1 for r in rows if r.get("correct") == "stale"),
    }


def verdict(measured: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """The classic emergence markers, each with its measured number."""
    rows = [
        (
            "回想（教完同一問法）",
            f"{measured['taught']:.0%}",
            "yes" if measured["taught"] >= 0.6 else "no",
        ),
        (
            "泛化（沒教過的說法）",
            f"{measured['transfer']:.0%}",
            "yes" if measured["transfer"] >= 0.6 else "no",
        ),
        (
            "組合（兩個事實同題）",
            "both" if measured["composition_both"] else "no",
            "yes" if measured["composition_both"] else "no",
        ),
        (
            "更正（被更正後改口）",
            f"{measured['correct']:.0%}",
            "yes" if measured["correct"] >= 0.6 else "no",
        ),
        (
            "保留（10 個無關回合後，含更正後的值）",
            str(measured["retention"]),
            "yes" if measured["retention"] == "correct" else "no",
        ),
    ]
    return rows


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_path", help="write the full result as JSON")
    parser.add_argument("--keep-data", action="store_true", help="keep the sandbox memory")
    parser.add_argument("--set", choices=("dev", "heldout", "both"), default="both")
    args = parser.parse_args()

    isolate_data_dir(args.keep_data)
    from ai.memory.taught_facts import reset_taught_facts

    reset_taught_facts()
    if SANDBOX.exists() and not args.keep_data:
        shutil.rmtree(SANDBOX, ignore_errors=True)
    os.environ.pop("ANGELA_LEGACY_ED3N", None)

    git_before = _git_state()
    service = build_native_service()
    await service.initialize()

    rec = Recorder()
    out: Dict[str, Any] = {
        "git": git_before,
        "layer": "memory",
        "measures": "recall_not_learning",
        "sets": {},
    }
    if args.set in ("dev", "both"):
        dev = await run_set(service, "probe-teach-dev", DEV_ITEMS, rec, DEV_ALIASES)
        out["sets"]["dev"] = {"summary": summarise(dev["items"], dev), **dev}
    if args.set in ("heldout", "both"):
        held = await run_set(service, "probe-teach-heldout", HELDOUT_ITEMS, rec, HELDOUT_ALIASES)
        out["sets"]["heldout"] = {"summary": summarise(held["items"], held), **held}

    out["routing"] = {}
    for turn in rec.turns:
        out["routing"][turn["route"]] = out["routing"].get(turn["route"], 0) + 1
    out["git_after"] = _git_state()
    out["code_changed_by_probe"] = out["git_after"] != git_before

    print("對話記憶量測（記憶層，不是學習；發明實體：不可能從語料或題庫撿到答案）")
    for name, payload in out["sets"].items():
        print(f"\n── {name}（n={payload['summary']['n']}） ──")
        for row in payload["items"]:
            print(
                f"  {row['subject']:<10} 冷:{row['cold']:<7} 教:{row['taught']:<7}"
                f" 英:{row['taught_en']:<7} 再教:{row['taught_2']:<7}"
                f" 換句話問:{row['transfer']:<7} 更正:{row['correct']:<7}"
            )
            print(f"      教後回應：{row['taught_text']}")
            print(f"      換句話問：{row['transfer_text']}")
        comp = payload["composition"]
        print(
            f"  組合：A={'✓' if comp['first'] else '✗'} B={'✓' if comp['second'] else '✗'}"
            f"  → {comp['response'][:120]}"
        )
        print(f"  保留（10 回合後）：{payload['retention']}")

    print("\n── 記憶層驗收（門檻 60%，機械判定；不代表學習／智能） ──")
    score = out["sets"].get("heldout") or out["sets"].get("dev")
    if score:
        for label, value, present in verdict(score["summary"]):
            print(f"  {label:<22} {value:>8}   {'有' if present == 'yes' else '沒有'}")
    print(f"\n  回答來源：{json.dumps(out['routing'], ensure_ascii=False)}")
    print(f"  探針是否改動程式碼：{'是' if out['code_changed_by_probe'] else '否'}")
    print("  學習證據：無 —— 見 scripts/probe_neural_learning.py（目前 fail）")

    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print(f"  JSON：{args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
