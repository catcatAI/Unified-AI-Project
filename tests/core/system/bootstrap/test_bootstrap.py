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
    print(f"Max FPS: {state['performance']['max_fps']}")
    print(f"LLM Model: {state['performance']['llm_model']}")

    assert "hardware" in state
    assert "environment" in state
    assert "performance" in state
    print("\n✅ Bootstrap test passed!")


if __name__ == "__main__":
    test_bootstrap()
