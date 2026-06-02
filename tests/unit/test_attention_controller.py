"""Tests for AttentionController and AttentionMode"""
import pytest
import time


class TestAttentionController:
    """Tests for AttentionController"""

    def test_import_classes(self):
        """Verify main classes and enums can be imported"""
        from core.perception.attention_controller import AttentionController, AttentionMode
        assert hasattr(AttentionController, 'update_target')
        assert hasattr(AttentionController, 'get_next_focus_point')
        assert hasattr(AttentionController, 'reset')
        assert hasattr(AttentionMode, 'EXPLORE')
        assert hasattr(AttentionMode, 'FOCUS')
        assert hasattr(AttentionMode, 'TRACK')
        assert hasattr(AttentionMode, 'IDLE')

    def test_attention_mode_enum(self):
        """Verify AttentionMode enum values are accessible"""
        from core.perception.attention_controller import AttentionMode
        assert isinstance(AttentionMode.EXPLORE.value, int)
        assert AttentionMode.EXPLORE != AttentionMode.FOCUS
        assert AttentionMode.FOCUS != AttentionMode.TRACK
        assert AttentionMode.TRACK != AttentionMode.IDLE
        modes = {AttentionMode.EXPLORE, AttentionMode.FOCUS, AttentionMode.TRACK, AttentionMode.IDLE}
        assert len(modes) == 4

    def test_instantiation(self):
        """Verify basic instantiation and core operations"""
        from core.perception.attention_controller import AttentionController, AttentionMode
        instance = AttentionController()
        assert instance.mode == AttentionMode.EXPLORE
        assert instance.last_focus_pos == (0.5, 0.5)
        assert instance.current_target_id is None
        assert instance.last_saccade_time == 0

        time.sleep(0.3)

        result = instance.update_target((0.8, 0.3), target_id="obj_1")
        assert result is True
        assert instance.mode == AttentionMode.FOCUS
        assert instance.last_focus_pos == (0.8, 0.3)
        assert instance.current_target_id == "obj_1"

        pos, target_id = instance.get_next_focus_point([])
        assert pos == (0.8, 0.3)
        assert target_id == "obj_1"

        instance.reset()
        assert instance.mode == AttentionMode.EXPLORE
        assert instance.current_target_id is None
        assert instance.last_focus_pos == (0.5, 0.5)
