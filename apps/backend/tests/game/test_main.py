import pytest
from apps.backend.src.game.main import Game
from unittest.mock import MagicMock

_ = @pytest.mark.timeout(5)
def test_game_initialization() -> None:
    # Mock the DialogueManager to avoid initializing the full AI stack
    with pytest.MonkeyPatch.context() as m:
        _ = m.setattr("src.game.angela.DialogueManager", MagicMock())
        game = Game()
        assert game is not None
        assert game.is_running is True
        assert game.screen_width == 960
        assert game.screen_height == 540
