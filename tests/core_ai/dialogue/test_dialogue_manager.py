import unittest
from unittest.mock import MagicMock, patch
import networkx as nx
from typing import Optional, Dict, Any, List, Tuple
import uuid # For test session IDs in __main__
import os # Added for os.path.exists and os.remove in __main__
import re # Added for regex in _is_kg_query
import json
import ast

# Assuming src is in PYTHONPATH for test execution
from src.core_ai.dialogue.dialogue_manager import DialogueManager # Changed
from src.shared.types.common_types import ( # Changed
    OperationalConfig, DialogueTurn, PendingHSPTaskInfo,
    ParsedToolIODetails, CritiqueResult, ToolDispatcherResponse, # Added for completeness if DM uses them directly
    FormulaConfigEntry, DialogueMemoryEntryMetadata
)
from hsp.types import (
    HSPTaskRequestPayload, HSPTaskResultPayload,
    HSPCapabilityAdvertisementPayload, HSPMessageEnvelope, HSPFactPayload
)
# Mock other direct dependencies if their actual classes are not needed for type hinting in test setups
# from core_ai.personality.personality_manager import PersonalityManager
# from core_ai.memory.ham_memory_manager import HAMMemoryManager
# from services.llm_interface import LLMInterface
# from core_ai.emotion_system import EmotionSystem
# from core_ai.crisis_system import CrisisSystem
# from core_ai.time_system import TimeSystem
# from core_ai.formula_engine import FormulaEngine
# from tools.tool_dispatcher import ToolDispatcher
# from core_ai.learning.self_critique_module import SelfCritiqueModule
# from core_ai.learning.fact_extractor_module import FactExtractorModule
# from core_ai.learning.learning_manager import LearningManager
# from core_ai.learning.content_analyzer_module import ContentAnalyzerModule
# from core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
# from services.sandbox_executor import SandboxExecutor
# from hsp.connector import HSPConnector


