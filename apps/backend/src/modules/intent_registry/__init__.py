from core.intent_registry import IntentRegistry


async def init(deps: dict = None) -> IntentRegistry:
    return IntentRegistry()


def on_card_pipeline_ready(**data):
    pass
