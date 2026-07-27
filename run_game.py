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
    ENEMIES,
    LOCATION_ENEMIES,
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
    upgrade_property,
    get_property_upgrade_cost,
    LOCATION_TYPES,
    SCENE_TYPE_ICONS,
    SCENE_TYPE_NAMES,
    ENTRY_REQUIREMENTS,
    check_entry_requirement,
    get_entry_requirement_hint,
    MECHANISM_TYPES,
    EFFECT_TYPES,
    resolve_mechanism_effect,
    check_mechanism_requirements,
    consume_mechanism_requirements,
    get_season,
    SEASON_ICONS,
    SEASONS,
    SEASON_NAMES,
    get_season_crop_bonus,
    get_season_weather_desc,
    VEHICLE_PART_CATALOG,
    VEHICLE_PART_SLOTS,
    equip_vehicle_part,
    unequip_vehicle_part,
    get_vehicle_part_bonuses,
    get_vehicle_part_status,
    apply_vehicle_part_bonuses,
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
_current_season = "春"
_current_weather = "☀晴"


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════


def clear_screen():
    """Clear terminal screen per INTERFACE_TERMINAL.md§清屏"""
    os.system("cls" if os.name == "nt" else "clear")


def _get_time_period(hour):
    """Get time period label for dynamic narration."""
    if 6 <= hour < 11: return "早晨"
    if 11 <= hour < 13: return "正午"
    if 13 <= hour < 17: return "午後"
    if 17 <= hour < 21: return "傍晚"
    return "夜晚"

