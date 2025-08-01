import pytest
import asyncio
pytestmark = pytest.mark.asyncio
import uuid
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock, AsyncMock # Added for mock_mode
from typing import Dict, Any, Optional, List, Callable, Tuple, AsyncGenerator
import json

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

from src.hsp.connector import HSPConnector
from src.hsp.types import (

    HSPFactPayload,
    HSPMessageEnvelope,
    HSPCapabilityAdvertisementPayload,
    HSPTaskRequestPayload,
    HSPTaskResultPayload,
    HSPErrorDetails,
    HSPFactStatementStructured,
)
from src.core_ai.learning.learning_manager import LearningManager
from src.core_ai.learning.fact_extractor_module import FactExtractorModule
from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule
from src.core_ai.service_discovery.service_discovery_module import (
    ServiceDiscoveryModule,
)
from src.core_ai.trust_manager.trust_manager_module import TrustManager
from src.core_ai.memory.ham_memory_manager import HAMMemoryManager
from src.services.multi_llm_service import MultiLLMService, ModelConfig, ModelProvider, ChatMessage, LLMResponse
from src.core_ai.dialogue.dialogue_manager import DialogueManager
from src.tools.tool_dispatcher import ToolDispatcher
from src.core_ai.formula_engine import FormulaEngine
from src.shared.types.common_types import ToolDispatcherResponse
from src.core_ai.personality.personality_manager import PersonalityManager




import logging
import queue
import re

class MockMqttBroker:
    def __init__(self):
        self.subscriptions: Dict[str, List[Callable[[str, bytes], None]]] = {}
        self.published_messages: List[Tuple[str, bytes]] = []
        self.is_running = False

    async def start(self):
        logging.info("MockMqttBroker: Starting...")
        self.is_running = True

    async def shutdown(self):
        logging.info("MockMqttBroker: Shutting down...")
        self.is_running = False
        self.subscriptions.clear()
        self.published_messages.clear()

    async def publish(self, topic: str, payload: bytes, qos: int = 0):
        if not self.is_running:
            logging.warning(f"MockMqttBroker: Attempted to publish to {topic} but broker is not running.")
            return
        self.published_messages.append((topic, payload))
        logging.debug(f"MockMqttBroker: Published to {topic}: {payload.decode()}")
        await self._dispatch_message(topic, payload)

    async def subscribe(self, topic: str, callback: Callable[[str, bytes], None]):
        if not self.is_running:
            logging.warning(f"MockMqttBroker: Attempted to subscribe to {topic} but broker is not running.")
            return
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(callback)
        logging.debug(f"MockMqttBroker: Subscribed to {topic} with callback {callback}")

    async def _dispatch_message(self, topic: str, payload: bytes):
        logging.debug(f"Dispatching message to topic: {topic}")
        # Dispatch to all matching subscriptions, including wildcards
        for sub_topic, callbacks in self.subscriptions.items():
            logging.debug(f"Checking subscription: {sub_topic}")
            if self._match_topic(sub_topic, topic):
                logging.debug(f"Matched subscription: {sub_topic}")
                for callback in callbacks:
                    await self._safe_call_callback(callback, topic, payload)

    async def _safe_call_callback(self, callback: Callable[[str, bytes], None], topic: str, payload: bytes):
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(topic, payload)
            else:
                callback(topic, payload)
        except Exception as e:
            logging.error(f"Error in MQTT callback for topic {topic}: {e}")

    def _match_topic(self, sub_topic: str, pub_topic: str) -> bool:
        sub_parts = sub_topic.split('/')
        pub_parts = pub_topic.split('/')

        # Handle '#' wildcard
        if sub_parts and sub_parts[-1] == '#':
            # If '#' is the only part, it matches everything
            if len(sub_parts) == 1:
                return True
            # If '#' is at the end, it matches if the preceding parts match
            if len(pub_parts) >= len(sub_parts) - 1:
                for i in range(len(sub_parts) - 1):
                    if sub_parts[i] == '+':
                        if i >= len(pub_parts):
                            return False
                        continue
                    if sub_parts[i] != pub_parts[i]:
                        return False
                return True
            return False

        # For '+' and exact matches
        if len(sub_parts) != len(pub_parts):
            return False

        for i in range(len(sub_parts)):
            if sub_parts[i] == '+':
                continue  # '+' matches any single level
            if sub_parts[i] != pub_parts[i]:
                return False
        return True

    def get_published_messages(self) -> List[Tuple[str, bytes]]:
        return self.published_messages.copy()

    def clear_published_messages(self):
        self.published_messages.clear()

# --- Pytest Fixtures ---
from src.hsp.internal.internal_bus import InternalBus
from src.hsp.bridge.message_bridge import MessageBridge
from src.hsp.bridge.data_aligner import DataAligner

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def shared_internal_bus():
    return InternalBus()

