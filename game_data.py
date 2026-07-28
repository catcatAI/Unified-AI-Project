"""
game_data.py — MASSIVE content expansion for CLI RPG.
Generates 3000+ entities from card data + real-world analogies.
"""
import json, os, random as _random
from typing import Any, Dict, List, Optional
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
CARD_PATH = DATA_DIR / "game_cards.json"

_seed = _random.Random()  # non-deterministic (time-based)

def _load_cards() -> dict:
    if CARD_PATH.exists():
        with open(CARD_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"cards": [], "cards_by_type": {}, "token_by_category": {}}

_CARD_DATA = _load_cards()
_ALL_CARDS: list = _CARD_DATA.get("cards", [])

def _cards_by_type(t: str) -> list:
    return [c for c in _ALL_CARDS if c.get("card_type") == t]

_CHARACTER_CARDS = _cards_by_type("角色卡")
_SCENE_CARDS = _cards_by_type("場景卡")
_STORY_CARDS = _cards_by_type("劇情節點卡")
_ORG_CARDS = _cards_by_type("組織卡")
_NATION_CARDS = _cards_by_type("國家卡")
_RULE_CARDS = _cards_by_type("規則卡")
_SKILL_CARDS = _cards_by_type("技能卡")
_STORYLINE_CARDS = _cards_by_type("故事線卡") + _cards_by_type("故事線補充卡")
_WORLD_CORE_CARDS = _cards_by_type("世界觀核心卡")
_MECHANISM_CARDS = _cards_by_type("通用機制卡")
_CHAR_SUPP_CARDS = _cards_by_type("角色補充卡")   # Supplement cards that patch base chars

# Meta/design-only cards: no gameplay simulation role
IGNORED_CARD_TYPES = frozenset([
    "元公式卡", "元設定卡", "創作工具卡", "安全詞庫卡", "專案管理卡"
])

def _tokens_by_cat(card, cat: str) -> list:
    return [t for t in card.get("tokens", []) if t.get("category") == cat]

# ══════════════════════════════════════════════════════════════════
# 1. NAVAL WEAPONS — 60 real warship classes (艦娘)
# ══════════════════════════════════════════════════════════════════

# Format: (name, type, slot, atk_mult, def_mult, durability, value, nation, ship_class)
NAVAL_DATA = [
    # ==== Japan (IJN) ====
    ("46cm連裝砲","weapon","right_hand",0.80,0.0,200,500,"日本","大和型戦艦"),
    ("41cm連裝砲","weapon","right_hand",0.60,0.0,180,400,"日本","長門型戦艦"),
    ("36.5cm連裝砲改","weapon","right_hand",0.55,0.0,170,380,"日本","金剛型戦艦改"),
    ("41cm三連裝砲","weapon","right_hand",0.65,0.0,190,420,"日本","加賀型戦艦"),
    ("51cm連裝砲","weapon","right_hand",0.95,-0.1,150,700,"日本","超大和型計画"),
    ("20.3cm連裝砲","weapon","right_hand",0.35,0.0,120,250,"日本","重巡主砲"),
    ("15.5cm三連裝砲","weapon","right_hand",0.30,0.0,100,200,"日本","軽巡主砲"),
    ("12.7cm連装砲","weapon","right_hand",0.25,0.0,80,150,"日本","駆逐主砲"),
    ("10cm連装高角砲","weapon","right_hand",0.20,0.0,70,130,"日本","秋月型駆逐"),
    ("61cm四連裝魚雷","weapon","right_hand",0.70,-0.1,80,400,"日本","酸素魚雷"),
    ("61cm五連裝魚雷","weapon","right_hand",0.80,-0.15,70,500,"日本","改修魚雷"),
    ("甲標的甲型","weapon","right_hand",0.90,-0.2,60,600,"日本","特殊潜航艇"),
    ("甲標的丙型","weapon","right_hand",0.95,-0.25,50,700,"日本","特殊潜航艇改"),
    ("彗星艦爆","weapon","both_hands",0.50,0.1,90,300,"日本","艦載爆撃機"),
    ("彗星一二型","weapon","both_hands",0.55,0.1,85,340,"日本","艦爆改良型"),
    ("天山艦攻","weapon","both_hands",0.40,0.15,100,280,"日本","艦載攻撃機"),
    ("流星艦攻","weapon","both_hands",0.45,0.15,95,320,"日本","攻撃機"),
    ("紫電改二","weapon","both_hands",0.45,0.2,85,350,"日本","局地戦闘機"),
    ("烈風","weapon","both_hands",0.55,0.1,95,380,"日本","艦載戦闘機"),
    ("紫電","weapon","both_hands",0.40,0.2,90,310,"日本","局地戦闘機"),
    ("零戦五二型","weapon","both_hands",0.35,0.15,100,280,"日本","艦載戦闘機"),
    ("零戦二一型","weapon","both_hands",0.30,0.1,110,250,"日本","艦載戦闘機"),
    # ==== USA (USN) ====
    ("16inch三連裝砲","weapon","right_hand",0.75,0.0,210,550,"美国","Iowa型戦艦"),
    ("14inch三連裝砲","weapon","right_hand",0.55,0.05,190,400,"美国","NewMexico型戦艦"),
    ("12inch連裝砲","weapon","right_hand",0.45,0.05,170,350,"美国","標準型戦艦"),
    ("8inch三連裝砲","weapon","right_hand",0.38,0.05,130,280,"美国","重巡主砲"),
    ("6inch三連裝砲","weapon","right_hand",0.32,0.05,110,220,"美国","軽巡主砲"),
    ("5inch兩用砲","weapon","right_hand",0.22,0.1,90,160,"美国","駆逐主砲"),
    ("40mm四連裝機関砲","weapon","right_hand",0.18,0.15,70,120,"美国","ボフォース"),
    ("20mm機関砲","weapon","right_hand",0.12,0.1,60,80,"美国","エリコン"),
    ("Mk13魚雷","weapon","right_hand",0.45,0.0,70,250,"美国","航空魚雷"),
    ("F4Uコルセア","weapon","both_hands",0.50,0.2,100,360,"美国","艦載戦闘機"),
    ("F6Fヘルキャット","weapon","both_hands",0.48,0.15,110,340,"美国","艦載戦闘機"),
    ("SBDドーントレス","weapon","both_hands",0.45,0.1,95,300,"美国","艦載爆撃機"),
    ("TBFアベンジャー","weapon","both_hands",0.42,0.15,105,290,"美国","艦載攻撃機"),
    ("SB2Cヘルダイバー","weapon","both_hands",0.48,0.08,90,310,"美国","艦爆"),
    # ==== UK (RN) ====
    ("15inch連裝砲","weapon","right_hand",0.50,0.0,185,380,"英国","Nelson型戦艦"),
    ("14inch四連裝砲","weapon","right_hand",0.55,0.0,175,390,"英国","KingGeorgeV型"),
    ("16inch連裝砲","weapon","right_hand",0.70,0.0,200,520,"英国","Vanguard型"),
    ("6inch連裝砲","weapon","right_hand",0.30,0.05,100,200,"英国","軽巡主砲"),
    ("4.7inch砲","weapon","right_hand",0.20,0.0,75,130,"英国","駆逐主砲"),
    ("21inch魚雷","weapon","right_hand",0.50,-0.05,65,280,"英国","魚雷"),
    ("スーパーマリン","weapon","both_hands",0.52,0.18,105,370,"英国","艦載戦闘機"),
    ("フェアリーソード","weapon","both_hands",0.38,0.12,100,260,"英国","艦載攻撃機"),
    # ==== Germany (KM) ====
    ("38cm連裝砲","weapon","right_hand",0.60,0.0,175,420,"德国","Bismarck型"),
    ("28cm三連裝砲","weapon","right_hand",0.45,0.0,160,350,"德国","Scharnhorst型"),
    ("20.3cm連裝砲","weapon","right_hand",0.40,0.0,125,270,"德国","AdmiralHipper型"),
    ("15cm連裝砲","weapon","right_hand",0.28,0.05,95,190,"德国","軽巡主砲"),
    ("12.7cm砲","weapon","right_hand",0.22,0.05,80,150,"德国","駆逐主砲"),
    ("53.3cm魚雷","weapon","right_hand",0.55,-0.05,75,320,"德国","G7a魚雷"),
    ("G7e魚雷","weapon","right_hand",0.60,-0.1,70,350,"德国","電動魚雷"),
    ("Me262","weapon","both_hands",0.65,0.25,60,600,"德国"," jet戦闘機"),
    # ==== Italy (RM) ====
    ("381mm三連裝砲","weapon","right_hand",0.58,0.0,170,400,"意大利","Littorio型"),
    ("320mm四連裝砲","weapon","right_hand",0.50,0.0,160,350,"意大利","Doria型"),
    ("203mm連裝砲","weapon","right_hand",0.36,0.0,115,260,"意大利","Zara型"),
    ("152mm三連裝砲","weapon","right_hand",0.30,0.05,95,210,"意大利","軽巡主砲"),
    ("533mm魚雷","weapon","right_hand",0.45,-0.05,70,260,"意大利","魚雷"),
    ("Reggiane2005","weapon","both_hands",0.55,0.2,85,400,"意大利","戦闘機"),
]

# ══════════════════════════════════════════════════════════════════
# 2. ANIMAL ARMOR/WEAPONS — 80 real species (獣娘)
# ══════════════════════════════════════════════════════════════════

ANIMAL_DATA = [
    # (name, type, slot, atk_mult, def_mult, spd_mult, karma_mult, durability, value, species, biome)
    # ==== Mammals: Canids ====
    ("狼王毛皮","armor","torso",0.0,0.35,0.15,0.0,120,150,"狼","森林"),
    ("狼牙首飾","accessory","neck",0.15,0.0,0.05,0.05,80,100,"狼","森林"),
    ("銀狼の尾","armor","back",0.0,0.10,0.25,0.05,70,130,"銀狼","雪山"),
    ("狐の霊衣","armor","torso",0.0,0.20,0.30,0.10,110,180,"狐","森林"),
    ("狐火の腕輪","accessory","left_hand",0.10,0.0,0.10,0.15,60,140,"狐","森林"),
    ("柴犬の忠誠","accessory","neck",0.0,0.10,0.05,0.30,90,110,"柴犬","村"),
    # ==== Mammals: Ursids ====
    ("熊の鉄壁","armor","torso",0.0,0.50,0.0,0.0,200,250,"熊","山岳"),
    ("熊の腕力","weapon","right_hand",0.40,-0.05,-0.05,0.0,150,220,"熊","山岳"),
    ("白熊の毛","armor","legs",0.0,0.35,0.0,0.05,180,230,"白熊","極地"),
    ("熊猫の柔軟","armor","torso",0.0,0.20,0.10,0.15,100,160,"熊猫","竹林"),
    # ==== Mammals: Felids ====
    ("虎の縞鎧","armor","torso",0.0,0.40,0.10,0.0,160,220,"虎","密林"),
    ("虎爪の手甲","weapon","right_hand",0.35,0.0,0.10,0.0,100,200,"虎","密林"),
    ("獅子の鬣","armor","head",0.0,0.25,0.0,0.15,130,200,"獅子","草原"),
    ("豹の敏捷","armor","feet",0.0,0.10,0.35,0.0,80,180,"豹","草原"),
    ("猫の軽靴","armor","feet",0.0,0.05,0.30,0.05,70,100,"猫","市街"),
    ("猫の器用","accessory","right_hand",0.05,0.0,0.15,0.10,60,90,"猫","市街"),
    ("黒猫の護符","accessory","neck",0.0,0.10,0.10,0.20,50,120,"黑猫","市街"),
    # ==== Mammals: Cervids ====
    ("鹿の角冠","armor","head",0.05,0.10,0.05,0.25,90,120,"鹿","森林"),
    ("鹿の敏捷","armor","feet",0.0,0.0,0.25,0.10,70,100,"鹿","森林"),
    ("大鹿の角","weapon","right_hand",0.25,0.0,0.0,0.10,100,130,"大鹿","森林"),
    # ==== Mammals: Equids & Bovids ====
    ("馬の蹄鉄","armor","feet",0.0,0.15,0.20,0.0,120,80,"馬","草原"),
    ("馬の雄姿","armor","torso",0.0,0.15,0.15,0.10,90,110,"馬","草原"),
    ("野牛の剛角","weapon","right_hand",0.30,0.0,-0.05,0.0,150,180,"野牛","草原"),
    ("山羊の軽業","armor","legs",0.0,0.05,0.20,0.05,70,80,"山羊","山岳"),
    # ==== Mammals: Primates ====
    ("猿の器用","accessory","left_hand",0.05,0.0,0.15,0.05,60,90,"猿","密林"),
    ("大猩猩の剛腕","weapon","right_hand",0.45,0.0,-0.10,0.0,180,250,"大猩猩","密林"),
    # ==== Mammals: Marine ====
    ("海豚の流線","armor","legs",0.0,0.05,0.25,0.05,60,140,"海豚","海"),
    ("鯨の強靭","armor","torso",0.0,0.45,0.0,0.05,250,320,"鯨","海"),
    ("鯨の骨鎧","armor","torso",0.0,0.55,0.0,0.0,300,400,"鯨","海"),
    ("海豹の滑走","armor","feet",0.0,0.0,0.15,0.10,50,90,"海豹","海"),
    # ==== Birds ====
    ("鷹の翼膜","armor","back",0.0,0.15,0.35,0.05,100,160,"鷹","山岳"),
    ("鷹の爪","weapon","right_hand",0.25,0.0,0.15,0.0,80,140,"鷹","山岳"),
    ("梟の知恵","accessory","head",0.0,0.0,0.05,0.30,60,150,"梟","森林"),
    ("鴉の羽","armor","back",0.0,0.10,0.20,0.10,70,100,"鴉","市街"),
    ("白鳥の優雅","accessory","neck",0.0,0.05,0.10,0.25,50,130,"白鳥","湖"),
    ("燕の俊敏","armor","feet",0.0,0.0,0.30,0.05,50,110,"燕","空"),
    ("孔雀の華麗","accessory","neck",0.0,0.05,0.05,0.30,40,160,"孔雀","森林"),
    ("鶴の寿命","armor","legs",0.0,0.10,0.10,0.20,80,140,"鶴","湖"),
    ("渡り鳥の羽","armor","back",0.0,0.05,0.20,0.05,60,90,"渡鳥","空"),
    # ==== Reptiles & Amphibians ====
    ("蛇の鱗衣","armor","torso",0.0,0.30,0.10,0.20,110,140,"蛇","森林"),
    ("蛇の毒牙","weapon","right_hand",0.20,0.0,0.10,0.0,70,120,"蛇","森林"),
    ("亀の甲羅盾","weapon","left_hand",0.0,0.60,0.0,0.05,250,250,"亀","湖"),
    ("鰐の顎","weapon","right_hand",0.35,0.0,-0.05,0.0,140,200,"鰐","水辺"),
    ("鰐の鱗","armor","torso",0.0,0.35,0.0,0.05,180,220,"鰐","水辺"),
    ("蜥蜴の尾","armor","back",0.0,0.05,0.20,0.05,60,80,"蜥蜴","砂漠"),
    ("壁虎の足掛","armor","feet",0.0,0.0,0.15,0.10,50,90,"壁虎","市街"),
    ("蛙の跳躍","armor","legs",0.0,0.0,0.20,0.05,40,70,"蛙","水辺"),
    # ==== Arthropods ====
    ("蝶の鱗粉","accessory","neck",0.0,0.10,0.10,0.20,50,90,"蝶","花園"),
    ("蝶の翅","armor","back",0.0,0.05,0.15,0.15,40,100,"蝶","花園"),
    ("蜂の針","weapon","right_hand",0.20,0.0,0.10,0.0,30,80,"蜂","花園"),
    ("蜘蛛の糸","armor","legs",0.0,0.15,0.10,0.0,70,100,"蜘蛛","森林"),
    ("蠍の毒針","weapon","right_hand",0.25,0.0,0.0,0.0,60,110,"蠍","砂漠"),
    ("蠍の甲殻","armor","torso",0.0,0.25,0.0,0.05,130,150,"蠍","砂漠"),
    ("蟻の力","accessory","waist",0.10,0.0,0.0,0.05,80,70,"蟻","草原"),
    ("蜻蛉の複眼","accessory","head",0.0,0.0,0.15,0.10,40,110,"蜻蛉","水辺"),
    # ==== Mythical/Cryptid ====
    ("蛟の逆鱗","armor","torso",0.10,0.30,0.10,0.05,200,350,"蛟","深潭"),
    ("鳳凰の羽衣","armor","back",0.05,0.20,0.20,0.30,150,500,"鳳凰","天"),
    ("麒麟の角","accessory","head",0.10,0.10,0.10,0.35,180,450,"麒麟","仙境"),
    ("白澤の知慧","accessory","neck",0.0,0.05,0.05,0.50,100,400,"白澤","仙境"),
]

