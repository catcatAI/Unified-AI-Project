import unittest
from unittest.mock import MagicMock, patch
import networkx as nx
from typing import Optional, Dict, Any, List, Tuple

# Assuming src is in PYTHONPATH for test execution
from core_ai.dialogue.dialogue_manager import DialogueManager

class TestDialogueManagerHelperMethods(unittest.TestCase):

    def setUp(self):
        # Basic DM for testing helper methods. Dependencies can be mocked if they were used by these helpers.
        # For these specific helpers, direct interaction with complex dependencies is minimal.
        # Provide minimal config. Ensure 'operational_configs' key exists if DialogueManager constructor accesses it.
        self.dm = DialogueManager(config={"operational_configs": {}})


        # Create a sample graph for testing _find_entity_node_id_in_kg and _query_session_kg
        self.sample_graph = nx.DiGraph()
        self.sample_graph.add_node("ent_google_org", label="Google", type="ORG")
        self.sample_graph.add_node("ent_microsoft_org", label="Microsoft", type="ORG")
        self.sample_graph.add_node("ent_sundar_person", label="Sundar Pichai", type="PERSON")
        self.sample_graph.add_node("ent_satya_person", label="Satya Nadella", type="PERSON")
        self.sample_graph.add_node("ent_redmond_gpe", label="Redmond", type="GPE")

        self.sample_graph.add_edge("ent_google_org", "ent_sundar_person", type="has_ceo")
        self.sample_graph.add_edge("ent_microsoft_org", "ent_satya_person", type="has_ceo")
        self.sample_graph.add_edge("ent_microsoft_org", "ent_redmond_gpe", type="located_in")
        self.sample_graph.add_edge("ent_google_org", "ent_redmond_gpe", type="competes_with_org_in_same_place_as_msft_hq") # A dummy rel


    def test_find_entity_node_id_in_kg_found(self):
        node_id = self.dm._find_entity_node_id_in_kg(self.sample_graph, "Google")
        self.assertEqual(node_id, "ent_google_org")

    def test_find_entity_node_id_in_kg_found_case_insensitive(self):
        node_id = self.dm._find_entity_node_id_in_kg(self.sample_graph, "microsoft")
        self.assertEqual(node_id, "ent_microsoft_org")

    def test_find_entity_node_id_in_kg_not_found(self):
        node_id = self.dm._find_entity_node_id_in_kg(self.sample_graph, "Apple")
        self.assertIsNone(node_id)

    def test_find_entity_node_id_in_kg_empty_graph(self):
        empty_graph = nx.DiGraph()
        node_id = self.dm._find_entity_node_id_in_kg(empty_graph, "Google")
        self.assertIsNone(node_id)

    def test_find_entity_node_id_in_kg_none_graph(self):
        node_id = self.dm._find_entity_node_id_in_kg(None, "Google") # type: ignore
        self.assertIsNone(node_id)


    def test_query_session_kg_found(self):
        self.dm.session_knowledge_graphs["test_session"] = self.sample_graph
        answer = self.dm._query_session_kg("test_session", "Google", "has_ceo")
        self.assertEqual(answer, "Sundar Pichai")

    def test_query_session_kg_entity_not_found(self):
        self.dm.session_knowledge_graphs["test_session"] = self.sample_graph
        answer = self.dm._query_session_kg("test_session", "Apple", "has_ceo")
        self.assertIsNone(answer)

    def test_query_session_kg_relationship_not_found(self):
        self.dm.session_knowledge_graphs["test_session"] = self.sample_graph
        answer = self.dm._query_session_kg("test_session", "Google", "located_in") # Google not located_in Redmond in this graph
        self.assertIsNone(answer)

    def test_query_session_kg_no_graph_for_session(self):
        answer = self.dm._query_session_kg("non_existent_session", "Google", "has_ceo")
        self.assertIsNone(answer)

    def test_query_session_kg_target_no_label(self):
        graph_no_label = nx.DiGraph()
        graph_no_label.add_node("ent_source_org", label="SourceOrg", type="ORG")
        graph_no_label.add_node("ent_target_no_label_person", type="PERSON") # No label attribute
        graph_no_label.add_edge("ent_source_org", "ent_target_no_label_person", type="has_contact")

        self.dm.session_knowledge_graphs["test_session_no_label"] = graph_no_label
        answer = self.dm._query_session_kg("test_session_no_label", "SourceOrg", "has_contact")
        self.assertEqual(answer, "ent_target_no_label_person") # Should return node ID as fallback


    def test_is_kg_query_ceo_pattern(self):
        result = self.dm._is_kg_query("who is ceo of Google?")
        self.assertIsNotNone(result)
        self.assertEqual(result, ("google", "has_ceo"))

    def test_is_kg_query_ceo_pattern_with_the(self):
        result = self.dm._is_kg_query("who is the ceo of Microsoft Corporation?")
        self.assertIsNotNone(result)
        self.assertEqual(result, ("microsoft corporation", "has_ceo"))

    def test_is_kg_query_ceo_pattern_with_a(self): # Although "a ceo" is less common for specific query
        result = self.dm._is_kg_query("who is a president of United States?") # Changed title for realism
        self.assertIsNotNone(result)
        self.assertEqual(result, ("united states", "has_president"))

    def test_is_kg_query_founder_pattern(self):
        result = self.dm._is_kg_query("who is founder of Apple Inc") # No question mark
        self.assertIsNotNone(result)
        self.assertEqual(result, ("apple inc", "has_founder"))

    def test_is_kg_query_location_located_pattern(self):
        result = self.dm._is_kg_query("where is Microsoft located")
        self.assertIsNotNone(result)
        self.assertEqual(result, ("microsoft", "located_in"))

    def test_is_kg_query_location_based_pattern(self):
        result = self.dm._is_kg_query("where is Apple based?")
        self.assertIsNotNone(result)
        self.assertEqual(result, ("apple", "located_in"))

    def test_is_kg_query_acquire_pattern_company(self):
        # This test assumes "acquire" is a relationship type the KG might have.
        result = self.dm._is_kg_query("what company did Google acquire?")
        self.assertIsNotNone(result)
        self.assertEqual(result, ("google", "acquire"))

    def test_is_kg_query_acquire_pattern_general(self):
        result = self.dm._is_kg_query("what did Apple acquire")
        self.assertIsNotNone(result)
        self.assertEqual(result, ("apple", "acquire"))

    def test_is_kg_query_entity_with_possessive_in_regex(self):
        # Test how the regex handles entities that might themselves contain 's or be complex.
        # The current regex `(.+)` captures the whole thing.
        # The cleaning logic for possessives is simple and might not perfectly normalize all complex entities.
        result = self.dm._is_kg_query("who is ceo of Google's parent company?")
        self.assertIsNotNone(result)
        # "google's parent company" is captured. It does not end with 's, so cleaning `entity[:-2]` doesn't apply.
        self.assertEqual(result, ("google's parent company", "has_ceo"))

    def test_is_kg_query_no_match(self):
        result = self.dm._is_kg_query("tell me a joke")
        self.assertIsNone(result)

    def test_is_kg_query_empty_input(self):
        result = self.dm._is_kg_query("")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()


