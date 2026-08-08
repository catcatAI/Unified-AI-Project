"""Game engine — integrates tokens, NPCs, quests, and all mechanics."""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Optional

from .i18n import I18n
from .models import Character, Scene, GameState, Message
from .npc import NPC, create_npc, create_npcs_for_scene
from .quests import QuestLog
from .token_effects import (
    apply_token_hp,
    apply_token_spirit,
    apply_token_skill_bonus,
    get_combat_dice_bonus,
    get_damage_resistance,
    get_token_descriptions,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent / "apps" / "game-rpg" / "data"
CARDS_PATH = DATA_DIR / "game_cards.json"

WORLDS = {
    "W01": {
        "name_key": "world_w01",
        "desc_key": "world_w01_desc",
        "scenes": ["S15", "S13", "S14", "S01", "S07", "S17", "SC-02"],
        "default_scene": "S15",
    },
    "W02": {
        "name_key": "world_w02",
        "desc_key": "world_w02_desc",
        "scenes": ["S01", "S02", "S03", "S04", "S08", "S09", "SC-01"],
        "default_scene": "S01",
    },
}

NPC_LINES = {
    "zh": [
        "「小心腳下，這裡的冰層不太穩定。」",
        "「你感覺到空氣中有微妙的震動嗎？那是靈子的流動。」",
        "「前方的路不太清楚，我們最好先觀察一下。」",
        "「别擔心，我會保護你的。」",
        "「你聽到了嗎？那個聲音……好像從很深的地方傳來。」",
        "「我們需要更多的情報。你有什麼發現嗎？」",
    ],
    "en": [
        '"Watch your step — the ice here is unstable."',
        '"Do you feel that vibration? That\'s the flow of spirit particles."',
        '"The path ahead is unclear. We should observe first."',
        '"Don\'t worry, I\'ll protect you."',
        '"Did you hear that? The sound... it comes from deep below."',
        '"We need more intelligence. Found anything?"',
    ],
    "ja": [
        "「足元に気をつけて、この辺りの氷は不安定だ。」",
        "「空気中に微かな振動を感じるか？あれは霊子の流れだ。」",
        "「先の道は不明確だ。様子を見た方がいい。」",
        "「心配しないで、守るから。」",
        "「聞こえたか？その音……ずっと深いところから来ているみたいだ。」",
        "「もっと情報が必要だ。何か見つけたか？」",
    ],
}


def load_cards(path: Path = CARDS_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_card(cards: list[dict], card_id: str) -> Optional[dict]:
    for c in cards:
        if c.get("card_id") == card_id:
            return c
    return None


def _extract_stat(card: dict, *keys: str, default="") -> str:
    stats = card.get("stats", {})
    for k in keys:
        if k in stats:
            return str(stats[k])
    return default


def get_playable_characters(cards: list[dict]) -> list[dict]:
    result = []
    for c in cards:
        if c.get("card_type") != "角色卡":
            continue
        name = c.get("name", "")
        if not name:
            continue
        tokens = c.get("tokens", [])
        cats = set(t.get("category", "") for t in tokens)
        if "vitality" in cats or "combat" in cats:
            result.append(c)
    return result


class GameEngine:
    """Core game loop — integrates all systems."""

    def __init__(self, cards_path: Path = CARDS_PATH):
        data = load_cards(cards_path)
        self.cards: list[dict] = data.get("cards", [])
        self.token_by_category: dict[str, int] = data.get("token_by_category", {})
        self._state: Optional[GameState] = None
        self.i18n = I18n("zh")
        self.selected_world: str = "W01"
        self.quest_log = QuestLog()
        self.npcs: list[NPC] = []
        self.hour: int = 12  # current game hour
        self._showing_interaction: bool = False
        self._pending_npc = None
        self._interaction_choices: list = []

    @property
    def state(self) -> GameState:
        if self._state is None:
            raise RuntimeError("Game not started.")
        return self._state

    def set_language(self, lang: str) -> None:
        self.i18n = I18n(lang)

    def get_worlds(self) -> list[dict]:
        result = []
        for wid, wdef in WORLDS.items():
            result.append({
                "id": wid,
                "name": self.i18n.t(wdef["name_key"]),
                "desc": self.i18n.t(wdef["desc_key"]),
            })
        return result

    def get_characters(self) -> list[dict]:
        chars = get_playable_characters(self.cards)
        return [
            {
                "card_id": c["card_id"],
                "name": c.get("name", c["card_id"]),
                "description": _extract_stat(c, "role定位", "定位", "身份", "core矛盾"),
                "tokens": c.get("tokens", []),
            }
            for c in chars
        ]

    def new_game(self, pc_card_id: str = "CC-01", scene_card_id: str = "S15") -> GameState:
        if not self.cards:
            raise RuntimeError("No character cards loaded.")
        pc_card = _find_card(self.cards, pc_card_id) or self.cards[0]
        scene_card = _find_card(self.cards, scene_card_id)
        pc_tokens = pc_card.get("tokens", [])

        # Apply token effects to stats
        max_hp, hp = apply_token_hp(pc_tokens)
        max_spirit, spirit = apply_token_spirit(pc_tokens)
        skill_bonus = apply_token_skill_bonus(pc_tokens)

        pc = Character(
            card_id=pc_card["card_id"],
            name=pc_card.get("name", pc_card["card_id"]),
            description=_extract_stat(pc_card, "role定位", "定位", "身份", "core矛盾"),
            tokens=pc_tokens,
            hp=hp,
            max_hp=max_hp,
            spirit=spirit,
            max_spirit=max_spirit,
            skill=min(50 + skill_bonus, 100),
            max_skill=100,
            inventory=[
                self.i18n.t("item_flashlight"),
                self.i18n.t("item_map"),
            ],
        )

        scene_name = ""
        if scene_card:
            scene_name = scene_card.get("name", "") or _extract_stat(
                scene_card, "location", "場景", "name", default=""
            )
        scene = Scene(
            card_id=scene_card["card_id"] if scene_card else scene_card_id,
            name=scene_name or "鏡湖周邊",
            description=_extract_stat(scene_card, "location", "場景", "nature", default="鏡湖周邊區域") if scene_card else "鏡湖周邊區域",
            spirit_density=float(
                _extract_stat(scene_card, "spirit_density", default="2.0")
                .replace("ppm", "").split("-")[0]
            ) if scene_card else 2.0,
            temperature=_extract_stat(scene_card, "temperature", default="常溫") if scene_card else "常溫",
            characters=_extract_stat(scene_card, "involved_characters", default="").split("、")
            if scene_card else [],
            tokens=scene_card.get("tokens", []) if scene_card else [],
        )

        self._state = GameState(pc=pc, scene=scene)
        self.npcs = create_npcs_for_scene(scene_card_id, lang=self.i18n.lang)
        self.hour = 12

        self._state.messages.append(Message(
            speaker="system",
            text=self.i18n.t("narration_scene_intro", name=scene.name, desc=scene.description),
            kind="narration",
        ))
        self._state.messages.append(Message(
            speaker="system",
            text=self.i18n.t("narration_enter_world", name=pc.name),
            kind="narration",
        ))
        if self.npcs:
            names = ", ".join(n.name for n in self.npcs)
            self._state.messages.append(Message(
                speaker="system",
                text=self.i18n.t("narration_present", names=names),
                kind="narration",
            ))
        else:
            self._state.messages.append(Message(
                speaker="system",
                text=self.i18n.t("narration_no_npcs"),
                kind="narration",
            ))

        self.quest_log.activate_quest("MQ-01")
        self._state.messages.append(Message(
            speaker="system",
            text=self.i18n.t("quest_started", title=self.quest_log.get_main_quests()[0].title),
            kind="system",
        ))

        self._refresh_choices()
        return self._state

    def is_game_over(self) -> bool:
        if self._state is None:
            return False
        return self._state.pc.hp <= 0 or self._state.turn >= 50

    def process_input(self, text: str) -> GameState:
        s = self._state
        text = text.strip()
        if not text:
            return s

        s.turn += 1
        self.hour = (self.hour + 1) % 24

        # Update NPC locations based on time
        for npc in self.npcs:
            npc.current_location = npc.get_current_activity(self.hour)

        if text.isdigit():
            idx = int(text) - 1
            if 0 <= idx < len(s.choices):
                self._handle_choice(idx)
            else:
                s.messages.append(Message(speaker="system", text=self.i18n.t("invalid_choice"), kind="system"))
        else:
            s.messages.append(Message(speaker="你", text=text, kind="action"))
            self._handle_free_input(text)

        self._refresh_choices()
        return s

    def _handle_choice(self, idx: int) -> None:
        s = self._state

        # Interaction mode: different choices when talking to NPC
        if self._showing_interaction:
            self._handle_interaction_choice(idx)
            self._refresh_choices()
            return

        choice = s.choices[idx]
        s.messages.append(Message(speaker="你", text=choice, kind="action"))

        if idx == 0:
            self._observe()
            self._check_quest_progress("observe")
        elif idx == 1:
            npc = self._npc_respond("dialogue")
            self._check_quest_progress("talk", npc_name=npc.name if npc else "")
        elif idx == 2:
            self._advance_scene()
            self._check_quest_progress("advance")
        elif idx == 3:
            self._rest()
            self._check_quest_progress("rest")
        elif idx == 4:
            self._show_inventory()
        elif idx == 5:
            self._show_status()
        elif idx == 6:
            self._show_quests()
        elif idx == 7:
            self._show_npc_info()

    def _handle_free_input(self, text: str) -> None:
        lower = text.lower()
        if any(k in lower for k in ["attack", "攻擊", "打", "戰鬥", "fight"]):
            self._combat(text)
            self._check_quest_progress("combat")
        elif any(k in lower for k in ["talk", "對話", "問", "說", "speak"]):
            self._npc_respond("dialogue")
        elif any(k in lower for k in ["go", "去", "走", "前進", "移動", "move"]):
            self._advance_scene()
        elif any(k in lower for k in ["rest", "休息", "睡"]):
            self._rest()
        elif any(k in lower for k in ["look", "看", "觀察", "檢查", "observe"]):
            self._observe()
        elif any(k in lower for k in ["quest", "任務"]):
            self._show_quests()
        elif any(k in lower for k in ["npc", "人物"]):
            self._show_npc_info()
        else:
            self._npc_respond("action")

    def _npc_respond(self, mode: str):
        s = self._state
        if not self.npcs:
            lines = self.i18n.t("no_one_nearby", default="這裡沒有人。")
            s.messages.append(Message(speaker="system", text=lines, kind="system"))
            return None

        # Pick NPC based on disposition (friendlier NPCs talk more)
        weights = [npc.disposition for npc in self.npcs]
        npc = random.choices(self.npcs, weights=weights, k=1)[0]

        # Greeting varies by time of day and disposition
        greeting = npc.get_greeting()
        s.messages.append(Message(speaker=npc.name, text=greeting, kind="dialogue"))

        # Give player real choices based on who NPC is
        self._show_interaction_choices(npc)
        return npc

    def _show_interaction_choices(self, npc: NPC) -> None:
        s = self._state
        choices = [
            ("ask_info", self.i18n.t("choice_ask_info", name=npc.name)),
            ("ask_help", self.i18n.t("choice_ask_help", name=npc.name)),
            ("give_item", self.i18n.t("choice_give_item", name=npc.name)),
            ("leave", self.i18n.t("choice_leave")),
        ]
        # NPC offers quest if available
        npc_quest_map = {
            "晞咕萊雅": "SQ-01",
            "紅": "SQ-02",
            "小狐丸": "MQ-02",
            "晴空": "SQ-03",
            "深痕·裂脊": "SQ-04",
            "翎翾": "SQ-05",
            "煦掠": "SQ-06",
        }
        quest_id = npc_quest_map.get(npc.name)
        if quest_id and not any(q.quest_id == quest_id for q in self.quest_log.quests if q.status != "available"):
            choices.insert(0, ("accept_quest", self.i18n.t("choice_accept_quest", name=npc.name)))

        self._pending_npc = npc
        self._interaction_choices = choices
        self._showing_interaction = True

    def _handle_interaction_choice(self, idx: int) -> None:
        s = self._state
        action_key, label = self._interaction_choices[idx]
        npc = self._pending_npc
        s.messages.append(Message(speaker="你", text=label, kind="action"))

        if action_key == "accept_quest":
            npc_quest_map = {
                "晞咕萊雅": "SQ-01", "紅": "SQ-02", "小狐丸": "MQ-02",
                "晴空": "SQ-03", "深痕·裂脊": "SQ-04", "翎翾": "SQ-05", "煦掠": "SQ-06",
            }
            quest_id = npc_quest_map.get(npc.name)
            if quest_id and self.quest_log.activate_quest(quest_id):
                quest = next(q for q in self.quest_log.quests if q.quest_id == quest_id)
                s.messages.append(Message(
                    speaker="system",
                    text=self.i18n.t("quest_started", title=quest.title),
                    kind="system",
                ))
            else:
                s.messages.append(Message(speaker=npc.name, text=self.i18n.t("npc_no_quest"), kind="dialogue"))

        elif action_key == "ask_info":
            info_lines = npc.get_dialogue()
            s.messages.append(Message(speaker=npc.name, text=info_lines, kind="dialogue"))
            # NPC gives a hint about current quest
            active_quests = self.quest_log.get_active()
            if active_quests:
                q = random.choice(active_quests)
                hint = self.i18n.t("npc_quest_hint", quest=q.title)
                s.messages.append(Message(speaker=npc.name, text=hint, kind="dialogue"))
            self._check_quest_progress("ask_info", npc_name=npc.name)

        elif action_key == "ask_help":
            if npc.disposition > 0.6:
                heal = random.randint(10, 25)
                s.pc.hp = min(s.pc.max_hp, s.pc.hp + heal)
                spirit = random.randint(5, 15)
                s.pc.spirit = min(s.pc.max_spirit, s.pc.spirit + spirit)
                s.messages.append(Message(
                    speaker=npc.name,
                    text=self.i18n.t("npc_help_yes", name=npc.name, heal=heal, spirit=spirit),
                    kind="dialogue",
                ))
            else:
                s.messages.append(Message(
                    speaker=npc.name,
                    text=self.i18n.t("npc_help_no", name=npc.name),
                    kind="dialogue",
                ))
            self._check_quest_progress("ask_help", npc_name=npc.name)

        elif action_key == "give_item":
            if s.pc.inventory:
                item = s.pc.inventory[0]
                s.pc.inventory.pop(0)
                npc.disposition = min(1.0, npc.disposition + 0.1)
                s.messages.append(Message(
                    speaker=npc.name,
                    text=self.i18n.t("npc_item_received", name=npc.name, item=item),
                    kind="dialogue",
                ))
                self._check_quest_progress("give_item", npc_name=npc.name)
            else:
                s.messages.append(Message(
                    speaker=npc.name,
                    text=self.i18n.t("npc_no_item"),
                    kind="dialogue",
                ))

        elif action_key == "leave":
            s.messages.append(Message(
                speaker="system",
                text=self.i18n.t("you_leave", name=npc.name),
                kind="narration",
            ))

        self._showing_interaction = False
        self._pending_npc = None
        self._interaction_choices = []

    def _advance_scene(self) -> None:
        s = self._state
        world = WORLDS.get(self.selected_world, WORLDS["W01"])
        scene_ids = world["scenes"]
        current_idx = scene_ids.index(s.scene.card_id) if s.scene.card_id in scene_ids else 0
        next_idx = (current_idx + 1) % len(scene_ids)
        next_id = scene_ids[next_idx]

        # Travel event: random encounter on the way
        travel_events = [
            ("danger", 0.25),
            ("discovery", 0.25),
            ("nothing", 0.50),
        ]
        roll = random.random()
        cumulative = 0
        event_type = "nothing"
        for etype, prob in travel_events:
            cumulative += prob
            if roll < cumulative:
                event_type = etype
                break

        if event_type == "danger":
            enemy = random.choice(["失控的靈子體", " Concept野兽", "流浪的自動人偶", "概念碎片結晶體"])
            enemy_en = random.choice(["Rogue spirit", "Concept beast", "Wandering automaton", "Concept crystal"])
            enemy_ja = random.choice(["暴走霊子体", "概念獣", "流浪オートマトン", "概念結晶体"])
            enemy_name = {"zh": enemy, "en": enemy_en, "ja": enemy_ja}[self.i18n.lang]
            dmg = random.randint(5, 15)
            s.pc.hp -= dmg
            s.messages.append(Message(
                speaker="system",
                text=self.i18n.t("travel_danger", enemy=enemy_name, dmg=dmg),
                kind="narration",
            ))
        elif event_type == "discovery":
            loot_options = [
                self.i18n.t("loot_spirit_crystal"),
                self.i18n.t("item_flashlight"),
                self.i18n.t("item_map"),
                "復原藥水" if self.i18n.lang == "zh" else "Healing Potion" if self.i18n.lang == "en" else "回復薬",
            ]
            loot = random.choice(loot_options)
            s.pc.inventory.append(loot)
            heal = random.randint(5, 15)
            s.pc.hp = min(s.pc.max_hp, s.pc.hp + heal)
            s.messages.append(Message(
                speaker="system",
                text=self.i18n.t("travel_discovery", item=loot, heal=heal),
                kind="narration",
            ))

        card = _find_card(self.cards, next_id)
        if card:
            name = card.get("name", "") or _extract_stat(card, "location", "場景", "name", default="")
            s.scene = Scene(
                card_id=card["card_id"],
                name=name or card["card_id"],
                description=_extract_stat(card, "location", "場景", "nature", default=""),
                spirit_density=float(
                    _extract_stat(card, "spirit_density", default="2.0")
                    .replace("ppm", "").split("-")[0]
                ),
                temperature=_extract_stat(card, "temperature", default="常溫"),
                characters=_extract_stat(card, "involved_characters", default="").split("、"),
                tokens=card.get("tokens", []),
            )
            self.npcs = create_npcs_for_scene(next_id, lang=self.i18n.lang)
            s.messages.append(Message(
                speaker="system",
                text=self.i18n.t("narration_scene_intro", name=s.scene.name, desc=s.scene.description),
                kind="narration",
            ))
            if self.npcs:
                names = ", ".join(n.name for n in self.npcs)
                s.messages.append(Message(speaker="system", text=self.i18n.t("narration_present", names=names), kind="narration"))
                # NPC reacts to player arrival
                npc = random.choice(self.npcs)
                greeting = npc.get_greeting()
                s.messages.append(Message(speaker=npc.name, text=greeting, kind="dialogue"))
            else:
                s.messages.append(Message(speaker="system", text=self.i18n.t("narration_no_npcs"), kind="narration"))

    def _rest(self) -> None:
        s = self._state
        heal = min(20, s.pc.max_hp - s.pc.hp)
        spirit_restore = min(15, s.pc.max_spirit - s.pc.spirit)
        s.pc.hp += heal
        s.pc.spirit += spirit_restore
        self.hour = (self.hour + 2) % 24
        msg = self.i18n.t("rest_msg", heal=heal, spirit=spirit_restore)
        s.messages.append(Message(speaker="system", text=msg, kind="system"))

        # Rest event: something happens while you rest
        roll = random.random()
        if roll < 0.25 and self.npcs:
            # NPC visits while resting
            npc = random.choice(self.npcs)
            visit_line = npc.get_dialogue()
            s.messages.append(Message(
                speaker=npc.name,
                text=self.i18n.t("rest_npc_visit", name=npc.name, line=visit_line),
                kind="dialogue",
            ))
        elif roll < 0.45:
            # Dream / vision
            dreams = [
                self.i18n.t("rest_dream_corridor"),
                self.i18n.t("rest_dream_voice"),
                self.i18n.t("rest_dream_memory"),
            ]
            s.messages.append(Message(
                speaker="system",
                text=random.choice(dreams),
                kind="narration",
            ))
        elif roll < 0.55:
            # Danger while resting
            dmg = random.randint(3, 10)
            s.pc.hp -= dmg
            s.messages.append(Message(
                speaker="system",
                text=self.i18n.t("rest_danger", dmg=dmg),
                kind="narration",
            ))

    def _combat(self, text: str) -> None:
        s = self._state
        # Generate a real enemy
        enemies = {
            "zh": [
                ("失控的靈子體", 15, 30),
                ("Concept野兽", 20, 40),
                ("流浪的自動人偶", 10, 25),
                ("概念碎片結晶體", 25, 35),
                ("腐蝕的記憶體", 12, 20),
                ("扭曲的空間裂隙", 30, 50),
            ],
            "en": [
                ("Rogue spirit", 15, 30),
                ("Concept beast", 20, 40),
                ("Wandering automaton", 10, 25),
                ("Concept crystal", 25, 35),
                ("Corrupted memory", 12, 20),
                ("Spatial rift", 30, 50),
            ],
            "ja": [
                ("暴走霊子体", 15, 30),
                ("概念獣", 20, 40),
                ("流浪オートマトン", 10, 25),
                ("概念結晶体", 25, 35),
                ("腐蝕記憶体", 12, 20),
                ("空間裂け目", 30, 50),
            ],
        }
        enemy_name, enemy_hp, enemy_dmg = random.choice(enemies[self.i18n.lang])
        s.messages.append(Message(
            speaker="system",
            text=self.i18n.t("combat_encounter", enemy=enemy_name),
            kind="narration",
        ))

        # Player attacks
        roll = random.randint(1, 12)
        combat_bonus = get_combat_dice_bonus(s.pc.tokens)
        skill_mod = s.pc.skill // 10
        total = roll + combat_bonus + skill_mod

        resistance = get_damage_resistance(s.pc.tokens)

        if total >= 10:
            dmg = random.randint(15, 35)
            enemy_hp -= dmg
            loot = random.choice([
                self.i18n.t("loot_spirit_crystal"),
                "記憶碎片" if self.i18n.lang == "zh" else "Memory shard" if self.i18n.lang == "en" else "記憶欠片",
                "概念殘片" if self.i18n.lang == "zh" else "Concept fragment" if self.i18n.lang == "en" else "概念断片",
            ])
            s.pc.inventory.append(loot)
            heal = random.randint(5, 15)
            s.pc.hp = min(s.pc.max_hp, s.pc.hp + heal)
            s.messages.append(Message(
                speaker="system",
                text=self.i18n.t("combat_win", enemy=enemy_name, dmg=dmg, item=loot, heal=heal),
                kind="system",
            ))
            self._check_quest_progress("combat")
        elif total >= 6:
            # Draw: both take damage
            player_dmg = random.randint(5, 15)
            enemy_dmg_actual = random.randint(3, 10)
            s.pc.hp -= int(player_dmg * (1 - resistance))
            s.messages.append(Message(
                speaker="system",
                text=self.i18n.t("combat_draw", enemy=enemy_name, player_dmg=player_dmg, enemy_dmg=enemy_dmg_actual),
                kind="system",
            ))
        else:
            # Player takes damage
            counter = random.randint(enemy_dmg // 2, enemy_dmg)
            reduced = int(counter * (1 - resistance))
            s.pc.hp -= reduced
            s.messages.append(Message(
                speaker="system",
                text=self.i18n.t("combat_lose", enemy=enemy_name, dmg=reduced, resist=int(resistance * 100)),
                kind="system",
            ))

    def _observe(self) -> None:
        s = self._state
        # Find something specific in the scene
        discoveries = [
            self.i18n.t("observe_footprints"),
            self.i18n.t("observe_crack"),
            self.i18n.t("observe_light"),
            self.i18n.t("observe_sound"),
            self.i18n.t("observe_mark"),
            self.i18n.t("observe_wind"),
            self.i18n.t("observe_temperature_change"),
        ]
        discovery = random.choice(discoveries)

        # Maybe find something useful
        find_roll = random.random()
        if find_roll < 0.3:
            # Find an item
            loot = random.choice([
                self.i18n.t("loot_spirit_crystal"),
                "補給物資" if self.i18n.lang == "zh" else "Supplies" if self.i18n.lang == "en" else "補給物資",
                "舊地圖" if self.i18n.lang == "zh" else "Old map" if self.i18n.lang == "en" else "古い地図",
            ])
            s.pc.inventory.append(loot)
            s.messages.append(Message(
                speaker="system",
                text=self.i18n.t("observe_find", discovery=discovery, item=loot),
                kind="narration",
            ))
        elif find_roll < 0.5:
            # Find a clue about the quest
            active = self.quest_log.get_active()
            if active:
                q = random.choice(active)
                s.messages.append(Message(
                    speaker="system",
                    text=self.i18n.t("observe_quest_clue", discovery=discovery, quest=q.title),
                    kind="narration",
                ))
            else:
                s.messages.append(Message(
                    speaker="system",
                    text=self.i18n.t("observe_generic", discovery=discovery),
                    kind="narration",
                ))
        else:
            # Just describe what you see
            s.messages.append(Message(
                speaker="system",
                text=self.i18n.t("observe_generic", discovery=discovery),
                kind="narration",
            ))

        # Maybe NPC approaches
        if self.npcs and random.random() < 0.4:
            npc = random.choice(self.npcs)
            approach_line = npc.get_dialogue()
            s.messages.append(Message(
                speaker=npc.name,
                text=approach_line,
                kind="dialogue",
            ))

    def _show_inventory(self) -> None:
        s = self._state
        items = ", ".join(s.pc.inventory) if s.pc.inventory else self.i18n.t("empty")
        msg = self.i18n.t("inventory_msg", items=items)
        s.messages.append(Message(speaker="system", text=msg, kind="system"))

    def _show_status(self) -> None:
        s = self._state
        lines = [
            s.pc.name,
            f"HP:  {s.pc.hp_bar} {s.pc.hp}/{s.pc.max_hp}",
            f"SP:  {s.pc.spirit_bar} {s.pc.spirit}/{s.pc.max_spirit}",
            f"SK:  {s.pc.skill_bar} {s.pc.skill}/{s.pc.max_skill}",
            self.i18n.t("status_turn_hour", turn=s.turn, hour=self.hour),
        ]
        token_descs = get_token_descriptions(s.pc.tokens, 3)
        if token_descs:
            lines.append(self.i18n.t("status_tokens"))
            lines.extend(token_descs)
        s.messages.append(Message(speaker="system", text="\n".join(lines), kind="system"))

    def _show_quests(self) -> None:
        s = self._state
        active = self.quest_log.get_active()
        completed = self.quest_log.get_completed()
        if not active and not completed:
            s.messages.append(Message(speaker="system", text=self.i18n.t("no_quests"), kind="system"))
            return
        lines = []
        for q in active:
            pct = int(q.progress * 100)
            obj_done = sum(1 for o in q.objectives if o.completed)
            obj_total = len(q.objectives)
            lines.append(self.i18n.t("quest_progress", id=q.quest_id, title=q.title, pct=pct, done=obj_done, total=obj_total))
        for q in completed:
            lines.append(self.i18n.t("quest_done", id=q.quest_id, title=q.title))
        s.messages.append(Message(speaker="system", text="\n".join(lines), kind="system"))

    def _show_npc_info(self) -> None:
        s = self._state
        if not self.npcs:
            s.messages.append(Message(speaker="system", text=self.i18n.t("no_npcs_here"), kind="system"))
            return
        lines = []
        for npc in self.npcs:
            activity = npc.get_current_activity(self.hour)
            lines.append(f"{npc.name} ({npc.card_id}) - {activity}")
            lines.append(self.i18n.t("npc_mood", mood=npc.mood, disp=npc.disposition))
        s.messages.append(Message(speaker="system", text="\n".join(lines), kind="system"))

    def _refresh_choices(self) -> None:
        s = self._state
        if self._showing_interaction:
            s.choices = [label for _, label in self._interaction_choices]
        else:
            s.choices = [
                self.i18n.t("choice_observe"),
                self.i18n.t("choice_talk"),
                self.i18n.t("choice_advance"),
                self.i18n.t("choice_rest"),
                self.i18n.t("choice_inventory"),
                self.i18n.t("choice_status"),
                self.i18n.t("choice_quests_short"),
                self.i18n.t("choice_npc_info_short"),
            ]

    def _check_quest_progress(self, action: str, npc_name: str = "") -> None:
        """Check if any quest objectives should be completed by the given action."""
        s = self._state
        scene_id = s.scene.card_id

        # Map interaction actions to base actions for quest matching
        base_action = action
        if action in ("ask_info", "ask_help", "give_item"):
            base_action = "talk"

        # Auto-activate quests when entering certain scenes
        if action == "advance":
            for q in self.quest_log.get_available():
                if q.source_card_id == scene_id:
                    self.quest_log.activate_quest(q.quest_id)
                    s.messages.append(Message(
                        speaker="system",
                        text=self.i18n.t("quest_started", title=q.title),
                        kind="system",
                    ))

        for quest in self.quest_log.get_active():
            for obj in quest.objectives:
                if obj.completed:
                    continue
                if obj.check(base_action, scene_id, npc_name, s.pc.inventory):
                    s.messages.append(Message(
                        speaker="system",
                        text=self.i18n.t("quest_obj_complete", desc=obj.description),
                        kind="system",
                    ))
            if quest.status != "completed" and all(o.completed for o in quest.objectives):
                quest.status = "completed"
                s.messages.append(Message(
                    speaker="system",
                    text=self.i18n.t("quest_complete", title=quest.title),
                    kind="system",
                ))
