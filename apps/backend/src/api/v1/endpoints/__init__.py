import importlib
import logging

logger = logging.getLogger(__name__)

# Registration order preserved from the original explicit imports so route
# matching/shadowing behaviour is byte-identical when every module loads.
_ENDPOINT_MODULES = ("drive", "vision", "audio", "mobile", "trace", "plugins")


def include_endpoint_routers(parent_router, prefix: str = "") -> None:
    """Lazy-import endpoint modules and register their routers.

    Each module is imported in its own try/except: one optional-dependency
    failure (e.g. drive without the google extra, which imports
    googleapiclient at module level) must not take down the other five
    endpoint groups — previously a single ImportError here silently
    dropped the entire v1 endpoint bundle.
    """
    for module_name in _ENDPOINT_MODULES:
        try:
            module = importlib.import_module(f".{module_name}", __name__)
        except ImportError as e:
            logger.warning(
                "v1 endpoint '%s' unavailable: %s (install its optional dependency to enable)",
                module_name,
                e,
            )
            continue
        endpoint_router = getattr(module, "router", None)
        if endpoint_router is None:
            logger.warning("v1 endpoint '%s' defines no router; skipped", module_name)
            continue
        parent_router.include_router(endpoint_router, prefix=prefix)
        logger.debug("Included v1 endpoint router: %s", module_name)
