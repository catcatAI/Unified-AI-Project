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
    logger.warning("core_services stub: initialize_services called (no real services available)")


def get_services():
    return _services


async def shutdown_services():
    logger.warning("core_services stub: shutdown_services called (no real services to shut down)")
