import asyncio
import uuid
import sys
from typing import Dict, Any

# Ensure the project root is in the Python path
sys.path.append('D:\Unified-AI-Project')

from src.core_services import initialize_services, get_services, shutdown_services, DEFAULT_LLM_CONFIG, DEFAULT_OPERATIONAL_CONFIGS

# --- CLI Specific AI ID ---
cli_ai_id = f"did:hsp:gemini_cli_instance_{uuid.uuid4().hex[:6]}"

async def chat_loop():
    """Main interactive chat loop with tool support."""
    services = get_services()
    dialogue_manager = services.get("dialogue_manager")
    tool_dispatcher = services.get("tool_dispatcher") # Get the tool_dispatcher

    if not dialogue_manager or not tool_dispatcher:
        print("Gemini CLI Error: DialogueManager or ToolDispatcher not available.")
        return

    session_id = f"gemini_cli_session_{uuid.uuid4().hex[:6]}"
    user_id = "gemini_cli_user"
    print(f"\n--- Gemini Interactive CLI (Tool Support Enabled) ---")
    print(f"Session ID: {session_id}")
    print("Type 'exit' or 'quit' to end the session.")
    print("---------------------------------")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting Gemini CLI...")
                break

            if not user_input.strip():
                continue

            # 1. Get initial response or tool call from DialogueManager
            dm_response = await dialogue_manager.get_response_with_tool_support(
                user_input=user_input,
                user_id=user_id,
                session_id=session_id
            )

            # 2. Check if the response is a tool call
            if dm_response.get("type") == "tool_call":
                tool_name = dm_response["tool_name"]
                tool_query = dm_response["tool_query"]
                action_params = dm_response.get("action_params", {})

                print(f"[CLI is executing tool: {tool_name} with query: '{tool_query}']")

                # 3. Execute the tool using the ToolDispatcher
                tool_result = tool_dispatcher.dispatch(
                    query=tool_query,
                    explicit_tool_name=tool_name,
                    **action_params
                )

                print(f"[CLI got tool result: {tool_result}]")

                # 4. Send the tool result back to the DialogueManager
                final_response = await dialogue_manager.get_response_from_tool_result(
                    tool_name=tool_name,
                    tool_result=tool_result,
                    session_id=session_id,
                    user_id=user_id
                )
                print(f"AI: {final_response}")

            # 5. If it's a regular text response, just print it
            elif dm_response.get("type") == "text":
                print(f"AI: {dm_response.get('content')}")
            else:
                print(f"AI: I received an unexpected response type: {dm_response.get('type')}")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting Gemini CLI...")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

def main():
    """Initializes services and runs the chat loop."""
    print(f"--- Unified-AI-Project Gemini CLI (Instance AI ID: {cli_ai_id}) ---")

    # Initialize core services, similar to the original CLI
    initialize_services(
        ai_id=cli_ai_id,
        use_mock_ham=True,
        llm_config=DEFAULT_LLM_CONFIG,
        operational_configs=DEFAULT_OPERATIONAL_CONFIGS
    )

    try:
        asyncio.run(chat_loop())
    except Exception as e:
        print(f"CLI Error: An unexpected error occurred during setup or runtime: {e}")
    finally:
        print("CLI: Initiating service shutdown...")
        shutdown_services()
        print("CLI: Exiting.")

if __name__ == '__main__':
    main()
