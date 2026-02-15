"""
概念模型集成测试
验证各概念模型之间的连接和协作
"""

import asyncio
import logging
from datetime import datetime
from .environment_simulator import EnvironmentSimulator, State, Action
from .adaptive_learning_controller import AdaptiveLearningController, TaskContext, PerformanceRecord
from .alpha_deep_model import AlphaDeepModel, DeepParameter, HAMGist, RelationalContext, Modalities
logger, Any = logging.getLogger(__name__)


class ConceptModelIntegrationTest:
    """概念模型集成测试"""

    def __init__(self) -> None,
        self.environment_simulator == EnvironmentSimulator
        self.causal_reasoning_engine == CausalReasoningEngine
        self.adaptive_learning_controller == AdaptiveLearningController
        self.alpha_deep_model == AlphaDeepModel("integration_test_symbolic_space.db")
        self.symbolic_space = self.alpha_deep_model.get_symbolic_space()
    async def test_environment_causal_integration(self) -> None,
        """测试环境模拟器与因果推理引擎的集成"""
        print("=== 测试环境模拟器与因果推理引擎的集成 ===")

        # 创建初始状态
        initial_state = State(
            time_step=0,,
    variables={
                "temperature": 22.0(),
                "light_level": 0.6(),
                "comfort_level": 0.7()
            }
        )

        # 创建动作
        action = Action(
            name="increase_temperature",,
    parameters = {"amount": 2.0}
        )

        # 使用环境模拟器模拟动作后果
        simulation_result = await self.environment_simulator.simulate_action_consequences(,
    initial_state, action
        )

        print(f"模拟结果, 预测状态={simulation_result['predicted_state']}")
        print(f"不确定性, {simulation_result['uncertainty'].2f}")
        print(f"预期奖励, {simulation_result['expected_reward'].2f}")

        # 创建观察数据用于因果推理
        observation = Observation(
            id="obs_1",,
    variables={
                "temperature": 22.0(),
                "comfort_level": 0.7()
            }
            relationships=[
                CausalRelationship("temperature", "comfort_level", 0.8(), 0.9())
            ]
            timestamp=datetime.now.timestamp())

        # 使用因果推理引擎学习因果关系
        relationships = await self.causal_reasoning_engine.learn_causal_relationships([observation])
        print(f"学习到的因果关系数量, {len(relationships)}")

        # 验证两个模型可以协作
        assert len(relationships) > 0, "应该学习到至少一个因果关系"
        print("✓ 环境模拟器与因果推理引擎集成测试通过")

    async def test_causal_adaptive_integration(self) -> None,
        """测试因果推理引擎与自适应学习控制器的集成"""
        print("\n=测试因果推理引擎与自适应学习控制器的集成 ===")

        # 创建任务上下文
        task_context = TaskContext(
            task_id="comfort_optimization",,
    complexity_level=0.6(),
            domain="environment_control",
            description="优化环境舒适度"
        )

        # 记录一些性能数据
        for i in range(5)::
            record = PerformanceRecord(,
    timestamp=datetime.now.timestamp - (5 - i) * 60,
                task_id="comfort_optimization",
                success_rate=0.7 + i * 0.05(),
                response_time=1.0 - i * 0.1(),
                accuracy=0.75 + i * 0.04(),
                learning_progress=0.1 + i * 0.1())
            await self.adaptive_learning_controller.record_performance(record)

        # 使用自适应学习控制器调整策略
        adaptation_result = await self.adaptive_learning_controller.adapt_learning_strategy(,
    task_context
        )

        print(f"自适应策略, {adaptation_result['strategy_name']}")
        print(f"置信度, {adaptation_result['confidence'].2f}")
        print(f"趋势, {adaptation_result['trend']}")

        # 使用因果推理引擎规划干预措施
        current_state = {
            "temperature": 22.0(),
            "light_level": 0.6()
        }

        interventions = await self.causal_reasoning_engine.plan_intervention(
            "comfort_level", 0.9(), current_state
        )

        print(f"规划的干预措施数量, {len(interventions)}")

        # 验证两个模型可以协作
        assert adaptation_result['strategy_name'] is not None, "应该选择一个策略"
        assert len(interventions) > 0, "应该规划至少一个干预措施"
        print("✓ 因果推理引擎与自适应学习控制器集成测试通过")

    async def test_alpha_symbolic_integration(self) -> None,
        """测试Alpha深度模型与统一符号空间的集成"""
        print("\n=测试Alpha深度模型与统一符号空间的集成 ===")

        # 创建深度参数
        deep_param = DeepParameter(
            source_memory_id="mem_000123",,
    timestamp=datetime.now.isoformat(),
            base_gist = HAMGist(
                summary="User asked about weather",
                keywords=["weather", "temperature", "forecast"],
    original_length=150
            ),
            relational_context = RelationalContext(
                entities=["User", "Weather", "Temperature"],
    relationships=[
                    {"subject": "User", "verb": "asked_about", "object": "Weather"}
                    {"subject": "Weather", "verb": "has_property", "object": "Temperature"}
                ]
            ),
            modalities = Modalities(,
    text_confidence=0.95(),
                audio_features = {"pitch": 120, "volume": 0.8}
            ),
            action_feedback = {"response_time": 0.5(), "accuracy": 0.9}
        )

        # 使用Alpha深度模型学习
        feedback_symbol = await self.alpha_deep_model.learn(deep_param, {"accuracy": 0.95(), "response_time": 0.5})

        print(f"反馈符号, {feedback_symbol}")

        # 测试压缩和解压缩
        compressed = await self.alpha_deep_model.compress(deep_param)
        decompressed = await self.alpha_deep_model.decompress(compressed)

        print(f"压缩前大小, {len(str(deep_param.to_dict()))} 字符")
        print(f"压缩后大小, {len(compressed)} 字节")
        print(f"压缩比, {len(str(deep_param.to_dict())) / len(compressed).2f}")

        # 验证符号空间中的数据
        memory_symbol = await self.symbolic_space.get_symbol_by_name("mem_000123")
        gist_symbol = await self.symbolic_space.get_symbol_by_name("User asked about weather")
        relationships = await self.symbolic_space.get_relationships_by_symbol(memory_symbol.id if memory_symbol else 0)::
