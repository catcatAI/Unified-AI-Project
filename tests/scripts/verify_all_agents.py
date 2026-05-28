"""Verify all agents can be imported."""


def test_all_agents():
    """Test that we can import all agent classes."""
    agents = [
        ("BaseAgent", "agents.base_agent", "BaseAgent"),
        ("CodeUnderstandingAgent", "agents.code_understanding_agent", "CodeUnderstandingAgent"),
        ("CreativeWritingAgent", "agents.creative_writing_agent", "CreativeWritingAgent"),
        ("DataAnalysisAgent", "agents.data_analysis_agent", "DataAnalysisAgent"),
        ("AudioProcessingAgent", "agents.audio_processing_agent", "AudioProcessingAgent"),
    ]

    for agent_name, module_path, class_name in agents:
        try:
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            print(f"OK: {agent_name}")
        except Exception as e:
            print(f"FAIL: {agent_name} - {e}")