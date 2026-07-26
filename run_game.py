"""Launch the CLI RPG simulation game."""
import sys
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
)


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
    print("  指令:")
    print("    1-9 : 選擇選項")
    print("    q/quit : 退出遊戲")
    print("    equip <欄位> : 裝備物品")
    print("    craft <配方ID> : 合成物品")
    print("    equipment : 查看裝備")
    print("    map : 查看地圖")
    print("    time : 查看時間")
    print("    inventory : 查看物品欄")
    print("")
    input("  按 Enter 開始遊戲...")

    equipment = EquipmentManager()
    inventory = ["草藥", "木柄"]
    day = 1
    hour = 8
    location = "方碑丘"

    while True:
        print("")
        print("-" * 40)
        print(get_time_desc(hour, day))
        print("位置: %s" % location)
        print("HP: 100/100  |  SP: 50/50  |  經驗: 0")
        print("-" * 40)

        activity, npc_loc, mood = get_npc_activity("小狐丸", hour)
        print("NPC 小狐丸: %s @ %s (%s)" % (activity, npc_loc, mood))

        print("")
        print("1. 探索周圍")
        print("2. 與NPC對話")
        print("3. 前往其他場景")
        print("4. 休息")
        print("5. 查看物品欄")
        print("6. 查看裝備")
        print("7. 查看地圖")
        print("8. 合成物品")
        print("")
        print("  > ", end="")

        ch = input().strip()

        if ch.lower() in ("q", "quit", "exit"):
            print("")
            print("遊戲結束。謝謝遊玩！")
            break

        if ch == "1":
            print("你在周圍探索，發現了一些有用的東西。")
            hour += 1
        elif ch == "2":
            print("你與附近的NPC交談，獲得了有用的信息。")
            hour += 1
        elif ch == "3":
            destinations = WORLD_MAP.get(location, {})
            if destinations:
                print("可以去的地方:")
                for i, (dir, dest) in enumerate(destinations.items(), 1):
                    print("  %d. %s -> %s" % (i, dir, dest))
                print("  0. 取消")
                choice = input("  > ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(destinations):
                    dest = list(destinations.values())[int(choice) - 1]
                    location = dest
                    print("移動到 %s" % dest)
                    hour += 1
        elif ch == "4":
            print("你休息了，體力恢復了。")
            hour += 2
            day += 1 if hour >= 24 else 0
            hour = hour % 24
        elif ch == "5":
            print("物品欄:")
            for i, item in enumerate(inventory, 1):
                print("  %d. %s" % (i, item))
            if not inventory:
                print("  （物品欄為空）")
        elif ch == "6":
            print(equipment.display())
        elif ch == "7":
            print(display_world_map(location))
        elif ch == "8":
            print("可用配方:")
            for r in RECIPES:
                print("  %s: %s (分類: %s)" % (r["recipe_id"], r["name"], r["category"]))
            recipe_id = input("  輸入配方ID: ").strip()
            success, result, msg = craft_item(recipe_id, inventory)
            if success:
                print("[成功] %s" % msg)
            else:
                print("[失敗] %s" % msg)
        else:
            print("未知指令。")


if __name__ == "__main__":
    start_game()