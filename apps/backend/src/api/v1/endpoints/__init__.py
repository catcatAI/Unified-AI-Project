import logging

logger = logging.getLogger(__name__)


def include_endpoint_routers(parent_router, prefix: str = "") -> None:
    """Lazy-import endpoint modules and register their routers."""
    from . import audio as _audio
    from . import drive as _drive
    from . import economy as _economy
    from . import mobile as _mobile
    from . import pet as _pet
    from . import plugins as _plugins
    from . import tactile as _tactile
    from . import trace as _trace
    from . import vision as _vision
    parent_router.include_router(_drive.router, prefix=prefix)
    parent_router.include_router(_pet.router, prefix=prefix)
    parent_router.include_router(_vision.router, prefix=prefix)
    parent_router.include_router(_audio.router, prefix=prefix)
    parent_router.include_router(_tactile.router, prefix=prefix)
    parent_router.include_router(_mobile.router, prefix=prefix)
    parent_router.include_router(_economy.router, prefix=prefix)
    parent_router.include_router(_trace.router, prefix=prefix)
    parent_router.include_router(_plugins.router, prefix=prefix)


