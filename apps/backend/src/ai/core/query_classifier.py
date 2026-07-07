# =============================================================================
# ANGELA-MATRIX: L2-L3[记忆层/身份层] βδ [A] L2+
# =============================================================================
#
# 职责: 查询分类器 v2 — 将用户查询分类到领域，含可执行性评估
# 维度: 认知维度 (β) 用于模式匹配，精神维度 (δ) 用于意图理解
# 安全: 使用 Key A (后端控制)
# 成熟度: L2+ 等级才能完全理解查询路由逻辑
# 版本: v2.0 — 新增 QueryResult, ExecutionGate 集成
#
# =============================================================================

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Pattern, Tuple

from core.system.config.magic_numbers import limit_value

logger = logging.getLogger(__name__)


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


@dataclass
class QueryResult:
    """意图分类结果"""
    primary_type: QueryType
    confidence: float                              # 0.0-1.0
    actionability: float = 0.0                     # 0.0-1.0
    action_type: str = "none"                      # read/create/modify/delete/send/system/none
    secondary_type: Optional[QueryType] = None
    secondary_confidence: float = 0.0
    reason: str = ""


# 操作类型推断用的关键字
_CREATE_VERBS = {"建立", "新增", "创建", "新增", "建立", "創建", "create", "new", "add"}
_MODIFY_VERBS = {"修改", "编辑", "重新命名", "修改", "編輯", "重新命名", "edit", "rename", "modify", "update"}
_DELETE_VERBS = {"删除", "移除", "清空", "刪除", "移除", "清除", "delete", "remove", "clear"}
_WRITE_VERBS = {"写入", "储存", "寫入", "儲存", "write", "save"}
_READ_PREFIXES = {"搜寻", "搜索", "查询", "查看", "读取", "找", "搜尋", "搜索", "查詢", "查看", "讀取", "找", "search", "find", "lookup"}
_SEND_VERBS = {"发送", "传送", "提交", "發送", "傳送", "提交", "send", "submit", "post"}
_MOVE_VERBS = {"移动", "移至", "移到", "移動", "移至", "移到", "搬", "move", "迁移", "遷移"}

# REFLEX 不覆盖的动词（这些是有意义的单字动词）
VERBS_NOT_REFLEX = {
    "看", "查", "开", "关", "跑", "跳", "读", "写", "听", "说",
    "吃", "喝", "搜", "删", "改", "传", "载", "买", "卖", "打",
}

# 明确知识查询模式（用于 `?` override 修正）
KNOWLEDGE_QUESTION_PATTERNS = [
    r"^什么是", r"^是什么", r"^是什麼", r"^怎麼", r"^怎么", r"^为什么", r"^為什麼", r"^為什么",
    r"^how\b", r"^what\b", r"^why\b", r"^when\b", r"^where\b", r"^who\b",
    r"^多少", r"^幾個", r"^几个", r"^谁", r"^誰", r"^今天", r"^明天", r"^明日", r"^昨天",
    r"天氣", r"天気", r"weather", r"温度", r"temperature", r"氣溫",
    r"記得", r"記憶", r"remember", r"recall", r"記住",
]

# 否定词
_NEGATION_WORDS = {"不要", "别", "取消", "停止", "stop", "cancel", "don't", "no"}

# 中文词边界（Python \b 不支援中文，手动加边界）
_WORD_BOUNDARY = r"(?:^|[\s，。！？,.\s])"
_WORD_BOUNDARY_END = r"(?:[\s，。！？,.\s]|$)"


