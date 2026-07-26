"""文字冒險遊戲 — 完整版 CLI。"""
from __future__ import annotations

import json
import random
import sys
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps", "backend", "src"))

DATA_DIR = Path(__file__).resolve().parent / "data"


# ═══════════════════════════════════════════════════
# Game State
# ═══════════════════════════════════════════════════

@dataclass
class GameState:
    hp: int = 100
    max_hp: int = 100
    sanity: int = 100
    knowledge: int = 0
    energy: int = 100  # torch battery,体力
    bonds: dict = field(default_factory=dict)  # npc_name -> 0-100
    inventory: list = field(default_factory=list)
    used_items: list = field(default_factory=list)  # items already consumed
    flags: dict = field(default_factory=dict)
    npc_memory: dict = field(default_factory=dict)  # npc -> list of things said/done
    scene_history: list = field(default_factory=list)
    scene_visits: dict = field(default_factory=dict)  # scene_id -> visit count
    turn: int = 0
    alive: bool = True
    ending: str = ""

    def modify_hp(self, delta):
        self.hp = max(0, min(self.max_hp, self.hp + delta))
        if self.hp <= 0:
            self.alive = False

    def modify_sanity(self, delta):
        self.sanity = max(0, min(100, self.sanity + delta))

    def modify_knowledge(self, delta):
        self.knowledge = max(0, min(100, self.knowledge + delta))

    def modify_energy(self, delta):
        self.energy = max(0, min(100, self.energy + delta))

    def bond(self, npc, delta=10):
        self.bonds[npc] = min(100, max(0, self.bonds.get(npc, 50) + delta))

    def remember(self, npc, event):
        """NPC remembers something you did."""
        if npc not in self.npc_memory:
            self.npc_memory[npc] = []
        if event not in self.npc_memory[npc]:
            self.npc_memory[npc].append(event)

    def did_to(self, npc, event):
        """Check if NPC remembers you doing something."""
        return event in self.npc_memory.get(npc, [])

    def has_item(self, item):
        return item in self.inventory and item not in self.used_items

    def use_item(self, item):
        """Consume an item."""
        if item in self.inventory and item not in self.used_items:
            self.used_items.append(item)
            return True
        return False

    def has(self, flag):
        return self.flags.get(flag, False)

    def set(self, flag, val=True):
        self.flags[flag] = val

    def has_knowledge(self, min_k):
        return self.knowledge >= min_k

    def has_bond(self, npc, min_b):
        return self.bonds.get(npc, 50) >= min_b

    def visits(self, scene_id):
        return self.scene_visits.get(scene_id, 0)

    def visit(self, scene_id):
        self.scene_visits[scene_id] = self.visits(scene_id) + 1

    def skill_check(self, difficulty=50):
        roll = random.randint(1, 100)
        bonus = self.knowledge // 2
        return (roll + bonus, roll + bonus >= difficulty)

    def sanity_check(self):
        return self.sanity > 30


# ═══════════════════════════════════════════════════
# Choice System
# ═══════════════════════════════════════════════════

@dataclass
class Choice:
    text: str
    next_scene: str
    effects: dict = field(default_factory=dict)
    # Conditions
    requires_item: str = ""
    requires_knowledge: int = 0
    requires_bond: str = ""  # "npc_name:min_value"
    requires_flag: str = ""
    requires_sanity: int = 0
    requires_no_item: str = ""  # blocked if you have this item
    requires_visits: int = 0  # minimum scene visits
    # Skill check
    skill_check: int = 0  # difficulty, 0 = automatic
    success_scene: str = ""
    fail_scene: str = ""
    # Item consumption
    consume_item: str = ""  # item used up by this choice
    # NPC memory
    npc_remember: str = ""  # "npc_name:event" - NPC remembers this
    npc_forget: str = ""  # "npc_name:event" - NPC forgets this

    def is_available(self, state: GameState) -> bool:
        if self.requires_item and not state.has_item(self.requires_item):
            return False
        if self.requires_no_item and state.has_item(self.requires_no_item):
            return False
        if self.requires_knowledge and not state.has_knowledge(self.requires_knowledge):
            return False
        if self.requires_bond:
            parts = self.requires_bond.split(":")
            npc, min_val = parts[0], int(parts[1])
            if not state.has_bond(npc, min_val):
                return False
        if self.requires_flag and not state.has(self.requires_flag):
            return False
        if self.requires_sanity and state.sanity < self.requires_sanity:
            return False
        return True

    def get_effects(self, state: GameState) -> dict:
        effects = dict(self.effects)
        if self.skill_check > 0:
            roll, success = state.skill_check(self.skill_check)
            effects["_roll"] = roll
            effects["_success"] = success
            if not success:
                effects["sanity"] = effects.get("sanity", 0) - 5
        if self.consume_item:
            effects["_consume"] = self.consume_item
        if self.npc_remember:
            parts = self.npc_remember.split(":", 1)
            effects["_remember"] = (parts[0], parts[1])
        if self.npc_forget:
            parts = self.npc_forget.split(":", 1)
            effects["_forget"] = (parts[0], parts[1])
        return effects


# ═══════════════════════════════════════════════════
# Scene Definitions
# ═══════════════════════════════════════════════════

SCENES = {}

def scene(id, narrative, choices, on_enter=None):
    SCENES[id] = {
        "id": id,
        "narrative": narrative,
        "choices": choices,
        "on_enter": on_enter,
    }


# ═══════════════════════════════════════════════════
# ACT 1: 開端
# ═══════════════════════════════════════════════════

scene("start", """你醒來。
四周是灰色的牆壁，空氣中帶著金屬和灰塵的味道。
你的口袋裡有一張紙條：「找到鏡湖。答案在那裡。」
沒有人告訴你這是哪裡，也沒有人告訴你該怎麼做。""", [
    Choice("推開門，走出去", "scene_S15"),
    Choice("搜索房間", "search_room"),
])

scene("search_room", """房間很小。一張床、一張桌子、一個抽屜。
抽屜裡有一支手電筒、一張地圖、一把小刀、和一塊乾糧。
地圖上標記了一個位置：鏡湖。""", [
    Choice("拿上所有東西，出發", "scene_S15",
          {"item": "手電筒", "item2": "地圖", "item3": "小刀", "item4": "乾糧"}),
    Choice("只拿有用的", "scene_S15", {"item": "手電筒", "item2": "地圖", "item3": "小刀"}),
    Choice("什麼都不拿，直接走", "scene_S15"),
])

# ═══════════════════════════════════════════════════
# ACT 2: 鏡湖
# ═══════════════════════════════════════════════════

scene("scene_S15", """鏡湖周邊。
湖面像鏡子一樣平靜，倒映著灰色的天空。
空氣中有一種奇怪的震動，像是什麼東西在湖底呼吸。
你感覺有人在看著你。""", [
    Choice("靠近湖邊", "lake_approach"),
    Choice("觀察四周", "lake_observe"),
    Choice("大聲喊叫", "lake_shout", requires_sanity=50),
    Choice("轉身離開", "leave_lake"),
    Choice("用地圖研究湖的結構", "lake_map_study", requires_item="地圖"),
    Choice("用小刀在岩石上做標記", "lake_mark", requires_item="小刀"),
])

scene("lake_map_study", """你攤開地圖研究。
地圖上標記了鏡湖的幾個特殊位置：
湖底深處有一個「迴廊入口」。
湖的東側有一條「地下水道」。
湖的西側有一個「冰層裂縫」。""", [
    Choice("前往地下水道入口", "underground_entrance", {"knowledge": 15, "flag": "knows地下水道"}),
    Choice("前往冰層裂縫", "lake_observe", {"knowledge": 10}),
    Choice("回到湖邊", "lake_approach"),
])

scene("lake_mark", """你在岩石上刻了一個箭頭，指向湖面。
這樣你回來的時候就能找到位置。
你注意到岩石下面壓著什麼東西。""", [
    Choice("撬開岩石", "lake_mark_find", {"energy": -5}),
    Choice("不碰，離開", "lake_approach"),
])

scene("lake_mark_find", """岩石下面有一個小盒子。
盒子裡有一張舊照片和一把小鑰匙。
照片上是一群人站在迴廊入口前。
背面寫著：「別忘了回來的路。」""", [
    Choice("收下照片和鑰匙", "lake_approach", {"item": "照片", "item2": "小鑰匙", "knowledge": 10}),
    Choice("只收下鑰匙", "lake_approach", {"item": "小鑰匙"}),
])

scene("lake_shout", """你的聲音在湖面上迴盪。
安靜。
然後，湖面裂開了一條縫。光從縫隙中透出來。
聲音從湖底傳來：「終於有人回應了。」""", [
    Choice("回應它", "lake_respond", {"knowledge": 10}),
    Choice("後退", "lake_approach"),
])

scene("lake_respond", """「你是誰？」你問。
「我是守門人。」聲音說。「我守護這面鏡湖已經很久了。」
「你來找答案。答案就在湖底。但你需要一把鑰匙。」
「鑰匙不在這裡。在學校。在圖書館。」""", [
    Choice("問怎麼去學校", "lake_to_school", {"flag": "knows_school", "knowledge": 5}),
    Choice("問更多關於迴廊的事", "lake_corridor_info", {"knowledge": 10}),
])

scene("lake_to_school", """「沿著鏡湖東側的小路走。」守門人說。
「學校就在那裡。圖書館在二樓。」
「晞咕萊雅管理那裡。她知道鑰匙在哪。」""", [
    Choice("前往學校", "scene_S01"),
    Choice("先探索鏡湖", "scene_S15"),
])

scene("lake_corridor_info", """「迴廊連接所有世界線。」守門人說。
「但不是每個人都能進去。你需要三樣東西：」
「一、理解。知道你在找什麼。」
「二、鑰匙。物理上的鑰匙。」
「三、勇氣。願意面對你不想看到的東西。」""", [
    Choice("你已經有理解了", "lake_approach", {"knowledge": 15}),
    Choice("去尋找鑰匙", "scene_S01", {"flag": "seeking_key"}),
])

scene("lake_approach", """你走向湖邊。腳下的冰層發出輕微的龜裂聲。
湖水清澈得不正常——你能看到湖底，但湖底似乎很深很深。
水面下有光在閃爍。""", [
    Choice("伸手觸碰水面", "touch_water"),
    Choice("退後，觀察", "lake_observe"),
    Choice("用小刀試探冰層", "ice_probe", requires_item="小刀"),
    Choice("沿著湖邊散步", "lake散步"),
    Choice("跳入湖中", "lake_deep", {"energy": -20}),
    Choice("探索湖邊的廢棄建築", "abandoned_house"),
])

scene("ice_probe", """你用小刀刺入冰層。
刀尖碰到堅硬的東西——不是冰，是金屬。
你撬開冰層，發現下面有一個金屬蓋子，上面刻著符號。
符號和地圖上的標記一樣。""", [
    Choice("打開蓋子", "underground_entrance", {"flag": "found_tunnel"}),
    Choice("記住位置，離開", "leave_lake", {"knowledge": 10, "flag": "knows_tunnel"}),
])

scene("underground_entrance", """蓋子下面是一條階梯，通向地下。
階梯很陡，你看不見底部。
手電筒的光照亮了前幾級階梯。牆壁上有水滴聲。""", [
    Choice("走下去", "underground_descent", requires_item="手電筒"),
    Choice("太暗了，不敢下去", "lake_approach"),
    Choice("在入口處做標記，離開", "leave_lake", {"flag": "mapped_tunnel"}),
])

scene("underground_descent", """你打開手電筒，沿著階梯走下去。
空氣越來越冷。牆壁上的符號越來越密集。
你走了大約一百階，然後階梯終止了。
你面前是一扇石門。""", [
    Choice("推開石門", "underground_room", {"energy": -10}),
    Choice("用手電筒觀察符號", "underground_symbols", {"knowledge": 15, "energy": -5}),
    Choice("回到地面", "scene_S15"),
    Choice("探索更深處", "dark_hallway"),
    Choice("感覺到有東西在暗處", "shadow_encounter"),
])

scene("underground_symbols", """你仔細觀察牆壁上的符號。
它們描述了一個過程：某種能量的流動路徑。
你發現其中一個符號和你口袋裡的地圖標記吻合。
如果這些符號是正確的，石門後面就是迴廊的入口。""", [
    Choice("推開石門", "underground_room", {"energy": -10}),
    Choice("帶著這個知識離開", "leave_lake", {"knowledge": 20}),
])

