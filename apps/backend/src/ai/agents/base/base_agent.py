import asyncio
import uuid
import logging
from typing import Dict, Any, Optional, List

# 延迟导入以避免循环导入
# from apps.backend.src.core_services import initialize_services, get_services, shutdown_services
from apps.backend.src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

class BaseAgent:
    """
    The base class for all specialized sub-agents.
    Handles the boilerplate of service initialization, HSP connection,
    and listening for tasks.
    """
    def __init__(self, agent_id: str, capabilities: List[Dict[str, Any]], agent_name: str = "BaseAgent"):
        """
        Initializes the BaseAgent.

        Args:
            agent_id (str): The unique identifier for this agent instance.
            capabilities (List[Dict[str, Any]]): A list of capability dictionaries
                                                  that this agent will advertise.
            agent_name (str, optional): The name of the agent. Defaults to "BaseAgent".
        """
        self.agent_id = agent_id
        self.capabilities = capabilities
        self.agent_name = agent_name
        self.hsp_connector = None
        self.is_running = False
        self.services = None

    async def _ainit(self):
        # 延迟导入以避免循环导入
        from apps.backend.src.core_services import initialize_services
        
        # Initialize core services required by the agent
        # Construct a minimal config for initialize_services
        # This is needed because initialize_services now requires a config dict
        # and BaseAgent might not have a full one.
        minimal_config = {
            "is_multiprocess": False,
            "mcp": {
                "mqtt_broker_address": "localhost",
                "mqtt_broker_port": 1883,
                "enable_fallback": True,
                "fallback_config": {}
            }
        }

        await initialize_services(
            config=minimal_config, # Pass the constructed config
            ai_id=self.agent_id,
            use_mock_ham=True, # Sub-agents typically don't need their own large memory
            llm_config=None, # Sub-agents use specific tools, may not need a full LLM
            operational_configs=None
        )
        
        # 延迟导入以避免循环导入
        from apps.backend.src.core_services import get_services
        self.services = get_services()
        self.hsp_connector = self.services.get("hsp_connector")

    async def start(self):
        """
        Starts the agent's main loop and connects to the HSP network.
        """
        logger.info(f"[{self.agent_id}] Setting is_running to True")
        self.is_running = True

        # Perform async initialization
        await self._ainit()

        if not self.hsp_connector:
            logger.error(f"[{self.agent_id}] Error: HSPConnector not available.")
            return

        logger.info(f"[{self.agent_id}] Starting...")

        # Register the task request handler
        if self.hsp_connector:
            self.hsp_connector.register_on_task_request_callback(self.handle_task_request)

        # Advertise capabilities
        if self.hsp_connector:
            for cap in self.capabilities:
                await self.hsp_connector.advertise_capability(cap)

        logger.info(f"[{self.agent_id}] is running and listening for tasks.")

        # Agent is now running, return control to the caller
        # The main loop (if any) should be managed externally or by a dedicated task

    async def stop(self):
        """
        Stops the agent and shuts down its services.
        """
        logger.info(f"[{self.agent_id}] Stopping...")
        self.is_running = False
        
        # 延迟导入以避免循环导入
        from apps.backend.src.core_services import shutdown_services
        await shutdown_services()
        logger.info(f"[{self.agent_id}] Stopped.")

    def is_healthy(self) -> bool:
        """
        A basic health check for the agent.
        Subclasses can override this for more specific health checks.
        """
        return self.is_running and self.hsp_connector and self.hsp_connector.is_connected

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        """
        The primary handler for incoming HSP task requests.
        This method should be overridden by subclasses to implement specific logic.
        """
        logger.info(f"[{self.agent_id}] Received task request: {task_payload.get('request_id')} for capability '{task_payload.get('capability_id_filter')}' from '{sender_ai_id}'.")

        # Default behavior: Acknowledge and report not implemented
        result_payload = HSPTaskResultPayload(
            request_id=task_payload.get("request_id", ""),
            status="failure",
            error_details={
                "error_code": "NOT_IMPLEMENTED",
                "error_message": f"The '{self.__class__.__name__}' has not implemented the 'handle_task_request' method."
            }
        )

        if self.hsp_connector and task_payload.get("callback_address"):
            callback_topic = task_payload["callback_address"]
            await self.hsp_connector.send_task_result(result_payload, callback_topic, task_payload.get("request_id"))
            logger.warning(f"[{self.agent_id}] Sent NOT_IMPLEMENTED failure response to {callback_topic}")

    async def send_task_success(self, request_id: str, sender_ai_id: str, callback_address: str, payload: Any):
        result_payload = HSPTaskResultPayload(
            request_id=request_id,
            executing_ai_id=self.agent_id,
            status="success",
            payload=payload
        )
        if self.hsp_connector:
            await self.hsp_connector.send_task_result(result_payload, callback_address, request_id)

    async def send_task_failure(self, request_id: str, sender_ai_id: str, callback_address: str, error_message: str):
        result_payload = HSPTaskResultPayload(
            request_id=request_id,
            executing_ai_id=self.agent_id,
            status="failure",
            error_details={
                "error_code": "TASK_EXECUTION_FAILED",
                "error_message": error_message
            }
        )
        if self.hsp_connector:
            await self.hsp_connector.send_task_result(result_payload, callback_address, request_id)

if __name__ == '__main__':
    # Example of how a BaseAgent could be run.
    # In a real scenario, a dedicated script would run a specific agent subclass.
    async def main():
        agent_id = f"did:hsp:base_agent_tester_{uuid.uuid4().hex[:6]}"

        # Example capability
        test_capability = {
            "capability_id": f"{agent_id}_echo_v1.0",
            "name": "Base Echo Service",
            "description": "A test echo service from a base agent.",
            "version": "1.0",
            "parameters": [{"name": "data", "type": "string", "required": True}],
            "returns": {"type": "string"}
        }

        agent = BaseAgent(agent_id=agent_id, capabilities=[test_capability])
        await agent.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBaseAgent test manually stopped.")