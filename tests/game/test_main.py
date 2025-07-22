import pytest
from src.game.main import Game

@pytest.mark.timeout(5)
def test_game_initialization():
    game = Game()
    assert game is not None
    assert game.is_running is True
    assert game.screen_width == 960
    assert game.screen_height == 540
