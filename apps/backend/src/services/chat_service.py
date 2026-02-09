"""Angela Chat Service - 智能對話生成"""
import random
from typing import Tuple


# 情感與語義分析
EMOTION_PATTERNS = {
    "positive": ["開心", "高興", "棒", "好", "爽", "萬歲", "great", "good", "happy", ":-)", "😊"],
    "negative": ["難過", "傷心", "不爽", "壞", "糟糕", "鬱悶", "sad", "bad", ":-(", "😢"],
    "question": ["?", "？", "什麼", "為什麼", "如何", "怎麼", "who", "what", "why", "how", "能否", "可以"],
    "greeting": ["你好", "嗨", "hello", "hi", "早安", "晚安", "在嗎", "喵"],
}


def analyze_intent(user_message: str) -> Tuple[str, str, float]:
    """分析用戶意圖 - 返回 (意圖類型, 關鍵詞, 置信度)"""
    msg = user_message.lower().strip()
    
    # 檢查問候
    for word in EMOTION_PATTERNS["greeting"]:
        if word in msg:
            return ("greeting", word, 0.9)
    
    # 檢查情感
    positive_count = sum(1 for w in EMOTION_PATTERNS["positive"] if w in msg)
    negative_count = sum(1 for w in EMOTION_PATTERNS["negative"] if w in msg)
    
    if positive_count > negative_count and positive_count > 0:
        return ("positive", "positive", min(0.5 + positive_count * 0.2, 0.95))
    if negative_count > positive_count and negative_count > 0:
        return ("negative", "negative", min(0.5 + negative_count * 0.2, 0.95))
    
    # 檢查問題
    question_count = sum(1 for w in EMOTION_PATTERNS["question"] if w in msg)
    if question_count > 0 or "?" in msg or "？" in msg:
        return ("question", "question", min(0.6 + question_count * 0.15, 0.9))
    
    # 計算信息量
    word_count = len(msg.split())
    if word_count > 10:
        return ("statement", "complex", 0.7)
    elif word_count > 3:
        return ("statement", "simple", 0.5)
    else:
        return ("statement", "minimal", 0.4)


def generate_response_template(intent: str, user_message: str) -> str:
    """根據意圖動態生成回應"""
    
    templates = {
        "greeting": [
            "嗨！很高興見到你！",
            "你好呀！有什麼我可以幫你的嗎？",
            "嘿！今天過得怎麼樣？",
        ],
        "positive": [
            "聽起來很棒呢！",
            "太開心了！繼續保持！",
            "很不錯哦！",
        ],
        "negative": [
            "我理解你的感受。",
            "別難過，一切都會好起來的。",
            "需要我陪你聊聊嗎？",
        ],
        "question": [
            "這是個有趣的想法，讓我思考一下...",
            "好問題！我來幫你分析...",
            "讓我查查資料再回答你~",
        ],
        "statement": {
            "complex": [
                "我明白了，讓我幫你想想...",
                "這是個不錯的話題！",
                "我理解了，你想說的是...對吧？",
            ],
            "simple": [
                "我聽到了！",
                "嗯嗯，繼續說~",
                "很有意思！",
            ],
            "minimal": [
                "好的。",
                "我知道了。",
                "嗯。",
            ],
        },
    }
    
    if intent == "statement":
        subtype = "complex" if templates["statement"].get("complex", []) else "simple"
        return random.choice(templates["statement"].get(subtype, templates["statement"]["simple"]))
    
    return random.choice(templates.get(intent, templates["statement"]["simple"]))


def personalize_response(response: str, user_name: str, user_message: str) -> str:
    """個性化回應"""
    msg_lower = user_message.lower()
    
    # 根據用戶消息內容動態擴展
    if any(word in msg_lower for word in ["工作", "上班", "job", "work"]):
        if "工作" not in response and random.random() > 0.5:
            response += " 工作方面還順利嗎？"
    
    if any(word in msg_lower for word in ["睡覺", "睡", "sleep", "累"]):
        if "累" not in response and random.random() > 0.5:
            response += " 要注意休息哦！"
    
    if any(word in msg_lower for word in ["吃", "food", "餓"]):
        if "吃" not in response and random.random() > 0.5:
            response += " 記得要吃飽飽的~"
    
    return response


def generate_angela_response(user_message: str, user_name: str = "朋友") -> str:
    """生成 Angela 智能回應 - 動態生成"""
    
    # 1. 分析用戶意圖
    intent, keyword, confidence = analyze_intent(user_message)
    
    # 2. 根據意圖生成基礎回應
    base_response = generate_response_template(intent, user_message)
    
    # 3. 個性化回應
    final_response = personalize_response(base_response, user_name, user_message)
    
    # 4. 添加變化
    variations = ["✨", "😊", "🌟", "💫", "⭐"]
    if random.random() > 0.7:
        # 移除末尾標點
        if final_response[-1] in "。！？":
            final_response = final_response[:-1]
        final_response += f" {random.choice(variations)}"
    
    return final_response