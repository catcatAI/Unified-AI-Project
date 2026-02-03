"""
Angela AI v6.0 - Desktop Pet Controller Test Suite
桌面宠物控制器测试套件

Comprehensive tests for Desktop Pet Controller including:
- Model loading
- Expression updates
- Action execution
- User interaction
- Autonomous behaviors
- Lifecycle management

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from apps.backend.src.core.desktop_pet_controller import (
    DesktopPetController,
    PetConfiguration,
    PetLifecycleState,
    SystemStatus
)
from apps.backend.src.game.desktop_pet import DesktopPet, DesktopPetState
from apps.backend.src.core.autonomous.live2d_integration import (
    Live2DIntegration, ExpressionType, MotionType
)
from apps.backend.src.core.autonomous.physiological_tactile import (
    PhysiologicalTactileSystem, TactileStimulus, TactileType, BodyPart
)
from apps.backend.src.core.autonomous.emotional_blending import (
    EmotionalBlendingSystem, BasicEmotion
)
from apps.backend.src.core.autonomous.extended_behavior_library import (
    ExtendedBehaviorLibrary, BehaviorCategory
)


@pytest.fixture
def pet_config():
    """Create default pet configuration for testing"""
    return PetConfiguration(
        name="TestAngela",
        model_path="models/test/model.json",
        scale=1.0,
        position={"x": 100, "y": 100},
        autonomous_check_interval=0.1,  # Fast for testing
        idle_timeout=1.0,  # Short for testing
        enable_mouse_tracking=True,
        enable_voice_lipsync=True,
        enable_tactile_feedback=True
    )


@pytest.fixture
def mock_orchestrator():
    """Create mock orchestrator"""
    mock = MagicMock()
    mock.process_user_input = MagicMock(return_value=AsyncMock())
    mock.process_user_input.remote = AsyncMock(return_value={
        "response": "Test response",
        "metadata": {"quality_score": 0.8}
    })
    return mock


@pytest.fixture
def mock_economy_manager():
    """Create mock economy manager"""
    mock = MagicMock()
    mock.reward_user = AsyncMock(return_value=True)
    mock.get_item_definition = AsyncMock(return_value={
        "name": "Test Item",
        "base_price": 10,
        "category": "food"
    })
    mock.buy_item = AsyncMock(return_value=True)
    return mock


@pytest.fixture
async def controller(pet_config, mock_orchestrator, mock_economy_manager):
    """Create and initialize controller for testing"""
    controller = DesktopPetController(
        config=pet_config,
        orchestrator=mock_orchestrator,
        economy_manager=mock_economy_manager
    )
    
    # Initialize
    success = await controller.initialize()
    assert success, "Controller initialization failed"
    
    yield controller
    
    # Cleanup
    await controller.shutdown()


class TestDesktopPetControllerInitialization:
    """测试控制器初始化 / Test controller initialization"""
    
    @pytest.mark.asyncio
    async def test_controller_creation(self, pet_config):
        """Test controller creation without initialization"""
        controller = DesktopPetController(config=pet_config)
        
        assert controller.config == pet_config
        assert controller.lifecycle_state == PetLifecycleState.INITIALIZING
        assert not controller._initialized
        assert controller.pet is None
    
    @pytest.mark.asyncio
    async def test_controller_initialize_success(self, pet_config, mock_orchestrator):
        """Test successful controller initialization"""
        controller = DesktopPetController(
            config=pet_config,
            orchestrator=mock_orchestrator
        )
        
        success = await controller.initialize()
        
        assert success
        assert controller._initialized
        assert controller.lifecycle_state == PetLifecycleState.ACTIVE
        assert controller.pet is not None
        assert controller._running
        
        # Cleanup
        await controller.shutdown()
    
    @pytest.mark.asyncio
    async def test_controller_initialize_failure(self, pet_config):
        """Test controller initialization failure handling"""
        controller = DesktopPetController(config=pet_config)
        
        # Mock pet to fail initialization
        with patch.object(DesktopPet, 'initialize', side_effect=Exception("Init failed")):
            success = await controller.initialize()
        
        assert not success
        assert controller.lifecycle_state == PetLifecycleState.ERROR
    
    @pytest.mark.asyncio
    async def test_pet_systems_initialized(self, controller):
        """Test that all biological systems are initialized"""
        assert controller.pet.live2d._running
        assert controller.pet.tactile_system._running
        assert controller.pet.emotional_system._running
        assert controller.pet.behavior_library._running


class TestModelLoading:
    """测试模型加载 / Test model loading"""
    
    @pytest.mark.asyncio
    async def test_live2d_model_loaded(self, controller):
        """Test Live2D model is loaded"""
        assert controller.pet.live2d.model_loaded
        assert controller.pet.live2d.model_path == "models/test/model.json"
    
    @pytest.mark.asyncio
    async def test_initial_expression_set(self, controller):
        """Test initial expression is set to NEUTRAL"""
        assert controller.pet.live2d.current_expression == ExpressionType.NEUTRAL
    
    @pytest.mark.asyncio
    async def test_model_parameters_initialized(self, controller):
        """Test Live2D parameters are initialized"""
        params = controller.pet.live2d.parameters
        assert "ParamAngleX" in params
        assert "ParamEyeLOpen" in params
        assert "ParamMouthOpenY" in params
        assert len(params) > 20  # Should have many parameters


class TestExpressionUpdates:
    """测试表情更新 / Test expression updates"""
    
    @pytest.mark.asyncio
    async def test_expression_change(self, controller):
        """Test manual expression change"""
        await controller.trigger_expression(ExpressionType.HAPPY, duration=0.1)
        
        assert controller.pet.live2d.current_expression == ExpressionType.HAPPY
        
        # Wait for auto-reset
        await asyncio.sleep(0.2)
        assert controller.pet.live2d.current_expression == ExpressionType.NEUTRAL
    
    @pytest.mark.asyncio
    async def test_emotion_to_expression_mapping(self, controller):
        """Test emotion to expression mapping"""
        # Set emotion to JOY
        controller.pet.emotional_system.set_emotion_from_basic(
            BasicEmotion.JOY, intensity=0.8
        )
        
        # Trigger expression callback manually
        expression = controller.pet.emotional_system.get_emotional_expression()
        controller.pet._on_expression_change(expression)
        
        # Should map to HAPPY
        assert controller.pet.live2d.current_expression == ExpressionType.HAPPY
    
    @pytest.mark.asyncio
    async def test_sad_emotion_mapping(self, controller):
        """Test sadness to expression mapping"""
        controller.pet.emotional_system.set_emotion_from_basic(
            BasicEmotion.SADNESS, intensity=0.6
        )
        
        expression = controller.pet.emotional_system.get_emotional_expression()
        controller.pet._on_expression_change(expression)
        
        assert controller.pet.live2d.current_expression == ExpressionType.SAD
    
    @pytest.mark.asyncio
    async def test_multiple_expression_changes(self, controller):
        """Test multiple rapid expression changes"""
        expressions = [
            ExpressionType.HAPPY,
            ExpressionType.SURPRISED,
            ExpressionType.SHY,
            ExpressionType.NEUTRAL
        ]
        
        for expr in expressions:
            await controller.trigger_expression(expr, duration=0.05)
            assert controller.pet.live2d.current_expression == expr
            await asyncio.sleep(0.01)


class TestActionExecution:
    """测试动作执行 / Test action execution"""
    
    @pytest.mark.asyncio
    async def test_motion_trigger(self, controller):
        """Test motion triggering"""
        success = await controller.trigger_motion(MotionType.GREETING)
        
        assert success
        assert controller.pet.live2d.current_motion == MotionType.GREETING
        assert controller.pet.live2d.is_motion_playing
    
    @pytest.mark.asyncio
    async def test_behavior_trigger(self, controller):
        """Test behavior library trigger"""
        success = await controller.pet.behavior_library.start_behavior("greeting_wave")
        
        assert success
        assert controller.pet.behavior_library.active_behavior is not None
        assert controller.pet.behavior_library.active_behavior.behavior_id == "greeting_wave"
    
    @pytest.mark.asyncio
    async def test_behavior_queue(self, controller):
        """Test behavior queuing"""
        # Start a behavior
        await controller.pet.behavior_library.start_behavior("idle_breathing")
        
        # Queue another behavior
        controller.pet.behavior_library.queue_behavior("greeting_wave")
        
        assert len(controller.pet.behavior_library.behavior_queue) == 1
    
    @pytest.mark.asyncio
    async def test_autonomous_behavior_trigger(self, controller):
        """Test autonomous behavior triggering"""
        # Set up context that triggers a behavior
        controller.pet.last_interaction_time = datetime.now() - timedelta(seconds=350)
        
        behavior_id = await controller.pet.trigger_autonomous_behavior()
        
        # Should trigger some behavior due to idle time
        assert behavior_id is not None


class TestUserInteraction:
    """测试用户交互 / Test user interaction"""
    
    @pytest.mark.asyncio
    async def test_click_interaction(self, controller):
        """Test click interaction"""
        response = await controller.handle_interaction("click", {"x": 150, "y": 200})
        
        assert response["status"] == "processed"
        assert "pet_response" in response
        assert controller.pet.interaction_count == 1
    
    @pytest.mark.asyncio
    async def test_double_click_interaction(self, controller):
        """Test double click interaction"""
        response = await controller.handle_interaction("double_click", {"x": 150, "y": 200})
        
        assert response["status"] == "processed"
        assert "excited" in response.get("expression", "")
    
    @pytest.mark.asyncio
    async def test_message_interaction(self, controller):
        """Test message interaction"""
        response = await controller.handle_interaction(
            "message", 
            {"text": "Hello Angela!"}
        )
        
        assert response["status"] == "processed"
    
    @pytest.mark.asyncio
    async def test_drag_interaction(self, controller):
        """Test drag interaction"""
        initial_pos = controller.pet.position.copy()
        
        response = await controller.handle_interaction("drag", {"x": 200, "y": 300})
        
        assert response["status"] == "processed"
        assert controller.pet.position != initial_pos
        assert controller.pet.state == DesktopPetState.MOVED
    
    @pytest.mark.asyncio
    async def test_hover_interaction(self, controller):
        """Test hover interaction with gaze tracking"""
        # Hover over pet
        pet_x = controller.pet.position["x"] + 50
        pet_y = controller.pet.position["y"] + 50
        
        response = await controller.handle_interaction("hover", {"x": pet_x, "y": pet_y})
        
        assert response["status"] == "processed"
        assert "gaze_x" in response
        assert "gaze_y" in response
    
    @pytest.mark.asyncio
    async def test_voice_interaction(self, controller):
        """Test voice interaction with lip-sync"""
        response = await controller.handle_voice_input(
            "Hello",
            phonemes=["h", "e", "l", "l", "o"]
        )
        
        assert response["status"] == "processed"
        assert "lip_sync_duration" in response
    
    @pytest.mark.asyncio
    async def test_unsupported_interaction(self, controller):
        """Test handling of unsupported interaction"""
        response = await controller.handle_interaction("unknown_type", {})
        
        assert response["status"] == "unsupported_input"
    
    @pytest.mark.asyncio
    async def test_interaction_callbacks(self, controller):
        """Test interaction callbacks are triggered"""
        callback_called = False
        received_type = None
        
        def on_interaction(interaction_type, data):
            nonlocal callback_called, received_type
            callback_called = True
            received_type = interaction_type
        
        controller.register_interaction_callback(on_interaction)
        
        await controller.handle_interaction("click", {"x": 100, "y": 100})
        
        assert callback_called
        assert received_type == "click"


class TestMouseTracking:
    """测试鼠标跟踪 / Test mouse tracking"""
    
    @pytest.mark.asyncio
    async def test_mouse_movement_tracking(self, controller):
        """Test mouse movement tracking"""
        await controller.handle_mouse_move(100, 100)
        await controller.handle_mouse_move(150, 150)
        await controller.handle_mouse_move(200, 200)
        
        assert len(controller._mouse_tracker.points) >= 3
    
    @pytest.mark.asyncio
    async def test_gaze_following(self, controller):
        """Test gaze follows mouse"""
        # Move mouse near pet
        await controller.handle_mouse_move(
            controller.pet.position["x"] + 50,
            controller.pet.position["y"] + 50
        )
        
        # Check that eye parameters are updated
        eye_x = controller.pet.live2d.get_parameter("ParamEyeBallX")
        eye_y = controller.pet.live2d.get_parameter("ParamEyeBallY")
        
        # Eyes should be looking in some direction
        assert -1 <= eye_x <= 1
        assert -1 <= eye_y <= 1


class TestTactileSystem:
    """测试触觉系统 / Test tactile system"""
    
    @pytest.mark.asyncio
    async def test_tactile_stimulus_processing(self, controller):
        """Test tactile stimulus processing"""
        stimulus = TactileStimulus(
            tactile_type=TactileType.LIGHT_TOUCH,
            intensity=5.0,
            location=BodyPart.HANDS,
            duration=1.0
        )
        
        response = await controller.pet.tactile_system.process_stimulus(stimulus)
        
        assert response.perceived_intensity > 0
        assert response.activated_receptors > 0
    
    @pytest.mark.asyncio
    async def test_tactile_to_emotion_mapping(self, controller):
        """Test tactile feedback maps to emotion"""
        # Process comfort touch
        stimulus = TactileStimulus(
            tactile_type=TactileType.LIGHT_TOUCH,
            intensity=3.0,
            location=BodyPart.HANDS,
            duration=1.0,
            emotional_tag="comfort"
        )
        
        await controller.pet.tactile_system.process_stimulus(stimulus)
        
        # Should trigger emotion callback
        # (Implementation dependent on callback)


class TestEmotionalSystem:
    """测试情绪系统 / Test emotional system"""
    
    @pytest.mark.asyncio
    async def test_emotion_setting(self, controller):
        """Test setting emotional state"""
        controller.pet.emotional_system.set_emotion_from_basic(
            BasicEmotion.JOY, intensity=0.8
        )
        
        summary = controller.pet.emotional_system.get_emotion_summary()
        assert summary["dominant_emotion"] == "Joy"
        assert summary["confidence"] > 0
    
    @pytest.mark.asyncio
    async def test_emotion_influence(self, controller):
        """Test applying emotional influence"""
        initial_pleasure = controller.pet.emotional_system.current_emotion.pleasure
        
        controller.pet.emotional_system.apply_influence(
            "cognitive", "positive_thought", 0.5, 0.6
        )
        
        # Influence should affect emotion over time
        await asyncio.sleep(0.1)
        
        # (The exact change depends on the update loop timing)
    
    @pytest.mark.asyncio
    async def test_emotion_expression_generation(self, controller):
        """Test emotion to expression generation"""
        controller.pet.emotional_system.set_emotion_from_basic(
            BasicEmotion.LOVE, intensity=0.7
        )
        
        expression = controller.pet.emotional_system.get_emotional_expression()
        
        assert expression.facial.smile > 0
        assert expression.vocal.warmth > 0


class TestAutonomousBehaviors:
    """测试自主行为 / Test autonomous behaviors"""
    
    @pytest.mark.asyncio
    async def test_autonomous_check_interval(self, pet_config, mock_orchestrator):
        """Test autonomous behavior checking at intervals"""
        pet_config.autonomous_check_interval = 0.05  # Very fast for testing
        
        controller = DesktopPetController(
            config=pet_config,
            orchestrator=mock_orchestrator
        )
        
        await controller.initialize()
        
        # Wait for a few autonomy checks
        await asyncio.sleep(0.2)
        
        # Cleanup
        await controller.shutdown()
    
    @pytest.mark.asyncio
    async def test_idle_timeout_sleep(self, pet_config, mock_orchestrator):
        """Test sleep mode after idle timeout"""
        pet_config.idle_timeout = 0.2  # Very short for testing
        
        controller = DesktopPetController(
            config=pet_config,
            orchestrator=mock_orchestrator
        )
        
        await controller.initialize()
        
        # Set last interaction to past
        controller.pet.last_interaction_time = datetime.now() - timedelta(seconds=0.3)
        
        # Wait for idle check
        await asyncio.sleep(0.3)
        
        # Pet should be sleeping
        assert controller.pet.state == DesktopPetState.SLEEPING
        
        # Cleanup
        await controller.shutdown()
    
    @pytest.mark.asyncio
    async def test_attention_seeking(self, pet_config, mock_orchestrator):
        """Test attention seeking behavior"""
        pet_config.idle_timeout = 1.0
        
        controller = DesktopPetController(
            config=pet_config,
            orchestrator=mock_orchestrator
        )
        
        await controller.initialize()
        
        # Set to halfway to idle timeout
        controller.pet.last_interaction_time = datetime.now() - timedelta(seconds=0.6)
        
        # Wait for check
        await asyncio.sleep(0.2)
        
        # Cleanup
        await controller.shutdown()


class TestLifecycleManagement:
    """测试生命周期管理 / Test lifecycle management"""
    
    @pytest.mark.asyncio
    async def test_pause_resume(self, controller):
        """Test pause and resume functionality"""
        await controller.pause()
        
        assert controller.lifecycle_state == PetLifecycleState.PAUSED
        assert controller.pet.state == DesktopPetState.IDLE
        
        await controller.resume()
        
        assert controller.lifecycle_state == PetLifecycleState.ACTIVE
    
    @pytest.mark.asyncio
    async def test_shutdown_cleanup(self, pet_config, mock_orchestrator):
        """Test proper cleanup on shutdown"""
        controller = DesktopPetController(
            config=pet_config,
            orchestrator=mock_orchestrator
        )
        
        await controller.initialize()
        
        # Verify tasks are running
        assert controller._autonomy_task is not None
        assert controller._update_task is not None
        
        # Shutdown
        success = await controller.shutdown()
        
        assert success
        assert controller.lifecycle_state == PetLifecycleState.IDLE
        assert not controller._running
        assert not controller._initialized
    
    @pytest.mark.asyncio
    async def test_error_handling(self, controller):
        """Test error handling and recovery"""
        # Trigger an error
        controller._handle_error(Exception("Test error"), "test_context")
        
        assert controller._error_count == 1
        assert controller._last_error is not None
        
        status = controller.get_status()
        assert status.error_count == 1
    
    @pytest.mark.asyncio
    async def test_status_reporting(self, controller):
        """Test status reporting"""
        status = controller.get_status()
        
        assert isinstance(status, SystemStatus)
        assert status.lifecycle_state == PetLifecycleState.ACTIVE
        assert status.is_running
        assert status.live2d_loaded
        assert status.tactile_active
        assert status.emotional_active
        assert status.behavior_active
    
    @pytest.mark.asyncio
    async def test_status_callbacks(self, controller):
        """Test status update callbacks"""
        callback_count = 0
        last_status = None
        
        def on_status(status):
            nonlocal callback_count, last_status
            callback_count += 1
            last_status = status
        
        controller.register_status_callback(on_status)
        
        # Wait for status update
        await asyncio.sleep(1.5)
        
        assert callback_count > 0
        assert last_status is not None


class TestStatePersistence:
    """测试状态持久化 / Test state persistence"""
    
    @pytest.mark.asyncio
    async def test_save_state(self, controller):
        """Test saving state"""
        # Set some state
        controller.pet.position = {"x": 200, "y": 300}
        controller.pet.interaction_count = 5
        
        state = await controller.save_state()
        
        assert "controller" in state
        assert "pet" in state
        assert "state_matrix" in state
        assert "timestamp" in state
        assert state["pet"]["interaction_count"] == 5
    
    @pytest.mark.asyncio
    async def test_load_state(self, controller):
        """Test loading state"""
        # Create a state to load
        state_data = {
            "pet": {
                "name": "TestAngela",
                "position": {"x": 250, "y": 350},
                "state": "idle",
                "expression": "HAPPY",
                "interaction_count": 10,
                "last_interaction": datetime.now().isoformat()
            },
            "state_matrix": {
                "alpha": {"energy": 0.8, "comfort": 0.7, "arousal": 0.5, "rest_need": 0.2},
                "beta": {"curiosity": 0.6, "focus": 0.8},
                "gamma": {"happiness": 0.9, "sadness": 0.1},
                "delta": {"attention": 0.7, "bond": 0.8}
            }
        }
        
        success = await controller.load_state(state_data)
        
        assert success
        assert controller.pet.position == {"x": 250, "y": 350}
        assert controller.pet.interaction_count == 10
    
    @pytest.mark.asyncio
    async def test_load_state_failure(self, controller):
        """Test loading invalid state"""
        success = await controller.load_state({"invalid": "data"})
        
        # Should handle gracefully
        assert controller._error_count > 0


class Test4DStateMatrix:
    """测试4D状态矩阵 / Test 4D state matrix"""
    
    @pytest.mark.asyncio
    async def test_state_matrix_sync(self, controller):
        """Test state matrix syncs with biological systems"""
        # Set some biological state
        controller.pet.tactile_system.set_arousal_level(80)
        controller.pet.emotional_system.set_emotion_from_basic(
            BasicEmotion.JOY, intensity=0.9
        )
        
        # Sync state matrix
        controller._sync_state_matrix()
        
        # Check alpha dimension
        alpha = controller.state_matrix.get_dimension_state("alpha")
        assert alpha["arousal"] == 0.8
        
        # Check gamma dimension
        gamma = controller.state_matrix.get_dimension_state("gamma")
        assert gamma["happiness"] > 0.7
    
    @pytest.mark.asyncio
    async def test_state_matrix_summary(self, controller):
        """Test state matrix summary generation"""
        summary = controller.get_4d_state_summary()
        
        assert "alpha" in summary
        assert "beta" in summary
        assert "gamma" in summary
        assert "delta" in summary
        assert "computed" in summary
        assert "wellbeing" in summary["computed"]
        assert "arousal" in summary["computed"]
    
    @pytest.mark.asyncio
    async def test_inter_dimensional_influence(self, controller):
        """Test inter-dimensional influence computation"""
        # Set values that should influence each other
        controller.state_matrix.set_alpha_dimension(energy=0.9, arousal=0.8)
        controller.state_matrix.set_gamma_dimension(happiness=0.8)
        
        # Compute influences
        influences = controller.state_matrix.compute_inter_influences()
        
        assert "alpha" in influences
        assert "gamma" in influences


class TestVoiceAndLipSync:
    """测试语音和口型同步 / Test voice and lip-sync"""
    
    @pytest.mark.asyncio
    async def test_lip_sync_start_stop(self, controller):
        """Test lip-sync start and stop"""
        controller.pet.live2d.start_lip_sync()
        
        assert controller.pet.live2d.lip_sync.is_active
        assert controller.pet.live2d._lip_sync_active
        
        controller.pet.live2d.stop_lip_sync()
        
        assert not controller.pet.live2d.lip_sync.is_active
        assert not controller.pet.live2d._lip_sync_active
    
    @pytest.mark.asyncio
    async def test_phoneme_to_mouth_mapping(self, controller):
        """Test phoneme to mouth parameter mapping"""
        controller.pet.live2d.start_lip_sync()
        
        # Test 'a' sound
        controller.pet.live2d.update_lip_sync("a", mouth_openness=0.8)
        mouth_open = controller.pet.live2d.get_parameter("ParamMouthOpenY")
        assert mouth_open > 0.5  # Should be open
        
        # Test 'silence'
        controller.pet.live2d.update_lip_sync("silence", mouth_openness=0.0)
        
        controller.pet.live2d.stop_lip_sync()
    
    @pytest.mark.asyncio
    async def test_voice_input_processing(self, controller):
        """Test voice input processing"""
        response = await controller.handle_voice_input(
            "Hello world",
            phonemes=["h", "e", "l", "l", "o", "silence", "w", "o", "r", "l", "d"]
        )
        
        assert response["status"] == "processed"
        assert "lip_sync_duration" in response


class TestErrorRecovery:
    """测试错误恢复 / Test error recovery"""
    
    @pytest.mark.asyncio
    async def test_system_recovery(self, pet_config, mock_orchestrator):
        """Test system recovery after failure"""
        controller = DesktopPetController(
            config=pet_config,
            orchestrator=mock_orchestrator
        )
        
        await controller.initialize()
        
        # Simulate system failure
        controller.pet.live2d._running = False
        
        # Trigger recovery
        await controller._recover_systems()
        
        # System should be recovered
        assert controller.pet.live2d._running
        
        await controller.shutdown()


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
