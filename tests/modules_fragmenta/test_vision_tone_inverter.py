import pytest

pytest.importorskip("fragmenta.vision_tone_inverter")
from fragmenta.vision_tone_inverter import VisionToneInverter


class TestVisionToneInverter:
    async def test_vision_tone_instantiation(self):
        inverter = VisionToneInverter()
        assert inverter is not None

    async def test_vision_tone_brighter(self):
        inverter = VisionToneInverter()
        result = inverter.invert_visual_tone(
            {"color_palette": ["#333333"]}, "brighter"
        )
        assert result is not None
        assert "tone_adjustment_note" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
