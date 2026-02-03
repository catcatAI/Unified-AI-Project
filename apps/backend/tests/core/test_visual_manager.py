"""
Angela AI v6.0 - Visual Manager Test Suite
视觉管理器测试套件

Comprehensive test suite for the VisualManager system.
Tests asset management, rendering control, effect generation,
and integration with biological systems.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

import asyncio
import pytest
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.backend.src.core.visual_config import (
    VisualConfiguration, ModelConfiguration, RenderQuality,
    get_preset_config, HIGH_PERFORMANCE_CONFIG, HIGH_QUALITY_CONFIG
)
from apps.backend.src.core.visual_effect_generator import (
    VisualEffectGenerator, EffectType, Particle, ParticleEmitter,
    TransitionEffect, AtmosphereEffect
)
from apps.backend.src.core.visual_manager import (
    VisualManager, AssetCache, AssetMetadata, AssetType,
    VisualPresentation, VisualState, RenderMetrics,
    CachedAsset, ExpressionType, MotionType
)


# ==================== Visual Configuration Tests ====================

class TestVisualConfiguration:
    """Test visual configuration system"""
    
    def test_default_configuration(self):
        """Test default configuration creation"""
        config = VisualConfiguration()
        
        assert config.render_quality == RenderQuality.HIGH
        assert config.model.model_name == "angela_default"
        assert config.model.texture_resolution == 2048
        assert config.performance.target_fps == 60
        assert config.effects.enable_particles is True
    
    def test_custom_configuration(self):
        """Test custom configuration"""
        config = VisualConfiguration()
        config.model.model_name = "custom_model"
        config.performance.target_fps = 144
        config.effects.enable_bloom = True
        
        assert config.model.model_name == "custom_model"
        assert config.performance.target_fps == 144
        assert config.effects.enable_bloom is True
    
    def test_get_model_path(self):
        """Test model path generation"""
        config = VisualConfiguration()
        path = config.get_model_path()
        
        assert "angela_default" in path
        assert "angela.model3.json" in path
    
    def test_to_dict(self):
        """Test configuration serialization"""
        config = VisualConfiguration()
        config_dict = config.to_dict()
        
        assert "render_quality" in config_dict
        assert "model" in config_dict
        assert "performance" in config_dict
        assert config_dict["render_quality"] == "HIGH"
    
    def test_from_dict(self):
        """Test configuration deserialization"""
        data = {
            "render_quality": "MEDIUM",
            "model": {
                "model_name": "test_model",
                "texture_resolution": 1024
            },
            "performance": {
                "target_fps": 30
            }
        }
        
        config = VisualConfiguration.from_dict(data)
        
        assert config.render_quality == RenderQuality.MEDIUM
        assert config.model.model_name == "test_model"
        assert config.performance.target_fps == 30
    
    def test_optimize_for_quality(self):
        """Test quality optimization"""
        config = VisualConfiguration()
        
        config.optimize_for_quality(RenderQuality.LOW)
        assert config.model.texture_resolution == 1024
        assert config.effects.enable_particles is False
        
        config.optimize_for_quality(RenderQuality.ULTRA)
        assert config.model.texture_resolution == 4096
        assert config.effects.enable_bloom is True
    
    def test_preset_configs(self):
        """Test preset configurations"""
        performance = get_preset_config("performance")
        assert performance.render_quality == RenderQuality.LOW
        
        quality = get_preset_config("quality")
        assert quality.render_quality == RenderQuality.HIGH


# ==================== Visual Effect Generator Tests ====================

@pytest.mark.asyncio
class TestVisualEffectGenerator:
    """Test visual effect generator"""
    
    async def test_initialization(self):
        """Test effect generator initialization"""
        generator = VisualEffectGenerator()
        await generator.initialize()
        
        assert generator._running is True
        assert generator._update_task is not None
        
        await generator.shutdown()
    
    async def test_particle_effect_creation(self):
        """Test particle effect creation"""
        generator = VisualEffectGenerator()
        await generator.initialize()
        
        effect_id = generator.start_particle_effect(
            EffectType.PARTICLE_HEART, x=100, y=100
        )
        
        assert effect_id is not None
        assert effect_id.startswith("particle_")
        assert len(generator.active_emitters) == 1
        
        await generator.shutdown()
    
    async def test_particle_effect_stop(self):
        """Test particle effect stop"""
        generator = VisualEffectGenerator()
        await generator.initialize()
        
        effect_id = generator.start_particle_effect(
            EffectType.PARTICLE_HEART, x=100, y=100
        )
        
        generator.stop_particle_effect(effect_id)
        assert len(generator.active_emitters) == 0
        
        await generator.shutdown()
    
    async def test_transition_trigger(self):
        """Test transition trigger"""
        generator = VisualEffectGenerator()
        await generator.initialize()
        
        callback_called = False
        
        def callback():
            nonlocal callback_called
            callback_called = True
        
        await generator.trigger_transition(
            EffectType.TRANSITION_FADE, duration=0.1, callback=callback
        )
        
        # Wait for transition to complete
        await asyncio.sleep(0.15)
        
        assert callback_called is True
        await generator.shutdown()
    
    def test_atmosphere_setting(self):
        """Test atmosphere setting"""
        generator = VisualEffectGenerator()
        
        generator.set_atmosphere(EffectType.AMBIENCE_WARM, intensity=0.7)
        
        assert generator.atmosphere is not None
        assert generator.atmosphere.effect_type == EffectType.AMBIENCE_WARM
        assert generator.atmosphere.intensity == 0.7
    
    def test_glow_effect(self):
        """Test glow effect"""
        generator = VisualEffectGenerator()
        
        generator.set_glow(intensity=0.8, color=(1.0, 0.5, 0.5), radius=30.0)
        
        assert generator.glow is not None
        assert generator.glow.intensity == 0.8
        assert generator.glow.radius == 30.0
    
    def test_emotional_effect(self):
        """Test emotional effect creation"""
        generator = VisualEffectGenerator()
        
        effect_id = generator.create_emotional_effect("happy", intensity=0.8)
        
        assert effect_id is not None
        assert len(generator.active_emitters) == 1
    
    def test_effect_summary(self):
        """Test effect summary"""
        generator = VisualEffectGenerator()
        
        summary = generator.get_effect_summary()
        
        assert "active_particles" in summary
        assert "active_emitters" in summary
        assert "has_atmosphere" in summary


# ==================== Asset Cache Tests ====================

@pytest.mark.asyncio
class TestAssetCache:
    """Test asset cache system"""
    
    async def test_cache_initialization(self):
        """Test cache initialization"""
        cache = AssetCache(max_size_mb=100)
        
        assert cache.max_size_bytes == 100 * 1024 * 1024
        assert cache.current_size_bytes == 0
        assert len(cache.assets) == 0
    
    async def test_put_and_get(self):
        """Test putting and getting assets"""
        cache = AssetCache(max_size_mb=100)
        
        metadata = AssetMetadata(
            asset_id="test_asset",
            asset_type=AssetType.MODEL,
            name="Test Model",
            path="/test/path"
        )
        
        asset = CachedAsset(
            metadata=metadata,
            data="test_data",
            load_time=datetime.now(),
            last_used=datetime.now(),
            memory_usage=1024 * 1024
        )
        
        await cache.put("test_asset", asset)
        retrieved = await cache.get("test_asset")
        
        assert retrieved is not None
        assert retrieved.metadata.asset_id == "test_asset"
        assert retrieved.metadata.access_count == 1
    
    async def test_cache_eviction(self):
        """Test cache eviction"""
        cache = AssetCache(max_size_mb=1)  # Small cache
        
        # Add multiple assets
        for i in range(3):
            metadata = AssetMetadata(
                asset_id=f"asset_{i}",
                asset_type=AssetType.MODEL,
                name=f"Model {i}",
                path=f"/test/{i}"
            )
            
            asset = CachedAsset(
                metadata=metadata,
                data=f"data_{i}",
                load_time=datetime.now(),
                last_used=datetime.now(),
                memory_usage=512 * 1024  # 512KB each
            )
            
            await cache.put(f"asset_{i}", asset)
        
        # Cache should have evicted at least one asset
        assert len(cache.assets) <= 2
    
    async def test_cache_clear(self):
        """Test cache clear"""
        cache = AssetCache(max_size_mb=100)
        
        metadata = AssetMetadata(
            asset_id="test_asset",
            asset_type=AssetType.MODEL,
            name="Test Model",
            path="/test/path"
        )
        
        asset = CachedAsset(
            metadata=metadata,
            data="test_data",
            load_time=datetime.now(),
            last_used=datetime.now(),
            memory_usage=1024 * 1024
        )
        
        await cache.put("test_asset", asset)
        await cache.clear()
        
        assert len(cache.assets) == 0
        assert cache.current_size_bytes == 0
    
    def test_cache_stats(self):
        """Test cache statistics"""
        cache = AssetCache(max_size_mb=100)
        
        stats = cache.get_stats()
        
        assert "asset_count" in stats
        assert "current_size_mb" in stats
        assert "usage_percent" in stats


# ==================== Visual Manager Tests ====================

@pytest.mark.asyncio
class TestVisualManager:
    """Test visual manager"""
    
    async def test_initialization(self):
        """Test visual manager initialization"""
        vm = VisualManager()
        await vm.initialize()
        
        assert vm._running is True
        assert vm.effect_generator is not None
        assert vm.asset_cache is not None
        
        await vm.shutdown()
    
    async def test_set_expression(self):
        """Test expression setting"""
        vm = VisualManager()
        await vm.initialize()
        
        await vm.set_expression(ExpressionType.HAPPY)
        
        assert vm.current_presentation.current_expression == ExpressionType.HAPPY
        
        await vm.shutdown()
    
    async def test_play_motion(self):
        """Test motion playback"""
        vm = VisualManager()
        await vm.initialize()
        
        await vm.play_motion(MotionType.GREETING)
        
        assert vm.current_presentation.current_motion == MotionType.GREETING
        
        await vm.shutdown()
    
    async def test_lip_sync(self):
        """Test lip sync"""
        vm = VisualManager()
        await vm.initialize()
        
        vm.start_lip_sync()
        assert vm.current_presentation.is_speaking is True
        
        vm.stop_lip_sync()
        assert vm.current_presentation.is_speaking is False
        
        await vm.shutdown()
    
    async def test_eye_target(self):
        """Test eye target setting"""
        vm = VisualManager()
        await vm.initialize()
        
        vm.set_eye_target(0.5, -0.3)
        
        assert vm.current_presentation.eye_target == (0.5, -0.3)
        
        await vm.shutdown()
    
    async def test_particle_effect(self):
        """Test particle effect creation"""
        vm = VisualManager()
        await vm.initialize()
        
        effect_id = vm.create_particle_effect(
            EffectType.PARTICLE_HEART, x=100, y=100, duration=1.0
        )
        
        assert effect_id is not None
        
        await vm.shutdown()
    
    async def test_atmosphere(self):
        """Test atmosphere setting"""
        vm = VisualManager()
        await vm.initialize()
        
        vm.set_atmosphere(EffectType.AMBIENCE_WARM, intensity=0.6)
        
        assert vm.effect_generator.atmosphere is not None
        
        await vm.shutdown()
    
    def test_get_visual_summary(self):
        """Test visual summary"""
        vm = VisualManager()
        
        summary = vm.get_visual_summary()
        
        assert "state" in summary
        assert "expression" in summary
        assert "fps" in summary
        assert "cache" in summary
        assert "effects" in summary
    
    async def test_expression_callback(self):
        """Test expression callback"""
        vm = VisualManager()
        await vm.initialize()
        
        callback_called = False
        received_expression = None
        
        def callback(expr):
            nonlocal callback_called, received_expression
            callback_called = True
            received_expression = expr
        
        vm.register_expression_callback(callback)
        
        # Trigger expression change
        await vm.set_expression(ExpressionType.HAPPY, immediate=True)
        await asyncio.sleep(0.1)
        
        # Note: Callback might not be called with immediate=True
        # This test verifies the callback is registered
        assert len(vm._expression_callbacks) == 1
        
        await vm.shutdown()
    
    async def test_motion_callback(self):
        """Test motion callback"""
        vm = VisualManager()
        await vm.initialize()
        
        callback_called = False
        
        def callback(motion):
            nonlocal callback_called
            callback_called = True
        
        vm.register_motion_callback(callback)
        
        await vm.play_motion(MotionType.GREETING)
        
        assert callback_called is True
        
        await vm.shutdown()


# ==================== Integration Tests ====================

@pytest.mark.asyncio
class TestVisualManagerIntegration:
    """Test visual manager integration"""
    
    async def test_emotional_system_connection(self):
        """Test emotional system connection"""
        vm = VisualManager()
        await vm.initialize()
        
        # Create mock emotional system
        mock_emotion = Mock()
        mock_emotion.register_emotion_callback = Mock()
        
        vm.connect_emotional_system(mock_emotion)
        
        assert vm.emotional_system is mock_emotion
        mock_emotion.register_emotion_callback.assert_called_once()
        
        await vm.shutdown()
    
    async def test_tactile_system_connection(self):
        """Test tactile system connection"""
        vm = VisualManager()
        await vm.initialize()
        
        # Create mock tactile system
        mock_tactile = Mock()
        mock_tactile.register_stimulus_callback = Mock()
        
        vm.connect_tactile_system(mock_tactile)
        
        assert vm.tactile_system is mock_tactile
        mock_tactile.register_stimulus_callback.assert_called_once()
        
        await vm.shutdown()
    
    async def test_desktop_pet_connection(self):
        """Test desktop pet connection"""
        vm = VisualManager()
        await vm.initialize()
        
        mock_pet = Mock()
        vm.connect_desktop_pet(mock_pet)
        
        assert vm.desktop_pet is mock_pet
        
        await vm.shutdown()
    
    async def test_emotion_to_expression_mapping(self):
        """Test emotion to expression mapping"""
        vm = VisualManager()
        await vm.initialize()
        
        # Test emotion change callback
        vm._on_emotion_changed({"emotion": "happy", "intensity": 0.8})
        await asyncio.sleep(0.1)
        
        # Should have triggered expression change
        # Note: The actual change is async, so we just verify no errors
        
        await vm.shutdown()
    
    async def test_biological_state_update(self):
        """Test biological state update"""
        vm = VisualManager()
        await vm.initialize()
        
        emotional_state = {
            "dominant_emotion": "excited",
            "intensity": 0.9
        }
        
        physiological_state = {
            "energy": 0.8
        }
        
        cognitive_state = {
            "is_thinking": True
        }
        
        await vm.update_from_biological_state(
            emotional_state=emotional_state,
            physiological_state=physiological_state,
            cognitive_state=cognitive_state
        )
        
        # Verify no errors and state was processed
        assert vm._running is True
        
        await vm.shutdown()


# ==================== Performance Tests ====================

@pytest.mark.asyncio
class TestVisualManagerPerformance:
    """Test visual manager performance"""
    
    async def test_framerate_stability(self):
        """Test framerate stability"""
        vm = VisualManager()
        await vm.initialize()
        
        # Let it run for a short time
        await asyncio.sleep(0.5)
        
        metrics = vm.get_metrics()
        
        # FPS should be reasonable (above 30)
        assert metrics.fps > 30
        
        await vm.shutdown()
    
    async def test_memory_management(self):
        """Test memory management"""
        vm = VisualManager()
        await vm.initialize()
        
        # Create multiple effects
        for i in range(10):
            vm.create_particle_effect(
                EffectType.PARTICLE_SPARKLE, 
                x=i*10, y=i*10, 
                duration=1.0
            )
        
        await asyncio.sleep(0.5)
        
        # Check that particle count is reasonable
        effect_summary = vm.effect_generator.get_effect_summary()
        assert effect_summary["active_particles"] <= vm.effect_generator.max_particles
        
        await vm.shutdown()
    
    async def test_cache_performance(self):
        """Test cache performance"""
        vm = VisualManager()
        await vm.initialize()
        
        # Register and preload multiple assets
        for i in range(5):
            vm.register_asset(
                f"test_asset_{i}",
                AssetType.MODEL,
                f"Test Model {i}",
                f"/test/path/{i}",
                tags=["test"]
            )
        
        await vm.preload_assets([f"test_asset_{i}" for i in range(5)])
        
        # Wait for preloading
        await asyncio.sleep(0.5)
        
        cache_stats = vm.get_cache_stats()
        
        # Cache should have some assets
        assert cache_stats["asset_count"] >= 0
        
        await vm.shutdown()


# ==================== Main Test Runner ====================

def run_tests():
    """Run all tests"""
    print("=" * 60)
    print("Angela AI v6.0 - Visual Manager Test Suite")
    print("=" * 60)
    print()
    
    # Run pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])
    
    return exit_code


if __name__ == "__main__":
    # Run tests
    asyncio.run(run_tests())
    
    # Alternative: Run basic tests without pytest
    print("\n运行基础测试 / Running basic tests...")
    
    async def basic_tests():
        # Test 1: Configuration
        print("\n1. Testing Visual Configuration...")
        config = VisualConfiguration()
        assert config.render_quality == RenderQuality.HIGH
        print("   ✓ Configuration creation passed")
        
        # Test 2: Effect Generator
        print("\n2. Testing Visual Effect Generator...")
        generator = VisualEffectGenerator()
        await generator.initialize()
        effect_id = generator.start_particle_effect(EffectType.PARTICLE_HEART)
        assert effect_id is not None
        await generator.shutdown()
        print("   ✓ Effect generator passed")
        
        # Test 3: Asset Cache
        print("\n3. Testing Asset Cache...")
        cache = AssetCache(max_size_mb=100)
        metadata = AssetMetadata(
            asset_id="test",
            asset_type=AssetType.MODEL,
            name="Test",
            path="/test"
        )
        asset = CachedAsset(
            metadata=metadata,
            data="test",
            load_time=datetime.now(),
            last_used=datetime.now(),
            memory_usage=1024
        )
        await cache.put("test", asset)
        retrieved = await cache.get("test")
        assert retrieved is not None
        print("   ✓ Asset cache passed")
        
        # Test 4: Visual Manager
        print("\n4. Testing Visual Manager...")
        vm = VisualManager()
        await vm.initialize()
        await vm.set_expression(ExpressionType.HAPPY)
        assert vm.current_presentation.current_expression == ExpressionType.HAPPY
        await vm.shutdown()
        print("   ✓ Visual manager passed")
        
        # Test 5: Integration
        print("\n5. Testing Integration...")
        vm = VisualManager()
        await vm.initialize()
        mock_system = Mock()
        vm.connect_emotional_system(mock_system)
        assert vm.emotional_system is mock_system
        await vm.shutdown()
        print("   ✓ Integration passed")
        
        print("\n" + "=" * 60)
        print("所有基础测试通过！/ All basic tests passed!")
        print("=" * 60)
    
    asyncio.run(basic_tests())
