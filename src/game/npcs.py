import pygame

class NPC:
    def __init__(self, game, name, x, y, portrait=None, sprite=None):
        self.game = game
        self.name = name
        self.image = sprite if sprite else pygame.Surface((48, 48))
        if not sprite:
            self.image.fill((255, 0, 255)) # Magenta for placeholder
        self.portrait = portrait
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.dialogue = []
        self.dialogue_index = 0

    async def interact(self):
        if self.dialogue_index < len(self.dialogue):
            # This should be handled by the UI, but for now, we'll print to console
            print(f"[{self.name}]: {self.dialogue[self.dialogue_index]}")
            self.dialogue_index += 1
        else:
            self.dialogue_index = 0 # Loop dialogue for now

    def render(self, surface):
        surface.blit(self.image, self.rect)

# --- NPC Definitions ---

# This could be loaded from a JSON or YAML file in the future
NPC_DATA = {
    "murakami": {
        "name": "長谷川爺爺",
        "type": "villager",
        "x": 200,
        "y": 150,
        "sprite": "villager1",
        "portrait": "pt_murakami",
        "dialogue": [
            "年輕人，回來啦！村子的未來就靠你們了。",
            "今天天氣真不錯啊，作物應該會長得很好吧。",
        ]
    },
    "tanaka": {
        "name": "田中先生",
        "type": "unemployed_uncle",
        "x": 300,
        "y": 250,
        "sprite": "uncle",
        "portrait": "pt_tanaka",
        "dialogue": [
            "唉…又是一天啊。",
            "想當年，我在城裡也是很風光的…",
        ]
    },
    "hibiki": {
        "name": "阿響",
        "type": "homeless_person",
        "x": 500,
        "y": 400,
        "sprite": "homeless",
        "portrait": "pt_hibiki",
        "dialogue": [
            "...",
            "(他只是靜靜地看了你一眼，沒有說話)",
        ]
    },
    "lina": {
        "name": "莉娜",
        "type": "blacksmith",
        "x": 400,
        "y": 100,
        "sprite": "blacksmith",
        "portrait": "pt_lina",
        "dialogue": [
            "是來學東西的，還是來閒逛的？我的時間很寶貴。",
            "好鐵，是需要千錘百鍊的。",
        ]
    }
}

class Villager(NPC):
    def __init__(self, game, name, x, y, dialogue, portrait, sprite):
        super().__init__(game, name, x, y, portrait, sprite)
        self.dialogue = dialogue

class UnemployedUncle(NPC):
    def __init__(self, game, name, x, y, dialogue, portrait, sprite):
        super().__init__(game, name, x, y, portrait, sprite)
        self.dialogue = dialogue

class HomelessPerson(NPC):
    def __init__(self, game, name, x, y, dialogue, portrait, sprite):
        super().__init__(game, name, x, y, portrait, sprite)
        self.dialogue = dialogue

class Blacksmith(NPC):
    def __init__(self, game, name, x, y, dialogue, portrait, sprite):
        super().__init__(game, name, x, y, portrait, sprite)
        self.dialogue = dialogue

def create_npc(game, npc_id):
    npc_data = NPC_DATA.get(npc_id)
    if not npc_data:
        return None

    npc_type = npc_data["type"]
    portrait = game.assets['sprites']['portraits'].get(npc_data['portrait'])
    sprite = game.assets['sprites']['characters'].get(npc_data['sprite'])

    if npc_type == "villager":
        return Villager(game, npc_data["name"], npc_data["x"], npc_data["y"], npc_data["dialogue"], portrait, sprite)
    elif npc_type == "unemployed_uncle":
        return UnemployedUncle(game, npc_data["name"], npc_data["x"], npc_data["y"], npc_data["dialogue"], portrait, sprite)
    elif npc_type == "homeless_person":
        return HomelessPerson(game, npc_data["name"], npc_data["x"], npc_data["y"], npc_data["dialogue"], portrait, sprite)
    elif npc_type == "blacksmith":
        return Blacksmith(game, npc_data["name"], npc_data["x"], npc_data["y"], npc_data["dialogue"], portrait, sprite)
    return None
