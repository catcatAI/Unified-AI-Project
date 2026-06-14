# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [C] [L0]
# =============================================================================
"""
GARDEN test fixtures.
"""

import os
import sys
import tempfile

import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from apps.backend.src.ai.garden.dictionary import VectorDictionary
from apps.backend.src.ai.garden.snn_core import TensorSNNCore
from apps.backend.src.ai.garden.garden_engine import GARDENEngine
from apps.backend.src.ai.garden.binary_store import BinaryStore
from apps.backend.src.ai.garden.kg_import import KGImporter


@pytest.fixture(scope="function")
def dictionary() -> VectorDictionary:
    """VectorDictionary with presets loaded."""
    d = VectorDictionary()
    d.load_presets()
    return d


@pytest.fixture(scope="function")
def snn_core() -> TensorSNNCore:
    """Empty TensorSNNCore with a few keys registered."""
    core = TensorSNNCore(timesteps=4)
    core._register_key("g1")
    core._register_key("g5")
    core._register_key("r1")
    core._register_key("r2")
    core._register_key("e1")
    core._register_key("c1")
    core.add_relation("g1", "g5", weight=0.9, bidirectional=True)
    core.add_relation("g5", "r1", weight=0.7, bidirectional=True)
    core.add_relation("g1", "r2", weight=0.5, bidirectional=True)
    core.add_relation("e1", "c1", weight=0.6, bidirectional=True)
    return core


@pytest.fixture(scope="function")
def engine() -> GARDENEngine:
    """GARDENEngine with presets loaded."""
    e = GARDENEngine()
    e.load_presets()
    return e


@pytest.fixture(scope="function")
def temp_dir() -> str:
    """Temporary directory for save/load tests."""
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


@pytest.fixture(scope="function")
def kg_importer() -> KGImporter:
    """Empty KGImporter instance."""
    return KGImporter()

