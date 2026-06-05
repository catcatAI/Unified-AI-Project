import logging

try:
    from core.intent_registry import IntentRegistry
except ImportError:
    IntentRegistry = None

logger = logging.getLogger(__name__)


async def init(deps: dict = None) -> IntentRegistry:
    return IntentRegistry()


def on_card_pipeline_ready(**data) -> None:
    logger.debug("on_card_pipeline_ready received: %s", data)
