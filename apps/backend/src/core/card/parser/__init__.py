"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
Card Import Pipeline — parser subpackage.
"""

try:
    from core.card.parser.conflict_detector import ConflictDetector
except ImportError:
    ConflictDetector = None
try:
    from core.card.parser.deterministic_parser import DeterministicParser
except ImportError:
    DeterministicParser = None
try:
    from core.card.parser.gdoc_reader import read_gdoc_file
except ImportError:
    read_gdoc_file = None
try:
    from core.card.parser.merge_engine import MergeEngine
except ImportError:
    MergeEngine = None
try:
    from core.card.parser.timeline_resolver import TimelineResolver
except ImportError:
    TimelineResolver = None

__all__ = [
    "ConflictDetector",
    "DeterministicParser",
    "MergeEngine",
    "TimelineResolver",
    "read_gdoc_file",
]