class TestDialogueManagerHelperMethods(unittest.TestCase):

    def setUp(self):
        # Basic DM for testing helper methods. Dependencies can be mocked if they were used by these helpers.
        # For these specific helpers, direct interaction with complex dependencies is minimal.
        # Provide minimal config. Ensure 'operational_configs' key exists if DialogueManager constructor accesses it.
        # OperationalConfig is total=False, so an empty dict is valid.
        self.dm = DialogueManager(config={}) # type: ignore


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
        # The method currently strips "'s", so "Google's parent company" becomes "Google parent company"
        self.assertEqual(result, ("google parent company", "has_ceo"))

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
        self.test_config: OperationalConfig = { # type: ignore
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
        self.dm.self_critique_module = MagicMock()
        self.dm.self_critique_module.critique_interaction.return_value = CritiqueResult(score=0.9, reason="Looks good.", suggested_alternative=None)
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


class TestDialogueManagerToolDrafting(unittest.TestCase):
    def setUp(self):
        self.mock_personality_manager = MagicMock()
        self.mock_personality_manager.get_current_personality_trait.return_value = "TestDraftAI"

        self.mock_llm_interface = MagicMock()

        self.test_config: OperationalConfig = { # type: ignore
            "operational_configs": {
                "timeouts": {"dialogue_manager_turn": 120},
                "learning_thresholds": {"min_critique_score_to_store": 0.0}
            }
        }

        patchers = {
            'PersonalityManager': patch('src.core_ai.dialogue.dialogue_manager.PersonalityManager', return_value=self.mock_personality_manager),
            'HAMMemoryManager': patch('src.core_ai.dialogue.dialogue_manager.HAMMemoryManager'),
            'EmotionSystem': patch('src.core_ai.dialogue.dialogue_manager.EmotionSystem'),
            'CrisisSystem': patch('src.core_ai.dialogue.dialogue_manager.CrisisSystem'),
            'TimeSystem': patch('src.core_ai.dialogue.dialogue_manager.TimeSystem'),
            'FormulaEngine': patch('src.core_ai.dialogue.dialogue_manager.FormulaEngine'),
            'ToolDispatcher': patch('src.core_ai.dialogue.dialogue_manager.ToolDispatcher'),
            'SelfCritiqueModule': patch('src.core_ai.dialogue.dialogue_manager.SelfCritiqueModule'),
            'FactExtractorModule': patch('src.core_ai.dialogue.dialogue_manager.FactExtractorModule'),
            'LearningManager': patch('src.core_ai.dialogue.dialogue_manager.LearningManager'),
            'ContentAnalyzerModule': patch('src.core_ai.dialogue.dialogue_manager.ContentAnalyzerModule'),
            'SandboxExecutor': patch('src.core_ai.dialogue.dialogue_manager.SandboxExecutor')
        }
        self.mocks = {name: patcher.start() for name, patcher in patchers.items()}
        for patcher in patchers.values():
            self.addCleanup(patcher.stop)

        self.dm = DialogueManager(
            llm_interface=self.mock_llm_interface,
            personality_manager=self.mock_personality_manager,
            config=self.test_config
        )
        self.dm.personality_manager = self.mock_personality_manager


    async def test_handle_draft_tool_request_success_flow(self):
        tool_name = "EchoTool"
        purpose_and_io_desc = "A simple tool that takes a string message and returns it."

        mock_io_details: ParsedToolIODetails = { # type: ignore
            "suggested_method_name": "echo",
            "class_docstring_hint": "An echo tool.",
            "method_docstring_hint": "Echoes the input message.",
            "parameters": [{"name": "message", "type": "str", "description": "The message to echo."}],
            "return_type": "str",
            "return_description": "The echoed message."
        }
        mock_io_details_json_str = json.dumps(mock_io_details)
        mock_generated_code = "class EchoTool:\n    pass # Dummy generated code"
        self.mocks['SandboxExecutor'].return_value.run.return_value = ("Mocked sandbox success", None)


        self.mock_llm_interface.generate_response.side_effect = [
            mock_io_details_json_str,
            mock_generated_code
        ]

        result_response = await self.dm.handle_draft_tool_request(tool_name, purpose_and_io_desc)

        self.assertEqual(self.mock_llm_interface.generate_response.call_count, 2)

        io_parsing_call_args = self.mock_llm_interface.generate_response.call_args_list[0]
        io_parsing_prompt_arg = io_parsing_call_args[1]['prompt']
        self.assertIn("You are an expert Python code analyst.", io_parsing_prompt_arg)
        self.assertIn(purpose_and_io_desc, io_parsing_prompt_arg)
        self.assertEqual(io_parsing_call_args[1]['params'], {"temperature": 0.1})

        code_gen_call_args = self.mock_llm_interface.generate_response.call_args_list[1]
        code_gen_prompt_arg = code_gen_call_args[1]['prompt']
        self.assertIn(f"Tool Class Name: {tool_name}", code_gen_prompt_arg)
        self.assertIn("class_docstring_hint\": \"An echo tool.\"", mock_io_details_json_str)
        self.assertIn("Method Name: echo", code_gen_prompt_arg)
        self.assertIn("message: str", code_gen_prompt_arg)
        self.assertIn("Return Type: str", code_gen_prompt_arg)
        self.assertEqual(code_gen_call_args[1]['params'], {"temperature": 0.3})

        self.assertIn(f"Okay, I've drafted a Python skeleton for a tool named `{tool_name}`", result_response)
        self.assertIn(mock_generated_code, result_response)
        self.assertIn("Info: The drafted code is syntactically valid Python.", result_response)

        self.mocks['SandboxExecutor'].return_value.run.assert_called_once()
        self.assertIn("---Sandbox Test Run---", result_response)
        self.assertIn("Execution Result: Mocked sandbox success", result_response)


    async def test_handle_draft_tool_request_code_syntax_error(self):
        tool_name = "SyntaxErrorTool"
        purpose_and_io_desc = "A tool that will have a syntax error."

        mock_io_details: ParsedToolIODetails = {"suggested_method_name": "broken", "class_docstring_hint":"d","method_docstring_hint":"d","parameters":[],"return_type":"Any","return_description":"d"} # type: ignore
        mock_io_details_json_str = json.dumps(mock_io_details)
        mock_generated_code_with_error = "class SyntaxErrorTool:\n def broken(self):\n  print 'oops'"

        self.mock_llm_interface.generate_response.side_effect = [
            mock_io_details_json_str,
            mock_generated_code_with_error
        ]

        result_response = await self.dm.handle_draft_tool_request(tool_name, purpose_and_io_desc)

        self.assertEqual(self.mock_llm_interface.generate_response.call_count, 2)
        self.assertIn(f"Okay, I've drafted a Python skeleton for a tool named `{tool_name}`", result_response)
        self.assertIn(mock_generated_code_with_error, result_response)
        self.assertIn("Warning: The drafted code has a syntax error", result_response)
        self.assertIn("line 3", result_response) # Updated to match ast.SyntaxError format

        self.mocks['SandboxExecutor'].return_value.run.assert_not_called()


    async def test_handle_draft_tool_request_sandbox_execution_error(self):
        tool_name = "SandboxErrorTool"
        purpose_and_io_desc = "A tool that is valid but will error in sandbox."

        mock_io_details: ParsedToolIODetails = { # type: ignore
            "suggested_method_name": "error_method",
            "class_docstring_hint": "Tool designed to error in sandbox.",
            "method_docstring_hint": "This method will raise an error.",
            "parameters": [], "return_type": "None", "return_description": "Error."
        }
        mock_io_details_json_str = json.dumps(mock_io_details)
        mock_valid_code = "class SandboxErrorTool:\n  def __init__(self, config=None): pass\n  def error_method(self):\n    raise ValueError('Sandbox test error')"

        self.mock_llm_interface.generate_response.side_effect = [
            mock_io_details_json_str,
            mock_valid_code
        ]

        self.mocks['SandboxExecutor'].return_value.run.return_value = (None, "ValueError: Sandbox test error")

        result_response = await self.dm.handle_draft_tool_request(tool_name, purpose_and_io_desc)

        self.assertEqual(self.mock_llm_interface.generate_response.call_count, 2)
        self.mocks['SandboxExecutor'].return_value.run.assert_called_once()
        self.assertIn("Info: The drafted code is syntactically valid Python.", result_response)
        self.assertIn("---Sandbox Test Run---", result_response)
        self.assertIn("Execution Error: ValueError: Sandbox test error", result_response)


    async def test_handle_draft_tool_request_io_parsing_json_error(self):
        tool_name = "BadJsonTool"
        purpose_and_io_desc = "This will cause a JSON error."

        self.mock_llm_interface.generate_response.return_value = "This is not valid JSON {oops"

        result_response = await self.dm.handle_draft_tool_request(tool_name, purpose_and_io_desc)

        self.mock_llm_interface.generate_response.assert_called_once()
        self.assertIn(f"I had trouble understanding the specific parameters and return types from your description for '{tool_name}'.", result_response)

    async def test_handle_draft_tool_request_io_parsing_value_error(self):
        tool_name = "ValueErrorTool"
        purpose_and_io_desc = "This will cause a value error if JSON is empty after extraction."

        self.mock_llm_interface.generate_response.return_value = "```json\n\n```"

        result_response = await self.dm.handle_draft_tool_request(tool_name, purpose_and_io_desc)

        self.mock_llm_interface.generate_response.assert_called_once()
        self.assertIn(f"I encountered an issue trying to structure the details for '{tool_name}'. Please try rephrasing your request.", result_response)

    async def test_handle_draft_tool_request_io_details_missing_keys_fallback(self):
        tool_name = "PartialTool"
        purpose_and_io_desc = "A tool with partial details."

        mock_io_details_partial_json_str = json.dumps({ # type: ignore
            "suggested_method_name": "do_partial_stuff",
            # "class_docstring_hint": "Missing class doc", # Missing
            "parameters": [{"name": "data", "type": "Any", "description": "Some data."}],
            # "return_type": "bool" # Missing
            # "return_description" is also missing
        })

        mock_generated_code = "class PartialTool:\n    pass # Dummy generated code"
        self.mocks['SandboxExecutor'].return_value.run.return_value = ("Partial sandbox success", None)


        self.mock_llm_interface.generate_response.side_effect = [
            mock_io_details_partial_json_str,
            mock_generated_code
        ]

        result_response = await self.dm.handle_draft_tool_request(tool_name, purpose_and_io_desc)
        self.assertEqual(self.mock_llm_interface.generate_response.call_count, 2)

        code_gen_call_args = self.mock_llm_interface.generate_response.call_args_list[1]
        code_gen_prompt_arg = code_gen_call_args[1]['prompt']
        self.assertIn(f"Class Docstring: {purpose_and_io_desc}", code_gen_prompt_arg)
        self.assertIn("Method Name: do_partial_stuff", code_gen_prompt_arg)
        self.assertIn("Return Type: Any", code_gen_prompt_arg)

        self.assertIn(f"Okay, I've drafted a Python skeleton for a tool named `{tool_name}`", result_response)

# Need to import json for the test class
# import json # Already imported at the top
