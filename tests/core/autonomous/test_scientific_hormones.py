"""
Verification test for scientific hormone modeling
"""
import asyncio
import math

from core.bio.endocrine_system import EndocrineSystem, HormoneType


async def test_hormone_scientific_decay():
    system = EndocrineSystem()

    await system.adjust_hormone(HormoneType.ADRENALINE, 50.0)
    initial_level = system.get_hormone_level(HormoneType.ADRENALINE)

    await system.advance_time(6.0 * 60.0)

    level_after_half_life = system.get_hormone_level(HormoneType.ADRENALINE)

    assert 34.0 < level_after_half_life < 36.0

    await system.advance_time(120.0 * 60.0)
    stable_level = system.get_hormone_level(HormoneType.ADRENALINE)
    assert 9.9 < stable_level < 10.1

if __name__ == "__main__":
    asyncio.run(test_hormone_scientific_decay())
