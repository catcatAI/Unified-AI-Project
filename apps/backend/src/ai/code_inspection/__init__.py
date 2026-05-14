"""
Angela Code Inspection Module
代碼檢查系統 - 原生實現，0 LLM 依賴

子模組：
  - code_inspector: AST + 模式匹配檢查器
  - knowledge_graph: 代碼結構知識圖譜
  - code_learning: 從人類反饋中學習

Author: Angela AI Development Team
Version: 6.2.1
"""

from ai.code_inspection.code_inspector import (
    CodeInspector,
    CodeFixer,
    ProjectInspector,
    ASTInspector,
    PatternMatcher,
    Issue,
    IssueCategory,
    Severity,
    InspectorReport,
    CodeFunction,
    CodeClass,
    ModuleInfo,
)

from ai.code_inspection.knowledge_graph import (
    KnowledgeGraph,
    GraphQueryEngine,
    GraphNode,
    GraphEdge,
)

from ai.code_inspection.code_learning import (
    CodeLearningEngine,
    LearnedPattern,
    LearningFeedback,
    CodeInspectorInterface,
    create_inspector,
)

__all__ = [
    "CodeInspector",
    "CodeFixer",
    "ProjectInspector",
    "ASTInspector",
    "PatternMatcher",
    "Issue",
    "IssueCategory",
    "Severity",
    "InspectorReport",
    "CodeFunction",
    "CodeClass",
    "ModuleInfo",
    "KnowledgeGraph",
    "GraphQueryEngine",
    "GraphNode",
    "GraphEdge",
    "CodeLearningEngine",
    "LearnedPattern",
    "LearningFeedback",
    "CodeInspectorInterface",
    "create_inspector",
]