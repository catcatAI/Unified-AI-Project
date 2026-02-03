import logging
import random
from typing import Any

# Assuming DialogueManager exists at this path
try:
    from apps.backend.src.ai.dialogue.dialogue_manager import DialogueManager
except ImportError:
    # Placeholder if DialogueManager is not yet implemented
    class DialogueManager:
        def __init__(self):
            logger.warning("DialogueManager not found, using placeholder.")

        async def get_response(
            self,
            player_message: str,
            context: dict[str, Any],
        ) -> str:
            return f"Placeholder response to: {player_message}"


logger = logging.getLogger(__name__)


class Angela:
    """Represents the primary AI character, Angela, within the "Angela's World" game.
    Manages her in-game representation, favorability system, dialogue integration,
    and proactive behaviors with enhanced AI-driven logic.
    """

    def __init__(self, dialogue_manager: DialogueManager | None = None):
        logger.info("Angela character initialized.")
        self.favorability: float = 50.0  # Initial favorability score (0-100)
        self.mood: str = "neutral"  # Initial mood (happy, neutral, sad, annoyed)
        self.dialogue_manager = (
            dialogue_manager if dialogue_manager else DialogueManager()
        )
        self.on_screen: bool = False
        self.position: dict[str, int] = {"x": 0, "y": 0}
        self.last_proactive_interaction_time: float = 0.0  # Simulate time for cooldown

    def update(self, game_state: dict[str, Any]):
        """Updates Angela's internal state based on the game state.
        This would handle animations, position updates, mood changes, etc.
        """
        logger.debug("Angela: Updating state.")
        # Simulate mood decay/change over time
        if random.random() < 0.01:  # Small chance to change mood randomly
            self.mood = random.choice(["happy", "neutral", "sad", "annoyed"])
            logger.debug(f"Angela's mood changed to {self.mood}.")

        self.check_for_proactive_interaction(game_state)

    def render(self, screen: Any):
        """Renders Angela's visual representation on the screen.
        'screen' would be a game engine specific object (e.g., pygame.Surface).
        """
        logger.debug("Angela: Rendering.")
        if self.on_screen:
            # Placeholder for drawing sprite at self.position
            # Visuals could change based on mood or favorability
            pass

    def increase_favorability(self, amount: float = 1.0):
        """Increases Angela's favorability with the player."""
        self.favorability = min(100.0, self.favorability + amount)
        if self.favorability > 75:
            self.mood = "happy"
        elif self.favorability > 25:
            self.mood = "neutral"
        else:
            self.mood = "sad"
        logger.info(
            f"Angela: Favorability increased to {self.favorability}. Mood: {self.mood}",
        )

    def decrease_favorability(self, amount: float = 1.0):
        """Decreases Angela's favorability with the player."""
        self.favorability = max(0.0, self.favorability - amount)
        if self.favorability > 75:
            self.mood = "happy"
        elif self.favorability > 25:
            self.mood = "neutral"
        else:
            self.mood = "sad"
        logger.info(
            f"Angela: Favorability decreased to {self.favorability}. Mood: {self.mood}",
        )

    async def give_gift(self, item: dict[str, Any]) -> str:
        """Player gives a gift to Angela, affecting favorability and mood."""
        item_name = item.get("name", "an item")
        item_value = item.get("value", 0)
        item_type = item.get("type", "misc")

        logger.info(
            f"Angela: Received gift: {item_name} (Value: {item_value}, Type: {item_type}).",
        )

        response = ""
        if item_value >= 20 and item_type == "favorite":
            self.increase_favorability(15.0)
            self.mood = "happy"
            response = f"Oh my, a {item_name}! It's my absolute favorite! Thank you so much, you're too kind!"
        elif item_value >= 10:
            self.increase_favorability(8.0)
            self.mood = random.choice(["happy", "neutral"])
            response = f"A {item_name}! How thoughtful of you. I really appreciate it."
        elif item_value > 0:
            self.increase_favorability(2.0)
            self.mood = "neutral"
            response = f"Oh, a {item_name}. Thank you."
        else:
            self.decrease_favorability(5.0)
            self.mood = "annoyed"
            response = f"Is this... a {item_name}? I'm not sure what to do with it. (Angela looks unimpressed)"

        return response

    async def get_dialogue(self, player_message: str, context: dict[str, Any]) -> str:
        """Gets Angela's dialogue response to a player message using the DialogueManager.
        Context now includes Angela's mood and favorability.
        """
        logger.info(f"Angela: Player says: {player_message[:50]}...")

        dialogue_context = {
            **context,
            "angela_favorability": self.favorability,
            "angela_mood": self.mood,
        }
        response = await self.dialogue_manager.get_response(
            player_message,
            dialogue_context,
        )
        logger.info(f"Angela: Responds: {response[:50]}...")
        return response

    def check_for_proactive_interaction(self, game_state: dict[str, Any]):
        """Angela initiates conversations or actions based on game state, favorability, and mood."""
        logger.debug("Angela: Checking for proactive interaction.")
        current_time = game_state.get(
            "current_time",
            0.0,
        )  # Assume game_state provides a time

        # Simple cooldown to prevent spamming interactions
        if (
            current_time - self.last_proactive_interaction_time < 60.0
        ):  # 60 seconds cooldown
            return

        interaction_triggered = False

        # Rule 1: Player health is low
        if (
            game_state.get("player_health", 100) < 30
            and self.favorability > 40
            and self.mood != "annoyed"
        ):
            logger.info("Angela: Noticed player health is low, offering help.")
            # In a real scenario, this would trigger a specific dialogue or action
            print(
                "Angela: 'You look a bit hurt! Are you alright? I can help if you need it.'",
            )
            interaction_triggered = True

        # Rule 2: Player has been idle for a while
        elif (
            game_state.get("player_idle_time", 0) > 120
            and self.favorability > 60
            and self.mood == "happy"
        ):
            logger.info("Angela: Player idle, initiating friendly chat.")
            print(
                "Angela: 'It's been quiet for a while. Anything interesting happening?'",
            )
            interaction_triggered = True

        # Rule 3: Low favorability and Angela is sad/annoyed
        elif self.favorability < 30 and self.mood in {"sad", "annoyed"}:
            logger.info(
                "Angela: Low favorability and negative mood, expressing concern/displeasure.",
            )
            if self.mood == "sad":
                print("Angela: (Sighs softly) 'I wish we could get along better...'")
            else:  # annoyed
                print("Angela: 'Is there something you wanted? I'm a bit busy.'")
            interaction_triggered = True

        if interaction_triggered:
            self.last_proactive_interaction_time = current_time
