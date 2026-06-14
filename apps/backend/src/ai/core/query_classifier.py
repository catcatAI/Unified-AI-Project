# =============================================================================
# ANGELA-MATRIX: L2-L3[记忆层/身份层] βδ [A] L2+
# =============================================================================
#
# 职责: 查询分类器 — 将用户查询分类到领域，用于 Model Bus 路由系统
# 维度: 认知维度 (β) 用于模式匹配，精神维度 (δ) 用于意图理解
# 安全: 使用 Key A (后端控制)
# 成熟度: L2+ 等级才能完全理解查询路由逻辑
#
# =============================================================================

import re
from enum import Enum
from typing import List, Pattern, Tuple

from core.system.config.magic_numbers import confidence_value, limit_value, threshold_value


class QueryType(Enum):
    REFLEX = "reflex"
    GREETING = "greeting"
    MATH = "math"
    LOGIC = "logic"
    KNOWLEDGE = "knowledge"
    CREATIVE = "creative"
    OPINION = "opinion"
    COMMAND = "command"
    UNKNOWN = "unknown"
    # Phase 2: extended types
    FILE = "file"
    SEARCH = "search"
    CODE = "code"
    EXECUTE = "execute"
    TASK = "task"
    VISION = "vision"
    AUDIO = "audio"


