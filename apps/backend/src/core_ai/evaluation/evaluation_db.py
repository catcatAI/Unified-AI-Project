import sqlite3
import logging
import json
from datetime import datetime
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class EvaluationDB:
    def __init__(self, db_path: str = "evaluations.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the SQLite database and creates the 'evaluations' table if it doesn't exist."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    feedback TEXT,
                    improvement_suggestions TEXT
                )
            """)
            conn.commit()
            logger.info(f"EvaluationDB initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error initializing EvaluationDB at {self.db_path}: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def add_evaluation(self, evaluation_data: Dict[str, Any]) -> int:
        """Adds a new evaluation record to the database. Returns the ID of the new record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        task_id = evaluation_data.get("task_id", "unknown")
        timestamp = evaluation_data.get("timestamp", datetime.now().isoformat())
        metrics = json.dumps(evaluation_data.get("metrics", {}))
        feedback = json.dumps(evaluation_data.get("feedback", {}))
        improvement_suggestions = json.dumps(evaluation_data.get("improvement_suggestions", []))

        cursor.execute("""
            INSERT INTO evaluations (task_id, timestamp, metrics, feedback, improvement_suggestions)
            VALUES (?, ?, ?, ?, ?)
        """, (task_id, timestamp, metrics, feedback, improvement_suggestions))
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.debug(f"Added evaluation for task {task_id} with ID: {record_id}")
        return record_id

    def get_evaluations_by_task_id(self, task_id: str) -> List[Dict[str, Any]]:
        """Retrieves all evaluations for a given task_id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM evaluations WHERE task_id = ? ORDER BY timestamp DESC", (task_id,))
        rows = cursor.fetchall()
        conn.close()
        
        evaluations = []
        for row in rows:
            evaluations.append({
                "id": row[0],
                "task_id": row[1],
                "timestamp": row[2],
                "metrics": json.loads(row[3]),
                "feedback": json.loads(row[4]),
                "improvement_suggestions": json.loads(row[5])
            })
        return evaluations

    def get_average_metrics(self, task_id: Optional[str] = None) -> Dict[str, float]:
        """Calculates average metrics across all or specific task evaluations."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT metrics FROM evaluations"
        params = ()
        if task_id:
            query += " WHERE task_id = ?"
            params = (task_id,)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        total_completion_time = 0.0
        total_success_rate = 0.0
        total_quality_score = 0.0
        count = 0

        for row in rows:
            metrics = json.loads(row[0])
            total_completion_time += metrics.get("completion_time", 0.0)
            total_success_rate += metrics.get("success_rate", 0.0)
            total_quality_score += metrics.get("quality_score", 0.0)
            count += 1
        
        if count == 0:
            return {"completion_time": 0.0, "success_rate": 0.0, "quality_score": 0.0}

        return {
            "completion_time": total_completion_time / count,
            "success_rate": total_success_rate / count,
            "quality_score": total_quality_score / count
        }

    def close(self):
        """Closes the database connection. (Not strictly necessary for sqlite3.connect, but good practice)."""
        pass

    def delete_db_file(self):
        """Deletes the database file. Use with caution, primarily for testing."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            logger.info(f"EvaluationDB file deleted: {self.db_path}")
        else:
            logger.warning(f"Attempted to delete non-existent EvaluationDB file: {self.db_path}")
