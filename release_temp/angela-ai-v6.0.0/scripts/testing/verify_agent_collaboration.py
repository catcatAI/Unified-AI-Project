import asyncio
import logging
from typing import Dict, Any, Optional, List

# Configure logging for the test script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Imports from the project ---
# This assumes the script is run from the project root 'Unified-AI-Project'
from apps.backend.src.ai.agent_manager import AgentManager
from apps.backend.src.ai.agents.base_agent import BaseAgent
from apps.backend.src.ai.agents.conversational_agent import ConversationalAgent
from apps.backend.src.ai.agents.agent_collaboration_manager import AgentCollaborationManager

# --- Test-specific Agent Definition ---
class ReceiverAgent(BaseAgent):
    """A simple agent designed to receive a message and store it for verification."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_message_received: Optional[Dict[str, Any]] = None

    async def perceive(self, task: Dict[str, Any], retrieved_memories: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> Any:
        logging.info(f"[{self.name}] Perceiving task: {task.get('type')}")
        return task

    async def decide(self, perceived_info: Any, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Simple decision: just act on the received task
        return {"action": "store_message", "data": perceived_info}

    async def act(self, decision: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        if decision.get("action") == "store_message":
            message_data = decision.get("data")
            logging.info(f"[{self.name}] Storing message: {message_data}")
            self.last_message_received = message_data
            return {"status": "message_stored"}
        return {"status": "unknown_action"}

    async def feedback(self, original_task: Dict[str, Any], action_result: Any, context: Optional[Dict[str, Any]] = None) -> None:
        # No feedback action needed for this simple test agent
        pass

async def main():
    """
    Main function to verify the multi-agent collaboration system.
    """
    logging.info("--- Starting Agent Collaboration Verification ---")
    manager = AgentManager()

    # 1. Register Agent Types
    logging.info("Registering agent types...")
    manager.register_agent_type("ConversationalAgent", ConversationalAgent)
    manager.register_agent_type("ReceiverAgent", ReceiverAgent)
    manager.register_agent_type("AgentCollaborationManager", AgentCollaborationManager)

    # 2. Launch Agents
    logging.info("Launching agents...")
    # The collaboration manager needs access to the agent manager, which is injected automatically.
    collaboration_manager = await manager.launch_agent("AgentCollaborationManager", name="CollaborationManager")
    alice = await manager.launch_agent("ConversationalAgent", name="Alice")
    bob = await manager.launch_agent("ReceiverAgent", name="Bob")

    if not all([collaboration_manager, alice, bob]):
        logging.error("FAILED: One or more agents failed to launch. Aborting test.")
        return

    # Allow a moment for all agents to start their loops
    await asyncio.sleep(0.1)

    # 3. Send a message from Alice to Bob
    logging.info(f"Alice ({alice.agent_id}) is sending a message to Bob ({bob.agent_id})...")
    test_message = {"type": "personal_message", "content": "Hello Bob, this is a test."}
    
    # Use the agent's built-in send_message method, which uses the manager
    await alice.send_message(target_agent_id=bob.agent_id, message_content=test_message)

    # 4. Wait and Verify
    logging.info("Waiting for message to be processed...")
    await asyncio.sleep(1) # Give enough time for routing and processing

    logging.info(f"Checking Bob's last received message...")
    if bob.last_message_received == test_message:
        logging.info(f"SUCCESS: Bob received the correct message: {bob.last_message_received}")
    else:
        logging.error(f"FAILED: Bob's last message is incorrect or missing. Got: {bob.last_message_received}")

    # 5. Cleanup
    logging.info("Stopping all agents...")
    await manager.stop_agent(alice.agent_id)
    await manager.stop_agent(bob.agent_id)
    await manager.stop_agent(collaboration_manager.agent_id)
    
    # Final check to ensure the collaboration manager ID was cleared
    if manager.collaboration_manager_id is None:
        logging.info("SUCCESS: Collaboration manager ID was cleared on stop.")
    else:
        logging.error("FAILED: Collaboration manager ID was not cleared on stop.")

    logging.info("--- Agent Collaboration Verification Finished ---")


if __name__ == "__main__":
    asyncio.run(main())
