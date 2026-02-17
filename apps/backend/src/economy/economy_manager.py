import logging
from typing import Dict, Any

from .economy_db import EconomyDB

logger = logging.getLogger(__name__)

class EconomyManager:
    """Manages the in-game economy, including currency, transactions,
    and market dynamics.
    Designed to be adaptable, allowing rules to be updated dynamically by the core AI.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initializes the EconomyManager with a given configuration."""
        self.config = config
        self.rules: Dict[str, Any] = {
            "transaction_tax_rate": self.config.get("initial_tax_rate", 0.05),
            "daily_coin_allowance": self.config.get("initial_allowance", 10.0)
        }
        self.db = EconomyDB(db_path=self.config.get("db_path", "economy.db"))
        
        # Item Registry for Angela's survival (Phase 13)
        self.item_registry = {
            "digital_energy_drink": {"price": 5.0, "restores": {"energy": 20}, "description": "Restores 20 energy"},
            "premium_bio_pellets": {"price": 10.0, "restores": {"hunger": 30, "happiness": 5}, "description": "High quality food"},
            "viral_toy_update": {"price": 15.0, "restores": {"happiness": 40}, "description": "Boosts mood significantly"},
            "system_optimizer_patch": {"price": 25.0, "restores": {"energy": 50, "happiness": 10}, "description": "Full system rejuvenation"},
            "medical_kit": {"price": 20.0, "restores": {"health": 30}, "description": "Restores 30 health"},
            "toy": {"price": 8.0, "restores": {"happiness": 20}, "description": "A simple toy for fun"}
        }
        
        logger.info(f"EconomyManager initialized with rules: {self.rules}")
        logger.info(f"Market opened with {len(self.item_registry)} items.")

    def process_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """
        DEPRECATED: Use add_transaction instead.
        Processes a transaction, updating balances and logging the event.
        
        This method now delegates to add_transaction for backward compatibility.
        """
        logger.warning(
            "DEPRECATED: process_transaction() is deprecated. "
            "Use add_transaction(user_id, amount, description) instead."
        )
        
        # Extract parameters from transaction_data
        user_id = transaction_data.get("user_id", "")
        amount = transaction_data.get("amount", 0.0)
        description = transaction_data.get("description", "Legacy transaction")
        
        # Delegate to new method
        return self.add_transaction(user_id, amount, description)

    def purchase_item(self, user_id: str, item_id: str) -> Dict[str, Any]:
        """Allows Angela to purchase an item from the registry."""
        if item_id not in self.item_registry:
            logger.error(f"Purchase failed: Item '{item_id}' not found in registry.")
            return {"success": False, "reason": "Item not found"}

        item = self.item_registry[item_id]
        price = item["price"]
        current_balance = self.db.get_balance(user_id)

        if current_balance < price:
            logger.warning(f"Purchase failed for {user_id}: Insufficient funds ({current_balance} < {price})")
            return {"success": False, "reason": "Insufficient funds"}

        # Deduct balance
        self.db.add_balance(user_id, -price)
        logger.info(f"User '{user_id}' purchased '{item_id}' for {price} coins.")
        
        return {
            "success": True,
            "item_id": item_id,
            "effects": item["restores"],
            "remaining_balance": current_balance - price
        }

    def process_cognitive_dividend(self, user_id: str, life_sense_amount: float, quality_score: float) -> float:
        """Processes cognitive dividends from AGI work, awarding coins based on output quality."""
        # Conversion formula: 1 Life Sense = 0.5 Coins (base), adjusted by quality
        base_rate = 0.5
        dividend_amount = life_sense_amount * base_rate * (0.5 + quality_score * 0.5)
        
        if dividend_amount > 0:
            self.db.add_balance(user_id, dividend_amount)
            logger.info(f"Awarded cognitive dividend of {dividend_amount:.2f} coins to user '{user_id}' (Life Sense: {life_sense_amount:.2f}, Quality: {quality_score:.2%})")
        
        return dividend_amount

    def get_balance(self, user_id: str) -> float:
        """Retrieves the currency balance for a given user."""
        logger.debug(f"Getting balance for user: {user_id}")
        return self.db.get_balance(user_id)

    def update_rules(self, new_rules: Dict[str, Any]):
        """Allows the core AI to dynamically update the economic rules."""
        logger.info(f"Updating economic rules from {self.rules} to {new_rules}")
        if "transaction_tax_rate" in new_rules:
            tax_rate = new_rules["transaction_tax_rate"]
            if not (0.0 <= tax_rate <= 1.0):
                logger.error(f"Invalid transaction_tax_rate: {tax_rate}. Must be between 0.0 and 1.0.")
                return
        if "daily_coin_allowance" in new_rules:
            allowance = new_rules["daily_coin_allowance"]
            if not (allowance >= 0.0):
                logger.error(f"Invalid daily_coin_allowance: {allowance}. Must be non-negative.")
                return

        self.rules.update(new_rules)
        logger.info("Economic rules updated successfully.")

    def add_transaction(self, user_id: str, amount: float, description: str = "") -> bool:
        """
        添加交易記錄並更新餘額

        Args:
            user_id: 用戶ID
            amount: 交易金額（正數為收入，負數為支出）
            description: 交易描述

        Returns:
            bool: 交易是否成功
        """
        try:
            if not user_id:
                logger.error("Transaction failed: Missing user_id")
                return False

            if amount == 0:
                logger.warning("Transaction amount is zero, skipping")
                return True

            # 獲取當前餘額
            current_balance = self.db.get_balance(user_id)

            # 檢查支出是否有足夠餘額
            if amount < 0 and current_balance < abs(amount):
                logger.warning(f"Transaction failed for {user_id}. Insufficient funds. Current: {current_balance}, Attempted: {abs(amount)}")
                return False

            # 計算稅費（僅對正交易）
            tax = 0.0
            if amount > 0:
                tax = amount * self.rules.get("transaction_tax_rate", 0.05)
                net_amount = amount - tax
            else:
                net_amount = amount

            # 更新餘額
            self.db.add_balance(user_id, net_amount)

            logger.info(
                f"Transaction added for user '{user_id}': "
                f"Amount: {amount}, Tax: {tax}, Net: {net_amount}, Description: {description}"
            )

            return True
        except Exception as e:
            logger.error(f"Error adding transaction for user '{user_id}': {e}")
            return False
