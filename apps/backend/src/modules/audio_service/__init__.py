from services.audio_service import AudioService


async def init(deps: dict = None) -> AudioService:
    return AudioService()
