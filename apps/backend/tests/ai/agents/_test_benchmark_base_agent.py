import pytest
import asyncio
from ai.agents.base_agent import BaseAgent
from typing import Any, Dict

# A concrete implementation of BaseAgent for benchmarking
class BenchmarkAgent(BaseAgent):
    async def perceive(self, task: Dict[str, Any]) -> Any:
        await asyncio.sleep(0.001) # Simulate some work
        return {"perceived_data": "benchmark_data"}

    async def decide(self, perceived_info: Any) -> Dict[str, Any]:
        await asyncio.sleep(0.001) # Simulate some work
        return {"action_type": "benchmark_action"}

    async def act(self, decision: Dict[str, Any]) -> Any:
        await asyncio.sleep(0.002) # Simulate some work
        return {"action_status": "success"}

    async def feedback(self, original_task: Dict[str, Any], action_result: Any) -> None:
        await asyncio.sleep(0.001) # Simulate some work
        pass

@pytest.fixture
def benchmark_agent():
    """Fixture to provide a BenchmarkAgent instance."""
    return BenchmarkAgent(name="BenchmarkAgent")

@pytest.mark.asyncio
async def test_base_agent_handle_task_benchmark(benchmark_agent: BenchmarkAgent, benchmark):
    """
    Benchmark the handle_task method of the BaseAgent.
    """
    task_data = {"type": "benchmark_task", "data": "sample"}
    benchmark.pedantic(benchmark_agent.handle_task, args=(task_data,), rounds=10, iterations=1)
