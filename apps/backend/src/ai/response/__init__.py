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

from .template_matcher import TemplateMatcher, MatchResult
from .composer import ResponseComposer, FragmentComposer
from .deviation_tracker import DeviationTracker, ResponseMetrics

__all__ = [
    "TemplateMatcher",
    "MatchResult",
    "ResponseComposer",
    "FragmentComposer",
    "DeviationTracker",
    "ResponseMetrics",
]