class QueryClassifier:
    """Pattern-based query classifier v2 for Model Bus routing."""

    def __init__(self, ed3n_engine=None):
        self._ed3n = ed3n_engine
        self._reflex_words = self._build_reflex_words()
        self._patterns = self._build_patterns()

    @staticmethod
    def _build_reflex_words() -> set:
        return {
            "hi", "ok", "okay", "hey", "yo", "oh", "ah",
            "嗯", "好", "是", "不", "啊", "哦", "喂", "嗨", "噢",
            "喵", "咪", "咕", "呜",
        }

    @staticmethod
    def _build_greeting_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.GREETING,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
                    r"(你好|早安|早上好|上午好|中午好|下午好|午安|晚上好|晚安|"
                    r"再见|拜拜|谢谢|感谢|"
                    r"\b(hello|hi|hey|good\s*morning|good\s*afternoon|good\s*evening|good\s*bye|thanks?|bye)\b)",
                    re.IGNORECASE,
                ),
                0.9,
            ),
            (
                QueryType.GREETING,
                re.compile(
                    r"(自我介紹|自我介绍|介紹自己|介绍自己|"
                    r"你是誰|你是谁|你叫什麼|你叫什么|你的名字|"
                    r"做個?自我|做一?個?自我|來一?個?自我|来一?个?自我|"
                    r"\b(introduce\s+yourself|who\s+are\s+you|what's\s+your\s+name)\b)",
                    re.IGNORECASE,
                ),
                0.85,
            ),
        ]

    @staticmethod
    def _build_math_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.MATH,
                re.compile(
                    r"(\d+\s*[\+\-\*\/]\s*\d+|"
                    r"(?:三|四|五|六|七|八|九|十|百|千|万)\s*(?:加|减|乘|除)\s*(?:三|四|五|六|七|八|九|十|百|千|万)|"
                    r"等于|等于多少|計算|计算|加法|减法|乘法|除法|"
                    r"\b(plus|minus|times|divided\s*by|calculate|solve|equation)\b)",
                    re.IGNORECASE,
                ),
                0.85,
            ),
        ]

    @staticmethod
    def _build_logic_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.LOGIC,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
                    r"(\b(true|false|and|or|not|if|bool|nor|xor|neither)\b|"
                    r"if\s+then|逻辑|推理|boolean|proposition)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
        ]

    @staticmethod
    def _build_knowledge_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.KNOWLEDGE,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
                    r"(什么是|是什么|是什麼|what\s+is|how\s+(does|do|can|to)|"
                    r"why\s+(is|does|do|can)|"
                    r"\b(define|explain)\b|"
                    r"怎麼回|怎么回|多少|how\s+many|what\s+are)|"
                    r"(能做|可以做|可以幫|能幫|可以帮|能幫我|可以幫我|"
                    r"你的能力|你的功能|你會什麼|你会什么|你能做|你可以做|"
                    r"介紹你的|介绍你的|能做什麼|能做什么|可以做什么|可以做什麼|"
                    r"能做啥|能幹嘛|能幹什麼|能干什么|可以幹嘛|可以干什么)",
                    re.IGNORECASE,
                ),
                0.7,
            ),
        ]

    @staticmethod
    def _build_creative_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.CREATIVE,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
                    r"(写|寫|作|创作|創作|编|編|画|畫|虚构|虛構|"
                    r"\b(write|poem|story|song|joke|"
                    r"imagine|pretend|creat|make\s+up|compose)\b|"
                    r"想象|想像|如果|假设|假設|绘|繪)",
                    re.IGNORECASE,
                ),
                0.75,
            ),
            (
                QueryType.CREATIVE,
                re.compile(
                    r"(主角|配角|角色|故事|小说|小說|剧情|劇情|"
                    r"詩|诗|散文|歌词|劇本|剧本|創作|创作|虚构|虛構)",
                    re.IGNORECASE,
                ),
                0.7,
            ),
        ]

    @staticmethod
    def _build_opinion_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.OPINION,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
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
        ]

    @staticmethod
    def _build_file_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.FILE,
                re.compile(
                    r"(?:^|[\s，。！？,.\s/])"
                    r"(整理|清理|删除|移动|移至|移到|复制|重命名|读取|写入|列出|建立|新建|修改|编辑|"
                    r"文件|文件夹|目录|路径|"
                    r"整理|清理|刪除|移動|移至|移到|複製|重命名|讀取|寫入|列出|建立|新建|修改|編輯|"
                    r"檔案|文件|資料夾|目錄|路徑|"
                    r"幫我删除|幫我刪除|幫我建立|幫我新建|幫我讀取|幫我寫入|"
                    r"帮我删除|帮我删除|帮我建立|帮我新建|帮我读取|帮我写入|"
                    r"\b(organize|delete|move|copy|rename|read|write|list|create|edit|"
                    r"file|folder|directory|path)\b)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
            # Supplementary: file op words without boundary (dense Chinese text, paths)
            (
                QueryType.FILE,
                re.compile(
                    r"(移至|移到|移動|移动|搬移|遷移|迁移|"
                    r"複製|复制|重新命名|重命名|刪除|删除|"
                    r"document|file|folder|directory)",
                    re.IGNORECASE,
                ),
                0.65,
            ),
        ]

    @staticmethod
    def _build_search_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.SEARCH,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
                    r"(搜寻|搜索|查找|找|查询|搜|"
                    r"搜尋|搜索|查找|找|查詢|搜|"
                    r"\b(search|find|look\s*for|google|query|lookup)\b)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
        ]

    @staticmethod
    def _build_code_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.CODE,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
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
        ]

    @staticmethod
    def _build_execute_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.EXECUTE,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
                    r"(执行|运行|开启|关闭|启动|停止|暂停|"
                    r"執行|運行|開啟|關閉|啟動|停止|暫停|"
                    r"\b(execute|run|open|close|start|stop|launch|kill)\b)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
        ]

    @staticmethod
    def _build_task_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.TASK,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
                    r"(任务|工作|待办|行程|排程|提醒|建立任务|删除任务|"
                    r"任務|工作|待辦|行程|排程|提醒|建立任務|刪除任務|"
                    r"\b(task|todo|schedule|reminder|plan|planned)\b)",
                    re.IGNORECASE,
                ),
                0.75,
            ),
        ]

    @staticmethod
    def _build_vision_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.VISION,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
                    r"(图片|照片|影像|截图|识别|看|"
                    r"圖片|照片|影像|截圖|辨識|看|"
                    r"\b(image|photo|picture|screenshot|recognize|see|vision)\b)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
        ]

    @staticmethod
    def _build_audio_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
            (
                QueryType.AUDIO,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
                    r"(语音|音频|录音|音乐|播放|听|"
                    r"語音|音訊|錄音|音樂|播放|聽|"
                    r"\b(audio|voice|speech|music|play|listen)\b)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
        ]

    @staticmethod
    def _build_command_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        return [
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

    @staticmethod
    def _build_patterns() -> List[Tuple[QueryType, Pattern, float]]:
        builders = [
            QueryClassifier._build_greeting_patterns,
            QueryClassifier._build_math_patterns,
            QueryClassifier._build_logic_patterns,
            QueryClassifier._build_knowledge_patterns,
            QueryClassifier._build_creative_patterns,
            QueryClassifier._build_opinion_patterns,
            QueryClassifier._build_file_patterns,
            QueryClassifier._build_search_patterns,
            QueryClassifier._build_code_patterns,
            QueryClassifier._build_execute_patterns,
            QueryClassifier._build_task_patterns,
            QueryClassifier._build_vision_patterns,
            QueryClassifier._build_audio_patterns,
            QueryClassifier._build_command_patterns,
        ]
        result: List[Tuple[QueryType, Pattern, float]] = []
        for b in builders:
            result.extend(b())
        return result

    def classify(self, text: str) -> QueryResult:
        """
        分类使用者输入。
        返回 QueryResult 包含 primary_type, confidence, actionability, action_type,
        secondary_type, secondary_confidence, reason
        """
        text = text.strip()
        if not text:
            return QueryResult(QueryType.UNKNOWN, 0.0, 0.0, "none", reason="empty_input")

        has_negation = any(neg in text for neg in _NEGATION_WORDS)

        # Step 1: 长文字启发式
        result = self._classify_by_length(text, has_negation)
        if result is not None:
            return result

        # Step 2: ED3N Dictionary classification (primary path)
        result = self._classify_by_dictionary(text, has_negation)
        if result is not None:
            return result

        # Steps 3-5: Regex pattern matching (fallback)
        result = self._classify_by_regex(text, has_negation)
        if result is not None:
            return result

        # Step 6: REFLEX override（单字 + 低置信度）
        result = self._classify_reflex_override(text)
        if result is not None:
            return result

        # Step 7: `?` override（只有明确知识查询模式）
        result = self._classify_question_override(text, has_negation)
        if result is not None:
            return result

        # Step 8: 回传 UNKNOWN
        return QueryResult(QueryType.UNKNOWN, 0.3, 0.0, "none", reason="no_match_fallback")

    def _classify_by_length(self, text: str, has_negation: bool) -> Optional[QueryResult]:
        if len(text) > limit_value("ai.query_classifier.max_direct_len", 200):
            conf = self._adjust_confidence(QueryType.KNOWLEDGE, text, 0.85, False, has_negation)
            return QueryResult(
                primary_type=QueryType.KNOWLEDGE, confidence=conf,
                actionability=self._calc_actionability(QueryType.KNOWLEDGE, text, conf),
                action_type=self._infer_action_type(QueryType.KNOWLEDGE, text),
                reason="long_text_heuristic",
            )
        return None

    def _classify_by_dictionary(self, text: str, has_negation: bool) -> Optional[QueryResult]:
        try:
            from ai.core.dictionary_classifier import get_dictionary_classifier
            dc = get_dictionary_classifier()
            dict_type, dict_action, dict_conf = dc.classify(text)
            if dict_conf >= 0.3 and dict_type != "unknown":
                qt = QueryType(dict_type)
                conf = self._adjust_confidence(qt, text, dict_conf, False, has_negation)
                return QueryResult(
                    primary_type=qt, confidence=conf,
                    actionability=self._calc_actionability(qt, text, conf),
                    action_type=dict_action, reason="dictionary_match",
                )
        except Exception as e:
            logger.debug(f"Dictionary lookup failed: {e}")
        return None

    def _classify_by_regex(self, text: str, has_negation: bool) -> Optional[QueryResult]:
        matches = []
        for qt, pattern, base_conf in self._patterns:
            m = pattern.search(text)
            if m:
                anchored = m.start() == 0 or m.end() == len(text)
                conf = self._adjust_confidence(qt, text, base_conf, anchored, has_negation)
                matches.append((qt, conf, self._calc_actionability(qt, text, conf),
                                self._infer_action_type(qt, text)))
        matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        if matches:
            primary = matches[0]
            secondary = matches[1] if len(matches) > 1 \
                and matches[1][1] >= primary[1] - 0.1 else None
            return QueryResult(
                primary_type=primary[0], confidence=primary[1],
                actionability=primary[2], action_type=primary[3],
                secondary_type=secondary[0] if secondary else None,
                secondary_confidence=secondary[1] if secondary else 0.0,
                reason="regex_pattern_match",
            )
        return None

    def _classify_reflex_override(self, text: str) -> Optional[QueryResult]:
        if len(text) < 2:
            if text not in VERBS_NOT_REFLEX:
                return QueryResult(QueryType.REFLEX, 0.95, 0.0, "none",
                                   reason="reflex_single_char_override")
            return QueryResult(QueryType.UNKNOWN, 0.4, 0.3, "read", reason="meaningful_single_char")
        # Multi-char reflex: all chars are reflex words (cat sounds, nods, etc.)
        if len(text) <= 10 and all(c in self._reflex_words for c in text):
            return QueryResult(QueryType.REFLEX, 0.9, 0.0, "none",
                               reason="reflex_all_chars_override")
        return None

    def _classify_question_override(self, text: str, has_negation: bool) -> Optional[QueryResult]:
        if text.endswith("?") or text.endswith("？"):
            if any(re.search(p, text, re.I) for p in KNOWLEDGE_QUESTION_PATTERNS):
                conf = self._adjust_confidence(QueryType.KNOWLEDGE, text, 0.65, False, has_negation)
                return QueryResult(QueryType.KNOWLEDGE, conf, 0.1, "none",
                                   reason="knowledge_question_mark_override")
            # Broad fallback: any remaining ?-ending text→KNOWLEDGE at lower confidence
            conf = self._adjust_confidence(QueryType.KNOWLEDGE, text, 0.45, False, has_negation)
            return QueryResult(QueryType.KNOWLEDGE, conf, 0.1, "none",
                               reason="knowledge_question_mark_fallback")
        return None

    def _adjust_confidence(self, query_type: QueryType, text: str,
                           base_conf: float, anchored: bool, has_negation: bool) -> float:
        """动态调整置信度"""
        conf = base_conf

        # 锚定匹配更可靠
        if anchored:
            conf += 0.05

        # 关键字密度
        words = text.split()
        if len(words) > 0:
            matching_keywords = sum(1 for w in words if len(w) >= 2)
            density = matching_keywords / len(words)
            if density > 0.5:
                conf += 0.05
            elif density < 0.2:
                conf -= 0.10

        # 输入长度
        if len(text) < 5:
            conf -= 0.05
        elif len(text) > 50:
            conf += 0.03

        # 否定词
        if has_negation:
            conf -= 0.15

        return max(0.1, min(0.95, conf))

    def _calc_actionability(self, query_type: QueryType, text: str, confidence: float) -> float:
        """计算可执行性分数"""
        type_base = {
            QueryType.EXECUTE: 0.9, QueryType.FILE: 0.85, QueryType.SEARCH: 0.8,
            QueryType.CODE: 0.75, QueryType.TASK: 0.7, QueryType.VISION: 0.6,
            QueryType.AUDIO: 0.6, QueryType.COMMAND: 0.5,
            QueryType.KNOWLEDGE: 0.1, QueryType.OPINION: 0.1, QueryType.CREATIVE: 0.1,
            QueryType.GREETING: 0.0, QueryType.REFLEX: 0.0, QueryType.UNKNOWN: 0.0,
            QueryType.MATH: 0.1, QueryType.LOGIC: 0.1,
        }.get(query_type, 0.3)

        # 明确动作动词 → 提高
        all_action_verbs = (
            list(_CREATE_VERBS) + list(_MODIFY_VERBS) + list(_DELETE_VERBS) +
            list(_SEND_VERBS) + list(_READ_PREFIXES) + list(_WRITE_VERBS)
        )
        if any(v in text for v in all_action_verbs):
            type_base = min(1.0, type_base + 0.1)

        # 模糊词 → 降低
        vague_words = ["一下", "看看", "处理", "弄", "搞", "整", "试试"]
        if any(w in text for w in vague_words):
            type_base = max(0.0, type_base - 0.2)

        # 否定词 → 大幅降低
        if any(neg in text for neg in _NEGATION_WORDS):
            type_base = max(0.0, type_base - 0.5)

        return type_base

    def _infer_action_type(self, query_type: QueryType, text: str) -> str:
        """根据意图和文字推断操作类型"""
        # 无操作类
        if query_type in (QueryType.GREETING, QueryType.REFLEX, QueryType.OPINION,
                          QueryType.CREATIVE, QueryType.KNOWLEDGE, QueryType.MATH,
                          QueryType.LOGIC):
            return "none"

        # 读取类
        if query_type in (QueryType.SEARCH, QueryType.VISION, QueryType.AUDIO):
            if any(w in text for w in _WRITE_VERBS):
                return "modify"
            return "read"

        # FILE 类：根据动词判断
        if query_type == QueryType.FILE:
            if any(w in text for w in _DELETE_VERBS):
                return "delete"
            if any(w in text for w in _CREATE_VERBS):
                return "create"
            if any(w in text for w in _MOVE_VERBS):
                return "modify"
            if any(w in text for w in _MODIFY_VERBS):
                return "modify"
            return "read"

        # CODE/EXECUTE → system
        if query_type in (QueryType.CODE, QueryType.EXECUTE):
            return "system"

        # TASK → create or delete
        if query_type == QueryType.TASK:
            if any(w in text for w in _DELETE_VERBS):
                return "delete"
            return "create"

        # COMMAND → 根据内容判断
        if query_type == QueryType.COMMAND:
            if any(w in text for w in _DELETE_VERBS):
                return "delete"
            if any(w in text for w in _CREATE_VERBS):
                return "create"
            if any(w in text for w in _MODIFY_VERBS):
                return "modify"
            return "read"

        return "none"

    def _keys_to_intent(self, keys: List[str]) -> Tuple[QueryType, float]:
        """Map ED3N dictionary keys to a QueryType with confidence."""
        if not keys:
            return QueryType.UNKNOWN, 0.0

        key_set = set(k.lower() for k in keys)

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
