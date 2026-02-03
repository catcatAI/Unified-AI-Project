import sqlite3
from typing import Any


class DatabaseManager:
    """Manages database connections and operations.
    Uses SQLite for a simple in-memory database for demonstration.
    """

    def __init__(self, db_path: str = ":memory:"):
        """Initializes the DatabaseManager.

        Args:
            db_path (str): Path to the SQLite database file. Use ':memory:' for an in-memory database.

        """
        self.db_path = db_path
        self.connection: sqlite3.Connection | None = None
        print(f"DatabaseManager initialized for path: {db_path}")

    def connect(self) -> bool:
        """Establishes a connection to the database."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            self.connection = None
            return False
        else:
            return True

    def disconnect(self):
        """Closes the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            print(f"Disconnected from database: {self.db_path}")

    def execute_query(self, query: str, params: tuple = ()) -> list[Any] | None:
        """Executes a SQL query and returns results for SELECT statements.

        Args:
            query (str): The SQL query to execute.
            params (tuple): Parameters for the query.

        Returns:
            Optional[List[Any]]: List of rows for SELECT queries, None otherwise.

        """
        if not self.connection:
            print("Error: Not connected to database.")
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()  # Commit changes for INSERT/UPDATE/DELETE
            if query.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            return None
        except sqlite3.Error as e:
            print(f"Error executing query '{query}': {e}")
            return None


if __name__ == "__main__":
    # Example Usage
    db_manager = DatabaseManager()  # In-memory database

    print("\n--- Test Connection ---")
    if db_manager.connect():
        # Create a table
        db_manager.execute_query(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)",
        )
        print("Table 'users' created.")

        # Insert data
        db_manager.execute_query(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            ("Alice", "alice@example.com"),
        )
        db_manager.execute_query(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            ("Bob", "bob@example.com"),
        )
        print("Data inserted.")

        # Select data
        users = db_manager.execute_query("SELECT * FROM users")
        print("\n--- All Users ---")
        for user in users:
            print(user)

        # Select specific user
        bob = db_manager.execute_query("SELECT * FROM users WHERE name = ?", ("Bob",))
        print("\n--- Bob ---")
        print(bob)

        # Update data
        db_manager.execute_query(
            "UPDATE users SET email = ? WHERE name = ?",
            ("bob_new@example.com", "Bob"),
        )
        updated_bob = db_manager.execute_query(
            "SELECT * FROM users WHERE name = ?",
            ("Bob",),
        )
        print("\n--- Updated Bob ---")
        print(updated_bob)

        # Disconnect
        db_manager.disconnect()
    else:
        print("Failed to connect to database.")
