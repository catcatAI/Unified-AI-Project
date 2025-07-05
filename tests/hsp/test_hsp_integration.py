import pytest
import asyncio
import uuid
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from typing import Dict, Any, Optional, List, Callable

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.hsp.connector import HSPConnector
from src.hsp.types import HSPFactPayload, HSPMessageEnvelope, HSPCapabilityAdvertisementPayload, \
    HSPTaskRequestPayload, HSPTaskResultPayload, HSPErrorDetails, HSPFactStatementStructured
from src.core_ai.learning.learning_manager import LearningManager
from src.core_ai.learning.fact_extractor_module import FactExtractorModule
from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule
from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
from src.core_ai.trust_manager.trust_manager_module import TrustManager
from src.core_ai.memory.ham_memory_manager import HAMMemoryManager
from src.services.llm_interface import LLMInterface, LLMInterfaceConfig
from src.core_ai.dialogue.dialogue_manager import DialogueManager
from src.tools.tool_dispatcher import ToolDispatcher
from src.core_ai.formula_engine import FormulaEngine
from src.shared.types.common_types import ToolDispatcherResponse


# --- Constants for Testing ---
TEST_AI_ID_MAIN = "did:hsp:test_ai_main_001"
TEST_AI_ID_PEER_A = "did:hsp:test_ai_peer_A_002"
TEST_AI_ID_PEER_B = "did:hsp:test_ai_peer_B_003"

MQTT_BROKER_ADDRESS = "localhost"
MQTT_BROKER_PORT = 1883

FACT_TOPIC_GENERAL = "hsp/knowledge/facts/test_general"
CAP_ADVERTISEMENT_TOPIC = "hsp/capabilities/advertisements/general"

# --- Mock Classes ---
class MockLLMInterface(LLMInterface):
    def __init__(self, config: Optional[LLMInterfaceConfig] = None):
        base_config = config or LLMInterfaceConfig(default_provider="mock", default_model="mock-model", providers={}, default_generation_params={})
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
                self.memory_store[old_ham_id_to_supersede]['metadata']['is_superseded_by'] = mem_id # type: ignore
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
            if meta.get('is_superseded_by'): continue
            match = True
            if data_type_filter and not entry.get("data_type", "").startswith(data_type_filter): match = False
            if metadata_filters and match:
                for key, value in metadata_filters.items():
                    if meta.get(key) != value: match = False; break
            if match: results.append({"id": mem_id, "metadata": meta, "raw_data": entry.get("raw_data"), "rehydrated_gist": {"summary": str(entry.get("raw_data"))}})
            if len(results) >= limit: break
        return results

# --- Pytest Fixtures ---
@pytest.fixture(scope="module")
def event_loop(): loop = asyncio.new_event_loop(); yield loop; loop.close()

@pytest.fixture
def mock_llm_fixture():
    llm = MockLLMInterface()
    llm.add_mock_response( "Berlin is the capital of Germany", '[{"fact_type": "general_statement", "content": {"subject": "Berlin", "relation": "is_capital_of", "object": "Germany"}, "confidence": 0.99}]')
    llm.add_mock_response("unsatisfactory_response_for_hsp_query_trigger", "I don't know about that topic.")
    return llm

@pytest.fixture
def fact_extractor_fixture(mock_llm_fixture: MockLLMInterface): return FactExtractorModule(llm_interface=mock_llm_fixture)
@pytest.fixture
def ham_manager_fixture(): return MockHAM()
@pytest.fixture(scope="module") # Make CA module-scoped if its init is slow (spaCy load)
def content_analyzer_module_fixture():
    try:
        analyzer = ContentAnalyzerModule()
        # For tests that modify the graph, ensure it's cleaned or use a function-scoped fixture if preferred
        # For this test structure, we'll clear graph within tests that modify it.
        return analyzer
    except Exception as e: pytest.skip(f"Skipping ContentAnalyzer tests: {e}")
@pytest.fixture
def trust_manager_fixture() -> TrustManager: return TrustManager()

@pytest.fixture
def main_ai_hsp_connector(trust_manager_fixture: TrustManager):
    conn_id_suffix = f"main_test_hsp_{uuid.uuid4().hex[:4]}"
    connector = HSPConnector(TEST_AI_ID_MAIN, MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, client_id_suffix=conn_id_suffix)
    if not connector.connect(): pytest.fail(f"Failed to connect main_ai_hsp_connector ({conn_id_suffix}).")
    time.sleep(0.5); yield connector; connector.disconnect(); time.sleep(0.1)

@pytest.fixture
def peer_a_hsp_connector(trust_manager_fixture: TrustManager):
    conn_id_suffix = f"peer_A_hsp_{uuid.uuid4().hex[:4]}"
    connector = HSPConnector(TEST_AI_ID_PEER_A, MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, client_id_suffix=conn_id_suffix)
    if not connector.connect(): pytest.fail(f"Failed to connect peer_a_hsp_connector ({conn_id_suffix}).")
    time.sleep(0.5); yield connector; connector.disconnect(); time.sleep(0.1)

