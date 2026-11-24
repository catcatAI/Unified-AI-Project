#!/usr/bin/env python3
"""Train TokenSNN as a classifier for routing (optimized)."""

import json
import random
import sys
import time
from pathlib import Path

REPO = Path("/home/cxuo/文件/GitHub/Unified-AI-Project")
sys.path.insert(0, str(REPO / "apps/backend/src"))

import torch
import torch.nn as nn

from ai.ed3n.token_snn import TokenSNN, CharVocab, TokenConfig

LABELS = ["math", "logic", "knowledge", "reasoning", "neural_bridge", "none"]
LABEL_TO_IDX = {l: i for i, l in enumerate(LABELS)}

TRAIN = REPO / "apps/backend/data/processed/core_train_cls2.jsonl"
VAL = REPO / "apps/backend/data/processed/core_val_cls2.jsonl"
OUT_CKPT = REPO / "data/checkpoints/tln_phase12.pt"
OUT_REPORT = REPO / "data/intelligence_reports/tln_phase12.json"


def load_data(path, max_samples=20000):
    pairs = []
    with open(path) as f:
        for i, line in enumerate(f):
            if i >= max_samples:
                break
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            pairs.append((row["input"], LABEL_TO_IDX[row["label"]]))
    return pairs


def main():
    device = "cpu"
    print(f"Device: {device}", flush=True)

    # Build vocab from training data
    texts = []
    with open(TRAIN) as f:
        for i, line in enumerate(f):
            if i >= 10000:
                break
            row = json.loads(line.strip())
            texts.append(row["input"])
    vocab = CharVocab.build(texts, min_count=1, max_vocab=128)
    print(f"Vocab size: {len(vocab.itos)}", flush=True)

    cfg = TokenConfig(
        arch="attention",
        d_emb=64,
        d_hidden=128,
        layers=2,
        n_heads=4,
        max_len=64,
        num_classes=6,
        use_container=False,
        mem_norm=True,
    )

    model = TokenSNN(vocab, cfg, device=device)
    model.net.train()

    train_pairs = load_data(TRAIN, max_samples=10000)
    val_pairs = load_data(VAL, max_samples=1000)
    print(f"Train: {len(train_pairs)}, Val: {len(val_pairs)}", flush=True)

    # Pre-encode all data
    print("Pre-encoding data...", flush=True)
    train_ids = []
    train_labels = []
    for prompt, label in train_pairs:
        ids = vocab.encode(prompt)[:64]
        train_ids.append(ids)
        train_labels.append(label)

    val_ids = []
    val_labels = []
    for prompt, label in val_pairs:
        ids = vocab.encode(prompt)[:64]
        val_ids.append(ids)
        val_labels.append(label)
    print("Encoding done.", flush=True)

    optimizer = torch.optim.Adam(model.net.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    n_epochs = 3
    batch_size = 64

    for epoch in range(n_epochs):
        random.shuffle(list(range(len(train_ids))))  # shuffle indices
        order = list(range(len(train_ids)))
        random.shuffle(order)

        total_loss = 0
        correct = 0
        total = 0
        n_batches = 0

        for i in range(0, len(order), batch_size):
            batch_idx = order[i : i + batch_size]
            ids_list = [train_ids[j] for j in batch_idx]
            labels_list = [train_labels[j] for j in batch_idx]

            max_len = max(len(ids) for ids in ids_list)
            ids_t = torch.full(
                (len(ids_list), max_len), vocab.pad_id, dtype=torch.long, device=device
            )
            for j, ids in enumerate(ids_list):
                ids_t[j, : len(ids)] = torch.tensor(ids, dtype=torch.long, device=device)
            labels_t = torch.tensor(labels_list, dtype=torch.long, device=device)

            logits = model.classify(ids_t)
            loss = criterion(logits, labels_t)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            preds = logits.argmax(dim=1)
            correct += (preds == labels_t).sum().item()
            total += len(labels_t)
            n_batches += 1

        acc = correct / total
        avg_loss = total_loss / n_batches
        print(f"Epoch {epoch + 1}: loss={avg_loss:.4f}, acc={acc:.4f}", flush=True)

    # Evaluate on val
    model.net.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for i in range(0, len(val_ids), batch_size):
            batch_ids = val_ids[i : i + batch_size]
            batch_labels = val_labels[i : i + batch_size]

            max_len = max(len(ids) for ids in batch_ids)
            ids_t = torch.full(
                (len(batch_ids), max_len), vocab.pad_id, dtype=torch.long, device=device
            )
            for j, ids in enumerate(batch_ids):
                ids_t[j, : len(ids)] = torch.tensor(ids, dtype=torch.long, device=device)
            labels_t = torch.tensor(batch_labels, dtype=torch.long, device=device)

            logits = model.classify(ids_t)
            preds = logits.argmax(dim=1)
            correct += (preds == labels_t).sum().item()
            total += len(batch_labels)

    val_acc = correct / total
    print(f"Val accuracy: {val_acc:.4f}", flush=True)

    # Test on some examples
    print("\nTest predictions:")
    test_qs = ["What is 2 + 3?", "What is the capital of France?", "Hello", "Is 5 > 3?"]
    model.net.eval()
    with torch.no_grad():
        for q in test_qs:
            ids = vocab.encode(q)[:128]
            ids_t = torch.tensor([ids], dtype=torch.long, device=device)
            logits = model.classify(ids_t)
            pred = LABELS[logits.argmax(dim=1).item()]
            print(f"  {q} -> {pred}")

    # Save
    model.save(str(OUT_CKPT))
    print(f"Saved to {OUT_CKPT}", flush=True)

    report = {
        "n_classes": 5,
        "labels": LABELS,
        "train_acc": acc,
        "val_acc": val_acc,
        "n_train": len(train_pairs),
        "n_val": len(val_pairs),
    }
    import json as j

    with open(OUT_REPORT, "w") as f:
        j.dump(report, f, indent=2)
    print(f"Report saved to {OUT_REPORT}", flush=True)


if __name__ == "__main__":
    main()
