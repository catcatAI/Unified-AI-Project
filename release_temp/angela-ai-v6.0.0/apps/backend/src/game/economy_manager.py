import logging
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)


class EconomyDB:
    """Manages the SQLite database for economy-related data, primarily player balances."""

    def __init__(self, db_path: str = "economy.db"):
        self.db_path = db_path
        self.conn = None  # Persistent connection
        self._connect()
        self._initialize_db()
        logger.info(f"EconomyDB initialized with database: {self.db_path}")

    def _connect(self):
        """Establishes a persistent database connection."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Access columns by name
            logger.debug(f"Connected to database: {self.db_path}")

    def _initialize_db(self):
        """Initializes the database schema if it doesn't exist, including balances, items, and inventory."""
        if self.conn:
            cursor = self.conn.cursor()
            # Balances table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS balances (
                    user_id TEXT PRIMARY KEY,
                    balance REAL NOT NULL DEFAULT 0.0
                )
            """)
            # Items definition table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    item_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    base_price REAL NOT NULL DEFAULT 0.0,
                    category TEXT
                )
            """)
            # Inventory table (linking users to items)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    user_id TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (user_id, item_id),
                    FOREIGN KEY (user_id) REFERENCES balances(user_id),
                    FOREIGN KEY (item_id) REFERENCES items(item_id)
                )
            """)
            self.conn.commit()
            logger.info("EconomyDB schema initialized (balances, items, inventory).")

    def get_balance(self, user_id: str) -> float:
        """Retrieves the balance for a given user_id."""
        if not self.conn:
            self._connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT balance FROM balances WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        return result["balance"] if result else 0.0

    def update_balance(self, user_id: str, amount: float) -> bool:
        """Updates the balance for a given user_id by adding the amount.
        Amount can be positive (deposit) or negative (withdrawal).
        Returns True on success, False if balance would go below zero.
        """
        current_balance = self.get_balance(user_id)
        new_balance = current_balance + amount

        if new_balance < 0:
            logger.warning(
                f"Attempted to set negative balance for {user_id}. Current: {current_balance}, Change: {amount}",
            )
            return False

        if not self.conn:
            self._connect()
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO balances (user_id, balance) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET balance = ?
        """,
            (user_id, new_balance, new_balance),
        )
        self.conn.commit()
        logger.info(f"User {user_id} balance updated to {new_balance}")
        return True

    def add_item_definition(self, item_id: str, name: str, description: str, base_price: float, category: str) -> bool:
        """Adds or updates an item definition."""
        if not self.conn: self._connect()
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO items (item_id, name, description, base_price, category) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(item_id) DO UPDATE SET name=?, description=?, base_price=?, category=?
            """, (item_id, name, description, base_price, category, name, description, base_price, category))
            self.conn.commit()
            logger.info(f"Item definition '{item_id}' added/updated.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding/updating item definition '{item_id}': {e}")
            return False

    def get_item_definition(self, item_id: str) -> dict[str, Any] | None:
        """Retrieves an item definition by item_id."""
        if not self.conn: self._connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM items WHERE item_id = ?", (item_id,))
        result = cursor.fetchone()
        return dict(result) if result else None
    
    def get_all_item_definitions(self) -> list[dict[str, Any]]:
        """Retrieves all item definitions."""
        if not self.conn: self._connect()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM items")
        return [dict(row) for row in cursor.fetchall()]

    def add_item_to_inventory(self, user_id: str, item_id: str, quantity: int) -> bool:
        """Adds a quantity of an item to a user's inventory."""
        if not self.conn: self._connect()
        cursor = self.conn.cursor()
        try:
            # Ensure user exists (optional, could be done at higher level)
            self.get_balance(user_id) 
            # Ensure item exists
            if not self.get_item_definition(item_id):
                logger.warning(f"Attempted to add non-existent item '{item_id}' to inventory for '{user_id}'.")
                return False

            cursor.execute("""
                INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)
                ON CONFLICT(user_id, item_id) DO UPDATE SET quantity = quantity + ?
            """, (user_id, item_id, quantity, quantity))
            self.conn.commit()
            logger.info(f"Added {quantity} of '{item_id}' to '{user_id}'s inventory.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding item '{item_id}' to inventory for '{user_id}': {e}")
            return False

    def remove_item_from_inventory(self, user_id: str, item_id: str, quantity: int) -> bool:
        """Removes a quantity of an item from a user's inventory."""
        if not self.conn: self._connect()
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            result = cursor.fetchone()
            if not result or result["quantity"] < quantity:
                logger.warning(f"Insufficient quantity of '{item_id}' in '{user_id}'s inventory to remove {quantity}.")
                return False

            new_quantity = result["quantity"] - quantity
            if new_quantity == 0:
                cursor.execute("DELETE FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
            else:
                cursor.execute("UPDATE inventory SET quantity = ? WHERE user_id = ? AND item_id = ?", (new_quantity, user_id, item_id))
            self.conn.commit()
            logger.info(f"Removed {quantity} of '{item_id}' from '{user_id}'s inventory. Remaining: {new_quantity}.")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error removing item '{item_id}' from inventory for '{user_id}': {e}")
            return False

    def get_user_inventory(self, user_id: str) -> list[dict[str, Any]]:
        """Retrieves a user's inventory."""
        if not self.conn: self._connect()
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT i.item_id, i.name, i.description, i.base_price, i.category, inv.quantity
            FROM inventory AS inv
            JOIN items AS i ON inv.item_id = i.item_id
            WHERE inv.user_id = ?
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info(f"EconomyDB connection to {self.db_path} closed.")


class EconomyManager:
    """
    Client for the EconomyManagerActor.
    Delegates calls to the remote EconomyManagerActor instance.
    """

    def __init__(self, config: dict[str, Any], db: EconomyDB | None = None):
        # Initialize Ray if not already done (for safety)
        if not ray.is_initialized():
            ray.init(ignore_reinit_error=True)
            
        self.actor = EconomyManagerActor.remote(config, db) # Create the remote actor
        logger.info("EconomyManager client initialized, EconomyManagerActor created.")

    def get_balance(self, user_id: str) -> float:
        """Returns the current balance of a user."""
        return ray.get(self.actor.get_balance.remote(user_id))

    def process_transaction(self, transaction_data: dict[str, Any]) -> bool:
        """Processes a transaction, applying tax and updating balances.
        transaction_data should contain 'user_id', 'amount' (cost of item/service).
        Returns True if the transaction is successful, False otherwise (e.g., insufficient funds).
        """
        return ray.get(self.actor.process_transaction.remote(transaction_data))

    def update_rules(self, new_rules: dict[str, Any]):
        """Updates the economic rules dynamically."""
        return ray.get(self.actor.update_rules.remote(new_rules))

    def reward_user(self, user_id: str, amount: float) -> bool:
        """Rewards a user with a certain amount of coins.
        This is a convenience wrapper around update_balance.
        """
        return ray.get(self.actor.reward_user.remote(user_id, amount))
    
    # --- Item and Inventory Management ---
    def add_item_definition(self, item_id: str, name: str, description: str, base_price: float, category: str) -> bool:
        """Adds or updates an item definition in the database."""
        return ray.get(self.actor.add_item_definition.remote(item_id, name, description, base_price, category))

    def get_item_definition(self, item_id: str) -> dict[str, Any] | None:
        """Retrieves an item definition by item_id."""
        return ray.get(self.actor.get_item_definition.remote(item_id))
    
    def get_all_item_definitions(self) -> list[dict[str, Any]]:
        """Retrieves all item definitions."""
        return ray.get(self.actor.get_all_item_definitions.remote())

    def buy_item(self, user_id: str, item_id: str, quantity: int = 1) -> bool:
        """Allows a user to buy an item. Deducts cost from balance and adds to inventory."""
        return ray.get(self.actor.buy_item.remote(user_id, item_id, quantity))

    def sell_item(self, user_id: str, item_id: str, quantity: int = 1) -> bool:
        """Allows a user to sell an item. Adds value to balance and removes from inventory."""
        return ray.get(self.actor.sell_item.remote(user_id, item_id, quantity))

    def get_user_inventory(self, user_id: str) -> list[dict[str, Any]]:
        """Retrieves a user's inventory."""
        return ray.get(self.actor.get_user_inventory.remote(user_id))

    # --- User-to-User Transactions ---
    def transfer_coins(self, sender_id: str, receiver_id: str, amount: float) -> bool:
        """Transfers coins from one user to another."""
        return ray.get(self.actor.transfer_coins.remote(sender_id, receiver_id, amount))


# Example usage (for testing/demonstration)
if __name__ == "__main__":
    # Clean up previous db for a fresh start
    import os

    if os.path.exists("economy.db"):
        os.remove("economy.db")

    config = {"initial_tax_rate": 0.05, "db_path": "economy.db"}
    econ_manager = EconomyManager(config)

    # Initial deposit for a user
    econ_manager.db.update_balance("player_01", 1000.0)
    print(f"Player 01 balance: {econ_manager.get_balance('player_01')}")

    # Process a transaction
    transaction = {"user_id": "player_01", "amount": 100.0}
    if econ_manager.process_transaction(transaction):
        print("Transaction successful!")
    else:
        print("Transaction failed!")
    print(
        f"Player 01 balance after transaction: {econ_manager.get_balance('player_01')}",
    )

    # Update rules
    econ_manager.update_rules({"transaction_tax_rate": 0.10})
    print(f"New tax rate: {econ_manager.rules['transaction_tax_rate']}")

    # Another transaction with new tax rate
    transaction_2 = {"user_id": "player_01", "amount": 50.0}
    if econ_manager.process_transaction(transaction_2):
        print("Second transaction successful!")
    else:
        print("Second transaction failed!")
    print(
        f"Player 01 balance after second transaction: {econ_manager.get_balance('player_01')}",
    )

    # Attempt a transaction with insufficient funds
    transaction_fail = {"user_id": "player_01", "amount": 1000.0}
    if econ_manager.process_transaction(transaction_fail):
        print("Failed transaction successful (ERROR)!")
    else:
        print("Failed transaction failed (CORRECT)!")
    print(
        f"Player 01 balance after failed transaction attempt: {econ_manager.get_balance('player_01')}",
    )
