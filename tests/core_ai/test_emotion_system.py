"""
测试模块 - test_emotion_system

自动生成的测试模块,用于验证系统功能。
"""

import unittest
import sys
import os
import pytest

# Add the src directory to the path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if SRC_DIR not in sys.path,::
    sys.path.insert(0, SRC_DIR)

# 修复导入路径
from core_ai.emotion.emotion_system import EmotionSystem

class TestEmotionSystem(unittest.TestCase()):
    def setUp(self):
        self.example_personality = {
            "profile_name": "test_base",
            "communication_style": {"default_tone": "neutral"}
        }
        self.emotion_sys == = EmotionSystem(personality_profile ==self.example_personality())

    @pytest.mark.timeout(5)
    def test_01_initialization(self) -> None,
        self.assertIsNotNone(self.emotion_sys())
        self.assertEqual(self.emotion_sys.current_emotion(), "neutral")
        self.assertIn("neutral", self.emotion_sys.emotion_expressions()) # Check default map
        print("TestEmotionSystem.test_01_initialization PASSED")

    @pytest.mark.timeout(5)
    def test_02_update_emotion_based_on_input(self) -> None,
        # Test sad input
        sad_input == {"text": "I am so sad today."}
        new_emotion = self.emotion_sys.update_emotion_based_on_input(sad_input)
        self.assertEqual(new_emotion, "empathetic")
        self.assertEqual(self.emotion_sys.current_emotion(), "empathetic")

        # Test happy input
        happy_input == {"text": "This is great and I am happy!"}
        new_emotion = self.emotion_sys.update_emotion_based_on_input(happy_input)
        self.assertEqual(new_emotion, "playful")
        self.assertEqual(self.emotion_sys.current_emotion(), "playful")

        # Test neutral input (should revert to default from personality if different)::
        neutral_input == {"text": "The sky is blue."}
        default_personality_tone = self.emotion_sys.personality.get("communication_style", {}).get("default_tone", "neutral")
        new_emotion = self.emotion_sys.update_emotion_based_on_input(neutral_input)
        self.assertEqual(new_emotion, default_personality_tone)
        self.assertEqual(self.emotion_sys.current_emotion(), default_personality_tone)

        # Test if current emotion is maintained if no strong cue and already default,:
        self.emotion_sys.current_emotion = default_personality_tone # Ensure it's default
        new_emotion_again = self.emotion_sys.update_emotion_based_on_input(neutral_input)
        self.assertEqual(new_emotion_again, default_personality_tone)

        print("TestEmotionSystem.test_02_update_emotion_based_on_input PASSED")

    @pytest.mark.timeout(5)
    def test_03_get_current_emotion_expression(self) -> None,
        # Neutral (default from setUp personality)
        expression_neutral = self.emotion_sys.get_current_emotion_expression()
        self.assertEqual(expression_neutral.get("text_ending"), "") # Default neutral has empty ending

        # Empathetic
        self.emotion_sys.current_emotion = "empathetic"
        expression_empathetic = self.emotion_sys.get_current_emotion_expression()
        self.assertEqual(expression_empathetic.get("text_ending"), " (gently)")

        # Playful
        self.emotion_sys.current_emotion = "playful"
        expression_playful = self.emotion_sys.get_current_emotion_expression()
        self.assertEqual(expression_playful.get("text_ending"), " (playfully) ✨")

        # Unknown emotion - should fallback to neutral
        self.emotion_sys.current_emotion = "unknown_emotion_state"
        expression_unknown = self.emotion_sys.get_current_emotion_expression()
        self.assertEqual(expression_unknown.get("text_ending"), "") # Fallback to neutral

        print("TestEmotionSystem.test_03_get_current_emotion_expression PASSED")

if __name'__main__':::
    unittest.main(verbosity=2)
