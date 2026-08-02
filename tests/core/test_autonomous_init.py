"""core.autonomous 套件级 API 测试"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.backend.src.core import autonomous as autonomous_pkg
from apps.backend.src.core.autonomous import get_system_info, initialize_all_systems


class TestGetSystemInfo:
    def test_returns_version(self):
        info = get_system_info()
        assert "version" in info
        assert "author" in info
        assert info["version"] == autonomous_pkg.__version__

    def test_module_groups_present(self):
        info = get_system_info()
        for group in ("biological", "execution", "integration", "art_learning"):
            assert group in info["modules"]
            assert info["modules"][group]

    def test_capabilities_nonempty(self):
        info = get_system_info()
        assert len(info["capabilities"]) > 0
        assert "autonomous_life_cycle" in info["capabilities"]


class TestInitializeAllSystems:
    def test_returns_all_systems(self, monkeypatch):
        # Avoid real heavy initialization: stub system constructors with mocks
        # that expose initialize() as an async no-op.
        def _mock_system(*args, **kwargs):
            system = MagicMock()
            system.initialize = AsyncMock()
            return system

        # Patch every system class referenced by initialize_all_systems.
        modules = {
            "core.bio.autonomic_nervous_system": "AutonomicNervousSystem",
            "core.bio.biological_integrator": "BiologicalIntegrator",
            "core.bio.emotional_blending": "EmotionalBlendingSystem",
            "core.bio.endocrine_system": "EndocrineSystem",
            "core.bio.extended_behavior_library": "ExtendedBehaviorLibrary",
            "core.bio.memory_neuroplasticity_bridge": "MemoryNeuroplasticityBridge",
            "core.bio.multidimensional_trigger": "MultidimensionalTriggerSystem",
            "core.bio.neuroplasticity": "NeuroplasticitySystem",
            "core.bio.physiological_tactile": "PhysiologicalTactileSystem",
            "core.engine.action_executor": "ActionExecutor",
            "core.engine.art_learning_system": "ArtLearningSystem",
            "core.engine.art_learning_workflow": "ArtLearningWorkflow",
            "core.engine.audio_system": "AudioSystem",
            "core.engine.browser_controller": "BrowserController",
            "core.engine.desktop_interaction": "DesktopInteraction",
            "core.engine.live2d_avatar_generator": "Live2DAvatarGenerator",
            "core.engine.live2d_integration": "Live2DIntegration",
            "core.life.autonomous_life_cycle": "AutonomousLifeCycle",
            "core.life.cyber_identity": "CyberIdentity",
            "core.life.digital_life_integrator": "DigitalLifeIntegrator",
            "core.life.self_generation": "SelfGeneration",
        }
        for module_name, class_name in modules.items():
            monkeypatch.setattr(
                f"{module_name}.{class_name}", _mock_system, raising=False
            )

        systems = asyncio.run(initialize_all_systems())
        assert isinstance(systems, dict)
        assert len(systems) >= 20
        assert "physiological_tactile" in systems
        assert "autonomous_life_cycle" in systems

    def test_returns_dict_keys_as_strings(self, monkeypatch):
        def _mock_system(*args, **kwargs):
            system = MagicMock()
            system.initialize = AsyncMock()
            return system

        modules = {
            "core.bio.autonomic_nervous_system": "AutonomicNervousSystem",
            "core.bio.biological_integrator": "BiologicalIntegrator",
            "core.bio.emotional_blending": "EmotionalBlendingSystem",
            "core.bio.endocrine_system": "EndocrineSystem",
            "core.bio.extended_behavior_library": "ExtendedBehaviorLibrary",
            "core.bio.memory_neuroplasticity_bridge": "MemoryNeuroplasticityBridge",
            "core.bio.multidimensional_trigger": "MultidimensionalTriggerSystem",
            "core.bio.neuroplasticity": "NeuroplasticitySystem",
            "core.bio.physiological_tactile": "PhysiologicalTactileSystem",
            "core.engine.action_executor": "ActionExecutor",
            "core.engine.art_learning_system": "ArtLearningSystem",
            "core.engine.art_learning_workflow": "ArtLearningWorkflow",
            "core.engine.audio_system": "AudioSystem",
            "core.engine.browser_controller": "BrowserController",
            "core.engine.desktop_interaction": "DesktopInteraction",
            "core.engine.live2d_avatar_generator": "Live2DAvatarGenerator",
            "core.engine.live2d_integration": "Live2DIntegration",
            "core.life.autonomous_life_cycle": "AutonomousLifeCycle",
            "core.life.cyber_identity": "CyberIdentity",
            "core.life.digital_life_integrator": "DigitalLifeIntegrator",
            "core.life.self_generation": "SelfGeneration",
        }
        for module_name, class_name in modules.items():
            monkeypatch.setattr(
                f"{module_name}.{class_name}", _mock_system, raising=False
            )

        systems = asyncio.run(initialize_all_systems())
        assert all(isinstance(k, str) for k in systems.keys())
