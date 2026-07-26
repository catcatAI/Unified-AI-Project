"""Launch the CLI RPG simulation game."""
import sys
import random as _random
from pathlib import Path

src = Path(__file__).resolve().parent / "apps" / "backend" / "src"
sys.path.insert(0, str(src))

from sim_systems import (
    EquipmentManager,
    craft_item,
    get_npc_activity,
    get_time_desc,
    display_world_map,
    REAL_ESTATE,
    WORLD_MAP,
    RECIPES,
    NPC_SCHEDULES,
    EQUIPMENT_SLOTS,
)


def advance_time(character, hours=1):
    character["hour"] = (character["hour"] + hours) % 24
    if character["hour"] == 0:
        character["day"] += 1


def show_help():
    print("")
    print("  可用指令:")
    print("    1. 探索周圍")
    print("    2. 與NPC對話")
    print("    3. 前往其他場景")
    print("    4. 休息 (恢復HP/SP)")
    print("    5. 查看物品欄")
    print("    6. 查看/裝備物品")
    print("    7. 查看地圖")
    print("    8. 合成物品")
    print("    h. 顯示幫助")
    print("    q/quit. 退出遊戲")
    print("")


def init_character():
    return {
        "name": "旅人",
        "hp": 100,
        "max_hp": 100,
        "sp": 50,
        "max_sp": 50,
        "atk": 10,
        "def": 5,
        "exp": 0,
        "gold": 50,
        "location": "方碑丘",
        "day": 1,
        "hour": 8,
        "inventory": ["草藥", "木柄"],
    }


def apply_equipment_bonuses(character, equipment):
    bonuses = equipment.get_stat_bonuses()
    character["atk"] = 10 + int(bonuses.get("atk", 0) * 10)
    character["def"] = 5 + int(bonuses.get("def", 0) * 10)


def do_explore(character):
    print("  你仔細探索了周圍的環境...")
    find = _random.choice(["草藥", "木柄", "火元素", "鐵礦", None, None])
    if find:
        character["inventory"].append(find)
        print("  你發現了: %s!" % find)
    else:
        print("  什麼特别的東西都沒找到。")


def do_travel(character):
    destinations = WORLD_MAP.get(character["location"], {})
    if not destinations:
        print("  這裡沒有已知的通路。")
        return
    print("  可以去的地方:")
    for i, (direction, dest) in enumerate(destinations.items(), 1):
        print("    %d. %s -> %s" % (i, direction, dest))
    print("    0. 取消")
    choice = input("  選擇: ").strip()
    if not choice.isdigit():
        print("  無效的選擇。")
        return
    idx = int(choice)
    if idx == 0:
        print("  取消移動。")
        return
    if 1 <= idx <= len(destinations):
        dest = list(destinations.values())[idx - 1]
        character["location"] = dest
        advance_time(character)
        print("  移動到 %s。" % dest)
        return
    print("  無效的選擇。")


def do_rest(character):
    heal = min(character["max_hp"] - character["hp"], 30)
    sp_heal = min(character["max_sp"] - character["sp"], 20)
    character["hp"] += heal
    character["sp"] += sp_heal
    print("  你休息了，恢復了 %dHP 和 %dSP。" % (heal, sp_heal))
    advance_time(character, 2)


def do_inventory(character):
    inv = character["inventory"]
    print("")
    print("  物品欄 (%d):" % len(inv))
    for i, item in enumerate(inv, 1):
        print("    %d. %s" % (i, item))
    if not inv:
        print("    （物品欄為空）")
    print("  金幣: %d" % character.get("gold", 0))


