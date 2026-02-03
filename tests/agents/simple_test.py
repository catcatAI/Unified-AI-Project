"""
Simple agent test to verify imports and basic instantiation.
"""

import pytest
from apps.backend.src.ai.agents.base.base_agent import BaseAgent

def test_simple_agent_creation():
    """Tests if a BaseAgent can be imported and instantiated."""
    try:
        agent = BaseAgent(
            agent_id="test_agent_123",
            agent_name="TestAgent",
            capabilities=[{
                "capability_id": "test_capability_1",
                "name": "Test Capability",
                "description": "A test capability",
                "version": "1.0"
            }]
        )
        assert agent.agent_id == "test_agent_123"
        assert agent.agent_name == "TestAgent"
    except Exception as e:
        pytest.fail(f"Failed to create BaseAgent: {e}")
