"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Card Import Pipeline — parser subpackage.
"""

from core.card.parser.conflict_detector import ConflictDetector
from core.card.parser.deterministic_parser import DeterministicParser
from core.card.parser.gdoc_reader import read_gdoc_file
from core.card.parser.merge_engine import MergeEngine
from core.card.parser.timeline_resolver import TimelineResolver

__all__ = [
    "ConflictDetector",
    "DeterministicParser",
    "MergeEngine",
    "TimelineResolver",
    "read_gdoc_file",
]
