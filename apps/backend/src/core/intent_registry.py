"""
IntentRegistry — 統一意圖檢測系統（B12）
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class IntentPattern:
    name: str
    keywords: List[str] = field(default_factory=list)
    category: str = "general"
    priority: int = 5
    handler: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# Default patterns loaded when no config available
_DEFAULT_PATTERNS: List[Dict[str, Any]] = [
    {"name": "math", "keywords": ["計算", "加", "減", "乘", "除", "積分", "微分", "導數", "數學", "函數", "方程式"], "priority": 3, "handler": "MathVerifier", "category": "computation"},
    {"name": "code", "keywords": ["代碼", "程式", "python", "javascript", "function", "class", "import", "debug", "bug", "refactor", "重構", "算法", "測試", "api"], "priority": 3, "handler": "CodeInspectorBridge", "category": "development"},
    {"name": "task", "keywords": ["幫我", "做一個", "規劃", "項目", "多步驟", "複雜", "分解", "子任務", "工作流", "project", "plan"], "priority": 4, "handler": "ProjectCoordinator", "category": "task"},
    {"name": "file_op", "keywords": ["整理", "桌面", "移動", "刪除", "創建文件", "刪除文件", "移動文件", "複製", "重新命名", "建立資料夾", "organize", "桌面整理"], "priority": 5, "handler": "FileOperationHandler", "category": "operation"},
    {"name": "web_search", "keywords": ["搜尋", "搜索", "查找", "查詢", "google", "上網查", "搜一下", "search", "find", "look up"], "priority": 4, "handler": "WebSearchHandler", "category": "search"},
    {"name": "learning", "keywords": ["記住", "學習", "偏好", "設定", "记住", "学会", "教會", "learn", "remember", "preference"], "priority": 4, "handler": "LearningHandler", "category": "learning"},
    {"name": "character_card", "keywords": ["角色", "角色卡", "生成角色", "人物", "人物卡", "創建角色", "character", "card", "角色創建"], "priority": 5, "handler": "CardPipeline", "category": "card"},
    {"name": "document", "keywords": ["報告", "文件", "整理", "卡片堆", "卡片", "開發文件", "彙整", "整理成", "生成報告", "輸出到", "document", "report", "doc"], "priority": 5, "handler": "DocumentBuilder", "category": "document"},
    {"name": "google_drive", "keywords": ["谷歌硬碟", "google硬碟", "Google硬碟", "google drive", "Google Drive", "雲端硬碟", "雲端磁碟", "同步drive", "列出雲端", "搜索雲端"], "priority": 5, "handler": "GoogleDriveHandler", "category": "integration"},
    {"name": "general", "keywords": [], "priority": 9, "handler": "GeneralHandler", "category": "general"},
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
            self._add_pattern(IntentPattern(
                name=item["name"],
                keywords=item.get("keywords", []),
                priority=item.get("priority", 5),
                handler=item.get("handler", ""),
                category=item.get("category", "general"),
                metadata=item.get("metadata", {}),
            ))
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

    def register(self, pattern_or_name: Any, keywords: Optional[List[str]] = None,
                 priority: int = 5, handler: str = "", category: str = "general") -> None:
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
                existing.priority = priority
                existing.handler = handler
                existing.category = category
                for kw in existing.keywords:
                    self._keyword_to_patterns.setdefault(kw, []).append(existing)
            else:
                pattern = IntentPattern(
                    name=name, keywords=keywords or [], priority=priority,
                    handler=handler, category=category,
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
        best_score = 0
        for p in self.patterns:
            if category and p.category != category:
                continue
            score = sum(1 for kw in p.keywords if kw in query)
            if score > best_score or (score == best_score and score > 0 and p.priority < getattr(best, "priority", 999)):
                best_score = score
                best = p
        if best is None or best_score == 0:
            return None, 0.0
        total_kw = max(len(best.keywords), 1)
        confidence = best_score / total_kw
        return best.name, confidence

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
