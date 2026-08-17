"""Quest system — state-based objective completion from card data."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QuestObjective:
    description: str
    completed: bool = False
    # State-based completion conditions
    require_action: str = ""       # "observe", "talk", "advance", "combat", "rest", "give_item", "ask_help"
    require_scene: str = ""        # card_id of required scene
    require_npc: str = ""          # NPC name required
    require_item: str = ""         # item name required
    require_times: int = 1         # how many times action must be done
    _count: int = 0                # current count

    def check(self, action: str, scene_id: str, npc_name: str, inventory: list[str]) -> bool:
        """Check if this objective completes given current game state."""
        if self.completed:
            return False

        # Check scene requirement
        if self.require_scene and scene_id != self.require_scene:
            return False

        # Check NPC requirement
        if self.require_npc and npc_name != self.require_npc:
            return False

        # Check item requirement (give_item)
        if self.require_item and action == "give_item":
            if self.require_item in inventory:
                self._count += 1
                if self._count >= self.require_times:
                    self.completed = True
                    return True
            return False

        # Check action match
        if self.require_action and action == self.require_action:
            self._count += 1
            if self.require_times <= 1:
                self.completed = True
                return True
            elif self._count >= self.require_times:
                self.completed = True
                return True
            return False

        return False


@dataclass
class Quest:
    quest_id: str
    title: str
    description: str
    quest_type: str = "side"  # main / side
    objectives: list[QuestObjective] = field(default_factory=list)
    rewards: list[str] = field(default_factory=list)
    status: str = "available"  # available / active / completed / failed
    source_card_id: str = ""

    @property
    def progress(self) -> float:
        if not self.objectives:
            return 0.0
        done = sum(1 for o in self.objectives if o.completed)
        return done / len(self.objectives)

    def activate(self) -> None:
        if self.status == "available":
            self.status = "active"

    def fail(self) -> None:
        self.status = "failed"


# ─── Quest definitions with state-based conditions ───

QUESTS: list[dict] = [
    {
        "quest_id": "MQ-01",
        "title": "鏡湖的秘密",
        "title_en": "Secrets of Mirror Lake",
        "title_ja": "鏡湖の秘密",
        "description": "調查鏡湖火山口下方的異常靈子流動",
        "quest_type": "main",
        "objectives": [
            {"description": "在鏡湖周邊探索", "require_action": "observe"},
            {"description": "調查冰層下的水流", "require_action": "observe"},
            {"description": "找到靈子流動的源頭", "require_action": "observe"},
        ],
        "rewards": ["解鎖新場景：鏡湖深層"],
        "source_card_id": "S15",
    },
    {
        "quest_id": "MQ-02",
        "title": "大正浪漫的迴響",
        "title_en": "Echo of Taisho Romance",
        "title_ja": "大正浪漫の響き",
        "description": "追隨小狐丸和左間小蒼蘭的記憶碎片",
        "quest_type": "main",
        "objectives": [
            {"description": "與小狐丸交談", "require_action": "talk", "require_npc": "小狐丸"},
            {"description": "參觀秘密鐵工廠", "require_action": "advance"},
            {"description": "了解大正年間的歷史", "require_action": "ask_info"},
        ],
        "rewards": ["解鎖小狐丸的過去"],
        "source_card_id": "CC-18",
    },
    {
        "quest_id": "SQ-01",
        "title": "圖書館的修補",
        "title_en": "Library Repairs",
        "title_ja": "図書館の修繕",
        "description": "幫助晞咕萊雅修補受損的書籍",
        "quest_type": "side",
        "objectives": [
            {"description": "找到受損的書籍", "require_action": "observe"},
            {"description": "收集修補材料", "require_action": "observe"},
            {"description": "完成修補", "require_action": "talk", "require_npc": "晞咕萊雅"},
        ],
        "rewards": ["晞咕萊雅好感度+20"],
        "source_card_id": "CC-38",
    },
    {
        "quest_id": "SQ-02",
        "title": "便利店的常客",
        "title_en": "Convenience Store Regular",
        "title_ja": "コンビニの常連",
        "description": "成為紅的便利店的常客",
        "quest_type": "side",
        "objectives": [
            {"description": "拜訪便利店3次", "require_action": "advance", "require_times": 3},
            {"description": "購買物品", "require_action": "give_item"},
            {"description": "與紅建立友誼", "require_action": "talk", "require_npc": "紅"},
        ],
        "rewards": ["紅好感度+15", "解鎖特殊商品"],
        "source_card_id": "CC-21",
    },
    {
        "quest_id": "SQ-03",
        "title": "翼膜的秘密",
        "title_en": "Secrets of the Wings",
        "title_ja": "翼の秘密",
        "description": "幫助晴空了解她的翼膜能力",
        "quest_type": "side",
        "objectives": [
            {"description": "觀察周圍的生物痕跡", "require_action": "observe"},
            {"description": "查找相關的書籍", "require_action": "observe"},
            {"description": "與同伴討論翼膜", "require_action": "ask_info"},
        ],
        "rewards": ["晴空好感度+25"],
        "source_card_id": "CC-19",
    },
    {
        "quest_id": "SQ-04",
        "title": "黑淵台的維護",
        "title_en": "Abyssal Podium Maintenance",
        "title_ja": "アビサルポディウムの維持",
        "description": "協助深痕·裂脊修補地熱管道",
        "quest_type": "side",
        "objectives": [
            {"description": "抵達黑淵台", "require_action": "advance", "require_scene": "SC-02"},
            {"description": "找到損壞的管道", "require_action": "observe"},
            {"description": "協助修補", "require_action": "talk", "require_npc": "深痕·裂脊"},
        ],
        "rewards": ["深痕·裂脊好感度+20"],
        "source_card_id": "CC-65",
    },
    {
        "quest_id": "SQ-05",
        "title": "競速之約",
        "title_en": "Racing Wager",
        "title_ja": "レースの賭け",
        "description": "翎翾與改裝滑翔翼人類的競速賭注",
        "quest_type": "side",
        "objectives": [
            {"description": "找到翎翾", "require_action": "talk", "require_npc": "翎翾"},
            {"description": "了解競速規則", "require_action": "ask_info", "require_npc": "翎翾"},
            {"description": "完成比賽", "require_action": "combat"},
        ],
        "rewards": ["翎翾好感度+15"],
        "source_card_id": "CC-50",
    },
    {
        "quest_id": "SQ-06",
        "title": "襲掠儀式",
        "title_en": "The Attack Ritual",
        "title_ja": "襲掠の儀式",
        "description": "煦掠的族群伴侶挑選儀式",
        "quest_type": "side",
        "objectives": [
            {"description": "被煦掠襲掠", "require_action": "combat"},
            {"description": "做出正確反應", "require_action": "talk", "require_npc": "煦掠"},
            {"description": "完成三階段", "require_action": "rest"},
        ],
        "rewards": ["煦掠好感度+30"],
        "source_card_id": "CC-52",
    },
    {
        "quest_id": "SQ-07",
        "title": "作物娘的煩惱",
        "title_en": "Crop Girl's Troubles",
        "title_ja": "作物娘の悩み",
        "description": "幫助SL-11的作物娘們解決生長問題",
        "quest_type": "side",
        "objectives": [
            {"description": "了解作物娘的問題", "require_action": "ask_info"},
            {"description": "調整好感度系統", "require_action": "give_item"},
            {"description": "讓作物恢復生長", "require_action": "rest"},
        ],
        "rewards": ["作物娘好感度+25"],
        "source_card_id": "SL-11",
    },
    {
        "quest_id": "SQ-08",
        "title": "認知共振的秘密",
        "title_en": "Secret of Cognitive Resonance",
        "title_ja": "認知共鳴の秘密",
        "description": "調查克洛諾斯的認知共振能力真相",
        "quest_type": "side",
        "objectives": [
            {"description": "找到認知共振的文獻", "require_action": "observe"},
            {"description": "分析共振機制", "require_action": "observe"},
            {"description": "揭露真相", "require_action": "ask_info"},
        ],
        "rewards": ["解鎖認知共振知識"],
        "source_card_id": "CCK-01",
    },
    {
        "quest_id": "MQ-03",
        "title": "迴廊的呼喚",
        "title_en": "Call of the Corridor",
        "title_ja": "回廊の呼び声",
        "description": "迴廊深處傳來的神秘訊號",
        "quest_type": "main",
        "objectives": [
            {"description": "抵達迴廊深層", "require_action": "advance", "require_scene": "S14"},
            {"description": "解讀訊號含義", "require_action": "observe"},
            {"description": "找到訊號源頭", "require_action": "advance"},
        ],
        "rewards": ["解鎖迴廊深層場景"],
        "source_card_id": "RC-01",
    },
    {
        "quest_id": "MQ-04",
        "title": "月面碎碎念",
        "title_en": "Moon Whisper",
        "title_ja": "月面囁き",
        "description": "月面基地持續傳來的低語",
        "quest_type": "main",
        "objectives": [
            {"description": "接收月面訊號", "require_action": "observe"},
            {"description": "分析低語內容", "require_action": "ask_info"},
            {"description": "回應或忽略", "require_action": "rest"},
        ],
        "rewards": ["解鎖月面場景"],
        "source_card_id": "EP-35D",
    },
]


class QuestLog:
    """Manages all quests for the current game."""

    def __init__(self):
        self.quests: list[Quest] = []
        self._init_quests()

    def _init_quests(self) -> None:
        for qd in QUESTS:
            objectives = []
            for od in qd["objectives"]:
                obj = QuestObjective(
                    description=od["description"],
                    require_action=od.get("require_action", ""),
                    require_scene=od.get("require_scene", ""),
                    require_npc=od.get("require_npc", ""),
                    require_item=od.get("require_item", ""),
                    require_times=od.get("require_times", 1),
                )
                objectives.append(obj)
            quest = Quest(
                quest_id=qd["quest_id"],
                title=qd["title"],
                description=qd["description"],
                quest_type=qd["quest_type"],
                objectives=objectives,
                rewards=qd["rewards"],
                source_card_id=qd.get("source_card_id", ""),
            )
            self.quests.append(quest)

    def get_available(self) -> list[Quest]:
        return [q for q in self.quests if q.status == "available"]

    def get_active(self) -> list[Quest]:
        return [q for q in self.quests if q.status == "active"]

    def get_completed(self) -> list[Quest]:
        return [q for q in self.quests if q.status == "completed"]

    def activate_quest(self, quest_id: str) -> bool:
        for q in self.quests:
            if q.quest_id == quest_id and q.status == "available":
                q.activate()
                return True
        return False

    def get_main_quests(self) -> list[Quest]:
        return [q for q in self.quests if q.quest_type == "main"]

    def get_side_quests(self) -> list[Quest]:
        return [q for q in self.quests if q.quest_type == "side"]
