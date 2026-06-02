"""Tests for economy/economy_db.py"""
import pytest


class TestEconomyDB:
    """Tests for EconomyDB"""

    def test_import(self):
        from economy.economy_db import EconomyDB
        assert EconomyDB is not None

    def test_instantiation_in_memory(self):
        from economy.economy_db import EconomyDB
        instance = EconomyDB(db_path=":memory:")
        assert instance is not None
        assert instance.conn is not None
        assert instance.cursor is not None
        instance.close()
        assert instance.conn is None

    def test_add_and_get_balance(self):
        from economy.economy_db import EconomyDB
        instance = EconomyDB(db_path=":memory:")
        instance.add_balance("user1", 100.0)
        balance = instance.get_balance("user1")
        assert balance == 100.0
        instance.close()

    def test_add_balance_multiple(self):
        from economy.economy_db import EconomyDB
        instance = EconomyDB(db_path=":memory:")
        instance.add_balance("user1", 50.0)
        instance.add_balance("user1", 25.0)
        assert instance.get_balance("user1") == 75.0
        instance.close()

    def test_get_balance_nonexistent(self):
        from economy.economy_db import EconomyDB
        instance = EconomyDB(db_path=":memory:")
        balance = instance.get_balance("nonexistent")
        assert balance == 0.0
        instance.close()

    def test_transfer_balance(self):
        from economy.economy_db import EconomyDB
        instance = EconomyDB(db_path=":memory:")
        instance.add_balance("alice", 100.0)
        instance.add_balance("bob", 50.0)
        instance.transfer("alice", "bob", 30.0)
        assert instance.get_balance("alice") == 70.0
        assert instance.get_balance("bob") == 80.0
        instance.close()
