"""Angela Chat Service - 智能對話生成"""

import random
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


# 情感與語義分析
EMOTION_PATTERNS = {
    "positive": [
        "開心",
        "高興",
        "棒",
        "好",
        "爽",
        "萬歲",
        "great",
        "good",
        "happy",
        ":-)",
        "😊",
        "太棒了",
        "完美",
        "厲害",
        "贏了",
        "成功",
    ],
    "negative": [
        "難過",
        "傷心",
        "不爽",
        "壞",
        "糟糕",
        "鬱悶",
        "sad",
        "bad",
        ":-(",
        "😢",
        "痛苦",
        "討厭",
        "失望",
        "崩潰",
        "壓力",
    ],
    "question": [
        "?",
        "？",
        "什麼",
        "為什麼",
        "如何",
        "怎麼",
        "who",
        "what",
        "why",
        "how",
        "能否",
        "可以",
        "哪裡",
        "幾點",
        "多少",
    ],
    "greeting": [
        "你好",
        "嗨",
        "hello",
        "hi",
        "早安",
        "晚安",
        "在嗎",
        "喵",
        "哈囉",
        "嘿",
        "見面",
        "好久不見",
        "回來了",
    ],
    "thanks": [
        "謝謝",
        "感謝",
        "thanks",
        "thank",
        "多謝",
        "不錯",
        "感謝你",
        "謝啦",
        "多謝你",
        "gracias",
    ],
    "goodbye": [
        "再見",
        "拜拜",
        "bye",
        "晚安",
        "走了",
        "要去",
        "離開",
        "先走",
        "下次見",
        "回頭見",
    ],
    "compliment": [
        "棒",
        "厲害",
        "讚",
        "強",
        "厲害",
        "美",
        "帥",
        "聰明",
        "好",
        "不錯",
        "amazing",
        "awesome",
        "perfect",
    ],
    "empathy": [
        "懂",
        "理解",
        "明白",
        "同情",
        "心疼",
        "擔心",
        "關心",
        "體會",
        "感同身受",
        "理解你",
    ],
    "curiosity": [
        "什麼",
        "怎麼",
        "為什麼",
        "哪裡",
        "幾點",
        "誰",
        "多少",
        "好奇",
        "想知道",
        "怎樣",
    ],
    "encouragement": [
        "加油",
        "努力",
        "堅持",
        "不放棄",
        "一定行",
        "相信",
        "支持",
        "你可以",
        "別放棄",
        "繼續",
    ],
}


