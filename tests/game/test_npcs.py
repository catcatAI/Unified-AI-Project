import pytest
from src.game.main import Game
from src.game.npcs import create_npc, NPC_DATA

@pytest.fixture
def game():
    return Game()

@pytest.mark.timeout(5)
def test_npc_creation(game):
    for npc_id in NPC_DATA.keys():
        npc = create_npc(game, npc_id)
        assert npc is not None
        assert npc.name == NPC_DATA[npc_id]['name']
        assert npc.dialogue == NPC_DATA[npc_id]['dialogue']

@pytest.mark.timeout(5)
def test_npc_creation_invalid_id(game):
    npc = create_npc(game, "invalid_id")
    assert npc is None
