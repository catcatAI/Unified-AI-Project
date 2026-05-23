import logging

logger = logging.getLogger(__name__)


def include_endpoint_routers(parent_router):
    """Lazy-import endpoint modules and register their routers."""
    from . import drive as _drive, pet as _pet, vision as _vision, audio as _audio
    from . import tactile as _tactile, mobile as _mobile, economy as _economy, trace as _trace
    parent_router.include_router(_drive.router)
    parent_router.include_router(_pet.router)
    parent_router.include_router(_vision.router)
    parent_router.include_router(_audio.router)
    parent_router.include_router(_tactile.router)
    parent_router.include_router(_mobile.router)
    parent_router.include_router(_economy.router)
    parent_router.include_router(_trace.router)


# Eager module references for direct importers (main_api_server.py, wiring.py)
from . import pet, economy
