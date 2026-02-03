import logging
import sqlite3
from typing import Any
import ray

# Assuming EconomyDB is a local dependency and does not need to be a Ray Actor itself
from apps.backend.src.game.economy_manager import EconomyDB # Import original EconomyDB class

logger = logging.getLogger(__name__)

@ray.remote
class EconomyManagerActor:
    """Manages all in-game economic activities, including transactions and dynamic rules, as a Ray Actor."""

    def __init__(self, config: dict[str, Any], db: EconomyDB | None = None):
        self.db = db if db else EconomyDB(config.get("db_path", "economy.db"))
        self.rules: dict[str, Any] = {
            "transaction_tax_rate": config.get("initial_tax_rate", 0.05),
            "daily_coin_allowance": config.get("daily_coin_allowance", 10.0),
        }
        logger.info("EconomyManagerActor initialized with rules: %s", self.rules)

    def get_balance(self, user_id: str) -> float:
        """Returns the current balance of a user."""
        return self.db.get_balance(user_id)

    def process_transaction(self, transaction_data: dict[str, Any]) -> bool:
        """Processes a transaction, applying tax and updating balances.
        transaction_data should contain 'user_id', 'amount' (cost of item/service).
        Returns True if the transaction is successful, False otherwise (e.g., insufficient funds).
        """
        user_id = transaction_data.get("user_id")
        amount = transaction_data.get("amount")

        if not user_id or amount is None or amount <= 0:
            logger.error("Invalid transaction data: %s", transaction_data)
            return False

        current_balance = self.db.get_balance(user_id)
        tax_rate = self.rules["transaction_tax_rate"]
        tax_amount = amount * tax_rate
        total_cost = amount + tax_amount

        if current_balance < total_cost:
            logger.warning(
                f"Transaction failed for {user_id}: Insufficient funds. Needed {total_cost}, has {current_balance}",
            )
            return False

        # Deduct total cost from user
        if not self.db.update_balance(user_id, -total_cost):
            return False  # Should not happen if balance check passed, but for safety

        logger.info(
            f"Transaction successful for {user_id}. Amount: {amount}, Tax: {tax_amount}, Total Cost: {total_cost}",
        )
        return True

    def update_rules(self, new_rules: dict[str, Any]):
        """Updates the economic rules dynamically."""
        for key, value in new_rules.items():
            if key in self.rules:
                self.rules[key] = value
                logger.info(f"Economic rule '{key}' updated to {value}")
            else:
                logger.warning(f"Attempted to update non-existent rule: {key}")

    def reward_user(self, user_id: str, amount: float) -> bool:
        """Rewards a user with a certain amount of coins.
        This is a convenience wrapper around update_balance.
        """
        if amount <= 0:
            return False
        return self.db.update_balance(user_id, amount)
    
    # --- Item and Inventory Management ---
    def add_item_definition(self, item_id: str, name: str, description: str, base_price: float, category: str) -> bool:
        """Adds or updates an item definition in the database."""
        return self.db.add_item_definition(item_id, name, description, base_price, category)

    def get_item_definition(self, item_id: str) -> dict[str, Any] | None:
        """Retrieves an item definition by item_id."""
        return self.db.get_item_definition(item_id)
    
    def get_all_item_definitions(self) -> list[dict[str, Any]]:
        """Retrieves all item definitions."""
        return self.db.get_all_item_definitions()

    def buy_item(self, user_id: str, item_id: str, quantity: int = 1) -> bool:
        """Allows a user to buy an item. Deducts cost from balance and adds to inventory."""
        if quantity <= 0:
            logger.error("Buy quantity must be positive.")
            return False
        item = self.db.get_item_definition(item_id)
        if not item:
            logger.warning(f"Attempted to buy non-existent item: {item_id}")
            return False

        cost = item["base_price"] * quantity
        transaction_data = {"user_id": user_id, "amount": cost}
        if self.process_transaction(transaction_data):
            if self.db.add_item_to_inventory(user_id, item_id, quantity):
                logger.info(f"User {user_id} bought {quantity} of {item_id} for {cost}.")
                return True
            else:
                logger.error(f"Failed to add item {item_id} to {user_id}'s inventory after purchase.")
                # Refund user if inventory update fails
                self.db.update_balance(user_id, cost) 
                return False
        else:
            logger.warning(f"User {user_id} failed to buy {item_id}: Insufficient funds.")
            return False

    def sell_item(self, user_id: str, item_id: str, quantity: int = 1) -> bool:
        """Allows a user to sell an item. Adds value to balance and removes from inventory."""
        if quantity <= 0:
            logger.error("Sell quantity must be positive.")
            return False
        item = self.db.get_item_definition(item_id)
        if not item:
            logger.warning(f"Attempted to sell non-existent item: {item_id}")
            return False

        if not self.db.remove_item_from_inventory(user_id, item_id, quantity):
            logger.warning(f"User {user_id} does not have enough of item {item_id} to sell {quantity}.")
            return False

        payout = item["base_price"] * quantity * 0.5 # Example: sell for half price
        self.db.update_balance(user_id, payout)
        logger.info(f"User {user_id} sold {quantity} of {item_id} for {payout}.")
        return True

    def get_user_inventory(self, user_id: str) -> list[dict[str, Any]]:
        """Retrieves a user's inventory."""
        return self.db.get_user_inventory(user_id)

    # --- User-to-User Transactions ---
    def transfer_coins(self, sender_id: str, receiver_id: str, amount: float) -> bool:
        """Transfers coins from one user to another."""
        if amount <= 0:
            logger.error("Transfer amount must be positive.")
            return False
        if sender_id == receiver_id:
            logger.warning("Sender and receiver cannot be the same.")
            return False

        # Deduct from sender (includes tax if applicable)
        sender_transaction_data = {"user_id": sender_id, "amount": amount}
        # Temporarily bypass tax for transfers for simplicity, or apply sender-side tax
        current_balance = self.db.get_balance(sender_id)
        if current_balance < amount: # Simplified check without tax for transfer
             logger.warning(f"Transfer failed for {sender_id}: Insufficient funds to send {amount}.")
             return False

        if not self.db.update_balance(sender_id, -amount):
            logger.error(f"Failed to deduct {amount} from {sender_id} during transfer.")
            return False

        # Add to receiver
        if not self.db.update_balance(receiver_id, amount):
            logger.error(f"Failed to add {amount} to {receiver_id} during transfer. Attempting to refund sender.")
            self.db.update_balance(sender_id, amount) # Refund sender
            return False
        
        logger.info(f"User {sender_id} transferred {amount} coins to {receiver_id}.")
        return True