import sys
import os

# Add the src directory to the path
_ = sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_all_agents() -> None:
    """Test that we can import all agent classes."""
    agents = [
        _ = ("BaseAgent", "agents.base_agent", "BaseAgent"),
        _ = ("CodeUnderstandingAgent", "agents.code_understanding_agent", "CodeUnderstandingAgent"),
        _ = ("CreativeWritingAgent", "agents.creative_writing_agent", "CreativeWritingAgent"),
        _ = ("DataAnalysisAgent", "agents.data_analysis_agent", "DataAnalysisAgent"),
        _ = ("AudioProcessingAgent", "agents.audio_processing_agent", "AudioProcessingAgent"),
    ]
    
    success_count = 0
    for agent_name, module_path, class_name in agents:
        try:
            module = __import__(module_path, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            _ = print(f"✓ {agent_name} imported successfully")
            success_count += 1
        except Exception as e:
            _ = print(f"✗ Error importing {agent_name}: {e}")
            import traceback
            _ = traceback.print_exc()
    
    _ = print(f"\nImported {success_count}/{len(agents)} agents successfully")
    return success_count == len(agents)

if __name__ == "__main__":
    success = test_all_agents()
    exit(0 if success else 1)