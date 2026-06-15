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

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Pattern, Tuple

from core.system.config.magic_numbers import limit_value


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
_CREATE_VERBS = {"建立", "新增", "创建", "新增", "建立", "create", "new", "add"}
_MODIFY_VERBS = {"修改", "编辑", "重新命名", "修改", "編輯", "重新命名", "edit", "rename", "modify", "update"}
_DELETE_VERBS = {"删除", "移除", "清空", "刪除", "移除", "清除", "delete", "remove", "clear"}
_WRITE_VERBS = {"写入", "储存", "寫入", "儲存", "write", "save"}
_READ_PREFIXES = {"搜寻", "搜索", "查询", "查看", "读取", "找", "搜尋", "搜索", "查詢", "查看", "讀取", "找", "search", "find", "lookup"}
_SEND_VERBS = {"发送", "传送", "提交", "發送", "傳送", "提交", "send", "submit", "post"}

# REFLEX 不覆盖的动词（这些是有意义的单字动词）
VERBS_NOT_REFLEX = {
    "看", "查", "开", "关", "跑", "跳", "读", "写", "听", "说",
    "吃", "喝", "搜", "删", "改", "传", "载", "买", "卖", "打",
}

# 明确知识查询模式（用于 `?` override 修正）
KNOWLEDGE_QUESTION_PATTERNS = [
    r"^什么是", r"^是什么", r"^是什麼", r"^怎麼", r"^怎么", r"^为什么", r"^為什麼", r"^為什么",
    r"^how\b", r"^what\b", r"^why\b", r"^when\b", r"^where\b", r"^who\b",
    r"^多少", r"^幾個", r"^几个", r"^谁", r"^誰", r"^今天", r"^明天", r"^昨天",
]

# 否定词
_NEGATION_WORDS = {"不要", "别", "取消", "停止", "stop", "cancel", "don't", "no"}

# 中文词边界（Python \b 不支援中文，手动加边界）
_WORD_BOUNDARY = r"(?:^|[\s，。！？,.\s])"
_WORD_BOUNDARY_END = r"(?:[\s，。！？,.\s]|$)"