def do_equipment_menu(character, equipment):
    print("")
    print("  1. 查看裝備欄")
    print("  2. 裝備物品")
    print("  3. 卸下裝備")
    print("  0. 返回")
    choice = input("  > ").strip()
    if choice == "1":
        print(equipment.display())
        return
    if choice == "2":
        print("  物品欄:")
        for i, item in enumerate(character["inventory"], 1):
            print("    %d. %s" % (i, item))
        if not character["inventory"]:
            print("    （物品欄為空）")
            return
        item_choice = input("  選擇物品編號: ").strip()
        if not item_choice.isdigit():
            print("  無效選擇。")
            return
        idx = int(item_choice) - 1
        if idx < 0 or idx >= len(character["inventory"]):
            print("  無效的編號。")
            return
        item_name = character["inventory"][idx]
        print("  可槽位:")
        for j, (sid, sname) in enumerate(EQUIPMENT_SLOTS, 1):
            cur = equipment.slots.get(sid)
            status = cur["item"]["name"] if cur and cur["item"] else "(空)"
            print("    %d. %s [%s]" % (j, sname, status))
        slot_choice = input("  選擇槽位編號: ").strip()
        if not slot_choice.isdigit():
            print("  無效選擇。")
            return
        slot_idx = int(slot_choice) - 1
        if slot_idx < 0 or slot_idx >= len(EQUIPMENT_SLOTS):
            print("  無效的槽位。")
            return
        slot_id = EQUIPMENT_SLOTS[slot_idx][0]
        old = equipment.equip(slot_id, {"name": item_name, "durability": 100})
        if old:
            character["inventory"].append(old)
        character["inventory"].pop(idx)
        apply_equipment_bonuses(character, equipment)
        print("  已裝備: %s -> %s" % (item_name, EQUIPMENT_SLOTS[slot_idx][1]))
    elif choice == "3":
        print(equipment.display())
        slot_id = input("  輸入要卸下的槽位ID: ").strip()
        valid_slots = {s[0] for s in EQUIPMENT_SLOTS}
        if slot_id not in valid_slots:
            print("  無效的槽位。")
            return
        old = equipment.unequip(slot_id)
        if old:
            character["inventory"].append(old)
            apply_equipment_bonuses(character, equipment)
            print("  已卸下: %s" % old.get("name", "?"))
        else:
            print("  該槽位是空的。")


def do_crafting(character):
    print("")
    print("  可用配方:")
    for r in RECIPES:
        print("    %s: %s (分類: %s, 失敗率: %d%%)" % (r["recipe_id"], r["name"], r["category"], int(r["failure_chance"] * 100)))
    recipe_id = input("  輸入配方ID (或按Enter取消): ").strip()
    if not recipe_id:
        return
    success, result, msg = craft_item(recipe_id, character["inventory"])
    if success:
        print("  [成功] %s" % msg)
    else:
        print("  [失敗] %s" % msg)
    advance_time(character)


def do_interact_npc(character):
    loc = character["location"]
    if loc == "方碑丘":
        print("")
        print("  你遇到了小狐丸。她正在整理鏡湖火山口的冰晶。")
        print("  小狐丸: 「你好，旅人。需要什麼幫助嗎？」")
        print("  1. 詢問消息")
        print("  2. 交流 (消耗SP)")
        print("  0. 離開")
        choice = input("  > ").strip()
        if choice == "1":
            print('  小狐丸: 「鏡湖的水晶最近變得不太穩定...最好小心點。」')
        elif choice == "2":
            if character["sp"] >= 10:
                character["sp"] -= 10
                character["exp"] += 15
                print("  小狐丸分享了她的知識。你獲得了15點經驗。")
                print("  (SP -10)")
            else:
                print("  SP不足，無法進行交流。")
        else:
            print("  你告別了小狐丸。")
    elif loc == "秘密鐵工廠":
        print("")
        print("  你遇到了左間小蒼蘭。她正在工作台前忙碌。")
        print("  左間小蒼蘭: 「需要什麼嗎？我可以幫你打造東西。」")
        print("  1. 詢問合成配方")
        print("  2. 休息 (恢復SP)")
        print("  0. 離開")
        choice = input("  > ").strip()
        if choice == "1":
            print("  左間小蒼蘭: 「你有火焰藥水配方和鐵劍配方。需要我詳細解釋嗎？」")
        elif choice == "2":
            character["sp"] = min(character["max_sp"], character["sp"] + 20)
            print("  你在工坊休息，恢復了20SP。")
        else:
            print("  你告別了左間小蒼蘭。")
    elif loc == "便利店":
        print("")
        print("  你遇到了紅。她正在店裡值班。")
        print("  紅: 「歡迎光臨！有需要什麼嗎？」")
        print("  1. 查看商店")
        print("  2. 交流")
        print("  0. 離開")
        choice = input("  > ").strip()
        if choice == "1":
            print("  紅: 「我有些草藥和材料可以交換你的物品。」")
            print("  (商店功能開發中)")
        elif choice == "2":
            print('  紅: 「這裡是方碑丘的安全區，白天和夜晚都很平靜。」')
        else:
            print("  你告別了紅。")
    else:
        print("  這裡沒有可以互動的NPC。")
    advance_time(character)
    print("")
    print("-" * 40)
    print(get_time_desc(character["hour"], character["day"]))
    print("位置: %s" % character["location"])
    print("HP: %d/%d  |  SP: %d/%d  |  攻擊: %d  |  防禦: %d  |  經驗: %d  |  金幣: %d" % (
        character["hp"], character["max_hp"],
        character["sp"], character["max_sp"],
        character["atk"], character["def"],
        character["exp"], character["gold"],
    ))
    print("-" * 40)
    activity, npc_loc, mood = get_npc_activity("小狐丸", character["hour"])
    print("NPC 小狐丸: %s @ %s (%s)" % (activity, npc_loc, mood))
    if 6 <= character["hour"] < 10:
        print("  (早晨 - 精力充沛)")
    elif 10 <= character["hour"] < 14:
        print("  (上午 - 正當午)")
    elif 14 <= character["hour"] < 18:
        print("  (午後 - 熱浪襲來)")
    elif 18 <= character["hour"] < 22:
        print("  (傍晚 - 涼風習習)")
    else:
        print("  (夜晚 - 闇影籠罩)")
    print("")


