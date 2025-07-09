import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List, TypedDict, Literal, Union, Tuple

from core_ai.memory.ham_memory_manager import HAMMemoryManager
from services.llm_interface import LLMInterface
from tools.tool_dispatcher import ToolDispatcher
from core_ai.personality.personality_manager import PersonalityManager
from core_ai.emotion_system import EmotionSystem
from core_ai.crisis_system import CrisisSystem
from core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
from hsp.connector import HSPConnector
from hsp.types import HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

# --- Enhanced State Management TypedDicts ---
class HSPStepDetails(TypedDict):
    step_id: str
    type: Literal["hsp_task"]
    capability_id: str
    target_ai_id: str
    request_parameters: Dict[str, Any] # Parameters to be sent in the HSP task request
    # input_sources defines where this step gets its data.
    # Each dict specifies a source step_id and optionally a key if the source result is a dict.
    input_sources: Optional[List[Dict[str, str]]] # e.g., [{"step_id": "s1", "output_key": "summary"}, {"step_id": "s2"}]
    # input_mapping defines how data from input_sources is mapped to this step's effective input or its request_parameters.
    # Keys are target parameter names for this step, values describe how to get the data.
    input_mapping: Optional[Dict[str, Any]] # e.g., {"text_to_process": "s1.summary", "user_context": "s2"} / Complex: {"prompt": "Summarize: {s1.summary} with context {s2}"}
    status: Literal["pending_dispatch", "dispatched", "awaiting_result",
                    "completed", "failed_response", "failed_dispatch", "timeout_error", "retrying"]
    correlation_id: Optional[str]
    dispatch_timestamp: Optional[str]
    result: Optional[Any]
    error_info: Optional[Dict[str, Any]]
    max_retries: int
    retries_left: int
    retry_delay_seconds: int
    last_retry_timestamp: Optional[str]

class LocalStepDetails(TypedDict):
    step_id: str
    type: Literal["local_tool", "local_llm", "local_chunk_process"]
    tool_or_model_name: str
    parameters: Dict[str, Any] # Parameters for the tool/LLM call, or chunking_params
    input_sources: Optional[List[Dict[str, str]]]
    input_mapping: Optional[Dict[str, Any]]
    status: Literal["pending", "in_progress", "completed", "failed"]
    result: Optional[Any] # Could be memory ID or actual content
    error_info: Optional[Dict[str, Any]]

ProcessingStep = Union[HSPStepDetails, LocalStepDetails]

class EnhancedStrategyPlan(TypedDict):
    plan_id: str
    name: str
    # A plan is a list of items. Each item is either a single ProcessingStep (sequential)
    # or a list of ProcessingSteps (parallel group).
    steps: List[Union[ProcessingStep, List[ProcessingStep]]]

class EnhancedComplexTaskState(TypedDict):
    complex_task_id: str
    original_task_description: Dict[str, Any]
    original_input_data: Any
    strategy_plan: EnhancedStrategyPlan
    step_results: Dict[str, Any] # Maps step_id to its result (or mem_id)
    overall_status: Literal["new", "planning", "executing", "waiting_for_hsp",
                            "merging_results", "completed", "failed_plan", "failed_execution"]
    current_executing_step_ids: List[str] # For parallel (currently tracks dispatched HSP)
    next_step_to_evaluate_index: int


