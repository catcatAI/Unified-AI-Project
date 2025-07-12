# src/core_ai/lis/err_introspector.py
"""
ERR-INTROSPECTOR module for the Linguistic Immune System (LIS).
Responsible for inspecting outputs (e.g., from Fragmenta) and generating
LIS incidents based on critique.
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from src.core_ai.learning.self_critique_module import SelfCritiqueModule
from src.core_ai.lis.lis_cache_interface import LISCacheInterface
from src.shared.types.common_types import (
    CritiqueResult,
    LIS_IncidentRecord,
    LIS_SemanticAnomalyDetectedEvent,
    LIS_AnomalyType # Will use a generic one for now
)

logger = logging.getLogger(__name__)

class ErrIntrospector:
    """
    Inspects outputs, generates critiques, and logs LIS incidents.
    """
    def __init__(self,
                 self_critique_module: SelfCritiqueModule,
                 lis_cache: LISCacheInterface):
        """
        Initializes the ErrIntrospector.

        Args:
            self_critique_module: An instance of SelfCritiqueModule.
            lis_cache: An instance of a class implementing LISCacheInterface (e.g., HAMLISCache).
        """
        if not self_critique_module:
            raise ValueError("SelfCritiqueModule dependency is required for ErrIntrospector.")
        if not lis_cache:
            raise ValueError("LISCacheInterface dependency is required for ErrIntrospector.")
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======

>>>>>>> Stashed changes
=======

>>>>>>> Stashed changes
        self.self_critique_module = self_critique_module
        self.lis_cache = lis_cache
        logger.info("ErrIntrospector initialized.")

    def inspect_fragmenta_output(self,
                                 complex_task_id: str,
                                 task_description: Dict[str, Any],
                                 fragmenta_output: Any,
                                 conversation_history: Optional[List[Dict[str, str]]] = None
                                 ) -> Optional[str]:
        """
        Inspects the output of a Fragmenta complex task, critiques it,
        and stores an LIS incident if issues are found or based on critique score.

        Args:
            complex_task_id: The ID of the Fragmenta complex task.
            task_description: The original description/goal of the Fragmenta task.
            fragmenta_output: The final output/result produced by Fragmenta.
            conversation_history: Optional conversation history leading up to the task.

        Returns:
            Optional[str]: The ID of the generated LIS incident if one was created, else None.
        """
        logger.debug(f"ErrIntrospector: Inspecting output for Fragmenta task ID {complex_task_id}")

        if not self.self_critique_module or not self.lis_cache:
            logger.error("ErrIntrospector: Missing critical dependencies (SelfCritiqueModule or LISCacheInterface). Cannot inspect.")
            return None

        # Prepare inputs for critique
        # The "user_input" for critique context should be the original goal/description of the Fragmenta task.
        critique_user_input = str(task_description.get('goal', task_description.get('name', 'Unknown Task')))
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======

>>>>>>> Stashed changes
=======

>>>>>>> Stashed changes
        # The "ai_response" for critique is the output from Fragmenta.
        # Convert complex fragmenta_output to a string representation if it's not already.
        critique_ai_response = ""
        if isinstance(fragmenta_output, (dict, list)):
            try:
                critique_ai_response = json.dumps(fragmenta_output, indent=2, default=str)
            except TypeError:
                critique_ai_response = str(fragmenta_output)
        else:
            critique_ai_response = str(fragmenta_output)
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======

>>>>>>> Stashed changes
=======

>>>>>>> Stashed changes
        # Limit length to avoid overly long critique prompts
        critique_ai_response = critique_ai_response[:1024] # Max 1024 chars for critique

        effective_conversation_history = conversation_history if conversation_history is not None else []

        critique_result = self.self_critique_module.critique_interaction(
            user_input=critique_user_input,
            ai_response=critique_ai_response,
            context_history=effective_conversation_history
        )

        if not critique_result:
            logger.warning(f"ErrIntrospector: Failed to obtain critique for Fragmenta task {complex_task_id}.")
            return None

        logger.info(f"ErrIntrospector: Critique obtained for {complex_task_id}: Score {critique_result['score']}")

        # Transform CritiqueResult to LIS_IncidentRecord
        # For now, let's assume any critique (even good ones) can be logged as an incident
        # for observability, or apply a threshold later.
<<<<<<< Updated upstream
<<<<<<< Updated upstream

        incident_id = f"lis_inc_{uuid.uuid4().hex}"
        anomaly_id = f"lis_anom_{uuid.uuid4().hex}"

=======
=======
>>>>>>> Stashed changes

        incident_id = f"lis_inc_{uuid.uuid4().hex}"
        anomaly_id = f"lis_anom_{uuid.uuid4().hex}"

<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        # Determine anomaly type and severity
        # Simple mapping: if score < 0.5, it's a more severe "issue".
        # Otherwise, it's more of an "observation" or "minor_flaw".
        # LIS_AnomalyType is a Literal, so we need to define valid types.
        # For now, using a generic type.
        anomaly_type: LIS_AnomalyType = "CRITIQUE_DETECTED_ISSUE" # Default generic type
        severity_score = round(1.0 - critique_result["score"], 2) # Invert score for severity

        if critique_result["score"] < 0.3:
            anomaly_type = "CRITICAL_PERFORMANCE_ISSUE" # Example specific type
        elif critique_result["score"] < 0.6:
            anomaly_type = "SUBOPTIMAL_RESPONSE_QUALITY" # Example specific type
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======

>>>>>>> Stashed changes
=======

>>>>>>> Stashed changes
        semantic_event: LIS_SemanticAnomalyDetectedEvent = {
            "anomaly_id": anomaly_id,
            "anomaly_type": anomaly_type,
            "description": critique_result.get("reason", "No specific reason provided by critique."),
            "severity_score": severity_score,
            "timestamp_detected": datetime.now(timezone.utc).isoformat(),
            "context_data": {
                "source_system": "FragmentaOrchestrator",
                "complex_task_id": complex_task_id,
                "original_task_goal": critique_user_input[:256], # Truncate for brevity
                "fragmenta_output_preview": critique_ai_response[:256] # Truncate
            },
            "suggested_action_level": "log_review" if critique_result["score"] >= 0.7 else "investigate_potential_improvement"
        }

        incident_record: LIS_IncidentRecord = {
            "incident_id": incident_id,
            "timestamp_logged": datetime.now(timezone.utc).isoformat(),
            "timestamp_last_updated": datetime.now(timezone.utc).isoformat(),
            "source_system_event_id": complex_task_id, # Link back to Fragmenta task
            "anomaly_event": semantic_event,
            "status": "NEW_INCIDENT_AWAITING_ANALYSIS", # Initial status
            "tags": ["fragmenta_output", "critique_based", f"critique_score_{critique_result['score']:.2f}"],
            "initial_analysis_notes": f"Automated critique score: {critique_result['score']:.2f}. Reason: {critique_result.get('reason', 'N/A')}",
            "intervention_reports": [],
            "analysis_and_resolution": {
                "analysis_summary": None,
                "identified_root_causes": [],
                "proposed_solutions": [critique_result["suggested_alternative"]] if critique_result.get("suggested_alternative") else [],
                "resolution_strategy_applied": None,
                "resolution_notes": None,
                "outcome_assessment": None
            }
        }

        try:
            storage_success = self.lis_cache.store_incident(incident_record)
            if storage_success:
                logger.info(f"ErrIntrospector: LIS incident {incident_id} created and stored for Fragmenta task {complex_task_id}.")
                return incident_id
            else:
                logger.error(f"ErrIntrospector: Failed to store LIS incident {incident_id} for Fragmenta task {complex_task_id}.")
                return None
        except Exception as e:
            logger.error(f"ErrIntrospector: Exception while storing LIS incident for task {complex_task_id}: {e}", exc_info=True)
            return None