scene("underground_room", """石門後面是一個圓形的房間。
中央有一個石台，上面放著一顆發光的水晶。
水晶的光是藍色的。
房間的另一側有一扇門，門上刻著迴廊的符號。""", [
    Choice("拿起水晶", "take_crystal", {"item": "水晶", "knowledge": 10}),
    Choice("直接走向迴廊之門", "corridor_entrance"),
    Choice("觀察房間的牆壁", "room_walls"),
    Choice("用水晶照亮房間角落", "room_corner", requires_item="水晶",
          consume_item="水晶", effects={"knowledge": 20, "flag": "saw_inscription"}),
])

scene("room_corner", """你舉起水晶，藍光照亮了房間的角落。
牆壁上刻著一行字：「鑰匙不在門上。鑰匙在你手裡。」
你低頭看。你的手在發光。
原來如此。鑰匙不是物理的東西。它是一種理解。""", [
    Choice("帶著這個理解進入迴廊", "corridor_entrance", {"knowledge": 25}),
])

scene("room_walls", """牆壁上刻著文字。你仔細閱讀：
「迴廊不是一條路。它是一個問題。」
「你帶著什麼進去，你就帶著什麼出來。」
「但你帶出來的，可能和你帶進去的不一樣。」""", [
    Choice("拿起水晶，進入迴廊", "corridor_entrance", {"item": "水晶"}),
    Choice("不拿水晶，直接進入", "corridor_entrance"),
])

scene("take_crystal", """你拿起水晶。
瞬間，你的腦子裡涌入了大量資訊。
你看到了迴廊。一條無盡的走廊，兩側的門不斷開合。
你看到了時間在流動。你看到了你自己。""", [
    Choice("帶著水晶進入迴廊", "corridor_entrance"),
    Choice("放下水晶，先離開", "leave_lake"),
])

scene("touch_water", """你的手指碰到水面。
冰冷。但不只是冷——是一種「概念性的冷」，像是有人在你的腦子裡放了一塊冰。
你看到了一個畫面：一個銀髮少女在月光下寫字。
畫面消失。你的手指在發抖。""", [
    Choice("繼續探索", "cave_entrance", {"knowledge": 15, "flag": "saw_vision"}),
    Choice("離開鏡湖", "leave_lake", {"sanity": -10}),
])

scene("lake_observe", """你蹲下來觀察。
冰層下有水流在移動，不是自然的水流——是有節奏的，像呼吸。
地上有足跡。不是人類的足跡。太小了，太整齊了。
足跡通向湖邊的一個洞穴。""", [
    Choice("跟隨足跡", "cave_entrance", {"flag": "found_footprints"}),
    Choice("記錄發現，離開", "leave_lake", {"knowledge": 5}),
    Choice("用小刀刮取冰層樣本", "ice_sample", requires_item="小刀"),
])

scene("ice_sample", """你用小刀刮下一塊冰層樣本。
冰是藍色的。不是反射——冰本身有顏色。
你把樣本舉到光線下。裡面有微小的氣泡在移動。
不是氣泡。是某種微小的生物。""", [
    Choice("把樣本收起來", "leave_lake", {"item": "冰層樣本", "knowledge": 10}),
    Choice("把樣本放回去", "leave_lake"),
])

scene("cave_entrance", """洞穴入口很窄，你必須側身才能進去。
裡面比你想像的寬敞。牆壁上刻著符號。
你感覺空氣中的震動在加強。
洞穴深處有聲音。""", [
    Choice("繼續深入", "cave_deep"),
    Choice("觀察符號", "cave_symbols", {"knowledge": 10}),
    Choice("在入口處做標記", "leave_cave", {"flag": "marked_cave"}),
])

scene("cave_deep", """洞穴越走越寬。
你看到了一個房間。中央有一個石台，上面放著一顆發光的水晶。
水晶的光是藍色的。""", [
    Choice("拿起水晶", "take_crystal", {"item": "水晶", "knowledge": 10}),
    Choice("觀察房間", "room_walls"),
    Choice("用手電筒照亮角落", "cave_corner", requires_item="手電筒"),
    Choice("用小刀刮取石台上的痕跡", "cave_sample", requires_item="小刀"),
])

scene("cave_corner", """你用手電筒照亮房間的角落。
你發現牆壁上有更多的符號。
這些符號描述了一個過程：如何用水晶打開迴廊的門。""", [
    Choice("記住這個過程", "cave_deep", {"knowledge": 20, "flag": "knows_crystal_ritual"}),
    Choice("繼續探索", "room_walls"),
])

scene("cave_sample", """你用小刀刮取石台上的痕跡。
石台上有某種液體的殘留物。
你把樣本收起來。""", [
    Choice("繼續探索", "cave_deep", {"item": "石台殘留物", "knowledge": 5}),
])

scene("cave_symbols", """你蹲下來研究符號。
它們似乎是一種坐標系統。每一對符號對應兩個位置。
你發現其中一對符號連接了鏡湖和學校。""", [
    Choice("前往學校", "scene_S01", {"knowledge": 5}),
    Choice("繼續深入洞穴", "cave_deep"),
])

scene("leave_cave", """你離開洞穴。
鏡湖依然平靜，但你看待它的方式不同了。""", [
    Choice("前往學校", "scene_S01"),
    Choice("前往市集", "scene_S17"),
    Choice("進入迴廊", "corridor_entrance", requires_flag="found_footprints"),
])

scene("leave_lake", """你離開鏡湖。""", [
    Choice("前往學校", "scene_S01"),
    Choice("前往市集", "scene_S17"),
    Choice("探索湖邊小路", "lake散步"),
    Choice("前往營火休息", "rest_campfire"),
    Choice("探索廢棄實驗室", "abandoned_lab"),
])

# ═══════════════════════════════════════════════════
# ACT 3: 學校
# ═══════════════════════════════════════════════════

scene("scene_S01", """方碑丘·概念學術高等學校。
走廊上人來人往，但沒有人在說話。
他們的嘴在動，但聲音像是被什麼東西吸收了。
你注意到一個女孩獨自站在走廊盡頭。""", [
    Choice("走向那個女孩", "meet_hikuraya"),
    Choice("觀察走廊裡的人", "observe_students"),
    Choice("前往圖書館", "library"),
    Choice("離開學校", "leave_school"),
    Choice("用地圖找路", "school_map", requires_item="地圖"),
    Choice("用小刀撬開鎖住的門", "school_locked_door", requires_item="小刀", skill_check=50),
])

scene("school_map", """你攤開地圖研究。
學校的結構比你想像的複雜。
地圖上標記了幾個特殊房間：「研究室」、「實驗室」、「地下室」。
你注意到地下室的標記旁邊有一個迴廊的符號。""", [
    Choice("前往地下室", "school_basement", {"knowledge": 10, "flag": "knows_basement"}),
    Choice("前往研究室", "school_research"),
    Choice("回到走廊", "scene_S01"),
])

scene("school_locked_door", """你用小刀撬開了鎖住的門。
門後面是一個小房間。
裡面有一張桌子和一個保險箱。""", [
    Choice("嘗試打開保險箱", "school_safe", skill_check=70),
    Choice("搜索房間", "school_search"),
    Choice("離開", "scene_S01"),
])

scene("school_safe", """你嘗試打開保險箱。""", [
    Choice("成功", "school_safe_open"),
    Choice("失敗", "school_safe_fail"),
])

scene("school_safe_open", """保險箱打開了。
裡面有一把鑰匙和一個筆記本。
筆記本上記錄了某種研究——關於意識和迴廊。""", [
    Choice("拿走鑰匙和筆記本", "scene_S01", {"item": "保險箱鑰匙", "item2": "研究筆記", "knowledge": 15}),
    Choice("只拿鑰匙", "scene_S01", {"item": "保險箱鑰匙"}),
])

scene("school_safe_fail", """保險箱紋絲不動。
你的小刀上有了一個缺口。""", [
    Choice("離開", "scene_S01"),
])

scene("school_search", """你搜索房間。
在桌子下面你發現了一個小盒子。
盒子裡有一張照片和一張紙條。""", [
    Choice("查看照片", "school_photo"),
    Choice("查看紙條", "school_note"),
])

scene("school_photo", """照片上是一群人站在迴廊入口前。
你認出了其中一個——是晞咕萊雅。
她在微笑。和現在的她完全不同。""", [
    Choice("記住這件事", "scene_S01", {"knowledge": 10, "flag": "saw_hikuraya_photo"}),
])

scene("school_note", """紙條上寫著：
「晞咕萊雅知道真相。但她選擇不說。
因為真相太沉重了。
如果你想知道，問她關於照片的事。」""", [
    Choice("記住這件事", "scene_S01", {"knowledge": 10, "flag": "knows_hikuraya_secret"}),
])

scene("school_basement", """你找到了地下室的入口。
門是鎖著的。但你注意到門上有一個符號——迴廊的標誌。
你用小刀試探鎖孔。鎖很複雜。""", [
    Choice("用保險箱鑰匙嘗試", "school_basement_open", requires_item="保險箱鑰匙"),
    Choice("強行撬鎖", "school_basement_pry", skill_check=80),
    Choice("離開", "scene_S01"),
])

scene("school_basement_open", """你用保險箱鑰匙打開了地下室的門。
門後面是一條階梯，通向地下。
你走了下去。""", [
    Choice("繼續", "underground_entrance"),
])

scene("school_basement_pry", """你嘗試撬鎖。""", [
    Choice("成功", "school_basement_open"),
    Choice("失敗", "scene_S01", {"sanity": -5}),
])

scene("school_research", """你找到了研究室。
門是開著的。裡面有一個穿白袍的人。
他看著你。「你是誰？你不應該在這裡。」""", [
    Choice("問他關於迴廊的事", "research_corridor"),
    Choice("問他關於晞咕萊雅的事", "research_hikuraya"),
    Choice("離開", "scene_S01"),
])

scene("research_corridor", """「迴廊？」研究者看起來很驚訝。
「你知道迴廊？」
「那是……很久以前的事了。我們曾經研究過它。」""", [
    Choice("「你們發現了什麼？」", "research_discovery"),
    Choice("「為什麼停止研究？」", "research_stop"),
])

scene("research_discovery", """「我們發現迴廊是活的。」研究者說。
「它會思考。它會選擇。」
「但我們無法控制它。所以我們放棄了。」""", [
    Choice("「謝謝你」", "scene_S01", {"knowledge": 20}),
])

scene("research_stop", """「因為我們害怕。」研究者說。
「迴廊的力量太大了。我們無法控制它。」
「所以我们選擇了忘記。」""", [
    Choice("「但你沒有忘記」", "scene_S01", {"knowledge": 15}),
])

scene("research_hikuraya", """「晞咕萊雅？」研究者嘆了口氣。
「她是我們的研究助手。她……和迴廊建立了聯繫。」
「然後她就留在了圖書館裡。」""", [
    Choice("「什麼聯繫？」", "research_link"),
    Choice("「謝謝你」", "scene_S01"),
])

scene("research_link", """「她可以和迴廊溝通。」研究者說。
「但代價是她失去了情感。」
「她選擇了知識而不是情感。」""", [
    Choice("「這值得嗎？」", "scene_S01", {"knowledge": 20, "flag": "knows_hikuraya_link"}),
    Choice("「謝謝你」", "scene_S01", {"knowledge": 15}),
])

scene("observe_students", """你觀察走廊裡的人。
他們的動作整齊得不自然。
你注意到他們的嘴在動，但你聽不到聲音。
突然，一個學生停下來，轉頭看著你。
他的眼睛是空的。""", [
    Choice("問他怎麼了", "empty_student"),
    Choice("轉身離開", "leave_school", {"sanity": -10}),
    Choice("用小刀威脅他", "threaten_student", requires_item="小刀", skill_check=60,
          success_scene="student_scared", fail_scene="student_attack"),
])

scene("threaten_student", "你威脅了他。", [Choice("離開", "leave_school")])

scene("student_scared", """學生退後了一步。
「別……別傷害我。」他的聲音恢復了。
「我聽得到你。只有你。」
「因為你……你是清醒的。」""", [
    Choice("問他發生了什麼", "student_info", {"knowledge": 15, "bond_student": 10}),
])

scene("student_attack", """學生沒有退後。他伸出手，抓住你的手腕。
他的力氣大得驚人。
「你不應該在這裡。」他說。
然後他鬆開手，轉身離開。""", [
    Choice("追上去", "leave_school", {"hp": -10}),
    Choice("留在原地", "leave_school"),
])

scene("student_info", """「我們都被同步了。」他說。
「從進入學校的那一刻起。」
「聲音被吸收了。思維被同步了。」
「但你……你沒有。為什麼？」""", [
    Choice("告訴他你從沒進過學校", "student_away", {"knowledge": 10}),
    Choice("你不知道", "student_unknown"),
])

