"""
Default agents that are automatically available in the system.
This module ensures that core agents like DataAnalysisAgent are always available
without needing to be manually created or launched.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from src.agents.data_analysis_agent import DataAnalysisAgent
from src.core_services import get_services

logger = logging.getLogger(__name__)

class DefaultAgentManager:
    """Manages default agents that are always available in the system."""
    
    def __init__(self):
        self.default_agents: Dict[str, Any] = {}
        self.initialized = False
    
    async def initialize_default_agents(self):
        """Initialize all default agents."""
        if self.initialized:
            return
        
        try:
            # Get core services
            services = get_services()
            if not services:
                logger.warning("Core services not available, skipping default agent initialization")
                return
            
            hsp_connector = services.get("hsp_connector")
            service_discovery = services.get("service_discovery")
            
            if not hsp_connector or not service_discovery:
                logger.warning("HSP connector or service discovery not available")
                return
            
            # Create and start DataAnalysisAgent
            data_agent = DataAnalysisAgent(agent_id="did:hsp:default_data_analysis_agent")
            data_agent.hsp_connector = hsp_connector
            await data_agent.start()
            
            # Register capabilities with service discovery
            from datetime import datetime, timezone
            for capability in data_agent.capabilities:
                capability_payload = {
                    "capability_id": capability["capability_id"],
                    "name": capability["name"],
                    "description": capability["description"],
                    "ai_id": data_agent.agent_id,
                    "input_schema_example": {"type": "object", "properties": {"csv_content": {"type": "string"}}},
                    "output_schema_example": {"type": "object", "properties": {"result": {"type": "string"}}},
                    "version": "1.0",
                    "availability_status": "online",
                    "tags": ["data", "analysis", "csv"]
                }
                
                # Add to service discovery (use current datetime)
                service_discovery.known_capabilities[capability["capability_id"]] = (
                    capability_payload,
                    datetime.now(timezone.utc)
                )
            
            self.default_agents["data_analysis"] = data_agent
            
            # Register task request handler with HSP connector
            hsp_connector.register_on_task_request_callback(self._handle_task_request)
            
            logger.info(f"Initialized {len(self.default_agents)} default agents")
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize default agents: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def _handle_task_request(self, payload: Dict[str, Any], sender_ai_id: str, envelope: Dict[str, Any]):
        """Handle incoming task requests and route to appropriate default agent."""
        try:
            capability_id_filter = payload.get("capability_id_filter")
            
            # Route to DataAnalysisAgent
            if capability_id_filter == "data_analysis_v1":
                data_agent = self.default_agents.get("data_analysis")
                if data_agent:
                    await data_agent.handle_task_request(payload, sender_ai_id, envelope)
                    return
            
            logger.warning(f"No default agent found for capability: {capability_id_filter}")
            
        except Exception as e:
            logger.error(f"Error handling task request in default agents: {e}")
    
    async def shutdown_default_agents(self):
        """Shutdown all default agents."""
        for agent_name, agent in self.default_agents.items():
            try:
                await agent.stop()
                logger.info(f"Stopped default agent: {agent_name}")
            except Exception as e:
                logger.error(f"Error stopping default agent {agent_name}: {e}")
        
        self.default_agents.clear()
        self.initialized = False

# Global instance
_default_agent_manager: Optional[DefaultAgentManager] = None

def get_default_agent_manager() -> DefaultAgentManager:
    """Get the global default agent manager instance."""
    global _default_agent_manager
    if _default_agent_manager is None:
        _default_agent_manager = DefaultAgentManager()
    return _default_agent_manager

async def initialize_default_agents():
    """Initialize default agents."""
    manager = get_default_agent_manager()
    await manager.initialize_default_agents()

async def shutdown_default_agents():
    """Shutdown default agents."""
    manager = get_default_agent_manager()
    await manager.shutdown_default_agents()