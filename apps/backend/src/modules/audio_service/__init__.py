try:
    from services.audio_service import AudioService
except ImportError:
    AudioService = None


async def init(deps: dict = None) -> AudioService:
    return AudioService()
