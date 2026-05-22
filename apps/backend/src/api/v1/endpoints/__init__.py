import logging

logger = logging.getLogger(__name__)


def include_endpoint_routers(parent_router):
    """Lazy-import endpoint modules and register their routers."""
    from . import drive, pet, vision, audio, tactile, mobile, economy, trace
    parent_router.include_router(drive.router)
    parent_router.include_router(pet.router)
    parent_router.include_router(vision.router)
    parent_router.include_router(audio.router)
    parent_router.include_router(tactile.router)
    parent_router.include_router(mobile.router)
    parent_router.include_router(economy.router)
    parent_router.include_router(trace.router)
