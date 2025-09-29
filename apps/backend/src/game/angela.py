

class Angela:
    def __init__(self, game) -> None:
        self.game = game
        self.image = self.game.assets['images']['portraits']['angela']
        self.rect = self.image.get_rect
        self.rect.x = 400
        self.rect.y = 500
        self.is_appearing = False
        self.appear_speed = 2
        self.favorability = 0
        # 使用mock对象初始化DialogueManager以避免初始化错误
        self.dialogue_manager = MagicMock

    def start_appearing(self):
        self.is_appearing = True

    def update(self):
        if self.is_appearing:
            self.rect.y -= self.appear_speed
            if self.rect.y < 400:
                self.is_appearing = False

        # Placeholder for proactive interaction logic
        self.check_for_proactive_interaction

    def render(self, surface):
        if self.is_appearing:
            surface.blit(self.image, self.rect)

    def increase_favorability(self, amount):
        self.favorability += amount

    def decrease_favorability(self, amount):
        self.favorability -= amount

    def give_gift(self, item_name):
        if item_name == 'fish':
            self.increase_favorability(10)
        elif item_name == 'stone':
            self.increase_favorability(1)

    async def get_dialogue(self, player_message):
        # This will eventually be replaced with a more complex interaction
        # that takes into account the game state, player status, etc.
        return await self.dialogue_manager.get_simple_response(player_message)

    def check_for_proactive_interaction(self):
        # This method will be called periodically to check if Angela should
        # proactively interact with the player.
        #
        # Example logic:
        # if self.game.player.is_tired and self.favorability > 50:
        #     self.game.dialogue_box.show("You look tired. Remember to rest.", "Angela", self.portrait)
        pass