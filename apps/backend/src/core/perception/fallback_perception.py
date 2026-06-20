import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FallbackPerception:
    """Fallback perception processor.

    Provides minimal perception processing when primary perception
    systems are unavailable.
    """

    def __init__(self):
        self._last_input: Optional[str] = None

    async def process(self, input_data: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Process input data as a fallback.

        Args:
            input_data: String input to process.
            **kwargs: Additional processing parameters.

        Returns:
            Processed result dict.
        """
        if input_data:
            self._last_input = input_data
        result = {
            "processed": bool(input_data),
            "length": len(input_data) if input_data else 0,
            "type": "text",
        }
        logger.debug("FallbackPerception: processed %d chars", result["length"])
        return result

    def get_last_input(self) -> Optional[str]:
        """Return the last processed input."""
        return self._last_input
