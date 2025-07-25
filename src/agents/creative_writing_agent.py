import asyncio
import uuid
from typing import Dict, Any, List

from src.agents.base_agent import BaseAgent
from src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
from src.services.llm_interface import LLMInterface

class CreativeWritingAgent(BaseAgent):
    """
    A specialized agent for creative writing tasks like generating marketing copy,
    short stories, or polishing text.
    """
    def __init__(self, agent_id: str):
        capabilities = [
            {
                "capability_id": f"{agent_id}_generate_marketing_copy_v1.0",
                "name": "generate_marketing_copy",
                "description": "Generates marketing copy for a given product and target audience.",
                "version": "1.0",
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
        super().__init__(agent_id=agent_id, capabilities=capabilities)

        # This agent directly uses the LLMInterface initialized in its services.
        self.llm_interface: LLMInterface = self.services.get("llm_interface")

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        request_id = task_payload.get("request_id")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        print(f"[{self.agent_id}] Handling task {request_id} for capability '{capability_id}'")

        if not self.llm_interface:
            result_payload = self._create_failure_payload(request_id, "INTERNAL_ERROR", "LLMInterface is not available.")
        else:
            try:
                if "generate_marketing_copy" in capability_id:
                    prompt = self._create_marketing_copy_prompt(params)
                    llm_response = await self.llm_interface.generate_response(prompt)
                    result_payload = self._create_success_payload(request_id, llm_response)
                elif "polish_text" in capability_id:
                    prompt = self._create_polish_text_prompt(params)
                    llm_response = await self.llm_interface.generate_response(prompt)
                    result_payload = self._create_success_payload(request_id, llm_response)
                else:
                    result_payload = self._create_failure_payload(request_id, "CAPABILITY_NOT_SUPPORTED", f"Capability '{capability_id}' is not supported by this agent.")
            except Exception as e:
                result_payload = self._create_failure_payload(request_id, "EXECUTION_ERROR", str(e))

        if self.hsp_connector and task_payload.get("callback_address"):
            callback_topic = task_payload["callback_address"]
            self.hsp_connector.send_task_result(result_payload, callback_topic)
            print(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}")

    def _create_marketing_copy_prompt(self, params: Dict[str, Any]) -> str:
        product = params.get('product_description', 'an unspecified product')
        audience = params.get('target_audience', 'a general audience')
        style = params.get('style', 'persuasive')
        return f"Generate marketing copy in a {style} tone for the following product: '{product}'. The target audience is: {audience}."

    def _create_polish_text_prompt(self, params: Dict[str, Any]) -> str:
        text = params.get('text_to_polish', '')
        return f"Please proofread and polish the following text for grammar, style, and clarity. Return only the improved text:\n\n---\n{text}\n---"

    def _create_success_payload(self, request_id: str, result: Any) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="success",
            payload=result
        )

    def _create_failure_payload(self, request_id: str, error_code: str, error_message: str) -> HSPTaskResultPayload:
        return HSPTaskResultPayload(
            request_id=request_id,
            status="failure",
            error_details={"error_code": error_code, "error_message": error_message}
        )

if __name__ == '__main__':
    async def main():
        agent_id = f"did:hsp:creative_writing_agent_{uuid.uuid4().hex[:6]}"
        agent = CreativeWritingAgent(agent_id=agent_id)
        await agent.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCreativeWritingAgent manually stopped.")
