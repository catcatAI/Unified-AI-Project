import asyncio
import uuid
from typing import Dict, Any, Optional, List

from src.core_services import initialize_services, get_services, shutdown_services
from src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

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

        # Initialize core services required by the agent
        initialize_services(
            ai_id=self.agent_id,
            use_mock_ham=True, # Sub-agents typically don't need their own large memory
            llm_config=None, # Sub-agents use specific tools, may not need a full LLM
            operational_configs=None
        )
        self.services = get_services()
        self.hsp_connector = self.services.get("hsp_connector")

    async def start(self):
        """
        Starts the agent's main loop and connects to the HSP network.
        """
        print(f"[{self.agent_id}] Setting is_running to True")
        self.is_running = True
        if not self.hsp_connector:
            print(f"[{self.agent_id}] Error: HSPConnector not available.")
            return

        print(f"[{self.agent_id}] Starting...")

        # Register the task request handler
        if self.hsp_connector:
            self.hsp_connector.register_on_task_request_callback(self.handle_task_request)

        # Advertise capabilities
        if self.hsp_connector:
            for cap in self.capabilities:
                await self.hsp_connector.advertise_capability(cap)

        print(f"[{self.agent_id}] is running and listening for tasks.")

        # Agent is now running, return control to the caller
        # The main loop (if any) should be managed externally or by a dedicated task

    async def stop(self):
        """
        Stops the agent and shuts down its services.
        """
        print(f"[{self.agent_id}] Stopping...")
        self.is_running = False
        shutdown_services()
        print(f"[{self.agent_id}] Stopped.")

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
        print(f"[{self.agent_id}] Received task request: {task_payload.get('request_id')} for capability '{task_payload.get('capability_id_filter')}' from '{sender_ai_id}'.")

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
            self.hsp_connector.send_task_result(result_payload, callback_topic)
            print(f"[{self.agent_id}] Sent NOT_IMPLEMENTED failure response to {callback_topic}")

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
