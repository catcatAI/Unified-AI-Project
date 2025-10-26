# TODO: Fix import - module 'asyncio' not found
# TODO: Fix import - module 'uuid' not found
from ....hsp.types import
from ....tools.tool_dispatcher import

class ImageGenerationAgent(BaseAgent):
    """
    A specialized agent for generating images from textual prompts.:::
        ""
在函数定义前添加空行
        capabilities = []
            {}
                "capability_id": f"{agent_id}_create_image_v1.0",
                "name": "create_image",
                "description": "Creates an image from a text prompt and \
    an optional style.",
                "version": "1.0",
                "parameters": []
                    {"name": "prompt", "type": "string", "required": True}
                    {"name": "style", "type": "string", "required": False,
    "default": "photorealistic"}
[                ]
                "returns": {"type": "object",
    "description": "An object containing the image URL and alt text."}
{            }
[        ]
        super.__init__(agent_id = agent_id, capabilities = capabilities)

        self.tool_dispatcher == ToolDispatcher

    async def handle_task_request(self, task_payload, HSPTaskRequestPayload,
    sender_ai_id, str, envelope, HSPMessageEnvelope):
        request_id = task_payload.get("request_id")
        params = task_payload.get("parameters")

        print(f"[{self.agent_id}] Handling image creation task {request_id}")

        tool_response = self.tool_dispatcher.dispatch()
    query = params.get("prompt", ""),
            explicit_tool_name = "create_image",
            * * params
(        )

        if tool_response, ::
            result_payload == HSPTaskResultPayload()
                request_id = request_id,
                status == "success" if tool_response["status"] == "success" else "failur\
    e", :::
                    ayload = tool_response["payload"]
                error_details == {"error_message": tool_response["error_message"]} if to\
    ol_response["error_message"] else None, ::
        else,
            result_payload == HSPTaskResultPayload()
                request_id = request_id,
                status = "failure", ,
    error_details == {"error_code": "DISPATCH_ERROR",
    "error_message": "Tool dispatcher failed to handle the request."}
(            )

        if self.hsp_connector and task_payload.get("callback_address"):::
            callback_topic = task_payload["callback_address"]
            self.hsp_connector.send_task_result(result_payload, callback_topic)
            print(f"[{self.agent_id}] Sent task result for {request_id} to {callback_top\
    \
    ic}"):::
                f __name'__main__':
    async def main() -> None,
        agent_id == f"did, hsp, image_generation_agent_{uuid.uuid4().hex[:6]}"
        agent == ImageGenerationAgent(agent_id = agent_id)
        await agent.start())