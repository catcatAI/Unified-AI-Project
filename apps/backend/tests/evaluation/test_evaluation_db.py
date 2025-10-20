import unittest
import os
import sqlite3
import json
from datetime import datetime
from apps.backend.src.ai.evaluation.evaluation_db import EvaluationDB

class TestEvaluationDB(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_evaluations.db"
        self.db = EvaluationDB(db_path=self.db_path)

    def tearDown(self):
        _ = self.db.close()
        _ = self.db.close()
        if os.path.exists(self.db_path):
            _ = os.remove(self.db_path)

    def test_init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='evaluations';")
        _ = self.assertIsNotNone(cursor.fetchone())
        _ = conn.close()

    def test_add_evaluation(self) -> None:
        evaluation_data = {
            "task_id": "task_1",
            _ = "timestamp": datetime.now().isoformat(),
            "metrics": {"completion_time": 10.0, "success_rate": 1.0, "quality_score": 0.9},
            "feedback": {"sentiment": "positive"},
            "improvement_suggestions": ["suggestion1"]
        }
        record_id = self.db.add_evaluation(evaluation_data)
        _ = self.assertIsInstance(record_id, int)
        _ = self.assertGreater(record_id, 0)

        # Verify data was inserted
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evaluations WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        _ = conn.close()
        _ = self.assertIsNotNone(row)
        _ = self.assertEqual(row[1], "task_1")
        _ = self.assertEqual(json.loads(row[3])["success_rate"], 1.0)

    def test_get_evaluations_by_task_id(self) -> None:
        eval1 = {"task_id": "task_A", "metrics": {"success_rate": 0.8}}
        eval2 = {"task_id": "task_B", "metrics": {"success_rate": 0.9}}
        eval3 = {"task_id": "task_A", "metrics": {"success_rate": 0.7}}
        _ = self.db.add_evaluation(eval1)
        _ = self.db.add_evaluation(eval2)
        _ = self.db.add_evaluation(eval3)

        evals_task_A = self.db.get_evaluations_by_task_id("task_A")
        _ = self.assertEqual(len(evals_task_A), 2)
        _ = self.assertEqual(evals_task_A[0]["metrics"]["success_rate"], 0.7) # Ordered by timestamp DESC

    def test_get_average_metrics(self) -> None:
        _ = self.db.add_evaluation({"task_id": "task_avg", "metrics": {"completion_time": 5.0, "success_rate": 1.0, "quality_score": 0.9}})
        _ = self.db.add_evaluation({"task_id": "task_avg", "metrics": {"completion_time": 7.0, "success_rate": 0.5, "quality_score": 0.6}})
        _ = self.db.add_evaluation({"task_id": "task_other", "metrics": {"completion_time": 3.0, "success_rate": 1.0, "quality_score": 0.8}})

        avg_all = self.db.get_average_metrics()
        _ = self.assertAlmostEqual(avg_all["completion_time"], (5.0 + 7.0 + 3.0) / 3)
        _ = self.assertAlmostEqual(avg_all["success_rate"], (1.0 + 0.5 + 1.0) / 3)
        _ = self.assertAlmostEqual(avg_all["quality_score"], (0.9 + 0.6 + 0.8) / 3)

        avg_task_avg = self.db.get_average_metrics(task_id="task_avg")
        _ = self.assertAlmostEqual(avg_task_avg["completion_time"], (5.0 + 7.0) / 2)
        _ = self.assertAlmostEqual(avg_task_avg["success_rate"], (1.0 + 0.5) / 2)
        _ = self.assertAlmostEqual(avg_task_avg["quality_score"], (0.9 + 0.6) / 2)

    def test_get_average_metrics_no_data(self) -> None:
        avg = self.db.get_average_metrics("non_existent_task")
        _ = self.assertEqual(avg["completion_time"], 0.0)
        _ = self.assertEqual(avg["success_rate"], 0.0)
        _ = self.assertEqual(avg["quality_score"], 0.0)

if __name__ == '__main__':
    _ = unittest.main()