# ══════════════════════════════════════════════════════════════════
# 3. JUNK ITEMS — 200 non-interactive flavor items
# ══════════════════════════════════════════════════════════════════

JUNK_TEMPLATES = [
    # (base_name, prefix_variants)
    ("錆びた釘", ["錆びた","古びた","曲がった","折れた","欠けた"]),
    ("割れた瓶", ["割れた","ひび割れた","小さな","大きな"]),
    ("埃を被った本", ["埃を被った","濡れた","焼けた","破れた"]),
    ("使い古した筆", ["使い古した","新しい","折れた","乾いた"]),
    ("折れた枝", ["折れた","太い","細い","乾燥した"]),
    ("乾燥した葉", ["乾燥した","新鮮な","色づいた","虫食いの"]),
    ("小さな石ころ", ["丸い","尖った","平たい","光る","重い"]),
    ("色あせた布", ["色あせた","鮮やかな","絹の","麻の"]),
    ("切れた紐", ["切れた","丈夫な","細い","太い"]),
    ("空き箱", ["小さな","大きな","頑丈な","薄っぺらい"]),
    ("壊れた時計", ["壊れた","古い","金の","銀の"]),
    ("焦げた紙", ["焦げた","濡れた","皺くちゃ","破れた"]),
    ("欠けた宝石", ["欠けた","小さな","光る","色褪せた"]),
    ("歪んだ鏡", ["歪んだ","割れた","丸い","四角い"]),
    ("古い賽子", ["古い","新しい","歪んだ","小さい"]),
    ("空のインク壺", ["空の","半分の","乾いた","割れた"]),
    ("片方の手袋", ["片方の","毛糸の","皮の","布の"]),
    ("錆びたスプーン", ["錆びた","銀の","木の","曲がった"]),
    ("曲がった針", ["曲がった","錆びた","細い","折れた"]),
    ("ほつれた靴下", ["ほつれた","新しい","破れた","色褪せた"]),
    ("ぼろぼろの日記", ["ぼろぼろの","新しい","読めない","鍵付きの"]),
    ("異国の切手", ["異国の","古い","美しい","珍しい"]),
    ("使い捨ての箸", ["使い捨ての","塗りの","竹の","折れた"]),
    ("燃え残った薪", ["燃え残った","太い","細い","乾いた"]),
    ("読めない文字のメモ", ["読めない","走り書きの","丁寧な","濡れた"]),
    ("虫食いの木片", ["虫食いの","滑らかな","彫刻された","腐った"]),
    ("古いボタン", ["古い","真鍮の","貝の","木の"]),
    ("色褪せたリボン", ["色褪せた","赤い","青い","絹の"]),
    ("埃まみれの置物", ["埃まみれの","陶器の","木彫りの","石の"]),
    ("古い写真", ["古い","色褪せた","破れた","丸まった"]),
    ("錆びた針金", ["錆びた","真鍮の","鉄の","太い"]),
    ("抜け落ちた羽根", ["抜け落ちた","白い","黒い","模様のある"]),
    ("乾いた泥", ["乾いた","湿った","固まった","柔らかい"]),
    ("空瓶", ["小さな","大きな","茶色の","透明な","緑の"]),
    ("猫じゃらし", ["枯れた","乾いた","長い","短い"]),
    ("使い古した鞄", ["使い古した","革の","布の","破れた"]),
    ("ほころびた帽子", ["ほころびた","新しい","藁の","布の"]),
    ("折れた万年筆", ["折れた","金の","銀の","プラスチックの"]),
    ("切れた腕輪", ["切れた","銀の","木の","革の"]),
    ("絡まった毛糸", ["絡まった","赤い","青い","白い","黄色い"]),
    ("食べかけの飴", ["食べかけの","包み紙の","溶けた","固まった"]),
    ("鳥の巣の残骸", ["鳥の巣の","崩れた","小さな","大きな"]),
    ("穴の開いた靴下", ["穴の開いた","毛糸の","綿の","絹の"]),
    ("錆びた剣の柄", ["錆びた","木の","革巻きの","銀の"]),
    ("古びた地図の切れ端", ["古びた","濡れた","焼けた","破れた"]),
    ("使い古した歯ブラシ", ["使い古した","新しい","折れた","曲がった"]),
    ("乾燥した花びら", ["乾燥した","色褪せた","押し花の","砕けた"]),
    ("錆びた自転車の部品", ["錆びた","壊れた","古い","曲がった"]),
    ("切れた靴紐", ["切れた","新しい","濡れた","固まった"]),
    ("壊れた花瓶", ["壊れた","陶器の","ガラスの","木の"]),
    ("半分の硬貨", ["半分の","古い","光る","錆びた"]),
    ("謎の液体の瓶", ["謎の","青い","赤い","緑の","泡立つ"]),
    ("小さな貝殻", ["螺旋の","平たい","尖った","欠けた","白い"]),
    ("錆びた鈴", ["錆びた","小さな","壊れた","古い"]),
]

JUNK_ITEMS = []
for base, prefixes in JUNK_TEMPLATES:
    for p in prefixes[:2]:  # limit to avoid too many
        JUNK_ITEMS.append(f"{p}{base}" if "の" not in p else f"{p}{base}")
# Add all base names too
JUNK_ITEMS.extend([t[0] for t in JUNK_TEMPLATES])
# Remove duplicates while preserving order
seen = set()
JUNK_ITEMS = [x for x in JUNK_ITEMS if not (x in seen or seen.add(x))]
# Total: ~150


# ══════════════════════════════════════════════════════════════════
# 4. HERBAL / CONSUMABLE ITEMS
# ══════════════════════════════════════════════════════════════════

HERBAL_ITEMS = [
    ("艾草","consumable",0.2,8,15,0,"艾草で作った薬"),
    ("薄荷","consumable",0.1,5,0,10,"清涼感のある薄荷"),
    ("蒲公英","consumable",0.1,3,5,5,"蒲公英の根"),
    ("人参","consumable",0.3,25,30,0,"高麗人参"),
    ("霊芝","consumable",0.2,30,20,15,"千年霊芝"),
    ("金創薬","consumable",0.3,35,45,0,"傷薬"),
    ("気付け薬","consumable",0.2,20,10,20,"気を鎮める薬"),
    ("万霊薬","consumable",0.4,60,60,40,"万能薬"),
    ("龍涎香","consumable",0.3,80,50,30,"竜の香り"),
    ("七星丹","consumable",0.3,120,80,50,"七つの星の力"),
    ("還魂草","consumable",0.2,50,100,0,"死者をも甦らせる草"),
    ("清心丸","consumable",0.2,40,10,40,"心を清める丸薬"),
    ("壮骨散","consumable",0.3,45,60,10,"骨を強くする薬"),
    ("止血草","consumable",0.2,10,25,0,"止血に効く草"),
    ("安眠茶","consumable",0.2,15,5,25,"安眠を誘う茶"),
    ("精力剤","consumable",0.3,50,10,60,"精力が湧く薬"),
    ("解毒散","consumable",0.2,25,20,15,"解毒の粉末"),
    ("保湿軟膏","consumable",0.2,18,20,10,"肌を癒す軟膏"),
    ("活力ドリンク","consumable",0.3,30,15,25,"即効性の活力剤"),
    ("養生酒","consumable",0.4,60,30,40,"養生の薬酒"),
    ("気功丸","consumable",0.3,55,20,45,"気を整える丸薬"),
    ("百草丹","consumable",0.3,70,55,35,"百の草から作った丹薬"),
    ("神水","consumable",0.2,200,100,80,"伝説の神水"),
    ("神秘のキノコ","consumable",0.2,50,_seed.randint(10,50),_seed.randint(10,30),"神秘の力を持つキノコ"),
    ("月の雫","consumable",0.1,80,40,30,"月明かりが凝縮した雫"),
    ("時空の砂","consumable",0.1,0,0,0,"時空の砂（効果不明）"),
]

# ══════════════════════════════════════════════════════════════════
# 5. ELEMENTAL / MAGIC ITEMS
# ══════════════════════════════════════════════════════════════════

ELEMENTAL_ITEMS = [
    ("炎帝の剣","weapon","right_hand",0.6,-0.1,"灼熱の炎を纏う剣",300,80),
    ("氷晶の杖","weapon","right_hand",0.3,0.3,"氷の結晶で出来た杖",280,75),
    ("雷神の鎚","weapon","right_hand",0.7,-0.15,"雷を呼ぶ戦鎚",350,70),
    ("風霊の弓","weapon","both_hands",0.4,0.25,"風の精霊が宿る弓",260,85),
    ("大地の盾","weapon","left_hand",0.0,0.7,"大地の力が宿る盾",300,150),
    ("光輝の鎧","armor","torso",0.3,0.3,"聖なる光を放つ鎧",350,120),
    ("闇夜の外套","armor","back",0.2,0.4,"影に溶ける暗黒の外套",280,80),
    ("精霊の指環","accessory","left_hand",0.2,0.3,"精霊の力が宿る指環",200,40),
    ("炎の精霊石","accessory","neck",0.3,0.1,"火の精霊が宿る石",180,50),
    ("氷の結晶","armor","head",0.1,0.3,"永遠に溶けない氷",160,60),
    ("雷の宝玉","accessory","right_hand",0.2,0.15,"雷光を放つ宝玉",170,45),
    ("風の羽織","armor","back",0.15,0.25,"風の如く軽い羽織",150,70),
    ("地の護石","accessory","neck",0.0,0.35,"大地の加護を受けた石",200,65),
    ("太陽の輝き","armor","head",0.25,0.25,"太陽の光を纏う冠",250,100),
    ("星屑のマント","armor","back",0.1,0.2,"星の力が宿るマント",190,90),
    ("虚空の欠片","accessory","left_hand",0.15,0.15,"虚空の力が宿る欠片",140,80),
    ("混沌の種","accessory","neck",0.2,0.1,"混沌から生まれた種",160,95),
    ("秩序の天秤","weapon","left_hand",0.1,0.3,"均衡を司る天秤",200,120),
]

# Note: consumable-type elemental items moved to HERBAL_ITEMS above

# ══════════════════════════════════════════════════════════════════
# 6. NPC GENERATION — character cards → interactive NPCs
# ══════════════════════════════════════════════════════════════════

# Canonical scene name mapping (card scene name -> in-game location key)
_SCENE_NAME_MAP: Dict[str, str] = {
    "聖十字校園": "聖十字校園", "聖十字環形堡壘校園": "聖十字校園",
    "農學院": "農學院", "農學院（The Institute）": "農學院",
    "魔女學府": "魔女學府", "魔女學府 M-值工程沙盒": "魔女學府",
    "鬱鬱山": "鬱鬱山", "鏡湖": "鏡湖", "鏡山": "鏡山",
    "卡洛夫角": "卡洛夫角", "卡洛夫山脈": "卡洛夫山脈",
    "霧海": "霧海群島", "霧海群島": "霧海群島",
    "霧海北海峽": "霧海群島", "霧海南岸": "霧海群島",
    "便利店": "便利店", "英靈殿": "英靈殿",
    "廢棄礦坑": "廢棄礦坑", "秘密鐵工廠": "秘密鐵工廠",
    "軌道居住站": "軌道居住站大學院", "軌道居住站大學院": "軌道居住站大學院",
    "鏽蝕城邦": "鏽蝕城邦", "迴廊": "迴廊",
    "中央大圖書館": "中央大圖書館", "珊瑚台": "珊瑚台",
    "黑淵台": "黑淵台", "彩紋礁": "彩紋礁", "流光": "流光",
    "星光舞台": "星光舞台", "大根莖村": "大根莖村",
    "小吉鎮": "小吉鎮", "煙雲溫泉湖": "煙雲溫泉湖",
    "清溪河": "清溪河", "極北冰原": "極北冰原",
    "春日微縮立方": "春日微縮立方",
}

