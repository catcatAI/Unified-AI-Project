"""C6 — ValueRangeMapping and NeuroVocabulary mapping tests"""

import sys
sys.path.insert(0, 'apps/backend/src')


class TestValueRangeMapping:

    def setup_method(self):
        from ai.response.composer import NeuroVocabulary
        self.nv = NeuroVocabulary()

    def test_learn_and_get_description(self):
        self.nv.learn_mapping('gamma.indolence', 0.42, '午後賴床不想動')
        desc = self.nv.get_description('gamma.indolence', 0.42)
        assert desc == '午後賴床不想動'

    def test_get_description_none_for_unknown(self):
        desc = self.nv.get_description('gamma.indolence', 0.99)
        assert desc is None

    def test_get_description_none_for_unknown_axis(self):
        desc = self.nv.get_description('nonexistent.axis', 0.5)
        assert desc is None

    def test_learn_multiple_same_axis(self):
        self.nv.learn_mapping('gamma.indolence', 0.1, '很低')
        self.nv.learn_mapping('gamma.indolence', 0.9, '很高')
        desc_low = self.nv.get_description('gamma.indolence', 0.1)
        desc_high = self.nv.get_description('gamma.indolence', 0.9)
        assert desc_low == '很低'
        assert desc_high == '很高'

    def test_learn_narrow_on_same_value(self):
        self.nv.learn_mapping('gamma.indolence', 0.5, '初始描述')
        # Same value again should narrow and increase confidence
        self.nv.learn_mapping('gamma.indolence', 0.5, '更精確的描述')
        mappings = self.nv.get_value_range_mappings('gamma.indolence')
        assert len(mappings) == 1
        assert mappings[0].usage_count == 2
        assert mappings[0].confidence > 0.3

    def test_covers_method(self):
        from ai.response.composer import ValueRangeMapping
        from datetime import datetime
        m = ValueRangeMapping(
            axis_field='test.axis',
            range_lo=0.2,
            range_hi=0.8,
            description='中間值',
            confidence=0.5,
        )
        assert m.covers(0.5) is True
        assert m.covers(0.2) is True
        assert m.covers(0.8) is True
        assert m.covers(0.1) is False
        assert m.covers(0.9) is False

    def test_narrow_method(self):
        from ai.response.composer import ValueRangeMapping
        from datetime import datetime
        m = ValueRangeMapping(
            axis_field='test.axis',
            range_lo=0.0,
            range_hi=1.0,
            description='全部',
            confidence=0.3,
        )
        m.narrow(0.5)
        assert m.range_lo == 0.49
        assert m.range_hi == 0.51

    def test_serialize_mappings(self):
        self.nv.learn_mapping('alpha.energy', 0.8, '高能量')
        self.nv.learn_mapping('beta.curiosity', 0.2, '低好奇')
        serialized = self.nv.serialize_mappings()
        assert len(serialized) >= 2
        fields = {s['axis_field'] for s in serialized}
        assert 'alpha.energy' in fields
        assert 'beta.curiosity' in fields

    def test_serialize_mappings_empty(self):
        serialized = self.nv.serialize_mappings()
        assert serialized == []

    def test_load_mappings_from_config(self):
        self.nv.load_mappings_from_config([
            {'axis_field': 'gamma.trust', 'range_lo': 0.6, 'range_hi': 1.0,
             'description': '信任', 'confidence': 0.8, 'usage_count': 5},
        ])
        desc = self.nv.get_description('gamma.trust', 0.8)
        assert desc == '信任'

    def test_load_mappings_from_config_empty(self):
        self.nv.load_mappings_from_config([])
        # No crash

    def test_confidence_increases_with_usage(self):
        self.nv.learn_mapping('theta.meta', 0.3, '初始')
        m1 = self.nv.get_value_range_mappings('theta.meta')[0]
        assert m1.confidence == 0.3
        self.nv.learn_mapping('theta.meta', 0.3, '再次學習')
        m2 = self.nv.get_value_range_mappings('theta.meta')[0]
        assert m2.confidence > 0.3
