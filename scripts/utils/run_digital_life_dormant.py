"""Standalone test: DORMANT auto-transition logic (runs outside pytest).
Bypasses circular import by patching sys.modules before importing the module."""
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, "apps/backend/src")

# Patch circular dependencies BEFORE any real import
import ai.lifecycle  # noqa: F811 - first import creates namespace
sys.modules["ai.lifecycle.llm_decision_loop"] = MagicMock()
sys.modules["ai.lifecycle.user_monitor"] = MagicMock()
sys.modules["ai.lifecycle.proactive_interaction_system"] = MagicMock()
sys.modules["services.brain_bridge_service"] = MagicMock()
sys.modules["services.weather_service"] = MagicMock()

import importlib
_mod = importlib.import_module("core.life.digital_life_integrator")
DLI = _mod.DigitalLifeIntegrator
LCS = _mod.LifeCycleState


def make_integrator(**overrides):
    inst = DLI.__new__(DLI)
    inst.config = overrides
    inst.state_matrix = MagicMock()
    inst.state_matrix.alpha.values={"tension": 0.1}
    inst.state_matrix.beta.values={"confusion": 0.1}
    inst.state_matrix.gamma.values={"calm": 0.8}
    inst.state_matrix.delta.values={"trust": 0.8}
    inst.state_matrix.evaluate_math_spatially.return_value=0.7
    inst._last_activity_time = datetime.now()
    inst._is_active=False
    inst._rest_threshold_minutes = overrides.get("rest_threshold_minutes", 30.0)
    inst._dormant_threshold_minutes = overrides.get("dormant_threshold_minutes", 120.0)
    inst._life_state = LCS.RESTING
    inst.life_cycle_state = LCS.RESTING
    inst.previous_state = LCS.INITIALIZING
    inst._transition_state = AsyncMock()
    inst._event_callbacks=[]
    inst.life_events=[]
    inst.logger = MagicMock()
    return inst


async def test_dormant_auto_1():
    """RESTING + 180min inactive -> DORMANT"""
    i = make_integrator()
    i._last_activity_time = datetime.now() - timedelta(minutes=180)
    i._is_active=False
    i.life_cycle_state = LCS.RESTING
    await i._check_activity_status()
    assert i._transition_state.await_count == 1, "Expected DORMANT transition"
    assert i._transition_state.await_args[0][0] == LCS.DORMANT
    print("PASS: test_dormant_auto_1")


async def test_dormant_auto_2():
    """RESTING + 60min inactive (under dormant threshold) -> no transition"""
    i = make_integrator(dormant_threshold_minutes=120.0)
    i._last_activity_time = datetime.now() - timedelta(minutes=60)
    i._is_active=False
    i.life_cycle_state = LCS.RESTING
    await i._check_activity_status()
    assert i._transition_state.await_count == 0, "Expected NO transition"
    print("PASS: test_dormant_auto_2")


async def test_dormant_auto_3():
    """MATURE + 45min inactive -> RESTING"""
    i = make_integrator(rest_threshold_minutes=30.0)
    i._last_activity_time = datetime.now() - timedelta(minutes=45)
    i._is_active=True
    i.life_cycle_state = LCS.MATURE
    await i._check_activity_status()
    assert i._transition_state.await_count == 1
    assert i._transition_state.await_args[0][0] == LCS.RESTING
    print("PASS: test_dormant_auto_3")


async def test_dormant_auto_4():
    """RESTING + activity within 60s -> MATURE"""
    i = make_integrator()
    i._last_activity_time = datetime.now()
    i._is_active=False
    i.life_cycle_state = LCS.RESTING
    await i._check_activity_status()
    assert i._transition_state.await_count == 1
    assert i._transition_state.await_args[0][0] == LCS.MATURE
    print("PASS: test_dormant_auto_4")


async def test_dormant_low_maturity_1():
    """RESTING + maturity 0.15 < 0.2 -> DORMANT"""
    i = make_integrator()
    i.life_cycle_state = LCS.RESTING
    i._compute_maturity_score = MagicMock(return_value=0.15)
    await i._process_life_cycle_transitions()
    assert i._transition_state.await_count == 1
    assert i._transition_state.await_args[0][0] == LCS.DORMANT
    print("PASS: test_dormant_low_maturity_1")


async def test_dormant_low_maturity_2():
    """RESTING + maturity 0.5 >= 0.2 -> no transition"""
    i = make_integrator()
    i.life_cycle_state = LCS.RESTING
    i._compute_maturity_score = MagicMock(return_value=0.5)
    await i._process_life_cycle_transitions()
    assert i._transition_state.await_count == 0
    print("PASS: test_dormant_low_maturity_2")


async def test_dormant_low_maturity_3():
    """MATURE + maturity 0.15 < 0.2 -> no transition (only RESTING -> DORMANT)"""
    i = make_integrator()
    i.life_cycle_state = LCS.MATURE
    i._compute_maturity_score = MagicMock(return_value=0.15)
    await i._process_life_cycle_transitions()
    assert i._transition_state.await_count == 0
    print("PASS: test_dormant_low_maturity_3")


async def main():
    tests=[
        test_dormant_auto_1, test_dormant_auto_2, test_dormant_auto_3,
        test_dormant_auto_4, test_dormant_low_maturity_1,
        test_dormant_low_maturity_2, test_dormant_low_maturity_3,
    ]
    failed=0
    for t in tests:
        try:
            await t()
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1
    print(f"\n{'='*40}\n{len(tests)-failed}/{len(tests)} passed" +
          (f", {failed} FAILED" if failed else ", all PASS"))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