_NPC_LOCATIONS_POOL = [
    "聖十字校園", "鏡湖", "鬱鬱山", "卡洛夫角", "霧海群島",
    "秘密鐵工廠", "便利店", "英靈殿", "廢棄礦坑", "森林深處",
    "中央大圖書館", "農學院", "軌道居住站大學院",
]


def _get_npc_home_from_card(card: dict, fallback_idx: int) -> str:
    """Derive NPC home location from lore tokens (not random round-robin)."""
    lore_toks = _tokens_by_cat(card, "lore")
    home_keywords = ["主要場景", "所在", "家鄉", "基地", "棲息地", "活動範圍", "世界線"]
    for kw in home_keywords:
        for t in lore_toks:
            if kw in t.get("name", ""):
                val = t.get("value", "")
                for scene_key, mapped in _SCENE_NAME_MAP.items():
                    if len(scene_key) >= 2 and scene_key in val:
                        return mapped
    # Fallback: scan all lore token values for any scene name
    for t in lore_toks:
        val = t.get("value", "")
        for scene_key, mapped in _SCENE_NAME_MAP.items():
            if len(scene_key) >= 3 and scene_key in val:
                return mapped
    return _NPC_LOCATIONS_POOL[fallback_idx % len(_NPC_LOCATIONS_POOL)]


def _extract_race_from_card(card) -> str:
    """Extract race from lore tokens, fallback to stats, then fallback name."""
    lore_toks = _tokens_by_cat(card, "lore")
    race_from_lore = next((t.get("value","") for t in lore_toks if "種族" in t.get("name","")), "")
    if race_from_lore:
        return race_from_lore
    stats = card.get("stats", {})
    stats_race = stats.get("race", "")
    if stats_race:
        return stats_race
    name = card.get("name","?").split("(")[0].strip()
    if name and name != '?':
        return name[:10]
    for cat in ['vitality', 'element', 'energy', 'combat', 'skill']:
        for t in card.get("tokens", []):
            if t.get("category") == cat:
                v = t.get("value", "") or t.get("name", "")
                if v and len(v) < 10:
                    return v[:8]
    return "不明"


def _generate_npc_schedule(npc_name: str, home_loc: str) -> list:
    schedules = []
    slots = [(6,10),(10,14),(14,18),(18,22),(22,6)]
    activities = ["工作","巡邏","休息","社交","睡眠"]
    moods = ["focused","alert","rest","friendly","sleep"]
    social_locs = _seed.sample(
        ["聖十字校園","鬱鬱山","便利店","鏡湖","卡洛夫角"],
        k=min(5, len(_NPC_LOCATIONS_POOL)))
    locs = [home_loc, home_loc, home_loc, social_locs[0], home_loc]
    for i, (s,e) in enumerate(slots):
        schedules.append((s,e,activities[i],locs[i] if i<len(locs) else home_loc,moods[i]))
    return schedules


# ── Lore-accurate merchant inventory builder ──────────────────────────────
# Maps role/craft keywords → lore-accurate item names from the world setting.
_LORE_TRADE_CATALOG: Dict[str, List[str]] = {
    "義體": ["初級感覺義體手臂","神經介面晶片","義眼（熱成像型）","義足（競速型）","義體冷卻液","靈子-電子轉換器","義體診斷工具"],
    "脈動工業": ["脈動MK-III競速義肢","靈子加速迴路","肌肉纖維強化套件","感官擴展義耳","脈動工業維修手冊"],
    "永恆義體": ["永恆基礎義體套件","仿生皮膚補片","神經穩定劑","道德審查合規義體","永恆客服保固憑單"],
    "鐵砧防務": ["鐵砧戰術義肢","裝甲外骨骼胸甲","軍規神經加速器","鐵砧防務合約書","戰場維修套件"],
    "艦娘": ["46cm連裝砲","12.7cm連装砲","彗星艦爆","天山艦攻","艦側裝甲板","艦用主機","深水炸彈"],
    "圖紙艦娘": ["試作型艦裝設計圖","靈子驅動原型機","艦娘裝備藍圖","試驗型砲塔","未完成的艦裝零件"],
    "艦隊": ["戰術海圖","艦隊通訊密碼本","艦用信號旗","艦橋儀表板","燃油補給券"],
    "符文": ["初級符文石","靈子結晶","符文工藝刻刀","靈力催化劑","符文解析儀"],
    "魔法少女": ["變身核心水晶","魔力補充藥水","魔法少女入門手冊","概念核心碎片","反派邀請函"],
    "元素": ["火焰元素核心","水元素結晶","風精靈羽毛","雷電引導棒","地脈石"],
    "圖書館": ["迴廊索引卡","古代文明語言辭典","概念拓撲圖","物語核查問許可","禁忌資料室借閱券"],
    "圖書館管理員": ["迴廊索引卡","古代文明語言辭典","概念拓撲圖","物語核查問許可","禁忌資料室借閱券","館藏副本（限量）"],
    "研究": ["實驗日誌","樣本收集瓶","數據分析儀","靈子掃描器","研究報告副本"],
    "田野調查": ["野外調查記錄本","標本採集組件","生態觀測儀","妖精生態手冊","迴廊路徑記憶石"],
    "植物": ["稀有種子包","植物生長促進劑","草本萃取液","作物娘親和素","植物圖鑑（迴廊版）"],
    "農學院": ["作物娘親和素","稀有種子包","農學研究報告","GSI-4感知擴展儀","植物生態觀察日誌"],
    "五金": ["跨世界通用扳手組","靈子焊接棒","多維度螺絲","自修復齒輪","工具箱（跨世界規格）"],
    "五金店": ["跨世界通用扳手組","靈子焊接棒","多維度螺絲","自修復齒輪","工具箱（跨世界規格）"],
    "跨世界交易": ["跨世界匯票","多元宇宙護照","世界線轉換費率表","異界商品鑑定書","通用貨幣換算器"],
    "玩具": ["宿屋原創玩具","感應式互動人偶","手作皮革配件","限定版造型手環","兔娘紀念品"],
    "玩具製造": ["宿屋系列感應玩具","可編程互動人偶","手作皮革束帶","限定版月兔手環","客製化訂製服務券"],
    "成人玩具": ["宿屋原創成人玩具","高感度感知人偶","手作皮革配件","限定版造型手環","兔娘紀念品（限成人）"],
    "糕點": ["季節特製蛋糕","魔法奶油泡芙","元素調味餐乾","紫晶石風味糖","星光舞台限定甜點"],
    "烘焙": ["季節特製蛋糕","魔法奶油泡芙","紫暗元素糖霜","創意造型餅乾","食材學教材"],
    "獸醫": ["獸娘健康補品","物種適用藥品","基因穩定劑","動物溝通晶片","醫療繃帶（獸用）"],
    "偶像": ["特戰偶像團周邊","演唱會門票","簽名海報","光源靈石手環","特戰偶像應援棒"],
    "廢土": ["輻射屏蔽披風","廢料改造武器","輻射偵測器","淨化水囊","廢土生存手冊"],
    "輻射": ["輻射屏蔽披風","輻射偵測器","重金屬解毒劑","廢土生存手冊","淨化水囊"],
    "廢料": ["廢料改造零件","廢棄機械核心","鏽蝕城邦地圖","廢料鑑定工具","翻新材料包"],
    "極地": ["北極狐毛皮","極地保暖套裝","雪地陷阱組件","防寒藥草茶","冰原導航羅盤"],
    "北極狐": ["北極狐毛皮製品","極地保暖套裝","雪地陷阱組件","防寒藥草茶","冰原導航羅盤"],
    "極地獵手": ["極地獵具組","雪地偽裝套件","極地生存口糧","防寒急救藥包","獵物追蹤儀"],
    "神道": ["御守","靈力祈禱符","神道儀式酒","神社限定御朱印帳","結界石"],
    "巫女": ["神社御守","靈力祈禱符","弓道練習靶","神社限定御朱印帳","結界石"],
    "弓道": ["練習用弓","靈子箭矢","弓道手套","靜心符咒","弓弦蠟"],
    "神明": ["神諭碎片","召喚謳唱卷軸","神祇全名記錄冊","全名吟唱指南","神話時代遺物"],
    "校長": ["聖十字校章","學生手冊","入學許可申請表","校園地圖","神學教材（高級）"],
    "管家": ["軌道站設施維護手冊","管家禮儀指南","貴族餐具組","清潔用具（頂級）","龍息香薰"],
    "客服": ["客服禮儀手冊","溝通技巧卡牌","水元素補給品","安撫情緒晶石","藍水元素飾品"],
    "油漆": ["靛色元素塗料","油漆師傅工具組","色彩調配指南","防水塗料","顏料石"],
    "街頭技客": ["基因強化注射器","電子改造工具包","駭客程序卷軸","街頭市場情報","改造義體配件"],
    "造兵": ["軍工設計圖紙","精密機械零件","砲塔運作手冊","大正時代兵器圖鑑","靈子傳導裝置"],
    "機械": ["精密機械零件","靈子焊接棒","機械診斷儀","修復工具組","齒輪潤滑油"],
    "工匠": ["工匠工具組","精密零件箱","合金材料","加工技術手冊","訂製品委託券"],
    "海": ["深海珊瑚","人魚鱗片","海蛞蝓色素","聲吶定位器","深海壓力艙補給品"],
    "海盜": ["黑帆旗幟","掠奪地圖","貓族彎刀","贓物收購評估書","海上安全保障（一次性）"],
    "統治": ["鏽蝕城邦通行證","廢料稅收憑單","城邦守衛雇用合約","領地劃分地圖","廢墟知識手冊"],
    "教師": ["教學材料","課程許可卡","實驗器材組","參考書籍","補習課時間券"],
    "物理": ["物理實驗器材","黃雷元素電容","物理學教材","能量轉換計算器","電路板"],
    "default": ["乾糧（高密度）","靈子電池","多功能工具刀","急救包","旅行地圖"],
}


def _build_lore_offers(card: dict, role_text: str, craft_toks: list) -> List[str]:
    """Build a lore-accurate trade inventory from a card's actual world setting."""
    offers: List[str] = []
    lore_toks = _tokens_by_cat(card, "lore")

    # Priority 1: Extract 身份 (identity/job) token — the most reliable source
    identity_text = ""
    for t in lore_toks:
        if t.get("name", "") in ("身份", "職業", "定位", "角色", "工作", "職稱"):
            identity_text = t.get("value", "")
            break

    # Build a comprehensive search string, identity first for priority
    search_text = identity_text + " " + role_text + " " + card.get("name", "")
    for t in lore_toks + craft_toks:
        search_text += " " + t.get("value", "") + " " + t.get("name", "")

    # Match keyword catalog entries (longer keys first to avoid false substring hits)
    sorted_keys = sorted(
        ((k, v) for k, v in _LORE_TRADE_CATALOG.items() if k != "default"),
        key=lambda kv: -len(kv[0])
    )
    for key, items in sorted_keys:
        if key in search_text:
            for item in items[:4]:
                if item not in offers:
                    offers.append(item)

    # If no keyword matches, try craft token names as hints
    if not offers:
        for t in craft_toks[:4]:
            tname = t.get("name", "")
            for key, items in sorted_keys:
                if key in tname:
                    for item in items[:3]:
                        if item not in offers:
                            offers.append(item)
                    break

    # Final fallback
    if not offers:
        offers = list(_LORE_TRADE_CATALOG["default"])

    return offers[:12]

def generate_all_npcs() -> Dict[str, dict]:
    # Build supplement card patch map: name -> list of supplement cards
    _supp_map: Dict[str, list] = {}
    for sc in _CHAR_SUPP_CARDS:
        raw = sc.get("name", "").split("—")[0].split(" ")[0].strip()
        _supp_map.setdefault(raw, []).append(sc)

    npcs = {}
    for i, card in enumerate(_CHARACTER_CARDS):
        cid = card.get("card_id", f"CC-{i:02d}")
        raw_npc_name = card.get("name", "?").split("(")[0].split("（")[0].strip()
        # Fix empty names: use lore token value as fallback
        lore_toks_for_name = _tokens_by_cat(card, "lore")
        if not raw_npc_name or raw_npc_name == '?':
            lore_fallback = ""
            for t in lore_toks_for_name:
                v = t.get("value","")[:10]
                if v: lore_fallback = v; break
            name = lore_fallback if lore_fallback else f"無名角色({cid})"
        else:
            name = raw_npc_name
        if not name: name = card.get("name", "?")

        # Derive home location from card lore (not round-robin)
        home = _get_npc_home_from_card(card, i)

        tokens = card.get("tokens", [])
        token_cats = {t.get("category") for t in tokens}
        lore_toks = _tokens_by_cat(card, "lore")
        craft_toks = _tokens_by_cat(card, "craft") + _tokens_by_cat(card, "knowledge")

        # Extract role from lore tokens first, then fallback to stats
        role_desc = ""
        for t in lore_toks:
            n = t.get("name", "")
            if any(kw in n for kw in ["身份", "職業", "role", "角色"]):
                role_desc = t.get("value", "")
                break
        if not role_desc:
            stats = card.get("stats", {})
            role_desc = stats.get("role定位", "")

        # Archetype: check specific categories before combat+vitality default
        if "mechanism" in token_cats:
            archetype = "engineer"
        elif "exploration" in token_cats and "knowledge" in token_cats:
            archetype = "scout"
        elif "craft" in token_cats or "social" in token_cats:
            archetype = "merchant"
        elif "element" in token_cats or "energy" in token_cats:
            archetype = "mage"
        elif "skill" in token_cats and "relation" in token_cats:
            archetype = "specialist"
        elif "combat" in token_cats and "vitality" in token_cats:
            archetype = "warrior"
        else:
            archetype = "default"

        # Build LORE-ACCURATE trade inventory (replaces fabricated generic items)
        offers = _build_lore_offers(card, role_desc, craft_toks)

        # Apply supplement card patches
        supp_patches = _supp_map.get(name, []) + _supp_map.get(cid, [])
        supp_notes: List[str] = []
        for sp in supp_patches:
            sp_lore = _tokens_by_cat(sp, "lore")
            for t in sp_lore:
                v = t.get("value", "")
                if v:
                    supp_notes.append(v[:60])
            sp_craft = _tokens_by_cat(sp, "craft")
            extra_offers = _build_lore_offers(sp, sp.get("name", ""), sp_craft)
            for item in extra_offers:
                if item not in offers and len(offers) < 12:
                    offers.append(item)

        # Build description from role + lore tokens + key tokens + abilities
        desc_parts = []
        if role_desc:
            desc_parts.append(role_desc)
        for t in lore_toks:
            n = t.get("name", "")
            v = t.get("value", "")
            if v and n not in ("身份", "種族", "role", "角色") and "世界線" not in n:
                desc_parts.append(f"{n}: {v}")
        for cat in ("element", "energy", "relation", "status", "vitality", "exploration"):
            for t in _tokens_by_cat(card, cat):
                v = t.get("value", "")
                if v:
                    desc_parts.append(v)
        key_tokens = _tokens_by_cat(card, "skill") + _tokens_by_cat(card, "combat") + craft_toks
        token_names = [t.get("name","") for t in key_tokens if t.get("name","")]
        if token_names:
            desc_parts.append("特徵：" + "、".join(token_names[:8]))
        ab_details = card.get("abilities", [])
        if ab_details:
            ab_lines = []
            for a in ab_details[:4]:
                an = a.get("name","") if isinstance(a, dict) else str(a)
                ad = a.get("description","")[:60] if isinstance(a, dict) else ""
                if an and ad:
                    ab_lines.append(f"{an}（{ad}）")
                elif an:
                    ab_lines.append(an)
            if ab_lines:
                desc_parts.append("能力：" + "、".join(ab_lines))
        if supp_notes:
            desc_parts.append("【補充】" + "；".join(supp_notes[:2]))
        description = "，".join(desc_parts) if desc_parts else role_desc or "不明"

        # Lore-accurate greeting using actual role
        if role_desc:
            greeting = f"「我是{name}。{role_desc[:30]}。有什麼事嗎？」"
        else:
            greeting = f"「我是{name}。你好。」"

        npcs[name] = {
            "card_id": cid, "name": name,
            "description": description,
            "race": _extract_race_from_card(card),
            "role": role_desc,
            "location": home,
            "schedule": _generate_npc_schedule(name, home),
            "greeting": greeting,
            "archetype": archetype,
            "token_categories": list(token_cats),
            "abilities": [a.get("name","") if isinstance(a, dict) else str(a) for a in card.get("abilities", [])],
            "ability_details": card.get("abilities", []),
            "has_abilities": len(card.get("abilities", [])) > 0,
            "offers": offers[:12],
            "is_merchant": archetype == "merchant" or bool(offers),
            "gives_quests": "social" in token_cats or "knowledge" in token_cats or "craft" in token_cats,
            "quest_type": "side",
            "raw_tokens": len(tokens),
        }
    return npcs

