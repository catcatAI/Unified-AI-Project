"""
IntentRegistry — 統一意圖檢測系統（B12）
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable
import re

logger = logging.getLogger(__name__)


@dataclass
class IntentPattern:
    """單一意圖模式定義"""
    name: str
    keywords: List[str]
    category: str
    priority: int = 0
    flags: int = re.IGNORECASE


@dataclass
class IntentRegistry:
    """
    統一意圖檢測 registry。

    用法：
        registry = IntentRegistry()
        intent = registry.detect("生成一個角色卡")
        # → "task" with confidence=0.8

    擴展：
        registry.register(IntentPattern(
            name="creative_writing",
            keywords=["寫", "創作", "故事"],
            category="task",
            priority=5,
        ))
    """
    patterns: List[IntentPattern] = field(default_factory=list)
    _keyword_to_patterns: Dict[str, List[Tuple[int, IntentPattern]]] = field(default_factory=dict)
    _initialized: bool = field(default=False, repr=False)

    def __post_init__(self) -> None:
        if not self._initialized:
            self._register_defaults()
            self._build_index()
            self._initialized = True

    def _register_defaults(self) -> None:
        try:
            from core.config_loader import get_angela_config
            cfg = get_angela_config()
            core = cfg.get_authority("angela_core", {})
            intents_cfg = core.get("intents", {})
            self.patterns = []
            for name, cfg_item in intents_cfg.items():
                keywords = cfg_item.get("keywords", [])
                category = cfg_item.get("handler", "general")
                priority = cfg_item.get("priority", 1)
                self.patterns.append(
                    IntentPattern(name, keywords, category, priority)
                )
        except Exception:
            logger.warning("Failed to load intents from config, using hardcoded defaults", exc_info=True)
            self._register_defaults_hardcoded()

    def _register_defaults_hardcoded(self) -> None:
        """Fallback: hardcoded defaults (向後兼容)"""
        self.patterns = [
            IntentPattern("task", ["生成", "建立", "創建", "整理", "彙整", "搜尋", "研究", "規劃", "策劃"], "task", priority=5),
            IntentPattern("math", ["計算", "加", "減", "乘", "除", "等於", "+", "-", "×", "÷"], "math", priority=6),
            IntentPattern("code", ["代碼", "code", "python", "函數", "function"], "code", priority=6),
            IntentPattern("llm_switch", ["[ollama:", "[openai:", "[anthropic:", "[模型"], "llm_switch", priority=7),
            IntentPattern("complex", ["生成", "建立", "創建", "整理", "彙整", "搜尋", "研究", "規劃", "角色", "文件", "報告"], "task", priority=4),
            IntentPattern("character_card", ["角色", "角色卡", "生成角色", "人物", "人物卡"], "character_card", priority=6),
            IntentPattern("document", ["報告", "文件", "整理", "彙整"], "document", priority=5),
            IntentPattern("research", ["搜尋", "查找", "研究", "找資料"], "research", priority=5),
            IntentPattern("plan", ["規劃", "策劃", "設計", "project"], "plan", priority=5),
            IntentPattern("general", [], "general", priority=0),
        ]

    def _build_index(self) -> None:
        self._keyword_to_patterns.clear()
        for pattern in self.patterns:
            if not pattern.keywords:
                continue
            for kw in pattern.keywords:
                kw_lower = kw.lower()
                if kw_lower not in self._keyword_to_patterns:
                    self._keyword_to_patterns[kw_lower] = []
                self._keyword_to_patterns[kw_lower].append((pattern.priority, pattern))

    def register(self, pattern: IntentPattern) -> None:
        """動態註冊新的意圖模式"""
        self.patterns.append(pattern)
        for kw in pattern.keywords:
            kw_lower = kw.lower()
            if kw_lower not in self._keyword_to_patterns:
                self._keyword_to_patterns[kw_lower] = []
            self._keyword_to_patterns[kw_lower].append((pattern.priority, pattern))

    def detect(self, text: str, category: Optional[str] = None) -> Tuple[Optional[str], float]:
        """
        檢測文字中的意圖。

        Returns:
            Tuple of (intent_name, confidence)
            confidence = matched_keywords / total_keywords_for_intent
        """
        text_lower = text.lower()
        matched: Dict[str, Tuple[int, Set[str]]] = {}

        for kw, pattern_list in self._keyword_to_patterns.items():
            if kw in text_lower:
                for _, pattern in pattern_list:
                    if category and pattern.category != category:
                        continue
                    if pattern.name not in matched:
                        matched[pattern.name] = (0, set())
                    matched[pattern.name] = (
                        matched[pattern.name][0] + 1,
                        matched[pattern.name][1] | {kw}
                    )

        if not matched:
            return (None, 0.0)

        best_name = max(matched, key=lambda n: matched[n][0])
        best_priority = next(
            p.priority for p in self.patterns if p.name == best_name
        )
        best_match_count = matched[best_name][0]
        confidence = min(1.0, best_match_count * 0.3 + best_priority * 0.1)
        return (best_name, confidence)

    def detect_category(self, text: str, category: str) -> Tuple[Optional[str], float]:
        """檢測特定 category 內的意圖"""
        return self.detect(text, category=category)

    def get_keywords(self, intent_name: str) -> List[str]:
        """獲取指定意圖的所有關鍵字"""
        for p in self.patterns:
            if p.name == intent_name:
                return p.keywords
        return []

    def detect_task_intent(self, text: str) -> Optional[str]:
        """ChatService._detect_task_intent 兼容介面"""
        intent, conf = self.detect(text, category="task")
        return intent if conf >= 0.3 else None

    def detect_complex_task(self, text: str) -> bool:
        """ProjectCoordinator._detect_complex_task 兼容介面"""
        intent, _ = self.detect(text, category="task")
        return intent is not None or len(text) > 50

    def detect_task_type(self, text: str) -> str:
        """DocumentBuilder._detect_task_type 兼容介面 — 僅匹配 task-type patterns"""
        text_lower = text.lower()
        for ttype in ("character_card", "document", "research", "plan"):
            pattern = next((p for p in self.patterns if p.name == ttype), None)
            if pattern and any(kw in text_lower for kw in pattern.keywords):
                return ttype
        return "general"