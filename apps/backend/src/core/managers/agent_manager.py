import subprocess
import os
import logging
import threading
from typing import Dict, Optional, List
import asyncio

class AgentManager:
    """
    Manages the lifecycle of specialized sub-agents.
    It can launch and terminate sub-agent processes.
    """
    def __init__(self, python_executable: str, agents_dir: Optional[str] = None) -> None:
    """
    Initializes the AgentManager.

    Args:
            python_executable (str) The absolute path to the python executable
                                     to be used for launching sub-agents.:
    agents_dir (Optional[str]) The directory where agent scripts are located.
    """
    self.python_executable = python_executable
    self.active_agents: Dict[str, subprocess.Popen] =
    self.agent_script_map: Dict[str, str] = self._discover_agent_scripts(agents_dir)
    self.launch_lock = threading.Lock

    logging.info(f"AgentManager initialized. Found agent scripts: {list(self.agent_script_map.keys)}")

    def _discover_agent_scripts(self, agents_dir: Optional[str] = None) -> Dict[str, str]:
    """
    Discovers available agent scripts in the specified directory.
    Returns a map of agent names to their script paths.
    """
    agent_map =
        try:

            if not agents_dir:


    agents_dir = os.path.join(os.path.dirname(__file__), '..', 'agents')

            if not os.path.isdir(agents_dir)


    logging.warning(f"[AgentManager] Agents directory not found: {agents_dir}")
                return

            for filename in os.listdir(agents_dir)
    if filename.endswith("_agent.py") and filename != "base_agent.py":

    agent_name = filename.replace(".py", "")
                    agent_map[agent_name] = os.path.join(agents_dir, filename)
            logging.info(f"[AgentManager] Discovered agent scripts: {agent_map}")
            return agent_map
        except Exception as e:

            logging.error(f"[AgentManager] Error discovering agent scripts: {e}")
            return

    def launch_agent(self, agent_name: str, args: Optional[List[str]] = None) -> Optional[str]
    """
    Launches a sub-agent in a new process.

    Args:
            agent_name (str) The name of the agent to launch (e.g., 'data_analysis_agent').
            args (Optional[List[str]]) A list of command-line arguments to pass to the agent script.

    Returns:
            Optional[str]: The agent's process ID (PID) as a string if successful, else None.
    """
    with self.launch_lock:
    if agent_name not in self.agent_script_map:

    logging.error(f"[AgentManager] Error: Agent '{agent_name}' not found.")
                return None

            if agent_name in self.active_agents and self.active_agents[agent_name].poll is None:


    logging.info(f"[AgentManager] Info: Agent '{agent_name}' is already running with PID {self.active_agents[agent_name].pid}.")
    return str(self.active_agents[agent_name].pid)

            script_path = self.agent_script_map[agent_name]
    command = [self.python_executable, script_path]
        if args:

    command.extend(args)

        try:


            logging.info(f"[AgentManager] Launching '{agent_name}' with command: {' '.join(command)}")
            # Using Popen to run the agent as a non-blocking background process
            process = subprocess.Popen(command)
            self.active_agents[agent_name] = process
            logging.info(f"[AgentManager] Successfully launched '{agent_name}' with PID {process.pid}.")
    return str(process.pid)
        except Exception as e:

            logging.error(f"[AgentManager] Failed to launch agent '{agent_name}': {e}")
            return None

    def check_agent_health(self, agent_name: str) -> bool:
    """
        Checks if an agent is healthy.:
    This is a placeholder for a more robust health check mechanism.
    """
        if agent_name in self.active_agents and self.active_agents[agent_name].poll is None:
            # In a real implementation, this would involve sending a health check
            # message to the agent and waiting for a response.
    return True
    return False

    def shutdown_agent(self, agent_name: str) -> bool:
    """
    Terminates a running sub-agent process.

    Args:
            agent_name (str) The name of the agent to shut down.

    Returns: bool True if the agent was terminated successfully, False otherwise.
    """
        if agent_name in self.active_agents and self.active_agents[agent_name].poll is None:

    process = self.active_agents[agent_name]
            logging.info(f"[AgentManager] Shutting down '{agent_name}' (PID: {process.pid})...")
            process.terminate  # Sends SIGTERM
            try:

                process.wait(timeout=5)  # Wait for the process to terminate
    logging.info(f"[AgentManager] Agent '{agent_name}' terminated.")
            except subprocess.TimeoutExpired:

                logging.warning(f"[AgentManager] Agent '{agent_name}' did not terminate gracefully, killing.")
                process.kill  # Sends SIGKILL
            del self.active_agents[agent_name]
            return True
        else:

            logging.warning(f"[AgentManager] Agent '{agent_name}' not found or not running.")
            return False

    def shutdown_all_agents(self)
    """
    Shuts down all active sub-agent processes managed by this manager.
    """
    logging.info("[AgentManager] Shutting down all active agents...")
    # Create a copy of keys to iterate over, as the dictionary will be modified
        for agent_name in list(self.active_agents.keys)

    self.shutdown_agent(agent_name)

    async def wait_for_agent_ready(self, agent_name: str, timeout: int = 30, service_discovery=None)
    """
        Waits for an agent to be ready by checking for its capability advertisement.
    """
        print(f"DEBUG: AgentManager.wait_for_agent_ready called for agent: {agent_name}")
        logging.info(f"[AgentManager] wait_for_agent_ready called for agent: {agent_name}")

        if service_discovery is None:
            # 简单等待一段时间，模拟等待agent启动
            logging.warning("[AgentManager] wait_for_agent_ready is using placeholder sleep as no service_discovery provided.")
            await asyncio.sleep(2)
            logging.info(f"[AgentManager] Assuming agent '{agent_name}' is ready after waiting.")
            return

    # 获取期望的能力ID
    expected_capability_id = "data_analysis_v1"  # 简化处理，实际应该从代理配置中获取

    # 等待代理启动并广告其能力
    start_time = asyncio.get_event_loop.time
    retry_count = 0
    max_retries = timeout * 2  # 每0.5秒检查一次

        logging.info(f"[AgentManager] Waiting for agent '{agent_name}' to advertise capability '{expected_capability_id}'")

    while retry_count < max_retries:


    logging.debug(f"[AgentManager] Attempting to find capability '{expected_capability_id}' (attempt {retry_count+1}/{max_retries})")
            found_caps = await service_discovery.find_capabilities(capability_id_filter=expected_capability_id)
            logging.debug(f"[AgentManager] Found {len(found_caps)} capabilities matching ID filter '{expected_capability_id}'")
            if found_caps:

    logging.info(f"[AgentManager] Agent '{agent_name}' is ready. Found capability: {expected_capability_id}")
                return

            retry_count += 1
            logging.debug(f"[AgentManager] Still waiting for agent '{agent_name}'. Retry {retry_count}/{max_retries}")
    await asyncio.sleep(0.5)

    logging.warning(f"[AgentManager] Agent '{agent_name}' not ready within {timeout} seconds. Checking all capabilities...")

    # 如果特定能力没找到，检查所有能力
    all_caps = await service_discovery.get_all_capabilities_async
    logging.info(f"[AgentManager] All known capabilities: {len(all_caps)}")
        for cap in all_caps:

    logging.info(f"[AgentManager] Capability: {cap.get('capability_id')} from AI: {cap.get('ai_id')}")

    # Additional debugging
        logging.info(f"[AgentManager] Looking for capability ID: {expected_capability_id}")
    # Try to find capabilities by name as well
    found_caps_by_name = await service_discovery.find_capabilities(capability_name_filter=expected_capability_id)
    logging.info(f"[AgentManager] Found {len(found_caps_by_name)} capabilities by name filter")

    def get_available_agents(self) -> List[str]:
    """
    Returns a list of available agent names.
    """
    return list(self.agent_script_map.keys)

    def get_active_agents(self) -> Dict[str, int]:
    """
    Returns a dictionary of active agents and their PIDs.
    """
    active_agents =
        for agent_name, process in self.active_agents.items:

    if process.poll is None:  # Agent is still running
                active_agents[agent_name] = process.pid
    return active_agents