class TestDialogueManagerKGIntegration(unittest.TestCase):
    def setUp(self):
        # Mock dependencies that DialogueManager initializes
        self.mock_personality_manager = MagicMock()
        self.mock_personality_manager.get_current_personality_trait.return_value = "TestAI"
        self.mock_personality_manager.get_initial_prompt.return_value = "Hello from TestAI."

        self.mock_memory_manager = MagicMock()
        self.mock_memory_manager.store_experience.return_value = "mem_id_123" # Dummy memory ID

        self.mock_llm_interface = MagicMock()
        self.mock_llm_interface.generate_response.return_value = "This is a fallback LLM response."

        self.mock_emotion_system = MagicMock()
        self.mock_emotion_system.get_current_emotion_expression.return_value = {"text_ending": ""} # No emotional suffix for tests

        self.mock_crisis_system = MagicMock()
        self.mock_crisis_system.assess_input_for_crisis.return_value = 0 # No crisis

        self.mock_formula_engine = MagicMock()
        self.mock_formula_engine.match_input.return_value = None # No formula match by default

        self.mock_content_analyzer = MagicMock()

        # Config for DialogueManager
        self.test_config = {
            "max_dialogue_history": 6,
            "operational_configs": {
                "timeouts": {"dialogue_manager_turn": 120},
                "learning_thresholds": {"min_critique_score_to_store": 0.0}
            },
            "crisis_response_text": "Crisis response."
        }

        self.dm = DialogueManager(
            personality_manager=self.mock_personality_manager,
            memory_manager=self.mock_memory_manager,
            llm_interface=self.mock_llm_interface,
            emotion_system=self.mock_emotion_system,
            crisis_system=self.mock_crisis_system,
            formula_engine=self.mock_formula_engine,
            content_analyzer=self.mock_content_analyzer, # Use the mock
            config=self.test_config
        )
        # Ensure self_critique_module and learning_manager are also mocked if their methods are called
        # For these tests, they might not be, but good practice if get_simple_response calls them.
        self.dm.self_critique_module = MagicMock()
        self.dm.self_critique_module.critique_interaction.return_value = {"score": 0.9, "reason": "Looks good."}
        self.dm.learning_manager = MagicMock()


    async def test_kg_qa_ceo_and_location(self):
        session_id = "kg_integ_test_session_01"
        user_id = "kg_integ_test_user_01"

        # 1. Setup: Define the mock KG that ContentAnalyzer will return
        mock_kg = nx.DiGraph()
        mock_kg.add_node("ent_innovate_corp_org", label="Innovate Corp", type="ORG")
        mock_kg.add_node("ent_jane_doe_person", label="Jane Doe", type="PERSON")
        mock_kg.add_node("ent_silicon_valley_gpe", label="Silicon Valley", type="GPE")
        mock_kg.add_node("ent_alphatech_org", label="AlphaTech", type="ORG")

        mock_kg.add_edge("ent_innovate_corp_org", "ent_jane_doe_person", type="has_ceo")
        mock_kg.add_edge("ent_innovate_corp_org", "ent_silicon_valley_gpe", type="located_in")
        mock_kg.add_edge("ent_innovate_corp_org", "ent_alphatech_org", type="acquire")

        self.mock_content_analyzer.analyze_content.return_value = (None, mock_kg) # Return (TypedDict_KG_placeholder, nx_Graph)

        # 2. Analyze text
        analyze_cmd = "!analyze: Innovate Corp is a tech company. Jane Doe is its CEO. It is in Silicon Valley and bought AlphaTech."
        # Need to run async methods with await if they are async
        analyze_response = await self.dm.get_simple_response(analyze_cmd, session_id, user_id)
        self.assertIn("Context analysis triggered", analyze_response)
        self.assertIn(session_id, self.dm.session_knowledge_graphs)
        self.assertEqual(self.dm.session_knowledge_graphs[session_id], mock_kg)

        # 3. Ask "who is ceo of Innovate Corp?"
        q1 = "who is ceo of Innovate Corp?"
        r1 = await self.dm.get_simple_response(q1, session_id, user_id)
        expected_r1 = f"{self.mock_personality_manager.get_current_personality_trait.return_value}: From the analyzed context, the ceo of Innovate Corp is Jane Doe."
        self.assertEqual(r1, expected_r1)

        # 4. Ask "where is Innovate Corp located?"
        q2 = "where is Innovate Corp located?"
        r2 = await self.dm.get_simple_response(q2, session_id, user_id)
        expected_r2 = f"{self.mock_personality_manager.get_current_personality_trait.return_value}: From the analyzed context, Innovate Corp is located in Silicon Valley."
        self.assertEqual(r2, expected_r2)

        # 5. Ask "what did Innovate Corp acquire?"
        q3 = "what did Innovate Corp acquire?"
        r3 = await self.dm.get_simple_response(q3, session_id, user_id)
        expected_r3 = f"{self.mock_personality_manager.get_current_personality_trait.return_value}: From the analyzed context, Innovate Corp acquired AlphaTech."
        self.assertEqual(r3, expected_r3)

        # Ensure LLM was not called for these KG-answered questions
        self.mock_llm_interface.generate_response.assert_not_called()


    async def test_kg_qa_fallback_if_kg_miss(self):
        session_id = "kg_integ_test_session_02"
        user_id = "kg_integ_test_user_02"

        mock_kg = nx.DiGraph() # Empty graph or irrelevant graph
        mock_kg.add_node("ent_other_org", label="Other Corp", type="ORG")
        self.mock_content_analyzer.analyze_content.return_value = (None, mock_kg)

        analyze_cmd = "!analyze: Some other unrelated text."
        await self.dm.get_simple_response(analyze_cmd, session_id, user_id)

        # Reset mock call count before the query that should go to LLM
        self.mock_llm_interface.generate_response.reset_mock()

        q1 = "who is ceo of Innovate Corp?" # Innovate Corp not in this session's KG
        r1 = await self.dm.get_simple_response(q1, session_id, user_id)

        # Expect fallback to LLM
        self.mock_llm_interface.generate_response.assert_called_once()
        expected_r1_fallback = f"{self.mock_personality_manager.get_current_personality_trait.return_value}: {self.mock_llm_interface.generate_response.return_value}"
        self.assertEqual(r1, expected_r1_fallback)

    async def test_kg_qa_fallback_if_no_kg_for_session(self):
        session_id = "kg_integ_test_session_03" # No !analyze for this session
        user_id = "kg_integ_test_user_03"

        self.mock_llm_interface.generate_response.reset_mock()

        q1 = "who is ceo of Innovate Corp?"
        r1 = await self.dm.get_simple_response(q1, session_id, user_id)

        # Expect fallback to LLM
        self.mock_llm_interface.generate_response.assert_called_once()
        expected_r1_fallback = f"{self.mock_personality_manager.get_current_personality_trait.return_value}: {self.mock_llm_interface.generate_response.return_value}"
        self.assertEqual(r1, expected_r1_fallback)

    async def test_kg_qa_no_answer_from_kg_then_fallback(self):
        session_id = "kg_integ_test_session_04"
        user_id = "kg_integ_test_user_04"

        mock_kg = nx.DiGraph()
        mock_kg.add_node("ent_innovate_corp_org", label="Innovate Corp", type="ORG")
        # No CEO relationship for Innovate Corp in this KG
        self.mock_content_analyzer.analyze_content.return_value = (None, mock_kg)

        analyze_cmd = "!analyze: Innovate Corp is a company."
        await self.dm.get_simple_response(analyze_cmd, session_id, user_id)

        self.mock_llm_interface.generate_response.reset_mock()

        q1 = "who is ceo of Innovate Corp?" # KG has Innovate Corp, but not its CEO
        r1 = await self.dm.get_simple_response(q1, session_id, user_id)

        self.mock_llm_interface.generate_response.assert_called_once()
        expected_r1_fallback = f"{self.mock_personality_manager.get_current_personality_trait.return_value}: {self.mock_llm_interface.generate_response.return_value}"
        self.assertEqual(r1, expected_r1_fallback)

# To run these async tests:
# Ensure your test runner can handle async tests (e.g., if running directly, use asyncio.run)
# If using `python -m unittest`, it should handle async test methods in modern Python versions.
# Example for running directly:
# async def run_tests():
#     suite = unittest.TestSuite()
#     suite.addTest(unittest.makeSuite(TestDialogueManagerHelperMethods))
#     suite.addTest(unittest.makeSuite(TestDialogueManagerKGIntegration))
#     runner = unittest.TextTestRunner()
#     runner.run(suite)

# if __name__ == '__main__':
#     import asyncio
#     asyncio.run(run_tests())
# This direct run part might need adjustment based on how unittest discovers/runs async tests.
# Standard `python -m unittest discover` or `python -m unittest path.to.test_module` should work.
