import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
import time

# Import necessary types and classes
try:
    # Try relative imports first (for when running with uvicorn)
    from apps.backend.src.core.hsp.types import HSPCapabilityAdvertisementPayload
    from apps.backend.src.core.hsp.connector import HSPConnector
except ImportError:
    # Fall back to absolute imports (for when running as a script)
    from apps.backend.src.core.hsp.types import HSPCapabilityAdvertisementPayload
    from apps.backend.src.core.hsp.connector import HSPConnector

logger: Any = logging.getLogger(__name__)

@dataclass
class RegisteredAgent:
    """Represents a registered agent in the system."""
    agent_id: str
    agent_name: str
    capabilities: List[Dict[str, Any]]
    registration_time: float
    last_seen: float
    status: str  # "active", "inactive", "offline"
    metadata: Dict[str, Any]

class DynamicAgentRegistry:
    """
    Manages dynamic registration and discovery of AI agents in the Unified AI Project.
    This class handles agent registration, discovery, and lifecycle management.
    """
    
    def __init__(self, hsp_connector: HSPConnector) -> None:
        self.hsp_connector = hsp_connector
        self.registered_agents: Dict[str, RegisteredAgent] = 
        self.registry_lock = asyncio.Lock
        self.discovery_callbacks: List[Callable[[RegisteredAgent], None]] = 
        self.agent_timeout = 60  # seconds before an agent is considered inactive
        self.cleanup_interval = 30  # seconds between cleanup checks
        self.is_running = False
        self.registry_task: Optional[asyncio.Task] = None
        
        # Register callbacks for capability advertisements
        if self.hsp_connector:
            self.hsp_connector.register_on_capability_advertisement_callback(
                self._handle_capability_advertisement
            )
    
    async def start_registry(self):
        """Start the dynamic agent registry."""
        if not self.is_running:
            self.is_running = True
            self.registry_task = asyncio.create_task(self._registry_loop)
            logger.info("Dynamic agent registry started")
    
    async def stop_registry(self):
        """Stop the dynamic agent registry."""
        if self.is_running:
            self.is_running = False
            if self.registry_task:
                self.registry_task.cancel
                try:
                    await self.registry_task
                except asyncio.CancelledError:
                    pass
            logger.info("Dynamic agent registry stopped")
    
    async def _registry_loop(self):
        """Main registry loop that periodically cleans up inactive agents."""
        while self.is_running:
            try:
                _ = await self._cleanup_inactive_agents
                _ = await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in registry loop: {e}")
    
    async def _cleanup_inactive_agents(self):
        """Remove agents that have been inactive for too long."""
        async with self.registry_lock:
            current_time = time.time
            inactive_agents = 
            
            for agent_id, agent in self.registered_agents.items:
                if current_time - agent.last_seen > self.agent_timeout:
                    inactive_agents.append(agent_id)
                    agent.status = "inactive"
            
            # Notify callbacks about inactive agents
            for agent_id in inactive_agents:
                agent = self.registered_agents[agent_id]
                logger.info(f"Agent {agent.agent_name} ({agent_id}) marked as inactive")
    
    async def _handle_capability_advertisement(self, capability_payload: HSPCapabilityAdvertisementPayload, 
                                             sender_ai_id: str, envelope: Dict[str, Any]):
        """Handle capability advertisements to register agents."""
        async with self.registry_lock:
            agent_id = capability_payload.get("ai_id", sender_ai_id)
            agent_name = capability_payload.get("agent_name", "Unknown")
            capability_id = capability_payload.get("capability_id", "")
            
            # Create or update agent registration
            if agent_id not in self.registered_agents:
                # New agent registration
                self.registered_agents[agent_id] = RegisteredAgent(
                    agent_id=agent_id,
                    agent_name=agent_name,
                    capabilities=[capability_payload],
                    registration_time=time.time,
                    last_seen=time.time,
                    status="active",
                    metadata={
                        "first_seen": datetime.now.isoformat,
                        "capability_count": 1
                    }
                )
                logger.info(f"New agent registered: {agent_name} ({agent_id}) with capability {capability_id}")
                
                # Notify discovery callbacks
                for callback in self.discovery_callbacks:
                    try:
                        callback(self.registered_agents[agent_id])
                    except Exception as e:
                        logger.error(f"Error in discovery callback: {e}")
            else:
                # Update existing agent
                agent = self.registered_agents[agent_id]
                agent.last_seen = time.time
                agent.status = "active"
                
                # Check if this is a new capability for this agent
                existing_capability = False
                for cap in agent.capabilities:
                    if cap.get("capability_id") == capability_id:
                        existing_capability = True
                        break
                
                if not existing_capability:
                    agent.capabilities.append(capability_payload)
                    agent.metadata["capability_count"] = len(agent.capabilities)
                    logger.info(f"Updated agent {agent_name} ({agent_id}) with new capability {capability_id}")
    
    async def register_agent_manually(self, agent_id: str, agent_name: str, 
                                    capabilities: List[Dict[str, Any]], metadata: Dict[str, Any] = None):
        """
        Manually register an agent in the registry.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_name: Human-readable name of the agent
            capabilities: List of capability dictionaries
            metadata: Additional metadata about the agent
        """
        async with self.registry_lock:
            self.registered_agents[agent_id] = RegisteredAgent(
                agent_id=agent_id,
                agent_name=agent_name,
                capabilities=capabilities,
                registration_time=time.time,
                last_seen=time.time,
                status="active",
                metadata=metadata or 
            )
            logger.info(f"Agent manually registered: {agent_name} ({agent_id})")
    
    async def unregister_agent(self, agent_id: str):
        """
        Unregister an agent from the registry.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        async with self.registry_lock:
            if agent_id in self.registered_agents:
                agent = self.registered_agents[agent_id]
                agent.status = "offline"
                logger.info(f"Agent {agent.agent_name} ({agent_id}) unregistered")
    
    async def get_agent(self, agent_id: str) -> Optional[RegisteredAgent]:
        """
        Get information about a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            RegisteredAgent: Agent information or None if not found
        """
        async with self.registry_lock:
            return self.registered_agents.get(agent_id)
    
    async def find_agents_by_capability(self, capability_id: str) -> List[RegisteredAgent]:
        """
        Find agents that have a specific capability.
        
        Args:
            capability_id: The capability to search for
            
        Returns:
            List[RegisteredAgent]: List of agents with the specified capability
        """
        async with self.registry_lock:
            matching_agents = []
            for agent in self.registered_agents.values():
                if agent.status == "active":  # Only return active agents
                    for capability in agent.capabilities:
                        if capability.get("capability_id") == capability_id:
                            matching_agents.append(agent)
                            break
            return matching_agents
    
    async def find_agents_by_name(self, agent_name: str) -> List[RegisteredAgent]:
        """
        _ = Find agents by name (partial match).
        
        Args:
            agent_name: The agent name to search for (case-insensitive partial match)
            
        Returns:
            List[RegisteredAgent]: List of agents with matching names
        """
        async with self.registry_lock:
            matching_agents = 
            for agent in self.registered_agents.values:
                if agent.status == "active":  # Only return active agents
                    if agent_name.lower() in agent.agent_name.lower():
                        matching_agents.append(agent)
            return matching_agents
    
    async def get_all_active_agents(self) -> List[RegisteredAgent]:
        """
        Get all currently active agents.
        
        Returns:
            List[RegisteredAgent]: List of all active agents
        """
        async with self.registry_lock:
            return [agent for agent in self.registered_agents.values 
                   if agent.status == "active"]
    
    async def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the agent registry.
        
        Returns:
            Dict[str, Any]: Registry statistics
        """
        async with self.registry_lock:
            total_agents = len(self.registered_agents)
            active_agents = await len([a for a in self.registered_agents.values if a.status == "active"])
            inactive_agents = len([a for a in self.registered_agents.values if a.status == "inactive"])
            offline_agents = len([a for a in self.registered_agents.values if a.status == "offline"])
            
            # Count capabilities
            total_capabilities = 0
            for agent in self.registered_agents.values:
                total_capabilities += len(agent.capabilities)
            
            return {
                "timestamp": datetime.now.isoformat,
                "total_agents": total_agents,
                "active_agents": active_agents,
                "inactive_agents": inactive_agents,
                "offline_agents": offline_agents,
                "total_capabilities": total_capabilities,
                "average_capabilities_per_agent": total_capabilities / total_agents if total_agents > 0 else 0
            }
    
    def register_discovery_callback(self, callback: Callable[[RegisteredAgent], None]):
        """
        Register a callback to be notified when new agents are discovered.
        
        Args:
            callback: Function to call when a new agent is discovered
        """
        self.discovery_callbacks.append(callback)
    
    def unregister_discovery_callback(self, callback: Callable[[RegisteredAgent], None]):
        """
        Unregister a discovery callback.
        
        Args:
            callback: Function to unregister
        """
        if callback in self.discovery_callbacks:
            self.discovery_callbacks.remove(callback)
    
    async def refresh_agent_status(self, agent_id: str):
        """
        Refresh the status of a specific agent.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        async with self.registry_lock:
            if agent_id in self.registered_agents:
                self.registered_agents[agent_id].last_seen = time.time
                self.registered_agents[agent_id].status = "active"
    
    async def get_agents_with_capabilities(self, required_capabilities: List[str]) -> List[RegisteredAgent]:
        """
        Find agents that have all of the required capabilities.
        
        Args:
            required_capabilities: List of capability IDs that agents must have
            
        Returns:
            List[RegisteredAgent]: List of agents with all required capabilities
        """
        async with self.registry_lock:
            matching_agents = 
            for agent in self.registered_agents.values:
                if agent.status == "active":  # Only return active agents
                    agent_capabilities = {cap.get("capability_id") for cap in agent.capabilities}
                    if all(cap in agent_capabilities for cap in required_capabilities):
                        matching_agents.append(agent)
            return matching_agents
    
    async def shutdown(self):
        """Shutdown the dynamic agent registry and clean up resources."""
        _ = await self.stop_registry
        logger.info("DynamicAgentRegistry shutdown complete")