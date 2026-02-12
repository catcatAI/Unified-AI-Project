"""
Agent Manager

Manages the lifecycle of specialized sub-agents, including launching,
terminating, and monitoring them.
Also serves as the central message router for HSP communication.
"""

# =============================================================================
# ANGELA-MATRIX: L6[执行层] 全层级 [A] L2+
# =============================================================================
#
# 职责: 管理专业子代理的生命周期，包括启动、终止和监控
# 维度: 涉及所有维度，协调 15 个专业代理的状态矩阵更新
# 安全: 使用 Key A (后端控制) 进行代理权限管理
# 成熟度: L2+ 等级可以理解代理系统的基本概念
#
# 管理的代理类型:
# - IN_PROCESS: 进程内代理（现有实现）
# - SUBPROCESS: 子进程代理（Phase 15）
# - REMOTE: 远程代理（未来扩展）
#
# 管理的专业代理 (15个):
# 1. CreativeWritingAgent - 创意写作与内容生成
# 2. ImageGenerationAgent - 图像生成代理
# 3. WebSearchAgent - 网络搜索代理
# 4. CodeUnderstandingAgent - 代码理解代理
# 5. DataAnalysisAgent - 数据分析代理
# 6. VisionProcessingAgent - 视觉处理代理
# 7. AudioProcessingAgent - 音频处理代理
# 8. KnowledgeGraphAgent - 知识图谱代理
# 9. NLPProcessingAgent - 自然语言处理代理
# 10. PlanningAgent - 规划代理
# 11-15. 其他扩展代理
#
# =============================================================================

import asyncio
import logging
import os
import subprocess
import sys
import threading
import time
import multiprocessing as mp
from typing import Dict, Optional, List, Any, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """代理類型"""
    IN_PROCESS = "in_process"      # 進程內代理（現有實現）
    SUBPROCESS = "subprocess"       # 子進程代理（Phase 15）
    REMOTE = "remote"              # 遠程代理（未來擴展）


@dataclass
class ProcessAgentInfo:
    """進程代理信息"""
    agent_id: str
    agent_type: str
    process: mp.Process
    start_time: float
    last_heartbeat: float
    restart_count: int = 0

