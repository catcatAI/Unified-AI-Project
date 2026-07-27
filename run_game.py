"""CLI RPG Simulation — Complete Game Loop."""
import sys
import os
import random as _random
from collections import Counter as _Counter
from pathlib import Path

src = Path(__file__).resolve().parent / "apps" / "backend" / "src"
sys.path.insert(0, str(src))

from sim_systems import (
    EquipmentManager,
    craft_item,
    get_npc_activity,
    get_time_desc,
    display_world_map,
    get_enemy,
    resolve_combat_turn,
    get_item_def,
    get_junk_items,
    ENEMY_ENCOUNTER_CHANCE,
    REAL_ESTATE,
    WORLD_MAP,
    LOCATION_VIBES,
    RECIPES,
    NPC_SCHEDULES,
    EQUIPMENT_SLOTS,
    get_equipment_slots_for_character,
    ITEM_CATALOG,
    QUESTS,
    DAILY_QUESTS_IDS,
    reset_daily_quests,
    RACE_TASK_IDS,
    VEHICLES,
    VEHICLE_LOCATIONS,
    SCENE_OBJECTS,
    WEATHER_TYPES,
    roll_weather,
    WEATHER_EFFECTS,
    roll_random_event,
    MAX_INVENTORY_SLOTS,
    MAX_INVENTORY_WEIGHT,
    MAX_PROPERTIES,
)
from game_data import expand_game

from character_system import (
    generate_character_from_card,
    create_blank_character,
    get_character_cards,
    display_character_sheet,
    display_body_parts,
    display_relationships,
    apply_damage,
    heal_character,
    add_relationship,
    get_relationship,
    gain_exp,
    gain_exp_with_skills,
    gain_skill_exp,
    get_skill_modifier,
    init_skills,
    init_quest_state,
    accept_quest,
    advance_quest_objective,
    check_quest_completion,
    complete_quest,
    get_active_quests,
    check_quest_eligibility,
    get_available_quests,
    init_vehicle_state,
    mount_vehicle,
    dismount_vehicle,
    get_portrait,
    get_reputation_tier,
    modify_reputation,
    save_game,
    load_game,
    delete_save,
    BODY_PARTS,
    C,
)

# ── Globals ────────────────────────────────────────────────────────────────
_current_weather = "☀晴"


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════


def clear_screen():
    """Clear terminal screen per INTERFACE_TERMINAL.md§清屏"""
    os.system("cls" if os.name == "nt" else "clear")


def _gm_narrate(character, new_location=None):
    """GM-style scene narration per GAME_OVERVIEW.md GM system."""
    loc = new_location or character.get("location","?")
    vibes = LOCATION_VIBES.get(loc,"")
    gm_descs = {
        "方碑丘": "微風吹過金黃色的稻田，村莊裡炊煙裊裊升起。",
        "鏡湖": "湖面如鏡，倒映著天空的雲彩。空氣中彌漫著淡淡的水氣。",
        "西翼大市集": "人聲鼎沸，各種叫賣聲此起彼落。香料和烤肉的香氣交織在一起。",
        "中央大圖書館": "宏偉的建築內藏書萬卷，陽光透過彩色玻璃窗灑落。",
        "海峽": "海風強勁，潮汐拍打著岩岸。遠方海平面與天際融為一線。",
        "秘密鐵工廠": "鐵鎚聲與蒸氣嘶鳴交織，火花在昏暗的空間中四濺。",
        "便利店": "明亮的燈光透過玻璃門照出，貨架上擺滿了日常用品。",
        "英靈殿": "古老的大殿中迴盪著腳步聲，牆上掛滿了武器與褪色的旗幟。",
        "廢棄礦坑": "陰暗的礦坑入口散發著潮濕的氣息，深不見底的黑暗令人卻步。",
        "森林深處": "參天大樹遮天蔽日，鳥鳴與蟲鳴交織成自然的交響曲。",
    }
    desc = gm_descs.get(loc)
    if desc:
        print(C.DIM + "  [GM] " + desc + C.RESET)
    print(vibes)
    npcs_near = []
    for npc_name in list(NPC_SCHEDULES.keys()):
        act, aloc, mood = get_npc_activity(npc_name, character["hour"])
        if aloc == loc:
            npcs_near.append(npc_name)
    if npcs_near:
        print(C.DIM + "  [GM] 你看到" + "、".join(npcs_near) + "在附近。" + C.RESET)

def advance_time(character, hours=1):
    global _current_weather
    character["hour"] = (character["hour"] + hours) % 24
    if character["hour"] == 0:
        character["day"] += 1
        _current_weather = roll_weather()

def print_banner(text, color=C.CYAN):
    print(color + "═"*50 + C.RESET)
    print(color + text.center(50) + C.RESET)
    print(color + "═"*50 + C.RESET)

def _restore(c, stat, amount):
    mk = "max_" + stat
    c[stat] = min(c.get(mk, 100), c.get(stat,0) + amount)

def _mini_bar(character, width=10):
    ratio = character["hp"] / character["max_hp"] if character["max_hp"]>0 else 0
    f = int(ratio * width)
    return C.RED + "█"*f + C.DIM + "░"*(width-f) + C.RESET


# ═══════════════════════════════════════════════════════════════════════════
# STATUS & HELP
# ═══════════════════════════════════════════════════════════════════════════

def print_status(character):
    global _current_weather
    print("")
    time_str = get_time_desc(character["hour"], character["day"])
    weather_info = _current_weather + " " + WEATHER_EFFECTS.get(_current_weather,{}).get("desc","")
    print(C.DIM + "─"*50 + C.RESET)
    print(C.CYAN + "  ◈ " + time_str + C.RESET + "  " + weather_info)
    race = character.get("race", "人類")
    print(C.WHITE + "  位置: " + character["location"] + C.RESET + "  " + C.MAGENTA + "[ " + race + " ]" + C.RESET, end="")
    if character.get("riding"):
        print(C.YELLOW + " [騎乘: " + character["riding"] + "]" + C.RESET)
    else:
        print("")

    # HP / SP / EXP bars
    hp_r = character["hp"]/character["max_hp"] if character["max_hp"]>0 else 0
    sp_r = character["sp"]/character["max_sp"] if character["max_sp"]>0 else 0
    hp_b = C.RED + "█"*int(hp_r*15) + C.DIM + "░"*(15-int(hp_r*15)) + C.RESET
    sp_b = C.BLUE + "█"*int(sp_r*15) + C.DIM + "░"*(15-int(sp_r*15)) + C.RESET
    print("  " + C.RED + "HP:" + C.RESET + " %3d/%d %s" % (character["hp"],character["max_hp"],hp_b) +
          "  " + C.RED + "ATK:%3d" % character["atk"] + C.RESET + "  " + C.RED + "DEF:%3d" % character["defense"] + C.RESET)
    print("  " + C.BLUE + "SP:" + C.RESET + " %3d/%d %s" % (character["sp"],character["max_sp"],sp_b) +
          "  " + C.YELLOW + "Lv.%d" % character["level"] + C.RESET + "  " + C.GREEN + "EXP:%d/%d" % (character["exp"], exp_needed_for_level(character["level"])) + C.RESET)

    # All NPCs — show those at current location + some high-rep ones
    print(C.DIM + "─"*50 + C.RESET)
    cur_loc = character["location"]
    npcs_here = []
    all_sched = NPC_SCHEDULES
    for npc_name in list(all_sched.keys()):
        act, aloc, mood = get_npc_activity(npc_name, character["hour"])
        if aloc == cur_loc:
            npcs_here.append((npc_name, act, aloc, mood))
    for npc_name, act, nloc, mood in npcs_here[:5]:
        mc = {"calm":C.GREEN,"alert":C.RED,"rest":C.BLUE,"friendly":C.MAGENTA,"sleep":C.GRAY,"focused":C.CYAN}
        mcol = mc.get(mood, C.WHITE)
        print("  " + C.CYAN + npc_name + C.RESET + ": " + act + " @ " + cur_loc + " (" + mcol + mood + C.RESET + ")")
    if not npcs_here:
        print(C.GRAY + "  附近似乎沒有NPC。" + C.RESET)
    # Active quests count
    active = get_active_quests(character)
    if active:
        print(C.GREEN + "  進行中任務: %d" % len(active) + C.RESET)
    print(C.DIM + "─"*50 + C.RESET)
    print("")

def exp_needed_for_level(level):
    return 100 + (level - 1) * 50

def print_help():
    print(C.WHITE + C.BOLD + "╔═══════════════════════════╗" + C.RESET)
    print(C.WHITE + C.BOLD + "║  指令選單" + " "*21 + C.BOLD + "║" + C.RESET)
    print(C.WHITE + C.BOLD + "╠═══════════════════════════╣" + C.RESET)
    print(C.WHITE + C.BOLD + "║" + C.RESET + " 1.探索  2.NPC對話  3.移動")
    print(C.WHITE + C.BOLD + "║" + C.RESET + " 4.休息  5.物品欄  6.角色")
    print(C.WHITE + C.BOLD + "║" + C.RESET + " 7.身體  8.裝備   9.地圖")
    print(C.WHITE + C.BOLD + "║" + C.RESET + "10.關係 11.合成  12.搜索")
    print(C.WHITE + C.BOLD + "║" + C.RESET + "13.任務 14.車輛  15.不動產")
    print(C.WHITE + C.BOLD + "║" + C.RESET + "  s.存檔   l.讀檔   q.退出")
    print(C.WHITE + C.BOLD + "╚═══════════════════════════╝" + C.RESET)


