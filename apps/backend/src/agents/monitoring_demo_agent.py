import asyncio
import logging
from typing import List, Dict, Any
import sys
import os
import time

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try:
    # Try relative imports first (for when running with uvicorn)
    from .base_agent import BaseAgent
    from apps.backend.src.core.hsp.types import HSPTaskRequestPayload, HSPMessageEnvelope
except ImportError:
    # Fall back to absolute imports (for when running as a script)
    from apps.backend.src.ai.agents.base_agent import BaseAgent
    from apps.backend.src.core.hsp.types import HSPTaskRequestPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

class MonitoringDemoAgent(BaseAgent):
    """
    A demo agent that showcases the monitoring and health check features.
    """
    
    def __init__(self, agent_id: str):
        # Define capabilities for this agent
        capabilities = [
            {
                "capability_id": "monitoring_demo_v1",
                "name": "Monitoring Demo",
                "description": "Demonstrates agent monitoring features",
                "version": "1.0"
            },
            {
                "capability_id": "health_check_v1",
                "name": "Health Check",
                "description": "Provides health check information",
                "version": "1.0"
            }
        ]
        
        super().__init__(agent_id, capabilities, "MonitoringDemoAgent")
        self._simulated_errors = 0  # For demo purposes
    
    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        """
        Handle incoming task requests.
        """
        logger.info(f"[{self.agent_id}] Handling task request from {sender_ai_id}")
        
        # Send heartbeat to monitoring system
        await self.send_heartbeat()
        
        request_id = task_payload.get("request_id", "")
        capability_id = task_payload.get("capability_id_filter", "")
        parameters = task_payload.get("parameters", {})
        
        try:
            # Process based on capability
            if capability_id == "monitoring_demo_v1":
                result = await self._handle_monitoring_demo(parameters)
            elif capability_id == "health_check_v1":
                result = await self._handle_health_check(parameters)
            else:
                # Default behavior for unhandled capabilities
                await self.send_task_failure(
                    request_id, 
                    sender_ai_id, 
                    task_payload.get("callback_address", ""), 
                    f"Unsupported capability: {capability_id}"
                )
                return
            
            # Send success response
            await self.send_task_success(
                request_id, 
                sender_ai_id, 
                task_payload.get("callback_address", ""), 
                result
            )
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Error handling task: {e}")
            await self.send_task_failure(
                request_id, 
                sender_ai_id, 
                task_payload.get("callback_address", ""), 
                str(e)
            )
    
    async def _handle_monitoring_demo(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle monitoring demo requests.
        """
        logger.info(f"[{self.agent_id}] Handling monitoring demo request")
        
        action = parameters.get("action", "status")
        
        if action == "status":
            # Get health report
            health_report = await self.get_health_report()
            return {
                "status": "success",
                "health_report": health_report,
                "message": "Health report retrieved successfully"
            }
        
        elif action == "simulate_error":
            # Simulate an error for demo purposes
            self._simulated_errors += 1
            error_msg = f"Simulated error #{self._simulated_errors}"
            
            # Report error to monitoring system
            if self.monitoring_manager:
                await self.monitoring_manager.report_error(self.agent_id, error_msg)
            
            return {
                "status": "error_simulated",
                "message": error_msg,
                "error_count": self._simulated_errors
            }
        
        elif action == "simulate_task":
            # Simulate a task with variable response time
            import random
            duration = parameters.get("duration", random.uniform(0.1, 1.0))
            
            # Sleep to simulate work
            await asyncio.sleep(duration)
            
            # Report task result to monitoring system
            if self.monitoring_manager:
                await self.monitoring_manager.report_task_result(
                    agent_id=self.agent_id,
                    success=True,
                    response_time_ms=duration * 1000
                )
            
            return {
                "status": "success",
                "message": f"Task completed in {duration:.2f} seconds",
                "duration_seconds": duration
            }
        
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }
    
    async def _handle_health_check(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle health check requests.
        """
        logger.info(f"[{self.agent_id}] Handling health check request")
        
        # Get detailed health information
        health_report = await self.get_health_report()
        
        # Add additional health information
        health_info = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "is_healthy": self.is_healthy(),
            "is_running": self.is_running,
            "uptime_seconds": asyncio.get_event_loop().time() - self._start_time if self._start_time else 0,
            "task_count": self._task_counter,
            "simulated_errors": self._simulated_errors,
            "hsp_connected": self.hsp_connector.is_connected if self.hsp_connector else False
        }
        
        # Merge with health report
        health_info.update(health_report)
        
        return {
            "status": "success",
            "health_info": health_info,
            "message": "Health check completed"
        }

async def main():
    """
    Main function to run the monitoring demo agent.
    """
    import uuid
    
    # Create agent with a unique ID
    agent_id = f"did:hsp:monitoring_demo_agent_{uuid.uuid4().hex[:8]}"
    agent = MonitoringDemoAgent(agent_id)
    
    try:
        # Start the agent
        await agent.start()
        logger.info(f"Monitoring Demo Agent {agent_id} started successfully")
        
        # Keep the agent running and periodically send heartbeats
        while agent.is_running:
            # Send heartbeat every 5 seconds
            await agent.send_heartbeat()
            await asyncio.sleep(5)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Error in main: {e}")
    finally:
        # Stop the agent
        await agent.stop()
        logger.info("Monitoring Demo Agent stopped")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the agent
    asyncio.run(main())