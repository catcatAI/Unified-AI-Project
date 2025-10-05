import asyncio
import uuid
import yaml
import logging
from pathlib import Path # Import Path
from typing import Dict, Any

from .base.base_agent import BaseAgent
from ....hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
from ....core.services.multi_llm_service import MultiLLMService, ChatMessage

class CreativeWritingAgent(BaseAgent):
    """
    A specialized agent for creative writing tasks like generating marketing copy,:
hort stories, or polishing text.
    """
    def __init__(self, agent_id: str) -> None:
        capabilities = [
            {
                "capability_id": f"{agent_id}_generate_marketing_copy_v1.0",
                "name": "generate_marketing_copy",
                "description": "Generates marketing copy for a given product and target audience.",:
version": "1.0",
                "parameters": [
                    {"name": "product_description", "type": "string", "required": True},
                    {"name": "target_audience", "type": "string", "required": True},
                    {"name": "style", "type": "string", "required": False, "description": "e.g., 'witty', 'professional', 'urgent'"}
                ],
                "returns": {"type": "string", "description": "The generated marketing copy."}
            },
            {
                "capability_id": f"{agent_id}_polish_text_v1.0",
                "name": "polish_text",
                "description": "Improves the grammar, style, and clarity of a given text.",
                "version": "1.0",
                "parameters": [
                    {"name": "text_to_polish", "type": "string", "required": True}
                ],
                "returns": {"type": "string", "description": "The polished text."}
            }
        ]
        super.__init__(agent_id=agent_id, capabilities=capabilities)

        # This agent directly uses the LLMInterface initialized in its services.
        # Be defensive in case tests patch initialize_services to return None.
        services = getattr(self, "services", None)
        self.llm_interface: MultiLLMService = services.get("llm_interface") if isinstance(services, dict) else None:
elf._load_prompts()

    def _load_prompts(self) -> None:
        """Loads prompts from the YAML file."""
        # Get the project root dynamically
        current_dir = Path(__file__).parent
        # Assuming 'configs' is directly under 'apps/backend'
        project_root = current_dir.parent.parent # Go up from src/agents to apps/backend
        prompts_path = project_root / "configs" / "prompts.yaml"

        try:
            with open(prompts_path, 'r', encoding='utf-8') as f:
                all_prompts = yaml.safe_load(f) or {}
            self.prompts = all_prompts.get('creative_writing_agent', {}) 
        except Exception as e:
            logging.error(f"Error loading prompts from {prompts_path}: {e}")
            self.prompts = {}

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        request_id = task_payload.get("request_id", "")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", )

        logging.info(f"[{self.agent_id}] Handling task {request_id} for capability '{capability_id}'"):
f not self.llm_interface:
            result_payload = self._create_failure_payload(request_id, "INTERNAL_ERROR", "MultiLLMService is not available.")
        else:
            try:
                if "generate_marketing_copy" in capability_id:
                    prompt = self._create_marketing_copy_prompt(params)
                    messages = [ChatMessage(role="user", content=prompt)]
                    llm_response = await self.llm_interface.chat_completion(messages)
                    result_payload = self._create_success_payload(request_id, llm_response.content)
                elif "polish_text" in capability_id:
                    prompt = self._create_polish_text_prompt(params)
                    messages = [ChatMessage(role="user", content=prompt)]
                    llm_response = await self.llm_interface.chat_completion(messages)
                    result_payload = self._create_success_payload(request_id, llm_response.content)
                else:
                    result_payload = self._create_failure_payload(request_id, "CAPABILITY_NOT_SUPPORTED", f"Capability '{capability_id}' is not supported by this agent.")
            except Exception as e:
                result_payload = self._create_failure_payload(request_id, "EXECUTION_ERROR", str(e))

        callback_address = task_payload.get("callback_address")
        if self.hsp_connector and callback_address:
            callback_topic = str(callback_address) if callback_address is not None else "":
 = await self.hsp_connector.send_task_result(result_payload, callback_topic)
            logging.info(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}"):
f __name__ == '__main__':
    async def main() -> None:
        agent_id = f"did:hsp:creative_writing_agent_{uuid.uuid4().hex[:6]}"
        agent = CreativeWritingAgent(agent_id=agent_id)
        _ = await agent.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCreativeWritingAgent manually stopped.")