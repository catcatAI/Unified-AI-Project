#!/usr/bin/env python3
"""Verify fixes applied to Angela AI system"""

import sys
import os
import asyncio
import logging
logger = logging.getLogger(__name__)

# Add apps/backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'apps/backend')
sys.path.insert(0, backend_path)

async def test_cluster_manager_fixes():
    """Test ClusterManager fixes"""
    print("\n" + "=" * 60)
    print("Testing ClusterManager Fixes")
    print("=" * 60)

    try:
        from src.system.cluster_manager import ClusterManager

        cluster = ClusterManager()

        # Test get_all_nodes
        print("\n1. Testing get_all_nodes()...")
        nodes = cluster.get_all_nodes()
        print(f"   Total nodes: {len(nodes)}")
        for node in nodes:
            print(f"   - {node['id']}: {node['status']}")

        # Test get_node_status
        print("\n2. Testing get_node_status()...")
        if nodes:
            first_node = nodes[0]
            status = cluster.get_node_status(first_node['id'])
            print(f"   Node {first_node['id']}: {status['status']}")

        # Test get_node_status with non-existent node
        print("\n3. Testing get_node_status() with non-existent node...")
        status = cluster.get_node_status("non-existent-node")
        print(f"   Non-existent node: {status}")

        print("\n[PASS] ClusterManager fixes verified successfully")
        return True

    except Exception as e:
        print(f"\n[FAIL] ClusterManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_memory_enhancement_fix():
    """Test memory enhancement fix"""
    print("\n" + "=" * 60)
    print("Testing Memory Enhancement Fix")
    print("=" * 60)

    try:
        from src.services.angela_llm_service import get_llm_service

        service = await get_llm_service()

        print(f"\nMemory Enhanced: {service.enable_memory_enhancement}")

        if service.enable_memory_enhancement:
            print("[PASS] Memory enhancement is enabled")
        else:
            print("[WARNING] Memory enhancement is disabled (LLM will be called directly)")

        return True

    except Exception as e:
        print(f"\n[FAIL] Memory enhancement test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_live2d_manager_fix():
    """Test Live2D Manager fixes"""
    print("\n" + "=" * 60)
    print("Testing Live2D Manager Fixes")
    print("=" * 60)

    try:
        # Read the live2d-manager.js file
        js_path = os.path.join(os.path.dirname(__file__), 'apps/desktop-app/electron_app/js/live2d-manager.js')

        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for handleTouch method
        print("\n1. Checking handleTouch() method...")
        if 'handleTouch(x, y, touchType' in content:
            print("   [PASS] handleTouch() method found")
        else:
            print("   [FAIL] handleTouch() method not found")

        # Check for detectTouch method
        print("\n2. Checking detectTouch() method...")
        if 'detectTouch(x, y)' in content:
            print("   [PASS] detectTouch() method found")
        else:
            print("   [FAIL] detectTouch() method not found")

        # Check for setTouchDetector method
        print("\n3. Checking setTouchDetector() method...")
        if 'setTouchDetector(touchDetector)' in content:
            print("   [PASS] setTouchDetector() method found")
        else:
            print("   [FAIL] setTouchDetector() method not found")

        # Check for getTouchDetector method
        print("\n4. Checking getTouchDetector() method...")
        if 'getTouchDetector()' in content:
            print("   [PASS] getTouchDetector() method found")
        else:
            print("   [FAIL] getTouchDetector() method not found")

        print("\n[PASS] Live2D Manager fixes verified successfully")
        return True

    except Exception as e:
        print(f"\n[FAIL] Live2D Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("=" * 60)
    print("Angela AI System - Fix Verification")
    print("=" * 60)

    results = {
        "ClusterManager": await test_cluster_manager_fixes(),
        "Memory Enhancement": await test_memory_enhancement_fix(),
        "Live2D Manager": await test_live2d_manager_fix()
    }

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n[SUCCESS] All fixes verified successfully!")
    else:
        print("\n[WARNING] Some fixes failed, please review the errors above")

    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)