scene("student_away", """「那就對了。」他說。
「同步只對在校時間超過一天的人有效。」
「你剛來。你還有時間。」
「找到圖書館。晞咕萊雅知道怎麼解除同步。」""", [
    Choice("前往圖書館", "library", {"flag": "knows_hikuraya_fix"}),
])

scene("student_unknown", """「也许你是特殊的。」他說。
「也許你的概念頻率和我們不一樣。」
「不管怎樣，去找晞咕萊雅。她在圖書館。」""", [
    Choice("前往圖書館", "library"),
])

scene("empty_student", """「你聽不見嗎？」他問。
你搖頭。
「那就對了。」他說。
「聲音在迴廊裡。去迴廊。」
他轉身離開。""", [
    Choice("前往迴廊", "corridor_entrance", {"knowledge": 10}),
    Choice("先去市集", "scene_S17"),
])

scene("library", """圖書館很安靜。比走廊更安靜。
書架上擺滿了書，但大部分都沒有標題。
一個女孩坐在角落裡，低頭看著一本書。
她看起來很小，蛇尾蜷縮在椅子上。""", [
    Choice("走向她", "meet_hikuraya"),
    Choice("觀察書架", "library_books"),
    Choice("尋找迴廊相關的書", "library_search", requires_knowledge=20),
])

scene("library_books", """你觀察書架。
書的封面沒有標題，但書脊上有微小的符號。
你發現這些符號和洞穴裡的一樣。
每一本書對應一個世界線。""", [
    Choice("嘗試打開一本書", "library_open_book"),
    Choice("和那個女孩說話", "meet_hikuraya"),
])

scene("library_open_book", """你打開一本書。
裡面不是文字。是某種……影像。
你看到了一個城市的廢墟。天空是紫色的。
書頁自動翻動。你看到了更多。""", [
    Choice("繼續看", "library_vision", {"knowledge": 15, "sanity": -5}),
    Choice("合上書", "library"),
])

scene("library_vision", """影像越來越清晰。
你看到了一個女孩在廢墟中行走。她的翅膀是金屬的。
她停下來，轉頭看向你。
「你能看到我？」她問。""", [
    Choice("回答她", "library_contact", {"flag": "contacted_wings", "knowledge": 10}),
    Choice("合上書", "library", {"sanity": -5}),
])

scene("library_contact", """「我能。」你說。
「你是誰？」她問。
「我不確定。」你說。
「我也是。」她說。「我在這裡很久了。」
「你知道怎麼離開嗎？」""", [
    Choice("告訴她你知道迴廊", "library_wings_know", {"bond_wings": 15, "knowledge": 10}),
    Choice("說你不知道", "library_wings_unknown"),
])

scene("library_wings_know", """「迴廊？」她的眼睛亮了。
「我聽過這個名字。但我不知道怎麼去。」
「如果你找到了，能告訴我嗎？」""", [
    Choice("答應她", "library", {"flag": "promised_wings", "bond_wings": 10}),
])

scene("library_wings_unknown", """「沒關係。」她說。
「我會繼續找的。」
書頁翻動，影像消失了。""", [
    Choice("合上書", "library"),
])

scene("library_search", """你在書架上尋找。
你找到了一本書，書脊上刻著迴廊的符號。
打開它，裡面是一張地圖。""", [
    Choice("帶走地圖", "library", {"item": "迴廊地圖", "knowledge": 15}),
    Choice("記住內容，放回去", "library", {"knowledge": 15}),
])

scene("meet_hikuraya", """你走向那個女孩。
她抬起頭。你看到了一雙沒有情感的眼睛——不是冷漠，是「低耗能」。
「你是新來的。」她說。
「我叫晞咕萊雅。我在這裡管理圖書館。」""", [
    Choice("問她關於鏡湖", "hikuraya_lake", requires_knowledge=5),
    Choice("問她關於迴廊", "hikuraya_corridor", requires_knowledge=15),
    Choice("問她在看什麼書", "hikuraya_book"),
    Choice("威脅她交出鑰匙", "hikuraya_threaten", requires_item="小刀",
          npc_remember="hikuraya:threatened"),
    Choice("問她關於照片的事", "hikuraya_photo", requires_flag="saw_hikuraya_photo"),
    Choice("問她關於研究的事", "hikuraya_research", requires_flag="knows_hikuraya_link"),
    Choice("向她請求幫助", "hikuraya_help_request", requires_bond="hikuraya:60"),
    Choice("離開", "leave_school"),
])

scene("hikuraya_photo", """「你看到了那張照片。」晞咕萊雅說。
「那是很久以前的事了。」
「我曾經是不同的人。」""", [
    Choice("「你現在是什麼人？」", "hikuraya_now"),
    Choice("「你後悔嗎？」", "hikuraya_regret"),
])

scene("hikuraya_now", """「我是知識的守護者。」她說。
「我放棄了情感。但我換來了理解。」
「這值得嗎？我不知道。」""", [
    Choice("「我覺得值得」", "leave_school", {"bond_hikuraya": 15, "knowledge": 10}),
    Choice("「我覺得不值得」", "leave_school", {"bond_hikuraya": -5}),
])

scene("hikuraya_regret", """「後悔？」她想了一會兒。
「有時候。」她說。
「但後悔也是情感。我已經學會了不感受它。」""", [
    Choice("「我很抱歉」", "leave_school", {"bond_hikuraya": 10}),
])

scene("hikuraya_research", """「你知道了。」她說。
「我和迴廊有聯繫。」
「但代價是我失去了情感。」""", [
    Choice("「你能幫我進入迴廊嗎？」", "hikuraya_can_help"),
    Choice("「謝謝你告訴我」", "leave_school", {"bond_hikuraya": 10}),
])

scene("hikuraya_can_help", """「我可以。」她說。
「但你需要先證明你值得。」
「幫我做一件事。」""", [
    Choice("「什麼事？」", "hikuraya_task"),
])

scene("hikuraya_task", """「圖書館裡有一本書。」她說。
「書名是「迴廊守則」。把它帶回來。」
「作為交換，我會幫你進入迴廊。」""", [
    Choice("接受任務", "library", {"flag": "hikuraya_quest"}),
    Choice("拒絕", "leave_school"),
])

scene("hikuraya_help_request", """「你願意幫我？」晞咕萊雅看著你。
「你已經走了這麼遠。」
「我可以給你一些幫助。」""", [
    Choice("接受她的幫助", "hikuraya_help_item"),
])

scene("hikuraya_help_item", """她從口袋裡拿出一顆小珠子。
「這是迴廊之珠。」她說。
「它會在迴廊裡幫助你。」
「帶好它。」""", [
    Choice("收下珠子", "leave_school", {"item": "迴廊之珠", "bond_hikuraya": 20}),
])

scene("hikuraya_threaten", """你拿出小刀。
晞咕萊雅看著你。她沒有退後。
「你在威脅我。」她說。語氣平淡，像是在陳述事實。
「你知道嗎？在迴廊裡，威脅是最沒用的策略。」
她站起來。你發現她比你想像的高。
「我不怕你。但我可以告訴你一件事：」
「用恐懼得到的東西，你帶不進迴廊。」""", [
    Choice("收起小刀，道歉", "hikuraya_apologize", {"bond_hikuraya": -20, "sanity": -10}),
    Choice("繼續威脅", "hikuraya_fight", {"hp": -30, "bond_hikuraya": -50}),
])

scene("hikuraya_apologize", """你收起小刀。
「對不起。」你說。
晞咕萊雅看著你。她的眼睛裡有某種東西——不是原諒，是……好奇。
「你害怕。」她說。「你害怕到覺得需要用暴力。」
「這讓我有點想幫你。」""", [
    Choice("問她願意幫你嗎", "hikuraya_help_after_apology", {"bond_hikuraya": 10}),
])

scene("hikuraya_help_after_apology", """「我可以給你一些指引。」她說。
「不是鑰匙。鑰匙你必須自己找到。」
「但我可以告訴你：迴廊的入口不在鏡湖。」
「它在你放棄尋找的那一刻出現。」""", [
    Choice("謝謝她", "library", {"knowledge": 20, "bond_hikuraya": 15}),
])

scene("hikuraya_fight", """你撲向她。
她退後一步。你的刀劃過空氣。
然後你感覺到一股力量擊中你的胸口。
你飛了出去，撞在書架上。
晞咕萊雅站在原地。她的手在發光。
「我說過。威脅是沒用的。」""", [
    Choice("掙扎著站起來", "leave_school", {"hp": -20, "bond_hikuraya": -30}),
])

scene("hikuraya_lake", """「鏡湖。你知道那裡。」她合上書。
「鏡湖下面是迴廊。迴廊連接所有世界線。」
「你想去那裡？大多数人到了那裡就回不來了。」""", [
    Choice("問她為什麼", "hikuraya_why"),
    Choice("表示你必須去", "hikuraya_must_go"),
    Choice("問她有沒有去過", "hikuraya_experience"),
])

scene("hikuraya_corridor", """晞咕萊雅看著你。
「你知道的比我預期的多。」
「迴廊。你真的想去？」""", [
    Choice("你必須去", "hikuraya_must_go"),
    Choice("問她怎麼去", "hikuraya_how"),
])

scene("hikuraya_how", """「去鏡湖。找到入口。」她說。
「但你需要鑰匙。」
「我有一把。但你必須說服我給你。」""", [
    Choice("問她怎麼說服她", "hikuraya_persuade"),
    Choice("問她想要什麼", "hikuraya_want"),
])

scene("hikuraya_persuade", """「告訴我一個真實的故事。」她說。
「不是別人告訴你的。是你親身經歷的。」
「一個你真正害怕的故事。」""", [
    Choice("告訴她你害怕的事", "hikuraya_story", skill_check=50,
          success_scene="hikuraya_trust", fail_scene="hikuraya_reject"),
])

scene("hikuraya_story", "你講了一個故事。", [Choice("繼續", "library")])

scene("hikuraya_trust", """晞咕萊雅聽完你的故事。
她沉默了很久。
然後她從口袋裡拿出一把小鑰匙。
「這是迴廊的鑰匙。」她說。
「拿去吧。但記住——迴廊會讓你面對你最害怕的東西。」""", [
    Choice("收下鑰匙", "library", {"item": "迴廊鑰匙", "bond_hikuraya": 20, "knowledge": 20}),
])

scene("hikuraya_reject", """晞咕萊雅看著你。
「你在說謊。」她說。
「你不是真的害怕。你只是想拿到鑰匙。」
「等你真正害怕的時候再來找我。」""", [
    Choice("離開", "leave_school", {"sanity": -5}),
])

scene("hikuraya_want", """「我想要一個故事。」她說。
「一個真實的故事。你親身經歷的。」
「一個你真正害怕的故事。」""", [
    Choice("告訴她你害怕的事", "hikuraya_story", skill_check=50,
          success_scene="hikuraya_trust", fail_scene="hikuraya_reject"),
])

scene("hikuraya_why", """「因為迴廊會給你你想要的東西。」
「不是寶藏。不是力量。是答案。」
「但答案不一定是你能承受的。」""", [
    Choice("你還是要去", "hikuraya_must_go"),
    Choice("問她經驗", "hikuraya_experience"),
])

scene("hikuraya_experience", """「我去過一次。」她說。
「我看到了自己。不是現在的自己。是可能的自己。」
「那個我……比我更像人。」
「但我選擇回來了。因為那個我太像人了，以至於忘記了自己是什麼。」""", [
    Choice("你還是要去", "corridor_entrance", {"knowledge": 15, "bond_hikuraya": 10}),
])

scene("hikuraya_must_go", """「你的眼神告訴我，你不會聽我的建議。」
「那就去吧。但記住一件事：在迴廊裡，不要說謊。」""", [
    Choice("記住她的話，前往迴廊", "corridor_entrance", {"knowledge": 10, "bond_hikuraya": 5}),
    Choice("問她有沒有鑰匙", "hikuraya_how"),
])

scene("hikuraya_book", """「這不是書。是某種……資料庫的實體介面。」
「裡面記錄了所有通過迴廊的人的記錄。」
「大部分人的記錄都很短。進去，出來，然後忘記。」""", [
    Choice("問長記錄的人", "hikuraya_long_records"),
    Choice("你想看自己的記錄", "hikuraya_own_record"),
])

scene("hikuraya_long_records", """「他們沒有回來。」她說。
「或者說，他們回來了，但不再是同一個人。」
「迴廊會改變你。」""", [
    Choice("你不怕改變", "corridor_entrance", {"knowledge": 5}),
])

