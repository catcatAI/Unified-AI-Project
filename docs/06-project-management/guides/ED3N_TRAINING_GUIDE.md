# ED3N Training Pipeline Guide

## Overview

ED3N (External Dictionary Decoupled Neural Network) is a hybrid reflex-associative network. It learns by:

1. **Dictionary Expansion** — growing entries for new concepts/tokens
2. **Hebbian Network Training** — strengthening connections between co-occurring input/output keys
3. **Reflex Pattern Generation** — creating exact-match patterns from training data

## Training Results Summary

| Metric | Value |
|--------|-------|
| Training data | 12,200 samples (10K arithmetic + 2K arithmetic test + 200 logic) |
| Network accuracy | ~77.7% (pre-PEMDAS). Latest native benchmark (`benchmark_ed3n_garden.py`, 2026-07-16) = **20/20 (100%)** across math/knowledge/reasoning/chain — but all 20 are answered by the *deterministic* engines (MathVerifier / knowledge_base / symbolic_reasoner / CoreNetwork transitive closure), **not the neural SNN**. Neural-net **net contribution ≈ 35%** (DET-CARRY differential = HYBRID − DET-ONLY, ED3N 35.3% / GARDEN 35.6% — see INTELLIGENCE_ASSESSMENT §4.1.1); the SNN-only score is distorted by OR-short-circuiting and is NOT the neural capability. |
| Seen problem accuracy | 100% (reflex exact match) |
| Dictionary entries | 46 (26 original + 20 math/logic presets) |
| Reflex patterns | 12,063 |
| Training time | ~5-7 minutes |

## Prerequisites

```bash
cd D:\Projects\Unified-AI-Project
python --version  # Requires 3.10+
```

## Data Format

ED3N expects training data as JSON with `input` and `output` fields:

```json
[
  {"input": "178 + 101", "output": "279"},
  {"input": "true OR false", "output": "true"}
]
```

Existing datasets at `apps/backend/data/raw_datasets/`:
- `arithmetic_train_dataset.json` (10K samples)
- `arithmetic_test_dataset.csv` (2K samples)
- `logic_test.json` (200 samples)

## Running Training

### Quick Start

```bash
# Train with default settings
python scripts/train_ed3n.py

# Train with custom parameters
python scripts/train_ed3n.py --epochs 5 --lr 0.05 --data-dir apps/backend/data/raw_datasets
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--epochs` | 3 | Number of training epochs |
| `--lr` | 0.05 | Learning rate (dictionary + network) |
| `--data-dir` | `apps/backend/data/raw_datasets` | Training data directory |
| `--output` | `data/checkpoints/ed3n_full.json` | Output checkpoint path |

### What Happens During Training

```
[1/5] Loading datasets...
[2/5] Initializing ED3N engine...
[3/5] Expanding dictionary + training...
  - Auto-grows dictionary entries for unknown tokens
  - Runs Hebbian training on dictionary layer
  - Runs Hebbian training on core network
[4/5] Generating reflex patterns...
  - Creates exact-match patterns for all training data
[5/5] Saving checkpoint...
```

## Loading and Using a Trained Model

```python
import sys
sys.path.insert(0, "D:\\Projects\\Unified-AI-Project")

from apps.backend.src.ai.ed3n.ed3n_engine import ED3NEngine

# Initialize and load checkpoint
engine = ED3NEngine()
engine.load("data/checkpoints/ed3n_full.json")

# Test
print(engine.process("178 + 101"))      # "279" (reflex exact match)
print(engine.process("你好"))            # "你好！很高兴见到你！" (preset reflex)
print(engine.process("true AND false"))  # "false" (network generalization)
```

> **Inference auto-loads the trained checkpoint.** In production, do NOT construct
> `ED3NEngine()` + manual `load()` — use the shared singleton so the trained
> weights produced by `train_pipeline.py` (`data/checkpoints/ed3n_full.json`) are
> actually loaded:
> ```python
> eng = ED3NEngine.get_shared(load_trained=True)   # loads data/checkpoints/ed3n_full.json if present
> ```
> This closes the train↔inference Save/Load gap: previously inference created
> fresh preset-only instances and orphaned the trained network on disk.

