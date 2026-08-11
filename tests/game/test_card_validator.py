# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""遊戲卡片數理化/結構一致性驗證測試。"""

import json

import pytest
from game.card_validator import GameCardValidator, load_report


class TestCardValidatorRules:
    def test_duplicate_card_id(self):
        report = _run(
            [
                {"card_id": "X", "card_type": "角色卡", "tokens": []},
                {"card_id": "X", "card_type": "角色卡", "tokens": []},
            ]
        )
        assert any(i.rule == "unique_id" for i in report.issues)

    def test_strength_out_of_bounds(self):
        report = _run(
            [
                {
                    "card_id": "A",
                    "card_type": "角色卡",
                    "tokens": [{"name": "t", "strength": 1.5}],
                }
            ]
        )
        assert any(i.rule == "strength_bounds" for i in report.issues)

    def test_strength_non_numeric(self):
        report = _run(
            [
                {
                    "card_id": "B",
                    "card_type": "角色卡",
                    "tokens": [{"name": "t", "strength": "high"}],
                }
            ]
        )
        assert any(i.rule == "strength_numeric" for i in report.issues)

    def test_positive_age(self):
        report = _run(
            [
                {
                    "card_id": "C",
                    "card_type": "角色卡",
                    "stats": {"age": -5},
                    "tokens": [],
                }
            ]
        )
        assert any(i.rule == "stat_positive" for i in report.issues)

    def test_percent_bounds(self):
        report = _run(
            [
                {
                    "card_id": "D",
                    "card_type": "角色卡",
                    "stats": {"暴擊率%": 150},
                    "tokens": [],
                }
            ]
        )
        assert any(i.rule == "stat_percent" for i in report.issues)

    def test_field_count_mismatch(self):
        report = _run(
            [
                {
                    "card_id": "E",
                    "card_type": "角色卡",
                    "raw_field_count": 5,
                    "tokens": [
                        {"name": "a", "strength": 0.5},
                        {"name": "b", "strength": 0.5},
                    ],
                }
            ]
        )
        assert any(i.rule == "field_count_mismatch" for i in report.issues)

    def test_duplicate_token_name(self):
        report = _run(
            [
                {
                    "card_id": "F",
                    "card_type": "角色卡",
                    "tokens": [
                        {"name": "同名能力", "strength": 0.5},
                        {"name": "同名能力", "strength": 0.3},
                    ],
                }
            ]
        )
        assert any(i.rule == "duplicate_token_name" for i in report.issues)

    def test_card_type_missing(self):
        report = _run([{"card_id": "G", "tokens": []}])
        assert any(i.rule == "card_type_missing" for i in report.issues)

    def test_valid_card_no_errors(self):
        report = _run(
            [
                {
                    "card_id": "H",
                    "card_type": "角色卡",
                    "stats": {"age": 14},
                    "raw_field_count": 1,
                    "tokens": [{"name": "體質", "strength": 0.5}],
                }
            ]
        )
        assert report.ok
        assert report.total_issues == 0

    def test_missing_strength_is_skipped(self):
        report = _run([{"card_id": "I", "card_type": "角色卡", "tokens": [{"name": "t"}]}])
        assert report.ok

    def test_string_percent_bounds(self):
        report = _run(
            [
                {
                    "card_id": "J",
                    "card_type": "角色卡",
                    "stats": {"暴擊率": "120%"},
                    "tokens": [],
                }
            ]
        )
        assert any(i.rule == "stat_percent_str" for i in report.issues)

    def test_nan_stat(self):
        report = _run(
            [
                {
                    "card_id": "K",
                    "card_type": "角色卡",
                    "stats": {"age": float("nan")},
                    "tokens": [],
                }
            ]
        )
        assert any(i.rule == "stat_numeric" or i.severity == "error" for i in report.issues)


class TestRealCardsIntegration:
    def test_real_cards_load_and_validate(self):
        report = load_report()
        assert report.total_cards == 351
        # real cards must have no hard errors
        assert report.ok

    def test_real_cards_no_duplicate_ids(self):
        report = load_report()
        assert not any(i.rule == "unique_id" for i in report.issues)


def _run(cards):
    validator = _ValidatorWithCards(cards)
    return validator.validate()


class _ValidatorWithCards(GameCardValidator):
    """以注入的卡片覆寫載入，避免依賴外部 JSON 檔。"""

    def __init__(self, cards):
        self.cards = cards
        self.path = None

    def _load(self):
        pass
