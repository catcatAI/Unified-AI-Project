import pytest
import uuid
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple # Added missing imports

from src.fragmenta.fragmenta_orchestrator import FragmentaOrchestrator, EnhancedStrategyPlan, HSPStepDetails, LocalStepDetails, ProcessingStep, EnhancedComplexTaskState
from src.hsp.types import HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope, HSPErrorDetails

# Attempt to import freezegun, but don't make it a hard requirement if not available for all tests
try:
    from freezegun import freeze_time
except ImportError:
    freeze_time = None # type: ignore

# --- Mocks for Dependencies ---

@pytest.fixture
def mock_ham_manager():
    mock = MagicMock()
    mock.store_experience.side_effect = lambda raw_data, data_type, metadata: f"mem_{uuid.uuid4().hex[:6]}"
    mock.recall_gist.side_effect = lambda mem_id: {"rehydrated_gist": f"recalled_{mem_id}"} if "mem_" in mem_id else None
    return mock

@pytest.fixture
def mock_tool_dispatcher():
    mock = MagicMock()
    def dispatch_side_effect(query, explicit_tool_name, **params):
        if explicit_tool_name == "error_tool":
            return {"status": "error", "message": "Tool failed"}
        return {"status": "success", "payload": f"tool_result_for_{explicit_tool_name}_query_{query}"}
    mock.dispatch.side_effect = dispatch_side_effect
    return mock

@pytest.fixture
def mock_llm_interface():
    mock = MagicMock()
    mock.generate_response.side_effect = lambda prompt, params: f"llm_response_to_{prompt[:30]}"
    return mock

@pytest.fixture
def mock_service_discovery():
    mock = MagicMock()
    mock_caps = {}

    def get_cap_by_id(cap_id, exclude_unavailable=True):
        cap = mock_caps.get(cap_id)
        if cap and exclude_unavailable and cap.get("availability_status") != "online": # type: ignore
            return None
        return cap

    mock.get_capability_by_id.side_effect = get_cap_by_id
    mock._mock_caps = mock_caps # To allow tests to populate it
    return mock

@pytest.fixture
def mock_hsp_connector():
    mock = MagicMock()
    mock.ai_id = "did:hsp:fragmenta_test_ai"
    mock.is_connected = True
    mock.send_task_request.side_effect = lambda payload, target_ai_id_or_topic: f"corr_{uuid.uuid4().hex[:6]}"

    # Store registered callbacks
    mock.task_result_callbacks = []
    def register_cb(cb):
        mock.task_result_callbacks.append(cb)
    mock.register_on_task_result_callback.side_effect = register_cb
    return mock

@pytest.fixture
def mock_config():
    return {
        "default_chunking_threshold": 50,
        "default_text_chunking_params": {"chunk_size": 30, "overlap": 5},
        "hsp_task_defaults": {
            "max_retries": 2, # Lower for faster tests
            "initial_retry_delay_seconds": 1, # Lower for faster tests
            "retry_backoff_factor": 1.5, # Small backoff
            "timeout_seconds": 5 # Short timeout for tests
        }
    }

@pytest.fixture
def orchestrator(mock_ham_manager, mock_tool_dispatcher, mock_llm_interface, mock_service_discovery, mock_hsp_connector, mock_config):
    fo = FragmentaOrchestrator(
        ham_manager=mock_ham_manager,
        tool_dispatcher=mock_tool_dispatcher,
        llm_interface=mock_llm_interface,
        service_discovery=mock_service_discovery,
        hsp_connector=mock_hsp_connector,
        config=mock_config
    )
    if mock_hsp_connector: # Ensure callback is registered for tests
        # In a real setup, core_services.py handles this registration.
        # For testing, we might need to simulate this if Fragmenta relies on it being pre-registered.
        # However, the current FragmentaOrchestrator's __init__ does not itself register.
        # It's assumed that the HSPConnector, when receiving a message, will find the callback.
        # So, we will add it to the mock_hsp_connector directly if tests need to simulate callback invocation.
         if not hasattr(mock_hsp_connector, 'task_result_callbacks') or not mock_hsp_connector.task_result_callbacks: # type: ignore
            mock_hsp_connector.task_result_callbacks = [] # type: ignore
            mock_hsp_connector.register_on_task_result_callback(fo._handle_hsp_sub_task_result) # type: ignore

    return fo

