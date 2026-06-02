"""Tests for economy/economy_manager.py"""
import pytest


class TestEconomyManager:
    """Tests for EconomyManager"""

    def test_import(self):
        from economy.economy_manager import EconomyManager
        assert EconomyManager is not None

    def test_instantiation_defaults(self):
        from economy.economy_manager import EconomyManager
        instance = EconomyManager(config={})
        assert instance is not None
        assert instance.rules["transaction_tax_rate"] == 0.05
        assert instance.rules["daily_coin_allowance"] == 10.0

    def test_instantiation_with_config(self):
        from economy.economy_manager import EconomyManager
        instance = EconomyManager(config={"initial_tax_rate": 0.1, "initial_allowance": 20.0})
        assert instance.rules["transaction_tax_rate"] == 0.1
        assert instance.rules["daily_coin_allowance"] == 20.0

    def test_item_registry_has_items(self):
        from economy.economy_manager import EconomyManager
        instance = EconomyManager(config={})
        assert "digital_energy_drink" in instance.item_registry
        assert "premium_bio_pellets" in instance.item_registry
        assert "medical_kit" in instance.item_registry
        assert "toy" in instance.item_registry
        assert len(instance.item_registry) >= 6

    def test_get_balance_default(self):
        from economy.economy_manager import EconomyManager
        instance = EconomyManager(config={})
        balance = instance.get_balance("new_user")
        assert balance == 0.0
