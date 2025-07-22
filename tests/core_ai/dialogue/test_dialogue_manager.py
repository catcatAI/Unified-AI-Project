import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import networkx as nx
from typing import Optional, Dict, Any, List, Tuple
import uuid
import os
import re
import json
import ast

from src.core_ai.dialogue.dialogue_manager import DialogueManager
from src.shared.types.common_types import (
    OperationalConfig,
    ParsedToolIODetails,
    CritiqueResult,
)
from src.hsp.types import (
    HSPTaskRequestPayload,
    HSPTaskResultPayload,
    HSPCapabilityAdvertisementPayload,
    HSPMessageEnvelope,
    HSPFactPayload,
)

# Define a consistent test output directory (relative to project root)
PROJECT_ROOT_FOR_TEST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TEST_STORAGE_DIR = os.path.join(PROJECT_ROOT_FOR_TEST, "tests", "test_output_data", "dialogue_manager")

@pytest.fixture(scope="function")
async def dialogue_manager_helper_fixture():
    # Mock dependencies for DialogueManager
    mock_personality_manager = MagicMock()
    mock_personality_manager.get_current_personality_trait.return_value = "TestAI"
    mock_memory_manager = MagicMock()
    mock_llm_interface = MagicMock()
    mock_emotion_system = MagicMock()
    mock_emotion_system.get_current_emotion_expression.return_value = {"text_ending": ""}
    mock_crisis_system = MagicMock()
    mock_crisis_system.assess_input_for_crisis.return_value = 0 # Default to no crisis
    mock_formula_engine = MagicMock()
    mock_formula_engine.match_input.return_value = None # Default to no formula match
    mock_content_analyzer = MagicMock()
    mock_tool_dispatcher = MagicMock()
    mock_self_critique_module = MagicMock()
    # Default behavior for critique: return a high score so it doesn't interfere with other tests
    mock_self_critique_module.critique_interaction.return_value = {"score": 1.0, "suggested_alternative": None}
    mock_learning_manager = AsyncMock()
    mock_learning_manager.process_and_store_learnables.return_value = []
    mock_repair_engine = MagicMock()
    mock_sandbox_executor = MagicMock()
    mock_time_system = MagicMock()

    # Provide minimal config. Ensure 'operational_configs' key exists if DialogueManager constructor accesses it.
    test_config: OperationalConfig = { # type: ignore
        "max_dialogue_history": 6,
        "operational_configs": {
            "timeouts": {"dialogue_manager_turn": 120},
            "learning_thresholds": {"min_critique_score_to_store": 0.0}
        },
        "crisis_response_text": "Crisis response."
    }

    # Patch the modules that DialogueManager initializes internally
    with patch('src.core_ai.personality.personality_manager.PersonalityManager', return_value=mock_personality_manager),         patch('src.core_ai.memory.ham_memory_manager.HAMMemoryManager', return_value=mock_memory_manager),         patch('src.services.llm_interface.LLMInterface', return_value=mock_llm_interface),         patch('src.core_ai.emotion_system.EmotionSystem', return_value=mock_emotion_system),         patch('src.core_ai.crisis_system.CrisisSystem', return_value=mock_crisis_system),         patch('src.core_ai.formula_engine.FormulaEngine', return_value=mock_formula_engine),         patch('src.core_ai.learning.content_analyzer_module.ContentAnalyzerModule', return_value=mock_content_analyzer),         patch('src.tools.tool_dispatcher.ToolDispatcher', return_value=mock_tool_dispatcher),         patch('src.core_ai.learning.self_critique_module.SelfCritiqueModule', return_value=mock_self_critique_module),         patch('src.core_ai.learning.learning_manager.LearningManager', return_value=mock_learning_manager),         patch('src.services.sandbox_executor.SandboxExecutor', return_value=mock_sandbox_executor),         patch('src.core_ai.time_system.TimeSystem', return_value=mock_time_system):

        dm = DialogueManager(
            personality_manager=mock_personality_manager,
            memory_manager=mock_memory_manager,
            llm_interface=mock_llm_interface,
            emotion_system=mock_emotion_system,
            crisis_system=mock_crisis_system,
            formula_engine=mock_formula_engine,
            content_analyzer=mock_content_analyzer,
            tool_dispatcher=mock_tool_dispatcher,
            self_critique_module=mock_self_critique_module,
            learning_manager=mock_learning_manager,
            # repair_engine=mock_repair_engine, # Removed this line
            sandbox_executor=mock_sandbox_executor,
            time_system=mock_time_system,
            config=test_config
        )

        # Create a sample graph for testing _find_entity_node_id_in_kg and _query_session_kg
        sample_graph = nx.DiGraph()
        sample_graph.add_node("ent_google_org", label="Google", type="ORG")
        sample_graph.add_node("ent_microsoft_org", label="Microsoft", type="ORG")
        sample_graph.add_node("ent_sundar_person", label="Sundar Pichai", type="PERSON")
        sample_graph.add_node("ent_satya_person", label="Satya Nadella", type="PERSON")
        sample_graph.add_node("ent_redmond_gpe", label="Redmond", type="GPE")

        sample_graph.add_edge("ent_google_org", "ent_sundar_person", type="has_ceo")
        sample_graph.add_edge("ent_microsoft_org", "ent_satya_person", type="has_ceo")
        sample_graph.add_edge("ent_microsoft_org", "ent_redmond_gpe", type="located_in")
        sample_graph.add_edge("ent_google_org", "ent_redmond_gpe", type="competes_with_org_in_same_place_as_msft_hq")

        return dm, sample_graph, mock_llm_interface, mock_personality_manager, mock_content_analyzer, mock_sandbox_executor, mock_self_critique_module, mock_learning_manager

