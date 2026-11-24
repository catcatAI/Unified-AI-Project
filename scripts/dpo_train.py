#!/usr/bin/env python3
"""Simplified DPO (Direct Preference Optimization) training.

Uses rule-based rewards: correct answer = chosen, incorrect = rejected.
Trains the model to prefer correct answers over incorrect ones.
"""
import json
import math
import random
from pathlib import Path

import torch
import torch.nn.functional as F

REPO = Path("/home/cxuo/文件/GitHub/Unified-AI-Project")
CKPT = REPO / "data/checkpoints/tln_phase3.pt"
TRAIN = REPO / "apps/backend/data/processed/core_train.jsonl"
OUT_CKPT = REPO / "data/checkpoints/tln_phase8.pt"
OUT_REPORT = REPO / "data/intelligence_reports/tln_phase8.json"

# Add src to path
import sys
sys.path.insert(0, str(REPO / "apps/backend/src"))
from ai.ed3n.token_snn import TokenSNN, TokenVocab, TokenConfig


def load_model(ckpt_path, device):
    import torch
    model = TokenSNN.load(str(ckpt_path), map_location=device, device=device)
    model.net.eval()
    return model


def compute_log_prob(model, ids, no_grad=False):
    """Compute log probability of a sequence under the model."""
    torch = __import__("torch")
    ctx = torch.no_grad() if no_grad else torch.enable_grad()
    with ctx:
        logits = model.net.forward(ids)  # (batch, seq, vocab)
    # Shift: predict token t+1 from position t
    log_probs = F.log_softmax(logits[:, :-1, :], dim=-1)  # (batch, seq-1, vocab)
    targets = ids[:, 1:]  # (batch, seq-1)
    # Gather log prob of target tokens
    target_log_probs = log_probs.gather(2, targets.unsqueeze(-1)).squeeze(-1)  # (batch, seq-1)
    # Sum over sequence
    return target_log_probs.sum(dim=1)  # (batch,)


def generate_preference_pairs(model, n_pairs=500):
    """Generate preference pairs from model's predictions.

    For each training question, generate an answer from the model.
    If the model's answer is wrong, use (correct, model_wrong) as (chosen, rejected).
    """
    pairs = []
    rows = []
    with open(TRAIN) as f:
        for line in f:
            row = json.loads(line.strip())
            rows.append(row)

    random.seed(42)
    sampled = random.sample(rows, min(n_pairs, len(rows)))

    for row in sampled:
        prompt = row["input"]
        correct_answer = row["output"]
        # Generate model's answer
        try:
            model_answer = model.generate(prompt, max_new=64)
        except Exception:
            continue
        # If model's answer differs from correct, create preference pair
        if model_answer.strip() != correct_answer.strip():
            pairs.append({
                "prompt": prompt,
                "chosen": correct_answer,
                "rejected": model_answer,
            })

    return pairs


def dpo_loss(policy_logp_chosen, policy_logp_rejected,
             ref_logp_chosen, ref_logp_rejected, beta=0.1):
    """DPO loss."""
    torch = __import__("torch")
    pi_ratio = policy_logp_chosen - policy_logp_rejected
    ref_ratio = ref_logp_chosen - ref_logp_rejected
    logits = beta * (pi_ratio - ref_ratio)
    loss = -F.logsigmoid(logits).mean()
    return loss


def main():
    device = "cpu"  # Use CPU for DPO (simpler)
    print(f"Device: {device}")

    # Load reference model (frozen)
    ref_model = load_model(CKPT, device)
    ref_model.net.eval()
    for p in ref_model.net.parameters():
        p.requires_grad = False

    # Policy model (trainable copy)
    policy_model = load_model(CKPT, device)
    policy_model.net.train()

    # Generate preference pairs
    print("Generating preference pairs...")
    pairs = generate_preference_pairs(policy_model, n_pairs=200)
    print(f"Generated {len(pairs)} preference pairs")

    if len(pairs) == 0:
        print("No preference pairs generated. Exiting.")
        return

    # Training
    optimizer = torch.optim.Adam(policy_model.net.parameters(), lr=1e-5)
    beta = 0.1
    n_epochs = 3
    batch_size = 4

    for epoch in range(n_epochs):
        random.shuffle(pairs)
        total_loss = 0
        n_batches = 0
        for i in range(0, len(pairs), batch_size):
            batch = pairs[i:i + batch_size]
            if len(batch) < 2:
                continue

            # Encode chosen and rejected
            chosen_ids_list = []
            rejected_ids_list = []
            for p in batch:
                # Encode prompt + chosen
                ids_c, _ = policy_model.encode_pair(p["prompt"], p["chosen"])
                ids_r, _ = policy_model.encode_pair(p["prompt"], p["rejected"])
                chosen_ids_list.append(ids_c)
                rejected_ids_list.append(ids_r)

            # Pad and compute log probs
            # (Simplified: process one at a time)
            policy_chosen_lps = []
            policy_rejected_lps = []
            ref_chosen_lps = []
            ref_rejected_lps = []

            for p in batch:
                ids_c, _ = policy_model.encode_pair(p["prompt"], p["chosen"])
                ids_r, _ = policy_model.encode_pair(p["prompt"], p["rejected"])

                ids_c_t = torch.tensor([ids_c], dtype=torch.long, device=device)
                ids_r_t = torch.tensor([ids_r], dtype=torch.long, device=device)

                # Policy log probs (with grad)
                policy_model.net.train()
                plp_c = compute_log_prob(policy_model, ids_c_t, no_grad=False)
                plp_r = compute_log_prob(policy_model, ids_r_t, no_grad=False)

                # Reference log probs (no grad)
                rlp_c = compute_log_prob(ref_model, ids_c_t, no_grad=True)
                rlp_r = compute_log_prob(ref_model, ids_r_t, no_grad=True)

                policy_chosen_lps.append(plp_c)
                policy_rejected_lps.append(plp_r)
                ref_chosen_lps.append(rlp_c)
                ref_rejected_lps.append(rlp_r)

            policy_chosen = torch.cat(policy_chosen_lps)
            policy_rejected = torch.cat(policy_rejected_lps)
            ref_chosen = torch.cat(ref_chosen_lps)
            ref_rejected = torch.cat(ref_rejected_lps)

            loss = dpo_loss(policy_chosen, policy_rejected, ref_chosen, ref_rejected, beta)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            n_batches += 1

        avg_loss = total_loss / max(n_batches, 1)
        print(f"Epoch {epoch + 1}: loss={avg_loss:.4f}, n_batches={n_batches}")

    # Save
    policy_model.save(str(OUT_CKPT))
    print(f"Saved to {OUT_CKPT}")

    # Report
    report = {
        "n_pairs": len(pairs),
        "n_epochs": n_epochs,
        "final_loss": avg_loss,
    }
    with open(OUT_REPORT, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to {OUT_REPORT}")


if __name__ == "__main__":
    main()