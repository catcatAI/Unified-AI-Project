import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from typing import Any, Dict, List, Optional

from ai.agents.tool_using_agent import ToolUsingAgent
from apps.backend.src.services.llm_service.model_manager import LLMResponse

# Mock service managers
@pytest.fixture
def mock_llm_manager():
    with patch('ai.agents.tool_using_agent.llm_manager') as mock:
        mock.generate = AsyncMock(return_value=LLMResponse(text="Mock LLM response", model_name="mock-llm", usage={}, provider_name="mock"))
        yield mock

@pytest.fixture
def mock_search_manager():
    with patch('ai.agents.tool_using_agent.search_manager') as mock:
        mock.search = AsyncMock(return_value=[{"title": "Mock Search", "url": "http://mock.com", "snippet": "Mock snippet"}])
        yield mock

@pytest.fixture
def mock_image_manager():
    with patch('ai.agents.tool_using_agent.image_manager') as mock:
        mock.generate_image = AsyncMock(return_value="http://mockimage.com/image.png")
        yield mock

@pytest.fixture
def mock_code_analysis_manager():
    with patch('ai.agents.tool_using_agent.code_analysis_manager') as mock:
        mock.analyze_code = AsyncMock(return_value={"explanation": "Mock explanation"})
        yield mock

@pytest.fixture
def mock_data_analysis_manager():
    with patch('ai.agents.tool_using_agent.data_analysis_manager') as mock:
        mock.analyze_data = AsyncMock(return_value={"summary": "Mock summary"})
        yield mock

@pytest.fixture
def mock_nlp_manager():
    with patch('ai.agents.tool_using_agent.nlp_manager') as mock:
        mock.process_text = AsyncMock(return_value={"sentiment": "positive"})
        yield mock

@pytest.fixture
def mock_vision_manager():
    with patch('ai.agents.tool_using_agent.vision_manager') as mock:
        mock.process_image = AsyncMock(return_value={"detected_objects": ["mock_object"]})
        yield mock

@pytest.fixture
def mock_audio_manager():
    with patch('ai.agents.tool_using_agent.audio_manager') as mock:
        mock.process_audio = AsyncMock(return_value={"transcribed_text": "Mock transcription"})
        yield mock

@pytest.fixture
def mock_planning_manager():
    with patch('ai.agents.tool_using_agent.planning_manager') as mock:
        mock.generate_plan = AsyncMock(return_value={"plan_id": "mock_plan", "steps": ["mock_step"]})
        yield mock

@pytest.fixture
def tool_using_agent_instance():
    """Fixture to provide a fresh ToolUsingAgent instance for each test."""
    return ToolUsingAgent(name="TestOrchestrator")

@pytest.mark.asyncio
async def test_tool_using_agent_init(tool_using_agent_instance):
    """Test that ToolUsingAgent initializes correctly."""
    assert isinstance(tool_using_agent_instance, ToolUsingAgent)
    assert tool_using_agent_instance.name == "TestOrchestrator"

@pytest.mark.asyncio
async def test_tool_using_agent_perceive(tool_using_agent_instance):
    """Test the perceive method."""
    task = {"tool": "llm", "parameters": {"prompt": "test"}}
    perceived_info = await tool_using_agent_instance.perceive(task, [], {})
    assert perceived_info["tool_name"] == "llm"
    assert perceived_info["tool_parameters"]["prompt"] == "test"

@pytest.mark.asyncio
async def test_tool_using_agent_decide_use_tool(tool_using_agent_instance):
    """Test the decide method when a tool is specified."""
    perceived_info = {"tool_name": "search", "tool_parameters": {"query": "test"}}
    decision = await tool_using_agent_instance.decide(perceived_info)
    assert decision["action"] == "use_tool"
    assert decision["tool_name"] == "search"

@pytest.mark.asyncio
async def test_tool_using_agent_decide_no_tool(tool_using_agent_instance):
    """Test the decide method when no tool is specified."""
    perceived_info = {"tool_name": None}
    decision = await tool_using_agent_instance.decide(perceived_info)
    assert decision["action"] == "no_tool"

@pytest.mark.asyncio
async def test_tool_using_agent_act_llm(tool_using_agent_instance, mock_llm_manager):
    """Test the act method with LLM tool."""
    decision = {"action": "use_tool", "tool_name": "llm", "tool_parameters": {"prompt": "Hello"}}
    result = await tool_using_agent_instance.act(decision)
    mock_llm_manager.generate.assert_called_once_with(model="simulated-llm", prompt="Hello")
    assert result["tool_name"] == "llm"
    assert result["response"].text == "Mock LLM response"

@pytest.mark.asyncio
async def test_tool_using_agent_act_search(tool_using_agent_instance, mock_search_manager):
    """Test the act method with Search tool."""
    decision = {"action": "use_tool", "tool_name": "search", "tool_parameters": {"query": "test"}}
    result = await tool_using_agent_instance.act(decision)
    mock_search_manager.search.assert_called_once_with(query="test", num_results=3)
    assert result["tool_name"] == "search"
    assert result["response"][0]["title"] == "Mock Search"

