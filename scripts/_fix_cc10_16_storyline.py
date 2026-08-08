# -*- coding: utf-8 -*-
"""修正 CC-10/CC-16 卡片故事線污染。

文本權威：《角色卡：小倉 靜子 — 大正軍國的孤獨觀測者》與
《世界線錨定 — 補充欄位》世界線總表：靜子／小倉靜子屬
W01-B 大正浪漫線（故事線 SL-06 大正浪漫與鋼鐵殉葬），
非 SL-10 魔女學府。
"""
import json
import sys
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "apps" / "game-rpg" / "data" / "game_cards.json"
SL06 = "SL-06 大正浪漫與鋼鐵殉葬"

raw = PATH.read_text(encoding="utf-8")
data = json.loads(raw)
cards = {c.get("card_id"): c for c in data.get("cards", [])}

fixed = []
for cid in ("CC-10", "CC-16"):
    c = cards.get(cid)
    if not c:
        print(f"!! {cid} 卡片不存在")
        continue
    st = c.setdefault("stats", {})
    old = st.get("所屬故事線")
    if old != SL06:
        st["所屬故事線"] = SL06
        fixed.append((cid, c.get("name"), old, SL06))

if not fixed:
    print("無需修正（已是 SL-06）")
    sys.exit(0)

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")

for cid, nm, old, new in fixed:
    print(f"修正 {cid} {nm}: {old!r} → {new!r}")
print("已寫回", PATH)
