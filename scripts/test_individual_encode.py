"""Test: what if we match tokens individually instead of whole text?"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.garden.garden_engine import GARDENEngine

e = GARDENEngine(compatibility_mode=True)
ckpt = os.path.join(os.path.dirname(__file__), "..", "data", "checkpoints", "garden_checkpoint")
if os.path.isdir(ckpt):
    e.load(ckpt)

def tokenize(text):
    """Split text into atomic tokens."""
    import re
    # Split on whitespace and punctuation, keep each token
    tokens = re.findall(r"[a-zA-Z0-9]+|[^\s]", text)
    return tokens

def encode_individual(text):
    """Match each token individually against the dictionary."""
    tokens = tokenize(text)
    all_keys = []
    for token in tokens:
        keys = e.dictionary.encode(token)
        if keys:
            all_keys.extend(keys)
        else:
            # Try lowercase
            keys = e.dictionary.encode(token.lower())
            if keys:
                all_keys.extend(keys)
    return all_keys

tests = [
    "1+1=?",
    "true OR false",
    "(true OR false) OR false",
    "NOT false",
    "Mallory is taller than Judy. Who is tallest?",
]

for text in tests:
    print(f"\n{'='*60}")
    print(f"Input: {text}")
    tokens = tokenize(text)
    print(f"Tokens: {tokens}")

    # Current: whole-text encode
    keys_whole = e.dictionary.encode(text)
    print(f"Whole-text encode: {keys_whole}")

    # New: individual token encode
    keys_individual = encode_individual(text)
    print(f"Individual encode: {keys_individual}")

    if keys_individual:
        # Show what each key maps to
        for k in keys_individual:
            entry = e.dictionary.entries.get(k)
            if entry:
                sf = entry.surface_forms.get("zh") or entry.surface_forms.get("en") or k
                print(f"  {k} -> {sf}")

        # Test SNN with individual keys
        snn_out = e.snn.forward(keys_individual)
        sorted_out = sorted(snn_out.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"SNN output top5:")
        for k, v in sorted_out:
            entry = e.dictionary.entries.get(k)
            sf = entry.surface_forms.get("zh") or entry.surface_forms.get("en") or k if entry else "???"
            print(f"  {k}: {v:.3f} -> {sf}")