# --- Helper Functions ---
def create_mock_hsp_capability(cap_id="test_hsp_cap", ai_id="did:hsp:peer_1", name="TestHSPCapability", status="online") -> HSPCapabilityAdvertisementPayload:
    return {
        "capability_id": cap_id, "ai_id": ai_id, "name": name,
        "description": "A test HSP capability.", "version": "1.0", "availability_status": status, # type: ignore
    }

def create_mock_hsp_success_result_envelope(correlation_id: str, request_id: str, executing_ai_id: str, result_payload_data: Dict) -> HSPMessageEnvelope:
    task_result_payload: HSPTaskResultPayload = {
        "result_id": f"res_{uuid.uuid4().hex[:6]}",
        "request_id": request_id,
        "executing_ai_id": executing_ai_id,
        "status": "success",
        "payload": result_payload_data
    }
    return {
        "hsp_envelope_version": "0.1", "message_id": f"msg_{uuid.uuid4().hex[:6]}",
        "correlation_id": correlation_id, "sender_ai_id": executing_ai_id,
        "recipient_ai_id": "did:hsp:fragmenta_test_ai",
        "timestamp_sent": datetime.now(timezone.utc).isoformat(),
        "message_type": "HSP::TaskResult_v0.1", "protocol_version": "0.1.1",
        "communication_pattern": "response", "payload": task_result_payload, # type: ignore
        "security_parameters": None, "qos_parameters": None, "routing_info": None, "payload_schema_uri": None
    }

def create_mock_hsp_failure_result_envelope(correlation_id: str, request_id: str, executing_ai_id: str, error_code: str, error_message: str) -> HSPMessageEnvelope:
    error_details: HSPErrorDetails = {"error_code": error_code, "error_message": error_message} # type: ignore
    task_result_payload: HSPTaskResultPayload = {
        "result_id": f"res_{uuid.uuid4().hex[:6]}",
        "request_id": request_id,
        "executing_ai_id": executing_ai_id,
        "status": "failure",
        "error_details": error_details
    }
    return {
        "hsp_envelope_version": "0.1", "message_id": f"msg_{uuid.uuid4().hex[:6]}",
        "correlation_id": correlation_id, "sender_ai_id": executing_ai_id,
        "recipient_ai_id": "did:hsp:fragmenta_test_ai",
        "timestamp_sent": datetime.now(timezone.utc).isoformat(),
        "message_type": "HSP::TaskResult_v0.1", "protocol_version": "0.1.1",
        "communication_pattern": "response", "payload": task_result_payload, # type: ignore
        "security_parameters": None, "qos_parameters": None, "routing_info": None, "payload_schema_uri": None
    }


# --- Test Cases ---

def test_orchestrator_initialization(orchestrator: FragmentaOrchestrator, mock_config):
    assert orchestrator.ham_manager is not None
    assert orchestrator.config == mock_config
    assert orchestrator.hsp_task_defaults["max_retries"] == 2

def test_analyze_input(orchestrator: FragmentaOrchestrator):
    info_text = orchestrator._analyze_input("hello")
    assert info_text["type"] == "text"
    assert info_text["size"] == 5
    info_struct = orchestrator._analyze_input({"key": "value"})
    assert info_struct["type"] == "structured_data"

def test_chunk_data(orchestrator: FragmentaOrchestrator):
    data = "This is a test sentence for chunking." # len 38
    params_small_chunk = {"chunk_size": 10, "overlap": 2}
    chunks = orchestrator._chunk_data(data, params_small_chunk)
    assert len(chunks) == 5
    assert chunks[0] == "This is a "
    assert chunks[1] == "a test sen"

    params_no_overlap = {"chunk_size": 10, "overlap": 0}
    chunks_no_overlap = orchestrator._chunk_data(data, params_no_overlap)
    assert len(chunks_no_overlap) == 4
    assert chunks_no_overlap[0] == "This is a "
    assert chunks_no_overlap[1] == "test sente"


