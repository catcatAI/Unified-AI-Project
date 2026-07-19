"""

Angela AI v6.0 - Trauma Memory System
创伤记忆系统

Manages traumatic memories with 70% slower forgetting rate.
Handles memory reactivation and intrusive recall.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.utils import safe_error

logger = logging.getLogger(__name__)

_MAX_PROCESSING_HISTORY = 300


@dataclass
class TraumaMemory:
    """创伤记忆 / Traumatic memory"""

    memory_id: str
    content: Any
    trauma_intensity: float  # 创伤强度 (0-1)
    encoding_timestamp: datetime = field(default_factory=datetime.now)
    reactivation_count: int = 0  # 重新激活次数

    def get_retention(self, current_time: Optional[datetime] = None) -> float:
        """
        计算创伤记忆保持率 / Calculate trauma memory retention

        创伤记忆以70%速度减缓遗忘
        Trauma memories fade 70% slower than normal memories
        """
        time = current_time or datetime.now()
        hours_since = (time - self.encoding_timestamp).total_seconds() / 3600.0

        # Normal forgetting: R = e^(-t/24)
        # Trauma forgetting: R = e^(-t/(24*1.7)) (70% slower = 1.7x stability)
        stability = 24.0 * 1.7
        retention = math.exp(-hours_since / stability)

        return retention


class TraumaMemorySystem:
    """
    创伤记忆系统 / Trauma Memory System

    Manages traumatic memories with 70% slower forgetting rate.
    Handles memory reactivation and intrusive recall.

    Trauma Characteristics:
    - High emotional intensity encoding
    - 70% slower forgetting (enhanced stability)
    - Easily reactivated by similar stimuli
    - Intrusive recall patterns

    Example:
        >>> trauma_system = TraumaMemorySystem()
        >>>
        >>> # Encode traumatic event
        >>> trauma = trauma_system.encode_trauma(
        ...     memory_id="trauma_001",
        ...     content="traumatic_event_description",
        ...     intensity=0.9
        ... )
        >>>
        >>> # Check retention over time (slower forgetting)
        >>> retention = trauma_system.get_retention("trauma_001")
        >>> print(f"Trauma retention: {retention:.2%}")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Trauma parameters
        self.trauma_intensity_threshold: float = self.config.get("intensity_threshold", 0.7)
        self.slowing_factor: float = 1.7  # 70% slower = 1.7x stability

        # Storage
        self.trauma_memories: Dict[str, TraumaMemory] = {}
        self.reactivation_triggers: Dict[str, List[str]] = {}

    def encode_trauma(
        self, memory_id: str, content: Any, intensity: float, timestamp: Optional[datetime] = None
    ) -> Optional[TraumaMemory]:
        """
        编码创伤记忆 / Encode a traumatic memory

        Args:
            memory_id: Unique memory identifier
            content: Memory content
            intensity: Trauma intensity (0-1, must exceed threshold)
            timestamp: Encoding timestamp

        Returns:
            TraumaMemory if intensity > threshold, None otherwise
        """
        if intensity < self.trauma_intensity_threshold:
            return None

        trauma = TraumaMemory(
            memory_id=memory_id,
            content=content,
            trauma_intensity=intensity,
            encoding_timestamp=timestamp or datetime.now(),
        )

        self.trauma_memories[memory_id] = trauma
        self.reactivation_triggers[memory_id] = []

        return trauma

    def get_retention(self, memory_id: str, current_time: Optional[datetime] = None) -> float:
        """
        获取创伤记忆保持率 / Get trauma memory retention

        Uses 70% slower forgetting curve.
        """
        if memory_id not in self.trauma_memories:
            return 0.0

        return self.trauma_memories[memory_id].get_retention(current_time)

    def reactivate(self, memory_id: str, trigger_context: str = "") -> bool:
        """
        重新激活创伤记忆 / Reactivate a traumatic memory

        Args:
            memory_id: Memory to reactivate
            trigger_context: Context that triggered reactivation

        Returns:
            True if reactivation occurred
        """
        if memory_id not in self.trauma_memories:
            return False

        trauma = self.trauma_memories[memory_id]
        trauma.reactivation_count += 1

        if trigger_context:
            self.reactivation_triggers[memory_id].append(trigger_context)

        return True

    def get_intrusion_likelihood(self, memory_id: str, current_stress: float = 0.5) -> float:
        """
        计算侵入性回忆可能性 / Calculate intrusive recall likelihood

        Higher when:
        - Memory has high trauma intensity
        - Memory has been reactivated many times
        - Current stress level is high
        """
        if memory_id not in self.trauma_memories:
            return 0.0

        trauma = self.trauma_memories[memory_id]

        # Base likelihood from trauma characteristics
        intensity_factor = trauma.trauma_intensity
        reactivation_factor = min(1.0, trauma.reactivation_count / 10.0)

        # Stress amplifies intrusion likelihood
        stress_factor = current_stress

        likelihood = intensity_factor * 0.4 + reactivation_factor * 0.3 + stress_factor * 0.3

        return min(1.0, likelihood)

    def get_all_trauma_memories(self) -> Dict[str, TraumaMemory]:
        """获取所有创伤记忆 / Get all trauma memories"""
        return self.trauma_memories.copy()

    def _process_trauma_reactivation(
        self,
        memory_id: str,
        trigger_context: str = "",
        current_stress_level: float = 0.5,
        coping_strategy: str = "default",
    ) -> Dict[str, Any]:
        """
        Process trauma memory reactivation — flashback handling, emotional
        regulation, over-activation prevention, and gradual extinction.

        Args:
            memory_id: Trauma memory identifier
            trigger_context: Context that caused reactivation
            current_stress_level: Current stress level (0-1)
            coping_strategy: "default", "grounding", "reframing",
                           "distraction", or "extinction"

        Returns:
            Dict with processing results including flashback intensity,
            regulation effectiveness, extinction progress.

        Raises:
            ValueError: If memory_id not found or strategy invalid
        """

        results = {
            "memory_id": memory_id,
            "reactivation_occurred": False,
            "flashback_intensity": 0.0,
            "emotional_regulation_applied": coping_strategy,
            "regulation_effectiveness": 0.0,
            "over_activation_prevented": False,
            "extinction_progress": 0.0,
            "recommended_actions": [],
            "timestamp": datetime.now().isoformat(),
        }

        try:
            trauma = self._validate_trauma_input(memory_id, coping_strategy)

            # 1. 计算闪回可能性 / Calculate flashback likelihood
            intrusion_likelihood = self.get_intrusion_likelihood(
                memory_id, current_stress=current_stress_level
            )

            # 2. 闪回处理 / Flashback handling
            self._handle_flashback(
                trauma,
                memory_id,
                trigger_context,
                intrusion_likelihood,
                current_stress_level,
                results,
            )

            # 3. 情感调节策略 / Emotional regulation strategies
            effectiveness = self._apply_emotional_regulation(
                coping_strategy, current_stress_level, results
            )

            # 4. 避免过度激活的机制 / Prevent over-activation mechanism
            self._prevent_over_activation(current_stress_level, results)

            # 5. 创伤记忆的逐步消退 / Gradual trauma extinction
            self._handle_trauma_extinction(trauma, coping_strategy, effectiveness, results)

            # 6. 生成推荐行动 / Generate recommended actions
            self._generate_recommended_actions(trauma, current_stress_level, results)

            # 7. 记录处理结果 / Log processing results
            self._log_processing_result(
                memory_id, trigger_context, current_stress_level, coping_strategy, results
            )

            results["status"] = "processed"

        except ValueError as e:
            results["status"] = "error"
            results["error"] = safe_error(e)
            results["error_type"] = "ValueError"
        except Exception as e:  # trauma processing must return safe fallback
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            results["status"] = "error"

            results["error"] = safe_error(e)
            results["error_type"] = type(e).__name__

        return results

    def _validate_trauma_input(self, memory_id: str, coping_strategy: str) -> str:
        """Validate trauma input."""
        if memory_id not in self.trauma_memories:
            raise ValueError(f"Trauma memory {memory_id} not found in system")
        valid_strategies = ["default", "grounding", "reframing", "distraction", "extinction"]
        if coping_strategy not in valid_strategies:
            raise ValueError(
                f"Invalid coping strategy: {coping_strategy}. "
                f"Must be one of: {valid_strategies}"
            )
        return self.trauma_memories[memory_id]

    def _handle_flashback(
        self,
        trauma,
        memory_id,
        trigger_context,
        intrusion_likelihood,
        current_stress_level,
        results,
    ) -> None:
        """Handle flashback request."""
        import math

        if intrusion_likelihood > 0.3:
            results["reactivation_occurred"] = True
            trauma.reactivation_count += 1
            if trigger_context:
                self.reactivation_triggers[memory_id].append(trigger_context)
            base_intensity = trauma.trauma_intensity
            reactivation_history_factor = min(1.0, trauma.reactivation_count / 20.0)
            stress_amplification = current_stress_level * 0.3
            if trauma.reactivation_count > 10:
                habituation_reduction = math.log10(trauma.reactivation_count) * 0.1
            else:
                habituation_reduction = 0.0
            flashback_intensity = min(
                1.0,
                base_intensity * (1 + reactivation_history_factor + stress_amplification)
                - habituation_reduction,
            )
            results["flashback_intensity"] = flashback_intensity
        else:
            results["flashback_intensity"] = 0.0

    def _apply_emotional_regulation(self, coping_strategy, current_stress_level, results) -> str:
        """Apply emotional regulation."""
        regulation_effects = {
            "default": 0.2,
            "grounding": 0.4,
            "reframing": 0.35,
            "distraction": 0.3,
            "extinction": 0.5,
        }
        base_regulation = regulation_effects.get(coping_strategy, 0.2)
        stress_impact = current_stress_level * 0.4
        effectiveness = max(0.0, base_regulation - stress_impact)
        results["regulation_effectiveness"] = effectiveness
        if results["reactivation_occurred"]:
            reduced_intensity = max(0.0, results["flashback_intensity"] - effectiveness)
            results["flashback_intensity"] = reduced_intensity
        return effectiveness

    def _prevent_over_activation(self, current_stress_level, results) -> None:
        """Prevent over activation."""
        if results["flashback_intensity"] > 0.7 and current_stress_level > 0.6:
            dampening = min(0.3, current_stress_level * 0.4)
            results["flashback_intensity"] = max(0.0, results["flashback_intensity"] - dampening)
            results["over_activation_prevented"] = True
            results["recommended_actions"].append("implement_grounding_protocol")
            results["recommended_actions"].append("reduce_stimuli")
        else:
            results["over_activation_prevented"] = False

    def _handle_trauma_extinction(self, trauma, coping_strategy, effectiveness, results) -> None:
        """Handle trauma extinction request."""
        if coping_strategy == "extinction":
            if results["reactivation_occurred"] and results["flashback_intensity"] < 0.5:
                extinction_boost = 0.05 + (effectiveness * 0.1)
                trauma.trauma_intensity = max(0.1, trauma.trauma_intensity - 0.02)
                results["extinction_progress"] = extinction_boost
                results["recommended_actions"].append("continue_extinction_therapy")
                results["recommended_actions"].append("track_extinction_progress")
            else:
                results["extinction_progress"] = 0.0
                results["recommended_actions"].append("reduce_intensity_before_extinction")
        else:
            if trauma.reactivation_count > 5 and results["flashback_intensity"] < 0.4:
                natural_extinction = min(0.3, trauma.reactivation_count * 0.01)
                results["extinction_progress"] = natural_extinction

    def _generate_recommended_actions(self, trauma, current_stress_level, results) -> None:
        """Generate recommended actions."""
        if not results["recommended_actions"]:
            if results["flashback_intensity"] > 0.5:
                results["recommended_actions"].append("apply_emotional_regulation")
                results["recommended_actions"].append("monitor_stress_levels")
            if trauma.reactivation_count > 15 and results["extinction_progress"] > 0.2:
                results["recommended_actions"].append("consider_therapeutic_extinction")
            if current_stress_level > 0.7:
                results["recommended_actions"].append("reduce_system_stress")
            if not results["recommended_actions"]:
                results["recommended_actions"].append("continue_monitoring")

    def _log_processing_result(
        self, memory_id, trigger_context, current_stress_level, coping_strategy, results
    ) -> None:
        """Log processing result."""
        processing_record = {
            "timestamp": datetime.now().isoformat(),
            "memory_id": memory_id,
            "trigger": trigger_context,
            "stress_level": current_stress_level,
            "strategy": coping_strategy,
            "intensity": results["flashback_intensity"],
            "regulation": results["regulation_effectiveness"],
            "extinction_progress": results["extinction_progress"],
        }
        if not hasattr(self, "_processing_history"):
            self._processing_history = []
        self._processing_history.append(processing_record)
        if len(self._processing_history) > _MAX_PROCESSING_HISTORY:
            self._processing_history = self._processing_history[-_MAX_PROCESSING_HISTORY:]