scene("hikuraya_own_record", """「你還沒有記錄。你剛來。」
「但如果你從迴廊回來，你的記錄會出現在這裡。」""", [
    Choice("前往迴廊", "corridor_entrance", {"knowledge": 5}),
])

scene("leave_school", """你離開學校。""", [
    Choice("前往鏡湖", "scene_S15"),
    Choice("前往市集", "scene_S17"),
    Choice("探索學校後面的小路", "hidden_path"),
    Choice("前往營火休息", "rest_campfire"),
])

# ═══════════════════════════════════════════════════
# ACT 4: 市集
# ═══════════════════════════════════════════════════

scene("scene_S17", """西翼大市集。
和學校不同，這裡有聲音。叫賣聲、笑聲、爭吵聲。
攤位上賣著各種你沒見過的東西。
一個攤位前站著一個紅髮女孩，正在和客人吵架。""", [
    Choice("走向紅髮女孩", "meet_red"),
    Choice("逛市集", "explore_market"),
    Choice("離開", "leave_market"),
])

scene("meet_red", """「我說了不賣就是不賣！」紅髮女孩對客人吼道。
客人離開後，她轉向你。
「你是誰？新面孔。」
她上下打量你。「你的眼神……你看過鏡湖了？」""", [
    Choice("承認", "red_knows_lake"),
    Choice("否認", "red_ignorant"),
    Choice("反問她怎麼知道", "red_how_know"),
])

scene("red_knows_lake", """「我就知道。」她說。
「我是紅。你去過鏡湖，那你一定也看過洞穴裡的東西。」
「你知道它們在說什麼嗎？」""", [
    Choice("說你知道迴廊", "red_corridor", {"knowledge": 5, "bond_red": 10}),
    Choice("說你不太確定", "red_uncertain"),
])

scene("red_corridor", """紅點點頭。
「聰明。」她從攤位下面拿出一個布包。
「如果你要去迴廊，你需要這個。」
布包裡是一張舊地圖。""", [
    Choice("收下地圖", "market", {"item": "迴廊地圖", "bond_red": 15}),
    Choice("問那個回來的人去哪了", "red_where"),
])

scene("red_where", """「他回來之後，就坐在市集角落，一直看著天空。」
「三天後，他就消失了。」""", [
    Choice("你還是要去", "corridor_entrance", {"bond_red": 10}),
    Choice("問她有沒有去過", "red_been"),
])

scene("red_been", """「我才不去。」她說。
「我聽過太多故事了。」
她遞給你一個發光的果實。「吃了它。你會需要體力。」""", [
    Choice("吃掉果實", "market", {"item": "發光果實", "hp": 20, "bond_red": 10}),
])

scene("red_uncertain", """「不確定？」她皺眉。
「那你最好在去迴廊之前搞清楚。」
「迴廊會問你問題。如果你回答不了……你就回不來了。」""", [
    Choice("問她怎麼準備", "red_prepare"),
    Choice("離開", "leave_market"),
])

scene("red_prepare", """「搞清楚你是誰。你想要什麼。你害怕什麼。」
「如果你不認識自己，你就分不清哪些是真實的。」""", [
    Choice("你認識自己", "corridor_entrance", {"knowledge": 10}),
    Choice("你不太確定", "corridor_entrance", {"sanity": -5}),
])

scene("red_ignorant", """「你騙不了我。」她說。
「沒關係。你不想說就不說。」""", [
    Choice("問她怎麼準備", "red_prepare"),
    Choice("離開", "leave_market"),
])

scene("red_how_know", """「我是紅。我賣東西。我見過很多人。」
「去過鏡湖的人，眼神都不一樣。」""", [
    Choice("承認你去過", "red_knows_lake"),
    Choice("離開", "leave_market"),
])

scene("explore_market", """你在市集裡逛。
一個老人在賣「記憶碎片」——裝在小瓶子裡的光。
一個小孩在賣「勇氣」——據說吃了會讓你不怕任何東西。
一個神秘的人在賣「迴廊的鑰匙」。
一個紅頭髮的女孩在角落裡站著。""", [
    Choice("買記憶碎片（用冰層樣本換）", "buy_memory", requires_item="冰層樣本", consume_item="冰層樣本"),
    Choice("買勇氣（代價：理智）", "buy_courage"),
    Choice("問鑰匙的價格", "ask_key_price"),
    Choice("問老人有沒有別的", "old_man_other"),
    Choice("走向紅頭髮的女孩", "red_meet"),
    Choice("離開", "leave_market"),
])

scene("old_man_other", """老人看著你。
「別的？」他想了想。
「你有什麼可以交換的？」
「我對……情感有興趣。恐懼、快樂、悲傷。」
「你有嗎？」""", [
    Choice("給他你的恐懼", "old_man_fear", skill_check=40,
          success_scene="old_man_fear_success", fail_scene="old_man_fear_fail"),
    Choice("給他你的快樂", "old_man_happy", skill_check=50,
          success_scene="old_man_happy_success", fail_scene="old_man_happy_fail"),
    Choice("離開", "leave_market"),
])

scene("old_man_fear", """你閉上眼睛。你感覺到了恐懼。""", [
    Choice("交出恐懼", "old_man_fear_success"),
    Choice("放棄", "old_man_fear_fail"),
])

scene("old_man_fear_success", """你閉上眼睛。你想起了你最害怕的東西。
你把那種恐懼從心裡拉出來，交給老人。
他接過來，舉到光線下。
「很好的恐懼。」他說。
他遞給你一瓶發光的液體。""", [
    Choice("這是什麼？", "old_man_potion"),
])

scene("old_man_fear_fail", """你試著交出恐懼。但你做不到。
你的恐懼太深了。你抓不住它。
老人搖頭。「你還沒準備好。」""", [
    Choice("離開", "leave_market"),
])

scene("old_man_happy", """你閉上眼睛。你感覺到了快樂。""", [
    Choice("交出快樂", "old_man_happy_success"),
    Choice("放棄", "old_man_happy_fail"),
])

scene("old_man_happy_success", """你閉上眼睛。你想起了你最快樂的記憶。
你把那種快樂從心裡拉出來，交給老人。
他接過來。他的眼睛亮了。
「稀有的快樂。」他說。
他遞給你一個小小的發光球體。""", [
    Choice("這是什麼？", "old_man_orb"),
])

scene("old_man_happy_fail", """你試著交出快樂。但你找不到。
你的快樂太遙遠了。它不在你手邊。
老人嘆氣。「沒關係。快樂本來就很難放手。」""", [
    Choice("離開", "leave_market"),
])

scene("old_man_potion", """「這是勇氣。」老人說。
「但和那個小孩賣的不一樣。這個不會讓你失去謹慎。」
「它會讓你在恐懼中行動。」""", [
    Choice("喝下去", "leave_market", {"item": "勇氣液", "knowledge": 10}),
])

scene("old_man_orb", """「這是記憶。」老人說。
「不是别人的。是你自己的。」
「你剛才交出的快樂。它會回來的。但可能不是以你期望的形式。」""", [
    Choice("收下球體", "leave_market", {"item": "記憶球", "knowledge": 10}),
])

scene("buy_memory", """你把冰層樣本遞給老人。
他接過來，舉到光線下。
「好東西。」他說。
他遞給你一個小瓶子。""", [
    Choice("打開瓶子", "memory_vision", {"knowledge": 20}),
])

scene("memory_vision", """你打開瓶子。
裡面的光飛出來，鑽進你的腦子。
你看到了一段記憶：一個女人在迴廊裡行走。
她停下來，說：「原來如此。」
然後她消失了。""", [
    Choice("這告訴你什麼？", "leave_market", {"knowledge": 15, "item": "記憶碎片"}),
])

scene("buy_courage", """「代價是你的理智。」小孩說。
「你確定？」""", [
    Choice("確定", "courage_eat", {"sanity": -15}),
    Choice("不確定", "explore_market"),
])

scene("courage_eat", """你吃下「勇氣」。
味道像是蜂蜜和辣椒。
你感覺自己確實不怕了。但你也感覺不到謹慎了。""", [
    Choice("前往迴廊", "corridor_entrance", {"item": "勇氣"}),
])

scene("ask_key_price", """「價格？」神秘人笑了。
「我不收錢。我收故事。」
「一個真實的故事。你親身經歷的。」""", [
    Choice("講你的故事", "key_story", skill_check=60,
          success_scene="key_got", fail_scene="key_fail"),
])

scene("key_story", "你講了一個故事。", [Choice("繼續", "leave_market")])

scene("key_got", """神秘人聽完你的故事。
「好故事。」他說。
他遞給你一把銅鑰匙。
「這是迴廊的鑰匙。使用它，你就回不來了。」""", [
    Choice("收下鑰匙", "leave_market", {"item": "迴廊鑰匙"}),
])

scene("key_fail", """神秘人搖頭。
「這個故事不夠真實。」他說。
「等你準備好再來。」""", [
    Choice("離開", "leave_market"),
])

scene("leave_market", """你離開市集。""", [
    Choice("前往鏡湖", "scene_S15"),
    Choice("前往學校", "scene_S01"),
    Choice("前往迴廊", "corridor_entrance"),
])

scene("market", """你在市集裡。""", [
    Choice("逛逛", "explore_market"),
    Choice("離開", "leave_market"),
])

# ═══════════════════════════════════════════════════
# ACT 5: 迴廊
# ═══════════════════════════════════════════════════

scene("corridor_entrance", """迴廊的入口在鏡湖下方。
你沿著路一路向下。空氣越來越冷。
你的體力在消耗。
最後，你看到了一扇門。
門上沒有把手。只有一行字：「你在找什麼？」""", [
    Choice("「答案。」", "corridor_answer", {"energy": -15}),
    Choice("「我自己。」", "corridor_self", {"energy": -15}),
    Choice("「我想回家。」", "corridor_home", {"energy": -15}),
    Choice("不回答，推門", "corridor_push"),
    Choice("使用迴廊鑰匙", "corridor_key", requires_item="迴廊鑰匙"),
    Choice("體力不足，先離開", "leave_lake", requires_no_item="發光果實"),
])

scene("corridor_key", """你把鑰匙插入門上的鎖孔。
門打開了。
你走進迴廊。
兩側的門不斷開合。每一扇門後面都是一個不同的世界。
你的腦子裡響起一個聲音：「你用鑰匙進來了。這給你一些優勢。」
「你可以多問一個問題。」""", [
    Choice("「關於我的答案」", "corridor_your_answer", {"flag": "extra_question"}),
    Choice("「關於這個世界的答案」", "corridor_world_answer", {"flag": "extra_question"}),
    Choice("「關於迴廊的答案」", "corridor_corridor_answer", {"flag": "extra_question"}),
])

scene("corridor_push", """你推門。
門沒有動。
你用力推。
門還是沒有動。
你後退一步。門上出現了新的字：「你還沒有準備好。」""", [
    Choice("「我準備好了」", "corridor_ready"),
    Choice("「告訴我怎麼準備」", "corridor_prepare"),
])

scene("corridor_ready", """「證明。」門上出現了新的字。
「告訴我你是誰。不是你的名字。不是你的過去。是你。」""", [
    Choice("「我是一個在找答案的人」", "corridor_answer"),
    Choice("「我是一個害怕的人」", "corridor_self"),
    Choice("「我是一個不想放棄的人」", "corridor_no_fear"),
])

scene("corridor_prepare", """「三個問題。」門上出現了文字。
「第一：你害怕什麼？」
「第二：你想要什麼？」
「第三：你願意付出什麼？」""", [
    Choice("回答三個問題", "corridor_questions"),
])

scene("corridor_questions", """你站在門前。你思考了很久。
最後你說：「我害怕失去。我想要理解。我願意付出我自己。」
門打開了。""", [
    Choice("走進迴廊", "corridor_inside"),
])

scene("corridor_answer", """門打開了。
你走進迴廊。兩側的門不斷開合。
聲音：「答案有很多個。你想要哪一個？」""", [
    Choice("「關於我的答案」", "corridor_your_answer"),
    Choice("「關於這個世界的答案」", "corridor_world_answer"),
    Choice("「關於迴廊的答案」", "corridor_corridor_answer"),
])

scene("corridor_self", """門打開了。
你走進迴廊。兩側的門不斷開合。
聲音：「你在這裡。你一直都在這裡。」""", [
    Choice("「我不明白」", "corridor_confused"),
    Choice("「你是誰？」", "corridor_identity"),
    Choice("閉上眼睛，感受", "corridor_feel"),
])