def test_determine_strategy_local_tool(orchestrator: FragmentaOrchestrator):
    task_desc = {"requested_tool": "my_tool", "tool_params": {"p1": "v1"}}
    plan = orchestrator._determine_processing_strategy(task_desc, {}, "task1")
    assert plan["name"] == "direct_tool_call_my_tool"
    assert len(plan["steps"]) == 1
    step = plan["steps"][0]
    assert step["type"] == "local_tool" # type: ignore
    assert step["tool_or_model_name"] == "my_tool" # type: ignore
    assert step["parameters"] == {"p1": "v1"} # type: ignore
    assert step["status"] == "pending" # type: ignore

def test_determine_strategy_hsp(orchestrator: FragmentaOrchestrator, mock_service_discovery: MagicMock):
    cap_adv = create_mock_hsp_capability("hsp_cap1", "peer_ai", "HSPSummarizer")
    mock_service_discovery._mock_caps["hsp_cap1"] = cap_adv # type: ignore

    task_desc = {"dispatch_to_hsp_capability_id": "hsp_cap1", "hsp_task_parameters": {"text": "abc"}}
    plan = orchestrator._determine_processing_strategy(task_desc, {}, "task_hsp")
    assert plan["name"] == "dispatch_to_hsp_capability"
    assert len(plan["steps"]) == 1
    step = plan["steps"][0] # type: HSPStepDetails
    assert step["type"] == "hsp_task"
    assert step["capability_id"] == "hsp_cap1"
    assert step["target_ai_id"] == "peer_ai"
    assert step["request_parameters"] == {"text": "abc"}
    assert step["status"] == "pending_dispatch"
    assert step["retries_left"] == orchestrator.hsp_task_defaults["max_retries"]

def test_determine_strategy_hsp_cap_not_found(orchestrator: FragmentaOrchestrator, mock_service_discovery: MagicMock):
    mock_service_discovery._mock_caps.clear() # type: ignore
    task_desc = {"dispatch_to_hsp_capability_id": "unknown_cap", "hsp_task_parameters": {}}
    plan = orchestrator._determine_processing_strategy(task_desc, {}, "task_hsp_fail")
    assert plan["name"] == "error_hsp_cap_unavailable_unknown_cap"
    assert len(plan["steps"]) == 1
    step = plan["steps"][0] # type: HSPStepDetails
    assert step["status"] == "failed_dispatch"
    assert step["error_info"] is not None # type: ignore
    assert step["error_info"]["message"] == "Capability 'unknown_cap' not found or unavailable." # type: ignore

# --- Tests for _advance_complex_task and HSP interactions ---

def test_process_single_local_llm_step_success(orchestrator: FragmentaOrchestrator, mock_llm_interface: MagicMock):
    task_desc = {"goal": "simple llm task"}
    input_data = "test prompt"
    result = orchestrator.process_complex_task(task_desc, input_data, "local_llm_task1")

    assert result["status"] == "completed"
    assert "llm_response_to_test prompt" in result["result"] # type: ignore
    mock_llm_interface.generate_response.assert_called_once()
    task_ctx = orchestrator._complex_task_context["local_llm_task1"]
    assert task_ctx["overall_status"] == "completed"
    assert len(task_ctx["step_results"]) == 1

