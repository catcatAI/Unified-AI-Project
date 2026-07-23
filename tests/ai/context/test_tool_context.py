import sys
from unittest.mock import MagicMock

_MODULE_MOCKS = {}
for name, mock in _MODULE_MOCKS.items():
    if name not in sys.modules:
        sys.modules[name] = mock

from datetime import datetime

import pytest

from apps.backend.src.ai.context.tool_context import (
    Tool,
    ToolCategory,
    ToolContextManager,
    ToolPerformanceMetrics,
    ToolUsageRecord,
)


class TestToolCategory:
    def test_creation_tool_category(self):
        cat = ToolCategory('cat1', 'Category 1', 'A test category')
        assert cat.category_id == 'cat1'
        assert cat.name == 'Category 1'
        assert cat.description == 'A test category'
        assert cat.parent_id is None
        assert cat.sub_categories == []
        assert cat.tools == []
        assert isinstance(cat.created_at, datetime)

    def test_creation_with_parent(self):
        parent = ToolCategory('parent', 'Parent')
        child = ToolCategory('child', 'Child', parent_id='parent')
        assert child.parent_id == 'parent'

    def test_add_sub_category(self):
        parent = ToolCategory('parent', 'Parent')
        child = ToolCategory('child', 'Child')
        parent.add_sub_category(child)
        assert child in parent.sub_categories

    def test_add_tool(self):
        cat = ToolCategory('cat1', 'Category 1')
        tool = Tool('tool1', 'Tool 1')
        cat.add_tool(tool)
        assert tool in cat.tools


class TestTool:
    def test_creation_tool(self):
        tool = Tool('tool1', 'Tool 1', 'A test tool', 'cat1')
        assert tool.tool_id == 'tool1'
        assert tool.name == 'Tool 1'
        assert tool.description == 'A test tool'
        assert tool.category_id == 'cat1'
        assert tool.usage_history == []
        assert isinstance(tool.performance_metrics, ToolPerformanceMetrics)
        assert isinstance(tool.created_at, datetime)

    def test_record_usage(self):
        tool = Tool('tool1', 'Tool 1')
        record = ToolUsageRecord({'param': 'value'}, 'result', 0.5, True)
        tool.record_usage(record)
        assert len(tool.usage_history) == 1
        assert tool.usage_history[0] is record
        assert tool.performance_metrics.total_calls == 1


class TestToolUsageRecord:
    def test_creation(self):
        params = {'input': 'test'}
        record = ToolUsageRecord(params, 'output', 1.5, True)
        assert record.parameters == params
        assert record.result == 'output'
        assert record.duration == 1.5
        assert record.success is True
        assert isinstance(record.timestamp, datetime)

    def test_failed_usage(self):
        record = ToolUsageRecord({}, None, 0.0, False)
        assert record.success is False


class TestToolPerformanceMetrics:
    def test_initial_state(self):
        metrics = ToolPerformanceMetrics()
        assert metrics.total_calls == 0
        assert metrics.success_rate == 0.0
        assert metrics.average_duration == 0.0
        assert metrics.last_used is None

    def test_update_from_successful_usage(self):
        metrics = ToolPerformanceMetrics()
        record = ToolUsageRecord({}, 'ok', 1.0, True)
        metrics.update_from_usage(record)
        assert metrics.total_calls == 1
        assert metrics.success_rate == 1.0
        assert metrics.average_duration == 1.0
        assert metrics.last_used is record.timestamp

    def test_update_from_failed_usage(self):
        metrics = ToolPerformanceMetrics()
        record = ToolUsageRecord({}, None, 2.0, False)
        metrics.update_from_usage(record)
        assert metrics.total_calls == 1
        assert metrics.success_rate == 0.0
        assert metrics.average_duration == 2.0

    def test_update_multiple_usages(self):
        metrics = ToolPerformanceMetrics()
        metrics.update_from_usage(ToolUsageRecord({}, 'ok', 1.0, True))
        metrics.update_from_usage(ToolUsageRecord({}, 'ok', 3.0, True))
        metrics.update_from_usage(ToolUsageRecord({}, None, 2.0, False))
        assert metrics.total_calls == 3
        assert metrics.success_rate == 2.0 / 3.0
        assert metrics.average_duration == (1.0 + 3.0 + 2.0) / 3.0


class TestToolContextManager:
    def test_init(self):
        mock_cm = MagicMock()
        mgr = ToolContextManager(mock_cm)
        assert mgr.context_manager is mock_cm
        assert mgr.categories == {}
        assert mgr.tools == {}

    def test_create_tool_category(self):
        mock_cm = MagicMock()
        mgr = ToolContextManager(mock_cm)
        result = mgr.create_tool_category('cat1', 'Category 1', 'desc')
        assert result is True
        assert 'cat1' in mgr.categories
        assert mgr.categories['cat1'].name == 'Category 1'

    def test_create_tool_category_with_parent(self):
        mock_cm = MagicMock()
        mgr = ToolContextManager(mock_cm)
        mgr.create_tool_category('parent', 'Parent')
        mgr.create_tool_category('child', 'Child', parent_id='parent')
        child_cat = mgr.categories['child']
        assert child_cat in mgr.categories['parent'].sub_categories

    def test_register_tool(self):
        mock_cm = MagicMock()
        mgr = ToolContextManager(mock_cm)
        result = mgr.register_tool('tool1', 'Tool 1', 'desc', 'cat1')
        assert result is True
        assert 'tool1' in mgr.tools
        assert mgr.tools['tool1'].name == 'Tool 1'

    def test_register_tool_with_category(self):
        mock_cm = MagicMock()
        mgr = ToolContextManager(mock_cm)
        mgr.create_tool_category('cat1', 'Category 1')
        mgr.register_tool('tool1', 'Tool 1', category_id='cat1')
        assert mgr.tools['tool1'] in mgr.categories['cat1'].tools

    def test_get_tool_context_not_found(self):
        mock_cm = MagicMock()
        mgr = ToolContextManager(mock_cm)
        assert mgr.get_tool_context('nonexistent') is None

    def test_record_tool_usage(self):
        mock_cm = MagicMock()
        mgr = ToolContextManager(mock_cm)
        mgr.register_tool('tool1', 'Tool 1')
        result = mgr.record_tool_usage('tool1', {'x': 1}, 'ok', 0.5, True)
        assert result is True
        tool = mgr.tools['tool1']
        assert len(tool.usage_history) == 1
        assert tool.usage_history[0].duration == 0.5
        assert tool.performance_metrics.total_calls == 1

    def test_record_tool_usage_not_found(self):
        mock_cm = MagicMock()
        mgr = ToolContextManager(mock_cm)
        result = mgr.record_tool_usage('nonexistent', {}, None, 0.0, False)
        assert result is False

    def test_get_category_tools(self):
        mock_cm = MagicMock()
        mgr = ToolContextManager(mock_cm)
        mgr.create_tool_category('cat1', 'Category 1')
        mgr.register_tool('tool1', 'Tool 1', category_id='cat1')
        mgr.register_tool('tool2', 'Tool 2', category_id='cat1')
        tools_info = mgr.get_category_tools('cat1')
        assert len(tools_info) == 2
        assert tools_info[0]['tool_id'] == 'tool1'
        assert tools_info[1]['tool_id'] == 'tool2'

    def test_get_category_tools_not_found(self):
        mock_cm = MagicMock()
        mgr = ToolContextManager(mock_cm)
        assert mgr.get_category_tools('nonexistent') == []