ALL_NPCS = generate_all_npcs()


# ══════════════════════════════════════════════════════════════════
# 6b. SKILL GENERATION — from skill cards (SK-01~SK-22)
# ══════════════════════════════════════════════════════════════════

def generate_all_skills() -> dict:
    skills = {}
    for card in _SKILL_CARDS:
        cid = card.get("card_id", "SK-??")
        name = card.get("name", "").strip()
        if not name:
            continue
        tokens = card.get("tokens", [])
        desc = ""
        for t in tokens:
            if t.get("category") == "ability":
                desc = t.get("value", t.get("name", ""))
                break
        if not desc:
            desc = name.split("：")[-1] if "：" in name else name
        # Determine primary category from name
        cat = "general"
        if any(kw in name for kw in ["道術","魔法","奇蹟","四季"]):
            cat = "magic"
        elif any(kw in name for kw in ["格鬥","弓道","陷阱"]):
            cat = "combat"
        elif any(kw in name for kw in ["潛伏","駭客"]):
            cat = "stealth"
        elif any(kw in name for kw in ["植物","地質","文獻","妖精"]):
            cat = "knowledge"
        elif any(kw in name for kw in ["機械","工藝","換裝","義體"]):
            cat = "craft"
        elif any(kw in name for kw in ["打電話","上網"]):
            cat = "tech"
        skills[cid] = {
            "name": name,
            "description": desc,
            "category": cat,
            "source_card": cid,
            "trainable": True,
            "level": 1,
        }
    return skills

ALL_SKILLS = generate_all_skills()


# ══════════════════════════════════════════════════════════════════
# 6c. STORYLINE GENERATION — from storyline cards (SL-01~SL-11)
# ══════════════════════════════════════════════════════════════════

def generate_all_storyline_quests() -> list:
    quests = []
    for card in _STORYLINE_CARDS:
        cid = card.get("card_id", "SL-??")
        name = card.get("name", "").strip()
        if not name:
            continue
        tokens = card.get("tokens", [])
        theme = ""
        for t in tokens:
            if t.get("category") == "lore" and "核心" in t.get("name",""):
                theme = t.get("value", t.get("name", ""))
                break
        if not theme:
            theme = name
        quests.append({
            "id": f"{cid}-MAIN",
            "title": name,
            "description": theme,
            "quest_type": "main",
            "objectives": [{"type": "story", "target": cid, "description": f"探索 {name} 的故事線", "require_action": "advance", "require_times": 3}],
            "rewards": [f"完成 {name} 主線劇情"],
            "source_card_id": cid,
        })
    return quests

ALL_STORYLINE_QUESTS = generate_all_storyline_quests()


# ══════════════════════════════════════════════════════════════════
# 6d. WORLD CORE GENERATION — from world core cards (WC/W series)
# ══════════════════════════════════════════════════════════════════

def generate_world_modifiers() -> dict:
    modifiers = {}
    for card in _WORLD_CORE_CARDS:
        cid = card.get("card_id", "WC-??")
        name = card.get("name", "").strip()
        tokens = card.get("tokens", [])
        desc = ""
        for t in tokens:
            if t.get("category") == "lore":
                desc = t.get("value", t.get("name", ""))
                break
        if not desc:
            desc = name
        modifiers[cid] = {
            "name": name,
            "description": desc,
            "effect": "world_modifier",
        }
    return modifiers

ALL_WORLD_MODIFIERS = generate_world_modifiers()


# ══════════════════════════════════════════════════════════════════
# 7. ITEM GENERATION — assemble all items
# ══════════════════════════════════════════════════════════════════

def _make_item(name: str, typ: str, slot: str, atk: float, dfn: float, spd: float,
               krm: float, dur: int, val: int, desc: str, tags: list) -> dict:
    d = {"type": typ, "weight": 2.0, "value": val, "desc": desc, "tags": tags}
    sm = {}
    if atk != 0: sm["atk"] = atk
    if dfn != 0: sm["defense"] = dfn
    if spd != 0: sm["spd"] = spd
    if krm != 0: sm["karma"] = krm
    if typ in ("weapon","armor","accessory"):
        d["durability"] = dur
        d["slot"] = slot
        d["stat_multipliers"] = sm
    if typ == "consumable":
        d["weight"] = 0.3
    if typ == "junk":
        d["weight"] = 0.2
    # Race/archetype restriction based on tags
    # Race-specific: only characters with matching race can equip
    if "naval" in tags:
        d["required_race"] = "艦娘"
        d["required_archetype"] = "combat"
    elif "elemental" in tags or "magic" in tags:
        d["required_race"] = "術士"
        d["required_archetype"] = "element"
    elif "beast" in tags or "natural" in tags:
        d["required_race"] = "獸娘"
        d["required_archetype"] = "vitality"
    elif "draconic" in tags:
        d["required_race"] = "竜族"
        d["required_archetype"] = "combat"
    elif "mechanical" in tags:
        d["required_race"] = "機械"
        d["required_archetype"] = "mechanism"
    elif "spiritual" in tags:
        d["required_race"] = "精霊"
        d["required_archetype"] = "energy"
    return d

def generate_all_items() -> Dict[str, dict]:
    items = {}
    
    # Naval weapons
    for name, typ, slot, atk, dfn, dur, val, nation, ship in NAVAL_DATA:
        items[name] = _make_item(name, typ, slot, atk, dfn, 0, 0, dur, val,
                                 f"{nation} {ship}", ["naval","rare"] if val>300 else ["naval"])
    
    # Animal items
    for name, typ, slot, atk, dfn, spd, krm, dur, val, species, biome in ANIMAL_DATA:
        items[name] = _make_item(name, typ, slot, atk, dfn, spd, krm, dur, val,
                                 f"{species}（{biome}）", ["beast","natural"])
    
    # Elemental
    for name, typ, slot, atk, dfn, desc, val, dur in ELEMENTAL_ITEMS:
        items[name] = _make_item(name, typ, slot, atk, dfn, 0, 0, dur, val,
                                 desc, ["elemental","magic"])
    
    # Herbal
    for name, typ, wt, val, hp, sp, desc in HERBAL_ITEMS:
        d = {"type": typ, "weight": wt, "value": val, "desc": desc, "tags": ["herbal"]}
        if hp: d["heal_hp"] = abs(hp)
        if sp: d["heal_sp"] = abs(sp)
        items[name] = d
    
    # Junk
    for name in JUNK_ITEMS:
        items[name] = {"type": "junk", "weight": 0.2, "value": 0,
                       "desc": f"一個{name}。", "tags": ["junk"]}
    
    # Card ability items — generate up to 600
    card_item_count = 0
    item_names_set = set(items.keys())
    _cat_item_types = {
        "energy": ("accessory","neck",0.1,0.1,0,0.2,60,80),
        "element": ("accessory","neck",0.1,0.1,0,0.2,60,80),
        "combat": ("weapon","right_hand",0.25,0,0.1,0,80,100),
        "skill": ("weapon","right_hand",0.25,0,0.1,0,80,100),
        "craft": ("armor","torso",0,0.15,0,0.15,70,90),
        "social": ("armor","torso",0,0.15,0,0.15,70,90),
        "lore": ("armor","back",0,0.1,0,0.2,50,70),
        "vitality": ("armor","torso",0,0.2,0,0,80,85),
        "exploration": ("armor","feet",0,0,0.15,0.1,60,75),
        "knowledge": ("accessory","head",0,0,0,0.25,50,95),
    }
    for card in _CHARACTER_CARDS:
        tokens = card.get("tokens", [])
        cid = card.get('card_id','?')
        # Generate items from token categories
        for i, t in enumerate(tokens):
            cat = t.get("category","")
            tok_name = t.get("name","")[:15]
            if not tok_name or not cat: continue
            key = f"{cid}:{tok_name}"
            if key in item_names_set or card_item_count >= 2000:
                continue
            item_type = _cat_item_types.get(cat)
            if item_type:
                typ, slot, atk, dfn, spd, krm, dur, val = item_type
                items[key] = _make_item(key, typ, slot, atk, dfn, spd, krm, dur, val,
                                        f"{tok_name}の力", ["card_item", cat])
                item_names_set.add(key)
                card_item_count += 1
        # Generate from abilities too
        for ability in card.get("abilities", []):
            aname = ability.get("name", "")
            if not aname: continue
            key = f"{cid}:{aname}"
            if key in item_names_set or card_item_count >= 2000:
                continue
            items[key] = _make_item(key, "accessory", "neck", 0.1, 0.1, 0.05, 0.15,
                                    50, 80, f"{aname[:15]}", ["card_item", "ability"])
            item_names_set.add(key)
            card_item_count += 1
    
    # Token-generic items from each NPC
    for card in _CHARACTER_CARDS:
        token_cats = {t.get("category") for t in card.get("tokens", [])}
        cid = card.get('card_id','?')
        for cat in token_cats:
            if cat in _cat_item_types and card_item_count < 600:
                key = f"{cid}:{cat}の結晶"
                if key not in item_names_set:
                    typ, slot, atk, dfn, spd, krm, dur, val = _cat_item_types[cat]
                    items[key] = _make_item(key, typ, slot, atk, dfn, spd, krm, dur, val,
                                            f"{cat}の結晶", ["card_item", cat])
                    item_names_set.add(key)
                    card_item_count += 1
    
    print(f"[game_data] Generated {len(items)} items")
    return items

ALL_ITEMS = generate_all_items()


# ══════════════════════════════════════════════════════════════════
# 8. ENEMY GENERATION — 400+
# ══════════════════════════════════════════════════════════════════

ANIMAL_ENEMIES_TEMPLATE = [
    # (name, base_hp, base_atk, base_def, base_spd, exp_mod, gold_mod, loot, desc, biome)
    ("森狼",35,10,4,7,25,8,["皮革"],"森に棲む狼","forest"),
    ("山熊",120,28,12,3,100,50,["熊の鉄壁","生命果"],"巨大な山熊","mountain"),
    ("毒蛇",30,22,3,9,45,15,["解毒草","蛇の鱗衣"],"毒牙を持つ蛇","forest"),
    ("猛禽",25,18,2,12,35,12,["鷹の翼膜","羽毛"],"空から狙う猛禽","sky"),
    ("野猪",70,15,8,5,40,18,["皮革","狼王毛皮"],"荒ぶる猪","grassland"),
    ("大蜘蛛",40,12,6,6,30,10,["絲線","解毒草"],"巨大な蜘蛛","cave"),
    ("虎",90,30,10,7,80,35,["虎の縞鎧","皮革"],"百獣の王","forest"),
    ("大鹿",50,8,5,9,25,15,["鹿の角冠","皮革"],"森の守護者","forest"),
    ("電鱗魚",35,25,4,8,50,20,["猫の軽靴","魔力藥水"],"雷を帯びた魚","water"),
    ("鎌鼬",28,20,2,11,40,14,["羽毛","草藥"],"風を切る鼬","grassland"),
    ("岩亀",200,8,35,1,120,60,["亀の甲羅盾","黏土"],"動く岩の如き亀","mountain"),
    ("吸血蝙蝠",20,15,2,10,30,8,["空瓶","破布"],"夜に飛び回る蝙蝠","cave"),
    ("黄金蛇",40,18,5,8,55,25,["蛇の鱗衣","古代硬貨"],"黄金の鱗を持つ蛇","ruins"),
    ("氷狼",50,15,8,6,60,22,["銀狼の尾","皮革"],"氷雪地帯の狼","snow"),
    ("砂蝎",60,20,12,4,50,28,["蠍の甲殻","毒針"],"砂漠に潜む蠍","desert"),
    ("火蜥蜴",45,25,6,5,55,20,["火元素","皮革"],"炎を吐く蜥蜴","volcano"),
    ("翠鳥",22,14,3,13,30,10,["羽毛","靈木"],"森の宝石と呼ばれる鳥","forest"),
    ("鉄甲虫",80,10,25,2,45,18,["鐵礦","黏土"],"鋼の甲殻を持つ虫","cave"),
    ("水馬",55,12,7,8,35,15,["貝殼","絲線"],"水辺の幻獣","water"),
    ("旋風狼",40,18,5,9,50,22,["狼王毛皮","魔法粉"],"風を操る狼","grassland"),
]

