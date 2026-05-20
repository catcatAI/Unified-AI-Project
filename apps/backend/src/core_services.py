"""
Standalone CLI mode — real services are loaded when running the backend server.
CLI handlers gracefully degrade with "not available" messages.
"""

import logging

logger = logging.getLogger(__name__)

DEFAULT_OPERATIONAL_CONFIGS = {}


class _Services:
    def get(self, key, default=None):
        return default

    def __contains__(self, key):
        return False


_services = _Services()


async def initialize_services(config=None, ai_id=None, use_mock_ham=False, operational_configs=None):
    logger.info("CLI standalone mode: services will be loaded when backend starts")
    if ai_id:
        logger.info(f"CLI configured with AI ID: {ai_id}")


def get_services():
    return _services


async def shutdown_services():
    logger.info("CLI standalone mode: no services to shut down")