scene("corridor_home", """門打開了。
你走進迴廊。兩側的門不斷開合。
聲音：「家不是一個地方。家是一種狀態。」""", [
    Choice("「回到我不害怕的時候」", "corridor_no_fear"),
    Choice("「回到有人等我的時候」", "corridor_alone"),
    Choice("「回到我知道答案的時候」", "corridor_knew_answer"),
])

# ═══════════════════════════════════════════════════
# ACT 6: 迴廊內部
# ═══════════════════════════════════════════════════

scene("corridor_your_answer", """你打開一扇門。
門後面是你自己。不是現在的你。是可能成為的你。
那個你在微笑。看起來很平靜。""", [
    Choice("問那個你：你快樂嗎？", "corridor_happy"),
    Choice("問那個你：你後悔嗎？", "corridor_regret"),
    Choice("關上門", "corridor_inside"),
])

scene("corridor_happy", """那個你說：「快樂不是終點。是一種習慣。」
「你不需要找到完美的答案。你只需要找到你能接受的答案。」""", [
    Choice("謝謝你", "corridor_inside", {"knowledge": 20, "sanity": 10}),
])

scene("corridor_regret", """那個你說：「我不後悔。因為每一個選擇都帶我到了這裡。」
「你不需要走最完美的路。你只需要走你能走的路。」""", [
    Choice("謝謝你", "corridor_inside", {"knowledge": 20, "sanity": 10}),
])

scene("corridor_world_answer", """你打開一扇門。
門後面是這個世界的全貌。你看到了所有的人。所有的故事。""", [
    Choice("這太多了", "corridor_inside", {"sanity": -10}),
    Choice("記錄你看到的", "corridor_inside", {"knowledge": 25}),
])

scene("corridor_corridor_answer", """你打開一扇門。
門後面是迴廊自己。它不是一條走廊。它是一個概念。""", [
    Choice("理解了", "corridor_inside", {"knowledge": 30}),
    Choice("太抽象了", "corridor_inside"),
])

scene("corridor_confused", """聲音說：「你不需要明白。你只需要接受。」""", [
    Choice("接受", "corridor_inside", {"sanity": 5}),
])

scene("corridor_identity", """聲音：「我是迴廊。我是所有可能性的總和。」
「你也是。」""", [
    Choice("「我不明白」", "corridor_confused"),
    Choice("「我明白了」", "corridor_inside", {"knowledge": 15}),
])

scene("corridor_feel", """你閉上眼睛。
你感覺到了迴廊。它不在你外面。它在你裡面。""", [
    Choice("睜開眼睛", "corridor_inside", {"knowledge": 20, "sanity": 15}),
])

scene("corridor_no_fear", """聲音：「恐懼不是敵人。它是信使。它告訴你什麼對你重要。」""", [
    Choice("聽從恐懼", "corridor_inside", {"sanity": 10}),
])

scene("corridor_alone", """聲音：「你從來不是一個人。每一個可能性都在這裡。」
「但你不能留在這裡。因為你必須做出選擇。」""", [
    Choice("做出選擇", "corridor_inside", {"sanity": 10, "knowledge": 15}),
])

scene("corridor_knew_answer", """聲音：「你知道答案。答案是：沒有意義。」
「但沒有意義不是壞事。你可以自己創造意義。」""", [
    Choice("接受", "corridor_inside", {"knowledge": 25, "sanity": 10}),
    Choice("拒絕", "corridor_inside", {"sanity": -10}),
])

scene("corridor_inside", """你在迴廊裡站了很久。你看到了很多。你學到了很多。
最後，一扇門在你面前打開。門後面是你來的地方。
但你知道還有更多。""", [
    Choice("走出去，回到鏡湖", "ending_return"),
    Choice("留在迴廊", "ending_stay"),
    Choice("走向另一扇門", "ending_another"),
    Choice("走向迴廊深處", "corridor_deep", requires_knowledge=50),
    Choice("使用迴廊之珠", "corridor_crystal_path", requires_item="迴廊之珠"),
    Choice("使用迴廊守則", "corridor_rules_path", requires_item="迴廊守則"),
    Choice("使用照片", "corridor_photo_path", requires_item="照片"),
    Choice("帶領雷歐一起走", "ending_together", requires_bond="leo:60"),
    Choice("帶領雷德一起走", "ending_with_red", requires_bond="red:50"),
])

scene("corridor_deep", """你走向迴廊深處。
門越來越少。走廊越來越寬。
你看到了一個巨大的房間。中央有一個平台。
平台上站著一個人——是你自己。""", [
    Choice("和那個你說話", "corridor_deep_talk"),
    Choice("繞過他", "corridor_inside"),
])

scene("corridor_deep_talk", """那個你說：「你走到這裡了。」
「你比我預期的走得更遠。」
「你想知道什麼？」""", [
    Choice("「為什麼我會在這裡？」", "corridor_deep_why"),
    Choice("「迴廊的意義是什麼？」", "corridor_deep_meaning"),
    Choice("「我該怎麼回去？」", "corridor_deep_return"),
])

scene("corridor_deep_why", """那個你說：「因為你選擇了。」
「每一個選擇都是一條路。你選了最難的那條。」
「但也是最有意義的那條。」""", [
    Choice("「謝謝你」", "corridor_inside", {"knowledge": 30, "sanity": 15}),
])

scene("corridor_deep_meaning", """那個你說：「迴廊沒有意義。」
「但它讓你有機會創造意義。」
「這就是它的意義。」""", [
    Choice("接受", "corridor_inside", {"knowledge": 25, "sanity": 10}),
])

scene("corridor_deep_return", """那個你說：「回去？」
「你不需要回去。你需要向前走。」
「回去是給那些不敢面對的人的。」""", [
    Choice("「我明白了」", "corridor_inside", {"knowledge": 20}),
    Choice("「我還是想回去」", "ending_return", {"sanity": -10}),
])

scene("corridor_crystal_path", """你舉起迴廊之珠。
珠子發出藍光。迴廊的門開始重新排列。
你面前出現了一條新的路。""", [
    Choice("走上新路", "ending_crystal", {"knowledge": 20}),
    Choice("回到原處", "corridor_inside"),
])

scene("corridor_rules_path", """你翻開迴廊守則。
守則上的文字開始發光。
你感覺到了迴廊的規則在你腦中運轉。""", [
    Choice("使用規則的力量", "ending_rules", {"knowledge": 25}),
    Choice("回到原處", "corridor_inside"),
])

scene("corridor_photo_path", """你拿出照片。
照片上的人們開始動了起來。
他們轉頭看著你。
「你找到了他們的鑰匙。」聲音說。""", [
    Choice("和照片裡的人說話", "ending_photo", {"knowledge": 15}),
    Choice("回到原處", "corridor_inside"),
])

# ═══════════════════════════════════════════════════
# 結局
# ═══════════════════════════════════════════════════

scene("ending_return", """你走出迴廊。
鏡湖依然平靜。但你知道湖底有什麼。
你回頭看了一眼。它正在關閉。
你轉身離開。你帶走了理解。你回到了你來的地方。但你已經不同了。""", [
    Choice("結束", None, {"ending": "return"}),
])

scene("ending_stay", """你留在迴廊。
兩側的門不斷開合。每一個世界都在你面前展開。
你開始走向每一扇門。也許有一天你會找到你想留下的世界。""", [
    Choice("結束", None, {"ending": "stay"}),
])

scene("ending_another", """你走向另一扇門。
門後面是一個你從未見過的世界。那裡有天空。真正的天空。
你深吸一口氣。空氣是甜的。你笑了。""", [
    Choice("結束", None, {"ending": "another"}),
])

scene("ending_crystal", """你走向新路。
路的盡頭是一扇門。門上刻著迴廊的標誌。
你推開門。門後面是一片星空。
你站在虛空中。四周都是星星。
你知道你找到了迴廊的核心。""", [
    Choice("在星空中漫步", "ending_star", {"knowledge": 30}),
    Choice("回到迴廊", "corridor_inside"),
])

scene("ending_star", """你在星空中走了很久。
你看到了無數的世界。無數的可能性。
最後，你找到了一個小光點。
你伸出手。光點在你手裡發光。""", [
    Choice("帶著光點離開", "ending_light", {"item": "迴廊之光"}),
    Choice("留在星空中", "ending_stay"),
])

scene("ending_light", """你帶著迴廊之光回到了鏡湖。
湖水在你面前裂開。你走了進去。
你回到了你來的地方。但你手裡的光在閃爍。
你知道你帶回了某種珍貴的東西。""", [
    Choice("結束", None, {"ending": "light"}),
])

scene("ending_rules", """你使用了迴廊守則的力量。
迴廊的規則在你腦中運轉。
你看到了迴廊的全貌——它不是一條走廊，它是一個活的存在。
它在呼吸。它在思考。它在等待。""", [
    Choice("和迴廊對話", "ending_rules_talk"),
    Choice("離開迴廊", "ending_return"),
])

scene("ending_rules_talk", """你對迴廊說：「我理解你了。」
迴廊回答：「你理解了。但你接受嗎？」
「我是所有可能性的總和。包括你害怕的那些。」""", [
    Choice("我接受", "ending_accept", {"sanity": 20, "knowledge": 30}),
    Choice("我害怕", "ending_fear"),
])

scene("ending_accept", """你深呼吸。你接受了迴廊。
包括它的美。它的醜。它的複雜。它的簡單。
你知道你永遠不會完全理解它。但你可以和它共存。""", [
    Choice("結束", None, {"ending": "accept"}),
])

scene("ending_fear", """你說：「我害怕。」
迴廊說：「恐懼是正常的。它告訴你什麼對你重要。」
「但你不能讓恐懼定義你。」""", [
    Choice("克服恐懼", "ending_accept", {"sanity": 10, "knowledge": 15}),
    Choice("讓恐懼帶路", "ending_lost"),
])

scene("ending_lost", """你讓恐懼帶路。
迴廊的門在你面前關閉。
你站在黑暗中。你不知道自己在哪。
但你知道你必須繼續走。""", [
    Choice("繼續走", "ending_stay"),
    Choice("停下來", "ending_lost_forever"),
])

scene("ending_lost_forever", """你停下來。
你不再走了。
你成為了迴廊的一部分。
也許有一天，你會找到出去的路。""", [
    Choice("結束", None, {"ending": "lost"}),
])

scene("ending_photo", """照片裡的人們看著你。
他們說：「你找到了我們的鑰匙。」
「我們曾經和你一樣。我們走進了迴廊。然後我們留在了這裡。」
「你可以加入我們。」""", [
    Choice("加入他們", "ending_photo_join"),
    Choice("帶著他們離開", "ending_photo_leave"),
])

scene("ending_photo_join", """你走進照片裡。
你和他們站在一起。
你知道你不再孤獨。
你找到了你的家。""", [
    Choice("結束", None, {"ending": "photo_join"}),
])

scene("ending_photo_leave", """你把照片從迴廊裡帶了出來。
你回到了鏡湖。照片裡的人們在微笑。
你知道他們在迴廊裡。但他們的精神和你在一起。""", [
    Choice("結束", None, {"ending": "photo_leave"}),
])

scene("ending_together", """雷歐站在你身邊。
「你真的要帶我一起去？」他問。
「我……我已經在這裡太久了。」""", [
    Choice("「我們一起走」", "ending_together_go"),
    Choice("「你準備好了嗎？」", "ending_together_ready"),
])

scene("ending_together_go", """你和雷歐一起走向另一扇門。
門後面是一個新的世界。
你們倆都深吸一口氣。
「我們做到了。」雷歐說。""", [
    Choice("結束", None, {"ending": "together"}),
])

scene("ending_together_ready", """雷歐想了一會兒。
「我不知道。」他說。
「但有你在，我覺得我可以試試。」""", [
    Choice("「那就走吧」", "ending_together_go"),
    Choice("「你再想想」", "corridor_inside"),
])

scene("ending_with_red", """雷德站在你身邊。
「你要走了嗎？」她問。
「我想和你一起去。」""", [
    Choice("「一起走」", "ending_with_red_go"),
    Choice("「你確定嗎？」", "ending_with_red_sure"),
])

scene("ending_with_red_go", """你和雷德一起走向另一扇門。
門後面是一個新的世界。
雷德笑了。「我從來沒想過我會離開市集。」""", [
    Choice("結束", None, {"ending": "with_red"}),
])

scene("ending_with_red_sure", """「我確定。」雷德說。
「我不想再留在市集了。我想看看外面的世界。」
「而且……我想和你一起走。」""", [
    Choice("「走吧」", "ending_with_red_go"),
    Choice("「你再想想」", "corridor_inside"),
])


