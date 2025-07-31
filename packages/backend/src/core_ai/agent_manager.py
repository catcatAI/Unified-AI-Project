import subprocess
import sys
import os
from typing import Dict, Optional, List

class AgentManager:
    """
    Manages the lifecycle of specialized sub-agents.
    It can launch and terminate sub-agent processes.
    """
    def __init__(self, python_executable: str):
        """
        Initializes the AgentManager.

        Args:
            python_executable (str): The absolute path to the python executable
                                     to be used for launching sub-agents.
        """
        self.python_executable = python_executable
        self.active_agents: Dict[str, subprocess.Popen] = {}
        self.agent_script_map: Dict[str, str] = self._discover_agent_scripts()

        print(f"AgentManager initialized. Found agent scripts: {list(self.agent_script_map.keys())}")

    def _discover_agent_scripts(self) -> Dict[str, str]:
        """
        Discovers available agent scripts in the 'src/agents' directory.
        Returns a map of agent names to their script paths.
        """
        agent_map = {}
        try:
            agents_dir = os.path.join(os.path.dirname(__file__), '..', 'agents')
            if not os.path.isdir(agents_dir):
                return {}

            for filename in os.listdir(agents_dir):
                if filename.endswith("_agent.py") and filename != "base_agent.py":
                    agent_name = filename.replace(".py", "")
                    agent_map[agent_name] = os.path.join(agents_dir, filename)
            return agent_map
        except FileNotFoundError:
            return {}

    def launch_agent(self, agent_name: str, args: Optional[List[str]] = None) -> Optional[str]:
        """
        Launches a sub-agent in a new process.

        Args:
            agent_name (str): The name of the agent to launch (e.g., 'data_analysis_agent').
            args (Optional[List[str]]): A list of command-line arguments to pass to the agent script.

        Returns:
            Optional[str]: The agent's process ID (PID) as a string if successful, else None.
        """
        if agent_name not in self.agent_script_map:
            print(f"[AgentManager] Error: Agent '{agent_name}' not found.")
            return None

        if agent_name in self.active_agents and self.active_agents[agent_name].poll() is None:
            print(f"[AgentManager] Info: Agent '{agent_name}' is already running with PID {self.active_agents[agent_name].pid}.")
            return str(self.active_agents[agent_name].pid)

        script_path = self.agent_script_map[agent_name]
        command = [self.python_executable, script_path]
        if args:
            command.extend(args)

        try:
            print(f"[AgentManager] Launching '{agent_name}' with command: {' '.join(command)}")
            # Using Popen to run the agent as a non-blocking background process
            process = subprocess.Popen(command)
            self.active_agents[agent_name] = process
            print(f"[AgentManager] Successfully launched '{agent_name}' with PID {process.pid}.")
            return str(process.pid)
        except Exception as e:
            print(f"[AgentManager] Failed to launch agent '{agent_name}': {e}")
            return None

    def check_agent_health(self, agent_name: str) -> bool:
        """
        Checks if an agent is healthy.
        This is a placeholder for a more robust health check mechanism.
        """
        if agent_name in self.active_agents and self.active_agents[agent_name].poll() is None:
            # In a real implementation, this would involve sending a health check
            # message to the agent and waiting for a response.
            return True
        return False

    def shutdown_agent(self, agent_name: str) -> bool:
        """
        Terminates a running sub-agent process.

        Args:
            agent_name (str): The name of the agent to shut down.

        Returns:
            bool: True if the agent was terminated successfully, False otherwise.
        """
        if agent_name in self.active_agents and self.active_agents[agent_name].poll() is None:
            process = self.active_agents[agent_name]
            print(f"[AgentManager] Shutting down '{agent_name}' (PID: {process.pid})...")
            process.terminate() # Sends SIGTERM
            try:
                process.wait(timeout=5) # Wait for the process to terminate
                print(f"[AgentManager] Agent '{agent_name}' terminated.")
            except subprocess.TimeoutExpired:
                print(f"[AgentManager] Agent '{agent_name}' did not terminate gracefully, killing.")
                process.kill() # Sends SIGKILL
            del self.active_agents[agent_name]
            return True
        else:
            print(f"[AgentManager] Agent '{agent_name}' not found or not running.")
            return False

    def shutdown_all_agents(self):
        """
        Shuts down all active sub-agent processes managed by this manager.
        """
        print("[AgentManager] Shutting down all active agents...")
        # Create a copy of keys to iterate over, as the dictionary will be modified
        for agent_name in list(self.active_agents.keys()):
            self.shutdown_agent(agent_name)

    async def wait_for_agent_ready(self, agent_name: str, timeout: int = 10):
        """
        Waits for an agent to be ready by checking for its capability advertisement.
        This is a placeholder for a more robust solution.
        """
        from src.core_services import get_services
        service_discovery = get_services().get("service_discovery")
        if not service_discovery:
            print("[AgentManager] Error: ServiceDiscoveryModule not available.")
            return

        for _ in range(timeout):
            capabilities = service_discovery.get_all_capabilities()
            for cap in capabilities:
                if agent_name in cap.get("capability_id", ""):
                    print(f"[AgentManager] Agent '{agent_name}' is ready.")
                    return
            await asyncio.sleep(1)
        print(f"[AgentManager] Warning: Timed out waiting for agent '{agent_name}' to be ready.")

if __name__ == '__main__':
    # A simple test for the AgentManager
    print("--- AgentManager Test ---")

    # In a real scenario, the python_executable would be read from a config
    # that the installer script creates.
    python_exec_path = sys.executable

    manager = AgentManager(python_executable=python_exec_path)

    print("\n1. Launching data_analysis_agent:")
    pid = manager.launch_agent("data_analysis_agent")
    assert pid is not None

    print("\n2. Trying to launch it again (should report it's running):")
    manager.launch_agent("data_analysis_agent")

    print("\n3. Waiting for 5 seconds...")
    import time
    time.sleep(5)

    print("\n4. Shutting down data_analysis_agent:")
    success = manager.shutdown_agent("data_analysis_agent")
    assert success is True

    print("\n5. Trying to shut it down again (should report not running):")
    manager.shutdown_agent("data_analysis_agent")

    print("\n--- AgentManager Test Complete ---")