## Evaluation

### Seen Problems (exact matches in training data)

```bash
python -c "
import sys; sys.path.insert(0, 'D:\\Projects\\Unified-AI-Project')
from apps.backend.src.ai.ed3n.ed3n_engine import ED3NEngine
e = ED3NEngine(); e.load('data/checkpoints/ed3n_full.json')
for q in ['178 + 101', '917 * 814', 'true OR false', 'NOT false']:
    print(f'{q:30s} -> {e.process(q)}')
"
```

Expected output:
```
178 + 101                      -> 279
917 * 814                      -> 746438
true OR false                  -> true
NOT false                      -> true
```

### Unseen Problems (network generalization)

```bash
python -c "
import sys; sys.path.insert(0, 'D:\\Projects\\Unified-AI-Project')
from apps.backend.src.ai.ed3n.ed3n_engine import ED3NEngine
e = ED3NEngine(); e.load('data/checkpoints/ed3n_full.json')
for q in ['true AND false', '(false OR true) AND false', '999 + 1']:
    print(f'{q:30s} -> {e.process(q)}')
"
```

## Understanding Results

### Reflex Layer (Exact Match)
- Handles all seen problems with 100% accuracy (reflex exact-match — this is NOT the neural SNN benchmark)
- Pattern matching: `if pattern in normalized_input`
- Includes 30 built-in conversation patterns + trained patterns
- Reflex patterns are persisted in checkpoints

### Network Layer (Hebbian Generalization)
- ~77% key activation accuracy
- Works best when input and output share **token overlap** (logic: true/false/AND/OR/NOT are all in presets)
- Does NOT generalize arithmetic computation — digit patterns are positional, not mathematical
- Network connections are persisted in `_network.json` files

### Dictionary Layer
- 46 preset entries: 26 conversational + 10 digits (0-9) + 5 operators + 5 logic
- All tokens in training data must match an entry for training to work
- Auto-grows entries for unknown tokens during training

## Limitations

1. **No true computation** — ED3N cannot add/subtract/multiply unseen numbers; it only retrieves learned associations
2. **Token dependency** — Input must tokenize to known dictionary entries; novel tokens need auto-growing
3. **Substring reflex matching** — Patterns match by substring; e.g., "1" could accidentally match "100"
4. **No backpropagation** — Uses Hebbian learning, not gradient descent; complex patterns may not converge

## Extending to New Data

1. Prepare data as JSON: `[{"input": "...", "output": "..."}]`
2. Ensure domain-specific tokens exist in the dictionary (or will be auto-grown)
3. Run `python scripts/train_ed3n.py`

### Adding Custom Presets

Edit `apps/backend/src/ai/ed3n/dictionary_layer.py:_build_presets()`:

```python
{
    "key": "your_key",
    "surface_forms": {"zh": "中文", "en": "english"},
    "contexts": [{"context_id": "domain", "type": "custom"}],
    "relations": {},
    "confidence": 1.0,
}
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `0 entries (0 new)` during expansion | All tokens already known | Check if tokens contain non-word characters |
| `0 examples created` | `encode()` returns empty | Add presets for domain tokens |
| `accuracy = 0.0` | No input_keys populated | Use `train_ed3n.py` which preprocesses data |
| Reflex patterns not loading | Checkpoint format mismatch | Ensure save/load include `reflex_patterns` |
| `TrainMetrics not JSON serializable` | Old checkpoint | Re-train with updated save method |

## Files

| File | Purpose |
|------|---------|
| `scripts/train_ed3n.py` | Main training pipeline |
| `data/checkpoints/ed3n_full.json` | Engine checkpoint (dictionary + reflex + settings) |
| `data/checkpoints/trainer_state.json` | Training metrics history |
| `data/checkpoints/network.json` | CoreNetwork connection weights |
| `apps/backend/src/ai/ed3n/ed3n_trainer.py` | ED3N training algorithm |
| `apps/backend/src/ai/ed3n/ed3n_engine.py` | ED3N engine (processing + save/load) |
