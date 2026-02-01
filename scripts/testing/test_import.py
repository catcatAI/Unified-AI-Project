#!/usr/bin/env python3
import sys
import os

# Add backend src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

try:
    print("Testing imports...")
    
    # Test basic imports
    print("Importing numpy...")
    import numpy as np
    print("✓ numpy imported")
    
    print("Importing redis...")
    import redis.asyncio as redis
    print("✓ redis imported")
    
    print("Importing AI ops modules...")
    from ai.ops.ai_ops_engine import AIOpsEngine, get_ai_ops_engine
    print("✓ ai_ops_engine imported")
    
    from ai.ops.intelligent_ops_manager import IntelligentOpsManager, get_intelligent_ops_manager
    print("✓ intelligent_ops_manager imported")
    
    print("\nTesting instantiation...")
    
    # Create instances
    ops_manager = get_intelligent_ops_manager()
    print("✓ ops_manager created")
    
    ai_ops = get_ai_ops_engine()
    print("✓ ai_ops created")
    
    print("\nAll imports successful!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()