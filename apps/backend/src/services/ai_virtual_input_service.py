"""
DEPRECATED (P8-2): This module has been removed. All functionality is either migrated or obsolete.
"""
import logging
logger = logging.getLogger(__name__)
logger.warning("services.ai_virtual_input_service is deprecated and has been removed (P8-2)")


class AIVirtualInputService:
    """Deprecated stub. Preserved for backward compatibility with tests."""
    def __init__(self, initial_mode: str = "simulation_only"):
        self.mode = initial_mode
        self.logger = logger
