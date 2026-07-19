"""
Angela AI v6.0 - Physiological Tactile System (Re-export Shim)
生理触觉系统

Re-exports all symbols from the split submodules:
- physiological_tactile_types: enums, dataclasses, BODY_TO_LIVE2D_MAPPING
- physiological_tactile_system: PhysiologicalTactileSystem
- physiological_tactile_analysis: TrajectoryAnalyzer, AdaptationMechanism, etc.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

import asyncio
import logging

from .physiological_tactile_analysis import *  # noqa: F401, F403
from .physiological_tactile_system import *  # noqa: F401, F403
from .physiological_tactile_types import *  # noqa: F401, F403

logger = logging.getLogger(__name__)


# Example usage
if __name__ == "__main__":

    async def _demo_tactile_stimuli(system):
        stimuli = [
            TactileStimulus(
                tactile_type=TactileType.LIGHT_TOUCH,
                intensity=3.0,
                location=BodyPart.HANDS,
                duration=2.0,
                source="user_interaction",
                emotional_tag="comfort",
            ),
            TactileStimulus(
                tactile_type=TactileType.PRESSURE,
                intensity=5.0,
                location=BodyPart.SHOULDERS,
                duration=5.0,
                source="massage",
                emotional_tag="relaxation",
            ),
            TactileStimulus(
                tactile_type=TactileType.TEMPERATURE,
                intensity=7.0,
                location=BodyPart.FACE,
                duration=1.0,
                source="environment",
                emotional_tag="anxiety",
            ),
        ]
        logger.info("\n处理触觉刺激 / Processing tactile stimuli:\n")
        for i, stimulus in enumerate(stimuli, 1):
            logger.info(f"{i}. {stimulus.tactile_type.name} on {stimulus.location.cn_name}")
            response = await system.process_stimulus(stimulus)
            logger.info(f"   感知强度: {response.perceived_intensity:.2f}")
            logger.info(f"   激活受体数: {response.activated_receptors}")
            logger.info()

    def _demo_receptor_status(system):
        logger.info("手掌受体状态 / Hand receptor status:")
        status = system.get_receptor_status(BodyPart.HANDS)
        for receptor_type, activation in status.items():
            logger.info(f"  - {receptor_type.name}: {activation:.3f}")

    async def _demo_arousal_change(system):
        logger.info("\n改变唤醒水平 / Changing arousal level to 80...")
        system.set_arousal_level(80)
        logger.info(f"手部敏感度: {system.get_body_part_sensitivity(BodyPart.HANDS):.3f}")
        await system.shutdown()
        logger.info("\n系统已关闭 / System shutdown complete")

    def _demo_trajectory_analyzer():
        import math

        logger.info("\n" + "=" * 60)
        logger.info("轨迹分析器演示 / Trajectory Analyzer Demo")
        logger.info("=" * 60)
        analyzer = TrajectoryAnalyzer()
        logger.info("\n1. 模拟曲线轨迹 / Simulating curved trajectory:")
        for i in range(20):
            angle = i * 0.3
            analyzer.add_point(
                math.cos(angle) * 50 + 100, math.sin(angle) * 30 + 100, pressure=0.5 + i * 0.02
            )
        analysis = analyzer.analyze()
        logger.info(
            f"   运动模式: {analysis.movement_pattern} ({analyzer.MOVEMENT_PATTERNS[analysis.movement_pattern]['cn']})"
        )
        logger.info(f"   平均速度: {analysis.velocity:.2f} px/s")
        logger.info(f"   曲率: {analysis.curvature:.4f}")
        logger.info(f"   置信度: {analysis.pattern_confidence:.2%}")
        logger.info("\n2. 模拟直线轨迹 / Simulating straight trajectory:")
        analyzer.clear()
        for i in range(20):
            analyzer.add_point(100 + i * 5, 100, pressure=0.8)
        analysis = analyzer.analyze()
        logger.info(
            f"   运动模式: {analysis.movement_pattern} ({analyzer.MOVEMENT_PATTERNS[analysis.movement_pattern]['cn']})"
        )
        logger.info(f"   平均速度: {analysis.velocity:.2f} px/s")

    def _demo_adaptation_mechanism():
        logger.info("\n" + "=" * 60)
        logger.info("适应机制演示 / Adaptation Mechanism Demo")
        logger.info("=" * 60)
        mechanism = AdaptationMechanism()
        mechanism.register_receptor("hand_touch", base_sensitivity=0.8)
        logger.info("\n3. 习惯化演示 / Habituation demonstration:")
        logger.info("   重复触摸刺激 / Repeated touch stimuli:")
        for i in range(5):
            state = mechanism.process_stimulus("hand_touch", "touch", intensity=0.6)
            logger.info(
                f"   刺激 #{i+1}: 敏感度={state.current_sensitivity:.3f}, 习惯化={state.habituation_level:.3f}"
            )
        logger.info("\n4. 去习惯化演示 / Dishabituation demonstration:")
        logger.info("   新刺激类型（振动）/ New stimulus type (vibration):")
        state = mechanism.process_stimulus("hand_touch", "vibration", intensity=0.8)
        logger.info(
            f"   敏感度恢复: {state.current_sensitivity:.3f}, 习惯化降低: {state.habituation_level:.3f}"
        )

    async def demo() -> None:
        system = PhysiologicalTactileSystem()
        await system.initialize()
        logger.info("=" * 60)
        logger.info("Angela AI v6.0 - 生理触觉系统演示")
        logger.info("Physiological Tactile System Demo")
        logger.info("=" * 60)
        await _demo_tactile_stimuli(system)
        _demo_receptor_status(system)
        await _demo_arousal_change(system)
        _demo_trajectory_analyzer()
        _demo_adaptation_mechanism()

    asyncio.run(demo())
