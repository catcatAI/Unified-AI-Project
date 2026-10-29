# -*- coding: utf-8 -*-
"""萬物皆軸引擎 M5 測試：內容灌入（計畫 §6.3 M5 驗收）。

驗收：卡片→軸值轉換快測試。覆蓋：真檔 351 卡全量轉換有效、快照確定性、
卡型→超類全覆盖、spot check（CC-01）、axis_system 譜系同步鎖定（import
直比 AXIS_SYSTEMS）、權威表 35 卡必入譜系快照、每值落譜系 fsm 狀態域。
"""

from __future__ import annotations

import axis_system
import pytest
from engine.content import (
    STORY_GROUP,
    STORY_ROLE_BY_CARD_TYPE,
    STORY_ROLES,
    card_to_lineage,
    card_to_values,
    cards_to_axis_snapshot,
    default_cards_path,
    lineage_axis_group,
    lineage_axis_snapshot,
    lineage_states,
    load_cards,
    story_group,
)


class TestCardsToStoryAxes:
    def test_real_file_loads_351_cards(self):
        assert default_cards_path().is_file()
        cards = load_cards()
        assert len(cards) == 351

    def test_all_351_convert_and_validate_against_group(self):
        grp = story_group()
        ct_spec = grp.axes["card_type"]
        role_spec = grp.axes["story_role"]
        for card in load_cards():
            values = card_to_values(card)
            assert ct_spec.contains(values["card_type"])
            assert role_spec.contains(values["story_role"])

    def test_axis_snapshot_deterministic_and_complete(self):
        a = cards_to_axis_snapshot(load_cards())
        b = cards_to_axis_snapshot(load_cards())
        assert a == b  # 確定性
        assert len(a) == 351
        assert "CC-01" in a

    def test_cc01_spot_check(self):
        snap = cards_to_axis_snapshot(load_cards())
        assert snap["CC-01"] == {"card_type": "角色卡", "story_role": "character"}

    def test_story_role_mapping_covers_all_data_card_types(self):
        # 同步鎖：映射鍵 == 資料卡型集合（新卡型未映射 → card_to_values 響亮 raise）
        data_types = {str(c.get("card_type", "")) for c in load_cards()}
        assert set(STORY_ROLE_BY_CARD_TYPE) == data_types
        assert set(STORY_ROLE_BY_CARD_TYPE.values()) == set(STORY_ROLES)

    def test_story_group_axes_structures(self):
        grp = story_group()
        assert grp.name == STORY_GROUP
        assert grp.contract.group == STORY_GROUP
        assert set(grp.axes) == {"card_type", "story_role"}
        assert grp.axes["card_type"].kind == "fsm"
        assert grp.axes["story_role"].kind == "fsm"
        # card_type 狀態域 = 資料實際 20 卡型
        assert set(grp.axes["card_type"].states) == {str(c["card_type"]) for c in load_cards()}
        assert grp.axes["story_role"].states == STORY_ROLES

    def test_unknown_card_type_raises(self):
        with pytest.raises(ValueError, match="STORY_ROLE_BY_CARD_TYPE"):
            card_to_values({"card_type": "外星卡"})

    def test_missing_card_id_raises(self):
        with pytest.raises(ValueError, match="missing card_id"):
            cards_to_axis_snapshot([{"card_type": "角色卡"}])

    def test_duplicate_card_id_raises(self):
        with pytest.raises(ValueError, match="duplicate"):
            cards_to_axis_snapshot(
                [
                    {"card_id": "X-1", "card_type": "角色卡"},
                    {"card_id": "X-1", "card_type": "場景卡"},
                ]
            )

    def test_missing_file_raises(self):
        from pathlib import Path

        with pytest.raises(FileNotFoundError, match="game cards not found"):
            load_cards(Path("/nonexistent/cards.json"))


class TestLineageToAxes:
    def test_lineage_states_sync_with_axis_system(self):
        # 同步鎖：lineage_states 逐鍵逐碼 == axis_system.AXIS_SYSTEMS（真源）
        for lineage in axis_system.AXIS_SYSTEMS:
            expected = {
                axis: tuple(codes) for axis, codes in axis_system.AXIS_SYSTEMS[lineage].items()
            }
            assert lineage_states(lineage) == expected

    def test_lineage_axis_group_is_fsm_dict(self):
        grp = lineage_axis_group("物種")
        assert grp.name == "lineage_物種"
        assert grp.contract.group == grp.name
        states = lineage_states("物種")
        assert set(grp.axes) == set(states)
        for name, spec in grp.axes.items():
            assert spec.kind == "fsm"
            assert spec.states == states[name]
        # provides 與軸一一對應
        assert set(grp.contract.provide_names()) == set(grp.axes)

    @pytest.mark.parametrize("lineage", ["物種", "AI", "義體人", "神話種"])
    def test_all_four_lineages_build(self, lineage):
        grp = lineage_axis_group(lineage)
        assert len(grp.axes) == 3  # 每譜系三軸位（§axis_system 譜系）

    def test_unknown_lineage_raises(self):
        with pytest.raises(KeyError, match="unknown lineage"):
            lineage_states("外星種")

    def test_card_to_lineage_authoritative_floor(self):
        # 權威分類表 35 卡必全數可解析並入快照
        cards = load_cards()
        snap = lineage_axis_snapshot(cards)
        assert set(axis_system.AUTHORITATIVE_CARD_AXES) <= set(snap)
        assert len(snap) > 0

    def test_every_resolvable_value_lands_in_lineage_states(self):
        cards = load_cards()
        snap = lineage_axis_snapshot(cards)
        checked = 0
        for cid, (lineage, axes) in snap.items():
            states = lineage_states(lineage)
            assert set(axes) <= set(states), f"{cid}: unknown axis for {lineage}"
            for axis, code in axes.items():
                assert code in states[axis], f"{cid}: {axis}={code!r} not in domain"
            checked += 1
        assert checked == len(snap)

    def test_unresolvable_cards_excluded_not_coerced(self):
        cards = load_cards()
        snap = lineage_axis_snapshot(cards)
        # 不可解析者被排除（而非硬塞預設值）：可解析數 == 快照數
        resolvable = sum(1 for c in cards if card_to_lineage(c) is not None)
        assert len(snap) == resolvable
        assert resolvable < len(cards)  # 確有未分類卡（魔女/術式等）

    def test_lineage_snapshot_deterministic(self):
        cards = load_cards()
        assert lineage_axis_snapshot(cards) == lineage_axis_snapshot(cards)