def _gm_narrate(character, new_location=None):
    """GM-style scene narration per GAME_OVERVIEW.md GM system.
    Shows only content NOT duplicated by print_status():
    location prose, player state, and relevant quest hints.
    """
    loc = new_location or character.get("location","?")
    hour = character.get("hour", 8)
    period = _get_time_period(hour)
    global _current_weather, _current_season
    cur_season = _current_season
    weather_today = _current_weather or "☀晴"

    # ── Weather-time feeling (short, unique) ──
    weather_feel = {
        "☀晴": { "早晨":"和煦的晨光", "正午":"烈日當空", "午後":"溫暖的陽光", "傍晚":"夕陽餘暉", "夜晚":"清冷的月光" },
        "⛅多雲": { "早晨":"天光微亮", "正午":"雲遮烈日", "午後":"天色陰沉", "傍晚":"灰暗的雲霞", "夜晚":"雲遮星光" },
        "🌧雨": { "早晨":"細雨綿綿", "正午":"雨勢不小", "午後":"雨水滴答", "傍晚":"雨中的暮色", "夜晚":"夜雨瀟瀟" },
        "🌫霧": { "早晨":"晨霧濃重", "正午":"迷霧籠罩", "午後":"霧氣繚繞", "傍晚":"暮靄沉沉", "夜晚":"夜霧瀰漫" },
        "🌩雷雨": { "早晨":"雷聲隱隱", "正午":"暴雨傾盆", "午後":"雷雨交加", "傍晚":"風雨暮色", "夜晚":"雷雨之夜" },
        "❄雪": { "早晨":"白雪覆蓋", "正午":"雪花飄落", "午後":"銀白世界", "傍晚":"雪映餘暉", "夜晚":"雪夜寒星" },
    }
    wf = weather_feel.get(weather_today, {}).get(period, "")
    if wf:
        wf = "（" + wf + "）"

    # ── Location prose (time-specific) ──
    gm_descs = {
        "方碑丘": {
            "早晨": "晨霧中的稻田閃爍著露珠，村莊從睡夢中醒來，雞鳴聲此起彼落。",
            "正午": "村莊廣場上熱鬧了起來，農民們在樹蔭下休息，分享著午餐。",
            "午後": "慵懶的午後，風吹過稻田，掀起金色的波浪。幾隻狗趴在路邊打盹。",
            "傍晚": "炊煙裊裊升起，村民們結束了一天的勞作，笑語聲從各家各戶傳來。",
            "夜晚": "村莊沉浸在夜色中，只有幾盞燈火在窗後搖曳。蟲鳴聲在田野間迴盪。",
        },
        "鏡湖": {
            "早晨": "湖面平靜如鏡，倒映著晨光中的雲彩。水氣在湖面上形成一層薄霧。",
            "正午": "陽光直射湖面，水波粼粼，像是撒了一把碎金。偶爾有魚躍出水面。",
            "午後": "湖面波光瀲灩，岸邊的蘆葦隨風搖曳。空氣中帶著淡淡的水草香氣。",
            "傍晚": "夕陽將湖面染成一片金紅，天色與水色交融，美不勝收。",
            "夜晚": "月光灑在湖面上，銀白色的光芒在水中搖曳。四周一片寂靜。",
        },
        "西翼大市集": {
            "早晨": "攤販們忙著擺設商品，市集漸漸甦醒。新鮮蔬果的香氣在空氣中飄散。",
            "正午": "市集達到高峰，人聲鼎沸。各種叫賣聲、討價還價聲交織成熱鬧的樂章。",
            "午後": "人潮稍退，但仍有不少顧客在各個攤位前流連。烤肉和香料的香氣交織。",
            "傍晚": "攤販們開始收拾，市集即將打烊。最後幾筆交易在暮色中完成。",
            "夜晚": "市集的燈火逐一熄滅，只剩下幾盞照明燈在空蕩的街道上投下光影。",
        },
        "中央大圖書館": {
            "早晨": "晨光透過彩繪玻璃窗，在書架間投下斑斕的光影。空氣中飄散著紙張和墨水香。",
            "正午": "圖書館內光線明亮，陽光從高處的天窗灑落。讀書人的翻頁聲輕輕迴盪。",
            "午後": "午後的圖書館格外寧靜，只有筆尖在紙上摩擦的沙沙聲。塵埃在光柱中飛舞。",
            "傍晚": "暮色中的圖書館籠罩在一片溫暖的昏暗中，管理員開始點燃油燈。",
            "夜晚": "月光從窗戶透入，書架在黑暗中投下長長的影子。圖書館幽深而神秘。",
        },
        "海峽": {
            "早晨": "晨風強勁，海面上波光粼粼。海鷗在礁石上棲息，時而振翅飛起。",
            "正午": "陽光下的海面一片湛藍，浪花拍打著岩岸，濺起白色的泡沫。",
            "午後": "海風帶著鹹味，潮汐漸漸退去，露出潮間帶的岩石和貝殼。",
            "傍晚": "夕陽沈入海平面，將天空和海面染成一片絢麗的橘紅。美景令人屏息。",
            "夜晚": "海浪聲在夜色中格外清晰。海面上倒映著月光，像是碎銀鋪成的路。",
        },
        "秘密鐵工廠": {
            "早晨": "鐵工廠一早便響起金屬撞擊聲。爐火映紅了工人的臉龐。",
            "正午": "爐火熊熊燃燒，鐵水在高溫下發出耀眼的光芒。鎚聲不絕於耳。",
            "午後": "師傅們專注地打磨著作品，火花在昏暗的空間中四濺。蒸氣嘶嘶作響。",
            "傍晚": "工作接近尾聲，鐵鎚聲漸漸稀疏。爐火的餘燼在暮色中閃著微光。",
            "夜晚": "工廠陷入寂靜，尚未完全冷卻的鐵器在黑暗中散發著淡淡的紅光。",
        },
        "便利店": {
            "早晨": "玻璃門上的『營業中』牌子已經翻轉，店員正在整理貨架上的商品。",
            "正午": "午休時間，店裡來了幾位客人，正在挑選便當和飲料。",
            "午後": "店內播放著輕柔的音樂，陽光透過玻璃門照進來，在地板上形成長長的影子。",
            "傍晚": "夕陽斜照，便利店的燈光亮起，在暮色中顯得格外溫暖明亮。",
            "夜晚": "便利店的燈光在夜色中像是一座燈塔，照亮了門前的街道。",
        },
        "英靈殿": {
            "早晨": "穿過厚重的石門，晨光投射在大殿的地面上。牆上的武器閃爍著冷光。",
            "正午": "高窗射入的光線照亮了壁畫上英雄們的容顏。大殿中央瀰漫著莊嚴的氣息。",
            "午後": "光線移動，壁畫在不同的光影下呈現不同的面貌。腳步聲在石板上迴盪。",
            "傍晚": "暮色中的大殿顯得格外肅穆。褪色的旗幟在微風中輕輕飄動。",
            "夜晚": "月光透過高窗灑落，將大理石地板照得發白。大殿在夜色中顯得神秘莫測。",
        },
        "廢棄礦坑": {
            "早晨": "礦坑入口處的雜草掛滿了露珠。從黑暗中傳出滴水的迴音。",
            "正午": "洞口的光線勉強照亮了前幾公尺的空間。更深處是一片絕對的黑暗。",
            "午後": "潮濕的空氣從礦坑深處湧出，帶著鐵鏽和泥土的氣味。",
            "傍晚": "暮色讓礦坑的入口顯得更為陰森。蝙蝠在洞口盤旋。",
            "夜晚": "月光勾勒出礦坑入口的輪廓。黑暗中似乎有什麼在注視著外面。",
        },
        "森林深處": {
            "早晨": "晨光穿過層層樹葉，在林間形成一道道光束。鳥鳴聲此起彼落。",
            "正午": "高大的樹冠遮蔽了大部分陽光，林間格外清涼。偶爾有松鼠跳過。",
            "午後": "午後的森林充滿了生機：蝴蝶在花叢間飛舞，啄木鳥在遠處敲打著樹幹。",
            "傍晚": "暮色中的森林漸漸安靜下來，夜行性動物開始甦醒。貓頭鷹的叫聲從遠處傳來。",
            "夜晚": "森林陷入黑暗，只有月光勉強照亮小徑。螢火蟲在草叢間閃爍著微光。",
        },
    }

    # Print location prose
    stype = LOCATION_TYPES.get(loc, "outdoor")
    sicon = SCENE_TYPE_ICONS.get(stype, "🌄")
    stname = SCENE_TYPE_NAMES.get(stype, "?")
    desc_vibe = LOCATION_VIBES.get(loc, "")
    loc_descs = gm_descs.get(loc, {})
    desc = loc_descs.get(period, "")
    season_tag = SEASON_ICONS.get(cur_season,"") + " " + SEASON_NAMES.get(cur_season, cur_season)
    if desc:
        print(C.DIM + sicon + f" {wf} {desc}" + C.RESET)
        print(C.DIM + "  [%s] %s [%s]" % (stname, desc_vibe, season_tag) + C.RESET)
    elif desc_vibe:
        print(C.DIM + sicon + f" {wf} {desc_vibe}" + C.RESET)
        print(C.DIM + "  %s" % season_tag + C.RESET)

    # ── Player state notes (short) ──
    state_notes = []
    hp_r = character["hp"] / character["max_hp"] if character["max_hp"] > 0 else 1.0
    if hp_r < 0.3:
        state_notes.append("重傷")
    elif hp_r < 0.6:
        state_notes.append("帶傷")
    if character.get("fatigue", 0) > 80:
        state_notes.append("極度疲勞")
    elif character.get("fatigue", 0) > 50:
        state_notes.append("有些疲倦")
    if character.get("pain", 0) > 60:
        state_notes.append("傷口疼痛")
    if character.get("bleed_rate", 0) > 0:
        state_notes.append(f"出血({character.get('bleed_rate',0)})")
    if character.get("riding"):
        vname = character["riding"]
        v = VEHICLES.get(vname, {})
        vs = character.get("vehicles", {}).get(vname, {})
        fuel_pct = int(vs.get("fuel", v.get("fuel", 100)) / max(v.get("fuel", 100), 1) * 100)
        state_notes.append(f"騎乘{vname}(燃料:{fuel_pct}%)")
    if state_notes:
        print(C.YELLOW + "  [" + " | ".join(state_notes) + "]" + C.RESET)

    # ── Quest hints (only for relevant items at this location) ──
    active_qs = get_active_quests(character)
    for qdef, qdata in active_qs:
        for obj in qdef.get("objectives", []):
            # Visit objective: direct location match
            if obj.get("type") == "visit" and obj.get("target") == loc:
                print(C.YELLOW + f"  ⚑ 你記得你的任務：{qdef['title']}" + C.RESET)
                break
            # Collect objective: check if item is findable at this location
            if obj.get("type") == "collect":
                target = obj.get("target", "")
                # Check scene objects
                scene_objs = SCENE_OBJECTS.get(loc, [])
                obj_item_found = False
                for sobj in scene_objs:
                    if target in sobj.get("contents", []):
                        obj_item_found = True
                        break
                # Check enemy loot at this location
                if not obj_item_found:
                    enemy_names = LOCATION_ENEMIES.get(loc, [])
                    for en in ENEMIES:
                        if en["name"] in enemy_names and target in en.get("loot", []):
                            obj_item_found = True
                            break
                # Also check alt_item
                alt = obj.get("alt_item", "")
                if alt and not obj_item_found:
                    for sobj in scene_objs:
                        if alt in sobj.get("contents", []):
                            obj_item_found = True
                            break
                if obj_item_found:
                    print(C.YELLOW + f"  ⚑ {obj.get('detail','此處可能有任務材料')}" + C.RESET)
                    break
