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


class TestNpcHomeVsCardText:
    """NPC 基地必須符合卡片文本：月球神在月之宮殿、艦娘在港鎮等。"""

    def test_key_npc_homes_match_card_text(self):
        """卡片文本明載地點的 NPC，排程基地必須落在文本提到的地點。"""
        import json
        import sim_systems
        from game_data import expand_game
        expand_game()
        cards = json.load(open("data/game_cards.json", encoding="utf-8"))["cards"]
        wm = sim_systems.WORLD_MAP
        misses = []
        for c in cards:
            nm = c.get("name", "")
            raw = nm.split("(")[0].split("（")[0].strip()
            loc = str((c.get("stats") or {}).get("location", "") or "")
            if not loc:
                continue
            mentioned = [l for l in wm if len(l) >= 2 and l in loc]
            if not mentioned:
                continue
            sched = sim_systems.NPC_SCHEDULES.get(raw)
            if not sched:
                continue
            home = sched[0][3]
            if home not in mentioned:
                misses.append("%s: 卡%s home=%s" % (nm, mentioned, home))
        assert not misses, "\n".join(misses)

    def test_species_base_override(self):
        """無地點資訊的 NPC 依種族/職業常理歸屬地（艦娘→港鎮、人魚→聲吶站、軌道管家→軌道站）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        scheds = sim_systems.NPC_SCHEDULES
        # 海艦娘：卡洛夫角（港鎮）；星艦原型是太空船 → 軌道站
        for name in ("霜", "星辰米亞"):
            key = next((k for k in scheds if name in k), None)
            assert key, "找不到 NPC %s" % name
            assert scheds[key][0][3] == "卡洛夫角", "%s 應在港鎮" % name
        key = next((k for k in scheds if "小吹雪" in k), None)
        assert key and scheds[key][0][3] == "軌道居住站大學院", "星艦原型應在軌道站"
        # 月之女神 / 月之公主：月之宮殿
        for name in ("塞勒涅", "輝夜姬"):
            key = next((k for k in scheds if name in k), None)
            assert key, "找不到 NPC %s" % name
            assert scheds[key][0][3] == "月之宮殿", "%s 應在月之宮殿" % name
        # 軌道站莊園管家：軌道居住站大學院
        key = next((k for k in scheds if "艾菈" in k), None)
        assert key and scheds[key][0][3] == "軌道居住站大學院"
        # 地球意志：森林深處
        key = next((k for k in scheds if "蓋婭" in k), None)
        assert key and scheds[key][0][3] == "森林深處"


class TestWorldLineLocations:
    """世界線標記與跨線移動：W03/W04 地點只能經由迴廊到達（文本權威）。"""

    def test_locations_tagged_with_world_line(self):
        """48 個可探索地點全有世界線標記。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        wl = sim_systems.LOCATION_WORLD_LINES
        assert len(wl) == len(sim_systems.WORLD_MAP)
        for loc in sim_systems.WORLD_MAP:
            assert wl.get(loc), "地點 %s 無世界線標記" % loc

    def test_cross_world_line_edges_go_through_corridor(self):
        """W03/W04/夢境層 地點只能從迴廊進入，不能從 W01 直接走路到。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        wl = sim_systems.LOCATION_WORLD_LINES
        bad = []
        for loc, conns in sim_systems.WORLD_MAP.items():
            cur = wl.get(loc, "W01")
            for _d, dest in conns.items():
                dst = wl.get(dest, "W01")
                if dest == "迴廊" or loc == "迴廊":
                    continue  # 迴廊是樞紐
                if "W01+迴廊" in (cur, dst):
                    continue  # W01+迴廊 雙屬
                if dst != cur:
                    bad.append("%s[%s]→%s[%s]" % (loc, cur, dest, dst))
        assert not bad, "跨世界線邊未經迴廊:\n" + "\n".join(bad)

    def test_corridor_connects_all_world_lines(self):
        """迴廊樞紐連通 W01/W03/W04/夢境層。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        corridor = sim_systems.WORLD_MAP.get("迴廊", {})
        dests = set(corridor.values())
        assert "聖十字校園" in dests, "迴廊應連 W01"
        assert "軌道居住站大學院" in dests, "迴廊應連 W03"
        assert "鏽蝕城邦" in dests, "迴廊應連 W04"
        wl = sim_systems.LOCATION_WORLD_LINES
        assert wl.get("鏽蝕城邦") == "W04"
        assert wl.get("軌道居住站大學院") == "W03"
        assert wl.get("高密度大氣結晶行星") == "夢境層"


