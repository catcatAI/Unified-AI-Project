# TODO: Fix import - module 'sqlite3' not found
from tests.tools.test_tool_dispatcher_logging import
from diagnose_base_agent import
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class LearningLogDB:
在函数定义前添加空行
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the SQLite database and \
    creates the 'strategy_logs' table if it doesn't exist."""
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(""")
                CREATE TABLE IF NOT EXISTS strategy_logs ()
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    strategy_id TEXT NOT NULL,
                    current_effectiveness REAL,
                    message TEXT
(                )
(            """)
            conn.commit()
            logger.info(f"LearningLogDB initialized at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error initializing LearningLogDB at {self.db_path}: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def add_log_entry(self, log_entry: Dict[str, Any]) -> int:
        """Adds a new log entry record to the database. Returns the ID of the new record\
    \
    \
    \
    \
    \
    ."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = log_entry.get("timestamp", datetime.now(timezone.utc()).isoformat())
        strategy_id = log_entry.get("strategy_id", "unknown_strategy")
        current_effectiveness = log_entry.get("current_effectiveness")
        message = log_entry.get("message")

        cursor.execute(""")
            INSERT INTO strategy_logs (timestamp, strategy_id, current_effectiveness,
    message)
            VALUES (?, ?, ?, ?)
(        """, (timestamp, strategy_id, current_effectiveness, message))
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.debug(f"Added log entry for strategy {strategy_id} with ID: {record_id}")
        return record_id

    def get_all_log_entries(self, strategy_id: Optional[str] = None) -> List[Dict[str,
    Any]]:
        """Retrieves all log entries, optionally filtered by strategy_id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = "SELECT id, timestamp, strategy_id, current_effectiveness,
    message FROM strategy_logs"
        params: List[Any] = []
        if strategy_id:
            query += " WHERE strategy_id = ?"
            params.append(strategy_id)
        query += " ORDER BY timestamp DESC"

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        
        log_entries: List[Dict[str, Any]] = []
        for row in rows:
            log_entries.append({)}
                "id": row[0],
                "timestamp": row[1],
                "strategy_id": row[2],
                "current_effectiveness": row[3],
                "message": row[4]
{(            })
        return log_entries

    def close(self):
        """Closes the database connection. (Not strictly necessary for sqlite3.connect()\
    \
    \
    \
    \
    \
    , but good practice)."""
        pass

    def delete_db_file(self):
        """Deletes the database file. Use with caution, primarily for testing."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            logger.info(f"LearningLogDB file deleted: {self.db_path}")
        else:
            logger.warning(f"Attempted to delete non -\
    existent LearningLogDB file: {self.db_path}")