def advance_time(character, hours=1):
    global _current_weather, _current_season
    character["hour"] = (character["hour"] + hours) % 24
    if character["hour"] == 0:
        character["day"] += 1
        old_season = _current_season
        _current_season = get_season(character["day"])
        _current_weather = roll_weather(_current_season)
        if _current_season != old_season:
            from sim_systems import SEASON_ICONS as _sic, SEASON_NAMES as _snm
            print(_sic.get(_current_season,"") + C.CYAN + "  ★ 季節更替: " + _snm.get(_current_season, _current_season) + " 來了！" + C.RESET)

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
    global _current_weather, _current_season
    print("")
    time_str = get_time_desc(character["hour"], character["day"])
    weather_info = _current_weather + " " + get_season_weather_desc(_current_weather, _current_season)
    print(C.DIM + "─"*50 + C.RESET)
    print(C.CYAN + "  ◈ " + time_str + C.RESET + "  " + weather_info)
    race = character.get("race", "人類")
    loc = character["location"]
    stype = LOCATION_TYPES.get(loc, "outdoor")
    sicon = SCENE_TYPE_ICONS.get(stype, "🌄")
    stname = SCENE_TYPE_NAMES.get(stype, "?")
    print(C.WHITE + "  " + sicon + " 位置: " + loc + C.RESET + "  " + C.MAGENTA + "[ " + race + " ]" + C.RESET + C.DIM + " (%s)" % stname + C.RESET, end="")
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

    # Season info
    print(C.DIM + "  季節: " + SEASON_ICONS.get(_current_season,"🌸") + " " + SEASON_NAMES.get(_current_season,_current_season))
    # Scene type info
    stype = LOCATION_TYPES.get(character["location"], "outdoor")
    sicon = SCENE_TYPE_ICONS.get(stype, "🌄")
    stname = SCENE_TYPE_NAMES.get(stype, "?")
    print(C.DIM + "  類型: " + sicon + " " + stname)
    # All NPCs — show those at current location + some high-rep ones
    print(C.DIM + "─"*50 + C.RESET)
    cur_loc = character["location"]
    npcs_here = []
    all_sched = NPC_SCHEDULES
    for npc_name in list(all_sched.keys()):
        act, aloc, mood = get_npc_activity(npc_name, character["hour"], _current_season)
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
    global _current_weather, _current_season
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
    icons = {"east":"→","west":"←","north":"↑","south":"↓","enter":"🚪","exit":"🚶","deep":"⬇"}
    for i,(d,loc) in enumerate(dests.items(),1):
        ic = icons.get(d,"•")
        vibe = LOCATION_VIBES.get(loc,"")
        stype = LOCATION_TYPES.get(loc, "outdoor")
        sicon = SCENE_TYPE_ICONS.get(stype, "🌄")
        req_hint = get_entry_requirement_hint(loc)
        req_color = C.RED if req_hint else C.GREEN
        print("    %d. %s %s %s  %s%s%s"%(i,ic,sicon,loc,vibe,req_color,req_hint,C.RESET))
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
                    # Apply part bonuses to vehicle stats
                    veh_state = character.get("vehicles", {}).get(character["riding"], {})
                    parts_data = {}
                    for sid, pname in veh_state.get("parts",{}).items():
                        parts_data[sid] = VEHICLE_PART_CATALOG.get(pname, {})
                    mod_v = apply_vehicle_part_bonuses(v, parts_data)
                    hours = max(1, int(1 / mod_v.get("speed",1.0)))
                    # Vehicle fuel consumption
                    fuel_used = mod_v.get("fuel_per_hour", v.get("fuel_per_hour", 0)) * hours
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
                    # Vehicle part durability decay during travel
                    if character.get("riding"):
                        veh_state = character.get("vehicles", {}).get(character["riding"], {})
                        parts_durability = veh_state.get("parts_durability", {})
                        decayed = False
                        for sid in list(parts_durability.keys()):
                            old_dur = parts_durability[sid]
                            new_dur = max(0, old_dur - _random.randint(1, 2))
                            parts_durability[sid] = new_dur
                            if old_dur > 0 and new_dur == 0:
                                part_name = veh_state.get("parts", {}).get(sid, "")
                                print(C.RED+"    ⚡ [%s] %s 損壞了!" % (sid, part_name) + C.RESET)
                                decayed = True
                                # Remove broken part, return to inventory
                                character["inventory"].append(part_name)
                                del veh_state["parts"][sid]
                                if sid in parts_durability:
                                    del parts_durability[sid]
                            else:
                                decayed = True
                        if decayed:
                            veh_state["parts_durability"] = parts_durability
            # Check entry requirements
            can_enter, fail_msg = check_entry_requirement(dest, character)
            if not can_enter:
                print(C.RED + "  🔒 " + (fail_msg or "無法進入。") + C.RESET)
                return
            character["location"] = dest
            advance_time(character, hours)
            # Arrival announcement
            vibe = LOCATION_VIBES.get(dest,"")
            print(C.GREEN + "  ⇨ 到達%s。%s" % (dest, vibe) + C.RESET)
            # GM narration on arrival
            _gm_narrate(character, dest)
            # Random event on travel
            roll_random_event(character)
            return
    print(C.RED+"  無效。"+C.RESET)