def test_process_single_hsp_step_success(orchestrator: FragmentaOrchestrator, mock_service_discovery: MagicMock, mock_hsp_connector: MagicMock):
    cap_id = "hsp_summarizer"
    peer_ai_id = "did:hsp:peer_summarizer"
    cap_adv = create_mock_hsp_capability(cap_id, peer_ai_id, "HSPSummarizer")
    mock_service_discovery._mock_caps[cap_id] = cap_adv # type: ignore

    task_desc = {"dispatch_to_hsp_capability_id": cap_id, "hsp_task_parameters": {"text": "summarize this"}}
    input_data = "some input"
    complex_task_id = "hsp_task_success"

    result = orchestrator.process_complex_task(task_desc, input_data, complex_task_id)
    assert result["status"] == "pending_hsp"
    assert len(result["correlation_ids"]) == 1 # type: ignore
    correlation_id = result["correlation_ids"][0] # type: ignore
    mock_hsp_connector.send_task_request.assert_called_once()

    task_ctx = orchestrator._complex_task_context[complex_task_id]
    hsp_step_details = task_ctx["strategy_plan"]["steps"][0] # type: HSPStepDetails
    assert hsp_step_details["status"] == "dispatched"
    assert hsp_step_details["correlation_id"] == correlation_id
    internal_req_id = mock_hsp_connector.send_task_request.call_args[1]['payload']['request_id']


    hsp_result_env = create_mock_hsp_success_result_envelope(
        correlation_id, internal_req_id, peer_ai_id, {"summary": "HSP summarized text"}
    )
    # Simulate callback by directly calling the handler if it's registered on the mock
    # This assumes mock_hsp_connector.task_result_callbacks list is populated correctly
    # In real scenario, HSPConnector invokes callbacks from its internal list.
    # Here we find the callback Fragmenta would have registered.
    frag_callback = None
    for cb in mock_hsp_connector.task_result_callbacks: # type: ignore
        if hasattr(cb, '__self__') and cb.__self__ == orchestrator:
            frag_callback = cb
            break
    assert frag_callback is not None, "Fragmenta's HSP result callback not found on mock_hsp_connector"
    frag_callback(hsp_result_env["payload"], hsp_result_env["sender_ai_id"], hsp_result_env)


    final_task_ctx = orchestrator._complex_task_context.get(complex_task_id)
    assert final_task_ctx is not None
    assert final_task_ctx["overall_status"] == "completed"

    output_dict = orchestrator.process_complex_task(task_desc, input_data, complex_task_id)
    assert output_dict["status"] == "completed"
    assert output_dict["result"] == {"summary": "HSP summarized text"}


