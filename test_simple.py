#!/usr/bin/env python3
"""
最简单的测试 - 不依赖Redis
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

try:
    print("Testing basic imports...")
    
    # Test importing without Redis
    import asyncio
    import logging
    from datetime import datetime
    from typing import Dict, Any, List, Optional
    from dataclasses import dataclass
    import numpy as np
    
    print("✓ Basic modules imported")
    
    # Test importing the classes directly
    from ai.ops.ai_ops_engine import AIOpsEngine
    print("✓ AIOpsEngine imported")
    
    from ai.ops.predictive_maintenance import PredictiveMaintenanceEngine
    print("✓ PredictiveMaintenanceEngine imported")
    
    from ai.ops.performance_optimizer import PerformanceOptimizer
    print("✓ PerformanceOptimizer imported")
    
    from ai.ops.capacity_planner import CapacityPlanner
    print("✓ CapacityPlanner imported")
    
    print("\nCreating instances...")
    
    # Create instances without initializing Redis
    ai_ops = AIOpsEngine()
    print("✓ AIOpsEngine instance created")
    
    maintenance = PredictiveMaintenanceEngine()
    print("✓ PredictiveMaintenanceEngine instance created")
    
    optimizer = PerformanceOptimizer()
    print("✓ PerformanceOptimizer instance created")
    
    planner = CapacityPlanner()
    print("✓ CapacityPlanner instance created")
    
    print("\nAll tests passed!")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()