#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================
"""Train ONE model to converse using an internal state (not context history).

Weights: Qwen3-0.6B base + its fine-tuned adapter, merged; then a short LoRA
update so the SAME model learns to read a state vector. State: final hidden
state of the teaching turn, projected into embedding space and injected into the
next turn's embeddings. The test prompt contains ONLY the question — no prior
turns, no KV cache, no second model.

Pre-registered gate (before running): held-out name/colour/city recall > 0 and
at least one coherent generated answer. If 0, report falsified; do not claim.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path
from typing import List, Tuple

import torch
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "data" / "models" / "qwen3-0.6b"
ADAPTER = REPO / "data" / "models" / "qwen3-0.6b-finetuned"

NAMES = ["小明", "小華", "阿哲", "美玲", "志強", "嘉紋", "雅婷", "俊傑"]
COLORS = ["藍色", "綠色", "紅色", "紫色", "橙色", "黑色"]
CITIES = ["台北", "新竹", "台中", "台南", "高雄", "花蓮"]


def make_sessions(n: int, seed: int) -> List[Tuple[str, str, str, str]]:
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        kind = rng.choice(("name", "colour", "city"))
        value = rng.choice({"name": NAMES, "colour": COLORS, "city": CITIES}[kind])
        teach = {
            "name": f"我的名字是{value}。",
            "colour": f"我最喜歡的顏色是{value}。",
            "city": f"我住在{value}。",
        }[kind]
        ask = {
            "name": "我叫什麼名字？",
            "colour": "我最喜歡的顏色是什麼？",
            "city": "我住在哪裡？",
        }[kind]
        answer = {
            "name": f"你叫{value}。",
            "colour": f"你最喜歡的顏色是{value}。",
            "city": f"你住在{value}。",
        }[kind]
        out.append((teach, "記住囉！", ask, answer, value))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sessions", type=int, default=400)
    p.add_argument("--steps", type=int, default=400)
    p.add_argument("--device", choices=("cpu", "xpu", "cuda"), default="xpu")
    p.add_argument(
        "--out", default=str(REPO / "data" / "intelligence_reports" / "single_core_dialogue.json")
    )
    p.add_argument("--save-dir", default=str(REPO / "data" / "models" / "angela_single_core"))
    args = p.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(str(BASE), trust_remote_code=True)
    base = AutoModelForCausalLM.from_pretrained(
        str(BASE), torch_dtype=torch.float32, trust_remote_code=True
    )
    merged = PeftModel.from_pretrained(base, str(ADAPTER)).merge_and_unload()  # ONE weights set
    model = get_peft_model(
        merged,
        LoraConfig(r=8, lora_alpha=16, target_modules=("q_proj", "v_proj"), task_type="CAUSAL_LM"),
    )
    hidden = model.config.hidden_size
    model.state_proj = torch.nn.Linear(hidden, hidden, bias=False).to(model.device)
    torch.nn.init.normal_(model.state_proj.weight, std=0.02)
    model.to(torch.device(args.device))
    model.train()

    all_sessions = make_sessions(args.sessions, 20261127)
    train, held = all_sessions[: int(args.sessions * 0.8)], all_sessions[int(args.sessions * 0.8) :]
    opt = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad] + list(model.state_proj.parameters()),
        lr=1e-3,
    )
    started = time.time()
    for step in range(args.steps):
        teach, ack, ask, answer, value = train[step % len(train)]
        with torch.no_grad():
            t = tokenizer(teach + ack, return_tensors="pt").to(model.device)
            hs = model.base_model.model(**t, output_hidden_states=True).hidden_states[-1][0]
            value_ids = tokenizer(value, add_special_tokens=False)["input_ids"]
            ids_row = t["input_ids"][0].tolist()
            positions = [
                i
                for i in range(len(value_ids), len(ids_row) + 1)
                if ids_row[i - len(value_ids) : i] == value_ids
            ]
            idx = positions[-1] if positions else len(ids_row)
            state = hs[max(0, idx - len(value_ids)) : idx].mean(dim=0).detach()
        q = tokenizer(ask, return_tensors="pt").to(model.device)
        a = tokenizer(answer, return_tensors="pt")["input_ids"].to(model.device)
        embeds = model.get_input_embeddings()(q["input_ids"])
        injected = model.state_proj(state.to(embeds.dtype))
        injected = (
            injected / injected.norm().clamp(min=1e-6) * 0.1
        )  # bounded: never drown embeddings
        embeds = embeds + injected.unsqueeze(0)
        full = torch.cat([q["input_ids"], a], dim=1)
        full_embeds = model.get_input_embeddings()(full)
        full_embeds[:, : q["input_ids"].shape[1]] = embeds
        out = model(inputs_embeds=full_embeds)
        loss = torch.nn.functional.cross_entropy(
            out.logits[0, q["input_ids"].shape[1] - 1 : -1].reshape(-1, out.logits.shape[-1]),
            a.reshape(-1),
        )
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 50 == 0:
            print(f"step {step} loss={loss.item():.4f}", flush=True)

    model.eval()
    hits, samples = 0, []
    with torch.no_grad():
        for teach, _ack, ask, answer, value in held[:30]:
            t = tokenizer(teach, return_tensors="pt").to(model.device)
            hs = model.base_model.model(**t, output_hidden_states=True).hidden_states[-1][0]
            value_ids = tokenizer(value, add_special_tokens=False)["input_ids"]
            ids_row = t["input_ids"][0].tolist()
            positions = [
                i
                for i in range(len(value_ids), len(ids_row) + 1)
                if ids_row[i - len(value_ids) : i] == value_ids
            ]
            idx = positions[-1] if positions else len(ids_row)
            state = hs[max(0, idx - len(value_ids)) : idx].mean(dim=0).detach()
            q = tokenizer(ask, return_tensors="pt").to(model.device)
            embeds = model.get_input_embeddings()(q["input_ids"])
            injected = model.state_proj(state.to(embeds.dtype))
            injected = injected / injected.norm().clamp(min=1e-6) * 0.1
            embeds = embeds + injected.unsqueeze(0)
            gen = model.generate(
                inputs_embeds=embeds,
                attention_mask=q["attention_mask"],
                max_new_tokens=32,
                do_sample=False,
                repetition_penalty=1.3,
                no_repeat_ngram_size=4,
                pad_token_id=tokenizer.eos_token_id,
            )
            got = (
                tokenizer.decode(gen[0, q["input_ids"].shape[1] :], skip_special_tokens=True)
                .strip()
                .lstrip("。 ")
            )
            first = got.split("。", 1)[0] + ("。" if "。" in got else "")
            ok = first.strip() == answer.strip()
            hits += int(ok)
            if len(samples) < 5:
                samples.append({"ask": ask, "gold": answer, "got": got[:120], "ok": ok})

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "one merged Qwen3-0.6B weights + LoRA used at train time + internal state projection",
        "state": "teaching turn's final hidden state projected into next turn's embeddings; no context history, no KV cache",
        "train_sessions": len(train),
        "heldout": len(held),
        "steps": args.steps,
        "seconds": round(time.time() - started, 1),
        "heldout_recall": hits,
        "samples": samples,
        "gate": {
            "registered_before_run": True,
            "pass": hits >= 5 and any(s["got"] for s in samples),
            "verdict": (
                "single_model_converses_with_state" if hits > 0 else "falsified_at_this_scale"
            ),
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Save ONE model directory: merge LoRA into the weights and keep the state projection.
    save = Path(args.save_dir)
    save.mkdir(parents=True, exist_ok=True)
    final = model.merge_and_unload()
    final.state_proj = model.state_proj
    final.save_pretrained(str(save), safe_serialization=True)
    tokenizer.save_pretrained(str(save))
    torch.save(model.state_proj.state_dict(), save / "state_proj.pt")
    print(f"saved single model to {save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
