# -*- coding: utf-8 -*-
"""軸譜系統（axis_system.py）單元測試。

覆蓋：四系譜軸碼解析、文件權威分類表、文本特例表、五維度親和力、
機制種族推導、裝備／消耗品／任務交互判定、數值加乘、顯示輔助。
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import axis_system as ax


# ═══════════════════════════════════════════════════════════════════════════
# 技能卡軸譜學習（批次 32）
# ═══════════════════════════════════════════════════════════════════════════


class TestSkillCardAxis:
    """技能卡學習的軸譜判定（魔法→能量/靈性、義體→機械、駭客→資訊等）。"""

    def _card(self, name, cat):
        return {"name": name, "category": cat}

    def test_magic_needs_energy_or_spirit(self):
        dims, thr = ax.skill_card_axis(self._card("道術：五雷正法", "magic"))
        assert set(dims) == {"能量", "靈性"} and thr == 0.4

    def test_tech_needs_information(self):
        dims, thr = ax.skill_card_axis(self._card("上網（網絡操作）", "tech"))
        assert dims == ("資訊",) and thr == 0.4

    def test_hacking_needs_information(self):
        dims, thr = ax.skill_card_axis(self._card("駭客（入侵系統）", "stealth"))
        assert dims == ("資訊",) and thr == 0.4

    def test_cyborg_body_needs_mechanical(self):
        dims, thr = ax.skill_card_axis(self._card("義體醫師", "craft"))
        assert dims == ("機械",) and thr == 0.4

    def test_race_skill_needs_spirit(self):
        dims, thr = ax.skill_card_axis(self._card("天翼技：知識掠取", "general"))
        assert dims == ("靈性",) and thr == 0.4

    def test_general_stealth_unrestricted(self):
        dims, thr = ax.skill_card_axis(self._card("潛伏：無聲移動", "stealth"))
        assert dims == () and thr == 0.0

    def test_target_skill_mapping(self):
        assert ax.skill_card_target_skill(self._card("x", "magic")) == "combat"
        assert ax.skill_card_target_skill(self._card("x", "stealth")) == "exploration"
        assert ax.skill_card_target_skill(self._card("x", "tech")) == "craft"
        assert ax.skill_card_target_skill(self._card("x", "knowledge")) == "knowledge"


# ═══════════════════════════════════════════════════════════════════════════
# 戰鬥軸譜相剋（批次 33）
# ═══════════════════════════════════════════════════════════════════════════


class TestCombatAxis:
    """靈體敵人對物理攻擊減傷、能量/靈性維度角色克制。"""

    _aff_mystic = {"物質": 0.4, "能量": 0.72, "靈性": 0.75, "機械": 0.05, "資訊": 0.12}
    _aff_physical = {"物質": 0.8, "能量": 0.17, "靈性": 0.17, "機械": 0.1, "資訊": 0.1}

    def test_normal_enemy_no_modifier(self):
        mult, is_spirit, note = ax.combat_axis_multiplier(self._aff_physical, "野狼")
        assert mult == 1.0 and not is_spirit and note == ""

    def test_spirit_enemy_physical_reduced(self):
        mult, is_spirit, note = ax.combat_axis_multiplier(self._aff_physical, "暗影靈")
        assert mult == 0.5 and is_spirit and note == "減傷"

    def test_spirit_enemy_mystic_boost(self):
        mult, is_spirit, note = ax.combat_axis_multiplier(self._aff_mystic, "幽靈")
        assert mult == 1.5 and is_spirit and note == "克制"

    def test_shadow_enemy_detected(self):
        mult, is_spirit, _ = ax.combat_axis_multiplier(self._aff_mystic, "織織之影")
        assert is_spirit and mult == 1.5

    def test_spirit_enemy_name_variants(self):
        for name in ("暗影靈", "幽靈", "織織之影", "深淵楓之影", "亡靈"):
            _, is_spirit, _ = ax.combat_axis_multiplier(self._aff_physical, name)
            assert is_spirit, name

    def test_gargoyle_not_spirit(self):
        """石像鬼是石像生物（掉落鐵礦/黏土），物理實體不該被靈體減傷。"""
        mult, is_spirit, note = ax.combat_axis_multiplier(self._aff_physical, "石像鬼")
        assert not is_spirit and mult == 1.0 and note == ""


# =============================================================================
# 1. 軸碼解析
# =============================================================================

class TestParseAxisCode:
    def test_species_s_h_p(self):
        r = ax.parse_axis_code("物種", "S-H-P")
        assert r == {
            "原種距離": ("S", "標準種"),
            "人形比例": ("H", "類人型"),
            "混血譜系": ("P", "純血"),
        }

    def test_ai_f3_a3_o0(self):
        r = ax.parse_axis_code("AI", "F3-A3-O0")
        assert r == {
            "人形模仿度": ("F3", "仿真人形"),
            "自主性": ("A3", "完全自主"),
            "程序開放度": ("O0", "封閉黑箱"),
        }

    def test_cyborg_c2_h2_b2(self):
        r = ax.parse_axis_code("義體人", "C2-H2-B2")
        assert r == {
            "義體化比例": ("C2", "中度（30%-70%）"),
            "外觀人形保留度": ("H2", "部分暴露"),
            "神經保留度": ("B2", "生物腦增強"),
        }

    def test_mythic_d1_o2_m2(self):
        r = ax.parse_axis_code("神話種", "D1-O2-M2")
        assert r == {
            "神性濃度": ("D1", "傳說級"),
            "原典忠實度": ("O2", "部分保留"),
            "存在維度": ("M2", "靈體/概念"),
        }

    def test_invalid_lineage(self):
        assert ax.parse_axis_code("不存在", "S-H-P") is None

    def test_invalid_code_length(self):
        assert ax.parse_axis_code("物種", "S-H") is None

    def test_invalid_code_position(self):
        assert ax.parse_axis_code("物種", "S-H-ZZ") is None

    def test_token_with_pipe(self):
        r = ax.parse_axis_code("物種", "獸娘｜ F-H-P")
        assert r is not None
        assert r["原種距離"] == ("F", "遠原種")


class TestAxisCodeFromToken:
    def test_full_token_value(self):
        assert ax.axis_code_from_token("獸娘｜ F-H-P（遠原種、類人型、純血）") == ("獸娘", "F-H-P")

    def test_simple_token(self):
        assert ax.axis_code_from_token("神話種|D1-O1-M2") == ("神話種", "D1-O1-M2")

    def test_invalid_token(self):
        assert ax.axis_code_from_token("") is None
        assert ax.axis_code_from_token("獸娘") is None


# =============================================================================
# 2. 文件權威分類表 + 文本特例表
# =============================================================================

class TestAuthoritativeAxes:
    @pytest.mark.parametrize("cid,lineage,code", [
        ("CC-35", "AI", "F3-A3-O0"),
        ("CC-31", "AI", "F1-A2-O1"),
        ("C16", "義體人", "C2-H2-B2"),
        ("CC-36", "神話種", "D2-O1-M1"),
        ("CC-05", "神話種", "D3-O1-M2"),
        ("CC-49", "物種", "S-H-P"),
        ("CC-52", "物種", "N-C-P"),
    ])
    def test_authoritative(self, cid, lineage, code):
        card = {"card_id": cid, "stats": {}, "tokens": []}
        assert ax.resolve_card_axis(card)[:2] == (lineage, code)

    @pytest.mark.parametrize("cid,lineage,code", [
        ("CC-19", "AI", "F1-A1-O0"),      # 機械妖精：防空砲化身，非人形載體
        ("CC-24", "神話種", "D3-O1-M1"),  # 維爾：共振文明使者，晶體節肢物質顯形
    ])
    def test_text_derived(self, cid, lineage, code):
        card = {"card_id": cid, "stats": {}, "tokens": []}
        assert ax.resolve_card_axis(card)[:2] == (lineage, code)

    def test_card_token_fallback(self):
        card = {
            "card_id": "ZZ-01", "stats": {"race": "測試"},
            "tokens": [{"name": "分類系譜", "value": "物種｜ S-S-P"}],
        }
        assert ax.resolve_card_axis(card)[:2] == ("物種", "S-S-P")

    def test_text_keyword_fallback_dragon(self):
        card = {"card_id": "ZZ-02", "stats": {"race": "天空龍娘"}, "tokens": []}
        assert ax.resolve_card_axis(card)[0] == "物種"

    def test_authoritative_beats_token(self):
        # 權威表優先於卡片 token（token 曾污染：CC-45/46 被誤填 神話種）
        card = {
            "card_id": "CC-45", "stats": {},
            "tokens": [{"name": "分類系譜", "value": "神話種｜ D1-O1-M2"}],
        }
        assert ax.resolve_card_axis(card)[:2] == ("物種", "F-C-P")


# =============================================================================
# 3. 五維度親和力
# =============================================================================

class TestAffinity:
    def test_human_baseline(self):
        aff = ax.affinity_vector(None, None)
        assert aff["物質"] == pytest.approx(0.85)
        assert aff["靈性"] == pytest.approx(0.30)

    def test_spirit_m2_low_physical(self):
        # D1-O2-M2 三軸平均後物質親和 0.4 —— 仍低於實體門檻 0.5（無法穿實體盔甲）
        m2 = ax.parse_axis_code("神話種", "D1-O2-M2")
        aff = ax.affinity_vector("神話種", m2)
        assert aff["物質"] < 0.5
        assert aff["靈性"] > 0.7
        assert aff["能量"] > 0.5

    def test_ai_high_mech_info(self):
        axes = ax.parse_axis_code("AI", "F3-A3-O0")
        aff = ax.affinity_vector("AI", axes)
        assert aff["機械"] > 0.6
        assert aff["資訊"] > 0.5

    def test_all_dimensions_present(self):
        for lineage in ("物種", "AI", "義體人", "神話種"):
            for code in ("S-H-P", "F3-A3-O0", "C2-H2-B2", "D1-O2-M2"):
                axes = ax.parse_axis_code(lineage, code)
                aff = ax.affinity_vector(lineage, axes)
                assert set(aff) == set(ax.DIMENSIONS)
                assert all(0.0 <= v <= 1.0 for v in aff.values())


# =============================================================================
# 4. 機制種族推導
# =============================================================================

class TestMechanicRace:
    def test_dragon(self):
        axes = ax.parse_axis_code("物種", "F-H-P")
        assert ax.mechanic_race_from_axis("物種", axes, "天空龍娘") == "龍族"

    def test_beast_default(self):
        axes = ax.parse_axis_code("物種", "S-H-P")
        assert ax.mechanic_race_from_axis("物種", axes, "狐娘（北極狐亞種）") == "獸娘"

    def test_ai_mech(self):
        axes = ax.parse_axis_code("AI", "F1-A1-O0")
        assert ax.mechanic_race_from_axis("AI", axes, "機械妖精") == "機械"

    def test_mythic_spirit(self):
        axes = ax.parse_axis_code("神話種", "D1-O2-M2")
        assert ax.mechanic_race_from_axis("神話種", axes, "惡意精靈") == "精靈"

    def test_witch_detect_race(self):
        # 無軸譜角色（準大魔女）走 detect_race 文本規則 → 術士
        from sim_systems import detect_race
        assert detect_race([], text_race="人類（魔女學府畢業生，準大魔女）") == "術士"

    def test_dragon_with_witch_school(self):
        # 「天空龍娘（魔女學府）」——主詞龍娘，不受場所詞干擾 → 龍族
        axes = ax.parse_axis_code("物種", "F-H-P")
        assert ax.mechanic_race_from_axis("物種", axes, "天空龍娘（魔女學府出身）") == "龍族"


# =============================================================================
# 5. 交互判定引擎
# =============================================================================

class TestInteraction:
    def setup_method(self):
        self.spirit = ax.affinity_vector("神話種", ax.parse_axis_code("神話種", "D1-O2-M2"))
        self.human = ax.affinity_vector(None, None)

    def test_can_interact_threshold(self):
        assert not ax.can_interact(self.spirit, "物質")
        assert ax.can_interact(self.spirit, "靈性")
        assert ax.can_interact(self.human, "物質")

    def test_interaction_depth_floor(self):
        assert ax.interaction_depth(self.spirit, "物質") == 0.0
        assert ax.interaction_depth(self.human, "物質") == pytest.approx(0.7)

    def test_equipment_spirit_cannot_wear_armor(self):
        armor = {"tags": ["metal", "armor"]}
        ok, depth, dim, msg = ax.evaluate_equipment(self.spirit, armor)
        assert ok is False
        assert depth == 0.0
        assert dim == "物質"

    def test_equipment_spirit_can_wear_aura(self):
        aura = {"tags": ["aura"]}
        ok, depth, dim, _ = ax.evaluate_equipment(self.spirit, aura)
        assert ok is True
        assert dim == "靈性"
        assert depth >= 0.5

    def test_equipment_untagged_ok(self):
        ok, depth, dim, _ = ax.evaluate_equipment(self.spirit, {"tags": []})
        assert ok is True
        assert depth == 1.0

    def test_consumable_all_allowed(self):
        potion = {"tags": ["consumable", "healing"]}
        spirit_tome = {"tags": ["consumable", "spiritual", "aura"]}
        ok1, _, _, _ = ax.evaluate_consumable(self.spirit, potion)
        ok2, _, _, _ = ax.evaluate_consumable(self.human, spirit_tome)
        assert ok1 is True and ok2 is True

    def test_consumable_depth_reflects_affinity(self):
        spirit_tome = {"tags": ["consumable", "spiritual", "aura"]}
        _, d1, _, _ = ax.evaluate_consumable(self.spirit, spirit_tome)
        _, d2, _, _ = ax.evaluate_consumable(self.human, spirit_tome)
        assert d1 > d2

    def test_item_dimension_mappings(self):
        assert ax.item_dimension({"tags": ["naval"]}) == "物質"
        assert ax.item_dimension({"tags": ["draconic"]}) == "物質"
        assert ax.item_dimension({"tags": ["metal", "armor"]}) == "物質"
        assert ax.item_dimension({"tags": ["mechanical", "cyber"]}) == "機械"
        assert ax.item_dimension({"tags": ["magic"]}) == "能量"
        assert ax.item_dimension({"tags": ["aura"]}) == "靈性"
        assert ax.item_dimension({"tags": ["data", "code"]}) == "資訊"
        assert ax.item_dimension({"tags": []}) is None

    def test_quest_axis_condition(self):
        ok, depth, missing = ax.evaluate_quest(self.spirit, {"維度": {"靈性": 0.5}})
        assert ok is True
        assert missing == []

    def test_quest_axis_reject(self):
        ok, _, missing = ax.evaluate_quest(self.spirit, {"維度": {"物質": 0.5}})
        assert ok is False
        assert missing


# =============================================================================
# 6. 數值加乘與顯示
# =============================================================================

class TestStatsAndDisplay:
    def test_stat_modifiers_shape(self):
        aff = ax.affinity_vector(None, None)
        mods = ax.stat_modifiers(aff)
        assert set(mods) == {"hp", "sp", "atk", "defense", "spd", "karma"}
        assert all(v > 0 for v in mods.values())

    def test_physical_high_hp(self):
        phys = ax.affinity_vector(None, None)
        spirit = ax.affinity_vector("神話種", ax.parse_axis_code("神話種", "D1-O2-M2"))
        assert ax.stat_modifiers(phys)["hp"] > ax.stat_modifiers(spirit)["hp"]
        assert ax.stat_modifiers(spirit)["sp"] > ax.stat_modifiers(phys)["sp"]

    def test_axis_display(self):
        assert ax.axis_display("物種", "S-H-P", ax.parse_axis_code("物種", "S-H-P")) == "物種｜ S-H-P（標準種、類人型、純血）"
        assert ax.axis_display(None, None, None) == "其他｜ 人類基線"

    def test_affinity_display_contains_dims(self):
        aff = ax.affinity_vector(None, None)
        disp = ax.affinity_display(aff)
        for dim in ax.DIMENSIONS:
            assert dim in disp

    def test_dimension_label_public(self):
        assert ax.dimension_label("靈性") == "靈性（靈體/概念）"


# =============================================================================
# 7. MECH_AFFINITY_BOOST 完整性
# =============================================================================

class TestBoost:
    def test_all_buckets_present(self):
        from sim_systems import RACE_DATA
        for bucket in RACE_DATA:
            assert bucket in ax.MECH_AFFINITY_BOOST, f"缺少 {bucket} 的親和力補強"

    def test_boost_positive_affinity(self):
        for bucket, boosts in ax.MECH_AFFINITY_BOOST.items():
            for dim, v in boosts.items():
                assert v >= 0.0
                assert dim in ax.DIMENSIONS

    def test_human_empty(self):
        assert ax.MECH_AFFINITY_BOOST["人類"] == {}


# =============================================================================
# 8. 好感度任務門檻（批次 35）
# =============================================================================

class TestRelationshipQuestGates:
    """NPC giver 的支線任務都該有好感度門檻——不同好感度解鎖不同任務分支。"""

    def _q(self, qid):
        import sim_systems
        return next(q for q in sim_systems.QUESTS if q["id"] == qid)

    def test_npc_side_quests_have_relationship_gate(self):
        import sim_systems
        npc_gated = 0
        for q in sim_systems.QUESTS:
            giver = q.get("giver", "")
            if q.get("type") == "side" and giver and giver != "系統":
                reqs = (q.get("conditions", {}) or {}).get("required_relationships", {}) or {}
                assert reqs.get(giver, 0) > 0, (
                    "支線任務 %s 由 %s 給出但無好感度門檻" % (q["id"], giver)
                )
                npc_gated += 1
        assert npc_gated >= 4  # 紅×2、小狐丸×2、小蒼蘭×1 等

    def test_quest_gate_matches_giver(self):
        import sim_systems
        for q in sim_systems.QUESTS:
            giver = q.get("giver", "")
            if giver and giver != "系統":
                reqs = (q.get("conditions", {}) or {}).get("required_relationships", {}) or {}
                for npc in reqs:
                    assert npc == giver, (
                        "任務 %s 的好感度門檻對象 %s 與 giver %s 不符"
                        % (q["id"], npc, giver)
                    )

    def test_low_relationship_blocks_quest(self):
        from character_system import check_quest_eligibility
        q = self._q("SQ-02")
        char = {"level": 5, "race": "人類", "mechanic_race": "人類",
                "reputation": 0, "relationships": {"小狐丸": 10},
                "completed_quests": [], "token_list": [], "axis": {}}
        ok, reason = check_quest_eligibility(char, q)
        assert not ok
        assert "好感度不足" in reason
        char["relationships"]["小狐丸"] = 20
        ok, reason = check_quest_eligibility(char, q)
        assert ok

    def test_main_quest_not_gated_by_relationship(self):
        """主線 MQ-02（左間小蒼蘭給）不設好感度門檻——主線不該被支線好感卡死。"""
        q = self._q("MQ-02")
        reqs = (q.get("conditions", {}) or {}).get("required_relationships", {}) or {}
        assert reqs == {}


# =============================================================================
# 9. 載具軸譜（批次 36）
# =============================================================================

class TestVehicleAxis:
    """載具依 fuel 類型判定誰能騎：魔法→能量/靈性、龍→龍族、機動→機械。"""

    def _v(self, fuel):
        return {"name": "test", "fuel": fuel}

    def _char(self, energy=0.17, spirit=0.17, mech=0.12, race="貓娘", mrace="獸娘"):
        return {
            "axis": {"affinity": {"能量": energy, "靈性": spirit, "機械": mech}},
            "race": race, "mechanic_race": mrace,
        }

    def test_vehicle_axis_mapping(self):
        assert ax.vehicle_axis(self._v("magic"))[0] == ("能量", "靈性")
        assert ax.vehicle_axis(self._v("bond"))[0] == ("龍族",)
        assert ax.vehicle_axis(self._v("fire"))[0] == ("能量",)
        assert ax.vehicle_axis(self._v("gas"))[0] == ("機械",)
        assert ax.vehicle_axis(self._v("coal"))[0] == ("機械",)
        for fuel in ("stamina", "feed", "human", "wind", "sail", "dog", 100):
            assert ax.vehicle_axis(self._v(fuel))[0] == ()

    def test_magic_broom_blocks_physical(self):
        cat = self._char()
        ok, reason = ax.can_use_vehicle(cat, self._v("magic"))
        assert not ok and "能量" in reason

    def test_magic_broom_allows_mage(self):
        mage = self._char(energy=0.72, spirit=0.75, race="術式適應體", mrace="術士")
        assert ax.can_use_vehicle(mage, self._v("magic"))[0]

    def test_dragon_mount_requires_dragon(self):
        dragon = self._char(energy=0.5, race="天空龍娘", mrace="龍族")
        cat = self._char()
        assert ax.can_use_vehicle(dragon, self._v("bond"))[0]
        assert not ax.can_use_vehicle(cat, self._v("bond"))[0]

    def test_motor_vehicle_requires_mechanical(self):
        eng = self._char(mech=0.85, race="艦娘", mrace="艦娘")
        cat = self._char()
        assert ax.can_use_vehicle(eng, self._v("gas"))[0]
        assert not ax.can_use_vehicle(cat, self._v("gas"))[0]

    def test_common_vehicle_unrestricted(self):
        for fuel in ("stamina", "feed"):
            assert ax.can_use_vehicle(self._char(), self._v(fuel))[0]

    def test_all_vehicles_mounted_on_scene(self):
        """每地點的載具都該掛到場景物件（原本 18 種載具是永遠拿不到的死資料）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        veh_by_loc = {}
        for loc, objs in sim_systems.SCENE_OBJECTS.items():
            for o in objs:
                if o.get("type") == "vehicle":
                    veh_by_loc[loc] = o.get("vehicle_type", "")
        for loc, vname in sim_systems.VEHICLE_LOCATIONS.items():
            assert vname in sim_systems.VEHICLES, "載具 %s 不在 VEHICLES" % vname
            assert veh_by_loc.get(loc) == vname, (
                "地點 %s 應掛載載具 %s，實際 %s" % (loc, vname, veh_by_loc.get(loc))
            )
        # 至少掛載 20 個地點（遠多於手寫 3 個）
        assert len(veh_by_loc) >= 20
