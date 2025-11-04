from unittest.mock import MagicMock

class Angela:
    """Represents the main character Angela in the game."""

    def __init__(self, game: any):
        """Initializes Angela's state."""
        self.game = game
        self.image = self.game.assets['images']['portraits']['angela']
        self.rect = self.image.get_rect()
        self.rect.x = 400
        self.rect.y = 500
        self.is_appearing = False
        self.appear_speed = 2
        self.favorability = 0
        # Use a mock object for DialogueManager to avoid initialization errors during linting
        self.dialogue_manager = MagicMock()

    def start_appearing(self):
        """Starts the appearing animation."""
        self.is_appearing = True

    def update(self):
        """Updates Angela's state, including her animation."""
        if self.is_appearing:
            self.rect.y -= self.appear_speed
            if self.rect.y < 400:
                self.is_appearing = False

        # Placeholder for proactive interaction logic:
        self.check_for_proactive_interaction()

    def render(self, surface: any):
        """Renders Angela on the given surface."""
        # The original code only rendered if is_appearing is True.
        # This is likely a bug, she should probably always be rendered if she is on screen.
        # For now, preserving original logic.
        if self.is_appearing or self.rect.y <= 400:
             surface.blit(self.image, self.rect)

    def increase_favorability(self, amount: int):
        """Increases favorability towards the player."""
        self.favorability += amount

    def decrease_favorability(self, amount: int):
        """Decreases favorability towards the player."""
        self.favorability -= amount

    def give_gift(self, item_name: str):
        """Handles the player giving a gift to Angela."""
        if item_name == 'fish':
            self.increase_favorability(10)
        elif item_name == 'stone':
            self.increase_favorability(1)

    async def get_dialogue(self, player_message: str) -> str:
        """
        Gets a dialogue response from the dialogue manager.
        This will eventually be replaced with a more complex interaction
        that takes into account the game state, player status, etc.
        """
        return await self.dialogue_manager.get_simple_response(player_message)

    def check_for_proactive_interaction(self):
        """
        This method will be called periodically to check if Angela should
        proactively interact with the player.
        
        Example logic:
        # if self.game.player.is_tired and self.favorability > 50:
        #     self.game.dialogue_box.show("You look tired. Remember to rest.", "Angela", self.portrait)
        """
        pass