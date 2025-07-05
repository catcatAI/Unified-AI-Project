import argparse
import sys
import asyncio
import uuid
from typing import Dict, Any, Optional

import argparse
import sys
import asyncio
import uuid
from typing import Dict, Any, Optional, List # Added List for MockHAM

import argparse
import sys
import asyncio
import uuid
from typing import Dict, Any, Optional, List # Added List for MockHAM

# Assuming src is in PYTHONPATH or this script is run from project root level
from core_ai.dialogue.dialogue_manager import DialogueManager
from core_ai.learning.learning_manager import LearningManager
from core_ai.learning.fact_extractor_module import FactExtractorModule
from core_ai.learning.content_analyzer_module import ContentAnalyzerModule
from core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule # Import ServiceDiscoveryModule
from core_ai.memory.ham_memory_manager import HAMMemoryManager
from services.llm_interface import LLMInterface, LLMInterfaceConfig
from hsp.connector import HSPConnector
from hsp.types import HSPFactPayload, HSPMessageEnvelope, HSPCapabilityAdvertisementPayload # Added HSPCapabilityAdvertisementPayload


# --- Global instances for simplicity in this CLI PoC ---
# In a real app, these would be managed by a proper application context or dependency injection.
cli_ai_id = f"did:hsp:cli_ai_instance_{uuid.uuid4().hex[:6]}"
llm_config: LLMInterfaceConfig = { #type: ignore
    "default_provider": "mock", "default_model": "cli-mock-v1",
    "providers": {}, "default_generation_params": {}
}
llm_interface = LLMInterface(config=llm_config) # Use mock LLM for CLI stability
fact_extractor = FactExtractorModule(llm_interface=llm_interface)

