#!/usr/bin/env python
"""Simple test script to verify hash table imports"""

print("Testing IntegerHashTable import...")
from apps.backend.src.core.state.integer_hash_table import IntegerHashTable

table = IntegerHashTable()
hash_val = table.set("test", 42)
value = table.get("test")

assert value == 42, f"Expected 42, got {value}"
print(f"✅ IntegerHashTable works! Set/Get test passed. Hash: {hash_val}")

print("\nTesting DecimalHashTable import...")
from apps.backend.src.core.state.decimal_hash_table import DecimalHashTable

dec_table = DecimalHashTable()
hash_val = dec_table.set("test_float", 3.14159)
value = dec_table.get("test_float")

assert abs(value - 3.14159) < 0.0001, f"Expected 3.14159, got {value}"
print(f"✅ DecimalHashTable works! Set/Get test passed. Hash: {hash_val}")

print("\nTesting PrecisionProjectionMatrix import...")
from apps.backend.src.core.state.precision_projection_matrix import PrecisionProjectionMatrix

matrix = PrecisionProjectionMatrix(auto_detect=False)
mode = matrix.get_precision_mode()
print(f"✅ PrecisionProjectionMatrix works! Current mode: {mode}")

print("\nTesting StateHashManager import...")
from apps.backend.src.core.state.state_hash_manager import StateHashManager

manager = StateHashManager(auto_adapt=False)
manager.set("int_state", 5)
manager.set("float_state", 0.8)
global_hash = manager.get_state_hash()

print(f"✅ StateHashManager works! Global hash: {global_hash}")

print("\n" + "="*60)
print("✅ ALL HASH+MATRIX COMPONENTS IMPORTED AND TESTED SUCCESSFULLY!")
print("="*60)
