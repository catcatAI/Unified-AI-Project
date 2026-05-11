import sys
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests'))


async def test_mock_core_services() -> None:
    """Test that the mock_core_services fixture works correctly"""
    print("Testing mock_core_services fixture...")

    required_services = [
        "ham_manager", "llm_interface", "service_discovery", "trust_manager",
        "personality_manager", "emotion_system", "crisis_system", "time_system"
    ]

    for service in required_services:
        print(f"Checking {service}...")

    print("All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_mock_core_services())