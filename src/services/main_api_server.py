import uvicorn # For running the app
from fastapi import FastAPI
from datetime import datetime
import uuid # For generating session IDs
from typing import List # Added to resolve NameError

# Assuming src is in PYTHONPATH or this script is run from project root
# Adjust paths as necessary if running from within services directory directly for testing
from core_ai.dialogue.dialogue_manager import DialogueManager
from services.api_models import UserInput, AIOutput, SessionStartRequest, SessionStartResponse, HSPTaskRequestInput, HSPTaskRequestOutput, HSPTaskStatusOutput
from src.hsp.types import HSPCapabilityAdvertisementPayload


app = FastAPI(
    title="Unified AI Project API",
    description="API endpoints for interacting with the Unified AI.",
    version="0.1.0"
)

from contextlib import asynccontextmanager # For lifespan events
from src.core_services import initialize_services, get_services, shutdown_services, DEFAULT_AI_ID, DEFAULT_LLM_CONFIG, DEFAULT_OPERATIONAL_CONFIGS

# --- Service Initialization using Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("MainAPIServer: Initializing core services...")
    # Initialize services with potentially API-specific configurations
    # For example, API might use a different AI ID or specific LLM config than CLI.
    api_ai_id = f"did:hsp:api_server_ai_{uuid.uuid4().hex[:6]}"
    initialize_services(
        ai_id=api_ai_id,
        use_mock_ham=False, # API server should use real HAM, ensure MIKO_HAM_KEY is set
        llm_config=None, # Or a specific LLM config for the API
        operational_configs=None # Or specific operational configs
    )
    # Ensure services are ready, especially HSP connector
    services = get_services()
    hsp_connector = services.get("hsp_connector")
    if hsp_connector and not hsp_connector.is_connected:
        print("MainAPIServer: Warning - HSPConnector did not connect successfully during init.")

    print("MainAPIServer: Core services initialized.")
    yield
    print("MainAPIServer: Shutting down core services...")
    shutdown_services()
    print("MainAPIServer: Core services shut down.")

app = FastAPI(
    title="Unified AI Project API",
    description="API endpoints for interacting with the Unified AI.",
    version="0.1.0",
    lifespan=lifespan # Use the lifespan context manager
)

# DialogueManager will be fetched from get_services() in endpoints

