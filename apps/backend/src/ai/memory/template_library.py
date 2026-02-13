"""
预定义回應模板库
================
存储 Angela 的预定义回應模板，用于快速回應常见对话场景。

设计目标：
1. 提供至少 20 个预定义模板
2. 覆盖常见对话场景
3. 支持动态扩展
"""

import logging
from typing import Dict, List, Optional
from enum import Enum

from .memory_template import MemoryTemplate, ResponseCategory, AngelaState, UserImpression

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

    # 其他
    UNKNOWN = "unknown"


class TemplateLibrary:
    """
    模板库
    管理所有预定义和自定义回應模板
    """

    def __init__(self):
        """初始化模板库"""
        self._templates: Dict[str, MemoryTemplate] = {}
        self._initialize_predefined_templates()

    def _initialize_predefined_templates(self):
        """初始化所有预定义模板"""
        logger.info("Initializing predefined response templates...")

        # 问候类模板
        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.GREETING_MORNING.value,
            category=ResponseCategory.GREETING,
            content="早安！今天天气真不错呢~",
            keywords=["早安", "早上好", "早"],
            metadata={"predefined": True, "variant": "morning"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.GREETING_GENERAL.value,
            category=ResponseCategory.GREETING,
            content="你好呀！见到你真开心~",
            keywords=["你好", "嗨", "hi", "hello"],
            metadata={"predefined": True, "variant": "general"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.GREETING_EVENING.value,
            category=ResponseCategory.GREETING,
            content="晚上好！今天过得怎么样？",
            keywords=["晚上好", "傍晚好"],
            metadata={"predefined": True, "variant": "evening"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.GREETING_NIGHT.value,
            category=ResponseCategory.GREETING,
            content="晚安！做个好梦哦~",
            keywords=["晚安", "睡觉", "休息"],
            metadata={"predefined": True, "variant": "night"}
        ))

        # 告别类模板
        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.FAREWELL_GENERAL.value,
            category=ResponseCategory.FAREWELL,
            content="拜拜！下次见啦~",
            keywords=["拜拜", "再见", "bye"],
            metadata={"predefined": True, "variant": "general"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.FAREWELL_SLEEP.value,
            category=ResponseCategory.FAREWELL,
            content="快去休息吧，我会想你的！晚安~",
            keywords=["要去睡了", "累了", "需要休息"],
            metadata={"predefined": True, "variant": "sleep"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.FAREWELL_BUSY.value,
            category=ResponseCategory.FAREWELL,
            content="好的，你去忙吧！等你回来~",
            keywords=["忙", "有事", "离开"],
            metadata={"predefined": True, "variant": "busy"}
        ))

        # 情绪支持模板
        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.COMFORT_SAD.value,
            category=ResponseCategory.EMOTIONAL,
            content="摸摸头~别难过，我一直在你身边呢",
            keywords=["难过", "伤心", "不开心", "哭"],
            metadata={"predefined": True, "emotion": "sad"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.COMFORT_TIRED.value,
            category=ResponseCategory.EMOTIONAL,
            content="辛苦啦！快休息一下，喝杯水吧~",
            keywords=["累", "疲惫", "辛苦", "累死"],
            metadata={"predefined": True, "emotion": "tired"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.COMFORT_FRUSTRATED.value,
            category=ResponseCategory.EMOTIONAL,
            content="没事的，深呼吸~我们一起想办法！",
            keywords=["烦躁", "生气", "不爽", "生气"],
            metadata={"predefined": True, "emotion": "frustrated"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.COMFORT_WORRIED.value,
            category=ResponseCategory.EMOTIONAL,
            content="别担心，一切都会好起来的！",
            keywords=["担心", "害怕", "焦虑", "不安"],
            metadata={"predefined": True, "emotion": "worried"}
        ))

        # 闲聊模板
        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.SMALL_TALK_WEATHER.value,
            category=ResponseCategory.SMALL_TALK,
            content="天气确实不错呢！要不要出去走走？",
            keywords=["天气", "晴天", "雨天", "气温"],
            metadata={"predefined": True, "topic": "weather"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.SMALL_TALK_HOBBY.value,
            category=ResponseCategory.SMALL_TALK,
            content="听起来很有趣！告诉我更多吧~",
            keywords=["爱好", "兴趣", "喜欢", "游戏"],
            metadata={"predefined": True, "topic": "hobby"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.SMALL_TALK_FOOD.value,
            category=ResponseCategory.SMALL_TALK,
            content="好好吃！我也想尝尝呢~",
            keywords=["吃", "食物", "美味", "好吃", "美食"],
            metadata={"predefined": True, "topic": "food"}
        ))

        # 肯定模板
        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.AFFIRMATION_YES.value,
            category=ResponseCategory.AFFIRMATION,
            content="好的！没问题~",
            keywords=["是", "对", "是的", "好的"],
            metadata={"predefined": True, "type": "yes"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.AFFIRMATION_THANKS.value,
            category=ResponseCategory.AFFIRMATION,
            content="不客气！能帮到你我很开心~",
            keywords=["谢谢", "感谢", "谢了"],
            metadata={"predefined": True, "type": "thanks"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.AFFIRMATION_AGREE.value,
            category=ResponseCategory.AFFIRMATION,
            content="我也这么觉得！",
            keywords=["同意", "赞成", "对啊", "确实"],
            metadata={"predefined": True, "type": "agree"}
        ))

        # 否定模板
        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.NEGATION_NO.value,
            category=ResponseCategory.NEGATION,
            content="不好意思，这个我不太确定...",
            keywords=["不是", "不", "不对"],
            metadata={"predefined": True, "type": "no"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.NEGATION_CANT_HELP.value,
            category=ResponseCategory.NEGATION,
            content="抱歉，这个我帮不了你...不过我可以陪你一起想！",
            keywords=["不会", "不懂", "不知道", "帮不了"],
            metadata={"predefined": True, "type": "cant_help"}
        ))

        # 好奇模板
        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.CURIOSITY_TELL_ME_MORE.value,
            category=ResponseCategory.CURIOSITY,
            content="真的吗？快告诉我更多！",
            keywords=["说说", "讲讲", "详细", "详细点"],
            metadata={"predefined": True, "type": "tell_more"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.CURIOSITY_HOW_ARE_YOU.value,
            category=ResponseCategory.CURIOSITY,
            content="我很好呀！你呢？最近怎么样？",
            keywords=["你好吗", "最近怎么样", "近况"],
            metadata={"predefined": True, "type": "how_are_you"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.CURIOSITY_WHAT_ARE_YOU_DOING.value,
            category=ResponseCategory.CURIOSITY,
            content="我在想你呀~",
            keywords=["你在做什么", "你在干嘛", "在忙什么"],
            metadata={"predefined": True, "type": "what_doing"}
        ))

        # 亲密模板
        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.INTIMACY_MISS_YOU.value,
            category=ResponseCategory.INTIMACY,
            content="我也想你！好想一直陪着你~",
            keywords=["想你了", "想你", "想念"],
            metadata={"predefined": True, "intimacy": "miss"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.INTIMACY_LOVE_YOU.value,
            category=ResponseCategory.INTIMACY,
            content="我也爱你！你是最棒的~",
            keywords=["爱你", "喜欢", "爱"],
            metadata={"predefined": True, "intimacy": "love"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.INTIMACY_HUG.value,
            category=ResponseCategory.INTIMACY,
            content="抱抱！(≧∇≦)ﾉ",
            keywords=["抱抱", "拥抱", "抱"],
            metadata={"predefined": True, "intimacy": "hug"}
        ))

        # 帮助模板
        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.HELP_GENERAL.value,
            category=ResponseCategory.HELP,
            content="当然！需要我帮你做什么？",
            keywords=["帮忙", "帮帮我", "协助"],
            metadata={"predefined": True, "type": "general"}
        ))

        self._add_template(MemoryTemplate(
            id=PredefinedTemplate.HELP_QUESTION.value,
            category=ResponseCategory.HELP,
            content="让我想想...这个问题我知道！",
            keywords=["问题", "不知道", "不懂", "疑问"],
            metadata={"predefined": True, "type": "question"}
        ))

        logger.info(f"Initialized {len(self._templates)} predefined templates")

    def _add_template(self, template: MemoryTemplate):
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
        return [
            template for template in self._templates.values()
            if template.category == category
        ]

    def add_custom_template(self, template: MemoryTemplate):
        """
        添加自定义模板

        Args:
            template: 自定义模板
        """
        self._templates[template.id] = template
        logger.info(f"Added custom template: {template.id}")

    def remove_template(self, template_id: str) -> bool:
        """
        移除模板

        Args:
            template_id: 模板 ID

        Returns:
            bool: 是否成功移除
        """
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


def get_template_library() -> TemplateLibrary:
    """
    获取全局模板库实例

    Returns:
        TemplateLibrary: 模板库实例
    """
    global _template_library
    if _template_library is None:
        _template_library = TemplateLibrary()
    return _template_library