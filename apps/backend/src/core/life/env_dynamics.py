# ANGELA-MATRIX: L0[基础层] [A] L1

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class EnvironmentDynamics:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def get_dynamic_threshold(self, key: str, default: float = 0.0) -> float:
        return self.config.get(key, default)
