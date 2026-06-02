"""Tests for UnifiedSymbolicSpace"""
import os
import pytest
from apps.backend.src.ai.symbolic_space.unified_symbolic_space import UnifiedSymbolicSpace

TEST_DB = "test_uss_temp.db"


class TestUnifiedSymbolicSpace:
    def setup_method(self, method=None):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def teardown_method(self, method=None):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def _make_uss(self):
        return UnifiedSymbolicSpace(db_path=TEST_DB)

    def test_import(self):
        from apps.backend.src.ai.symbolic_space.unified_symbolic_space import UnifiedSymbolicSpace
        assert hasattr(UnifiedSymbolicSpace, 'add_symbol')
        assert hasattr(UnifiedSymbolicSpace, 'get_symbol')
        assert hasattr(UnifiedSymbolicSpace, 'update_symbol')
        assert hasattr(UnifiedSymbolicSpace, 'delete_symbol')
        assert hasattr(UnifiedSymbolicSpace, 'add_relationship')
        assert hasattr(UnifiedSymbolicSpace, 'get_relationships')
        assert hasattr(UnifiedSymbolicSpace, 'delete_relationship')

    def test_instantiation(self):
        instance = self._make_uss()
        assert instance.db_path == TEST_DB

    def test_add_symbol(self):
        instance = self._make_uss()
        sid = instance.add_symbol("test_sym", "TestType", {"key": "val"})
        assert sid is not None
        assert isinstance(sid, int)
        assert sid > 0

    def test_add_symbol_no_properties(self):
        instance = self._make_uss()
        sid = instance.add_symbol("simple", "Simple")
        assert sid is not None

    def test_add_duplicate_symbol_updates(self):
        instance = self._make_uss()
        instance.add_symbol("dup", "Type1", {"a": 1})
        instance.add_symbol("dup", "Type2", {"b": 2})
        symbol = instance.get_symbol("dup")
        assert symbol["type"] == "Type2"
        assert symbol["properties"]["a"] == 1
        assert symbol["properties"]["b"] == 2

    def test_get_symbol(self):
        instance = self._make_uss()
        instance.add_symbol("found", "Test", {"x": 10})
        symbol = instance.get_symbol("found")
        assert symbol is not None
        assert symbol["symbol_name"] == "found"
        assert symbol["type"] == "Test"
        assert symbol["properties"] == {"x": 10}

    def test_get_symbol_not_found(self):
        instance = self._make_uss()
        symbol = instance.get_symbol("nonexistent")
        assert symbol is None

    def test_update_symbol_name(self):
        instance = self._make_uss()
        instance.add_symbol("old", "Type")
        assert instance.update_symbol("old", new_symbol_name="new") is True
        assert instance.get_symbol("old") is None
        assert instance.get_symbol("new") is not None

    def test_update_symbol_type(self):
        instance = self._make_uss()
        instance.add_symbol("typed", "OldType")
        instance.update_symbol("typed", new_type="NewType")
        assert instance.get_symbol("typed")["type"] == "NewType"

    def test_update_symbol_properties(self):
        instance = self._make_uss()
        instance.add_symbol("props", "T", {"a": 1})
        instance.update_symbol("props", properties={"b": 2})
        symbol = instance.get_symbol("props")
        assert symbol["properties"]["a"] == 1
        assert symbol["properties"]["b"] == 2

    def test_update_symbol_no_changes(self):
        instance = self._make_uss()
        instance.add_symbol("nochg", "T")
        assert instance.update_symbol("nochg") is False

    def test_delete_symbol(self):
        instance = self._make_uss()
        instance.add_symbol("del", "Type")
        assert instance.delete_symbol("del") is True
        assert instance.get_symbol("del") is None

    def test_delete_nonexistent_symbol(self):
        instance = self._make_uss()
        assert instance.delete_symbol("ghost") is False

    def test_add_relationship(self):
        instance = self._make_uss()
        instance.add_symbol("src", "Source")
        instance.add_symbol("tgt", "Target")
        rid = instance.add_relationship("src", "tgt", "related_to", {"s": 0.9})
        assert rid is not None
        assert isinstance(rid, int)

    def test_add_relationship_missing_source(self):
        instance = self._make_uss()
        instance.add_symbol("tgt", "Target")
        rid = instance.add_relationship("ghost", "tgt", "rel")
        assert rid is None

    def test_get_relationships(self):
        instance = self._make_uss()
        instance.add_symbol("alice", "Person")
        instance.add_symbol("bob", "Person")
        instance.add_relationship("alice", "bob", "knows")
        rels = instance.get_relationships("alice")
        assert len(rels) == 1
        assert rels[0]["type"] == "knows"
        assert rels[0]["source"] == "alice"
        assert rels[0]["target"] == "bob"

    def test_get_relationships_no_symbol(self):
        instance = self._make_uss()
        assert instance.get_relationships("ghost") == []

    def test_delete_relationship(self):
        instance = self._make_uss()
        instance.add_symbol("a", "A")
        instance.add_symbol("b", "B")
        rid = instance.add_relationship("a", "b", "connects")
        assert instance.delete_relationship(rid) is True
        assert len(instance.get_relationships("a")) == 0

    def test_delete_nonexistent_relationship(self):
        instance = self._make_uss()
        assert instance.delete_relationship(99999) is False

    def test_delete_symbol_cascades_relationships(self):
        instance = self._make_uss()
        instance.add_symbol("x", "X")
        instance.add_symbol("y", "Y")
        instance.add_relationship("x", "y", "links")
        instance.delete_symbol("x")
        assert len(instance.get_relationships("y")) == 0
