#!/usr/bin/env python
"""Standalone test for hash+matrix system (bypasses core imports)"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src', 'core', 'state'))

print("Testing IntegerHashTable...")
from integer_hash_table import IntegerHashTable

table = IntegerHashTable()
hash_val = table.set("emotion.level", 5)
value = table.get("emotion.level")
assert value == 5
print(f"✅ IntegerHashTable: set/get works (hash={hash_val})")

fingerprint1 = table.get_state_fingerprint()
table.set("hormone.active", 1)
fingerprint2 = table.get_state_fingerprint()
assert fingerprint1 != fingerprint2
print(f"✅ IntegerHashTable: fingerprint changes on state update")

print("\nTesting DecimalHashTable...")
from decimal_hash_table import DecimalHashTable

dec_table = DecimalHashTable()
hash_val = dec_table.set("hormone.alpha", 0.8523)
value = dec_table.get("hormone.alpha")
assert abs(value - 0.8523) < 0.0001
print(f"✅ DecimalHashTable: set/get works (hash={hash_val})")

decayed = dec_table.track_decay("hormone.decay", 1.0, 0.1, 1.0)
assert 0.9 < decayed < 0.91
print(f"✅ DecimalHashTable: decay tracking works (value={decayed:.4f})")

print("\nTesting PrecisionProjectionMatrix...")
from precision_projection_matrix import PrecisionProjectionMatrix, PrecisionMode

matrix = PrecisionProjectionMatrix(auto_detect=False)
mode = matrix.get_precision_mode()
assert mode == "DEC4"
print(f"✅ PrecisionProjectionMatrix: default mode is {mode}")

matrix.set_ram_limit("4GB")
mode = matrix.get_precision_mode()
assert mode == "INT8"
print(f"✅ PrecisionProjectionMatrix: 4GB RAM → {mode} mode")

int8_val = matrix.project_to_int8(0.5, 0.0, 1.0)
recovered = matrix.project_from_int8(int8_val, 0.0, 1.0)
assert abs(recovered - 0.5) < 0.01
print(f"✅ PrecisionProjectionMatrix: INT8 projection works (0.5 → {int8_val} → {recovered:.3f})")

print("\nTesting StateHashManager...")
from state_hash_manager import StateHashManager

manager = StateHashManager(auto_adapt=False)
initial_hash = manager.get_state_hash()

manager.set("emotion.level", 5)
manager.set("hormone.alpha", 0.8)
final_hash = manager.get_state_hash()

assert initial_hash != final_hash
print(f"✅ StateHashManager: global hash changes (initial={initial_hash}, final={final_hash})")

causality_valid = manager.verify_causality(initial_hash, final_hash)
assert causality_valid
print(f"✅ StateHashManager: causality verification passed")

stats = manager.get_stats()
assert stats["integer_operations"] == 1
assert stats["decimal_operations"] == 1
print(f"✅ StateHashManager: stats tracking works ({stats['integer_operations']} int, {stats['decimal_operations']} dec)")

export = manager.export_full_state()
assert "global_hash" in export
assert "integer_table" in export
assert "decimal_table" in export
print(f"✅ StateHashManager: state export works")

print("\n" + "="*70)
print("✅ ALL HASH+MATRIX DUAL SYSTEM COMPONENTS TESTED SUCCESSFULLY!")
print("="*70)
print("\nSummary:")
print("- IntegerHashTable: ✅ (discrete states, uint64 hashing)")
print("- DecimalHashTable: ✅ (continuous states, DEC4/DEC8 precision)")
print("- PrecisionProjectionMatrix: ✅ (adaptive precision, RAM-aware)")
print("- StateHashManager: ✅ (unified coordinator, causality verification)")
print("\nPerformance:")
print(f"- Hash calculation: < 0.1ms (estimated)")
print(f"- State operations: {stats['total_operations']} ops")
print(f"- Precision mode: {manager.get_precision_mode()}")
