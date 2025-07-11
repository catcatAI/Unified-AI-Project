import argparse
import sys
import asyncio
import uuid
from typing import Dict, Any, Optional, List
import gettext

# Assuming src is in PYTHONPATH or this script is run from project root level
from src.hsp.types import HSPFactPayload, HSPMessageEnvelope, HSPCapabilityAdvertisementPayload, HSPTaskResultPayload # Added src. and HSPTaskResultPayload
from src.core_services import initialize_services, get_services, shutdown_services, DEFAULT_AI_ID, DEFAULT_LLM_CONFIG, DEFAULT_OPERATIONAL_CONFIGS # Import new service management

import os # Added for environment variable

# Setup basic gettext for now
# In a real app, this would be more sophisticated, likely based on a global language setting
try:
    # Determine language from environment variable APP_LANG, default to 'en'
    app_lang = os.environ.get('APP_LANG', 'en')

    # Ensure localedir is absolute or relative to this script's location if needed.
    # For simplicity, assuming 'locales' is in the project root relative to where this script is run from.
    # A more robust way might be to calculate localedir based on script path.
    locales_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'locales')


    translation = gettext.translation('messages', localedir=locales_path, languages=[app_lang], fallback=True)
    translation.install()
    _ = translation.gettext
    print(f"CLI: Loaded translations for language: {app_lang}", file=sys.stderr)
except FileNotFoundError:
    # Fallback if .mo file not found or gettext not fully set up
    _ = lambda s: s
    print(f"CLI: Warning - Could not load translations for language '{os.environ.get('APP_LANG', 'en')}'. Using fallback (original strings). Ensure .mo files are compiled and locales_path is correct: {locales_path}", file=sys.stderr)


# --- CLI Specific AI ID ---
cli_ai_id = f"did:hsp:cli_ai_instance_{uuid.uuid4().hex[:6]}"