# Mock HAM for CLI PoC to avoid file I/O and encryption complexities here
class MockHAM(HAMMemoryManager):
    def __init__(self):
        super().__init__(encryption_key="mock_key_for_cli_ham_ignore", db_path=None, auto_load=False) # type: ignore
        self.memory_store: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
        print("CLI_PoC: Using MockHAMMemoryManager.")

    def store_experience(self, raw_data: Any, data_type: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        mem_id = f"mock_ham_{self.next_id}"
        self.next_id += 1
        self.memory_store[mem_id] = {"raw_data": raw_data, "data_type": data_type, "metadata": metadata or {}}
        print(f"MockHAM: Stored '{data_type}' with ID {mem_id}. Meta: {metadata}")
        return mem_id

    def recall_experience(self, memory_id: str) -> Optional[Dict[str, Any]]:
        return self.memory_store.get(memory_id)

    def search_memories(self, search_query: str, search_type: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10) -> List[Dict[str, Any]]: # type: ignore
        # Simplified search
        results = []
        for mem_id, entry in self.memory_store.items():
            if search_query.lower() in str(entry.get('raw_data', '')).lower() or \
               search_query.lower() in str(entry.get('metadata', {})).lower():
                results.append({"memory_id": mem_id, "data": entry['raw_data'], "metadata": entry['metadata'], "score": 1.0})
                if len(results) >= limit:
                    break
        return results


ham_manager = MockHAM() # Using MockHAM for CLI

hsp_connector: Optional[HSPConnector] = None
learning_manager: Optional[LearningManager] = None
dialogue_manager: Optional[DialogueManager] = None
service_discovery_module: Optional[ServiceDiscoveryModule] = None # Add global for ServiceDiscoveryModule

# --- HSP Callbacks ---
def handle_incoming_hsp_fact(fact_payload: HSPFactPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
    global learning_manager # Ensure global learning_manager is accessible
    print(f"\n[CLI App] HSP Fact Received from '{sender_ai_id}':")
    print(f"  Fact ID: {fact_payload.get('id')}, Statement: {fact_payload.get('statement_nl') or fact_payload.get('statement_structured')}")
    if learning_manager:
        print(f"  Forwarding to LearningManager for processing...")
        learning_manager.process_and_store_hsp_fact(fact_payload, sender_ai_id, full_envelope)
    else:
        print("  LearningManager not initialized, cannot process HSP fact.")

def handle_incoming_capability_advertisement(cap_payload: HSPCapabilityAdvertisementPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope):
    global service_discovery_module # Ensure global service_discovery_module is accessible
    print(f"\n[CLI App] HSP Capability Advertisement Received from '{sender_ai_id}':")
    print(f"  Capability ID: {cap_payload.get('capability_id')}, Name: {cap_payload.get('name')}")
    if service_discovery_module:
        service_discovery_module.process_capability_advertisement(cap_payload, sender_ai_id, full_envelope)
    else:
        print("  ServiceDiscoveryModule not initialized, cannot process capability advertisement.")


def init_global_services():
    global hsp_connector, learning_manager, dialogue_manager, fact_extractor, service_discovery_module

    content_analyzer = ContentAnalyzerModule()
    service_discovery_module = ServiceDiscoveryModule() # Instantiate ServiceDiscoveryModule

    hsp_connector = HSPConnector(
        ai_id=cli_ai_id,
        broker_address="localhost", # Ensure MQTT broker is running here
        broker_port=1883
    )

    learning_manager_config = {
        "learning_thresholds": {
            "min_fact_confidence_to_store": 0.6,
            "min_fact_confidence_to_share_via_hsp": 0.75,
            "min_hsp_fact_confidence_to_store": 0.5 # Threshold for storing facts from HSP
        },
        "default_hsp_fact_topic": "hsp/knowledge/facts/cli_general"
    }
    learning_manager = LearningManager(
        ai_id=cli_ai_id,
        ham_memory_manager=ham_manager,
        fact_extractor=fact_extractor, # fact_extractor is already global
        content_analyzer=content_analyzer, # Pass content_analyzer
        hsp_connector=hsp_connector,
        operational_config=learning_manager_config
    )

    # Register callbacks with HSPConnector
    hsp_connector.register_on_fact_callback(handle_incoming_hsp_fact)
    hsp_connector.register_on_capability_advertisement_callback(handle_incoming_capability_advertisement)
    # TODO: Register callbacks for TaskRequest and TaskResult when DialogueManager/ToolDispatcher is ready to handle them.

    if hsp_connector.connect(): # Starts MQTT loop in background thread
        print(f"CLI App: HSPConnector connected for AI ID {cli_ai_id}. Subscribing to topics...")
        hsp_connector.subscribe("hsp/knowledge/facts/#") # Listen to all facts for PoC
        hsp_connector.subscribe("hsp/capabilities/advertisements/#") # Listen to all capability advertisements
    else:
        print(f"CLI App: FAILED to connect HSPConnector for AI ID {cli_ai_id}.")

    # Initialize DialogueManager
    # Pass ServiceDiscoveryModule to DialogueManager if it's going to use it directly for finding capabilities.
    # For now, DialogueManager is not directly using it in this CLI PoC.
    dialogue_manager = DialogueManager(
        learning_manager=learning_manager,
        # service_discovery=service_discovery_module # Example if DM needs it
        # llm_interface=llm_interface # DM already creates its own LLMInterface
    )
    print("CLI App: DialogueManager initialized.")


def handle_query(args):
    global dialogue_manager
    if not dialogue_manager:
        print("CLI Error: DialogueManager not initialized. Run init first or there was an issue.")
        return

    print(f"CLI: Sending query to DialogueManager: '{args.query_text}'")

    # DialogueManager.get_simple_response is async
    # It also internally calls LearningManager.process_and_store_learnables
    # which now also uses HSPConnector.publish_fact (which is synchronous)
    response_text = asyncio.run(dialogue_manager.get_simple_response(
        text_input=args.query_text,
        user_id="cli_user",
        session_id="cli_session_1"
        # Assuming get_simple_response is updated or calls a method that uses these
    ))
    print(f"AI: {response_text}")


def handle_publish_fact(args):
    global learning_manager
    if not learning_manager or not learning_manager.hsp_connector or not learning_manager.hsp_connector.is_connected:
        print("CLI Error: LearningManager or HSPConnector not ready for publishing.")
        return

    print(f"CLI: Publishing a manual fact via HSP: '{args.fact_statement}'")
    fact_id = f"manual_fact_{uuid.uuid4().hex[:6]}"
    timestamp = datetime.now(timezone.utc).isoformat()

    hsp_payload = HSPFactPayload(
        id=fact_id,
        statement_type="natural_language",
        statement_nl=args.fact_statement,
        source_ai_id=cli_ai_id,
        timestamp_created=timestamp,
        confidence_score=args.confidence, # Get from args
        weight=1.0,
        tags=["manual_cli_fact"]
    )
    topic = args.topic or learning_manager.default_hsp_fact_topic
    success = learning_manager.hsp_connector.publish_fact(hsp_payload, topic)
    if success:
        print(f"CLI: Manual fact '{fact_id}' published to topic '{topic}'.")
    else:
        print(f"CLI: Failed to publish manual fact to topic '{topic}'.")


def main_cli_logic():
    global hsp_connector # To access for shutdown

    parser = argparse.ArgumentParser(description="Unified-AI-Project Command Line Interface")
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # Query sub-command
    query_parser = subparsers.add_parser("query", help="Send a query to the AI")
    query_parser.add_argument("query_text", type=str, help="The query text to send to the AI")
    query_parser.set_defaults(func=handle_query)

    # Publish Fact sub-command (for testing HSP)
    publish_parser = subparsers.add_parser("publish_fact", help="Manually publish a fact via HSP")
    publish_parser.add_argument("fact_statement", type=str, help="The statement of the fact")
    publish_parser.add_argument("--confidence", type=float, default=0.9, help="Confidence score (0.0-1.0)")
    publish_parser.add_argument("--topic", type=str, help="HSP topic to publish to")
    publish_parser.set_defaults(func=handle_publish_fact)

    # Config sub-command (placeholder, not functional for HSP yet)
    # config_parser = subparsers.add_parser("config", help="Manage system configuration")
    # ... (config args) ...

    print(f"--- Unified-AI-Project CLI (AI ID: {cli_ai_id}) ---")

    try:
        init_global_services() # Initialize services including HSPConnector

        if len(sys.argv) <= 1 : # No actual command given, just script name
             parser.print_help(sys.stderr)
             sys.exit(1)

        args = parser.parse_args()
        args.func(args) # Call the appropriate handler

        # Keep alive briefly if not querying, to allow HSP messages to arrive if testing subscriptions
        if args.command != "query":
            print("\nCLI: Task complete. Listening for HSP messages for a few seconds (Ctrl+C to exit)...")
            asyncio.run(asyncio.sleep(10)) # Keep alive to receive messages if any test is ongoing

    except KeyboardInterrupt:
        print("\nCLI: Keyboard interrupt received. Shutting down...")
    except Exception as e:
        print(f"\nCLI Error: An unexpected error occurred: {e}")
    finally:
        if hsp_connector and hsp_connector.is_connected:
            print("CLI: Disconnecting HSPConnector...")
            hsp_connector.disconnect()
        print("CLI: Exiting.")


if __name__ == '__main__':
    main_cli_logic()
