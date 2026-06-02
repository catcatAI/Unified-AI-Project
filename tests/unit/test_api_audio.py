"""Tests for api/v1/endpoints/audio.py"""
import pytest


class TestAudioEndpoint:
    """Tests for audio endpoint module"""

    def test_import(self):
        from api.v1.endpoints.audio import router
        assert router is not None
        assert router.prefix == "/audio"

    def test_router_tags(self):
        from api.v1.endpoints.audio import router
        assert "Audio" in router.tags
