"""
Angela AI v6.0 - Physiological Tactile System
生理触觉系统主处理器

Main tactile processing system class with receptor management,
stimulus processing, and Live2D integration.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.system.config.magic_numbers import cache_value, loop_sleep

from .physiological_tactile_types import (
    BODY_TO_LIVE2D_MAPPING,
    BodyPart,
    BodyRegion,
    EmotionalTactileMapping,
    Live2DTouchResponse,
    Receptor,
    ReceptorType,
    TactileResponse,
    TactileStimulus,
    TactileType,
)

logger = logging.getLogger(__name__)


class PhysiologicalTactileSystem:
    """
    生理触觉系统主类 / Main physiological tactile system class

    Simulates a comprehensive tactile system with 6 receptor types across 18 body parts.
    Implements dynamic sensitivity modulation based on arousal state and emotional context.

    Attributes:
        receptors: Dictionary mapping body parts to their receptor arrays
        arousal_level: Current arousal state (0-100)
        active_stimuli: Currently active tactile stimuli
        emotional_mappings: Mapping between emotions and tactile preferences

    Example:
        >>> system = PhysiologicalTactileSystem()
        >>> await system.initialize()
        >>>
        >>> # Create a touch stimulus
        >>> stimulus = TactileStimulus(
        ...     tactile_type=TactileType.LIGHT_TOUCH,
        ...     intensity=5.0,
        ...     location=BodyPart.HANDS,
        ...     duration=2.0
        ... )
        >>>
        >>> # Process the stimulus
        >>> response = await system.process_stimulus(stimulus)
        >>> print(f"Perceived intensity: {response.perceived_intensity}")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.receptors: Dict[BodyPart, List[Receptor]] = {}
        self.arousal_level: float = 50.0  # 0-100
        self.active_stimuli: List[TactileStimulus] = []
        self.emotional_mappings: Dict[str, EmotionalTactileMapping] = {}
        self._stimulus_history: List[TactileStimulus] = []
        self._max_history_size = cache_value("tactile_history", 1000)
        self._running = False
        self._update_task: Optional[asyncio.Task] = None

        # Callbacks for various events
        self._on_stimulus_callbacks: List[Callable[[TactileStimulus], None]] = []
        self._on_threshold_callbacks: Dict[BodyPart, List[Callable[[float], None]]] = {}

        self._initialize_receptors()
        self._initialize_emotional_mappings()

    def _initialize_receptors(self) -> None:
        """初始化所有身体部位的受体"""
        receptor_configs = {
            ReceptorType.MEISSNER: {"density": 0.8, "adaptation": 0.9},
            ReceptorType.MERKEL: {"density": 0.6, "adaptation": 0.2},
            ReceptorType.PACINIAN: {"density": 0.4, "adaptation": 0.8},
            ReceptorType.RUFFINI: {"density": 0.3, "adaptation": 0.3},
            ReceptorType.FREE_NERVE: {"density": 1.0, "adaptation": 0.1},
            ReceptorType.HAIR_FOLLICLE: {"density": 0.7, "adaptation": 0.7},
        }

        # Define receptor distribution per body part
        distribution = {
            BodyPart.HANDS: [
                ReceptorType.MEISSNER,
                ReceptorType.MERKEL,
                ReceptorType.PACINIAN,
                ReceptorType.FREE_NERVE,
            ],
            BodyPart.FINGERS: [ReceptorType.MEISSNER, ReceptorType.MERKEL, ReceptorType.PACINIAN],
            BodyPart.FACE: [
                ReceptorType.MEISSNER,
                ReceptorType.FREE_NERVE,
                ReceptorType.HAIR_FOLLICLE,
            ],
            BodyPart.FEET: [ReceptorType.MEISSNER, ReceptorType.PACINIAN, ReceptorType.FREE_NERVE],
            BodyPart.FOREHEAD: [ReceptorType.MEISSNER, ReceptorType.FREE_NERVE],
            BodyPart.NECK: [ReceptorType.RUFFINI, ReceptorType.FREE_NERVE],
            BodyPart.FOREARMS: [ReceptorType.MEISSNER, ReceptorType.PACINIAN, ReceptorType.RUFFINI],
            BodyPart.UPPER_ARMS: [ReceptorType.PACINIAN, ReceptorType.RUFFINI],
            BodyPart.SHOULDERS: [ReceptorType.RUFFINI, ReceptorType.FREE_NERVE],
            BodyPart.CHEST: [ReceptorType.FREE_NERVE, ReceptorType.RUFFINI],
            BodyPart.BACK: [ReceptorType.FREE_NERVE, ReceptorType.RUFFINI],
            BodyPart.ABDOMEN: [ReceptorType.FREE_NERVE],
            BodyPart.WAIST: [ReceptorType.FREE_NERVE, ReceptorType.RUFFINI],
            BodyPart.HIPS: [ReceptorType.PACINIAN, ReceptorType.RUFFINI],
            BodyPart.THIGHS: [ReceptorType.PACINIAN, ReceptorType.RUFFINI],
            BodyPart.KNEES: [ReceptorType.FREE_NERVE, ReceptorType.PACINIAN],
            BodyPart.CALVES: [ReceptorType.PACINIAN, ReceptorType.FREE_NERVE],
            BodyPart.TOP_OF_HEAD: [ReceptorType.HAIR_FOLLICLE, ReceptorType.FREE_NERVE],
        }

        for body_part in BodyPart:
            self.receptors[body_part] = []
            receptor_types = distribution.get(body_part, [ReceptorType.FREE_NERVE])

            for r_type in receptor_types:
                config = receptor_configs[r_type]
                receptor = Receptor(
                    receptor_type=r_type,
                    body_part=body_part,
                    density=config["density"] * body_part.base_sensitivity,
                    sensitivity=body_part.base_sensitivity,
                    adaptation_rate=config["adaptation"],
                )
                self.receptors[body_part].append(receptor)

    def _initialize_emotional_mappings(self) -> None:
        """初始化情绪-触觉映射"""
        self.emotional_mappings = {
            "joy": EmotionalTactileMapping(
                emotion="joy",
                associated_tactile=[TactileType.LIGHT_TOUCH, TactileType.TEMPERATURE],
                intensity_modifier=1.2,
                preferred_locations=[BodyPart.HANDS, BodyPart.FACE],
            ),
            "comfort": EmotionalTactileMapping(
                emotion="comfort",
                associated_tactile=[TactileType.LIGHT_TOUCH, TactileType.PRESSURE],
                intensity_modifier=0.9,
                preferred_locations=[BodyPart.BACK, BodyPart.SHOULDERS, BodyPart.HANDS],
            ),
            "anxiety": EmotionalTactileMapping(
                emotion="anxiety",
                associated_tactile=[TactileType.TEMPERATURE, TactileType.PAIN],
                intensity_modifier=1.5,
                preferred_locations=[BodyPart.CHEST, BodyPart.ABDOMEN, BodyPart.HANDS],
            ),
            "relaxation": EmotionalTactileMapping(
                emotion="relaxation",
                associated_tactile=[TactileType.PRESSURE, TactileType.TEMPERATURE],
                intensity_modifier=0.7,
                preferred_locations=[BodyPart.BACK, BodyPart.SHOULDERS, BodyPart.NECK],
            ),
            "excitement": EmotionalTactileMapping(
                emotion="excitement",
                associated_tactile=[TactileType.VIBRATION, TactileType.LIGHT_TOUCH],
                intensity_modifier=1.3,
                preferred_locations=[BodyPart.HANDS, BodyPart.FACE, BodyPart.FOREARMS],
            ),
            "sadness": EmotionalTactileMapping(
                emotion="sadness",
                associated_tactile=[TactileType.TEMPERATURE, TactileType.PRESSURE],
                intensity_modifier=0.8,
                preferred_locations=[BodyPart.SHOULDERS, BodyPart.BACK],
            ),
            "anger": EmotionalTactileMapping(
                emotion="anger",
                associated_tactile=[TactileType.PAIN, TactileType.TEMPERATURE],
                intensity_modifier=1.4,
                preferred_locations=[BodyPart.HANDS, BodyPart.FACE, BodyPart.CHEST],
            ),
        }

    async def initialize(self) -> None:
        """Initialize the tactile system"""
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())

    async def shutdown(self) -> None:
        """Shutdown the tactile system"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                logger.debug("Update task cancelled during shutdown")

    async def _update_loop(self) -> None:
        """Background update loop for receptor adaptation"""
        while self._running:
            try:
                await self._adapt_receptors()
                await self._decay_stimuli()
                await asyncio.sleep(loop_sleep("tactile_update", 0.1))  # 100ms update interval
            except Exception as e:  # broad exception acceptable: tactile update loop must be resilient
                logger.error("Physiological tactile update loop error: %s", e, exc_info=True)
                await asyncio.sleep(loop_sleep("tactile_update", 0.1))

    async def _adapt_receptors(self) -> None:
        """Adapt receptor sensitivity based on continuous stimulation"""
        for body_part, receptors in self.receptors.items():
            for receptor in receptors:
                if receptor.last_stimulus:
                    time_since = (datetime.now() - receptor.last_stimulus).total_seconds()
                    if time_since > 0:
                        # Adaptation formula: exponential decay
                        receptor.current_activation *= 1 - receptor.adaptation_rate * 0.1
                        if receptor.current_activation < 0.01:
                            receptor.current_activation = 0.0

    async def _decay_stimuli(self) -> None:
        """Decay active stimuli over time"""
        current_time = datetime.now()
        remaining_stimuli = []

        for stimulus in self.active_stimuli:
            elapsed = (current_time - stimulus.timestamp).total_seconds()
            if elapsed < stimulus.duration:
                remaining_stimuli.append(stimulus)

        self.active_stimuli = remaining_stimuli

    def set_arousal_level(self, level: float) -> None:
        """
        Set the arousal level which affects tactile sensitivity

        Args:
            level: Arousal level from 0 (deeply relaxed) to 100 (highly aroused)
        """
        self.arousal_level = max(0.0, min(100.0, level))
        self._update_sensitivities()

    def _update_sensitivities(self) -> None:
        """Update receptor sensitivities based on arousal"""
        # Higher arousal = increased sensitivity for most receptors
        arousal_factor = 0.5 + (self.arousal_level / 100.0) * 1.0

        for body_part, receptors in self.receptors.items():
            for receptor in receptors:
                base = body_part.base_sensitivity
                # Pain receptors are more sensitive at high arousal
                if receptor.receptor_type == ReceptorType.FREE_NERVE:
                    receptor.sensitivity = base * arousal_factor * 1.2
                else:
                    receptor.sensitivity = base * arousal_factor

    async def process_stimulus(self, stimulus: TactileStimulus) -> "TactileResponse":
        """
        Process a tactile stimulus and generate a response

        Args:
            stimulus: The tactile stimulus to process

        Returns:
            TactileResponse: The system's response to the stimulus
        """
        # Add to history
        self._stimulus_history.append(stimulus)
        if len(self._stimulus_history) > self._max_history_size:
            self._stimulus_history.pop(0)

        # Add to active stimuli
        self.active_stimuli.append(stimulus)

        # Calculate perceived intensity
        location_receptors = self.receptors.get(stimulus.location, [])
        relevant_receptors = [
            r for r in location_receptors if r.receptor_type in stimulus.receptor_types
        ]

        if not relevant_receptors:
            relevant_receptors = location_receptors

        # Calculate activation
        total_activation = 0.0
        max_density = 0.0

        for receptor in relevant_receptors:
            activation = stimulus.intensity * receptor.sensitivity * receptor.density
            receptor.current_activation = max(receptor.current_activation, activation)
            receptor.last_stimulus = datetime.now()
            total_activation += activation
            max_density += receptor.density

        # Normalize by receptor density
        if max_density > 0:
            perceived_intensity = total_activation / max_density
        else:
            perceived_intensity = stimulus.intensity

        # Apply emotional modulation
        if stimulus.emotional_tag and stimulus.emotional_tag in self.emotional_mappings:
            mapping = self.emotional_mappings[stimulus.emotional_tag]
            perceived_intensity *= mapping.intensity_modifier

        # Trigger callbacks
        for callback in self._on_stimulus_callbacks:
            try:
                callback(stimulus)
            except Exception as e:  # broad exception acceptable: stimulus callbacks should not break stimulus processing
                logger.error(f"Error in {__name__}: {e}", exc_info=True)

        # Check thresholds
        self._check_thresholds(stimulus.location, perceived_intensity)

        return TactileResponse(
            stimulus=stimulus,
            perceived_intensity=min(10.0, perceived_intensity),
            activated_receptors=len(relevant_receptors),
            duration=stimulus.duration,
            timestamp=datetime.now(),
            spatial_token=(*stimulus.location.coordinate, datetime.now().timestamp())
        )

    def _check_thresholds(self, body_part: BodyPart, intensity: float) -> None:
        """Check if any thresholds are exceeded"""
        if body_part in self._on_threshold_callbacks:
            for callback in self._on_threshold_callbacks[body_part]:
                try:
                    callback(intensity)
                except Exception as e:  # broad exception acceptable: threshold callbacks should not break threshold checking
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)

    def register_stimulus_callback(self, callback: Callable[[TactileStimulus], None]) -> None:
        """Register a callback for stimulus events"""
        self._on_stimulus_callbacks.append(callback)

    def register_threshold_callback(self, body_part: BodyPart, callback: Callable[[float], None]) -> None:
        """Register a callback for threshold events on a specific body part"""
        if body_part not in self._on_threshold_callbacks:
            self._on_threshold_callbacks[body_part] = []
        self._on_threshold_callbacks[body_part].append(callback)

    def get_body_part_sensitivity(self, body_part: BodyPart) -> float:
        """Get current sensitivity for a body part"""
        receptors = self.receptors.get(body_part, [])
        if not receptors:
            return 0.0
        return sum(r.sensitivity for r in receptors) / len(receptors)

    def get_active_stimuli_by_location(self, location: BodyPart) -> List[TactileStimulus]:
        """Get all active stimuli for a specific body part"""
        return [s for s in self.active_stimuli if s.location == location]

    def get_receptor_status(self, body_part: BodyPart) -> Dict[ReceptorType, float]:
        """Get current activation status of receptors for a body part"""
        receptors = self.receptors.get(body_part, [])
        return {r.receptor_type: r.current_activation for r in receptors}

    def apply_emotional_context(self, emotion: str, intensity: float = 1.0) -> None:
        """
        Apply emotional context to tactile processing

        Args:
            emotion: Emotion name
            intensity: Emotional intensity (0-1)
        """
        if emotion in self.emotional_mappings:
            mapping = self.emotional_mappings[emotion]
            # Temporarily increase sensitivity for preferred locations
            for location in mapping.preferred_locations:
                for receptor in self.receptors.get(location, []):
                    receptor.sensitivity *= 1 + 0.3 * intensity

    # Live2D Integration Methods
    def get_live2d_response_for_touch(
        self, body_part: BodyPart, touch_type: str = "pat", intensity: float = 0.5
    ) -> Dict[str, float]:
        """
        Get Live2D parameter response for a body touch

        Args:
            body_part: Body part being touched
            touch_type: Type of touch (pat, stroke, poke, pinch, etc.)
            intensity: Touch intensity (0-1)

        Returns:
            Dictionary of Live2D parameter names to values
        """
        body_part.name.lower()

        # Map BodyPart enum names to mapping keys
        mapping_key = self._get_body_part_mapping_key(body_part)

        if mapping_key not in BODY_TO_LIVE2D_MAPPING:
            return {}

        part_mapping = BODY_TO_LIVE2D_MAPPING[mapping_key]

        # Get touch response (default to "pat" if touch type not found)
        touch_mapping = part_mapping.get(touch_type, part_mapping.get("pat", {}))

        # Calculate parameter values based on intensity
        live2d_params = {}
        for param_name, (min_val, max_val) in touch_mapping.items():
            # Interpolate based on intensity
            value = min_val + (max_val - min_val) * intensity

            # Apply body part sensitivity
            sensitivity = body_part.base_sensitivity
            value = value * sensitivity

            live2d_params[param_name] = value

        return live2d_params

    def _get_body_part_mapping_key(self, body_part: BodyPart) -> str:
        """Map BodyPart enum to BODY_TO_LIVE2D_MAPPING keys"""
        mapping = {
            BodyPart.TOP_OF_HEAD: "top_of_head",
            BodyPart.FOREHEAD: "forehead",
            BodyPart.FACE: "face",
            BodyPart.NECK: "neck",
            BodyPart.CHEST: "chest",
            BodyPart.BACK: "back",
            BodyPart.ABDOMEN: "abdomen",
            BodyPart.WAIST: "waist",
            BodyPart.HIPS: "hips",
            BodyPart.THIGHS: "thighs",
            BodyPart.SHOULDERS: "shoulders",
            BodyPart.UPPER_ARMS: "upper_arms",
            BodyPart.FOREARMS: "forearms",
            BodyPart.HANDS: "hands",
            BodyPart.FINGERS: "fingers",
            BodyPart.KNEES: "knees",
            BodyPart.CALVES: "calves",
            BodyPart.FEET: "feet",
        }
        return mapping.get(body_part, body_part.name.lower())

    async def process_stimulus_with_live2d(
        self, stimulus: TactileStimulus, touch_type: str = "pat"
    ) -> TactileResponse:
        """
        Process tactile stimulus and return response with Live2D parameters

        Args:
            stimulus: Tactile stimulus
            touch_type: Type of touch interaction

        Returns:
            TactileResponse with live2d_parameters
        """
        # Process normally first
        response = await self.process_stimulus(stimulus)

        # Add Live2D parameters
        intensity = stimulus.intensity / 10.0  # Normalize to 0-1
        live2d_params = self.get_live2d_response_for_touch(stimulus.location, touch_type, intensity)

        # Add emotional modifiers
        if stimulus.emotional_tag:
            live2d_params = self._apply_emotional_to_live2d(
                live2d_params, stimulus.emotional_tag, intensity
            )

        response.live2d_parameters = live2d_params

        return response

    def _apply_emotional_to_live2d(
        self, params: Dict[str, float], emotion: str, intensity: float
    ) -> Dict[str, float]:
        """Apply emotional context to Live2D parameters"""
        modified = params.copy()

        # Emotion-specific parameter adjustments
        emotion_modifiers = {
            "joy": {"ParamCheek": 0.3, "ParamEyeLSmile": 0.5, "ParamEyeRSmile": 0.5},
            "comfort": {"ParamEyeLOpen": -0.1, "ParamEyeROpen": -0.1, "ParamCheek": 0.2},
            "anxiety": {"ParamBrowLY": 0.3, "ParamBrowRY": 0.3, "ParamEyeLOpen": 0.2},
            "relaxation": {"ParamEyeLOpen": -0.2, "ParamEyeROpen": -0.2, "ParamBreath": 0.3},
            "excitement": {"ParamEyeLOpen": 0.2, "ParamEyeROpen": 0.2, "ParamCheek": 0.4},
            "sadness": {"ParamBrowLY": -0.3, "ParamBrowRY": -0.3, "ParamMouthForm": -0.3},
            "anger": {"ParamBrowLAngle": 0.5, "ParamBrowRAngle": 0.5, "ParamEyeLOpen": 0.1},
            "love": {"ParamCheek": 0.6, "ParamEyeLSmile": 0.6, "ParamEyeRSmile": 0.6},
        }

        if emotion in emotion_modifiers:
            for param, modifier in emotion_modifiers[emotion].items():
                if param in modified:
                    modified[param] = max(-1.0, min(1.0, modified[param] + modifier * intensity))
                else:
                    modified[param] = modifier * intensity

        return modified

    def get_all_body_live2d_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Get all body part to Live2D mappings"""
        return BODY_TO_LIVE2D_MAPPING.copy()

    def get_live2d_touch_zones(self) -> List[Dict[str, Any]]:
        """
        Get touch zone definitions for Live2D integration

        Returns:
            List of touch zone definitions with body parts and parameters
        """
        zones = []

        for body_part in BodyPart:
            mapping_key = self._get_body_part_mapping_key(body_part)

            if mapping_key in BODY_TO_LIVE2D_MAPPING:
                part_mapping = BODY_TO_LIVE2D_MAPPING[mapping_key]

                # Collect all parameters for this body part
                all_params = set()
                for touch_type, params in part_mapping.items():
                    all_params.update(params.keys())

                zones.append(
                    {
                        "body_part": body_part.name,
                        "cn_name": body_part.cn_name,
                        "sensitivity": body_part.base_sensitivity,
                        "touch_types": list(part_mapping.keys()),
                        "parameters": list(all_params),
                        "region": body_part.region.name,
                    }
                )

        return zones