class TestWorldLineEntryGates:
    """跨世界線門檻：迴廊樞紐無門檻，W03/W04/夢境層需等級歷練。"""

    def test_corridor_hub_is_free(self):
        """迴廊是連接各世界線的橋樑，Lv1 即可進入。"""
        from sim_systems import check_entry_requirement
        ok, _ = check_entry_requirement("迴廊", {"level": 1})
        assert ok

    def test_w03_w04_require_level(self):
        """W03 軌道站/W04 廢土需 Lv6，玻璃荒漠（靈爆核心）Lv8。"""
        from sim_systems import check_entry_requirement
        ch = {"level": 1}
        for loc in ("軌道居住站大學院", "鏽蝕城邦", "熒光沼澤",
                    "高密度大氣結晶行星", "綻放混成園"):
            ok, _ = check_entry_requirement(loc, ch)
            assert not ok, "%s Lv1 不該進入" % loc
        assert check_entry_requirement("鏽蝕城邦", {"level": 6})[0]
        assert not check_entry_requirement("玻璃荒漠", {"level": 6})[0]
        assert check_entry_requirement("玻璃荒漠", {"level": 8})[0]

    def test_cross_line_quest_givers_reachable_early(self):
        """所有排程含跨線地點的 NPC，社交時段（18+）必須在 W01 可及處——
        Lv1 玩家也能接任務，流程不卡死。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        wl = sim_systems.LOCATION_WORLD_LINES
        cross_line = []
        for name, sched in sim_systems.NPC_SCHEDULES.items():
            locs = {l for (_st, _e, _a, l, _m) in sched}
            if any(wl.get(l, "W01") not in ("W01", "W01+迴廊") for l in locs):
                cross_line.append(name)
        assert cross_line, "應存在跨線 NPC"
        for name in cross_line:
            sched = sim_systems.NPC_SCHEDULES[name]
            # 社交時段：與 18-22 有交集的槽位（涵蓋 17-21/19-23 等跨界範圍）
            social = [(l, st, et) for (st, et, _a, l, _m) in sched if st < 22 and et > 18]
            assert social, "%s 應有社交時段" % name
            assert any(wl.get(l, "W01") in ("W01", "W01+迴廊") for l, _s, _e in social), \
                "%s 社交時段應在 W01 可及處" % name

    def test_corridor_hub_has_explorable_content(self):
        """迴廊樞紐 Lv1 可進——需有場景物件讓低等玩家有探索內容（不只折返）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        objs = sim_systems.SCENE_OBJECTS.get("迴廊", [])
        assert len(objs) >= 3, "迴廊應有世界法則碎片/數據流等探索物件"

    def test_world_line_rules_w02_no_magic(self):
        """W02 琥珀紀元絕對無魔——小吉鎮/大根莖村魔法道具與魔法載具失效
        （V3.4：零靈子聚合度、靈子/電子設備無法運作）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        wl = sim_systems.LOCATION_WORLD_LINES
        assert wl.get("小吉鎮") == "W02"
        assert wl.get("大根莖村") == "W02"
        for loc in ("小吉鎮", "大根莖村"):
            _w, fx = sim_systems.get_world_line_effect(loc)
            assert _w == "W02"
            assert fx.get("magic_scale") == 0.0
            assert fx.get("tech_scale") == 0.0
        # 魔力藥水在 W02 完全失效、草藥不受影響
        potion = sim_systems.ITEM_CATALOG.get("魔力藥水")
        mult, blk = sim_systems.world_line_consumable_effect("小吉鎮", potion, "魔力藥水")
        assert mult == 0.0 and blk
        herb = sim_systems.ITEM_CATALOG.get("草藥")
        mult2, blk2 = sim_systems.world_line_consumable_effect("小吉鎮", herb, "草藥")
        assert mult2 == 1.0 and not blk2

    def test_world_line_rules_scales(self):
        """世界線魔法/電子倍率依 V3.4：W03 電子最高精度+靈子低落、
        W04 電子損壞；地點級聚合度修正（聖十字校園低、玻璃荒漠極高）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        _w, fx = sim_systems.get_world_line_effect("軌道居住站大學院")
        assert fx.get("magic_scale") == 0.5   # 靈子不足效能低落
        assert fx.get("tech_scale") == 1.5    # 電子最高精度
        _w, fx = sim_systems.get_world_line_effect("玻璃荒漠")
        assert fx.get("magic_scale") == 2.0   # 靈爆核心 >100ppm
        assert fx.get("tech_scale") == 0.2    # 電子大量損壞
        # 地點級聚合度：聖十字校園靈波吸收層降低靈子
        _w, fx = sim_systems.get_world_line_effect("聖十字校園")
        assert fx.get("magic_scale") < 1.0

    def test_world_line_vehicle_category(self):
        """載具世界線分類：魔法掃帚 magic、機車 tech、馬/小舟 natural。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        assert sim_systems.get_vehicle_world_category(sim_systems.VEHICLES["魔法掃帚"]) == "magic"
        assert sim_systems.get_vehicle_world_category(sim_systems.VEHICLES["機車"]) == "tech"
        assert sim_systems.get_vehicle_world_category(sim_systems.VEHICLES["馬"]) == "natural"
        assert sim_systems.get_vehicle_world_category(sim_systems.VEHICLES["小舟"]) == "natural"
        # 魔法載具在 W02 無法運作（magic_scale 0.0）
        _w, fx = sim_systems.get_world_line_effect("小吉鎮")
        assert fx.get("magic_scale") == 0.0

    def test_w02_villages_via_corridor(self):
        """W02 村落（小吉鎮/大根莖村）只能經由迴廊到達——霧海群島
        不再直連小吉鎮（跨線邊全經迴廊）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        wl = sim_systems.LOCATION_WORLD_LINES
        assert sim_systems.WORLD_MAP.get("小吉鎮", {}).get("enter") == "迴廊"
        assert sim_systems.WORLD_MAP.get("霧海群島", {}).get("north") == "迴廊"
        assert sim_systems.WORLD_MAP.get("迴廊", {}).get("west") == "小吉鎮"
        # 未經迴廊的跨線邊 = 0
        bad = []
        for loc, conns in sim_systems.WORLD_MAP.items():
            cur = wl.get(loc, "W01")
            for _d, dest in conns.items():
                dst = wl.get(dest, "W01")
                if dest == "迴廊" or loc == "迴廊":
                    continue
                if "W01+迴廊" in (cur, dst):
                    continue
                if dst != cur:
                    bad.append(f"{loc}[{cur}] → {dest}[{dst}]")
        assert not bad, "跨線邊應全經迴廊: %s" % bad