# ═══════════════════════════════════════════════════
# ACT 7: 隱藏路線 — 更多場景和選擇
# ═══════════════════════════════════════════════════

# --- Item-usage mechanics ---

scene("dark_hallway", """你走在一條完全黑暗的走廊裡。
腳下的地面不平。你聽到了水滴聲。
沒有光源你什麼都看不見。""", [
    Choice("用手電筒照亮", "dark_hallway_lit", requires_item="手電筒",
          consume_item="手電筒", effects={"energy": -5, "flag": "lit_hallway"}),
    Choice("摸黑前進", "dark_hallway_dark", {"hp": -15, "sanity": -10}),
    Choice("回到原處", "leave_lake"),
])

scene("dark_hallway_lit", """手電筒照亮了走廊。
你看到了牆壁上的壁畫——描繪了一個巨大的迴廊。
走廊盡頭有一扇門，門上有三道鎖。
每道鎖旁邊都有一個符號：太陽、月亮、星星。""", [
    Choice("用太陽鑰匙開第一道鎖", "hallway_lock_1", requires_item="太陽鑰匙",
          consume_item="太陽鑰匙"),
    Choice("強行撬鎖", "hallway_lock_pry", skill_check=60),
    Choice("觀察壁畫尋找線索", "hallway_mural", {"knowledge": 15}),
    Choice("離開", "leave_lake"),
])

scene("dark_hallway_dark", """你摸黑前進。手撞到了牆壁，腳踩到了什麼濕滑的東西。
你聽到了嘶嘶聲——蛇？蟲？你不知道。
你跌倒了。膝蓋撞在地上。很痛。""", [
    Choice("繼續前進", "hallway_lock_1", {"hp": -10}),
    Choice("退回", "leave_lake", {"hp": -5}),
])

scene("hallway_lock_1", """第一道鎖打開了。
門上的太陽符號發出微弱的光。
你聽到了機械運轉的聲音——門在解鎖。""", [
    Choice("用月亮鑰匙開第二道鎖", "hallway_lock_2", requires_item="月亮鑰匙",
          consume_item="月亮鑰匙"),
    Choice("嘗試推門", "hallway_push_fail"),
    Choice("觀察門的結構", "hallway_lock_observe", {"knowledge": 10}),
    Choice("觀察壁畫尋找線索", "hallway_mural", {"knowledge": 15}),
])

scene("hallway_mural", """你仔細觀察走廊上的壁畫。
壁畫描繪了一個人走進迴廊的過程。
你注意到壁畫上有三個符號：太陽、月亮、星星。
每個符號旁邊都有一個小人——似乎在做某種動作。
太陽旁邊的小人在祈祷。月亮旁邊的小人在等待。星星旁邊的小人在跳躍。""", [
    Choice("記住這個線索", "hallway_lock_1", {"knowledge": 20}),
    Choice("離開", "leave_lake"),
])

scene("hallway_push_fail", """你推門。門紋絲不動。
還有兩道鎖。你必須找到鑰匙。""", [
    Choice("用小刀撬鎖", "hallway_lock_pry", skill_check=60),
    Choice("離開", "leave_lake"),
])

scene("hallway_lock_observe", """你觀察門的結構。
三道鎖是連鎖的——開了第一道才能開第二道。
每道鑰匙對應一個符號。你注意到鎖孔裡有某種殘留物。""", [
    Choice("用小刀清理鎖孔", "hallway_lock_clean"),
    Choice("離開", "leave_lake"),
])

scene("hallway_lock_clean", """你用小刀清理了鎖孔。
裡面有乾涸的液體——可能是很久以前有人嘗試過。
你在殘留物中發現了一個微小的符號：迴廊的標誌。""", [
    Choice("記住這個線索", "hallway_lock_2", {"knowledge": 15, "item": "鎖孔殘留物"}),
    Choice("繼續嘗試開鎖", "hallway_lock_2"),
])

scene("hallway_lock_2", """第二道鎖打開了。
月亮符號也亮了。
現在只剩下最後一道鎖——星星。""", [
    Choice("用星星鑰匙開最後一道鎖", "hallway_lock_3", requires_item="星星鑰匙",
          consume_item="星星鑰匙"),
    Choice("用小刀強行撬鎖", "hallway_lock_pry", skill_check=80),
    Choice("觀察周圍", "hallway_lock_surround"),
])

scene("hallway_lock_surround", """你觀察周圍。
走廊兩側的壁畫上，星星的數量在變化——有些是5角，有些是6角。
你數了數。6角星對應門上的鎖孔。""", [
    Choice("用這個知識嘗試撬鎖", "hallway_lock_pry", skill_check=60),
    Choice("繼續找鑰匙", "hallway_lock_3"),
])

scene("hallway_lock_3", """第三道鎖打開了。
三道符號同時發光。
門緩緩打開。你看到了迴廊的入口——一個發光的藍色漩渦。""", [
    Choice("走進漩渦", "corridor_entrance", {"knowledge": 20, "energy": -10}),
    Choice("先休息一下", "hallway_rest", {"energy": 15}),
    Choice("回到湖邊", "leave_lake"),
])

scene("hallway_lock_pry", """你嘗試撬鎖。""", [
    Choice("成功", "hallway_lock_pry_success"),
    Choice("失敗", "hallway_lock_pry_fail"),
])

scene("hallway_lock_pry_success", """咔嚓。
鎖彈開了。你聽到了機械運轉的聲音。
門緩緩打開。""", [
    Choice("走進去", "corridor_entrance", {"knowledge": 15}),
])

scene("hallway_lock_pry_fail", """你的小刀卡住了。
鎖紋絲不動。刀片上有了一個缺口。""", [
    Choice("放棄，找鑰匙", "hallway_lock_2"),
    Choice("離開", "leave_lake"),
])

scene("hallway_rest", """你靠在牆壁上休息。
手電筒的光在天花板上投射出搖曳的影子。
你聽到遠處有腳步聲。""", [
    Choice("等待", "hallway_stranger"),
    Choice("繼續前進", "corridor_entrance"),
])

scene("hallway_stranger", """一個身影出現了。
是一個穿著制服的人。他看著你。
「你也是來找迴廊的？」他問。""", [
    Choice("「是的」", "hallway_stranger_talk"),
    Choice("「你是誰？」", "hallway_stranger_who"),
    Choice("不回答，離開", "corridor_entrance"),
])

scene("hallway_stranger_who", """「我叫雷歐。」他說。
「我是守衛。負責保護迴廊的入口。」
「很久沒有人來了。」""", [
    Choice("「為什麼沒人來？」", "hallway_stranger_why"),
    Choice("「你能幫我嗎？」", "hallway_stranger_help"),
    Choice("離開", "corridor_entrance"),
])

scene("hallway_stranger_why", """「因為大家都忘了。」雷歐說。
「迴廊不是一條路。它是一個問題。」
「只有敢問問題的人才會來這裡。」""", [
    Choice("「你問過嗎？」", "hallway_stranger_asked"),
    Choice("「我想問問題」", "hallway_stranger_help", {"knowledge": 10}),
])

scene("hallway_stranger_asked", """「我問過。」雷歐說。
「但我的答案不一定是你的答案。」
「每個人的迴廊都不一樣。」""", [
    Choice("「謝謝你」", "corridor_entrance", {"knowledge": 15, "bond_leo": 15}),
    Choice("「你能告訴我答案嗎？」", "hallway_stranger_answer"),
])

scene("hallway_stranger_answer", """雷歐搖頭。
「如果我告訴你答案，那就不會是你的答案。」
「你必須自己走進去。」""", [
    Choice("「我明白了」", "corridor_entrance", {"knowledge": 10, "bond_leo": 10}),
])

scene("hallway_stranger_talk", """「太好了。」雷歐說。
「我以為我會在這裡一個人待一輩子。」
「你想聽聽我的故事嗎？」""", [
    Choice("聽他的故事", "hallway_stranger_story"),
    Choice("直接進入迴廊", "corridor_entrance"),
])

scene("hallway_stranger_story", """雷歐告訴你他的故事。
他曾經是一個考古學家。他發現了迴廊的入口。
然後他就留在了這裡。
「因為我害怕。」他說。「我害怕進去之後就回不來了。」""", [
    Choice("「你現在還怕嗎？」", "hallway_stranger_fear"),
    Choice("「我會幫你克服恐懼」", "hallway_stranger_brave", {"bond_leo": 20}),
])

scene("hallway_stranger_fear", """「不怕了。」雷歐說。
「我已經習慣了。」
「但你不同。你還年輕。你應該進去。」""", [
    Choice("「謝謝你」", "corridor_entrance", {"knowledge": 15, "bond_leo": 15}),
])

scene("hallway_stranger_brave", """「真的嗎？」雷歐的眼睛亮了。
「你願意幫我？」
「我……我不知道。我已經在這裡太久了。」""", [
    Choice("「我們一起進去」", "corridor_entrance", {"bond_leo": 30, "knowledge": 10}),
    Choice("「你先準備好」", "corridor_entrance", {"bond_leo": 15}),
])

scene("hallway_stranger_help", """「幫你？」雷歐想了想。
「我可以告訴你迴廊的規則。」
「進入之後，你會遇到三個選擇。每個選擇都是一面鏡子。」""", [
    Choice("「什麼鏡子？」", "hallway_stranger_mirror"),
    Choice("「記住了」", "corridor_entrance", {"knowledge": 20, "bond_leo": 15}),
])

scene("hallway_stranger_mirror", """「第一面是過去。你會看到你曾經是什麼。」
「第二面是現在。你會看到你是什麼。」
「第三面是未來。你會看到你可能是什麼。」
「不要害怕。鏡子只是反射。」""", [
    Choice("「謝謝你」", "corridor_entrance", {"knowledge": 25, "bond_leo": 20}),
])

# --- Puzzle scenes ---

scene("puzzle_symbols", """你發現了一個石板。
上面有六個符號，但其中兩個是空白的。
你需要填入正確的符號才能解開謎題。""", [
    Choice("用小刀刻上太陽和月亮", "puzzle_fail"),
    Choice("用水晶照射石板", "puzzle_crystal", requires_item="水晶"),
    Choice("用地圖上的標記對照", "puzzle_map", requires_item="地圖"),
    Choice("放棄", "leave_lake"),
])

scene("puzzle_crystal", """你用水晶照射石板。
水晶的藍光和石板上的符號產生共鳴。
空白的符號逐漸顯現：星星和迴廊的標誌。
石板滑開。你發現了一個暗格。""", [
    Choice("取出暗格裡的東西", "puzzle_reward"),
    Choice("記錄下來", "leave_lake", {"knowledge": 25, "flag": "solved_symbols"}),
])

scene("puzzle_map", """你用地圖上的標記對照石板。
地圖上的標記和符號完全吻合。
空白的符號應該是：星星和迴廊的標誌。
你用小刀刻上去。石板滑開了。""", [
    Choice("取出暗格裡的東西", "puzzle_reward"),
    Choice("記錄下來", "leave_lake", {"knowledge": 20, "flag": "solved_symbols"}),
])

scene("puzzle_fail", """你刻了太陽和月亮。
石板沒有反應。
你看著錯誤的符號，嘆了口氣。""", [
    Choice("用水晶嘗試", "puzzle_crystal", requires_item="水晶"),
    Choice("用地圖嘗試", "puzzle_map", requires_item="地圖"),
    Choice("放棄", "leave_lake", {"sanity": -5}),
])

scene("puzzle_reward", """暗格裡有一張紙條和一顆小珠子。
紙條上寫著：「迴廊的鑰匙不是物理的。它是一種理解。」
珠子發出微弱的藍光。""", [
    Choice("收下珠子", "leave_lake", {"item": "迴廊之珠", "knowledge": 15}),
    Choice("只記住紙條的話", "leave_lake", {"knowledge": 20}),
])

# --- Combat encounters ---

scene("shadow_encounter", """你面前出現了一個陰影。
它不是人形。它是一個概念——你內心深處的恐懼凝聚而成。
它向你逼近。""", [
    Choice("用小刀攻擊", "shadow_fight", {"hp": -20}),
    Choice("用水晶照射", "shadow_crystal", requires_item="水晶"),
    Choice("逃跑", "shadow_flee", {"hp": -10, "energy": -15}),
    Choice("面對它", "shadow_face", {"sanity": -15}),
    Choice("叫雷德幫忙", "shadow_red_help", requires_bond="red:40"),
    Choice("叫雷歐幫忙", "shadow_leo_help", requires_bond="leo:40"),
    Choice("使用迴廊之珠", "shadow_pearl", requires_item="迴廊之珠"),
])