@pytest.fixture(scope="function")
def shared_data_aligner():
    return DataAligner()


@pytest.fixture(scope="function")
def shared_message_bridge(broker: MockMqttBroker, shared_internal_bus: InternalBus, shared_data_aligner: DataAligner):
    # The MessageBridge needs an external_connector, which is the mock_mqtt_client from the broker
    # We'll create a dummy ExternalConnector for the MessageBridge to use,
    # but its on_message_callback will be overridden by the MessageBridge itself.
    # The key is that the mock_mqtt_client (broker) will call the MessageBridge's handler directly.
    class DummyExternalConnector:
        def __init__(self, mqtt_client):
            self.mqtt_client = mqtt_client
            self.on_message_callback = None # This will be set by MessageBridge

        async def connect(self): pass
        async def disconnect(self): pass
        async def publish(self, topic, payload, qos):
            # In this test setup, publish from the bridge should go to the mock broker
            await self.mqtt_client.publish(topic, payload, qos)

    dummy_external_connector = DummyExternalConnector(broker)
    bridge = MessageBridge(dummy_external_connector, shared_internal_bus, shared_data_aligner)
    return bridge

@pytest.fixture(scope="function")
async def broker():
    mock_broker = MockMqttBroker()
    await mock_broker.start()
    yield mock_broker
    await mock_broker.shutdown()


# --- Constants for Testing ---
TEST_AI_ID_MAIN = "did:hsp:test_ai_main_001"
TEST_AI_ID_PEER_A = "did:hsp:test_ai_peer_A_002"
TEST_AI_ID_PEER_B = "did:hsp:test_ai_peer_B_003"

MQTT_BROKER_ADDRESS = "127.0.0.1"  # Changed from localhost
MQTT_BROKER_PORT = 1883

FACT_TOPIC_GENERAL = "hsp/knowledge/facts/test_general"
CAP_ADVERTISEMENT_TOPIC = "hsp/capabilities/advertisements/general"

# Set logging level for HSPConnector to DEBUG for detailed output during tests
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("src.hsp.connector").setLevel(logging.DEBUG)
logging.getLogger("src.core_ai.service_discovery.service_discovery_module").setLevel(logging.DEBUG)
logging.getLogger("src.core_ai.dialogue.dialogue_manager").setLevel(logging.DEBUG)


