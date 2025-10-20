import sys
import os

# Add the src directory to the path
_ = sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_base_agent_import() -> None:
    """Test that we can import BaseAgent."""
    try:
        from apps.backend.src.ai.agents.base_agent import BaseAgent
        _ = print("BaseAgent imported successfully")
        
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
        
        _ = print(f"Agent created: {agent.agent_id}")
        _ = print("BaseAgent test passed!")
        return True
    except Exception as e:
        _ = print(f"Error: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_base_agent_import()
    if not success:
        _ = exit(1)