scene("shadow_red_help", """雷德衝到你面前。
「我來幫你！」她舉起拳頭。
陰影後退了一步。""", [
    Choice("一起攻擊", "shadow_team_attack", {"hp": -10, "bond_red": 10}),
    Choice("趁機逃跑", "dark_hallway", {"energy": -10}),
])

scene("shadow_team_attack", """你和雷德一起攻擊陰影。
陰影發出了尖叫。
它開始溶解。""", [
    Choice("繼續攻擊", "shadow_defeat", {"knowledge": 15, "sanity": 10}),
])

scene("shadow_leo_help", """雷歐站到你面前。
「別怕。」他說。
他舉起手。一道光從他手裡射出。
陰影被光吞噬了。""", [
    Choice("看著陰影消失", "shadow_after", {"knowledge": 20, "sanity": 15, "bond_leo": 15}),
])

scene("shadow_pearl", """你舉起迴廊之珠。
珠子發出強烈的藍光。
陰影被光吞噬了。它消失了。""", [
    Choice("繼續前進", "dark_hallway", {"knowledge": 25, "sanity": 20}),
])

scene("shadow_fight", """你衝向陰影，用小刀刺向它。
刀穿過了它的身體——它沒有實體。
但你的攻擊讓它暫時後退了。""", [
    Choice("繼續攻擊", "shadow_defeat", {"hp": -15}),
    Choice("趁機逃跑", "dark_hallway", {"energy": -10}),
])

scene("shadow_crystal", """你舉起水晶。藍光照亮了陰影。
陰影發出了尖銳的叫聲。
它開始溶解。藍光吞噬了它。""", [
    Choice("看著它消失", "shadow_after", {"knowledge": 15, "sanity": 10}),
])

scene("shadow_flee", """你轉身就跑。
身後的陰影在追你。你聽到了它的呼吸聲。
你跑了很久，直到你聽不到它為止。""", [
    Choice("停下來喘氣", "dark_hallway", {"sanity": -5}),
])

scene("shadow_face", """你站住不動。你面對陰影。
它逼近你。你感覺到冰冷的氣息。
然後，它開始說話。「你是誰？」""", [
    Choice("「我是我」", "shadow_defeat", {"knowledge": 20, "sanity": 10}),
    Choice("「我不知道」", "shadow_defeat", {"sanity": -5}),
])

scene("shadow_defeat", """陰影散去了。
你站在原地，喘著氣。
你感覺到了某種變化——你比之前更強了。""", [
    Choice("繼續前進", "dark_hallway", {"knowledge": 10, "sanity": 5}),
])

scene("shadow_after", """陰影消失了。
你站在原地。你感覺到了某種東西——不是恐懼，是理解。
恐懼是信使。它告訴你什麼對你重要。""", [
    Choice("繼續前進", "dark_hallway", {"knowledge": 15}),
])

# --- NPC dialogue trees ---

scene("red_meet", """你走向那個紅頭髮的女孩。
她看著你。她的眼睛很亮。
「你好。」她說。
「我叫雷德。你是新來的嗎？」""", [
    Choice("「是的」", "red_talk"),
    Choice("「你是誰？」", "red_who"),
    Choice("「這裡是哪裡？」", "red_where"),
    Choice("離開", "leave_market"),
])

scene("red_who", """「我叫雷德。」她說。
「我以前是學生。然後我來到了這裡。」
「你呢？你以前是做什麼的？」""", [
    Choice("「我是個普通人」", "red_normal"),
    Choice("「我是個探索者」", "red_explorer"),
    Choice("不回答", "red_talk"),
])

scene("red_normal", """「普通人？」雷德笑了。
「普通人不會來到迴廊。」
「你一定有什麼特別的地方。」""", [
    Choice("「也許吧」", "red_talk", {"bond_red": 10}),
])

scene("red_explorer", """「探索者？」雷德的眼睛亮了。
「我喜歡探索。」
「你知道嗎？市集裡有很多可以探索的東西。」""", [
    Choice("「告訴我」", "red_explore", {"bond_red": 15}),
    Choice("「謝謝你」", "leave_market"),
])

scene("red_explore", """「市集裡有一個老人在賣記憶。」雷德說。
「還有一個小孩在賣勇氣。」
「最有趣的是那個賣迴廊鑰匙的人。」""", [
    Choice("「鑰匙在哪裡？」", "red_key"),
    Choice("「謝謝你」", "leave_market", {"knowledge": 10}),
])

scene("red_key", """「鑰匙？」雷德想了想。
「我聽說鑰匙在鏡湖底下。」
「但我不確定。我從來沒去過鏡湖。」""", [
    Choice("「你想一起去嗎？」", "red_join", requires_bond="red:30"),
    Choice("「謝謝你」", "leave_market", {"knowledge": 10}),
])

scene("red_join", """「真的嗎？」雷德驚訝地說。
「你願意帶我去？」
「好！我跟你一起去！」""", [
    Choice("一起出發", "lake_to_market", {"bond_red": 20, "flag": "red_joined"}),
])

scene("lake_to_market", """你和雷德一起走向市集。
路上她告訴你很多關於迴廊的事。
「我聽說迴廊有三道門。」她說。
「第一道是過去。第二道是現在。第三道是未來。」""", [
    Choice("抵達市集", "scene_S17", {"knowledge": 10}),
])

scene("red_talk", """「你看起來很困惑。」雷德說。
「沒關係。每個人都很困惑。」
「你知道嗎？困惑是好事。它意味著你在思考。」""", [
    Choice("「你很聰明」", "red_flatter", {"bond_red": 10}),
    Choice("「謝謝你」", "leave_market"),
])

scene("red_flatter", """雷德笑了。
「謝謝。你也很會說話。」
「我們可以做朋友嗎？」""", [
    Choice("「當然」", "leave_market", {"bond_red": 20}),
    Choice("「再看看」", "leave_market", {"bond_red": 5}),
])

# --- More exploration scenes ---

scene("abandoned_lab", """你發現了一個廢棄的實驗室。
桌子上有文件、試管、和一個破碎的屏幕。
文件上寫著某種研究計畫——關於「意識轉移」。""", [
    Choice("閱讀文件", "lab_files", {"knowledge": 20}),
    Choice("檢查試管", "lab_tubes"),
    Choice("嘗試修復屏幕", "lab_screen", skill_check=50),
    Choice("離開", "leave_lake"),
    Choice("用小刀撬開抽屜", "lab_drawer", requires_item="小刀"),
    Choice("用手電筒照亮暗處", "lab_dark", requires_item="手電筒"),
])

scene("lab_drawer", """你用小刀撬開了鎖住的抽屜。
裡面有一個筆記本和一個小瓶子。
筆記本上記錄了實驗的細節。""", [
    Choice("閱讀筆記本", "lab_notebook"),
    Choice("帶走小瓶子", "leave_lake", {"item": "實驗液體", "knowledge": 10}),
])

scene("lab_notebook", """筆記本上記錄了實驗的過程。
最後一頁寫著：「實驗失敗了。但我們發現了迴廊。」
「迴廊不是我們創造的。它一直都在。」""", [
    Choice("記錄這個發現", "leave_lake", {"knowledge": 15, "flag": "lab_notebook_read"}),
    Choice("帶著筆記本離開", "leave_lake", {"item": "實驗筆記", "knowledge": 10}),
])

scene("lab_dark", """你用手電筒照亮實驗室的暗處。
你發現了一個隱藏的門。
門上寫著「緊急出口」。""", [
    Choice("打開門", "lab_emergency"),
    Choice("不碰，離開", "leave_lake"),
])

scene("lab_emergency", """你打開了緊急出口。
門後面是一條走廊，通向地下。
你走了下去。""", [
    Choice("繼續", "underground_entrance"),
])

scene("lab_files", """文件描述了一個實驗：將人類意識轉移到數位世界。
研究者認為這是逃避死亡的方法。
最後一頁寫著：「實驗失敗了。意識沒有轉移。但迴廊被打開了。」""", [
    Choice("記錄這個發現", "leave_lake", {"knowledge": 15, "flag": "lab_discovery"}),
    Choice("帶著文件離開", "leave_lake", {"item": "實驗文件", "knowledge": 10}),
])

scene("lab_tubes", """你檢查試管。
裡面有某種液體。有些是藍色的，有些是紅色的。
你不知道它們是什麼。但你看起來很危險。""", [
    Choice("帶走藍色液體", "leave_lake", {"item": "藍色液體"}),
    Choice("帶走紅色液體", "leave_lake", {"item": "紅色液體"}),
    Choice("不碰任何東西", "leave_lake"),
])

scene("lab_screen", """你嘗試修復屏幕。
你找到了問題——一根斷裂的電纜。
你把電纜接上。屏幕亮了。""", [
    Choice("查看屏幕內容", "lab_screen_content"),
    Choice("離開", "leave_lake"),
])

scene("lab_screen_content", """屏幕上顯示了一段影片。
影片中是一個穿白袍的人。
「如果你在看這個，說明實驗失敗了。」
「迴廊被打開了。但我們關不上它。」
「請幫我們關上它。」""", [
    Choice("「我會試試」", "leave_lake", {"knowledge": 25, "flag": "lab_mission"}),
    Choice("「這不是我的問題」", "leave_lake", {"sanity": -10}),
])

scene("abandoned_house", """你發現了一棟廢棄的房子。
門是開著的。你走了進去。
裡面有家具、照片、和一個舊電視。""", [
    Choice("查看照片", "house_photos"),
    Choice("打開電視", "house_tv", requires_item="乾糧"),
    Choice("搜索抽屜", "house_drawers"),
    Choice("離開", "leave_lake"),
    Choice("用小刀撬開鎖住的櫃子", "house_cabinet", requires_item="小刀"),
    Choice("用手電筒照亮閣樓", "house_attic", requires_item="手電筒"),
])

scene("house_cabinet", """你用小刀撬開了鎖住的櫃子。
裡面有一個舊盒子和一封信。
信上寫著：「給未來的探索者。」""", [
    Choice("閱讀信", "house_letter"),
    Choice("打開盒子", "house_box"),
])

scene("house_letter", """信上寫著：
「如果你在看這封信，說明你已經走到了這裡。」
「迴廊不是一條路。它是一個問題。」
「不要害怕。你會找到答案的。」""", [
    Choice("收下信", "leave_lake", {"knowledge": 15, "flag": "house_letter_read"}),
])

scene("house_box", """你打開盒子。
裡面有一把小鑰匙和一張照片。
照片上是一群人站在迴廊入口前。""", [
    Choice("收下鑰匙和照片", "leave_lake", {"item": "小鑰匙", "item2": "照片", "knowledge": 10}),
])

scene("house_attic", """你用手電筒照亮閣樓。
閣樓上有一張桌子和一個舊筆記本。
筆記本上記錄了一個家庭的故事。""", [
    Choice("閱讀筆記本", "house_diary"),
    Choice("離開", "leave_lake"),
])

scene("house_diary", """筆記本上記錄了一個家庭的故事。
最後一段寫著：「我們必須離開。迴廊在召喚我們。」
「如果你找到了這個，請幫我們關上它。」""", [
    Choice("記錄這個發現", "leave_lake", {"knowledge": 20, "flag": "house_diary_read"}),
    Choice("帶著筆記本離開", "leave_lake", {"item": "家庭筆記", "knowledge": 15}),
])

scene("house_photos", """照片上是一家人。
父母、孩子、和一個老人。
他們看起來很幸福。
照片背面寫著日期——很久以前。""", [
    Choice("繼續探索", "house_drawers", {"sanity": -5}),
    Choice("離開", "leave_lake"),
])

scene("house_tv", """你打開電視。屏幕閃爍了一下。
然後顯示了一段影片。
影片中是一個女孩在唱歌。歌詞你聽不懂。
但旋律很美。""", [
    Choice("繼續看", "house_tv_end", {"sanity": 10, "energy": 10}),
    Choice("關掉電視", "house_drawers"),
])

scene("house_tv_end", """影片結束了。屏幕變黑。
然後顯示了一行字：「謝謝你看完。」
你感覺到了某種溫暖。""", [
    Choice("繼續探索", "house_drawers"),
    Choice("離開", "leave_lake", {"sanity": 5}),
])

scene("house_drawers", """你搜索抽屜。
在一個抽屜裡你發現了一把鑰匙和一張紙條。
紙條上寫著：「這是迴廊的鑰匙。請帶走它。」""", [
    Choice("帶走鑰匙", "leave_lake", {"item": "迴廊鑰匙"}),
    Choice("不拿任何東西", "leave_lake"),
])

# --- More corridor scenes ---

