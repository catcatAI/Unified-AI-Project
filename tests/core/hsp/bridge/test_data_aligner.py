"""Tests for DataAligner — data format alignment (outgoing/incoming)."""
import pytest
from core.hsp.bridge.data_aligner import DataAligner


class TestDataAligner:
    def test_init(self):
        da = DataAligner()
        assert da is not None

    def test_align_outgoing_identity(self):
        da = DataAligner()
        payload = {"key": "value", "num": 42}
        assert da.align_outgoing(payload) is payload

    def test_align_incoming_identity(self):
        da = DataAligner()
        payload = {"data": [1, 2, 3]}
        assert da.align_incoming(payload) is payload

    def test_align_empty_dict(self):
        da = DataAligner()
        assert da.align_outgoing({}) == {}
        assert da.align_incoming({}) == {}

    def test_align_nested_structure(self):
        da = DataAligner()
        nested = {"outer": {"inner": [1, 2, 3]}}
        result = da.align_outgoing(nested)
        assert result["outer"]["inner"] == [1, 2, 3]
