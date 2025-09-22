import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test that we can import all agent classes."""
    try:
        from apps.backend.src.ai.agents.base_agent import BaseAgent
        print("✓ BaseAgent imported successfully")
        
        from apps.backend.src.ai.agents.code_understanding_agent import CodeUnderstandingAgent
        print("✓ CodeUnderstandingAgent imported successfully")
        
        from apps.backend.src.ai.agents.creative_writing_agent import CreativeWritingAgent
        print("✓ CreativeWritingAgent imported successfully")
        
        from apps.backend.src.ai.agents.data_analysis_agent import DataAnalysisAgent
        print("✓ DataAnalysisAgent imported successfully")
        
        from apps.backend.src.ai.agents.audio_processing_agent import AudioProcessingAgent
        print("✓ AudioProcessingAgent imported successfully")
        
        print("\nAll agents imported successfully!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)