#!/usr/bin/env python3
"""Two-layer model: classify then generate.

Layer 1: Classify question type (math/logic/knowledge/reasoning/none)
Layer 2: Generate answer conditioned on question type

The idea: classification provides a "hint" that helps generation.
"""
import json
import random
import sys
from pathlib import Path

REPO = Path("/home/cxuo/文件/GitHub/Unified-AI-Project")
sys.path.insert(0, str(REPO / "apps/backend/src"))

import torch
import torch.nn as nn

from ai.ed3n.token_snn import TokenSNN, CharVocab, TokenConfig

LABELS = ["math", "logic", "knowledge", "reasoning", "none"]
LABEL_TO_IDX = {l: i for i, l in enumerate(LABELS)}

TRAIN = REPO / "apps/backend/data/processed/core_train.jsonl"
OUT_CKPT = REPO / "data/checkpoints/tln_phase13.pt"
OUT_REPORT = REPO / "data/intelligence_reports/tln_phase13.json"

# Load data
def load_data(path, max_samples=5000):
    pairs = []
    with open(path) as f:
        for i, line in enumerate(f):
            if i >= max_samples:
                break
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            prompt = row.get("input", "").strip()
            answer = row.get("output", "").strip()
            if prompt and answer:
                # Simple routing label
                p = prompt.lower()
                if any(c.isdigit() for c in p) and any(op in p for op in ['+', '-', '*', '/']):
                    label = "math"
                elif any(kw in p for kw in ['capital', 'population', 'president', 'country']):
                    label = "knowledge"
                elif any(kw in p for kw in ['taller', 'shorter', 'bigger', 'why', 'because']):
                    label = "reasoning"
                else:
                    label = "none"
                pairs.append((prompt, answer, LABEL_TO_IDX[label]))
    return pairs

