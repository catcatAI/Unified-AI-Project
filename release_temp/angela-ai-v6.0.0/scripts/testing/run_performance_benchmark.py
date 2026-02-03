import asyncio
import logging
import time
from typing import List

# Configure logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Imports from the project ---
from apps.backend.src.ai.agent_manager import AgentManager
from apps.backend.src.ai.agents.conversational_agent import ConversationalAgent

# --- Benchmark Configuration ---
NUM_AGENTS = 5
NUM_TASKS_PER_AGENT = 4
TOTAL_TASKS = NUM_AGENTS * NUM_TASKS_PER_AGENT
MODEL_TO_TEST = "distilgpt2" # Use the small, local model for a consistent CPU-bound benchmark

async def main():
    """
    Main function to establish a performance benchmark for the agent and LLM systems.
    """
    logging.info("--- Starting Performance Benchmark Establishment ---")
    logging.info(f"Configuration: {NUM_AGENTS} agents, {NUM_TASKS_PER_AGENT} tasks per agent, {TOTAL_TASKS} total tasks.")
    logging.info(f"Model under test: '{MODEL_TO_TEST}'")

    manager = AgentManager()
    manager.register_agent_type("ConversationalAgent", ConversationalAgent)

    # 1. Launch Agents
    logging.info("Launching agent pool...")
    agents: List[ConversationalAgent] = []
    for i in range(NUM_AGENTS):
        agent = await manager.launch_agent("ConversationalAgent", name=f"BenchmarkAgent-{i}")
        if agent:
            agents.append(agent)

    if len(agents) != NUM_AGENTS:
        logging.error("FAILED: Not all agents launched successfully. Aborting benchmark.")
        return

    # Give agents a moment to start
    await asyncio.sleep(0.1)
    
    # 2. Submit tasks and start timer
    logging.info("Submitting task burst...")
    start_time = time.perf_counter()

    tasks = []
    for agent in agents:
        # --- Monkey-patch the handle_task method ONCE per agent ---
        # We need a way to know when a task is done. We'll modify the agent's handle_task
        # for this benchmark to set the result on the future.
        original_handle_task = agent.handle_task
        
        async def handle_task_with_future(task, original_task_func=original_handle_task, *args, **kwargs):
            result = await original_task_func(task, *args, **kwargs)
            if 'completion_future' in task and not task['completion_future'].done():
                task['completion_future'].set_result(result)
            return result

        agent.handle_task = handle_task_with_future
        # --- End of monkey-patching ---

        for i in range(NUM_TASKS_PER_AGENT):
            task_payload = {
                "user_input": f"Write a short story about a robot, task #{i+1}.",
                # Use a custom property to track completion
                "completion_future": asyncio.Future()
            }
            tasks.append(task_payload['completion_future'])
            await agent.submit_task(task_payload)

    # 3. Wait for all tasks to complete
    logging.info("All tasks submitted. Waiting for completion...")
    await asyncio.gather(*tasks)
    
    end_time = time.perf_counter()
    logging.info("All tasks completed.")

    # 4. Calculate and report metrics
    total_time = end_time - start_time
    tasks_per_second = TOTAL_TASKS / total_time if total_time > 0 else float('inf')
    avg_time_per_task = total_time / TOTAL_TASKS if TOTAL_TASKS > 0 else 0

    logging.info("\n--- Performance Benchmark Results ---")
    logging.info(f"Total Tasks Completed: {TOTAL_TASKS}")
    logging.info(f"Total Time Elapsed:    {total_time:.4f} seconds")
    logging.info(f"Tasks Per Second:      {tasks_per_second:.4f} tasks/sec")
    logging.info(f"Average Time Per Task: {avg_time_per_task:.4f} sec/task")
    logging.info("-------------------------------------\n")
    logging.info("This is the initial performance benchmark. It can be used as a baseline for future optimizations.")

    # 5. Cleanup
    logging.info("Stopping all agents...")
    for agent in agents:
        await manager.stop_agent(agent.agent_id)
    
    logging.info("--- Performance Benchmark Finished ---")


if __name__ == "__main__":
    # This is a CPU-intensive benchmark, it may take a while.
    asyncio.run(main())
