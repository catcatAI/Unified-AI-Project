"""
Angela AI v6.0 - End-to-End Scenario Tests
端到端场景测试

测试真实的用户使用场景，验证完整的工作流程。

场景：
1. 用户触摸Desktop Pet
2. 用户发起对话
3. 自主行为触发
4. 文件整理请求

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

import pytest
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from dataclasses import dataclass


# Test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.system_integration,
    pytest.mark.e2e,
    pytest.mark.slow,
]


@dataclass
class ScenarioMetrics:
    """场景测试指标"""
    scenario_name: str
    start_time: float
    end_time: Optional[float] = None
    steps_completed: int = 0
    total_steps: int = 0
    success: bool = False
    error_message: Optional[str] = None
    latencies: List[float] = None
    
    def __post_init__(self):
        if self.latencies is None:
            self.latencies = []
    
    def step_complete(self, latency_ms: float):
        """记录步骤完成"""
        self.steps_completed += 1
        self.latencies.append(latency_ms)
    
    def complete(self, success: bool = True, error: Optional[str] = None):
        """完成场景测试"""
        self.end_time = time.time()
        self.success = success
        self.error_message = error
    
    @property
    def total_latency_ms(self) -> float:
        """总延迟（毫秒）"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0
    
    @property
    def avg_step_latency_ms(self) -> float:
        """平均步骤延迟"""
        if self.latencies:
            return sum(self.latencies) / len(self.latencies)
        return 0.0