def print_status(character):
    print("")
    print("-" * 40)
    print(get_time_desc(character["hour"], character["day"]))
    print("位置: %s" % character["location"])
    print("HP: %d/%d  |  SP: %d/%d  |  攻擊: %d  |  防禦: %d  |  經驗: %d  |  金幣: %d" % (
        character["hp"], character["max_hp"],
        character["sp"], character["max_sp"],
        character["atk"], character["def"],
        character["exp"], character["gold"],
    ))
    print("-" * 40)
    activity, npc_loc, mood = get_npc_activity("小狐丸", character["hour"])
    print("NPC 小狐丸: %s @ %s (%s)" % (activity, npc_loc, mood))
    if 6 <= character["hour"] < 10:
        print("  (早晨 - 精力充沛)")
    elif 10 <= character["hour"] < 14:
        print("  (上午 - 正當午)")
    elif 14 <= character["hour"] < 18:
        print("  (午後 - 熱浪襲來)")
    elif 18 <= character["hour"] < 22:
        print("  (傍晚 - 涼風習習)")
    else:
        print("  (夜晚 - 闇影籠罩)")
    print("")


def print_menu():
    print("  1. 探索周圍")
    print("  2. 與NPC對話")
    print("  3. 前往其他場景")
    print("  4. 休息")
    print("  5. 查看物品欄")
    print("  6. 查看/裝備物品")
    print("  7. 查看地圖")
    print("  8. 合成物品")
    print("  h. 幫助")
    print("")
    print("  > ", end="")


def start_game():
    print("")
    print("=" * 60)
    print("  角色扮演模擬 — CLI RPG Simulation")
    print("  Target: CLI only, no UI, symbol portraits")
    print("=" * 60)
    print("")
    print("  這是一個基於終端機的角色扮演模擬遊戲。")
    print("  使用數字鍵盤輸入指令，輸入 q 退出遊戲。")
    print("")
    show_help()
    input("  按 Enter 開始遊戲...")

    character = init_character()
    equipment = EquipmentManager()
    location = character["location"]

    while True:
        print_status(character)
        print_menu()
        ch = input().strip().lower()

        if ch in ("q", "quit", "exit"):
            print("")
            print("遊戲結束。謝謝遊玩！")
            break

        if ch == "h":
            show_help()
            continue

        if ch == "1":
            do_explore(character)

        elif ch == "2":
            do_interact_npc(character)
            advance_time(character)

        elif ch == "3":
            do_travel(character)

        elif ch == "4":
            do_rest(character)

        elif ch == "5":
            do_inventory(character)

        elif ch == "6":
            do_equipment_menu(character, equipment)

        elif ch == "7":
            print(display_world_map(location))

        elif ch == "8":
            do_crafting(character)

        else:
            print("  未知指令。輸入 h 查看幫助。")


if __name__ == "__main__":
    start_game()