
import logging
import sys
import os
import asyncio

# Add src to path
sys.path.insert(0, os.path.abspath('apps/backend/src'))

output_file = 'logging_debug.txt'

with open(output_file, 'w') as f:
    try:
        from services.main_api_server import logger as app_logger, brain_bridge
        from services.brain_bridge_service import logger as bb_logger
    except ImportError as e:
        f.write(f"ImportError: {e}\n")
        sys.exit(1)

    f.write("="*40 + "\n")
    f.write("LOGGER CONFIGURATION\n")
    f.write("="*40 + "\n")
    root = logging.getLogger()
    f.write(f"Root handlers: {root.handlers}\n")
    f.write(f"App logger ({app_logger.name}) handlers: {app_logger.handlers}\n")
    f.write(f"BrainBridge logger ({bb_logger.name}) handlers: {bb_logger.handlers}\n")
    f.write(f"Propagate (App): {app_logger.propagate}\n")
    f.write(f"Propagate (BB): {bb_logger.propagate}\n")

    # Check if basicConfig was called
    if len(root.handlers) > 0:
        f.write(f"Root handler 0 type: {type(root.handlers[0])}\n")
    
    f.write("\n" + "="*40 + "\n")
    f.write("BRAIN BRIDGE STATE\n")
    f.write("="*40 + "\n")
    f.write(f"BrainBridge running: {brain_bridge._running}\n")
