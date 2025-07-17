import pytest
import asyncio
import uuid
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from typing import Dict, Any, Optional, List, Callable
import json

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
from src.services.llm_interface import LLMInterface, LLMInterfaceConfig
from src.core_ai.dialogue.dialogue_manager import DialogueManager
from src.tools.tool_dispatcher import ToolDispatcher
from src.core_ai.formula_engine import FormulaEngine
from src.shared.types.common_types import ToolDispatcherResponse
from src.core_ai.personality.personality_manager import PersonalityManager


from amqtt.broker import Broker

import logging

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
class MockLLMInterface(LLMInterface):
    def __init__(self, config: Optional[LLMInterfaceConfig] = None):
        base_config = config or LLMInterfaceConfig(
            default_provider="mock", 
            default_model="mock-model", 
            providers={}, 
            default_generation_params={}
        )
        super().__init__(config=base_config)
        self.mock_responses: Dict[str, str] = {}
        self.generate_response_history: List[Dict[str, Any]] = []

    def add_mock_response(self, prompt_contains: str, response: str):
        self.mock_responses[prompt_contains] = response

    def generate_response(self, prompt: str, model_name: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> str:
        self.generate_response_history.append({"prompt": prompt, "model_name": model_name, "params": params})
        for key, resp in self.mock_responses.items():
            if key in prompt:
                return resp
        if "completely_unhandled_query_for_llm" in prompt:
            return "I'm not sure how to help with that, but I can process this with LLM."
        if "hsp_task_failed_what_now" in prompt:
            return "It seems the specialist AI couldn't help with that. Let me try to answer directly using my own knowledge."
        return "[]"


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
    return FactExtractorModule(llm_interface=mock_llm_fixture)


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

@pytest.fixture
def broker():
    b = Broker()

    def run_broker():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(b.start())
        loop.run_forever()

    thread = threading.Thread(target=run_broker)
    thread.daemon = True
    thread.start()
    yield b
    b.shutdown()


@pytest.fixture
async def main_ai_hsp_connector(trust_manager_fixture: TrustManager, broker):
    connector = HSPConnector(
        TEST_AI_ID_MAIN,
        MQTT_BROKER_ADDRESS,
        MQTT_BROKER_PORT,
    )
    await connector.connect()
    yield connector
    await connector.disconnect()


@pytest.fixture
async def peer_a_hsp_connector(trust_manager_fixture: TrustManager, broker):
    connector = HSPConnector(
        TEST_AI_ID_PEER_A,
        MQTT_BROKER_ADDRESS,
        MQTT_BROKER_PORT,
    )
    await connector.connect()
    yield connector
    await connector.disconnect()


@pytest.fixture
async def peer_b_hsp_connector(trust_manager_fixture: TrustManager, broker):
    connector = HSPConnector(
        TEST_AI_ID_PEER_B,
        MQTT_BROKER_ADDRESS,
        MQTT_BROKER_PORT,
    )
    await connector.connect()
    yield connector
    await connector.disconnect()


@pytest.fixture
async def configured_learning_manager(
    ham_manager_fixture: MockHAM,
    fact_extractor_fixture: FactExtractorModule,
    content_analyzer_module_fixture: ContentAnalyzerModule,
    main_ai_hsp_connector: HSPConnector,
    trust_manager_fixture: TrustManager,
    personality_manager_fixture: PersonalityManager
):
    if asyncio.iscoroutine(main_ai_hsp_connector):
        main_ai_hsp_connector = await main_ai_hsp_connector
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
    return lm


@pytest.fixture
async def service_discovery_module_fixture(main_ai_hsp_connector: HSPConnector, trust_manager_fixture: TrustManager):
    if asyncio.iscoroutine(main_ai_hsp_connector):
        main_ai_hsp_connector = await main_ai_hsp_connector
    sdm = ServiceDiscoveryModule(trust_manager=trust_manager_fixture)
    main_ai_hsp_connector.register_on_capability_advertisement_callback(sdm.process_capability_advertisement)
    assert main_ai_hsp_connector.subscribe(f"{CAP_ADVERTISEMENT_TOPIC}/#"), \
        f"Main AI failed to subscribe to {CAP_ADVERTISEMENT_TOPIC}/#"
    await asyncio.sleep(0.2)
    return sdm


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
    if asyncio.iscoroutine(configured_learning_manager):
        configured_learning_manager = await configured_learning_manager
    if asyncio.iscoroutine(service_discovery_module_fixture):
        service_discovery_module_fixture = await service_discovery_module_fixture
    if asyncio.iscoroutine(main_ai_hsp_connector):
        main_ai_hsp_connector = await main_ai_hsp_connector
    
    dm_config = {
        "operational_configs": configured_learning_manager.operational_config if configured_learning_manager else {}
    }
    mock_td = MagicMock(spec=ToolDispatcher)
    dm = DialogueManager(
        ai_id=TEST_AI_ID_MAIN,
        personality_manager=personality_manager_fixture,
        memory_manager=configured_learning_manager.ham_memory,
        llm_interface=mock_llm_fixture,
        service_discovery_module=service_discovery_module_fixture,
        hsp_connector=main_ai_hsp_connector,
        content_analyzer=content_analyzer_module_fixture,
        learning_manager=configured_learning_manager,
        config=dm_config
    )
    results_topic = f"hsp/results/{TEST_AI_ID_MAIN}/#"
    assert main_ai_hsp_connector.subscribe(results_topic), f"Main AI failed to sub to {results_topic}"
    await asyncio.sleep(0.1)  # Allow subscription to be processed
    return dm


# --- Test Classes ---
@pytest.mark.skip(reason="Skipping HSP integration tests due to MQTT broker dependency")
class TestHSPFactPublishing:
    @pytest.mark.asyncio
    async def test_learning_manager_publishes_fact_via_hsp(
        self,
        configured_learning_manager: LearningManager,
        peer_a_hsp_connector: HSPConnector
    ):
        # ... (test body as previously defined) ...
        received_facts_on_peer: List[Dict[str, Any]] = []
        
        def peer_fact_handler(fact_payload: HSPFactPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
            if sender_ai_id == TEST_AI_ID_MAIN:
                received_facts_on_peer.append({"payload": fact_payload, "envelope": envelope})
                
        peer_a_hsp_connector.register_on_fact_callback(peer_fact_handler)
        assert peer_a_hsp_connector.subscribe(FACT_TOPIC_GENERAL)
        time.sleep(0.2)
        
        await configured_learning_manager.process_and_store_learnables(
            text="Berlin is the capital of Germany.",
            user_id="test_user_pub",
            session_id="test_session_pub",
            source_interaction_ref="test_interaction_pub_01"
        )
        
        time.sleep(1.0)
        assert len(received_facts_on_peer) > 0
        rp = received_facts_on_peer[0]["payload"]
        assert rp.get("source_ai_id") == TEST_AI_ID_MAIN
        assert rp.get("statement_structured", {}).get("subject") == "Berlin"


@pytest.mark.skip(reason="Skipping HSP integration tests due to MQTT broker dependency")
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
        if not main_ai_hsp_connector.subscribe(FACT_TOPIC_GENERAL):
            pytest.fail("Main AI connector failed to subscribe")
        
        time.sleep(0.2)
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
        
        peer_a_hsp_connector.publish_fact(fact_ht, FACT_TOPIC_GENERAL)
        await asyncio.sleep(1.5)
        
        assert len(ham_manager_fixture.memory_store) == 1
        meta_ht = ham_manager_fixture.memory_store[list(ham_manager_fixture.memory_store.keys())[0]]['metadata']
        assert abs(meta_ht['confidence'] - (0.95 * 0.9)) < 0.001
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
        
        peer_b_hsp_connector.publish_fact(fact_lt, FACT_TOPIC_GENERAL)
        await asyncio.sleep(1.5)
        
        assert len(ham_manager_fixture.memory_store) == 0
        assert not ca_mock.called
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
        if not main_ai_hsp_connector.subscribe(FACT_TOPIC_GENERAL):
            pytest.fail("Main AI failed to subscribe")
        
        time.sleep(0.2)
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
        
        peer_a_hsp_connector.publish_fact(fact, topic=FACT_TOPIC_GENERAL)
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
        if not main_ai_hsp_connector.subscribe(FACT_TOPIC_GENERAL):
            pytest.fail("Main AI connector failed to subscribe to general fact topic for mapping test")
        
        time.sleep(0.2)
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
        
        peer_a_hsp_connector.publish_fact(fact_to_publish_for_mapping, topic=FACT_TOPIC_GENERAL)
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
