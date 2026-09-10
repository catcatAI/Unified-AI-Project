"""
Test suite for Attractor Field
测试 记忆吸引子梯度场

测试场景：
1. 吸引子创建与属性
2. 梯度计算
3. 导航（梯度下降）
4. 吸引子命中检测
5. 混合行为生成
"""

import math

import pytest

try:
    from ai.memory.attractor_field import (
        BehaviorTone,
        GradientField,
        GradientResult,
        MemoryAttractor,
    )
except ImportError:
    pytest.skip("MemoryAttractor not available (stub module)", allow_module_level=True)


class TestMemoryAttractor:
    """MemoryAttractor 测试类"""

    def test_create_attractor(self):
        attractor = MemoryAttractor(
            coord=[0.7, 0.8, 0.6, 0.5, 0.5],
            description="温暖共情",
            behavior="我理解你的感受。",
            tone=BehaviorTone.SYMPATHETIC,
            mass=1.5,
            radius=0.3,
            tags=["共情", "温暖", "支持"],
        )
        assert attractor.mass == 1.5
        assert attractor.radius == 0.3
        assert BehaviorTone.SYMPATHETIC in attractor.tone

    def test_attractor_belongs_to_multiple_tones(self):
        attractor = MemoryAttractor(
            coord=[0.8, 0.5, 0.7, 0.6, 0.3],
            description="情绪激励",
            behavior="太棒了！",
            tone=BehaviorTone.EXCITED,
            mass=1.2,
        )
        assert len(attractor.tone) >= 1


class TestGradientField:
    """GradientField 测试类"""

    @pytest.fixture
    def field(self):
        return GradientField()

    def test_default_attractors_created(self, field):
        assert len(field.attractors) > 0

    def test_compute_gradient_near_attractor(self, field):
        empathy_coord = [0.7, 0.8, 0.9, 0.6, 0.5]
        result = field.compute_gradient(empathy_coord)
        assert result.gradient_strength > 0
        assert len(result.nearest_attractors) > 0

    def test_navigation_steps(self, field):
        start_state = [0.3, 0.4, 0.5, 0.5, 0.5]
        result = field.navigate(start_state, max_steps=5, dt=0.15)
        assert result.navigation_steps >= 0
        assert len(result.nearest_attractors) > 0

    def test_convergence(self, field):
        start_state = [0.3, 0.4, 0.5, 0.5, 0.5]
        result1 = field.navigate(start_state, max_steps=3, dt=0.15)
        result2 = field.navigate(start_state, max_steps=10, dt=0.15)
        assert result2.navigation_steps >= result1.navigation_steps

    def test_gradient_direction_toward_attractor(self, field):
        start = [0.1, 0.1, 0.1, 0.1, 0.1]
        result = field.navigate(start, max_steps=10, dt=0.15)

        closest_attractor = result.nearest_attractors[0][0]
        dist_start = math.sqrt(sum((s - a) ** 2 for s, a in zip(start, closest_attractor.coord)))
        dist_end = math.sqrt(sum((e - a) ** 2 for e, a in zip(result.current_state, closest_attractor.coord)))

        assert dist_end < dist_start or result.gradient_strength < 0.01

    def test_certainty_inverse_of_confusion(self, field):
        low_confusion_state = [0.5, 0.5, 0.5, 0.5, 0.9]
        high_confusion_state = [0.5, 0.5, 0.5, 0.5, 0.1]

        result_low = field.compute_gradient(low_confusion_state)
        result_high = field.compute_gradient(high_confusion_state)

        assert result_low.certainty >= result_high.certainty

    def test_attractor_influence_falls_off(self, field):
        coord_near = [0.65, 0.75, 0.85, 0.55, 0.45]
        coord_far = [0.2, 0.2, 0.2, 0.2, 0.2]

        result_near = field.compute_gradient(coord_near)
        result_far = field.compute_gradient(coord_far)

        assert result_near.gradient_strength >= result_far.gradient_strength

    def test_blended_behavior_not_empty(self, field):
        start = [0.5, 0.5, 0.5, 0.5, 0.5]
        result = field.navigate(start, max_steps=5, dt=0.15)
        assert result.blended_behavior != ""
        assert result.blended_tone in BehaviorTone

    def test_tone_mapping(self, field):
        tone_map = field._tone_mapping(BehaviorTone.SYMPATHETIC)
        assert len(tone_map) == 5
        assert 0.0 <= tone_map[2] <= 1.0

    def test_gaussian_decay(self, field):
        decay_0 = field._gaussian_decay(0, 0.3)
        decay_1 = field._gaussian_decay(0.3, 0.3)
        decay_2 = field._gaussian_decay(0.6, 0.3)

        assert decay_0 == 1.0
        assert 0.0 < decay_1 < 1.0
        assert 0.0 < decay_2 < decay_1

    def test_load_and_save_attractors(self, field):
        import json
        import os
        import tempfile

        attractor = MemoryAttractor(
            coord=[0.6, 0.6, 0.6, 0.6, 0.6],
            description="Test Attractor",
            behavior="Testing...",
            tone=BehaviorTone.CURIOUS,
            mass=1.0,
            radius=0.2,
            tags=["test"],
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            field.attractors = [attractor]
            field.save_attractors(temp_path)

        field2 = GradientField()
        field2.load_attractors(temp_path)

        assert len(field2.attractors) == 1
        assert field2.attractors[0].description == "Test Attractor"

        os.unlink(temp_path)


class TestBehaviorTone:
    """BehaviorTone 枚举测试"""

    def test_all_tones_exist(self):
        expected = ["certain", "warm", "hesitant", "curious", "sympathetic", "excited", "fearful", "calm"]
        actual = [t.value for t in BehaviorTone]
        for e in expected:
            assert e in actual

    def test_tone_count(self):
        assert len(BehaviorTone) == 8