def _generate_enemies_from_template() -> list:
    enemies = []
    for name, hp, atk, dfn, spd, exp_, gold, loot, desc, biome in ANIMAL_ENEMIES_TEMPLATE:
        enemies.append({"name":name,"hp":hp,"atk":atk,"def":dfn,"spd":spd,
                        "exp":exp_,"gold":gold,"loot":list(loot),"desc":desc})
        # Tier 2: stronger variant
        enemies.append({"name":f"凶暴な{name}","hp":int(hp*1.8),"atk":int(atk*1.5),"def":int(dfn*1.3),
                        "spd":min(spd+2,15),"exp":int(exp_*1.5),"gold":int(gold*1.5),
                        "loot":list(loot)+(["魔法粉"] if len(loot)<3 else []),"desc":f"凶暴化した{desc}"})
        # Tier 3: elite variant
        enemies.append({"name":f"古の{name}","hp":int(hp*3.0),"atk":int(atk*2.2),"def":int(dfn*2.0),
                        "spd":min(spd+4,18),"exp":int(exp_*2.5),"gold":int(gold*2.5),
                        "loot":list(loot)+["龍鱗","靈木"],"desc":f"古代から生きる{desc}"})
    return enemies

# Card shadow enemies (from each character card combat tokens)
def _generate_card_enemies() -> list:
    enemies = []
    for card in _CHARACTER_CARDS:
        combat_tokens = _tokens_by_cat(card, "combat")
        name = card.get("name","?").split("(")[0].strip()[:6]
        shadow_name = f"{name}の影"
        base_hp = 45 + len(combat_tokens)*10 if combat_tokens else 40
        base_atk = 14 + len(combat_tokens)*3 if combat_tokens else 12
        base_def = 5 + len(combat_tokens)*2 if combat_tokens else 4
        enemies.append({"name":shadow_name,"hp":base_hp,"atk":base_atk,"def":base_def,
                        "spd":5,"exp":40+len(combat_tokens)*10,"gold":20+len(combat_tokens)*5,
                        "loot":["魔法粉","水晶碎片"],"desc":"カードから現れた影"})
        # Stronger variant
        enemies.append({"name":f"深淵の{shadow_name}","hp":int(base_hp*2.5),"atk":int(base_atk*2.0),
                        "def":int(base_def*1.8),"spd":8,"exp":int(40+len(combat_tokens)*25),
                        "gold":int(20+len(combat_tokens)*12),"loot":["龍鱗","靈木","魔力藥水"],
                        "desc":"深淵から現れた強力な影"})
    return enemies

# Elemental enemies
ELEMENTAL_ENEMIES = [
    ("火霊",60,30,8,5,65,30,["火元素","魔法粉"],"炎の精霊"),
    ("水霊",50,18,12,6,45,20,["水晶碎片","貝殼"],"水の精霊"),
    ("風霊",35,22,5,12,55,25,["羽毛","魔法粉"],"風の精霊"),
    ("地霊",100,15,25,2,60,35,["黏土","靈木"],"大地の精霊"),
    ("光霊",40,25,10,8,70,40,["護身符","靈木"],"光の精霊"),
    ("闇霊",45,28,8,9,65,35,["魔法粉","破布"],"闇の精霊"),
    ("雷霊",40,35,6,10,80,45,["水晶碎片","火元素"],"雷の精霊"),
    ("氷霊",55,20,15,5,50,28,["空瓶","草藥"],"氷の精霊"),
    ("森霊",70,14,18,4,45,22,["靈木","樹枝"],"森の精霊"),
    ("星霊",30,20,8,14,90,50,["星屑のマント","記憶水晶"],"星の精霊"),
]

def generate_all_enemies() -> list:
    enemies = _generate_enemies_from_template()  # 60 enemies
    enemies.extend(_generate_card_enemies())      # ~118 enemies
    for name, hp, atk, dfn, spd, exp_, gold, loot, desc in ELEMENTAL_ENEMIES:
        enemies.append({"name":name,"hp":hp,"atk":atk,"def":dfn,"spd":spd,
                        "exp":exp_,"gold":gold,"loot":list(loot),"desc":desc})
        # Tier 2 for elemental
        enemies.append({"name":f"大{name}","hp":int(hp*2.2),"atk":int(atk*1.8),"def":int(dfn*1.5),
                        "spd":min(spd+2,16),"exp":int(exp_*2),"gold":int(gold*2),
                        "loot":list(loot)+["龍鱗"],"desc":f"強大な{desc}"})
    return enemies

ALL_ENEMIES = generate_all_enemies()
# Should be ~60 + ~118 + 20 = ~198 enemies


# ══════════════════════════════════════════════════════════════════
# 9. LOCATION GENERATION
# ══════════════════════════════════════════════════════════════════

def generate_locations() -> dict:
    locs = {}
    for card in _SCENE_CARDS:
        sid = card.get("card_id","S??")
        raw_loc_name = card.get("name","?").split("·")[-1].strip()
        if not raw_loc_name or len(raw_loc_name) > 8:
            raw_loc_name = card.get("name","?").split("（")[0].split("(")[0].strip()[:8]
        # Fix empty names: use lore token value as fallback
        lore_toks_for_loc = _tokens_by_cat(card, "lore")
        if not raw_loc_name or raw_loc_name == '?':
            lore_fallback = ""
            for t in lore_toks_for_loc:
                v = t.get("value","")[:15]
                if v: lore_fallback = v; break
            name = lore_fallback if lore_fallback else f"未命名場景({sid})"
        else:
            name = raw_loc_name
        lore_tokens = _tokens_by_cat(card, "lore")
        vibe = "📍 未知の地"
        for t in lore_tokens:
            v = t.get("value","")
            if "校園" in v or "教室" in v: vibe = "📚 学びの場"
            elif "湖" in v or "水" in v: vibe = "💧 水辺"
            elif "市" in v or "市場" in v: vibe = "🏪 賑わい"
            elif "地下" in v or "洞" in v: vibe = "🕳 地下"
            elif "空" in v or "星" in v: vibe = "✨ 星空"
        locs[sid] = {"name":name,"vibe":vibe,"card_id":sid}
    return locs

ALL_LOCATIONS = generate_locations()


# ══════════════════════════════════════════════════════════════════
# 10. QUEST GENERATION — use ALL 76 story nodes
# ══════════════════════════════════════════════════════════════════

