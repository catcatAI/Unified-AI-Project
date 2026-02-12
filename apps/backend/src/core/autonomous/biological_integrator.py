"""
Angela AI v6.0 - Biological Integrator
生物系统整合器

Integrates all biological simulation systems (tactile, endocrine, nervous,
neuroplasticity, emotions) and manages their interconnections and mutual influences.

Features:
- Coordinates all biological subsystems
- Manages cross-system interactions
- Synchronizes physiological-emotional-hormonal states
- Maintains biological homeostasis

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import asyncio
import logging
logger = logging.getLogger(__name__)

from .physiological_tactile import PhysiologicalTactileSystem, TactileType, BodyPart
from .endocrine_system import EndocrineSystem, HormoneType
from .autonomic_nervous_system import AutonomicNervousSystem, NerveType
from .neuroplasticity import NeuroplasticitySystem
from .emotional_blending import EmotionalBlendingSystem, BasicEmotion


@dataclass
class SystemInteraction:
    """系统间交互 / System interaction definition"""
    source_system: str
    target_system: str
    interaction_type: str
    influence_strength: float  # 0-1
    bidirectional: bool = False


class BiologicalIntegrator:
    """
    生物系统整合器主类 / Main biological integrator class
    
    Coordinates and integrates all biological simulation systems for Angela AI,
    managing their interactions and maintaining overall biological homeostasis.
    
    Attributes:
        tactile_system: Physiological tactile system
        endocrine_system: Hormonal/endocrine system
        nervous_system: Autonomic nervous system
        neuroplasticity_system: Learning and memory plasticity
        emotional_system: Emotional processing and blending
        interactions: Active system interactions
    
    Example:
        >>> integrator = BiologicalIntegrator()
        >>> await integrator.initialize()
        >>> 
        >>> # Process a stress event through all systems
        >>> await integrator.process_stress_event(intensity=0.7)
        >>> 
        >>> # Get integrated biological state
        >>> state = integrator.get_biological_state()
        >>> print(f"Overall arousal: {state['arousal']:.2f}")
        >>> print(f"Emotional state: {state['dominant_emotion']}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Biological subsystems
        self.tactile_system: PhysiologicalTactileSystem = PhysiologicalTactileSystem()
        self.endocrine_system: EndocrineSystem = EndocrineSystem()
        self.nervous_system: AutonomicNervousSystem = AutonomicNervousSystem()
        self.neuroplasticity_system: NeuroplasticitySystem = NeuroplasticitySystem()
        self.emotional_system: EmotionalBlendingSystem = EmotionalBlendingSystem()
        
        # Interactions
        self.interactions: List[SystemInteraction] = []
        self._setup_default_interactions()
        
        # State tracking
        self._last_update: datetime = datetime.now()
        # Configurable homeostatic targets (from config or use defaults)
        self._homeostatic_targets = self.config.get('homeostatic_targets', {
            "arousal": 50.0,
            "stress": 20.0,
            "mood": 0.6,
        })
        
        # Update interval from config (default 5 seconds)
        self._update_interval = self.config.get('update_interval', 5.0)
        
        # Running state
        self._running = False
        self._integration_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._state_callbacks: List[Callable[[Dict[str, Any]], None]] = []
    
    def _setup_default_interactions(self):
        """Set up default system interactions"""
        self.interactions = [
            # Nervous system influences hormones
            SystemInteraction("nervous", "endocrine", "arousal_to_adrenaline", 0.8),
            
            # Hormones influence emotions
            SystemInteraction("endocrine", "emotional", "hormonal_mood", 0.7, True),
            
            # Emotions influence nervous system
            SystemInteraction("emotional", "nervous", "emotion_to_arousal", 0.6, True),
            
            # Tactile influences emotions
            SystemInteraction("tactile", "emotional", "touch_to_emotion", 0.5),
            
            # Emotions influence tactile sensitivity
            SystemInteraction("emotional", "tactile", "emotion_to_sensitivity", 0.4, True),
            
            # Nervous system influences tactile sensitivity
            SystemInteraction("nervous", "tactile", "arousal_to_sensitivity", 0.6),
            
            # Stress hormones influence neuroplasticity
            SystemInteraction("endocrine", "neuroplasticity", "cortisol_to_memory", 0.5),
            
            # Emotional memories influence neuroplasticity
            SystemInteraction("emotional", "neuroplasticity", "emotional_memory", 0.7),
        ]
    
    async def initialize(self):
        """Initialize all biological systems"""
        self._running = True
        
        # Initialize subsystems
        await self.tactile_system.initialize()
        await self.endocrine_system.initialize()
        await self.nervous_system.initialize()
        await self.neuroplasticity_system.initialize()
        await self.emotional_system.initialize()
        
        # Set up cross-system callbacks
        self._setup_cross_system_callbacks()
        
        # Start integration loop
        self._integration_task = asyncio.create_task(self._integration_loop())
    
    async def shutdown(self):
        """Shutdown all biological systems"""
        self._running = False
        
        if self._integration_task:
            self._integration_task.cancel()
            try:
                await self._integration_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown subsystems
        await self.tactile_system.shutdown()
        await self.endocrine_system.shutdown()
        await self.nervous_system.shutdown()
        await self.neuroplasticity_system.shutdown()
        await self.emotional_system.shutdown()
    
    def _setup_cross_system_callbacks(self):
        """Set up callbacks for cross-system communication"""
        # Nervous system arousal changes affect endocrine system
        self.nervous_system.register_arousal_callback(self._on_arousal_change)
        
        # Hormone changes affect emotional system
        self.endocrine_system.register_change_callback(self._on_hormone_change)
        
        # Emotional changes affect nervous system
        self.emotional_system.register_emotion_change_callback(self._on_emotion_change)
    
    def _on_arousal_change(self, arousal: float):
        """Handle arousal level changes"""
        # Affect tactile sensitivity
        self.tactile_system.set_arousal_level(arousal)
        
        # High arousal triggers adrenaline
        if arousal > 70:
            asyncio.create_task(
                self.endocrine_system.trigger_stress_response(
                    (arousal - 70) / 30, 
                    stress_type="acute"
                )
            )
    
    def _on_hormone_change(self, hormone_type: HormoneType, old_val: float, new_val: float):
        """Handle hormone level changes"""
        # Dopamine and serotonin affect emotions
        if hormone_type in [HormoneType.DOPAMINE, HormoneType.SEROTONIN]:
            normalized = (new_val - 20) / 80  # Rough normalization
            self.emotional_system.apply_influence(
                "hormonal",
                hormone_type.en_name.lower(),
                normalized,
                0.6
            )
        
        # Adrenaline affects nervous system
        if hormone_type == HormoneType.ADRENALINE:
            arousal_boost = (new_val / 100) * 20
            current_arousal = self.nervous_system.arousal_level
            self.nervous_system.set_arousal_directly(
                min(100, current_arousal + arousal_boost)
            )
    
    def _on_emotion_change(self, old_emotion, new_emotion):
        """Handle emotional state changes"""
        # Affect nervous system based on emotion arousal
        arousal_impact = new_emotion.arousal * 30  # -30 to 30
        current_arousal = self.nervous_system.arousal_level
        self.nervous_system.set_arousal_directly(
            max(0, min(100, current_arousal + arousal_impact))
        )
        
        # Emotional touch preferences
        if new_emotion.pleasure > 0.5:
            # Positive emotions prefer gentle touch
            self.tactile_system.apply_emotional_context("joy", new_emotion.intensity)
        elif new_emotion.pleasure < -0.3:
            # Negative emotions
            self.tactile_system.apply_emotional_context("anxiety", new_emotion.intensity)
    
    async def _integration_loop(self):
        """Background loop for system integration - Configurable"""
        while self._running:
            await self._apply_homeostasis()
            await self._synchronize_states()
            await asyncio.sleep(self._update_interval)  # Configurable update interval
    
    async def _apply_homeostasis(self):
        """Apply homeostatic regulation across all systems"""
        # Gradual return to baseline for each system
        current_arousal = self.nervous_system.arousal_level
        target_arousal = self._homeostatic_targets["arousal"]
        
        if abs(current_arousal - target_arousal) > 5:
            adjustment = (target_arousal - current_arousal) * 0.02
            self.nervous_system.set_arousal_directly(current_arousal + adjustment)
    
    async def _synchronize_states(self):
        """Synchronize states across all biological systems"""
        # Calculate integrated state
        integrated_state = self.get_biological_state()
        
        # Notify state callbacks
        for callback in self._state_callbacks:
            try:
                callback(integrated_state)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

    
    async def process_stress_event(self, intensity: float, duration: float = 10.0):
        """
        Process a stress event through all biological systems
        
        Args:
            intensity: Stress intensity (0-1)
            duration: Duration in seconds
        """
        # Trigger sympathetic nervous system
        await self.nervous_system.apply_stimulus(
            "stress_event",
            NerveType.SYMPATHETIC,
            intensity,
            duration
        )
        
        # Trigger endocrine stress response
        await self.endocrine_system.trigger_stress_response(
            intensity,
            stress_type="acute" if duration < 30 else "chronic"
        )
        
        # Affect emotions
        self.emotional_system.apply_influence(
            "physiological",
            "stress",
            intensity,
            0.8
        )
    
    async def process_relaxation_event(self, intensity: float = 0.5):
        """
        Process a relaxation event through all biological systems
        
        Args:
            intensity: Relaxation intensity (0-1)
        """
        # Trigger parasympathetic nervous system
        await self.nervous_system.apply_stimulus(
            "relaxation",
            NerveType.PARASYMPATHETIC,
            intensity,
            30.0
        )
        
        # Trigger positive hormones
        await self.endocrine_system.trigger_emotional_response(
            "relaxation",
            intensity
        )
        
        # Positive emotional influence
        self.emotional_system.set_emotion_from_basic(
            BasicEmotion.CALM,
            intensity
        )
    
    async def process_touch_interaction(
        self, 
        body_part: BodyPart, 
        intensity: float,
        emotional_context: Optional[str] = None
    ):
        """
        Process a touch interaction through biological systems
        
        Args:
            body_part: Body part touched
            intensity: Touch intensity
            emotional_context: Optional emotional context
        """
        from .physiological_tactile import TactileStimulus
        
        # Create tactile stimulus
        stimulus = TactileStimulus(
            tactile_type=TactileType.LIGHT_TOUCH,
            intensity=intensity * 10,
            location=body_part,
            duration=2.0,
            emotional_tag=emotional_context
        )
        
        # Process through tactile system
        response = await self.tactile_system.process_stimulus(stimulus)
        
        # Trigger emotional response based on perceived intensity
        if response.perceived_intensity > 7:
            # Strong touch
            if emotional_context == "comfort":
                self.emotional_system.set_emotion_from_basic(BasicEmotion.LOVE, 0.6)
            else:
                self.emotional_system.set_emotion_from_basic(BasicEmotion.SURPRISE, 0.5)
        
        # Trigger oxytocin for positive touch
        if emotional_context in ["comfort", "love", "joy"]:
            await self.endocrine_system.adjust_hormone(HormoneType.OXYTOCIN, 15.0 * intensity)
    
    def get_biological_state(self) -> Dict[str, Any]:
        """Get comprehensive integrated biological state"""
        # Get individual system states
        nervous_state = self.nervous_system.get_system_summary()
        endocrine_effects = self.endocrine_system.calculate_systemic_effects()
        emotional_summary = self.emotional_system.get_emotion_summary()
        
        dominant_emotion, confidence = self.emotional_system.get_dominant_emotion()
        
        return {
            "arousal": self.nervous_system.arousal_level,
            "sympathetic_tone": self.nervous_system.sympathetic_tone,
            "parasympathetic_tone": self.nervous_system.parasympathetic_tone,
            "dominant_emotion": dominant_emotion.en_name if dominant_emotion else "unknown",
            "emotion_confidence": confidence,
            "hormonal_effects": endocrine_effects,
            "stress_level": self.endocrine_system.stress_level,
            "physiological": {
                "heart_rate": nervous_state["physiological"]["heart_rate"],
                "blood_pressure": nervous_state["physiological"]["blood_pressure"],
            },
            "mood": emotional_summary["pad_state"]["pleasure"],
            "timestamp": datetime.now().isoformat()
        }
    
    def register_state_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for integrated state updates"""
        self._state_callbacks.append(callback)
    
    def get_system_by_name(self, name: str) -> Any:
        """Get a biological system by name"""
        systems = {
            "tactile": self.tactile_system,
            "endocrine": self.endocrine_system,
            "nervous": self.nervous_system,
            "neuroplasticity": self.neuroplasticity_system,
            "emotional": self.emotional_system,
        }
        return systems.get(name)
    
    async def _handle_system_interaction(
        self,
        source_system: str,
        target_system: str,
        interaction_type: str,
        intensity: float
    ) -> Dict[str, Any]:
        """
        处理生物系统间的实际协调逻辑 / Handle actual coordination logic between biological systems
        
        实现以下生理-内分泌-情绪系统间的相互影响：
        - 生理系统影响内分泌系统（压力反应）
        - 内分泌系统影响情绪系统（激素效应）
        - 自主神经系统调节生理状态（唤醒水平）
        - 添加激素对情绪的具体影响计算
        - 添加神经激活对生理参数的影响
        
        Implements the following physiological-endocrine-emotional system interactions:
        - Physiological system affects endocrine system (stress response)
        - Endocrine system affects emotional system (hormonal effects)
        - Autonomic nervous system regulates physiological state (arousal level)
        - Specific calculations for hormone effects on emotions
        - Neural activation effects on physiological parameters
        
        Args:
            source_system: Source biological system name (nervous, endocrine, tactile, emotional)
            target_system: Target biological system name
            interaction_type: Type of interaction (e.g., 'arousal_to_adrenaline', 'hormonal_mood')
            intensity: Influence strength (0-1)
            
        Returns:
            Dict containing interaction results and system state changes
            
        Example:
            >>> result = await integrator._handle_system_interaction(
            ...     "nervous", "endocrine", "arousal_to_adrenaline", 0.8
            ... )
            >>> print(f"Hormone change: {result['hormone_change']:.2f}")
        """
        results = {
            "source": source_system,
            "target": target_system,
            "interaction_type": interaction_type,
            "intensity": intensity,
            "changes": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Get source and target system instances
            source = self.get_system_by_name(source_system)
            target = self.get_system_by_name(target_system)
            
            if not source or not target:
                results["error"] = f"System not found: {source_system} or {target_system}"
                return results
            
            # 1. 生理系统影响内分泌系统 / Physiological system affects endocrine system
            if interaction_type == "arousal_to_adrenaline" and source_system == "nervous":
                # Calculate adrenaline release based on arousal level
                arousal = getattr(source, 'arousal_level', 50.0)
                adrenaline_increase = (arousal / 100.0) * intensity * 25.0  # Max 25 unit increase
                
                if hasattr(target, 'adjust_hormone'):
                    await target.adjust_hormone(HormoneType.ADRENALINE, adrenaline_increase)
                    results["changes"]["adrenaline"] = f"+{adrenaline_increase:.1f}"
                    
                    # Trigger cortisol for sustained arousal
                    if arousal > 60:
                        cortisol_increase = ((arousal - 60) / 40.0) * intensity * 15.0
                        await target.adjust_hormone(HormoneType.CORTISOL, cortisol_increase)
                        results["changes"]["cortisol"] = f"+{cortisol_increase:.1f}"
            
            # 2. 内分泌系统影响情绪系统 / Endocrine system affects emotional system
            elif interaction_type == "hormonal_mood" and source_system == "endocrine":
                # Calculate emotional influence from hormone levels
                hormone_effects = {}
                
                if hasattr(source, 'get_hormone_level'):
                    # Dopamine effect on pleasure/joy
                    dopamine = source.get_hormone_level(HormoneType.DOPAMINE)
                    dopamine_normalized = (dopamine - 20) / 80  # Normalize to -0.25 to 1.0
                    hormone_effects["pleasure"] = dopamine_normalized * intensity * 0.6
                    
                    # Serotonin effect on mood stability
                    serotonin = source.get_hormone_level(HormoneType.SEROTONIN)
                    serotonin_normalized = (serotonin - 30) / 70
                    hormone_effects["mood_stability"] = serotonin_normalized * intensity * 0.5
                    
                    # Adrenaline effect on arousal/anxiety
                    adrenaline = source.get_hormone_level(HormoneType.ADRENALINE)
                    if adrenaline > 50:
                        hormone_effects["anxiety"] = ((adrenaline - 50) / 50) * intensity * 0.7
                    
                    # Oxytocin effect on bonding/trust
                    oxytocin = source.get_hormone_level(HormoneType.OXYTOCIN)
                    if oxytocin > 40:
                        hormone_effects["trust"] = ((oxytocin - 40) / 60) * intensity * 0.5
                    
                    # Cortisol effect on stress/negative mood
                    cortisol = source.get_hormone_level(HormoneType.CORTISOL)
                    if cortisol > 30:
                        hormone_effects["stress"] = ((cortisol - 30) / 70) * intensity * 0.8
                
                # Apply emotional influence
                if hasattr(target, 'apply_influence'):
                    for emotion, value in hormone_effects.items():
                        if abs(value) > 0.1:  # Only apply significant effects
                            target.apply_influence("hormonal", emotion, value, intensity)
                
                results["changes"]["emotional_influences"] = hormone_effects
            
            # 3. 自主神经系统调节生理状态 / Autonomic nervous system regulates physiological state
            elif interaction_type == "emotion_to_arousal" and source_system == "emotional":
                # Calculate arousal change from emotional state
                if hasattr(source, 'get_dominant_emotion'):
                    emotion, confidence = source.get_dominant_emotion()
                    if emotion:
                        # Emotion arousal affects nervous system
                        arousal_impact = emotion.arousal * 30 * intensity  # -30 to +30
                        
                        if hasattr(target, 'arousal_level') and hasattr(target, 'set_arousal_directly'):
                            current_arousal = target.arousal_level
                            new_arousal = max(0, min(100, current_arousal + arousal_impact))
                            target.set_arousal_directly(new_arousal)
                            results["changes"]["arousal"] = f"{new_arousal - current_arousal:+.1f}"
                            
                            # High arousal triggers sympathetic activation
                            if new_arousal > 70 and hasattr(target, 'apply_stimulus'):
                                await target.apply_stimulus(
                                    "emotional_arousal",
                                    NerveType.SYMPATHETIC,
                                    (new_arousal - 70) / 30,
                                    5.0
                                )
            
            # 4. 触觉系统影响情绪系统 / Tactile system affects emotional system
            elif interaction_type == "touch_to_emotion" and source_system == "tactile":
                # Calculate emotional response from tactile input
                if hasattr(source, 'get_sensitivity_level'):
                    sensitivity = source.get_sensitivity_level()
                    
                    # High sensitivity increases emotional response
                    if sensitivity > 0.6 and hasattr(target, 'apply_influence'):
                        target.apply_influence("tactile", "sensitivity", sensitivity * intensity, 0.5)
                        results["changes"]["tactile_sensitivity"] = f"{sensitivity * intensity:.2f}"
            
            # 5. 压力激素影响神经可塑性 / Stress hormones affect neuroplasticity
            elif interaction_type == "cortisol_to_memory" and source_system == "endocrine":
                # Cortisol can impair memory formation under chronic stress
                if hasattr(source, 'get_hormone_level'):
                    cortisol = source.get_hormone_level(HormoneType.CORTISOL)
                    
                    if cortisol > 50 and hasattr(target, 'set_learning_rate'):
                        # High cortisol reduces learning rate
                        learning_impairment = ((cortisol - 50) / 50) * intensity * 0.4
                        target.set_learning_rate(1.0 - learning_impairment)
                        results["changes"]["learning_rate"] = f"{1.0 - learning_impairment:.2f}"
                        results["changes"]["stress_impact"] = "impaired"
                    elif hasattr(target, 'set_learning_rate'):
                        # Normal learning rate
                        target.set_learning_rate(1.0)
            
            # 6. 情绪记忆影响神经可塑性 / Emotional memories affect neuroplasticity
            elif interaction_type == "emotional_memory" and source_system == "emotional":
                # Emotional intensity enhances memory consolidation
                if hasattr(source, 'get_emotional_intensity'):
                    emotional_intensity = source.get_emotional_intensity()
                    
                    if emotional_intensity > 0.5 and hasattr(target, 'enhance_consolidation'):
                        # Strong emotions enhance memory consolidation
                        enhancement = (emotional_intensity - 0.5) * 2 * intensity * 0.3
                        target.enhance_consolidation(enhancement)
                        results["changes"]["consolidation_enhancement"] = f"+{enhancement:.2f}"
            
            # Log successful interaction
            results["status"] = "success"
            
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            results["status"] = "error"

            results["error"] = str(e)
            results["error_type"] = type(e).__name__
        
        return results
    
    async def execute_system_interaction(
        self,
        interaction: SystemInteraction,
        intensity: float = 0.5
    ) -> Dict[str, Any]:
        """
        执行预定义的系统交互 / Execute a predefined system interaction
        
        Args:
            interaction: SystemInteraction definition
            intensity: Influence intensity (0-1)
            
        Returns:
            Interaction results
        """
        return await self._handle_system_interaction(
            interaction.source_system,
            interaction.target_system,
            interaction.interaction_type,
            intensity * interaction.influence_strength
        )


# Example usage
if __name__ == "__main__":
    async def demo():
        integrator = BiologicalIntegrator()
        await integrator.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - 生物系统整合器演示")
        print("Biological Integrator Demo")
        print("=" * 60)
        
        # Show initial state
        print("\n初始生物状态 / Initial biological state:")
        state = integrator.get_biological_state()
        print(f"  唤醒水平: {state['arousal']:.1f}")
        print(f"  主要情绪: {state['dominant_emotion']}")
        
        # Process stress
        print("\n处理压力事件 / Processing stress event:")
        await integrator.process_stress_event(intensity=0.7)
        await asyncio.sleep(1)
        
        state = integrator.get_biological_state()
        print(f"  唤醒水平: {state['arousal']:.1f}")
        print(f"  压力水平: {state['stress_level']:.2f}")
        print(f"  心率: {state['physiological']['heart_rate']:.0f}")
        
        # Process relaxation
        print("\n处理放松事件 / Processing relaxation event:")
        await integrator.process_relaxation_event(intensity=0.6)
        await asyncio.sleep(1)
        
        state = integrator.get_biological_state()
        print(f"  唤醒水平: {state['arousal']:.1f}")
        print(f"  情绪: {state['dominant_emotion']}")
        
        await integrator.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
