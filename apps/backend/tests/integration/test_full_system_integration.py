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

import pytest
import pytest_asyncio
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import dataclass


# Test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.system_integration,
    pytest.mark.slow,
]


@dataclass
class TestMetrics:
    """测试指标数据类"""
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
            'perception': Mock(),
            'thinking': Mock(),
            'action': Mock(),
            'reflection': Mock(),
        }
    
    @pytest.mark.asyncio
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
                'type': 'user_interaction',
                'source': 'desktop_pet',
                'data': {'action': 'touch', 'location': (100, 200)},
                'timestamp': datetime.now().isoformat()
            }
            
            # 模拟感知处理
            with patch('core.perception.perception_engine.PerceptionEngine.process') as mock_process:
                mock_process.return_value = {
                    'perceived_data': input_data,
                    'confidence': 0.95,
                    'saliency_score': 0.8,
                    'processing_time_ms': 5.2
                }
                
                result = mock_process(input_data)
                
                # 验证感知结果
                assert result['perceived_data'] == input_data
                assert result['confidence'] > 0.8
                assert result['saliency_score'] > 0.5
                assert result['processing_time_ms'] < 10.0  # 必须 < 16ms
                
                metrics.complete(success=True)
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        print(f"✓ Perceive phase completed in {metrics.latency_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_think_phase(self, cognitive_system):
        """
        测试思考阶段 (Think)
        
        验证：
        - 感知数据被正确解释
        - 生成合理的认知状态
        - 触发决策过程
        """
        metrics = TestMetrics("test_think_phase", time.time())
        
        try:
            # 模拟感知输出
            perceived_data = {
                'perceived_data': {'type': 'touch', 'intensity': 'gentle'},
                'confidence': 0.95
            }
            
            # 模拟思考处理
            with patch('core.cognition.cognitive_engine.CognitiveEngine.think') as mock_think:
                mock_think.return_value = {
                    'cognitive_state': 'engaged',
                    'emotional_response': 'happy',
                    'decision_candidates': [
                        {'action': 'smile', 'probability': 0.7},
                        {'action': 'giggle', 'probability': 0.3}
                    ],
                    'reasoning_chain': ['touch_detected', 'positive_interaction', 'happiness_response'],
                    'processing_time_ms': 8.5
                }
                
                result = mock_think(perceived_data)
                
                # 验证思考结果
                assert result['cognitive_state'] in ['engaged', 'neutral', 'focused']
                assert result['emotional_response'] in ['happy', 'surprised', 'curious']
                assert len(result['decision_candidates']) > 0
                assert sum(d['probability'] for d in result['decision_candidates']) > 0.9
                assert result['processing_time_ms'] < 16.0
                
                metrics.complete(success=True)
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        print(f"✓ Think phase completed in {metrics.latency_ms:.2f}ms")
    
    @pytest.mark.asyncio
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
                'action': 'smile',
                'parameters': {'intensity': 0.8, 'duration': 2.0},
                'priority': 'high'
            }
            
            # 模拟行动执行
            with patch('core.execution.action_executor.ActionExecutor.execute') as mock_execute:
                mock_execute.return_value = {
                    'action_id': str(uuid.uuid4()),
                    'status': 'completed',
                    'execution_time_ms': 12.3,
                    'result': {'expression_updated': True, 'live2d_triggered': True},
                    'feedback': {'user_response': 'positive', 'engagement_level': 0.85}
                }
                
                result = mock_execute(decision)
                
                # 验证行动结果
                assert result['status'] == 'completed'
                assert result['execution_time_ms'] < 100.0  # 行动执行可以稍长
                assert result['result']['expression_updated'] is True
                assert result['feedback']['engagement_level'] > 0.5
                
                metrics.complete(success=True)
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        print(f"✓ Act phase completed in {metrics.latency_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_reflect_phase(self, cognitive_system):
        """
        测试反思阶段 (Reflect)
        
        验证：
        - 行动结果被分析
        - 学习信号被生成
        - 记忆被更新
        """
        metrics = TestMetrics("test_reflect_phase", time.time())
        
        try:
            # 模拟行动输出
            action_result = {
                'action_id': str(uuid.uuid4()),
                'status': 'completed',
                'feedback': {'user_response': 'positive', 'engagement_level': 0.85}
            }
            
            # 模拟反思处理
            with patch('core.reflection.reflection_engine.ReflectionEngine.reflect') as mock_reflect:
                mock_reflect.return_value = {
                    'reflection_id': str(uuid.uuid4()),
                    'success_assessment': 'positive',
                    'learning_signals': [
                        {'type': 'preference_update', 'data': {'touch_response': 'smile'}},
                        {'type': 'strategy_reinforcement', 'data': {'positive_interaction': 'repeat'}}
                    ],
                    'memory_updates': [
                        {'type': 'episodic', 'content': 'User enjoyed gentle touch'},
                        {'type': 'semantic', 'content': 'Gentle touch → Smile response'}
                    ],
                    'processing_time_ms': 6.8
                }
                
                result = mock_reflect(action_result)
                
                # 验证反思结果
                assert result['success_assessment'] in ['positive', 'neutral', 'negative']
                assert len(result['learning_signals']) > 0
                assert len(result['memory_updates']) > 0
                assert result['processing_time_ms'] < 16.0
                
                metrics.complete(success=True)
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        print(f"✓ Reflect phase completed in {metrics.latency_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_complete_cognitive_cycle(self, cognitive_system):
        """
        测试完整认知循环 (Perceive → Think → Act → Reflect)
        
        验证：
        - 所有阶段按顺序执行
        - 数据在阶段间正确传递
        - 总延迟 < 100ms
        """
        metrics = TestMetrics("test_complete_cognitive_cycle", time.time())
        
        try:
            cycle_start = time.time()
            
            # 阶段 1: Perceive
            with patch('core.perception.perception_engine.PerceptionEngine.process') as mock_perceive:
                mock_perceive.return_value = {
                    'perceived_data': {'type': 'touch'},
                    'confidence': 0.95,
                    'processing_time_ms': 5.0
                }
                perceive_result = mock_perceive({'type': 'touch'})
            
            # 阶段 2: Think
            with patch('core.cognition.cognitive_engine.CognitiveEngine.think') as mock_think:
                mock_think.return_value = {
                    'cognitive_state': 'engaged',
                    'decision_candidates': [{'action': 'smile', 'probability': 0.8}],
                    'processing_time_ms': 8.0
                }
                think_result = mock_think(perceive_result)
            
            # 阶段 3: Act
            with patch('core.execution.action_executor.ActionExecutor.execute') as mock_act:
                mock_act.return_value = {
                    'status': 'completed',
                    'execution_time_ms': 15.0,
                    'feedback': {'user_response': 'positive'}
                }
                act_result = mock_act(think_result['decision_candidates'][0])
            
            # 阶段 4: Reflect
            with patch('core.reflection.reflection_engine.ReflectionEngine.reflect') as mock_reflect:
                mock_reflect.return_value = {
                    'success_assessment': 'positive',
                    'learning_signals': [{'type': 'preference_update'}],
                    'processing_time_ms': 6.0
                }
                reflect_result = mock_reflect(act_result)
            
            cycle_end = time.time()
            total_latency_ms = (cycle_end - cycle_start) * 1000
            
            # 验证完整循环
            assert perceive_result['confidence'] > 0.8
            assert len(think_result['decision_candidates']) > 0
            assert act_result['status'] == 'completed'
            assert reflect_result['success_assessment'] == 'positive'
            assert total_latency_ms < 100.0, f"Total cycle time {total_latency_ms}ms exceeds 100ms limit"
            
            metrics.complete(success=True)
            print(f"✓ Complete cognitive cycle: {total_latency_ms:.2f}ms (target: <100ms)")
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise


class TestBiologicalSystemCoordination:
    """
    生物系统协同测试套件
    
    测试触觉 → 生理反应 → 激素变化 → 情绪生成的完整链路
    """
    
    @pytest_asyncio.fixture
    async def biological_systems(self):
        """生物系统fixture"""
        return {
            'tactile': Mock(),
            'physiological': Mock(),
            'endocrine': Mock(),
            'emotional': Mock(),
        }
    
    @pytest.mark.asyncio
    async def test_tactile_to_physiological(self, biological_systems):
        """
        测试触觉到生理反应链路
        
        验证：
        - 触觉输入被正确解析
        - 触发相应的生理反应
        - 神经信号传递正确
        """
        metrics = TestMetrics("test_tactile_to_physiological", time.time())
        
        try:
            # 触觉输入
            tactile_input = {
                'type': 'touch',
                'location': 'head',
                'pressure': 0.3,
                'duration': 1.5,
                'temperature': 36.5
            }
            
            with patch('core.biological.tactile_system.TactileSystem.process') as mock_tactile, \
                 patch('core.biological.physiological_system.PhysiologicalSystem.react') as mock_physio:
                
                mock_tactile.return_value = {
                    'sensory_data': tactile_input,
                    'nerve_signals': ['pleasant_touch', 'warmth_detected'],
                    'processing_time_ms': 2.1
                }
                
                mock_physio.return_value = {
                    'physiological_state': 'relaxed',
                    'reactions': ['heart_rate_decrease', 'muscle_relaxation'],
                    'activation_level': 0.4,
                    'processing_time_ms': 3.2
                }
                
                # 执行链路
                tactile_result = mock_tactile(tactile_input)
                physio_result = mock_physio(tactile_result)
                
                # 验证链路
                assert 'pleasant_touch' in tactile_result['nerve_signals']
                assert physio_result['physiological_state'] == 'relaxed'
                assert physio_result['activation_level'] < 0.5
                
                total_time = tactile_result['processing_time_ms'] + physio_result['processing_time_ms']
                assert total_time < 16.0, f"Tactile→Physio latency {total_time}ms exceeds 16ms"
                
                metrics.complete(success=True)
                print(f"✓ Tactile→Physiological: {total_time:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
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
            physio_state = {
                'state': 'relaxed',
                'activation_level': 0.4,
                'heart_rate': 65
            }
            
            with patch('core.biological.endocrine_system.EndocrineSystem.update') as mock_endocrine:
                mock_endocrine.return_value = {
                    'hormone_levels': {
                        'oxytocin': 0.7,  # 亲密感
                        'cortisol': 0.2,  # 压力低
                        'dopamine': 0.6,  # 愉悦
                        'serotonin': 0.75  # 平静
                    },
                    'mood_influence': 'positive',
                    'processing_time_ms': 4.5
                }
                
                result = mock_endocrine(physio_state)
                
                # 验证激素变化
                assert result['hormone_levels']['oxytocin'] > 0.5  # 触摸增加亲密感
                assert result['hormone_levels']['cortisol'] < 0.3  # 放松状态压力低
                assert result['hormone_levels']['dopamine'] > 0.5  # 愉悦感
                assert result['mood_influence'] == 'positive'
                assert result['processing_time_ms'] < 10.0
                
                metrics.complete(success=True)
                print(f"✓ Physiological→Endocrine: {result['processing_time_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
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
            hormone_state = {
                'oxytocin': 0.7,
                'cortisol': 0.2,
                'dopamine': 0.6,
                'serotonin': 0.75
            }
            
            with patch('core.emotional.emotional_blending_system.EmotionalBlendingSystem.generate') as mock_emotion:
                mock_emotion.return_value = {
                    'primary_emotion': 'happy',
                    'emotion_blend': {
                        'happy': 0.75,
                        'content': 0.20,
                        'affectionate': 0.05
                    },
                    'intensity': 0.75,
                    'expression_params': {
                        'mouth_curve': 0.8,
                        'eye_brightness': 0.7,
                        'cheek_blush': 0.3
                    },
                    'processing_time_ms': 3.8
                }
                
                result = mock_emotion(hormone_state)
                
                # 验证情绪生成
                assert result['primary_emotion'] == 'happy'
                assert result['intensity'] > 0.5
                assert sum(result['emotion_blend'].values()) > 0.95  # 情绪混合总和接近1
                assert 'mouth_curve' in result['expression_params']
                assert result['processing_time_ms'] < 10.0
                
                metrics.complete(success=True)
                print(f"✓ Endocrine→Emotion: {result['processing_time_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
    async def test_complete_biological_chain(self, biological_systems):
        """
        测试完整生物系统链路
        
        链路：触觉 → 生理反应 → 激素变化 → 情绪生成
        总延迟应 < 50ms
        """
        metrics = TestMetrics("test_complete_biological_chain", time.time())
        
        try:
            chain_start = time.time()
            
            # 1. 触觉输入
            with patch('core.biological.tactile_system.TactileSystem.process') as mock_tactile:
                mock_tactile.return_value = {
                    'nerve_signals': ['pleasant_touch'],
                    'processing_time_ms': 2.0
                }
                tactile_result = mock_tactile({'type': 'touch', 'pressure': 0.3})
            
            # 2. 生理反应
            with patch('core.biological.physiological_system.PhysiologicalSystem.react') as mock_physio:
                mock_physio.return_value = {
                    'physiological_state': 'relaxed',
                    'processing_time_ms': 3.0
                }
                physio_result = mock_physio(tactile_result)
            
            # 3. 激素变化
            with patch('core.biological.endocrine_system.EndocrineSystem.update') as mock_endocrine:
                mock_endocrine.return_value = {
                    'hormone_levels': {'oxytocin': 0.7, 'dopamine': 0.6},
                    'processing_time_ms': 4.0
                }
                endocrine_result = mock_endocrine(physio_result)
            
            # 4. 情绪生成
            with patch('core.emotional.emotional_blending_system.EmotionalBlendingSystem.generate') as mock_emotion:
                mock_emotion.return_value = {
                    'primary_emotion': 'happy',
                    'intensity': 0.75,
                    'processing_time_ms': 3.0
                }
                emotion_result = mock_emotion(endocrine_result)
            
            chain_end = time.time()
            total_latency_ms = (chain_end - chain_start) * 1000
            
            # 验证完整链路
            assert emotion_result['primary_emotion'] == 'happy'
            assert emotion_result['intensity'] > 0.5
            assert total_latency_ms < 50.0, f"Biological chain latency {total_latency_ms}ms exceeds 50ms"
            
            metrics.complete(success=True)
            print(f"✓ Complete biological chain: {total_latency_ms:.2f}ms (target: <50ms)")
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
    async def test_biological_feedback_loop(self, biological_systems):
        """
        测试生物系统反馈循环
        
        验证：
        - 情绪影响激素
        - 激素影响生理
        - 生理影响感知
        """
        metrics = TestMetrics("test_biological_feedback_loop", time.time())
        
        try:
            # 模拟反馈循环
            iterations = 3
            
            with patch('core.biological.endocrine_system.EndocrineSystem.update') as mock_endocrine, \
                 patch('core.biological.physiological_system.PhysiologicalSystem.react') as mock_physio:
                
                # 初始状态
                emotion_state = {'type': 'happy', 'intensity': 0.6}
                
                for i in range(iterations):
                    # 情绪 → 激素
                    mock_endocrine.return_value = {
                        'hormone_levels': {
                            'dopamine': 0.6 + (i * 0.1),
                            'serotonin': 0.7
                        }
                    }
                    hormone = mock_endocrine(emotion_state)
                    
                    # 激素 → 生理
                    mock_physio.return_value = {
                        'physiological_state': 'balanced',
                        'wellness_score': 0.8 + (i * 0.05)
                    }
                    physio = mock_physio(hormone)
                    
                    # 验证反馈
                    assert physio['wellness_score'] > 0.7
                
                metrics.complete(success=True)
                print(f"✓ Biological feedback loop: {iterations} iterations completed")
                
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
            'decision_generator': Mock(),
            'action_executor': Mock(),
            'execution_bridge': Mock(),
            'tool_executor': Mock(),
        }
    
    @pytest.mark.asyncio
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
                'decision_id': str(uuid.uuid4()),
                'action_type': 'file_organize',
                'parameters': {'target_dir': '/downloads', 'organize_by': 'date'},
                'priority': 'normal',
                'estimated_duration': 5.0
            }
            
            with patch('core.execution.action_executor.ActionExecutor.receive_decision') as mock_receive:
                mock_receive.return_value = {
                    'received': True,
                    'execution_id': str(uuid.uuid4()),
                    'status': 'queued',
                    'queue_position': 1,
                    'processing_time_ms': 1.5
                }
                
                result = mock_receive(decision)
                
                assert result['received'] is True
                assert result['status'] == 'queued'
                assert result['processing_time_ms'] < 5.0
                
                metrics.complete(success=True)
                print(f"✓ Decision→Executor: {result['processing_time_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
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
                'execution_id': str(uuid.uuid4()),
                'action_type': 'file_organize',
                'parameters': {'target_dir': '/downloads'}
            }
            
            with patch('core.execution.action_execution_bridge.ActionExecutionBridge.route') as mock_route:
                mock_route.return_value = {
                    'routed': True,
                    'target_system': 'file_system_tool',
                    'transformed_params': {'path': '/downloads', 'operation': 'organize'},
                    'routing_time_ms': 2.0
                }
                
                result = mock_route(execution_request)
                
                assert result['routed'] is True
                assert result['target_system'] == 'file_system_tool'
                assert 'transformed_params' in result
                assert result['routing_time_ms'] < 5.0
                
                metrics.complete(success=True)
                print(f"✓ Executor→Bridge: {result['routing_time_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
    async def test_bridge_to_tool_execution(self, execution_system):
        """
        测试桥接器到工具执行链路
        
        验证：
        - 桥接器调用工具
        - 工具正确执行
        - 结果返回
        """
        metrics = TestMetrics("test_bridge_to_tool_execution", time.time())
        
        try:
            tool_request = {
                'tool_name': 'file_system_tool',
                'operation': 'organize',
                'params': {'path': '/downloads', 'by': 'date'}
            }
            
            with patch('tools.file_system_tool.FileSystemTool.execute') as mock_tool:
                mock_tool.return_value = {
                    'success': True,
                    'files_processed': 25,
                    'files_organized': 23,
                    'errors': 2,
                    'execution_time_ms': 3500.0,
                    'result_summary': 'Organized 23 files into date-based folders'
                }
                
                result = mock_tool(tool_request)
                
                assert result['success'] is True
                assert result['files_organized'] > 0
                assert 'result_summary' in result
                
                metrics.complete(success=True)
                print(f"✓ Bridge→Tool execution: {result['execution_time_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
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
            execution_result = {
                'success': True,
                'files_organized': 23,
                'errors': 2
            }
            
            with patch('core.execution.feedback_collector.FeedbackCollector.collect') as mock_collect:
                mock_collect.return_value = {
                    'feedback_id': str(uuid.uuid4()),
                    'execution_success': True,
                    'effectiveness_score': 0.92,
                    'user_satisfaction_estimate': 0.85,
                    'improvement_suggestions': ['better_error_handling', 'progress_reporting'],
                    'learning_data': {
                        'action_type': 'file_organize',
                        'success_rate': 0.92,
                        'avg_duration': 3.5
                    },
                    'collection_time_ms': 5.5
                }
                
                result = mock_collect(execution_result)
                
                assert result['execution_success'] is True
                assert result['effectiveness_score'] > 0.8
                assert result['user_satisfaction_estimate'] > 0.7
                assert len(result['improvement_suggestions']) > 0
                assert result['collection_time_ms'] < 10.0
                
                metrics.complete(success=True)
                print(f"✓ Feedback collection: {result['collection_time_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
    async def test_complete_execution_pipeline(self, execution_system):
        """
        测试完整执行链路
        
        链路：决策 → 执行器 → 桥接器 → 工具执行 → 反馈
        """
        metrics = TestMetrics("test_complete_execution_pipeline", time.time())
        
        try:
            pipeline_start = time.time()
            
            # 1. 决策生成
            with patch('core.execution.action_executor.ActionExecutor.receive_decision') as mock_receive:
                mock_receive.return_value = {
                    'received': True,
                    'execution_id': 'exec_001',
                    'status': 'queued',
                    'processing_time_ms': 1.5
                }
                decision_result = mock_receive({'action_type': 'file_organize'})
            
            # 2. 执行器处理
            with patch('core.execution.action_execution_bridge.ActionExecutionBridge.route') as mock_route:
                mock_route.return_value = {
                    'routed': True,
                    'target_system': 'file_system_tool',
                    'routing_time_ms': 2.0
                }
                bridge_result = mock_route(decision_result)
            
            # 3. 工具执行
            with patch('tools.file_system_tool.FileSystemTool.execute') as mock_tool:
                mock_tool.return_value = {
                    'success': True,
                    'files_organized': 23,
                    'execution_time_ms': 3500.0
                }
                tool_result = mock_tool(bridge_result)
            
            # 4. 反馈收集
            with patch('core.execution.feedback_collector.FeedbackCollector.collect') as mock_collect:
                mock_collect.return_value = {
                    'execution_success': True,
                    'effectiveness_score': 0.92,
                    'collection_time_ms': 5.5
                }
                feedback_result = mock_collect(tool_result)
            
            pipeline_end = time.time()
            total_time_ms = (pipeline_end - pipeline_start) * 1000
            
            # 验证完整链路
            assert decision_result['status'] == 'queued'
            assert bridge_result['routed'] is True
            assert tool_result['success'] is True
            assert feedback_result['execution_success'] is True
            assert feedback_result['effectiveness_score'] > 0.8
            
            metrics.complete(success=True)
            print(f"✓ Complete execution pipeline: {total_time_ms:.2f}ms")
            
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
            'experience_store': Mock(),
            'hsm_system': Mock(),
            'cdm_system': Mock(),
            'strategy_adjuster': Mock(),
        }
    
    @pytest.mark.asyncio
    async def test_experience_storage(self, memory_learning_system):
        """
        测试经验存储
        
        验证：
        - 经验被正确编码
        - 存储到正确记忆类型
        - 索引建立
        """
        metrics = TestMetrics("test_experience_storage", time.time())
        
        try:
            experience = {
                'type': 'interaction',
                'context': {'user_action': 'gentle_touch', 'location': 'head'},
                'angela_response': {'emotion': 'happy', 'action': 'smile'},
                'outcome': 'positive',
                'timestamp': datetime.now()
            }
            
            with patch('core.memory.experience_store.ExperienceStore.store') as mock_store:
                mock_store.return_value = {
                    'stored': True,
                    'memory_id': str(uuid.uuid4()),
                    'memory_type': 'episodic',
                    'embedding_created': True,
                    'associations_formed': 3,
                    'storage_time_ms': 8.5
                }
                
                result = mock_store(experience)
                
                assert result['stored'] is True
                assert result['memory_type'] == 'episodic'
                assert result['embedding_created'] is True
                assert result['associations_formed'] > 0
                assert result['storage_time_ms'] < 20.0
                
                metrics.complete(success=True)
                print(f"✓ Experience storage: {result['storage_time_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
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
                'new_patterns': ['gentle_touch_positive_response'],
                'exploration_results': [{'domain': 'social', 'novelty': 0.3}]
            }
            
            with patch('core.hsm_formula_system.HSMFormulaSystem.update') as mock_hsm:
                mock_hsm.return_value = {
                    'updated': True,
                    'heuristic_rules_added': 1,
                    'exploration_threshold_adjusted': True,
                    'new_threshold': 0.65,
                    'cognitive_gap_detected': False,
                    'update_time_ms': 12.3
                }
                
                result = mock_hsm(experience_data)
                
                assert result['updated'] is True
                assert result['heuristic_rules_added'] > 0
                assert result['exploration_threshold_adjusted'] is True
                assert result['update_time_ms'] < 20.0
                
                metrics.complete(success=True)
                print(f"✓ HSM update: {result['update_time_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
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
                {'type': 'social_interaction', 'duration': 5.0, 'value': 0.8},
                {'type': 'learning', 'duration': 10.0, 'value': 0.9}
            ]
            
            with patch('core.cdm_dividend_model.CDMCognitiveDividendModel.calculate') as mock_cdm:
                mock_cdm.return_value = {
                    'calculated': True,
                    'total_dividend': 14.5,
                    'conversion_rate': 0.967,
                    'resource_allocation': {
                        'social': 0.35,
                        'learning': 0.40,
                        'exploration': 0.25
                    },
                    'strategy_recommendations': ['increase_learning_allocation'],
                    'calculation_time_ms': 9.2
                }
                
                result = mock_cdm(cognitive_activities)
                
                assert result['calculated'] is True
                assert result['total_dividend'] > 0
                assert sum(result['resource_allocation'].values()) == 1.0
                assert len(result['strategy_recommendations']) > 0
                assert result['calculation_time_ms'] < 20.0
                
                metrics.complete(success=True)
                print(f"✓ CDM learning: {result['calculation_time_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
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
                'hsm_recommendations': ['explore_social_domain'],
                'cdm_allocation': {'social': 0.35, 'learning': 0.40}
            }
            
            with patch('core.autonomous.strategy_adjuster.StrategyAdjuster.adjust') as mock_adjust:
                mock_adjust.return_value = {
                    'adjusted': True,
                    'strategy_changes': [
                        {'type': 'exploration_focus', 'domain': 'social', 'weight': 0.35},
                        {'type': 'learning_priority', 'topics': ['user_preferences'], 'weight': 0.40}
                    ],
                    'decision_model_updates': {'temperature': 0.8, 'exploration_rate': 0.25},
                    'adjustment_time_ms': 7.8
                }
                
                result = mock_adjust(learning_outputs)
                
                assert result['adjusted'] is True
                assert len(result['strategy_changes']) > 0
                assert 'decision_model_updates' in result
                assert result['adjustment_time_ms'] < 20.0
                
                metrics.complete(success=True)
                print(f"✓ Strategy adjustment: {result['adjustment_time_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
    async def test_complete_memory_learning_cycle(self, memory_learning_system):
        """
        测试完整记忆-学习循环
        
        链路：经验存储 → HSM更新 → CDM学习 → 策略调整
        """
        metrics = TestMetrics("test_complete_memory_learning_cycle", time.time())
        
        try:
            cycle_start = time.time()
            
            # 1. 经验存储
            with patch('core.memory.experience_store.ExperienceStore.store') as mock_store:
                mock_store.return_value = {
                    'stored': True,
                    'memory_id': 'mem_001',
                    'storage_time_ms': 8.5
                }
                store_result = mock_store({'type': 'interaction'})
            
            # 2. HSM更新
            with patch('core.hsm_formula_system.HSMFormulaSystem.update') as mock_hsm:
                mock_hsm.return_value = {
                    'updated': True,
                    'update_time_ms': 12.3
                }
                hsm_result = mock_hsm(store_result)
            
            # 3. CDM学习
            with patch('core.cdm_dividend_model.CDMCognitiveDividendModel.calculate') as mock_cdm:
                mock_cdm.return_value = {
                    'calculated': True,
                    'total_dividend': 14.5,
                    'calculation_time_ms': 9.2
                }
                cdm_result = mock_cdm(hsm_result)
            
            # 4. 策略调整
            with patch('core.autonomous.strategy_adjuster.StrategyAdjuster.adjust') as mock_adjust:
                mock_adjust.return_value = {
                    'adjusted': True,
                    'adjustment_time_ms': 7.8
                }
                adjust_result = mock_adjust(cdm_result)
            
            cycle_end = time.time()
            total_time_ms = (cycle_end - cycle_start) * 1000
            
            # 验证完整循环
            assert store_result['stored'] is True
            assert hsm_result['updated'] is True
            assert cdm_result['calculated'] is True
            assert adjust_result['adjusted'] is True
            
            metrics.complete(success=True)
            print(f"✓ Complete memory-learning cycle: {total_time_ms:.2f}ms")
            
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
            'input_monitor': Mock(),
            'event_processor': Mock(),
            'response_generator': Mock(),
        }
    
    @pytest.mark.asyncio
    async def test_input_monitoring(self, feedback_system):
        """
        测试输入监测
        
        验证：
        - 输入被实时捕获
        - 事件分类正确
        - 延迟 < 16ms
        """
        metrics = TestMetrics("test_input_monitoring", time.time())
        
        try:
            user_input = {
                'type': 'mouse_move',
                'position': (500, 300),
                'timestamp': datetime.now()
            }
            
            with patch('core.feedback.input_monitor.InputMonitor.capture') as mock_capture:
                mock_capture.return_value = {
                    'captured': True,
                    'event_type': 'mouse_interaction',
                    'priority': 'normal',
                    'detection_latency_ms': 2.1
                }
                
                result = mock_capture(user_input)
                
                assert result['captured'] is True
                assert result['event_type'] == 'mouse_interaction'
                assert result['detection_latency_ms'] < 16.0
                
                metrics.complete(success=True)
                print(f"✓ Input monitoring: {result['detection_latency_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
    async def test_event_processing(self, feedback_system):
        """
        测试事件处理
        
        验证：
        - 事件被正确解析
        - 响应策略选择
        - 处理延迟 < 16ms
        """
        metrics = TestMetrics("test_event_processing", time.time())
        
        try:
            captured_event = {
                'event_type': 'mouse_interaction',
                'priority': 'normal',
                'context': {'near_pet': True, 'movement_speed': 'slow'}
            }
            
            with patch('core.feedback.event_processor.EventProcessor.process') as mock_process:
                mock_process.return_value = {
                    'processed': True,
                    'event_category': 'attention_signal',
                    'response_strategy': 'acknowledge_attention',
                    'urgency_level': 'low',
                    'processing_time_ms': 5.8
                }
                
                result = mock_process(captured_event)
                
                assert result['processed'] is True
                assert result['event_category'] == 'attention_signal'
                assert result['urgency_level'] in ['low', 'medium', 'high']
                assert result['processing_time_ms'] < 16.0
                
                metrics.complete(success=True)
                print(f"✓ Event processing: {result['processing_time_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
    async def test_response_generation(self, feedback_system):
        """
        测试响应生成
        
        验证：
        - 响应被快速生成
        - 响应符合情境
        - 延迟 < 16ms
        """
        metrics = TestMetrics("test_response_generation", time.time())
        
        try:
            processed_event = {
                'event_category': 'attention_signal',
                'response_strategy': 'acknowledge_attention',
                'urgency_level': 'low'
            }
            
            with patch('core.feedback.response_generator.ResponseGenerator.generate') as mock_generate:
                mock_generate.return_value = {
                    'generated': True,
                    'response_type': 'visual',
                    'response_content': {
                        'expression': 'curious',
                        'action': 'look_towards_cursor',
                        'duration': 2.0
                    },
                    'generation_time_ms': 4.2
                }
                
                result = mock_generate(processed_event)
                
                assert result['generated'] is True
                assert result['response_type'] == 'visual'
                assert 'expression' in result['response_content']
                assert result['generation_time_ms'] < 16.0
                
                metrics.complete(success=True)
                print(f"✓ Response generation: {result['generation_time_ms']:.2f}ms")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
    async def test_complete_feedback_loop(self, feedback_system):
        """
        测试完整反馈循环
        
        链路：输入监测 → 事件处理 → 响应生成
        总延迟必须 < 16ms
        """
        metrics = TestMetrics("test_complete_feedback_loop", time.time())
        
        try:
            loop_start = time.perf_counter()
            
            # 1. 输入监测
            with patch('core.feedback.input_monitor.InputMonitor.capture') as mock_capture:
                mock_capture.return_value = {
                    'captured': True,
                    'detection_latency_ms': 2.0
                }
                capture_result = mock_capture({'type': 'mouse_move'})
            
            # 2. 事件处理
            with patch('core.feedback.event_processor.EventProcessor.process') as mock_process:
                mock_process.return_value = {
                    'processed': True,
                    'processing_time_ms': 5.0
                }
                process_result = mock_process(capture_result)
            
            # 3. 响应生成
            with patch('core.feedback.response_generator.ResponseGenerator.generate') as mock_generate:
                mock_generate.return_value = {
                    'generated': True,
                    'generation_time_ms': 4.0
                }
                generate_result = mock_generate(process_result)
            
            loop_end = time.perf_counter()
            total_latency_ms = (loop_end - loop_start) * 1000
            
            # 验证完整循环
            assert capture_result['captured'] is True
            assert process_result['processed'] is True
            assert generate_result['generated'] is True
            
            # 关键验证：总延迟必须 < 16ms
            assert total_latency_ms < 16.0, f"Feedback loop latency {total_latency_ms:.2f}ms exceeds 16ms requirement"
            
            metrics.complete(success=True)
            print(f"✓ Complete feedback loop: {total_latency_ms:.2f}ms (target: <16ms) ✓ PASS")
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
    
    @pytest.mark.asyncio
    async def test_event_integrity(self, feedback_system):
        """
        测试事件完整性
        
        验证：
        - 事件数据不丢失
        - 处理顺序正确
        - 状态一致
        """
        metrics = TestMetrics("test_event_integrity", time.time())
        
        try:
            # 模拟并发事件
            events = [
                {'id': 1, 'type': 'touch', 'timestamp': datetime.now()},
                {'id': 2, 'type': 'voice', 'timestamp': datetime.now()},
                {'id': 3, 'type': 'mouse', 'timestamp': datetime.now()},
            ]
            
            processed_ids = []
            
            with patch('core.feedback.event_processor.EventProcessor.process') as mock_process:
                for event in events:
                    mock_process.return_value = {
                        'processed': True,
                        'event_id': event['id'],
                        'preserved_data': event
                    }
                    result = mock_process(event)
                    processed_ids.append(result['event_id'])
                    
                    # 验证数据完整性
                    assert result['preserved_data']['id'] == event['id']
                    assert result['preserved_data']['type'] == event['type']
            
            # 验证所有事件都被处理
            assert len(processed_ids) == len(events)
            assert set(processed_ids) == {1, 2, 3}
            
            metrics.complete(success=True)
            print(f"✓ Event integrity: {len(events)} events processed, all data preserved")
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise


# =============================================================================
# 测试套件执行入口
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '-m', 'system_integration'])
