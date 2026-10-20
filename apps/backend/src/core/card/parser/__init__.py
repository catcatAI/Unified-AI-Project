"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Card Import Pipeline — parser subpackage.
"""

import importlib
from typing import TYPE_CHECKING, Any, Optional


def _optional_import(qualified: str) -> Any:
    """Optional from-import with ImportError → None fallback.

    Equivalent to ``try: from mod import attr / except ImportError: attr = None``:
    module-load ImportError and missing attribute both resolve to None.
    """
    module_name, _, attr = qualified.rpartition(".")
    try:
        return getattr(importlib.import_module(module_name), attr, None)
    except ImportError:
        return None


if TYPE_CHECKING:
    from core.card.parser.conflict_detector import ConflictDetector
    from core.card.parser.deterministic_parser import DeterministicParser
    from core.card.parser.gdoc_reader import read_gdoc_file
    from core.card.parser.merge_engine import MergeEngine
    from core.card.parser.timeline_resolver import TimelineResolver
else:
    ConflictDetector = _optional_import("core.card.parser.conflict_detector.ConflictDetector")
    DeterministicParser = _optional_import(
        "core.card.parser.deterministic_parser.DeterministicParser"
    )
    read_gdoc_file = _optional_import("core.card.parser.gdoc_reader.read_gdoc_file")
    MergeEngine = _optional_import("core.card.parser.merge_engine.MergeEngine")
    TimelineResolver = _optional_import("core.card.parser.timeline_resolver.TimelineResolver")

__all__ = [
    "ConflictDetector",
    "DeterministicParser",
    "MergeEngine",
    "TimelineResolver",
    "read_gdoc_file",
]
