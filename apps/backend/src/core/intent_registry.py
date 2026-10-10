"""
IntentRegistry — 統一意圖檢測系統（B12）

Scoring:
  - confidence = density (keyword-char coverage / query length)
  - anti_keywords reduce confidence by 50% each (capped at 90%)
  - format_keys (optional): at least one must match to keep route
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class IntentPattern:
    name: str
    keywords: List[str] = field(default_factory=list)
    anti_keywords: List[str] = field(default_factory=list)
    format_keys: List[str] = field(default_factory=list)
    category: str = "general"
    priority: int = 5
    handler: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# Default patterns loaded when no config available
_DEFAULT_PATTERNS: List[Dict[str, Any]] = [
    {
        "name": "math",
        "keywords": [
            "計算",
            "加",
            "減",
            "乘",
            "除",
            "積分",
            "微分",
            "導數",
            "數學",
            "函數",
            "方程式",
            "math",
            "calculate",
            "solve",
            "equation",
            "plus",
            "minus",
            "times",
            "divided by",
            "=",
            "+",
            "-",
            "*",
            "/",
            "%",
        ],
        "anti_keywords": ["思路", "想法", "概念", "meaning", "concept"],
        "priority": 3,
        "handler": "MathVerifier",
        "category": "computation",
    },
    {
        "name": "code",
        "keywords": [
            "代碼",
            "程式",
            "python",
            "javascript",
            "function",
            "class",
            "import",
            "debug",
            "bug",
            "refactor",
            "重構",
            "算法",
            "測試",
            "api",
        ],
        "priority": 3,
        "handler": "CodeInspectorBridge",
        "category": "development",
    },
    {
        "name": "task",
        "keywords": [
            "幫我",
            "做一個",
            "規劃",
            "項目",
            "多步驟",
            "複雜",
            "分解",
            "子任務",
            "工作流",
            "project",
            "plan",
        ],
        "priority": 4,
        "handler": "ProjectCoordinator",
        "category": "task",
    },
    {
        "name": "file_op",
        "keywords": [
            "整理",
            "桌面",
            "移動",
            "刪除",
            "創建文件",
            "刪除文件",
            "移動文件",
            "複製",
            "重新命名",
            "建立資料夾",
            "organize",
            "桌面整理",
        ],
        "anti_keywords": ["思路", "想法", "概念", "邏輯"],
        "priority": 5,
        "handler": "FileOperationHandler",
        "category": "operation",
    },
    {
        "name": "web_search",
        "keywords": [
            "搜尋",
            "搜索",
            "查找",
            "查詢",
            "google",
            "上網查",
            "搜一下",
            "search",
            "find",
            "look up",
        ],
        "priority": 4,
        "handler": "WebSearchHandler",
        "category": "search",
    },
    {
        "name": "app_mount",
        "keywords": [
            "掛載",
            "掛上",
            "裝載",
            "卸載",
            "卸下",
            "卸载",
            "挂载",
            "有哪些應用",
            "有哪些应用",
            "可用應用",
            "可用应用",
            "mount",
            "unmount",
            "代理狀態",
            "代理健康",
            "代理正常",
            "會話狀態",
            "会话状态",
            "會話開著",
            "会话开着",
            "agent status",
            "agent health",
        ],
        "priority": 4,
        "handler": "WorkspaceMountHandler",
        "metadata": {
            "handler_id": "workspace",
            # Mounting needs an explicit mount/unmount verb or a list-apps
            # question — without this gate "上傳應用" would mount things.
            "require_keywords": [
                "掛載",
                "掛上",
                "裝載",
                "卸載",
                "卸下",
                "卸载",
                "挂载",
                "有哪些應用",
                "有哪些应用",
                "可用應用",
                "可用应用",
                "mount",
                "unmount",
                "代理狀態",
                "代理健康",
                "代理正常",
                "會話狀態",
                "会话状态",
                "會話開著",
                "会话开着",
                "agent status",
                "agent health",
            ],
        },
        "category": "app_mount",
    },
    {
        "name": "learning",
        "keywords": [
            "記住",
            "學習",
            "偏好",
            "設定",
            "记住",
            "学会",
            "教會",
            "learn",
            "remember",
            "preference",
        ],
        "priority": 4,
        "handler": "LearningHandler",
        # handler_id: the ModelBus handler id this intent dispatches to. The
        # "handler" field above is a human-readable class name and was never
        # resolvable to anything executable, which is why a user-taught fact
        # ("請記住 X") never reached LearningHandler and the model only *said*
        # it remembered. ExecutionGate resolves this id and authorizes it.
        "metadata": {
            "handler_id": "learning",
            # Storing a fact needs an explicit "remember/teach me" verb. The
            # keyword list also holds nouns (設定 / 偏好 / 學習) that describe a
            # topic, not an instruction — without this gate 「設定檔在哪」 would
            # be stored as a taught fact.
            "require_keywords": [
                "記住",
                "记住",
                "記得",
                "记得",
                "记住這",
                "请记住",
                "請記住",
                "教我",
                "教會",
                "教会",
                "學會",
                "学会",
                "幫我記",
                "帮我记",
                "remember",
                "learn",
                "teach",
                "memorize",
            ],
        },
        "category": "learning",
    },
    {
        "name": "image_generation",
        "keywords": [
            "生成圖",
            "生成图片",
            "生成一張",
            "生成一张",
            "生圖",
            "生图",
            "畫一張",
            "画一张",
            "畫一隻",
            "画一只",
            "繪圖",
            "绘图",
            "插畫",
            "插画",
            "generate an image",
            "generate image",
            "create an image",
            "make an image",
            "draw a",
            "draw me",
        ],
        # Anything the EDA / hardware agent owns is NOT an image request: the
        # vision handler used to swallow 「生成 RTL」 style asks and answered
        # 「請提供圖片路徑」.
        "anti_keywords": [
            "rtl",
            "hdl",
            "verilog",
            "systemverilog",
            "pcb",
            "電路",
            "电路",
            "晶片",
            "芯片",
            "layout",
            "佈局",
            "布局",
            "netlist",
            "gerber",
            "kicad",
            "eda",
            "硬體",
            "硬件",
            "計算卡",
            "计算卡",
        ],
        "priority": 3,
        "handler": "ImageGenerationHandler",
        "metadata": {
            "handler_id": "image_generate",
            # An explicit "make me a picture" instruction is required; a bare
            # 「圖片」 mention must not trigger generation.
            "require_keywords": [
                "生成",
                "產生",
                "生成圖",
                "生成图片",
                "生圖",
                "生图",
                "畫",
                "画",
                "繪",
                "绘",
                "做一張",
                "做一张",
                "來一張",
                "来一张",
                "generate",
                "create an image",
                "make an image",
                "draw",
            ],
        },
        "category": "image_generation",
    },
    {
        "name": "character_card",
        "keywords": [
            "角色",
            "角色卡",
            "生成角色",
            "人物",
            "人物卡",
            "創建角色",
            "character",
            "card",
            "角色創建",
        ],
        "priority": 5,
        "handler": "CardPipeline",
        "category": "card",
    },
    {
        "name": "document",
        "keywords": [
            "報告",
            "文件",
            "整理",
            "卡片堆",
            "卡片",
            "開發文件",
            "彙整",
            "整理成",
            "生成報告",
            "輸出到",
            "document",
            "report",
            "doc",
            "分析",
            "優化",
            "摘要",
            "總結",
            "分類",
            "精簡",
            "濃縮",
            "歸納",
            "歸檔",
        ],
        "anti_keywords": ["思路", "想法", "概念"],
        "format_keys": ["/", "\\", "data", "docs"],
        "priority": 3,
        "handler": "DocumentBuilder",
        "category": "document",
    },
    {
        "name": "google_drive",
        "keywords": [
            "谷歌硬碟",
            "google硬碟",
            "Google硬碟",
            "google drive",
            "Google Drive",
            "雲端硬碟",
            "雲端磁碟",
            "同步drive",
            "列出雲端",
            "搜索雲端",
        ],
        "priority": 5,
        "handler": "GoogleDriveHandler",
        "category": "integration",
    },
    {
        "name": "vision",
        "keywords": [
            "圖片",
            "影像",
            "照片",
            "圖像",
            "視覺",
            "看這張",
            "分析圖片",
            "image",
            "photo",
            "picture",
            "vision",
            "analyze image",
            "what.*image",
            "detect",
        ],
        "anti_keywords": ["想像", "幻想", " dream", "imagin"],
        "priority": 4,
        "handler": "VisionHandler",
        "category": "multimodal",
    },
    {
        "name": "audio",
        "keywords": [
            "音訊",
            "語音",
            "音頻",
            "聲音",
            "音樂",
            "歌曲",
            "錄音",
            "轉錄",
            "audio",
            "voice",
            "speech",
            "transcribe",
            "song",
            "music",
            "what.*sound",
            "listen",
        ],
        "anti_keywords": ["想像", " dream", "imagin"],
        "priority": 4,
        "handler": "AudioHandler",
        "category": "multimodal",
    },
    {
        "name": "general",
        "keywords": [],
        "priority": 9,
        "handler": "GeneralHandler",
        "category": "general",
    },
]


class IntentRegistry:
    """Unified intent detection system."""

    def __init__(self, patterns_config: Optional[List[Dict[str, Any]]] = None):
        self.patterns: List[IntentPattern] = []
        self._keyword_to_patterns: Dict[str, List[IntentPattern]] = {}
        self._initialized = False
        self._load_patterns(patterns_config)

    def _load_patterns(self, patterns_config: Optional[List[Dict[str, Any]]] = None) -> None:
        source = patterns_config if patterns_config else _DEFAULT_PATTERNS
        for item in source:
            self._add_pattern(
                IntentPattern(
                    name=item["name"],
                    keywords=item.get("keywords", []),
                    anti_keywords=item.get("anti_keywords", []),
                    format_keys=item.get("format_keys", []),
                    priority=item.get("priority", 5),
                    handler=item.get("handler", ""),
                    category=item.get("category", "general"),
                    metadata=item.get("metadata", {}),
                )
            )
        self._initialized = True

    def _add_pattern(self, pattern: IntentPattern) -> None:
        self.patterns.append(pattern)
        for kw in pattern.keywords:
            self._keyword_to_patterns.setdefault(kw, []).append(pattern)

    def _rebuild_keyword_index(self) -> None:
        self._keyword_to_patterns = {}
        for p in self.patterns:
            for kw in p.keywords:
                self._keyword_to_patterns.setdefault(kw, []).append(p)

    def register(
        self,
        pattern_or_name: Any,
        keywords: Optional[List[str]] = None,
        priority: int = 5,
        handler: str = "",
        category: str = "general",
        anti_keywords: Optional[List[str]] = None,
        format_keys: Optional[List[str]] = None,
    ) -> None:
        if isinstance(pattern_or_name, IntentPattern):
            pattern = pattern_or_name
            self.patterns.append(pattern)
            for kw in pattern.keywords:
                self._keyword_to_patterns.setdefault(kw, []).append(pattern)
        else:
            name = pattern_or_name
            existing = next((p for p in self.patterns if p.name == name), None)
            if existing:
                for kw in list(existing.keywords):
                    self._keyword_to_patterns.get(kw, []).remove(existing)
                existing.keywords = keywords or []
                existing.anti_keywords = anti_keywords or existing.anti_keywords
                existing.format_keys = format_keys or existing.format_keys
                existing.priority = priority
                existing.handler = handler
                existing.category = category
                for kw in existing.keywords:
                    self._keyword_to_patterns.setdefault(kw, []).append(existing)
            else:
                pattern = IntentPattern(
                    name=name,
                    keywords=keywords or [],
                    priority=priority,
                    handler=handler,
                    category=category,
                    anti_keywords=anti_keywords or [],
                    format_keys=format_keys or [],
                )
                self.patterns.append(pattern)
                for kw in pattern.keywords:
                    self._keyword_to_patterns.setdefault(kw, []).append(pattern)

    def unregister(self, name: str) -> bool:
        before = len(self.patterns)
        self.patterns = [p for p in self.patterns if p.name != name]
        self._rebuild_keyword_index()
        return len(self.patterns) < before

    def detect(self, query: str, category: Optional[str] = None) -> Tuple[Optional[str], float]:
        if not query:
            return None, 0.0
        best: Optional[IntentPattern] = None
        best_score = 0.0
        best_priority = 999
        for p in self.patterns:
            if category and p.category != category:
                continue

            # Positive keyword coverage
            matched_positions: set = set()
            for kw in p.keywords:
                if not kw:
                    continue
                if kw.isascii() and kw.isalpha():
                    # English: word-boundary aware
                    for m in re.finditer(
                        rf"(?<![a-zA-Z]){re.escape(kw)}(?![a-zA-Z])", query, re.IGNORECASE
                    ):
                        for i in range(m.start(), m.end()):
                            matched_positions.add(i)
                else:
                    # CJK: substring match (density check later prevents false positives)
                    idx = 0
                    while True:
                        idx = query.find(kw, idx)
                        if idx == -1:
                            break
                        for i in range(idx, idx + len(kw)):
                            matched_positions.add(i)
                        idx += 1

            if not matched_positions:
                continue

            # Density: unique keyword-char positions / query length
            query_len = max(len(query), 1)
            density = len(matched_positions) / query_len

            # Anti-keyword penalty: each anti match cuts remaining score by 50%
            anti_hits = sum(1 for akw in p.anti_keywords if akw in query)
            penalty = 1.0 - min(anti_hits * 0.5, 0.9)
            score = density * penalty

            # Format gate: if format_keys specified, at least one must match
            if p.format_keys:
                has_format = any(fk in query for fk in p.format_keys)
                if not has_format:
                    score *= 0.3  # heavy discount, not zero

            if score > best_score or (
                score == best_score and score > 0 and p.priority < best_priority
            ):
                best_score = score
                best = p
                best_priority = p.priority

        if best is None or best_score <= 0:
            return None, 0.0
        return best.name, min(best_score, 1.0)

    def detect_task_intent(self, query: str) -> Optional[str]:
        name, conf = self.detect(query)
        return name if conf > 0.3 else None

    def detect_complex_task(self, query: str) -> bool:
        name, conf = self.detect(query)
        if len(query) > 50:
            return True
        return conf > 0.5

    def detect_task_type(self, query: str) -> str:
        name, conf = self.detect(query)
        return name if name else "general"

    def get_keywords(self, name: str) -> List[str]:
        pattern = next((p for p in self.patterns if p.name == name), None)
        return list(pattern.keywords) if pattern else []

    def lookup(self, query: str) -> Optional[IntentPattern]:
        name, _ = self.detect(query)
        if name is None:
            return None
        return next((p for p in self.patterns if p.name == name), None)

    def get_pattern(self, name: str) -> Optional[IntentPattern]:
        return next((p for p in self.patterns if p.name == name), None)

    def list_patterns(self) -> List[Dict[str, Any]]:
        return [
            {"name": p.name, "keywords": p.keywords, "priority": p.priority, "handler": p.handler}
            for p in self.patterns
        ]


__all__ = ["IntentRegistry", "IntentPattern"]
