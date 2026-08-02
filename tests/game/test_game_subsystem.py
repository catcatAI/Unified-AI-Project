"""apps/backend/src/game 遊戲子系統測試"""

import pytest

from apps.backend.src.game import Character, GameEngine, GameState, I18n, Scene
from apps.backend.src.game.engine import NPC_LINES
from apps.backend.src.game.token_effects import (
    TokenEffect,
    apply_token_hp,
    apply_token_spirit,
    apply_token_skill_bonus,
    compute_token_effects,
    get_combat_dice_bonus,
    get_damage_resistance,
    get_token_descriptions,
)


class TestTokenEffects:
    def test_compute_combat_effect(self):
        effects = compute_token_effects(
            [{"category": "combat", "name": "斬擊", "strength": 1.0}]
        )
        assert len(effects) == 1
        assert effects[0].dice_bonus == 10
        assert effects[0].special == "combat_attack"

    def test_compute_vitality_effect(self):
        effects = compute_token_effects(
            [{"category": "vitality", "name": "生命力", "strength": 1.0}]
        )
        assert effects[0].stat_bonus["hp"] == 30
        assert effects[0].resistance == 0.3

    def test_compute_unknown_category(self):
        assert compute_token_effects([{"category": "unknown", "name": "x"}]) == []

    def test_apply_token_hp(self):
        max_hp, hp = apply_token_hp(
            [{"category": "vitality", "name": "生命力", "strength": 1.0}], base_hp=100
        )
        assert max_hp >= 100
        assert hp <= max_hp

    def test_apply_token_spirit(self):
        max_spirit, spirit = apply_token_spirit(
            [{"category": "energy", "name": "靈力", "strength": 1.0}], base_spirit=50
        )
        assert max_spirit >= 50
        assert spirit <= max_spirit

    def test_get_combat_dice_bonus(self):
        bonus = get_combat_dice_bonus(
            [{"category": "combat", "name": "斬擊", "strength": 1.0}]
        )
        assert bonus > 0


class TestNPC_LINES:
    def test_has_zh_and_en(self):
        assert "zh" in NPC_LINES
        assert "en" in NPC_LINES

    def test_lines_are_nonempty(self):
        assert len(NPC_LINES["zh"]) > 0
        assert len(NPC_LINES["en"]) > 0
        assert len(NPC_LINES["zh"]) == len(NPC_LINES["en"])


class TestGameModels:
    def test_character_initializable(self):
        char = Character(card_id="C01", name="主角")
        assert char.name == "主角"
        assert char.hp == 100

    def test_scene_initializable(self):
        scene = Scene(card_id="S01", name="冰原")
        assert scene.name == "冰原"
        assert scene.spirit_density == 2.0

    def test_game_state_initializable(self):
        char = Character(card_id="C01", name="主角")
        scene = Scene(card_id="S01", name="冰原")
        state = GameState(pc=char, scene=scene)
        assert state.pc.name == "主角"
        assert state.turn == 0


class TestGameEngine:
    def test_engine_initializable(self):
        engine = GameEngine()
        assert engine is not None

    def test_i18n_translates(self):
        i18n = I18n("zh")
        assert hasattr(i18n, "t") or hasattr(i18n, "translate")