# Helper Methods Tests
@pytest.mark.asyncio
async def test_find_entity_node_id_in_kg_found(dialogue_manager_helper_fixture):
    dm, sample_graph, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    node_id = dm._find_entity_node_id_in_kg(sample_graph, "Google")
    assert node_id == "ent_google_org"

@pytest.mark.asyncio
async def test_find_entity_node_id_in_kg_found_case_insensitive(dialogue_manager_helper_fixture):
    dm, sample_graph, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    node_id = dm._find_entity_node_id_in_kg(sample_graph, "microsoft")
    assert node_id == "ent_microsoft_org"

@pytest.mark.asyncio
async def test_find_entity_node_id_in_kg_not_found(dialogue_manager_helper_fixture):
    dm, sample_graph, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    node_id = dm._find_entity_node_id_in_kg(sample_graph, "Apple")
    assert node_id is None

@pytest.mark.asyncio
async def test_find_entity_node_id_in_kg_empty_graph(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    empty_graph = nx.DiGraph()
    node_id = dm._find_entity_node_id_in_kg(empty_graph, "Google")
    assert node_id is None

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_find_entity_node_id_in_kg_none_graph(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    node_id = dm._find_entity_node_id_in_kg(None, "Google") # type: ignore
    assert node_id is None

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_query_session_kg_found(dialogue_manager_helper_fixture):
    dm, sample_graph, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    dm.session_knowledge_graphs["test_session"] = sample_graph
    answer = dm._query_session_kg("test_session", "Google", "has_ceo")
    assert answer == "Sundar Pichai"

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_query_session_kg_entity_not_found(dialogue_manager_helper_fixture):
    dm, sample_graph, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    dm.session_knowledge_graphs["test_session"] = sample_graph
    answer = dm._query_session_kg("test_session", "Apple", "has_ceo")
    assert answer is None

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_query_session_kg_relationship_not_found(dialogue_manager_helper_fixture):
    dm, sample_graph, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    dm.session_knowledge_graphs["test_session"] = sample_graph
    answer = dm._query_session_kg("test_session", "Google", "located_in")
    assert answer is None

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_query_session_kg_no_graph_for_session(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    answer = dm._query_session_kg("non_existent_session", "Google", "has_ceo")
    assert answer is None

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_query_session_kg_target_no_label(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    graph_no_label = nx.DiGraph()
    graph_no_label.add_node("ent_source_org", label="SourceOrg", type="ORG")
    graph_no_label.add_node("ent_target_no_label_person", type="PERSON")
    graph_no_label.add_edge("ent_source_org", "ent_target_no_label_person", type="has_contact")

    dm.session_knowledge_graphs["test_session_no_label"] = graph_no_label
    answer = dm._query_session_kg("test_session_no_label", "SourceOrg", "has_contact")
    assert answer == "ent_target_no_label_person"


@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_is_kg_query_ceo_pattern(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    result = dm._is_kg_query("who is ceo of Google?")
    assert result is not None
    assert result == ("google", "has_ceo")

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_is_kg_query_ceo_pattern_with_the(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    result = dm._is_kg_query("who is the ceo of Microsoft Corporation?")
    assert result is not None
    assert result == ("microsoft corporation", "has_ceo")

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_is_kg_query_ceo_pattern_with_a(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    result = dm._is_kg_query("who is a president of United States?")
    assert result is not None
    assert result == ("united states", "has_president")

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_is_kg_query_founder_pattern(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    result = dm._is_kg_query("who is founder of Apple Inc")
    assert result is not None
    assert result == ("apple inc", "has_founder")

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_is_kg_query_location_located_pattern(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    result = dm._is_kg_query("where is Microsoft located")
    assert result is not None
    assert result == ("microsoft", "located_in")

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_is_kg_query_location_based_pattern(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    result = dm._is_kg_query("where is Apple based?")
    assert result is not None
    assert result == ("apple", "located_in")

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_is_kg_query_acquire_pattern_company(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    result = dm._is_kg_query("what company did Google acquire?")
    assert result is not None
    assert result == ("google", "acquire")

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_is_kg_query_acquire_pattern_general(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    result = dm._is_kg_query("what did Apple acquire")
    assert result is not None
    assert result == ("apple", "acquire")

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_is_kg_query_entity_with_possessive_in_regex(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    result = dm._is_kg_query("who is ceo of Google's parent company?")
    assert result is not None
    assert result == ("google's parent company", "has_ceo")

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_is_kg_query_no_match(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    result = dm._is_kg_query("tell me a joke")
    assert result is None

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_is_kg_query_empty_input(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, _, _ = await dialogue_manager_helper_fixture
    result = dm._is_kg_query("")
    assert result is None

# KG Integration Tests
@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_kg_qa_ceo_and_location(dialogue_manager_helper_fixture):
    dm, _, mock_llm_interface, mock_personality_manager, mock_content_analyzer, _, _, _ = await dialogue_manager_helper_fixture
    session_id = "kg_integ_test_session_01"
    user_id = "kg_integ_test_user_01"

    mock_kg = nx.DiGraph()
    mock_kg.add_node("ent_innovate_corp_org", label="Innovate Corp", type="ORG")
    mock_kg.add_node("ent_jane_doe_person", label="Jane Doe", type="PERSON")
    mock_kg.add_node("ent_silicon_valley_gpe", label="Silicon Valley", type="GPE")
    mock_kg.add_node("ent_alphatech_org", label="AlphaTech", type="ORG")

    mock_kg.add_edge("ent_innovate_corp_org", "ent_jane_doe_person", type="has_ceo")
    mock_kg.add_edge("ent_innovate_corp_org", "ent_silicon_valley_gpe", type="located_in")
    mock_kg.add_edge("ent_innovate_corp_org", "ent_alphatech_org", type="acquire")

    mock_content_analyzer.analyze_content.return_value = (None, mock_kg) # Return (TypedDict_KG_placeholder, nx_Graph)

    analyze_cmd = "!analyze: Innovate Corp is a tech company. Jane Doe is its CEO. It is in Silicon Valley and bought AlphaTech."
    analyze_response = await dm.get_simple_response(analyze_cmd, session_id, user_id)
    assert "Context analysis triggered" in analyze_response
    assert session_id in dm.session_knowledge_graphs
    assert dm.session_knowledge_graphs[session_id] == mock_kg

    q1 = "who is ceo of Innovate Corp?"
    r1 = await dm.get_simple_response(q1, session_id, user_id)
    expected_r1 = f"{mock_personality_manager.get_current_personality_trait.return_value}: From the analyzed context, the ceo of Innovate Corp is Jane Doe."
    assert r1 == expected_r1

    q2 = "where is Innovate Corp located?"
    r2 = await dm.get_simple_response(q2, session_id, user_id)
    expected_r2 = f"{mock_personality_manager.get_current_personality_trait.return_value}: From the analyzed context, Innovate Corp is located in Silicon Valley."
    assert r2 == expected_r2

    q3 = "what did Innovate Corp acquire?"
    r3 = await dm.get_simple_response(q3, session_id, user_id)
    expected_r3 = f"{mock_personality_manager.get_current_personality_trait.return_value}: From the analyzed context, Innovate Corp acquired AlphaTech."
    assert r3 == expected_r3

    mock_llm_interface.generate_response.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_kg_qa_fallback_if_kg_miss(dialogue_manager_helper_fixture):
    dm, _, mock_llm_interface, mock_personality_manager, mock_content_analyzer, _, _, _ = await dialogue_manager_helper_fixture
    session_id = "kg_integ_test_session_02"
    user_id = "kg_integ_test_user_02"

    mock_kg = nx.DiGraph() # Empty graph or irrelevant graph
    mock_kg.add_node("ent_other_org", label="Other Corp", type="ORG")
    mock_content_analyzer.analyze_content.return_value = (None, mock_kg)

    analyze_cmd = "!analyze: Some other unrelated text."
    await dm.get_simple_response(analyze_cmd, session_id, user_id)

    # Reset mock call count before the query that should go to LLM
    mock_llm_interface.generate_response.reset_mock()

    q1 = "who is ceo of Innovate Corp?" # Innovate Corp not in this session's KG
    r1 = await dm.get_simple_response(q1, session_id, user_id)

    # Expect fallback to LLM
    mock_llm_interface.generate_response.assert_called_once()
    expected_r1_fallback = f"{mock_personality_manager.get_current_personality_trait.return_value}: {mock_llm_interface.generate_response.return_value}"
    assert r1 == expected_r1_fallback

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_kg_qa_fallback_if_no_kg_for_session(dialogue_manager_helper_fixture):
    dm, _, mock_llm_interface, mock_personality_manager, _, _, _, _ = dialogue_manager_helper_fixture
    session_id = "kg_integ_test_session_03" # No !analyze for this session
    user_id = "kg_integ_test_user_03"

    mock_llm_interface.generate_response.reset_mock()

    q1 = "who is ceo of Innovate Corp?"
    r1 = await dm.get_simple_response(q1, session_id, user_id)

    # Expect fallback to LLM
    mock_llm_interface.generate_response.assert_called_once()
    expected_r1_fallback = f"{mock_personality_manager.get_current_personality_trait.return_value}: {mock_llm_interface.generate_response.return_value}"
    assert r1 == expected_r1_fallback

@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒超時
async def test_kg_qa_no_answer_from_kg_then_fallback(dialogue_manager_helper_fixture):
    dm, _, mock_llm_interface, mock_personality_manager, mock_content_analyzer, _, _, _ = await dialogue_manager_helper_fixture
    session_id = "kg_integ_test_session_04"
    user_id = "kg_integ_test_user_04"

    mock_kg = nx.DiGraph()
    mock_kg.add_node("ent_innovate_corp_org", label="Innovate Corp", type="ORG")
    # No CEO relationship for Innovate Corp in this KG
    mock_content_analyzer.analyze_content.return_value = (None, mock_kg)

    analyze_cmd = "!analyze: Innovate Corp is a company."
    await dm.get_simple_response(analyze_cmd, session_id, user_id)

    mock_llm_interface.generate_response.reset_mock()

    q1 = "who is ceo of Innovate Corp?" # KG has Innovate Corp, but not its CEO
    r1 = await dm.get_simple_response(q1, session_id, user_id)

    mock_llm_interface.generate_response.assert_called_once()
    expected_r1_fallback = f"{mock_personality_manager.get_current_personality_trait.return_value}: {mock_llm_interface.generate_response.return_value}"
    assert r1 == expected_r1_fallback

# Tool Drafting Tests
@pytest.fixture(scope="function")
async def dialogue_manager_tool_drafting_fixture():
    mock_personality_manager = MagicMock()
    mock_personality_manager.get_current_personality_trait.return_value = "TestDraftAI"
    mock_llm_interface = MagicMock()

    test_config: OperationalConfig = { # type: ignore
        "operational_configs": {
            "timeouts": {"dialogue_manager_turn": 120},
            "learning_thresholds": {"min_critique_score_to_store": 0.0}
        }
    }

    patchers = {
        'PersonalityManager': patch('src.core_ai.dialogue.dialogue_manager.PersonalityManager', return_value=mock_personality_manager),
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
    mocks = {name: patcher.start() for name, patcher in patchers.items()}
    # No need for addCleanup with pytest fixtures, teardown is handled by fixture scope

    dm = DialogueManager(
        llm_interface=mock_llm_interface,
        personality_manager=mock_personality_manager,
        config=test_config
    )
    dm.personality_manager = mock_personality_manager # Ensure the mock is used

    yield dm, mock_llm_interface, mocks

    # Teardown for mocks (if not handled by pytest's default patching behavior)
    for patcher in patchers.values():
        patcher.stop()

@pytest.mark.asyncio
async def test_handle_draft_tool_request_success_flow(dialogue_manager_tool_drafting_fixture):
    dm, mock_llm_interface, mocks = dialogue_manager_tool_drafting_fixture
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
    mocks['SandboxExecutor'].return_value.run.return_value = ("Mocked sandbox success", None)


    mock_llm_interface.generate_response.side_effect = [
        mock_io_details_json_str,
        mock_generated_code
    ]

    result_response = await dm.handle_draft_tool_request(tool_name, purpose_and_io_desc)

    assert mock_llm_interface.generate_response.call_count == 2

    io_parsing_call_args = mock_llm_interface.generate_response.call_args_list[0]
    io_parsing_prompt_arg = io_parsing_call_args[1]['prompt']
    assert "You are an expert Python code analyst." in io_parsing_prompt_arg
    assert purpose_and_io_desc in io_parsing_prompt_arg
    assert io_parsing_call_args[1]['params'] == {"temperature": 0.1}

    code_gen_call_args = mock_llm_interface.generate_response.call_args_list[1]
    code_gen_prompt_arg = code_gen_call_args[1]['prompt']
    assert f"Tool Class Name: {tool_name}" in code_gen_prompt_arg
    assert "class_docstring_hint\": \"An echo tool.\"" in mock_io_details_json_str
    assert "Method Name: echo" in code_gen_prompt_arg
    assert "message: str" in code_gen_prompt_arg
    assert "Return Type: str" in code_gen_prompt_arg
    assert code_gen_call_args[1]['params'] == {"temperature": 0.3}

    assert f"Okay, I've drafted a Python skeleton for a tool named `{tool_name}`" in result_response
    assert mock_generated_code in result_response
    assert "Info: The drafted code is syntactically valid Python." in result_response

    mocks['SandboxExecutor'].return_value.run.assert_called_once()
    assert "---Sandbox Test Run---" in result_response
    assert "Execution Result: Mocked sandbox success" in result_response


@pytest.mark.asyncio
async def test_handle_draft_tool_request_code_syntax_error(dialogue_manager_tool_drafting_fixture):
    dm, mock_llm_interface, mocks = dialogue_manager_tool_drafting_fixture
    tool_name = "SyntaxErrorTool"
    purpose_and_io_desc = "A tool that will have a syntax error."

    mock_io_details: ParsedToolIODetails = {"suggested_method_name": "broken", "class_docstring_hint":"d","method_docstring_hint":"d","parameters":[],"return_type":"Any","return_description":"d"} # type: ignore
    mock_io_details_json_str = json.dumps(mock_io_details)
    mock_generated_code_with_error = "class SyntaxErrorTool:\n def broken(self):\n  print 'oops'"

    mock_llm_interface.generate_response.side_effect = [
        mock_io_details_json_str,
        mock_generated_code_with_error
    ]

    result_response = await dm.handle_draft_tool_request(tool_name, purpose_and_io_desc)

    assert mock_llm_interface.generate_response.call_count == 2
    assert f"Okay, I've drafted a Python skeleton for a tool named `{tool_name}`" in result_response
    assert mock_generated_code_with_error in result_response
    assert "Warning: The drafted code has a syntax error" in result_response
    assert "line 3" in result_response

    mocks['SandboxExecutor'].return_value.run.assert_not_called()


@pytest.mark.asyncio
async def test_handle_draft_tool_request_sandbox_execution_error(dialogue_manager_tool_drafting_fixture):
    dm, mock_llm_interface, mocks = dialogue_manager_tool_drafting_fixture
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

    mock_llm_interface.generate_response.side_effect = [
        mock_io_details_json_str,
        mock_valid_code
    ]

    mocks['SandboxExecutor'].return_value.run.return_value = (None, "ValueError: Sandbox test error")

    result_response = await dm.handle_draft_tool_request(tool_name, purpose_and_io_desc)

    assert mock_llm_interface.generate_response.call_count == 2
    mocks['SandboxExecutor'].return_value.run.assert_called_once()
    assert "Info: The drafted code is syntactically valid Python." in result_response
    assert "---Sandbox Test Run---" in result_response
    assert "Execution Error: ValueError: Sandbox test error" in result_response


@pytest.mark.asyncio
async def test_handle_draft_tool_request_io_parsing_json_error(dialogue_manager_tool_drafting_fixture):
    dm, mock_llm_interface, _ = dialogue_manager_tool_drafting_fixture
    tool_name = "BadJsonTool"
    purpose_and_io_desc = "This will cause a JSON error."

    mock_llm_interface.generate_response.return_value = "This is not valid JSON {oops"

    result_response = await dm.handle_draft_tool_request(tool_name, purpose_and_io_desc)

    mock_llm_interface.generate_response.assert_called_once()
    assert f"I had trouble understanding the specific parameters and return types from your description for '{tool_name}'." in result_response

@pytest.mark.asyncio
async def test_handle_draft_tool_request_io_parsing_value_error(dialogue_manager_tool_drafting_fixture):
    dm, mock_llm_interface, _ = dialogue_manager_tool_drafting_fixture
    tool_name = "ValueErrorTool"
    purpose_and_io_desc = "This will cause a value error if JSON is empty after extraction."

    mock_llm_interface.generate_response.return_value = "```json\n\n```"

    result_response = await dm.handle_draft_tool_request(tool_name, purpose_and_io_desc)

    mock_llm_interface.generate_response.assert_called_once()
    assert f"I encountered an issue trying to structure the details for '{tool_name}'. Please try rephrasing your request." in result_response

@pytest.mark.asyncio
async def test_handle_draft_tool_request_io_details_missing_keys_fallback(dialogue_manager_tool_drafting_fixture):
    dm, mock_llm_interface, mocks = dialogue_manager_tool_drafting_fixture
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
    mocks['SandboxExecutor'].return_value.run.return_value = ("Partial sandbox success", None)


    mock_llm_interface.generate_response.side_effect = [
        mock_io_details_partial_json_str,
        mock_generated_code
    ]

    result_response = await dm.handle_draft_tool_request(tool_name, purpose_and_io_desc)
    assert mock_llm_interface.generate_response.call_count == 2

    code_gen_call_args = mock_llm_interface.generate_response.call_args_list[1]
    code_gen_prompt_arg = code_gen_call_args[1]['prompt']
    assert f"Class Docstring: {purpose_and_io_desc}" in code_gen_prompt_arg
    assert "Method Name: do_partial_stuff" in code_gen_prompt_arg
    assert "Return Type: Any" in code_gen_prompt_arg

    assert f"Okay, I've drafted a Python skeleton for a tool named `{tool_name}`" in result_response

@pytest.mark.asyncio
async def test_low_critique_score_triggers_repair(dialogue_manager_helper_fixture):
    dm, _, _, _, _, _, mock_self_critique_module, _ = await dialogue_manager_helper_fixture
    session_id = "repair_test_session"
    user_id = "repair_test_user"
    user_input = "This is a test input."
    initial_response = "This is a bad response."
    repaired_response = "This is a better response."

    dm.llm_interface.generate_response.return_value = initial_response
    mock_self_critique_module.critique_interaction.return_value = CritiqueResult(
        score=0.2,
        reason="The response was bad.",
        suggested_alternative=repaired_response
    )

    final_response = await dm.get_simple_response(user_input, session_id, user_id)

    assert final_response == repaired_response
