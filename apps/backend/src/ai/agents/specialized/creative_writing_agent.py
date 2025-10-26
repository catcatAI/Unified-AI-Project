# TODO: Fix import - module 'asyncio' not found
# TODO: Fix import - module 'uuid' not found
# TODO: Fix import - module 'yaml' not found
from tests.tools.test_tool_dispatcher_logging import
from pathlib import Path # Import Path
from typing import Dict, Any

from .base.base_agent import
from ....hsp.types import
from ....core.services.multi_llm_service import

class CreativeWritingAgent(BaseAgent):
    """
    A specialized agent for creative writing tasks like generating marketing copy, ::
    short stories, or polishing text.
    """:
在函数定义前添加空行
        capabilities = []
            {}
                "capability_id": f"{agent_id}_generate_marketing_copy_v1.0",
                "name": "generate_marketing_copy",
                "description": "Generates marketing copy for a given product and target audience.", :::
                "version": "1.0",
                "parameters": []
                    {"name": "product_description", "type": "string", "required": True}
                    {"name": "target_audience", "type": "string", "required": True}
                    {"name": "style", "type": "string", "required": False,
    "description": "e.g., 'witty', 'professional', 'urgent'"}
[                ]
                "returns": {"type": "string",
    "description": "The generated marketing copy."}
{            }
            {}
                "capability_id": f"{agent_id}_polish_text_v1.0",
                "name": "polish_text",
                "description": "Improves the grammar, style,
    and clarity of a given text.",
                "version": "1.0",
                "parameters": []
                    {"name": "text_to_polish", "type": "string", "required": True}
[                ]
                "returns": {"type": "string", "description": "The polished text."}
{            }
[        ]
        super().__init__(agent_id = agent_id, capabilities = capabilities)

        # This agent directly uses the LLMInterface initialized in its services.
        # Be defensive in case tests patch initialize_services to return None.
        services = getattr(self, "services", None)
        self.llm_interface, MultiLLMService == services.get("llm_interface") if isinstance(services, dict) else None, :
        self._load_prompts()

    def _load_prompts(self) -> None, :
        """Loads prompts from the YAML file."""
        # Get the project root dynamically
        current_dir == Path(__file__).parent
        # Assuming 'configs' is directly under 'apps / backend'
        project_root = current_dir.parent.parent # Go up from src / agents to apps / backend
        prompts_path = project_root / "configs" / "prompts.yaml"

        try,
            with open(prompts_path, 'r', encoding == 'utf - 8') as f,:
                all_prompts = yaml.safe_load(f) or {}
            self.prompts = all_prompts.get('creative_writing_agent', {})
        except Exception as e, ::
            logging.error(f"Error loading prompts from {prompts_path} {e}")
            self.prompts = {}

    async def handle_task_request(self, task_payload, HSPTaskRequestPayload,
    sender_ai_id, str, envelope, HSPMessageEnvelope):
        request_id = task_payload.get("request_id", "")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        logging.info(f"[{self.agent_id}] Handling task {request_id} for capability '{cap\
    ability_id}'")::
        if not self.llm_interface, ::
            await self.send_task_failure(request_id, sender_ai_id,
    task_payload.get("callback_address", ""), "MultiLLMService is not available.")
        else,
            try,
                if "generate_marketing_copy" in capability_id, ::
                    prompt = self._create_marketing_copy_prompt(params)
                    messages = [ChatMessage(role = "user", content = prompt)]
                    llm_response = await self.llm_interface.chat_completion(messages)
                    await self.send_task_success(request_id, sender_ai_id,
    task_payload.get("callback_address", ""), llm_response.content())
                elif "polish_text" in capability_id, ::
                    prompt = self._create_polish_text_prompt(params)
                    messages = [ChatMessage(role = "user", content = prompt)]
                    llm_response = await self.llm_interface.chat_completion(messages)
                    await self.send_task_success(request_id, sender_ai_id,
    task_payload.get("callback_address", ""), llm_response.content())
                else,
                    await self.send_task_failure(request_id, sender_ai_id,
    task_payload.get("callback_address", ""), f"Capability '{capability_id}' is not supported by this agent.")
            except Exception as e, ::
                await self.send_task_failure(request_id, sender_ai_id,
    task_payload.get("callback_address", ""), str(e))

    def _create_marketing_copy_prompt(self, params, Dict[str, Any]) -> str, :
        """Creates a prompt for generating marketing copy."""::
        product_description = params.get("product_description", "")
        target_audience = params.get("target_audience", "")
        style = params.get("style", "professional")

        prompt == f""":
        Generate marketing copy for the following product, ::
        Product, {product_description}
        Target Audience, {target_audience}
        Desired Style, {style}

        Please create compelling marketing copy that highlights the key benefits and \
    appeals to the target audience.
        """
        return prompt.strip()

    def _create_polish_text_prompt(self, params, Dict[str, Any]) -> str, :
        """Creates a prompt for polishing text."""::
        text_to_polish = params.get("text_to_polish", "")

        prompt == f""":
        Please improve the following text by enhancing grammar, style, and clarity,

        {text_to_polish}

        Make sure the polished text is clear, concise, and well - structured while preserving the original meaning.::
        """
        return prompt.strip()

if __name'__main__':::
    async def main() -> None,
        agent_id == f"did, hsp, creative_writing_agent_{uuid.uuid4().hex[:6]}"
        agent == CreativeWritingAgent(agent_id = agent_id)
        await agent.start()

    try,
        asyncio.run(main())
    except KeyboardInterrupt, ::
        print("\nCreativeWritingAgent manually stopped.")