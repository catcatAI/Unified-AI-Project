#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [α] [B] [L3]
# =============================================================================
"""Fine-tune Qwen3-0.6B with LoRA on our QA data (manual training loop)."""
import json
import torch
from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model, TaskType
from torch.utils.data import DataLoader, Dataset

REPO = Path("/home/cxuo/文件/GitHub/Unified-AI-Project")
MODEL_DIR = REPO / "data/models/qwen3-0.6b"
TRAIN_DATA = REPO / "apps/backend/data/processed/core_train.jsonl"
OUTPUT_DIR = REPO / "data/models/qwen3-0.6b-finetuned"

# Load tokenizer and model
print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR), trust_remote_code=True)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    str(MODEL_DIR),
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)

# Apply LoRA
print("Applying LoRA...")
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()

# Prepare data
print("Preparing data...")
data = []
with open(TRAIN_DATA) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        prompt = row.get("input", "").strip()
        answer = row.get("output", "").strip()
        if prompt and answer:
            text = f"User: {prompt}\nAssistant: {answer}"
            data.append(text)

data = data[:2000]  # Limit for speed
print(f"Using {len(data)} training examples")

class QADataset(Dataset):
    def __init__(self, texts, tokenizer, max_length=256):
        self.texts = texts
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoded = self.tokenizer(
            self.texts[idx],
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        input_ids = encoded["input_ids"].squeeze(0)
        attention_mask = encoded["attention_mask"].squeeze(0)
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": input_ids.clone(),
        }

dataset = QADataset(data, tokenizer)
dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

# Training
print("Starting training...")
optimizer = torch.optim.AdamW(model.parameters(), lr=2e-4)
device = next(model.parameters()).device
model.train()

for epoch in range(1):
    total_loss = 0
    for step, batch in enumerate(dataloader):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        if step % 10 == 0:
            print(f"  Step {step}/{len(dataloader)}: loss={loss.item():.4f}")

    avg_loss = total_loss / len(dataloader)
    print(f"Epoch {epoch + 1}: avg_loss={avg_loss:.4f}")

# Save
print("Saving model...")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
model.save_pretrained(str(OUTPUT_DIR))
tokenizer.save_pretrained(str(OUTPUT_DIR))
print(f"Model saved to {OUTPUT_DIR}")