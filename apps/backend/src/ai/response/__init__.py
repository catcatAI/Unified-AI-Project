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

from .template_matcher import TemplateMatcher, MatchResult
from .composer import (
    ResponseComposer,
    FragmentComposer,
    NeuroFragment,
    NeuroVocabulary,
    NeuroBlender,
)
from .deviation_tracker import DeviationTracker, ResponseMetrics
from .learning_loop import LearningLoop, FragmentExtractor, get_learning_loop
from .neuro_auto_selector import (
    NeuroAutoSelector,
    HardwareAnalyzer,
    BudgetScheduler,
    StateInterpreter,
    LearnRecorder,
    AutoDecision,
    AutoBackendChoice,
    HardwareTier,
)

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