@pytest.fixture
def peer_b_hsp_connector(trust_manager_fixture: TrustManager):
    conn_id_suffix = f"peer_B_hsp_{uuid.uuid4().hex[:4]}"
    connector = HSPConnector(TEST_AI_ID_PEER_B, MQTT_BROKER_ADDRESS, MQTT_BROKER_PORT, client_id_suffix=conn_id_suffix)
    if not connector.connect(): pytest.fail(f"Failed to connect peer_b_hsp_connector ({conn_id_suffix}).")
    time.sleep(0.5); yield connector; connector.disconnect(); time.sleep(0.1)

@pytest.fixture
def configured_learning_manager( ham_manager_fixture: MockHAM, fact_extractor_fixture: FactExtractorModule,
    content_analyzer_module_fixture: ContentAnalyzerModule, main_ai_hsp_connector: HSPConnector, trust_manager_fixture: TrustManager ):
    config = { "learning_thresholds": {"min_fact_confidence_to_store":0.7,"min_fact_confidence_to_share_via_hsp":0.8,"min_hsp_fact_confidence_to_store":0.55,"hsp_fact_conflict_confidence_delta":0.1}, "default_hsp_fact_topic":FACT_TOPIC_GENERAL}
    lm = LearningManager( TEST_AI_ID_MAIN, ham_manager_fixture, fact_extractor_fixture, content_analyzer_module_fixture, main_ai_hsp_connector, trust_manager_fixture, config )
    if main_ai_hsp_connector: main_ai_hsp_connector.register_on_fact_callback(lm.process_and_store_hsp_fact)
    return lm

@pytest.fixture
def service_discovery_module_fixture(main_ai_hsp_connector: HSPConnector, trust_manager_fixture: TrustManager):
    sdm = ServiceDiscoveryModule(trust_manager=trust_manager_fixture)
    main_ai_hsp_connector.register_on_capability_advertisement_callback(sdm.process_capability_advertisement)
    assert main_ai_hsp_connector.subscribe(f"{CAP_ADVERTISEMENT_TOPIC}/#"), f"Main AI failed to subscribe to {CAP_ADVERTISEMENT_TOPIC}/#"
    time.sleep(0.2); return sdm

@pytest.fixture
def dialogue_manager_fixture( configured_learning_manager: LearningManager, service_discovery_module_fixture: ServiceDiscoveryModule,
    main_ai_hsp_connector: HSPConnector, mock_llm_fixture: MockLLMInterface,
    content_analyzer_module_fixture: ContentAnalyzerModule, trust_manager_fixture: TrustManager ):
    dm_config = { "operational_configs": configured_learning_manager.operational_config if configured_learning_manager else {} }
    # Ensure DM gets the same instances of components as other fixtures if they are meant to be shared state for a test
    # For ToolDispatcher, DM's __init__ creates one if not provided. For tests needing to mock it, it's passed here.
    mock_td = MagicMock(spec=ToolDispatcher)

    dm = DialogueManager( ai_id=TEST_AI_ID_MAIN,
        personality_manager=configured_learning_manager.personality_manager,
        memory_manager=configured_learning_manager.memory_manager,
        llm_interface=mock_llm_fixture, # Use the test-specific mock LLM
        service_discovery_module=service_discovery_module_fixture,
        hsp_connector=main_ai_hsp_connector,
        trust_manager=trust_manager_fixture,
        content_analyzer=content_analyzer_module_fixture,
        emotion_system=configured_learning_manager.emotion_system,
        crisis_system=configured_learning_manager.crisis_system,
        time_system=configured_learning_manager.time_system,
        formula_engine=configured_learning_manager.formula_engine,
        tool_dispatcher=mock_td, # Pass the mock ToolDispatcher
        self_critique_module=configured_learning_manager.self_critique_module,
        learning_manager=configured_learning_manager,
        sandbox_executor=None,
        config=dm_config )
    results_topic = f"hsp/results/{TEST_AI_ID_MAIN}/#"; assert main_ai_hsp_connector.subscribe(results_topic), f"Main AI failed to sub to {results_topic}"
    time.sleep(0.2); return dm

