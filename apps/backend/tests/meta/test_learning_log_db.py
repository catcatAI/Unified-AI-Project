import unittest
import os
import sqlite3
import json
from datetime import datetime
from apps.backend.src.ai.meta.learning_log_db import LearningLogDB

class TestLearningLogDB(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_learning_logs.db"
        self.db = LearningLogDB(db_path=self.db_path)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strategy_logs';")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_add_log_entry(self):
        log_entry_data = {
            "timestamp": datetime.now().isoformat(),
            "strategy_id": "strategy_A",
            "current_effectiveness": 0.85,
            "message": "Strategy improved"
        }
        record_id = self.db.add_log_entry(log_entry_data)
        self.assertIsInstance(record_id, int)
        self.assertGreater(record_id, 0)

        # Verify data was inserted
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM strategy_logs WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[2], "strategy_A")
        self.assertEqual(row[3], 0.85)

    def test_get_all_log_entries(self):
        log1 = {"strategy_id": "strategy_X", "current_effectiveness": 0.7, "timestamp": "2023-01-01T10:00:00"}
        log2 = {"strategy_id": "strategy_Y", "current_effectiveness": 0.9, "timestamp": "2023-01-01T11:00:00"}
        log3 = {"strategy_id": "strategy_X", "current_effectiveness": 0.75, "timestamp": "2023-01-01T12:00:00"}
        self.db.add_log_entry(log1)
        self.db.add_log_entry(log2)
        self.db.add_log_entry(log3)

        all_logs = self.db.get_all_log_entries()
        self.assertEqual(len(all_logs), 3)
        self.assertEqual(all_logs[0]["strategy_id"], "strategy_X") # Ordered by timestamp DESC

        strategy_x_logs = self.db.get_all_log_entries(strategy_id="strategy_X")
        self.assertEqual(len(strategy_x_logs), 2)
        self.assertEqual(strategy_x_logs[0]["current_effectiveness"], 0.75)

    def test_get_all_log_entries_empty(self):
        logs = self.db.get_all_log_entries("non_existent_strategy")
        self.assertEqual(len(logs), 0)

if __name__ == '__main__':
    unittest.main()
