from services.tactile_service import TactileService


async def init(deps: dict = None) -> TactileService:
    return TactileService()
