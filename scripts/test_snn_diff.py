"""Quick test: does the SNN produce different outputs for different inputs?"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.garden.garden_engine import GARDENEngine

e = GARDENEngine(compatibility_mode=True)
e.load(os.path.join(os.path.dirname(__file__), "..", "data", "checkpoints", "garden_checkpoint"))

tests = ["178+101", "true OR false", "hello", "什么是人工智能"]
for t in tests:
    k = e.dictionary.encode(t)
    o = e.snn.forward(k)
    top = sorted(o.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"{t:25s} keys={str(k[:4]):40s} top={top}")
