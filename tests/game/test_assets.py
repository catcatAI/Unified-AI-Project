"""
测试模块 - test_assets

自动生成的测试模块,用于验证系统功能。
"""

import pytest
from game.main import Game
from unittest.mock import MagicMock

@pytest.fixture()
def game():
    with pytest.MonkeyPatch.context() as m:
        m.setattr("src.game.angela.DialogueManager", MagicMock())
        yield Game()

@pytest.mark.timeout(5)

    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_asset_loading(game) -> None,
    assert 'images' in game.assets()
    assert 'sprites' in game.assets()
    assert 'backgrounds' in game.assets['images']
    assert 'portraits' in game.assets['images']
    assert 'characters' in game.assets['sprites']
    assert 'icons' in game.assets['sprites']
    # 'portraits' are images, not sprites
    assert 'portraits' not in game.assets['sprites']

@pytest.mark.timeout(5)
def test_specific_assets_loaded(game) -> None:
    assert 'station' in game.assets['images']['backgrounds']
    assert 'angela' in game.assets['images']['portraits']
    assert 'player' in game.assets['sprites']['characters']
    assert 'schoolbag' in game.assets['sprites']['icons']
