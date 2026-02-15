import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai.integration.unified_control_center import UnifiedControlCenter
from pet.pet_manager import PetManager

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AGU_Loop_Verification")

async def verify_agu_loop():
    logger.info("=== Starting AGI Learning Loop & Pet Sync Verification ===")
    
    # 1. Initialize PetManager with a mock broadcast callback
    broadcast_received = []
    async def mock_broadcast(msg_type, payload):
        logger.info(f"📡 [MOCK WS] Broadcast received: {msg_type}")
        broadcast_received.append((msg_type, payload))

    pet_manager = PetManager(
        pet_id="test_angela",
        config={"initial_personality": {"curiosity": 0.5}},
        broadcast_callback=mock_broadcast
    )
    logger.info("✅ PetManager initialized with mock broadcast.")

    # 2. Initialize Unified Control Center
    ucc = UnifiedControlCenter()
    ucc.start()
    logger.info("✅ Unified Control Center initialized and started.")

    # 3. Define a complex task
    task = {
        "id": "task_phi_99",
        "name": "Social Intelligence Expansion",
        "description": "Analyze user interaction patterns to optimize empathy resonance.",
        "priority": 9,
        "type": "learning"
    }

    # 4. Process the task through the LUCP loop (Learn-Understand-Calculate-Perform)
    logger.info(f"🚀 Processing complex task: {task['name']}")
    result = await ucc.process_complex_task(task)
    
    logger.info(f"📊 Task processing result: {result['status']}")
    if result['status'] == 'success':
        logger.info(f"   - Evaluation Rating: {result['evaluation']['overall_rating']:.2f}")
        logger.info(f"   - New Strategy: {result['strategy_update']['new_strategy']}")
        logger.info(f"   - Reasoning: {result['evaluation']['suggestions']}")
    else:
        logger.error(f"   - Task failed/rejected: {result.get('error') or result.get('reason')}")

    # 5. Verify Pet Interaction and Sync
    logger.info("🧬 Testing Pet Interaction and Live2D Sync...")
    await pet_manager.handle_interaction({"type": "play"})
    
    # Wait a bit for the async notification task
    await asyncio.sleep(0.5)
    
    if any(msg[0] == "pet_state_update" for msg in broadcast_received):
        logger.info("✅ Live2D Sync Broadcast verified!")
        latest_state = broadcast_received[-1][1]['state']
        logger.info(f"   - Current Animation: {latest_state['current_animation']}")
        logger.info(f"   - Happiness: {latest_state['happiness']}")
    else:
        logger.error("❌ Live2D Sync Broadcast FAILED!")

    ucc.stop()
    logger.info("=== Verification Complete ===")

if __name__ == "__main__":
    asyncio.run(verify_agu_loop())
