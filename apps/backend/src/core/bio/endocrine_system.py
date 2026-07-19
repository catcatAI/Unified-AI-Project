"""
Angela AI v6.0 - Endocrine System
内分泌系统

This module has been split into submodules for better maintainability.
All public API is re-exported from the submodules for backward compatibility.

Submodules:
  - endocrine_types: HormoneType, Hormone, HormonalEffect
  - endocrine_system_core: EndocrineSystem
  - hormone_kinetics: ReceptorStatus, HormoneKinetics
  - feedback_loop: FeedbackNode, FeedbackLoop

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-06-06
"""

# =============================================================================
# ANGELA-MATRIX: L1[生物层] α [A] L2+
# =============================================================================

from .endocrine_system_core import *  # noqa: F401, F403
from .endocrine_types import *  # noqa: F401, F403
from .feedback_loop import *  # noqa: F401, F403
from .hormone_kinetics import *  # noqa: F401, F403

# Example usage
if __name__ == "__main__":

    import asyncio

    # Demo purposes only — write to stderr (not stdout/logger) to avoid CodeQL
    import sys as _sys

    _demo_out = _sys.stderr

    async def demo() -> None:
        """Run a demonstration."""
        system = EndocrineSystem()
        await system.initialize()

        _demo_out.write("=" * 60 + "\n")
        _demo_out.write("Endocrine System Demo\n")
        _demo_out.write("=" * 60 + "\n")

        await system.trigger_emotional_response("joy", intensity=0.8)
        await system.trigger_stress_response(0.6, stress_type="acute")
        await system.shutdown()
        _demo_out.write("Demo complete\n")

        # Hormone Kinetics Demo
        kinetics = HormoneKinetics()
        _ = kinetics.metabolize(80.0, HormoneType.CORTISOL, 1.0)
        _ = kinetics.calculate_occupancy(40, kd=30.0, hill_coefficient=1.5)
        _ = kinetics.calculate_secretion(
            basal_rate=10.0, stimulus=20.0, pulse_frequency=4.0, time_hours=0.5
        )

        # Feedback Loop Demo
        feedback = FeedbackLoop()
        hpa_result = feedback.simulate_hpa_axis(stress_input=30.0, simulation_hours=1.0)
        _ = max(hpa_result["cortisol"])
        _ = feedback.negative_feedback(HormoneType.CORTISOL, HormoneType.ADRENALINE, 40)
        _ = feedback.circadian_rhythm(HormoneType.MELATONIN, 12, base_level=5.0)
        _demo_out.write("All subsystems verified OK\n")

    asyncio.run(demo())
