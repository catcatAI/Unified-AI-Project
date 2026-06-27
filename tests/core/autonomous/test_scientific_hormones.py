"""
Verification test for scientific hormone modeling
"""
import asyncio
import math

from core.bio.endocrine_system import EndocrineSystem, HormoneType


async def test_hormone_scientific_decay():
    print("Testing Scientific Hormone Decay (Phase 3)...")
    system = EndocrineSystem()
    
    # 1. Trigger an acute boost in adrenaline
    print("\nBoosting Adrenaline...")
    await system.adjust_hormone(HormoneType.ADRENALINE, 50.0)
    initial_level = system.get_hormone_level(HormoneType.ADRENALINE)
    print(f"Initial Adrenaline: {initial_level:.2f}")
    
    # Adrenaline half-life is 6 minutes
    # After 6 minutes, it should be roughly halfway back to base_level (10.0)
    # Target = 10 + (60 - 10) * 0.5 = 35.0
    
    print("\nSimulating 6 minutes of decay...")
    await system.advance_time(6.0 * 60.0)
    
    level_after_half_life = system.get_hormone_level(HormoneType.ADRENALINE)
    print(f"Level after 1 half-life: {level_after_half_life:.2f} (Expected: ~35.0)")
    
    # Verify exponential decay property
    assert 34.0 < level_after_half_life < 36.0
    
    # 2. Verify long-term stability
    print("\nSimulating 2 hours of decay...")
    await system.advance_time(120.0 * 60.0)
    stable_level = system.get_hormone_level(HormoneType.ADRENALINE)
    print(f"Stable level: {stable_level:.2f} (Expected: ~10.0)")
    assert 9.9 < stable_level < 10.1
    
    print("\n✅ Scientific Actualization test passed!")

if __name__ == "__main__":
    asyncio.run(test_hormone_scientific_decay())
