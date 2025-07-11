import logging
import uuid
from datetime import datetime, timezone, timedelta # Added timedelta
from typing import Dict, Optional, Any, List, TypedDict, Literal, Union, Tuple

from core_ai.memory.ham_memory_manager import HAMMemoryManager
from services.llm_interface import LLMInterface
from tools.tool_dispatcher import ToolDispatcher
from core_ai.personality.personality_manager import PersonalityManager
from core_ai.emotion_system import EmotionSystem
from core_ai.crisis_system import CrisisSystem
from core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule, StoredCapabilityInfo # Added StoredCapabilityInfo for __main__
from hsp.connector import HSPConnector
from hsp.types import HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
# Import ErrIntrospector for optional integration
try:
    from core_ai.lis.err_introspector import ErrIntrospector
except ImportError:
    ErrIntrospector = None # Allows Fragmenta to run if LIS components are not fully available

logger = logging.getLogger(__name__)

# --- Enhanced State Management TypedDicts ---
class HSPStepDetails(TypedDict):
    step_id: str
    type: Literal["hsp_task"]
    capability_id: str
    target_ai_id: str
    request_parameters: Dict[str, Any]
    input_sources: Optional[List[Dict[str, str]]]
    input_mapping: Optional[Dict[str, Any]]
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
    parameters: Dict[str, Any]
    input_sources: Optional[List[Dict[str, str]]]
    input_mapping: Optional[Dict[str, Any]]
    status: Literal["pending", "in_progress", "completed", "failed", "retrying_local"] # Added "retrying_local"
    result: Optional[Any]
    error_info: Optional[Dict[str, Any]]
    # Fields for retry logic, similar to HSPStepDetails
    max_retries: int
    retries_left: int
    retry_delay_seconds: int
    last_retry_timestamp: Optional[str]

ProcessingStep = Union[HSPStepDetails, LocalStepDetails]

class EnhancedStrategyPlan(TypedDict):
    plan_id: str
    name: str
    steps: List[Union[ProcessingStep, List[ProcessingStep]]]

