"""Module wrapper for MathVerifier — initialized via lifespan.py, not module auto-start."""

from services.math_verifier import MathVerifier


async def init(deps: dict = None) -> MathVerifier:
    return MathVerifier()


async def start(instance: MathVerifier) -> None:
    pass


async def stop(instance: MathVerifier) -> None:
    pass