if freeze_time:
    @freeze_time("2024-07-15 10:00:00 UTC")
    def test_hsp_step_timeout_and_retry_success(orchestrator: FragmentaOrchestrator, mock_service_discovery: MagicMock, mock_hsp_connector: MagicMock):
        cap_id = "hsp_timeout_cap"
        peer_ai_id = "did:hsp:peer_timeout"
        cap_adv = create_mock_hsp_capability(cap_id, peer_ai_id, "TimeoutCap")
        mock_service_discovery._mock_caps[cap_id] = cap_adv # type: ignore
        task_desc = {"dispatch_to_hsp_capability_id": cap_id, "hsp_task_parameters": {"data": "info"}}
        complex_task_id = "hsp_task_timeout_retry"

        orchestrator.process_complex_task(task_desc, "input", complex_task_id)
        task_ctx = orchestrator._complex_task_context[complex_task_id]
        hsp_step = task_ctx["strategy_plan"]["steps"][0] # type: HSPStepDetails
        assert hsp_step["status"] == "dispatched"
        original_correlation_id = hsp_step["correlation_id"]
        assert original_correlation_id is not None
        internal_req_id_attempt1 = mock_hsp_connector.send_task_request.call_args[1]['payload']['request_id']

        current_time = datetime.now(timezone.utc)
        with freeze_time(current_time + timedelta(seconds=orchestrator.hsp_task_defaults["timeout_seconds"] + 1)):
            orchestrator._advance_complex_task(complex_task_id)
        assert hsp_step["status"] == "timeout_error"
        # Retries_left isn't decremented until an actual retry attempt is made by _advance_complex_task discovering this state
        assert hsp_step["retries_left"] == orchestrator.hsp_task_defaults["max_retries"]

        orchestrator._advance_complex_task(complex_task_id) # This call should transition to 'retrying'
        assert hsp_step["status"] == "retrying"
        assert hsp_step["retries_left"] == orchestrator.hsp_task_defaults["max_retries"] - 1

        last_retry_ts_str = hsp_step["last_retry_timestamp"]
        assert last_retry_ts_str is not None
        last_retry_ts = datetime.fromisoformat(last_retry_ts_str)

        retry_delay = hsp_step["retry_delay_seconds"]
        with freeze_time(last_retry_ts + timedelta(seconds=retry_delay + 1)):
            orchestrator._advance_complex_task(complex_task_id)

        assert hsp_step["status"] == "dispatched"
        assert hsp_step["correlation_id"] != original_correlation_id
        retry_correlation_id = hsp_step["correlation_id"]
        assert retry_correlation_id is not None
        # send_task_request would have been called again for retry
        internal_req_id_attempt2 = mock_hsp_connector.send_task_request.call_args_list[-1][1]['payload']['request_id']


        hsp_result_env = create_mock_hsp_success_result_envelope(
            retry_correlation_id, internal_req_id_attempt2, peer_ai_id, {"data": "retry success data"}
        )

        frag_callback = orchestrator._handle_hsp_sub_task_result # Direct call for test
        frag_callback(hsp_result_env["payload"], hsp_result_env["sender_ai_id"], hsp_result_env) # type: ignore

        final_output = orchestrator.process_complex_task(task_desc, "input", complex_task_id)
        assert final_output["status"] == "completed"
        assert final_output["result"] == {"data": "retry success data"}
        assert hsp_step["status"] == "completed"


    @freeze_time("2024-07-15 11:00:00 UTC")
    def test_hsp_step_timeout_and_retry_exhausted(orchestrator: FragmentaOrchestrator, mock_service_discovery: MagicMock, mock_hsp_connector: MagicMock):
        cap_id = "hsp_exhaust_cap"
        peer_ai_id = "did:hsp:peer_exhaust"
        cap_adv = create_mock_hsp_capability(cap_id, peer_ai_id, "ExhaustCap")
        mock_service_discovery._mock_caps[cap_id] = cap_adv # type: ignore
        task_desc = {"dispatch_to_hsp_capability_id": cap_id, "hsp_task_parameters": {}}
        complex_task_id = "hsp_task_exhaust"
        max_retries = orchestrator.hsp_task_defaults["max_retries"]

        orchestrator.process_complex_task(task_desc, "input", complex_task_id)
        task_ctx = orchestrator._complex_task_context[complex_task_id]
        hsp_step = task_ctx["strategy_plan"]["steps"][0] # type: HSPStepDetails

        current_time = datetime.now(timezone.utc)
        for i in range(max_retries + 1):
            assert hsp_step["status"] == "dispatched"

            dispatch_time = datetime.fromisoformat(hsp_step["dispatch_timestamp"] if hsp_step["dispatch_timestamp"] else current_time.isoformat() ) # type: ignore
            current_time = dispatch_time + timedelta(seconds=orchestrator.hsp_task_defaults["timeout_seconds"] + 1)
            with freeze_time(current_time):
                orchestrator._advance_complex_task(complex_task_id)
            assert hsp_step["status"] == "timeout_error"

            orchestrator._advance_complex_task(complex_task_id) # Process the timeout to potentially enter retry

            if i < max_retries:
                assert hsp_step["status"] == "retrying"
                assert hsp_step["retries_left"] == max_retries - (i + 1)

                last_retry_ts_str = hsp_step["last_retry_timestamp"]
                assert last_retry_ts_str is not None
                last_retry_ts = datetime.fromisoformat(last_retry_ts_str)

                delay_factor = orchestrator.hsp_task_defaults.get("retry_backoff_factor", 2)
                num_prev_retries_for_delay_calc = i
                current_retry_delay = hsp_step["retry_delay_seconds"] * (delay_factor ** num_prev_retries_for_delay_calc)

                current_time = last_retry_ts + timedelta(seconds=current_retry_delay + 1)
                with freeze_time(current_time):
                    orchestrator._advance_complex_task(complex_task_id)
            else:
                 assert hsp_step["status"] == "timeout_error"
                 assert hsp_step["retries_left"] == 0

        final_output = orchestrator.process_complex_task(task_desc, "input", complex_task_id)
        assert final_output["status"] == "failed"
        assert task_ctx["overall_status"] == "failed_execution"


