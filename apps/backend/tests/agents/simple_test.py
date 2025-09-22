import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_simple():
    """Simple test to verify imports work."""
    try:
        from apps.backend.src.ai.agents.base_agent import BaseAgent
        print("BaseAgent imported successfully")
        
        # Create a simple agent instance
        agent = BaseAgent(
            agent_id="test_agent_123",
            capabilities=[{
                "capability_id": "test_capability_1",
                "name": "Test Capability",
                "description": "A test capability",
                "version": "1.0"
            }],
            agent_name="TestAgent"
        )
        
        print(f"Agent created: {agent.agent_id}")
        print("All tests passed!")
        return True
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple()
    if not success:
        exit(1)