class EnhancedComplexTaskState(TypedDict):
    complex_task_id: str
    original_task_description: Dict[str, Any]
    original_input_data: Any
    strategy_plan: EnhancedStrategyPlan
    step_results: Dict[str, Any]
    overall_status: Literal["new", "planning", "executing", "waiting_for_hsp",
                            "merging_results", "completed", "failed_plan", "failed_execution"]
    current_executing_step_ids: List[str]
    next_stage_index: int # Renamed from next_step_to_evaluate_index for clarity with stages
    current_step_indices_in_stage: List[int] # Tracks progress within a parallel stage


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
                 err_introspector: Optional['ErrIntrospector'] = None, # Added ErrIntrospector
                 config: Optional[Dict[str, Any]] = None):

        self.ham_manager = ham_manager
        self.tool_dispatcher = tool_dispatcher
        self.llm_interface = llm_interface
        self.service_discovery = service_discovery
        self.hsp_connector = hsp_connector
        self.personality_manager = personality_manager
        self.emotion_system = emotion_system
        self.crisis_system = crisis_system
        self.err_introspector = err_introspector # Store it
        self.config = config or {}

        if ErrIntrospector is None and err_introspector is not None:
            logger.warning("FragmentaOrchestrator: ErrIntrospector provided but class could not be imported. LIS inspection will be disabled.")
            self.err_introspector = None


        self.hsp_task_defaults = self.config.get("hsp_task_defaults", {
            "max_retries": 3, "initial_retry_delay_seconds": 5,
            "retry_backoff_factor": 2, "timeout_seconds": 300
        })
        self.local_task_defaults = self.config.get("local_task_defaults", {
            "max_retries": 0, "initial_retry_delay_seconds": 1 # Default to no retries for local tasks
        })
        self._pending_hsp_sub_tasks: Dict[str, Tuple[str, str]] = {}
        self._complex_task_context: Dict[str, EnhancedComplexTaskState] = {}
        logger.info(f"FragmentaOrchestrator Initialized. Dependencies: HAM={bool(self.ham_manager)}, Tools={bool(self.tool_dispatcher)}, LLM={bool(self.llm_interface)}, SDM={bool(self.service_discovery)}, HSP-Conn={bool(self.hsp_connector)}")

    def process_complex_task(self, task_description: Dict[str, Any], input_data: Any, complex_task_id: Optional[str] = None) -> Dict[str, Any]:
        is_new_task = False
        if complex_task_id is None:
            complex_task_id = f"frag_task_{uuid.uuid4().hex[:8]}"
            is_new_task = True
            logger.info(f"Fragmenta: New complex task (ID: {complex_task_id}). Desc: {str(task_description)[:100]}...")
        elif complex_task_id not in self._complex_task_context:
            logger.error(f"Fragmenta: Unknown complex_task_id '{complex_task_id}' for resumed processing.")
            return {"status": "error", "message": f"Unknown complex_task_id {complex_task_id}", "complex_task_id": complex_task_id}

        if is_new_task:
            input_info = self._analyze_input(input_data)
            strategy_plan = self._determine_processing_strategy(task_description, input_info, complex_task_id)
            self._complex_task_context[complex_task_id] = EnhancedComplexTaskState(
                complex_task_id=complex_task_id,
                original_task_description=task_description, original_input_data=input_data,
                strategy_plan=strategy_plan, step_results={}, overall_status="new", # Start as 'new' before validation
                current_executing_step_ids=[], next_stage_index=0, current_step_indices_in_stage=[]
            )

            if not self._validate_strategy_plan(strategy_plan, complex_task_id):
                task_ctx = self._complex_task_context[complex_task_id]
                task_ctx["overall_status"] = "failed_plan"
                logger.error(f"F (ID: {complex_task_id}): Strategy plan validation failed.")
                return self._get_final_status(task_ctx)

            # If validation passes, move to planning/executing
            self._complex_task_context[complex_task_id]["overall_status"] = "planning"

        return self._advance_complex_task(complex_task_id)

    def _validate_strategy_plan(self, plan: EnhancedStrategyPlan, complex_task_id: str) -> bool:
        all_step_ids_in_plan = set()
        processed_step_ids_for_dependency_check = set()

        if not plan.get("steps"):
            logger.error(f"F_Validate (ID: {complex_task_id}, Plan: {plan['plan_id']}): Plan has no steps.")
            return False

        for i, stage_item in enumerate(plan["steps"]):
            current_stage_steps: List[ProcessingStep] = stage_item if isinstance(stage_item, list) else [stage_item] # type: ignore

            current_stage_step_ids = set()
            for step_detail in current_stage_steps:
                step_id = step_detail.get("step_id")
                if not step_id:
                    logger.error(f"F_Validate (ID: {complex_task_id}, Plan: {plan['plan_id']}, Stage: {i}): Step found without a step_id.")
                    return False
                if step_id in all_step_ids_in_plan:
                    logger.error(f"F_Validate (ID: {complex_task_id}, Plan: {plan['plan_id']}, Stage: {i}): Duplicate step_id '{step_id}' found.")
                    return False
                all_step_ids_in_plan.add(step_id)
                current_stage_step_ids.add(step_id)

                step_type = step_detail.get("type")
                if step_type not in ["hsp_task", "local_tool", "local_llm", "local_chunk_process"]:
                    logger.error(f"F_Validate (ID: {complex_task_id}, Plan: {plan['plan_id']}, Step: {step_id}): Invalid step type '{step_type}'.")
                    return False

                # Validate input_sources
                if step_detail.get("input_sources"):
                    for source_info in step_detail["input_sources"]:
                        source_step_id = source_info.get("step_id")
                        if not source_step_id:
                            logger.error(f"F_Validate (ID: {complex_task_id}, Plan: {plan['plan_id']}, Step: {step_id}): Input source missing 'step_id'.")
                            return False
                        if source_step_id == step_id: # Self-dependency
                            logger.error(f"F_Validate (ID: {complex_task_id}, Plan: {plan['plan_id']}, Step: {step_id}): Step '{step_id}' cannot have itself as an input source.")
                            return False
                        if source_step_id not in processed_step_ids_for_dependency_check:
                            # This check ensures source_step_id comes from a *previous* stage or *earlier within the same parallel stage* (though true parallel check is tricky here)
                            # For simplicity, we're primarily checking against already fully processed stages for sequential plans.
                            # A more robust check for parallel stages would ensure sources are not from later stages or from steps defined later in the same parallel list.
                            # However, the current logic of _prepare_step_input dynamically checks statuses, so this is a structural pre-check.
                            logger.warning(f"F_Validate (ID: {complex_task_id}, Plan: {plan['plan_id']}, Step: {step_id}): Input source step '{source_step_id}' not found in previously processed steps or stages. This might be an issue for non-parallel plans or if it's a forward reference within a parallel stage.")
                            # Not returning False here as _prepare_step_input will be the ultimate gatekeeper for readiness.
                            # This is more of a structural sanity check. A strict check would be:
                            # if source_step_id not in processed_step_ids_for_dependency_check and source_step_id not in current_stage_step_ids (for parallel cases where order might not be guaranteed):
                            #    logger.error(f"F_Validate (ID: {complex_task_id}, Plan: {plan['plan_id']}, Step: {step_id}): Input source step '{source_step_id}' is a forward reference or not found.")
                            #    return False

            # After processing all steps in a stage, add their IDs to the set of processed steps
            processed_step_ids_for_dependency_check.update(current_stage_step_ids)

        logger.info(f"F_Validate (ID: {complex_task_id}, Plan: {plan['plan_id']}): Plan validation successful.")
        return True

    def _find_step_index(self, steps: List[ProcessingStep], step_id: str) -> int:
        for i, step in enumerate(steps):
            if step["step_id"] == step_id: return i
        raise ValueError(f"Step with ID '{step_id}' not found in plan.")

    def _prepare_step_input(self, step_detail: ProcessingStep, task_ctx: EnhancedComplexTaskState) -> Tuple[Any, bool, bool]:
        prepared_inputs_map: Dict[str, Any] = {}
        dependencies_met = True
        dependency_failure = False
        if not step_detail.get("input_sources"):
            return prepared_inputs_map, True, False
        for source_info in step_detail["input_sources"]:
            source_step_id = source_info["step_id"]
            source_output_key = source_info.get("output_key")
            source_step_plan_detail: Optional[ProcessingStep] = None
            for stage_item in task_ctx["strategy_plan"]["steps"]:
                current_steps_to_check = stage_item if isinstance(stage_item, list) else [stage_item]
                for s_detail in current_steps_to_check:
                    if s_detail["step_id"] == source_step_id:
                        source_step_plan_detail = s_detail; break
                if source_step_plan_detail: break
            if not source_step_plan_detail:
                logger.error(f"F (ID: {task_ctx['complex_task_id']}, S: {step_detail['step_id']}): Input source step '{source_step_id}' not found in plan.")
                dependencies_met = False; dependency_failure = True; break
            if source_step_plan_detail["status"] == "failed":
                logger.warning(f"F (ID: {task_ctx['complex_task_id']}, S: {step_detail['step_id']}): Dependency '{source_step_id}' failed.")
                dependencies_met = False; dependency_failure = True; break
            if source_step_plan_detail["status"] != "completed":
                logger.debug(f"F (ID: {task_ctx['complex_task_id']}, S: {step_detail['step_id']}): Dependency '{source_step_id}' not completed (status: {source_step_plan_detail['status']}).")
                dependencies_met = False; break
            source_result = task_ctx["step_results"].get(source_step_id)
            if source_result is None and source_step_plan_detail["status"] == "completed":
                 logger.warning(f"F (ID: {task_ctx['complex_task_id']}, S: {step_detail['step_id']}): Dependency '{source_step_id}' completed but result is None.")
            input_key_prefix = f"{source_step_id}"
            if source_output_key:
                if isinstance(source_result, dict): prepared_inputs_map[f"{input_key_prefix}.{source_output_key}"] = source_result.get(source_output_key)
                else: logger.warning(f"F (ID: {task_ctx['complex_task_id']}, S: {step_detail['step_id']}): Source '{source_step_id}' result not dict for key '{source_output_key}'."); prepared_inputs_map[f"{input_key_prefix}.{source_output_key}"] = None
            else: prepared_inputs_map[input_key_prefix] = source_result
        return prepared_inputs_map, dependencies_met, dependency_failure

    def _execute_or_dispatch_step(self, complex_task_id: str, step_to_execute: ProcessingStep,
                                 current_step_input_map: Dict[str, Any], task_ctx: EnhancedComplexTaskState) -> None:
        step_id = step_to_execute["step_id"]; effective_params = step_to_execute["parameters"].copy()
        if step_to_execute.get("input_mapping"):
            for target_param, source_template in step_to_execute["input_mapping"].items():
                if isinstance(source_template, str):
                    format_context = current_step_input_map.copy(); format_context["$original_input"] = task_ctx["original_input_data"]; format_context["$task_description"] = task_ctx["original_task_description"]
                    try:
                        if source_template.startswith("{") and source_template.endswith("}") and source_template[1:-1] in format_context: effective_params[target_param] = format_context[source_template[1:-1]]
                        else:
                            val_to_set = source_template
                            for k, v in format_context.items(): placeholder = "{" + k + "}"; val_to_set = val_to_set.replace(placeholder, str(v)) if placeholder in val_to_set else val_to_set
                            effective_params[target_param] = val_to_set
                    except Exception as e: logger.error(f"F (ID: {complex_task_id}, S: {step_id}): Input mapping error for '{target_param}': {e}. Template: '{source_template}'"); step_to_execute["status"] = "failed"; step_to_execute["error_info"] = {"message": f"Input mapping error: {e}"}; return
                else: effective_params[target_param] = source_template
        step_to_execute["parameters"] = effective_params
        if step_to_execute["type"] == "hsp_task":
            hsp_step_details = step_to_execute; hsp_step_details["request_parameters"] = effective_params
            logger.info(f"F (ID: {complex_task_id}, S: {step_id}): Dispatching HSP task with params: {str(effective_params)[:100]}...")
            self._dispatch_hsp_sub_task(complex_task_id, step_id, hsp_step_details)
            if hsp_step_details["status"] == "dispatched": task_ctx["overall_status"] = "waiting_for_hsp"
        elif step_to_execute["type"] in ["local_tool", "local_llm", "local_chunk_process"]:
            local_step_details = step_to_execute; local_step_details["status"] = "in_progress"
            logger.info(f"F (ID: {complex_task_id}, S: {step_id}): Executing local '{local_step_details['tool_or_model_name']}' with params: {str(effective_params)[:100]}...")
            try:
                step_input_data = current_step_input_map if current_step_input_map else task_ctx["original_input_data"] # Simplified input choice
                if local_step_details["type"] == "local_chunk_process":
                    all_chunks = self._chunk_data(step_input_data, local_step_details["parameters"].get("chunking_params"))
                    chunk_results = [self._dispatch_chunk_to_processing(chunk, {"tool_or_model": local_step_details["tool_or_model_name"], "params": local_step_details["parameters"]}, complex_task_id, i, len(all_chunks)) for i, chunk in enumerate(all_chunks)]
                    local_step_details["result"] = chunk_results # Assuming chunk processing itself handles internal errors or returns partial success
                else:
                    local_step_details["result"] = self._dispatch_chunk_to_processing(step_input_data, {"tool_or_model": local_step_details["tool_or_model_name"], "params": local_step_details["parameters"]}, complex_task_id, 0, 1)

                # Check if _dispatch_chunk_to_processing indicated an error (e.g. by returning specific error object or None)
                # For simplicity, we'll assume _dispatch_chunk_to_processing raises an exception on failure, caught below.
                local_step_details["status"] = "completed"; task_ctx["step_results"][step_id] = local_step_details["result"]

            except Exception as e:
                logger.error(f"F (ID: {complex_task_id}, S: {step_id}): Local step execution failed: {e}", exc_info=True)
                if local_step_details["retries_left"] > 0:
                    local_step_details["status"] = "retrying_local"
                    local_step_details["error_info"] = {"message": str(e), "reason": "Execution error, will retry"}
                    # Retries_left will be decremented in _advance_complex_task
                else:
                    local_step_details["status"] = "failed"
                    local_step_details["error_info"] = {"message": str(e), "reason": "Execution error, no retries left"}
        else:
            logger.error(f"F (ID: {complex_task_id}, S: {step_id}): Unknown step type: {step_to_execute['type']}")
            step_to_execute["status"] = "failed"; step_to_execute["error_info"] = {"message": f"Unknown step type {step_to_execute['type']}"} # type: ignore

    def _advance_complex_task(self, complex_task_id: str) -> Dict[str, Any]:
        task_ctx = self._complex_task_context.get(complex_task_id)
        if not task_ctx: return {"status": "error", "message": f"Context lost for task {complex_task_id}", "complex_task_id": complex_task_id}
        if task_ctx["overall_status"] == "planning": task_ctx["overall_status"] = "executing"
        if task_ctx["overall_status"] in ["completed", "failed_execution", "failed_plan"]: return self._get_final_status(task_ctx)

        plan = task_ctx["strategy_plan"]
        while task_ctx["next_stage_index"] < len(plan["steps"]):
            current_stage_idx = task_ctx["next_stage_index"]
            stage_item = plan["steps"][current_stage_idx]
            steps_in_stage: List[ProcessingStep] = stage_item if isinstance(stage_item, list) else [stage_item] # type: ignore

            all_steps_in_stage_processed_or_blocked = True
            any_step_in_stage_active_or_retrying = False # Dispatched, awaiting_result, retrying, in_progress

            for step_detail in steps_in_stage:
                step_id = step_detail["step_id"]
                if step_detail["status"] in ["completed", "failed"]: continue # Already terminal

                # Check for permanent failure (no retries left)
                if step_detail["status"] in ["failed_dispatch", "failed_response", "timeout_error"] and step_detail["type"] == "hsp_task" and step_detail["retries_left"] == 0:
                    logger.error(f"F (ID: {complex_task_id}, S: {step_id}): HSP step failed permanently."); task_ctx["overall_status"] = "failed_execution"; return self._get_final_status(task_ctx)
                if step_detail["status"] == "failed" and step_detail["type"] != "hsp_task" and step_detail["retries_left"] == 0 : # Covers local steps that have failed and no retries left
                    logger.error(f"F (ID: {complex_task_id}, S: {step_id}): Local step failed permanently."); task_ctx["overall_status"] = "failed_execution"; return self._get_final_status(task_ctx)

                # Prepare inputs and check dependencies
                prepared_input_map, deps_met, dep_failure = self._prepare_step_input(step_detail, task_ctx)
                if dep_failure: task_ctx["overall_status"] = "failed_execution"; return self._get_final_status(task_ctx)
                if not deps_met: all_steps_in_stage_processed_or_blocked = False; continue # Cannot run this step yet

                # Handle HSP step specific pre-dispatch logic (timeout, retry timing)
                if step_detail["type"] == "hsp_task":
                    hsp_step = step_detail # type: HSPStepDetails
                    if hsp_step["status"] in ["dispatched", "awaiting_result"] and hsp_step["dispatch_timestamp"]:
                        dispatch_time = datetime.fromisoformat(hsp_step["dispatch_timestamp"])
                        if datetime.now(timezone.utc) - dispatch_time > timedelta(seconds=self.hsp_task_defaults["timeout_seconds"]):
                            hsp_step["status"] = "timeout_error"; hsp_step["error_info"] = {"message": "HSP task timed out."}

                    if hsp_step["status"] == "retrying" and hsp_step["last_retry_timestamp"]:
                        last_retry_ts = datetime.fromisoformat(hsp_step["last_retry_timestamp"])
                        # HSP uses exponential backoff, for local we can use a simpler fixed delay or make it configurable
                        delay = hsp_step["retry_delay_seconds"] * (self.hsp_task_defaults["retry_backoff_factor"] ** (hsp_step["max_retries"] - hsp_step["retries_left"] -1))
                        if datetime.now(timezone.utc) - last_retry_ts < timedelta(seconds=delay):
                            any_step_in_stage_active_or_retrying = True; all_steps_in_stage_processed_or_blocked = False; continue

                # Handle Local step specific pre-dispatch logic (retry timing)
                elif step_detail["type"] != "hsp_task" and step_detail["status"] == "retrying_local" and step_detail["last_retry_timestamp"]: # type: ignore
                    local_step_retrying = step_detail # type: LocalStepDetails
                    last_retry_ts = datetime.fromisoformat(local_step_retrying["last_retry_timestamp"])
                    # Using fixed delay for local steps for now
                    if datetime.now(timezone.utc) - last_retry_ts < timedelta(seconds=local_step_retrying["retry_delay_seconds"]):
                        any_step_in_stage_active_or_retrying = True; all_steps_in_stage_processed_or_blocked = False; continue


                # Execute or Dispatch if ready
                # For HSP: pending_dispatch, or retryable failures with retries left
                # For Local: pending, or retrying_local with retries left
                is_hsp_retryable = step_detail["type"] == "hsp_task" and \
                                   step_detail["status"] in ["retrying", "failed_dispatch", "failed_response", "timeout_error"] and \
                                   step_detail["retries_left"] > 0
                is_local_retryable = step_detail["type"] != "hsp_task" and \
                                     step_detail["status"] == "retrying_local" and \
                                     step_detail["retries_left"] > 0 # type: ignore

                if step_detail["status"] in ["pending", "pending_dispatch"] or is_hsp_retryable or is_local_retryable:
                    if is_hsp_retryable and step_detail["status"] != "pending_dispatch": # Is an HSP retryable failure
                        step_detail["retries_left"] -=1; step_detail["status"] = "retrying"; step_detail["last_retry_timestamp"] = datetime.now(timezone.utc).isoformat()
                        logger.info(f"F (ID: {complex_task_id}, S: {step_id}): Retrying HSP. Left: {step_detail['retries_left']}.")
                        any_step_in_stage_active_or_retrying = True; all_steps_in_stage_processed_or_blocked = False; continue

                    elif is_local_retryable: # Is a Local retryable failure
                        local_step_to_retry = step_detail # type: LocalStepDetails
                        local_step_to_retry["retries_left"] -= 1
                        local_step_to_retry["status"] = "pending" # Reset to pending for re-execution by _execute_or_dispatch_step
                        local_step_to_retry["last_retry_timestamp"] = datetime.now(timezone.utc).isoformat()
                        logger.info(f"F (ID: {complex_task_id}, S: {step_id}): Retrying Local Step. Left: {local_step_to_retry['retries_left']}.")
                        # _execute_or_dispatch_step will be called below for this "pending" step

                    self._execute_or_dispatch_step(complex_task_id, step_detail, prepared_input_map, task_ctx)

                # After execution attempt, check status
                if step_detail["status"] in ["dispatched", "awaiting_result", "retrying", "in_progress", "retrying_local"]:
                    any_step_in_stage_active_or_retrying = True; all_steps_in_stage_processed_or_blocked = False
                elif step_detail["status"] not in ["completed", "failed"]: # Still pending for other reasons
                    all_steps_in_stage_processed_or_blocked = False


            if not all_steps_in_stage_processed_or_blocked: # Some steps in stage are not terminal and/or waiting
                task_ctx["overall_status"] = "waiting_for_hsp" if any_step_in_stage_active_or_retrying and any(s["type"]=="hsp_task" and s["status"] in ["dispatched", "awaiting_result", "retrying"] for s in steps_in_stage) else "executing"
                return self._get_final_status(task_ctx) # Wait for next event or tick

            # If all steps in stage are terminal (completed or permanently failed)
            task_ctx["next_stage_index"] +=1

        # All stages processed
        task_ctx["overall_status"] = "merging_results"
        # Simplified final result: result of the very last step in the plan
        final_step_in_plan = plan["steps"][-1]
        final_step_id_in_plan = final_step_in_plan[0]["step_id"] if isinstance(final_step_in_plan, list) else final_step_in_plan["step_id"]
        final_result = task_ctx["step_results"].get(final_step_id_in_plan) # type: ignore
        task_ctx["overall_status"] = "completed"
        return {"status": "completed", "result": final_result, "complex_task_id": complex_task_id}


    def _get_final_status(self, task_ctx: EnhancedComplexTaskState) -> Dict[str, Any]:
        response: Dict[str, Any] = {"status": task_ctx["overall_status"], "complex_task_id": task_ctx["complex_task_id"]}
        if task_ctx["overall_status"] == "waiting_for_hsp":
            active_corr_ids = [ s["correlation_id"] for stage in task_ctx["strategy_plan"]["steps"] for s in (stage if isinstance(stage, list) else [stage]) if s["type"] == "hsp_task" and s.get("correlation_id") and s["status"] in ["dispatched", "awaiting_result"] ] # type: ignore
            if active_corr_ids: response["correlation_ids"] = active_corr_ids
        if task_ctx["overall_status"] == "failed_execution":
            response["message"] = "One or more steps failed permanently."; response["step_results"] = task_ctx["step_results"]

        # Store task outcome in HAM if terminal state reached
        if task_ctx["overall_status"] in ["completed", "failed_execution", "failed_plan"]:
            self._store_task_outcome_in_ham(task_ctx)

        # If task completed successfully, and ErrIntrospector is available, inspect output
        if task_ctx["overall_status"] == "completed" and self.err_introspector and ErrIntrospector is not None:
            final_result_for_inspection = response.get("result") # Result from the current response dict
            if final_result_for_inspection is not None:
                try:
                    logger.info(f"F (ID: {task_ctx['complex_task_id']}): Task completed. Triggering ErrIntrospector inspection.")
                    # Conversation history might not be directly available to Fragmenta tasks.
                    # Passing None or an empty list for now.
                    # Task description is passed for context.
                    incident_id = self.err_introspector.inspect_fragmenta_output(
                        complex_task_id=task_ctx['complex_task_id'],
                        task_description=task_ctx['original_task_description'],
                        fragmenta_output=final_result_for_inspection,
                        conversation_history=[] # Placeholder for now
                    )
                    if incident_id:
                        logger.info(f"F (ID: {task_ctx['complex_task_id']}): ErrIntrospector created LIS incident {incident_id}.")
                    else:
                        logger.warning(f"F (ID: {task_ctx['complex_task_id']}): ErrIntrospector inspection did not result in an LIS incident.")
                except Exception as e:
                    logger.error(f"F (ID: {task_ctx['complex_task_id']}): Error during ErrIntrospector inspection: {e}", exc_info=True)
            else:
                logger.info(f"F (ID: {task_ctx['complex_task_id']}): Task completed, but no final result in response for ErrIntrospector inspection.")

        return response

    def _store_task_outcome_in_ham(self, task_ctx: EnhancedComplexTaskState) -> None:
        if not self.ham_manager:
            logger.warning(f"F (ID: {task_ctx['complex_task_id']}): HAMMemoryManager not available. Cannot store task outcome.")
            return

        description_summary = str(task_ctx['original_task_description'].get('goal', task_ctx['original_task_description'].get('name', 'N/A')))[:256]

        outcome_details_str = "Task completed."
        final_step_in_plan = None
        if task_ctx["strategy_plan"]["steps"]:
            last_stage_item = task_ctx["strategy_plan"]["steps"][-1]
            final_step_in_plan = last_stage_item[0] if isinstance(last_stage_item, list) and last_stage_item else (last_stage_item if not isinstance(last_stage_item, list) else None)

        if task_ctx["overall_status"] == "completed" and final_step_in_plan:
            final_result = task_ctx["step_results"].get(final_step_in_plan["step_id"]) # type: ignore
            outcome_details_str = f"Completed successfully. Final step '{final_step_in_plan['step_id']}' result type: {type(final_result).__name__}, summary: {str(final_result)[:128]}"
        elif task_ctx["overall_status"] == "failed_execution":
            failed_step_ids = [
                s["step_id"] for stage in task_ctx["strategy_plan"]["steps"]
                for s in (stage if isinstance(stage, list) else [stage]) # type: ignore
                if s["status"] == "failed" or (s.get("retries_left") == 0 and s["status"] not in ["completed", "pending", "pending_dispatch"]) # type: ignore
            ]
            first_failed_step_id = failed_step_ids[0] if failed_step_ids else "unknown"
            # Try to get error message from the first failed step
            error_message = "Unknown error."
            for stage in task_ctx["strategy_plan"]["steps"]:
                for step_detail_item in (stage if isinstance(stage, list) else [stage]): # type: ignore
                    if step_detail_item["step_id"] == first_failed_step_id:
                        error_info = step_detail_item.get("error_info")
                        if error_info and isinstance(error_info, dict):
                            error_message = error_info.get("message", "No error message provided.")
                        break
                if error_message != "Unknown error.": break
            outcome_details_str = f"Failed execution. First failed step: '{first_failed_step_id}'. Error: {str(error_message)[:256]}"

        elif task_ctx["overall_status"] == "failed_plan":
            outcome_details_str = f"Failed due to plan issue. Plan ID: {task_ctx['strategy_plan']['plan_id']}"

        all_step_statuses = {}
        for stage in task_ctx["strategy_plan"]["steps"]:
            for step_detail in (stage if isinstance(stage, list) else [stage]): # type: ignore
                 all_step_statuses[step_detail["step_id"]] = step_detail["status"]

        task_outcome_payload = {
            "complex_task_id": task_ctx["complex_task_id"],
            "original_task_description_summary": description_summary,
            "strategy_plan_id": task_ctx["strategy_plan"]["plan_id"],
            "strategy_plan_name": task_ctx["strategy_plan"]["name"],
            "final_status": task_ctx["overall_status"],
            "timestamp_concluded": datetime.now(timezone.utc).isoformat(),
            "input_data_info": self._analyze_input(task_ctx["original_input_data"]), # Re-analyze or store initial analysis
            "outcome_details": outcome_details_str,
            "all_step_statuses": all_step_statuses
        }


        # Extract keywords from description_summary for HAM metadata
        summary_keywords = []
        if isinstance(description_summary, str):
            # Simple keyword extraction: lowercase, split, take unique, first N words (e.g., up to 5)
            # More sophisticated keyword extraction could be used in the future.
            words = [word.strip(".,!?;:'\"()") for word in description_summary.lower().split()]
            unique_words = []
            for word in words:
                if word and word not in unique_words: # Basic stopword removal could be added here
                    unique_words.append(word)
            summary_keywords = unique_words[:5]

        ham_metadata = {
            "source_module": "FragmentaOrchestrator",
            "complex_task_id_ref": task_ctx["complex_task_id"], # For potential direct HAM query on this ID
            "task_description_keywords": summary_keywords,
            "strategy_plan_name_ref": task_ctx["strategy_plan"]["name"], # Add plan name for easier filtering
            "final_status_ref": task_ctx["overall_status"] # Add final status for easier filtering
        }

        try:
            mem_id = self.ham_manager.store_experience(
                raw_data=task_outcome_payload,
                data_type="fragmenta_task_outcome_v0.1",
                metadata=ham_metadata # type: ignore
            )
            if mem_id:
                logger.info(f"F (ID: {task_ctx['complex_task_id']}): Stored task outcome in HAM (MemID: {mem_id}).")
            else:
                logger.error(f"F (ID: {task_ctx['complex_task_id']}): Failed to store task outcome in HAM.")
        except Exception as e:
            logger.error(f"F (ID: {task_ctx['complex_task_id']}): Exception storing task outcome in HAM: {e}", exc_info=True)


    def _analyze_input(self, input_data: any) -> dict: # Keep as is
        input_type = "unknown"; input_size = 0
        if isinstance(input_data, str): input_type = "text"; input_size = len(input_data)
        elif isinstance(input_data, (list, dict)): input_type = "structured_data"; input_size = len(str(input_data))
        return {"type": input_type, "size": input_size, "content_preview": str(input_data)[:100]}

    def _determine_processing_strategy(self, task_description: Dict[str, Any], input_info: Dict[str, Any], complex_task_id: str) -> EnhancedStrategyPlan:
        task_goal_summary = str(task_description.get('goal', task_description.get('name', 'N/A')))[:128]
        logger.debug(f"F (ID: {complex_task_id}): Determining strategy for task: {task_goal_summary}")

        # --- Query HAM for past outcomes of similar tasks (Conceptual V1 - Logging only) ---
        if self.ham_manager:
            # Extract 1-2 primary keywords from the current task's goal summary for HAM metadata query.
            current_task_raw_keywords = [kw.strip(".,!?;:'\"()") for kw in task_goal_summary.lower().split() if kw.strip(".,!?;:'\"()")]
            # Filter out very short words, could also use a stopword list here.
            current_task_filtered_keywords = [kw for kw in current_task_raw_keywords if len(kw) > 2]
            # Take up to 2 unique, primary keywords for querying.
            query_keywords_for_ham_metadata = list(set(current_task_filtered_keywords))[:2]

            all_retrieved_past_outcomes: List[Any] = [] # Stores HAMRecallResult objects
            processed_ham_ids_for_aggregation = set() # To avoid duplicates if multiple keywords match same outcome

            if query_keywords_for_ham_metadata:
                logger.info(f"F (ID: {complex_task_id}): Will query HAM for past outcomes using metadata_filters with keywords: {query_keywords_for_ham_metadata}")
                for keyword in query_keywords_for_ham_metadata:
                    # This query relies on HAMMemoryManager.query_core_memory's metadata_filters
                    # being able to check if 'keyword' is contained within the list stored in
                    # the 'task_description_keywords' metadata field of HAM entries.
                    # If HAM only supports exact match for list metadata fields, this specific query might need HAM enhancement.
                    # For now, this demonstrates the intended targeted query.
                    metadata_filter_query = {"task_description_keywords": keyword}
                    logger.debug(f"F (ID: {complex_task_id}): Attempting HAM query with filter: {metadata_filter_query}")
                    try:
                        retrieved_for_keyword = self.ham_manager.query_core_memory(
                            metadata_filters=metadata_filter_query,
                            data_type_filter="fragmenta_task_outcome_v0.1",
                            limit=5 # Get a few results per keyword
                        )
                        if retrieved_for_keyword:
                            logger.debug(f"F (ID: {complex_task_id}): HAM query for keyword '{keyword}' returned {len(retrieved_for_keyword)} items.")
                            for item in retrieved_for_keyword:
                                ham_id = item.get("id")
                                if ham_id and ham_id not in processed_ham_ids_for_aggregation:
                                    all_retrieved_past_outcomes.append(item)
                                    processed_ham_ids_for_aggregation.add(ham_id)
                        else:
                            logger.debug(f"F (ID: {complex_task_id}): HAM query for keyword '{keyword}' returned no items.")
                    except Exception as e_query:
                         logger.error(f"F (ID: {complex_task_id}): Exception during HAM query for keyword '{keyword}': {e_query}", exc_info=True)

            if all_retrieved_past_outcomes:
                logger.info(f"F (ID: {complex_task_id}): Aggregated {len(all_retrieved_past_outcomes)} unique past task outcomes from HAM queries.")
                for outcome_recall_result in all_retrieved_past_outcomes: # Log details of what was found
                    if isinstance(outcome_recall_result.get("rehydrated_gist"), dict):
                        past_payload = outcome_recall_result["rehydrated_gist"]
                        logger.info(f"  - Past Task ID: {past_payload.get('complex_task_id')}, Strategy: {past_payload.get('strategy_plan_name')}, Status: {past_payload.get('final_status')}")
                    else:
                        logger.warning(f"  - Past outcome (MemID: {outcome_recall_result.get('id')}) gist not a dict: {type(outcome_recall_result.get('rehydrated_gist'))}")

            # --- Basic Adaptive Logic based on past_outcomes ---
            problematic_past_strategy_names: List[str] = []
            if all_retrieved_past_outcomes:
                strategy_failure_counts: Dict[str, int] = {}
                for outcome_recall_result in all_retrieved_past_outcomes: # Iterate over the aggregated list
                    if isinstance(outcome_recall_result.get("rehydrated_gist"), dict):
                        past_payload = outcome_recall_result["rehydrated_gist"]
                        past_strategy_name = past_payload.get('strategy_plan_name')
                        past_status = past_payload.get('final_status')
                        if past_strategy_name and past_status == "failed_execution":
                            strategy_failure_counts[past_strategy_name] = strategy_failure_counts.get(past_strategy_name, 0) + 1

                    # Identify strategies that failed frequently (e.g., more than once for this simple heuristic)
                    for name, count in strategy_failure_counts.items():
                        if count > 1: # Arbitrary threshold for "frequent failure"
                            problematic_past_strategy_names.append(name)
                            logger.info(f"F (ID: {complex_task_id}): Strategy '{name}' identified as problematic (failed {count} times) for similar past tasks.")

            except Exception as e:
                logger.error(f"F (ID: {complex_task_id}): Error processing past task outcomes from HAM: {e}", exc_info=True)
        # --- End HAM Query & Basic Adaptive Logic Section ---

        steps: List[ProcessingStep] = []; plan_name = "default_single_step_plan"; plan_id = f"plan_{complex_task_id}_{uuid.uuid4().hex[:4]}"

        # --- Standard Strategy Determination Logic ---
        # This logic will now be influenced by `problematic_past_strategy_names`

        # 1. HSP Dispatch based on direct request
        if task_description.get("dispatch_to_hsp_capability_id"):
            tentative_plan_name = "dispatch_to_hsp_capability"
            if tentative_plan_name in problematic_past_strategy_names:
                logger.warning(f"F (ID: {complex_task_id}): Default strategy '{tentative_plan_name}' was problematic in the past. Skipping direct HSP dispatch based on task_description field.")
            elif not self.service_discovery or not self.hsp_connector:
                plan_name = "error_hsp_unavailable" # This will likely be caught by validation or result in failure
            else:
                cap_id = task_description["dispatch_to_hsp_capability_id"]
                capability = self.service_discovery.get_capability_by_id(cap_id, exclude_unavailable=True)
                if capability and capability.get("ai_id"):
                    plan_name = tentative_plan_name # Use the good name
                    steps.append(HSPStepDetails(step_id=f"{plan_id}_s0_hsp", type="hsp_task", capability_id=cap_id, target_ai_id=capability["ai_id"], request_parameters=task_description.get("hsp_task_parameters",{}), input_sources=None,input_mapping=None,status="pending_dispatch",correlation_id=None,dispatch_timestamp=None,result=None,error_info=None,max_retries=self.hsp_task_defaults["max_retries"],retries_left=self.hsp_task_defaults["max_retries"],retry_delay_seconds=self.hsp_task_defaults["initial_retry_delay_seconds"],last_retry_timestamp=None))
                else:
                    plan_name = f"error_hsp_cap_unavailable_{cap_id}"
                    steps.append(HSPStepDetails(step_id=f"{plan_id}_s0_hsp_fail",type="hsp_task",capability_id=cap_id,target_ai_id="unknown",request_parameters={},input_sources=None,input_mapping=None,status="failed_dispatch",correlation_id=None,dispatch_timestamp=None,result=None,error_info={"message":f"Cap '{cap_id}' not found"},max_retries=0,retries_left=0,retry_delay_seconds=0,last_retry_timestamp=None))

        # 2. Local Tool Call based on direct request (if no HSP step was added yet)
        if not steps and task_description.get("requested_tool"):
            rt = task_description["requested_tool"]
            tentative_plan_name = f"direct_tool_call_{rt}"
            if tentative_plan_name in problematic_past_strategy_names:
                logger.warning(f"F (ID: {complex_task_id}): Default strategy '{tentative_plan_name}' was problematic in the past. Skipping direct tool call.")
            else:
                plan_name = tentative_plan_name
                steps.append(LocalStepDetails(step_id=f"{plan_id}_s0_local",type="local_tool",tool_or_model_name=rt,parameters=task_description.get("tool_params",{}),input_sources=None,input_mapping=None,status="pending",result=None,error_info=None, max_retries=self.local_task_defaults["max_retries"], retries_left=self.local_task_defaults["max_retries"], retry_delay_seconds=self.local_task_defaults["initial_retry_delay_seconds"], last_retry_timestamp=None))

        # 3. Default local processing (chunking or direct LLM) if no specific dispatch/tool request filled `steps`
        if not steps:
            if input_info.get("type") == "text" and input_info.get("size",0) > self.config.get("default_chunking_threshold",1000):
                tentative_plan_name = "chunk_summarize_local"
                if tentative_plan_name in problematic_past_strategy_names:
                    logger.warning(f"F (ID: {complex_task_id}): Default strategy '{tentative_plan_name}' was problematic. Falling through (may lead to direct_llm_local or error).")
                    # If chunking was problematic, maybe direct LLM is the fallback, or it will hit the final default.
                else:
                    plan_name = tentative_plan_name
                    steps.append(LocalStepDetails(step_id=f"{plan_id}_s0_chunk",type="local_chunk_process",tool_or_model_name="llm_summarize_chunk",parameters={"chunking_params": self.config.get("default_text_chunking_params"), "merging_params":{"method":"join_with_newline"}},input_sources=None,input_mapping=None,status="pending",result=None,error_info=None, max_retries=self.local_task_defaults["max_retries"], retries_left=self.local_task_defaults["max_retries"], retry_delay_seconds=self.local_task_defaults["initial_retry_delay_seconds"], last_retry_timestamp=None))

            if not steps: # If chunking wasn't chosen or was skipped due to past failures
                tentative_plan_name = "direct_llm_local"
                if tentative_plan_name in problematic_past_strategy_names:
                     logger.warning(f"F (ID: {complex_task_id}): Default strategy '{tentative_plan_name}' was problematic. No further fallbacks, may lead to error_no_steps.")
                else:
                    plan_name = tentative_plan_name
                    steps.append(LocalStepDetails(step_id=f"{plan_id}_s0_llm",type="local_llm",tool_or_model_name="llm_direct_process",parameters={},input_sources=None,input_mapping=None,status="pending",result=None,error_info=None, max_retries=self.local_task_defaults["max_retries"], retries_left=self.local_task_defaults["max_retries"], retry_delay_seconds=self.local_task_defaults["initial_retry_delay_seconds"], last_retry_timestamp=None))

        # 4. Final fallback if no steps were generated by any logic above
        if not steps:
            plan_name="error_no_steps"
            steps.append(LocalStepDetails(step_id=f"{plan_id}_s0_err",type="local_llm",tool_or_model_name="error",parameters={},input_sources=None,input_mapping=None,status="failed",result=None,error_info={"message":"No steps generated"}, max_retries=0, retries_left=0, retry_delay_seconds=0, last_retry_timestamp=None)) # No retries for error step

        return EnhancedStrategyPlan(plan_id=plan_id, name=plan_name, steps=steps)

    def _chunk_data(self, data: any, chunking_params: Optional[Dict[str, Any]] = None) -> list: # Keep as is
        if not isinstance(data, str) or not chunking_params: return [data]
        cs, ov = chunking_params.get("chunk_size",100), chunking_params.get("overlap",10); chunks, start = [], 0
        while start < len(data): end = min(start+cs, len(data)); chunks.append(data[start:end]); start += (cs-ov) if end != len(data) else cs
        return chunks if chunks else [data]

    def _dispatch_chunk_to_processing(self, chunk: any, strategy_step: Dict[str, Any], task_id: str, chunk_index: int, total_chunks: int) -> Any: # Keep as is
        tool_name, params = strategy_step.get("tool_or_model","identity"), strategy_step.get("params",{})
        logger.info(f"F (TID:{task_id}): Dispatching chunk {chunk_index+1}/{total_chunks} to '{tool_name}'.")
        res = None
        if "llm" in tool_name: res = self.llm_interface.generate_response(f"Task({task_id}),Chunk({chunk_index+1}/{total_chunks}): {str(chunk)}",params) if self.llm_interface else f"[LLM N/A - {str(chunk)[:30]}]"
        elif tool_name=="identity": res=chunk
        elif self.tool_dispatcher: tr=self.tool_dispatcher.dispatch(str(chunk),tool_name,**params); res = tr.get("payload") if isinstance(tr,dict) and tr.get("status")=="success" else f"[{tool_name} err: {str(tr)[:100]}]"
        else: res = f"[UnknownProcessor '{tool_name}' - {str(chunk)[:30]}]"
        if self.ham_manager and res is not None:
            mid = self.ham_manager.store_experience(str(res),"fragmenta_chunk_result",{"original_task_id":task_id,"chunk_idx":chunk_index,"total_chunks":total_chunks,"proc":tool_name}); return mid if mid else res
        return res

    def _merge_results(self, results_or_ids: list, merging_params: Optional[Dict[str, Any]] = None) -> any: # Keep as is
        m = (merging_params or {}).get("method"); logger.info(f"F: Merging {len(results_or_ids)} items. Method: '{m}'.")
        if not results_or_ids: return None
        content = [ (self.ham_manager.recall_gist(item)["rehydrated_gist"] if isinstance(item,str) and item.startswith("mem_") and self.ham_manager and self.ham_manager.recall_gist(item) else item) for item in results_or_ids if item is not None]
        if not content: return None
        eff_m = m if m else ("simple_join" if len(content)>1 else "direct")
        if eff_m=="direct": return content[0]
        if eff_m=="join_with_newline": return "\n".join(map(str,content))
        if eff_m=="simple_join": return " ".join(map(str,content))
        if eff_m=="return_as_list": return content
        return content[0] if len(content)==1 else content

    def _dispatch_hsp_sub_task(self, complex_task_id: str, step_id: str, hsp_step: HSPStepDetails) -> Optional[str]: # Keep as is
        if not self.hsp_connector or not self.hsp_connector.is_connected:
            hsp_step["status"]="failed_dispatch"; hsp_step["error_info"]={"message":"HSPConnector N/A or not connected."}; return None
        req_id = f"frag_hsp_{uuid.uuid4().hex[:8]}"; cb_addr = f"hsp/results/{self.hsp_connector.ai_id}"
        payload=HSPTaskRequestPayload(request_id=req_id,requester_ai_id=self.hsp_connector.ai_id,target_ai_id=hsp_step["target_ai_id"],capability_id_filter=hsp_step["capability_id"],parameters=hsp_step["request_parameters"],callback_address=cb_addr)
        logger.info(f"F (ID:{complex_task_id},S:{step_id}): Sending HSP TaskReq(IRID:{req_id}) to AI '{hsp_step['target_ai_id']}' for cap '{hsp_step['capability_id']}'.")
        corr_id = self.hsp_connector.send_task_request(payload,hsp_step["target_ai_id"])
        if corr_id: hsp_step["correlation_id"]=corr_id; hsp_step["dispatch_timestamp"]=datetime.now(timezone.utc).isoformat(); hsp_step["status"]="dispatched"; self._pending_hsp_sub_tasks[corr_id]=(complex_task_id,step_id); return corr_id
        else: hsp_step["status"]="failed_dispatch"; hsp_step["error_info"]={"message":"HSPConnector send failed."}; return None

    def _handle_hsp_sub_task_result(self, result_payload: HSPTaskResultPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope) -> None: # Keep as is
        corr_id = full_envelope.get('correlation_id')
        if not corr_id or not (lookup := self._pending_hsp_sub_tasks.pop(corr_id, None)):
            logger.warning(f"F: HSP result for unknown/processed CorrID: {corr_id}. Payload: {str(result_payload)[:100]}"); return
        complex_task_id, step_id = lookup
        logger.info(f"F (ID:{complex_task_id},S:{step_id}): Got HSP result for CorrID {corr_id} from AI {sender_ai_id}.")
        task_ctx = self._complex_task_context.get(complex_task_id)
        if not task_ctx: logger.error(f"F: Context for task {complex_task_id} not found for HSP result. CorrID:{corr_id}"); return

        step_to_update: Optional[HSPStepDetails] = None
        for stage in task_ctx["strategy_plan"]["steps"]: # Iterate through stages
            for step_in_stage in (stage if isinstance(stage, list) else [stage]): # type: ignore
                if step_in_stage["step_id"] == step_id and step_in_stage["type"] == "hsp_task":
                    step_to_update = step_in_stage; break # type: ignore
            if step_to_update: break

        if not step_to_update: logger.error(f"F (ID:{complex_task_id}): HSPStepDetails for step '{step_id}' not found. CorrID:{corr_id}"); return
        if step_to_update["status"] in ["completed", "failed_response", "failed_dispatch", "timeout_error"]: logger.warning(f"F (ID:{complex_task_id},S:{step_id}): HSP result for already terminal step (status:{step_to_update['status']}). CorrID:{corr_id}. Ignoring."); return

        if result_payload.get('status') == 'success':
            step_to_update["status"]="completed"; step_to_update["result"]=result_payload.get('payload'); task_ctx["step_results"][step_id]=result_payload.get('payload')
        else:
            step_to_update["status"]="failed_response"; step_to_update["error_info"]=result_payload.get('error_details',{"message":"Unknown HSP error"}); task_ctx["step_results"][step_id]=None # type: ignore
        self._advance_complex_task(complex_task_id)

# Example __main__ block (ensure TrustManager is imported if used here)
# from core_ai.trust_manager.trust_manager_module import TrustManager
# from core_ai.service_discovery.service_discovery_module import StoredCapabilityInfo
# ... (rest of a potential __main__ block) ...
