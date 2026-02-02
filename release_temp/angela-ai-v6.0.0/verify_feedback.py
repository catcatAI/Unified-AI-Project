import asyncio
import logging
import sys

# Configure logging to print to stdout
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', stream=sys.stdout)

from apps.backend.src.ai.dialogue.dialogue_manager import DialogueManager
from apps.backend.src.ai.memory.vector_store import VectorStore

async def main():
    print("\n--- Verifying VectorStore Feedback ---")
    # This should trigger the "LOCAL JSON PERSISTENCE MODE" warning
    vs = VectorStore(collection_name="test_feedback_collection")
    
    print("\n--- Verifying DialogueManager Feedback ---")
    dm = DialogueManager()
    # This should trigger the "[SIMULATION]" prefix and warning
    response = await dm.get_response("Hello", {"angela_mood": "happy"})
    print(f"Response: {response['response']}")

if __name__ == "__main__":
    asyncio.run(main())
