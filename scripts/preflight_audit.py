import os
import sys
import shutil
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PreFlight")

def check_dependencies():
    logger.info("Checking System Dependencies...")
    deps = {
        "tesseract": shutil.which("tesseract"),
        "ffmpeg": shutil.which("ffmpeg"),
        "python": sys.executable
    }
    for name, path in deps.items():
        if path:
            logger.info(f"  [OK] {name} found at: {path}")
        else:
            logger.warning(f"  [MISSING] {name} is NOT in system PATH. Some features will fail.")

def check_module_load():
    logger.info("Verifying Module Integration...")
    # Add src to path to simulate backend environment
    sys.path.append(os.path.abspath("apps/backend/src"))
    
    try:
        from ai.translation.simultaneous_translation import SimultaneousTranslationService
        from ai.alignment.emotion_system import EmotionSystem
        from services.audio_service import AudioService
        from ai.memory.ham_memory.ham_manager import HAMMemoryManager
        from integrations.os_bridge_adapter import OSBridgeAdapter
        
        logger.info("  [OK] All core modules imported successfully without circular dependencies.")
    except Exception as e:
        logger.error(f"  [FAIL] Module Import Error: {e}")
        import traceback
        traceback.print_exc()

def verify_bridge_path():
    logger.info("Verifying OS Bridge Pathing...")
    # Based on OSBridgeAdapter logic:
    # ../../../../gemini-os-bridge/bridge.py relative to integrations/
    base_dir = os.path.abspath("apps/backend/src/integrations")
    bridge_path = os.path.abspath(os.path.join(base_dir, "../../../../gemini-os-bridge/bridge.py"))
    
    if os.path.exists(bridge_path):
        logger.info(f"  [OK] Bridge script found at: {bridge_path}")
    else:
        logger.error(f"  [FAIL] Bridge script NOT found at: {bridge_path}")

if __name__ == "__main__":
    check_dependencies()
    check_module_load()
    verify_bridge_path()
