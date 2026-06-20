"""
Tactile Service - Physical touch simulation and feedback.

Bridges REST/WebSocket tactile endpoints to the physiological tactile system
when available, with a backward-compatible mock fallback.

ANGELA-MATRIX: L6[执行层] αγ [A] L2+
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Map common body part strings to physiological_tactile_types BodyPart enum values
_BODY_PART_MAP = {
    "hands": "HANDS",
    "hand": "HANDS",
    "fingers": "FINGERS",
    "finger": "FINGERS",
    "face": "FACE",
    "forehead": "FOREHEAD",
    "neck": "NECK",
    "forearms": "FOREARMS",
    "forearm": "FOREARMS",
    "upper_arms": "UPPER_ARMS",
    "upperarm": "UPPER_ARMS",
    "shoulders": "SHOULDERS",
    "shoulder": "SHOULDERS",
    "chest": "CHEST",
    "back": "BACK",
    "abdomen": "ABDOMEN",
    "waist": "WAIST",
    "hips": "HIPS",
    "hip": "HIPS",
    "thighs": "THIGHS",
    "thigh": "THIGHS",
    "knees": "KNEES",
    "knee": "KNEES",
    "calves": "CALVES",
    "calf": "CALVES",
    "feet": "FEET",
    "foot": "FEET",
    "top_of_head": "TOP_OF_HEAD",
    "head": "TOP_OF_HEAD",
    "generic": "HANDS",
}

# Map tactile type strings to TactileType enum values
_TACTILE_TYPE_MAP = {
    "light_touch": "LIGHT_TOUCH",
    "touch": "LIGHT_TOUCH",
    "pressure": "PRESSURE",
    "temperature": "TEMPERATURE",
    "vibration": "VIBRATION",
    "pain": "PAIN",
    "itch": "ITCH",
    "pat": "LIGHT_TOUCH",
    "stroke": "LIGHT_TOUCH",
    "poke": "PRESSURE",
    "pinch": "PRESSURE",
}


class TactileService:
    """Service for tactile touch simulation and biological feedback.

    When *physiological_system* is provided, delegates to
    ``PhysiologicalTactileSystem`` for realistic simulation; otherwise
    falls back to a simple mock.
    """

    def __init__(self, config: dict = None, physiological_system: Any = None):
        self.config = config or {}
        self.enabled = True
        self._physio = physiological_system
        logger.info(
            "TactileService initialized (physio_system=%s)",
            "available" if physiological_system else "mock",
        )

    async def model_object_tactile(self, visual_data: Dict[str, Any]) -> Dict[str, Any]:
        object_id = visual_data.get("object_id", visual_data.get("id", "unknown_obj"))
        return {
            "object_id": object_id,
            "tactile_properties": visual_data.get("features", visual_data),
        }

    async def simulate_touch(
        self,
        object_id: str,
        contact_point: Dict[str, Any],
        origin: str = "System",
    ) -> Dict[str, Any]:
        """Simulate a tactile touch event and return biological feedback."""
        body_part_str = contact_point.get("body_part", "generic")
        pressure = contact_point.get("pressure", 0.5)
        touch_type = contact_point.get("touch_type", "touch")
        logger.info(
            "simulate_touch: object=%s, body_part=%s, pressure=%s",
            object_id, body_part_str, pressure,
        )

        if self._physio is not None:
            try:
                return await self._simulate_via_physio(body_part_str, pressure, touch_type, object_id, origin)
            except Exception as e:
                logger.warning("Physio tactile failed, falling back to mock: %s", e)

        # Fallback mock
        return {
            "object_id": object_id,
            "status": "processed",
            "reflex": "withdrawal" if pressure > 0.8 else "normal",
            "feedback": {
                "intensity": min(1.0, pressure * 1.2),
                "texture": "smooth",
                "temperature": 36.5,
            },
        }

    async def _simulate_via_physio(
        self,
        body_part_str: str,
        pressure: float,
        touch_type: str,
        object_id: str,
        origin: str,
    ) -> Dict[str, Any]:
        from core.bio.physiological_tactile_types import BodyPart, TactileType, TactileStimulus

        key = _BODY_PART_MAP.get(body_part_str.lower(), "HANDS")
        bp = BodyPart[key]
        tt_key = _TACTILE_TYPE_MAP.get(touch_type, "LIGHT_TOUCH")
        tt = TactileType[tt_key]

        stimulus = TactileStimulus(
            tactile_type=tt,
            intensity=pressure * 10.0,
            location=bp,
            duration=1.0,
        )
        response = await self._physio.process_stimulus(stimulus)
        return {
            "object_id": object_id,
            "status": "processed",
            "reflex": "withdrawal" if response.perceived_intensity > 7.0 else "normal",
            "feedback": {
                "intensity": round(min(1.0, response.perceived_intensity / 10.0), 3),
                "texture": "smooth",
                "temperature": 36.5,
                "perceived_intensity": round(response.perceived_intensity, 3),
                "activated_receptors": response.activated_receptors,
            },
        }

    async def model_tactile_feedback(self, visual_data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.model_object_tactile(visual_data)

    async def trigger_physical_feedback(
        self, device_id: str, intensity: float, pattern: str,
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {"status": "disabled"}
        if self._physio is not None:
            try:
                from core.bio.physiological_tactile_types import BodyPart, TactileType, TactileStimulus
                stimulus = TactileStimulus(
                    tactile_type=TactileType.VIBRATION,
                    intensity=min(10.0, intensity * 10.0),
                    location=BodyPart.HANDS,
                    duration=min(5.0, len(pattern) * 0.5),
                )
                await self._physio.process_stimulus(stimulus)
            except Exception as e:
                logger.warning("Physio feedback failed: %s", e)
        return {
            "status": "success",
            "device_id": device_id,
            "pattern": pattern,
        }

    async def process(self, input_data: Any) -> Dict[str, Any]:
        return {"error": "Invalid input format for tactile processing"}
