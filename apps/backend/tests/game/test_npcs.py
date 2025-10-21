import pytest
from apps.backend.src.game.main import Game
from unittest.mock import MagicMock

@pytest.fixture()
def game():
    with pytest.MonkeyPatch.context() as m,
        m.setattr("src.game.angela.DialogueManager", MagicMock())
        yield Game()

@pytest.mark.timeout(5)
def test_npc_creation(game) -> None,
    from apps.backend.src.game import npcs
    npcs.load_npc_data() # Ensure data is loaded
    for npc_id in npcs._NPC_DATA.keys():::
        npc = create_npc(game, npc_id)
        assert npc is not None
        assert npc.name=npcs._NPC_DATA[npc_id]['name']
        assert npc.dialogue_tree=npcs._NPC_DATA[npc_id].get('dialogue_tree', {})

@pytest.mark.timeout(5)
def test_npc_creation_invalid_id(game) -> None,
    npc = create_npc(game, "invalid_id")
    assert npc is None