# --- HSP Callbacks for CLI ---
# These callbacks will now use services obtained from get_services()
def cli_handle_incoming_hsp_fact(fact_payload: HSPFactPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
    services = get_services()
    learning_manager = services.get("learning_manager")
    print(_("\n[CLI App] HSP Fact Received from '{sender_ai_id}':").format(sender_ai_id=sender_ai_id))
    print(_("  Fact ID: {fact_id}, Statement: {statement}").format(fact_id=fact_payload.get('id'), statement=(fact_payload.get('statement_nl') or fact_payload.get('statement_structured'))))
    if learning_manager:
        print(_("  Forwarding to LearningManager for processing..."))
        # Note: LearningManager's process_and_store_hsp_fact might call ContentAnalyzer internally
        learning_manager.process_and_store_hsp_fact(fact_payload, sender_ai_id, full_envelope)
    else:
        print(_("  LearningManager not available via core_services, cannot process HSP fact."))

def cli_handle_incoming_capability_advertisement(cap_payload: HSPCapabilityAdvertisementPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
    services = get_services()
    service_discovery_module = services.get("service_discovery")
    print(_("\n[CLI App] HSP Capability Advertisement Received from '{sender_ai_id}':").format(sender_ai_id=sender_ai_id))
    print(_("  Capability ID: {capability_id}, Name: {name}").format(capability_id=cap_payload.get('capability_id'), name=cap_payload.get('name')))
    if service_discovery_module:
        service_discovery_module.process_capability_advertisement(cap_payload, sender_ai_id, full_envelope)
    else:
        print(_("  ServiceDiscoveryModule not available via core_services, cannot process capability advertisement."))

def cli_handle_incoming_task_result(result_payload: HSPTaskResultPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
    # This is a generic handler for task results if CLI were to directly observe them.
    # However, DialogueManager handles task results it initiated.
    # This callback might be useful if CLI itself sends a task request and needs to handle the result directly.
    # For now, DM's own callback registered in its __init__ (via core_services) handles results for DM-initiated tasks.
    print(_("\n[CLI App] Generic HSP TaskResult Received from '{sender_ai_id}' for CorrID '{correlation_id}':").format(sender_ai_id=sender_ai_id, correlation_id=full_envelope.get('correlation_id')))
    print(_("  Status: {status}, Payload: {payload}").format(status=result_payload.get('status'), payload=result_payload.get('payload')))


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
        print(_("CLI App: Core service HSP callbacks are expected to be registered by initialize_services."))
        # If we wanted the CLI to also directly see all facts (in addition to LM), we could do:
        # hsp_connector.register_on_fact_callback(cli_handle_incoming_hsp_fact) # This would make CLI print them too.
        # hsp_connector.register_on_capability_advertisement_callback(cli_handle_incoming_capability_advertisement) # If SDM wasn't already doing it.
        # hsp_connector.register_on_task_result_callback(cli_handle_incoming_task_result) # If CLI needs to see ALL task results.

    else:
        print(_("CLI App: HSPConnector not available from core_services. Cannot register CLI HSP callbacks."))


def handle_query(args):
    services = get_services()
    dialogue_manager = services.get("dialogue_manager")
    if not dialogue_manager:
        print(_("CLI Error: DialogueManager not available from core_services."))
        return

    print(_("CLI: Sending query to DialogueManager: '{query_text}'").format(query_text=args.query_text))

    response_text = asyncio.run(dialogue_manager.get_simple_response(
        user_input=args.query_text, # Changed text_input to user_input
        user_id="cli_user",
        session_id=f"cli_session_{uuid.uuid4().hex[:6]}" # Unique session for each query
    ))
    print(_("AI: {response_text}").format(response_text=response_text))


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
        print(_("CLI Error: HSPConnector not ready for publishing."))
        return

    print(_("CLI: Publishing a manual fact via HSP as AI '{current_instance_ai_id}': '{fact_statement}'").format(current_instance_ai_id=current_instance_ai_id, fact_statement=args.fact_statement))
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
        print(_("CLI: Manual fact '{fact_id}' published to topic '{topic}'.").format(fact_id=fact_id, topic=topic))
    else:
        print(_("CLI: Failed to publish manual fact to topic '{topic}'.").format(topic=topic))


def main_cli_logic():
    parser = argparse.ArgumentParser(description=_("Unified-AI-Project Command Line Interface"))
    subparsers = parser.add_subparsers(dest="command", help=_("Available commands"), required=False)

    query_parser = subparsers.add_parser("query", help=_("Send a query to the AI"))
    query_parser.add_argument("query_text", type=str, help=_("The query text to send to the AI"))
    query_parser.set_defaults(func=handle_query)

    publish_parser = subparsers.add_parser("publish_fact", help=_("Manually publish a fact via HSP"))
    publish_parser.add_argument("fact_statement", type=str, help=_("The statement of the fact"))
    publish_parser.add_argument("--confidence", type=float, default=0.9, help=_("Confidence score (0.0-1.0)"))
    publish_parser.add_argument("--topic", type=str, help=_("HSP topic to publish to"))
    publish_parser.set_defaults(func=handle_publish_fact)

    print(_("--- Unified-AI-Project CLI (Instance AI ID will be: {cli_ai_id}) ---").format(cli_ai_id=cli_ai_id))

    # Initialize core services
    # For CLI, we might want to use MockHAM and MockLLM by default.
    # core_services.initialize_services can be extended to accept flags for this.
    initialize_services(
        ai_id=cli_ai_id,
        use_mock_ham=True, # Use MockHAM for CLI
        llm_config=DEFAULT_LLM_CONFIG, # Use mock LLM for CLI
        operational_configs=DEFAULT_OPERATIONAL_CONFIGS
    )
    setup_cli_hsp_callbacks() # Register any CLI-specific callbacks if needed

    try:
        if len(sys.argv) <= 1 :
             parser.print_help(sys.stderr)
             # Keep CLI running to listen for HSP messages if no command is given
             print(_("\nCLI: No command provided. Listening for HSP messages for 60 seconds (Ctrl+C to exit)..."))
             asyncio.run(asyncio.sleep(60))
             sys.exit(0)

        args = parser.parse_args()
        if hasattr(args, 'func'):
            args.func(args)
            # If it was not a query, keep alive briefly for HSP messages
            if args.command != "query":
                 print(_("\nCLI: Task complete. Listening for HSP messages for a few seconds (Ctrl+C to exit)..."))
                 asyncio.run(asyncio.sleep(10))
        else: # Should be caught by len(sys.argv) check if truly no command
            parser.print_help(sys.stderr)


    except KeyboardInterrupt:
        print(_("\nCLI: Keyboard interrupt received. Shutting down..."))
    except Exception as e:
        print(_("\nCLI Error: An unexpected error occurred: {error}").format(error=e))
    finally:
        print(_("CLI: Initiating service shutdown..."))
        shutdown_services() # From core_services
        print(_("CLI: Exiting."))


if __name__ == '__main__':
    main_cli_logic()
