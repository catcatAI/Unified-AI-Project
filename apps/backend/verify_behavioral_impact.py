import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Setup logging to capture everything
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
root_logger.addHandler(handler)
logger = logging.getLogger("BehavioralVerification")

# Add src and project root to path
project_root = Path(__file__).parent
monorepo_root = project_root.parent.parent
sys.path.append(str(monorepo_root.absolute()))
sys.path.append(str((project_root / "src").absolute()))

async def verify_behavioral_impact():
    logger.info("=== Starting AGI Behavioral Impact Verification ===")
    
    from core.autonomous.digital_life_integrator import DigitalLifeIntegrator
    from services.brain_bridge_service import BrainBridgeService
    from services.angela_llm_service import AngelaLLMService
    from core.autonomous.action_executor import Action, ActionCategory, ActionPriority

    # 1. Initialize core system
    dli = DigitalLifeIntegrator()
    # Initialize components but don't start background loops
    try:
        await dli.initialize()
    except Exception as e:
        logger.error(f"DLI Initialization failed: {e}")
        import traceback
        traceback.print_exc()
    
    bridge = BrainBridgeService(dli)
    llm_service = AngelaLLMService()
    
    logger.info("System components initialized.")

    # 2. Test Sensation Bridge (Fixed Schema)
    logger.info("--- Phase 1: Sensation Bridge Verification ---")
    
    # Manually induce 'Exhaustion' and 'High Stress'
    bio = dli.biological_integrator
    bio.endocrine_system.energy_level = 0.1 # Very tired
    bio.endocrine_system.stress_level = 0.9 # Very stressed
    bio.nervous_system.arousal_level = 0.1  # Lethargic
    
    # Sync metrics
    await bridge.sync_metrics()
    
    # Verify file content
    status_file = Path("apps/backend/data/brain_status.json")
    if status_file.exists():
        with open(status_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.info(f"Bridge Snapshot: Energy={data['biological']['hormonal_effects']['energy']}, Stress={data['biological']['stress_level']}")
            if "biological" in data and "hormonal_effects" in data["biological"]:
                logger.info("✅ BrainBridgeService schema is correct (Nested).")
            else:
                logger.error("❌ BrainBridgeService schema is still flat or incorrect.")
    else:
        logger.error("❌ brain_status.json not found.")

    # 3. Test Prompt Injection
    logger.info("--- Phase 2: LLM Prompt Injection Verification ---")
    # Check if a few keywords are present
    prompt = llm_service._get_biological_state() # Assuming _get_biological_state returns the prompt string directly
    logger.info(f"Generated Bio-Prompt: \"{prompt}\"")
    if ("累" in prompt or "疲倦" in prompt) and "壓力極大" in prompt:
        logger.info("✅ AngelaLLMService is reflecting biological states in prompt.")
    else:
        logger.error("❌ AngelaLLMService failed to reflect biological states in prompt.")

    # 4. Test Behavioral Strain (Action Executor)
    logger.info("--- Phase 3: Behavioral Strain Verification ---")
    executor = dli.action_executor
    # Ensure DLI is connected (DLI.initialize does this, but we do it manually for safety here)
    executor.set_digital_life_integrator(dli)
    
    async def dummy_action(**kwargs):
        return "Done"

    action = Action.create(
        name="test_strain_action",
        category=ActionCategory.UI,
        priority=ActionPriority.NORMAL,
        function=dummy_action
    )
    
    start_time = asyncio.get_event_loop().time()
    await executor._execute_action(action)
    duration = asyncio.get_event_loop().time() - start_time
    
    logger.info(f"Action execution duration under high strain: {duration:.2f}s")
    if duration > 0.5: # Should have a delay
        logger.info("✅ ActionExecutor is applying behavioral strain delay.")
    else:
        logger.error("❌ ActionExecutor performed action without strain delay.")

    # 5. Test Cognitive Load (UCC)
    logger.info("--- Phase 4: Cognitive Load Verification ---")
    ucc = dli.unified_control_center
    if ucc:
        ucc.set_digital_life_integrator(dli)
        
        # Simulate high cognitive gap
        # gap = (1 - L11) + complexity... 
        # Let's just mock the metrics return for the test
        dli.get_formula_metrics = lambda: {"current_metrics": {"cognitive_gap": 0.9}}
        
        start_time = asyncio.get_event_loop().time()
        await ucc.process_complex_task({"name": "Overwhelming Task"})
        duration = asyncio.get_event_loop().time() - start_time
        
        logger.info(f"UCC task duration under high cognitive load: {duration:.2f}s")
        if duration > 1.5: # 2.0s delay implemented
            logger.info("✅ UnifiedControlCenter is applying cognitive load delay.")
        else:
            logger.error("❌ UnifiedControlCenter ignored cognitive load.")
    else:
        logger.error("❌ UnifiedControlCenter was not initialized.")

    logger.info("=== Verification Complete ===")

if __name__ == "__main__":
    asyncio.run(verify_behavioral_impact())
