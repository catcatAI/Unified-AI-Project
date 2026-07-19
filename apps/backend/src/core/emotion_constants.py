"""
共用情緒關鍵字常數

提取自 emotion_analyzer.py 和 user_monitor.py 的共同關鍵字。
"""

# 情緒分類共用關鍵字
# 格式: {emotion_label: [keywords]}
EMOTION_KEYWORDS = {
    "happy": [
        "开心",
        "高兴",
        "快乐",
        "棒",
        "好",
        "哈哈",
        "喜欢",
        "爱",
        "happy",
        "great",
        "awesome",
        "good",
        "love",
        "like",
    ],
    "sad": [
        "难过",
        "悲伤",
        "失望",
        "不好",
        "哭",
        "痛苦",
        "sad",
        "bad",
        "disappointed",
        "cry",
        "pain",
    ],
    "angry": [
        "烦",
        "生气",
        "讨厌",
        "糟糕",
        "失败",
        "frustrated",
        "annoyed",
        "angry",
        "hate",
        "failed",
    ],
    "fear": [
        "担心",
        "害怕",
        "紧张",
        "焦虑",
        "worried",
        "scared",
        "nervous",
        "anxious",
        "afraid",
    ],
    "surprise": [
        "哇",
        "天啊",
        "wow",
        "amazing",
    ],
    "calm": [
        "平静",
        "放松",
        "calm",
        "relax",
        "relaxed",
    ],
}
