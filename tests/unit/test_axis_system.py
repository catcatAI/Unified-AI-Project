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

    def test_cross_line_npc_social_stays_in_own_world_line(self):
        """跨線 NPC（家鄉非 W01）的社交地點必須與家鄉同一世界線——
        W02 絕對無魔村莊不會每天去 W01 便利店、W03 軌道站居民不會每天
        下到地表、W04 灰燼拾荒王同理（跨線通勤不合文本常理）。
        迴廊／W01+迴廊 樞紐居民除外（文本：迴廊是連接各世界線的橋樑）。
        任務 giver 可達性：W02 村莊經迴廊樞紐 Lv1 可達（無門檻），
        W03/W04 有等級門檻（Lv6），任務自然被世界線入口閘門分級。"""
        import sim_systems
        from game_data import expand_game, ALL_NPCS
        expand_game()
        wl = sim_systems.LOCATION_WORLD_LINES
        cross_line = [
            n for n in sim_systems.NPC_SCHEDULES
            if ALL_NPCS.get(n, {}).get("location") and
            wl.get(ALL_NPCS[n]["location"], "W01") not in ("W01",)
        ]
        assert cross_line, "應存在跨線 NPC"
        offenders = []
        for name in cross_line:
            home_wl = wl.get(ALL_NPCS[name]["location"], "W01")
            if home_wl in ("迴廊", "W01+迴廊"):
                continue  # 樞紐通行者（文本允許跨線）
            for (st, et, _a, l, _m) in sim_systems.NPC_SCHEDULES[name]:
                if wl.get(l, "W01") != home_wl:
                    offenders.append((name, home_wl, l))
        assert not offenders, "跨線社交（應留在自家世界線）：%s" % offenders[:6]
        # W02 村莊可達性：小吉鎮經迴廊樞紐 Lv1 可進、大根莖村由小吉鎮連通
        # （任務 giver 小吉/雞頭四 的任務鏈不卡死）
        w02 = sim_systems.WORLD_MAP.get("小吉鎮", {})
        assert w02.get("enter") == "迴廊" or "迴廊" in str(w02.get("enter")), \
            "小吉鎮（W02）應經迴廊樞紐進入"
        d02 = sim_systems.WORLD_MAP.get("大根莖村", {})
        assert "小吉鎮" in str(d02.get("west") or d02.get("east") or ""), \
            "大根莖村（W02）應由小吉鎮連通"

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

    def test_w02_shops_no_dead_stock(self):
        """W02 絕對無魔村莊商店不得販賣魔法/電子道具（死亡庫存）——
        小吉/雞頭四 offers 中任何道具在家鄉使用時不得完全失效。"""
        import sim_systems
        from game_data import expand_game, ALL_NPCS
        expand_game()
        for nm in ("小吉", "雞頭四"):
            home = ALL_NPCS.get(nm, {}).get("location", "")
            assert home in ("小吉鎮", "大根莖村")
            for o in (ALL_NPCS.get(nm, {}).get("offers") or []):
                idf = sim_systems.ITEM_CATALOG.get(o, {})
                if not idf:
                    continue
                mult, blk = sim_systems.world_line_consumable_effect(home, idf, o)
                assert mult > 0.0, "%s 的 %s 在 %s 完全失效（死亡庫存）" % (nm, o, home)

    def test_item_world_category_name_keywords(self):
        """get_item_world_category 名稱關鍵字：靈子系→magic、電子/機械系→tech，
        天然療傷草藥（靈芝）不受誤傷。"""
        import sim_systems
        assert sim_systems.get_item_world_category({}, "靈子電池") == "magic"
        assert sim_systems.get_item_world_category({}, "精密機械零件") == "tech"
        assert sim_systems.get_item_world_category({}, "靈芝") == "natural"
        assert sim_systems.get_item_world_category({}, "草藥") == "natural"
        assert sim_systems.get_item_world_category({}, "治療藥水") == "natural"

    def test_story_quest_title_clean_and_w02_rewards(self):
        """SN 故事任務標題/描述淨化（劇情節點卡 name 含「標題+多空白+長敘事」時
        只取標題段、描述取第一句），且 W02 giver 任務獎勵不得為 magic/tech
        道具（絕對無魔世界線拿到也用不了）。"""
        import sim_systems
        from game_data import expand_game, ALL_NPCS
        expand_game()
        wl = sim_systems.LOCATION_WORLD_LINES
        item_names = set(sim_systems.ITEM_CATALOG)
        # 標題不得含長敘事殘片（多空白或「歲時」等卡面敘事字樣）
        for q in sim_systems.QUESTS:
            if q["id"].startswith("SN-"):
                assert len(q["title"]) <= 22, "SN 任務標題過長: %s %r" % (q["id"], q["title"])
                assert "  " not in q["title"], "SN 任務標題含多空白: %s" % q["id"]
        # W02 giver 任務獎勵不得為 magic/tech
        for q in sim_systems.QUESTS:
            ri = q.get("reward_item") or ""
            giver = q.get("giver") or ""
            gloc = (ALL_NPCS.get(giver) or {}).get("location", "")
            if wl.get(gloc, "W01") == "W02" and ri in item_names:
                cat = sim_systems.get_item_world_category(sim_systems.ITEM_CATALOG[ri], ri)
                assert cat == "natural", "W02 任務 %s 獎勵死道具 %s (%s)" % (q["id"], ri, cat)

    def test_world_clock_switches_with_location(self):
        """世界時鐘隨角色地點切換活躍世界線：到 W02 看到琥珀紀元、
        W03 星曆、W04 灰燼紀元、回 W01 恢復公元曆——每個世界有自己
        的時間並同步對齊隱藏在文本外的整體時鐘（移動/渡水/傳送/衝刺
        皆應呼叫 _sync_clock_to_location）。"""
        import sim_systems
        from game_data import expand_game
        import world_clock as wc
        expand_game()
        # 每條世界線的曆法應與文本一致（V3.4：W02 琥珀紀元/W03 星曆/W04 灰燼）
        _wl_clock = {
            "W02": "琥珀紀元",
            "W03": "星曆",
            "W04": "灰燼紀元",
            "夢境層": "墮落之城",
            "迴廊": "概念時間流",
        }
        # 夢境層（墮落之城）曆法名含「墮落之城」即可（實際為「墮落之城內部年」）
        _wl_to_clock = {
            "W02": "W02", "W03": "W03", "W04": "W04",
            "夢境層": "SL-04", "迴廊": "CORRIDOR",
        }
        _wl_map = sim_systems.LOCATION_WORLD_LINES
        for _loc in _wl_map:
            _wl = _wl_map[_loc]
            if _wl not in _wl_to_clock:
                continue
            _clock_id = _wl_to_clock[_wl]
            _cal = wc.get_calendar(_clock_id)
            assert _wl_clock[_wl] in _cal, \
                "%s(%s) 應含 %s，實際 %s" % (_loc, _clock_id, _wl_clock[_wl], _cal)

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

    def test_world_line_equipment_scaling(self):
        """魔法裝備的 stat_multipliers 受世界線聚合度縮放（V3.4）：
        W02 絕對無魔→失效、W03 靈子低落→減半、玻璃荒漠靈爆核心→增強；
        普通武器不受影響。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        ch = {"race": "人類", "mechanic_race": "人類", "token_list": [], "level": 1}
        em = sim_systems.EquipmentManager(ch)
        em.equip("right_hand", {"name": "炎帝之劍", "durability": 100,
                                "current_durability": 100, "stat_multipliers": {"atk": 0.5}})
        b = em.get_stat_bonuses("小吉鎮")
        assert b.get("atk", 0) == 0.0, "W02 絕對無魔魔法武器應失效"
        b = em.get_stat_bonuses("軌道居住站大學院")
        assert abs(b.get("atk", 0) - 0.25) < 1e-6, "W03 靈子低落魔法武器應減半"
        b = em.get_stat_bonuses("玻璃荒漠")
        assert abs(b.get("atk", 0) - 1.0) < 1e-6, "玻璃荒漠靈爆核心魔法武器應增強"
        # 普通武器不受世界線影響
        em2 = sim_systems.EquipmentManager(ch)
        em2.equip("right_hand", {"name": "鐵劍", "durability": 100,
                                 "current_durability": 100, "stat_multipliers": {"atk": 0.3}})
        b = em2.get_stat_bonuses("小吉鎮")
        assert abs(b.get("atk", 0) - 0.3) < 1e-6, "普通武器不受世界線影響"

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

    def test_world_line_enemies_match_line(self):
        """批次 43：跨線地點的遭遇敵人應符合世界線權威（《世界線錨定—補充欄位》：
        W04 = 灰燼行者/拾荒王/螢光獵手；W03 = 下層工業港機械系；
        夢境層 = 概念構成（暗影/幽靈/元素）；S07 熒光沼澤 = 變異兩棲生物）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        le = sim_systems.LOCATION_ENEMIES
        assert "螢光獵手" in le.get("熒光沼澤", []), "熒光沼澤應有螢光獵手（變異兩棲生物）"
        assert "灰燼行者" in le.get("玻璃荒漠", []), "玻璃荒漠應有灰燼行者（靈爆中心）"
        assert "拾荒王" in le.get("鏽蝕城邦", []), "鏽蝕城邦應有拾荒王"
        assert "站內巡邏無人機" in le.get("軌道居住站大學院", []), "W03 應有機械系敵人"
        for loc in ("高密度大氣結晶行星", "綻放混成園"):
            assert any(n in le.get(loc, []) for n in ("暗影靈", "幽靈", "元素核心")), \
                f"夢境層 {loc} 應有概念構成系敵人"
        # 這些地點不該再有隨機/影之敵
        for loc in ("熒光沼澤", "玻璃荒漠", "鏽蝕城邦", "軌道居住站大學院"):
            assert not any("之影" in n for n in le.get(loc, [])), f"{loc} 不應有影之敵"

    def test_safe_zones_no_elite_enemies(self):
        """批次 43：新手安全區（便利店/聖十字校園/鏡湖/清溪河/W02 村落）
        不得有凶暴/遠古/深淵/W03-W04 強敵。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        strong_kw = ("凶暴", "兇暴", "遠古", "深淵", "灰燼", "拾荒", "螢光",
                     "無人機", "維修機械")
        for loc in ("便利店", "聖十字校園", "鏡湖", "清溪河"):
            bad = [n for n in sim_systems.LOCATION_ENEMIES.get(loc, []) if any(k in n for k in strong_kw)]
            assert not bad, f"安全區 {loc} 出現強敵: {bad}"
        # W02 村落是絕對無魔安全村——無遭遇敵人
        for loc in ("小吉鎮", "大根莖村"):
            assert not sim_systems.LOCATION_ENEMIES.get(loc), f"{loc} 應無遭遇敵人"

    def test_all_map_locations_have_enemy_pools(self):
        """批次 50：所有地圖地點都有敵人群可遭遇（探索不落空），
        唯文本設定的絕對無魔安全村（小吉鎮/大根莖村）除外。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        no_magic_villages = ("小吉鎮", "大根莖村")
        empty = []
        for loc in sim_systems.WORLD_MAP:
            if loc in no_magic_villages:
                continue
            if not sim_systems.LOCATION_ENEMIES.get(loc):
                empty.append(loc)
        assert not empty, f"無敵人群的地圖地點: {empty}"
        # 敵人群不得引用不存在的敵人
        emap = {e["name"] for e in sim_systems.ENEMIES}
        ghost = [(loc, n) for loc, pool in sim_systems.LOCATION_ENEMIES.items()
                 for n in pool if n not in emap]
        assert not ghost, f"幽靈敵人: {ghost}"

    def test_relax_locations_no_strong_enemies(self):
        """批次 51：休閒/商業/住宅場所（市集/溫泉/圖書館/學府/校園/便利店
        等）不得有非影之敵的強敵（遠古/凶暴/深淵前綴或 HP>=120/ATK>=30）
        ——文明場所出現遠古虎/大地靈違反文本常理；影之敵（演出設計）豁免。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        relax = ("便利店", "聖十字校園", "鏡湖", "清溪河", "小吉鎮", "大根莖村",
                 "中央大圖書館", "煙雲溫泉湖", "西翼大市集", "農學院", "魔女學府",
                 "聖十字環形堡壘校園", "直播控制室")
        emap = {e["name"]: e for e in sim_systems.ENEMIES}
        bad = []
        for loc in relax:
            for n in sim_systems.LOCATION_ENEMIES.get(loc, []):
                if "之影" in n:
                    continue
                e = emap.get(n, {})
                if (any(k in n for k in ("遠古", "凶暴", "兇暴", "深淵"))
                        or (e.get("hp") or 0) >= 120 or (e.get("atk") or 0) >= 30):
                    bad.append((loc, n))
        assert not bad, f"休閒場所出現強敵: {bad}"

    def test_shadow_enemy_names_no_broken_parentheses(self):
        """批次 43：卡片影之敵名稱不能含殘留括號（全形括號 split 失敗
        會產生「小無（Xiǎ之影」這種缺右括號的名字）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        shadows = [e["name"] for e in sim_systems.ENEMIES if "之影" in e["name"]]
        assert shadows, "應有影之敵"
        bad = [s for s in shadows if "（" in s or "(" in s]
        assert not bad, f"影之敵名稱含殘留括號: {bad}"
        # 演出場景刻意保留影之敵（演出對戰），普通場景不得污染
        perf = [loc for loc in sim_systems.LOCATION_ENEMIES if any(
            k in loc for k in ("舞台", "演唱會", "直播", "模式"))]
        assert any(any("之影" in n for n in sim_systems.LOCATION_ENEMIES.get(loc, [])) for loc in perf), \
            "演出場景應保留影之敵"

    def test_w04_enemy_stats_present(self):
        """批次 43：新增 W03/W04 專屬敵人有完整數值（世界線錨定實證）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        names = {e["name"]: e for e in sim_systems.ENEMIES}
        for n in ("灰燼行者", "灰燼行者長", "螢光獵手", "沼澤變異體", "拾荒王",
                  "站內巡邏無人機", "軌道站維修機械"):
            e = names.get(n)
            assert e, f"缺少 W03/W04 敵人: {n}"
            assert e["hp"] > 0 and e["atk"] > 0 and e["exp"] > 0, f"{n} 數值不完整"

    def test_npc_shop_offers_all_in_catalog(self):
        """批次 44：卡片 NPC 的個人商店庫存（offers）必須全部存在於
        ITEM_CATALOG——否則商店固定只賣 5 種，語境庫存（艦娘裝備/神話道具/
        義體/極地裝備等）是死資料。"""
        import json
        import sim_systems
        from game_data import expand_game
        expand_game()
        cat = sim_systems.ITEM_CATALOG
        missing = {}
        for n, nd in sim_systems.NPC_METADATA.items():
            for it in nd.get("offers", []):
                if it not in cat:
                    missing.setdefault(it, []).append(n)
        assert not missing, f"NPC offers 引用不存在道具: {list(missing)[:8]}"

    def test_npc_personal_shop_world_categories(self):
        """批次 44：NPC 個人商店道具的世界線分類正確——靈子電池/神諭碎片
        是 magic（W02 絕對無魔失效）、12.7cm連装砲是 tech（W03 電子加成）、
        乾糧是 natural（不受世界線影響）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        cat = sim_systems.ITEM_CATALOG
        assert sim_systems.get_item_world_category(cat["靈子電池"], "靈子電池") == "magic"
        assert sim_systems.get_item_world_category(cat["12.7cm連装砲"], "12.7cm連装砲") == "tech"
        assert sim_systems.get_item_world_category(cat["神諭碎片"], "神諭碎片") == "magic"
        assert sim_systems.get_item_world_category(cat["魔力補充藥水"], "魔力補充藥水") == "magic"
        assert sim_systems.get_item_world_category(cat["乾糧（高密度）"], "乾糧（高密度）") == "natural"
        # 世界線效果：靈子電池在 W02 失效、W03 減半
        m, blk = sim_systems.world_line_consumable_effect(
            "小吉鎮", cat["靈子電池"], "靈子電池")
        assert m == 0.0 and blk, "W02 絕對無魔下靈子電池應失效"

    def test_no_wl_enemy_leak_anywhere(self):
        """批次 43 reviewer：W03/W04 專屬敵人只能出現在跨線覆寫目標地點，
        不得洩漏到任何 W01 地點（含場景卡建立的地點，如珊瑚台）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        wl = sim_systems.LOCATION_WORLD_LINES
        targets = ("熒光沼澤", "玻璃荒漠", "鏽蝕城邦", "鏽蝕城邦地下",
                   "軌道居住站大學院", "高密度大氣結晶行星", "綻放混成園")
        wl_names = ("灰燼行者", "灰燼行者長", "螢光獵手", "沼澤變異體", "拾荒王",
                    "站內巡邏無人機", "軌道站維修機械")
        leak = []
        for loc, names in sim_systems.LOCATION_ENEMIES.items():
            if loc in targets:
                continue
            for n in names:
                if n in wl_names:
                    leak.append(f"{loc}:{n}")
        assert not leak, f"W03/W04 敵人洩漏到 W01: {leak}"

    def test_normal_scenes_no_shadow_enemies(self):
        """批次 52（改）：影之敵（X之影）只允許出現在演出場景與角色家鄉
        （批次 52 的暗影挑戰指派 _SHADOW_HOME_MAP）；隨機污染普通場景的
        影之敵（非家鄉指派）不得存在。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        perf_kw = ("舞台", "演唱會", "模式", "瞬間", "盲區", "更衣室", "直播",
                   "控制室", "核心室", "體育場", "競技", "演出")
        home_map = getattr(sim_systems, "SHADOW_HOME_MAP", {}) or {}
        bad = []
        for loc, names in sim_systems.LOCATION_ENEMIES.items():
            if any(k in loc for k in perf_kw):
                continue
            assigned = set(home_map.get(loc, []))
            for n in names:
                if "之影" in n and n not in assigned:
                    bad.append(f"{loc}:{n}")
        assert not bad, f"非家鄉指派的影之敵污染普通場景: {bad}"
        # 演出場景保留影之敵
        assert any(any("之影" in n for n in sim_systems.LOCATION_ENEMIES.get(loc, []))
                   for loc in sim_systems.LOCATION_ENEMIES if any(k in loc for k in perf_kw)), \
            "演出場景應保留影之敵"

    def test_card_shadow_enemies_encounterable(self):
        """批次 52：卡片影之敵（X之影/深淵X之影）不得是死資料——
        普通版暗影必須可遭遇（絕對無魔安全村角色或家鄉池已達上限者除外），
        且任一場所的影之敵不得超過其非影敵（文明場所遭遇以場所主題為主）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        perf_kw = ("舞台", "演唱會", "模式", "瞬間", "盲區", "更衣室", "直播",
                   "控制室", "核心室", "體育場", "競技", "演出")
        placed = {n for pool in sim_systems.LOCATION_ENEMIES.values() for n in pool}
        all_shadows = [e["name"] for e in sim_systems.ENEMIES if "之影" in e["name"]]
        unplaced = [n for n in all_shadows if n not in placed]
        normal = [n for n in unplaced if not n.startswith("深淵")]
        reg = getattr(sim_systems, "SHADOW_CHALLENGES", {}) or {}
        # 普通版未放置只允許：安全村角色，或家鄉池已達上限（影之敵≥非影敵）
        for n in normal:
            home = reg.get(n, "")
            pool = sim_systems.LOCATION_ENEMIES.get(home, [])
            nonshadow = len([x for x in pool if "之影" not in x])
            shadowcnt = len([x for x in pool if "之影" in x])
            assert (home in ("小吉鎮", "大根莖村") or shadowcnt >= nonshadow), \
                f"普通版影之敵 {n}@{home} 未放置且未達上限"
        # 影之敵不得淹沒非演出場所的遭遇池（演出場景是暗影對戰場地，豁免）；
        # 無非影敵的場所（角色家鄉即挑戰點）最多 1 個影之敵。
        for loc, pool in sim_systems.LOCATION_ENEMIES.items():
            if any(k in loc for k in perf_kw):
                continue
            nonshadow = len([x for x in pool if "之影" not in x])
            shadowcnt = len([x for x in pool if "之影" in x])
            assert shadowcnt <= max(1, nonshadow), \
                f"{loc} 影之敵({shadowcnt})超過非影敵({nonshadow})"
        # 家鄉指派的一致性：SHADOW_HOME_MAP 的每個條目都真的在該地點池中
        home_map = getattr(sim_systems, "SHADOW_HOME_MAP", {}) or {}
        for loc, names in home_map.items():
            pool = sim_systems.LOCATION_ENEMIES.get(loc, [])
            for n in names:
                assert n in pool, f"家鄉指派 {n}@{loc} 不在遭遇池"
        assert placed, "沒有任何影之敵可遭遇"

    def test_wood_drop_enables_quest_completion(self):
        """批次 45：SQ-09「收集材料」需木材×3——先前木材 0 掉落
        （商店/掉落/配方皆無）→ 任務永不可完成。森林系敵人
        （哥布林/森狼/野豬/巨熊/大鹿/虎/狼）必須掉木材。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        cat = sim_systems.ITEM_CATALOG
        assert "木材" in cat, "木材必須存在於 ITEM_CATALOG"
        wood_droppers = [e["name"] for e in sim_systems.ENEMIES if "木材" in e.get("loot", [])]
        assert wood_droppers, "沒有任何敵人掉木材——SQ-09 永不可完成"
        # 森林系基底敵人至少有一個掉木材
        keys = ("哥布林", "森狼", "野豬", "巨熊", "大鹿", "虎")
        assert any(any(k in n for k in keys) for n in wood_droppers), \
            f"森林系敵人應掉木材: {wood_droppers}"
        # 全任務 collect 目標都至少有獲取路徑（商店/掉落/配方）
        shop_items = {it for n, nd in sim_systems.NPC_METADATA.items()
                      for it in nd.get("offers", [])}
        loot_items = {it for e in sim_systems.ENEMIES for it in e.get("loot", [])}
        recipe_items = {r.get("result_item") or r.get("result") for r in sim_systems.RECIPES}
        recipe_items |= {ing.get("item") if isinstance(ing, dict) else ing
                         for r in sim_systems.RECIPES
                         for ing in r.get("ingredients", []) or r.get("materials", [])}
        unobtainable = []
        for q in sim_systems.QUESTS:
            for obj in q.get("objectives", []):
                if obj.get("type") == "collect":
                    t = obj.get("target")
                    if t not in shop_items and t not in loot_items and t not in recipe_items:
                        unobtainable.append(f"{q.get('id')}:{t}")
        assert not unobtainable, f"collect 目標無獲取路徑: {unobtainable}"

    def test_quest_givers_and_targets_exist(self):
        """批次 45：所有任務 giver NPC 必須存在於 NPC_METADATA，
        giver_location 與 defeat/goto 目標地點必須存在於地圖。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        loc_set = (set(sim_systems.WORLD_MAP) | set(sim_systems.LOCATION_ENEMIES)
                   | set(sim_systems.LOCATION_VIBES))
        enemy_set = {e["name"] for e in sim_systems.ENEMIES}
        npc_set = set(sim_systems.NPC_METADATA)
        problems = []
        for q in sim_systems.QUESTS:
            g = q.get("giver", "")
            if g and g != "系統" and g not in npc_set:
                problems.append(f"giver NPC 不存在: {g} ({q.get('id')})")
            gl = q.get("giver_location", "") or q.get("location", "")
            if gl and gl not in loc_set:
                problems.append(f"giver 地點不存在: {gl} ({q.get('id')})")
            for obj in q.get("objectives", []):
                if obj.get("type") == "defeat":
                    en = obj.get("enemy") or obj.get("target")
                    if en and en not in enemy_set:
                        problems.append(f"defeat 目標敵人不存在: {en} ({q.get('id')})")
                elif obj.get("type") == "goto":
                    if obj.get("location") and obj.get("location") not in loc_set:
                        problems.append(f"goto 目標地點不存在: {obj.get('location')} ({q.get('id')})")
        assert not problems, "\n".join(problems[:12])

    def test_flying_and_water_vehicle_abilities(self):
        """批次 46：擴充載具（熱氣球/魔法掃帚/飛空艇/龍騎乘/漁船/帆船）
        必須有對應能力——飛行載具可飛越水域、船可渡水。騎乘時
        get_water_routes 需開通水域路線；非飛行/渡水載具（腳踏車）不得。"""
        import sim_systems
        from game_data import expand_game
        from character_system import generate_character_from_card, init_skills, mount_vehicle
        expand_game()
        abilities = sim_systems.VEHICLE_ABILITIES
        # 飛行載具
        for vn in ("熱氣球", "魔法掃帚", "魔法飛毯", "飛空艇", "龍騎乘"):
            assert "飛行" in abilities.get(vn, {}), f"{vn} 應有飛行能力（描述為飛行載具）"
        # 水載具
        for vn in ("漁船", "帆船", "大型帆船", "小舟"):
            assert "渡水" in abilities.get(vn, {}), f"{vn} 應有渡水能力"
        # 騎乘飛行載具 → 水域路線開通
        import json
        cards = json.load(open("data/game_cards.json", encoding="utf-8"))["cards"]
        ch = generate_character_from_card(next(c for c in cards if c["card_id"] == "CC-01"))
        init_skills(ch)
        ch.setdefault("vehicles", {})["熱氣球"] = {"owned": True, "fuel": "fire"}
        mount_vehicle(ch, "熱氣球", ch["vehicles"])
        assert sim_systems.get_water_routes("鏡湖", ch), "騎熱氣球應可飛越水域"
        # 騎帆船 → 渡水
        ch.setdefault("vehicles", {})["帆船"] = {"owned": True, "fuel": "wind"}
        mount_vehicle(ch, "帆船", ch["vehicles"])
        assert sim_systems.get_water_routes("鏡湖", ch), "騎帆船應可渡水"
        # 腳踏車（無能力）不得渡水
        ch.setdefault("vehicles", {})["腳踏車"] = {"owned": True, "fuel": 100}
        mount_vehicle(ch, "腳踏車", ch["vehicles"])
        assert not sim_systems.get_water_routes("鏡湖", ch), "腳踏車不能渡水"

    def test_vehicle_world_line_category(self):
        """批次 46：載具世界線分類——魔法載具（魔法掃帚/飛空艇）→ magic
        （W02 失效）、蒸汽/機動（蒸氣機車/機車/吉普車）→ tech、
        生物/人力（馬/腳踏車/船）→ natural。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        v = sim_systems.VEHICLES
        assert sim_systems.get_vehicle_world_category(v["魔法掃帚"]) == "magic"
        assert sim_systems.get_vehicle_world_category(v["飛空艇"]) == "magic"
        assert sim_systems.get_vehicle_world_category(v["蒸氣機車"]) == "tech"
        assert sim_systems.get_vehicle_world_category(v["機車"]) == "tech"
        assert sim_systems.get_vehicle_world_category(v["馬"]) == "natural"
        assert sim_systems.get_vehicle_world_category(v["腳踏車"]) == "natural"
        assert sim_systems.get_vehicle_world_category(v["漁船"]) == "natural"

    def test_movement_abilities_negation_aware(self):
        """批次 53：移動能力關鍵字匹配需否定語境感知——文本種族描述常以
        否定句排除亞種歸屬（「純血術式適應體，非龍娘/獸人/妖精等亞種」），
        否定子句內的關鍵字不得觸發能力（東 雲 純血魔女曾被誤判可飛行）；
        真天使（否定的是位階非翅膀）仍可飛行。"""
        from axis_system import movement_abilities
        # 否定語境：純血魔女明言非龍娘/妖精等亞種 → 不得因「妖精」字眼飛
        m = movement_abilities(
            text_race="魔女（まじょ）——純血術式適應體，非龍娘/獸人/妖精等亞種")
        assert not m.get("fly"), f"否定子句誤觸發飛行: {m}"
        # 真天使（無大天使位階是位階否定，非翅膀否定）→ 可飛行
        m2 = movement_abilities(
            text_race="天使（第三環・醫療專責／非戰鬥型，無大天使位階，無熾天使權能）")
        assert m2.get("fly"), f"真天使應可飛行: {m2}"
        # 、/／ 是列表分隔符不中斷否定範圍（「非A、B、C」整串否定）
        m3 = movement_abilities(
            text_race="魔女——純血術式適應體，非龍娘、獸人、妖精等亞種")
        assert not m3.get("fly"), f"、分隔的否定列表誤觸發飛行: {m3}"
        # 不/未 單字不視為否定（未來型天使/不具人形的妖精仍為天使/妖精）
        assert movement_abilities(text_race="未來型天使（試作）").get("fly")
        assert movement_abilities(text_race="不具人形的妖精").get("fly")
        # 正常正向匹配不受影響
        assert movement_abilities(text_race="天空龍娘").get("fly")
        assert movement_abilities(text_race="艦娘").get("sail")
        assert movement_abilities(text_race="人魚").get("swim")
        assert not movement_abilities(text_race="人類").get("fly")

    def test_all_locations_reachable_from_campus(self):
        """批次 47：地圖全域可達性——從聖十字校園出發（含反向入邊，
        等同 run_game do_travel 合併邏輯）所有 WORLD_MAP 地點皆可達。
        原缺陷：方向鍵衝突（校園 west 只能存便利店或秘密鐵工廠之一）
        讓 12+ 場景單向死路（星光舞台/英靈殿/迴廊/月之宮殿等
        玩家進去就回不來或根本進不去）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        wm = sim_systems.WORLD_MAP
        from collections import deque
        start = "聖十字校園"
        reach = {start}
        q = deque([start])
        while q:
            cur = q.popleft()
            outs = list(wm.get(cur, {}).values())
            for loc, e in wm.items():
                if loc != cur and cur in e.values():
                    outs.append(loc)
            for d in outs:
                if d and d not in reach:
                    reach.add(d)
                    q.append(d)
        unreachable = [l for l in wm if l not in reach]
        assert not unreachable, f"不可達地點: {unreachable}"
        # 演出場景（星光舞台及其子區域）必須可達（SC-20 卡片內容可玩）
        assert "星光舞台" in reach, "星光舞台不可達"
        assert "演唱會模式" in reach, "演唱會模式不可達"


# =============================================================================
# 10. 演出場景內容（批次 48）
# =============================================================================

class TestPerformanceScenes:
    """SC-20 星光舞台演出場景稽核：載具不得誤停（漁船/熱氣球塞進舞台）、
    須有舞台設備物件（主舞台/音響塔/導播台）、偶像團 NPC 依文本歸位。"""

    _PERF_KW = ("舞台", "演唱會", "模式", "瞬間", "盲區", "更衣室", "直播",
                "控制室", "核心室", "體育場", "異常")

    def test_no_vehicles_parked_in_performance_scenes(self):
        """演出場景不得被載具 fallback 隨機指派（原缺陷：星光舞台=漁船、
        演唱會模式=熱氣球、伺服器核心室=雪橇——與演出語境完全無關）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        bad = [(loc, vn) for loc, vn in sim_systems.VEHICLE_LOCATIONS.items()
               if any(k in loc for k in self._PERF_KW)]
        assert not bad, f"演出場景誤停載具: {bad}"

    def test_performance_scenes_have_stage_equipment(self):
        """星光舞台須有舞台設備物件（主舞台/音響塔/導播台等），
        而非被交通工具塞滿。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        objs = [o.get("name", "") for o in sim_systems.SCENE_OBJECTS.get("星光舞台", [])]
        stage_kw = ("主舞台", "音響", "導播台", "燈光", "麥克風", "舞台")
        hits = [o for o in objs if any(k in o for k in stage_kw)]
        assert hits, f"星光舞台應有舞台設備物件: {objs}"
        # 不得再有交通工具型場景物件（漁船/熱氣球）
        veh = [o for o in objs if any(v in o for v in ("漁船", "熱氣球", "蒸氣機車", "飛空艇"))]
        assert not veh, f"星光舞台仍有交通工具物件: {veh}"

    def test_cross_world_line_contextual_vehicles(self):
        """跨線場景的載具應符語境：熒光沼澤（沼澤）不得停腳踏車。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        assert sim_systems.VEHICLE_LOCATIONS.get("熒光沼澤") != "腳踏車", "熒光沼澤不該停腳踏車"
        assert sim_systems.VEHICLE_LOCATIONS.get("軌道居住站大學院") != "自行車", \
            "軌道站不該停自行車（太空站）"

    def test_idol_group_npcs_at_star_stage(self):
        """文本（CC-30/31/47）：特戰偶像團、台灣AI小N、呃咔屬星光舞台
        演出區域——主要排程地點須在星光舞台。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        for name, expect in (("特戰偶像團", "星光舞台"), ("台灣AI小N", "星光舞台"),
                             ("呃咔", "星光舞台"), ("奶油泡芙", "西翼大市集")):
            nd = sim_systems.NPC_METADATA.get(name)
            assert nd, f"NPC {name} 不存在"
            sched = sim_systems.NPC_SCHEDULES.get(name, [])
            assert sched, f"NPC {name} 無排程"
            main = sched[0][3]
            assert main == expect, f"{name} 主要排程地 {main} ≠ {expect}"
            assert main in sim_systems.WORLD_MAP, f"{name} 的基地 {main} 不在可探索地圖（玩家無法到達）"

    def test_idol_group_reachable_at_work_hours(self):
        """10 點（工作時段）在星光舞台能遇到偶像團（排程查詢）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        found = []
        for name in ("特戰偶像團", "台灣AI小N", "呃咔"):
            act, aloc, _mood = sim_systems.get_npc_activity(name, 10, "春")
            if aloc == "星光舞台":
                found.append(name)
        assert found == ["特戰偶像團", "台灣AI小N", "呃咔"], f"10點星光舞台應有 3 偶像團: {found}"

    def test_idol_group_offers_in_catalog(self):
        """偶像團 NPC 的商店庫存（offers）全部存在於 ITEM_CATALOG
        （演唱會門票/簽名海報/特戰偶像團周邊等演出語境商品）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        cat = sim_systems.ITEM_CATALOG
        for n in ("特戰偶像團", "呃咔", "奶油泡芙"):
            for it in sim_systems.NPC_METADATA.get(n, {}).get("offers", []):
                assert it in cat, f"{n} 的 offers 引用不存在道具: {it}"


# =============================================================================
# 11. 任務可達性與平衡（批次 49）
# =============================================================================

class TestQuestReachabilityBalance:
    """任務稽核：giver 排程時段可達、獎勵曲線不倒掛、
    目標敵人強度與任務等級匹配、時段限制與 giver 排程重疊。"""

    def _req_lv(self, q):
        c = q.get("conditions", {}) or {}
        return c.get("required_level") or q.get("required_level") or q.get("level", 1)

    def _overlap(self, a, b, c, d):
        a2, b2 = (a, b) if b > a else (a, b + 24)
        c2, d2 = (c, d) if d > c else (c, d + 24)
        return a2 < d2 and c2 < b2

    def test_quest_giver_schedules_cover_wake_hours(self):
        """所有 giver NPC 排程涵蓋常見造訪時段（8-22 逐時）——
        玩家在白天/傍晚造訪不會撲空。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        probs = []
        for q in sim_systems.QUESTS:
            g = q.get("giver", "")
            if not g or g == "系統":
                continue
            sched = sim_systems.NPC_SCHEDULES.get(g)
            assert sched, f"giver {g} 無排程"
            hours = set()
            for st, et, _a, _l, _m in sched:
                h = st
                while h != et:
                    hours.add(h)
                    h = (h + 1) % 24
            missing = [h for h in (8, 10, 12, 14, 16, 18, 20, 22) if h not in hours]
            if missing:
                probs.append(f"{q['id']} ({g}): 缺口 {missing}")
        assert not probs, "\n".join(probs[:10])

    def test_quest_reward_curve_no_inversion(self):
        """任務獎勵曲線：同級任務 EXP 差異 ≤3 倍、高級任務不低於低級 2 倍。"""
        import collections
        import sim_systems
        from game_data import expand_game
        expand_game()
        by_level = collections.defaultdict(list)
        for q in sim_systems.QUESTS:
            # 每日任務（DQ）是刻意低獎勵的重複性任務，不納入曲線；
            # reward_exp 非數值（None/文字列表，如 SL-XX-MAIN 故事追蹤任務
            # 獎勵=劇情）亦排除——依 schema 判斷而非 id 後綴。
            if q.get("type") == "daily":
                continue
            rw = q.get("reward_exp")
            if not isinstance(rw, (int, float)):
                continue
            lv = self._req_lv(q)
            by_level[lv].append((q["id"], rw))
        for lv, items in by_level.items():
            exps = [e for _i, e in items if e > 0]
            if len(exps) >= 2:
                assert max(exps) / min(exps) <= 3.0, (
                    f"Lv{lv} 同級 EXP 差過大: {items}")
        for lv in sorted(by_level):
            for lv2 in sorted(by_level):
                if lv2 > lv:
                    hi = max(e for _i, e in by_level[lv] if e > 0)
                    lo = min(e for _i, e in by_level[lv2] if e > 0)
                    assert hi <= lo * 2, f"倒掛: Lv{lv} 最高 {hi} > Lv{lv2} 最低 {lo}"

    def test_quest_enemy_strength_matches_level(self):
        """任務 defeat 目標的敵人強度（HP 推估等級）不得超過任務等級 +2——
        Lv1 任務不該叫玩家打 HP150 的古代守衛。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        enemy_map = {e["name"]: e for e in sim_systems.ENEMIES}
        probs = []
        for q in sim_systems.QUESTS:
            lv = self._req_lv(q)
            for obj in q.get("objectives", []):
                if obj.get("type") == "defeat":
                    en = obj.get("enemy") or obj.get("target")
                    e = enemy_map.get(en)
                    if not e:
                        continue
                    est_lv = max(1, (e.get("hp", 30) - 20) // 25 + 1)
                    if est_lv > lv + 2:
                        probs.append(f"{q['id']} Lv{lv} 要打 {en} (HP{e.get('hp')})")
        assert not probs, "\n".join(probs[:10])

    def test_quest_time_window_overlaps_giver_schedule(self):
        """任務 time_available 時段內 giver 至少有排程槽位重疊
        （含跨午夜時段如 SQ-08 18-6——小狐丸 18-22 西翼大市集）。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        probs = []
        for q in sim_systems.QUESTS:
            g = q.get("giver", "")
            if not g or g == "系統":
                continue
            ta = (q.get("conditions", {}) or {}).get("time_available")
            if not ta:
                continue
            sh, eh = ta.get("start_hour", 0), ta.get("end_hour", 24)
            sched = sim_systems.NPC_SCHEDULES.get(g, [])
            ok = any(self._overlap(sh, eh, st, et) for (st, et, _a, _l, _m) in sched)
            if not ok:
                probs.append(f"{q['id']} ({g}): 時段 {sh}-{eh} 內無排程")
        assert not probs, "\n".join(probs[:10])

    def test_quest_goto_targets_world_line_reachable(self):
        """任務 goto/visit 目標若是跨世界線地點，其進入等級不得超過任務等級——
        Lv1 任務不該要玩家去需 Lv6 的 W03/W04。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        wl = sim_systems.LOCATION_WORLD_LINES
        entry = sim_systems.ENTRY_REQUIREMENTS
        probs = []
        for q in sim_systems.QUESTS:
            lv = self._req_lv(q)
            for obj in q.get("objectives", []):
                loc = obj.get("location") or obj.get("target")
                if obj.get("type") in ("goto", "visit") and loc:
                    w = wl.get(loc, "W01")
                    if w not in ("W01", "W01+迴廊"):
                        req = (entry.get(loc, {}) or {}).get("required_level", 0)
                        if req > lv:
                            probs.append(f"{q['id']} Lv{lv} → {loc} 需 Lv{req} ({w})")
        assert not probs, "\n".join(probs[:10])

    def test_common_consumable_prices_sane(self):
        """初期消耗品價格與 Lv1-3 任務平均獎勵相符——
        治療藥水 40G 對 Lv1-3 任務約 50G 平均獎勵可負擔。"""
        import sim_systems
        from game_data import expand_game
        expand_game()
        cat = sim_systems.ITEM_CATALOG
        assert cat["治療藥水"]["value"] <= 60, "治療藥水不該過貴"
        assert cat["乾糧"]["value"] <= 15, "乾糧應是廉價口糧"
        # 艦裝/軍武類（稀有）可高價，但常規消耗品不得 >150G
        for n in ("解毒草", "草藥", "魔力藥水", "治療藥水", "乾糧"):
            assert cat[n]["value"] <= 150, f"常規道具 {n} 價格離群"