# ═══════════════════════════════════════════════════════════════════════════
# REST
# ═══════════════════════════════════════════════════════════════════════════

def do_rest(character):
    global _current_weather, _current_season
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
        # Mechanism-specific icons
        if obj["type"] == "mechanism":
            mtype = obj.get("mechanism_type", "")
            ic = MECHANISM_TYPES.get(mtype, {}).get("icon", "⚙")
        locked = " 🔒" if obj.get("locked") else ""
        triggered_flag = " ✅" if obj.get("triggered") else " 🔄"
        mech_flag = triggered_flag if obj["type"] == "mechanism" else ""
        print("    %d. %s %s%s%s" % (i, ic, obj["name"], locked, mech_flag))
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
                        veh_state[vt] = {"owned": True, "location": loc, "fuel": init_fuel, "parts": {}, "parts_durability": {}}
                        character["vehicles"] = veh_state
                        print(C.GREEN+"  你獲得了 %s! (燃料:%d)"%(vt,init_fuel)+C.RESET)
                    mount_vehicle(character, vt, veh_state)
                    print(C.GREEN+"  騎上了 %s!"%vt+C.RESET)

    elif obj_type == "mechanism":
        mech_type = obj.get("mechanism_type","?")
        mech_info = MECHANISM_TYPES.get(mech_type, {})

        # Already triggered / one-time?
        if obj.get("triggered") and obj.get("trigger_once"):
            repeat_msg = obj.get("on_repeat", "這個機關已經被觸發過了。")
            print(C.GRAY+"  " + repeat_msg + C.RESET)
            advance_time(character)
            return

        # Show mechanism info
        print(C.YELLOW+"  ⚙ 機關類型: %s %s" % (mech_info.get("icon","⚙"), mech_info.get("name",mech_type))+C.RESET)
        reqs = obj.get("requirements", {})
        if reqs:
            req_msg = obj.get("requirements_msg", "需要特定條件才能觸發。")
            print(C.MAGENTA+"  ! " + req_msg + C.RESET)

        # Show charges-based progress
        charges = obj.get("charges", 0)
        max_ch = obj.get("max_charges", 0)
        if max_ch > 0:
            progress = obj.get("progress_msg", "")
            if progress:
                print(C.CYAN+"  " + (progress % obj.get("charges", 0)) + C.RESET)

        # Check requirements
        can_activate, req_fail_msg = check_mechanism_requirements(obj, character)
        if not can_activate:
            fail_msg = obj.get("failure_msg", req_fail_msg or "條件不足，無法啟動。")
            print(C.RED+"  ✗ " + fail_msg + C.RESET)
            advance_time(character)
            return

        # Activation prompt
        print(C.GREEN+"  1. 啟動機關"+C.RESET)
        print(C.GRAY+"  0. 取消"+C.RESET)
        mc = input("  %s>%s " % (C.YELLOW,C.RESET)).strip()
        if mc != "1":
            return

        # Consume requirements
        consume_mechanism_requirements(obj, character)

        # Resolve effect
        success, msg, side = resolve_mechanism_effect(obj, character, loc)
        if success:
            print(C.CYAN+"  " + msg + C.RESET)
        else:
            print(C.RED+"  " + msg + C.RESET)

        # Mark triggered
        if obj.get("trigger_once"):
            obj["triggered"] = True
        elif max_ch > 0:
            # Gear mechanism: increment charges
            obj["charges"] = obj.get("charges", 0) + 1
            if obj["charges"] >= max_ch:
                obj["triggered"] = True
            else:
                # Show progress
                progress = obj.get("progress_msg", "")
                if progress:
                    print(C.CYAN+"  " + (progress % obj["charges"]) + C.RESET)

        # Handle side effects
        s_teleport = side.get("teleport_to")
        if s_teleport:
            character["location"] = s_teleport
            print(C.GREEN+"  🌀 你被傳送到了 %s！" % s_teleport + C.RESET)
            _gm_narrate(character, s_teleport)

        s_enemy = side.get("enemy_spawn")
        if s_enemy:
            print(C.RED+"  👻 %s 出現了！" % s_enemy + C.RESET)
            # Find enemy definition
            for e in ENEMIES:
                if e["name"] == s_enemy:
                    do_combat(character, e)
                    break

        s_route = side.get("route_add")
        if s_route:
            direction, target_loc = s_route
            # Add route to WORLD_MAP for the relevant location
            if target_loc in WORLD_MAP:
                if direction not in WORLD_MAP[target_loc]:
                    WORLD_MAP[target_loc][direction] = loc
                if target_loc not in WORLD_MAP.get(loc, {}):
                    # Also add reverse route
                    rev_dirs = {"東":"西","西":"東","南":"北","北":"南","深處":"入口","入口":"深處"}
                    rev_dir = rev_dirs.get(direction, direction)
                    if loc not in WORLD_MAP.get(target_loc, {}):
                        WORLD_MAP.setdefault(target_loc, {})[rev_dir] = loc
                print(C.GREEN+"  🛤 新的道路被打開了！%s → %s" % (direction, target_loc) + C.RESET)

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
        act, aloc, mood = get_npc_activity(npc_name, character["hour"], _current_season)
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

