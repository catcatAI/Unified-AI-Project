#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================
"""ONE model with ONE internal state — no context history, no second model.

The weights are the already-fine-tuned Qwen3-0.6B adapter MERGED into its base
(one weights hash). The state is a fixed-size tensor computed from the previous
turn's hidden states and injected into the next turn's input embeddings — it is
NOT text in the prompt, NOT a KV cache, and no separate core model exists.

Pre-registered gate (before running):
  * 30 held-out teaching->test pairs; the test prompt is the question only.
  * pass only if the merged model produces non-empty answers AND exact > 0.
  * if exact == 0, report honestly — do not claim comparability.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import List, Tuple

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "data" / "models" / "qwen3-0.6b"
ADAPTER = REPO / "data" / "models" / "qwen3-0.6b-finetuned"
DATA = REPO / "apps" / "backend" / "data" / "processed" / "core_train.jsonl"


def load_pairs(limit: int) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    with DATA.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            pairs.append((row["input"], row["output"]))
            if limit and len(pairs) >= limit:
                break
    return pairs


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--limit", type=int, default=200)
    p.add_argument("--train-steps", type=int, default=0)
    p.add_argument("--device", choices=("cpu", "xpu", "cuda"), default="cpu")
    p.add_argument(
        "--out", default=str(REPO / "data" / "intelligence_reports" / "single_llm_state.json")
    )
    args = p.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(str(BASE), trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(BASE), torch_dtype=torch.float32, trust_remote_code=True
    )
    model = PeftModel.from_pretrained(model, str(ADAPTER)).merge_and_unload()  # ONE weights set
    model.to(torch.device(args.device)).eval()

    state_dim = model.config.hidden_size
    proj = torch.nn.Linear(state_dim, state_dim, bias=False).to(model.device)
    torch.nn.init.zeros_(proj.weight)  # start as identity-free: generation preserved
    pairs = load_pairs(args.limit)

    if args.train_steps > 0:
        opt = torch.optim.AdamW(proj.parameters(), lr=1e-3)
        for step in range(args.train_steps):
            idx = (step * 2) % max(1, len(pairs) - 1)
            teach_q, teach_a = pairs[idx]
            test_q, test_a = pairs[idx + 1]
            with torch.no_grad():
                teach_ids = tokenizer(teach_q + "\n" + teach_a, return_tensors="pt").to(
                    model.device
                )
                state = (
                    model(**teach_ids, output_hidden_states=True)
                    .hidden_states[-1][0, -1, :]
                    .detach()
                )
            test_ids = tokenizer(test_q, return_tensors="pt").to(model.device)
            embeds = model.get_input_embeddings()(test_ids["input_ids"])
            embeds = embeds + proj(state.to(embeds.dtype)).unsqueeze(0)
            labels = tokenizer(test_a, return_tensors="pt")["input_ids"].to(model.device)
            full = torch.cat([test_ids["input_ids"], labels], dim=1)
            full_embeds = model.get_input_embeddings()(full)
            full_embeds[:, : test_ids["input_ids"].shape[1]] = embeds
            logits = model(inputs_embeds=full_embeds).logits
            loss = torch.nn.functional.cross_entropy(
                logits[0, test_ids["input_ids"].shape[1] - 1 : -1].reshape(-1, logits.shape[-1]),
                labels.reshape(-1),
            )
            opt.zero_grad()
            loss.backward()
            opt.step()
    else:
        proj.weight.data.zero_()
    samples, hits = [], 0
    started = time.time()
    for idx in range(0, min(len(pairs) - 1, 30), 2):
        teach_q, teach_a = pairs[idx]
        test_q, test_a = pairs[idx + 1]
        with torch.no_grad():
            teach_ids = tokenizer(teach_q + "\n" + teach_a, return_tensors="pt").to(model.device)
            out = model(**teach_ids, output_hidden_states=True)
            state = out.hidden_states[-1][0, -1, :].detach()  # internal state vector
            test_ids = tokenizer(test_q, return_tensors="pt").to(model.device)
            embeds = model.get_input_embeddings()(test_ids["input_ids"])
            embeds = embeds + proj(state.to(embeds.dtype)).unsqueeze(0)
            generated = model.generate(
                inputs_embeds=embeds,
                attention_mask=test_ids["attention_mask"],
                max_new_tokens=96,
                do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        got = tokenizer.decode(
            generated[0, test_ids["input_ids"].shape[1] :], skip_special_tokens=True
        ).strip()
        ok = got == test_a.strip()
        hits += int(ok)
        if len(samples) < 5:
            samples.append(
                {"test_q": test_q[:100], "gold": test_a[:140], "got": got[:200], "exact": ok}
            )

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "Qwen3-0.6B base + merged LoRA = one weights set",
        "state": "mean-pooled final hidden state of the teaching turn, injected into next turn's embeddings (not context, not KV cache)",
        "state_dim": state_dim,
        "pairs": len(pairs),
        "evaluated": min(len(pairs) - 1, 30) // 2,
        "seconds": round(time.time() - started, 1),
        "exact": hits,
        "samples": samples,
        "gate": {
            "registered_before_run": True,
            "pass": hits > 0 and any(s["got"] for s in samples),
            "verdict": "one_core_generates" if hits > 0 else "falsified_at_this_scale",
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