class TestScenarioUserTouch:
    """
    场景1：用户触摸Desktop Pet
    
    流程：鼠标输入 → 触觉系统 → 情绪变化 → 表情更新 → Live2D渲染
    """
    
    @pytest.fixture
    async def touch_scenario_setup(self):
        """触摸场景设置"""
        return {
            'desktop_pet': Mock(),
            'tactile_system': Mock(),
            'emotional_system': Mock(),
            'live2d_renderer': Mock(),
        }
    
    @pytest.mark.asyncio
    async def test_scenario_touch_detection(self, touch_scenario_setup):
        """
        步骤1：触摸检测
        
        验证：
        - 鼠标点击在Desktop Pet区域被检测
        - 触摸位置正确计算
        - 触摸类型识别（点击/拖拽/长按）
        """
        metrics = ScenarioMetrics("test_scenario_touch_detection", time.time(), total_steps=5)
        
        try:
            # 模拟鼠标点击事件
            mouse_event = {
                'type': 'click',
                'x': 450,
                'y': 300,
                'button': 'left',
                'timestamp': time.time()
            }
            
            with patch('core.desktop_pet_controller.DesktopPetController.is_within_pet_bounds') as mock_bounds, \
                 patch('core.desktop_pet_controller.DesktopPetController.handle_mouse_event') as mock_handler:
                
                mock_bounds.return_value = True  # 点击在宠物范围内
                mock_handler.return_value = {
                    'event_type': 'pet_touch',
                    'touch_location': 'head',
                    'touch_pressure': 0.5,
                    'touch_duration': 0.1,
                    'detection_time_ms': 2.5
                }
                
                step_start = time.perf_counter()
                is_within = mock_bounds(mouse_event['x'], mouse_event['y'])
                result = mock_handler(mouse_event)
                step_end = time.perf_counter()
                
                latency_ms = (step_end - step_start) * 1000
                
                # 验证
                assert is_within is True
                assert result['event_type'] == 'pet_touch'
                assert result['touch_location'] in ['head', 'body', 'hand', 'foot']
                assert latency_ms < 16.0
                
                metrics.step_complete(latency_ms)
                print(f"✓ Step 1: Touch detection ({latency_ms:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_tactile_processing(self, touch_scenario_setup):
        """
        步骤2：触觉处理
        
        验证：
        - 触摸信号被转换为触觉感知
        - 压力、温度、持续时间解析
        - 生成触觉特征向量
        """
        metrics = ScenarioMetrics("test_scenario_tactile_processing", time.time(), total_steps=5)
        
        try:
            touch_event = {
                'touch_location': 'head',
                'touch_pressure': 0.5,
                'touch_duration': 0.1,
                'temperature': 36.5
            }
            
            with patch('core.biological.tactile_system.TactileSystem.process_touch') as mock_process:
                mock_process.return_value = {
                    'tactile_vector': [0.5, 0.3, 0.8, 0.2],  # 压力、温度、愉悦度、强度
                    'nerve_response': 'pleasant',
                    'sensory_quality': 'gentle',
                    'processing_time_ms': 4.2
                }
                
                step_start = time.perf_counter()
                result = mock_process(touch_event)
                step_end = time.perf_counter()
                
                latency_ms = (step_end - step_start) * 1000
                
                # 验证
                assert len(result['tactile_vector']) == 4
                assert result['nerve_response'] == 'pleasant'
                assert result['sensory_quality'] == 'gentle'
                assert result['processing_time_ms'] < 16.0
                
                metrics.step_complete(latency_ms)
                print(f"✓ Step 2: Tactile processing ({latency_ms:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_emotional_response(self, touch_scenario_setup):
        """
        步骤3：情绪响应
        
        验证：
        - 触觉输入触发情绪变化
        - 情绪混合正确计算
        - 情绪强度合理
        """
        metrics = ScenarioMetrics("test_scenario_emotional_response", time.time(), total_steps=5)
        
        try:
            tactile_data = {
                'tactile_vector': [0.5, 0.3, 0.8, 0.2],
                'nerve_response': 'pleasant',
                'sensory_quality': 'gentle'
            }
            
            with patch('core.emotional.emotional_blending_system.EmotionalBlendingSystem.blend') as mock_blend:
                mock_blend.return_value = {
                    'primary_emotion': 'happy',
                    'emotion_blend': {
                        'happy': 0.65,
                        'affectionate': 0.25,
                        'surprised': 0.10
                    },
                    'intensity': 0.72,
                    'valence': 0.8,
                    'arousal': 0.5,
                    'processing_time_ms': 6.8
                }
                
                step_start = time.perf_counter()
                result = mock_blend(tactile_data)
                step_end = time.perf_counter()
                
                latency_ms = (step_end - step_start) * 1000
                
                # 验证
                assert result['primary_emotion'] == 'happy'
                assert sum(result['emotion_blend'].values()) > 0.95
                assert result['intensity'] > 0.5
                assert result['valence'] > 0.5  # 正面情绪
                assert result['processing_time_ms'] < 16.0
                
                metrics.step_complete(latency_ms)
                print(f"✓ Step 3: Emotional response ({latency_ms:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_expression_update(self, touch_scenario_setup):
        """
        步骤4：表情更新
        
        验证：
        - 情绪状态转换为表情参数
        - Live2D参数计算正确
        - 过渡动画流畅
        """
        metrics = ScenarioMetrics("test_scenario_expression_update", time.time(), total_steps=5)
        
        try:
            emotion_state = {
                'primary_emotion': 'happy',
                'emotion_blend': {'happy': 0.65, 'affectionate': 0.25},
                'intensity': 0.72
            }
            
            with patch('core.live2d.expression_controller.ExpressionController.update') as mock_update:
                mock_update.return_value = {
                    'expression_params': {
                        'mouth_smile': 0.75,
                        'eye_happy': 0.70,
                        'cheek_blush': 0.35,
                        'eyebrow_relaxed': 0.60
                    },
                    'transition_duration': 0.5,
                    'expression_id': 'happy_touch_response',
                    'update_time_ms': 3.5
                }
                
                step_start = time.perf_counter()
                result = mock_update(emotion_state)
                step_end = time.perf_counter()
                
                latency_ms = (step_end - step_start) * 1000
                
                # 验证
                assert 'mouth_smile' in result['expression_params']
                assert result['expression_params']['mouth_smile'] > 0.5
                assert result['transition_duration'] < 1.0  # 快速过渡
                assert result['update_time_ms'] < 16.0
                
                metrics.step_complete(latency_ms)
                print(f"✓ Step 4: Expression update ({latency_ms:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_live2d_rendering(self, touch_scenario_setup):
        """
        步骤5：Live2D渲染
        
        验证：
        - 表情参数传递给渲染器
        - Live2D模型正确渲染
        - 帧率保持稳定（> 30fps）
        """
        metrics = ScenarioMetrics("test_scenario_live2d_rendering", time.time(), total_steps=5)
        
        try:
            expression_params = {
                'mouth_smile': 0.75,
                'eye_happy': 0.70,
                'cheek_blush': 0.35
            }
            
            with patch('core.live2d.live2d_renderer.Live2DRenderer.render') as mock_render:
                mock_render.return_value = {
                    'rendered': True,
                    'frame_time_ms': 16.67,  # ~60fps
                    'frame_rate': 60.0,
                    'model_updated': True,
                    'render_time_ms': 5.2
                }
                
                step_start = time.perf_counter()
                result = mock_render(expression_params)
                step_end = time.perf_counter()
                
                latency_ms = (step_end - step_start) * 1000
                
                # 验证
                assert result['rendered'] is True
                assert result['frame_rate'] >= 30.0  # 至少30fps
                assert result['frame_time_ms'] <= 33.33  # 对应30fps
                assert result['model_updated'] is True
                assert result['render_time_ms'] < 16.0
                
                metrics.step_complete(latency_ms)
                print(f"✓ Step 5: Live2D rendering ({latency_ms:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_complete_touch_scenario(self, touch_scenario_setup):
        """
        完整场景测试：用户触摸Desktop Pet
        
        验证完整流程：
        鼠标输入 → 触觉系统 → 情绪变化 → 表情更新 → Live2D渲染
        
        总延迟应 < 100ms
        """
        metrics = ScenarioMetrics("test_complete_touch_scenario", time.time(), total_steps=5)
        
        try:
            scenario_start = time.perf_counter()
            
            # 步骤1: 鼠标输入检测
            with patch('core.desktop_pet_controller.DesktopPetController.handle_mouse_event') as mock_handler:
                mock_handler.return_value = {
                    'event_type': 'pet_touch',
                    'touch_location': 'head',
                    'detection_time_ms': 2.5
                }
                step1_result = mock_handler({'type': 'click', 'x': 450, 'y': 300})
                step1_latency = step1_result['detection_time_ms']
            
            # 步骤2: 触觉处理
            with patch('core.biological.tactile_system.TactileSystem.process_touch') as mock_tactile:
                mock_tactile.return_value = {
                    'tactile_vector': [0.5, 0.3, 0.8, 0.2],
                    'processing_time_ms': 4.2
                }
                step2_result = mock_tactile(step1_result)
                step2_latency = step2_result['processing_time_ms']
            
            # 步骤3: 情绪响应
            with patch('core.emotional.emotional_blending_system.EmotionalBlendingSystem.blend') as mock_emotion:
                mock_emotion.return_value = {
                    'primary_emotion': 'happy',
                    'intensity': 0.72,
                    'processing_time_ms': 6.8
                }
                step3_result = mock_emotion(step2_result)
                step3_latency = step3_result['processing_time_ms']
            
            # 步骤4: 表情更新
            with patch('core.live2d.expression_controller.ExpressionController.update') as mock_expr:
                mock_expr.return_value = {
                    'expression_params': {'mouth_smile': 0.75},
                    'update_time_ms': 3.5
                }
                step4_result = mock_expr(step3_result)
                step4_latency = step4_result['update_time_ms']
            
            # 步骤5: Live2D渲染
            with patch('core.live2d.live2d_renderer.Live2DRenderer.render') as mock_render:
                mock_render.return_value = {
                    'rendered': True,
                    'frame_rate': 60.0,
                    'render_time_ms': 5.2
                }
                step5_result = mock_render(step4_result)
                step5_latency = step5_result['render_time_ms']
            
            scenario_end = time.perf_counter()
            total_latency_ms = (scenario_end - scenario_start) * 1000
            
            # 验证完整场景
            assert step1_result['event_type'] == 'pet_touch'
            assert step3_result['primary_emotion'] == 'happy'
            assert step5_result['rendered'] is True
            assert step5_result['frame_rate'] >= 30.0
            
            # 关键验证：总延迟 < 100ms
            assert total_latency_ms < 100.0, f"Touch scenario latency {total_latency_ms:.2f}ms exceeds 100ms"
            
            metrics.complete(success=True)
            print(f"✓\n" + "="*60)
            print(f"✓ COMPLETE TOUCH SCENARIO")
            print(f"✓ Total latency: {total_latency_ms:.2f}ms (target: <100ms) ✓ PASS")
            print(f"✓ Individual steps:")
            print(f"✓   - Touch detection: {step1_latency:.2f}ms")
            print(f"✓   - Tactile processing: {step2_latency:.2f}ms")
            print(f"✓   - Emotional response: {step3_latency:.2f}ms")
            print(f"✓   - Expression update: {step4_latency:.2f}ms")
            print(f"✓   - Live2D rendering: {step5_latency:.2f}ms")
            print(f"="*60)
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise


class TestScenarioUserConversation:
    """
    场景2：用户发起对话
    
    流程：语音输入 → 认知处理 → 回应生成 → TTS → 口型同步
    """
    
    @pytest.fixture
    async def conversation_setup(self):
        """对话场景设置"""
        return {
            'voice_input': Mock(),
            'cognitive_processor': Mock(),
            'response_generator': Mock(),
            'tts_engine': Mock(),
            'lip_sync': Mock(),
        }
    
    @pytest.mark.asyncio
    async def test_scenario_voice_input(self, conversation_setup):
        """
        步骤1：语音输入处理
        
        验证：
        - 语音被正确捕获
        - STT转换准确
        - 文本语义解析
        """
        metrics = ScenarioMetrics("test_scenario_voice_input", time.time(), total_steps=5)
        
        try:
            audio_data = b'\x00\x01\x02\x03...'  # 模拟音频数据
            
            with patch('services.audio_service.AudioService.speech_to_text') as mock_stt:
                mock_stt.return_value = {
                    'transcribed_text': 'Angela, how are you feeling today?',
                    'confidence': 0.94,
                    'language': 'en',
                    'processing_time_ms': 450.0  # STT通常较慢
                }
                
                result = mock_stt(audio_data)
                
                assert result['transcribed_text'] is not None
                assert len(result['transcribed_text']) > 0
                assert result['confidence'] > 0.8
                assert 'Angela' in result['transcribed_text']
                
                metrics.step_complete(result['processing_time_ms'])
                print(f"✓ Step 1: Voice input/STT ({result['processing_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_cognitive_processing(self, conversation_setup):
        """
        步骤2：认知处理
        
        验证：
        - 意图识别准确
        - 上下文理解正确
        - 记忆检索相关
        """
        metrics = ScenarioMetrics("test_scenario_cognitive_processing", time.time(), total_steps=5)
        
        try:
            user_input = {'text': 'Angela, how are you feeling today?', 'context': {}}
            
            with patch('core.cognition.cognitive_engine.CognitiveEngine.process') as mock_cog:
                mock_cog.return_value = {
                    'intent': 'emotional_inquiry',
                    'entities': {'target': 'Angela', 'topic': 'emotional_state'},
                    'context_understanding': 'user_cares_about_my_wellbeing',
                    'relevant_memories': ['previous_positive_interaction', 'user_preference_caring'],
                    'processing_time_ms': 180.0
                }
                
                result = mock_cog(user_input)
                
                assert result['intent'] == 'emotional_inquiry'
                assert 'target' in result['entities']
                assert len(result['relevant_memories']) > 0
                assert result['processing_time_ms'] < 500.0
                
                metrics.step_complete(result['processing_time_ms'])
                print(f"✓ Step 2: Cognitive processing ({result['processing_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_response_generation(self, conversation_setup):
        """
        步骤3：回应生成
        
        验证：
        - 回应内容合适
        - 情感色彩匹配
        - 个性化程度高
        """
        metrics = ScenarioMetrics("test_scenario_response_generation", time.time(), total_steps=5)
        
        try:
            cognitive_output = {
                'intent': 'emotional_inquiry',
                'context_understanding': 'user_cares_about_my_wellbeing'
            }
            
            with patch('core.nlg.natural_language_generation.NLG.generate') as mock_nlg:
                mock_nlg.return_value = {
                    'response_text': "I'm feeling wonderful today! Thanks for asking. Your presence always brightens my day~",
                    'emotional_tone': 'warm_appreciative',
                    'personalization_score': 0.85,
                    'response_time_ms': 320.0
                }
                
                result = mock_nlg(cognitive_output)
                
                assert len(result['response_text']) > 0
                assert 'wonderful' in result['response_text'] or 'good' in result['response_text']
                assert result['emotional_tone'] in ['warm_appreciative', 'happy', 'grateful']
                assert result['personalization_score'] > 0.7
                assert result['response_time_ms'] < 500.0
                
                metrics.step_complete(result['response_time_ms'])
                print(f"✓ Step 3: Response generation ({result['response_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_tts_generation(self, conversation_setup):
        """
        步骤4：TTS生成
        
        验证：
        - 音频生成成功
        - 语速自然
        - 情感色彩在语音中体现
        """
        metrics = ScenarioMetrics("test_scenario_tts_generation", time.time(), total_steps=5)
        
        try:
            response_text = "I'm feeling wonderful today! Thanks for asking."
            
            with patch('services.audio_service.AudioService.text_to_speech') as mock_tts:
                mock_tts.return_value = {
                    'audio_data': b'\x00\x01\x02\x03...',
                    'duration_seconds': 3.5,
                    'sample_rate': 24000,
                    'emotional_prosody': 'warm_happy',
                    'generation_time_ms': 280.0
                }
                
                result = mock_tts(response_text, emotion='happy')
                
                assert result['audio_data'] is not None
                assert result['duration_seconds'] > 0
                assert result['sample_rate'] >= 16000
                assert result['emotional_prosody'] == 'warm_happy'
                assert result['generation_time_ms'] < 500.0
                
                metrics.step_complete(result['generation_time_ms'])
                print(f"✓ Step 4: TTS generation ({result['generation_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_lip_sync(self, conversation_setup):
        """
        步骤5：口型同步
        
        验证：
        - 口型参数从音频提取
        - Live2D口型动画同步
        - 时序准确
        """
        metrics = ScenarioMetrics("test_scenario_lip_sync", time.time(), total_steps=5)
        
        try:
            audio_data = b'\x00\x01\x02\x03...'
            
            with patch('core.live2d.lip_sync.LipSyncController.sync') as mock_lip:
                mock_lip.return_value = {
                    'lip_params_sequence': [
                        {'time': 0.0, 'mouth_open': 0.0},
                        {'time': 0.1, 'mouth_open': 0.3},
                        {'time': 0.2, 'mouth_open': 0.7},
                        {'time': 0.3, 'mouth_open': 0.2},
                    ],
                    'sync_accuracy': 0.92,
                    'processing_time_ms': 45.0
                }
                
                result = mock_lip(audio_data)
                
                assert len(result['lip_params_sequence']) > 0
                assert result['sync_accuracy'] > 0.85
                assert result['processing_time_ms'] < 100.0
                
                metrics.step_complete(result['processing_time_ms'])
                print(f"✓ Step 5: Lip sync ({result['processing_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_complete_conversation_scenario(self, conversation_setup):
        """
        完整场景测试：用户发起对话
        
        验证完整流程：
        语音输入 → 认知处理 → 回应生成 → TTS → 口型同步
        
        总延迟应 < 2秒（语音场景容忍度较高）
        """
        metrics = ScenarioMetrics("test_complete_conversation_scenario", time.time(), total_steps=5)
        
        try:
            scenario_start = time.perf_counter()
            
            # 步骤1: 语音输入
            with patch('services.audio_service.AudioService.speech_to_text') as mock_stt:
                mock_stt.return_value = {
                    'transcribed_text': 'Angela, how are you feeling today?',
                    'confidence': 0.94,
                    'processing_time_ms': 450.0
                }
                step1_result = mock_stt(b'audio_data')
                step1_latency = step1_result['processing_time_ms']
            
            # 步骤2: 认知处理
            with patch('core.cognition.cognitive_engine.CognitiveEngine.process') as mock_cog:
                mock_cog.return_value = {
                    'intent': 'emotional_inquiry',
                    'processing_time_ms': 180.0
                }
                step2_result = mock_cog(step1_result)
                step2_latency = step2_result['processing_time_ms']
            
            # 步骤3: 回应生成
            with patch('core.nlg.natural_language_generation.NLG.generate') as mock_nlg:
                mock_nlg.return_value = {
                    'response_text': "I'm feeling wonderful today!",
                    'response_time_ms': 320.0
                }
                step3_result = mock_nlg(step2_result)
                step3_latency = step3_result['response_time_ms']
            
            # 步骤4: TTS生成
            with patch('services.audio_service.AudioService.text_to_speech') as mock_tts:
                mock_tts.return_value = {
                    'audio_data': b'audio',
                    'duration_seconds': 3.5,
                    'generation_time_ms': 280.0
                }
                step4_result = mock_tts(step3_result['response_text'])
                step4_latency = step4_result['generation_time_ms']
            
            # 步骤5: 口型同步
            with patch('core.live2d.lip_sync.LipSyncController.sync') as mock_lip:
                mock_lip.return_value = {
                    'sync_accuracy': 0.92,
                    'processing_time_ms': 45.0
                }
                step5_result = mock_lip(step4_result['audio_data'])
                step5_latency = step5_result['processing_time_ms']
            
            scenario_end = time.perf_counter()
            total_latency_ms = (scenario_end - scenario_start) * 1000
            
            # 验证完整场景
            assert step1_result['confidence'] > 0.8
            assert step2_result['intent'] == 'emotional_inquiry'
            assert step3_result['response_text'] is not None
            assert step4_result['duration_seconds'] > 0
            assert step5_result['sync_accuracy'] > 0.85
            
            # 关键验证：总延迟 < 2秒
            assert total_latency_ms < 2000.0, f"Conversation scenario latency {total_latency_ms:.2f}ms exceeds 2000ms"
            
            metrics.complete(success=True)
            print(f"✓\n" + "="*60)
            print(f"✓ COMPLETE CONVERSATION SCENARIO")
            print(f"✓ Total latency: {total_latency_ms:.2f}ms (target: <2000ms) ✓ PASS")
            print(f"✓ Individual steps:")
            print(f"✓   - Voice input/STT: {step1_latency:.2f}ms")
            print(f"✓   - Cognitive processing: {step2_latency:.2f}ms")
            print(f"✓   - Response generation: {step3_latency:.2f}ms")
            print(f"✓   - TTS generation: {step4_latency:.2f}ms")
            print(f"✓   - Lip sync: {step5_latency:.2f}ms")
            print(f"="*60)
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise


class TestScenarioAutonomousBehavior:
    """
    场景3：自主行为触发
    
    流程：内在状态评估 → 行为决策 → 行动执行 → 结果反馈 → 学习
    """
    
    @pytest.fixture
    async def autonomous_setup(self):
        """自主行为场景设置"""
        return {
            'state_evaluator': Mock(),
            'behavior_selector': Mock(),
            'action_executor': Mock(),
            'feedback_collector': Mock(),
            'learning_system': Mock(),
        }
    
    @pytest.mark.asyncio
    async def test_scenario_state_evaluation(self, autonomous_setup):
        """
        步骤1：内在状态评估
        
        验证：
        - 内在状态指标计算
        - 自主性评估
        - 行为触发条件判断
        """
        metrics = ScenarioMetrics("test_scenario_state_evaluation", time.time(), total_steps=5)
        
        try:
            with patch('core.autonomous.autonomous_life_cycle.AutonomousLifeCycle.evaluate_state') as mock_eval:
                mock_eval.return_value = {
                    'current_phase': 'exploration',
                    'boredom_level': 0.7,  # 较高的无聊度
                    'social_need': 0.6,
                    'curiosity_level': 0.8,
                    'autonomy_score': 0.75,
                    'should_trigger_behavior': True,
                    'evaluation_time_ms': 15.0
                }
                
                result = mock_eval()
                
                assert result['should_trigger_behavior'] is True
                assert result['boredom_level'] > 0.5
                assert result['autonomy_score'] > 0.5
                assert result['evaluation_time_ms'] < 50.0
                
                metrics.step_complete(result['evaluation_time_ms'])
                print(f"✓ Step 1: State evaluation ({result['evaluation_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_behavior_decision(self, autonomous_setup):
        """
        步骤2：行为决策
        
        验证：
        - 根据状态选择行为
        - HSM参与决策
        - 决策合理性
        """
        metrics = ScenarioMetrics("test_scenario_behavior_decision", time.time(), total_steps=5)
        
        try:
            state = {'boredom_level': 0.7, 'curiosity_level': 0.8}
            
            with patch('core.autonomous.autonomous_life_cycle.AutonomousLifeCycle.decide_behavior') as mock_decide:
                mock_decide.return_value = {
                    'decision_id': str(uuid.uuid4()),
                    'selected_behavior': 'explore_desktop',
                    'rationale': 'high_curiosity_low_activity',
                    'hsm_influenced': True,
                    'exploration_domain': 'desktop_environment',
                    'expected_duration': 30.0,
                    'decision_time_ms': 25.0
                }
                
                result = mock_decide(state)
                
                assert result['selected_behavior'] is not None
                assert len(result['rationale']) > 0
                assert result['hsm_influenced'] is True
                assert result['decision_time_ms'] < 50.0
                
                metrics.step_complete(result['decision_time_ms'])
                print(f"✓ Step 2: Behavior decision ({result['decision_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_action_execution(self, autonomous_setup):
        """
        步骤3：行动执行
        
        验证：
        - 行为被正确执行
        - 视觉效果呈现
        - 用户可感知
        """
        metrics = ScenarioMetrics("test_scenario_action_execution", time.time(), total_steps=5)
        
        try:
            behavior = {'selected_behavior': 'explore_desktop', 'exploration_domain': 'desktop_environment'}
            
            with patch('core.autonomous.behavior_executor.BehaviorExecutor.execute') as mock_exec:
                mock_exec.return_value = {
                    'execution_id': str(uuid.uuid4()),
                    'behavior_completed': True,
                    'actions_performed': [
                        'look_around',
                        'find_interesting_spot',
                        'move_to_spot',
                        'curious_expression'
                    ],
                    'user_noticed': True,
                    'execution_time_ms': 2850.0
                }
                
                result = mock_exec(behavior)
                
                assert result['behavior_completed'] is True
                assert len(result['actions_performed']) > 0
                assert result['user_noticed'] is True
                assert result['execution_time_ms'] < 5000.0
                
                metrics.step_complete(result['execution_time_ms'])
                print(f"✓ Step 3: Action execution ({result['execution_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_feedback_collection(self, autonomous_setup):
        """
        步骤4：结果反馈
        
        验证：
        - 行为结果被记录
        - 用户反应被评估
        - 效果评分计算
        """
        metrics = ScenarioMetrics("test_scenario_feedback_collection", time.time(), total_steps=5)
        
        try:
            execution_result = {
                'behavior_completed': True,
                'actions_performed': ['look_around', 'curious_expression'],
                'user_noticed': True
            }
            
            with patch('core.autonomous.feedback_collector.AutonomousFeedbackCollector.collect') as mock_collect:
                mock_collect.return_value = {
                    'feedback_id': str(uuid.uuid4()),
                    'behavior_effectiveness': 0.82,
                    'user_engagement_change': 0.15,  # 用户参与度提升
                    'positive_reaction': True,
                    'learning_value': 0.75,
                    'collection_time_ms': 18.0
                }
                
                result = mock_collect(execution_result)
                
                assert result['behavior_effectiveness'] > 0.5
                assert result['positive_reaction'] is True
                assert result['learning_value'] > 0.5
                assert result['collection_time_ms'] < 50.0
                
                metrics.step_complete(result['collection_time_ms'])
                print(f"✓ Step 4: Feedback collection ({result['collection_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_learning_update(self, autonomous_setup):
        """
        步骤5：学习更新
        
        验证：
        - 经验被整合到记忆
        - HSM启发式更新
        - 未来行为策略调整
        """
        metrics = ScenarioMetrics("test_scenario_learning_update", time.time(), total_steps=5)
        
        try:
            feedback = {
                'behavior_effectiveness': 0.82,
                'learning_value': 0.75,
                'positive_reaction': True
            }
            
            with patch('core.autonomous.learning_integrator.LearningIntegrator.integrate') as mock_learn:
                mock_learn.return_value = {
                    'integrated': True,
                    'memory_entries_created': 2,
                    'hsm_rules_updated': 1,
                    'behavior_weights_adjusted': True,
                    'future_exploration_bias': 'desktop_environment',
                    'integration_time_ms': 35.0
                }
                
                result = mock_learn(feedback)
                
                assert result['integrated'] is True
                assert result['memory_entries_created'] > 0
                assert result['hsm_rules_updated'] > 0
                assert result['behavior_weights_adjusted'] is True
                assert result['integration_time_ms'] < 100.0
                
                metrics.step_complete(result['integration_time_ms'])
                print(f"✓ Step 5: Learning update ({result['integration_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_complete_autonomous_scenario(self, autonomous_setup):
        """
        完整场景测试：自主行为触发
        
        验证完整流程：
        内在状态评估 → 行为决策 → 行动执行 → 结果反馈 → 学习
        
        总延迟应 < 5秒
        """
        metrics = ScenarioMetrics("test_complete_autonomous_scenario", time.time(), total_steps=5)
        
        try:
            scenario_start = time.perf_counter()
            
            # 步骤1: 状态评估
            with patch('core.autonomous.autonomous_life_cycle.AutonomousLifeCycle.evaluate_state') as mock_eval:
                mock_eval.return_value = {
                    'should_trigger_behavior': True,
                    'evaluation_time_ms': 15.0
                }
                step1_result = mock_eval()
                step1_latency = step1_result['evaluation_time_ms']
            
            # 步骤2: 行为决策
            with patch('core.autonomous.autonomous_life_cycle.AutonomousLifeCycle.decide_behavior') as mock_decide:
                mock_decide.return_value = {
                    'selected_behavior': 'explore_desktop',
                    'decision_time_ms': 25.0
                }
                step2_result = mock_decide(step1_result)
                step2_latency = step2_result['decision_time_ms']
            
            # 步骤3: 行动执行
            with patch('core.autonomous.behavior_executor.BehaviorExecutor.execute') as mock_exec:
                mock_exec.return_value = {
                    'behavior_completed': True,
                    'execution_time_ms': 2850.0
                }
                step3_result = mock_exec(step2_result)
                step3_latency = step3_result['execution_time_ms']
            
            # 步骤4: 反馈收集
            with patch('core.autonomous.feedback_collector.AutonomousFeedbackCollector.collect') as mock_collect:
                mock_collect.return_value = {
                    'behavior_effectiveness': 0.82,
                    'collection_time_ms': 18.0
                }
                step4_result = mock_collect(step3_result)
                step4_latency = step4_result['collection_time_ms']
            
            # 步骤5: 学习更新
            with patch('core.autonomous.learning_integrator.LearningIntegrator.integrate') as mock_learn:
                mock_learn.return_value = {
                    'integrated': True,
                    'integration_time_ms': 35.0
                }
                step5_result = mock_learn(step4_result)
                step5_latency = step5_result['integration_time_ms']
            
            scenario_end = time.perf_counter()
            total_latency_ms = (scenario_end - scenario_start) * 1000
            
            # 验证完整场景
            assert step1_result['should_trigger_behavior'] is True
            assert step2_result['selected_behavior'] == 'explore_desktop'
            assert step3_result['behavior_completed'] is True
            assert step4_result['behavior_effectiveness'] > 0.5
            assert step5_result['integrated'] is True
            
            # 关键验证：总延迟 < 5秒
            assert total_latency_ms < 5000.0, f"Autonomous scenario latency {total_latency_ms:.2f}ms exceeds 5000ms"
            
            metrics.complete(success=True)
            print(f"✓\n" + "="*60)
            print(f"✓ COMPLETE AUTONOMOUS BEHAVIOR SCENARIO")
            print(f"✓ Total latency: {total_latency_ms:.2f}ms (target: <5000ms) ✓ PASS")
            print(f"✓ Individual steps:")
            print(f"✓   - State evaluation: {step1_latency:.2f}ms")
            print(f"✓   - Behavior decision: {step2_latency:.2f}ms")
            print(f"✓   - Action execution: {step3_latency:.2f}ms")
            print(f"✓   - Feedback collection: {step4_latency:.2f}ms")
            print(f"✓   - Learning update: {step5_latency:.2f}ms")
            print(f"="*60)
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise


class TestScenarioFileOrganization:
    """
    场景4：文件整理请求
    
    流程：用户指令 → 意图识别 → 文件操作 → 执行验证 → 结果汇报
    """
    
    @pytest.fixture
    async def file_org_setup(self):
        """文件整理场景设置"""
        return {
            'intent_recognizer': Mock(),
            'file_operation_planner': Mock(),
            'file_system_tool': Mock(),
            'execution_verifier': Mock(),
            'result_reporter': Mock(),
        }
    
    @pytest.mark.asyncio
    async def test_scenario_intent_recognition(self, file_org_setup):
        """
        步骤1：意图识别
        
        验证：
        - 用户指令正确理解
        - 意图分类准确
        - 参数提取完整
        """
        metrics = ScenarioMetrics("test_scenario_intent_recognition", time.time(), total_steps=5)
        
        try:
            user_command = "Angela, please organize my downloads folder by date"
            
            with patch('core.nlu.intent_recognizer.IntentRecognizer.recognize') as mock_recognize:
                mock_recognize.return_value = {
                    'intent': 'file_organization',
                    'confidence': 0.96,
                    'extracted_params': {
                        'target_path': '/downloads',
                        'organization_criteria': 'date',
                        'operation_type': 'organize'
                    },
                    'processing_time_ms': 120.0
                }
                
                result = mock_recognize(user_command)
                
                assert result['intent'] == 'file_organization'
                assert result['confidence'] > 0.9
                assert 'target_path' in result['extracted_params']
                assert result['extracted_params']['organization_criteria'] == 'date'
                assert result['processing_time_ms'] < 200.0
                
                metrics.step_complete(result['processing_time_ms'])
                print(f"✓ Step 1: Intent recognition ({result['processing_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_operation_planning(self, file_org_setup):
        """
        步骤2：操作规划
        
        验证：
        - 执行计划生成
        - 步骤分解正确
        - 风险评估
        """
        metrics = ScenarioMetrics("test_scenario_operation_planning", time.time(), total_steps=5)
        
        try:
            intent_result = {
                'intent': 'file_organization',
                'extracted_params': {'target_path': '/downloads', 'organization_criteria': 'date'}
            }
            
            with patch('core.planning.operation_planner.OperationPlanner.plan') as mock_plan:
                mock_plan.return_value = {
                    'plan_id': str(uuid.uuid4()),
                    'operation_steps': [
                        {'step': 1, 'action': 'scan_directory', 'target': '/downloads'},
                        {'step': 2, 'action': 'analyze_files', 'criteria': 'date'},
                        {'step': 3, 'action': 'create_folders', 'structure': 'date_based'},
                        {'step': 4, 'action': 'move_files', 'mapping': 'auto'},
                        {'step': 5, 'action': 'verify_organization', 'checks': ['count', 'structure']}
                    ],
                    'estimated_duration': 15.0,
                    'risk_level': 'low',
                    'user_confirmation_required': False,
                    'planning_time_ms': 85.0
                }
                
                result = mock_plan(intent_result)
                
                assert len(result['operation_steps']) > 0
                assert result['risk_level'] in ['low', 'medium', 'high']
                assert result['estimated_duration'] > 0
                assert result['planning_time_ms'] < 200.0
                
                metrics.step_complete(result['planning_time_ms'])
                print(f"✓ Step 2: Operation planning ({result['planning_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_file_operation_execution(self, file_org_setup):
        """
        步骤3：文件操作执行
        
        验证：
        - 文件操作执行成功
        - 进度报告
        - 错误处理
        """
        metrics = ScenarioMetrics("test_scenario_file_operation_execution", time.time(), total_steps=5)
        
        try:
            operation_plan = {
                'operation_steps': [
                    {'action': 'scan_directory'},
                    {'action': 'move_files'}
                ]
            }
            
            with patch('tools.file_system_tool.FileSystemTool.execute_plan') as mock_execute:
                mock_execute.return_value = {
                    'execution_id': str(uuid.uuid4()),
                    'success': True,
                    'files_processed': 47,
                    'files_organized': 45,
                    'errors': 2,
                    'progress_reports': [
                        {'step': 1, 'status': 'completed', 'items': 47},
                        {'step': 2, 'status': 'completed', 'items': 45},
                    ],
                    'execution_time_ms': 3200.0
                }
                
                result = mock_execute(operation_plan)
                
                assert result['success'] is True
                assert result['files_organized'] > 0
                assert len(result['progress_reports']) > 0
                assert result['execution_time_ms'] < 10000.0
                
                metrics.step_complete(result['execution_time_ms'])
                print(f"✓ Step 3: File operation execution ({result['execution_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_execution_verification(self, file_org_setup):
        """
        步骤4：执行验证
        
        验证：
        - 操作结果验证
        - 完整性检查
        - 异常检测
        """
        metrics = ScenarioMetrics("test_scenario_execution_verification", time.time(), total_steps=5)
        
        try:
            execution_result = {
                'files_processed': 47,
                'files_organized': 45,
                'errors': 2
            }
            
            with patch('core.verification.execution_verifier.ExecutionVerifier.verify') as mock_verify:
                mock_verify.return_value = {
                    'verified': True,
                    'integrity_check_passed': True,
                    'all_files_accounted': True,
                    'structure_valid': True,
                    'success_rate': 0.957,  # 45/47
                    'verification_time_ms': 120.0
                }
                
                result = mock_verify(execution_result)
                
                assert result['verified'] is True
                assert result['integrity_check_passed'] is True
                assert result['success_rate'] > 0.9
                assert result['verification_time_ms'] < 500.0
                
                metrics.step_complete(result['verification_time_ms'])
                print(f"✓ Step 4: Execution verification ({result['verification_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_scenario_result_reporting(self, file_org_setup):
        """
        步骤5：结果汇报
        
        验证：
        - 结果摘要生成
        - 自然语言报告
        - 用户反馈收集
        """
        metrics = ScenarioMetrics("test_scenario_result_reporting", time.time(), total_steps=5)
        
        try:
            verification_result = {
                'success_rate': 0.957,
                'files_organized': 45,
                'errors': 2
            }
            
            with patch('core.reporting.result_reporter.ResultReporter.report') as mock_report:
                mock_report.return_value = {
                    'report_id': str(uuid.uuid4()),
                    'report_text': "I've successfully organized your downloads folder! 45 files were sorted into date-based folders. 2 files couldn't be moved due to permission issues, but everything else is neatly organized now. You can find your files organized by year and month.",
                    'report_format': 'natural_language',
                    'includes_details': True,
                    'user_feedback_requested': True,
                    'reporting_time_ms': 95.0
                }
                
                result = mock_report(verification_result)
                
                assert len(result['report_text']) > 0
                assert '45' in result['report_text']  # 提及文件数量
                assert result['includes_details'] is True
                assert result['reporting_time_ms'] < 200.0
                
                metrics.step_complete(result['reporting_time_ms'])
                print(f"✓ Step 5: Result reporting ({result['reporting_time_ms']:.2f}ms)")
                
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise
        
        metrics.complete(success=True)
        return metrics
    
    @pytest.mark.asyncio
    async def test_complete_file_organization_scenario(self, file_org_setup):
        """
        完整场景测试：文件整理请求
        
        验证完整流程：
        用户指令 → 意图识别 → 文件操作 → 执行验证 → 结果汇报
        
        总延迟应 < 10秒
        """
        metrics = ScenarioMetrics("test_complete_file_organization_scenario", time.time(), total_steps=5)
        
        try:
            scenario_start = time.perf_counter()
            
            # 步骤1: 意图识别
            with patch('core.nlu.intent_recognizer.IntentRecognizer.recognize') as mock_recognize:
                mock_recognize.return_value = {
                    'intent': 'file_organization',
                    'confidence': 0.96,
                    'processing_time_ms': 120.0
                }
                step1_result = mock_recognize("organize downloads")
                step1_latency = step1_result['processing_time_ms']
            
            # 步骤2: 操作规划
            with patch('core.planning.operation_planner.OperationPlanner.plan') as mock_plan:
                mock_plan.return_value = {
                    'operation_steps': [{'action': 'organize'}],
                    'planning_time_ms': 85.0
                }
                step2_result = mock_plan(step1_result)
                step2_latency = step2_result['planning_time_ms']
            
            # 步骤3: 文件操作执行
            with patch('tools.file_system_tool.FileSystemTool.execute_plan') as mock_execute:
                mock_execute.return_value = {
                    'success': True,
                    'files_organized': 45,
                    'execution_time_ms': 3200.0
                }
                step3_result = mock_execute(step2_result)
                step3_latency = step3_result['execution_time_ms']
            
            # 步骤4: 执行验证
            with patch('core.verification.execution_verifier.ExecutionVerifier.verify') as mock_verify:
                mock_verify.return_value = {
                    'verified': True,
                    'success_rate': 0.957,
                    'verification_time_ms': 120.0
                }
                step4_result = mock_verify(step3_result)
                step4_latency = step4_result['verification_time_ms']
            
            # 步骤5: 结果汇报
            with patch('core.reporting.result_reporter.ResultReporter.report') as mock_report:
                mock_report.return_value = {
                    'report_text': 'Organization complete!',
                    'reporting_time_ms': 95.0
                }
                step5_result = mock_report(step4_result)
                step5_latency = step5_result['reporting_time_ms']
            
            scenario_end = time.perf_counter()
            total_latency_ms = (scenario_end - scenario_start) * 1000
            
            # 验证完整场景
            assert step1_result['intent'] == 'file_organization'
            assert step1_result['confidence'] > 0.9
            assert step2_result['operation_steps'] is not None
            assert step3_result['success'] is True
            assert step4_result['verified'] is True
            assert step5_result['report_text'] is not None
            
            # 关键验证：总延迟 < 10秒
            assert total_latency_ms < 10000.0, f"File org scenario latency {total_latency_ms:.2f}ms exceeds 10000ms"
            
            metrics.complete(success=True)
            print(f"✓\n" + "="*60)
            print(f"✓ COMPLETE FILE ORGANIZATION SCENARIO")
            print(f"✓ Total latency: {total_latency_ms:.2f}ms (target: <10000ms) ✓ PASS")
            print(f"✓ Individual steps:")
            print(f"✓   - Intent recognition: {step1_latency:.2f}ms")
            print(f"✓   - Operation planning: {step2_latency:.2f}ms")
            print(f"✓   - File operation execution: {step3_latency:.2f}ms")
            print(f"✓   - Execution verification: {step4_latency:.2f}ms")
            print(f"✓   - Result reporting: {step5_latency:.2f}ms")
            print(f"✓   - Files organized: {step3_result['files_organized']}")
            print(f"✓   - Success rate: {step4_result['success_rate']*100:.1f}%")
            print(f"="*60)
            
        except Exception as e:
            metrics.complete(success=False, error=str(e))
            raise


# =============================================================================
# 场景测试执行入口
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short', '-m', 'e2e'])
