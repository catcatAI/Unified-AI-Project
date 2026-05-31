"""Module wrapper for MathVerifier — initialized via lifespan.py, not module auto-start."""

import logging

from services.math_verifier import MathVerifier

logger = logging.getLogger(__name__)


async def init(deps: dict = None) -> MathVerifier:
    return MathVerifier()


async def start(instance: MathVerifier) -> None:
    logger.debug("MathVerifier start — deferred-init wrapper (no-op)")


async def stop(instance: MathVerifier) -> None:
    logger.debug("MathVerifier stop — deferred-init wrapper (no-op)")
