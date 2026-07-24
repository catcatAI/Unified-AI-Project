"""Check what's actually in the dictionary."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.garden.garden_engine import GARDENEngine

e = GARDENEngine(compatibility_mode=True)
ckpt = os.path.join(os.path.dirname(__file__), "..", "data", "checkpoints", "garden_checkpoint")
if os.path.isdir(ckpt):
    e.load(ckpt)

entries = e.dictionary.entries
print(f"Total entries: {len(entries)}")

# Show first 30
print("\nFirst 30 entries:")
for i, (k, v) in enumerate(list(entries.items())[:30]):
    en = v.surface_forms.get("en", "?")[:50]
    zh = v.surface_forms.get("zh", "?")[:50]
    print(f"  {k:8s} en={en:50s} zh={zh}")

# Check if any entry contains numbers, operators, or logic keywords
print("\n--- Searching for math/logic/reasoning tokens ---")
keywords = ["1", "2", "3", "+", "-", "*", "/", "=", "?", "true", "false", "and", "or", "not",
            "taller", "shorter", "who", "what", "how"]
for kw in keywords:
    found = []
    for k, v in entries.items():
        en = v.surface_forms.get("en", "")
        zh = v.surface_forms.get("zh", "")
        if kw.lower() in en.lower() or kw in zh:
            found.append((k, en[:40], zh[:40]))
    if found:
        print(f"\n  '{kw}' found in {len(found)} entries:")
        for k, en, zh in found[:5]:
            print(f"    {k}: en={en} zh={zh}")
    else:
        print(f"\n  '{kw}' NOT FOUND in any entry")