def test_hsp_task_result_failure_and_retry(orchestrator: FragmentaOrchestrator, mock_service_discovery: MagicMock, mock_hsp_connector: MagicMock):
    cap_id = "hsp_fail_cap"
    peer_ai_id = "did:hsp:peer_fail"
    cap_adv = create_mock_hsp_capability(cap_id, peer_ai_id, "FailCap")
    mock_service_discovery._mock_caps[cap_id] = cap_adv # type: ignore
    task_desc = {"dispatch_to_hsp_capability_id": cap_id, "hsp_task_parameters": {}}
    complex_task_id = "hsp_task_fail_retry"

    orchestrator.process_complex_task(task_desc, "input", complex_task_id)
    task_ctx = orchestrator._complex_task_context[complex_task_id]
    hsp_step = task_ctx["strategy_plan"]["steps"][0] # type: HSPStepDetails
    correlation_id_attempt1 = hsp_step["correlation_id"]
    assert correlation_id_attempt1 is not None
    internal_req_id_attempt1 = mock_hsp_connector.send_task_request.call_args[1]['payload']['request_id']


    hsp_failure_env = create_mock_hsp_failure_result_envelope(
        correlation_id_attempt1, internal_req_id_attempt1, peer_ai_id, "PEER_ERROR", "Peer processing failed"
    )
    # Simulate callback registration and invocation
    frag_callback = orchestrator._handle_hsp_sub_task_result
    frag_callback(hsp_failure_env["payload"], hsp_failure_env["sender_ai_id"], hsp_failure_env) # type: ignore
    assert hsp_step["status"] == "failed_response"

    # Advance task - should go into 'retrying'
    current_time = datetime.now(timezone.utc)
    if freeze_time:
        with freeze_time(current_time) as frozen_time:
            orchestrator._advance_complex_task(complex_task_id)
            assert hsp_step["status"] == "retrying"
            assert hsp_step["retries_left"] == orchestrator.hsp_task_defaults["max_retries"] - 1

            frozen_time.tick(timedelta(seconds=hsp_step["retry_delay_seconds"] + 1))
            orchestrator._advance_complex_task(complex_task_id)
    else:
        orchestrator._advance_complex_task(complex_task_id)
        assert hsp_step["status"] == "retrying"
        hsp_step["last_retry_timestamp"] = (datetime.now(timezone.utc) - timedelta(seconds=hsp_step["retry_delay_seconds"] + 5)).isoformat()
        orchestrator._advance_complex_task(complex_task_id)

    assert hsp_step["status"] == "dispatched"
    correlation_id_attempt2 = hsp_step["correlation_id"]
    assert correlation_id_attempt2 is not None and correlation_id_attempt2 != correlation_id_attempt1
    internal_req_id_attempt2 = mock_hsp_connector.send_task_request.call_args_list[-1][1]['payload']['request_id']


    hsp_success_env = create_mock_hsp_success_result_envelope(
        correlation_id_attempt2, internal_req_id_attempt2, peer_ai_id, {"data": "retry success data"}
    )
    frag_callback(hsp_success_env["payload"], hsp_success_env["sender_ai_id"], hsp_success_env) # type: ignore

    final_output = orchestrator.process_complex_task(task_desc, "input", complex_task_id)
    assert final_output["status"] == "completed"
    assert final_output["result"] == {"data": "retry success data"}


# --- Tests for _prepare_step_input ---
def test_prepare_step_input_no_sources(orchestrator: FragmentaOrchestrator):
    task_desc = {"goal": "test"}
    input_data = "original_input"
    plan = orchestrator._determine_processing_strategy(task_desc, orchestrator._analyze_input(input_data), "task_prep_0")
    orchestrator._complex_task_context["task_prep_0"] = EnhancedComplexTaskState(
        complex_task_id="task_prep_0", original_task_description=task_desc, original_input_data=input_data,
        strategy_plan=plan, step_results={}, overall_status="executing",
        current_executing_step_ids=[], next_step_to_evaluate_index=0
    )
    task_ctx = orchestrator._complex_task_context["task_prep_0"]
    step_details_no_source = plan["steps"][0] # Assuming first step has no input_sources by default
    step_details_no_source["input_sources"] = None # Explicitly set for test clarity

    prepared_input, deps_met, dep_failure = orchestrator._prepare_step_input(step_details_no_source, task_ctx) # type: ignore
    assert deps_met is True
    assert dep_failure is False
    assert prepared_input == "original_input"

