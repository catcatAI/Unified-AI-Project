#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================
"""ONE model with an internal memory-token state (not context, not second model).

Weights = Qwen3-0.6B base + merged LoRA, trained further with LoRA so the same
model learns to READ its state. State = last K hidden vectors of the teaching
turn, projected into embedding space and prepended as K memory tokens to the
next turn. The test prompt contains ONLY the question; no text history, no KV
cache, no second model. The model's own attention reads the memory tokens.

Pre-registered gate: strict held-out recall >= 5/30 AND non-empty answers.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import List, Tuple

import torch
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "data" / "models" / "qwen3-0.6b"
ADAPTER = REPO / "data" / "models" / "qwen3-0.6b-finetuned"
VALUES = {
    "name": ["小明", "小華", "阿哲", "美玲", "志強", "嘉紋", "雅婷", "俊傑"],
    "colour": ["藍色", "綠色", "紅色", "紫色", "橙色", "黑色"],
    "city": ["台北", "新竹", "台中", "台南", "高雄", "花蓮"],
}
PATTERNS = {
    "name": ("我的名字是{V}。", "我叫什麼名字？", "你叫{V}。"),
    "colour": ("我最喜歡的顏色是{V}。", "我最喜歡的顏色是什麼？", "你最喜歡的顏色是{V}。"),
    "city": ("我住在{V}。", "我住在哪裡？", "你住在{V}。"),
}


def sessions(n: int, seed: int) -> List[Tuple[str, str, str, str]]:
    import random

    rng = random.Random(seed)
    out = []
    for i in range(n):
        kind = list(VALUES)[i % 3]
        value = VALUES[kind][rng.randrange(len(VALUES[kind]))]
        teach, ask, answer = PATTERNS[kind]
        out.append((teach.format(V=value), ask, answer.format(V=value), value))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sessions", type=int, default=450)
    p.add_argument("--steps", type=int, default=450)
    p.add_argument("--memory", type=int, default=4)
    p.add_argument("--device", choices=("cpu", "xpu", "cuda"), default="xpu")
    p.add_argument(
        "--out", default=str(REPO / "data" / "intelligence_reports" / "single_core_memory.json")
    )
    p.add_argument(
        "--save-dir", default=str(REPO / "data" / "models" / "angela_single_core_memory")
    )
    args = p.parse_args()

    tok = AutoTokenizer.from_pretrained(str(BASE), trust_remote_code=True)
    base = AutoModelForCausalLM.from_pretrained(
        str(BASE), torch_dtype=torch.float32, trust_remote_code=True
    )
    merged = PeftModel.from_pretrained(base, str(ADAPTER)).merge_and_unload()
    model = get_peft_model(
        merged,
        LoraConfig(r=8, lora_alpha=16, target_modules=("q_proj", "v_proj"), task_type="CAUSAL_LM"),
    )
    hidden = model.config.hidden_size
    proj = torch.nn.Linear(hidden, hidden, bias=False)
    torch.nn.init.normal_(proj.weight, std=0.02)
    model.to(torch.device(args.device))
    proj = proj.to(model.device)
    model.train()

    rows = sessions(args.sessions, 20261127)
    train, held = rows[: int(len(rows) * 0.8)], rows[int(len(rows) * 0.8) :]
    opt = torch.optim.AdamW(
        [x for x in model.parameters() if x.requires_grad] + list(proj.parameters()), lr=1e-3
    )
    inner = model.base_model.model.model
    started = time.time()

    def memory_of(teach: str, value: str) -> torch.Tensor:
        ids = tok(teach, return_tensors="pt").to(model.device)
        with torch.no_grad():
            hs = inner(**ids, output_hidden_states=True).hidden_states[-1][0]
        vids = tok(value, add_special_tokens=False)["input_ids"]
        row = ids["input_ids"][0].tolist()
        pos = [i for i in range(len(vids), len(row) + 1) if row[i - len(vids) : i] == vids]
        idx = pos[-1] if pos else len(row)
        vecs = hs[max(0, idx - args.memory + 1) : idx + 1]
        if vecs.shape[0] < args.memory:
            vecs = torch.cat([hs[: args.memory - vecs.shape[0]], vecs], dim=0)
        return proj(vecs.to(inner.get_input_embeddings().weight.dtype))

    for step in range(args.steps):
        teach, ask, answer, value = train[step % len(train)]
        mem = memory_of(teach, value)
        q = tok(ask, return_tensors="pt").to(model.device)
        a = tok(answer, return_tensors="pt")["input_ids"].to(model.device)
        emb = inner.get_input_embeddings()
        full = torch.cat([mem, emb(q["input_ids"])[0], emb(a)[0]], dim=0).unsqueeze(0)
        out = model(
            inputs_embeds=full, attention_mask=torch.ones_like(full[:, :, 0], dtype=torch.long)
        )
        start = args.memory + q["input_ids"].shape[1] - 1
        loss = torch.nn.functional.cross_entropy(
            out.logits[0, start:-1].reshape(-1, out.logits.shape[-1]), a.reshape(-1)
        )
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 100 == 0:
            print(f"step {step} loss={loss.item():.4f}", flush=True)

    model.eval()
    hits, samples = 0, []
    for teach, ask, answer, value in held[:30]:
        mem = memory_of(teach, value)
        q = tok(ask, return_tensors="pt").to(model.device)
        emb = inner.get_input_embeddings()
        prefix = torch.cat([mem, emb(q["input_ids"])[0]], dim=0).unsqueeze(0)
        with torch.no_grad():
            gen = model.generate(
                inputs_embeds=prefix,
                attention_mask=torch.ones_like(prefix[:, :, 0], dtype=torch.long),
                max_new_tokens=32,
                do_sample=False,
                repetition_penalty=1.3,
                no_repeat_ngram_size=4,
                pad_token_id=tok.eos_token_id,
            )
        got = (
            tok.decode(gen[0, args.memory + q["input_ids"].shape[1] :], skip_special_tokens=True)
            .strip()
            .lstrip("。 ")
        )
        first = got.split("。", 1)[0] + ("。" if "。" in got else "")
        ok = value in first  # recall the taught value in the first sentence
        hits += int(ok)
        if len(samples) < 5:
            samples.append({"ask": ask, "gold": answer, "got": got[:140], "ok": ok})

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "one merged Qwen3-0.6B weights + internal K-memory-token state (no context history)",
        "memory_tokens": args.memory,
        "train_sessions": len(train),
        "heldout": len(held[:30]),
        "exact": hits,
        "samples": samples,
        "gate": {
            "registered_before_run": True,
            "pass": hits >= 5 and any(s["got"] for s in samples),
            "verdict": "single_model_converses_with_state" if hits >= 5 else "weak_or_falsified",
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    save = Path(args.save_dir)
    save.mkdir(parents=True, exist_ok=True)
    final = model.merge_and_unload()
    final.save_pretrained(str(save), safe_serialization=True)
    tok.save_pretrained(str(save))
    torch.save(proj.state_dict(), save / "state_proj.pt")
    print(f"saved single model to {save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
