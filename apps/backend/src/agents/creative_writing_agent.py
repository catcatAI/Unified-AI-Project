import asyncio
import uuid
import os
import logging
from typing import Dict, Any, List

from .base_agent import BaseAgent
from hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope, ChatMessage
from core.services.multi_llm_service import MultiLLMService


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
                "description": "Polishes given text for grammar, style, and clarity.",
                "version": "1.0",
                "parameters": [
                    {"name": "text_to_polish", "type": "string", "required": True}
                ],
                "returns": {"type": "string", "description": "The polished text."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities)
        # Initialize the LLM interface
        self.llm_interface = MultiLLMService()
        logging.info(f"[{self.agent_id}] CreativeWritingAgent initialized with capabilities: {[cap['name'] for cap in capabilities]}")

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        request_id = task_payload.get("request_id")
        capability_id = task_payload.get("capability_id_filter", "")
        params = task_payload.get("parameters", {})

        logging.info(f"[{self.agent_id}] Handling task {request_id} for capability '{capability_id}'")

        try:
            if "generate_marketing_copy" in capability_id:
                result = await self._generate_marketing_copy(params)
                result_payload = self._create_success_payload(request_id, result)
            elif "polish_text" in capability_id:
                result = await self._polish_text(params)
                result_payload = self._create_success_payload(request_id, result)
            else:
                result_payload = self._create_failure_payload(request_id, "CAPABILITY_NOT_SUPPORTED", f"Capability '{capability_id}' is not supported by this agent.")
        except Exception as e:
            logging.error(f"[{self.agent_id}] Error processing task {request_id}: {e}")
            result_payload = self._create_failure_payload(request_id, "EXECUTION_ERROR", str(e))

        if self.hsp_connector and task_payload.get("callback_address"):
            callback_topic = task_payload["callback_address"]
            await self.hsp_connector.send_task_result(result_payload, callback_topic)
            logging.info(f"[{self.agent_id}] Sent task result for {request_id} to {callback_topic}")

    async def _generate_marketing_copy(self, params: Dict[str, Any]) -> str:
        """Generates marketing copy based on product description and target audience."""
        product_description = params.get('product_description', '')
        target_audience = params.get('target_audience', '')
        style = params.get('style', 'professional')

        if not product_description or not target_audience:
            raise ValueError("Both product_description and target_audience are required")

        # Create a prompt for the LLM
        prompt = f"""
        Generate marketing copy for the following product:
        
        Product: {product_description}
        Target Audience: {target_audience}
        Style: {style}
        
        The marketing copy should be compelling and highlight the key benefits of the product.
        """
        
        # Use the LLM service to generate the copy
        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.llm_interface.chat_completion(messages=messages)
        
        return response.content

    async def _polish_text(self, params: Dict[str, Any]) -> str:
        """Polishes text for grammar, style, and clarity."""
        text_to_polish = params.get('text_to_polish', '')

        if not text_to_polish:
            raise ValueError("text_to_polish is required")

        # Create a prompt for the LLM
        prompt = f"""
        Please proofread and polish the following text for grammar, style, and clarity.
        Return only the improved text without any additional comments:
        
        Text: {text_to_polish}
        """
        
        # Use the LLM service to polish the text
        messages = [ChatMessage(role="user", content=prompt)]
        response = await self.llm_interface.chat_completion(messages=messages)
        
        return response.content

    def _create_success_payload(self, request_id: str, result: str) -> HSPTaskResultPayload:
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