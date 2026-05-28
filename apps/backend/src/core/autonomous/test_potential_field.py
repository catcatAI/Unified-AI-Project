"""
Verification test for Potential Field Spatial Gravity
"""
import math
from typing import Dict, Any, Tuple

from core.engine.state_matrix import StateMatrix4D
from core.engine.cognitive_operations import PotentialFieldEngine

def test_potential_field_mechanics():
    print("Testing Potential Field Mechanics (Phase 3)...")
    engine = PotentialFieldEngine()
    
    # 1. Test Linear Force (Far distance)
    # Target is (10, 0, 0), Current is (0, 0, 0). Dist = 10 (> 0.5)
    # Pull factor 0.1. Delta 0.5. Force mag = 0.1 * 0.5 = 0.05
    disp = engine.calculate_attractive_displacement((0,0,0), (10,0,0), 0.1)
    print(f"Far distance displacement: {disp}")
    assert disp == (0.05, 0.0, 0.0)
    
    # 2. Test Quadratic Force (Near distance)
    # Target is (0.2, 0, 0), Current is (0, 0, 0). Dist = 0.2 (< 0.5)
    # Pull factor 0.1. Force mag = 0.1 * 0.2 = 0.02
    disp_near = engine.calculate_attractive_displacement((0,0,0), (0.2,0,0), 0.1)
    print(f"Near distance displacement: {disp_near}")
    assert math.isclose(disp_near[0], 0.02)
    
    # 3. Test Integration with StateMatrix
    matrix = StateMatrix4D()
    # Set Alpha intent to far away
    matrix.alpha.intent_vector = (1.0, 0.0, 0.0)
    matrix.alpha.coordinate = (0.0, 0.0, 0.0)
    
    print("\nApplying Intent Gravity in Matrix...")
    # pull_factor default is likely 0.05. delta 0.5. dist 1.0 > 0.5. 
    # force = 0.05 * 0.5 = 0.025
    matrix.apply_intent_gravity(pull_factor=0.05)
    
    new_coord = matrix.alpha.coordinate
    print(f"Alpha new coordinate: {new_coord}")
    assert math.isclose(new_coord[0], 0.025)
    
    # 4. Test Inter-dimensional Drag
    # If Alpha moves to (0.025, 0, 0), it should drag Beta
    matrix.beta.coordinate = (0.0, 0.0, 0.0)
    print("\nApplying Inter-dimensional Drag (Alpha drags Beta)...")
    # trigger_dim Alpha (0.025, 0, 0). Beta (0, 0, 0). dist 0.025 < 0.5.
    # drag_factor 0.1. force = 0.1 * 0.025 = 0.0025
    matrix.apply_inter_dimensional_drag("alpha", drag_factor=0.1)
    beta_coord = matrix.beta.coordinate
    print(f"Beta new coordinate: {beta_coord}")
    assert math.isclose(beta_coord[0], 0.0025)

    print("\n✅ Potential Field Mechanics test passed!")

if __name__ == "__main__":
    test_potential_field_mechanics()
