"""
Test Template Matcher
=====================
Unit tests for P0-2 template matching system
"""

import pytest
import time
from apps.backend.src.ai.response.template_matcher import (
    TemplateMatcher,
    MatchResult,
    MatchLevel,
    Template,
)


@pytest.fixture
def matcher():
    """创建测试用的模板匹配器"""
    m = TemplateMatcher()

    m.add_template(
        template_id="greeting_1",
        content="你好呀！见到你真开心~",
        patterns=["你好"],
        keywords=["你好", "嗨", "hi", "hello"],
    )

    m.add_template(
        template_id="farewell_1",
        content="拜拜！下次见啦~",
        patterns=["拜拜"],
        keywords=["拜拜", "再见", "bye"],
    )

    m.add_template(
        template_id="thanks_1",
        content="不客气！能帮到你我很开心~",
        patterns=["谢谢"],
        keywords=["谢谢", "感谢", "谢了"],
    )

    return m


def test_exact_match(matcher):
    """测试精确匹配"""
    result = matcher.match("你好呀！见到你真开心~")

    assert result.score == 1.0
    assert result.level == MatchLevel.EXACT
    assert result.template_id == "greeting_1"
    assert result.match_time_ms < 5.0


def test_semantic_match(matcher):
    """测试语义匹配"""
    result = matcher.match("你好呀见到你真开心")

    assert result.score > 0.7
    assert result.level == MatchLevel.SEMANTIC
    assert result.template_id == "greeting_1"


def test_fuzzy_match(matcher):
    """测试模糊匹配"""
    result = matcher.match("你好朋友")

    assert result.score > 0.5
    assert result.level == MatchLevel.FUZZY
    assert "greeting_1" in result.template_id


def test_no_match(matcher):
    """测试无匹配"""
    result = matcher.match("量子力学的薛丁格方程式")

    assert result.score == 0.0
    assert result.level == MatchLevel.NO_MATCH


def test_performance(matcher):
    """测试性能 - 匹配速度 < 5ms"""
    start = time.time()

    for i in range(100):
        result = matcher.match("你好")

    elapsed = (time.time() - start) * 1000
    avg_time = elapsed / 100

    assert avg_time < 5.0, f"Average match time {avg_time:.2f}ms exceeds 5ms target"


def test_keyword_extraction():
    """测试关键词提取"""
    matcher = TemplateMatcher()
    keywords = matcher._extract_keywords("你好，我想知道这个问题的答案")

    assert "好" in keywords
    assert "想" in keywords
    assert "知" in keywords
    assert "问" in keywords
    assert "题" in keywords
    assert "答" in keywords
    assert "案" in keywords


def test_template_usage_tracking(matcher):
    """测试模板使用追踪"""
    result = matcher.match("你好")

    matcher.record_template_usage(result.template_id, True)

    template = matcher.templates.get(result.template_id)
    assert template.usage_count == 1
    assert template.success_rate > 0.9

    matcher.record_template_usage(result.template_id, False)
    assert template.usage_count == 2
    assert template.success_rate < 1.0


def test_multiple_templates_ranking(matcher):
    """测试多个模板的排序"""
    matcher.add_template(
        template_id="greeting_2",
        content="嗨！",
        patterns=["嗨"],
        keywords=["你好", "嗨", "hi"],
    )

    result = matcher.match("你好")

    assert result.score > 0.5
    assert result.template_id in ["greeting_1", "greeting_2"]


def test_stats():
    """测试统计信息"""
    matcher = TemplateMatcher()

    matcher.add_template(
        template_id="test_1",
        content="测试",
        patterns=["测试"],
        keywords=["测试"],
    )

    matcher.match("测试")
    matcher.match("测试内容")
    matcher.match("其他内容")

    stats = matcher.get_stats()

    assert stats["total_matches"] == 3
    assert stats["exact_matches"] >= 1
    assert stats["average_match_time"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
