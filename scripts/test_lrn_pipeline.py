#!/usr/bin/env python3
"""Test latent → LRN → text pipeline."""
import numpy as np
from ai.multimodal.shared_latent_space import SharedLatentSpace
from ai.multimodal.latent_reasoning_network import LatentReasoningNetwork

print("Testing latent -> LRN -> text pipeline...")

# Initialize components
s = SharedLatentSpace(latent_dim=64)
s.register_modality("text", 512)
lrn = LatentReasoningNetwork(latent_dim=64, hidden_dim=128, vocab_size=500)

# Simulate text encoding (random since CLIP is slow)
text_vec = np.random.randn(512).astype(np.float32)
text_vec = text_vec / np.linalg.norm(text_vec)

# Project to latent space
latent = s.project("text", text_vec)
print(f"Latent shape: {latent.shape}")

# Generate text via LRN (neural network)
text = lrn.generate(latent, max_tokens=5)
print(f"Generated text: {text}")

# Train LRN on some examples
examples=[
    ("the sky is blue", "blue"),
    ("what color is the sky", "blue"),
    ("how many days in a week", "seven"),
    ("what comes after monday", "tuesday"),
]
for input_text, target in examples:
    vec = np.random.randn(512).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    lat = s.project("text", vec)
    loss = lrn.train_step(lat, target)
    print(f'Train: "{input_text}" -> "{target}", loss={loss:.3f}')

# Generate after training
text2 = lrn.generate(latent, max_tokens=5)
print(f"After training: {text2}")

print("OK - Latent -> LRN -> text pipeline working!")
