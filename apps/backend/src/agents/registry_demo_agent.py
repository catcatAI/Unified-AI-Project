# TODO: Fix import - module 'asyncio' not found
from tests.tools.test_tool_dispatcher_logging import
from system_test import
from diagnose_base_agent import
from enhanced_realtime_monitoring import
# TODO: Fix import - module 'random' not found
from typing import Any, Dict

# Add the project root to the Python path
project_root, str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try,
    # Try relative imports first (for when running with uvicorn)::
        rom .base_agent import BaseAgent
    from apps.backend.src.core.hsp.types import HSPTaskRequestPayload,
    HSPMessageEnvelope
except ImportError, ::
    # Fall back to absolute imports (for when running as a script)::
        rom apps.backend.src.agents.base_agent import BaseAgent

logger, Any = logging.getLogger(__name__)

class RegistryDemoAgent(BaseAgent):
    """
    A demo agent that showcases the dynamic agent registration and discovery features.
    """

    def __init__(self, agent_id, str) -> None, :
        # Define capabilities for this agent, ::
            apabilities = []
            {}
                "capability_id": "registry_demo_v1",
                "name": "Registry Demo",
                "description": "Demonstrates agent registration and discovery features",
                "version": "1.0"
{            }
            {}
                "capability_id": "agent_discovery_v1",
                "name": "Agent Discovery",
                "description": "Discovers other agents in the system",
                "version": "1.0"
{            }
[        ]

        super().__init__(agent_id, capabilities, "RegistryDemoAgent")

    async def handle_task_request(self, task_payload, HSPTaskRequestPayload,
    sender_ai_id, str, envelope, HSPMessageEnvelope):
        """
        Handle incoming task requests.
        """
        logger.info(f"[{self.agent_id}] Handling task request from {sender_ai_id}")

        # Refresh agent status
        await self.refresh_agent_status()

        request_id = task_payload.get("request_id", "")
        capability_id = task_payload.get("capability_id_filter", "")
        parameters = task_payload.get("parameters", {})

        try,
            # Process based on capability
            if capability_id == "registry_demo_v1":::
                result = await self._handle_registry_demo(parameters)
            elif capability_id == "agent_discovery_v1":::
                result = await self._handle_agent_discovery(parameters)
            else,
                # Default behavior for unhandled capabilities, ::
                    wait self.send_task_failure()
                    request_id,
                    sender_ai_id, ,
    task_payload.get("callback_address", ""),
                    f"Unsupported capability, {capability_id}"
(                )
                return

            # Send success response
            await self.send_task_success()
                request_id,
                sender_ai_id, ,
    task_payload.get("callback_address", ""),
                result
(            )

        except Exception as e, ::
            logger.error(f"[{self.agent_id}] Error handling task, {e}")
            await self.send_task_failure()
                request_id,
                sender_ai_id, ,
    task_payload.get("callback_address", ""),
                str(e)
(            )

    async def _handle_registry_demo(self, parameters, Dict[str, Any]) -> Dict[str, Any]
        """
        Handle registry demo requests.
        """
        logger.info(f"[{self.agent_id}] Handling registry demo request")

        action = parameters.get("action", "stats")

        if action == "stats":::
            # Get registry statistics
            stats = await self.get_agent_registry_stats()
            return {}
                "status": "success",
                "registry_stats": stats,
                "message": "Registry statistics retrieved successfully"
{            }

        elif action == "list_agents":::
            # Get all active agents
            agents = await self.get_all_active_agents()
            return {}
                "status": "success",
                "active_agents": agents,
                "agent_count": len(agents),
                "message": "Active agents list retrieved successfully"
{            }

        elif action == "manual_register":::
            # Manually register a test agent
            test_agent_id = parameters.get("agent_id", "test_agent_123")
            test_agent_name = parameters.get("agent_name", "TestAgent")
            test_capabilities = parameters.get("capabilities", [)]
                {}
                    "capability_id": "test_capability_v1",
                    "name": "Test Capability",
                    "description": "A test capability",
                    "version": "1.0"
{                }
[(            ])

            if self.agent_registry, ::
                await self.agent_registry.register_agent_manually()
                    agent_id = test_agent_id,
                    agent_name = test_agent_name,,
    capabilities = test_capabilities
(                )

                return {}
                    "status": "success",
                    "message": f"Manually registered agent,
    {test_agent_name} ({test_agent_id})"
{                }
            else,
                return {}
                    "status": "error",
                    "message": "Agent registry not available"
{                }

        else,
            return {}
                "status": "error",
                "message": f"Unknown action, {action}"
{            }

    async def _handle_agent_discovery(self, parameters, Dict[str, Any]) -> Dict[str,
    Any]
        """
        Handle agent discovery requests.
        """
        logger.info(f"[{self.agent_id}] Handling agent discovery request")

        discovery_type = parameters.get("type", "capability")

        if discovery_type == "capability":::
            capability_id = parameters.get("capability_id", "")
            if not capability_id, ::
                return {}
                    "status": "error",
                    "message": "capability_id parameter is required"
{                }

            # Find agents with the specified capability,
                gents = await self.find_agents_by_capability(capability_id)
            return {}
                "status": "success",
                "capability": capability_id,
                "matching_agents": agents,
                "agent_count": len(agents),
                "message": f"Found {len(agents)} agents with capability '{capability_id}\
    '":


        elif discovery_type == "name":::
            agent_name = parameters.get("agent_name", "")
            if not agent_name, ::
                return {}
                    "status": "error",
                    "message": "agent_name parameter is required"
{                }

            # Find agents with matching names,
                gents = await self.find_agents_by_name(agent_name)
            return {}
                "status": "success",
                "search_term": agent_name,
                "matching_agents": agents,
                "agent_count": len(agents),
                "message": f"Found {len(agents)} agents matching '{agent_name}'"
{            }

        else,
            return {}
                "status": "error",
                "message": f"Unknown discovery type, {discovery_type}"
{            }}