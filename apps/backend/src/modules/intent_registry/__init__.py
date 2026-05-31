import logging

from core.intent_registry import IntentRegistry

logger = logging.getLogger(__name__)


async def init(deps: dict = None) -> IntentRegistry:
    return IntentRegistry()


def on_card_pipeline_ready(**data):
    logger.debug("on_card_pipeline_ready received: %s", data)
