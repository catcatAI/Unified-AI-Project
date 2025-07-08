import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Any, List, TypedDict, Literal

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

class PendingHSPSubTaskInfo(TypedDict):
    original_complex_task_id: str
    dispatched_capability_id: str
    request_payload_parameters: Dict[str, Any] # Parameters sent in HSPTaskRequest
    dispatch_timestamp: str
    # Potentially other context, e.g., which step of a multi-step plan this HSP task belongs to.

class ComplexTaskState(TypedDict):
    task_description: Dict[str, Any]
    input_data: Any
    strategy_plan: Dict[str, Any]
    current_step_index: int
    intermediate_results: List[Any]
    pending_hsp_correlation_ids: List[str]
    status: Literal["new", "analyzing_input", "determining_strategy",
                    "chunking", "processing_local_chunk", "awaiting_hsp_dispatch",
                    "awaiting_hsp_result", "hsp_result_received", "merging",
                    "completed", "failed"]


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

        self._pending_hsp_sub_tasks: Dict[str, PendingHSPSubTaskInfo] = {}
        self._complex_task_context: Dict[str, ComplexTaskState] = {}

        # Register HSP result handler if connector is available
        # This registration might ideally happen in core_services.py after both are initialized
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
        """
        if complex_task_id is None:
            complex_task_id = f"frag_task_{uuid.uuid4().hex[:8]}"
            logger.info(f"Fragmenta: New complex task received (ID: {complex_task_id}). Description: {str(task_description)[:100]}...")

            input_info = self._analyze_input(input_data)
            logger.info(f"Fragmenta (ID: {complex_task_id}): Input analysis - Type: {input_info.get('type')}, Size: {input_info.get('size')}")

            strategy = self._determine_processing_strategy(task_description, input_info, complex_task_id)
            logger.info(f"Fragmenta (ID: {complex_task_id}): Determined strategy - Name: {strategy.get('name')}")

            self._complex_task_context[complex_task_id] = ComplexTaskState(
                task_description=task_description, input_data=input_data,
                strategy_plan=strategy, current_step_index=0,
                intermediate_results=[], pending_hsp_correlation_ids=[],
                status="determining_strategy" # Initial status
            )
        elif complex_task_id not in self._complex_task_context:
            logger.error(f"Fragmenta: Unknown complex_task_id {complex_task_id} for resumed processing.")
            return {"status": "error", "message": f"Unknown complex_task_id {complex_task_id}", "complex_task_id": complex_task_id}

        task_ctx = self._complex_task_context[complex_task_id]
        strategy = task_ctx["strategy_plan"]

        # Main processing loop / state machine for the complex task
        current_status = task_ctx["status"]
        logger.info(f"Fragmenta (ID: {complex_task_id}): Processing task, current status: {current_status}")

        if current_status == "determining_strategy" or current_status == "new": # Start or restart
            if strategy.get("name") == "dispatch_to_hsp_capability":
                task_ctx["status"] = "awaiting_hsp_dispatch"
            elif strategy.get("requires_chunking"):
                task_ctx["status"] = "chunking"
            else: # Direct local processing (tool or LLM)
                task_ctx["status"] = "processing_local_chunk" # Treat as single chunk

        if task_ctx["status"] == "awaiting_hsp_dispatch":
            capability_info = strategy.get("hsp_capability_info")
            hsp_params = strategy.get("hsp_task_parameters")
            if not capability_info or not hsp_params:
                logger.error(f"Fragmenta (ID: {complex_task_id}): Missing capability_info or hsp_task_parameters for HSP dispatch strategy.")
                task_ctx["status"] = "failed"
                return {"status": "error", "message": "Invalid HSP dispatch strategy config.", "complex_task_id": complex_task_id}

            correlation_id = self._dispatch_hsp_sub_task(complex_task_id, capability_info, hsp_params)
            if correlation_id:
                task_ctx["pending_hsp_correlation_ids"].append(correlation_id)
                task_ctx["status"] = "awaiting_hsp_result"
                logger.info(f"Fragmenta (ID: {complex_task_id}): HSP sub-task dispatched (CorrID: {correlation_id}). Status now 'awaiting_hsp_result'.")
                return {"status": "pending_hsp", "complex_task_id": complex_task_id, "correlation_id": correlation_id}
            else:
                logger.error(f"Fragmenta (ID: {complex_task_id}): Failed to dispatch HSP sub-task.")
                task_ctx["status"] = "failed"
                return {"status": "error", "message": "Failed to dispatch HSP sub-task", "complex_task_id": complex_task_id}

        elif task_ctx["status"] == "chunking":
            chunks = self._chunk_data(task_ctx["input_data"], strategy.get("chunking_params"))
            task_ctx["intermediate_results"] = [None] * len(chunks) # Placeholders for chunk results
            task_ctx["current_step_index"] = 0 # To iterate through chunks
            task_ctx["status"] = "processing_local_chunk"
            logger.info(f"Fragmenta (ID: {complex_task_id}): Data chunked into {len(chunks)} chunks. Status 'processing_local_chunk'.")
            # Fall through to process the first chunk if local

        if task_ctx["status"] == "processing_local_chunk":
            # This part handles local chunk processing (tool or LLM)
            # For simplicity, let's assume one local processing step for now
            # In a real scenario, strategy['steps'] would be iterated.

            current_chunk_index = task_ctx["current_step_index"]
            # Assuming chunks were prepared if needed, or input_data is the single "chunk"
            data_to_process = task_ctx["input_data"]
            if strategy.get("requires_chunking"):
                all_chunks = self._chunk_data(task_ctx["input_data"], strategy.get("chunking_params"))
                if current_chunk_index >= len(all_chunks):
                    logger.info(f"Fragmenta (ID: {complex_task_id}): All local chunks processed.")
                    task_ctx["status"] = "merging" # Move to merging
                    # Potentially re-invoke process_complex_task to trigger merge
                    return self.process_complex_task(task_description, input_data, complex_task_id)

                data_to_process = all_chunks[current_chunk_index]

            processing_step_details = strategy.get("processing_step", {})
            logger.info(f"Fragmenta (ID: {complex_task_id}): Processing local data/chunk {current_chunk_index + 1} with '{processing_step_details.get('tool_or_model')}'.")

            processed_content_or_mem_id = self._dispatch_chunk_to_processing(
                data_to_process,
                processing_step_details,
                task_id=complex_task_id, # Using complex_task_id as the base task_id for HAM metadata
                chunk_index=current_chunk_index,
                total_chunks=len(task_ctx["intermediate_results"]) if strategy.get("requires_chunking") else 1
            )
            task_ctx["intermediate_results"][current_chunk_index] = processed_content_or_mem_id
            task_ctx["current_step_index"] += 1

            if not strategy.get("requires_chunking") or task_ctx["current_step_index"] >= len(task_ctx["intermediate_results"]):
                task_ctx["status"] = "merging"
                logger.info(f"Fragmenta (ID: {complex_task_id}): Local processing complete. Status 'merging'.")
            else: # More chunks to process locally
                logger.info(f"Fragmenta (ID: {complex_task_id}): Chunk {current_chunk_index} processed. More local chunks remaining.")
                # This implies process_complex_task might be called iteratively for each chunk,
                # or this loop needs to be internal. For now, assume iterative calls for simplicity of external state.
                # However, for a single public method, an internal loop is better.
                # Let's assume for now that if requires_chunking, all chunks are processed here before moving to merge.
                # This part needs refinement for true iterative chunk processing if _dispatch is not batch.
                # For now, this test implementation might only process the first chunk if called once.
                # Let's adjust to process all local chunks in one go if strategy is local chunking.
                if strategy.get("requires_chunking"): # Re-check, if we are here, means we are processing chunks
                    all_chunks = self._chunk_data(task_ctx["input_data"], strategy.get("chunking_params"))
                    for i in range(len(all_chunks)): # Process all chunks
                         chunk_data = all_chunks[i]
                         processed_res = self._dispatch_chunk_to_processing(
                             chunk_data, processing_step_details, complex_task_id, i, len(all_chunks)
                         )
                         task_ctx["intermediate_results"][i] = processed_res
                    task_ctx["status"] = "merging"


        if task_ctx["status"] == "hsp_result_received": # Status set by _handle_hsp_sub_task_result
            # This means an HSP result came in. We expect it to be in intermediate_results.
            # This logic might be too simple if there are multiple HSP calls or mixed local/HSP.
            logger.info(f"Fragmenta (ID: {complex_task_id}): HSP result processed by callback. Moving to merge. Results: {task_ctx['intermediate_results']}")
            task_ctx["status"] = "merging"

        if task_ctx["status"] == "merging":
            final_result = self._merge_results(task_ctx["intermediate_results"], strategy.get("merging_params"))
            task_ctx["status"] = "completed"
            logger.info(f"Fragmenta (ID: {complex_task_id}): Merging complete. Final result type: {type(final_result)}. Status 'completed'.")
            # Clean up context for completed task
            # final_task_data = self._complex_task_context.pop(complex_task_id, None)
            return {"status": "completed", "result": final_result, "complex_task_id": complex_task_id}

        # If still awaiting HSP results, or other intermediate states
        if task_ctx["status"] == "awaiting_hsp_result":
             logger.info(f"Fragmenta (ID: {complex_task_id}): Still awaiting HSP results for {task_ctx['pending_hsp_correlation_ids']}.")
             return {"status": "pending_hsp", "complex_task_id": complex_task_id, "correlation_ids": task_ctx['pending_hsp_correlation_ids']}

        logger.warning(f"Fragmenta (ID: {complex_task_id}): Task reached an unhandled state: {task_ctx['status']}.")
        return {"status": task_ctx["status"], "complex_task_id": complex_task_id, "message": "Processing (intermediate/unknown state)..."}


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

    def _determine_processing_strategy(self, task_description: Dict[str, Any], input_info: Dict[str, Any], complex_task_id: str) -> Dict[str, Any]:
        logger.debug(f"Fragmenta (ID: {complex_task_id}): Determining strategy for task: {task_description.get('goal', 'N/A')}")

        # Priority 1: Explicit HSP dispatch request in task_description
        if task_description.get("dispatch_to_hsp_capability_id"):
            if not self.service_discovery or not self.hsp_connector:
                logger.warning(f"Fragmenta (ID: {complex_task_id}): HSP dispatch requested but SDM or HSPConnector not available.")
                return {"name": "error_hsp_unavailable", "status": "failed"} # Fallback or error strategy

            cap_id = task_description["dispatch_to_hsp_capability_id"]
            capability = self.service_discovery.get_capability_by_id(cap_id, exclude_unavailable=True)
            if capability:
                logger.info(f"Fragmenta (ID: {complex_task_id}): Strategy: Explicit HSP dispatch to capability ID '{cap_id}'.")
                return {
                    "name": "dispatch_to_hsp_capability",
                    "requires_chunking": False,
                    "hsp_capability_info": capability,
                    "hsp_task_parameters": task_description.get("hsp_task_parameters", {})
                }
            else:
                logger.warning(f"Fragmenta (ID: {complex_task_id}): Requested HSP capability ID '{cap_id}' not found or unavailable.")
                # Fall through to other strategies or return error strategy

        # Priority 2: Specific local tool requested
        requested_tool = task_description.get("requested_tool")
        if requested_tool:
            logger.info(f"Fragmenta (ID: {complex_task_id}): Strategy: Direct call to local tool '{requested_tool}'.")
            return {
                "name": f"direct_tool_call_{requested_tool}",
                "requires_chunking": False, # Most tools might not handle chunked input directly this way
                "processing_step": {"tool_or_model": requested_tool, "params": task_description.get("tool_params", {})}
            }

        # Priority 3: General local processing (chunking for large text, or direct LLM)
        input_type = input_info.get("type", "unknown")
        input_size = input_info.get("size", 0)
        chunking_threshold = self.config.get("default_chunking_threshold", 200) # Increased threshold

        if input_type == "text" and input_size > chunking_threshold:
            logger.info(f"Fragmenta (ID: {complex_task_id}): Strategy: Text input size {input_size} > threshold {chunking_threshold}. Applying chunking and local LLM summarization.")
            return {
                "name": "chunk_and_summarize_text_locally",
                "requires_chunking": True,
                "chunking_params": self.config.get("default_text_chunking_params", {"chunk_size": 150, "overlap": 20}),
                "processing_step": {"tool_or_model": "llm_summarize_chunk", "params": {}}, # Each chunk summarized
                "merging_params": {"method": "join_with_newline"} # Then results joined
            }

        logger.info(f"Fragmenta (ID: {complex_task_id}): Strategy: Default direct local LLM processing for input type '{input_type}', size {input_size}.")
        return {
            "name": "direct_local_llm_process",
            "requires_chunking": False,
            "processing_step": {"tool_or_model": "llm_direct_process", "params": {}} # General LLM processing
        }

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

    def _dispatch_hsp_sub_task(self, complex_task_id: str, capability_to_use: HSPCapabilityAdvertisementPayload, task_parameters: Dict[str, Any]) -> Optional[str]:
        if not self.hsp_connector:
            logger.error(f"Fragmenta (ID: {complex_task_id}): HSPConnector not available for dispatching HSP task.")
            return None
        if not self.hsp_connector.is_connected:
            logger.error(f"Fragmenta (ID: {complex_task_id}): HSPConnector not connected. Cannot dispatch HSP task.")
            return None

        hsp_request_id = f"frag_hsp_req_{uuid.uuid4().hex[:8]}"
        target_ai_id = capability_to_use.get('ai_id')
        capability_id = capability_to_use.get('capability_id')

        if not target_ai_id or not capability_id :
            logger.error(f"Fragmenta (ID: {complex_task_id}): Target AI ID or Capability ID missing in capability info for HSP dispatch.")
            return None

        # Define where the result should come back. Could be a generic Fragmenta endpoint or task-specific.
        # For now, assume DialogueManager or core_services handles routing based on correlation_id.
        # The callback_address in HSPTaskRequestPayload is for the *other* AI to send the result to.
        # So, it should be a topic this AI (via HSPConnector) is subscribed to.
        # e.g., f"hsp/results/{self.hsp_connector.ai_id}/{hsp_request_id}" - unique per request
        # or a general results topic f"hsp/results/{self.hsp_connector.ai_id}"
        callback_address = f"hsp/results/{self.hsp_connector.ai_id}" # General results topic for this AI

        hsp_task_payload = HSPTaskRequestPayload(
            request_id=hsp_request_id,
            requester_ai_id=self.hsp_connector.ai_id,
            target_ai_id=target_ai_id,
            capability_id_filter=capability_id,
            parameters=task_parameters,
            callback_address=callback_address
        )

        logger.info(f"Fragmenta (ID: {complex_task_id}): Attempting to send HSP TaskRequest (ReqID: {hsp_request_id}) to AI '{target_ai_id}' for capability '{capability_id}'.")
        correlation_id = self.hsp_connector.send_task_request(payload=hsp_task_payload, target_ai_id_or_topic=target_ai_id)

        if correlation_id:
            pending_info = PendingHSPSubTaskInfo(
                original_complex_task_id=complex_task_id,
                dispatched_capability_id=capability_id,
                request_payload_parameters=task_parameters,
                dispatch_timestamp=datetime.now(timezone.utc).isoformat()
            )
            self._pending_hsp_sub_tasks[correlation_id] = pending_info
            logger.info(f"Fragmenta (ID: {complex_task_id}): HSP TaskRequest sent. Correlation ID: {correlation_id}. Stored pending info.")
            return correlation_id
        else:
            logger.error(f"Fragmenta (ID: {complex_task_id}): Failed to send HSP TaskRequest via connector.")
            return None

    def _handle_hsp_sub_task_result(self, result_payload: HSPTaskResultPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope) -> None:
        correlation_id = full_envelope.get('correlation_id')
        if not correlation_id:
            logger.warning("Fragmenta: Received HSP task result without correlation_id. Cannot process.")
            return

        pending_info = self._pending_hsp_sub_tasks.pop(correlation_id, None)
        if not pending_info:
            logger.warning(f"Fragmenta: Received HSP task result for unknown or already processed correlation_id: {correlation_id}")
            return

        complex_task_id = pending_info['original_complex_task_id']
        logger.info(f"Fragmenta (ID: {complex_task_id}): Received HSP sub-task result for CorrID {correlation_id} from AI {sender_ai_id}.")

        task_ctx = self._complex_task_context.get(complex_task_id)
        if not task_ctx:
            logger.error(f"Fragmenta: Context for complex task ID {complex_task_id} not found while processing HSP result. CorrID: {correlation_id}")
            return

        if correlation_id in task_ctx["pending_hsp_correlation_ids"]:
            task_ctx["pending_hsp_correlation_ids"].remove(correlation_id)

        actual_result_payload = result_payload.get('payload')
        if result_payload.get('status') == 'success':
            logger.info(f"Fragmenta (ID: {complex_task_id}): HSP sub-task success. Result: {str(actual_result_payload)[:100]}...")
            # Store or append result for merging
            task_ctx["intermediate_results"].append(actual_result_payload) # Or a processed version of it
        else:
            error_details = result_payload.get('error_details', 'Unknown error')
            logger.error(f"Fragmenta (ID: {complex_task_id}): HSP sub-task failed. Error: {error_details}")
            task_ctx["intermediate_results"].append(f"[HSP Task Error from {sender_ai_id}: {error_details}]")
            # Potentially change task_ctx status to "failed" or trigger alternative strategy

        # If all pending HSP tasks for this complex_task_id are now resolved
        if not task_ctx["pending_hsp_correlation_ids"] and task_ctx["status"] == "awaiting_hsp_result":
            task_ctx["status"] = "hsp_result_received" # Signal that results are in, ready for merge/next step
            logger.info(f"Fragmenta (ID: {complex_task_id}): All pending HSP results received. Status 'hsp_result_received'.")
            # Re-trigger processing of the main complex task
            # This assumes process_complex_task is re-entrant and can pick up from this state.
            # self.process_complex_task(task_ctx["task_description"], task_ctx["input_data"], complex_task_id)
            # Making process_complex_task fully re-entrant and state-driven is complex.
            # For now, this callback updates the context. The user/system might need to call process_complex_task again.
            # Or, this callback could directly trigger the merge if this was the only step.
        elif task_ctx["status"] == "awaiting_hsp_result":
             logger.info(f"Fragmenta (ID: {complex_task_id}): Still awaiting results for other HSP tasks: {task_ctx['pending_hsp_correlation_ids']}")


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
