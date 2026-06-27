"""
Angela Response Composition & Matching System
==============================================
实现 P0-2 优先级：响应组合与匹配系统

核心组件：
1. TemplateMatcher - 基于哈希的模板匹配
2. ResponseComposer - 片段组合器
3. TemplateLibrary - 预计算模板库
4. DeviationTracker - 偏差追踪器
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

from .composer import (
    FragmentComposer,
    NeuroBlender,
    NeuroFragment,
    NeuroVocabulary,
    ResponseComposer,
)
from .deviation_tracker import DeviationTracker, ResponseMetrics
from .learning_loop import FragmentExtractor, LearningLoop, get_learning_loop
from .neuro_auto_selector import (
    AutoBackendChoice,
    AutoDecision,
    BudgetScheduler,
    HardwareAnalyzer,
    HardwareTier,
    LearnRecorder,
    NeuroAutoSelector,
    StateInterpreter,
)
from .template_matcher import MatchResult, TemplateMatcher

__all__ = [
    "TemplateMatcher",
    "MatchResult",
    "ResponseComposer",
    "FragmentComposer",
    "NeuroFragment",
    "NeuroVocabulary",
    "NeuroBlender",
    "DeviationTracker",
    "ResponseMetrics",
    "LearningLoop",
    "FragmentExtractor",
    "get_learning_loop",
    "NeuroAutoSelector",
    "HardwareAnalyzer",
    "BudgetScheduler",
    "StateInterpreter",
    "LearnRecorder",
    "AutoDecision",
    "AutoBackendChoice",
    "HardwareTier",
]
