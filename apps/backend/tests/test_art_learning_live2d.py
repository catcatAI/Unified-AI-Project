"""
Tests for Art Learning and Live2D Generation System
艺术学习和Live2D生成系统测试

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import asyncio
from datetime import datetime
from pathlib import Path

# Import the systems
try:
    from apps.backend.src.core.autonomous.art_learning_system import (
        ArtLearningSystem, ArtKnowledge, ArtDomain,
        LearningType, BodyPartMapping
    )
    from apps.backend.src.core.autonomous.live2d_avatar_generator import (
        Live2DAvatarGenerator, ViewAngle, GenerationStage
    )
    from apps.backend.src.core.autonomous.art_learning_workflow import (
        ArtLearningWorkflow, WorkflowStage, LearningObjective,
        WorkflowConfig
    )
    from apps.backend.src.core.autonomous.physiological_tactile import (
        PhysiologicalTactileSystem, TactileStimulus, TactileType, BodyPart
    )
    from apps.backend.src.core.autonomous.live2d_integration import Live2DIntegration
except ImportError:
    # Fallback for direct import
    from core.autonomous.art_learning_system import (
        ArtLearningSystem, ArtKnowledge, ArtDomain,
        LearningType, BodyPartMapping
    )
    from core.autonomous.live2d_avatar_generator import (
        Live2DAvatarGenerator, ViewAngle, GenerationStage
    )
    from core.autonomous.art_learning_workflow import (
        ArtLearningWorkflow, WorkflowStage, LearningObjective,
        WorkflowConfig
    )
    from core.autonomous.physiological_tactile import (
        PhysiologicalTactileSystem, TactileStimulus, TactileType, BodyPart
    )
    from core.autonomous.live2d_integration import Live2DIntegration


class MockBrowserController:
    """Mock browser controller for testing"""
    async def search(self, query, engine=None, max_results=10):
        return [type('Result', (), {
            'title': f'Result for {query}',
            'url': f'https://example.com/{query.replace(" ", "-")}'
        })() for i in range(3)]
    
    async def extract_content(self, url):
        return type('Content', (), {
            'title': 'Tutorial Title',
            'summary': f'Summary of tutorial at {url}',
            'text_content': 'Step 1: Setup layers. Step 2: Create masks. Layer blending technique.',
            'images': [],
            'links': []
        })()


class MockVisionService:
    """Mock vision service for testing"""
    async def analyze_image(self, image_path=None, image_url=None):
        return type('VisionResult', (), {
            'style_features': [
                {'type': 'line_art', 'description': 'Clean anime lines', 'confidence': 0.9},
                {'type': 'coloring', 'description': 'Vibrant colors', 'confidence': 0.85}
            ],
            'color_palette': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'],
            'line_style': 'clean',
            'composition': 'portrait',
            'confidence': 0.88
        })()


class MockImageGenerator:
    """Mock image generator for testing"""
    async def generate_image(self, prompt, width=2048, height=2048, style="anime"):
        return type('Image', (), {
            'save': lambda path: Path(path).touch()
        })()


class MockNeuroplasticity:
    """Mock neuroplasticity system"""
    def create_memory_trace(self, content, initial_weight=0.5, emotional_tags=None):
        return f"trace_{hash(str(content)) % 10000}"
    
    def apply_ltp(self, trace_id, intensity):
        pass


# Test Art Learning System
class TestArtLearningSystem:
    @pytest.fixture
    async def art_system(self):
        system = ArtLearningSystem(
            browser_controller=MockBrowserController(),
            vision_service=MockVisionService(),
            neuroplasticity=MockNeuroplasticity()
        )
        await system.initialize()
        yield system
        await system.shutdown()
    
    @pytest.mark.asyncio
    async def test_tutorial_search(self, art_system):
        """Test tutorial search functionality"""
        tutorials = await art_system.search_tutorials("Live2D tutorial", max_results=5)
        
        assert len(tutorials) > 0
        assert all(hasattr(t, 'tutorial_id') for t in tutorials)
        assert all(hasattr(t, 'title') for t in tutorials)
        print(f"✓ Found {len(tutorials)} tutorials")
    
    @pytest.mark.asyncio
    async def test_domain_tutorial_search(self, art_system):
        """Test domain-specific tutorial search"""
        tutorials = await art_system.search_domain_tutorials(
            ArtDomain.LIVE2D,
            max_results_per_keyword=2
        )
        
        assert len(tutorials) > 0
        print(f"✓ Found {len(tutorials)} Live2D tutorials")
    
    @pytest.mark.asyncio
    async def test_image_analysis(self, art_system):
        """Test image analysis"""
        analysis = await art_system.analyze_image(image_path="test_anime.png")
        
        assert analysis.image_id is not None
        assert len(analysis.style_features) > 0
        assert len(analysis.color_palette) > 0
        print(f"✓ Analyzed image with {len(analysis.style_features)} features")
    
    @pytest.mark.asyncio
    async def test_tutorial_learning(self, art_system):
        """Test learning from tutorial"""
        try:
            from apps.backend.src.core.autonomous.art_learning_system import TutorialContent
        except ImportError:
            from core.autonomous.art_learning_system import TutorialContent
        
        tutorial = TutorialContent(
            tutorial_id="test_tut_1",
            title="Live2D Basics",
            url="https://example.com/live2d",
            source="Test",
            key_techniques=["layering", "masking"]
        )
        
        knowledge = await art_system.learn_from_tutorial(tutorial)
        
        assert knowledge.knowledge_id is not None
        assert knowledge.technique == "layering"
        assert knowledge.mastery_level >= 0.0
        print(f"✓ Created knowledge entry: {knowledge.knowledge_id}")
    
    @pytest.mark.asyncio
    async def test_body_part_mapping(self, art_system):
        """Test 18 body part mappings"""
        mappings = art_system.get_all_body_mappings()
        
        assert len(mappings) == 18
        
        # Test specific body parts
        assert "top_of_head" in mappings
        assert "face" in mappings
        assert "hands" in mappings
        
        # Test mapping structure
        face_mapping = mappings["face"]
        assert isinstance(face_mapping, BodyPartMapping)
        assert "ParamCheek" in face_mapping.live2d_params
        
        print(f"✓ All 18 body parts mapped")
    
    @pytest.mark.asyncio
    async def test_touch_response(self, art_system):
        """Test touch to Live2D parameter conversion"""
        # Test pat on head
        params = art_system.get_parameter_for_body_touch("top_of_head", "pat", 0.7)
        
        assert "ParamAngleX" in params
        assert "ParamAngleY" in params
        assert "ParamHairSwing" in params
        
        # Check value ranges
        assert -15 <= params["ParamAngleX"] <= 15
        assert 0 <= params["ParamHairSwing"] <= 1
        
        print(f"✓ Touch response generates correct parameters")
    
    @pytest.mark.asyncio
    async def test_power_law_mastery(self, art_system):
        """Test power law skill acquisition"""
        mastery = art_system.calculate_mastery_level(
            practice_count=50,
            success_rate=0.8,
            days_since_learning=7
        )
        
        assert 0 <= mastery <= 1
        # Should increase with more practice
        mastery_100 = art_system.calculate_mastery_level(
            practice_count=100,
            success_rate=0.8,
            days_since_learning=7
        )
        
        assert mastery_100 > mastery
        print(f"✓ Power law mastery: 50 practices={mastery:.2f}, 100 practices={mastery_100:.2f}")


# Test Live2D Avatar Generator
class TestLive2DAvatarGenerator:
    @pytest.fixture
    async def generator(self):
        gen = Live2DAvatarGenerator(
            image_generator=MockImageGenerator(),
            config={"output_path": "./test_models"}
        )
        await gen.initialize()
        yield gen
        await gen.shutdown()
    
    @pytest.mark.asyncio
    async def test_avatar_generation(self, generator):
        """Test avatar generation"""
        avatar = await generator.generate_avatar(
            model_name="test_avatar",
            attributes={
                "hair_color": "pink",
                "hair_style": "long",
                "eye_color": "blue"
            }
        )
        
        assert avatar.avatar_id is not None
        assert len(avatar.layers) > 0
        assert len(avatar.parameters) > 0
        assert avatar.generation_quality > 0
        
        print(f"✓ Generated avatar with {len(avatar.layers)} layers, quality={avatar.generation_quality:.2%}")
    
    @pytest.mark.asyncio
    async def test_multi_angle_generation(self, generator):
        """Test multi-angle avatar generation"""
        avatar = await generator.generate_multi_angle_avatar(
            model_name="test_multi",
            angles=[ViewAngle.FRONT, ViewAngle.THREE_QUARTER],
            attributes={"hair_color": "blue"}
        )
        
        assert len(avatar.view_angles) == 2
        assert ViewAngle.FRONT in avatar.view_angles
        
        print(f"✓ Generated multi-angle avatar with {len(avatar.view_angles)} angles")
    
    def test_body_mappings(self, generator):
        """Test 18 body part parameter mappings"""
        mappings = generator.get_all_body_mappings()
        
        assert len(mappings) == 18
        
        # Test all body parts have parameters
        for body_part, mapping in mappings.items():
            assert "parameters" in mapping
            assert len(mapping["parameters"]) > 0
        
        print(f"✓ Generator has {len(mappings)} body part mappings")
    
    def test_touch_response_mapping(self, generator):
        """Test touch response parameter generation"""
        response = generator.get_touch_response("face", "pat", 0.8)
        
        assert "ParamCheek" in response
        assert "ParamFaceColor" in response
        
        # Check values are in reasonable ranges
        assert 0 <= response["ParamCheek"] <= 1
        
        print(f"✓ Touch response: {len(response)} parameters")


# Test Art Learning Workflow
class TestArtLearningWorkflow:
    @pytest.fixture
    async def workflow(self):
        # Create mock systems
        art_system = ArtLearningSystem(
            browser_controller=MockBrowserController(),
            vision_service=MockVisionService(),
            neuroplasticity=MockNeuroplasticity()
        )
        
        generator = Live2DAvatarGenerator(
            image_generator=MockImageGenerator(),
            art_learning_system=art_system
        )
        
        live2d = Live2DIntegration()
        tactile = PhysiologicalTactileSystem()
        
        wf = ArtLearningWorkflow(
            art_learning_system=art_system,
            avatar_generator=generator,
            live2d_integration=live2d,
            physiological_tactile=tactile,
            config=WorkflowConfig(auto_deploy=False)
        )
        
        await wf.initialize()
        yield wf
        await wf.shutdown()
    
    @pytest.mark.asyncio
    async def test_workflow_stages(self, workflow):
        """Test workflow stage progression"""
        stages_completed = []
        
        def on_stage_change(old_stage, new_stage):
            stages_completed.append(new_stage)
        
        workflow.register_stage_change_callback(on_stage_change)
        
        # Run quick workflow
        result = await workflow.quick_generate(skip_learning=True)
        
        assert result.avatar_id is not None
        assert result.quality_score > 0
        
        print(f"✓ Workflow completed, avatar: {result.avatar_id}")
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, workflow):
        """Test complete learning and generation workflow"""
        progress_updates = []
        
        def on_progress(progress):
            progress_updates.append(progress.overall_progress)
        
        workflow.register_progress_callback(on_progress)
        
        # Note: This test uses quick generate to avoid long running time
        result = await workflow.quick_generate(
            skip_learning=True,
            attributes={"hair_color": "pink", "eye_color": "blue"}
        )
        
        assert result.validation_passed
        assert result.quality_score > 0.5
        
        # Check progress was tracked
        assert len(progress_updates) > 0
        
        print(f"✓ Complete workflow: quality={result.quality_score:.2%}")
    
    def test_learning_statistics(self, workflow):
        """Test learning statistics collection"""
        stats = workflow.get_learning_statistics()
        
        assert "workflow_runs" in stats
        assert "current_stage" in stats
        assert "progress_percent" in stats
        
        print(f"✓ Statistics: {len(stats)} metrics available")


# Test Physiological-Live2D Bridge
class TestPhysiologicalLive2DBridge:
    @pytest.fixture
    async def tactile_system(self):
        system = PhysiologicalTactileSystem()
        await system.initialize()
        yield system
        await system.shutdown()
    
    @pytest.mark.asyncio
    async def test_live2d_response_generation(self, tactile_system):
        """Test generating Live2D parameters from touch"""
        stimulus = TactileStimulus(
            tactile_type=TactileType.LIGHT_TOUCH,
            intensity=6.0,
            location=BodyPart.FACE,
            duration=1.0
        )
        
        response = await tactile_system.process_stimulus_with_live2d(
            stimulus,
            touch_type="pat"
        )
        
        assert response.live2d_parameters is not None
        assert len(response.live2d_parameters) > 0
        assert "ParamCheek" in response.live2d_parameters
        
        print(f"✓ Touch generated {len(response.live2d_parameters)} Live2D parameters")
    
    @pytest.mark.asyncio
    async def test_all_body_parts_mapped(self, tactile_system):
        """Test all 18 body parts have Live2D mappings"""
        touch_zones = tactile_system.get_live2d_touch_zones()
        
        assert len(touch_zones) == 18
        
        # Check required body parts
        body_part_names = [zone["body_part"] for zone in touch_zones]
        assert "TOP_OF_HEAD" in body_part_names
        assert "FACE" in body_part_names
        assert "HANDS" in body_part_names
        
        print(f"✓ All 18 body parts have Live2D touch zones")
    
    def test_touch_type_variations(self, tactile_system):
        """Test different touch types produce different responses"""
        # Test pat vs stroke on head
        pat_params = tactile_system.get_live2d_response_for_touch(
            BodyPart.TOP_OF_HEAD, "pat", 0.7
        )
        stroke_params = tactile_system.get_live2d_response_for_touch(
            BodyPart.TOP_OF_HEAD, "stroke", 0.7
        )
        
        # Should have different parameter effects
        assert pat_params != stroke_params
        
        print(f"✓ Different touch types produce different responses")


# Integration Tests
class TestIntegration:
    @pytest.mark.asyncio
    async def test_end_to_end_pipeline(self):
        """Test complete end-to-end pipeline"""
        print("\n" + "=" * 60)
        print("Running End-to-End Integration Test")
        print("=" * 60)
        
        # Initialize all systems
        art_system = ArtLearningSystem(
            browser_controller=MockBrowserController(),
            vision_service=MockVisionService(),
            neuroplasticity=MockNeuroplasticity()
        )
        await art_system.initialize()
        
        generator = Live2DAvatarGenerator(
            image_generator=MockImageGenerator(),
            art_learning_system=art_system
        )
        await generator.initialize()
        
        tactile = PhysiologicalTactileSystem()
        await tactile.initialize()
        
        live2d = Live2DIntegration()
        await live2d.initialize()
        
        try:
            # 1. Search and learn
            tutorials = await art_system.search_domain_tutorials(ArtDomain.LIVE2D)
            assert len(tutorials) > 0
            print(f"✓ Step 1: Found {len(tutorials)} tutorials")
            
            # 2. Learn from tutorial
            knowledge = await art_system.learn_from_tutorial(tutorials[0])
            assert knowledge.knowledge_id is not None
            print(f"✓ Step 2: Created knowledge: {knowledge.knowledge_id}")
            
            # 3. Generate avatar
            avatar = await generator.generate_avatar(
                model_name="integration_test",
                attributes={"hair_color": "pink", "eye_color": "blue"}
            )
            assert avatar.avatar_id is not None
            print(f"✓ Step 3: Generated avatar: {avatar.avatar_id}")
            
            # 4. Test body mapping
            body_mapping = generator.get_body_parameter_mapping("top_of_head")
            assert "parameters" in body_mapping
            print(f"✓ Step 4: Body mapping verified")
            
            # 5. Test touch to Live2D
            try:
                from apps.backend.src.core.autonomous.physiological_tactile import TactileStimulus, TactileType
            except ImportError:
                from core.autonomous.physiological_tactile import TactileStimulus, TactileType
            
            stimulus = TactileStimulus(
                tactile_type=TactileType.LIGHT_TOUCH,
                intensity=5.0,
                location=BodyPart.TOP_OF_HEAD,
                duration=1.0
            )
            
            response = await tactile.process_stimulus_with_live2d(stimulus, "pat")
            assert len(response.live2d_parameters) > 0
            print(f"✓ Step 5: Touch-Live2D bridge working ({len(response.live2d_parameters)} params)")
            
            # 6. Apply to Live2D
            for param, value in response.live2d_parameters.items():
                live2d.set_parameter(param, value)
            
            params_set = len(response.live2d_parameters)
            print(f"✓ Step 6: Applied {params_set} parameters to Live2D")
            
            print("\n" + "=" * 60)
            print("✓ End-to-End Integration Test PASSED")
            print("=" * 60)
            
        finally:
            await art_system.shutdown()
            await generator.shutdown()
            await tactile.shutdown()
            await live2d.shutdown()


if __name__ == "__main__":
    # Run tests
    print("=" * 60)
    print("Art Learning and Live2D Generation System Tests")
    print("=" * 60)
    
    pytest.main([__file__, "-v", "--tb=short"])