def analyze_intent(user_message: str) -> Tuple[str, str, float]:
    """分析用戶意圖 - 返回 (意圖類型, 關鍵詞, 置信度)"""
    msg = user_message.lower().strip()

    # 檢查再見
    for word in EMOTION_PATTERNS["goodbye"]:
        if word in msg:
            return ("goodbye", word, 0.9)

    # 檢查感謝
    for word in EMOTION_PATTERNS["thanks"]:
        if word in msg:
            return ("thanks", word, 0.9)

    # 檢查問候
    for word in EMOTION_PATTERNS["greeting"]:
        if word in msg:
            return ("greeting", word, 0.9)

    # 檢查讚美
    compliment_count = sum(1 for w in EMOTION_PATTERNS["compliment"] if w in msg)
    if compliment_count > 0:
        return ("compliment", "compliment", min(0.6 + compliment_count * 0.15, 0.95))

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

    # 檢查好奇心
    curiosity_count = sum(1 for w in EMOTION_PATTERNS["curiosity"] if w in msg)
    if curiosity_count > 0:
        return ("curiosity", "curiosity", min(0.5 + curiosity_count * 0.15, 0.85))

    # 檢查鼓勵
    encouragement_count = sum(1 for w in EMOTION_PATTERNS["encouragement"] if w in msg)
    if encouragement_count > 0:
        return (
            "encouragement",
            "encouragement",
            min(0.5 + encouragement_count * 0.15, 0.85),
        )

    # 檢查同理心
    empathy_count = sum(1 for w in EMOTION_PATTERNS["empathy"] if w in msg)
    if empathy_count > 0:
        return ("empathy", "empathy", min(0.5 + empathy_count * 0.15, 0.85))

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
            "哈囉！我們又見面了~",
            "早安/晚安！一切都好嗎？",
            "你好！有什麼新鮮事嗎？",
            "嗨嗨！今天想聊什麼呢？",
            "哈囉哈囉！期待我們的對話~",
        ],
        "positive": [
            "聽起來很棒呢！",
            "太開心了！繼續保持！",
            "很不錯哦！",
            "這真是太好了！為你感到高興！",
            "哇！太厲害了！",
            "這是個很棒的進步呢！",
            "看來你今天心情不錯~",
            "繼續保持這種狀態！",
            "你的努力一定會有回報的！",
            "這真是太令人振奮了！",
        ],
        "negative": [
            "我理解你的感受。",
            "別難過，一切都會好起來的。",
            "需要我陪你聊聊嗎？",
            "抱抱你，一切沒事的。",
            "我能感受到你的情緒，慢慢來。",
            "這只是暫時的，你一定可以度過。",
            "想說什麼都可以，我會一直聽著。",
            "給自己一些時間，沒關係的。",
            "如果需要幫助，隨時告訴我。",
            "我會一直支持你的。",
        ],
        "question": [
            "這是個有趣的想法，讓我思考一下...",
            "好問題！我來幫你分析...",
            "讓我查查資料再回答你~",
            "嗯...讓我想想...",
            "這個問題很有意思！",
            "我來幫你找找答案~",
            "讓我好好思考一下你的問題。",
            "這個問題值得深入探討！",
            "我需要一些時間來思考這個問題。",
            "好問題！讓我們一起來解決。",
        ],
        "thanks": [
            "不客氣！能幫到你我很開心~",
            "隨時為你服務！",
            "很樂意幫助你！",
            "沒什麼啦，小事一樁~",
            "有需要隨時找我哦！",
            "你的謝意我收到了！",
            "這是我應該做的~",
            "別客氣，我們是朋友嘛！",
            "能幫到你真好！",
            "隨時歡迎你來找我！",
        ],
        "goodbye": [
            "再見！期待下次見面~",
            "拜拜！要照顧好自己哦！",
            "下次見！",
            "再見啦，會想念你的！",
            "保重！有空再來聊~",
            "祝你今天過得愉快！",
            "再見，期待我們的下次對話！",
            "拜拜，一切都順利！",
            "下次見，加油哦！",
            "再見！心情愉快！",
        ],
        "compliment": [
            "謝謝你的誇獎！我好開心~",
            "你也很棒呀！",
            "彼此彼此啦~",
            "哈哈，你過獎了！",
            "謝謝！聽到你這麼說我感到很溫暖。",
            "你也很了不起！",
            "能被你稱讚是我的榮幸！",
            "我們一起變得更好吧！",
            "你的眼光真好！",
            "謝謝！你讓我更有信心了！",
        ],
        "statement": {
            "complex": [
                "我明白了，讓我幫你想想...",
                "這是個不錯的話題！",
                "我理解了，你想說的是...對吧？",
                "嗯，這點很有意思...",
                "我聽懂了，繼續說下去~",
                "這個觀點值得思考！",
                "我理解你的意思了。",
                "這說明什麼呢？讓我分析一下...",
                "你的想法很有見地！",
                "這個角度我沒想到，謝謝分享！",
            ],
            "simple": [
                "我聽到了！",
                "嗯嗯，繼續說~",
                "很有意思！",
                "我知道了！",
                "嗯哼...",
                "原來是這樣！",
                "好的好的~",
                "我明白了！",
                "喔喔！",
                "這樣啊~",
            ],
            "minimal": [
                "好的。",
                "我知道了。",
                "嗯。",
                "了解。",
                "OK。",
                "嗯嗯。",
                "好喔。",
                "收到。",
                "嗯~",
                "OK~",
            ],
        },
        "empathy": [
            "我理解你的感受。",
            "這一定不容易吧...",
            "我能感受到你的心情。",
            "你很勇敢，真的。",
            "你做得很好了，別太苛刻自己。",
            "相信你自己，你一定可以的。",
            "我會一直支持你的。",
            "慢慢來，不急於一時。",
            "你已經盡力了，這就足夠了。",
            "別擔心，有我在呢。",
        ],
        "curiosity": [
            "真的嗎？再多告訴我一些！",
            "後來怎麼樣了？",
            "這太有趣了！然後呢？",
            "哇！這是什麼？",
            "我也很好奇！",
            "快說快說！",
            "這還蠻新鮮的！",
            "原來如此！還有嗎？",
            "太神奇了！怎麼做到的？",
            "我聽得很認真呢！",
        ],
        "encouragement": [
            "你可以的！加油！",
            "我相信你！",
            "你比你想像中更強大！",
            "一步一步來，沒問題的！",
            "你已經做得很好了！",
            "不要放棄，繼續前進！",
            "這只是個小挑戰，你一定可以！",
            "堅持就是勝利！",
            "你有這個能力的！",
            "讓我們一起努力！",
        ],
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
