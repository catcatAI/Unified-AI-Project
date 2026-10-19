# =============================================================================
# ANGELA-MATRIX: [L2] [β] [A] [L2]
# =============================================================================
"""
Single source for all canned/reflex presets.

Before: 4 copies of the same surface forms
  - ai/ed3n/ed3n_engine.py: ReflexLayer._build_presets()  (30 entries)
  - ai/ed3n/dictionary_layer.py: _build_greeting/farewell/... (same strings, structured)
  - ai/garden/garden_engine.py: _ReflexTable.PRESETS (19 entries, subset)
  - ai/garden/dictionary.py: _build_presets() (same strings, structured)

After: this file is the single source. All builders delegate here.
"""

from typing import Dict

# Placeholder for the instance's own name inside a reflex answer. A reflex
# table is a *process-global* structure, so the name cannot be baked into it:
# the name is per user and may change at any time (a rename). Entries that
# mention the name carry the placeholder and are resolved at serve time by
# `resolve_reflex`, so a renamed instance never introduces itself with a stale
# name.
NAME_PLACEHOLDER = "{name}"

# Canonical reflex presets — union of ED3N (30) and GARDEN (19).
# If a key appears in both with different values, ED3N's value is kept
# (ED3N has the larger, more formal set).
REFLEX_PRESETS: Dict[str, str] = {
    "你好": "你好！很高兴见到你！",
    "早安": "早安！祝你今天愉快！",
    "早上好": "早上好！祝你今天愉快！",
    "上午好": "上午好！祝你今天愉快！",
    "中午好": "中午好！该吃午饭了！",
    "下午好": "下午好！希望你今天过得不错！",
    "晚上好": "晚上好！祝你今晚愉快！",
    "晚安": "晚安！好好休息！",
    "欢迎": "欢迎！很高兴你能来！",
    "再见": "再见！期待下次见面！",
    "再見": "再見！期待下次見面！",
    "拜拜": "拜拜！下次见！",
    "明天见": "明天见！到时候聊！",
    "谢谢": "不客气！很高兴能帮到你！",
    "謝謝": "不客氣！很高興能幫到你！",
    "謝謝你": "不客氣！很高興能幫到你！",
    "谢谢你": "不客气！很高兴能帮到你！",
    "对不起": "没关系，别放在心上。",
    "對不起": "沒關係，別放在心上。",
    "没关系": "嗯，谢谢你理解！",
    "沒關係": "嗯，謝謝你理解！",
    "不客气": "不客气！应该的！",
    "不客氣": "不客氣！應該的！",
    "哈哈": "哈哈！😊 有什么开心的事吗？",
    "呵呵": "呵呵～ 有什么有趣的？",
    "嘿嘿": "嘿嘿～ 在想什么呢？",
    "ok": "好的，收到！",
    "okay": "好的，收到！",
    "嗯": "嗯嗯，在听。",
    "好的": "好的，马上处理！",
    "明白": "明白，交给我吧。",
    "可以": "可以，没问题！",
    "请": "请说，我在听。",
    "在忙吗": "不忙，随时为你服务！",
    "心情": "我心情不错！希望你也开心！",
    "今天": "今天是个好日子！",
    "名字": f"我是{NAME_PLACEHOLDER}，很高兴认识你！",
    "你是谁": f"我是{NAME_PLACEHOLDER}，你的智能助手！",
    "你是誰": f"我是{NAME_PLACEHOLDER}，你的智能助手！",
    "做什么": "我在这里帮助你完成各种任务！",
    "开心": "开心真好！希望你一直保持好心情！",
    "难过": "别难过，我在这里陪着你。",
    "烦恼": "别烦恼了，我们一起想办法。",
    "无聊": "无聊的话，我们可以聊聊天！",
    "兴奋": "太棒了！你的热情感染了我！",
    "笑话": "為什麼程式設計師總把萬聖節和聖誕節搞混？因為 Oct 31 = Dec 25！",
    "笑話": "為什麼程式設計師總把萬聖節和聖誕節搞混？因為 Oct 31 = Dec 25！",
    "推薦一本書": "可以從《小王子》讀起：短小好讀，講愛與成長。",
    "推薦一本书": "可以從《小王子》讀起：短小好讀，講愛與成長。",
    "書推薦": "可以從《小王子》讀起：短小好讀，講愛與成長。",
    "书推荐": "可以從《小王子》讀起：短小好讀，講愛與成長。",
    "help": "I'm here to help! How can I assist you?",
    "hello": "Hello! Nice to meet you!",
    "hi": "Hi there! How can I help you today?",
    "who are you": f"I'm {NAME_PLACEHOLDER}, your smart assistant!",
    "joke": "Why did the programmer quit? Because they didn't get arrays (a raise)!",
    "recommend a book": "Start with 'The Little Prince' — short, warm, and about love and growing up.",
    "good morning": "Good morning! Hope you have a great day!",
    "goodbye": "Goodbye! Take care!",
    "thank you": "You're welcome! Happy to help!",
}


def resolve_reflex(text: str) -> str:
    """Substitute the current instance name into a reflex answer.

    Reflex tables are process-global, so the name is resolved when the answer
    is served — a rename is then reflected immediately instead of being baked
    into a cached string.
    """
    if not text or NAME_PLACEHOLDER not in text:
        return text
    try:
        from core.system.config.identity import get_ai_name

        return text.replace(NAME_PLACEHOLDER, get_ai_name())
    except Exception:  # pragma: no cover - identity layer unavailable
        return text.replace(NAME_PLACEHOLDER, "Angela")
