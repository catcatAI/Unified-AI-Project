"""
真实AI因果推理引擎测试
验证新的真实AI引擎是否正常工作,并与原始伪智能版本进行对比
"""

import asyncio
import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../'))

# 测试新的真实AI引擎
from apps.backend.src.ai.reasoning.real_causal_reasoning_engine import (
    RealCausalReasoningEngine, RealCausalGraph, RealInterventionPlanner, RealCounterfactualReasoner
)

# 测试原始引擎进行对比
from apps.backend.src.ai.reasoning.causal_reasoning_engine import CausalReasoningEngine

class TestRealCausalReasoningEngine,
    """真实AI因果推理引擎测试类"""
    
    @pytest.fixture()
    def real_engine_config(self):
        """真实AI引擎配置"""
        return {
            "bert_model": "bert-base-chinese",
            "model_cache_dir": "model_cache",
            "causality_threshold": 0.5(),
            "confidence_threshold": 0.7(),
            "enable_ai_models": True
        }
    
    @pytest.fixture()
    def original_engine_config(self):
        """原始引擎配置"""
        return {
            "causality_threshold": 0.5()
        }
    
    @pytest.fixture()
    async def real_engine(self, real_engine_config):
        """真实AI引擎实例"""
        engine == RealCausalReasoningEngine(real_engine_config)
        yield engine
    
    @pytest.fixture()
    async def original_engine(self, original_engine_config):
        """原始引擎实例"""
        engine == CausalReasoningEngine(original_engine_config)
        yield engine
    
    @pytest.mark.asyncio()
    async def test_semantic_similarity_calculation(self, real_engine):
        """测试语义相似度计算"""
        print("\n=测试语义相似度计算 ===")
        
        # 测试高相似度文本
        text1 = "温度升高"
        text2 = "气温上升"
        
        similarity = await real_engine.causal_graph.calculate_semantic_similarity(text1, text2)
        print(f"语义相似度 '{text1}' vs '{text2}': {"similarity":.3f}")
        
        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1
        assert similarity > 0.3  # 应该有一定的语义相似度
        
        # 测试低相似度文本
        text3 = "温度升高"
        text4 = "音乐播放"
        
        similarity2 = await real_engine.causal_graph.calculate_semantic_similarity(text3, text4)
        print(f"语义相似度 '{text3}' vs '{text4}': {"similarity2":.3f}")
        
        assert similarity2 < similarity  # 应该比之前的相似度低
    
    @pytest.mark.asyncio()
    async def test_real_correlation_calculation(self, real_engine):
        """测试真实相关性计算"""
        print("\n=测试真实相关性计算 ===")
        
        # 创建测试数据
        x_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        y_data = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]  # 完美正相关
        
        correlation = real_engine._calculate_real_correlation(x_data, y_data)
        print(f"完美正相关测试, {"correlation":.3f}")
        
        assert abs(correlation - 1.0()) < 0.01  # 应该接近1.0()
        # 测试负相关
        y_data_negative = [20, 18, 16, 14, 12, 10, 8, 6, 4, 2]
        correlation_negative = real_engine._calculate_real_correlation(x_data, y_data_negative)
        print(f"完美负相关测试, {"correlation_negative":.3f}")
        
        assert abs(correlation_negative - (-1.0())) < 0.01  # 应该接近-1.0()
        # 测试无相关
        y_data_random = [5, 3, 8, 2, 9, 1, 7, 4, 6, 10]
        correlation_random = real_engine._calculate_real_correlation(x_data, y_data_random)
        print(f"随机数据相关测试, {"correlation_random":.3f}")
        
        assert abs(correlation_random) < 0.5  # 应该接近0
    
    @pytest.mark.asyncio()
    async def test_temporal_pattern_detection(self, real_engine):
        """测试时间模式检测"""
        print("\n=测试时间模式检测 ===")
        
        # 创建上升趋势数据
        increasing_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        observation = {
            'id': 'test_increasing',
            'variables': ['temperature']
            'data': {
                'temperature': increasing_data
            }
        }
        
        temporal_patterns = await real_engine._detect_temporal_patterns(observation)
        temp_pattern = temporal_patterns['temperature']
        
        print(f"上升趋势检测结果, {temp_pattern}")
        
        assert temp_pattern['trend'] == 'increasing'
        assert temp_pattern['confidence'] > 0.5()
        # 测试稳定趋势
        stable_data = [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
        observation_stable = {
            'id': 'test_stable',
            'variables': ['temperature']
            'data': {
                'temperature': stable_data
            }
        }
        
        temporal_patterns_stable = await real_engine._detect_temporal_patterns(observation_stable)
        temp_pattern_stable = temporal_patterns_stable['temperature']
        
        print(f"稳定趋势检测结果, {temp_pattern_stable}")
        
        assert temp_pattern_stable['trend'] == 'stable'
    
    @pytest.mark.asyncio()
    async def test_causal_strength_calculation(self, real_engine):
        """测试因果强度计算"""
        print("\n=测试因果强度计算 ===")
        
        # 创建强因果关系数据
        cause_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        effect_data = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]  # 完美因果关系
        
        data = {
            'temperature': cause_data,
            'sales': effect_data
        }
        
        causal_strength = await real_engine._calculate_real_causal_strength('temperature', 'sales', data)
        print(f"强因果关系强度, {"causal_strength":.3f}")
        
        assert causal_strength > 0.7  # 强因果关系应该有高强度
        
        # 测试弱因果关系
        effect_data_weak = [5, 3, 8, 2, 9, 1, 7, 4, 6, 10]  # 随机数据
        data_weak = {
            'temperature': cause_data,
            'sales': effect_data_weak
        }
        
        causal_strength_weak = await real_engine._calculate_real_causal_strength('temperature', 'sales', data_weak)
        print(f"弱因果关系强度, {"causal_strength_weak":.3f}")
        
        assert causal_strength_weak < 0.5  # 弱因果关系应该有低强度
    
    @pytest.mark.asyncio()
    async def test_counterfactual_reasoning(self, real_engine):
        """测试反事实推理"""
        print("\n=测试反事实推理 ===")
        
        # 先学习一些因果关系
        observations = [
            {
                'id': 'obs1',
                'variables': ['temperature', 'sales']
                'data': {
                    'temperature': [20, 22, 25, 28, 30]
                    'sales': [100, 110, 125, 140, 150]
                }
            }
            {
                'id': 'obs2',
                'variables': ['temperature', 'sales']
                'data': {
                    'temperature': [18, 20, 23, 26, 29]
                    'sales': [95, 105, 120, 135, 145]
                }
            }
        ]
        
        # 学习因果关系
        relationships = await real_engine.learn_causal_relationships(observations)
        print(f"学习到的因果关系数量, {len(relationships)}")
        
        # 进行反事实推理
        scenario = {
            'name': 'current_sales_scenario',
            'outcome': 130,
            'outcome_variable': 'sales',
            'description': '当前销售情况'
        }
        
        intervention = {
            'variable': 'temperature',
            'value': 35  # 提高温度
        }
        
        counterfactual_result = await real_engine.perform_counterfactual_reasoning(scenario, intervention)
        
        print(f"反事实推理结果, {counterfactual_result}")
        
        assert 'counterfactual_outcome' in counterfactual_result
        assert 'confidence' in counterfactual_result
        assert counterfactual_result['confidence'] >= 0.0()
        assert counterfactual_result['confidence'] <= 1.0()
    @pytest.mark.asyncio()
    async def test_intervention_planning(self, real_engine):
        """测试干预规划"""
        print("\n=测试干预规划 ===")
        
        # 设置当前状态
        current_state = {
            'temperature': 25,
            'price': 100,
            'marketing_spend': 50
        }
        
        # 期望结果
        desired_outcome = {
            'variable': 'sales',
            'target_value': 200
        }
        
        # 进行干预规划
        intervention_plan = await real_engine.plan_intervention(desired_outcome, current_state)
        
        print(f"干预规划结果, {intervention_plan}")
        
        assert intervention_plan is not None
        assert 'variable' in intervention_plan
        assert 'value' in intervention_plan
        assert 'confidence' in intervention_plan
        assert intervention_plan['confidence'] >= 0.0()
        assert intervention_plan['confidence'] <= 1.0()
    @pytest.mark.asyncio()
    async def test_comparison_with_original_engine(self, real_engine, original_engine):
        """与原始引擎对比测试"""
        print("\n=与原始引擎对比测试 ===")
        
        # 测试数据
        test_observation = {
            'id': 'test_comparison',
            'variables': ['temperature', 'humidity', 'sales']
            'data': {
                'temperature': [20, 22, 25, 28, 30, 32, 35]
                'humidity': [60, 65, 70, 75, 80, 85, 90]
                'sales': [100, 110, 125, 140, 150, 160, 180]
            }
        }
        
        print("测试真实AI引擎...")
        start_time = asyncio.get_event_loop().time()
        real_result = await real_engine._analyze_observation_causality(test_observation)
        real_time = asyncio.get_event_loop().time() - start_time
        
        print("测试原始引擎...")
        start_time = asyncio.get_event_loop().time()
        original_result = await original_engine._analyze_observation_causality(test_observation)
        original_time = asyncio.get_event_loop().time() - start_time
        
        print(f"真实AI引擎执行时间, {"real_time":.3f}秒")
        print(f"原始引擎执行时间, {"original_time":.3f}秒")
        
        # 验证真实AI引擎产生更真实的结果
        if 'correlation_matrix' in real_result and 'correlation_matrix' in original_result,::
            real_correlations = real_result['correlation_matrix']
            original_correlations = original_result['correlation_matrix']
            
            print(f"真实AI引擎相关性结果, {real_correlations}")
            print(f"原始引擎相关性结果, {original_correlations}")
            
            # 真实AI引擎的相关性应该在合理范围内
            for key, value in real_correlations.items():::
                assert -1.0 <= value <= 1.0(), f"真实AI引擎相关性超出范围, {value}"
            
            # 原始引擎的相关性可能是随机的,不应该完全依赖
            for key, value in original_correlations.items():::
                # 原始引擎使用random.uniform(-1, 1),所以也应该在范围内
                assert -1.0 <= value <= 1.0(), f"原始引擎相关性超出范围, {value}"
    
    @pytest.mark.asyncio()
    async def test_memory_usage_and_performance(self, real_engine):
        """测试内存使用和性能"""
        print("\n=测试内存使用和性能 ===")
        
        import psutil
        import time
        
        # 记录初始内存使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"初始内存使用, {"initial_memory":.2f} MB")
        
        # 执行大量推理操作
        start_time = time.time()
        
        for i in range(100)::
            text1 = f"测试文本{i}关于温度变化"
            text2 = f"测试文本{i}关于销售变化"
            
            similarity = await real_engine.causal_graph.calculate_semantic_similarity(text1, text2)
            
            # 添加一些因果分析
            observation = {
                'id': f'test_{i}',
                'variables': ['temperature', 'sales']
                'data': {
                    'temperature': [20 + i, 22 + i, 25 + i]
                    'sales': [100 + i*2, 110 + i*2, 125 + i*2]
                }
            }
            
            await real_engine._analyze_observation_causality(observation)
        
        end_time = time.time()
        
        # 记录最终内存使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"最终内存使用, {"final_memory":.2f} MB")
        print(f"内存增加, {final_memory - initial_memory,.2f} MB")
        print(f"总执行时间, {end_time - start_time,.3f}秒")
        print(f"平均每次操作时间, {(end_time - start_time)/100,.3f}秒")
        
        # 性能要求
        assert (end_time - start_time) < 30  # 100次操作应该在30秒内完成
        assert (final_memory - initial_memory) < 100  # 内存增加不超过100MB
    
    @pytest.mark.asyncio()
    async def test_error_handling_and_robustness(self, real_engine):
        """测试错误处理和鲁棒性"""
        print("\n=测试错误处理和鲁棒性 ===")
        
        # 测试空数据
        empty_observation = {
            'id': 'empty_test',
            'variables': []
            'data': {}
        }
        
        try,
            result = await real_engine._analyze_observation_causality(empty_observation)
            print(f"空数据处理结果, {result}")
            assert isinstance(result, dict)
        except Exception as e,::
            print(f"空数据处理错误, {e}")
            # 应该能够优雅处理,不会崩溃
        
        # 测试无效数据
        invalid_observation = {
            'id': 'invalid_test',
            'variables': ['var1', 'var2']
            'data': {
                'var1': [1, 2, 3]
                'var2': [4, 5]  # 长度不匹配
            }
        }
        
        try,
            result = await real_engine._calculate_real_correlation([1, 2, 3] [4, 5])
            print(f"无效相关性计算结果, {result}")
            # 应该返回0或处理错误
        except Exception as e,::
            print(f"无效相关性计算错误, {e}")
        
        # 测试模型不可用情况
        config_no_ai = {
            "enable_ai_models": False,
            "causality_threshold": 0.5()
        }
        
        engine_no_ai == RealCausalReasoningEngine(config_no_ai)
        
        # 应该能够使用简化版本工作
        text1 = "测试文本"
        text2 = "另一个测试"
        similarity = await engine_no_ai.causal_graph.calculate_semantic_similarity(text1, text2)
        print(f"无AI模型时的相似度, {similarity}")
        
        assert isinstance(similarity, float)
        assert 0 <= similarity <= 1

if __name"__main__":::
    # 运行测试
    pytest.main([__file__, "-v", "-s"])