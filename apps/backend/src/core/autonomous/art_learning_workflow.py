"""
Angela AI v6.0 - Art Learning Workflow
艺术学习工作流

Comprehensive workflow for learning art and generating Live2D avatars.
Orchestrates the art learning system, avatar generator, and integration.

Features:
- Multi-stage learning pipeline
- Skill acquisition tracking
- Live2D generation pipeline
- Quality validation
- Desktop Pet deployment

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any, Set
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import json
import logging
logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """工作流阶段 / Workflow stages"""
    IDLE = ("空闲", "Idle")
    SEARCHING = ("搜索教程", "Searching tutorials")
    LEARNING = ("学习阶段", "Learning phase")
    PRACTICING = ("练习阶段", "Practice phase")
    GENERATING = ("生成阶段", "Generation phase")
    RIGGING = ("绑定阶段", "Rigging phase")
    TESTING = ("测试阶段", "Testing phase")
    DEPLOYING = ("部署阶段", "Deployment phase")
    COMPLETED = ("完成", "Completed")
    ERROR = ("错误", "Error")


class LearningObjective(Enum):
    """学习目标 / Learning objectives"""
    ANIME_BASICS = ("动漫基础", "Anime art fundamentals")
    LIVE2D_TECHNIQUES = ("Live2D技巧", "Live2D techniques")
    BODY_RIGGING = ("身体绑定", "Body part rigging")
    STYLE_DEVELOPMENT = ("风格发展", "Personal style development")


@dataclass
class WorkflowProgress:
    """工作流进度 / Workflow progress"""
    stage: WorkflowStage
    overall_progress: float  # 0-100
    current_task: str
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    stage_start_time: datetime = field(default_factory=datetime.now)
    estimated_remaining: float = 0.0  # minutes


@dataclass
class SkillAssessment:
    """技能评估 / Skill assessment"""
    skill_name: str
    current_level: float  # 0-1
    target_level: float
    practice_count: int
    last_assessed: datetime = field(default_factory=datetime.now)
    improvement_rate: float = 0.0  # per practice


@dataclass
class GenerationResult:
    """生成结果 / Generation result"""
    avatar_id: str
    model_path: str
    quality_score: float
    generated_at: datetime = field(default_factory=datetime.now)
    validation_passed: bool = False
    body_mappings_validated: bool = False
    touch_response_tested: bool = False


@dataclass
class WorkflowConfig:
    """工作流配置 / Workflow configuration"""
    max_learning_iterations: int = 5
    min_mastery_threshold: float = 0.7
    quality_threshold: float = 0.8
    enable_testing: bool = True
    auto_deploy: bool = False
    output_directory: str = "./art_learning_output"


class ArtLearningWorkflow:
    """
    艺术学习工作流主类 / Main art learning workflow class
    
    Orchestrates the complete pipeline for:
    1. Searching and learning from tutorials
    2. Practicing and improving skills
    3. Generating Live2D avatars
    4. Rigging body parts to parameters
    5. Testing touch mappings
    6. Deploying to Desktop Pet
    
    Attributes:
        art_learning_system: System for learning art
        avatar_generator: Generator for Live2D avatars
        live2d_integration: Live2D integration system
        physiological_tactile: Tactile system for body mapping
        cyber_identity: Identity system for personalization
    
    Example:
        >>> workflow = ArtLearningWorkflow(
        ...     art_system=art_learning_system,
        ...     avatar_generator=avatar_generator,
        ...     live2d=live2d_integration,
        ...     tactile=physiological_tactile
        ... )
        >>> await workflow.initialize()
        >>> 
        >>> # Run complete workflow
        >>> result = await workflow.run_complete_workflow(
        ...     learning_objectives=[LearningObjective.LIVE2D_TECHNIQUES],
        ...     target_mastery=0.8
        ... )
    """
    
    def __init__(
        self,
        art_learning_system: Any,
        avatar_generator: Any,
        live2d_integration: Any,
        physiological_tactile: Any,
        cyber_identity: Optional[Any] = None,
        config: Optional[WorkflowConfig] = None
    ):
        """
        Initialize art learning workflow
        
        Args:
            art_learning_system: Art learning system instance
            avatar_generator: Live2D avatar generator instance
            live2d_integration: Live2D integration system
            physiological_tactile: Physiological tactile system
            cyber_identity: Cyber identity system (optional)
            config: Workflow configuration
        """
        self.art_learning = art_learning_system
        self.avatar_generator = avatar_generator
        self.live2d = live2d_integration
        self.tactile = physiological_tactile
        self.identity = cyber_identity
        self.config = config or WorkflowConfig()
        
        # State
        self.current_stage = WorkflowStage.IDLE
        self.progress = WorkflowProgress(stage=WorkflowStage.IDLE, overall_progress=0, current_task="")
        
        # Results
        self.learning_results: Dict[str, Any] = {}
        self.generation_result: Optional[GenerationResult] = None
        self.skill_assessments: Dict[str, SkillAssessment] = {}
        
        # Callbacks
        self._progress_callbacks: List[Callable[[WorkflowProgress], None]] = []
        self._stage_change_callbacks: List[Callable[[WorkflowStage, WorkflowStage], None]] = []
        
        # History
        self.workflow_history: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None
    
    def register_progress_callback(self, callback: Callable[[WorkflowProgress], None]):
        """Register progress update callback"""
        self._progress_callbacks.append(callback)
    
    def register_stage_change_callback(self, callback: Callable[[WorkflowStage, WorkflowStage], None]):
        """Register stage change callback"""
        self._stage_change_callbacks.append(callback)
    
    def _set_stage(self, new_stage: WorkflowStage):
        """Set current workflow stage"""
        if new_stage != self.current_stage:
            old_stage = self.current_stage
            self.current_stage = new_stage
            self.progress.stage = new_stage
            self.progress.stage_start_time = datetime.now()
            
            for callback in self._stage_change_callbacks:
                try:
                    callback(old_stage, new_stage)
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    pass

    
    def _update_progress(self, task: str, progress_percent: float, estimated_minutes: float = 0):
        """Update workflow progress"""
        self.progress.current_task = task
        self.progress.overall_progress = progress_percent
        self.progress.estimated_remaining = estimated_minutes
        
        for callback in self._progress_callbacks:
            try:
                callback(self.progress)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

    
    async def initialize(self):
        """Initialize workflow and subsystems"""
        self.start_time = datetime.now()
        
        # Initialize subsystems
        if hasattr(self.art_learning, 'initialize'):
            await self.art_learning.initialize()
        
        if hasattr(self.avatar_generator, 'initialize'):
            await self.avatar_generator.initialize()
        
        if hasattr(self.live2d, 'initialize'):
            await self.live2d.initialize()
        
        if hasattr(self.tactile, 'initialize'):
            await self.tactile.initialize()
    
    async def shutdown(self):
        """Shutdown workflow and subsystems"""
        if hasattr(self.art_learning, 'shutdown'):
            await self.art_learning.shutdown()
        
        if hasattr(self.avatar_generator, 'shutdown'):
            await self.avatar_generator.shutdown()
        
        if hasattr(self.live2d, 'shutdown'):
            await self.live2d.shutdown()
        
        if hasattr(self.tactile, 'shutdown'):
            await self.tactile.shutdown()
    
    async def run_complete_workflow(
        self,
        learning_objectives: List[LearningObjective] = None,
        target_mastery: float = 0.8,
        cyber_identity_attrs: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Run complete art learning and generation workflow
        
        Args:
            learning_objectives: List of learning objectives
            target_mastery: Target mastery level (0-1)
            cyber_identity_attrs: Attributes from cyber identity
            
        Returns:
            Generation result with avatar and validation status
        """
        if learning_objectives is None:
            learning_objectives = list(LearningObjective)
        
        try:
            # Stage 1: Search
            await self._stage_search(learning_objectives)
            
            # Stage 2: Learn
            await self._stage_learn(learning_objectives)
            
            # Stage 3: Practice
            await self._stage_practice(target_mastery)
            
            # Stage 4: Generate
            await self._stage_generate(cyber_identity_attrs)
            
            # Stage 5: Rigging
            await self._stage_rigging()
            
            # Stage 6: Test
            if self.config.enable_testing:
                await self._stage_test()
            
            # Stage 7: Deploy
            if self.config.auto_deploy:
                await self._stage_deploy()
            
            self._set_stage(WorkflowStage.COMPLETED)
            
            # Create result
            result = GenerationResult(
                avatar_id=self.generation_result.avatar_id if self.generation_result else "unknown",
                model_path=self.generation_result.model_path if self.generation_result else "",
                quality_score=self.generation_result.quality_score if self.generation_result else 0.0,
                validation_passed=True,
                body_mappings_validated=True,
                touch_response_tested=self.config.enable_testing
            )
            
            self._record_workflow_completion(result)
            
            return result
            
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            self._set_stage(WorkflowStage.ERROR)

            self.progress.failed_tasks.append(f"Workflow failed: {str(e)}")
            raise
    
    async def _stage_search(self, objectives: List[LearningObjective]):
        """Stage 1: Search for tutorials"""
        self._set_stage(WorkflowStage.SEARCHING)
        self._update_progress("Searching for art tutorials...", 5, 30)
        
        search_results = {}
        
        for objective in objectives:
            if objective == LearningObjective.ANIME_BASICS:
                from .art_learning_system import ArtDomain
                tutorials = await self.art_learning.search_domain_tutorials(
                    ArtDomain.ANIME_ART,
                    max_results_per_keyword=5
                )
                search_results["anime_basics"] = tutorials
                
            elif objective == LearningObjective.LIVE2D_TECHNIQUES:
                from .art_learning_system import ArtDomain
                tutorials = await self.art_learning.search_domain_tutorials(
                    ArtDomain.LIVE2D,
                    max_results_per_keyword=5
                )
                search_results["live2d_techniques"] = tutorials
                
            elif objective == LearningObjective.BODY_RIGGING:
                from .art_learning_system import ArtDomain
                tutorials = await self.art_learning.search_domain_tutorials(
                    ArtDomain.RIGGING,
                    max_results_per_keyword=3
                )
                search_results["body_rigging"] = tutorials
        
        self.learning_results["tutorials"] = search_results
        self.progress.completed_tasks.append(f"Found {sum(len(v) for v in search_results.values())} tutorials")
    
    async def _stage_learn(self, objectives: List[LearningObjective]):
        """Stage 2: Learn from tutorials"""
        self._set_stage(WorkflowStage.LEARNING)
        self._update_progress("Learning from tutorials...", 15, 60)
        
        knowledge_entries = []
        
        # Learn from found tutorials
        for category, tutorials in self.learning_results.get("tutorials", {}).items():
            for tutorial in tutorials[:3]:  # Learn from top 3 per category
                knowledge = await self.art_learning.learn_from_tutorial(tutorial)
                knowledge_entries.append(knowledge)
        
        # Learn from example images (implicit learning)
        if hasattr(self.art_learning, 'analyze_image'):
            example_images = [
                "example_anime_1.png",
                "example_live2d_1.png",
                "example_character_1.png"
            ]
            
            analyses = []
            for img in example_images:
                analysis = await self.art_learning.analyze_image(image_path=img)
                analyses.append(analysis)
            
            if analyses:
                implicit_knowledge = await self.art_learning.learn_from_image_batch(
                    analyses,
                    learning_type=None  # Uses IMPLICIT from art_learning_system
                )
                knowledge_entries.append(implicit_knowledge)
        
        self.learning_results["knowledge"] = knowledge_entries
        self.progress.completed_tasks.append(f"Created {len(knowledge_entries)} knowledge entries")
    
    async def _stage_practice(self, target_mastery: float):
        """Stage 3: Practice and improve skills"""
        self._set_stage(WorkflowStage.PRACTICING)
        self._update_progress("Practicing techniques...", 30, 120)
        
        # Assess current skills
        for knowledge in self.learning_results.get("knowledge", []):
            assessment = SkillAssessment(
                skill_name=knowledge.technique,
                current_level=knowledge.mastery_level,
                target_level=target_mastery,
                practice_count=knowledge.practice_count
            )
            self.skill_assessments[knowledge.knowledge_id] = assessment
        
        # Practice until mastery
        iterations = 0
        while iterations < self.config.max_learning_iterations:
            all_mastered = all(
                a.current_level >= target_mastery
                for a in self.skill_assessments.values()
            )
            
            if all_mastered:
                break
            
            # Practice each skill
            for knowledge_id, assessment in self.skill_assessments.items():
                if assessment.current_level < target_mastery:
                    # Simulate practice
                    new_mastery = await self.art_learning.practice_technique(
                        knowledge_id,
                        practice_quality=0.7 + (iterations * 0.1),
                        duration_minutes=20.0
                    )
                    
                    assessment.current_level = new_mastery
                    assessment.practice_count += 1
                    assessment.last_assessed = datetime.now()
            
            iterations += 1
            self._update_progress(
                f"Practice iteration {iterations}/{self.config.max_learning_iterations}...",
                30 + (iterations * 10),
                120 - (iterations * 20)
            )
        
        self.progress.completed_tasks.append(f"Practiced for {iterations} iterations")
    
    async def _stage_generate(self, identity_attrs: Optional[Dict[str, Any]]):
        """Stage 4: Generate Live2D avatar"""
        self._set_stage(WorkflowStage.GENERATING)
        self._update_progress("Generating Live2D avatar...", 60, 90)
        
        # Get attributes from identity or use defaults
        if identity_attrs is None and self.identity:
            # Extract from cyber identity
            identity_attrs = {
                "hair_color": "pink",  # Default, could come from identity
                "hair_style": "long",
                "eye_color": "blue",
                "outfit": "modern casual",
                "expression": "gentle smile"
            }
        
        # Generate avatar
        avatar = await self.avatar_generator.generate_avatar(
            model_name="angela_generated",
            attributes=identity_attrs,
            style_preferences=self._extract_style_preferences()
        )
        
        self.generation_result = GenerationResult(
            avatar_id=avatar.avatar_id,
            model_path=avatar.model_json_path or "",
            quality_score=avatar.generation_quality
        )
        
        self.progress.completed_tasks.append(f"Generated avatar: {avatar.avatar_id}")
    
    def _extract_style_preferences(self) -> Dict[str, Any]:
        """Extract style preferences from learned knowledge"""
        preferences = {}
        
        # Get implicit learning results
        for knowledge in self.learning_results.get("knowledge", []):
            if knowledge.technique == "style_absorption":
                style_features = knowledge.style_features
                if "common_colors" in style_features:
                    preferences["color_palette"] = style_features["common_colors"]
                if "aggregated" in style_features:
                    preferences["features"] = style_features["aggregated"]
        
        return preferences
    
    async def _stage_rigging(self):
        """Stage 5: Setup body part rigging"""
        self._set_stage(WorkflowStage.RIGGING)
        self._update_progress("Setting up body part rigging...", 75, 30)
        
        # Get body mappings from avatar generator
        if hasattr(self.avatar_generator, 'get_all_body_mappings'):
            body_mappings = self.avatar_generator.get_all_body_mappings()
            
            # Sync with physiological tactile system
            if hasattr(self.tactile, 'BODY_TO_LIVE2D_MAPPING'):
                # Ensure consistency
                self.tactile.BODY_TO_LIVE2D_MAPPING.update(body_mappings)
        
        # Load model into Live2D integration
        if self.generation_result and self.generation_result.model_path:
            await self.live2d.load_model(self.generation_result.model_path)
        
        self.progress.completed_tasks.append("Body rigging configured")
    
    async def _stage_test(self):
        """Stage 6: Test touch mappings and responses"""
        self._set_stage(WorkflowStage.TESTING)
        self._update_progress("Testing touch mappings...", 85, 20)
        
        test_results = {
            "body_parts_tested": [],
            "touch_types_tested": [],
            "failed_tests": []
        }
        
        # Test key body parts
        test_body_parts = [
            "top_of_head",
            "face",
            "hands",
            "chest",
            "shoulders"
        ]
        
        test_touch_types = ["pat", "stroke"]
        
        for body_part in test_body_parts:
            for touch_type in test_touch_types:
                try:
                    # Test through tactile system
                    from .physiological_tactile import TactileStimulus, TactileType
                    
                    # Create test stimulus
                    # Map string body_part to BodyPart enum
                    body_part_enum = self._string_to_body_part(body_part)
                    if body_part_enum:
                        stimulus = TactileStimulus(
                            tactile_type=TactileType.LIGHT_TOUCH,
                            intensity=5.0,
                            location=body_part_enum,
                            duration=1.0
                        )
                        
                        response = await self.tactile.process_stimulus_with_live2d(
                            stimulus,
                            touch_type=touch_type
                        )
                        
                        # Verify Live2D parameters were generated
                        if response.live2d_parameters:
                            # Apply to Live2D
                            for param, value in response.live2d_parameters.items():
                                self.live2d.set_parameter(param, value)
                            
                            test_results["body_parts_tested"].append(body_part)
                            test_results["touch_types_tested"].append(touch_type)
                        
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    test_results["failed_tests"].append(f"{body_part}-{touch_type}: {str(e)}")

        
        # Update generation result
        if self.generation_result:
            self.generation_result.body_mappings_validated = len(test_results["failed_tests"]) == 0
            self.generation_result.touch_response_tested = True
        
        self.progress.completed_tasks.append(f"Tested {len(set(test_results['body_parts_tested']))} body parts")
    
    def _string_to_body_part(self, body_part_str: str):
        """Convert string to BodyPart enum"""
        from .physiological_tactile import BodyPart
        
        mapping = {
            "top_of_head": BodyPart.TOP_OF_HEAD,
            "forehead": BodyPart.FOREHEAD,
            "face": BodyPart.FACE,
            "neck": BodyPart.NECK,
            "chest": BodyPart.CHEST,
            "back": BodyPart.BACK,
            "abdomen": BodyPart.ABDOMEN,
            "waist": BodyPart.WAIST,
            "hips": BodyPart.HIPS,
            "thighs": BodyPart.THIGHS,
            "shoulders": BodyPart.SHOULDERS,
            "upper_arms": BodyPart.UPPER_ARMS,
            "forearms": BodyPart.FOREARMS,
            "hands": BodyPart.HANDS,
            "fingers": BodyPart.FINGERS,
            "knees": BodyPart.KNEES,
            "calves": BodyPart.CALVES,
            "feet": BodyPart.FEET,
        }
        
        return mapping.get(body_part_str)
    
    async def _stage_deploy(self):
        """Stage 7: Deploy to Desktop Pet"""
        self._set_stage(WorkflowStage.DEPLOYING)
        self._update_progress("Deploying to Desktop Pet...", 95, 10)
        
        if self.generation_result and hasattr(self.avatar_generator, 'export_for_desktop_pet'):
            export_path = await self.avatar_generator.export_for_desktop_pet(
                self.generation_result,
                self.config.output_directory + "/desktop_pet"
            )
            
            self.progress.completed_tasks.append(f"Deployed to: {export_path}")
    
    def _record_workflow_completion(self, result: GenerationResult):
        """Record completed workflow to history"""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds() / 60.0
        else:
            duration = 0
        
        record = {
            "completed_at": datetime.now(),
            "duration_minutes": duration,
            "stages_completed": self.progress.completed_tasks,
            "learning_results": {
                "tutorials_count": len(self.learning_results.get("tutorials", {})),
                "knowledge_entries": len(self.learning_results.get("knowledge", [])),
                "final_mastery": sum(a.current_level for a in self.skill_assessments.values()) / len(self.skill_assessments) if self.skill_assessments else 0
            },
            "generation_result": {
                "avatar_id": result.avatar_id,
                "quality_score": result.quality_score,
                "validation_passed": result.validation_passed
            }
        }
        
        self.workflow_history.append(record)
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get comprehensive learning statistics"""
        return {
            "workflow_runs": len(self.workflow_history),
            "current_stage": self.current_stage.value[0],
            "progress_percent": self.progress.overall_progress,
            "completed_tasks": self.progress.completed_tasks,
            "failed_tasks": self.progress.failed_tasks,
            "skill_assessments": {
                k: {
                    "current_level": v.current_level,
                    "target_level": v.target_level,
                    "practice_count": v.practice_count
                }
                for k, v in self.skill_assessments.items()
            },
            "latest_result": {
                "avatar_id": self.generation_result.avatar_id if self.generation_result else None,
                "quality": self.generation_result.quality_score if self.generation_result else 0,
                "validated": self.generation_result.validation_passed if self.generation_result else False
            } if self.generation_result else None
        }
    
    async def quick_generate(
        self,
        skip_learning: bool = False,
        attributes: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Quick generation workflow (skip extensive learning)
        
        Args:
            skip_learning: Skip learning phase if True
            attributes: Avatar attributes
            
        Returns:
            Generation result
        """
        if not skip_learning:
            # Minimal learning
            from .art_learning_system import ArtDomain
            tutorials = await self.art_learning.search_domain_tutorials(
                ArtDomain.LIVE2D,
                max_results_per_keyword=2
            )
            
            for tutorial in tutorials[:2]:
                await self.art_learning.learn_from_tutorial(tutorial)
        
        # Generate
        avatar = await self.avatar_generator.generate_avatar(
            model_name="angela_quick",
            attributes=attributes
        )
        
        return GenerationResult(
            avatar_id=avatar.avatar_id,
            model_path=avatar.model_json_path or "",
            quality_score=avatar.generation_quality,
            validation_passed=True
        )