def do_real_estate(character, equipment=None):
    print("\n"+C.CYAN+"┌"+"─"*44+"┐"+C.RESET)
    print(C.CYAN+"│  不動產系統 (升級系統已開放)"+C.RESET+" "*16+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"├"+"─"*44+"┤"+C.RESET)
    owned = character.get("owned_properties", {})
    if owned:
        print(C.CYAN+"│  擁有的不動產:"+C.RESET+" "*25+C.CYAN+"│"+C.RESET)
        for pname, pdata in owned.items():
            pd = REAL_ESTATE.get(pname, {})
            lv = pdata.get("level", 1)
            mlv = pd.get("max_level", 1)
            funcs = ", ".join(pdata.get("functions", pd.get("functions",[])))
            lv_str = "Lv.%d/%d" % (lv, mlv)
            print(C.CYAN+"│  "+C.YELLOW+"🏠 %s"%pname+C.RESET+" [%s] %s"%(funcs, lv_str) + " "*(28-len(pname)-len(funcs)-len(lv_str)) + C.CYAN+"│"+C.RESET)
    else:
        print(C.CYAN+"│  "+C.GRAY+"你還沒有不動產。"+C.RESET+" "*22+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"├"+"─"*44+"┤"+C.RESET)
    print(C.CYAN+"│  1. 查看/購買可購買的不動產"+C.RESET+" "*6+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"│  2. 使用不動產功能"+C.RESET+" "*14+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"│  3. 升級不動產"+C.RESET+" "*18+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"│  "+C.GRAY+"0. 返回"+C.RESET+" "*32+C.CYAN+"│"+C.RESET)
    print(C.CYAN+"└"+"─"*44+"┘"+C.RESET)
    ch = input("  %s>%s " % (C.YELLOW,C.RESET)).strip()
    if ch=="1":
        print(C.CYAN+"  可購買:"+C.RESET)
        for i,pname in enumerate(REAL_ESTATE_KEYS,1):
            pd = REAL_ESTATE[pname]
            owned_flag = " ✓" if pname in owned else ""
            ptype = pd.get("type","?")
            mlv = pd.get("max_level", 1)
            type_icons = {"house":"🏠","shop":"🏪","workshop":"🔧","warehouse":"📦","farm":"🌾","tower":"🗼"}
            ic = type_icons.get(ptype,"🏠")
            print("    %d. %s %s — %dG [%s] Lv.%d%s"%(i,ic,pname,pd["price"],",".join(pd["functions"]),mlv,owned_flag))
            print("       "+C.DIM+"%s"%pd.get("desc","")+C.RESET)
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
                    character.setdefault("owned_properties",{})[pname] = {"name":pname,"functions":list(pd["functions"]),"level":1}
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
        olist = list(owned.keys())
        for i, pname in enumerate(olist,1):
            pd = REAL_ESTATE.get(pname, {})
            funcs = ", ".join(owned[pname].get("functions", pd.get("functions",[])))
            lv = owned[pname].get("level", 1)
            print("    %d. 🏠 %s [%s] Lv.%d"%(i,pname,funcs,lv))
        pc = input("  %s使用編號:%s "%(C.YELLOW,C.RESET)).strip()
        if pc.isdigit():
            pi = int(pc)-1
            if 0<=pi<len(olist):
                pname = olist[pi]
                pd = REAL_ESTATE.get(pname, {})
                funcs = owned[pname].get("functions", pd.get("functions",[]))
                lv = owned[pname].get("level", 1)
                print(C.CYAN+"  🏠 %s — Lv.%d 功能: %s"%(pname,lv,", ".join(funcs))+C.RESET)
                if "rest" in funcs:
                    print(C.GREEN+"    1. 休息 (完全恢復)"+C.RESET)
                if "craft" in funcs:
                    print(C.GREEN+"    2. 使用工作台(合成)"+C.RESET)
                if "store" in funcs:
                    print(C.GREEN+"    3. 倉庫(查看物品)"+C.RESET)
                if "study" in funcs:
                    print(C.GREEN+"    4. 研究 (SP消耗→技能經驗)"+C.RESET)
                if "farm" in funcs:
                    print(C.GREEN+"    5. 農場 (收穫作物)"+C.RESET)
                if "observe" in funcs:
                    print(C.GREEN+"    6. 觀測 (探索情報)"+C.RESET)
                if "trade" in funcs:
                    print(C.GREEN+"    7. 交易 (買賣物品)"+C.RESET)
                if "guest" in funcs:
                    print(C.GREEN+"    8. 招待客人 (好感度提升)"+C.RESET)
                print(C.GRAY+"    0. 取消"+C.RESET)
                ac = input("  %s>%s "%(C.YELLOW,C.RESET)).strip()
                if ac=="1" and "rest" in funcs:
                    character["hp"] = character["max_hp"]
                    character["sp"] = character["max_sp"]
                    character["fatigue"] = 0
                    character["pain"] = 0
                    print(C.GREEN+"  ✓ 完全恢復! 疲勞和痛覺已消除。"+C.RESET)
                    advance_time(character,2)
                elif ac=="2" and "craft" in funcs:
                    do_crafting(character, equipment)
                elif ac=="3" and "store" in funcs:
                    do_inventory(character)
                elif ac=="4" and "study" in funcs:
                    if character["sp"] >= 15:
                        character["sp"] -= 15
                        gain_skill_exp(character, "knowledge", 10)
                        gain_exp_with_skills(character, 20, "knowledge", 15)
                        print(C.GREEN+"  研究完畢! 知識技能經驗提升。"+C.RESET+" (SP-15)")
                        advance_time(character,1)
                    else:
                        print(C.RED+"  SP不足 (需要15)!"+C.RESET)
                elif ac=="5" and "farm" in funcs:
                    crops = ["草藥","乾糧","靈木","生命果"]
                    roll = _random.random()
                    if roll < 0.4:
                        harvest = "草藥"
                        qty = _random.randint(2,5)
                    elif roll < 0.7:
                        harvest = "乾糧"
                        qty = _random.randint(3,6)
                    elif roll < 0.9:
                        harvest = "靈木"
                        qty = _random.randint(1,3)
                    else:
                        harvest = "生命果"
                        qty = 1
                    # Apply season crop bonus
                    season_bonus = get_season_crop_bonus(_current_season, harvest)
                    qty = max(1, int(qty * season_bonus))
                    for _ in range(qty):
                        character["inventory"].append(harvest)
                    print(C.GREEN+"  🌾 收穫了 %s x%d!"%(harvest,qty)+C.RESET)
                    advance_time(character,1)
                elif ac=="6" and "observe" in funcs:
                    gain_exp_with_skills(character, 15, "exploration", 5)
                    print(C.CYAN+"  你觀察到遠方有什麼在發光..."+C.RESET)
                    print(C.DIM+"  (探索技能經驗提升)"+C.RESET)
                    advance_time(character,1)
                elif ac=="7" and "trade" in funcs:
                    do_inventory(character)
                    print(C.GRAY+"  (交易功能: 可在商店購買/出售)"+C.RESET)
                elif ac=="8" and "guest" in funcs:
                    modify_reputation(character, 5)
                    print(C.GREEN+"  你招待了客人，聲望 +5!"+C.RESET)
                    advance_time(character,1)

    elif ch=="3":
        if not owned:
            print(C.GRAY+"  沒有不動產可升級。"+C.RESET)
            return
        print(C.CYAN+"  可升級的不動產:"+C.RESET)
        olist = list(owned.keys())
        upg_available = []
        for i, pname in enumerate(olist,1):
            pd = REAL_ESTATE.get(pname, {})
            lv = owned[pname].get("level", 1)
            mlv = pd.get("max_level", 1)
            cost_info = get_property_upgrade_cost(character, pname)
            cost_str = ""
            if cost_info:
                cost_g, cost_desc, add_funcs = cost_info
                cost_str = C.GREEN+" → Lv.%d: %dG (%s)"%(lv+1, cost_g, cost_desc)+C.RESET
                upg_available.append(i)
            else:
                cost_str = C.GRAY+" (已達最高等級)"+C.RESET
            print("    %d. 🏠 %s [Lv.%d/%d] %s"%(i,pname,lv,mlv,cost_str))
        if not upg_available:
            print(C.GRAY+"  所有不動產已達最高等級。"+C.RESET)
            return
        uc = input("  %s升級編號 (0取消):%s "%(C.YELLOW,C.RESET)).strip()
        if uc.isdigit():
            ui = int(uc)-1
            if 0<=ui<len(olist):
                pname = olist[ui]
                if ui+1 not in upg_available:
                    print(C.RED+"  該不動產已達最高等級。"+C.RESET)
                    return
                succ, msg = upgrade_property(character, pname)
                if succ:
                    print(C.GREEN+"  ✓ "+msg+C.RESET)
                    gain_skill_exp(character, "craft", 5)
                else:
                    print(C.RED+"  ✗ "+msg+C.RESET)
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
        elif ch=="15": do_real_estate(character, equipment)
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