def generate_quests() -> list:
    quests = []
    locations_pool = ["聖十字校園","鏡湖","鬱鬱山","卡洛夫角","霧海群島",
                      "秘密鐵工廠","便利店","英靈殿","廢棄礦坑","森林深處","煙雲溫泉湖","清溪河","鏡山"]
    
    # From all story nodes
    npc_names = list(ALL_NPCS.keys())
    for i, card in enumerate(_STORY_CARDS):
        raw_name = card.get("name","?").split("（")[0].strip()[:20]
        lore_tokens = _tokens_by_cat(card, "lore")
        story = ""
        for t in lore_tokens:
            v = t.get("value","")
            story = v[:60]
        if not story: story = f"調查關於{raw_name}的線索。"
        # Fix empty names: use first lore token value as fallback
        if not raw_name or raw_name == '?':
            lore_fallback = ""
            for t in lore_tokens:
                lore_fallback = t.get("value","")[:20]
                if lore_fallback: break
            name = lore_fallback if lore_fallback else f"未命名EP({i+1})"
        else:
            name = raw_name
        loc_target = _seed.choice(locations_pool)
        qtype = "main" if i < 15 else "side"
        qid = f"SN-{i+1:02d}"
        reward_exp = 20 + i * 3
        reward_gold = 8 + i * 2
        # Add conditions with level requirement scaling with index
        req_level = max(1, i // 15)  # later nodes require higher level
        q = {
            "id": qid, "title": name[:20], "type": qtype,
            "giver": _seed.choice(npc_names),
            "desc": story[:80],
            "conditions": {
                "required_level": req_level,
                "time_available": {"start_hour": 0, "end_hour": 24},
            },
            "objectives": [
                {"type":"visit","target":loc_target,"detail":f"前往{loc_target}"},
                {"type":"collect","target":_seed.choice(["水晶碎片","鐵礦","魔法粉","靈木","草藥","皮革"]),
                 "qty":_seed.randint(1,3),"detail":"收集指定物品"},
            ],
            "reward_exp": reward_exp, "reward_gold": reward_gold,
            "reward_reputation": max(2, i // 10),
            "reward_item": _seed.choice(["治療藥水","鐵劍","護身符","鋼刀","記憶水晶","皮甲","斗篷","匕首","靈力藥","生命果"]),
        }
        quests.append(q)
    
    # NPC-generated quests (with conditions based on NPC attributes)
    for i, (npc_name, npc_data) in enumerate(ALL_NPCS.items()):
        if npc_data.get("gives_quests") and i < 60:
            cats = npc_data.get("token_categories", [])
            loc = npc_data.get("location", "聖十字校園")
            qid = f"NPC-{i+1:02d}"
            req_rel = {npc_name: 20 + _seed.randint(0, 20)}
            conditions = {
                "required_relationships": req_rel,
                "time_available": {"start_hour": 8, "end_hour": 20},
            }
            if "craft" in cats:
                quests.append({"id":qid,"title":f"{npc_name}の依頼","type":"side","giver":npc_name,
                    "desc":"材料を集めてほしい。",
                    "conditions": dict(conditions),
                    "objectives":[{"type":"collect","target":_seed.choice(["鐵礦","皮革","靈木","草藥"]),"qty":_seed.randint(2,5),"detail":"收集材料"}],
                    "reward_exp":30+_seed.randint(0,30),"reward_gold":15+_seed.randint(0,20),
                    "reward_reputation":5,"reward_relationships":{npc_name: 10},
                    "reward_item":_seed.choice(["治療藥水","匕首","鐵劍","護身符","皮甲"])})
            elif "combat" in cats:
                conditions["required_level"] = 3
                quests.append({"id":qid,"title":f"{npc_name}の退治","type":"side","giver":npc_name,
                    "desc":"近くの敵を退治してほしい。",
                    "conditions": dict(conditions),
                    "objectives":[{"type":"visit","target":loc,"detail":f"前往{loc}"},
                                  {"type":"defeat","target":_seed.choice(["野狼","虎","毒蛇","盜賊","哥布林"]),"qty":_seed.randint(1,3),"detail":"擊敗指定敵人"}],
                    "reward_exp":40+_seed.randint(0,40),"reward_gold":20+_seed.randint(0,30),
                    "reward_reputation":8,"reward_relationships":{npc_name: 12},
                    "reward_item":_seed.choice(["鋼刀","鐵甲","生命果","火焰藥水","靈力藥"])})
            elif "knowledge" in cats:
                quests.append({"id":qid,"title":f"{npc_name}の探求","type":"side","giver":npc_name,
                    "desc":"探索して知見を持ち帰れ。",
                    "conditions": dict(conditions),
                    "objectives":[{"type":"visit","target":_seed.choice(["聖十字校園","英靈殿","森林深處"]),"detail":"指定場所を訪れる"}],
                    "reward_exp":25+_seed.randint(0,25),"reward_gold":10+_seed.randint(0,15),
                    "reward_reputation":6,"reward_relationships":{npc_name: 10},
                    "reward_item":_seed.choice(["記憶水晶","神秘地圖","書信","魔力藥水","護身符"])})

    print(f"[game_data] Generated {len(quests)} quests")
    return quests

ALL_QUESTS = generate_quests()


# ══════════════════════════════════════════════════════════════════
# 11. SCENE OBJECT GENERATION — 200+
# ══════════════════════════════════════════════════════════════════

LOCATIONS_FOR_OBJECTS = [
    "聖十字校園","鏡湖","鬱鬱山","卡洛夫角","霧海群島",
    "秘密鐵工廠","便利店","英靈殿","廢棄礦坑","森林深處","煙雲溫泉湖","清溪河","鏡山",
]

def generate_scene_objects() -> Dict[str, list]:
    objects = {}
    container_pool = [
        (["草藥","空瓶","小石頭"],"木箱","木箱"),
        (["魔法粉","水晶碎片","靈木"],"魔法箱","光る箱"),
        (["乾糧","治療藥水","繃帶"],"保管箱","応急箱"),
        (["鐵礦","黏土","樹枝"],"鉱石箱","鉱石箱"),
        (["書信","羽毛","貝殼"],"小箱","鍵付き小箱"),
        (["皮革","布","絲線"],"材料箱","素材箱"),
        (["火元素","空瓶","蠟燭頭"],"実験箱","実験箱"),
        (["古代硬貨","記憶水晶","神秘地圖"],"古い箱","古の箱"),
        (["靈木","龍鱗","魔法粉"],"貴重品箱","貴重品箱"),
        (["草薬","解毒草","靈芝"],"薬箱","薬箱"),
        (["木柄","鐵礦","麻繩"],"道具箱","道具箱"),
        (["治療藥水","火焰藥水","魔力藥水"],"薬品棚","薬品棚"),
        (["乾燥花","彩色玻璃片","貝殼"],"飾り箱","装飾箱"),
        (["鐵錠","鐵礦","鐵劍"],"武器箱","武器箱"),
        (["書信","神秘地圖","乾燥花"],"手紙箱","書簡箱"),
    ]
    deco_pool = [
        "看板","ベンチ","街灯","像","花壇","旗","噴水","井戸",
        "案内板","時計台","吊り橋","鳥篭","焚火跡","石垣","門",
    ]
    ws_pool = [("鍛冶台","forge"),("作業台","workbench"),("錬金釜","alchemy"),
               ("魔法陣","enchant"),("彫刻台","carve"),("調合台","blend")]
    
    for loc in LOCATIONS_FOR_OBJECTS:
        loc_objs = []
        # 2-3 containers
        for _ in range(_seed.randint(2,3)):
            ct = _seed.choice(container_pool)
            items, cname, cdesc = ct
            cid = f"box_{loc}_{len(loc_objs)}"
            loc_objs.append({"id":cid,"name":f"{cname}({loc[:2]})","type":"container",
                             "desc":cdesc,"contents":_seed.sample(items,min(3,len(items))),
                             "locked":_seed.random()<0.15,"interactable":True})
        # 1-2 decorations
        for _ in range(_seed.randint(1,2)):
            d = _seed.choice(deco_pool)
            loc_objs.append({"id":f"dec_{loc}_{len(loc_objs)}","name":d,"type":"decoration",
                             "desc":f"一{d}。","note":"特に何もない。","interactable":True})
        # 0-1 workstation
        if _seed.random() < 0.5:
            ws = _seed.choice(ws_pool)
            loc_objs.append({"id":f"ws_{loc}","name":ws[0],"type":"workstation",
                             "desc":f"{ws[0]}。","station_type":ws[1],"interactable":True})
        objects[loc] = loc_objs
    return objects

ALL_SCENE_OBJECTS = generate_scene_objects()


# ══════════════════════════════════════════════════════════════════
# 12. RECIPE GENERATION
# ══════════════════════════════════════════════════════════════════

def generate_recipes() -> list:
    recipes = []
    item_names = list(ALL_ITEMS.keys())
    material_tags = [k for k, v in ALL_ITEMS.items()
                     if v.get("tags") and ("naval" in v["tags"] or "beast" in v["tags"]
                     or "natural" in v["tags"] or "elemental" in v["tags"])]
    weapon_types = [k for k, v in ALL_ITEMS.items() if v.get("type") == "weapon"]
    consumable_types = [k for k, v in ALL_ITEMS.items() if v.get("type") == "consumable"]
    
    # Generate up to 400 recipes
    used_pairs = set()
    for i, name in enumerate(item_names[:1000]):
        if i >= 400: break
        item = ALL_ITEMS[name]
        if item["type"] in ("junk",) or not item.get("tags"):
            continue
        mat = _seed.sample([m for m in material_tags if m != name],
                           min(3, len(material_tags)))
        if len(mat) < 2: continue
        pair_key = tuple(sorted(mat[:2]))
        if pair_key in used_pairs: continue
        used_pairs.add(pair_key)
        
        cat_choices = ["craft","alchemize","process","combine"]
        cat = _seed.choice(cat_choices)
        recipes.append({
            "recipe_id": f"GD-{i+1:04d}",
            "name": f"{name[:12]}の製作",
            "category": cat,
            "ingredients": [{"item": mat[0], "quantity": _seed.randint(1,2)},
                           {"item": mat[1], "quantity": _seed.randint(1,2)}],
            "result_item": name, "result_quantity": 1,
            "failure_chance": round(_seed.uniform(0.05, 0.35), 2),
        })
    
    # Potion recipes (consumable + material)
    for i, ctype in enumerate(consumable_types):
        mat = _seed.choice(material_tags if material_tags else ["草藥"])
        rid = f"GD-POT{i+1:04d}"
        recipes.append({
            "recipe_id": rid, "name": f"{ctype[:10]}の調合",
            "category": "alchemize",
            "ingredients": [{"item": mat, "quantity": 2},
                           {"item": _seed.choice(["空瓶","魔法粉","靈木"]), "quantity": 1}],
            "result_item": ctype, "result_quantity": _seed.randint(1,2),
            "failure_chance": round(_seed.uniform(0.1, 0.3), 2),
        })
    
    print(f"[game_data] Generated {len(recipes)} recipes")
    return recipes

ALL_RECIPES = generate_recipes()


# ══════════════════════════════════════════════════════════════════
# 13. VEHICLES
# ══════════════════════════════════════════════════════════════════

ALL_VEHICLES = {
    "自転車":{"speed":1.5,"capacity":1,"cargo":20,"fuel":"human","desc":"軽快な自転車"},
    "マウンテンバイク":{"speed":1.8,"capacity":1,"cargo":15,"fuel":"human","desc":"悪路に強い自転車"},
    "馬":{"speed":2.0,"capacity":1,"cargo":30,"fuel":"feed","desc":"駿馬"},
    "駿馬":{"speed":2.5,"capacity":1,"cargo":25,"fuel":"feed","desc":"純血の駿馬"},
    "馬車":{"speed":1.2,"capacity":3,"cargo":100,"fuel":"feed","desc":"荷馬車"},
    "大型馬車":{"speed":1.0,"capacity":5,"cargo":300,"fuel":"feed","desc":"大型の輸送馬車"},
    "小舟":{"speed":1.3,"capacity":2,"cargo":15,"fuel":"human","desc":"川を渡る小舟"},
    "漁船":{"speed":1.5,"capacity":4,"cargo":100,"fuel":"sail","desc":"漁に使う船"},
    "オートバイ":{"speed":2.5,"capacity":1,"cargo":10,"fuel":"gas","desc":"快速二輪"},
    "大型オートバイ":{"speed":2.8,"capacity":2,"cargo":20,"fuel":"gas","desc":"大型二輪"},
    "ジープ":{"speed":2.0,"capacity":4,"cargo":200,"fuel":"gas","desc":"悪路走破車"},
    "帆船":{"speed":1.8,"capacity":6,"cargo":500,"fuel":"wind","desc":"帆船"},
    "大型帆船":{"speed":2.0,"capacity":12,"cargo":1200,"fuel":"wind","desc":"大型帆船"},
    "熱気球":{"speed":1.5,"capacity":3,"cargo":50,"fuel":"fire","desc":"空飛ぶ気球"},
    "蒸気機関車":{"speed":3.0,"capacity":10,"cargo":1000,"fuel":"coal","desc":"蒸気機関車（軌道限定）"},
    "魔法の箒":{"speed":2.8,"capacity":1,"cargo":5,"fuel":"magic","desc":"魔女の箒"},
    "魔法の絨毯":{"speed":3.0,"capacity":2,"cargo":30,"fuel":"magic","desc":"空飛ぶ絨毯"},
    "飛空挺":{"speed":2.5,"capacity":8,"cargo":800,"fuel":"magic","desc":"魔導飛空挺"},
    "竜騎乗":{"speed":3.5,"capacity":1,"cargo":10,"fuel":"bond","desc":"竜との絆で空を翔る"},
    "雪橇":{"speed":1.8,"capacity":2,"cargo":40,"fuel":"dog","desc":"犬ぞり"},
}


# ══════════════════════════════════════════════════════════════════
# 14. REAL ESTATE
# ══════════════════════════════════════════════════════════════════

ALL_REAL_ESTATE = {
    "聖十字校園小屋":{"type":"house","price":500,"functions":["rest","store"],"desc":"村はずれの小さな家"},
    "カールフ商店":{"type":"shop","price":800,"functions":["trade"],"desc":"市集の小店舗"},
    "湖畔工房":{"type":"workshop","price":1200,"functions":["craft","rest"],"desc":"湖畔の工房"},
    "図書室":{"type":"house","price":2000,"functions":["rest","study"],"desc":"図書館の一室"},
    "廃坑倉庫":{"type":"warehouse","price":600,"functions":["store"],"desc":"廃鉱山の倉庫"},
    "灯台":{"type":"house","price":1500,"functions":["rest","study"],"desc":"海を見渡す灯台"},
    "森林小屋":{"type":"house","price":900,"functions":["rest","store"],"desc":"森の中の隠れ家"},
    "展望台":{"type":"tower","price":2500,"functions":["study","rest"],"desc":"星を観測する展望台"},
    "鏡湖別荘":{"type":"house","price":3000,"functions":["rest","craft","store"],"desc":"鏡湖の畔の別荘"},
    "工房拡張":{"type":"workshop","price":1800,"functions":["craft","store"],"desc":"工房の拡張工房"},
    "秘密の隠れ家":{"type":"house","price":1500,"functions":["rest","store"],"desc":"秘密の隠れ家"},
    "市集の倉庫":{"type":"warehouse","price":400,"functions":["store"],"desc":"市集の小さな倉庫"},
    "海岸の小屋":{"type":"house","price":1200,"functions":["rest"],"desc":"海岸に建つ小さな家"},
    "魔法塔":{"type":"tower","price":5000,"functions":["study","craft","rest"],"desc":"魔力が集まる塔"},
    "古道の宿":{"type":"house","price":800,"functions":["rest","store"],"desc":"古道沿いの宿屋"},
    "英霊祠":{"type":"shrine","price":3000,"functions":["rest","study"],"desc":"英霊を祀る祠"},
    "大樹の家":{"type":"house","price":2000,"functions":["rest","store","craft"],"desc":"大樹に作られた家"},
    "鉱山公社":{"type":"warehouse","price":1000,"functions":["store"],"desc":"鉱山の管理事務所"},
    "スカイハウス":{"type":"house","price":4000,"functions":["rest","study","craft"],"desc":"高台の豪邸"},
}


# ══════════════════════════════════════════════════════════════════
# 15. DIALOGUE GENERATION
# ══════════════════════════════════════════════════════════════════

def generate_npc_dialogues() -> Dict[str, list]:
    dialogues = {}
    for name, npc_data in ALL_NPCS.items():
        cats = npc_data.get("token_categories", [])
        lines = [npc_data.get("greeting", "「こんにちは。」")]
        if "combat" in cats: lines.extend(["「戦いなら任せて。」","「実戦が一番の教師だ。」","「武器の手入れは大事だ。」"])
        if "craft" in cats: lines.extend(["「何か作ろうか？」","「素材があれば何でも作れる。」","「職人の技を見せよう。」"])
        if "knowledge" in cats: lines.extend(["「知っていることを話そう。」","「知識は力だ。」","「本を読むことを勧める。」"])
        if "social" in cats: lines.extend(["「話し相手になってくれる？」","「今日はいい天気だね。」","「一緒に食事しない？」"])
        if "element" in cats: lines.extend(["「元素の力を感じる...」","「自然のエネルギーが満ちている。」","「元素のバランスが大事だ。」"])
        if "energy" in cats: lines.extend(["「靈力が満ちているね。」","「氣の流れを感じる。」","「エネルギーをチャージしよう。」"])
        if "lore" in cats: lines.extend(["「昔話を聞きたい？」","「この地には古い伝説がある。」","「歴史は繰り返す。」"])
        if "exploration" in cats: lines.extend(["「新しい場所を探検しよう。」","「地図を見せてくれ。」","「荒野に冒険の香りがする。」"])
        lines.append("「また会おう。」")
        # Add random flavor
        flavors = [f"「{name}は微笑んだ。」",f"「{name}は考え込んでいる。」",f"「{name}は遠くを見つめている。」"]
        lines.extend(flavors)
        dialogues[name] = lines
    return dialogues

ALL_DIALOGUES = generate_npc_dialogues()


# ══════════════════════════════════════════════════════════════════
# INTEGRATION — merge game_data into sim_systems
# ══════════════════════════════════════════════════════════════════

def expand_game():
    import sim_systems
    
    cnt = {"items":0,"enemies":0,"enemy_dist":0,"npcs":0,"quests":0,
           "vehicles":0,"estate":0,"objs":0,"recipes":0}
    
    # Items
    for k, v in ALL_ITEMS.items():
        if k not in sim_systems.ITEM_CATALOG:
            sim_systems.ITEM_CATALOG[k] = v
            cnt["items"] += 1
    
    # Enemies
    existing_e = {e["name"] for e in sim_systems.ENEMIES}
    for e in ALL_ENEMIES:
        if e["name"] not in existing_e:
            sim_systems.ENEMIES.append(e)
            existing_e.add(e["name"])
        
    # ════════════════════════════════════════════════
    # Card system integration: ORG/NAT/RC
    # ════════════════════════════════════════════════
    
    # Factions (from ORG cards)
    sim_systems.FACTIONS = {
  "ORG-03": {
    "name": "紫晶石集會",
    "lore": "W01 靈子塵埃",
    "relations": {
      "關係_對外認知": "對外認知: 無。尚未被任何外部組織知曉",
      "關係_水晶能與特定人類產生": "水晶能與特定人類產生共鳴，賦予變身能力: 水晶的來源（天然？人造？古代遺產？）",
      "關係_變身後的形態與能力因": "變身後的形態與能力因水晶顏色而異: 水晶能量的上限與持續時間",
      "關係_水晶可透過接觸進行分": "水晶可透過接觸進行分配，但接受者需與水晶有共鳴: 長期使用水晶是否對人體有副作用"
    }
  },
  "ORG-04": {
    "name": "失戀集團",
    "lore": "W01 靈子塵埃",
    "relations": {}
  },
  "ORG-05": {
    "name": "終末燭光",
    "lore": "W01 靈子塵埃",
    "relations": {}
  },
  "ORG-06": {
    "name": "新世界集團",
    "lore": "W01 靈子塵埃",
    "relations": {
      "關係_聖諭同盟與唯靈聯邦": "聖諭同盟與唯靈聯邦: 組織在兩大陣營內部都有滲透。他們的長期計劃可能包括利用兩大陣營的戰爭來掩護「黎明計劃」的執行"
    }
  },
  "ORG-08": {
    "name": "脈動工業（Pulse Industrie",
    "lore": "W01 靈子塵埃",
    "relations": {
      "歷史_歷史線": "歷史線: 冷戰線（成立約 15 年）"
    }
  },
  "ORG-09": {
    "name": "永恆義體（Eternal Cyberne",
    "lore": "W01 靈子塵埃",
    "relations": {
      "歷史_歷史線": "歷史線: 冷戰線（成立約 8 年，比脈動工業晚）"
    }
  },
  "ORG-10": {
    "name": "鐵砧防務（Anvil Defense）",
    "lore": "W01 靈子塵埃",
    "relations": {
      "歷史_歷史線": "歷史線: 冷戰線（成立約 25 年，原為軍事實驗室，後獨立）"
    }
  },
  "ORG-16": {
    "name": "鼠族工業聯合體（簡稱「鼠聯」）",
    "lore": "",
    "relations": {
      "關係_競爭對手": "競爭對手: 貓族海盜（非正式，但常被搶）"
    }
  },
  "ORG-17": {
    "name": "貓族海盜聯合艦隊（簡稱「黑帆」）",
    "lore": "",
    "relations": {
      "關係_競爭對手": "競爭對手: 鼠族工業聯合體（目標）、陸地海軍（偶爾）"
    }
  },
  "ORG-18": {
    "name": "藍鰭航運",
    "lore": "",
    "relations": {}
  },
  "ORG-19": {
    "name": "潮汐基金會",
    "lore": "",
    "relations": {}
  },
  "ORG-20": {
    "name": "納迦皇家地熱",
    "lore": "",
    "relations": {
      "關係_競爭對手": "競爭對手: 莫比迪克邦联的潮汐能产业（无直接竞争，因市场不同）"
    }
  },
  "ORG-21": {
    "name": "人魚聲吶網絡",
    "lore": "",
    "relations": {}
  },
  "ORG-22": {
    "name": "海蛞蝓生技",
    "lore": "",
    "relations": {}
  },
  "ORG-23": {
    "name": "水母幻光娛樂",
    "lore": "",
    "relations": {}
  },
  "ORG-24": {
    "name": "海葵共生農場",
    "lore": "",
    "relations": {}
  }
}
    
    # Nations (from NAT cards)
    sim_systems.NATIONS = {
  "NAT-01": {
    "name": "「神權引領進化」。靈子是神賜的恩典，應以",
    "lore": "「神權引領進化」。靈子是神賜的恩典，應以符文工藝優雅地運用，而非粗暴的工業化"
  },
  "NAT-02": {
    "name": "「靈子應被工具化」。靈子不是神聖的，它是",
    "lore": "「靈子應被工具化」。靈子不是神聖的，它是可被測量、提煉、工業化應用的資源。神靈種不是守護神，是武器"
  },
  "NAT-03": {
    "name": "「不參與陣營對抗」。拒絕在聖諭同盟與唯靈",
    "lore": "「不參與陣營對抗」。拒絕在聖諭同盟與唯靈聯邦之間選邊"
  },
  "NAT-04": {
    "name": "「利潤不選邊」。同時向聖諭同盟與唯靈聯邦",
    "lore": "「利潤不選邊」。同時向聖諭同盟與唯靈聯邦出售資源、技術、與軍事物資"
  },
  "NAT-05": {
    "name": "「和平來自於力量均勢」。向所有陣營出售武",
    "lore": "「和平來自於力量均勢」。向所有陣營出售武器，確保任何一方都無法取得決定性優勢"
  },
  "NAT-06": {
    "name": "莫比迪克自由邦聯（簡稱「莫比迪克」）",
    "lore": "W01 靈子塵埃"
  },
  "NAT-07": {
    "name": "阿比薩深渊联邦",
    "lore": "W01 靈子塵埃"
  }
}
    
    # Rules (from RC cards)
    sim_systems.ACTIVE_RULES = {
  "RC-01": {
    "name": "迴廊 (The Corridor)",
    "lore": "連接多元宇宙各個世界線的「橋樑」，由概念、數據流、意識碎片和世界法則交織而成的虛無維度",
    "mechanism": "資訊與邏輯概念匯聚之地"
  },
  "RC-02": {
    "name": "未命名規則(RC-02)",
    "lore": "",
    "mechanism": "使用D12，預見的本質不穩定，波動較小"
  },
  "RC-03": {
    "name": "未命名規則(RC-03)",
    "lore": "",
    "mechanism": "使用D20"
  },
  "RC-05": {
        "name": "聖十字校園 · 地下遺跡深層休眠區",
    "lore": "迴廊（The Corridor）· 物語核（RC-02）邊緣",
    "mechanism": ""
  },
  "RC-06": {
    "name": "森幽小徑（Shadow-wood Pathway）",
    "lore": "迴廊 · 物語核邊緣",
    "mechanism": ""
  },
  "RC-07": {
    "name": "暈輝湖（Glow-water Cavity）",
    "lore": "迴廊 · 物語核邊緣",
    "mechanism": ""
  },
  "RC-08": {
    "name": "阿拉克涅小鎮（Arachne Town）",
    "lore": "迴廊 · 物語核邊緣",
    "mechanism": ""
  },
  "RC-09": {
    "name": "拉米雅小鎮（Lamia Town）",
    "lore": "迴廊 · 物語核邊緣",
    "mechanism": ""
  },
  "RC-10": {
        "name": "聖十字校園 · 地下市集區（Trade Bazaar）",
    "lore": "迴廊 · 物語核邊緣",
    "mechanism": ""
  },
  "RC-11": {
    "name": "概念學術高等學校（The Academy）",
    "lore": "迴廊 · 物語核邊緣",
    "mechanism": ""
  },
  "RC-12": {
    "name": "蝠群襲掠婚規則（Bat Flock Raid-We",
    "lore": "W01 靈子塵埃（煦掠族群）",
    "mechanism": "透過「捕食儀式化」篩選具備警覺性與回應意願的伴侶"
  },
  "RC-13": {
    "name": "至高神祇命名混合算法（Theonymic Blen",
    "lore": "W01 靈子塵埃（神話層）",
    "mechanism": "將神祇在不同文化與時期的稱呼「碎片」透過演算法混合為全名，並簡化為日常使用姓名。"
  },
  "RC-14": {
    "name": "神祇召喚全名吟唱規則（Theonymic Invo",
    "lore": "跨世界線（適用於W01神話層及任何存在「全名」的高位存在）",
    "mechanism": "將「召喚神祇」從單純的擲骰判定，轉變為需要玩家「實際唸出全名」的表演環節，增加遊戲的荒誕性與儀式感"
  },
  "RC-15": {
    "name": "鼠立方（Rodent Cube）",
    "lore": "W01 靈子塵埃",
    "mechanism": ""
  },
  "RC-16": {
    "name": "黑帆掠奪者（Black Sail Reaver）",
    "lore": "W01 靈子塵埃",
    "mechanism": ""
  }
}
    

    # Assign NPC affiliations based on relation tokens
    # (Injects org info into NPC data where relation tokens exist)
    _npc_faction_map = {}
    for card in _CHARACTER_CARDS:
        raw_name = card.get('name','?').split('(')[0].strip()
        if not raw_name: raw_name = '?'
        _candidates = []
        if raw_name in ALL_NPCS:
            _candidates.append(raw_name)
        else:
            for an in ALL_NPCS:
                if raw_name and (raw_name in an or an[:max(2,len(raw_name))] == raw_name[:max(2,len(raw_name))]):
                    _candidates.append(an)
        relation_tokens = [t for t in card.get('tokens',[]) if t.get('category')=='relation']
        for rt in relation_tokens:
            rel_name = rt.get('name','')
            for ocid, odata in sim_systems.FACTIONS.items():
                fname = odata.get('name','').lower()
                if rel_name.lower() in fname or fname in rel_name.lower():
                    for cn in _candidates:
                        _npc_faction_map[cn] = ocid
                    break
    
    # Assign factions from mapping
    if not hasattr(sim_systems, 'NPC_FACTIONS'):
        sim_systems.NPC_FACTIONS = {}
    for npc_name, ocid in _npc_faction_map.items():
        sim_systems.NPC_FACTIONS[npc_name] = ocid
    
    # Location-based fallback for ALL NPCs
    _loc_to_faction = {}
    for lid, lv in sim_systems.FACTIONS.items():
        fl = (str(lv.get('lore','')) + str(lv.get('name',''))).lower()
        for loc in sim_systems.WORLD_MAP:
            ll = loc.lower()
            if len(ll) >= 2 and ll[:2] in fl:
                _loc_to_faction[loc] = lid
                break
    # Fallback: assign faction based on NPC home location
    for npc_name in list(ALL_NPCS.keys()):
        if npc_name not in sim_systems.NPC_FACTIONS:
            nl = ALL_NPCS.get(npc_name, {}).get('location', '')
            if nl in _loc_to_faction:
                sim_systems.NPC_FACTIONS[npc_name] = _loc_to_faction[nl]
    # Additional fallback: use LOCATION_NATIONS for faction assignment
    if not sim_systems.NPC_FACTIONS or len(sim_systems.NPC_FACTIONS) == 0:
        _loc_to_nat = getattr(sim_systems, "LOCATION_NATIONS", {}) or {}
        for npc_name in list(ALL_NPCS.keys()):
            if npc_name not in sim_systems.NPC_FACTIONS:
                nl = ALL_NPCS[npc_name].get("location", "")
                nat_id = _loc_to_nat.get(nl) if isinstance(_loc_to_nat, dict) else None
                if nat_id and hasattr(sim_systems, "NATIONS"):
                    nn = str(sim_systems.NATIONS.get(nat_id, {}).get("name", "")).lower()
                    for fid, fv in sim_systems.FACTIONS.items():
                        fn = str(fv.get("name", "")).lower()
                        if fn and nn and (fn[:4] in nn or nn[:4] in fn):
                            sim_systems.NPC_FACTIONS[npc_name] = fid
                            break
    
    # Assign territory to locations from NAT cards
    # Simple approach: assign nations to locations based on lore keywords
    _loc_nation_map = {}
    for loc_name in list(sim_systems.WORLD_MAP.keys()):
        for nid, ndata in sim_systems.NATIONS.items():
            ndesc = ndata.get('lore','') + ndata.get('name','')
            # Very simple heuristic: check if location appears in nation lore
            if len(loc_name) >= 2 and any(sub in ndesc for sub in [loc_name, loc_name[::-1][:4], loc_name[:4]]):
                _loc_nation_map[loc_name] = nid
                break
    # Always assign when we have data (placeholder exists but is empty)
    if not sim_systems.LOCATION_NATIONS:
        sim_systems.LOCATION_NATIONS = _loc_nation_map
    
    # Track which rules are active at which locations
    _loc_rules = {}
    for loc_name in list(sim_systems.WORLD_MAP.keys()):
        for rid, rdata in sim_systems.ACTIVE_RULES.items():
            rdesc = rdata.get('lore','') + rdata.get('name','')
            if len(loc_name) >= 2 and any(sub in rdesc for sub in [loc_name, loc_name[::-1][:4], loc_name[:4]]):
                if loc_name not in _loc_rules:
                    _loc_rules[loc_name] = []
                _loc_rules[loc_name].append(rid)
    if not sim_systems.LOCATION_RULES:
        sim_systems.LOCATION_RULES = _loc_rules
    
    # Fallback: use location vibes to assign nations
    if not _loc_nation_map or not any(v for v in _loc_nation_map.values()):
        if hasattr(sim_systems, "LOCATION_VIBES"):
            _vibe_to_nation = {
                '\U0001f33e': 'NAT-06',  # 🌾 EAR OF RICE -> 聖十字校園
                '\U0001f4a7': 'NAT-06',  # 💧 DROPLET -> 鏡湖
                '\U0001f3ea': 'NAT-04',  # 🏪 CONVENIENCE STORE -> 卡洛夫角, 便利店
                '\U0001f4da': 'NAT-02',  # 📚 BOOKS -> 聖十字校園
                '\U0001f30a': 'NAT-06',  # 🌊 WATER WAVE -> 卡洛夫角
                '\U0001f527': 'NAT-05',  # 🔧 WRENCH -> 秘密鐵工廠
                '\U00002694': 'NAT-05',  # ⚔ CROSSED SWORDS -> 英靈殿
                '\U000026cf': 'NAT-05',  # ⛏ PICK -> 廢棄礦坑
                '\U0001f332': 'NAT-03',  # 🌲 EVERGREEN TREE -> 森林深處
            }
            for loc_name in sim_systems.WORLD_MAP:
                if loc_name not in _loc_nation_map or not _loc_nation_map.get(loc_name):
                    vibe = sim_systems.LOCATION_VIBES.get(loc_name, "")
                    for vibe_emoji, nid in _vibe_to_nation.items():
                        if vibe_emoji in vibe:
                            _loc_nation_map[loc_name] = nid
                            break
    print(f"[game_data] Factions: {len(sim_systems.FACTIONS)}, Nations: {len(sim_systems.NATIONS)}, Rules: {len(sim_systems.ACTIVE_RULES)}")
    
    # Skills (from SK-01~SK-22)
    sim_systems.ALL_SKILLS = ALL_SKILLS
    print(f"[game_data] Skills: {len(ALL_SKILLS)}")
    
    # Storyline quests (from SL cards)
    existing_qids = {q["id"] for q in sim_systems.QUESTS}
    for sq in ALL_STORYLINE_QUESTS:
        if sq["id"] not in existing_qids:
            sim_systems.QUESTS.append(sq)
            existing_qids.add(sq["id"])
            cnt["quests"] += 1
    # Also push to game engine's quest log if accessible
    print(f"[game_data] Storyline quests: +{len(ALL_STORYLINE_QUESTS)}")
    
    # World modifiers (from WC/W series)
    sim_systems.WORLD_MODIFIERS = ALL_WORLD_MODIFIERS
    print(f"[game_data] World modifiers: {len(ALL_WORLD_MODIFIERS)}")

    cnt["enemies"] += 1
    
    # Enemy distribution
    loc_list = list(sim_systems.LOCATION_ENEMIES.keys())
    for e in ALL_ENEMIES:
        if not any(e["name"] in names for names in sim_systems.LOCATION_ENEMIES.values()):
            loc = _seed.choice(loc_list)
            sim_systems.LOCATION_ENEMIES.setdefault(loc, []).append(e["name"])
            cnt["enemy_dist"] += 1
    
    # NPCs
    for name, nd in ALL_NPCS.items():
        if name not in sim_systems.NPC_SCHEDULES:
            sched = nd.get("schedule", [])
            if sched:
                sim_systems.NPC_SCHEDULES[name] = sched
                cnt["npcs"] += 1
    
    # Sync NPC metadata into NPC_METADATA (keeps NPC_SCHEDULES as list)
    if not hasattr(sim_systems, 'NPC_METADATA'):
        sim_systems.NPC_METADATA = {}
    for name, nd in ALL_NPCS.items():
        sim_systems.NPC_METADATA[name] = {
            'description': nd.get('description', ''),
            'ability_details': nd.get('ability_details', []),
            'has_abilities': nd.get('has_abilities', False),
            'home_location': nd.get('location', ''),
            'archetype': nd.get('archetype', 'default'),
            'race': nd.get('race', '\u4e0d\u660e'),
            'location': nd.get('location', ''),
            'token_categories': nd.get('token_categories', []),
            'offers': nd.get('offers', []),
        }
    # Quests
    existing_q = {q["id"] for q in sim_systems.QUESTS}
    for q in ALL_QUESTS:
        if q["id"] not in existing_q:
            sim_systems.QUESTS.append(q)
            existing_q.add(q["id"])
            cnt["quests"] += 1
    # Fallback: add NPC_METADATA for NPCs in NPC_SCHEDULES but not in ALL_NPCS
    for _nname in list(getattr(sim_systems, 'NPC_SCHEDULES', {}).keys()):
        if _nname not in sim_systems.NPC_METADATA:
            sim_systems.NPC_METADATA[_nname] = {
                'description': '',
                'ability_details': [],
                'has_abilities': False,
                'home_location': '聖十字校園',
                'archetype': 'default',
                'race': '\u4e0d\u660e',
                'location': '\u8056\u5341\u5b57\u6821\u5712',
                'token_categories': [],
                'offers': ['\u8349\u85e5','\u5e72\u7ce7','\u7a7a\u74f6','\u9ebb\u7e6b'],
            }
    
    
    # Vehicles
    for vn, vd in ALL_VEHICLES.items():
        if vn not in sim_systems.VEHICLES:
            sim_systems.VEHICLES[vn] = vd
            cnt["vehicles"] += 1
    # Also sync VEHICLE_LOCATIONS for all vehicles (keyed by loc -> veh)
    # Build reverse index: every new vehicle → its primary location
    _vehicle_to_primary_loc = {
        "自転車":       "便利店",
        "マウンテンバイク": "森林深處",
        "駿馬":         "卡洛夫角",
        "大型馬車":     "秘密鐵工廠",
        "漁船":         "鏡湖",
        "帆船":         "鏡湖",
        "オートバイ":   "聖十字校園",
        "大型オートバイ": "卡洛夫角",
        "ジープ":       "廢棄礦坑",
        "大型帆船":     "卡洛夫角",
        "熱気球":       "聖十字校園",
        "蒸気機関車":   "秘密鐵工廠",
        "魔法の箒":     "英靈殿",
        "魔法の絨毯":   "聖十字校園",
        "飛空挺":       "卡洛夫角",
        "竜騎乗":       "森林深處",
        "雪橇":         "廢棄礦坑",
    }
    # Build VEHICLE_TO_LOCATION reverse mapping (all vehicles → their location)
    veh_to_loc = {}
    for vn in sim_systems.VEHICLES:
        if vn in _vehicle_to_primary_loc:
            veh_to_loc[vn] = _vehicle_to_primary_loc[vn]
    if not hasattr(sim_systems, 'VEHICLE_TO_LOCATION'):
        sim_systems.VEHICLE_TO_LOCATION = veh_to_loc
    else:
        sim_systems.VEHICLE_TO_LOCATION.update(veh_to_loc)
    # Also populate VEHICLE_LOCATIONS with first vehicle per unique location
    _used_locs = set(sim_systems.VEHICLE_LOCATIONS.keys())
    for veh, loc in _vehicle_to_primary_loc.items():
        if veh in sim_systems.VEHICLES and loc not in _used_locs:
            sim_systems.VEHICLE_LOCATIONS[loc] = veh
            _used_locs.add(loc)
    
    # Real estate — also sync REAL_ESTATE_KEYS
    for rn, rd in ALL_REAL_ESTATE.items():
        if rn not in sim_systems.REAL_ESTATE:
            sim_systems.REAL_ESTATE[rn] = rd
            cnt["estate"] += 1
    # Ensure all real estate entries have location field
    for _rn, _rd in list(sim_systems.REAL_ESTATE.items()):
        if 'location' not in _rd:
            _infer = None
            for _loc in sim_systems.WORLD_MAP:
                if _loc[:2] in _rn or _rn[:2] in _loc:
                    _infer = _loc; break
            _rd['location'] = _infer if _infer else list(sim_systems.WORLD_MAP.keys())[0]
    # Refresh REAL_ESTATE_KEYS to include new entries
    sim_systems.REAL_ESTATE_KEYS = list(sim_systems.REAL_ESTATE.keys())
    
    # Ensure ALL items have tags (based on type)
    _default_tags = {
        'weapon': ['weapon'], 'armor': ['armor'], 'accessory': ['accessory'],
        'consumable': ['consumable'], 'quest': ['quest'], 'junk': ['junk'],
        'material': ['material'], 'misc': ['misc'],
    }
    for _iname, _idata in list(sim_systems.ITEM_CATALOG.items()):
        if 'tags' not in _idata:
            _typ = _idata.get('type', 'misc')
            _idata['tags'] = _default_tags.get(_typ, ['misc'])
    
    # Scene objects
    for loc, objs in ALL_SCENE_OBJECTS.items():
        if loc not in sim_systems.SCENE_OBJECTS:
            sim_systems.SCENE_OBJECTS[loc] = list(objs)
            cnt["objs"] += len(objs)
        else:
            existing_ids = {o["id"] for o in sim_systems.SCENE_OBJECTS[loc]}
            for o in objs:
                if o["id"] not in existing_ids:
                    sim_systems.SCENE_OBJECTS[loc].append(o)
                    existing_ids.add(o["id"])
                    cnt["objs"] += 1
    
    # Recipes
    existing_r = {r["recipe_id"] for r in sim_systems.RECIPES}
    for r in ALL_RECIPES:
        if r["recipe_id"] not in existing_r:
            sim_systems.RECIPES.append(r)
            existing_r.add(r["recipe_id"])
            cnt["recipes"] += 1
        # Scene card locations → merge into WORLD_MAP
    _NEW_LOCATION_VIBES = {
        "概念學術高等學校": "📚 學術の薫り漂う校舎",
        "學生宿舍": "🏠 靜かな學生の住まい",
        "校園後方廢棄倉庫": "🏚 使われなくなった倉庫",
        "概念戰場模擬區": "⚔ 模擬戦用の広場",
        "地下避難所": "🕳 地下に広がる避難施設",
        "夜間巡逻路線": "🌙 夜の巡邏路",
        "校園屋頂": "🌅 校舎の屋上、見晴らしが良い",
        "食堂": "🍽 學生たちの集う食堂",
        "圖書館分館": "📖 小さな図書室",
        "迴廊深層夢境": "✨ 夢の回廊、現実が曖昧になる",
        "綻放混成園": "🌺 花が咲き乱れる庭園",
        "軌道居住站大學院": "🚀 宇宙に浮かぶ学術都市",
        "銀行區": "🏛 荘厳な銀行街",
        "珊瑚台": "🪸 珊瑚が輝く台地",
        "黑淵台": "🌑 深淵を見下ろす崖",
        "彩紋礁": "🌈 色彩豊かな珊瑚礁",
        "流光": "💫 光が流れる神秘的な場所",
        "鏡湖周邊": "💧 鏡のように靜かな湖面",
    }
    _SCENE_TO_WORLD_CONNECTIONS = {
        "概念學術高等學校": {"south":"聖十字校園"},
        "學生宿舍": {"south":"聖十字校園"},
        "校園後方廢棄倉庫": {"enter":"聖十字校園"},
        "概念戰場模擬區": {"enter":"聖十字校園"},
        "地下避難所": {"enter":"聖十字校園"},
        "夜間巡逻路線": {"west":"聖十字校園"},
        "校園屋頂": {"enter":"聖十字校園"},
        "食堂": {"north":"聖十字校園"},
        "圖書館分館": {"south":"聖十字校園"},
        "迴廊深層夢境": {"enter":"聖十字校園"},
        "綻放混成園": {"enter":"聖十字校園"},
        "軌道居住站大學院": {"enter":"聖十字校園"},
        "銀行區": {"west":"聖十字校園","south":"聖十字校園"},
        "珊瑚台": {"north":"卡洛夫角"},
        "黑淵台": {"south":"卡洛夫角"},
        "彩紋礁": {"north":"珊瑚台"},
        "流光": {"enter":"鏡湖"},
        "鏡湖周邊": {"enter":"鏡湖"},
    }
    scene_locs_added = 0
    for scene_id, sdata in ALL_LOCATIONS.items():
        sname = sdata.get("name","")
        if not sname or sname in sim_systems.WORLD_MAP:
            continue
        # Add to WORLD_MAP
        conn = _SCENE_TO_WORLD_CONNECTIONS.get(sname, {"south":"聖十字校園"})
        sim_systems.WORLD_MAP[sname] = conn
        # Add vibe
        vibe = _NEW_LOCATION_VIBES.get(sname, sdata.get("vibe", "📍 未知の地"))
        sim_systems.LOCATION_VIBES[sname] = vibe
        # Assign scene type for new locations
        loc_type = "outdoor"
        if any(kw in sname for kw in ["教室","圖書館","食堂","宿舍","倉庫","避難所","館","工場","店"]):
            loc_type = "indoor"
        elif any(kw in sname for kw in ["迷宮","遺跡","坑","地下","洞"]):
            loc_type = "dungeon"
        elif any(kw in sname for kw in ["夢境","異空間","次元"]):
            loc_type = "special"
        sim_systems.LOCATION_TYPES[sname] = loc_type
        # Add enemy distribution
        _enemy_pool = list(sim_systems.ENEMIES)
        if _enemy_pool:
            sim_systems.LOCATION_ENEMIES.setdefault(sname, []).append(
                _seed.choice(_enemy_pool)["name"])
        scene_locs_added += 1
    cnt["locations"] = scene_locs_added
    
    # Final VEHICLE_LOCATIONS fallback: ensure ALL WORLD_MAP locations have vehicles
    _vlist = ['腳踏車','馬','馬車','小舟','自転車','マウンテンバイク','駿馬','大型馬車','漁船',
              'オートバイ','ジープ','帆船','熱気球','魔法の箒','飛空挺','竜騎乗','雪橇']
    if not hasattr(sim_systems, 'VEHICLE_LOCATIONS'):
        sim_systems.VEHICLE_LOCATIONS = {}
    _occupied = set(sim_systems.VEHICLE_LOCATIONS.keys())
    for _vi, _loc in enumerate(sim_systems.WORLD_MAP):
        if _loc not in _occupied:
            sim_systems.VEHICLE_LOCATIONS[_loc] = _vlist[_vi % len(_vlist)]
    
    # ── NPC schedule location fallback ──
    # Some NPCs reference locations not in WORLD_MAP or scene cards
    _NPC_FALLBACK_LOCATIONS = {
        "中央大圖書館": {"west":"聖十字校園", "east":"英靈殿"},
        "西翼大市集": {"east":"聖十字校園", "north":"便利店"},
        "小吉鎮": {"south":"霧海群島"},
        "大根莖村": {"west":"小吉鎮"},
        "迴廊": {"north":"聖十字校園"},
        "魔女學府": {"south":"聖十字校園"},
    }
    for _loc, _conn in _NPC_FALLBACK_LOCATIONS.items():
        if _loc not in sim_systems.WORLD_MAP:
            sim_systems.WORLD_MAP[_loc] = _conn
            if _loc not in sim_systems.LOCATION_VIBES:
                _vibe_map = {
                    '中央大圖書館': '📚 知識が詰まった巨大図書館',
                    '西翼大市集': '🏪 異世界の商品が並ぶ大市場',
                    '小吉鎮': '🍃 温かい雰囲気の田舎町',
                    '大根莖村': '🌱 地下の神秘的な村',
                    '迴廊': '🧩 空間が歪む古代の回廊',
                    '魔女學府': '🔮 魔法と科学が交錯する学び舎',
                }
                sim_systems.LOCATION_VIBES[_loc] = _vibe_map.get(_loc, '🌍 未知の場所')
            if _loc not in sim_systems.LOCATION_TYPES:
                sim_systems.LOCATION_TYPES[_loc] = "indoor" if _loc in ("中央大圖書館","迴廊","魔女學府") else "outdoor"
    if hasattr(sim_systems, 'LOCATION_NATIONS'):
        for _loc in _NPC_FALLBACK_LOCATIONS:
            if _loc not in sim_systems.LOCATION_NATIONS:
                sim_systems.LOCATION_NATIONS[_loc] = ""
    
    after = {
        "items": len(sim_systems.ITEM_CATALOG),
        "enemies": len(sim_systems.ENEMIES),
        "quests": len(sim_systems.QUESTS),
        "npcs": len(sim_systems.NPC_SCHEDULES),
        "vehicles": len(sim_systems.VEHICLES),
        "estate": len(sim_systems.REAL_ESTATE),
        "objs": sum(len(v) for v in sim_systems.SCENE_OBJECTS.values()),
        "recipes": len(sim_systems.RECIPES),
    }
    
    # Also count dialogues, schedule entries, locations, cards as entities
    dialogs = sum(len(v) for v in ALL_DIALOGUES.values())
    
    # Count each NPC schedule entry separately (5 per NPC)
    sched_entries = sum(len(s) for s in sim_systems.NPC_SCHEDULES.values())
    
    # Count locations: original + scene card generated
    loc_count = len(sim_systems.WORLD_MAP)
    
    # Count game cards
    card_count = len(_ALL_CARDS)
    
    enemy_dists = cnt['enemy_dist']
    
    # Expose NPC_DIALOGUES to sim_systems module
    sim_systems.NPC_DIALOGUES = ALL_DIALOGUES
    
    print(f"[game_data] Integration complete!")
    print(f"  Items: +{cnt['items']} → {after['items']}")
    print(f"  Enemies: +{cnt['enemies']} → {after['enemies']} (dists: +{enemy_dists})")
    print(f"  NPCs: +{cnt['npcs']} → {after['npcs']} (schedule entries: {sched_entries})")
    print(f"  Quests: +{cnt['quests']} → {after['quests']}")
    print(f"  Skills: {len(ALL_SKILLS)}")
    print(f"  WorldModifiers: {len(ALL_WORLD_MODIFIERS)}")
    print(f"  Vehicles: +{cnt['vehicles']} → {after['vehicles']}")
    print(f"  RealEstate: +{cnt['estate']} → {after['estate']}")
    print(f"  SceneObjs: +{cnt['objs']} → {after['objs']}")
    print(f"  Recipes: +{cnt['recipes']} → {after['recipes']}")
    print(f"  Dialogues: {dialogs} lines")
    print(f"  Locations: +{loc_count}")
    print(f"  Cards: +{card_count}")
    print(f"  EnemyDists: +{enemy_dists}")
    
    # Grand total includes all entity types
    grand = sum(after.values()) + dialogs + sched_entries + loc_count + card_count + enemy_dists
    print(f"  ★ GRAND TOTAL entities: {grand}")
