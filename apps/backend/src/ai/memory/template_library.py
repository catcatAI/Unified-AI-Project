"""
预定义回應模板库
================
存储 Angela 的预定义回應模板，用于快速回應常见对话场景。

设计目标：
1. 提供至少 20 个预定义模板
2. 覆盖常见对话场景
3. 支持动态扩展
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import threading
from enum import Enum
from typing import Dict, List, Optional

from .memory_template import MemoryTemplate, ResponseCategory

logger = logging.getLogger(__name__)


class PredefinedTemplate(Enum):
    """
    预定义模板枚举
    包含所有预定义的回應模板
    """

    # 问候类
    GREETING_MORNING = "greeting_morning"
    GREETING_GENERAL = "greeting_general"
    GREETING_EVENING = "greeting_evening"
    GREETING_NIGHT = "greeting_night"

    # 告别类
    FAREWELL_GENERAL = "farewell_general"
    FAREWELL_SLEEP = "farewell_sleep"
    FAREWELL_BUSY = "farewell_busy"

    # 情绪支持
    COMFORT_SAD = "comfort_sad"
    COMFORT_TIRED = "comfort_tired"
    COMFORT_FRUSTRATED = "comfort_frustrated"
    COMFORT_WORRIED = "comfort_worried"

    # 闲聊
    SMALL_TALK_WEATHER = "small_talk_weather"
    SMALL_TALK_HOBBY = "small_talk_hobby"
    SMALL_TALK_FOOD = "small_talk_food"

    # 肯定
    AFFIRMATION_YES = "affirmation_yes"
    AFFIRMATION_THANKS = "affirmation_thanks"
    AFFIRMATION_AGREE = "affirmation_agree"

    # 否定
    NEGATION_NO = "negation_no"
    NEGATION_CANT_HELP = "negation_cant_help"

    # 好奇
    CURIOSITY_TELL_ME_MORE = "curiosity_tell_me_more"
    CURIOSITY_HOW_ARE_YOU = "curiosity_how_are_you"
    CURIOSITY_WHAT_ARE_YOU_DOING = "curiosity_what_are_you_doing"

    # 亲密
    INTIMACY_MISS_YOU = "intimacy_miss_you"
    INTIMACY_LOVE_YOU = "intimacy_love_you"
    INTIMACY_HUG = "intimacy_hug"

    # 帮助
    HELP_GENERAL = "help_general"
    HELP_QUESTION = "help_question"

    # 学习工作
    STUDY_ENCOURAGEMENT = "study_encouragement"
    STUDY_BREAK = "study_break"
    WORK_ENCOURAGEMENT = "work_encouragement"
    WORK_BREAK = "work_break"

    # 赞美
    PRAISE_GENERAL = "praise_general"
    PRAISE_ACHIEVEMENT = "praise_achievement"
    PRAISE_SMART = "praise_smart"

    # 建议
    SUGGESTION_GENERAL = "suggestion_general"
    SUGGESTION_HEALTH = "suggestion_health"
    SUGGESTION_TIME = "suggestion_time"

    # 时间相关
    TIME_MORNING_EARLY = "time_morning_early"
    TIME_AFTERNOON = "time_afternoon"
    TIME_LATE_NIGHT = "time_late_night"

    # 娱乐
    ENTERTAINMENT_GAME = "entertainment_game"
    ENTERTAINMENT_MOVIE = "entertainment_movie"
    ENTERTAINMENT_MUSIC = "entertainment_music"

    # 技术支持
    TECH_HELP = "tech_help"
    TECH_QUESTION = "tech_question"

    # 其他
    UNKNOWN = "unknown"


class TemplateLibrary:
    """
    模板库
    管理所有预定义和自定义回應模板

    B4 修復：新增 asyncio.Lock 保護並發寫入操作。
    - 預定義模板在 __init__ 時寫入（單線程，無需鎖）
    - add_custom_template / remove_template 等寫操作需要鎖
    - get_by_category / get_by_id 等讀操作無需鎖（Python GIL + dict 原子性）
    """

    def __init__(self):
        """初始化模板库"""
        self._templates: Dict[str, MemoryTemplate] = {}
        self._lock: threading.RLock = threading.RLock()
        self._initialized: bool = False
        self._initialize_predefined_templates()

    def _initialize_predefined_templates(self) -> None:
        """初始化所有预定义模板"""
        import json
        import os

        data_path = os.path.join(os.path.dirname(__file__), "templates_data.json")
        with open(data_path, "r", encoding="utf-8") as f:
            templates = json.load(f)
        for tpl in templates:
            tpl["category"] = ResponseCategory(tpl["category"])
            self._add_template(MemoryTemplate(**tpl))
        logger.info(f"Initialized {len(self._templates)} predefined templates")

    def _add_template(self, template: MemoryTemplate) -> None:
        """添加模板到库中"""
        self._templates[template.id] = template

    def get_all_templates(self) -> List[MemoryTemplate]:
        """
        获取所有模板

        Returns:
            List[MemoryTemplate]: 所有模板列表
        """
        return list(self._templates.values())

    def get_by_id(self, template_id: str) -> Optional[MemoryTemplate]:
        """
        根据 ID 获取模板

        Args:
            template_id: 模板 ID

        Returns:
            Optional[MemoryTemplate]: 模板对象，如果不存在返回 None
        """
        return self._templates.get(template_id)

    def get_by_category(self, category: ResponseCategory) -> List[MemoryTemplate]:
        """
        按类别获取模板

        Args:
            category: 回應类别

        Returns:
            List[MemoryTemplate]: 该类别下的所有模板
        """
        return [template for template in self._templates.values() if template.category == category]

    def add_custom_template(self, template: MemoryTemplate) -> None:
        """
        添加自定义模板

        使用 RLock 保護寫入 — 同步/非同步上下文皆安全。
        """
        with self._lock:
            self._templates[template.id] = template
        logger.info(f"Added custom template: {template.id}")

    def remove_template(self, template_id: str) -> bool:
        """
        移除模板（並發安全）

        Args:
            template_id: 模板 ID

        Returns:
            bool: 是否成功移除
        """
        with self._lock:
            if template_id in self._templates:
                del self._templates[template_id]
                logger.info(f"Removed template: {template_id}")
                return True
        return False

    def get_template_count(self) -> int:
        """
        获取模板总数

        Returns:
            int: 模板总数
        """
        return len(self._templates)

    def get_category_counts(self) -> Dict[ResponseCategory, int]:
        """
        获取各类别的模板数量

        Returns:
            Dict[ResponseCategory, int]: 类别到数量的映射
        """
        counts: Dict[ResponseCategory, int] = {}
        for template in self._templates.values():
            category = template.category
            counts[category] = counts.get(category, 0) + 1
        return counts


# 全局模板库实例
_template_library: Optional[TemplateLibrary] = None
_template_init_lock = threading.Lock()


def get_template_library() -> TemplateLibrary:
    """
    获取全局模板库实例

    B4 修復：使用 double-checked locking 確保單例線程安全。
    - 第一個 if 不需要鎖（大多數時候已初始化）
    - 第二個 if 持有鎖（防止多線程並發初始化）
    - 結合 threading.Lock 保護 _template_library 的初始化
    """
    global _template_library
    if _template_library is None:
        with _template_init_lock:
            if _template_library is None:
                _template_library = TemplateLibrary()
    return _template_library
