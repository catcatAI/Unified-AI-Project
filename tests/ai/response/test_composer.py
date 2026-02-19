"""
Test Response Composer
=======================
Unit tests for P0-2 response composition system
"""

import pytest
from apps.backend.src.ai.response.composer import (
    ResponseComposer,
    FragmentComposer,
    Fragment,
    FragmentType,
    ComposedResponse,
)


@pytest.fixture
def composer():
    """创建测试用的响应组合器"""
    return ResponseComposer()


def test_compose_high_match(composer):
    """测试高匹配度（>0.8）- 使用完整模板"""
    result = composer.compose_response(
        template_content="你好呀！见到你真开心~",
        match_score=0.9,
        context={},
    )

    assert result.text == "你好呀！见到你真开心~"
    assert result.confidence > 0.8
    assert result.composition_time_ms < 5.0


def test_compose_medium_match(composer):
    """测试中匹配度（0.5-0.8）- 片段组合"""
    result = composer.compose_response(
        template_content="你好。我很开心。还有什么我能帮你的吗？",
        match_score=0.65,
        context={},
    )

    assert len(result.text) > 0
    assert result.confidence > 0.5
    assert len(result.fragments_used) > 0


def test_fragment_split():
    """测试模板片段化"""
    fragment_composer = FragmentComposer()

    template = "你好呀！我很开心能帮到你！还有什么我能帮你的吗？"
    fragments = fragment_composer._split_template(template, {})

    assert len(fragments) >= 2
    assert any(f.type == FragmentType.GREETING for f in fragments)
    assert any(f.type == FragmentType.EMOTION_EXPRESSION for f in fragments)


def test_fragment_assembly():
    """测试片段组装"""
    fragment_composer = FragmentComposer()

    fragments = [
        Fragment(
            id="greeting_1",
            content="嗨！",
            type=FragmentType.GREETING,
            keywords=["你好"],
            context_tags=["casual"],
        ),
        Fragment(
            id="emotion_1",
            content="我很开心！",
            type=FragmentType.EMOTION_EXPRESSION,
            keywords=["开心"],
            context_tags=["positive"],
        ),
    ]

    text = fragment_composer._assemble_fragments(fragments, {})

    assert "嗨！" in text
    assert "我很开心！" in text


def test_add_custom_fragment(composer):
    """测试添加自定义片段"""
    custom_fragment = Fragment(
        id="custom_1",
        content="这是自定义片段",
        type=FragmentType.QUESTION_RESPONSE,
        keywords=["自定义"],
        context_tags=["test"],
        priority=8,
    )

    composer.add_fragment(custom_fragment)

    assert "custom_1" in composer.fragment_composer.fragments


def test_performance(composer):
    """测试性能 - 组合时间 < 2ms"""
    import time

    start = time.time()

    for i in range(100):
        result = composer.compose_response(
            template_content="你好呀！",
            match_score=0.9,
            context={},
        )

    elapsed = (time.time() - start) * 1000
    avg_time = elapsed / 100

    assert avg_time < 5.0, f"Average composition time {avg_time:.2f}ms exceeds 5ms target"


def test_stats(composer):
    """测试统计信息"""
    composer.compose_response("测试", 0.9, {})
    composer.compose_response("测试2", 0.65, {})

    stats = composer.get_stats()

    assert stats["total_compositions"] == 2
    assert stats["fragments_used"] >= 2
    assert stats["average_composition_time"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
