import sqlite3
from typing import Dict, Optional

class EconomyDB:
    """
    Handles all database operations for the economy system.
    Initializes the SQLite database and creates the 'balances' table if it doesn't exist.
    """

    def __init__(self, db_path: str = "economy.db") -> None:
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._connect()
        self._create_table()

    def _connect(self) -> None:
        """Connects to the SQLite database."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def _create_table(self) -> None:
        """Creates the balances table if it does not exist."""
        if self.cursor:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS balances (
                    user_id TEXT PRIMARY KEY,
                    balance REAL NOT NULL DEFAULT 0.0
                )
            """)
            if self.conn:
                self.conn.commit()

    def close(self) -> None:
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def add_balance(self, user_id: str, amount: float) -> None:
        """Adds a specified amount to a user's balance."""
        if self.cursor and self.conn:
            self.cursor.execute("""
                INSERT INTO balances (user_id, balance) VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET balance = balance + excluded.balance;
            """, (user_id, amount))
            self.conn.commit()

    def get_balance(self, user_id: str) -> float:
        """Retrieves the balance for a given user."""
        if self.cursor:
            self.cursor.execute("SELECT balance FROM balances WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            return result[0] if result else 0.0
        return 0.0

    def transfer_balance(self, from_user_id: str, to_user_id: str, amount: float) -> bool:
        """Transfers a balance from one user to another."""
        if amount <= 0:
            return False

        from_balance = self.get_balance(from_user_id)
        if from_balance < amount:
            return False

        if self.cursor and self.conn:
            # Use a transaction
            try:
                # Debit from sender
                self.cursor.execute("UPDATE balances SET balance = balance - ? WHERE user_id = ?", (amount, from_user_id))
                # Credit to receiver
                self.cursor.execute("""
                    INSERT INTO balances (user_id, balance) VALUES (?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET balance = balance + excluded.balance;
                """, (to_user_id, amount))
                self.conn.commit()
                return True
            except sqlite3.Error:
                self.conn.rollback()
                return False
        return False

    def delete_user(self, user_id: str) -> None:
        """Deletes a user from the balances table."""
        if self.cursor and self.conn:
            self.cursor.execute("DELETE FROM balances WHERE user_id = ?", (user_id,))
            self.conn.commit()

    def get_all_balances(self) -> Dict[str, float]:
        """Retrieves all user balances from the database."""
        if self.cursor:
            self.cursor.execute("SELECT user_id, balance FROM balances")
            return {row[0]: row[1] for row in self.cursor.fetchall()}
        return {}

    def reset_database(self) -> None:
        """Drops the existing balances table and recreates it."""
        if self.cursor and self.conn:
            self.cursor.execute("DROP TABLE IF EXISTS balances")
            self._create_table()
            self.conn.commit()
