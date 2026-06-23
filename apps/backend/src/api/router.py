"""
API路由模块
"""

import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter()

# Import and include sub-routers
try:
    from api.routes.chat_routes import router as chat_router
    router.include_router(chat_router, prefix="/api/v1")
    logger.debug("Included chat_routes")
except ImportError as e:
    logger.warning(f"chat_routes not available: {e}")

try:
    from api.routes.desktop_routes import router as desktop_router
    router.include_router(desktop_router, prefix="/api/v1")
    logger.debug("Included desktop_routes")
except ImportError as e:
    logger.warning(f"desktop_routes not available: {e}")

try:
    from api.routes.ops_routes import router as ops_router
    router.include_router(ops_router, prefix="/api/v1")
    logger.debug("Included ops_routes")
except ImportError as e:
    logger.warning(f"ops_routes not available: {e}")

try:
    from api.v1.endpoints import include_endpoint_routers
    include_endpoint_routers(router, prefix="/api/v1")
    logger.debug("Included v1 endpoint routers")
except ImportError as e:
    logger.warning(f"v1 endpoint routers not available: {e}")

try:
    from api.routes.meta_routes import router as meta_router
    router.include_router(meta_router, prefix="/api/v1")
    logger.debug("Included meta_routes")
except ImportError as e:
    logger.warning(f"meta_routes not available: {e}")

try:
    from api.routes.multimodal_routes import router as multimodal_router
    router.include_router(multimodal_router, prefix="/api/v1")
    logger.debug("Included multimodal_routes")
except ImportError as e:
    logger.warning(f"multimodal_routes not available: {e}")

try:
    from api.routes.image_generation_routes import router as image_gen_router
    router.include_router(image_gen_router, prefix="/api/v1")
    logger.debug("Included image_generation_routes")
except ImportError as e:
    logger.warning(f"image_generation_routes not available: {e}")

