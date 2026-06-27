import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ElementLayer:
    """
    Handles decomposition and transformation of input/output into fundamental
    data elements based on the Fragmenta architecture.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.transformation_count = 0
        logger.debug("ElementLayer initialized.")

    def process_elements(self, data_elements: List[Any]) -> List[Any]:
        """
        Processes a list of data elements by applying registered transformations.
        """
        logger.info(f"Processing {len(data_elements)} elements.")
        processed_elements: List[Any] = []
        for element in data_elements:
            transformed_element = self._transform_element(element)
            self.transformation_count += 1
            processed_elements.append(transformed_element)
        return processed_elements

    def _transform_element(self, element: Any, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Transforms a single element based on its type.
        Supports dict, list, str, and numeric types.
        """
        if isinstance(element, dict):
            element["processed_by_element_layer"] = True
            for key, val in element.items():
                if isinstance(val, str):
                    element[key] = val.strip()
        elif isinstance(element, str):
            element = element.strip()
        elif isinstance(element, (int, float)):
            element = element * self.config.get("scale_factor", 1.0)
        return element


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("--- ElementLayer Example ---")
    layer = ElementLayer()
    sample_data = [
        {"type": "text", "content": "Hello world"},
        {"type": "emotion_cue", "value": "happy"},
    ]
    processed = layer.process_elements(sample_data)
    logger.info(f"Processed elements: {processed}")
    logger.info("ElementLayer example finished.")
