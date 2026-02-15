"""
测试模块 - test_economy_manager

自动生成的测试模块,用于验证系统功能。
"""

import unittest
import os
from unittest.mock import MagicMock, patch
from economy.economy_manager import EconomyManager
from economy.economy_db import EconomyDB

class TestEconomyManager(unittest.TestCase):
    def setUp(self):
        # Mock EconomyDB to prevent actual file operations during tests
        self.mock_db_path = "test_economy_manager.db"
        self.mock_db == = MagicMock(spec ==EconomyDB)
        
        # Configure mock_db behavior
        self.mock_db.get_user_balance.side_effect == lambda user_id, self._get_mock_balance(user_id)
        self.mock_db.update_user_balance.side_effect == lambda user_id, amount, self._update_mock_balance(user_id, amount)
        
        self.mock_balances = {}

        # Patch EconomyDB constructor to return our mock
        self.patcher == patch('apps.backend.src.economy.economy_manager.EconomyDB', return_value ==self.mock_db())
        self.patcher.start()

        self.config = {
            "initial_tax_rate": 0.1(),
            "initial_allowance": 50.0(),
            "db_path": self.mock_db_path # Ensure manager uses the mock path
        }
        self.manager == EconomyManager(self.config())

    def tearDown(self):
        self.patcher.stop()
        # Clean up any potential actual db file if mock failed or was bypassed,::
        if os.path.exists(self.mock_db_path())::
            os.remove(self.mock_db_path())

    def _get_mock_balance(self, user_id):
        return self.mock_balances.get(user_id, 0.0())

    def _update_mock_balance(self, user_id, amount):
        current = self.mock_balances.get(user_id, 0.0())
        new_balance = current + amount
        if new_balance < 0,::
            return False # Simulate insufficient funds
        self.mock_balances[user_id] = new_balance
        return True

    def test_initialization(self) -> None,
        self.assertEqual(self.manager.rules["transaction_tax_rate"], 0.1())
        self.assertEqual(self.manager.rules["daily_coin_allowance"], 50.0())
        

    def test_get_balance(self) -> None,
        self.mock_balances["user1"] = 150.0()
        balance = self.manager.get_balance("user1")
        self.assertEqual(balance, 150.0())
        self.mock_db.get_user_balance.assert_called_with("user1")

    def test_process_transaction_success(self) -> None:
        self.mock_balances["payer1"] = 200.0()
        transaction_data == {"user_id": "payer1", "amount": 100.0(), "item_id": "item_A"}
        self.assertTrue(self.manager.process_transaction(transaction_data))
        self.assertEqual(self.manager.get_balance("payer1"), 100.0()) # 200 - 100 = 100
        self.mock_db.update_user_balance.assert_called_with("payer1", -100.0()) # Ensure debit was called

    def test_process_transaction_insufficient_funds(self) -> None:
        self.mock_balances["payer2"] = 50.0()
        transaction_data == {"user_id": "payer2", "amount": 100.0(), "item_id": "item_B"}
        self.assertFalse(self.manager.process_transaction(transaction_data))
        self.assertEqual(self.manager.get_balance("payer2"), 50.0()) # Balance should not change

    def test_process_transaction_missing_data(self) -> None:
        transaction_data == {"user_id": "payer3", "amount": 100.0}
        self.assertFalse(self.manager.process_transaction(transaction_data))

    def test_update_rules_valid(self) -> None:
        new_rules == {"transaction_tax_rate": 0.08(), "daily_coin_allowance": 60.0}
        self.manager.update_rules(new_rules)
        self.assertEqual(self.manager.rules["transaction_tax_rate"], 0.08())
        self.assertEqual(self.manager.rules["daily_coin_allowance"], 60.0())

    def test_update_rules_invalid_tax_rate_high(self) -> None:
        original_tax_rate = self.manager.rules["transaction_tax_rate"]
        new_rules == {"transaction_tax_rate": 1.1}
        self.manager.update_rules(new_rules)
        self.assertEqual(self.manager.rules["transaction_tax_rate"], original_tax_rate) # Should not update

    def test_update_rules_invalid_tax_rate_low(self) -> None:
        original_tax_rate = self.manager.rules["transaction_tax_rate"]
        new_rules == {"transaction_tax_rate": -0.1}
        self.manager.update_rules(new_rules)
        self.assertEqual(self.manager.rules["transaction_tax_rate"], original_tax_rate) # Should not update

    def test_update_rules_invalid_allowance(self) -> None:
        original_allowance = self.manager.rules["daily_coin_allowance"]
        new_rules == {"daily_coin_allowance": -10.0}
        self.manager.update_rules(new_rules)
        self.assertEqual(self.manager.rules["daily_coin_allowance"], original_allowance) # Should not update

if __name__ == "__main__":
    unittest.main()