class QueryClassifier:
    """Pattern-based query classifier for Model Bus routing."""

    def __init__(self):
        self._reflex_words: set = {
            "hi", "ok", "okay", "hey", "yo", "oh", "ah",
            "嗯", "好", "是", "不", "啊", "哦", "喂", "嗨", "噢",
        }

        self._patterns: List[Tuple[QueryType, Pattern, float]] = [
            (
                QueryType.GREETING,
                re.compile(
                    r"(你好|早上好|上午好|中午好|下午好|晚上好|晚安|"
                    r"再见|拜拜|谢谢|感谢|"
                    r"\b(hello|hi|hey|good\s*morning|good\s*afternoon|good\s*evening|good\s*bye|thanks?|bye)\b)",
                    re.IGNORECASE,
                ),
                0.9,
            ),
            (
                QueryType.MATH,
                re.compile(
                    r"(\d+\s*[\+\-\*\/]\s*\d+|"
                    r"等于|计算|加|减|乘|除|"
                    r"\b(plus|minus|times|divided\s*by|calculate|solve|equation)\b)",
                    re.IGNORECASE,
                ),
                0.85,
            ),
            (
                QueryType.LOGIC,
                re.compile(
                    r"(\b(true|false|and|or|not|if|bool|nor|xor|neither)\b|"
                    r"if\s+then|逻辑|推理|boolean|proposition)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
            (
                QueryType.KNOWLEDGE,
                re.compile(
                    r"(什么是|是什么|what\s+is|how\s+(does|do|can|to)|"
                    r"why\s+(is|does|do|can)|"
                    r"\b(define|explain)\b|"
                    r"怎么回|多少|how\s+many|what\s+are)",
                    re.IGNORECASE,
                ),
                0.7,
            ),
            (
                QueryType.CREATIVE,
                re.compile(
                    r"(写|作|创作|编|画|虚构|"
                    r"\b(write|poem|story|song|joke|"
                    r"imagine|pretend|creat|make\s+up|compose)\b|"
                    r"想象|如果|假设|绘)",
                    re.IGNORECASE,
                ),
                0.75,
            ),
            (
                QueryType.OPINION,
                re.compile(
                    r"(觉得|认为|看法|意见|评价|建议|"
                    r"推荐|喜欢|不喜欢|优点|缺点|比较|"
                    r"覺得|認為|看法|意見|評價|建議|"
                    r"推薦|喜歡|不喜歡|優點|缺點|比較|"
                    r"\b(opinion|think|believe|feel|suggest|recommend|"
                    r"pros|cons|compare|prefer|better|worse)\b)",
                    re.IGNORECASE,
                ),
                0.75,
            ),
            (
                QueryType.FILE,
                re.compile(
                    r"(整理|清理|删除|移动|复制|重命名|读取|写入|列出|"
                    r"文件|文件夹|目录|路径|"
                    r"整理|清理|刪除|移動|複製|重命名|讀取|寫入|列出|"
                    r"檔案|文件|資料夾|目錄|路徑|"
                    r"\b(organize|delete|move|copy|rename|read|write|list|"
                    r"file|folder|directory|path)\b)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
            (
                QueryType.SEARCH,
                re.compile(
                    r"(搜寻|搜索|查找|找|查询|搜|"
                    r"搜尋|搜索|查找|找|查詢|搜|"
                    r"\b(search|find|look\s*for|google|query|lookup)\b)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
            (
                QueryType.CODE,
                re.compile(
                    r"(程序|代码|函数|变量|循环|数组|对象|"
                    r"调试|重构|优化|实现|"
                    r"程式|代碼|函數|變數|迴圈|陣列|物件|"
                    r"除錯|重構|優化|實作|"
                    r"\b(code|program|script|debug|bug|function|variable|"
                    r"loop|array|refactor|implement)\b)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
            (
                QueryType.EXECUTE,
                re.compile(
                    r"(执行|运行|开启|关闭|启动|停止|暂停|"
                    r"執行|運行|開啟|關閉|啟動|停止|暫停|"
                    r"\b(execute|run|open|close|start|stop|launch|kill)\b)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
            (
                QueryType.TASK,
                re.compile(
                    r"(任务|工作|待办|行程|排程|提醒|"
                    r"任務|工作|待辦|行程|排程|提醒|"
                    r"\b(task|todo|schedule|reminder|plan|planned)\b)",
                    re.IGNORECASE,
                ),
                0.75,
            ),
            (
                QueryType.VISION,
                re.compile(
                    r"(图片|照片|影像|截图|识别|看|"
                    r"圖片|照片|影像|截圖|辨識|看|"
                    r"\b(image|photo|picture|screenshot|recognize|see|vision)\b)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
            (
                QueryType.AUDIO,
                re.compile(
                    r"(语音|音频|录音|音乐|播放|听|"
                    r"語音|音訊|錄音|音樂|播放|聽|"
                    r"\b(audio|voice|speech|music|play|listen)\b)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
            (
                QueryType.COMMAND,
                re.compile(
                    r"^((打開|關閉|啟動|停止|暫停|運行|執行|幫我|請)|"
                    r"\b(open|close|start|stop|please)\b|can\s+you|could\s+you)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
        ]

    def classify(self, text: str) -> Tuple[QueryType, float]:
        """Classify a query text into a QueryType with confidence score 0.0-1.0.

        Uses regex patterns as primary signal, ED3N encode_soft as auxiliary.
        """
        text = text.strip()

        if not text:
            return QueryType.UNKNOWN, 0.0

        if len(text) > limit_value("ai.query_classifier.max_direct_len", 200):
            return QueryType.KNOWLEDGE, confidence_value("ai.query_classifier.long_text_conf", 0.85)

        best_type = QueryType.UNKNOWN
        best_conf = 0.0

        for query_type, pattern, confidence in self._patterns:
            if pattern.search(text):
                if confidence > best_conf:
                    best_type = query_type
                    best_conf = confidence

        # ED3N encode_soft auxiliary signal
        try:
            from ai.ed3n.ed3n_engine import ED3NEngine
            ed3n = ED3NEngine()
            keys = ed3n.dictionary.encode_soft(text)
            ed3n_type, ed3n_conf = self._keys_to_intent(keys)
            if ed3n_conf > best_conf:
                best_type = ed3n_type
                best_conf = ed3n_conf
        except Exception:
            pass

        if text.lower() in self._reflex_words or (len(text) < limit_value("ai.query_classifier.reflex_min_len", 2) and best_conf < threshold_value("ai.query_classifier.reflex_conf_threshold", 0.5)):
            return QueryType.REFLEX, confidence_value("ai.query_classifier.reflex_conf", 0.95)

        if best_conf < threshold_value("ai.query_classifier.question_conf_threshold", 0.5) and text.rstrip().endswith("?"):
            return QueryType.KNOWLEDGE, confidence_value("ai.query_classifier.question_conf", 0.65)

        if best_conf > threshold_value("ai.query_classifier.min_accept_conf", 0.5):
            return best_type, best_conf

        return QueryType.UNKNOWN, confidence_value("ai.query_classifier.unknown_conf", 0.3)

    def _keys_to_intent(self, keys: List[str]) -> Tuple[QueryType, float]:
        """Map ED3N dictionary keys to a QueryType with confidence."""
        if not keys:
            return QueryType.UNKNOWN, 0.0

        key_set = set(k.lower() for k in keys)

        # Map known keys to intent types
        intent_map = {
            QueryType.GREETING: {"你好", "hello", "hi", "早上好", "晚上好", "嗨", "hey"},
            QueryType.MATH: {"数学", "计算", "加法", "减法", "乘法", "除法", "math", "calculate"},
            QueryType.KNOWLEDGE: {"知识", "学习", "教育", "science", "knowledge", "learn"},
            QueryType.CREATIVE: {"创作", "写作", "诗歌", "故事", "creative", "write", "poem"},
            QueryType.FILE: {"檔案", "文件", "整理", "删除", "file", "organize", "delete"},
            QueryType.SEARCH: {"搜寻", "查找", "搜索", "search", "find", "google"},
            QueryType.CODE: {"程式", "代码", "函数", "code", "program", "function"},
            QueryType.VISION: {"图片", "照片", "影像", "image", "photo", "vision"},
            QueryType.AUDIO: {"语音", "音乐", "录音", "audio", "voice", "music"},
            QueryType.TASK: {"任务", "工作", "待辦", "task", "todo", "schedule"},
        }

        best_type = QueryType.UNKNOWN
        best_conf = 0.0

        for intent_type, intent_keys in intent_map.items():
            overlap = len(key_set & intent_keys)
            if overlap >= 2:
                conf = min(0.85, 0.5 + overlap * 0.1)
                if conf > best_conf:
                    best_type = intent_type
                    best_conf = conf

        return best_type, best_conf
