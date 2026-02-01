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
        self._homeostatic_targets = {
            "arousal": 50.0,
            "stress": 20.0,
            "mood": 0.6,
        }
        
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
        """Background loop for system integration"""
        while self._running:
            await self._apply_homeostasis()
            await self._synchronize_states()
            await asyncio.sleep(5)  # Update every 5 seconds
    
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
            except Exception:
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
