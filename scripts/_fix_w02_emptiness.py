# -*- coding: utf-8 -*-
"""批次 58：W02 琥珀紀元村莊空盪修復——場景物件與敵人群補齊。

根因：data/game_supplement.json 的 locations_for_objects 只有 13 個 W01 地點，
小吉鎮/大根莖村（W02 琥珀紀元）完全缺席——場景物件不生成（0 個）、
LOCATION_ENEMIES 無鍵（0 種敵人）。玩家經迴廊到 W02 後什麼都不能做，
琥珀紀元世界線形同虛設（且 W02 是 Lv1 可達的世界線）。

修復：
1. locations_for_objects 補 小吉鎮、大根莖村（生成容器/裝飾/工作台）
2. W02 村莊敵人群補中世紀系（野狼/哥布林/野豬/毒蛇/大蜘蛛/森狼）——
   數量值均為普通等級（HP<120、ATK<30），符合《琥珀紀元》硬核中世紀語境
"""
import json
import os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps", "game-rpg", "data", "game_supplement.json")
with open(PATH, "r", encoding="utf-8") as f:
    sup = json.load(f)

locs = sup.setdefault("locations_for_objects", [])
added = []
for l in ("小吉鎮", "大根莖村"):
    if l not in locs:
        locs.append(l)
        added.append(l)

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(sup, f, ensure_ascii=False, indent=1)

print("locations_for_objects 補齊:", added or "已存在")
# 敵人群正式指派在 game_data.py distribution 段（種子化 setdefault），
# 不在 JSON 重複定義（避免兩處真相來源漂移）。