# --- Test Classes ---
class TestHSPFactPublishing:
    def test_learning_manager_publishes_fact_via_hsp( self, configured_learning_manager: LearningManager, peer_a_hsp_connector: HSPConnector ):
        # ... (test body as previously defined) ...
        received_facts_on_peer: List[Dict[str,Any]] = []
        def peer_fact_handler(fact_payload: HSPFactPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
            if sender_ai_id == TEST_AI_ID_MAIN: received_facts_on_peer.append({"payload": fact_payload, "envelope": envelope})
        peer_a_hsp_connector.register_on_fact_callback(peer_fact_handler)
        assert peer_a_hsp_connector.subscribe(FACT_TOPIC_GENERAL); time.sleep(0.2)
        configured_learning_manager.process_and_store_learnables(text="Berlin is the capital of Germany.", user_id="test_user_pub", session_id="test_session_pub", source_interaction_ref="test_interaction_pub_01")
        time.sleep(1.0); assert len(received_facts_on_peer) > 0
        rp = received_facts_on_peer[0]["payload"]; assert rp.get("source_ai_id") == TEST_AI_ID_MAIN; assert rp.get("statement_structured", {}).get("subject") == "Berlin"

class TestHSPFactConsumption:
    @pytest.mark.asyncio
    async def test_main_ai_consumes_nl_fact_and_updates_kg_check_trust_influence(
        self, configured_learning_manager: LearningManager, content_analyzer_module_fixture: ContentAnalyzerModule,
        peer_a_hsp_connector: HSPConnector, peer_b_hsp_connector: HSPConnector,
        main_ai_hsp_connector: HSPConnector, trust_manager_fixture: TrustManager, ham_manager_fixture: MockHAM ):
        # ... (test body as previously defined) ...
        if not main_ai_hsp_connector.subscribe(FACT_TOPIC_GENERAL): pytest.fail("Main AI connector failed to subscribe")
        time.sleep(0.2); trust_manager_fixture.update_trust_score(TEST_AI_ID_PEER_A, new_absolute_score=0.9)
        content_analyzer_module_fixture.graph.clear(); ham_manager_fixture.memory_store.clear()
        lm_mock = MagicMock(wraps=configured_learning_manager.process_and_store_hsp_fact); configured_learning_manager.process_and_store_hsp_fact = lm_mock
        ca_mock = MagicMock(wraps=content_analyzer_module_fixture.process_hsp_fact_content); content_analyzer_module_fixture.process_hsp_fact_content = ca_mock
        fid_ht = f"pa_nl_ht_{uuid.uuid4().hex[:4]}"; nl_ht = "Alpha stable."; fact_ht = HSPFactPayload(id=fid_ht,statement_type="natural_language",statement_nl=nl_ht,source_ai_id=TEST_AI_ID_PEER_A,timestamp_created=datetime.now(timezone.utc).isoformat(),confidence_score=0.95,tags=["nl","ht"]); peer_a_hsp_connector.publish_fact(fact_ht,FACT_TOPIC_GENERAL); await asyncio.sleep(1.5) #type: ignore
        assert lm_mock.called; assert len(ham_manager_fixture.memory_store)==1
        meta_ht = ham_manager_fixture.memory_store[list(ham_manager_fixture.memory_store.keys())[0]]['metadata']
        assert abs(meta_ht['confidence'] - (0.95*0.9)) < 0.001; assert ca_mock.called

        trust_manager_fixture.update_trust_score(TEST_AI_ID_PEER_B, new_absolute_score=0.1)
        content_analyzer_module_fixture.graph.clear(); ham_manager_fixture.memory_store.clear(); lm_mock.reset_mock(); ca_mock.reset_mock()
        fid_lt = f"pb_nl_lt_{uuid.uuid4().hex[:4]}"; nl_lt = "Beta unstable."; fact_lt = HSPFactPayload(id=fid_lt,statement_type="natural_language",statement_nl=nl_lt,source_ai_id=TEST_AI_ID_PEER_B,timestamp_created=datetime.now(timezone.utc).isoformat(),confidence_score=0.95,tags=["nl","lt"]); peer_b_hsp_connector.publish_fact(fact_lt,FACT_TOPIC_GENERAL); await asyncio.sleep(1.5) #type: ignore
        assert lm_mock.called; assert len(ham_manager_fixture.memory_store)==0; assert not ca_mock.called
        print("[Test Trust Influence on Fact Storage] Verified.")

    @pytest.mark.asyncio
    async def test_main_ai_consumes_structured_fact_updates_kg(
        self, configured_learning_manager: LearningManager, content_analyzer_module_fixture: ContentAnalyzerModule,
        peer_a_hsp_connector: HSPConnector, main_ai_hsp_connector: HSPConnector, trust_manager_fixture: TrustManager ):
        # ... (test body as previously defined) ...
        if not main_ai_hsp_connector.subscribe(FACT_TOPIC_GENERAL): pytest.fail("Main AI failed to subscribe")
        time.sleep(0.2); trust_manager_fixture.update_trust_score(TEST_AI_ID_PEER_A, new_absolute_score=0.9)
        content_analyzer_module_fixture.graph.clear()
        lm_mock = MagicMock(wraps=configured_learning_manager.process_and_store_hsp_fact); configured_learning_manager.process_and_store_hsp_fact = lm_mock
        ca_mock = MagicMock(wraps=content_analyzer_module_fixture.process_hsp_fact_content); content_analyzer_module_fixture.process_hsp_fact_content = ca_mock
        fid = f"pa_sfact_{uuid.uuid4().hex[:4]}"; s="hsp:e:Device1"; p="hsp:p:temp"; o=23.5
        fact = HSPFactPayload(id=fid,statement_type="semantic_triple",statement_structured=HSPFactStatementStructured(subject_uri=s,predicate_uri=p,object_literal=o,object_datatype="xsd:float"),source_ai_id=TEST_AI_ID_PEER_A,timestamp_created=datetime.now(timezone.utc).isoformat(),confidence_score=0.99,tags=["hsp_struct"]) #type: ignore
        peer_a_hsp_connector.publish_fact(fact, topic=FACT_TOPIC_GENERAL); await asyncio.sleep(1.5)
        assert lm_mock.called; assert ca_mock.called
        g=content_analyzer_module_fixture.graph; r_type=p.split('/')[-1].split('#')[-1]
        assert g.has_node(s) and g.nodes[s].get('hsp_source_info',{}).get('origin_fact_id')==fid
        obj_node_id = next((n_id for n_id in g.nodes() if f"literal_{o}" in n_id), None); assert obj_node_id # Updated literal node ID matching
        assert g.has_edge(s,obj_node_id) and g.edges[s,obj_node_id].get('type')==r_type
        print(f"[Test Consume Structured Fact] Verified by CA.")

    @pytest.mark.asyncio
    async def test_ca_semantic_mapping_for_hsp_structured_fact(
        self, configured_learning_manager: LearningManager,
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
        ext_name_pred_uri = "http://xmlns.com/foaf/0.1/name" # Mapped to cai_prop:name
        person_name_literal = "Peer Test Person"

        fact_id_for_mapping = f"peer_A_map_fact_{uuid.uuid4().hex[:6]}"
        fact_to_publish_for_mapping = HSPFactPayload(
            id=fact_id_for_mapping,
            statement_type="semantic_triple",
            statement_structured=HSPFactStatementStructured( #type: ignore
                subject_uri=ext_person_uri,
                predicate_uri=ext_name_pred_uri,
                object_literal=person_name_literal,
                object_datatype="xsd:string"
            ),
            source_ai_id=TEST_AI_ID_PEER_A,
            timestamp_created=datetime.now(timezone.utc).isoformat(),
            confidence_score=0.97,
            tags=["hsp_structured_map_test"] #type: ignore
        )
        peer_a_hsp_connector.publish_fact(fact_to_publish_for_mapping, topic=FACT_TOPIC_GENERAL)
        await asyncio.sleep(1.5)

        assert ca_process_mock.called, "ContentAnalyzerModule.process_hsp_fact_content was not called for mapping test"

        graph = content_analyzer_module_fixture.graph

        # Check for mapped subject node: original URI used as ID if not mapped, type should be mapped
        # CA's current mapping logic uses original URI as ID if not directly mapped to an instance URI.
        # The TYPE of the node should reflect the mapping.
        mapped_person_type = content_analyzer_module_fixture.ontology_mapping["http://example.com/ontology#Person"] # "cai_type:Person"
        assert graph.has_node(ext_person_uri), f"Node for external URI '{ext_person_uri}' not found."
        assert graph.nodes[ext_person_uri].get("type") == mapped_person_type
        assert graph.nodes[ext_person_uri].get("original_uri") == ext_person_uri
        assert graph.nodes[ext_person_uri].get("label") == "peer_person_123" # Derived from URI fragment

        # Check for mapped predicate (edge type)
        mapped_name_predicate = content_analyzer_module_fixture.ontology_mapping[ext_name_pred_uri] # "cai_prop:name"

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


class TestHSPTaskBrokering: # ... (all existing tests in this class remain the same) ...
    @pytest.mark.asyncio
    async def test_e2e_task_brokering_flow_with_trust(
        self, dialogue_manager_fixture: DialogueManager, service_discovery_module_fixture: ServiceDiscoveryModule,
        main_ai_hsp_connector: HSPConnector, peer_a_hsp_connector: HSPConnector, trust_manager_fixture: TrustManager ):
        peer_ai_id = TEST_AI_ID_PEER_A ; cap_id = f"{peer_ai_id}_simple_math_v1.0"
        trust_manager_fixture.update_trust_score(peer_ai_id, new_absolute_score=0.7)
        reqs: List[Any] = []; received_results_in_dm: List[Any] = []
        def peer_handler(p,s,e): reqs.append(p); params=p['parameters']; op1=params.get('operand1'); op2=params.get('operand2'); stat,res,err = ("success",op1+op2,None) if isinstance(op1,(int,float)) and isinstance(op2,(int,float)) else ("failure",None,{"error_code":"INVALID","error_message":"Bad ops"}); rp=HSPTaskResultPayload(result_id="r1",request_id=p['request_id'],executing_ai_id=peer_ai_id,status=stat,payload={"result":res} if stat=="success" else None,error_details=err,timestamp_completed=datetime.now(timezone.utc).isoformat()); peer_a_hsp_connector.send_task_result(rp,p['callback_address'],e['correlation_id']) #type: ignore
        peer_a_hsp_connector.register_on_task_request_callback(peer_handler); assert peer_a_hsp_connector.subscribe(f"hsp/requests/{peer_ai_id}/#")
        adv=HSPCapabilityAdvertisementPayload(capability_id=cap_id,ai_id=peer_ai_id,name="Simple Mock Math",description="Adds",version="1.0",availability_status="online",tags=["math"]); assert peer_a_hsp_connector.publish_capability_advertisement(adv,CAP_ADVERTISEMENT_TOPIC); await asyncio.sleep(0.5) #type: ignore
        assert len(service_discovery_module_fixture.find_capabilities(capability_id_filter=cap_id,min_trust_score=0.5))==1

        orig_dm_handler = dialogue_manager_fixture._handle_incoming_hsp_task_result
        dialogue_manager_fixture._handle_incoming_hsp_task_result=MagicMock(wraps=lambda p,s,e:(received_results_in_dm.append(p), orig_dm_handler(p,s,e))) #type: ignore

        await dialogue_manager_fixture.get_simple_response(f"hsp_task:{cap_id} with params {{\"operand1\":20,\"operand2\":5}}", "u1","s1"); await asyncio.sleep(1.5)
        assert len(reqs)>0 and dialogue_manager_fixture._handle_incoming_hsp_task_result.called and len(received_results_in_dm)>0
        assert received_results_in_dm[0]['status']=='success' and received_results_in_dm[0]['payload']['result']==25
        assert abs(trust_manager_fixture.get_trust_score(peer_ai_id)-(0.7+0.05)) < 0.001

        received_results_in_dm.clear(); reqs.clear()
        await dialogue_manager_fixture.get_simple_response(f"hsp_task:{cap_id} with params {{\"operand1\":\"bad\",\"operand2\":5}}", "u1","s1"); await asyncio.sleep(1.5)
        assert len(reqs)>0 and dialogue_manager_fixture._handle_incoming_hsp_task_result.call_count > 1 and len(received_results_in_dm)>0
        assert received_results_in_dm[0]['status']=='failure'
        assert abs(trust_manager_fixture.get_trust_score(peer_ai_id)-(0.7+0.05-0.1)) < 0.001
        dialogue_manager_fixture._handle_incoming_hsp_task_result = orig_dm_handler

    @pytest.mark.asyncio
    async def test_dm_fallback_to_hsp_on_local_tool_unhandled(
        self, dialogue_manager_fixture: DialogueManager, service_discovery_module_fixture: ServiceDiscoveryModule,
        peer_a_hsp_connector: HSPConnector, mock_llm_fixture: MockLLMInterface, main_ai_hsp_connector: HSPConnector ):
        peer_id=TEST_AI_ID_PEER_A; cap_id=f"{peer_id}_special_hsp_op_v1"; search_term="special_fallback_op"
        reqs:List[Any]=[]; def handler(p,s,e): reqs.append(p); r_p=HSPTaskResultPayload(result_id="r_fb",request_id=p['request_id'],executing_ai_id=peer_id,status="success",payload={"data":"fallback_done"},timestamp_completed=datetime.now(timezone.utc).isoformat()); peer_a_hsp_connector.send_task_result(r_p,p['callback_address'],e['correlation_id']) #type: ignore
        peer_a_hsp_connector.register_on_task_request_callback(handler); peer_a_hsp_connector.subscribe(f"hsp/requests/{peer_id}/#")
        adv=HSPCapabilityAdvertisementPayload(capability_id=cap_id,ai_id=peer_id,name="FallbackOp",description="Handles fallback.",version="1.0",availability_status="online",tags=[search_term]); assert peer_a_hsp_connector.publish_capability_advertisement(adv,CAP_ADVERTISEMENT_TOPIC); await asyncio.sleep(0.5) #type: ignore
        assert len(service_discovery_module_fixture.find_capabilities(capability_id_filter=cap_id))==1
        mock_td=dialogue_manager_fixture.tool_dispatcher; assert isinstance(mock_td,MagicMock)
        mock_td.dispatch.return_value=ToolDispatcherResponse(status="unhandled_by_local_tool",tool_name_attempted=search_term,payload=None, error_message="Local unhandled") #type: ignore
        dialogue_manager_fixture._dispatch_hsp_task_request=MagicMock(wraps=dialogue_manager_fixture._dispatch_hsp_task_request)
        res_h:List[Any]=[]; orig_h=dialogue_manager_fixture._handle_incoming_hsp_task_result; dialogue_manager_fixture._handle_incoming_hsp_task_result=MagicMock(wraps=lambda p,s,e:res_h.append(p)) #type: ignore
        mock_llm_fixture.generate_response_history.clear()
        mock_fe=MagicMock(spec=FormulaEngine); formula={"name":"f_fallback","action":"dispatch_tool","parameters":{"tool_name":search_term,"tool_query":"q_fallback","other_data":"context"}}; mock_fe.match_input.return_value=formula; mock_fe.execute_formula.return_value={"action_name":"dispatch_tool","action_params":formula["parameters"]}; dialogue_manager_fixture.formula_engine=mock_fe #type: ignore
        await dialogue_manager_fixture.get_simple_response("trigger_fallback_formula","u_fb","s_fb"); await asyncio.sleep(1.5)
        mock_td.dispatch.assert_called_once(); dialogue_manager_fixture._dispatch_hsp_task_request.assert_called_once()
        dispatch_hsp_args = dialogue_manager_fixture._dispatch_hsp_task_request.call_args[0]
        dispatched_cap_adv: HSPCapabilityAdvertisementPayload = dispatch_hsp_args[0] #type: ignore
        dispatched_req_params: Dict[str,Any] = dispatch_hsp_args[1]
        assert dispatched_cap_adv["capability_id"] == cap_id
        assert dispatched_req_params.get("query") == "q_fallback"
        assert dispatched_req_params.get("other_data") == "context"
        assert dialogue_manager_fixture._handle_incoming_hsp_task_result.called and len(res_h)>0 and res_h[0]['status']=='success'
        assert not mock_llm_fixture.generate_response_history; dialogue_manager_fixture._handle_incoming_hsp_task_result=orig_h; dialogue_manager_fixture.formula_engine=FormulaEngine()

    @pytest.mark.asyncio
    async def test_dm_local_tool_success_no_hsp_fallback( self, dialogue_manager_fixture: DialogueManager, mock_llm_fixture: MockLLMInterface ):
        mock_td=dialogue_manager_fixture.tool_dispatcher; assert isinstance(mock_td,MagicMock); tool_n,tool_q,res_p="local_echo","echo_local","Echoed:echo_local"
        mock_td.dispatch.return_value=ToolDispatcherResponse(status="success",payload=res_p,tool_name_attempted=tool_n,original_query_for_tool=tool_q) #type: ignore
        mock_fe=MagicMock(spec=FormulaEngine); formula={"name":"f_local","action":"dispatch_tool","parameters":{"tool_name":tool_n,"tool_query":tool_q}}; mock_fe.match_input.return_value=formula; mock_fe.execute_formula.return_value={"action_name":"dispatch_tool","action_params":formula["parameters"]}; dialogue_manager_fixture.formula_engine=mock_fe #type: ignore
        dialogue_manager_fixture._dispatch_hsp_task_request=MagicMock(wraps=dialogue_manager_fixture._dispatch_hsp_task_request); mock_llm_fixture.generate_response_history.clear()
        resp = await dialogue_manager_fixture.get_simple_response("trigger_local_echo","u_ls","s_ls")
        ai_name = dialogue_manager_fixture.personality_manager.get_current_personality_trait("display_name", dialogue_manager_fixture.ai_id)
        assert f"{ai_name}: {res_p}" in resp
        mock_td.dispatch.assert_called_once(); dialogue_manager_fixture._dispatch_hsp_task_request.assert_not_called(); assert not mock_llm_fixture.generate_response_history
        dialogue_manager_fixture.formula_engine=FormulaEngine()

    @pytest.mark.asyncio
    async def test_dm_no_local_no_hsp_fallback_to_llm( self, dialogue_manager_fixture: DialogueManager, service_discovery_module_fixture: ServiceDiscoveryModule, mock_llm_fixture: MockLLMInterface ):
        service_discovery_module_fixture.find_capabilities=MagicMock(return_value=[]); mock_fe=MagicMock(spec=FormulaEngine); mock_fe.match_input.return_value=None; dialogue_manager_fixture.formula_engine=mock_fe
        mock_td=dialogue_manager_fixture.tool_dispatcher; assert isinstance(mock_td,MagicMock); mock_td.dispatch.return_value=ToolDispatcherResponse(status="unhandled_by_local_tool",payload=None) #type: ignore
        dialogue_manager_fixture._dispatch_hsp_task_request=MagicMock(wraps=dialogue_manager_fixture._dispatch_hsp_task_request); mock_llm_fixture.generate_response_history.clear()
        llm_resp="I'm not sure how to help with that, but I can process this with LLM."; user_q="completely_unhandled_query_for_llm"
        resp = await dialogue_manager_fixture.get_simple_response(user_q,"u_llm_fb","s_llm_fb")
        ai_name = dialogue_manager_fixture.personality_manager.get_current_personality_trait("display_name", dialogue_manager_fixture.ai_id)
        assert f"{ai_name}: {llm_resp}" in resp
        mock_fe.match_input.assert_called_once(); dialogue_manager_fixture._dispatch_hsp_task_request.assert_called_once(); service_discovery_module_fixture.find_capabilities.assert_called()
        assert len(mock_llm_fixture.generate_response_history)>0; assert mock_llm_fixture.generate_response_history[0]["prompt"].strip().endswith(user_q)
        dialogue_manager_fixture.formula_engine=FormulaEngine()

    @pytest.mark.asyncio
    async def test_dm_hsp_fallback_hsp_task_fails(
        self, dialogue_manager_fixture: DialogueManager, service_discovery_module_fixture: ServiceDiscoveryModule,
        peer_a_hsp_connector: HSPConnector, mock_llm_fixture: MockLLMInterface, main_ai_hsp_connector: HSPConnector ):
        peer_id=TEST_AI_ID_PEER_A; cap_id=f"{peer_id}_failing_op_v1"; search_term="failing_hsp_op"
        def handler(p,s,e): err_d=HSPErrorDetails(error_code="FAIL",error_message="failed_peer"); rp=HSPTaskResultPayload(result_id="r_f",request_id=p['request_id'],executing_ai_id=peer_id,status="failure",error_details=err_d,timestamp_completed=datetime.now(timezone.utc).isoformat()); peer_a_hsp_connector.send_task_result(rp,p['callback_address'],e['correlation_id']) #type: ignore
        peer_a_hsp_connector.register_on_task_request_callback(handler); peer_a_hsp_connector.subscribe(f"hsp/requests/{peer_id}/#")
        adv=HSPCapabilityAdvertisementPayload(capability_id=cap_id,ai_id=peer_id,name="FailingOp",description="fails",version="1.0",availability_status="online",tags=[search_term]); assert peer_a_hsp_connector.publish_capability_advertisement(adv,CAP_ADVERTISEMENT_TOPIC); await asyncio.sleep(0.5) #type: ignore
        assert len(service_discovery_module_fixture.find_capabilities(capability_id_filter=cap_id))==1
        mock_td=dialogue_manager_fixture.tool_dispatcher; mock_td.dispatch.return_value=ToolDispatcherResponse(status="unhandled_by_local_tool",payload=None) #type: ignore
        mock_fe=MagicMock(spec=FormulaEngine); formula={"name":"f_fail_hsp","action":"dispatch_tool","parameters":{"tool_name":search_term,"tool_query":"q_fail_hsp"}}; mock_fe.match_input.return_value=formula; mock_fe.execute_formula.return_value={"action_name":"dispatch_tool","action_params":formula["parameters"]}; dialogue_manager_fixture.formula_engine=mock_fe #type: ignore
        dialogue_manager_fixture._dispatch_hsp_task_request=MagicMock(wraps=dialogue_manager_fixture._dispatch_hsp_task_request)
        res_h:List[Any]=[]; orig_h=dialogue_manager_fixture._handle_incoming_hsp_task_result; dialogue_manager_fixture._handle_incoming_hsp_task_result=MagicMock(wraps=lambda p,s,e:(res_h.append(p),orig_h(p,s,e))) #type: ignore
        mock_llm_fixture.generate_response_history.clear()
        user_q = "hsp_task_failed_what_now"
        resp = await dialogue_manager_fixture.get_simple_response(user_q,"u_hsp_f","s_hsp_f")
        assert "I've sent your request" in resp; await asyncio.sleep(1.5)
        dialogue_manager_fixture._dispatch_hsp_task_request.assert_called_once(); assert dialogue_manager_fixture._handle_incoming_hsp_task_result.called; assert len(res_h)>0
        assert res_h[0]['status']=='failure' and res_h[0]['error_details']['error_code']=="FAIL" #type: ignore
        assert not mock_llm_fixture.generate_response_history
        print("[Test HSP Fail -> User Informed] Verified HSP task dispatch, failure handling by DM. LLM not called for this turn.")
        dialogue_manager_fixture.formula_engine=FormulaEngine(); dialogue_manager_fixture._handle_incoming_hsp_task_result=orig_h

    @pytest.mark.asyncio
    async def test_task_result_description_processed_by_content_analyzer(
        self, dialogue_manager_fixture: DialogueManager, service_discovery_module_fixture: ServiceDiscoveryModule,
        content_analyzer_module_fixture: ContentAnalyzerModule, main_ai_hsp_connector: HSPConnector, peer_a_hsp_connector: HSPConnector ):
        peer_id=TEST_AI_ID_PEER_A; cap_id=f"{peer_id}_describe_entity_v1.0"
        adv=HSPCapabilityAdvertisementPayload(capability_id=cap_id,ai_id=peer_id,name="MockDesc",description="desc",version="1.0",availability_status="online",tags=["mock","description"],input_schema_example={"entity_name":"string"},output_schema_example={"description":"string"}) #type: ignore
        peer_a_hsp_connector.publish_capability_advertisement(adv,CAP_ADVERTISEMENT_TOPIC); await asyncio.sleep(0.5)
        assert len(service_discovery_module_fixture.find_capabilities(capability_id_filter=cap_id))==1
        orig_ca_method=content_analyzer_module_fixture.process_hsp_fact_content; content_analyzer_module_fixture.process_hsp_fact_content=MagicMock(wraps=orig_ca_method)
        def handler(p,s,e): entity=p['parameters'].get('entity_name','Default'); desc=f"Entity '{entity}' is a prominent feature in the Cygnus constellation."; res_p=HSPTaskResultPayload(result_id="r_desc",request_id=p['request_id'],executing_ai_id=peer_id,status="success",payload={"description":desc},timestamp_completed=datetime.now(timezone.utc).isoformat()); peer_a_hsp_connector.send_task_result(res_p,p['callback_address'],e['correlation_id']) #type: ignore
        peer_a_hsp_connector.register_on_task_request_callback(handler); peer_a_hsp_connector.subscribe(f"hsp/requests/{peer_id}/#"); time.sleep(0.2)
        entity_desc="GalaxyNova"; await dialogue_manager_fixture.get_simple_response(f"hsp_task:{cap_id} with params {{\"entity_name\":\"{entity_desc}\"}}","u_ca","s_ca"); await asyncio.sleep(1.5)
        content_analyzer_module_fixture.process_hsp_fact_content.assert_called()
        ca_args=content_analyzer_module_fixture.process_hsp_fact_content.call_args[0][0]; assert f"entity '{entity_desc}'" in ca_args.get('statement_nl','').lower() #type: ignore
        g=content_analyzer_module_fixture.graph; assert any(entity_desc.lower() in n_d.get('label','').lower() and n_d.get('hsp_source_info',{}).get('source_ai')==peer_id for _,n_d in g.nodes(data=True))
        content_analyzer_module_fixture.process_hsp_fact_content=orig_ca_method

    @pytest.mark.asyncio
    async def test_dm_prefers_higher_trust_capability(
        self, dialogue_manager_fixture: DialogueManager, service_discovery_module_fixture: ServiceDiscoveryModule,
        peer_a_hsp_connector: HSPConnector, peer_b_hsp_connector: HSPConnector,
        trust_manager_fixture: TrustManager, main_ai_hsp_connector: HSPConnector ):
        cap_name="shared_calc"; cap_id_a=f"{TEST_AI_ID_PEER_A}_{cap_name}_v1"; cap_id_b=f"{TEST_AI_ID_PEER_B}_{cap_name}_v1"
        trust_manager_fixture.update_trust_score(TEST_AI_ID_PEER_A,new_absolute_score=0.9)
        trust_manager_fixture.update_trust_score(TEST_AI_ID_PEER_B,new_absolute_score=0.3)
        adv_a=HSPCapabilityAdvertisementPayload(capability_id=cap_id_a,ai_id=TEST_AI_ID_PEER_A,name=cap_name,description="Calc by A",version="1.0",availability_status="online",tags=[cap_name]); peer_a_hsp_connector.publish_capability_advertisement(adv_a,CAP_ADVERTISEMENT_TOPIC) #type: ignore
        adv_b=HSPCapabilityAdvertisementPayload(capability_id=cap_id_b,ai_id=TEST_AI_ID_PEER_B,name=cap_name,description="Calc by B",version="1.0",availability_status="online",tags=[cap_name]); peer_b_hsp_connector.publish_capability_advertisement(adv_b,CAP_ADVERTISEMENT_TOPIC); await asyncio.sleep(0.5) #type: ignore
        caps=service_discovery_module_fixture.find_capabilities(capability_name_filter=cap_name,sort_by_trust=True); assert len(caps)==2 and caps[0]['ai_id']==TEST_AI_ID_PEER_A
        dialogue_manager_fixture._dispatch_hsp_task_request=MagicMock(wraps=dialogue_manager_fixture._dispatch_hsp_task_request)
        mock_fe=MagicMock(spec=FormulaEngine); formula={"name":"f_shared","action":"dispatch_tool","parameters":{"tool_name":cap_name,"tool_query":"1+1"}}; mock_fe.match_input.return_value=formula; mock_fe.execute_formula.return_value={"action_name":"dispatch_tool","action_params":formula["parameters"]}; dialogue_manager_fixture.formula_engine=mock_fe #type: ignore
        mock_td=dialogue_manager_fixture.tool_dispatcher; mock_td.dispatch.return_value=ToolDispatcherResponse(status="unhandled_by_local_tool",payload=None) #type: ignore
        await dialogue_manager_fixture.get_simple_response("trigger_shared_calc","u_trust_pref","s_trust_pref"); await asyncio.sleep(0.5)
        dialogue_manager_fixture._dispatch_hsp_task_request.assert_called_once()
        selected_cap_adv:HSPCapabilityAdvertisementPayload = dialogue_manager_fixture._dispatch_hsp_task_request.call_args[0][0] #type: ignore
        assert selected_cap_adv["ai_id"] == TEST_AI_ID_PEER_A, f"DM did not select higher trust peer. Got: {selected_cap_adv['ai_id']}"
        dialogue_manager_fixture.formula_engine=FormulaEngine()


# To run these tests:
# 1. Ensure an MQTT broker is running on localhost:1883 (e.g. docker run -it -p 1883:1883 eclipse-mosquitto)
# 2. From the project root: pytest tests/hsp/test_hsp_integration.py
#
# Note: These tests involve network communication and timing.
#       `time.sleep` is used for simplicity to allow messages to propagate.
#       If tests are flaky, these sleep durations might need adjustment or a more robust
#       event signaling mechanism between the connectors and test assertions.
```
