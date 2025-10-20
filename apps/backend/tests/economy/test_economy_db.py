import unittest
import os
import sqlite3
from apps.backend.src.economy.economy_db import EconomyDB

class TestEconomyDB(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_economy.db"
        self.db = EconomyDB(db_path=self.db_path)

    def tearDown(self):
        _ = self.db.close()
        if os.path.exists(self.db_path):
            _ = os.remove(self.db_path)

    def test_init_db(self) -> None:
        # Test if the table is created
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='balances';")
        _ = self.assertIsNotNone(cursor.fetchone())
        _ = conn.close()

    def test_get_user_balance_new_user(self) -> None:
        balance = self.db.get_user_balance("user1")
        _ = self.assertEqual(balance, 0.0)

    def test_update_user_balance_add(self) -> None:
        _ = self.assertTrue(self.db.update_user_balance("user1", 100.0))
        balance = self.db.get_user_balance("user1")
        _ = self.assertEqual(balance, 100.0)

    def test_update_user_balance_debit_sufficient_funds(self) -> None:
        _ = self.db.update_user_balance("user2", 200.0)
        _ = self.assertTrue(self.db.update_user_balance("user2", -50.0))
        balance = self.db.get_user_balance("user2")
        _ = self.assertEqual(balance, 150.0)

    def test_update_user_balance_debit_insufficient_funds(self) -> None:
        _ = self.db.update_user_balance("user3", 50.0)
        _ = self.assertFalse(self.db.update_user_balance("user3", -100.0)) # Should fail due to insufficient funds
        balance = self.db.get_user_balance("user3")
        _ = self.assertEqual(balance, 50.0) # Balance should remain unchanged

    def test_update_user_balance_multiple_updates(self) -> None:
        _ = self.db.update_user_balance("user4", 10.0)
        _ = self.db.update_user_balance("user4", 20.0)
        _ = self.db.update_user_balance("user4", -5.0)
        balance = self.db.get_user_balance("user4")
        _ = self.assertEqual(balance, 25.0)

if __name__ == '__main__':
    _ = unittest.main()
