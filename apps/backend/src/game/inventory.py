from typing import Dict

class Inventory:
    """A simple inventory system for the game."""

    def __init__(self) -> None:
        """Initializes the inventory."""
        self.items: Dict[str, int] = {}

    def add_item(self, item_name: str, quantity: int = 1):
        """Adds an item to the inventory."""
        if item_name in self.items:
            self.items[item_name] += quantity
        else:
            self.items[item_name] = quantity

    def remove_item(self, item_name: str, quantity: int = 1) -> bool:
        """Removes an item from the inventory. Returns False if item not present."""
        if item_name in self.items:
            self.items[item_name] -= quantity
            if self.items[item_name] <= 0:
                del self.items[item_name]
            return True
        return False

    def get_item_count(self, item_name: str) -> int:
        """Gets the count of a specific item in the inventory."""
        return self.items.get(item_name, 0)