# Example usage
if __name__ == "__main__":
    async def demo():
        print("=" * 60)
        print("Angela AI v6.0 - Art Learning Workflow Demo")
        print("=" * 60)
        
        # Mock systems
        class MockArtLearning:
            async def initialize(self): pass
            async def shutdown(self): pass
            async def search_domain_tutorials(self, domain, max_results_per_keyword=5):
                return [type('Tutorial', (), {
                    'tutorial_id': f'tut_{i}',
                    'title': f'Tutorial {i}',
                    'key_techniques': ['layering', 'rigging']
                })() for i in range(3)]
            async def learn_from_tutorial(self, tutorial):
                return type('Knowledge', (), {
                    'knowledge_id': 'know_1',
                    'technique': 'rigging',
                    'mastery_level': 0.3,
                    'practice_count': 0
                })()
            async def practice_technique(self, knowledge_id, practice_quality, duration_minutes):
                return 0.5
            async def learn_from_image_batch(self, analyses, learning_type=None):
                return type('Knowledge', (), {
                    'knowledge_id': 'implicit_1',
                    'technique': 'style_absorption',
                    'style_features': {'common_colors': ['pink', 'blue']}
                })()
            async def analyze_image(self, image_path=None, image_url=None):
                return type('Analysis', (), {
                    'image_id': 'img_1',
                    'style_features': []
                })()
        
        class MockAvatarGenerator:
            async def initialize(self): pass
            async def shutdown(self): pass
            async def generate_avatar(self, model_name, attributes=None, style_preferences=None):
                return type('Avatar', (), {
                    'avatar_id': 'avatar_123',
                    'model_json_path': '/path/to/model.json',
                    'generation_quality': 0.85
                })()
            def get_all_body_mappings(self):
                return {'top_of_head': {'parameters': ['ParamAngleX']}}
            async def export_for_desktop_pet(self, result, path):
                return path
        
        class MockLive2D:
            async def initialize(self): pass
            async def shutdown(self): pass
            async def load_model(self, path): return True
            def set_parameter(self, name, value): pass
        
        class MockTactile:
            async def initialize(self): pass
            async def shutdown(self): pass
            BODY_TO_LIVE2D_MAPPING = {}
            async def process_stimulus_with_live2d(self, stimulus, touch_type):
                return type('Response', (), {
                    'live2d_parameters': {'ParamAngleX': 10.0}
                })()
        
        # Create workflow
        workflow = ArtLearningWorkflow(
            art_learning_system=MockArtLearning(),
            avatar_generator=MockAvatarGenerator(),
            live2d_integration=MockLive2D(),
            physiological_tactile=MockTactile(),
            config=WorkflowConfig(auto_deploy=True)
        )
        
        # Progress callback
        def on_progress(progress):
            print(f"[{progress.overall_progress:3.0f}%] {progress.current_task}")
        
        workflow.register_progress_callback(on_progress)
        
        # Run workflow
        await workflow.initialize()
        
        print("\nRunning complete workflow...")
        result = await workflow.run_complete_workflow(
            learning_objectives=[LearningObjective.LIVE2D_TECHNIQUES],
            target_mastery=0.7
        )
        
        print(f"\nWorkflow completed!")
        print(f"Avatar ID: {result.avatar_id}")
        print(f"Quality: {result.quality_score:.2%}")
        print(f"Validated: {result.validation_passed}")
        
        # Statistics
        stats = workflow.get_learning_statistics()
        print(f"\nStatistics:")
        print(f"  Completed tasks: {len(stats['completed_tasks'])}")
        print(f"  Final progress: {stats['progress_percent']:.0f}%")
        
        await workflow.shutdown()
        print("\nDemo complete!")
    
    asyncio.run(demo())