def test_prepare_step_input_single_source_completed(orchestrator: FragmentaOrchestrator):
    step1_details: LocalStepDetails = {"step_id": "s1", "type": "local_llm", "tool_or_model_name": "tm", "parameters": {}, "status": "completed", "input_sources":None, "input_mapping":None, "result": {"text": "output_from_s1"}, "error_info": None}
    step2_details: LocalStepDetails = {"step_id": "s2", "type": "local_llm", "tool_or_model_name": "tm2", "parameters": {}, "status": "pending", "input_sources": [{"step_id": "s1"}], "input_mapping": None, "result": None, "error_info": None}
    plan = EnhancedStrategyPlan(plan_id="p1", name="test_plan", steps=[step1_details, step2_details]) # type: ignore
    task_ctx = EnhancedComplexTaskState(
        complex_task_id="task_prep_1", original_task_description={}, original_input_data="orig",
        strategy_plan=plan, step_results={"s1": {"text": "output_from_s1"}},
        overall_status="executing", current_executing_step_ids=[], next_step_to_evaluate_index=1
    )
    prepared_input, deps_met, dep_failure = orchestrator._prepare_step_input(step2_details, task_ctx)
    assert deps_met is True
    assert dep_failure is False
    assert prepared_input == {"text": "output_from_s1"} # Returns the whole result of s1

def test_prepare_step_input_single_source_with_output_key(orchestrator: FragmentaOrchestrator):
    step1_details: LocalStepDetails = {"step_id": "s1", "type": "local_llm", "tool_or_model_name": "tm", "parameters": {}, "status": "completed", "input_sources":None, "input_mapping":None, "result": {"text": "output_from_s1", "extra": "value"}, "error_info": None}
    step2_details: LocalStepDetails = {"step_id": "s2", "type": "local_llm", "tool_or_model_name": "tm2", "parameters": {}, "status": "pending", "input_sources": [{"step_id": "s1", "output_key": "text"}], "input_mapping": None, "result": None, "error_info": None}
    plan = EnhancedStrategyPlan(plan_id="p1", name="test_plan", steps=[step1_details, step2_details]) # type: ignore
    task_ctx = EnhancedComplexTaskState(
        complex_task_id="task_prep_2", original_task_description={}, original_input_data="orig",
        strategy_plan=plan, step_results={"s1": {"text": "output_from_s1", "extra": "value"}},
        overall_status="executing", current_executing_step_ids=[], next_step_to_evaluate_index=1
    )
    prepared_input, deps_met, dep_failure = orchestrator._prepare_step_input(step2_details, task_ctx)
    assert deps_met is True
    assert dep_failure is False
    assert prepared_input == {"s1.text": "output_from_s1"} # Map includes the keyed value

def test_prepare_step_input_dependency_not_met(orchestrator: FragmentaOrchestrator):
    step1_details: LocalStepDetails = {"step_id": "s1", "type": "local_llm", "tool_or_model_name": "tm", "parameters": {}, "status": "pending", "input_sources":None, "input_mapping":None, "result": None, "error_info": None} # s1 is pending
    step2_details: LocalStepDetails = {"step_id": "s2", "type": "local_llm", "tool_or_model_name": "tm2", "parameters": {}, "status": "pending", "input_sources": [{"step_id": "s1"}], "input_mapping": None, "result": None, "error_info": None}
    plan = EnhancedStrategyPlan(plan_id="p1", name="test_plan", steps=[step1_details, step2_details]) # type: ignore
    task_ctx = EnhancedComplexTaskState(
        complex_task_id="task_prep_3", original_task_description={}, original_input_data="orig",
        strategy_plan=plan, step_results={}, overall_status="executing",
        current_executing_step_ids=[], next_step_to_evaluate_index=1
    )
    _, deps_met, dep_failure = orchestrator._prepare_step_input(step2_details, task_ctx)
    assert deps_met is False
    assert dep_failure is False

