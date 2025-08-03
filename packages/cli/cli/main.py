import argparse
import sys
import asyncio
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.backend.src.hsp.types import HSPFactPayload, HSPMessageEnvelope, HSPCapabilityAdvertisementPayload, HSPTaskResultPayload # Added HSPTaskResultPayload
from apps.backend.src.core_services import initialize_services, get_services, shutdown_services, DEFAULT_AI_ID, DEFAULT_OPERATIONAL_CONFIGS # Import new service management

# --- CLI Specific AI ID ---
cli_ai_id = f"did:hsp:cli_ai_instance_{uuid.uuid4().hex[:6]}"

# --- HSP Callbacks for CLI ---
# These callbacks will now use services obtained from get_services()
def cli_handle_incoming_hsp_fact(fact_payload: HSPFactPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
    services = get_services()
    learning_manager = services.get("learning_manager")
    print(f"\n[CLI App] HSP Fact Received from '{sender_ai_id}':")
    print(f"  Fact ID: {fact_payload.get('id')}, Statement: {fact_payload.get('statement_nl') or fact_payload.get('statement_structured')}")
    if learning_manager:
        print(f"  Forwarding to LearningManager for processing...")
        # Note: LearningManager's process_and_store_hsp_fact might call ContentAnalyzer internally
        learning_manager.process_and_store_hsp_fact(fact_payload, sender_ai_id, full_envelope)
    else:
        print("  LearningManager not available via core_services, cannot process HSP fact.")

def cli_handle_incoming_capability_advertisement(cap_payload: HSPCapabilityAdvertisementPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
    services = get_services()
    service_discovery_module = services.get("service_discovery")
    print(f"\n[CLI App] HSP Capability Advertisement Received from '{sender_ai_id}':")
    print(f"  Capability ID: {cap_payload.get('capability_id')}, Name: {cap_payload.get('name')}")
    if service_discovery_module:
        service_discovery_module.process_capability_advertisement(cap_payload, sender_ai_id, full_envelope)
    else:
        print("  ServiceDiscoveryModule not available via core_services, cannot process capability advertisement.")

def cli_handle_incoming_task_result(result_payload: HSPTaskResultPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
    # This is a generic handler for task results if CLI were to directly observe them.
    # However, DialogueManager handles task results it initiated.
    # This callback might be useful if CLI itself sends a task request and needs to handle the result directly.
    # For now, DM's own callback registered in its __init__ (via core_services) handles results for DM-initiated tasks.
    print(f"\n[CLI App] Generic HSP TaskResult Received from '{sender_ai_id}' for CorrID '{full_envelope.get('correlation_id')}':")
    print(f"  Status: {result_payload.get('status')}, Payload: {result_payload.get('payload')}")


def setup_cli_hsp_callbacks():
    """Registers CLI-specific HSP callbacks AFTER core services are initialized."""
    services = get_services()
    hsp_connector = services.get("hsp_connector")
    if hsp_connector:
        # The core_services.initialize_services already registers:
        # - LearningManager's fact callback
        # - ServiceDiscoveryModule's capability advertisement callback
        # - DialogueManager's task result callback (via DM's __init__)

        # If CLI needs to *additionally* or *differently* handle these, register here.
        # For example, to just print *all* facts, not just those processed by LM:
        # hsp_connector.register_on_fact_callback(cli_handle_incoming_hsp_fact)
        # For now, we rely on the service-level registrations done in core_services.
        print("CLI App: Core service HSP callbacks are expected to be registered by initialize_services.")
        # If we wanted the CLI to also directly see all facts (in addition to LM), we could do:
        # hsp_connector.register_on_fact_callback(cli_handle_incoming_hsp_fact) # This would make CLI print them too.
        # hsp_connector.register_on_capability_advertisement_callback(cli_handle_incoming_capability_advertisement) # If SDM wasn't already doing it.
        # hsp_connector.register_on_task_result_callback(cli_handle_incoming_task_result) # If CLI needs to see ALL task results.

    else:
        print("CLI App: HSPConnector not available from core_services. Cannot register CLI HSP callbacks.")


async def handle_query(args):
    services = get_services()
    dialogue_manager = services.get("dialogue_manager")
    if not dialogue_manager:
        print("CLI Error: DialogueManager not available from core_services.")
        return

    print(f"CLI: Sending query to DialogueManager: '{args.query_text}'")

    response_text = await dialogue_manager.get_simple_response(
        user_input=args.query_text,
        user_id="cli_user",
        session_id=f"cli_session_{uuid.uuid4().hex[:6]}" # Unique session for each query
    )
    print(f"AI: {response_text}")


def handle_publish_fact(args):
    services = get_services()
    hsp_connector = services.get("hsp_connector")
    # The AI ID used for publishing should be the one this CLI instance was initialized with.
    # core_services.initialize_services takes an ai_id.
    # We stored it as `cli_ai_id` at the top of this script for clarity.

    # Retrieve the AI ID that the services were initialized with
    # This assumes that the services (like DM) store their ai_id
    dm_instance = services.get("dialogue_manager")
    current_instance_ai_id = dm_instance.ai_id if dm_instance else cli_ai_id


    if not hsp_connector or not hsp_connector.is_connected:
        print("CLI Error: HSPConnector not ready for publishing.")
        return

    print(f"CLI: Publishing a manual fact via HSP as AI '{current_instance_ai_id}': '{args.fact_statement}'")
    fact_id = f"manual_cli_fact_{uuid.uuid4().hex[:6]}"
    timestamp = datetime.now(timezone.utc).isoformat()

    hsp_payload = HSPFactPayload(
        id=fact_id,
        statement_type="natural_language",
        statement_nl=args.fact_statement,
        source_ai_id=current_instance_ai_id,
        timestamp_created=timestamp,
        confidence_score=args.confidence,
        weight=1.0, #type: ignore
        tags=["manual_cli_fact"] #type: ignore
    )

    learning_manager_instance = services.get("learning_manager")
    topic = args.topic or (learning_manager_instance.default_hsp_fact_topic if learning_manager_instance else "hsp/knowledge/facts/cli_manual") #type: ignore

    success = hsp_connector.publish_fact(hsp_payload, topic)
    if success:
        print(f"CLI: Manual fact '{fact_id}' published to topic '{topic}'.")
    else:
        print(f"CLI: Failed to publish manual fact to topic '{topic}'.")


async def main_cli_logic():
    parser = argparse.ArgumentParser(description="Unified-AI-Project Command Line Interface")
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=False)

    query_parser = subparsers.add_parser("query", help="Send a query to the AI")
    query_parser.add_argument("query_text", type=str, help="The query text to send to the AI")
    query_parser.set_defaults(func=handle_query)

    publish_parser = subparsers.add_parser("publish_fact", help="Manually publish a fact via HSP")
    publish_parser.add_argument("fact_statement", type=str, help="The statement of the fact")
    publish_parser.add_argument("--confidence", type=float, default=0.9, help="Confidence score (0.0-1.0)")
    publish_parser.add_argument("--topic", type=str, help="HSP topic to publish to")
    publish_parser.set_defaults(func=handle_publish_fact)

    print(f"--- Unified-AI-Project CLI (Instance AI ID will be: {cli_ai_id}) ---")

    # Initialize core services
    # For CLI, we might want to use MockHAM and MockLLM by default.
    # core_services.initialize_services can be extended to accept flags for this.
    config = {
        "mcp": {
            "mqtt_broker_address": "localhost",
            "mqtt_broker_port": 1883,
            "enable_fallback": True,
            "fallback_config": {}
        }
    }
    await initialize_services(
        config=config,
        ai_id=cli_ai_id,
        use_mock_ham=True, # Use MockHAM for CLI
        
        operational_configs=DEFAULT_OPERATIONAL_CONFIGS
    )
    services = get_services()
    service_discovery_module = services.get("service_discovery")
    if service_discovery_module:
        service_discovery_module.start_cleanup_task()
    setup_cli_hsp_callbacks() # Register any CLI-specific callbacks if needed

    try:
        if len(sys.argv) <= 1 :
             parser.print_help(sys.stderr)
             # Keep CLI running to listen for HSP messages if no command is given
             print("\nCLI: No command provided. Listening for HSP messages for 60 seconds (Ctrl+C to exit)...")
             await asyncio.sleep(60)
             return # Exit the function gracefully

        args = parser.parse_args()
        if hasattr(args, 'func'):
            if asyncio.iscoroutinefunction(args.func):
                await args.func(args)
            else:
                args.func(args)
            # If it was not a query, keep alive briefly for HSP messages
            if args.command != "query":
                 print("\nCLI: Task complete. Listening for HSP messages for a few seconds (Ctrl+C to exit)...")
                 await asyncio.sleep(10)
        else: # Should be caught by len(sys.argv) check if truly no command
            parser.print_help(sys.stderr)


    except KeyboardInterrupt:
        print("\nCLI: Keyboard interrupt received. Shutting down...")
    except Exception as e:
        print(f"\nCLI Error: An unexpected error occurred: {e}")
    finally:
        print("CLI: Initiating service shutdown...")
        if service_discovery_module:
            service_discovery_module.stop_cleanup_task()
        await shutdown_services() # From core_services
        print("CLI: Exiting.")


if __name__ == '__main__':
    asyncio.run(main_cli_logic())
