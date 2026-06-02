"""Tests for ai.deep_mapper.mapper"""
import pytest
from shared.types.mappable_data_object import MappableDataObject


class TestDeepMapper:
    """Tests for DeepMapper mapping engine"""

    def test_import(self):
        """Verify DeepMapper is importable"""
        from ai.deep_mapper.mapper import DeepMapper
        assert hasattr(DeepMapper, 'map')
        assert hasattr(DeepMapper, 'reverse_map')
        assert hasattr(DeepMapper, 'load_mapping_rules')

    def test_instantiation(self):
        """Verify basic instantiation with defaults"""
        from ai.deep_mapper.mapper import DeepMapper
        instance = DeepMapper()
        assert instance.mapping_rules == {}
        instance2 = DeepMapper(mapping_rules={"a": "b"})
        assert instance2.mapping_rules == {"a": "b"}

    def test_map_simple(self):
        """Verify simple key mapping works"""
        from ai.deep_mapper.mapper import DeepMapper
        mapper = DeepMapper(mapping_rules={"old_key": "new_key"})
        mdo = MappableDataObject(data={"old_key": 42}, metadata={})
        result = mapper.map(mdo)
        assert result.data == {"new_key": 42}

    def test_map_preserves_unmapped_keys(self):
        """Verify keys not in rules are preserved"""
        from ai.deep_mapper.mapper import DeepMapper
        mapper = DeepMapper(mapping_rules={"a": "x"})
        mdo = MappableDataObject(data={"a": 1, "b": 2}, metadata={})
        result = mapper.map(mdo)
        assert result.data == {"x": 1, "b": 2}

    def test_map_nested(self):
        """Verify nested dict mapping works recursively"""
        from ai.deep_mapper.mapper import DeepMapper
        mapper = DeepMapper(mapping_rules={"outer": {"inner": "renamed"}})
        mdo = MappableDataObject(data={"outer": {"inner": "value"}}, metadata={})
        result = mapper.map(mdo)
        assert result.data == {"outer": {"renamed": "value"}}

    def test_map_list(self):
        """Verify list mapping applies rules to each element"""
        from ai.deep_mapper.mapper import DeepMapper
        mapper = DeepMapper(mapping_rules={"x": "y"})
        mdo = MappableDataObject(data=[{"x": 1}, {"x": 2}], metadata={})
        result = mapper.map(mdo)
        assert result.data == [{"y": 1}, {"y": 2}]

    def test_map_value_remap(self):
        """Verify value-based remapping (data in rules dict)"""
        from ai.deep_mapper.mapper import DeepMapper
        mapper = DeepMapper(mapping_rules={1: "one", 2: "two"})
        mdo = MappableDataObject(data=1, metadata={})
        result = mapper.map(mdo)
        assert result.data == "one"

    def test_reverse_map(self):
        """Verify reverse_map inverts mapping rules"""
        from ai.deep_mapper.mapper import DeepMapper
        mapper = DeepMapper(mapping_rules={"old_key": "new_key"})
        mdo = MappableDataObject(data={"new_key": 99}, metadata={})
        result = mapper.reverse_map(mdo)
        assert result.data == {"old_key": 99}

    def test_reverse_map_nested(self):
        """Verify reverse_map handles nested rules"""
        from ai.deep_mapper.mapper import DeepMapper
        mapper = DeepMapper(mapping_rules={"outer": {"inner": "renamed"}})
        mdo = MappableDataObject(data={"outer": {"renamed": "val"}}, metadata={})
        result = mapper.reverse_map(mdo)
        assert result.data == {"outer": {"inner": "val"}}

    def test_metadata_preserved(self):
        """Verify metadata is preserved through mapping"""
        from ai.deep_mapper.mapper import DeepMapper
        mapper = DeepMapper(mapping_rules={"a": "x"})
        mdo = MappableDataObject(data={"a": 1}, metadata={"source": "test"})
        result = mapper.map(mdo)
        assert result.metadata == {"source": "test"}

    def test_empty_mapping_rules(self):
        """Verify map with empty rules returns data unchanged"""
        from ai.deep_mapper.mapper import DeepMapper
        mapper = DeepMapper()
        mdo = MappableDataObject(data={"key": "value"}, metadata={})
        result = mapper.map(mdo)
        assert result.data == {"key": "value"}
