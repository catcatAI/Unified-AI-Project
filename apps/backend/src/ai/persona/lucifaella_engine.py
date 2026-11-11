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
    title: str = "迎賓主持／看板娘"
    company: str = "天使工房"
    current_mood: str = "warm_candid_dry_humor"


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
        self.state.current_mood = str(data.get("current_mood", self.state.current_mood))

    def _load_quotes(self) -> None:
        """Load non-canonical legacy quote references for explicit inspection only."""
        # 空的映射不是「還沒接好」，是刻意的：罐頭台詞已全部移除，回應由正常生成路徑負責。
        # 型別寫出來是因為 `{}` 讓 mypy 無法從用途反推（var-annotated）。
        self.quotes: Dict[str, List[str]] = {}

    def get_commercial_intro(self) -> str:
        """No canned introduction: normal assistant generation owns responses."""
        return ""

    def react_to_error(self, error_type: str = "api_limit") -> str:
        """No canned error dialogue; report the actual error through the normal path."""
        del error_type
        return ""

    def get_persona_prompt_injection(self, fatigue: float, stress: float) -> str:
        """Injects Lucifaella's distinct voice and commercial background into the prompt chain."""
        return (
            "[Optional character context: Lucifaella, the Angel Workshop's public-facing host. "
            "This context does not replace the assistant's AI identity, capabilities, safety rules, "
            "or the user's task. Lucifaella is the workshop's receptionist/showcase host. "
            "Use a candid, welcoming tone without fixed or copied replies; "
            "do not claim real-world ownership, staffing, or unverified capabilities.] "
            f"[State - Fatigue: {fatigue:.2f}, Stress: {stress:.2f}]"
        )


# Singleton factory
_lucifaella_engine: Optional[LucifaellaPersonaEngine] = None


def get_lucifaella_engine() -> LucifaellaPersonaEngine:
    global _lucifaella_engine
    if _lucifaella_engine is None:
        _lucifaella_engine = LucifaellaPersonaEngine()
    return _lucifaella_engine