class QueryClassifier:
    """Pattern-based query classifier v2 for Model Bus routing."""

    def __init__(self):
        self._reflex_words: set = {
            "hi", "ok", "okay", "hey", "yo", "oh", "ah",
            "嗯", "好", "是", "不", "啊", "哦", "喂", "嗨", "噢",
        }

        self._patterns: List[Tuple[QueryType, Pattern, float]] = [
            (
                QueryType.GREETING,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
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
                    r"(?:^|[\s，。！？,.\s])"
                    r"(\b(true|false|and|or|not|if|bool|nor|xor|neither)\b|"
                    r"if\s+then|逻辑|推理|boolean|proposition)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
            (
                QueryType.KNOWLEDGE,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
                    r"(什么是|是什么|是什麼|what\s+is|how\s+(does|do|can|to)|"
                    r"why\s+(is|does|do|can)|"
                    r"\b(define|explain)\b|"
                    r"怎麼回|怎么回|多少|how\s+many|what\s+are)",
                    re.IGNORECASE,
                ),
                0.7,
            ),
            (
                QueryType.CREATIVE,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
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
            (
                QueryType.FILE,
                re.compile(
                    r"(?:^|[\s，。！？,.\s])"
                    r"(整理|清理|删除|移动|复制|重命名|读取|写入|列出|建立|新建|修改|编辑|"
                    r"文件|文件夹|目录|路径|"
                    r"整理|清理|刪除|移動|複製|重命名|讀取|寫入|列出|建立|新建|修改|編輯|"
                    r"檔案|文件|資料夾|目錄|路徑|"
                    r"\b(organize|delete|move|copy|rename|read|write|list|create|edit|"
                    r"file|folder|directory|path)\b)",
                    re.IGNORECASE,
                ),
                0.8,
            ),
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

    def classify(self, text: str) -> QueryResult:
        """
        分类使用者输入。
        返回 QueryResult 包含 primary_type, confidence, actionability, action_type,
        secondary_type, secondary_confidence, reason
        """
        text = text.strip()
        if not text:
            return QueryResult(QueryType.UNKNOWN, 0.0, 0.0, "none", reason="empty_input")

        # Step 0: 否定词检测
        has_negation = any(neg in text for neg in _NEGATION_WORDS)

        # Step 1: 长文字启发式
        if len(text) > limit_value("ai.query_classifier.max_direct_len", 200):
            conf = 0.85
            conf = self._adjust_confidence(QueryType.KNOWLEDGE, text, conf, False, has_negation)
            action_type = self._infer_action_type(QueryType.KNOWLEDGE, text)
            return QueryResult(
                primary_type=QueryType.KNOWLEDGE,
                confidence=conf,
                actionability=self._calc_actionability(QueryType.KNOWLEDGE, text, conf),
                action_type=action_type,
                reason="long_text_heuristic"
            )

        # Step 2: 多模式匹配（收集所有匹配）
        matches = []
        for qt, pattern, base_conf in self._patterns:
            m = pattern.search(text)
            if m:
                anchored = m.start() == 0 or m.end() == len(text)
                conf = self._adjust_confidence(qt, text, base_conf, anchored, has_negation)
                act = self._calc_actionability(qt, text, conf)
                atype = self._infer_action_type(qt, text)
                matches.append((qt, conf, act, atype))

        # Step 3: ED3N 辅助分类（可选，失败不影响）
        try:
            if hasattr(self, '_ed3n') and self._ed3n:
                ed3n_type, ed3n_conf = self._ed3n_classify(text)
                if ed3n_conf > 0.5:
                    atype = self._infer_action_type(ed3n_type, text)
                    act = self._calc_actionability(ed3n_type, text, ed3n_conf)
                    matches.append((ed3n_type, ed3n_conf, act, atype))
        except Exception:
            pass  # ED3N 不可用时忽略

        # Step 4: 排序（先比 confidence，再比 actionability）
        matches.sort(key=lambda x: (x[1], x[2]), reverse=True)

        # Step 5: 选择最佳匹配
        if matches:
            primary = matches[0]
            secondary = None
            if len(matches) > 1 and matches[1][1] >= primary[1] - 0.1:
                secondary = matches[1]

            return QueryResult(
                primary_type=primary[0],
                confidence=primary[1],
                actionability=primary[2],
                action_type=primary[3],
                secondary_type=secondary[0] if secondary else None,
                secondary_confidence=secondary[1] if secondary else 0.0,
                reason="pattern_match"
            )

        # Step 6: REFLEX override（单字 + 低置信度）
        if len(text) < 2:
            if text not in VERBS_NOT_REFLEX:
                return QueryResult(
                    QueryType.REFLEX, 0.95, 0.0, "none",
                    reason="reflex_single_char_override"
                )
            # 是有意义的动词，不 override，降低置信度
            return QueryResult(
                QueryType.UNKNOWN, 0.4, 0.3, "read",
                reason="meaningful_single_char"
            )

        # Step 7: `?` override（只有明确知识查询模式）
        if text.endswith("?") or text.endswith("？"):
            if any(re.search(p, text, re.I) for p in KNOWLEDGE_QUESTION_PATTERNS):
                conf = 0.65
                conf = self._adjust_confidence(QueryType.KNOWLEDGE, text, conf, False, has_negation)
                return QueryResult(
                    QueryType.KNOWLEDGE, conf, 0.1, "none",
                    reason="knowledge_question_mark_override"
                )

        # Step 8: 回传 UNKNOWN
        return QueryResult(
            QueryType.UNKNOWN, 0.3, 0.0, "none",
            reason="no_match_fallback"
        )

    def _ed3n_classify(self, text: str) -> Tuple[QueryType, float]:
        """ED3N 辅助分类。返回 (QueryType, confidence)"""
        try:
            keys = text.lower().split()
            if len(keys) < 2:
                return QueryType.UNKNOWN, 0.0
            encoded = self._ed3n.dictionary.encode_soft(keys)
            if hasattr(encoded, 'intent') and encoded.confidence > 0.5:
                intent_map = {
                    "file": QueryType.FILE,
                    "search": QueryType.SEARCH,
                    "code": QueryType.CODE,
                    "execute": QueryType.EXECUTE,
                    "task": QueryType.TASK,
                }
                qt = intent_map.get(encoded.intent, QueryType.UNKNOWN)
                return qt, min(0.85, 0.5 + len(keys) * 0.1)
        except Exception:
            pass
        return QueryType.UNKNOWN, 0.0

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
