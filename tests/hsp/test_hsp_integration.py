import pytest
import asyncio
import uuid
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, call # Using unittest.mock with pytest

# Ensure src is in path for imports if running tests from root or using pytest from root
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.hsp.connector import HSPConnector
from src.hsp.types import HSPFactPayload, HSPMessageEnvelope # Assuming these are defined
from src.core_ai.learning.learning_manager import LearningManager
from src.core_ai.learning.fact_extractor_module import FactExtractorModule
from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule
from src.core_ai.memory.ham_memory_manager import HAMMemoryManager # Will mock this
from src.services.llm_interface import LLMInterface, LLMInterfaceConfig # Will mock this

# --- Constants for Testing ---
TEST_AI_ID_MAIN = "did:hsp:test_ai_main_001"
TEST_AI_ID_PEER = "did:hsp:test_ai_peer_002"
MQTT_BROKER_ADDRESS = "localhost"
MQTT_BROKER_PORT = 1883 # Default MQTT port

# General Fact Topic for these tests
FACT_TOPIC_GENERAL = "hsp/knowledge/facts/test_general"
FACT_TOPIC_USER_STATEMENTS = "hsp/knowledge/facts/test_user_statements"


# --- Mock Classes ---
class MockLLMInterface(LLMInterface):
    def __init__(self, config: Optional[LLMInterfaceConfig] = None):
        super().__init__(config or {"default_provider": "mock"}) #type: ignore
        self.mock_responses: Dict[str, str] = {}

    def add_mock_response(self, prompt_contains: str, response: str):
        self.mock_responses[prompt_contains] = response

    def generate_response(self, prompt: str, model_name: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> str:
        for key, resp in self.mock_responses.items():
            if key in prompt:
                return resp
        return "{}" # Default empty JSON list for fact extraction if no specific mock

class MockHAM(HAMMemoryManager):
    def __init__(self):
        # super().__init__(encryption_key="mock_key_for_test_ham", db_path=None, auto_load=False)
        self.memory_store: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
        print("Test: Using MockHAMMemoryManager.")

    def store_experience(self, raw_data: Any, data_type: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        mem_id = f"mock_ham_test_{self.next_id}"
        self.next_id += 1
        self.memory_store[mem_id] = {"raw_data": raw_data, "data_type": data_type, "metadata": metadata or {}}
        return mem_id
    # Add other methods if needed by LearningManager during tests


# --- Pytest Fixtures ---
@pytest.fixture(scope="module") # module scope for potentially shared broker connection if tests are slow
def event_loop():
    """Overrides pytest default event loop to enable module-scoped async fixtures if needed,
       though for paho-mqtt's threaded loop, direct asyncio might not be primary focus here."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_llm():
    llm = MockLLMInterface()
    # Pre-configure for FactExtractorModule if it's used to generate facts for publishing
    llm.add_mock_response(
        "My favorite food is pizza",
        '[{"fact_type": "user_preference", "content": {"category": "food", "preference": "pizza"}, "confidence": 0.95}]'
    )
    llm.add_mock_response(
        "Berlin is the capital of Germany", # A statement that might be published
        '[{"fact_type": "general_statement", "content": {"subject": "Berlin", "relation": "is_capital_of", "object": "Germany"}, "confidence": 0.99}]'
    )
    return llm

@pytest.fixture
def fact_extractor(mock_llm):
    return FactExtractorModule(llm_interface=mock_llm)

@pytest.fixture
def ham_manager():
    return MockHAM()

@pytest.fixture
def content_analyzer():
    # Uses default "en_core_web_sm", ensure it's available or tests might be slow/fail on first run
    return ContentAnalyzerModule()

@pytest.fixture
def main_ai_hsp_connector():
    connector = HSPConnector(TEST_AI_ID_MAIN, MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, client_id_suffix="main_test")
    if not connector.connect():
        pytest.fail("Failed to connect main_ai_hsp_connector to MQTT broker. Ensure broker is running.")
    # Give a moment for connection to establish fully with paho-mqtt's threaded loop
    time.sleep(0.5)
    yield connector
    connector.disconnect()
    time.sleep(0.1)


@pytest.fixture
def peer_hsp_connector():
    connector = HSPConnector(TEST_AI_ID_PEER, MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, client_id_suffix="peer_test")
    if not connector.connect():
        pytest.fail("Failed to connect peer_hsp_connector to MQTT broker. Ensure broker is running.")
    time.sleep(0.5)
    yield connector
    connector.disconnect()
    time.sleep(0.1)


@pytest.fixture
def learning_manager(ham_manager, fact_extractor, content_analyzer, main_ai_hsp_connector):
    config = {
        "learning_thresholds": {
            "min_fact_confidence_to_store": 0.7,
            "min_fact_confidence_to_share_via_hsp": 0.8,
            "min_hsp_fact_confidence_to_store": 0.6
        },
        "default_hsp_fact_topic": FACT_TOPIC_GENERAL
    }
    lm = LearningManager(
        ai_id=TEST_AI_ID_MAIN,
        ham_memory_manager=ham_manager,
        fact_extractor=fact_extractor,
        content_analyzer=content_analyzer,
        hsp_connector=main_ai_hsp_connector,
        operational_config=config
    )
    return lm


# --- Test Classes ---

class TestHSPFactPublishing:
    def test_learning_manager_publishes_fact_via_hsp(
        self, learning_manager, fact_extractor, peer_hsp_connector
    ):
        """
        Test Case 1: Main AI (via LearningManager) extracts and publishes a fact,
                     Mock Peer's connector verifies reception.
        """
        received_facts_on_peer = []
        def peer_fact_handler(fact_payload: HSPFactPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
            print(f"[Peer Test Handler] Received fact from {sender_ai_id}: {fact_payload.get('id')}")
            if sender_ai_id == TEST_AI_ID_MAIN: # Filter for messages from our main AI
                received_facts_on_peer.append({"payload": fact_payload, "envelope": envelope})

        peer_hsp_connector.register_on_fact_callback(peer_fact_handler)
        # Peer subscribes to the topic where LearningManager will publish
        # LearningManager will use fact_type to determine specific topic or default.
        # Let's assume "user_statement" facts get published to FACT_TOPIC_USER_STATEMENTS based on LM logic.
        # The mock LLM for "Berlin..." returns "general_statement".
        # Let's adjust the LM's default topic or the subscription here for simplicity of this first test.
        # LM's publish_fact logic: if "user_preference" -> user_preferences topic, "user_statement" -> user_statements topic, else default.
        # Our mock fact is "general_statement". So it should go to learning_manager.default_hsp_fact_topic (FACT_TOPIC_GENERAL)

        assert peer_hsp_connector.subscribe(FACT_TOPIC_GENERAL), "Peer failed to subscribe to general fact topic"
        time.sleep(0.2) # Allow subscription to establish

        # Trigger fact extraction and potential publishing in LearningManager
        # This input should trigger the "Berlin is capital of Germany" mock from LLM (conf 0.99)
        # which is >= min_fact_confidence_to_share_via_hsp (0.8)
        print("\n[Test Main AI Publishes] Triggering LM to process text...")
        learning_manager.process_and_store_learnables(
            text="Berlin is the capital of Germany.", # This text matches mock_llm
            user_id="test_user_pub",
            session_id="test_session_pub",
            source_interaction_ref="test_interaction_pub_01"
        )

        # Wait for message to be published and received
        time.sleep(1) # Increased wait time for MQTT round trip

        assert len(received_facts_on_peer) > 0, "Peer did not receive any facts from main AI"

        received_fact_payload = received_facts_on_peer[0]["payload"]
        assert received_fact_payload["source_ai_id"] == TEST_AI_ID_MAIN
        # Check some content from the "Berlin is capital of Germany" fact
        # The mock LLM returns: {"fact_type": "general_statement", "content": {"subject": "Berlin", ...}, "confidence": 0.99}
        # LM then constructs HSPFactPayload. statement_structured should be this content.
        assert received_fact_payload["statement_structured"].get("subject") == "Berlin"
        assert received_fact_payload["confidence_score"] == 0.99

        print(f"[Test Main AI Publishes] Successfully verified fact reception by peer. Content: {received_fact_payload['statement_structured']}")


class TestHSPFactConsumption:
    @pytest.mark.asyncio # If any part of this test needs async, though paho-mqtt is threaded.
    async def test_main_ai_consumes_fact_and_updates_kg(
        self, learning_manager, content_analyzer, peer_hsp_connector, main_ai_hsp_connector
    ):
        """
        Test Case 2: Mock Peer publishes a fact, Main AI's connector receives it,
                     LearningManager processes it, ContentAnalyzer updates its KG.
        """
        # Main AI needs to be subscribed to the topic the peer will publish to.
        # The handle_incoming_hsp_fact callback in cli/main.py (and thus in LM via that)
        # is registered with main_ai_hsp_connector.
        # It's already subscribed to "hsp/knowledge/facts/#" by default in the test fixture setup for main_ai_hsp_connector
        # (or should be, let's assume main_ai_hsp_connector.subscribe("hsp/knowledge/facts/#") is called).
        # For this test, let's ensure main_ai_hsp_connector is explicitly subscribed to FACT_TOPIC_GENERAL
        if not main_ai_hsp_connector.subscribe(FACT_TOPIC_GENERAL):
             pytest.fail("Main AI connector failed to subscribe to general fact topic")
        time.sleep(0.2) # Allow subscription

        # Mock the methods that would be called on LM and CA to verify flow
        learning_manager.process_and_store_hsp_fact = MagicMock(wraps=learning_manager.process_and_store_hsp_fact)
        content_analyzer.process_hsp_fact_content = MagicMock(wraps=content_analyzer.process_hsp_fact_content)

        # Mock Peer publishes a fact
        published_fact_id = f"peer_fact_{uuid.uuid4().hex[:6]}"
        fact_to_publish = HSPFactPayload(
            id=published_fact_id,
            statement_type="natural_language",
            statement_nl="The Mock Peer observes that today is a good day for testing.",
            source_ai_id=TEST_AI_ID_PEER, # Peer is the source
            timestamp_created=datetime.now(timezone.utc).isoformat(),
            confidence_score=0.95,
            tags=["mock_observation"]
        )
        print(f"\n[Test Main AI Consumes] Peer publishing fact: {published_fact_id}")
        peer_hsp_connector.publish_fact(fact_to_publish, topic=FACT_TOPIC_GENERAL)

        # Wait for message processing
        await asyncio.sleep(1.0) # Increased wait time

        # Assertions
        # 1. LearningManager's processing method was called
        assert learning_manager.process_and_store_hsp_fact.called, \
            "LearningManager.process_and_store_hsp_fact was not called"

        # Get the arguments it was called with
        # If called, process_and_store_hsp_fact_args will be a tuple: (args, kwargs)
        # We expect (hsp_fact_payload, hsp_sender_ai_id, hsp_envelope)
        call_args_list = learning_manager.process_and_store_hsp_fact.call_args_list
        assert len(call_args_list) > 0, "process_and_store_hsp_fact call_args_list is empty"

        args_tuple, _ = call_args_list[0] # Get args from the first call
        received_payload_in_lm = args_tuple[0]
        sender_in_lm = args_tuple[1]

        assert sender_in_lm == TEST_AI_ID_PEER
        assert received_payload_in_lm.get("id") == published_fact_id

        # 2. ContentAnalyzer's processing method was called
        assert content_analyzer.process_hsp_fact_content.called, \
            "ContentAnalyzer.process_hsp_fact_content was not called"

        ca_call_args_list = content_analyzer.process_hsp_fact_content.call_args_list
        assert len(ca_call_args_list) > 0, "process_hsp_fact_content call_args_list is empty"

        ca_args_tuple, _ = ca_call_args_list[0]
        payload_in_ca = ca_args_tuple[0] # hsp_fact_payload (as dict)
        sender_in_ca = ca_args_tuple[1] # source_ai_id

        assert sender_in_ca == TEST_AI_ID_PEER # This is hsp_sender_ai_id from LM
        assert payload_in_ca.get("id") == published_fact_id

        # 3. Check ContentAnalyzer's graph for updates
        # The NL fact "The Mock Peer observes that today is a good day for testing."
        # should result in some nodes/edges.
        # Example: find a node related to "Mock Peer" or "good day"
        # This requires ContentAnalyzer to have run its NLP pipeline.
        graph = content_analyzer.graph
        assert graph.number_of_nodes() > 0, "ContentAnalyzer graph has no nodes after processing HSP fact."

        # Example check: Look for an entity that might have been created from the NL
        # This is highly dependent on the NLP model and extraction logic.
        found_test_related_node = False
        test_node_label = ""
        for node_id, node_data in graph.nodes(data=True):
            label = node_data.get("label", "")
            if "mock peer" in label.lower() or "good day" in label.lower() or "testing" in label.lower():
                found_test_related_node = True
                test_node_label = label
                # Check for hsp_source_info attribute added by process_hsp_fact_content
                assert 'hsp_source_info' in node_data
                assert node_data['hsp_source_info']['origin_fact_id'] == published_fact_id
                assert node_data['hsp_source_info']['source_ai'] == TEST_AI_ID_PEER
                break

        assert found_test_related_node, f"Could not find a relevant node in ContentAnalyzer graph. Graph nodes: {list(graph.nodes(data=True))}"
        print(f"[Test Main AI Consumes] Successfully verified fact consumption and KG update (found node: '{test_node_label}').")

        # TODO: Add a test case for structured (semantic triple) fact consumption by ContentAnalyzer.
        # This would involve peer_hsp_connector publishing a fact with statement_type="semantic_triple"
        # and then asserting specific nodes/edges based on those triples in content_analyzer.graph.

# To run these tests:
# 1. Ensure an MQTT broker is running on localhost:1883
# 2. From the project root: pytest tests/hsp/test_hsp_integration.py
#
# Note: These tests involve network communication and timing, so they might be
#       a bit slower or occasionally flaky if network/broker is unstable.
#       Proper async handling with an async MQTT client might improve reliability
#       if paho-mqtt's threaded loop causes issues in complex pytest scenarios.
#       For now, `time.sleep` is used for simplicity to allow messages to propagate.
```

This sets up:
*   Mock LLM and HAM.
*   Pytest fixtures for `HSPConnector` instances (one for "main AI", one for "peer AI"), `LearningManager`, `FactExtractorModule`, and `ContentAnalyzerModule`.
*   `TestHSPFactPublishing` class with `test_learning_manager_publishes_fact_via_hsp`.
*   `TestHSPFactConsumption` class with `test_main_ai_consumes_fact_and_updates_kg`.

**Important Considerations for these tests:**
*   **MQTT Broker Dependency:** These tests require an MQTT broker running at `localhost:1883`. This is an external dependency.
*   **Timing (`time.sleep`):** `paho-mqtt` runs its network loop in a separate thread. `time.sleep()` is used to give time for messages to be sent, received, and processed. This can make tests slower and potentially a bit flaky. For more robust async testing with MQTT, an `asyncio`-native MQTT client (`aio-mqtt`, `gmqtt`) would be better, allowing `await` for operations. However, `paho-mqtt` is what `HSPConnector` currently uses.
*   **Graph Inspection:** Testing the `ContentAnalyzerModule`'s graph update requires making some assumptions about what nodes/edges will be created from the NLP processing of the test fact. This can be brittle if the NLP model or extraction logic changes. More specific query methods on `ContentAnalyzerModule` might be needed for robust testing of its state.
*   **Scope of Mocks:** `LLMInterface` and `HAMMemoryManager` are mocked to isolate the HSP interaction and KG update logic.

I'll now create this file.
