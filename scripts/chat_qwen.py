#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [α] [B] [L3]
# =============================================================================
"""Chat with the fine-tuned Qwen model."""
import sys
from pathlib import Path
import torch

REPO = Path("/home/cxuo/文件/GitHub/Unified-AI-Project")
MODEL_DIR = REPO / "data/models/qwen3-0.6b-finetuned"
BASE_DIR = REPO / "data/models/qwen3-0.6b"

from transformers import AutoModelForCausalLM, AutoTokenizer

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(str(MODEL_DIR), trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    str(MODEL_DIR),
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
)
model.eval()

questions = [
    "What is 2 + 3?",
    "What is the capital of France?",
    "Hello",
    "Tell me a joke",
    "How many legs does a dog have?",
    "What color is the sky?",
]

for q in questions:
    prompt = f"User: {q}\nAssistant:"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=50,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )
    response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    print(f"Q: {q}")
    print(f"A: {response.strip()}")
    print()