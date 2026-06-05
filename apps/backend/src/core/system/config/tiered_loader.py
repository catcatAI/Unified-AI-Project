"""
Tiered Configuration Loader
Implements the Default -> User -> Angela priority chain.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG: Dict[str, Any] = {
    "standard": {
        "behavior": {
            "thresholds": {
                "engagement": 0.7,
                "attention": 0.5,
                "response_time": 2.0,
            }
        }
    }
}


def get_config(path: str) -> Optional[Dict[str, Any]]:
    """Retrieve config by dotted path (e.g. 'standard/behavior/thresholds')."""
    keys = path.split("/")
    val: Any = _DEFAULT_CONFIG
    for key in keys:
        if isinstance(val, dict):
            val = val.get(key)
        else:
            return None
        if val is None:
            return None
    return val if isinstance(val, dict) else None
