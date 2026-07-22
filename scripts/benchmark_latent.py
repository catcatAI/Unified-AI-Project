#!/usr/bin/env python3
"""Quick benchmark for ED3N with latent space reasoning."""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from ai.ed3n.ed3n_engine import ED3NEngine

print("Initializing ED3N with latent space...")
t0 = time.time()
e = ED3NEngine(auto_load_presets=True, auto_load_dictionaries=False)
e.enable_latent_space()
print(f"Init: {time.time()-t0:.1f}s")

# Math
print("\n=== Math Tests ===")
math_tests=[
    ("1 + 1 = ?", "2"),
    ("2 + 3 * 4 = ?", "14"),
    ("100 / 25 = ?", "4"),
    ("15 - 7 = ?", "8"),
    ("3 * 7 = ?", "21"),
]
math_pass=0
for q, expected in math_tests:
    r = e.process(q)
    passed = expected in r if r else False
    math_pass += int(passed)
    status="PASS" if passed else "FAIL"
    print(f"  {q} -> {r} [{status}]")
print(f"Math: {math_pass}/5")

# Knowledge
print("\n=== Knowledge Tests ===")
knowledge_tests=[
    ("What color is the sky?", "blue"),
    ("What is the opposite of hot?", "cold"),
    ("What animal says meow?", "cat"),
    ("How many days in a week?", "7"),
    ("What planet is known as the Red Planet?", "Mars"),
]
knowledge_pass=0
for q, expected in knowledge_tests:
    r = e.process(q)
    passed = expected.lower() in r.lower() if r else False
    knowledge_pass += int(passed)
    status="PASS" if passed else "FAIL"
    print(f"  {q} -> {r} [{status}]")
print(f"Knowledge: {knowledge_pass}/5")

# Reasoning
print("\n=== Reasoning Tests ===")
reasoning_tests=[
    ("A is taller than B. B is taller than C. Who is tallest?", "A"),
    ("If today is Monday, what day is tomorrow?", "Tuesday"),
    ("John has 3 apples. He gives 1 away. How many left?", "2"),
]
reasoning_pass=0
for q, expected in reasoning_tests:
    r = e.process(q)
    passed = expected.lower() in r.lower() if r else False
    reasoning_pass += int(passed)
    status="PASS" if passed else "FAIL"
    print(f"  {q} -> {r} [{status}]")
print(f"Reasoning: {reasoning_pass}/3")

total = math_pass + knowledge_pass + reasoning_pass
print(f"\n=== Total: {total}/13 ({total/13*100:.0f}%) ===")