@pytest.mark.asyncio
async def test_tool_using_agent_act_image_generation(tool_using_agent_instance, mock_image_manager):
    """Test the act method with Image Generation tool."""
    decision = {"action": "use_tool", "tool_name": "image_generation", "tool_parameters": {"prompt": "sunset"}}
    result = await tool_using_agent_instance.act(decision)
    mock_image_manager.generate_image.assert_called_once_with(prompt="sunset", style="photorealistic", size="512x512")
    assert result["tool_name"] == "image_generation"
    assert result["response"] == "http://mockimage.com/image.png"

@pytest.mark.asyncio
async def test_tool_using_agent_act_code_analysis(tool_using_agent_instance, mock_code_analysis_manager):
    """Test the act method with Code Analysis tool."""
    decision = {"action": "use_tool", "tool_name": "code_analysis", "tool_parameters": {"code": "def f(): pass"}}
    result = await tool_using_agent_instance.act(decision)
    mock_code_analysis_manager.analyze_code.assert_called_once_with(code="def f(): pass", request_type="explain", language="python")
    assert result["tool_name"] == "code_analysis"
    assert result["response"]["explanation"] == "Mock explanation"

@pytest.mark.asyncio
async def test_tool_using_agent_act_data_analysis(tool_using_agent_instance, mock_data_analysis_manager):
    """Test the act method with Data Analysis tool."""
    decision = {"action": "use_tool", "tool_name": "data_analysis", "tool_parameters": {"data": [{"a": 1}]}}
    result = await tool_using_agent_instance.act(decision)
    mock_data_analysis_manager.analyze_data.assert_called_once_with(data=[{"a": 1}], analysis_type="summary", parameters={})
    assert result["tool_name"] == "data_analysis"
    assert result["response"]["summary"] == "Mock summary"

@pytest.mark.asyncio
async def test_tool_using_agent_act_nlp_processing(tool_using_agent_instance, mock_nlp_manager):
    """Test the act method with NLP Processing tool."""
    decision = {"action": "use_tool", "tool_name": "nlp_processing", "tool_parameters": {"text": "text"}}
    result = await tool_using_agent_instance.act(decision)
    mock_nlp_manager.process_text.assert_called_once_with(text="text", processing_type="sentiment", parameters={})
    assert result["tool_name"] == "nlp_processing"
    assert result["response"]["sentiment"] == "positive"

@pytest.mark.asyncio
async def test_tool_using_agent_act_vision_processing(tool_using_agent_instance, mock_vision_manager):
    """Test the act method with Vision Processing tool."""
    decision = {"action": "use_tool", "tool_name": "vision_processing", "tool_parameters": {"image_source": "img.jpg"}}
    result = await tool_using_agent_instance.act(decision)
    mock_vision_manager.process_image.assert_called_once_with(image_source="img.jpg", processing_type="object_detection", parameters={})
    assert result["tool_name"] == "vision_processing"
    assert result["response"]["detected_objects"] == ["mock_object"]

@pytest.mark.asyncio
async def test_tool_using_agent_act_audio_processing(tool_using_agent_instance, mock_audio_manager):
    """Test the act method with Audio Processing tool."""
    decision = {"action": "use_tool", "tool_name": "audio_processing", "tool_parameters": {"audio_source": "audio.wav"}}
    result = await tool_using_agent_instance.act(decision)
    mock_audio_manager.process_audio.assert_called_once_with(audio_source="audio.wav", processing_type="speech_to_text", parameters={})
    assert result["tool_name"] == "audio_processing"
    assert result["response"]["transcribed_text"] == "Mock transcription"

@pytest.mark.asyncio
async def test_tool_using_agent_act_planning(tool_using_agent_instance, mock_planning_manager):
    """Test the act method with Planning tool."""
    decision = {"action": "use_tool", "tool_name": "planning", "tool_parameters": {"goal": "plan"}}
    result = await tool_using_agent_instance.act(decision)
    mock_planning_manager.generate_plan.assert_called_once_with(goal="plan", constraints=[], context="")
    assert result["tool_name"] == "planning"
    assert result["response"]["plan_id"] == "mock_plan"

@pytest.mark.asyncio
async def test_tool_using_agent_act_unknown_tool(tool_using_agent_instance):
    """Test the act method with an unknown tool."""
    decision = {"action": "use_tool", "tool_name": "unknown_tool", "tool_parameters": {}}
    result = await tool_using_agent_instance.act(decision)
    assert result["tool_name"] == "unknown_tool"
    assert "Simulated response for unknown tool 'unknown_tool'" in result["response"]

@pytest.mark.asyncio
async def test_tool_using_agent_feedback(tool_using_agent_instance):
    """Test the feedback method."""
    original_task = {"tool": "llm", "parameters": {"prompt": "test"}}
    action_result = {"tool_name": "llm", "response": "some response"}
    # Just ensure it runs without error
    await tool_using_agent_instance.feedback(original_task, action_result)