def test_prepare_step_input_dependency_failed(orchestrator: FragmentaOrchestrator):
    step1_details: LocalStepDetails = {"step_id": "s1", "type": "local_llm", "tool_or_model_name": "tm", "parameters": {}, "status": "failed", "input_sources":None, "input_mapping":None, "result": None, "error_info": {"msg":"s1 failed"}} # s1 failed
    step2_details: LocalStepDetails = {"step_id": "s2", "type": "local_llm", "tool_or_model_name": "tm2", "parameters": {}, "status": "pending", "input_sources": [{"step_id": "s1"}], "input_mapping": None, "result": None, "error_info": None}
    plan = EnhancedStrategyPlan(plan_id="p1", name="test_plan", steps=[step1_details, step2_details]) # type: ignore
    task_ctx = EnhancedComplexTaskState(
        complex_task_id="task_prep_4", original_task_description={}, original_input_data="orig",
        strategy_plan=plan, step_results={"s1": None}, overall_status="executing",
        current_executing_step_ids=[], next_step_to_evaluate_index=1
    )
    _, deps_met, dep_failure = orchestrator._prepare_step_input(step2_details, task_ctx)
    assert deps_met is False
    assert dep_failure is True

# --- Tests for input_mapping in _execute_or_dispatch_step ---
def test_execute_step_with_input_mapping_simple_template(orchestrator: FragmentaOrchestrator):
    # This test focuses on the input_mapping part of _execute_or_dispatch_step
    # It assumes _prepare_step_input has provided the necessary data in current_step_input_map
    step_details: LocalStepDetails = {
        "step_id": "s_map", "type": "local_llm", "tool_or_model_name": "mapped_llm",
        "parameters": {"base_param": "initial"}, # Default params for the tool
        "input_sources": [{"step_id": "s_source", "output_key": "text_val"}],
        "input_mapping": {"prompt": "Input was: {s_source.text_val} and original: {$original_input}"}, # type: ignore
        "status": "pending", "result": None, "error_info": None
    }
    task_ctx = EnhancedComplexTaskState( # Mocked task_ctx
        complex_task_id="task_map_1", original_task_description={"desc_key": "task_desc_val"},
        original_input_data="original task data", strategy_plan=MagicMock(), step_results={},
        overall_status="executing", current_executing_step_ids=[], next_step_to_evaluate_index=0
    )
    # This is what _prepare_step_input would produce for current_step_input argument
    prepared_inputs_map = {"s_source.text_val": "hello from source"}

    with patch.object(orchestrator, '_dispatch_chunk_to_processing') as mock_dispatch:
        orchestrator._execute_or_dispatch_step("task_map_1", step_details, prepared_inputs_map, task_ctx)

    mock_dispatch.assert_called_once()
    call_args = mock_dispatch.call_args[0]
    strategy_step_arg = call_args[1] # This is the dict like {"tool_or_model": ..., "params": ...}

    expected_prompt = "Input was: hello from source and original: original task data"
    assert strategy_step_arg["params"]["prompt"] == expected_prompt
    assert strategy_step_arg["params"]["base_param"] == "initial" # Ensure original params preserved if not overwritten


def test_execute_step_with_input_mapping_direct_assignment(orchestrator: FragmentaOrchestrator):
    step_details: LocalStepDetails = {
        "step_id": "s_map_direct", "type": "local_tool", "tool_or_model_name": "direct_tool",
        "parameters": {},
        "input_sources": [{"step_id": "s_data"}],
        "input_mapping": {"data_input": "{s_data}", "fixed_val": "literal"}, # type: ignore
        "status": "pending", "result": None, "error_info": None
    }
    task_ctx = MagicMock() # Simplified context
    prepared_inputs_map = {"s_data": {"complex": "object"}}

    with patch.object(orchestrator, '_dispatch_chunk_to_processing') as mock_dispatch:
        orchestrator._execute_or_dispatch_step("task_map_2", step_details, prepared_inputs_map, task_ctx)

    strategy_step_arg = mock_dispatch.call_args[0][1]
    assert strategy_step_arg["params"]["data_input"] == {"complex": "object"} # Direct assignment of complex type
    assert strategy_step_arg["params"]["fixed_val"] == "literal"


# TODO: Add tests for PARALLEL execution scenarios using the new plan structure
# - Plan with [[stepA, stepB], stepC]
# - Verify A and B are dispatched if deps met
# - Verify _advance_complex_task waits if A is done but B is pending_hsp
# - Verify C is dispatched only after A and B are complete
# - Verify failure in A (a parallel branch) leads to overall_status = failed_execution

# To run tests:
# pytest tests/fragmenta/test_fragmenta_orchestrator.py
# (Ensure pytest and optionally pytest-freezegun are installed)