# ═══════════════════════════════════════════════════════════════════════════
# CHARACTER SELECTION
# ═══════════════════════════════════════════════════════════════════════════

def select_character():
    cards = get_character_cards()
    PAGE_SIZE = 10
    total_cards = len(cards)
    total_pages = (total_cards + PAGE_SIZE - 1) // PAGE_SIZE
    page = 0

    while True:
        print_banner("選擇你的角色 (%d位)" % total_cards, C.MAGENTA)
        print("")
        start = page * PAGE_SIZE
        end = min(start + PAGE_SIZE, total_cards)
        for i in range(start, end):
            card = cards[i]
            name = card.get("name","?")
            cid = card.get("card_id","???")
            ts = card.get("token_summary",{})
            if isinstance(ts, dict):
                tstr = " ".join("%s:%d"%(k,v) for k,v in ts.items())
            else:
                tstr = str(ts)[:50]
            print("  %s%2d. [%s]%s %s" % (C.CYAN,i+1,cid,C.RESET,name))
            print("      %s%s%s" % (C.DIM,tstr[:50],C.RESET))
        print("")
        # Navigation footer
        nav = []
        if page > 0:
            nav.append("p.上一頁")
        if page < total_pages - 1:
            nav.append("n.下一頁")
        nav.append("c.自定義角色")
        print("  " + "  ".join(nav))
        print(C.GRAY + "  第 %d/%d 頁 — 輸入編號選擇角色" % (page + 1, total_pages) + C.RESET)
        print("")
        ch = input("  %s>%s " % (C.YELLOW,C.RESET)).strip().lower()
        if ch in ("n", "next") and page < total_pages - 1:
            page += 1
            continue
        elif ch in ("p", "prev") and page > 0:
            page -= 1
            continue
        elif ch in ("c", "custom"):
            print(C.YELLOW + "\n  你選擇了自定義角色。" + C.RESET)
            char = create_blank_character()
            name = input(C.CYAN + "  輸入角色名稱: " + C.RESET).strip()
            if name:
                char["name"] = name
            init_skills(char)
            init_quest_state(char)
            init_vehicle_state(char)
            advance_time(char)
            return char
        elif ch.isdigit():
            idx = int(ch) - 1
            if 0 <= idx < total_cards:
                card = cards[idx]
                char = generate_character_from_card(card)
                init_skills(char)
                init_quest_state(char)
                init_vehicle_state(char)
                print(C.GREEN + "\n  你選擇了: %s (卡片 %s)" % (char["name"],char["card_id"]) + C.RESET)
                advance_time(char)
                return char
        print(C.RED + "  無效輸入。" + C.RESET)
        continue


# ═══════════════════════════════════════════════════════════════════════════
# COMBAT
# ═══════════════════════════════════════════════════════════════════════════

def do_combat(character, enemy):
    print(C.RED+C.BOLD+"\n⚔ "+"="*40+" ⚔"+C.RESET)
    print(C.RED+C.BOLD+"  戰鬥! 遭遇了 %s!" % enemy["name"]+C.RESET)
    print("  " + enemy.get("desc","") + " | HP:%d ATK:%d DEF:%d" % (enemy["hp"],enemy["atk"],enemy["def"]))
    print(C.RED+C.BOLD+"⚔ "+"="*40+" ⚔"+C.RESET)
    e_hp = enemy["hp"]
    e_max = enemy["hp"]
    while e_hp > 0 and character["hp"] > 0:
        print("\n  " + C.WHITE+C.BOLD+"[你的回合]"+C.RESET)
        print("    "+C.GREEN+"1. 攻擊"+C.RESET+"    "+C.BLUE+"2. 防禦"+C.RESET+"    "+C.YELLOW+"0. 逃跑"+C.RESET)
        act = input("    "+C.YELLOW+">"+C.RESET+" ").strip()
        defending = False
        if act == "2":
            defending = True
            print(C.BLUE+"    🛡 防禦姿態!"+C.RESET)
        # Escape
        if act == "0":
            if _random.random() < 0.5:
                print(C.GREEN+"    ✓ 成功逃脫!"+C.RESET)
                return True
            else:
                print(C.RED+"    ✗ 逃跑失敗!"+C.RESET)

        if act == "1" or act == "0":
            pa = character["atk"] + get_skill_modifier(character, "combat")
            ps = character.get("spd",5)
            dmg, crit = resolve_combat_turn(pa, ps, enemy["def"], e_hp)
            e_hp -= dmg
            cs = C.YELLOW+" (暴擊!)"+C.RESET if crit else ""
            print(C.RED+"    ⚔ 造成 %d 傷害!%s" % (dmg,cs)+C.RESET)
            for m in gain_skill_exp(character,"combat",3):
                print("      "+C.CYAN+m+C.RESET)
            # Consume weapon durability
            for hand in ["right_hand","left_hand","both_hands"]:
                broke = equipment.use_durability(hand, 1)
                if broke:
                    eq_info = equipment.slots.get(hand)
                    if eq_info and eq_info["item"]:
                        iname = eq_info["item"].get("name","?")
                        print(f"      {C.RED}⚡ {iname} 損壞了!{C.RESET}")
                        old = equipment.unequip(hand)
                        if old:
                            character["inventory"].append(old.get("name","?"))
                        equipment.apply_stat_bonuses(character)

        if e_hp <= 0:
            break

        dm = 0.7 if defending else 1.0
        ed = max(1, int(enemy["atk"]*dm - character["defense"]*0.3))
        ed = min(ed, character["hp"])
        valid = [p[0] for p in BODY_PARTS if p[0] in character.get("body_parts",{})]
        bp = _random.choice(valid) if valid else "torso"
        apply_damage(character, ed, bp)
        # Fatigue/pain system per NUMERICAL_SYSTEMS.md
        character["fatigue"] = character.get("fatigue", 0) + _random.randint(3, 8)
        character["pain"] = character.get("pain", 0) + _random.randint(2, 6)
        # Bleeding: ongoing damage per NUMERICAL_SYSTEMS.md
        bleed = character.get("bleed_rate", 0)
        if bleed > 0:
            bdmg = min(character["hp"], bleed)
            character["hp"] -= bdmg
            print(C.RED+"      🩸 傷口流血，失去 %dHP! (出血率:%d)"%(bdmg,bleed)+C.RESET)
        if _random.random() < 0.15 and character.get("pain", 0) > 30:
            character["bleed_rate"] = character.get("bleed_rate", 0) + 1
            print(C.RED+"      🩸 傷口開始流血!"+C.RESET)
        # Fatigue thresholds per NUMERICAL_SYSTEMS.md
        fatigue_val = character.get("fatigue", 0)
        if fatigue_val > 80:
            print(C.YELLOW+"      💤 疲勞度已高! 行動速度下降。"+C.RESET)
        if fatigue_val > 90 and _random.random() < 0.3:
            print(C.RED+"      💤 疲勞過度，無法行動!"+C.RESET)
        # Pain thresholds per NUMERICAL_SYSTEMS.md
        pain_val = character.get("pain", 0)
        if pain_val > 60 and _random.random() < 0.3:
            print(C.RED+"      😖 傷口疼痛使你行動失敗!"+C.RESET)
        if pain_val > 80 and _random.random() < 0.5:
            print(C.RED+"      😖 劇痛使你癱瘓!"+C.RESET)
        ds = C.BLUE+" (減半)"+C.RESET if defending else ""
        print(C.MAGENTA+"    💥 %s 造成 %d 傷害!%s" % (enemy["name"],ed,ds)+C.RESET)
        # Consume armor durability on hit (per ITEM_EQUIPMENT_SYSTEM.md: 戰鬥受擊消耗耐久)
        for slot in ["torso","head","legs","feet","back"]:
            equipment.use_durability(slot, _random.randint(2,6))
        ebar = C.RED+"█"*int(max(0,e_hp/e_max)*10)+C.DIM+"░"*(10-int(max(0,e_hp/e_max)*10))+C.RESET
        print("      Enemy: %s %d/%d" % (ebar,e_hp,e_max))
        print("      Your:  "+_mini_bar(character)+" %d/%d"%(character["hp"],character["max_hp"]))

    if e_hp <= 0:
        eg = enemy["exp"]
        gg = enemy["gold"]
        print("\n"+C.GREEN+C.BOLD+"  勝利!"+C.RESET)
        print("  "+C.YELLOW+"獲得 %d EXP, %d 金幣!"%(eg,gg)+C.RESET)
        for li in enemy.get("loot",[]):
            if _random.random()<0.5:
                character["inventory"].append(li)
                print("  "+C.CYAN+"獲得物品: %s"%li+C.RESET)
        character["gold"] = character.get("gold",0) + gg
        modify_reputation(character,2)
        for m in gain_exp_with_skills(character,eg,"exploration",5):
            print("  "+C.MAGENTA+C.BOLD+m+C.RESET)
        # Advance quest objectives
        for q in get_active_quests(character):
            qdef, qdata = q
            advance_quest_objective(character, qdef["id"], "defeat", enemy["name"], 1)
        advance_time(character)
        return True
    else:
        print(C.RED+C.BOLD+"  ☠ 被擊敗!"+C.RESET)
        return False


# ═══════════════════════════════════════════════════════════════════════════
# EXPLORATION
# ═══════════════════════════════════════════════════════════════════════════

