"""
IntentRegistry — 統一意圖檢測系統（B12）
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class IntentPattern:
    name: str
    keywords: List[str] = field(default_factory=list)
    priority: int = 5
    handler: str = ""
    category: str = "general"
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
    {"name": "document", "keywords": ["報告", "文件", "整理", "彙整", "整理成", "生成報告", "document", "report", "doc"], "priority": 5, "handler": "DocumentBuilder", "category": "document"},
    {"name": "google_drive", "keywords": ["谷歌硬碟", "google硬碟", "Google硬碟", "google drive", "Google Drive", "雲端硬碟", "雲端磁碟", "同步drive", "列出雲端", "搜索雲端"], "priority": 5, "handler": "GoogleDriveHandler", "category": "integration"},
    {"name": "general", "keywords": [], "priority": 9, "handler": "GeneralHandler", "category": "general"},
]


class IntentRegistry:
    """Unified intent detection system."""

    def __init__(self, patterns_config: Optional[List[Dict[str, Any]]] = None):
        self.patterns: List[IntentPattern] = []
        self._load_patterns(patterns_config)

    def _load_patterns(self, patterns_config: Optional[List[Dict[str, Any]]] = None) -> None:
        source = patterns_config if patterns_config else _DEFAULT_PATTERNS
        for item in source:
            self.patterns.append(IntentPattern(
                name=item["name"],
                keywords=item.get("keywords", []),
                priority=item.get("priority", 5),
                handler=item.get("handler", ""),
                category=item.get("category", "general"),
                metadata=item.get("metadata", {}),
            ))

    def register(self, name: str, keywords: List[str], priority: int = 5, handler: str = "", category: str = "general") -> None:
        existing = next((p for p in self.patterns if p.name == name), None)
        if existing:
            existing.keywords = keywords
            existing.priority = priority
            existing.handler = handler
            existing.category = category
        else:
            self.patterns.append(IntentPattern(
                name=name, keywords=keywords, priority=priority,
                handler=handler, category=category,
            ))

    def unregister(self, name: str) -> bool:
        before = len(self.patterns)
        self.patterns = [p for p in self.patterns if p.name != name]
        return len(self.patterns) < before

    def lookup(self, query: str) -> Optional[IntentPattern]:
        best: Optional[IntentPattern] = None
        best_score = 0
        for p in self.patterns:
            score = sum(1 for kw in p.keywords if kw in query)
            if score > best_score or (score == best_score and p.priority < getattr(best, "priority", 999)):
                best_score = score
                best = p
        return best if best_score > 0 else None

    def detect_complex_task(self, query: str) -> bool:
        return bool(self.lookup(query))

    def detect_task_type(self, query: str) -> str:
        match = self.lookup(query)
        return match.name if match else "general"

    def get_pattern(self, name: str) -> Optional[IntentPattern]:
        return next((p for p in self.patterns if p.name == name), None)

    def list_patterns(self) -> List[Dict[str, Any]]:
        return [
            {"name": p.name, "keywords": p.keywords, "priority": p.priority, "handler": p.handler}
            for p in self.patterns
        ]


__all__ = ["IntentRegistry", "IntentPattern"]
