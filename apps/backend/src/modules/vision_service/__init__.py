from services.vision_service import VisionService


async def init(deps: dict = None) -> VisionService:
    return VisionService()


async def start(instance: VisionService, deps: dict = None) -> None:
    await instance.initialize()


async def stop(instance: VisionService) -> None:
    await instance.shutdown()
