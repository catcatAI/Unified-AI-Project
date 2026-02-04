"""
Angela AI v6.0 - Core Integration Tests
核心模块集成测试

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

import sys

def run_tests():
    print("=" * 60)
    print("Angela AI v6.0 - 核心模块集成测试")
    print("=" * 60)
    print()
    
    total_passed = 0
    total_failed = 0
    
    # Test 1: Precision System
    print("📋 TestPrecisionSystem")
    try:
        from core.precision.precision_manager import create_precision_system
        system = create_precision_system()
        assert system is not None
        print("  ✅ test_precision_system_creation")
        total_passed += 1
        
        result = system.encode('test_pi', 3.14159265)
        assert result['integer_part'] == 3
        print("  ✅ test_precision_encoding_decoding")
        total_passed += 1
        
        context = {result['decimal_ref']: 1415}
        decoded = system.decode(result, context)
        assert abs(decoded - 3.1415) < 0.0001
        print("  ✅ test_precision_loss_tracking")
        total_passed += 1
        
    except Exception as e:
        print(f"  ❌ {str(e)[:60]}")
        total_failed += 3
    print()
    
    # Test 2: Maturity System
    print("📋 TestMaturitySystem")
    try:
        from core.maturity.maturity_system import create_maturity_system
        ms = create_maturity_system()
        assert ms is not None
        print("  ✅ test_maturity_system_creation")
        total_passed += 1
        
        status = ms.get_status()
        assert status['level'] == 0
        print("  ✅ test_initial_level")
        total_passed += 1
        
        for _ in range(15):
            ms.interact({'type': 'conversation', 'duration': 60})
        status = ms.get_status()
        assert status['level'] >= 1
        print("  ✅ test_level_progression")
        total_passed += 1
        
    except Exception as e:
        print(f"  ❌ {str(e)[:60]}")
        total_failed += 3
    print()
    
    # Test 3: Soul Core
    print("📋 TestSoulCore")
    try:
        from core.metamorphosis.soul_core import create_soul_core
        soul = create_soul_core()
        assert soul is not None
        print("  ✅ test_soul_creation")
        total_passed += 1
        
        assert soul.signature.soul_id.startswith('soul_')
        print("  ✅ test_soul_signature")
        total_passed += 1
        
        assert soul.verify_integrity() is True
        print("  ✅ test_soul_integrity")
        total_passed += 1
        
    except Exception as e:
        print(f"  ❌ {str(e)[:60]}")
        total_failed += 3
    print()
    
    # Test 4: Body Adapter
    print("📋 TestBodyAdapter")
    try:
        from core.metamorphosis.body_adapter import create_body_adapter
        adapter = create_body_adapter()
        assert adapter is not None
        print("  ✅ test_adapter_creation")
        total_passed += 1
        
        snapshot = adapter.create_snapshot(emotional_state={'happiness': 0.8})
        assert snapshot.version == '6.0.0'
        print("  ✅ test_snapshot_creation")
        total_passed += 1
        
        record = adapter.prepare_transfer('6.0.0', '6.0.0', snapshot)
        success, new_snapshot = adapter.execute_transfer(record, snapshot)
        assert success is True
        print("  ✅ test_transfer_process")
        total_passed += 1
        
    except Exception as e:
        print(f"  ❌ {str(e)[:60]}")
        total_failed += 3
    print()
    
    # Test 5: Transition Animation
    print("📋 TestTransitionAnimation")
    try:
        from core.metamorphosis.transition_anim import create_transition_manager
        manager = create_transition_manager()
        assert manager is not None
        print("  ✅ test_transition_manager_creation")
        total_passed += 1
        
        _, frames = manager.create_upgrade_transition('6.0.0', '6.1.0')
        assert len(frames) == 90
        print("  ✅ test_upgrade_transition")
        total_passed += 1
        
        summary = manager.animator.get_animation_summary()
        assert summary['total_frames'] == 90
        print("  ✅ test_animation_summary")
        total_passed += 1
        
    except Exception as e:
        print(f"  ❌ {str(e)[:60]}")
        total_failed += 3
    print()
    
    # Test 6: Core Exports
    print("📋 TestCoreExports")
    try:
        from core import (
            SoulCore, SoulSignature, IdentityCore, MemoryEssence,
            BodyAdapter, StateSnapshot, TransferRecord,
            TransitionAnimator, TransitionManager, TransitionConfig,
            PrecisionManager, DecimalMemoryBank, HierarchicalPrecisionRouter,
            MaturityLevel, MaturityManager,
        )
        assert SoulCore is not None
        assert BodyAdapter is not None
        assert TransitionManager is not None
        print("  ✅ test_all_exports_available")
        total_passed += 1
        
    except Exception as e:
        print(f"  ❌ {str(e)[:60]}")
        total_failed += 1
    print()
    
    print("=" * 60)
    print(f"测试结果: {total_passed} 通过, {total_failed} 失败")
    print("=" * 60)
    
    return total_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
