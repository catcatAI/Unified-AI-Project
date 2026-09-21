# -*- coding: utf-8 -*-
"""
Tests for MSBA MultimodalBlocks.
"""

import pytest

from ai.msba.multimodal_blocks import AudioBlock, VisionBlock


class TestVisionBlock:
    def test_creation(self):
        block = VisionBlock()
        assert block.block_id == "vision"
        assert len(block.hit_sources) == 7

    def test_get_activations_text(self):
        block = VisionBlock()
        result = block.get_hit_activations("What is in this image?")
        assert result["object_detection"] > 0.0
        assert result["scene_classification"] > 0.0

    def test_get_activations_no_vision_keywords(self):
        block = VisionBlock()
        result = block.get_hit_activations("hello world")
        assert all(v == 0.0 for v in result.values())

    def test_get_activations_with_image_data(self):
        block = VisionBlock()
        # image_data=None means no real analysis
        result = block.get_hit_activations("describe this picture", image_data=None)
        assert "object_detection" in result


class TestAudioBlock:
    def test_creation(self):
        block = AudioBlock()
        assert block.block_id == "audio"
        assert len(block.hit_sources) == 7

    def test_get_activations_text(self):
        block = AudioBlock()
        result = block.get_hit_activations("What does this sound like?")
        assert result["speech_recognition"] > 0.0
        assert result["music_detection"] > 0.0

    def test_get_activations_no_audio_keywords(self):
        block = AudioBlock()
        result = block.get_hit_activations("hello world")
        assert all(v == 0.0 for v in result.values())

    def test_get_activations_with_audio_data(self):
        block = AudioBlock()
        result = block.get_hit_activations("listen to this", audio_data=None)
        assert "speech_recognition" in result
