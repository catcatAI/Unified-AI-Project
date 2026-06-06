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

from .endocrine_types import *  # noqa: F401, F403
from .endocrine_system_core import *  # noqa: F401, F403
from .hormone_kinetics import *  # noqa: F401, F403
from .feedback_loop import *  # noqa: F401, F403


# Example usage
if __name__ == "__main__":

    import asyncio
    import logging

    logger = logging.getLogger(__name__)

    async def demo() -> None:
        """Run a demonstration."""
        system = EndocrineSystem()
        await system.initialize()

        logger.info("=" * 60)
        logger.info("Angela AI v6.0 - 内分泌系统演示")
        logger.info("Endocrine System Demo")
        logger.info("=" * 60)

        # Show initial state
        logger.info("\n初始激素水平 / Initial hormone levels:")
        for hormone_type, level in system.get_all_hormone_levels().items():
            logger.info(f"  {hormone_type.cn_name}: {level:.1f}")

        # Trigger emotions
        logger.info("\n触发情绪反应 / Triggering emotional responses:")

        logger.info("\n1. 快乐 / Joy:")
        await system.trigger_emotional_response("joy", intensity=0.8)
        logger.info(f"   多巴胺: {system.get_hormone_level(HormoneType.DOPAMINE):.1f}")
        logger.info(f"   血清素: {system.get_hormone_level(HormoneType.SEROTONIN):.1f}")

        logger.info("\n2. 压力 / Stress:")
        await system.trigger_stress_response(0.6, stress_type="acute")
        logger.info(f"   肾上腺素: {system.get_hormone_level(HormoneType.ADRENALINE):.1f}")
        logger.info(f"   皮质醇: {system.get_hormone_level(HormoneType.CORTISOL):.1f}")

        # Show systemic effects
        logger.info("\n系统性影响 / Systemic effects:")
        effects = system.calculate_systemic_effects()
        for system_name, value in effects.items():
            logger.info(f"  {system_name}: {value:.2f}")

        await system.shutdown()
        logger.info("\n系统已关闭 / System shutdown complete")

        # Hormone Kinetics Demo
        logger.info("\n" + "=" * 60)
        logger.info("激素动力学演示 / Hormone Kinetics Demo")
        logger.info("=" * 60)

        kinetics = HormoneKinetics()

        logger.info("\n3. 半衰期代谢 / Half-life metabolism:")
        initial = 80.0
        for hours in [0.5, 1.0, 2.0, 4.0]:
            remaining = kinetics.metabolize(initial, HormoneType.CORTISOL, hours)
            logger.info(
                f"   {hours}小时后 / after {hours}h: {remaining:.1f} (半衰期 / half-life: 1.5h)"
            )

        logger.info("\n4. 受体占用 (Hill方程) / Receptor occupancy (Hill equation):")
        for level in [10, 20, 40, 80]:
            occupancy = kinetics.calculate_occupancy(level, kd=30.0, hill_coefficient=1.5)
            logger.info(f"   激素水平 {level}: 占用率 / occupancy: {occupancy:.2%}")

        logger.info("\n5. 分泌调节 / Secretion regulation:")
        for t in [0, 0.25, 0.5, 0.75, 1.0]:
            secretion = kinetics.calculate_secretion(
                basal_rate=10.0, stimulus=20.0, pulse_frequency=4.0, time_hours=t
            )
            logger.info(f"   t={t}h: 分泌率 / secretion rate: {secretion:.2f}")

        # Feedback Loop Demo
        logger.info("\n" + "=" * 60)
        logger.info("反馈回路演示 / Feedback Loop Demo")
        logger.info("=" * 60)

        feedback = FeedbackLoop()

        logger.info("\n6. HPA轴模拟 / HPA axis simulation:")
        hpa_result = feedback.simulate_hpa_axis(stress_input=30.0, simulation_hours=1.0)
        logger.info(f"   初始CRH: {hpa_result['crh'][0]:.1f}")
        logger.info(f"   峰值ACTH: {max(hpa_result['acth']):.1f}")
        logger.info(f"   峰值皮质醇: {max(hpa_result['cortisol']):.1f}")

        logger.info("\n7. 负反馈调节 / Negative feedback:")
        cortisol_levels = [20, 40, 60, 80]
        for level in cortisol_levels:
            inhibition = feedback.negative_feedback(
                HormoneType.CORTISOL, HormoneType.ADRENALINE, level
            )
            logger.info(f"   皮质醇 / cortisol {level}: 抑制 / inhibition: {inhibition:.2%}")

        logger.info("\n8. 昼夜节律 / Circadian rhythm:")
        for hour in [0, 6, 12, 18, 22]:
            melatonin = feedback.circadian_rhythm(HormoneType.MELATONIN, hour, base_level=5.0)
            cortisol = feedback.circadian_rhythm(HormoneType.CORTISOL, hour, base_level=20.0)
            logger.info(
                f"   {hour:02d}:00 - 褪黑素 / melatonin: {melatonin:.1f}, 皮质醇 / cortisol: {cortisol:.1f}"
            )

    asyncio.run(demo())
