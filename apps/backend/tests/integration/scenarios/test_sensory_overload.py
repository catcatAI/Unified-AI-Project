"""
Stress test for Endocrine and StateMatrix systems under extreme sensory input.
Ensures numerical stability and prevents value explosion.
"""
import asyncio
import random
import sys
from pathlib import Path

# Add project root (apps/backend) to sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.autonomous.endocrine_system import EndocrineSystem, HormoneType
from core.autonomous.state_matrix import StateMatrix4D


async def test_sensory_overload():
    print("🚀 [Stress Test] Starting Sensory Overload Scenario...")
    endocrine = EndocrineSystem()
    matrix = StateMatrix4D()
    
    # Simulate 1000 high-frequency "touch/stress" events
    print("Simulating 1000 high-intensity impulses...")
    for i in range(1000):
        # 1. Endocrine pulse
        await endocrine.adjust_hormone(HormoneType.ADRENALINE, random.uniform(5, 20))
        await endocrine.adjust_hormone(HormoneType.CORTISOL, random.uniform(2, 10))
        
        # 2. Matrix jump
        matrix.update_alpha(arousal=random.uniform(0.8, 1.0))
        matrix.set_intent_target("alpha", (random.random(), random.random(), random.random()))
        matrix.apply_intent_gravity()
        
        # 3. Time advancement (simulating 1 second per impulse)
        await endocrine.advance_time(1.0)
        
        if i % 200 == 0:
            adr = endocrine.get_hormone_level(HormoneType.ADRENALINE)
            coord = matrix.alpha.coordinate
            print(f"   Tick {i}: Adrenaline={adr:.2f}, AlphaCoord={coord}")
            
            # Check for NaN or Inf
            assert not any(map(lambda x: x != x or abs(x) == float('inf'), coord))
            assert adr == adr and abs(adr) != float('inf')

    # Final Boundary Check
    for ht in HormoneType:
        level = endocrine.get_hormone_level(ht)
        assert 0 <= level <= 100.0, f"Hormone {ht} out of bounds: {level}"
        
    print("\n✅ Sensory Overload test passed! Numerical stability confirmed.")

if __name__ == "__main__":
    asyncio.run(test_sensory_overload())
