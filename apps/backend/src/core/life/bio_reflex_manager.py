# ANGELA-MATRIX: L0[基础层] [A] L1

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class BiogenicReflexManager:
    def __init__(self, bio_integrator: Optional[Any] = None):
        self.bio_integrator = bio_integrator

    async def trigger_physical_trauma(self, body_part: str, damage: float) -> None:
        logger.warning(f"Physical trauma triggered: body_part={body_part}, damage={damage}")
        if self.bio_integrator and hasattr(self.bio_integrator, "on_trauma"):
            self.bio_integrator.on_trauma(body_part, damage)
