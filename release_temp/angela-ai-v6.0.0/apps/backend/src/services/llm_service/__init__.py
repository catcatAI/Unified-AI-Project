# This file makes the 'llm_service' directory a Python package
# and creates a single, shared instance of the LLMManager.

import logging

from .model_manager import LLMManager

logger = logging.getLogger(__name__)

logger.info("Creating shared LLMManager instance...")
# Create a singleton instance that can be imported by other parts of the application
llm_manager = LLMManager()
logger.info("Shared LLMManager instance created.")
