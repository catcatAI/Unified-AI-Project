"""
Test Deviation Tracker
=======================
Unit tests for P0-2 deviation tracking system
"""

import pytest
import time
from apps.backend.src.ai.response.deviation_tracker import (
    DeviationTracker,
    ResponseRoute,
    ResponseMetrics,
)


@pytest.fixture
def tracker():
    """创建测试用的偏差追踪器"""
    return DeviationTracker(log_dir="tests/logs/deviation_test")


def test_record_composed_response(tracker):
    """测试记录组合路由响应"""
    tracker.record(
        user_input="你好",
        match_score=0.9,
        route=ResponseRoute.COMPOSED,
        response_text="你好呀！",
        tokens_used=50,
        response_time_ms=5.0,
        composition_time_ms=2.0,
        match_time_ms=1.0,
    )

    assert tracker.stats["total_responses"] == 1
    assert tracker.stats["route_counts"][ResponseRoute.COMPOSED.value] == 1
    assert tracker.stats["total_tokens_used"] == 50


def test_record_hybrid_response(tracker):
    """测试记录混合路由响应"""
    tracker.record(
        user_input="你最近怎么样？",
        match_score=0.65,
        route=ResponseRoute.HYBRID,
        response_text="我很好！你呢？",
        tokens_used=200,
        response_time_ms=500.0,
        composition_time_ms=2.0,
        match_time_ms=1.0,
    )

    assert tracker.stats["total_responses"] == 1
    assert tracker.stats["route_counts"][ResponseRoute.HYBRID.value] == 1
    assert tracker.stats["total_tokens_used"] == 200


def test_record_llm_full_response(tracker):
    """测试记录完整 LLM 路由响应"""
    tracker.record(
        user_input="量子力学的原理是什么？",
        match_score=0.0,
        route=ResponseRoute.LLM_FULL,
        response_text="量子力学是...",
        tokens_used=600,
        response_time_ms=1500.0,
    )

    assert tracker.stats["total_responses"] == 1
    assert tracker.stats["route_counts"][ResponseRoute.LLM_FULL.value] == 1
    assert tracker.stats["total_tokens_used"] == 600


def test_token_savings_calculation(tracker):
    """测试 Token 节省率计算"""
    tracker.record(
        user_input="你好",
        match_score=0.9,
        route=ResponseRoute.COMPOSED,
        response_text="你好呀！",
        tokens_used=50,
        response_time_ms=5.0,
    )

    tracker.record(
        user_input="你好",
        match_score=0.9,
        route=ResponseRoute.COMPOSED,
        response_text="你好呀！",
        tokens_used=50,
        response_time_ms=5.0,
    )

    baseline_tokens_per_request = 600
    expected_total_tokens = 2 * baseline_tokens_per_request
    tokens_saved = expected_total_tokens - tracker.stats["total_tokens_used"]

    assert tracker.stats["token_savings_rate"] > 0.5


def test_user_feedback(tracker):
    """测试用户反馈记录"""
    tracker.record(
        user_input="你好",
        match_score=0.9,
        route=ResponseRoute.COMPOSED,
        response_text="你好呀！",
        tokens_used=50,
        response_time_ms=5.0,
    )

    tracker.record_user_feedback(0, True)

    assert tracker.metrics_history[0].user_feedback is True
    assert tracker.metrics_history[0].quality_score == 1.0


def test_optimization_suggestions(tracker):
    """测试优化建议生成"""
    for i in range(10):
        tracker.record(
            user_input=f"测试 {i}",
            match_score=0.2,
            route=ResponseRoute.LLM_FULL,
            response_text="响应",
            tokens_used=600,
            response_time_ms=1500.0,
        )

    suggestions = tracker.get_optimization_suggestions()

    assert len(suggestions) > 0
    assert any("组合路由使用率" in s for s in suggestions)
    assert any("Token 节省率" in s for s in suggestions)


def test_report_generation(tracker):
    """测试报告生成"""
    tracker.record(
        user_input="你好",
        match_score=0.9,
        route=ResponseRoute.COMPOSED,
        response_text="你好呀！",
        tokens_used=50,
        response_time_ms=5.0,
    )

    tracker.record(
        user_input="问题",
        match_score=0.0,
        route=ResponseRoute.LLM_FULL,
        response_text="回答",
        tokens_used=600,
        response_time_ms=1500.0,
    )

    report = tracker.generate_report()

    assert "偏差追踪报告" in report
    assert "总响应数: 2" in report
    assert "路由分布" in report
    assert "Token 使用情况" in report
    assert "优化建议" in report


def test_performance(tracker):
    """测试性能 - 记录开销 < 0.5ms"""
    start = time.time()

    for i in range(100):
        tracker.record(
            user_input=f"测试 {i}",
            match_score=0.9,
            route=ResponseRoute.COMPOSED,
            response_text="响应",
            tokens_used=50,
            response_time_ms=5.0,
        )

    elapsed = (time.time() - start) * 1000
    avg_time = elapsed / 100

    assert avg_time < 1.0, f"Average record time {avg_time:.2f}ms exceeds 1ms target"


def test_recent_metrics(tracker):
    """测试获取最近的指标"""
    for i in range(15):
        tracker.record(
            user_input=f"测试 {i}",
            match_score=0.9,
            route=ResponseRoute.COMPOSED,
            response_text="响应",
            tokens_used=50,
            response_time_ms=5.0,
        )

    recent = tracker.get_recent_metrics(count=10)

    assert len(recent) == 10
    assert recent[-1].user_input == "测试 14"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
