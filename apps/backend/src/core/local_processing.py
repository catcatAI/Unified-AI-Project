import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class LocalProcessor:
    """Local data processor.

    Handles processing of data on the local machine without
    external service dependencies.
    """

    def __init__(self):
        self._processed_count = 0

    async def process(self, data: Optional[Any] = None, **kwargs) -> Dict[str, Any]:
        """Process data locally.

        Args:
            data: Data to process (string, dict, or other).
            **kwargs: Processing parameters.

        Returns:
            Processing result with status and metadata.
        """
        self._processed_count += 1
        result = {
            "status": "processed",
            "count": self._processed_count,
            "data_type": type(data).__name__ if data is not None else "None",
        }
        logger.debug("LocalProcessor: processed item %d", self._processed_count)
        return result

    def get_processed_count(self) -> int:
        """Return total processed item count."""
        return self._processed_count