def do_explore(character, equipment):
    global _current_weather
    we = WEATHER_EFFECTS.get(_current_weather, {"encounter":0.4,"loot_bonus":0})
    enc_chance = we["encounter"]
    loot_bonus = we["loot_bonus"]

    print(C.CYAN+"\n  🧭 探索 " + character["location"] + " ..."+C.RESET)
    # Random event before combat
    roll_random_event(character)

    # Combat check
    riding_bonus = 1.0
    if character.get("riding"):
        v = VEHICLES.get(character["riding"])
        if v:
            riding_bonus = v.get("speed", 1.0)
    if _random.random() < enc_chance / riding_bonus:
        enemy = get_enemy(character["location"])
        if enemy:
            result = do_combat(character, enemy)
            if not result:
                character["hp"] = max(1, character["max_hp"]//4)
                print(C.RED+"  你在昏迷中醒來...體力嚴重消耗。"+C.RESET)
                advance_time(character,3)
            return

    # Loot
    all_finds = ["草藥","木柄","火元素","鐵礦","乾糧","治療藥水","空瓶","樹枝","小石頭","貝殼","麻繩"]
    if character["hour"]>=20 or character["hour"]<5:
        all_finds += ["魔力藥水","護身符","火元素","水晶碎片","魔法粉"]
    explore_mod = get_skill_modifier(character,"exploration")
    if explore_mod>0 and _random.random()<0.3:
        all_finds += ["皮甲","鐵錠","匕首","靈木","鐵劍"]

    # Maybe junk
    if _random.random() < 0.25:
        junk = get_junk_items()
        if junk:
            all_finds.append(_random.choice(junk))

    # Loot bonus from weather (full WEATHER_EFFECTS implementation)
    if loot_bonus > 0:
        bonus_finds = []
        if _random.random() < loot_bonus:
            bonus_finds = ["水晶碎片","魔法粉","火元素","靈木"]
            all_finds.append(_random.choice(bonus_finds))

    find = _random.choice(all_finds)
    if find:
        idf = get_item_def(find)
        character["inventory"].append(find)
        print(C.GREEN+"  ✓ 發現: %s!"%find+C.RESET)
        if idf.get("desc"):
            print(C.DIM+"    %s"%idf["desc"]+C.RESET)
    else:
        print(C.GRAY+"  ⋯ 什麼都沒有。"+C.RESET)
    for m in gain_skill_exp(character,"exploration",2):
        print("  "+C.CYAN+m+C.RESET)
    # Consume feet/legs durability during exploration
    for slot in ["feet","legs"]:
        equipment.use_durability(slot, _random.randint(1,2))
    advance_time(character)


# ═══════════════════════════════════════════════════════════════════════════
# TRAVEL
# ═══════════════════════════════════════════════════════════════════════════

def do_travel(character):
    dests = WORLD_MAP.get(character["location"], {})
    if not dests:
        print(C.GRAY+"  ⚻ 沒有通路。"+C.RESET)
        return
    print(C.CYAN+"  可去的地方:"+C.RESET)
    icons = {"east":"→","west":"←","north":"↑","south":"↓","enter":"🚪","exit":"🚶"}
    for i,(d,loc) in enumerate(dests.items(),1):
        ic = icons.get(d,"•")
        vibe = LOCATION_VIBES.get(loc,"")
        print("    %d. %s %s  %s"%(i,ic,loc,vibe))
    print("    %s0. 取消%s"%(C.GRAY,C.RESET))
    ch = input("  %s選擇:%s " % (C.YELLOW,C.RESET)).strip()
    if not ch.isdigit(): return
    idx = int(ch)
    if idx==0: return
    if 1<=idx<=len(dests):
            dest = list(dests.values())[idx-1]
            # Travel time
            hours = 1
            if character.get("riding"):
                v = VEHICLES.get(character["riding"])
                if v:
                    hours = max(1, int(1 / v.get("speed",1.0)))
                    # Vehicle fuel consumption
                    fuel_used = v.get("fuel_per_hour", 0) * hours
                    if fuel_used > 0:
                        # Track fuel in vehicle state
                        veh_state = character.get("vehicles", {}).get(character["riding"], {})
                        veh_fuel = veh_state.get("fuel", v.get("fuel", 100))
                        veh_fuel = max(0, veh_fuel - fuel_used)
                        if "vehicles" not in character:
                            character["vehicles"] = {}
                        if character["riding"] not in character["vehicles"]:
                            character["vehicles"][character["riding"]] = {}
                        character["vehicles"][character["riding"]]["fuel"] = veh_fuel
                        if veh_fuel <= 0:
                            print(C.RED+"    ⛽ %s燃料耗盡，無法騎乘!"%character["riding"]+C.RESET)
                            character["riding"] = None
                        else:
                            fuel_pct = int(veh_fuel / v.get("fuel", 100) * 100)
                            print(C.YELLOW+"    ⛽ 燃料: %d%%"%fuel_pct+C.RESET)
            character["location"] = dest
            advance_time(character, hours)
            vibe = LOCATION_VIBES.get(dest,"")
            print(C.GREEN+"  移動到 %s。%s" % (dest, vibe)+C.RESET)
            # Random event on travel
            roll_random_event(character)
            return
    print(C.RED+"  無效。"+C.RESET)


# ═══════════════════════════════════════════════════════════════════════════
# REST
# ═══════════════════════════════════════════════════════════════════════════

def do_rest(character):
    global _current_weather
    we = WEATHER_EFFECTS.get(_current_weather, {"rest_bonus":1.0})
    bonus = we["rest_bonus"]
    heal_hp = min(character["max_hp"]-character["hp"], int(35*bonus))
    heal_sp = min(character["max_sp"]-character["sp"], int(25*bonus))
    character["hp"] += heal_hp
    character["sp"] += heal_sp
    # Fatigue/pain recovery during rest
    character["fatigue"] = max(0, character.get("fatigue", 0) - 30)
    character["pain"] = max(0, character.get("pain", 0) - 20)

    events = [
        (0.2,"夢境","🌙 做了奇異的夢...關於鏡湖的光。",
         lambda c:[_restore(c,"sp",30),_restore(c,"hp",40),
                   gain_exp_with_skills(c,10,"knowledge",10)]),
        (0.1,"NPC訪問","🌷 有NPC來探望你，感覺心情好了。",
         lambda c:[_restore(c,"hp",20),_restore(c,"sp",20),modify_reputation(c,3)]),
        (0.1,"危險","⚡ 被聲響驚醒!幸好沒事。",
         lambda c: c["hp"]<c["max_hp"]-10 and c.update({"hp":min(c["max_hp"],c["hp"]+10)})),
        (0.6,"平靜","💤 安安靜靜地休息。",
         lambda c:[_restore(c,"hp",35),_restore(c,"sp",25)]),
    ]
    roll = _random.random()
    cum = 0.0
    triggered = False
    for prob, ename, desc, action in events:
        cum += prob
        if roll < cum:
            print(C.CYAN+"\n  [休息事件: %s]"%ename+C.RESET+" "+desc)
            action(character)
            triggered = True
            break
    if not triggered:
        print(C.CYAN+"\n  💤 休息，恢復 %dHP %dSP。"%(heal_hp,heal_sp)+C.RESET)
    else:
        print(C.GRAY+"  (HP+%d, SP+%d)"%(heal_hp,heal_sp)+C.RESET)
    advance_time(character,2)


# ═══════════════════════════════════════════════════════════════════════════
# INVENTORY
# ═══════════════════════════════════════════════════════════════════════════

def do_inventory(character):
    inv = character["inventory"]
    total_w = sum(get_item_def(i).get("weight",0.5) for i in inv)
    print("")
    print(C.CYAN+"┌"+"─"*40+"┐"+C.RESET)
    print(C.CYAN+"│  物品欄 (%d/%d)  負重 %.1f/%.0f kg" % (len(inv),MAX_INVENTORY_SLOTS,total_w,MAX_INVENTORY_WEIGHT)+C.RESET)
    print(C.CYAN+"├"+"─"*40+"┤"+C.RESET)
    tc = {"consumable":C.GREEN,"weapon":C.RED,"armor":C.BLUE,"material":C.YELLOW,
          "accessory":C.MAGENTA,"quest":C.CYAN,"junk":C.GRAY,"misc":C.WHITE}
    if not inv:
        print(C.CYAN+"│  "+C.GRAY+"（空）"+C.RESET+" "*33+C.CYAN+"│"+C.RESET)
    else:
        item_counts = _Counter(inv)
        seen = set()
        display_idx = 1
        for i, item in enumerate(inv,1):
            if item in seen:
                continue
            seen.add(item)
            count = item_counts[item]
            d = get_item_def(item)
            ty = d.get("type","misc")
            co = tc.get(ty,C.WHITE)
            wt = d.get("weight",0.5)
            val = d.get("value",0)
            stack_str = ""
            max_stk = d.get("max_stack", 0)
            if max_stk > 0 and count > 1:
                stack_str = C.DIM+" x%d"%count+C.RESET
            rarity = C.DIM+""+C.RESET
            if "rare" in d.get("tags", []) or "龍鱗" in item or "生命" in item:
                rarity = C.YELLOW+"★"+C.RESET
            elif val > 150:
                rarity = C.MAGENTA+"✦"+C.RESET
            line = "  %s%2d.%s %s%s %s%s%s" % (co,display_idx,C.RESET,rarity,co,item,stack_str,C.RESET) + " (%.1fkg)"%wt
            print(C.CYAN+"│ "+line.ljust(40)+C.CYAN+"│"+C.RESET)
            display_idx += 1
    print(C.CYAN+"└"+"─"*40+"┘"+C.RESET)
    print("  "+C.YELLOW+"金幣: %d"%character.get("gold",0)+C.RESET)
    if total_w > MAX_INVENTORY_WEIGHT:
        print(C.RED+"  ⚠ 負重過載!"+C.RESET)
    if len(inv) >= MAX_INVENTORY_SLOTS:
        print(C.YELLOW+"  ⚠ 物品欄已滿!"+C.RESET)
    # ── Use/Discard items ──
    if inv:
        print("  "+C.CYAN+"選擇物品編號使用，或輸入 d+編號 丟棄 (如 d3)"+C.RESET)
        ch = input("  %s>%s " % (C.YELLOW,C.RESET)).strip()
        # Map display index to flat index (first occurrence of Nth unique item)
        unique_items = []
        seen = set()
        for it in inv:
            if it not in seen:
                seen.add(it)
                unique_items.append(it)
        def _display_to_flat(didx):
            if 0 <= didx < len(unique_items):
                target = unique_items[didx]
                return inv.index(target)
            return -1
        if ch.startswith('d') or ch.startswith('D'):
            idx_str = ch[1:]
            if idx_str.isdigit():
                didx = int(idx_str) - 1
                fidx = _display_to_flat(didx)
                if fidx >= 0:
                    item_name = inv.pop(fidx)
                    print(C.GRAY+"  丟棄了 %s。"%item_name+C.RESET)
        elif ch.isdigit():
            didx = int(ch) - 1
            fidx = _display_to_flat(didx)
            if fidx >= 0:
                item_name = inv[fidx]
                idf = get_item_def(item_name)
                if idf.get("type") == "consumable":
                    hh = idf.get("heal_hp", 0)
                    hs = idf.get("heal_sp", 0)
                    if hh > 0 or hs > 0:
                        if hh > 0:
                            ah = min(character["max_hp"]-character["hp"], hh)
                            character["hp"] += ah
                            print(C.GREEN+"  使用了 %s +%dHP!"%(item_name,ah)+C.RESET)
                        if hs > 0:
                            a2 = min(character["max_sp"]-character["sp"], hs)
                            character["sp"] += a2
                            print(C.BLUE+"  使用了 %s +%dSP!"%(item_name,a2)+C.RESET)
                        inv.pop(fidx)
                    elif "解毒" in item_name or idf.get("cure"):
                        print(C.GREEN+"  使用了 %s。"%item_name+C.RESET)
                        inv.pop(fidx)
                    else:
                        print(C.GRAY+"  無法直接使用。"+C.RESET)
                else:
                    print(C.GRAY+"  %s 無法直接使用。去裝備欄裝備它。"%item_name+C.RESET)


# ═══════════════════════════════════════════════════════════════════════════
# EQUIPMENT
# ═══════════════════════════════════════════════════════════════════════════

def do_equipment_menu(character, equipment):
    print("\n"+C.WHITE+C.BOLD+"  裝備管理"+C.RESET)
    print("  "+C.CYAN+"1. 查看"+C.RESET+"  "+C.CYAN+"2. 裝備"+C.RESET+"  "+C.CYAN+"3. 卸下"+C.RESET+"  "+C.GRAY+"0. 返回"+C.RESET)
    ch = input("  %s>%s " % (C.YELLOW,C.RESET)).strip()
    if ch=="1":
        print(equipment.display())
        b = equipment.get_stat_bonuses()
        if b:
            print(C.DIM+"  加成: "+" ".join("%s%+.1f"%(k,v) for k,v in b.items())+C.RESET)
    elif ch=="2":
        inv = character["inventory"]
        print(C.CYAN+"  物品欄:"+C.RESET)
        for i,item in enumerate(inv,1):
            d = get_item_def(item)
            sl = d.get("slot","")
            h = " (→%s)"%sl if sl else ""
            print("    %d. %s%s"%(i,item,h))
        if not inv:
            print(C.GRAY+"    （空）"+C.RESET); return
        ic = input("  %s編號:%s " % (C.YELLOW,C.RESET)).strip()
        if not ic.isdigit(): return
        idx = int(ic)-1
        if idx<0 or idx>=len(inv): return
        iname = inv[idx]
        idf = get_item_def(iname)
        # Check race requirement
        req_race = idf.get("required_race", "")
        if req_race:
            char_race = character.get("race", "人類")
            if req_race != char_race:
                print(C.RED+"  ⚠ %s 是 %s 專用裝備! 你的角色是 %s。" % (iname, req_race, char_race)+C.RESET)
                return
        # Consumable: use directly
        if idf.get("type")=="consumable":
            hh = idf.get("heal_hp",0)
            hs = idf.get("heal_sp",0)
            if hh>0:
                ah = min(character["max_hp"]-character["hp"],hh)
                character["hp"] += ah
                print(C.GREEN+"  使用了 %s +%dHP!"%(iname,ah)+C.RESET)
            if hs>0:
                a2 = min(character["max_sp"]-character["sp"],hs)
                character["sp"] += a2
                print(C.BLUE+"  使用了 %s +%dSP!"%(iname,a2)+C.RESET)
            inv.pop(idx)
            gain_skill_exp(character,"craft",1)
            return
        # Archetype/race equipment check
        req_arch = idf.get("required_archetype", "")
        if req_arch:
            char_tokens = {t.get("category","") for t in character.get("token_list", [])}
            if req_arch not in char_tokens:
                print(C.RED+"  ⚠ %s 需要 [%s] 類別特質才能裝備!" % (iname, req_arch)+C.RESET)
                print(C.GRAY+"    你的角色沒有「%s」類別的token。" % req_arch+C.RESET)
                return
        # Equip — use dynamic slot list from equipment object
        ss = idf.get("slot","")
        slot_list = equipment._slot_order
        for j,(sid,sname) in enumerate(slot_list):
            cur = equipment.slots.get(sid)
            st = cur["item"]["name"] if cur and cur["item"] else "(空)"
            mk = " ★" if sid==ss else ""
            print("    %d. %s [%s]%s"%(j+1,sname,st,mk))
        sc = input("  %s槽位編號:%s " % (C.YELLOW,C.RESET)).strip()
        if not sc.isdigit(): return
        si = int(sc)-1
        if si<0 or si>=len(slot_list): return
        sid = slot_list[si][0]
        md = idf.get("durability",100)
        old = equipment.equip(sid, {"name":iname,"durability":md,"current_durability":md,
                                     "stat_multipliers":idf.get("stat_multipliers",{})})
        if old:
            character["inventory"].append(old.get("name",old))
        inv.pop(idx)
        equipment.apply_stat_bonuses(character)
        slot_name = next((n for s,n in slot_list if s==sid), sid)
        print(C.GREEN+"  已裝備 %s → %s"%(iname,slot_name)+C.RESET)
    elif ch=="3":
        print(equipment.display())
        sid = input("  %s卸下槽位ID:%s " % (C.YELLOW,C.RESET)).strip()
        vs = {s[0] for s in equipment._slot_order}
        if sid not in vs: return
        old = equipment.unequip(sid)
        if old:
            character["inventory"].append(old.get("name","?"))
            equipment.apply_stat_bonuses(character)
            print(C.GREEN+"  已卸下 %s"%old.get("name","?")+C.RESET)
        else:
            print(C.GRAY+"  該槽位空的。"+C.RESET)


# ═══════════════════════════════════════════════════════════════════════════
# CRAFTING
# ═══════════════════════════════════════════════════════════════════════════

def do_crafting(character, equipment=None):
    print("")
    print(C.CYAN+"┌"+"─"*44+"┐"+C.RESET)
    print(C.CYAN+"│  合成系統"+C.RESET+" "*33+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"├"+"─"*44+"┤"+C.RESET)
    for r in RECIPES:
        igs = ", ".join("%s x%d"%(ig["item"],ig["quantity"]) for ig in r["ingredients"])
        has = all(character["inventory"].count(ig["item"])>=ig["quantity"] for ig in r["ingredients"])
        st = C.GREEN+"✓"+C.RESET if has else C.RED+"✗"+C.RESET
        print(C.CYAN+("│ %s %s %s: %s"%(st,r["recipe_id"],r["name"],igs)).ljust(42)+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"│  "+C.GREEN+"輸入 r 修復裝備"+C.RESET+" "*20+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"└"+"─"*44+"┘"+C.RESET)
    rid = input("  %s配方ID (r=修復, Enter取消):%s " % (C.YELLOW,C.RESET)).strip().lower()
    if not rid: return
    if rid == 'r':
        if equipment:
            from sim_systems import repair_equipment as _repair
            suc, msg = _repair(equipment, character)
            if suc:
                print(C.GREEN+"  ✓ "+msg+C.RESET)
            else:
                print(C.RED+"  ✗ "+msg+C.RESET)
        else:
            print(C.RED+"  無法修復: 無裝備管理器。"+C.RESET)
        advance_time(character)
        return
    suc, res, msg = craft_item(rid, character["inventory"])
    if suc:
        print(C.GREEN+"  ✓ "+msg+C.RESET)
        gain_skill_exp(character,"craft",8)
    else:
        print(C.RED+"  ✗ "+msg+C.RESET)
    advance_time(character)


# ═══════════════════════════════════════════════════════════════════════════
# SCENE OBJECT INTERACTION (搜索)
# ═══════════════════════════════════════════════════════════════════════════

def do_scene_search(character, equipment):
    loc = character["location"]
    objs = SCENE_OBJECTS.get(loc, [])
    if not objs:
        print(C.GRAY+"\n  這裡沒有可互動的物體。"+C.RESET)
        return

    # Check for workstation bonus
    has_workshop = False
    for prop_name, prop in character.get("owned_properties", {}).items():
        if "craft" in prop.get("functions", []):
            has_workshop = True

    print(C.CYAN+"\n  可互動物體:"+C.RESET)
    for i, obj in enumerate(objs, 1):
        icons = {"container":"📦","decoration":"🎨","workstation":"🔧","vehicle":"🚢"}
        ic = icons.get(obj["type"],"•")
        locked = " 🔒" if obj.get("locked") else ""
        print("    %d. %s %s%s" % (i, ic, obj["name"], locked))
    print("    %s0. 取消%s" % (C.GRAY, C.RESET))
    ch = input("  %s選擇:%s " % (C.YELLOW, C.RESET)).strip()
    if not ch.isdigit(): return
    idx = int(ch)-1
    if idx<0 or idx>=len(objs): return
    obj = objs[idx]
    obj_name = obj.get("name","?")
    obj_type = obj.get("type","")
    print(C.CYAN+"\n  [%s] %s" % (obj_name, obj.get("desc",""))+C.RESET)

    if obj_type == "decoration":
        note = obj.get("note","")
        if note:
            print("  " + C.YELLOW + note + C.RESET)
        else:
            print(C.GRAY+"  只是個普通的%s。"%obj_name+C.RESET)

    elif obj_type == "container":
        if obj.get("locked"):
            key_needed = obj.get("key","")
            has_key = key_needed and key_needed in character["inventory"]
            if has_key:
                print(C.GREEN+"  🔑 用%s解鎖了!"%key_needed+C.RESET)
                obj["locked"] = False
            else:
                print(C.RED+"  🔒 鎖住了。需要: %s"%key_needed+C.RESET)
                return
        contents = obj.get("contents", [])
        if contents:
            print(C.GREEN+"  📦 找到:"+C.RESET)
            for item in contents:
                character["inventory"].append(item)
                print("    ✓ %s"%item)
            obj["contents"] = []  # looted
        else:
            print(C.GRAY+"  📦 裡面是空的。"+C.RESET)

    elif obj_type == "workstation":
        st = obj.get("station_type","")
        print(C.CYAN+"  🔧 這是個%s工作台。"%st+C.RESET)
        if has_workshop:
            print(C.GREEN+"  (你擁有的工坊提供額外加成!)"+C.RESET)
        print(C.GREEN+"  1. 使用工作台(恢復SP)"+C.RESET)
        print(C.GREEN+"  2. 合成(使用工作台加成)"+C.RESET)
        print(C.GRAY+"  0. 離開"+C.RESET)
        wc = input("  %s>%s " % (C.YELLOW,C.RESET)).strip()
        if wc == "1":
            heal = 15 * (2 if has_workshop else 1)
            _restore(character, "sp", heal)
            print(C.BLUE+"  在%s休息，恢復%dSP。"%(obj_name,heal)+C.RESET)
        elif wc == "2":
            do_crafting(character, equipment)

    elif obj_type == "vehicle":
        vt = obj.get("vehicle_type","")
        if vt:
            # Check if player owns it or can use it
            if vt in VEHICLES:
                print(C.CYAN+"  🚢 %s - %s" % (vt, VEHICLES[vt]["desc"])+C.RESET)
                print(C.GREEN+"  1. 騎乘"+C.RESET)
                print(C.GRAY+"  0. 取消"+C.RESET)
                vc = input("  %s>%s " % (C.YELLOW,C.RESET)).strip()
                if vc == "1":
                    # Check if owned or can be found here
                    veh_state = character.get("vehicles", {})
                    if vt not in veh_state or not veh_state[vt].get("owned", False):
                        vdef = VEHICLES.get(vt, {})
                        init_fuel = vdef.get("fuel", 100)
                        veh_state[vt] = {"owned": True, "location": loc, "fuel": init_fuel}
                        character["vehicles"] = veh_state
                        print(C.GREEN+"  你獲得了 %s! (燃料:%d)"%(vt,init_fuel)+C.RESET)
                    mount_vehicle(character, vt, veh_state)
                    print(C.GREEN+"  騎上了 %s!"%vt+C.RESET)

    advance_time(character)


# ═══════════════════════════════════════════════════════════════════════════
# NPC INTERACTION
# ═══════════════════════════════════════════════════════════════════════════

def do_interact_npc(character):
    loc = character["location"]
    rep = character.get("reputation",0)
    # Find ALL NPCs at this location based on schedule
    npcs_here = []
    all_sched = NPC_SCHEDULES
    for npc_name in all_sched:
        act, aloc, mood = get_npc_activity(npc_name, character["hour"])
        if aloc == loc:
            npcs_here.append((npc_name, act, aloc, mood))

    if not npcs_here:
        print(C.GRAY+"\n  這裡沒有可互動的NPC。"+C.RESET)
        return

    print(C.CYAN+"\n  遇到的NPC:"+C.RESET)
    for i,(n,act,aloc,m) in enumerate(npcs_here,1):
        mc_icons = {"focused":"⚔","alert":"👁","rest":"💤","friendly":"😊","sleep":"😴"}
        ic = mc_icons.get(m,"•")
        print("    %d. %s%s %s (%s)"%(i,ic,n,act))
    print("    %s0. 取消%s"%(C.GRAY,C.RESET))
    ch = input("  %s>%s " % (C.YELLOW,C.RESET)).strip()
    if not ch.isdigit(): return
    idx = int(ch)-1
    if idx<0 or idx>=len(npcs_here): return
    npc_name, npc_act, npc_loc, npc_mood = npcs_here[idx]

    # NPC-specific interactions for known NPCs, generic for others
    if npc_name == "小狐丸":
        print("\n" + C.CYAN + "  小狐丸正在" + npc_act + "。" + C.RESET)
        if rep >= 20:
            print(C.CYAN+"  小狐丸: 「你好，旅人。」"+C.RESET)
            print(C.GREEN+"  1. 詢問消息"+C.RESET)
            print(C.CYAN+"  2. 交流 (SP-10)"+C.RESET)
            print(C.GREEN+"  3. 送禮物"+C.RESET)
            print(C.CYAN+"  4. 接受任務"+C.RESET)
        else:
            print(C.CYAN+"  小狐丸淡淡看了你一眼。"+C.RESET)
            print(C.GREEN+"  1. 打招呼"+C.RESET)
            print(C.CYAN+"  2. 交流 (SP-10)"+C.RESET)
        print(C.GRAY+"  0. 離開"+C.RESET)
        c = input("  %s>%s " % (C.YELLOW,C.RESET)).strip()

        if c=="1":
            if rep>=20:
                print(C.YELLOW+'  小狐丸: 「鏡湖的水晶最近不太穩定...小心點。」'+C.RESET)
                add_relationship(character,"小狐丸",2)
                modify_reputation(character,1)
            else:
                print(C.YELLOW+'  小狐丸: 「...你好。」'+C.RESET)
                add_relationship(character,"小狐丸",1)
        elif c=="2":
            if character["sp"]>=10:
                character["sp"]-=10
                eg = 15+rep//10
                print(C.CYAN+"  交流獲得%d經驗。"%eg+C.RESET+C.GRAY+" (SP-10)"+C.RESET)
                for m in gain_exp_with_skills(character,eg,"knowledge",5):
                    print("  "+C.MAGENTA+m+C.RESET)
                add_relationship(character,"小狐丸",5)
            else:
                print(C.RED+"  SP不足!"+C.RESET)
        elif c=="3" and rep>=20:
            gifts = [g for g in ["草藥","火元素","水晶碎片"] if g in character["inventory"]]
            if gifts:
                g = _random.choice(gifts)
                character["inventory"].remove(g)
                add_relationship(character,"小狐丸",10)
                modify_reputation(character,2)
                print(C.GREEN+"  送出%s, +10好感!"%g+C.RESET)
            else:
                print(C.GRAY+"  你沒有可送的禮物。"+C.RESET)
        elif c=="4" and rep>=20:
            _try_accept_quest(character, "SQ-02") or _try_accept_quest(character, "SQ-08")
        else:
            if rep>=20: add_relationship(character,"小狐丸",-1)
            print(C.GRAY+"  告別小狐丸。"+C.RESET)

    elif npc_name == "左間小蒼蘭":
        print("\n"+C.CYAN+"  左間小蒼蘭正在%s。"%npc_act+C.RESET)
        print(C.CYAN+"  左間小蒼蘭: 「需要什麼？」"+C.RESET)
        print(C.GREEN+"  1. 詢問合成配方"+C.RESET)
        print(C.CYAN+"  2. 工坊休息 (SP+20)"+C.RESET)
        print(C.GREEN+"  3. 學習製作 (SP-8)"+C.RESET)
        print(C.CYAN+"  4. 接受任務"+C.RESET)
        print(C.GRAY+"  0. 離開"+C.RESET)
        c = input("  %s>%s "%(C.YELLOW,C.RESET)).strip()
        if c=="1":
            print(C.YELLOW+"  小蒼蘭展示了配方: 火焰藥水、鐵劍、皮甲、治療藥水。"+C.RESET)
            add_relationship(character,"左間小蒼蘭",3)
        elif c=="2":
            hs = min(character["max_sp"]-character["sp"],25)
            character["sp"]+=hs
            print(C.BLUE+"  工坊休息 +%dSP。"%hs+C.RESET)
            add_relationship(character,"左間小蒼蘭",2)
        elif c=="3":
            if character["sp"]>=8:
                character["sp"]-=8
                for m in gain_exp_with_skills(character,10,"craft",8):
                    print("  "+C.MAGENTA+m+C.RESET)
                print(C.GREEN+"  學到製作技巧!"+C.RESET)
                add_relationship(character,"左間小蒼蘭",4)
            else:
                print(C.RED+"  SP不足!"+C.RESET)
        elif c=="4":
            _try_accept_quest(character,"MQ-02") or _try_accept_quest(character,"SQ-07")
        else:
            add_relationship(character,"左間小蒼蘭",-1)
            print(C.GRAY+"  告別小蒼蘭。"+C.RESET)

    elif npc_name == "紅":
        print("\n"+C.CYAN+"  紅正在%s。"%npc_act+C.RESET)
        if rep>=15:
            print(C.CYAN+"  紅: 「歡迎光臨!」"+C.RESET)
        else:
            print(C.CYAN+"  紅: 「...需要什麼？」"+C.RESET)
        print(C.GREEN+"  1. 商店"+C.RESET)
        print(C.CYAN+"  2. 交流"+C.RESET)
        print(C.CYAN+"  3. 接受任務"+C.RESET)
        print(C.GRAY+"  0. 離開"+C.RESET)
        c = input("  %s>%s "%(C.YELLOW,C.RESET)).strip()
        if c=="1":
            print(C.CYAN+"  紅的商店:"+C.RESET)
            items_sold = [("草藥",10),("乾糧",8),("治療藥水",40),("皮甲",60),("解毒草",20)]
            for i,(name,price) in enumerate(items_sold,1):
                lock = "" if i<4 else C.DIM+" (需聲望%d)"%({"皮甲":20,"解毒草":10}.get(name,0))+C.RESET
                print("  %d. %s (%dG)%s"%(i,name,price,lock))
            bc = input("  %s購買編號 (0取消):%s "%(C.YELLOW,C.RESET)).strip()
            if bc.isdigit():
                bi = int(bc)-1
                if 0<=bi<len(items_sold):
                    iname, iprice = items_sold[bi]
                    rep_needed = {"草藥":0,"乾糧":0,"治療藥水":0,"皮甲":20,"解毒草":10}.get(iname,0)
                    if rep<rep_needed:
                        print(C.RED+"  聲望不足 (需%d)"%rep_needed+C.RESET)
                    elif character.get("gold",0)>=iprice:
                        character["gold"]=character.get("gold",0)-iprice
                        character["inventory"].append(iname)
                        print(C.GREEN+"  買了 %s!"%iname+C.RESET)
                        add_relationship(character,"紅",1)
                    else:
                        print(C.RED+"  金幣不足!"+C.RESET)
        elif c=="2":
            print(C.YELLOW+'  紅: 「這裡是安全區。」'+C.RESET)
            add_relationship(character,"紅",2)
            modify_reputation(character,1)
        elif c=="3":
            _try_accept_quest(character,"SQ-01") or _try_accept_quest(character,"SQ-06")
        else:
            add_relationship(character,"紅",-1)
            print(C.GRAY+"  告別紅。"+C.RESET)

    else:
        # Generic NPC interaction for dynamically generated NPCs
        print("\n"+C.CYAN+"  %s正在%s。"%(npc_name,npc_act)+C.RESET)
        rep_tier = get_reputation_tier(rep)
        mood_color = {"calm":C.GREEN,"alert":C.RED,"rest":C.BLUE,"friendly":C.MAGENTA,"sleep":C.GRAY,"focused":C.CYAN}
        mood_icon = {"focused":"⚔","alert":"👁","rest":"💤","friendly":"😊","sleep":"😴"}
        print(C.CYAN+"  %s: 聲望[%s] %s%s%s"%(npc_name,rep_tier,mood_icon.get(npc_mood,""),mood_color.get(npc_mood,C.WHITE),npc_mood)+C.RESET)
        # Reputation-based greeting variety
        greet_pool = {
            "敵意": ["「...離我遠點。」","「哼。」","「你來做什麼？」"],
            "冷淡": ["「...你好。」","「有事嗎？」","「說吧。」"],
            "中立": ["「你好啊。」","「今天天氣不錯。」","「有什麼需要？」"],
            "友好": ["「嗨!」","「又見面了!」","「有什麼能幫你的？」"],
            "親密": ["「你來啦!」","「剛好想找你!」","「一起去喝杯茶？」"],
        }
        greet = _random.choice(greet_pool.get(rep_tier, ["「...」"]))
        # 80+ reputation: hidden info & special dialogue
        if rep >= 80:
            print(C.MAGENTA + "  (好感度高，%s露出了開心的笑容。)"%npc_name + C.RESET)
            if _random.random() < 0.4:
                hidden_info = [
                    "悄悄告訴你，鏡湖深處藏著古代的遺跡...",
                    "你知道嗎？英靈殿底下還有更深的樓層。",
                    "我聽說西翼市集有人賣很特別的東西...",
                    "這個世界遠比你想像的大。",
                ]
                print(C.MAGENTA + "  %s低聲說: 「%s」" % (npc_name, _random.choice(hidden_info)) + C.RESET)
                gain_skill_exp(character, "knowledge", 5)
        print(C.CYAN+"  1. "+C.GREEN+"打招呼"+C.RESET)
        print(C.CYAN+"  2. "+C.BLUE+"交流"+C.RESET+" (SP-10)")
        print(C.CYAN+"  3. "+C.CYAN+"送禮物"+C.RESET)
        # Shop option for NPCs at commercial locations
        shop_locations = ["西翼大市集","便利店"]
        if loc in shop_locations:
            print(C.CYAN+"  4. "+C.YELLOW+"商店 (買東西)"+C.RESET)
        quest_opt = 5 if loc in shop_locations else 4
        if rep >= 50 and len(get_active_quests(character)) < 3:
            print(C.CYAN+"  %d. "%quest_opt+C.YELLOW+"接受任務"+C.RESET)
        print(C.GRAY+"  0. 離開"+C.RESET)
        c = input("  %s>%s "%(C.YELLOW,C.RESET)).strip()
        if c=="1":
            npc_emote = _random.choice(["「こんにちは。」","「ニーハオ。」","「ハロー。」"])
            print(C.YELLOW+'  %s: %s %s'%(npc_name,greet,npc_emote)+C.RESET)
            add_relationship(character,npc_name,2)
            modify_reputation(character,1)
        elif c=="2":
            if character["sp"]>=10:
                character["sp"]-=10
                eg = 10+rep//15
                print(C.CYAN+"  交流獲得%d經驗。"%eg+C.RESET+C.GRAY+" (SP-10)"+C.RESET)
                for m in gain_exp_with_skills(character,eg,"social",3):
                    print("  "+C.MAGENTA+m+C.RESET)
                add_relationship(character,npc_name,5)
            else:
                print(C.RED+"  SP不足!"+C.RESET)
        elif c=="3":
            gifts = [g for g in ["草藥","空瓶","貝殼","乾糧","乾燥花","羽毛"] if g in character.get("inventory",[])]
            if gifts:
                g = _random.choice(gifts)
                character["inventory"].remove(g)
                rep_gain = 8 + rep//20  # More rep = better gift reception
                add_relationship(character,npc_name,rep_gain)
                modify_reputation(character,2)
                gift_responses = {
                    "敵意": ["「...不要。」","「拿走。」"],
                    "冷淡": ["「...謝謝。」","「放這吧。」"],
                    "中立": ["「哦，謝謝!」","「你太客氣了。」"],
                    "友好": ["「哇，是%s! 謝謝!」","「你最好了!」"],
                    "親密": ["「謝謝你送的%s!」","「我會好好珍惜%s的!」"],
                }
                gr = _random.choice(gift_responses.get(rep_tier, ["「...」"]))
                if "%s" in gr:
                    print(C.GREEN+"  送出%s! %s"%(g,gr%g)+C.RESET)
                else:
                    print(C.GREEN+"  送出%s! %s"%(g,gr)+C.RESET)
            else:
                print(C.GRAY+"  沒有可送的禮物。"+C.RESET)
        elif c=="4" and rep >= 50:
            # Find eligible available quests
            available = get_available_quests(character)
            eligible = [q for q, reason in available if reason is None and q["type"]=="side"]
            ineligible = [q for q, reason in available if reason is not None and q["type"]=="side"]
            if eligible:
                q = _random.choice(eligible)
                accept_quest(character, q)
                print(C.GREEN+"  ✓ 接受了任務: %s"%q["title"]+C.RESET)
                print(C.DIM+"    %s"%q["desc"]+C.RESET)
                add_relationship(character,npc_name,10)
            elif ineligible:
                q, reason = ineligible[0]
                print(C.YELLOW+"  ⚠ 有任務但條件不符: %s - %s" % (q["title"], reason)+C.RESET)
            else:
                print(C.GRAY+"  目前沒有可接受的任務。"+C.RESET)
        else:
            add_relationship(character,npc_name,-1)
            print(C.GRAY+"  告別%s。"%npc_name+C.RESET)

    advance_time(character)

def _time_range_str(time_avail):
    """Format time range for display."""
    if not time_avail:
        return ""
    sh = time_avail.get("start_hour", 0)
    eh = time_avail.get("end_hour", 24)
    if sh == 0 and eh == 24:
        return "隨時可接"
    return "%d:00~%d:00" % (sh, eh)

def _try_accept_quest(character, qid):
    q = next((qq for qq in QUESTS if qq["id"]==qid), None)
    if not q:
        return False
    # Check eligibility
    eligible, reason = check_quest_eligibility(character, q)
    if not eligible:
        print(C.RED+"  ⚠ %s"%reason+C.RESET)
        return False
    if accept_quest(character, q):
        print(C.GREEN+"  ✓ 接受了任務: %s"%q["title"]+C.RESET)
        print(C.DIM+"    %s"%q["desc"]+C.RESET)
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════
# QUEST SYSTEM
# ═══════════════════════════════════════════════════════════════════════════

def do_quest_menu(character):
    print("")
    print(C.CYAN+"┌"+"─"*44+"┐"+C.RESET)
    print(C.CYAN+"│  任務系統"+C.RESET+" "*33+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"├"+"─"*44+"┤"+C.RESET)
    print(C.CYAN+"│  1. 查看進行中的任務"+C.RESET+" "*17+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"│  2. 查看可接受的任務"+C.RESET+" "*16+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"│  3. 查看已完成任務"+C.RESET+" "*17+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"│  "+C.GRAY+"0. 返回"+C.RESET+" "*32+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"└"+"─"*44+"┘"+C.RESET)
    ch = input("  %s>%s " % (C.YELLOW,C.RESET)).strip()
    if ch=="1":
        active = get_active_quests(character)
        if not active:
            print(C.GRAY+"  沒有進行中的任務。"+C.RESET)
            return
        for qdef, qdata in active:
            type_color = C.RED if qdef["type"]=="main" else (C.MAGENTA if qdef["type"]=="daily" else C.GREEN)
            print("\n  " + type_color + "[%s] %s: %s" % (qdef["id"],qdef["title"],qdef["desc"]) + C.RESET)
            print("  " + C.DIM + "    給予者: %s" % qdef.get("giver","?") + C.RESET)
            for obj in qdef["objectives"]:
                key = obj["type"]+":"+obj["target"]
                prog = qdata["progress"].get(key,0)
                qty = obj.get("qty",1)
                done = "✓" if prog>=qty else "%d/%d"%(prog,qty)
                ac = C.GREEN if prog>=qty else C.YELLOW
                print("    %s %s [%s]" % (ac, obj.get("detail","?"), done) + C.RESET)
            print("    報酬: %dEXP %dG%s" % (qdef.get("reward_exp",0),qdef.get("reward_gold",0),
                  " +"+qdef.get("reward_item","") if qdef.get("reward_item") else ""))
    elif ch=="2":
        avail = get_available_quests(character)
        if not avail:
            print(C.GRAY+"  目前沒有可接受的任務。"+C.RESET)
            return
        print(C.GREEN+"  ✓ = 可接取   ⚠ = 有條件不符合"+C.RESET)
        for q, reason in avail:
            tc = C.RED if q["type"]=="main" else (C.MAGENTA if q["type"]=="daily" else C.GREEN)
            status = C.GREEN+"✓"+C.RESET if reason is None else C.YELLOW+"⚠"+C.RESET
            print("  %s %s[%s] %s%s" % (status, tc, q["id"], q["title"], C.RESET)+" - "+q.get("giver","?"))
            print("    "+C.DIM+q["desc"][:50]+C.RESET)
            if reason:
                print("    "+C.RED+"  ⚠ "+reason+C.RESET)
            # Show time availability
            ta = q.get("conditions",{}).get("time_available",{})
            if ta:
                print("    "+C.CYAN+"  🕐 "+_time_range_str(ta)+C.RESET)
    elif ch=="3":
        completed = character.get("completed_quests",[])
        if not completed:
            print(C.GRAY+"  尚未完成任何任務。"+C.RESET)
            return
        for cid in completed:
            q = next((qq for qq in QUESTS if qq["id"]==cid), None)
            if q:
                print(f"  {C.GREEN}✓ [{q['id']}] {q['title']}{C.RESET}")

    # Check quest completion after any action
    for qdef, qdata in get_active_quests(character):
        if check_quest_completion(character, qdef["id"]):
            reward = complete_quest(character, qdef["id"])
            if reward:
                print("\n"+C.YELLOW+C.BOLD+"  ⭐ 任務完成: %s!"%qdef["title"]+C.RESET)
                print("    "+C.GREEN+"獲得 %dEXP, %dG"%(reward["exp"],reward["gold"])+C.RESET)
                if reward.get("item"):
                    print("    "+C.CYAN+"獲得物品: %s"%reward["item"]+C.RESET)
                # Apply reputation reward
                rep_r = qdef.get("reward_reputation", 0)
                if rep_r:
                    modify_reputation(character, rep_r)
                # Apply relationship rewards
                rel_r = qdef.get("reward_relationships", {})
                if rel_r:
                    for npc_name, val in rel_r.items():
                        add_relationship(character, npc_name, val)
                        print("    "+C.YELLOW+"🤝 %s 好感度 +%d"%(npc_name,val)+C.RESET)
                # Unlock next quest chain
                nq = qdef.get("next_quest", "")
                if nq:
                    print("    "+C.CYAN+"解鎖下一階段任務!"+C.RESET)


# ═══════════════════════════════════════════════════════════════════════════
# VEHICLE
# ═══════════════════════════════════════════════════════════════════════════

def do_vehicle_menu(character):
    print("\n"+C.CYAN+"┌"+"─"*44+"┐"+C.RESET)
    print(C.CYAN+"│  載具系統"+C.RESET+" "*33+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"├"+"─"*44+"┤"+C.RESET)

    owned = character.get("vehicles",{})
    if not owned or not any(v.get("owned",False) for v in owned.values()):
        print(C.CYAN+"│  "+C.GRAY+"尚未擁有載具。探索世界找到它們!"+C.RESET+" "*6+C.CYAN+"│"+C.RESET)
    else:
        for vname, vstate in owned.items():
            if vstate.get("owned",False):
                vdef = VEHICLES.get(vname,{})
                riding = character.get("riding")==vname
                status = C.GREEN+"騎乘中"+C.RESET if riding else C.GRAY+"待機"+C.RESET
                print(C.CYAN+("│  "+C.YELLOW+vname+C.RESET+" - %s | 速度x%.1f | %s"%(vdef.get("desc",""),vdef.get("speed",1.0),status)).ljust(46)+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"├"+"─"*44+"┤"+C.RESET)
    current = character.get("riding")
    if current:
        print(C.CYAN+"│  目前騎乘: "+C.GREEN+current+C.RESET+" "*24+C.CYAN+"│"+C.RESET)
        print(C.CYAN+"│  2. 下載具"+C.RESET+" "*32+C.CYAN+"│"+C.RESET)
    else:
        print(C.CYAN+"│  目前: 步行"+C.RESET+" "*29+C.CYAN+"│"+C.RESET)
        owned_list = [v for v,vs in owned.items() if vs.get("owned",False)]
        if owned_list:
            print(C.CYAN+"│  2. 騎乘載具"+C.RESET+" "*28+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"│  "+C.GRAY+"0. 返回"+C.RESET+" "*32+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"└"+"─"*44+"┘"+C.RESET)
    ch = input("  %s>%s " % (C.YELLOW,C.RESET)).strip()
    if ch=="2":
        if character.get("riding"):
            dismount_vehicle(character)
            print(C.GRAY+"  下了載具。"+C.RESET)
        else:
            owned_list = [v for v,vs in owned.items() if vs.get("owned",False)]
            if owned_list:
                print(C.CYAN+"  可用載具:"+C.RESET)
                for i, vn in enumerate(owned_list,1):
                    print("    %d. %s"%(i,vn))
                vc = input("  %s選擇:%s "%(C.YELLOW,C.RESET)).strip()
                if vc.isdigit():
                    vi = int(vc)-1
                    if 0<=vi<len(owned_list):
                        vn = owned_list[vi]
                        mount_vehicle(character, vn, owned)
                        print(C.GREEN+"  騎上 %s!"%vn+C.RESET)
            else:
                print(C.GRAY+"  沒有可用載具。"+C.RESET)


# ═══════════════════════════════════════════════════════════════════════════
# REAL ESTATE
# ═══════════════════════════════════════════════════════════════════════════

def do_real_estate(character):
    print("\n"+C.CYAN+"┌"+"─"*44+"┐"+C.RESET)
    print(C.CYAN+"│  不動產系統"+C.RESET+" "*31+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"├"+"─"*44+"┤"+C.RESET)
    owned = character.get("owned_properties", {})
    if owned:
        print(C.CYAN+"│  擁有的不動產:"+C.RESET+" "*25+C.CYAN+"│"+C.RESET)
        for pname, pdata in owned.items():
            pd = REAL_ESTATE.get(pname, {})
            funcs = ", ".join(pd.get("functions",[]))
            print(C.CYAN+"│  "+C.YELLOW+"🏠 %s"%pname+C.RESET+" [%s]"%funcs + " "*(30-len(pname)-len(funcs)) + C.CYAN+"│"+C.RESET)
    else:
        print(C.CYAN+"│  "+C.GRAY+"你還沒有不動產。"+C.RESET+" "*22+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"├"+"─"*44+"┤"+C.RESET)
    print(C.CYAN+"│  1. 查看可購買的不動產"+C.RESET+" "*12+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"│  2. 使用不動產功能"+C.RESET+" "*14+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"│  "+C.GRAY+"0. 返回"+C.RESET+" "*32+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"└"+"─"*44+"┘"+C.RESET)
    ch = input("  %s>%s " % (C.YELLOW,C.RESET)).strip()
    if ch=="1":
        print(C.CYAN+"  可購買:"+C.RESET)
        from sim_systems import REAL_ESTATE_KEYS
        for i, pname in enumerate(REAL_ESTATE_KEYS,1):
            pd = REAL_ESTATE[pname]
            owned_flag = " ✓" if pname in owned else ""
            print("    %d. 🏠 %s — %dG [%s]%s"%(i,pname,pd["price"],",".join(pd["functions"]),owned_flag))
        bc = input("  %s購買編號 (0取消):%s "%(C.YELLOW,C.RESET)).strip()
        if bc.isdigit():
            bi = int(bc)-1
            if 0<=bi<len(REAL_ESTATE_KEYS):
                pname = REAL_ESTATE_KEYS[bi]
                pd = REAL_ESTATE[pname]
                price = pd["price"]
                if pname in owned:
                    print(C.YELLOW+"  你已經擁有這個不動產。"+C.RESET)
                elif character.get("gold",0) >= price and len(owned) < MAX_PROPERTIES:
                    character["gold"] = character.get("gold",0) - price
                    character.setdefault("owned_properties",{})[pname] = {"name":pname,"functions":pd["functions"]}
                    character["owned_properties"][pname]["location"] = character["location"]
                    print(C.GREEN+"  ✓ 購買了 %s!"%pname+C.RESET)
                    modify_reputation(character,5)
                elif len(owned) >= MAX_PROPERTIES:
                    print(C.RED+"  已達不動產上限 (%d)!"%MAX_PROPERTIES+C.RESET)
                else:
                    print(C.RED+"  金幣不足 (需要%dG)!"%price+C.RESET)
    elif ch=="2":
        if not owned:
            print(C.GRAY+"  沒有不動產可用。"+C.RESET)
            return
        print(C.CYAN+"  你的不動產:"+C.RESET)
        for i, pname in enumerate(owned.keys(),1):
            pd = REAL_ESTATE.get(pname, {})
            funcs = pd.get("functions",[])
            print("    %d. 🏠 %s [%s]"%(i,pname,",".join(funcs)))
        pc = input("  %s使用編號:%s "%(C.YELLOW,C.RESET)).strip()
        if pc.isdigit():
            pi = int(pc)-1
            owned_list = list(owned.keys())
            if 0<=pi<len(owned_list):
                pname = owned_list[pi]
                pd = REAL_ESTATE.get(pname, {})
                funcs = pd.get("functions",[])
                print(C.CYAN+"  🏠 %s — 可用功能: %s"%(pname,",".join(funcs))+C.RESET)
                if "rest" in funcs:
                    print(C.GREEN+"    1. 休息 (完全恢復)"+C.RESET)
                if "craft" in funcs:
                    print(C.GREEN+"    2. 使用工作台(合成)"+C.RESET)
                if "store" in funcs:
                    print(C.GREEN+"    3. 倉庫(查看物品)"+C.RESET)
                print(C.GRAY+"    0. 取消"+C.RESET)
                ac = input("  %s>%s "%(C.YELLOW,C.RESET)).strip()
                if ac=="1" and "rest" in funcs:
                    character["hp"] = character["max_hp"]
                    character["sp"] = character["max_sp"]
                    print(C.GREEN+"  ✓ 完全恢復!"+C.RESET)
                    advance_time(character,2)
                elif ac=="2" and "craft" in funcs:
                    do_crafting(character, equipment)
                elif ac=="3" and "store" in funcs:
                    do_inventory(character)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN GAME LOOP
# ═══════════════════════════════════════════════════════════════════════════

def start_game():
    global _current_weather
    # Expand game data from game_data module (card-based content)
    expand_game()
    print("")
    print(C.MAGENTA+C.BOLD+"╔"+"═"*58+"╗"+C.RESET)
    print(C.MAGENTA+C.BOLD+"║"+C.RESET+"  "+C.WHITE+C.BOLD+"CLI 角色扮演模擬 — CLI RPG Simulation"+C.RESET + " "*9 + C.MAGENTA+C.BOLD+"║"+C.RESET)
    print(C.MAGENTA+C.BOLD+"║"+C.RESET+"  "+C.CYAN+"CLI only, symbol portraits, simulation"+C.RESET + " "*12 + C.MAGENTA+C.BOLD+"║"+C.RESET)
    print(C.MAGENTA+C.BOLD+"╚"+"═"*58+"╝"+C.RESET)
    print("")
    print(C.GRAY+"  基於終端機的角色扮演模擬遊戲。"+C.RESET)
    print(C.GRAY+"  使用數字指令，輸入 q 退出。"+C.RESET)
    print("")
    print_help()
    input("  "+C.YELLOW+"按 Enter 開始..."+C.RESET)

    _current_weather = roll_weather()
    character = select_character()
    equipment = EquipmentManager(character)  # Pass character for race-specific slots
    equipment.apply_stat_bonuses(character)

    # Auto-accept main quest MQ-01 (QUESTS is imported at module level)
    mq1 = next((q for q in QUESTS if q["id"]=="MQ-01"), None)
    if mq1:
        accept_quest(character, mq1)
        print(C.GREEN+"\n  自動接受主線任務: 鏡湖的秘密"+C.RESET)
    
    # Auto-save on start
    save_game(character)
    
    # Auto-accept race-specific task
    char_race = character.get("race", "人類")
    race_task_id = {"艦娘":"TASK-01","術士":"TASK-02","竜族":"TASK-03","機械":"TASK-04"}.get(char_race)
    if race_task_id:
        rt = next((q for q in QUESTS if q["id"]==race_task_id), None)
        if rt:
            accept_quest(character, rt)
            print(C.CYAN+"  自動接受種族任務: %s"%rt["title"]+C.RESET)

    last_day_checked = character["day"]
    while True:
        # Reset daily quests each new day
        if character["day"] != last_day_checked:
            reset_daily_quests(character, character["day"])
            # Auto-accept daily quests
            for dq in QUESTS:
                if dq["type"] == "daily" and dq["id"] not in character.get("quests",{}):
                    eligible, reason = check_quest_eligibility(character, dq)
                    if eligible:
                        accept_quest(character, dq)
                        print(C.MAGENTA+"\n  📋 新的一天 — 自動接受每日任務: %s"%dq["title"]+C.RESET)
            last_day_checked = character["day"]
        
        portrait = get_portrait(character)
        print(C.CYAN + portrait + C.RESET)
        print_status(character)
        print_help()
        ch = input("  %s>%s " % (C.YELLOW,C.RESET)).strip().lower()

        if ch in ("q","quit","exit"):
            save = input("  %s存檔後離開? (y/n):%s " % (C.YELLOW,C.RESET)).strip().lower()
            if save == "y":
                save_game(character)
                print(C.GREEN+"  存檔完成!"+C.RESET)
            print(C.GREEN+C.BOLD+"\n遊戲結束。謝謝遊玩!"+C.RESET)
            print(C.GRAY+"  最終: Lv.%d | %d天 | %dG | %d任務完成" % (
                character["level"], character["day"], character.get("gold",0),
                len(character.get("completed_quests",[]))) + C.RESET)
            rels = character.get("relationships",{})
            if rels:
                top = max(rels, key=rels.get)
                print(C.GRAY+"  最佳關係: %s (%d)" % (top, rels[top]) + C.RESET)
            break
        if ch == "s":
            save_game(character)
            print(C.GREEN+"  存檔完成!"+C.RESET)
            continue
        if ch == "l":
            saved = load_game()
            if saved:
                character = saved
                print(C.GREEN+"  讀檔成功!"+C.RESET)
            else:
                print(C.RED+"  沒有存檔。"+C.RESET)
            continue
        if ch=="h": print_help(); continue
        if ch=="1": do_explore(character, equipment)
        elif ch=="2": do_interact_npc(character)
        elif ch=="3": do_travel(character)
        elif ch=="4": do_rest(character)
        elif ch=="5": do_inventory(character)
        elif ch=="6":
            p = get_portrait(character)
            print(C.CYAN+p+C.RESET)
            print(display_character_sheet(character))
        elif ch=="7": print(display_body_parts(character))
        elif ch=="8": do_equipment_menu(character, equipment)
        elif ch=="9": print(display_world_map(character["location"]))
        elif ch=="10": print(display_relationships(character))
        elif ch=="11": do_crafting(character, equipment)
        elif ch=="12": do_scene_search(character, equipment)
        elif ch=="13": do_quest_menu(character)
        elif ch=="14": do_vehicle_menu(character)
        elif ch=="15": do_real_estate(character)
        else: print(C.RED+"  未知指令。輸入 h 查看幫助。"+C.RESET)

        # Auto-check quest completion after any action
        for qdef, qdata in get_active_quests(character):
            if check_quest_completion(character, qdef["id"]):
                reward = complete_quest(character, qdef["id"])
                if reward:
                    print("\n"+C.YELLOW+C.BOLD+"  ⭐ 任務完成: %s!"%qdef["title"]+C.RESET)
                    print("    "+C.GREEN+"獲得 %dEXP, %dG"%(reward["exp"],reward["gold"])+C.RESET)
                    if reward.get("item"):
                        print("    "+C.CYAN+"獲得物品: %s"%reward["item"]+C.RESET)
                    # Apply reputation reward
                    rep_r = qdef.get("reward_reputation", 0)
                    if rep_r:
                        modify_reputation(character, rep_r)
                        print("    "+C.MAGENTA+"聲望 +%d"%rep_r+C.RESET)
                    # Apply relationship rewards
                    rel_r = qdef.get("reward_relationships", {})
                    if rel_r:
                        for npc_name, val in rel_r.items():
                            add_relationship(character, npc_name, val)
                            print("    "+C.YELLOW+"🤝 %s 好感度 +%d"%(npc_name,val)+C.RESET)
                    # Unlock next quest chain
                    nq = qdef.get("next_quest", "")
                    if nq:
                        print("    "+C.CYAN+"解鎖下一階段任務!"+C.RESET)

if __name__ == "__main__":
    start_game()