scene("corridor_mirror_past", """你看到了一面鏡子。
鏡子裡是過去的你。年輕、無憂無慮。
那個你在微笑。""", [
    Choice("和過去的你說話", "corridor_mirror_past_talk"),
    Choice("走開", "corridor_inside"),
])

scene("corridor_mirror_past_talk", """過去的你說：「你還記得我嗎？」
「你曾經那麼快樂。那麼無畏。」
「發生了什麼？」""", [
    Choice("「我長大了」", "corridor_inside", {"knowledge": 10, "sanity": -5}),
    Choice("「我忘了」", "corridor_inside", {"sanity": -10}),
])

scene("corridor_mirror_present", """你看到了一面鏡子。
鏡子裡是現在的你。疲憊、困惑、但堅定。
那個你點了點頭。""", [
    Choice("和現在的你說話", "corridor_mirror_present_talk"),
    Choice("走開", "corridor_inside"),
])

scene("corridor_mirror_present_talk", """現在的你說：「你做得很好。」
「你走了這麼遠。」
「繼續走。」""", [
    Choice("「謝謝你」", "corridor_inside", {"sanity": 10, "knowledge": 10}),
])

scene("corridor_mirror_future", """你看到了一面鏡子。
鏡子裡是一片空白。未來還沒被創造。
你只看到了你自己。""", [
    Choice("和未來的你說話", "corridor_mirror_future_talk"),
    Choice("走開", "corridor_inside"),
])

scene("corridor_mirror_future_talk", """你說：「你好。」
鏡子裡的你說：「你好。」
「你在找什麼？」
「我在找答案。」""", [
    Choice("「你會找到的」", "corridor_inside", {"knowledge": 20, "sanity": 15}),
    Choice("「我不確定」", "corridor_inside", {"knowledge": 10}),
])

# --- Hidden path scenes ---

scene("hidden_path", """你發現了一條隱藏的小路。
小路很窄，只能容一個人通過。
你不知道它通向哪裡。""", [
    Choice("走進去", "hidden_path_inside"),
    Choice("回到原處", "leave_lake"),
])

scene("hidden_path_inside", """你沿著小路走。
兩側是高牆。你聽不到外面的聲音。
最後，你看到了一個房間。""", [
    Choice("進入房間", "hidden_room"),
    Choice("回到小路", "leave_lake"),
])

scene("hidden_room", """房間裡只有一張桌子和一把椅子。
桌上有一本日記。
日記的封面寫著：「迴廊守則」。""", [
    Choice("閱讀日記", "hidden_diary"),
    Choice("離開", "leave_lake"),
])

scene("hidden_diary", """日記裡記錄了迴廊的規則：
1. 迴廊是活的。它會思考。
2. 你的選擇會影響迴廊。
3. 迴廊會給你你應得的答案。
4. 不要試圖作弊。迴廊知道。
5. 最重要的規則：相信自己。""", [
    Choice("記錄這些規則", "leave_lake", {"knowledge": 30, "flag": "knows_rules"}),
    Choice("帶著日記離開", "leave_lake", {"item": "迴廊守則", "knowledge": 20}),
])

# --- Food/rest scenes ---

scene("rest_campfire", """你找到了一個營火。
火還在燃燒。你坐下來休息。""", [
    Choice("吃乾糧", "rest_eat", requires_item="乾糧", consume_item="乾糧",
          effects={"energy": 30, "hp": 10}),
    Choice("只是休息", "rest_sleep", {"energy": 20}),
    Choice("觀察周圍", "rest_observe"),
])

scene("rest_eat", """你吃了乾糧。
感覺好多了。你的體力恢復了。""", [
    Choice("繼續休息", "rest_sleep"),
    Choice("繼續前進", "leave_lake"),
])

scene("rest_sleep", """你躺下來睡了一會兒。
你夢到了鏡湖。湖水是藍色的。
你在湖底看到了迴廊的入口。""", [
    Choice("繼續睡", "rest_dream"),
    Choice("醒來", "leave_lake", {"energy": 15}),
])

scene("rest_dream", """你在夢裡走進了迴廊。
迴廊和你之前看到的不一樣。
它更亮。更寬。更溫暖。""", [
    Choice("在夢裡探索", "rest_dream_explore"),
    Choice("醒來", "leave_lake", {"knowledge": 10, "energy": 10}),
])

scene("rest_dream_explore", """你在夢裡走了很久。
你看到了很多門。每扇門後面都是一個世界。
你推開了一扇門。""", [
    Choice("門後面是什麼？", "rest_dream_end"),
])

scene("rest_dream_end", """門後面是你最想看到的東西。
你笑了。你知道這只是夢。但你不在乎。""", [
    Choice("醒來", "leave_lake", {"sanity": 15, "knowledge": 15}),
])

scene("rest_observe", """你觀察周圍。
營火的火焰在跳動。你聽到了遠處的水聲。
你看起來很安全。""", [
    Choice("繼續休息", "rest_sleep"),
    Choice("離開", "leave_lake"),
])

# --- More lake scenes ---

scene("lake_deep", """你潛入湖底。
水很冷。你看到了湖底的石頭和水草。
在深處，你看到了一個發光的入口。""", [
    Choice("游向入口", "lake_entrance", requires_item="手電筒"),
    Choice("浮出水面", "scene_S01", {"energy": -10}),
])

scene("lake_entrance", """你游向入口。
入口是一個發光的藍色漩渦。
你游了進去。""", [
    Choice("進入漩渦", "corridor_entrance", {"energy": -20}),
])

scene("lake_surface", """你在湖面上。
湖水很平靜。你看到了倒影。
你看到的不是你自己——是迴廊。""", [
    Choice("跳入湖中", "lake_deep", {"energy": -15}),
    Choice("沿著湖邊走", "scene_S01"),
    Choice("觀察倒影", "lake_reflection", {"knowledge": 10}),
])

scene("lake散步", """你沿著湖邊走。
湖面很平靜。你看到了遠處有一個營火的煙。
你聽到了市集的方向有人聲。""", [
    Choice("走向營火", "rest_campfire"),
    Choice("走向市集", "scene_S04"),
    Choice("回到湖邊", "lake_approach"),
    Choice("探索湖邊的廢棄實驗室", "abandoned_lab"),
])

scene("scene_S04", """你走向市集的方向。
路上你經過了一些廢棄的建築。
最後你看到了市集的入口。""", [
    Choice("進入市集", "scene_S17"),
    Choice("探索廢棄建築", "abandoned_house"),
    Choice("回到湖邊", "lake散步"),
])

scene("lake_reflection", """你仔細觀察倒影。
倒影裡的迴廊和你之前看到的不一樣。
它有更多的門。更多的可能性。""", [
    Choice("跳入湖中", "lake_deep", {"energy": -15}),
    Choice("離開", "scene_S01"),
])


# ═══════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def print_wrapped(text, width=60):
    for line in text.strip().split("\n"):
        if not line.strip():
            print()
            continue
        words = line.split()
        current = ""
        for w in words:
            if len(current) + len(w) + 1 > width:
                print("  " + current)
                current = w
            else:
                current = (current + " " + w).strip()
        if current:
            print("  " + current)

def show_stats(state):
    hp_bar = "█" * (state.hp // 10) + "░" * (10 - state.hp // 10)
    san_bar = "█" * (state.sanity // 10) + "░" * (10 - state.sanity // 10)
    en_bar = "█" * (state.energy // 10) + "░" * (10 - state.energy // 10)
    print(f"  HP: {hp_bar} {state.hp}/{state.max_hp}")
    print(f"  理智: {san_bar} {state.sanity}/100")
    print(f"  體力: {en_bar} {state.energy}/100")
    print(f"  知識: {state.knowledge}/100")
    if state.bonds:
        bonds = ", ".join(f"{k}:{v}" for k, v in state.bonds.items())
        print(f"  關係: {bonds}")
    active_items = [i for i in state.inventory if i not in state.used_items]
    if active_items:
        print(f"  物品: {', '.join(active_items)}")
    if state.used_items:
        print(f"  已用: {', '.join(state.used_items)}")

def apply_effects(state, effects):
    for key, val in effects.items():
        if key.startswith("_"):
            if key == "_consume":
                state.use_item(val)
            elif key == "_remember":
                state.remember(val[0], val[1])
            elif key == "_forget":
                if val[0] in state.npc_memory and val[1] in state.npc_memory[val[0]]:
                    state.npc_memory[val[0]].remove(val[1])
            continue
        if key == "hp":
            state.modify_hp(val)
        elif key == "sanity":
            state.modify_sanity(val)
        elif key == "knowledge":
            state.modify_knowledge(val)
        elif key == "energy":
            state.modify_energy(val)
        elif key.startswith("item") and val not in state.inventory:
            state.inventory.append(val)
        elif key == "flag":
            state.set(val)
        elif key == "ending":
            state.ending = val
        elif key.startswith("bond_"):
            npc = key[5:]
            state.bond(npc, val)


def main():
    print("\n╔══════════════════════════════════╗")
    print("║    迴廊之弦                      ║")
    print("║    Corridor of Strings            ║")
    print("╚══════════════════════════════════╝")
    print()
    print("  一個關於選擇、記憶和可能性的故事。")
    print("  你的選擇會影響物品、知識、關係和結局。")
    print()
    input("  按 Enter 開始...")

    state = GameState()
    scene_id = "start"

    while scene_id and scene_id in SCENES:
        scene_data = SCENES[scene_id]
        clear()

        # Show narrative
        print("\n" + "=" * 50)
        print_wrapped(scene_data["narrative"])
        print("=" * 50)
        show_stats(state)
        print("-" * 50)

        # Filter available choices
        all_choices = scene_data["choices"]
        available = [c for c in all_choices if c.is_available(state)]

        if not available:
            print("\n  你沒有任何可以做的事。")
            input("  按 Enter 繼續...")
            break

        # Show choices
        for i, c in enumerate(available, 1):
            marker = ""
            if c.requires_item:
                marker = f" [需要: {c.requires_item}]"
            elif c.requires_knowledge:
                marker = f" [需要知識: {c.requires_knowledge}]"
            print(f"  {i}) {c.text}{marker}")
        print()

        # Get input
        while True:
            ch = input("  > ").strip()
            if ch.isdigit() and 1 <= int(ch) <= len(available):
                break
            if ch.lower() in ("q", "quit", "exit"):
                scene_id = None
                break
            # Eat food command
            if ch.lower() in ("eat", "吃", "吃東西"):
                food_items = [i for i in state.inventory if i in ("乾糧", "發光果實", "勇氣液") and i not in state.used_items]
                if food_items:
                    item = food_items[0]
                    state.use_item(item)
                    state.modify_energy(30)
                    print(f"\n  [吃了 {item}。體力 +30]")
                else:
                    print("\n  [沒有可以吃的東西]")
                continue

        if scene_id is None:
            break

        # Apply choice
        choice = available[int(ch) - 1]
        effects = choice.get_effects(state)
        apply_effects(state, effects)

        # Show skill check result
        if choice.skill_check > 0:
            roll = effects.get("_roll", 0)
            success = effects.get("_success", False)
            if success:
                print(f"\n  [技能檢查通過! 擲出 {roll}]")
            else:
                print(f"\n  [技能檢查失敗! 擲出 {roll}]")
            input("  按 Enter 繼續...")

        # Show item consumption
        if choice.consume_item:
            print(f"\n  [使用了: {choice.consume_item}]")
            input("  按 Enter 繼續...")

        state.turn += 1
        state.visit(scene_id)
        state.scene_history.append(scene_id)
        # Energy drain per turn
        state.modify_energy(-3)
        scene_id = choice.next_scene

        # Low energy warning
        if state.energy <= 20 and state.energy > 0:
            print(f"\n  [警告: 體力不足! {state.energy}/100]")
            input("  按 Enter 繼續...")
        elif state.energy <= 0:
            print(f"\n  [你精疲力竭了。]")
            state.alive = False

        if not state.alive:
            clear()
            print("\n" + "=" * 50)
            print("  你倒下了。")
            print(f"  走過的場景: {len(state.scene_history)}")
            print("=" * 50)
            break

    # Ending
    if state.ending:
        clear()
        print("\n" + "=" * 50)
        print(f"  結局: {state.ending}")
        print(f"  走過的場景: {len(state.scene_history)}")
        print(f"  知識: {state.knowledge}/100")
        print(f"  理智: {state.sanity}/100")
        if state.bonds:
            print(f"  關係: {state.bonds}")
        if state.inventory:
            print(f"  物品: {', '.join(state.inventory)}")
        print("=" * 50)
        print()
        input("  按 Enter 結束...")


if __name__ == "__main__":
    main()
