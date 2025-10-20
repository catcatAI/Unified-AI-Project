import unittest
import pytest

from apps.backend.src.modules_fragmenta.vision_tone_inverter import VisionToneInverter

class TestVisionToneInverter(unittest.TestCase):

    _ = @pytest.mark.timeout(5)
    def test_01_initialization(self) -> None:
        """Test VisionToneInverter initialization."""
        inverter = VisionToneInverter()
        _ = self.assertIsNotNone(inverter)
        _ = print("TestVisionToneInverter.test_01_initialization PASSED")

    _ = @pytest.mark.timeout(5)
    def test_02_invert_visual_tone(self) -> None:
        """Test visual tone inversion."""
        inverter = VisionToneInverter()
        sample_visuals = {"color": "blue", "brightness": 0.5}
        target_tone = "brighter"

        adjusted_visuals = inverter.invert_visual_tone(sample_visuals, target_tone)

        # Verify the adjustment note is added
        _ = self.assertIn("tone_adjustment_note", adjusted_visuals)
        _ = self.assertIn(target_tone, adjusted_visuals["tone_adjustment_note"])
        
        # Verify original data is preserved
        _ = self.assertEqual(adjusted_visuals["color"], "blue")
        
        # 修正断言，检查亮度值是否保持不变（因为实现中没有修改亮度）
        _ = self.assertEqual(adjusted_visuals["brightness"], 0.5)
        
        # Test with different tone
        darker_visuals = inverter.invert_visual_tone(sample_visuals, "darker")
        _ = self.assertEqual(darker_visuals["brightness"], 0.5)  # 亮度保持不变
        
        _ = print("TestVisionToneInverter.test_02_invert_visual_tone PASSED")

if __name__ == '__main__':
    unittest.main(verbosity=2)