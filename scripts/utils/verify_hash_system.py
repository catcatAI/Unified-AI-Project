#!/usr/bin/env python
"""Quick verification script for Hash+Matrix Dual System"""

import sys
import os

project_root = os.path.dirname(__file__)
sys.path.insert(0, project_root)

os.environ['ANGELA_KEY_A'] = 'test_key_a_' + '0' * 32
os.environ['ANGELA_KEY_B'] = 'test_key_b_' + '0' * 32
os.environ['ANGELA_KEY_C'] = 'test_key_c_' + '0' * 32

print("Testing Hash+Matrix components...")

print("\n1. IntegerHashTable...")
from apps.backend.src.core.state.integer_hash_table import IntegerHashTable
table = IntegerHashTable()
table.set("test", 42)
assert table.get("test") == 42
print("   ✅ Works")

print("\n2. DecimalHashTable...")
from apps.backend.src.core.state.decimal_hash_table import DecimalHashTable
dec_table = DecimalHashTable()
dec_table.set("test", 3.14)
assert abs(dec_table.get("test") - 3.14) < 0.01
print("   ✅ Works")

print("\n3. PrecisionProjectionMatrix...")
from apps.backend.src.core.state.precision_projection_matrix import PrecisionProjectionMatrix
matrix = PrecisionProjectionMatrix(auto_detect=False)
assert matrix.get_precision_mode() == "DEC4"
print("   ✅ Works")

print("\n4. StateHashManager...")
from apps.backend.src.core.state.state_hash_manager import StateHashManager
manager = StateHashManager(auto_adapt=False)
manager.set("test1", 1)
manager.set("test2", 0.5)
hash_val = manager.get_state_hash()
assert hash_val > 0
print(f"   ✅ Works (hash={hash_val})")

print("\n5. Key Integration...")
from apps.backend.src.shared.key_manager import UnifiedKeyManager
key_mgr = UnifiedKeyManager()
signature = key_mgr.sign_with_key_a(12345)
assert len(signature) == 64
verified = key_mgr.verify_signature_with_key_a(12345, signature)
assert verified
print("   ✅ Works")

print("\n" + "="*60)
print("✅ ALL COMPONENTS FUNCTIONAL")
print("="*60)
