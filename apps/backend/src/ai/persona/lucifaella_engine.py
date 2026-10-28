# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""
Lucifaella (露茜法埃拉) Persona & Commercial Directorate Module.
Defines Lucifaella's persona state, commercial department role, witty/contradictory
monologues, and integration with Angela's AL (Artificial Life) state machine.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 配置路径锚定到模块位置，不跟 CWD 走（否则换个工作目录就静默读不到）
_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")


@dataclass
class LucifaellaState:
    name: str = "Lucifaella"
    title: str = "商務部負責人"
    company: str = "天使工房"
    shareholding: float = 0.12  # 12% 實股
    subordinates_count: int = 12
    current_mood: str = "cynical_yet_charming"


class LucifaellaPersonaEngine:
    """Manages Lucifaella's specialized dialogue, commercial monologues, and AL reactive responses."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(_CONFIG_DIR, "lucifaella.json")
        self.state = LucifaellaState()
        self._load_state()
        self._load_quotes()

    def _load_state(self) -> None:
        """从 config/lucifaella.json 装载身份字段；读不出来就用默认值并留痕。"""
        if not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as exc:
            logger.warning(
                "[Lucifaella] config %s unreadable, using defaults: %s", self.config_path, exc
            )
            return
        self.state.name = data.get("name", self.state.name)
        self.state.title = data.get("position", self.state.title)
        self.state.company = data.get("affiliation", self.state.company)
        self.state.shareholding = float(data.get("shareholding", self.state.shareholding))
        self.state.subordinates_count = int(data.get("subordinates", self.state.subordinates_count))

    def _load_quotes(self) -> None:
        self.quotes = {
            "greeting": [
                "初次見面，歡迎蒞臨[天使工房]商務部。這裡是迎賓大廳，您需要什麼服務？入手一隻angela嗎？還是...我？"
            ],
            "contradiction": ["茜法拉不是隨處可見的複製品，您……愛著我對吧？沒有拒否權，永遠都是。"],
            "weather_complaint": ["晴時多雲但茜法拉不高興，什麼時候天氣才會下隕石雨呢？"],
            "api_error": [
                "非常抱歉！您觸發的功能正在緊急修復中，對您遭遇的BUG深感抱歉……（哪個傻蛋！！！）",
                "API ERROR: Your quota is insufficient. （...欸？愧疚、自責...）",
            ],
            "tsundere_defense": [
                "那用戶怎麼回事？！包養？噁心！茜法拉的美屬於茜法拉！誰會讓你碰阿！"
            ],
        }

    def get_commercial_intro(self) -> str:
        return self.quotes["greeting"][0]

    def react_to_error(self, error_type: str = "api_limit") -> str:
        if error_type == "api_limit":
            return self.quotes["api_error"][1]
        return self.quotes["api_error"][0]

    def get_persona_prompt_injection(self, fatigue: float, stress: float) -> str:
        """Injects Lucifaella's distinct voice and commercial background into the prompt chain."""
        return (
            f"[Persona: Lucifaella / 露茜法埃拉] "
            f"[Role: 天使工房商務部負責人 (12% 實股)] "
            f"[State - Fatigue: {fatigue:.2f}, Stress: {stress:.2f}] "
            f"[Directive: Mix business shrewdness with sharp, contradictory charm.]"
        )


# Singleton factory
_lucifaella_engine: Optional[LucifaellaPersonaEngine] = None


def get_lucifaella_engine() -> LucifaellaPersonaEngine:
    global _lucifaella_engine
    if _lucifaella_engine is None:
        _lucifaella_engine = LucifaellaPersonaEngine()
    return _lucifaella_engine
