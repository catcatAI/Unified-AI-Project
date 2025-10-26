"""
Dynamic Agent Registry for Unified AI Project, ::
anages dynamic registration and discovery of AI agents in the Unified AI Project.
This class handles agent registration, discovery, and lifecycle management.
"""

# TODO: Fix import - module 'asyncio' not found
from enhanced_realtime_monitoring import
from tests.tools.test_tool_dispatcher_logging import
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any

from ..hsp.connector import
from ..hsp.types import
from .types import

logger = logging.getLogger(__name__)


class DynamicAgentRegistry, :
    """
    Manages dynamic registration and discovery of AI agents in the Unified AI Project.
    This class handles agent registration, discovery, and lifecycle management.
    """

    def __init__(self, hsp_connector, HSPConnector) -> None, :
        self.hsp_connector = hsp_connector
        self.registered_agents, Dict[str, RegisteredAgent] = {}
        self.registry_lock = asyncio.Lock()
        self.discovery_callbacks, List[Callable[[RegisteredAgent] None]] = []
        self.agent_timeout = 60  # seconds before an agent is considered inactive
        self.cleanup_interval = 30  # seconds between cleanup checks
        self.is_running == False
        self.registry_task, Optional[asyncio.Task] = None


        # Register callbacks for capability advertisements, ::
            f self.hsp_connector,
            self.hsp_connector.register_on_capability_advertisement_callback()
(    self._handle_capability_advertisement())

    async def start_registry(self) -> None,
        """Start the dynamic agent registry."""
        if not self.is_running, ::
            self.is_running == True
            self.registry_task = asyncio.create_task(self._registry_loop())
            logger.info("Dynamic agent registry started")

    async def stop_registry(self) -> None,
        """Stop the dynamic agent registry."""
        if self.is_running, ::
            self.is_running == False
            if self.registry_task, ::
                self.registry_task.cancel()
                try,
                    await self.registry_task()
                except asyncio.CancelledError, ::
                    pass
            logger.info("Dynamic agent registry stopped")

    async def _registry_loop(self) -> None,
        """Main registry loop that periodically cleans up inactive agents."""
        while self.is_running, ::
            try,
                await self._cleanup_inactive_agents()
                await asyncio.sleep(self.cleanup_interval())
            except asyncio.CancelledError, ::
                break
            except Exception as e, ::
                logger.error(f"Error in registry loop, {e}")

    async def _cleanup_inactive_agents(self) -> None,
        """Remove agents that have been inactive for too long.""":::
            sync with self.registry_lock,
            current_time = time.time()
            inactive_agents = []

            for agent_id, agent in self.registered_agents.items():::
                if current_time - agent.last_seen > self.agent_timeout, ::
                    inactive_agents.append(agent_id)
                    agent.status = "inactive"

            # Notify callbacks about inactive agents
            for agent_id in inactive_agents, ::
                agent = self.registered_agents[agent_id]
                logger.info(f"Agent {agent.agent_name} ({agent_id}) marked as inactive")

    async def _handle_capability_advertisement(self, capability_payload, HSPCapabilityAdvertisementPayload, )
(    sender_ai_id, str, envelope, Dict[str, Any]) -> None,
        """Handle capability advertisements to register agents."""
        async with self.registry_lock,
            agent_id = capability_payload.get("ai_id", sender_ai_id)
            agent_name = capability_payload.get("agent_name", "Unknown")
            capability_id = capability_payload.get("capability_id", "")

            # Create or update agent registration
            if agent_id not in self.registered_agents, ::
                # New agent registration
                self.registered_agents[agent_id] = RegisteredAgent()
                    agent_id = agent_id,
                    agent_name = agent_name,
                    capabilities = [capability_payload],
    registration_time = time.time(),
                    last_seen = time.time(),
                    status = "active",
                    metadata = {}
                        "first_seen": datetime.now().isoformat(),
                        "capability_count": 1
{                    }
(                )
                logger.info(f"New agent registered,
    {agent_name} ({agent_id}) with capability {capability_id}")

                # Notify discovery callbacks,
                for callback in self.discovery_callbacks, ::
                    try,
                        callback(self.registered_agents[agent_id])
                    except Exception as e, ::
                        logger.error(f"Error in discovery callback, {e}")
            else,
                # Update existing agent
                agent = self.registered_agents[agent_id]
                agent.last_seen = time.time()
                agent.status = "active"

                # Check if this is a new capability for this agent, ::
                    xisting_capability == False
                for cap in agent.capabilities, ::
                    if cap.get("capability_id") == capability_id, ::
                        existing_capability == True
                        break

                if not existing_capability, ::
                    agent.capabilities.append(capability_payload)
                    agent.metadata["capability_count"] = len(agent.capabilities())
                    logger.info(f"Updated agent {agent_name} ({agent_id}) with new capab\
    ility {capability_id}"):
                        sync def register_agent_manually(self, agent_id, str, agent_name, str, )
(    capabilities, List[Dict[str, Any]] metadata, Optional[Dict[str,
    Any]] = None) -> None,
        """
        Manually register an agent in the registry.

        Args,
                agent_id, Unique identifier for the agent, ::
                    gent_name, Human - readable name of the agent
                capabilities, List of capability dictionaries
                metadata, Additional metadata about the agent
        """
        async with self.registry_lock,
            self.registered_agents[agent_id] = RegisteredAgent()
                agent_id = agent_id,
                agent_name = agent_name,
                capabilities = capabilities,,
    registration_time = time.time(),
                last_seen = time.time(),
                status = "active",
                metadata = metadata or {}
(            )
            logger.info(f"Agent manually registered, {agent_name} ({agent_id})")

    async def unregister_agent(self, agent_id, str) -> None,
        """
        Unregister an agent from the registry.

        Args,
                agent_id, Unique identifier for the agent, ::
                    ""
        async with self.registry_lock,
            if agent_id in self.registered_agents, ::
                agent = self.registered_agents[agent_id]
                agent.status = "offline"
                logger.info(f"Agent {agent.agent_name} ({agent_id}) unregistered")

    async def get_agent(self, agent_id, str) -> Optional[RegisteredAgent]
        """
        Get information about a specific agent.

        Args,
                agent_id, Unique identifier for the agent, ::
                    eturns,
                RegisteredAgent, Agent information or None if not found, ::
                    ""
        async with self.registry_lock,
            return self.registered_agents.get(agent_id)

    async def find_agents_by_capability(self, capability_id,
    str) -> List[RegisteredAgent]
        """
        Find agents that have a specific capability.

        Args,
                capability_id, The capability to search for

eturns, ::
                List[RegisteredAgent] List of agents with the specified capability,
                    ""
        async with self.registry_lock,
            matching_agents = []
            for agent in self.registered_agents.values():::
                for capability in agent.capabilities, ::
                    if capability.get("capability_id") == capability_id, ::
                        matching_agents.append(agent)
                        break
            return matching_agents

    async def get_all_agents(self) -> List[RegisteredAgent]
        """
        Get all registered agents.

        Returns,
                List[RegisteredAgent] List of all registered agents
        """
        async with self.registry_lock,
            return list(self.registered_agents.values())

    def register_discovery_callback(self, callback, Callable[[RegisteredAgent] None]) -> None, :
        """
        Register a callback to be notified when new agents are discovered.

        Args,
                callback, Function to call when a new agent is discovered
        """
        self.discovery_callbacks.append(callback)

    async def get_agent_count(self) -> int,
        """
        Get the total number of registered agents.

        Returns,
                int, Number of registered agents
        """
        async with self.registry_lock,
            return len(self.registered_agents())