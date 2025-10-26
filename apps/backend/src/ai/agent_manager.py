"""
Agent Manager

Manages the lifecycle of specialized sub - agents, including launching,
terminating, and monitoring them.
"""

from tests.run_test_subprocess import
from system_test import
from diagnose_base_agent import
from tests.tools.test_tool_dispatcher_logging import
# TODO: Fix import - module 'threading' not found
from typing import Dict, Optional, List, Any
# TODO: Fix import - module 'asyncio' not found

logger = logging.getLogger(__name__)

class AgentManager:
    """
    Manages the lifecycle of specialized sub - agents.
    It can launch and terminate sub - agent processes.
    """

    def __init__(self, python_executable: Optional[str] = None,
    agents_dir: Optional[str] = None) -> None:
        """
        Initializes the AgentManager.

        Args:
            python_executable: Python executable path.
            agents_dir: The directory where agent scripts are located.
        """
        self.python_executable = python_executable or sys.executable
        self.agents: Dict[str, Any] = {}
        self.agent_factories: Dict[str, Any] = {}
        self.active_agents: Dict[str, subprocess.Popen[Any]] = {}
        self.agent_script_map: Dict[str, str] = self._discover_agent_scripts(agents_dir)
        self.launch_lock = threading.Lock()
        logger.info(f"AgentManager initialized. Found agent scripts: {list(self.agent_sc\
    \
    ript_map.keys())}")

    def register_agent_factory(self, agent_type: str, factory: Any):
        """注册代理工厂"""
        self.agent_factories[agent_type] = factory

    async def create_agent(self, agent_type: str, name: str):
        """创建代理"""
        if agent_type in self.agent_factories:
            return self.agent_factories[agent_type](name)
        return None

    async def add_agent(self, agent: Any) -> bool:
        """添加代理"""
        self.agents[agent.agent_id] = agent
        return True

    async def remove_agent(self, agent_id: str) -> bool:
        """移除代理"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False

    def get_agent(self, agent_id: str) -> Optional[Any]:
        """获取代理"""
        return self.agents.get(agent_id)

    async def start_agent(self, agent_id: str) -> bool:
        """启动代理"""
        agent = self.agents.get(agent_id)
        if agent:
            return await agent.start()
        return False

    async def stop_agent(self, agent_id: str) -> bool:
        """停止代理"""
        agent = self.agents.get(agent_id)
        if agent:
            return await agent.stop()
        return False

    async def start_all_agents(self) -> Dict[str, Any]:
        """启动所有代理"""
        results = {}
        for agent_id, agent in self.agents.items():
            results[agent_id] = await agent.start()
        return results

    async def stop_all_agents(self) -> Dict[str, Any]:
        """停止所有代理"""
        results = {}
        for agent_id, agent in self.agents.items():
            results[agent_id] = await agent.stop()
        return results

    def list_agents(self) -> List[str]:
        """列出所有代理"""
        return list(self.agents.keys())

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取代理状态"""
        agent = self.agents.get(agent_id)
        if agent:
            if hasattr(agent, 'get_status'):
                return agent.get_status()
            return {"status": "active", if hasattr(agent,
    'is_running') and agent.is_running else "inactive"}
        return None

    def _discover_agent_scripts(self, agents_dir: Optional[str] = None) -> Dict[str,
    str]:
        """
        Discovers available agent scripts in the specified directory.
        Returns a map of agent names to their script paths.
        """
        agent_map = {}
        try:
            if not agents_dir:
                agents_dir = os.path.join(os.path.dirname(__file__), '..', 'agents')

            if not os.path.isdir(agents_dir):
                logger.warning(f"[AgentManager] Agents directory not found: {agents_dir}\
    \
    ")
                return agent_map

            for filename in os.listdir(agents_dir):
                if filename.endswith("_agent.py") and filename != "base_agent.py":
                    agent_name = filename.replace(".py", "")
                    agent_map[agent_name] = os.path.join(agents_dir, filename)
            logger.info(f"[AgentManager] Discovered agent scripts: {agent_map}")
            return agent_map
        except Exception as e:
            logger.error(f"[AgentManager] Error discovering agent scripts: {e}")
            return agent_map

    def launch_agent(self, agent_name: str,
    args: Optional[List[str]] = None) -> Optional[str]:
        """
        Launches a sub - agent in a new process.

        Args:
            agent_name (str): The name of the agent to launch (e.g.,
    'data_analysis_agent').
            args (Optional[List[str]]): A list of command -\
    line arguments to pass to the agent script.

        Returns:
            Optional[str]: The agent's process ID (PID) as a string if successful,
    else None.
        """
        with self.launch_lock:
            if agent_name not in self.agent_script_map:
                logger.error(f"[AgentManager] Error: Agent '{agent_name}' not found.")
                return None

            if agent_name in self.active_agents and \
    self.active_agents[agent_name].poll() is None:
                logger.info(f"[AgentManager] Info: Agent '{agent_name}' is already runni\
    \
    ng with PID {self.active_agents[agent_name].pid}.")
                return str(self.active_agents[agent_name].pid)

            script_path = self.agent_script_map[agent_name]
            command = [self.python_executable, script_path]
            if args:
                command.extend(args)

            try:
                logger.info(f"[AgentManager] Launching '{agent_name}' with command: {' '\
    \
    .join(command)}")
                process = subprocess.Popen(command)
                self.active_agents[agent_name] = process
                logger.info(f"[AgentManager] Successfully launched '{agent_name}' with P\
    \
    ID {process.pid}.")
                return str(process.pid)
            except Exception as e:
                logger.error(f"[AgentManager] Failed to launch agent '{agent_name}': {e}\
    \
    ")
                return None

    def check_agent_health(self, agent_name: str) -> bool:
        """
        Checks if an agent is healthy. This is a placeholder.
        """
        if agent_name in self.active_agents and \
    self.active_agents[agent_name].poll() is None:
            return True
        return False

    def shutdown_agent(self, agent_name: str) -> bool:
        """
        Terminates a running sub - agent process.

        Args:
            agent_name (str): The name of the agent to shut down.

        Returns:
            bool: True if the agent was terminated successfully, False otherwise.
        """
        if agent_name in self.active_agents and \
    self.active_agents[agent_name].poll() is None:
            process = self.active_agents[agent_name]
            logger.info(f"[AgentManager] Shutting down '{agent_name}' (PID: {process.pid\
    \
    })...")
            process.terminate()  # Sends SIGTERM
            try:
                process.wait(timeout = 5)  # Wait for the process to terminate
                logger.info(f"[AgentManager] Agent '{agent_name}' terminated.")
            except subprocess.TimeoutExpired:
                logger.warning(f"[AgentManager] Agent '{agent_name}' did not terminate g\
    \
    racefully, killing.")
                process.kill()  # Sends SIGKILL
            del self.active_agents[agent_name]
            return True
        else:
            logger.warning(f"[AgentManager] Agent '{agent_name}' not found or \
    not running.")
            return False

    def shutdown_all_agents(self):
        """
        Shuts down all active sub - agent processes managed by this manager.
        """
        logger.info("[AgentManager] Shutting down all active agents...")
        for agent_name in list(self.active_agents.keys()):
            self.shutdown_agent(agent_name)

    async def wait_for_agent_ready(self, agent_name: str, timeout: int = 10,
    service_discovery: Optional[Any] = None):
        """
        Waits for an agent to be ready by checking for its capability advertisement.
        """
        if service_discovery is None:
            logger.warning("[AgentManager] wait_for_agent_ready is using placeholder sle\
    \
    ep as no service_discovery provided.")
            await asyncio.sleep(2)
            logger.info(f"[AgentManager] Assuming agent '{agent_name}' is ready after wa\
    \
    iting.")
            return

        expected_capability_id = "data_analysis_v1"  # Placeholder

        logger.info(f"[AgentManager] Waiting for agent '{agent_name}' to advertise capab\
    \
    ility '{expected_capability_id}'")
        max_retries = timeout * 2  # Check every 0.5s
        for i in range(max_retries):
            found_caps = await service_discovery.find_capabilities(capability_id_filter \
    = expected_capability_id)
            if found_caps:
                logger.info(f"[AgentManager] Agent '{agent_name}' is ready. Found capabi\
    \
    lity: {expected_capability_id}")
                return
            logger.debug(f"[AgentManager] Still waiting for agent '{agent_name}'. Retry \
    {i + 1} / {max_retries}")
            await asyncio.sleep(0.5)

        logger.warning(f"[AgentManager] Agent '{agent_name}' not ready within {timeout} \
    \
    seconds.")

    def get_available_agents(self) -> List[str]:
        """
        Returns a list of available agent names.
        """
        return list(self.agent_script_map.keys())

    def get_active_agents(self) -> Dict[str, int]:
        """
        Returns a dictionary of active agents and their PIDs.
        """
        active_agents = {}
        for agent_name, process in self.active_agents.items():
            if process.poll() is None:  # Agent is still running:
                active_agents[agent_name] = process.pid
        return active_agents

    async def get_agent_capabilities(self, agent_name: str,
    service_discovery: Any) -> List[Dict[str, Any]]:
        """
        Retrieves the capabilities of a specific agent.
        """
        if service_discovery is None:
            logger.warning("[AgentManager] Service discovery not available.")
            return []
        return await service_discovery.get_all_capabilities_async()
