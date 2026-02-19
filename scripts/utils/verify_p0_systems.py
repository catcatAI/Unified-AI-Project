#!/usr/bin/env python3
"""Verify P0-1/P0-2/P0-3 Systems Implementation"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend'))

print("="*60)
print("P0 Systems Verification")
print("="*60)

# P0-1: Hash+Matrix Dual System
print("\n[P0-1] Hash+Matrix Dual System")
try:
    from src.core.state.integer_hash_table import IntegerHashTable
    from src.core.state.decimal_hash_table import DecimalHashTable
    from src.core.state.precision_projection_matrix import PrecisionProjectionMatrix
    from src.core.state.state_hash_manager import StateHashManager
    print("  ✓ Integer Hash Table")
    print("  ✓ Decimal Hash Table")
    print("  ✓ Precision Projection Matrix")
    print("  ✓ State Hash Manager")
    
    # Quick functional test
    manager = StateHashManager()
    manager.set("test.value", 42)
    hash1 = manager.get_state_hash()
    print(f"  ✓ State hash generated: {hash1[:16]}...")
    p0_1_ok = True
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    p0_1_ok = False

# P0-2: Response Composition & Matching
print("\n[P0-2] Response Composition & Matching")
try:
    from src.ai.response.template_matcher import TemplateMatcher
    from src.ai.response.composer import ResponseComposer
    from src.ai.response.deviation_tracker import DeviationTracker
    print("  ✓ Template Matcher")
    print("  ✓ Response Composer")
    print("  ✓ Deviation Tracker")
    
    # Quick functional test
    matcher = TemplateMatcher()
    matcher.add_template("greet_hello", "你好", keywords=["你好", "hello"], category="greeting")
    result = matcher.match("你好")
    print(f"  ✓ Match test: score={result.score:.2f}, level={result.level.value}")
    p0_2_ok = True
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    p0_2_ok = False

# P0-3: Causal Chain Tracing
print("\n[P0-3] Causal Chain Tracing")
try:
    from src.core.tracing.causal_tracer import CausalTracer
    from src.core.tracing.causal_chain import CausalChain, CausalNode, LayerType
    from src.core.tracing.chain_validator import CausalChainValidator
    print("  ✓ Causal Tracer")
    print("  ✓ Causal Chain")
    print("  ✓ Chain Validator")
    
    # Quick functional test
    tracer = CausalTracer()
    trace_id = tracer.start(LayerType.L1_ENDOCRINE, "test_module", "test_action", {"key": "value"})
    print(f"  ✓ Trace started: {trace_id[:16]}...")
    p0_3_ok = True
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    p0_3_ok = False

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"P0-1 Hash+Matrix:      {'✓ PASS' if p0_1_ok else '✗ FAIL'}")
print(f"P0-2 Response System:  {'✓ PASS' if p0_2_ok else '✗ FAIL'}")
print(f"P0-3 Causal Tracing:   {'✓ PASS' if p0_3_ok else '✗ FAIL'}")

all_ok = p0_1_ok and p0_2_ok and p0_3_ok
print(f"\nOverall:               {'✅ ALL SYSTEMS OPERATIONAL' if all_ok else '⚠️  SOME SYSTEMS FAILED'}")
print("="*60)

sys.exit(0 if all_ok else 1)
