
import asyncio
import os
from dotenv import load_dotenv
import logging # Added logging
import uuid # Added uuid
from src.core_services import initialize_services, get_services, shutdown_services
from src.services.llm_interface import LLMInterfaceConfig
from src.hsp.types import HSPTaskRequestPayload, HSPEchoTaskRequestPayload, HSPEchoTaskResultPayload, HSPCapabilityAdvertisementPayload, HSPMessageEnvelope # Added HSP types

# Load environment variables from .env file
load_dotenv()

ECHO_CAPABILITY_ID = "hsp:capability:echo_service_v0.1" # Define the capability ID

async def main():
    print("--- Running Simple Test Script with Gemini LLM and HSP Echo Test ---")

    # Define the query and echo message
    test_query = "Hello, Angela. Are you there? Who are you?"
    echo_message = "Hello from the main AI! Please echo this back."
    echo_target_ai_id = "did:hsp:echo_ai_001" # The AI ID of our echo executor

    # Define the configuration to use Google Gemini
    gemini_llm_config: LLMInterfaceConfig = {
        "default_provider": "gemini",
        "default_model": "gemini-1.5-flash-latest", # Using a fast and capable model
        "providers": {
            "gemini": {
                # The API key will be read from the GEMINI_API_KEY environment variable
                # by the LLMInterface, so we don't need to specify it here.
            }
        },
        "default_generation_params": {
            "temperature": 0.7,
            "max_output_tokens": 250
        },
        "operational_configs": {}
    }

    # Initialize all services, passing the Gemini config
    initialize_services(use_mock_ham=True, llm_config=gemini_llm_config, hsp_broker_address="localhost", hsp_broker_port=1883)

    # Get the dialogue manager instance and HSP related services immediately after initialization
    services = get_services()
    dialogue_manager = services.get("dialogue_manager")
    hsp_connector = services.get("hsp_connector") # Get HSP connector
    service_discovery = services.get("service_discovery") # Get service discovery

    if not dialogue_manager:
        print("ERROR: DialogueManager not found after initialization.")
        shutdown_services()
        return
    if not hsp_connector or not service_discovery:
        print("ERROR: HSPConnector or ServiceDiscovery not found after initialization. Cannot perform HSP test.")
        shutdown_services()
        return

    # Give ServiceDiscoveryModule some time to receive capability advertisements
    await asyncio.sleep(2)

    # Request all AIs to re-advertise their capabilities to ensure discovery
    print("Requesting capability re-advertisements...")
    hsp_connector.request_capability_re_advertisement()

    # Poll for the Echo Capability to ensure it's discovered
    # 1. Find the Echo Capability
    print("Polling for Echo Capability...")
    found_capabilities: list[HSPCapabilityAdvertisementPayload] = []
    max_retries = 10
    retry_delay = 0.5 # seconds
    for i in range(max_retries):
        found_capabilities = service_discovery.find_capabilities(capability_id_filter=ECHO_CAPABILITY_ID) # Changed to capability_id_filter
        if found_capabilities:
            print(f"Echo Capability found after {i+1} retries.")
            break
        print(f"Attempt {i+1}/{max_retries}: Echo Capability not yet found. Retrying in {retry_delay}s...")
        await asyncio.sleep(retry_delay)

    if not found_capabilities:
        print(f"ERROR: Echo capability '{ECHO_CAPABILITY_ID}' not found after {max_retries} retries. Is echo_task_executor.py running and advertising?")
        shutdown_services()
        return

    selected_capability = found_capabilities[0]
    print(f"Found Echo Capability: {selected_capability.get('name')} from AI: {selected_capability.get('ai_id')}")

    # 2. Prepare the Echo Task Request Payload
    echo_request_payload: HSPEchoTaskRequestPayload = {"message": echo_message}

    # 3. Prepare the general HSP Task Request Payload
    task_request_payload: HSPTaskRequestPayload = {
        "request_id": str(uuid.uuid4()),
        "requester_ai_id": dialogue_manager.ai_id, # Use the DM's AI ID as requester
        "target_ai_id": echo_target_ai_id,
        "capability_id_filter": ECHO_CAPABILITY_ID,
        "parameters": echo_request_payload,
        "callback_address": f"hsp/results/{dialogue_manager.ai_id}/#" # Listen for results on a specific topic
    }

    # Use an asyncio.Queue to get the result from the callback
    echo_result_queue = asyncio.Queue()

    def echo_result_callback(result_payload: HSPEchoTaskResultPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
        if full_envelope.get("correlation_id") == task_request_payload["request_id"]:
            print(f"\n--- Received Echo Task Result from {sender_ai_id} ---")
            print(f"Status: {result_payload.get('status')}")
            if result_payload.get("status") == "success":
                echoed_data: HSPEchoTaskResultPayload = result_payload["payload"] # type: ignore
                print(f"Echoed Message: {echoed_data.get('echoed_message')}")
                print(f"Original Request ID: {echoed_data.get('original_request_id')}")
            else:
                print(f"Error Details: {result_payload.get('error_details')}")
            echo_result_queue.put_nowait(result_payload) # Put the full result payload into the queue

    # Register the callback
    hsp_connector.register_on_task_result_callback(echo_result_callback)

    # 4. Send the Task Request
    print(f"Sending Echo Task Request with message: \"{echo_message}\"")
    correlation_id = hsp_connector.send_task_request(task_request_payload, echo_target_ai_id)

    if correlation_id:
        print(f"Task Request sent. Correlation ID: {correlation_id}. Waiting for result...")
        try:
            # Wait for the result with a timeout
            received_result = await asyncio.wait_for(echo_result_queue.get(), timeout=10) # 10 second timeout
            print("HSP Echo Test Completed.")
        except asyncio.TimeoutError:
            print("HSP Echo Test: Timed out waiting for echo result.")
        finally:
            # Clean up the callback
            hsp_connector.unregister_on_task_result_callback(echo_result_callback)
    else:
        print("Failed to send HSP Task Request.")

    # Cleanly shut down services
    shutdown_services()
    print("--- Simple Test Script Finished ---")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # Configure logging
    # Ensure the environment variable is set before running
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        print("Please set it before running this script.")
    else:
        asyncio.run(main())