class FragmentaOrchestrator:
    def __init__(self,
                 ham_manager: Optional[HAMMemoryManager] = None,
                 tool_dispatcher: Optional[ToolDispatcher] = None,
                 llm_interface: Optional[LLMInterface] = None,
                 service_discovery: Optional[ServiceDiscoveryModule] = None,
                 hsp_connector: Optional[HSPConnector] = None,
                 personality_manager: Optional[PersonalityManager] = None,
                 emotion_system: Optional[EmotionSystem] = None,
                 crisis_system: Optional[CrisisSystem] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initializes the FragmentaOrchestrator.
        Dependencies are injected.
        """
        self.ham_manager = ham_manager
        self.tool_dispatcher = tool_dispatcher
        self.llm_interface = llm_interface
        self.service_discovery = service_discovery
        self.hsp_connector = hsp_connector
        self.personality_manager = personality_manager
        self.emotion_system = emotion_system
        self.crisis_system = crisis_system
        self.config = config or {}

        # Default HSP task configurations
        self.hsp_task_defaults = self.config.get("hsp_task_defaults", {
            "max_retries": 3,
            "initial_retry_delay_seconds": 5,
            "retry_backoff_factor": 2,
            "timeout_seconds": 300 # 5 minutes default timeout for an HSP task
        })

        # _pending_hsp_sub_tasks maps correlation_id to (complex_task_id, step_id)
        self._pending_hsp_sub_tasks: Dict[str, Tuple[str, str]] = {}
        self._complex_task_context: Dict[str, EnhancedComplexTaskState] = {} # Uses new state TypedDict

        # Register HSP result handler if connector is available
        # This registration is confirmed to be handled by core_services.py
        # The _handle_hsp_sub_task_result method will be called by the HSPConnector.
        # For now, if hsp_connector is provided, we attempt to register.
        if self.hsp_connector:
            # Assuming a generic task result callback that might be shared or
            # a more specific one if HSPConnector supports multiple handlers for TaskResults.
            # For this implementation, DialogueManager already registers one.
            # Fragmenta will need to coordinate or have its own distinct path.
            # Let's assume for now it will be registered externally or this is a placeholder.
            logger.info("FragmentaOrchestrator: HSPConnector provided. Callback registration for HSP task results should be handled by the integrating service (e.g., core_services.py or DialogueManager).")
            # Example: self.hsp_connector.register_on_task_result_callback(self._handle_hsp_sub_task_result) -> This would make Fragmenta always listen.
            # It's better if only active tasks are listened for, or results are routed.

        logger.info(f"FragmentaOrchestrator Initialized. HAM: {'Yes' if self.ham_manager else 'No'}, Tools: {'Yes' if self.tool_dispatcher else 'No'}, LLM: {'Yes' if self.llm_interface else 'No'}, SDM: {'Yes' if self.service_discovery else 'No'}, HSP-Conn: {'Yes' if self.hsp_connector else 'No'}")

    def process_complex_task(self, task_description: Dict[str, Any], input_data: Any, complex_task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point for Fragmenta to process a complex task.
        Manages state for potentially asynchronous operations like HSP calls.
        This method is re-entrant.
        """
        is_new_task = False
        if complex_task_id is None:
            complex_task_id = f"frag_task_{uuid.uuid4().hex[:8]}"
            is_new_task = True
            logger.info(f"Fragmenta: New complex task received (ID: {complex_task_id}). Description: {str(task_description)[:100]}...")
        elif complex_task_id not in self._complex_task_context:
            logger.error(f"Fragmenta: Unknown complex_task_id '{complex_task_id}' for resumed processing.")
            return {"status": "error", "message": f"Unknown complex_task_id {complex_task_id}", "complex_task_id": complex_task_id}

        if is_new_task:
            input_info = self._analyze_input(input_data)
            logger.info(f"Fragmenta (ID: {complex_task_id}): Input analysis - Type: {input_info.get('type')}, Size: {input_info.get('size')}")
            strategy_plan = self._determine_processing_strategy(task_description, input_info, complex_task_id)
            logger.info(f"Fragmenta (ID: {complex_task_id}): Determined strategy plan '{strategy_plan['name']}' with {len(strategy_plan['steps'])} steps.")

            self._complex_task_context[complex_task_id] = EnhancedComplexTaskState(
                complex_task_id=complex_task_id,
                original_task_description=task_description,
                original_input_data=input_data,
                strategy_plan=strategy_plan,
                step_results={},
                overall_status="planning",
                current_executing_step_ids=[],
                next_step_to_evaluate_index=0
            )

        return self._advance_complex_task(complex_task_id)

    def _advance_complex_task(self, complex_task_id: str) -> Dict[str, Any]:
        """
        Internal method to advance the state of a complex task.
        This is the core state machine.
        """
        task_ctx = self._complex_task_context.get(complex_task_id)
        if not task_ctx:
            logger.error(f"Fragmenta: Cannot advance task, context not found for ID '{complex_task_id}'.")
            return {"status": "error", "message": f"Context lost for task {complex_task_id}", "complex_task_id": complex_task_id}

        logger.info(f"Fragmenta (ID: {complex_task_id}): Advancing task. Overall status: {task_ctx['overall_status']}, Next step index: {task_ctx['next_step_to_evaluate_index']}")

        strategy_plan = task_ctx["strategy_plan"]

        # Initial transition from planning
        if task_ctx["overall_status"] == "planning":
            task_ctx["overall_status"] = "executing"

        if task_ctx["overall_status"] == "executing":
            all_steps_completed = True
            can_dispatch_more = True # Assume we can try to dispatch current step

            while task_ctx["next_step_to_evaluate_index"] < len(strategy_plan["steps"]) and can_dispatch_more:
                current_step_index = task_ctx["next_step_to_evaluate_index"]
                step_details = strategy_plan["steps"][current_step_index] # This is a ProcessingStep (Union)
                step_id = step_details["step_id"]

                if step_details["status"] in ["completed", "failed_dispatch", "failed_response", "timeout_error"]: # Already terminal for this step
                    task_ctx["next_step_to_evaluate_index"] += 1
                    continue # Move to next step in plan

                all_steps_completed = False # Found a non-completed step

                # Check dependencies
                dependencies_met = True
                if step_details.get("input_source_step_id"):
                    source_step_id = step_details["input_source_step_id"]
                    if source_step_id not in task_ctx["step_results"]:
                        logger.debug(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): Dependency '{source_step_id}' not met. Waiting.")
                        dependencies_met = False
                        can_dispatch_more = False # Block further dispatch in this cycle if a dependency is pending
                    # Also check if source step failed; if so, this step might also fail or need alternative handling (TBD by error strategy)

                if not dependencies_met:
                    break # Cannot proceed with this step or subsequent ones in this cycle

                # Prepare input for the current step
                current_step_input = task_ctx["original_input_data"] # Default to original task input
                if step_details.get("input_source_step_id"):
                    source_step_id = step_details["input_source_step_id"] # type: ignore
                    source_result = task_ctx["step_results"].get(source_step_id)
                    # TODO: Implement input_parameter_mapping logic here if exists
                    # TODO: Check if source_step failed; if so, this step should likely not run or plan fails.
                    if source_step_id and task_ctx["strategy_plan"]["steps"][self._find_step_index(task_ctx["strategy_plan"]["steps"], source_step_id)]["status"] != "completed":
                        logger.warning(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): Source step '{source_step_id}' not completed or failed. Halting this path.")
                        task_ctx["overall_status"] = "failed_execution" # Or a more specific "dependency_failed"
                        can_dispatch_more = False
                        break
                    current_step_input = source_result # Simplified: direct output becomes input

                # Dispatch logic based on step type and status
                if step_details["type"] == "hsp_task":
                    hsp_step = step_details # type: HSPStepDetails

                    # Timeout Check for dispatched/awaiting_result HSP steps
                    if hsp_step["status"] in ["dispatched", "awaiting_result"] and hsp_step["dispatch_timestamp"]:
                        dispatch_time = datetime.fromisoformat(hsp_step["dispatch_timestamp"])
                        timeout_seconds = self.hsp_task_defaults.get("timeout_seconds", 300)
                        if datetime.now(timezone.utc) - dispatch_time > timedelta(seconds=timeout_seconds):
                            logger.warning(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): HSP Task timed out (CorrID: {hsp_step.get('correlation_id')}).")
                            hsp_step["status"] = "timeout_error"
                            hsp_step["error_info"] = {"message": f"HSP task timed out after {timeout_seconds} seconds."}
                            # Retry logic will be checked below

                    if hsp_step["status"] == "pending_dispatch":
                        logger.info(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): Dispatching HSP task.")
                        correlation_id = self._dispatch_hsp_sub_task(complex_task_id, step_id, hsp_step) # Updates step status internally
                        if hsp_step["status"] == "dispatched": # Successfully dispatched
                            task_ctx["overall_status"] = "waiting_for_hsp"
                        else: # Dispatch failed (e.g. status became "failed_dispatch")
                            task_ctx["overall_status"] = "failed_execution"
                            can_dispatch_more = False # Stop processing this plan
                        task_ctx["next_step_to_evaluate_index"] += 1
                        can_dispatch_more = False # Wait for HSP result or failure

                    elif hsp_step["status"] in ["failed_dispatch", "failed_response", "timeout_error"]:
                        if hsp_step["retries_left"] > 0:
                            logger.info(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): Attempting retry. Retries left: {hsp_step['retries_left']}.")
                            hsp_step["retries_left"] -= 1
                            hsp_step["status"] = "retrying"
                            hsp_step["last_retry_timestamp"] = datetime.now(timezone.utc).isoformat()
                            # We'll check the delay in the next cycle if status is 'retrying'
                            task_ctx["overall_status"] = "executing" # May still be executing other paths or this retry
                            can_dispatch_more = False # Pause this step's path for retry delay
                        else:
                            logger.error(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): HSP Task failed after all retries. Status: {hsp_step['status']}.")
                            task_ctx["overall_status"] = "failed_execution"
                            can_dispatch_more = False # Stop processing this plan
                        task_ctx["next_step_to_evaluate_index"] += 1 # Consider this path terminal or moving to retry

                    elif hsp_step["status"] == "retrying":
                        last_retry_ts = datetime.fromisoformat(hsp_step["last_retry_timestamp"] if hsp_step["last_retry_timestamp"] else "1970-01-01T00:00:00+00:00") # type: ignore
                        # Basic backoff, can be made more sophisticated
                        current_retry_delay = hsp_step["retry_delay_seconds"] * (self.hsp_task_defaults.get("retry_backoff_factor", 2) ** (hsp_step["max_retries"] - hsp_step["retries_left"] -1))

                        if datetime.now(timezone.utc) - last_retry_ts > timedelta(seconds=current_retry_delay):
                            logger.info(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): Retry delay passed. Re-dispatching.")
                            hsp_step["status"] = "pending_dispatch" # Trigger re-dispatch in next iteration
                            # Loop will pick it up as pending_dispatch, effectively restarting the step.
                            # No increment of next_step_to_evaluate_index here, as we want to re-process this step.
                            can_dispatch_more = True # Allow immediate re-evaluation for dispatch
                            continue # Re-evaluate this same step now marked as pending_dispatch
                        else:
                            logger.debug(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): In retry delay. Waiting.")
                            task_ctx["overall_status"] = "waiting_for_hsp" # Still waiting overall
                            can_dispatch_more = False # Block this path

                    elif hsp_step["status"] == "dispatched" or hsp_step["status"] == "awaiting_result":
                        # This means it's waiting for a callback, do nothing for this step in this cycle
                        task_ctx["overall_status"] = "waiting_for_hsp"
                        all_steps_completed = False
                        can_dispatch_more = False # Block this path until result or timeout
                        task_ctx["next_step_to_evaluate_index"] += 1 # Evaluate next step in plan if any

                elif step_details["type"] in ["local_tool", "local_llm", "local_chunk_process"]:
                    local_step = step_details # type: LocalStepDetails
                    if local_step["status"] == "pending":
                        local_step["status"] = "in_progress"
                        logger.info(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): Executing local step '{local_step['tool_or_model_name']}'.")
                        try:
                            if local_step["type"] == "local_chunk_process":
                                # Handle chunk processing logic - this might be complex and involve multiple sub-operations
                                # For now, treat as a single dispatch for simplicity of state machine.
                                # Actual chunking and merging would happen here or in _dispatch_chunk_to_processing
                                all_chunks = self._chunk_data(current_step_input, local_step["parameters"].get("chunking_params"))
                                chunk_results_or_ids = []
                                for i, chunk_data in enumerate(all_chunks):
                                    chunk_res_id = self._dispatch_chunk_to_processing(
                                        chunk_data,
                                        {"tool_or_model": local_step["tool_or_model_name"], "params": local_step["parameters"]}, # Pass relevant params
                                        complex_task_id, i, len(all_chunks)
                                    )
                                    chunk_results_or_ids.append(chunk_res_id)
                                # The result of a chunk_process step is the list of results/ids before merging
                                local_step["result"] = chunk_results_or_ids
                            else:
                                # Simplified: _dispatch_chunk_to_processing used for single local steps too
                                local_step["result"] = self._dispatch_chunk_to_processing(
                                    current_step_input,
                                    {"tool_or_model": local_step["tool_or_model_name"], "params": local_step["parameters"]},
                                    complex_task_id, 0, 1 # chunk_index, total_chunks
                                )
                            local_step["status"] = "completed"
                            task_ctx["step_results"][step_id] = local_step["result"]
                        except Exception as e:
                            logger.error(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): Local step execution failed: {e}", exc_info=True)
                            local_step["status"] = "failed"
                            local_step["error_info"] = {"message": str(e)}
                            task_ctx["overall_status"] = "failed_execution" # Or more nuanced
                            can_dispatch_more = False # Stop processing
                        task_ctx["next_step_to_evaluate_index"] += 1
                else: # Unknown step type or unhandled status for the step
                    logger.warning(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): Unhandled step type '{step_details['type']}' or status '{step_details['status']}'. Skipping.")
                    task_ctx["next_step_to_evaluate_index"] += 1
                    # Potentially mark step as failed or stalled

            # After loop, check if all steps are completed
            if task_ctx["next_step_to_evaluate_index"] >= len(strategy_plan["steps"]):
                # Re-check all_steps_completed by iterating through actual step statuses
                all_steps_completed_final_check = True
                for step in strategy_plan["steps"]:
                    if step["status"] != "completed":
                        all_steps_completed_final_check = False
                        if step["status"] in ["failed_dispatch", "failed_response", "timeout_error", "failed"]:
                            task_ctx["overall_status"] = "failed_execution"
                            break
                        elif step["status"] in ["pending_dispatch", "dispatched", "awaiting_result", "retrying", "pending", "in_progress"]:
                             # Still waiting for some steps (e.g. HSP or a long local task not yet finished by this synchronous call)
                             if step["type"] == "hsp_task" and step["status"] != "awaiting_result":
                                 # This case should ideally not happen if logic is correct, means an HSP task is stuck before awaiting_result
                                 logger.warning(f"Fragmenta (ID: {complex_task_id}, Step: {step['step_id']}): HSP task in unexpected non-terminal state: {step['status']}")
                             elif step["type"] == "hsp_task": # and status is awaiting_result or dispatched
                                task_ctx["overall_status"] = "waiting_for_hsp"

                if task_ctx["overall_status"] == "failed_execution":
                    logger.error(f"Fragmenta (ID: {complex_task_id}): Plan execution failed.")
                    # self._complex_task_context.pop(complex_task_id, None) # Cleanup
                    return {"status": "failed", "message": "One or more steps failed.", "complex_task_id": complex_task_id, "step_results": task_ctx["step_results"]}

                if all_steps_completed_final_check:
                    task_ctx["overall_status"] = "merging_results"

            # If still executing but some steps are pending (e.g. HSP), status would be "executing" or "waiting_for_hsp"
            if task_ctx["overall_status"] == "executing" and any(s["status"] not in ["completed", "failed", "failed_dispatch", "failed_response", "timeout_error"] for s in strategy_plan["steps"]):
                 # Check if any HSP tasks are outstanding to correctly set overall status
                is_waiting_for_hsp = any(s["type"] == "hsp_task" and s["status"] in ["dispatched", "awaiting_result", "retrying"] for s in strategy_plan["steps"])
                if is_waiting_for_hsp:
                    task_ctx["overall_status"] = "waiting_for_hsp"

        if task_ctx["overall_status"] == "merging_results":
            # Find the "final" step or use a predefined output mapping from strategy
            # For now, assume the result of the last step is the main result, or a specific merge strategy is defined
            merging_params = {}
            # Example: if strategy plan had a "final_result_step_id" or "merge_strategy"
            # final_result_source_step_id = strategy_plan.get("final_output_from_step_id", strategy_plan["steps"][-1]["step_id"] if strategy_plan["steps"] else None)
            # merged_result = task_ctx["step_results"].get(final_result_source_step_id)

            # More robust merging logic:
            # If a 'local_chunk_process' step was used, its result is a list of chunk results/IDs
            # These now need to be merged using its 'merging_params'.
            final_results_to_merge = []
            for step_detail in strategy_plan["steps"]:
                if step_detail["type"] == "local_chunk_process" and step_detail["status"] == "completed":
                    # This step's result is a list of sub-results that need merging
                    chunk_proc_results = task_ctx["step_results"].get(step_detail["step_id"], [])
                    merging_params_for_chunk = step_detail["parameters"].get("merging_params", {"method": "join_with_newline"})
                    merged_chunk_output = self._merge_results(chunk_proc_results, merging_params_for_chunk)
                    final_results_to_merge.append(merged_chunk_output)
                elif step_detail["status"] == "completed": # Other completed steps
                    final_results_to_merge.append(task_ctx["step_results"].get(step_detail["step_id"]))

            # If multiple top-level steps completed, how to merge them?
            # For now, if there's only one item in final_results_to_merge, that's our result.
            # Otherwise, use a default join or expect strategy to define this.
            if len(final_results_to_merge) == 1:
                final_output = final_results_to_merge[0]
            else: # Default merge for multiple top-level results
                final_output = self._merge_results(final_results_to_merge, {"method": "return_as_list"})


            task_ctx["overall_status"] = "completed"
            logger.info(f"Fragmenta (ID: {complex_task_id}): Merging complete. Final result type: {type(final_output)}. Overall status 'completed'.")
            # self._complex_task_context.pop(complex_task_id, None) # Cleanup
            return {"status": "completed", "result": final_output, "complex_task_id": complex_task_id}

        # Return current status if still ongoing
        if task_ctx["overall_status"] == "waiting_for_hsp":
             active_corr_ids = [s["correlation_id"] for s in strategy_plan["steps"] if s["type"] == "hsp_task" and s.get("correlation_id") and s["status"] == "awaiting_result"]
             logger.info(f"Fragmenta (ID: {complex_task_id}): Overall status 'waiting_for_hsp'. Active Correlation IDs: {active_corr_ids}")
             return {"status": "pending_hsp", "complex_task_id": complex_task_id, "correlation_ids": active_corr_ids}

        logger.info(f"Fragmenta (ID: {complex_task_id}): Task in intermediate overall status: {task_ctx['overall_status']}. Next step idx: {task_ctx['next_step_to_evaluate_index']}")
        # Ensure we return a consistent structure even for intermediate states
        return {"status": task_ctx['overall_status'],
                "complex_task_id": complex_task_id,
                "message": f"Processing step {task_ctx['next_step_to_evaluate_index'] +1 } / {len(strategy_plan['steps'])}",
                "current_step_details": strategy_plan["steps"][task_ctx['next_step_to_evaluate_index']] if task_ctx['next_step_to_evaluate_index'] < len(strategy_plan["steps"]) else None
                }

    def _find_step_index(self, steps: List[ProcessingStep], step_id: str) -> int:
        """Helper to find the index of a step by its ID."""
        for i, step in enumerate(steps):
            if step["step_id"] == step_id:
                return i
        raise ValueError(f"Step with ID '{step_id}' not found in plan.")

    def _analyze_input(self, input_data: any) -> dict:
        input_type = "unknown"
        input_size = 0
        if isinstance(input_data, str):
            input_type = "text"
            input_size = len(input_data)
        elif isinstance(input_data, (list, dict)):
            input_type = "structured_data"
            input_size = len(str(input_data)) # Simplistic size for list/dict
        return {"type": input_type, "size": input_size, "content_preview": str(input_data)[:100]}

    def _determine_processing_strategy(self, task_description: Dict[str, Any], input_info: Dict[str, Any], complex_task_id: str) -> EnhancedStrategyPlan:
        logger.debug(f"Fragmenta (ID: {complex_task_id}): Determining strategy for task: {task_description.get('goal', 'N/A')}")

        steps: List[ProcessingStep] = []
        plan_name = "default_single_step_plan"
        plan_id = f"plan_{complex_task_id}_{uuid.uuid4().hex[:4]}"

        # Priority 1: Explicit HSP dispatch request in task_description
        if task_description.get("dispatch_to_hsp_capability_id"):
            if not self.service_discovery or not self.hsp_connector:
                logger.warning(f"Fragmenta (ID: {complex_task_id}): HSP dispatch requested but SDM or HSPConnector not available. Cannot create HSP step.")
                # Create a failed plan or a plan with a single failed step
                plan_name = "error_hsp_unavailable"
                # Optionally add a 'failed_plan_step' here if desired, or handle upstream
            else:
                cap_id = task_description["dispatch_to_hsp_capability_id"]
                capability = self.service_discovery.get_capability_by_id(cap_id, exclude_unavailable=True)
                if capability and capability.get("ai_id"):
                    plan_name = "dispatch_to_hsp_capability"
                    logger.info(f"Fragmenta (ID: {complex_task_id}): Strategy: Explicit HSP dispatch to capability ID '{cap_id}'.")
                    hsp_step: HSPStepDetails = {
                        "step_id": f"{plan_id}_step_0_hsp",
                        "type": "hsp_task",
                        "capability_id": cap_id,
                        "target_ai_id": capability["ai_id"], # ai_id from capability payload
                        "request_parameters": task_description.get("hsp_task_parameters", {}),
                        "input_source_step_id": None,
                        "input_parameter_mapping": None,
                        "status": "pending_dispatch",
                        "correlation_id": None,
                        "dispatch_timestamp": None,
                        "result": None,
                        "error_info": None,
                        "max_retries": self.hsp_task_defaults.get("max_retries", 3),
                        "retries_left": self.hsp_task_defaults.get("max_retries", 3),
                        "retry_delay_seconds": self.hsp_task_defaults.get("initial_retry_delay_seconds", 5),
                        "last_retry_timestamp": None,
                    }
                    steps.append(hsp_step) # Appending a single step (sequential stage)
                else:
                    logger.warning(f"Fragmenta (ID: {complex_task_id}): Requested HSP capability ID '{cap_id}' not found, unavailable, or missing ai_id. Creating a failed step.")
                    plan_name = f"error_hsp_cap_unavailable_{cap_id}"
                    failed_hsp_step: HSPStepDetails = {
                        "step_id": f"{plan_id}_step_0_hsp_failed_discovery",
                        "type": "hsp_task",
                        "capability_id": cap_id, "target_ai_id": "unknown", "request_parameters": {},
                        "input_source_step_id": None, "input_parameter_mapping": None,
                        "status": "failed_dispatch", # Mark as failed dispatch due to discovery issue
                        "correlation_id": None, "dispatch_timestamp": None, "result": None,
                        "error_info": {"message": f"Capability '{cap_id}' not found or unavailable."},
                        "max_retries": 0, "retries_left": 0, "retry_delay_seconds": 0, "last_retry_timestamp": None,
                    }
                    steps.append(failed_hsp_step)

        # Priority 2: Specific local tool requested (if no step was created by HSP logic)
        if not steps and task_description.get("requested_tool"):
            requested_tool = task_description["requested_tool"]
            plan_name = f"direct_tool_call_{requested_tool}"
            logger.info(f"Fragmenta (ID: {complex_task_id}): Strategy: Direct call to local tool '{requested_tool}'.")
            local_step: LocalStepDetails = {
                "step_id": f"{plan_id}_step_0_local_tool",
                "type": "local_tool",
                "tool_or_model_name": requested_tool,
                "parameters": task_description.get("tool_params", {}),
                "input_source_step_id": None,
                "input_parameter_mapping": None,
                "status": "pending",
                "result": None,
                "error_info": None,
            }
            steps.append(local_step)

        # Priority 3: General local processing (chunking for large text, or direct LLM) (if no steps yet)
        if not steps:
            input_type = input_info.get("type", "unknown")
            input_size = input_info.get("size", 0)
            # Using a higher default threshold to avoid excessive chunking for moderately sized texts
            chunking_threshold = self.config.get("default_chunking_threshold", 1000)

            if input_type == "text" and input_size > chunking_threshold:
                plan_name = "chunk_and_summarize_text_locally"
                logger.info(f"Fragmenta (ID: {complex_task_id}): Strategy: Text input size {input_size} > threshold {chunking_threshold}. Applying chunking and local LLM summarization.")
                # This strategy implies multiple steps: one for each chunk, then a merge step.
                # For simplicity in this refactor, we'll represent it as one 'local_chunk_process' step.
                # The actual chunking and iteration will happen inside _dispatch_chunk_to_processing or a dedicated method.
                chunk_process_step: LocalStepDetails = {
                    "step_id": f"{plan_id}_step_0_chunk_process",
                    "type": "local_chunk_process", # Special type to indicate chunking
                    "tool_or_model_name": "llm_summarize_chunk", # The operation per chunk
                    "parameters": {"chunking_params": self.config.get("default_text_chunking_params", {"chunk_size": 800, "overlap": 50}),
                                   "merging_params": {"method": "join_with_newline"}},
                    "input_source_step_id": None,
                    "input_parameter_mapping": None,
                    "status": "pending",
                    "result": None,
                    "error_info": None,
                }
                steps.append(chunk_process_step)
            else: # Default: Direct local LLM processing
                plan_name = "direct_local_llm_process"
                logger.info(f"Fragmenta (ID: {complex_task_id}): Strategy: Default direct local LLM processing for input type '{input_type}', size {input_size}.")
                llm_direct_step: LocalStepDetails = {
                    "step_id": f"{plan_id}_step_0_llm_direct",
                    "type": "local_llm",
                    "tool_or_model_name": "llm_direct_process", # General LLM processing
                    "parameters": {},
                    "input_source_step_id": None,
                    "input_parameter_mapping": None,
                    "status": "pending",
                    "result": None,
                    "error_info": None,
                }
                steps.append(llm_direct_step)

        if not steps: # Fallback if all logic above fails to produce a step
            logger.error(f"Fragmenta (ID: {complex_task_id}): No processing steps generated for task. Creating a failed plan.")
            plan_name = "error_no_steps_generated"
            # Optionally add a dummy failed step to the plan
            failed_step_placeholder: LocalStepDetails = {
                "step_id": f"{plan_id}_step_0_failed_plan",
                "type": "local_llm",
                "tool_or_model_name": "error_placeholder",
                "parameters": {}, "input_source_step_id": None, "input_parameter_mapping": None,
                "status": "failed", "result": None,
                "error_info": {"message": "Failed to determine any valid processing step."}
            }
            steps.append(failed_step_placeholder)


        return EnhancedStrategyPlan(plan_id=plan_id, name=plan_name, steps=steps)

    def _chunk_data(self, data: any, chunking_params: Optional[Dict[str, Any]] = None) -> list:
        if not isinstance(data, str) or not chunking_params:
            return [data]

        chunk_size = chunking_params.get("chunk_size", 100)
        overlap = chunking_params.get("overlap", 10)
        chunks = []
        start = 0
        while start < len(data):
            end = min(start + chunk_size, len(data))
            chunk_to_add = data[start:end]
            chunks.append(chunk_to_add)
            if end == len(data):
                break
            start += (chunk_size - overlap)
        return chunks if chunks else [data]

    def _dispatch_chunk_to_processing(self, chunk: any, strategy_step: Dict[str, Any], task_id: str, chunk_index: int, total_chunks: int) -> Any:
        tool_or_model_name = strategy_step.get("tool_or_model", "identity")
        params = strategy_step.get("params", {})
        logger.info(f"Fragmenta (TaskID: {task_id}): Dispatching chunk {chunk_index+1}/{total_chunks} to local processor '{tool_or_model_name}'.")

        processed_content = None
        if "llm" in tool_or_model_name:
            if self.llm_interface:
                prompt = f"Task ({task_id}), Chunk ({chunk_index+1}/{total_chunks}): {str(chunk)}"
                if tool_or_model_name == "llm_summarize_chunk":
                    prompt = f"Summarize this text chunk ({chunk_index+1}/{total_chunks}) for task {task_id}: {str(chunk)}"
                processed_content = self.llm_interface.generate_response(prompt=prompt, params=params)
            else:
                logger.warning(f"Fragmenta (TaskID: {task_id}): LLMInterface not available for '{tool_or_model_name}'.")
                processed_content = f"[LLM N/A - Chunk: {str(chunk)[:30]}...]"
        elif tool_or_model_name == "identity":
            processed_content = chunk
        elif self.tool_dispatcher: # Assuming tool_dispatcher.tools is not how we check
            logger.info(f"Fragmenta (TaskID: {task_id}): Attempting dispatch to ToolDispatcher for tool '{tool_or_model_name}'.")
            # ToolDispatcher.dispatch might raise error if tool not found, or return error structure
            tool_result = self.tool_dispatcher.dispatch(
                query=str(chunk), # Or construct a more specific query based on task
                explicit_tool_name=tool_or_model_name,
                **params
            )
            if isinstance(tool_result, dict) and tool_result.get("status") == "success":
                processed_content = tool_result.get("payload")
            else: # Handle tool error or unexpected format
                processed_content = f"[Tool '{tool_or_model_name}' error/unavailable. Result: {str(tool_result)[:100]}]"
        else:
            logger.warning(f"Fragmenta (TaskID: {task_id}): Unknown local processor '{tool_or_model_name}' or ToolDispatcher unavailable.")
            processed_content = f"[UnknownProcessor '{tool_or_model_name}' - Chunk: {str(chunk)[:30]}...]"

        if self.ham_manager and processed_content is not None:
            metadata = {
                "original_task_id": task_id, "chunk_index": chunk_index, "total_chunks": total_chunks,
                "processor": tool_or_model_name, "strategy_step_params": params
            }
            mem_id = self.ham_manager.store_experience(
                raw_data=str(processed_content), data_type="fragmenta_chunk_result", metadata=metadata
            )
            if mem_id:
                logger.info(f"Fragmenta (TaskID: {task_id}): Stored chunk result {chunk_index+1} in HAM with ID {mem_id}.")
                return mem_id
            else:
                logger.warning(f"Fragmenta (TaskID: {task_id}): Failed to store chunk result {chunk_index+1} in HAM.")
        return processed_content # Fallback if HAM fails or not available

    def _merge_results(self, chunk_results_or_ids: list, merging_params: Optional[Dict[str, Any]] = None) -> any:
        # Determine the merge method. If no params or method specified, and only one result, default to returning it directly.
        # If multiple results and no method, default to simple_join.
        method_from_params = merging_params.get("method") if merging_params else None

        logger.info(f"Fragmenta: Merging {len(chunk_results_or_ids)} items. Requested method: '{method_from_params}'.")
        if not chunk_results_or_ids: return None

        actual_content_list = []
        for item_res_or_id in chunk_results_or_ids:
            if isinstance(item_res_or_id, str) and item_res_or_id.startswith("mem_") and self.ham_manager:
                recalled_data = self.ham_manager.recall_gist(item_res_or_id)
                if recalled_data and "rehydrated_gist" in recalled_data:
                    actual_content_list.append(recalled_data["rehydrated_gist"])
                else:
                    actual_content_list.append(f"[Error retrieving HAM ID {item_res_or_id}]")
            elif item_res_or_id is not None:
                actual_content_list.append(item_res_or_id)

        if not actual_content_list: return None

        effective_method = method_from_params
        if not effective_method: # If no method was specified in params
            if len(actual_content_list) == 1:
                return actual_content_list[0] # Default for single item: return as is
            else:
                effective_method = "simple_join" # Default for multiple items: simple_join

        if effective_method == "join_with_newline":
            return "\n".join(map(str, actual_content_list))
        elif effective_method == "simple_join":
            return " ".join(map(str, actual_content_list))
        # Add other specific merge strategies here, e.g., "return_first", "return_list_of_dicts"
        elif effective_method == "return_as_list":
             return actual_content_list
        elif effective_method == "return_first_if_single_else_list":
            return actual_content_list[0] if len(actual_content_list) == 1 else actual_content_list

        # Fallback for unknown method or if single item and no specific non-join method
        if len(actual_content_list) == 1 and method_from_params is None: # Handles case where method was None and only one item
             return actual_content_list[0]

        logger.warning(f"Fragmenta: Fallback for merge. Method: '{effective_method}'. Returning list or first item.")
        return actual_content_list if len(actual_content_list) > 1 else actual_content_list[0]

    def _dispatch_hsp_sub_task(self, complex_task_id: str, step_id: str, hsp_step_details: HSPStepDetails) -> Optional[str]:
        if not self.hsp_connector:
            logger.error(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): HSPConnector not available.")
            hsp_step_details["status"] = "failed_dispatch"
            hsp_step_details["error_info"] = {"message": "HSPConnector not available."}
            return None
        if not self.hsp_connector.is_connected:
            logger.error(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): HSPConnector not connected.")
            hsp_step_details["status"] = "failed_dispatch"
            hsp_step_details["error_info"] = {"message": "HSPConnector not connected."}
            return None

        # Generate a unique request_id for this specific HSP call, correlation_id will be handled by HSPConnector
        hsp_internal_request_id = f"frag_hsp_req_{uuid.uuid4().hex[:8]}"

        # The callback_address should be a topic this AI (via HSPConnector) is subscribed to,
        # allowing results for different tasks/steps to be routed back correctly.
        # For now, a general results topic for this AI. Specific routing will depend on correlation_id.
        callback_address = f"hsp/results/{self.hsp_connector.ai_id}"

        hsp_task_payload = HSPTaskRequestPayload(
            request_id=hsp_internal_request_id,
            requester_ai_id=self.hsp_connector.ai_id, # Fragmenta's AI ID via connector
            target_ai_id=hsp_step_details["target_ai_id"],
            capability_id_filter=hsp_step_details["capability_id"],
            parameters=hsp_step_details["request_parameters"],
            callback_address=callback_address
        )

        logger.info(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): Attempting to send HSP TaskRequest (InternalReqID: {hsp_internal_request_id}) to AI '{hsp_step_details['target_ai_id']}' for capability '{hsp_step_details['capability_id']}'.")

        # HSPConnector.send_task_request is expected to return a correlation_id it generates
        new_correlation_id = self.hsp_connector.send_task_request(
            payload=hsp_task_payload,
            target_ai_id_or_topic=hsp_step_details["target_ai_id"]
        )

        if new_correlation_id:
            hsp_step_details["correlation_id"] = new_correlation_id
            hsp_step_details["dispatch_timestamp"] = datetime.now(timezone.utc).isoformat()
            hsp_step_details["status"] = "dispatched" # Or "awaiting_result" if send_task_request is synchronous in effect
                                                    # Assuming send_task_request is async and returns correlation_id immediately
            self._pending_hsp_sub_tasks[new_correlation_id] = (complex_task_id, step_id)
            logger.info(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): HSP TaskRequest sent. Correlation ID: {new_correlation_id}.")
            return new_correlation_id
        else:
            logger.error(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): Failed to send HSP TaskRequest (connector returned None for correlation_id).")
            hsp_step_details["status"] = "failed_dispatch"
            hsp_step_details["error_info"] = {"message": "HSPConnector failed to send task request."}
            return None

    def _handle_hsp_sub_task_result(self, result_payload: HSPTaskResultPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope) -> None:
        correlation_id = full_envelope.get('correlation_id')
        if not correlation_id:
            logger.warning("Fragmenta: Received HSP task result without correlation_id. Cannot process.")
            return

        lookup_info = self._pending_hsp_sub_tasks.pop(correlation_id, None)
        if not lookup_info:
            logger.warning(f"Fragmenta: Received HSP task result for unknown or already processed correlation_id: {correlation_id}. Payload: {str(result_payload)[:200]}")
            return

        complex_task_id, step_id = lookup_info
        logger.info(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): Received HSP sub-task result for CorrID {correlation_id} from AI {sender_ai_id}.")

        task_ctx = self._complex_task_context.get(complex_task_id)
        if not task_ctx:
            logger.error(f"Fragmenta: Context for complex task ID {complex_task_id} not found while processing HSP result. CorrID: {correlation_id}, StepID: {step_id}")
            return

        # Find the specific HSPStepDetails in the strategy plan
        step_to_update: Optional[HSPStepDetails] = None
        for step in task_ctx["strategy_plan"]["steps"]:
            if step["step_id"] == step_id and step["type"] == "hsp_task":
                step_to_update = step # type: HSPStepDetails
                break

        if not step_to_update:
            logger.error(f"Fragmenta (ID: {complex_task_id}): HSPStepDetails for step_id '{step_id}' not found in plan. CorrID: {correlation_id}")
            return

        # Defensive check: if already completed/failed, this might be a duplicate/late message
        if step_to_update["status"] in ["completed", "failed_response", "failed_dispatch", "timeout_error"]:
            logger.warning(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): Received HSP result for already terminated step (status: {step_to_update['status']}). CorrID: {correlation_id}. Ignoring.")
            return

        actual_result_data = result_payload.get('payload')
        if result_payload.get('status') == 'success':
            logger.info(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): HSP sub-task success. Result: {str(actual_result_data)[:100]}...")
            step_to_update["status"] = "completed"
            step_to_update["result"] = actual_result_data
            task_ctx["step_results"][step_id] = actual_result_data
        else:
            error_details = result_payload.get('error_details', {"message": "Unknown HSP error from peer"})
            logger.error(f"Fragmenta (ID: {complex_task_id}, Step: {step_id}): HSP sub-task failed. Error: {error_details}")
            step_to_update["status"] = "failed_response" # Will be handled by retry logic later
            step_to_update["error_info"] = error_details # type: ignore
            task_ctx["step_results"][step_id] = None # Or some error marker

        # Signal that this complex task needs re-evaluation
        self._advance_complex_task(complex_task_id)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.info("--- FragmentaOrchestrator Manual Test ---")

    # Mock dependencies
    mock_ham = HAMMemoryManager(core_storage_filename="frag_test_ham.json") # Needs MIKO_HAM_KEY or will use temp
    mock_llm = LLMInterface(config={"default_provider": "mock"}) # Basic mock
    mock_sdm = ServiceDiscoveryModule(trust_manager=TrustManager()) # Needs TrustManager
    mock_hsp_connector = HSPConnector(ai_id="did:hsp:fragmenta_test_ai", broker_address="localhost")
    # In a real scenario, connector would need to be connected. For this test, methods might fail if not connected.

    fragmenta = FragmentaOrchestrator(
        ham_manager=mock_ham,
        llm_interface=mock_llm,
        service_discovery=mock_sdm,
        hsp_connector=mock_hsp_connector,
        config={"default_chunking_threshold": 50,
                "default_text_chunking_params": {"chunk_size": 30, "overlap": 5}}
    )

    # Register Fragmenta's HSP result handler with the mock connector
    # This is how core_services.py should ideally do it.
    if mock_hsp_connector:
        mock_hsp_connector.register_on_task_result_callback(fragmenta._handle_hsp_sub_task_result)


    # Test 1: Simple local LLM processing (short text)
    task_desc_simple = {"goal": "echo input short"}
    input_simple = "This is a short input."
    logger.info(f"\nProcessing simple local task: {task_desc_simple['goal']}")
    result_simple = fragmenta.process_complex_task(task_desc_simple, input_simple)
    logger.info(f"Result for simple task: {result_simple}")

    # Test 2: Local chunking and LLM processing
    task_desc_large_local = {"goal": "summarize large local text"}
    input_large_local = "This is a larger piece of text that definitely should be chunked for local processing. It repeats. " * 3
    logger.info(f"\nProcessing large local text task: {task_desc_large_local['goal']} (length: {len(input_large_local)})")
    result_large_local = fragmenta.process_complex_task(task_desc_large_local, input_large_local)
    logger.info(f"Result for large local text task: {result_large_local}")

    # Test 3: HSP Dispatch (conceptual - requires mock SDM to return a capability and mock HSP connector to "send")
    # Setup a mock capability in SDM
    mock_capability: HSPCapabilityAdvertisementPayload = {
        "capability_id": "mock_hsp_summarizer_v1", "ai_id": "did:hsp:peer_ai_1", "name": "HSPSummarizer",
        "description": "Summarizes text via HSP.", "version": "1.0", "availability_status": "online",
        "tags": ["summary", "hsp"]
    }
    # Manually add to mock_sdm store for testing (as if it was advertised)
    # sdm.process_capability_advertisement would be the normal way.
    # For this direct test, we'll assume it's there.
    # To make this testable, we'd need to mock sdm.get_capability_by_id

    task_desc_hsp = {
        "goal": "summarize via hsp",
        "dispatch_to_hsp_capability_id": "mock_hsp_summarizer_v1", # Hint to use this
        "hsp_task_parameters": {"text_to_summarize": "Some text for the HSP peer to summarize."}
    }
    input_hsp = "This input might be ignored if params are fully in hsp_task_parameters."
    # If your SDM is the real one, you'd need to process an advertisement first
    # For now, this test path might fail if get_capability_by_id in _determine_processing_strategy doesn't find it.
    # To make this test pass without running a full HSP network:
    # 1. Ensure mock_sdm has the capability.
    # 2. Mock hsp_connector.send_task_request to return a correlation_id.
    # 3. Then, manually call fragmenta._handle_hsp_sub_task_result with a mock result.

    logger.info(f"\nProcessing HSP task (conceptual): {task_desc_hsp['goal']}")
    # Simulate SDM finding the capability
    if fragmenta.service_discovery:
        # This direct store manipulation is for test setup only.
        # In real operation, process_capability_advertisement would populate this.
        fragmenta.service_discovery._capabilities_store["mock_hsp_summarizer_v1"] = StoredCapabilityInfo(
             payload=mock_capability, sender_ai_id="did:hsp:peer_ai_1",
             last_seen_timestamp=datetime.now(timezone.utc), message_id="test_msg_hsp_cap"
        )

    # Assume HSP connector is not connected for this offline test, so dispatch will likely fail or return pending
    result_hsp = fragmenta.process_complex_task(task_desc_hsp, input_hsp, complex_task_id="test_hsp_task_001")
    logger.info(f"Initial result for HSP task: {result_hsp}")

    if result_hsp.get("status") == "pending_hsp":
        logger.info("HSP task is pending as expected (connector likely not connected or not receiving actual reply).")
        # To test the result handling part, we would manually call _handle_hsp_sub_task_result:
        mock_hsp_result_payload: HSPTaskResultPayload = {
            "result_id": "res_abc", "request_id": "frag_hsp_req_mock", # This should match the one generated by _dispatch
            "executing_ai_id": "did:hsp:peer_ai_1", "status": "success",
            "payload": {"summary": "This is the HSP summary."}
        }
        mock_hsp_envelope: HSPMessageEnvelope = { # type: ignore
            "correlation_id": result_hsp.get("correlation_id") or result_hsp.get("correlation_ids", [])[0], # Get the actual correlation ID
             # Fill other required envelope fields...
            "hsp_envelope_version": "0.1", "message_id": "hsp_res_msg", "sender_ai_id": "did:hsp:peer_ai_1",
            "recipient_ai_id": fragmenta.hsp_connector.ai_id if fragmenta.hsp_connector else "test_ai",
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": "HSP::TaskResult_v0.1", "protocol_version": "0.1.1",
            "communication_pattern": "response", "payload": mock_hsp_result_payload
        }
        if mock_hsp_envelope["correlation_id"]:
             logger.info(f"Simulating HSP result reception for CorrID: {mock_hsp_envelope['correlation_id']}")
             fragmenta._handle_hsp_sub_task_result(mock_hsp_result_payload, "did:hsp:peer_ai_1", mock_hsp_envelope)

             # After result is handled, re-call process_complex_task for the same ID to continue
             logger.info(f"Re-processing complex task 'test_hsp_task_001' after simulated HSP result.")
             final_hsp_result = fragmenta.process_complex_task(task_description=None, input_data=None, complex_task_id="test_hsp_task_001") # type: ignore
             logger.info(f"Final result for HSP task after simulated callback: {final_hsp_result}")
        else:
            logger.warning("Could not get correlation_id to simulate HSP result.")


    logger.info("\nFragmentaOrchestrator placeholder script finished.")
