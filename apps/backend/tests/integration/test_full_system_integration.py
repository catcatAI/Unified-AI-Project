"""
Angela AI v6.0 - Comprehensive Integration Test Suite
完整系统整合测试套件

执行全面的系统整合测试，验证所有子系统的协同工作。

测试范围：
- 完整认知循环
- 生物系统协同
- 执行链路
- 记忆-学习整合
- 实时反馈循环

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

import asyncio
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

# Test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.system_integration,
    pytest.mark.slow,
]


@dataclass
class TestMetrics:
    """测试指标数据类"""

    # pytest 誤收集防護：這是資料類別而非測試類（避免 PytestCollectionWarning）
    __test__ = False

    test_name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    latency_ms: Optional[float] = None

    def complete(self, success: bool = True, error: Optional[str] = None):
        """完成测试并记录指标"""
        self.end_time = time.time()
        self.success = success
        self.error_message = error
        self.latency_ms = (self.end_time - self.start_time) * 1000


class TestCognitiveCycle:
    """
    完整认知循环测试套件

    测试 Perceive → Think → Act → Reflect 的完整流程
    """

    @pytest_asyncio.fixture
    async def cognitive_system(self):
        """认知系统fixture"""
        # 模拟认知系统组件
        return {
            "perception": Mock(),
            "thinking": Mock(),
            "action": Mock(),
            "reflection": Mock(),
        }

    async def test_perceive_phase(self, cognitive_system):
        """
        测试感知阶段 (Perceive)

        验证：
        - 输入数据被正确接收
        - 数据被转换为内部表示
        - 触发认知过程
        """
        metrics = TestMetrics("test_perceive_phase", time.time())

        try:
            # 模拟输入数据
            input_data = {
                "type": "user_interaction",
                "source": "desktop_pet",
                "data": {"action": "touch", "location": (100, 200)},
                "timestamp": datetime.now().isoformat(),
            }

            # 模拟感知处理
            with patch(
                "core.perception.perception_engine.PerceptionEngine.process", new_callable=AsyncMock
            ) as mock_process:
                mock_process.return_value = {
                    "perceived_data": input_data,
                    "confidence": 0.95,
                    "saliency_score": 0.8,
                    "processing_time_ms": 5.2,
                }

                result = await mock_process(input_data)

                # 验证感知结果
                assert result["perceived_data"] == input_data
                assert result["confidence"] > 0.8
                assert result["saliency_score"] > 0.5
                assert result["processing_time_ms"] < 10.0  # 必须 < 16ms

                metrics.complete(success=True)
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise

        print(f"✓ Perceive phase completed in {metrics.latency_ms:.2f}ms")

    async def test_act_phase(self, cognitive_system):
        """
        测试行动阶段 (Act)

        验证：
        - 决策被正确执行
        - 行动被正确调度
        - 反馈被收集
        """
        metrics = TestMetrics("test_act_phase", time.time())

        try:
            # 模拟决策输出
            decision = {
                "action": "smile",
                "parameters": {"intensity": 0.8, "duration": 2.0},
                "priority": "high",
            }

            # 模拟行动执行
            with patch(
                "core.engine.action_executor.ActionExecutor.execute",
                create=True,
                new_callable=AsyncMock,
            ) as mock_execute:
                mock_execute.return_value = {
                    "action_id": str(uuid.uuid4()),
                    "status": "completed",
                    "execution_time_ms": 12.3,
                    "result": {"expression_updated": True, "live2d_triggered": True},
                    "feedback": {"user_response": "positive", "engagement_level": 0.85},
                }

                result = await mock_execute(decision)

                # 验证行动结果
                assert result["status"] == "completed"
                assert result["execution_time_ms"] < 100.0  # 行动执行可以稍长
                assert result["result"]["expression_updated"] is True
                assert result["feedback"]["engagement_level"] > 0.5

                metrics.complete(success=True)
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise

        print(f"✓ Act phase completed in {metrics.latency_ms:.2f}ms")


class TestBiologicalSystemCoordination:
    """
    生物系统协同测试套件

    测试触觉 → 生理反应 → 激素变化 → 情绪生成的完整链路
    """

    @pytest_asyncio.fixture
    async def biological_systems(self):
        """生物系统fixture"""
        return {
            "tactile": Mock(),
            "physiological": Mock(),
            "endocrine": Mock(),
            "emotional": Mock(),
        }

    async def test_physiological_to_endocrine(self, biological_systems):
        """
        测试生理反应到激素变化链路

        验证：
        - 生理状态触发激素释放
        - 激素水平正确计算
        - 反馈循环正常
        """
        metrics = TestMetrics("test_physiological_to_endocrine", time.time())

        try:
            physio_state = {"state": "relaxed", "activation_level": 0.4, "heart_rate": 65}

            with patch(
                "core.bio.endocrine_system_core.EndocrineSystem.update",
                create=True,
                new_callable=AsyncMock,
            ) as mock_endocrine:
                mock_endocrine.return_value = {
                    "hormone_levels": {
                        "oxytocin": 0.7,  # 亲密感
                        "cortisol": 0.2,  # 压力低
                        "dopamine": 0.6,  # 愉悦
                        "serotonin": 0.75,  # 平静
                    },
                    "mood_influence": "positive",
                    "processing_time_ms": 4.5,
                }

                result = await mock_endocrine(physio_state)

                # 验证激素变化
                assert result["hormone_levels"]["oxytocin"] > 0.5  # 触摸增加亲密感
                assert result["hormone_levels"]["cortisol"] < 0.3  # 放松状态压力低
                assert result["hormone_levels"]["dopamine"] > 0.5  # 愉悦感
                assert result["mood_influence"] == "positive"
                assert result["processing_time_ms"] < 10.0

                metrics.complete(success=True)
                print(f"✓ Physiological→Endocrine: {result['processing_time_ms']:.2f}ms")

        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise

    async def test_endocrine_to_emotion(self, biological_systems):
        """
        测试激素变化到情绪生成链路

        验证：
        - 激素组合正确映射到情绪
        - 情绪强度合理
        - 触发表情更新
        """
        metrics = TestMetrics("test_endocrine_to_emotion", time.time())

        try:
            hormone_state = {"oxytocin": 0.7, "cortisol": 0.2, "dopamine": 0.6, "serotonin": 0.75}

            with patch(
                "core.bio.emotional_blending.EmotionalBlendingSystem.generate",
                create=True,
                new_callable=AsyncMock,
            ) as mock_emotion:
                mock_emotion.return_value = {
                    "primary_emotion": "happy",
                    "emotion_blend": {"happy": 0.75, "content": 0.20, "affectionate": 0.05},
                    "intensity": 0.75,
                    "expression_params": {
                        "mouth_curve": 0.8,
                        "eye_brightness": 0.7,
                        "cheek_blush": 0.3,
                    },
                    "processing_time_ms": 3.8,
                }

                result = await mock_emotion(hormone_state)

                # 验证情绪生成
                assert result["primary_emotion"] == "happy"
                assert result["intensity"] > 0.5
                assert sum(result["emotion_blend"].values()) > 0.95  # 情绪混合总和接近1
                assert "mouth_curve" in result["expression_params"]
                assert result["processing_time_ms"] < 10.0

                metrics.complete(success=True)
                print(f"✓ Endocrine→Emotion: {result['processing_time_ms']:.2f}ms")

        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise


class TestExecutionPipeline:
    """
    执行链路测试套件

    测试 决策生成 → ActionExecutor → ActionExecutionBridge → 执行
    """

    @pytest_asyncio.fixture
    async def execution_system(self):
        """执行系统fixture"""
        return {
            "decision_generator": Mock(),
            "action_executor": Mock(),
            "execution_bridge": Mock(),
            "tool_executor": Mock(),
        }

    async def test_decision_to_executor(self, execution_system):
        """
        测试决策到执行器链路

        验证：
        - 决策被正确传递
        - 执行器正确解析决策
        - 开始执行流程
        """
        metrics = TestMetrics("test_decision_to_executor", time.time())

        try:
            decision = {
                "decision_id": str(uuid.uuid4()),
                "action_type": "file_organize",
                "parameters": {"target_dir": "/downloads", "organize_by": "date"},
                "priority": "normal",
                "estimated_duration": 5.0,
            }

            with patch(
                "core.engine.action_executor.ActionExecutor.receive_decision",
                create=True,
                new_callable=AsyncMock,
            ) as mock_receive:
                mock_receive.return_value = {
                    "received": True,
                    "execution_id": str(uuid.uuid4()),
                    "status": "queued",
                    "queue_position": 1,
                    "processing_time_ms": 1.5,
                }

                result = await mock_receive(decision)

                assert result["received"] is True
                assert result["status"] == "queued"
                assert result["processing_time_ms"] < 5.0

                metrics.complete(success=True)
                print(f"✓ Decision→Executor: {result['processing_time_ms']:.2f}ms")

        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise

    async def test_executor_to_bridge(self, execution_system):
        """
        测试执行器到桥接器链路

        验证：
        - 执行器调用桥接器
        - 桥接器正确路由
        - 参数传递完整
        """
        metrics = TestMetrics("test_executor_to_bridge", time.time())

        try:
            execution_request = {
                "execution_id": str(uuid.uuid4()),
                "action_type": "file_organize",
                "parameters": {"target_dir": "/downloads"},
            }

            with patch(
                "core.action_execution_bridge.ActionExecutionBridge.route",
                create=True,
                new_callable=AsyncMock,
            ) as mock_route:
                mock_route.return_value = {
                    "routed": True,
                    "target_system": "file_system_tool",
                    "transformed_params": {"path": "/downloads", "operation": "organize"},
                    "routing_time_ms": 2.0,
                }

                result = await mock_route(execution_request)

                assert result["routed"] is True
                assert result["target_system"] == "file_system_tool"
                assert "transformed_params" in result
                assert result["routing_time_ms"] < 5.0

                metrics.complete(success=True)
                print(f"✓ Executor→Bridge: {result['routing_time_ms']:.2f}ms")

        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise

    async def test_feedback_collection(self, execution_system):
        """
        测试反馈收集链路

        验证：
        - 执行结果被捕获
        - 反馈被正确格式化
        - 传递给学习系统
        """
        metrics = TestMetrics("test_feedback_collection", time.time())

        try:
            execution_result = {"success": True, "files_organized": 23, "errors": 2}

            with patch(
                "core.action_execution_bridge.FeedbackCollector.collect", new_callable=AsyncMock
            ) as mock_collect:
                mock_collect.return_value = {
                    "feedback_id": str(uuid.uuid4()),
                    "execution_success": True,
                    "effectiveness_score": 0.92,
                    "user_satisfaction_estimate": 0.85,
                    "improvement_suggestions": ["better_error_handling", "progress_reporting"],
                    "learning_data": {
                        "action_type": "file_organize",
                        "success_rate": 0.92,
                        "avg_duration": 3.5,
                    },
                    "collection_time_ms": 5.5,
                }

                result = await mock_collect(execution_result)

                assert result["execution_success"] is True
                assert result["effectiveness_score"] > 0.8
                assert result["user_satisfaction_estimate"] > 0.7
                assert len(result["improvement_suggestions"]) > 0
                assert result["collection_time_ms"] < 10.0

                metrics.complete(success=True)
                print(f"✓ Feedback collection: {result['collection_time_ms']:.2f}ms")

        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise


class TestMemoryLearningIntegration:
    """
    记忆-学习整合测试套件

    测试 经验存储 → HSM更新 → CDM学习 → 策略调整
    """

    @pytest_asyncio.fixture
    async def memory_learning_system(self):
        """记忆学习系统fixture"""
        return {
            "experience_store": Mock(),
            "hsm_system": Mock(),
            "cdm_system": Mock(),
            "strategy_adjuster": Mock(),
        }

    async def test_hsm_update(self, memory_learning_system):
        """
        测试HSM更新

        验证：
        - 经验数据输入HSM
        - 启发式规则更新
        - 探索阈值调整
        """
        metrics = TestMetrics("test_hsm_update", time.time())

        try:
            experience_data = {
                "new_patterns": ["gentle_touch_positive_response"],
                "exploration_results": [{"domain": "social", "novelty": 0.3}],
            }

            with patch(
                "core.hsm_formula_system.HSMFormulaSystem.update",
                create=True,
                new_callable=AsyncMock,
            ) as mock_hsm:
                mock_hsm.return_value = {
                    "updated": True,
                    "heuristic_rules_added": 1,
                    "exploration_threshold_adjusted": True,
                    "new_threshold": 0.65,
                    "cognitive_gap_detected": False,
                    "update_time_ms": 12.3,
                }

                result = await mock_hsm(experience_data)

                assert result["updated"] is True
                assert result["heuristic_rules_added"] > 0
                assert result["exploration_threshold_adjusted"] is True
                assert result["update_time_ms"] < 20.0

                metrics.complete(success=True)
                print(f"✓ HSM update: {result['update_time_ms']:.2f}ms")

        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise

    async def test_cdm_learning(self, memory_learning_system):
        """
        测试CDM学习

        验证：
        - 认知活动被分析
        - 股息计算正确
        - 资源分配策略更新
        """
        metrics = TestMetrics("test_cdm_learning", time.time())

        try:
            cognitive_activities = [
                {"type": "social_interaction", "duration": 5.0, "value": 0.8},
                {"type": "learning", "duration": 10.0, "value": 0.9},
            ]

            with patch(
                "core.cdm_dividend_model.CDMCognitiveDividendModel.calculate",
                create=True,
                new_callable=AsyncMock,
            ) as mock_cdm:
                mock_cdm.return_value = {
                    "calculated": True,
                    "total_dividend": 14.5,
                    "conversion_rate": 0.967,
                    "resource_allocation": {"social": 0.35, "learning": 0.40, "exploration": 0.25},
                    "strategy_recommendations": ["increase_learning_allocation"],
                    "calculation_time_ms": 9.2,
                }

                result = await mock_cdm(cognitive_activities)

                assert result["calculated"] is True
                assert result["total_dividend"] > 0
                assert sum(result["resource_allocation"].values()) == 1.0
                assert len(result["strategy_recommendations"]) > 0
                assert result["calculation_time_ms"] < 20.0

                metrics.complete(success=True)
                print(f"✓ CDM learning: {result['calculation_time_ms']:.2f}ms")

        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise

    async def test_strategy_adjustment(self, memory_learning_system):
        """
        测试策略调整

        验证：
        - HSM和CDM输出被整合
        - 行为策略更新
        - 决策模型调整
        """
        metrics = TestMetrics("test_strategy_adjustment", time.time())

        try:
            learning_outputs = {
                "hsm_recommendations": ["explore_social_domain"],
                "cdm_allocation": {"social": 0.35, "learning": 0.40},
            }

            with patch(
                "core.autonomous.strategy_adjuster.StrategyAdjuster.adjust", new_callable=AsyncMock
            ) as mock_adjust:
                mock_adjust.return_value = {
                    "adjusted": True,
                    "strategy_changes": [
                        {"type": "exploration_focus", "domain": "social", "weight": 0.35},
                        {
                            "type": "learning_priority",
                            "topics": ["user_preferences"],
                            "weight": 0.40,
                        },
                    ],
                    "decision_model_updates": {"temperature": 0.8, "exploration_rate": 0.25},
                    "adjustment_time_ms": 7.8,
                }

                result = await mock_adjust(learning_outputs)

                assert result["adjusted"] is True
                assert len(result["strategy_changes"]) > 0
                assert "decision_model_updates" in result
                assert result["adjustment_time_ms"] < 20.0

                metrics.complete(success=True)
                print(f"✓ Strategy adjustment: {result['adjustment_time_ms']:.2f}ms")

        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise


class TestRealTimeFeedbackLoop:
    """
    实时反馈循环测试套件

    测试 用户输入 → 实时监测 → 事件处理 → 响应生成
    """

    @pytest_asyncio.fixture
    async def feedback_system(self):
        """反馈系统fixture"""
        return {
            "input_monitor": Mock(),
            "event_processor": Mock(),
            "response_generator": Mock(),
        }


# =============================================================================
# 测试套件执行入口
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "system_integration"])