class AgentManager:
    """
    Manages the lifecycle of specialized sub - agents.
    It can launch and terminate sub - agent processes.
    """

    def __init__(self, python_executable: Optional[str] = None,
                 agents_dir: Optional[str] = None,
                 enable_process_agents: bool = True,
                 enable_router: bool = True) -> None:
        """
        Initializes the AgentManager.

        Args:
            python_executable: Python executable path.
            agents_dir: The directory where agent scripts are located.
            enable_process_agents: 是否啟用進程代理支持（Phase 15）
            enable_router: 是否啟用消息路由器
        """
        self.python_executable = python_executable or sys.executable
        self.agents: Dict[str, Any] = {}
        self.agent_factories: Dict[str, Any] = {}
        self.active_agents: Dict[str, subprocess.Popen[Any]] = {}
        self.agent_script_map: Dict[str, str] = self._discover_agent_scripts(agents_dir)
        self.launch_lock = threading.Lock()
        
        # Phase 15: 進程代理支持
        self.enable_process_agents = enable_process_agents
        self.process_agents: Dict[str, ProcessAgentInfo] = {}
        self.health_check_interval = 10.0  # 秒
        self.max_restart_attempts = 3
        self._health_monitor_task: Optional[asyncio.Task] = None
        
        # HSP Message Router
        self.enable_router = enable_router
        self.router_process: Optional[subprocess.Popen] = None
        self.router_port = 11435
        self.router_url = f"http://127.0.0.1:{self.router_port}"
        
        # Start router if enabled
        if self.enable_router:
            self._start_router()
        
        logger.info(f"AgentManager initialized. Found agent scripts: {list(self.agent_script_map.keys())}")
        logger.info(f"Process agents enabled: {self.enable_process_agents}")
        logger.info(f"Router enabled: {self.enable_router} (port {self.router_port})")

    def _start_router(self):
        """Start the HSP Message Router as a background process."""
        try:
            # Create a simple router script
            router_script = '''
import asyncio
import json
import logging
from fastapi import FastAPI
import uvicorn
import httpx
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HSPRouter")

app = FastAPI()

registry = {}
message_history = []

@app.post("/register")
async def register_agent(data: dict):
    agent_id = data.get("agent_id")
    port = data.get("port")
    if agent_id:
        registry[agent_id] = {"port": port, "capabilities": data.get("capabilities", [])}
        logger.info(f"Agent registered: {agent_id} at port {port}")
        return {"status": "registered", "agent_id": agent_id}
    return {"error": "Missing agent_id"}, 400

@app.post("/unregister")
async def unregister_agent(data: dict):
    agent_id = data.get("agent_id")
    if agent_id and agent_id in registry:
        del registry[agent_id]
        logger.info(f"Agent unregistered: {agent_id}")
        return {"status": "unregistered"}
    return {"error": "Agent not found"}, 404

@app.get("/registry")
async def get_registry():
    return {"agents": registry}

@app.post("/send")
async def send_message(data: dict):
    target_id = data.get("target_id")
    message = data.get("message", {})
    if target_id in registry:
        target = registry[target_id]
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"http://127.0.0.1:{target['port']}/message", json=message, timeout=5.0)
            return {"status": "delivered", "target": target_id}
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            return {"status": "failed", "error": str(e)}

    return {"status": "failed", "error": "Target not found"}

@app.post("/broadcast")
async def broadcast_message(data: dict):
    message = data.get("message", {})
    results = []
    for agent_id, info in registry.items():
        try:
            async with httpx.AsyncClient() as client:
                await client.post(f"http://127.0.0.1:{info['port']}/message", json=message, timeout=5.0)
            results.append({"agent": agent_id, "status": "delivered"})
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            results.append({"agent": agent_id, "status": "failed", "error": str(e)})

    return {"status": "broadcast", "results": results}

@app.get("/health")
async def health():
    return {"status": "healthy", "agents": len(registry)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=11435, log_level="error")
'''
            
            # Write router script
            router_path = "/tmp/hsp_router.py"
            with open(router_path, 'w') as f:
                f.write(router_script)
            
            # Start router process
            self.router_process = subprocess.Popen(
                [sys.executable, router_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for router to start
            import time
            time.sleep(1)
            
            # Check if router is running
            if self.router_process.poll() is None:
                logger.info(f"HSP Router started on port {self.router_port}")
                # Verify router is responding
                import httpx
                try:
                    response = httpx.get(f"{self.router_url}/health", timeout=2)
                    if response.status_code == 200:
                        logger.info("HSP Router health check passed")
                except Exception:
                    logger.warning("HSP Router health check failed")
            else:
                logger.error("Failed to start HSP Router")
                
        except Exception as e:
            logger.error(f"Error starting router: {e}")
            self.enable_router = False

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
            return {"status": "active" if hasattr(agent, 'is_running') and agent.is_running else "inactive"}
        return None

    def _discover_agent_scripts(self, agents_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Discovers available agent scripts in the specified directory.
        Returns a map of agent names to their script paths.
        """
        agent_map = {}
        try:
            if not agents_dir:
                # Primary: specialized subdirectory (where actual agents are)
                specialized_dir = os.path.join(os.path.dirname(__file__), 'specialized')
                if os.path.isdir(specialized_dir):
                    agents_dir = specialized_dir
                else:
                    # Fallback: parent agents directory
                    agents_dir = os.path.join(os.path.dirname(__file__), '..', 'agents')

            if not os.path.isdir(agents_dir):
                logger.warning(f"[AgentManager] Agents directory not found: {agents_dir}")
                return agent_map

            for filename in os.listdir(agents_dir):
                if filename.endswith("_agent.py") and filename != "base_agent.py":
                    agent_name = filename.replace(".py", "")
                    agent_map[agent_name] = os.path.join(agents_dir, filename)
            
            logger.info(f"[AgentManager] Discovered {len(agent_map)} agent scripts in: {agents_dir}")
            if agent_map:
                logger.info(f"[AgentManager] Agents: {list(agent_map.keys())}")
            return agent_map
        except Exception as e:
            logger.error(f"[AgentManager] Error discovering agent scripts: {e}")
            return agent_map

    def launch_agent(self, agent_name: str,
                     args: Optional[List[str]] = None) -> Optional[str]:
        """
        Launches a sub-agent in a new process.

        Args:
            agent_name (str): The name of the agent to launch (e.g.,
    'data_analysis_agent').
            args (Optional[List[str]]): A list of command-line arguments to pass to the agent script.

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
                logger.info(f"[AgentManager] Info: Agent '{agent_name}' is already running with PID {self.active_agents[agent_name].pid}.")
                return str(self.active_agents[agent_name].pid)

            script_path = self.agent_script_map[agent_name]
            command = [self.python_executable, script_path]
            if args:
                command.extend(args)

            try:
                # Set PYTHONPATH for proper imports
                backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
                env = os.environ.copy()
                env['PYTHONPATH'] = backend_root
                env['ANGELA_AGENT_MODE'] = 'subprocess'
                
                logger.info(f"[AgentManager] Launching '{agent_name}' with PYTHONPATH={backend_root}")
                process = subprocess.Popen(command, env=env)
                self.active_agents[agent_name] = process
                logger.info(f"[AgentManager] Successfully launched '{agent_name}' with PID {process.pid}.")
                return str(process.pid)
            except Exception as e:
                logger.error(f"[AgentManager] Failed to launch agent '{agent_name}': {e}")
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
        Terminates a running sub-agent process.

        Args:
            agent_name (str): The name of the agent to shut down.

        Returns:
            bool: True if the agent was terminated successfully, False otherwise.
        """
        if agent_name in self.active_agents and \
                self.active_agents[agent_name].poll() is None:
            process = self.active_agents[agent_name]
            logger.info(f"[AgentManager] Shutting down '{agent_name}' (PID: {process.pid})...")
            process.terminate()  # Sends SIGTERM
            try:
                process.wait(timeout=5)  # Wait for the process to terminate
                logger.info(f"[AgentManager] Agent '{agent_name}' terminated.")
            except subprocess.TimeoutExpired:
                logger.warning(f"[AgentManager] Agent '{agent_name}' did not terminate gracefully, killing.")
                process.kill()  # Sends SIGKILL
            del self.active_agents[agent_name]
            return True
        else:
            logger.warning(f"[AgentManager] Agent '{agent_name}' not found or not running.")
            return False

    def shutdown_all_agents(self):
        """
        Shuts down all active sub - agent processes managed by this manager.
        """
        logger.info("[AgentManager] Shutting down all active agents...")
        for agent_name in list(self.active_agents.keys()):
            self.shutdown_agent(agent_name)
        
        # Shutdown router
        if self.router_process:
            logger.info("[AgentManager] Shutting down HSP Router...")
            self.router_process.terminate()
            try:
                self.router_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.router_process.kill()
            logger.info("[AgentManager] HSP Router stopped")

    async def wait_for_agent_ready(self, agent_name: str, timeout: int = 10,
                                   service_discovery: Optional[Any] = None):
        """
        Waits for an agent to be ready by checking for its capability advertisement.
        """
        if service_discovery is None:
            logger.warning("[AgentManager] wait_for_agent_ready is using placeholder sleep as no service_discovery provided.")
            await asyncio.sleep(2)
            logger.info(f"[AgentManager] Assuming agent '{agent_name}' is ready after waiting.")
            return

        expected_capability_id = "data_analysis_v1"  # Placeholder

        logger.info(f"[AgentManager] Waiting for agent '{agent_name}' to advertise capability '{expected_capability_id}'")
        max_retries = timeout * 2  # Check every 0.5s
        for i in range(max_retries):
            found_caps = await service_discovery.find_capabilities(capability_id_filter=expected_capability_id)
            if found_caps:
                logger.info(f"[AgentManager] Agent '{agent_name}' is ready. Found capability: {expected_capability_id}")
                return
            logger.debug(f"[AgentManager] Still waiting for agent '{agent_name}'. Retry {i + 1} / {max_retries}")
            await asyncio.sleep(0.5)

        logger.warning(f"[AgentManager] Agent '{agent_name}' not ready within {timeout} seconds.")

    def get_available_agents(self) -> List[str]:
        """
        Returns a list of available agent names.
        """
        return list(self.agent_script_map.keys())

    async def auto_load_agents(self) -> int:
        """
        Auto-load all discovered agent scripts and create instances.
        Returns the number of agents successfully loaded.
        """
        loaded_count = 0
        for agent_name, script_path in self.agent_script_map.items():
            try:
                # Import the agent module
                import importlib.util
                spec = importlib.util.spec_from_file_location(agent_name, script_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Find agent class (capitalize first letter)
                    agent_class_name = agent_name.replace('_', ' ').title().replace(' ', '') + 'Agent'
                    if hasattr(module, agent_class_name):
                        agent_class = getattr(module, agent_class_name)
                        # Create agent instance
                        agent = agent_class(agent_id=agent_name, agent_name=agent_name)
                        self.agents[agent_name] = agent
                        loaded_count += 1
                        logger.info(f"[AgentManager] Auto-loaded agent: {agent_name}")
                    else:
                        logger.warning(f"[AgentManager] No {agent_class_name} class in {agent_name}")
            except Exception as e:
                logger.error(f"[AgentManager] Failed to load agent {agent_name}: {e}")
        
        logger.info(f"[AgentManager] Auto-loaded {loaded_count}/{len(self.agent_script_map)} agents")
        return loaded_count

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