def main():
    device = "cpu"
    print(f"Device: {device}", flush=True)

    # Build vocab
    texts = []
    with open(TRAIN) as f:
        for i, line in enumerate(f):
            if i >= 5000:
                break
            row = json.loads(line.strip())
            texts.append(row["input"])
    vocab = CharVocab.build(texts, min_count=1, max_vocab=128)
    print(f"Vocab size: {len(vocab.itos)}", flush=True)

    # Create model with both classifier and generator
    cfg = TokenConfig(
        arch="attention",
        d_emb=64,
        d_hidden=128,
        layers=2,
        n_heads=4,
        max_len=64,
        num_classes=5,
        use_container=False,
        mem_norm=True,
    )

    model = TokenSNN(vocab, cfg, device=device)
    model.net.train()

    # Add class embedding to model (for conditioning generation)
    # We'll use the classifier output as additional input to the generator
    class_emb = nn.Embedding(5, 128)  # 5 classes -> 128-dim embedding
    model.net.class_emb = class_emb

    # Training data
    pairs = load_data(TRAIN, max_samples=5000)
    print(f"Train: {len(pairs)}", flush=True)

    # Training
    optimizer = torch.optim.Adam(list(model.net.parameters()) + list(class_emb.parameters()), lr=1e-3)
    criterion_cls = nn.CrossEntropyLoss()
    criterion_gen = nn.CrossEntropyLoss()

    n_epochs = 3
    batch_size = 32

    for epoch in range(n_epochs):
        random.shuffle(pairs)
        total_loss = 0
        cls_correct = 0
        gen_correct = 0
        total = 0
        n_batches = 0

        for i in range(0, len(pairs), batch_size):
            batch = pairs[i:i + batch_size]
            if len(batch) < 2:
                continue

            # Prepare batch
            prompts = [p[0] for p in batch]
            answers = [p[1] for p in batch]
            labels = [p[2] for p in batch]

            # Encode prompts
            prompt_ids_list = [vocab.encode(p)[:32] for p in prompts]
            max_plen = max(len(ids) for ids in prompt_ids_list)
            prompt_ids = torch.full((len(batch), max_plen), vocab.pad_id, dtype=torch.long, device=device)
            for j, ids in enumerate(prompt_ids_list):
                prompt_ids[j, :len(ids)] = torch.tensor(ids, dtype=torch.long, device=device)

            # Encode answers
            answer_ids_list = [vocab.encode(a)[:32] for a in answers]
            max_alen = max(len(ids) for ids in answer_ids_list)
            answer_ids = torch.full((len(batch), max_alen), vocab.pad_id, dtype=torch.long, device=device)
            for j, ids in enumerate(answer_ids_list):
                answer_ids[j, :len(ids)] = torch.tensor(ids, dtype=torch.long, device=device)

            # Layer 1: Classify
            cls_logits = model.classify(prompt_ids)  # (batch, 5)
            cls_loss = criterion_cls(cls_logits, torch.tensor(labels, dtype=torch.long, device=device))

            # Get predicted class (use ground truth during training for stability)
            pred_class = torch.tensor(labels, dtype=torch.long, device=device)
            class_context = class_emb(pred_class)  # (batch, 128)

            # Layer 2: Generate answer conditioned on class
            # Prepend class embedding to input
            # Encode prompt + answer as single sequence
            full_ids_list = []
            for j in range(len(batch)):
                full = vocab.encode(prompts[j])[:32] + [vocab.stoi.get(' ', vocab.pad_id)] + vocab.encode(answers[j])[:32]
                full_ids_list.append(full)

            max_flen = max(len(ids) for ids in full_ids_list)
            full_ids = torch.full((len(batch), max_flen), vocab.pad_id, dtype=torch.long, device=device)
            for j, ids in enumerate(full_ids_list):
                full_ids[j, :len(ids)] = torch.tensor(ids, dtype=torch.long, device=device)

            # Forward pass
            hidden = model.net.encode(full_ids)  # (batch, seq, d_model)
            # Add class context to all positions
            hidden = hidden + class_context.unsqueeze(1)  # broadcast
            logits = model.net.head(hidden)  # (batch, seq, vocab)

            # Compute CE on answer positions only
            # Find answer start (after prompt + space)
            gen_loss = torch.tensor(0.0, device=device)
            n_gen = 0
            for j in range(len(batch)):
                prompt_len = len(vocab.encode(prompts[j])[:32]) + 1  # +1 for space
                # CE on answer positions
                for t in range(prompt_len, min(len(full_ids_list[j]) - 1, max_flen - 1)):
                    target = full_ids[j, t + 1]
                    if target == vocab.pad_id:
                        break
                    gen_loss = gen_loss + criterion_gen(logits[j, t].unsqueeze(0), target.unsqueeze(0))
                    n_gen += 1

            if n_gen > 0:
                gen_loss = gen_loss / n_gen

            # Total loss
            loss = cls_loss + 0.5 * gen_loss

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            cls_preds = cls_logits.argmax(dim=1)
            cls_correct += (cls_preds == torch.tensor(labels, dtype=torch.long, device=device)).sum().item()
            total += len(batch)
            n_batches += 1

        cls_acc = cls_correct / total
        avg_loss = total_loss / n_batches
        print(f"Epoch {epoch + 1}: loss={avg_loss:.4f}, cls_acc={cls_acc:.4f}", flush=True)

    # Test
    print("\nTest predictions:")
    model.net.eval()
    class_emb.eval()
    with torch.no_grad():
        for q in ["What is 2 + 3?", "What is the capital of France?", "Hello", "Tell me a joke"]:
            ids = vocab.encode(q)[:32]
            ids_t = torch.tensor([ids], dtype=torch.long, device=device)
            cls_logits = model.classify(ids_t)
            cls_pred = LABELS[cls_logits.argmax(dim=1).item()]
            print(f"  {q} -> class={cls_pred}")

    # Save
    model.save(str(OUT_CKPT))
    print(f"Saved to {OUT_CKPT}", flush=True)

    report = {
        "n_epochs": n_epochs,
        "final_loss": avg_loss,
        "cls_acc": cls_acc,
    }
    import json as j
    with open(OUT_REPORT, "w") as f:
        j.dump(report, f, indent=2)
    print(f"Report saved to {OUT_REPORT}", flush=True)


if __name__ == "__main__":
    main()