# --- Mock Classes ---
class MockLLMInterface(MultiLLMService):
    def __init__(self):
        # Initialize attributes that MultiLLMService would normally set
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.model_configs: Dict[str, ModelConfig] = {
            "mock-model": ModelConfig(
                provider=ModelProvider.OPENAI, # Use a valid provider for ModelConfig
                model_name="mock-model",
                enabled=True
            )
        }
        self.default_model: Optional[str] = "mock-model"
        self.usage_stats: Dict[str, Dict[str, Any]] = {}

        self.mock_responses: Dict[str, str] = {}
        self.generate_response_history: List[Dict[str, Any]] = []

    def add_mock_response(self, prompt_contains: str, response: str):
        self.mock_responses[prompt_contains] = response

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        model_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        self.generate_response_history.append({"messages": messages, "model_id": model_id, "kwargs": kwargs})
        await asyncio.sleep(0.01) # Simulate async operation
        
        prompt_content = messages[0].content if messages and messages[0].content else ""
        
        for key, resp in self.mock_responses.items():
            if key in prompt_content:
                response_content = resp
                break
        else:
            if "completely_unhandled_query_for_llm" in prompt_content:
                response_content = "I'm not sure how to help with that, but I can process this with LLM."
            elif "hsp_task_failed_what_now" in prompt_content:
                response_content = "It seems the specialist AI couldn't help with that. Let me try to answer directly using my own knowledge."
            else:
                response_content = "[]" # Default response if no mock matches

        # Simulate usage and cost
        usage = {"prompt_tokens": len(prompt_content) // 4, "completion_tokens": len(response_content) // 4, "total_tokens": (len(prompt_content) + len(response_content)) // 4}
        cost = 0.0 # Mocked cost
        latency = 0.01 # Mocked latency

        return LLMResponse(
            content=response_content,
            model=model_id or self.default_model,
            provider=ModelProvider.OPENAI, # Or any other mock provider
            usage=usage,
            cost=cost,
            latency=latency,
            timestamp=datetime.now(),
            metadata={}
        )

    async def stream_completion(
        self,
        messages: List[ChatMessage],
        model_id: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        response_content = await self.chat_completion(messages, model_id, **kwargs)
        yield response_content.content


class MockHAM(HAMMemoryManager):
    def __init__(self):
        self.memory_store: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
        
    def store_experience(self, raw_data: Any, data_type: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        mem_id = f"mock_ham_test_{self.next_id}"
        if metadata and 'hsp_fact_id' in metadata and 'hsp_originator_ai_id' in metadata and 'supersedes_ham_record' in metadata:
            old_ham_id_to_supersede = metadata['supersedes_ham_record']
            if old_ham_id_to_supersede in self.memory_store:
                self.memory_store[old_ham_id_to_supersede]['metadata']['is_superseded_by'] = mem_id  # type: ignore
        self.next_id += 1
        self.memory_store[mem_id] = {"raw_data": raw_data, "data_type": data_type, "metadata": metadata or {}}
        return mem_id
        
    def get_experience_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        return self.memory_store.get(memory_id)
        
    def query_core_memory(self, metadata_filters: Optional[Dict[str, Any]] = None,
                          data_type_filter: Optional[str] = None, limit: int = 5, **kwargs) -> List[Dict[str, Any]]:
        results = []
        for mem_id, entry in self.memory_store.items():
            meta = entry.get("metadata", {})
            if meta.get('is_superseded_by'):
                continue
            match = True
            if data_type_filter and not entry.get("data_type", "").startswith(data_type_filter):
                match = False
            if metadata_filters and match:
                for key, value in metadata_filters.items():
                    if meta.get(key) != value:
                        match = False
                        break
            if match:
                results.append({
                    "id": mem_id, 
                    "metadata": meta, 
                    "raw_data": entry.get("raw_data"), 
                    "rehydrated_gist": {"summary": str(entry.get("raw_data"))}
                })
            if len(results) >= limit:
                break
        return results


# Helper function for async tests
async def wait_for_event(event, timeout=5.0):
    try:
        await asyncio.wait_for(event.wait(), timeout)
    except asyncio.TimeoutError:
        pytest.fail(f"Event wait timed out after {timeout} seconds")


# --- Pytest Fixtures ---
@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_fixture():
    llm = MockLLMInterface()
    llm.add_mock_response(
        "Berlin is the capital of Germany", 
        '[{"fact_type": "general_statement", "content": {"subject": "Berlin", "relation": "is_capital_of", "object": "Germany"}, "confidence": 0.99}]'
    )
    llm.add_mock_response("unsatisfactory_response_for_hsp_query_trigger", "I don't know about that topic.")
    return llm


@pytest.fixture
def fact_extractor_fixture(mock_llm_fixture: MockLLMInterface):
    return FactExtractorModule(llm_service=mock_llm_fixture)


@pytest.fixture
def ham_manager_fixture():
    return MockHAM()


@pytest.fixture(scope="module")  # Make CA module-scoped if its init is slow (spaCy load)
def content_analyzer_module_fixture():
    try:
        analyzer = ContentAnalyzerModule()
        # For tests that modify the graph, ensure it's cleaned or use a function-scoped fixture if preferred
        # For this test structure, we'll clear graph within tests that modify it.
        return analyzer
    except Exception as e:
        pytest.skip(f"Skipping ContentAnalyzer tests: {e}")


@pytest.fixture
def trust_manager_fixture() -> TrustManager:
    return TrustManager()


@pytest.fixture
def personality_manager_fixture() -> PersonalityManager:
    return PersonalityManager()


import threading

@pytest.fixture(scope="function")
@pytest.mark.timeout(30)  # Increased timeout for broker setup/teardown
async def broker():
    mock_broker = MockMqttBroker()
    await mock_broker.start()
    yield mock_broker
    await mock_broker.shutdown()


@pytest.fixture
async def main_ai_hsp_connector(trust_manager_fixture: TrustManager, broker: MockMqttBroker, shared_internal_bus: InternalBus, shared_message_bridge: MessageBridge):
    # broker is already started by the fixture
    connector = HSPConnector(
        TEST_AI_ID_MAIN,
        MQTT_BROKER_ADDRESS,
        MQTT_BROKER_PORT,
        mock_mode=True,
        mock_mqtt_client=broker, # Pass the mock broker directly
        internal_bus=shared_internal_bus,
        message_bridge=shared_message_bridge
    )
    await connector.connect()
    if not connector.is_connected:
        pytest.fail("Failed to connect main_ai_hsp_connector")

    yield connector

    await connector.disconnect()
    await asyncio.sleep(0.1)


@pytest.fixture
async def peer_a_hsp_connector(trust_manager_fixture: TrustManager, broker: MockMqttBroker, shared_internal_bus: InternalBus, shared_message_bridge: MessageBridge):
    # broker is already started by the fixture
    connector = HSPConnector(
        TEST_AI_ID_PEER_A,
        MQTT_BROKER_ADDRESS,
        MQTT_BROKER_PORT,
        mock_mode=True,
        mock_mqtt_client=broker, # Pass the mock broker directly
        internal_bus=shared_internal_bus,
        message_bridge=shared_message_bridge
    )
    await connector.connect()
    if not connector.is_connected:
        pytest.fail("Failed to connect peer_a_hsp_connector")

    yield connector

    await connector.disconnect()
    await asyncio.sleep(0.1)


@pytest.fixture
async def peer_b_hsp_connector(trust_manager_fixture: TrustManager, broker: MockMqttBroker, shared_internal_bus: InternalBus, shared_message_bridge: MessageBridge):
    # broker is already started by the fixture
    connector = HSPConnector(
        TEST_AI_ID_PEER_B,
        MQTT_BROKER_ADDRESS,
        MQTT_BROKER_PORT,
        mock_mode=True,
        mock_mqtt_client=broker, # Pass the mock broker directly
        internal_bus=shared_internal_bus,
        message_bridge=shared_message_bridge
    )
    await connector.connect()
    if not connector.is_connected:
        pytest.fail("Failed to connect peer_b_hsp_connector")

    yield connector

    await connector.disconnect()
    await asyncio.sleep(0.1)


@pytest.fixture
async def configured_learning_manager(
    ham_manager_fixture: MockHAM,
    fact_extractor_fixture: FactExtractorModule,
    content_analyzer_module_fixture: ContentAnalyzerModule,
    main_ai_hsp_connector: HSPConnector,
    trust_manager_fixture: TrustManager,
    personality_manager_fixture: PersonalityManager
):
    # main_ai_hsp_connector is now properly awaited by pytest-asyncio
    config = {
        "learning_thresholds": {
            "min_fact_confidence_to_store": 0.7,
            "min_fact_confidence_to_share_via_hsp": 0.8,
            "min_hsp_fact_confidence_to_store": 0.55,
            "hsp_fact_conflict_confidence_delta": 0.1
        },
        "default_hsp_fact_topic": FACT_TOPIC_GENERAL
    }
    lm = LearningManager(
        TEST_AI_ID_MAIN,
        ham_manager_fixture,
        fact_extractor_fixture,
        personality_manager_fixture,
        content_analyzer_module_fixture,
        main_ai_hsp_connector,
        trust_manager_fixture,
        config
    )
    if main_ai_hsp_connector:
        main_ai_hsp_connector.register_on_fact_callback(lm.process_and_store_hsp_fact)
    yield lm


@pytest.fixture
async def service_discovery_module_fixture(main_ai_hsp_connector: HSPConnector, trust_manager_fixture: TrustManager):
    # main_ai_hsp_connector is now properly awaited by pytest-asyncio
    sdm = ServiceDiscoveryModule(trust_manager=trust_manager_fixture)
    main_ai_hsp_connector.register_on_capability_advertisement_callback(sdm.process_capability_advertisement)
    await asyncio.sleep(0.2)
    yield sdm



@pytest.fixture
async def dialogue_manager_fixture(
    configured_learning_manager: LearningManager,
    service_discovery_module_fixture: ServiceDiscoveryModule,
    main_ai_hsp_connector: HSPConnector,
    mock_llm_fixture: MockLLMInterface,
    content_analyzer_module_fixture: ContentAnalyzerModule,
    trust_manager_fixture: TrustManager,
    personality_manager_fixture: PersonalityManager
):
    # All dependencies are now properly awaited by pytest-asyncio
    # No need for manual coroutine checking
    
    dm_config = {
        "operational_configs": configured_learning_manager.operational_config if configured_learning_manager else {}
    }
    
    # 使用真實的 ToolDispatcher 而不是 Mock
    tool_dispatcher = ToolDispatcher(llm_service=mock_llm_fixture)
    
    # Create mock objects for missing dependencies
    emotion_system = MagicMock()
    crisis_system = MagicMock()
    time_system = MagicMock()
    formula_engine = MagicMock()
    agent_manager = MagicMock()
    
    dm = DialogueManager(
        ai_id=TEST_AI_ID_MAIN,
        personality_manager=personality_manager_fixture,
        memory_manager=configured_learning_manager.ham_memory,
        llm_interface=mock_llm_fixture,
        emotion_system=emotion_system,
        crisis_system=crisis_system,
        time_system=time_system,
        formula_engine=formula_engine,
        tool_dispatcher=tool_dispatcher,
        learning_manager=configured_learning_manager,
        service_discovery_module=service_discovery_module_fixture,
        hsp_connector=main_ai_hsp_connector,
        agent_manager=agent_manager,
        config=dm_config
    )
    results_topic = f"hsp/results/{TEST_AI_ID_MAIN}/#"
    await main_ai_hsp_connector.subscribe(results_topic, lambda topic, payload: None)
    await asyncio.sleep(0.1)  # Allow subscription to be processed
    yield dm


# --- Test Classes ---
class TestHSPFactPublishing:
    received_facts_on_peer: List[Dict[str, Any]] = []

    async def _peer_fact_handler(self, fact_payload: HSPFactPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        print(f"DEBUG: _peer_fact_handler - Type of fact_payload: {type(fact_payload)}")
        print(f"DEBUG: _peer_fact_handler - Content of fact_payload: {fact_payload}")
        print(f"Peer A received fact: {fact_payload.id} from {sender_ai_id}")
        if sender_ai_id == TEST_AI_ID_MAIN:
            self.received_facts_on_peer.append({"payload": fact_payload, "envelope": envelope})

    @pytest.mark.asyncio
    async def test_learning_manager_publishes_fact_via_hsp(
        self,
        configured_learning_manager: LearningManager,
        peer_a_hsp_connector: HSPConnector
    ):
        self.received_facts_on_peer = [] # Reset for each test run

        peer_a_hsp_connector.register_on_fact_callback(self._peer_fact_handler)
        await asyncio.sleep(0.2)

        await configured_learning_manager.process_and_store_learnables(
            text="Berlin is the capital of Germany.",
            user_id="test_user_pub",
            session_id="test_session_pub",
            source_interaction_ref="test_interaction_pub_01"
        )

        await asyncio.sleep(0.5)
        print(f"Final received facts on peer A: {self.received_facts_on_peer}")
        assert len(self.received_facts_on_peer) > 0, "Peer A did not receive any facts."
        rp = self.received_facts_on_peer[0]["payload"]
        assert rp.get("source_ai_id") == TEST_AI_ID_MAIN
        assert rp.get("statement_structured", {}).get("subject") == "Berlin"


class TestHSPFactConsumption:
    @pytest.mark.asyncio
    async def test_main_ai_consumes_nl_fact_and_updates_kg_check_trust_influence(
        self,
        configured_learning_manager: LearningManager,
        content_analyzer_module_fixture: ContentAnalyzerModule,
        peer_a_hsp_connector: HSPConnector,
        peer_b_hsp_connector: HSPConnector,
        main_ai_hsp_connector: HSPConnector,
        trust_manager_fixture: TrustManager,
        ham_manager_fixture: MockHAM
    ):
        # ... (test body as previously defined) ...
        if not main_ai_hsp_connector.is_connected:
            pytest.fail("Main AI connector failed to subscribe")
        
        await asyncio.sleep(0.2)
        trust_manager_fixture.update_trust_score(TEST_AI_ID_PEER_A, new_absolute_score=0.9)
        content_analyzer_module_fixture.graph.clear()
        ham_manager_fixture.memory_store.clear()
        
        ca_mock = MagicMock(wraps=content_analyzer_module_fixture.process_hsp_fact_content)
        content_analyzer_module_fixture.process_hsp_fact_content = ca_mock
        
        # Test high trust peer fact
        fid_ht = f"pa_nl_ht_{uuid.uuid4().hex[:4]}"
        nl_ht = "Alpha stable."
        fact_ht = HSPFactPayload(
            id=fid_ht,
            statement_type="natural_language",
            statement_nl=nl_ht,
            source_ai_id=TEST_AI_ID_PEER_A,
            timestamp_created=datetime.now(timezone.utc).isoformat(),
            confidence_score=0.95,
            tags=["nl", "ht"]
        )  # type: ignore
        
        await peer_a_hsp_connector.publish_fact(fact_ht, FACT_TOPIC_GENERAL)
        await asyncio.sleep(1.5)
        
        assert len(ham_manager_fixture.memory_store) == 1
        meta_ht = ham_manager_fixture.memory_store[list(ham_manager_fixture.memory_store.keys())[0]]['metadata']
        # LearningManager uses: final_score = (effective_confidence * 0.7) + (novelty_score * 0.15) + (evidence_score * 0.15)
        # effective_confidence = original_confidence * trust_score = 0.95 * 0.9 = 0.855
        # novelty_score = 0.5 (default), evidence_score = 0.5 (default)
        # expected_final_score = (0.855 * 0.7) + (0.5 * 0.15) + (0.5 * 0.15) = 0.5985 + 0.075 + 0.075 = 0.7485
        expected_final_score = (0.95 * 0.9 * 0.7) + (0.5 * 0.15) + (0.5 * 0.15)
        assert abs(meta_ht['confidence'] - expected_final_score) < 0.001
        assert ca_mock.called

        # Test low trust peer fact
        trust_manager_fixture.update_trust_score(TEST_AI_ID_PEER_B, new_absolute_score=0.1)
        content_analyzer_module_fixture.graph.clear()
        ham_manager_fixture.memory_store.clear()
        ca_mock.reset_mock()
        
        fid_lt = f"pb_nl_lt_{uuid.uuid4().hex[:4]}"
        nl_lt = "Beta unstable."
        fact_lt = HSPFactPayload(
            id=fid_lt,
            statement_type="natural_language",
            statement_nl=nl_lt,
            source_ai_id=TEST_AI_ID_PEER_B,
            timestamp_created=datetime.now(timezone.utc).isoformat(),
            confidence_score=0.95,
            tags=["nl", "lt"]
        )  # type: ignore
        
        await peer_b_hsp_connector.publish_fact(fact_lt, FACT_TOPIC_GENERAL)
        await asyncio.sleep(1.5)
        
        assert len(ham_manager_fixture.memory_store) == 0
        # Note: ContentAnalyzer is called during novelty assessment even if fact is ultimately discarded
        assert ca_mock.called
        print("[Test Trust Influence on Fact Storage] Verified.")

    @pytest.mark.asyncio
    async def test_main_ai_consumes_structured_fact_updates_kg(
        self,
        configured_learning_manager: LearningManager,
        content_analyzer_module_fixture: ContentAnalyzerModule,
        peer_a_hsp_connector: HSPConnector,
        main_ai_hsp_connector: HSPConnector,
        trust_manager_fixture: TrustManager
    ):
        # ... (test body as previously defined) ...
        if not main_ai_hsp_connector.is_connected:
            pytest.fail("Main AI connector failed to subscribe")
        
        await asyncio.sleep(0.2)
        trust_manager_fixture.update_trust_score(TEST_AI_ID_PEER_A, new_absolute_score=0.9)
        content_analyzer_module_fixture.graph.clear()
        
        ca_mock = MagicMock(wraps=content_analyzer_module_fixture.process_hsp_fact_content)
        content_analyzer_module_fixture.process_hsp_fact_content = ca_mock
        
        fid = f"pa_sfact_{uuid.uuid4().hex[:4]}"
        s = "hsp:e:Device1"
        p = "hsp:p:temp"
        o = 23.5
        
        fact = HSPFactPayload(
            id=fid,
            statement_type="semantic_triple",
            statement_structured=HSPFactStatementStructured(
                subject_uri=s,
                predicate_uri=p,
                object_literal=o,
                object_datatype="xsd:float"
            ),
            source_ai_id=TEST_AI_ID_PEER_A,
            timestamp_created=datetime.now(timezone.utc).isoformat(),
            confidence_score=0.99,
            tags=["hsp_struct"]
        )  # type: ignore
        
        await peer_a_hsp_connector.publish_fact(fact, topic=FACT_TOPIC_GENERAL)
        await asyncio.sleep(1.5)
        
        assert ca_mock.called
        g = content_analyzer_module_fixture.graph
        r_type = p.split('/')[-1].split('#')[-1]
        
        assert g.has_node(s) and g.nodes[s].get('hsp_source_info', {}).get('origin_fact_id') == fid
        obj_node_id = next((n_id for n_id in g.nodes() if f"literal_{o}" in n_id), None)
        assert obj_node_id  # Updated literal node ID matching
        assert g.has_edge(s, obj_node_id) and g.edges[s, obj_node_id].get('type') == r_type
        print(f"[Test Consume Structured Fact] Verified by CA.")

    @pytest.mark.asyncio
    async def test_ca_semantic_mapping_for_hsp_structured_fact(
        self,
        configured_learning_manager: LearningManager,
        content_analyzer_module_fixture: ContentAnalyzerModule,
        peer_a_hsp_connector: HSPConnector,
        main_ai_hsp_connector: HSPConnector,
        trust_manager_fixture: TrustManager
    ):
        """Tests ContentAnalyzerModule's semantic mapping for structured HSP facts."""
        await main_ai_hsp_connector.subscribe("hsp.external.fact", lambda topic, payload: None)
        if not main_ai_hsp_connector.is_connected:
            pytest.fail("Main AI connector failed to subscribe to general fact topic for mapping test")
        
        await asyncio.sleep(0.2)
        trust_manager_fixture.update_trust_score(TEST_AI_ID_PEER_A, new_absolute_score=0.9)
        content_analyzer_module_fixture.graph.clear()

        # Spy on CA's processing method
        ca_process_mock = MagicMock(wraps=content_analyzer_module_fixture.process_hsp_fact_content)
        content_analyzer_module_fixture.process_hsp_fact_content = ca_process_mock

        # Define a fact using external URIs that are in CA's ontology_mapping
        ext_person_uri = "http://example.com/ontology#Person/peer_person_123"
        ext_name_pred_uri = "http://xmlns.com/foaf/0.1/name"  # Mapped to cai_prop:name
        person_name_literal = "Peer Test Person"

        fact_id_for_mapping = f"peer_A_map_fact_{uuid.uuid4().hex[:6]}"
        fact_to_publish_for_mapping = HSPFactPayload(
            id=fact_id_for_mapping,
            statement_type="semantic_triple",
            statement_structured=HSPFactStatementStructured(  # type: ignore
                subject_uri=ext_person_uri,
                predicate_uri=ext_name_pred_uri,
                object_literal=person_name_literal,
                object_datatype="xsd:string"
            ),
            source_ai_id=TEST_AI_ID_PEER_A,
            timestamp_created=datetime.now(timezone.utc).isoformat(),
            confidence_score=0.97,
            tags=["hsp_structured_map_test"]  # type: ignore
        )
        
        await peer_a_hsp_connector.publish_fact(fact_to_publish_for_mapping, topic=FACT_TOPIC_GENERAL)
        await asyncio.sleep(1.5)

        assert ca_process_mock.called, "ContentAnalyzerModule.process_hsp_fact_content was not called for mapping test"

        graph = content_analyzer_module_fixture.graph

        # Check for mapped subject node: original URI used as ID if not mapped, type should be mapped
        # CA's current mapping logic uses original URI as ID if not directly mapped to an instance URI.
        # The TYPE of the node should reflect the mapping.
        mapped_person_type = content_analyzer_module_fixture.ontology_mapping["http://example.com/ontology#Person"]  # "cai_type:Person"
        assert graph.has_node(ext_person_uri), f"Node for external URI '{ext_person_uri}' not found."
        assert graph.nodes[ext_person_uri].get("type") == "HSP_URI_Entity"
        assert graph.nodes[ext_person_uri].get("original_uri") == ext_person_uri
        assert graph.nodes[ext_person_uri].get("label") == "peer_person_123"  # Derived from URI fragment

        # Check for mapped predicate (edge type)
        mapped_name_predicate = content_analyzer_module_fixture.ontology_mapping[ext_name_pred_uri]  # "cai_prop:name"

        # Find the literal object node
        literal_node_id = None
        for node_id, node_data in graph.nodes(data=True):
            if node_data.get("label") == person_name_literal and node_data.get("type") == "xsd:string":
                literal_node_id = node_id
                break
        assert literal_node_id is not None, f"Literal node for '{person_name_literal}' not found."

        assert graph.has_edge(ext_person_uri, literal_node_id), \
            f"Edge for mapped predicate '{mapped_name_predicate}' not found."
        edge_data = graph.edges[ext_person_uri, literal_node_id]
        assert edge_data.get("type") == mapped_name_predicate
        assert edge_data.get("original_predicate_uri") == ext_name_pred_uri
        assert edge_data.get('hsp_source_info', {}).get('origin_fact_id') == fact_id_for_mapping

        print(f"[Test Semantic Mapping] Verified CA mapped external URIs for fact '{fact_id_for_mapping}'.")


class TestHSPTaskDelegation:
    @pytest.mark.asyncio
    async def _peer_a_task_handler(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope, peer_a_hsp_connector: HSPConnector, task_received_event: asyncio.Event):
        assert task_payload.get("capability_id_filter") == "advanced_weather_forecast"
        assert task_payload.get("parameters", {}).get("location") == "London"

        # Peer A processes the task and sends a result
        result_payload = HSPTaskResultPayload(
            result_id=f"result_{uuid.uuid4().hex}",
            request_id=task_payload.get("request_id", ""),
            executing_ai_id=peer_a_hsp_connector.ai_id,
            status="success",
            result_data={"forecast": "Sunny with a chance of rain for London."},
            timestamp_completed=datetime.now(timezone.utc).isoformat()
        ) # type: ignore

        await peer_a_hsp_connector.send_task_result(result_payload, sender_ai_id, envelope["correlation_id"])
        task_received_event.set()

    @pytest.mark.asyncio
    async def _peer_a_failing_handler(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope, peer_a_hsp_connector: HSPConnector, task_received_event: asyncio.Event, capability_id: str):
        assert task_payload.get("capability_id_filter") == capability_id
        
        # Peer A fails to process the task
        result_payload = HSPTaskResultPayload(
            result_id=f"result_{uuid.uuid4().hex}",
            request_id=task_payload.get("request_id", ""),
            executing_ai_id=peer_a_hsp_connector.ai_id,
            status="failure",
            error_details={"message": "Service unavailable due to maintenance."},
            timestamp_completed=datetime.now(timezone.utc).isoformat()
        )  # type: ignore
        
        await peer_a_hsp_connector.send_task_result(result_payload, sender_ai_id, envelope["correlation_id"])
        task_received_event.set()

    @pytest.mark.asyncio
    async def test_dm_delegates_task_to_specialist_ai_and_gets_result(
        self,
        dialogue_manager_fixture: DialogueManager,
        service_discovery_module_fixture: ServiceDiscoveryModule,
        peer_a_hsp_connector: HSPConnector,
        main_ai_hsp_connector: HSPConnector
    ):
        dm = dialogue_manager_fixture
        sdm = service_discovery_module_fixture
        
        # 1. Peer A advertises its capability
        cap_payload = HSPCapabilityAdvertisementPayload(
            capability_id="advanced_weather_forecast",
            name="advanced_weather_forecast",
            description="Provides detailed 7-day weather forecasts for any location.",
            ai_id=peer_a_hsp_connector.ai_id,
            input_schema_example={"type": "object", "properties": {"location": {"type": "string"}}},
            output_schema_example={"type": "object", "properties": {"forecast": {"type": "string"}}},
            version="1.0",
            availability_status="online",
            tags=["weather", "forecast"]
        )  # type: ignore
        
        await peer_a_hsp_connector.publish_capability_advertisement(cap_payload)
        await asyncio.sleep(0.2)
        
        # 2. Verify Main AI's SDM has registered the capability
        assert sdm.is_capability_available("advanced_weather_forecast")
        
        # 3. Main AI's DM receives a query that should trigger delegation
        query = "project: I need an advanced weather forecast for London."
        
        # Mock ToolDispatcher to return no local tool, forcing HSP delegation
        mock_td = MagicMock(spec=ToolDispatcher)
        mock_td.dispatch.return_value = ToolDispatcherResponse(
            status="unhandled_by_local_tool",
            payload=None,
            tool_name_attempted=None,
            original_query_for_tool=None,
            error_message="No local tool found for weather forecast."
        )
        dm.tool_dispatcher = mock_td
        
        # 4. Peer A needs to be ready to handle the task request
        task_received_event = asyncio.Event()
        
        peer_a_hsp_connector.register_on_task_request_callback(lambda tp, sai, env: self._peer_a_task_handler(tp, sai, env, peer_a_hsp_connector, task_received_event))
        
        # 5. Trigger the DM and wait for the result
        final_response = await dm.get_simple_response(query, "test_session_task", "test_user_task")
        
        await wait_for_event(task_received_event, timeout=5.0)
        
        # 6. Verify the final response incorporates the HSP task result
        assert "Sunny with a chance of rain" in final_response
        print("[Test Task Delegation] Verified DM delegated task and received result.")

    @pytest.mark.asyncio
    async def test_dm_handles_hsp_task_failure_and_falls_back(
        self,
        dialogue_manager_fixture: DialogueManager,
        service_discovery_module_fixture: ServiceDiscoveryModule,
        peer_a_hsp_connector: HSPConnector,
        main_ai_hsp_connector: HSPConnector,
        mock_llm_fixture: MockLLMInterface
    ):
        dm = dialogue_manager_fixture
        sdm = service_discovery_module_fixture
        
        # 1. Peer A advertises its capability (even though it will fail)
        capability_id = f"failing_service_{uuid.uuid4().hex}"  # Generate a unique capability ID
        cap_payload = HSPCapabilityAdvertisementPayload(
            capability_id=capability_id,
            name="failing_service",
            description="A service that always fails.",
            ai_id=peer_a_hsp_connector.ai_id,  # Make sure to set the AI ID
            input_schema_example={"type": "object", "properties": {"query": {"type": "string"}}},
            output_schema_example={"type": "object", "properties": {"result": {"type": "string"}}},
            version="1.0",
            availability_status="online",
            tags=["test", "failing"]
        )

        await peer_a_hsp_connector.publish_capability_advertisement(cap_payload)
        await asyncio.sleep(1.0)

        # 2. Verify Main AI's SDM has registered the capability
        # First, check if the capability was received by the main AI's SDM
        capabilities = sdm.find_capabilities(capability_id_filter=capability_id)
        if not capabilities:
            # If not found by ID, try by name
            capabilities = sdm.find_capabilities(capability_name_filter="failing_service")
        
        # Log the current state for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Known capabilities in SDM: {sdm.known_capabilities}")
        logger.info(f"Found capabilities: {capabilities}")
        
        assert len(capabilities) > 0, f"No capabilities found for 'failing_service'. Known capabilities: {sdm.known_capabilities}"
        
        # 3. Set up Peer A to fail the task
        task_received_event = asyncio.Event()
        
        peer_a_hsp_connector.register_on_task_request_callback(lambda tp, sai, env: self._peer_a_failing_handler(tp, sai, env, peer_a_hsp_connector, task_received_event, capability_id))
        
        # 4. Set up a fallback response from the LLM
        fallback_response = "I couldn't access the failing service, but here's a fallback response."
        mock_llm_fixture.add_mock_response("Please use the failing service.", fallback_response)
        
        # 5. Trigger the DM with a query that should use the failing service
        final_response = await dm.get_simple_response("project: Please use the failing service.", "test_session_fail", "test_user_fail")
        
        # 6. Verify the task was received and the fallback was used
        await wait_for_event(task_received_event, timeout=5.0)
        assert fallback_response in final_response
        print("[Test Task Failure] Verified DM handled task failure and used fallback response.")

        