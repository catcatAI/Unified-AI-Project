import pytest
from src.game.main import Game

@pytest.fixture
def game():
    return Game()

def test_asset_loading(game):
    assert 'images' in game.assets
    assert 'sprites' in game.assets
    assert 'backgrounds' in game.assets['images']
    assert 'portraits' in game.assets['images']
    assert 'characters' in game.assets['sprites']
    assert 'icons' in game.assets['sprites']
    assert 'portraits' in game.assets['sprites']

def test_specific_assets_loaded(game):
    assert 'station' in game.assets['images']['backgrounds']
    assert 'angela' in game.assets['images']['portraits']
    assert 'player_walk_cycle' in game.assets['sprites']['characters']
    assert 'item_shizuku' in game.assets['sprites']['icons']