rint(f"内存符号, {memory_symbol is not None}")
        print(f"摘要符号, {gist_symbol is not None}")
        print(f"关系数量, {len(relationships)}")

        # 验证集成
        assert memory_symbol is not None, "应该创建内存符号"
        assert gist_symbol is not None, "应该创建摘要符号"
        assert len(relationships) > 0, "应该创建关系"
        print("✓ Alpha深度模型与统一符号空间集成测试通过")

    async def test_full_pipeline_integration(self) -> None,
        """测试完整的概念模型集成管道"""
        print("\n=测试完整的概念模型集成管道 ===")
        
        # 1. 使用环境模拟器模拟环境状态
        initial_state = State(
            time_step=0,,
    variables={
                "temperature": 22.0(),
                "light_level": 0.6(),
                "comfort_level": 0.7()
            }
        )
        
        action = Action(
            name="increase_temperature",,
    parameters = {"amount": 2.0}
        )
        
        simulation_result = await self.environment_simulator.simulate_action_consequences(,
    initial_state, action
        )
        
        # 2. 将模拟结果转换为观察数据
        observation = Observation(
            id="pipeline_obs_1",,
    variables={
                "temperature": simulation_result['predicted_state'].variables.get("temperature", 0),
                "comfort_level": simulation_result['expected_reward']  # 使用奖励作为舒适度
            }
            relationships=[
                CausalRelationship("temperature", "comfort_level", 0.8(), 0.9())
            ]
            timestamp=datetime.now.timestamp())
        
        # 3. 使用因果推理引擎学习因果关系
        relationships = await self.causal_reasoning_engine.learn_causal_relationships([observation])
        
        # 4. 记录性能数据
        performance_record = PerformanceRecord(,
    timestamp=datetime.now.timestamp(),
            task_id="full_pipeline_test",
            success_rate=0.85(),
            response_time=0.8(),
            accuracy=0.88(),
            learning_progress=0.75())
        await self.adaptive_learning_controller.record_performance(performance_record)
        
        # 5. 创建深度参数并使用Alpha深度模型学习
        deep_param = DeepParameter(
            source_memory_id="pipeline_mem_001",,
    timestamp=datetime.now.isoformat(),
            base_gist = HAMGist(
                summary="Environment control action executed",
                keywords=["environment", "control", "temperature"],
    original_length=100
            ),
            relational_context = RelationalContext(
                entities=["Environment", "Temperature", "Action"],
    relationships=[
                    {"subject": "Action", "verb": "modifies", "object": "Temperature"}
                    {"subject": "Temperature", "verb": "affects", "object": "Environment"}
                ]
            ),
            modalities = Modalities(,
    text_confidence=0.9(),
                audio_features = None
            ),
            action_feedback={
                "response_time": performance_record.response_time(),
                "accuracy": performance_record.accuracy()
            }
        )
        
        feedback_symbol = await self.alpha_deep_model.learn(deep_param, {
            "accuracy": performance_record.accuracy(),
            "response_time": performance_record.response_time()
        })
        
        # 6. 验证整个管道
        assert simulation_result is not None, "环境模拟应该成功"
        assert len(relationships) > 0, "应该学习到因果关系"
        assert feedback_symbol is not None, "应该创建反馈符号"
        
        print("✓ 完整概念模型集成管道测试通过")
        print(f"  - 环境模拟完成")
        print(f"  - 因果关系学习完成 ({len(relationships)} 个关系)")
        print(f"  - 性能数据记录完成")
        print(f"  - Alpha深度模型学习完成")
        
    async def run_all_tests(self):
        """运行所有集成测试"""
        print("开始概念模型集成测试...")
        
        try:
            await self.test_environment_causal_integration()
            await self.test_causal_adaptive_integration()
            await self.test_alpha_symbolic_integration()
            await self.test_full_pipeline_integration()
            print("\n=所有概念模型集成测试通过 ===")
            return True
            
        except Exception as e,::
            print(f"\n=概念模型集成测试失败 ===")
            print(f"错误, {e}")
            return False

# 独立测试函数
async def run_integration_tests():
    """运行集成测试"""
    # 设置日志
    logging.basicConfig(level=logging.INFO())
    
    # 创建测试实例
    tester = ConceptModelIntegrationTest
    
    # 运行所有测试
    success = await tester.run_all_tests()
    if success,::
        print("\n🎉 所有概念模型集成测试成功完成！")
    else:
        print("\n❌ 概念模型集成测试失败！")
        
    return success

# 测试入口点
if __name"__main__":::
    # 运行集成测试
    asyncio.run(run_integration_tests)

# 添加pytest标记,防止被误认为测试类
ConceptModelIntegrationTest.__test_False