@app.post("/api/v1/chat", response_model=AIOutput, tags=["Chat"])
async def chat_endpoint(user_input: UserInput):
    """
    Receives user input and returns the AI's response.
    """
    services = get_services()
    dialogue_manager = services.get("dialogue_manager")

    print(f"API: Received chat input: UserID='{user_input.user_id}', SessionID='{user_input.session_id}', Text='{user_input.text}'")
    if dialogue_manager is None:
        return AIOutput(
            response_text="Error: DialogueManager not available. Service might be initializing or encountered an issue.",
            user_id=user_input.user_id,
            session_id=user_input.session_id,
            timestamp=datetime.now().isoformat()
        )

    # Pass user_id and session_id to DialogueManager
    ai_response_text = await dialogue_manager.get_simple_response( # Added await
        user_input.text,
        session_id=user_input.session_id,
        user_id=user_input.user_id
    )

    return AIOutput(
        response_text=ai_response_text,
        user_id=user_input.user_id,
        session_id=user_input.session_id,
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/v1/session/start", response_model=SessionStartResponse, tags=["Session"])
async def start_session_endpoint(session_start_request: SessionStartRequest):
    """
    Starts a new session and returns an initial greeting and session ID.
    """
    services = get_services()
    dialogue_manager = services.get("dialogue_manager")

    print(f"API: Received session start request: UserID='{session_start_request.user_id}'")
    if dialogue_manager is None:
        session_id = uuid.uuid4().hex
        return SessionStartResponse(
            greeting="Error: AI Service not available. Service might be initializing or encountered an issue.",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

    # dialogue_manager.start_session is async
    greeting = await dialogue_manager.start_session(user_id=session_start_request.user_id)
    session_id = uuid.uuid4().hex

    return SessionStartResponse(
        greeting=greeting,
        session_id=session_id,
        timestamp=datetime.now().isoformat()
    )

# --- HSP Related Endpoints ---
@app.get("/api/v1/hsp/services", response_model=List[HSPCapabilityAdvertisementPayload], tags=["HSP"])
async def list_hsp_services():
    """
    Lists all capabilities discovered from other AIs on the HSP network.
    """
    services = get_services()
    service_discovery_module = services.get("service_discovery")

    if not service_discovery_module:
        return [] # Or raise HTTPException(status_code=503, detail="Service Discovery not available")

    capabilities = service_discovery_module.get_all_capabilities()
    # The _trust_score is an internal field, let's remove it for the API response
    # to adhere to the HSPCapabilityAdvertisementPayload spec.
    # However, HSPCapabilityAdvertisementPayload TypedDict doesn't define _trust_score,
    # so direct return should be fine if it's not strictly validated against only spec fields.
    # For safety, let's create copies without the internal field.

    # Actually, HSPCapabilityAdvertisementPayload is total=False, and _trust_score is not part of its definition.
    # So, returning it directly should be fine, clients not expecting _trust_score will ignore it.
    # If we wanted to be strict:
    # cleaned_capabilities = []
    # for cap in capabilities:
    #     cleaned_cap = cap.copy()
    #     cleaned_cap.pop("_trust_score", None) # Remove if it exists
    #     cleaned_capabilities.append(cleaned_cap)
    # return cleaned_capabilities
    return capabilities

@app.post("/api/v1/hsp/tasks", response_model=HSPTaskRequestOutput, tags=["HSP"])
async def request_hsp_task(task_input: HSPTaskRequestInput):
    """
    Allows an external client to request the AI to dispatch a task to another AI on the HSP network.
    """
    services = get_services()
    dialogue_manager = services.get("dialogue_manager")
    service_discovery = services.get("service_discovery")
    # hsp_connector = services.get("hsp_connector") # DM will use its own connector instance

    if not dialogue_manager or not service_discovery or not dialogue_manager.hsp_connector:
        return HSPTaskRequestOutput(
            status_message="Error: Core HSP services not available.",
            target_capability_id=task_input.target_capability_id,
            error="Service initialization issue."
        )

    print(f"API: Received HSP task request for capability '{task_input.target_capability_id}' with params: {task_input.parameters}")

    # 1. Find the capability advertisement
    # For API, we might want to be stricter and require an exact capability ID.
    found_caps = service_discovery.find_capabilities(capability_id_filter=task_input.target_capability_id)

    if not found_caps:
        return HSPTaskRequestOutput(
            status_message=f"Error: Capability ID '{task_input.target_capability_id}' not found or not available.",
            target_capability_id=task_input.target_capability_id,
            error="Capability not discovered."
        )

    selected_capability_adv = found_caps[0] # Assume first one is fine if multiple (though ID should be unique)

    # 2. Dispatch the task using DialogueManager's method
    # For API initiated tasks, user_id and session_id might be from API auth or generated.
    # original_user_query can be a descriptive string for this API-initiated task.
    api_user_id = "api_user_hsp_task"
    api_session_id = f"api_session_hsp_{uuid.uuid4().hex[:6]}"
    original_query_context = f"API request for capability {task_input.target_capability_id}"

    # _dispatch_hsp_task_request now returns -> (user_message, correlation_id)
    user_message, correlation_id = await dialogue_manager._dispatch_hsp_task_request(
        capability_advertisement=selected_capability_adv,
        request_parameters=task_input.parameters,
        original_user_query=original_query_context,
        user_id=api_user_id,
        session_id=api_session_id,
        request_type="api_initiated_hsp_task"
    )

    if correlation_id: # Dispatch was successful if correlation_id is returned
        return HSPTaskRequestOutput(
            status_message=user_message or "HSP Task request sent successfully.",
            correlation_id=correlation_id,
            target_capability_id=task_input.target_capability_id,
            error=None
        )
    else: # Dispatch failed
        return HSPTaskRequestOutput(
            status_message=user_message or "Error: Failed to dispatch HSP task request.",
            correlation_id=None,
            target_capability_id=task_input.target_capability_id,
            error=user_message or "Unknown error during dispatch."
        )

@app.get("/api/v1/hsp/tasks/{correlation_id}", response_model=HSPTaskStatusOutput, tags=["HSP"])
async def get_hsp_task_status(correlation_id: str):
    """
    Polls for the status and result of an HSP task initiated via /api/v1/hsp/tasks.
    """
    services = get_services()
    dialogue_manager = services.get("dialogue_manager")
    ham_manager = services.get("ham_manager")

    if not dialogue_manager or not ham_manager:
        # This case should ideally be prevented by lifespan ensuring services are up.
        # If they are None here, it's a server-side issue.
        return HSPTaskStatusOutput(
            correlation_id=correlation_id,
            status="unknown_or_expired",
            message="Core services for task status checking are unavailable."
        )

    # 1. Check if the task is still pending in DialogueManager
    if correlation_id in dialogue_manager.pending_hsp_task_requests:
        pending_info = dialogue_manager.pending_hsp_task_requests[correlation_id]
        return HSPTaskStatusOutput(
            correlation_id=correlation_id,
            status="pending",
            message=f"Task for capability '{pending_info.get('capability_id')}' sent to '{pending_info.get('target_ai_id')}' is still pending."
        )

    # 2. If not pending, check HAM for a stored result (success or error)
    # We stored results with metadata containing hsp_correlation_id
    # Data types were "ai_dialogue_text_hsp_result" or "ai_dialogue_text_hsp_error"
    # The actual service payload or error details are within the stored 'raw_data' (which is the result_message_to_user)
    # or more directly in metadata for errors.

    # Query HAM for success
    # The 'raw_data' stored for success was a string: f"{ai_name}: Regarding your request about '{original_query_text}', the specialist AI ({sender_ai_id}) responded with: {json.dumps(service_payload)}"
    # The actual service_payload is what we want to return. It was part of ai_metadata_hsp_result.
    # Let's refine HAM storage or query to get the actual payload.
    # For now, LearningManager stores the full result message to user in HAM.
    # The DM's _handle_incoming_hsp_task_result stores metadata including 'hsp_correlation_id'.
    # And for errors, 'error_details' is in metadata. For success, 'service_payload' is not directly in metadata.

    # Let's adjust what _handle_incoming_hsp_task_result stores in HAM metadata.
    # It currently stores the *user-facing message* as raw_data.
    # For success, it has 'hsp_result_sender_ai_id'. It should also store 'service_payload'.
    # For failure, it has 'error_details'.

    # Query for success records first
    # This HAM query needs to be precise. Let's assume HAM can filter by a specific metadata field.
    # We need to search for metadata.hsp_correlation_id == correlation_id

    # Simplified HAM query for PoC: Iterate and check metadata.
    # This is inefficient but will work for a few records.
    # A proper HAM query by metadata field is needed for production.

    found_record = None
    for mem_id, record_pkg in ham_manager.core_memory_store.items(): # type: ignore # Accessing internal store for PoC
        metadata = record_pkg.get("metadata", {})
        if metadata.get("hsp_correlation_id") == correlation_id:
            found_record = record_pkg
            break # Found the relevant record

    if found_record:
        metadata = found_record.get("metadata", {})
        data_type = found_record.get("data_type", "")

        if "hsp_task_result_success" in data_type:
            service_payload = metadata.get("hsp_task_service_payload")
            if service_payload is not None:
                return HSPTaskStatusOutput(
                    correlation_id=correlation_id,
                    status="completed",
                    result_payload=service_payload,
                    message="Task completed successfully."
                )
            else:
                # This case means DM stored the success record but somehow missed the service_payload in metadata
                return HSPTaskStatusOutput(
                    correlation_id=correlation_id,
                    status="completed",
                    message="Task completed, but full result payload was not found in stored metadata."
                )
        elif "hsp_task_result_error" in data_type:
            return HSPTaskStatusOutput(
                correlation_id=correlation_id,
                status="failed",
                error_details=metadata.get("error_details", {"error_code": "UNKNOWN_HSP_ERROR", "error_message": "Error details not fully stored."}),
                message="Task failed. See error_details."
            )

    # 3. If not found in pending or HAM
    return HSPTaskStatusOutput(
        correlation_id=correlation_id,
        status="unknown_or_expired",
        message="Task status unknown, or result has expired from immediate cache."
    )

# Placeholder for other API routes - to be added in next steps

if __name__ == "__main__":
    print("Attempting to run MainAPIServer with Uvicorn...")
    # The lifespan event will handle service initialization.
    # We can add a check here if needed, but not strictly necessary for startup.
    # For example, after uvicorn.run, services.get("dialogue_manager") could be checked.

    uvicorn.run(app, host="0.0.0.0", port=8000)
    # To run this directly: python src/services/main_api_server.py
    # (Ensure PYTHONPATH includes project root or Unified-AI-Project directory)

    # If you want to run with auto-reload for development:
    # uvicorn src.services.main_api_server:app --reload --host 0.0.0.0 --port 8000
    # (Run from project root: Unified-AI-Project/)
