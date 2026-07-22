"""
Test script for BootstrapManager
"""

from core.system.bootstrap import get_bootstrap_manager


def test_bootstrap() -> None:
    """Test bootstrap behavior."""
    print("Testing BootstrapManager...")
    manager = get_bootstrap_manager()
    state = manager.run_full_bootstrap()

    print("\n[Bootstrap State]")
    print(f"OS: {state['environment']['os']}")
    print(f"Python: {state['environment']['python']}")
    print(f"Hardware Tier: {state['hardware']['performance_tier']}")
    print(f"GPU: {state['hardware']['gpu']}")
    print(f"Max FPS: {state['performance'].get('max_fps', 'N/A')}")
    print(f"LLM Model: {state['performance'].get('llm_model', 'N/A')}")

    assert "hardware" in state
    assert "environment" in state
    assert "performance" in state
    print("\n✅ Bootstrap test passed!")


