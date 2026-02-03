import pytest
import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Configure logging for the module
logger = logging.getLogger(__name__)

# Add project paths for module discovery
project_root = Path(__file__).resolve().parents[2] # Go up to D:\Projects\Unified-AI-Project
backend_path = project_root / "apps" / "backend"
src_path = backend_path / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(src_path))

# Import necessary components for the stress test
from apps.backend.src.services.llm_service.model_manager import LLMManager, MODEL_PROVIDER_MAP
from apps.backend.src.services.llm_service.base_provider import BaseLLMProvider, LLMResponse

# Mark all tests in this file as part of the 'performance' benchmark group
pytestmark = pytest.mark.benchmark(group="performance")

class MockBenchmarkLLMProvider(BaseLLMProvider):
    """A mock provider that simulates a fast LLM response for benchmarking."""
    @property
    def provider_name(self) -> str:
        return "mock_benchmark_provider"

    async def generate(self, model: str, prompt: str, **kwargs: Any) -> LLMResponse:
        # Simulate a tiny I/O delay, e.g., internal queuing or processing
        await asyncio.sleep(0.001) 
        return LLMResponse(
            text="This is a benchmark response.",
            model_name=model,
            provider_name=self.provider_name
        )

@pytest.fixture(scope="module")
def stress_llm_manager():
    """
    Pytest fixture to set up an LLMManager instance for stress testing.
    It's scoped to the module to avoid re-initializing on every test function.
    """
    # Create a manager instance for the test module
    manager = LLMManager()
    
    # Register our mock provider
    manager.register_provider("mock_benchmark_provider", MockBenchmarkLLMProvider())
    
    # Add a route in the map for our mock model to use the mock provider
    MODEL_PROVIDER_MAP["stress-model"] = "mock_benchmark_provider"
    
    return manager

@pytest.mark.asyncio
async def test_stress_llm_generate_concurrent(benchmark, stress_llm_manager: LLMManager):
    """
    Benchmarks the LLMManager under concurrent load using the mock provider.
    This simulates multiple simultaneous requests to the LLM service.
    """
    num_concurrent_tasks = 100
    num_requests_per_task = 10

    async def make_requests():
        tasks = [
            stress_llm_manager.generate(model="stress-model", prompt=f"stress test prompt {i}")
            for i in range(num_requests_per_task)
        ]
        await asyncio.gather(*tasks)

    async def run_concurrent_stress():
        concurrent_tasks = [make_requests() for _ in range(num_concurrent_tasks)]
        await asyncio.gather(*concurrent_tasks)

    # Use benchmark.pedantic for async functions
    # The setup function returns the coroutine, and benchmark.pedantic will await it.
    benchmark.pedantic(run_concurrent_stress, setup=lambda: None, rounds=1, iterations=1)

if __name__ == "__main__":
    logger.info("Executing stress_test.py directly (placeholder).")
    pytest.main([__file__])