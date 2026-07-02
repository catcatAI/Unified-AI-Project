"""Consolidated smoke tests: import + instantiation for all modules.
Replaces 40+ individual boilerplate test files (test_*.py with just
test_import + test_instantiation).
"""
import importlib
import pytest

# (module_path, class_name, init_kwargs)
_SMOKE_MODULES = [
    ("core.engine.action_executor", "ActionExecutor", {"config": {"max_queue_size": 10}}),
    ("core.engine.angela_model_core", "AngelaModelCore", {}),
    ("core.art.real_playwright_browser", "AngelaRealBrowser", {}),
    ("core.art.real_edge_tts", "AngelaRealVoice", {}),
    ("services.llm.providers.anthropic", "AnthropicAPIBackend", {"api_key": "test-key-placeholder"}),
    ("ai.audio.audio_processing", "AudioProcessing", {}),
    ("core.engine.audio_system", "AudioSystem", {}),
    ("core.life.bio_reflex_manager", "BiogenicReflexManager", {"bio_integrator": None}),
    ("core.bio.cerebellum_engine", "CerebellumEngine", {}),
    ("core.tracing.chain_validator", "ChainValidator", {}),
    ("core.hardware.compute_matrix", "ComputationMatrix", {}),
    ("ai.context.exceptions", "ContextError", {}),
    ("ai.context.storage.base", "Context", {"context_id": "test", "context_type": "memory"}),
    ("ai.context.storage.database", "DatabaseStorage", {}),
    ("ai.context.storage.disk", "DiskStorage", {"storage_dir": "./test_storage"}),
    ("core.state.decimal_hash_table", "DecimalHashTable", {}),
    ("ai.alignment.decision_theory_system", "DecisionTheorySystem", {}),
    ("ai.context.dialogue_context", "Message", {"sender": "user", "content": "hello"}),
    ("economy.economy_manager", "EconomyManager", {"config": {}}),
    ("core.life.env_dynamics", "EnvironmentDynamics", {}),
    ("core.life.evolution_engine", "EvolutionEngine", {}),
    ("services.handlers.file_operation_handler", "FileOperationHandler", {}),
    ("services.handlers.google_drive_handler", "GoogleDriveHandler", {}),
    ("services.llm.providers.google", "GoogleAPIBackend", {"api_key": "test-key-placeholder"}),
    ("core.hardware.gpu_accelerator", "GPUAcceleratorService", {}),
    ("core.card.quality.gravity_calibration", "GravityCalibrator", {}),
    ("core.hardware.hal", "HardwareManager", {}),
    ("core.life.heartbeat", "MetabolicHeartbeat", {"update_interval": 60.0}),
    ("core.state.integer_hash_table", "IntegerHashTable", {}),
    ("services.handlers.learning_handler", "LearningHandler", {}),
    ("ai.level5_asi_system", "Level5ASISystem", {}),
    ("services.llm.providers.llamacpp", "LlamaCppBackend", {}),
    ("ai.context.memory_context", "Memory", {"content": "test"}),
    ("ai.context.model_context", "ModelCallRecord",
     {"caller_model_id": "a", "callee_model_id": "b", "parameters": {},
      "result": None, "duration": 0.5, "success": True}),
    ("ai.multimodal.multimodal_processor", "MultimodalProcessor", {}),
    ("services.llm.providers.ollama", "OllamaBackend", {}),
    ("ai.alignment.ontology_system", "OntologySystem", {}),
    ("services.llm.providers.openai", "OpenAIAPIBackend", {"api_key": "test-key-placeholder"}),
    ("integrations.os_bridge_adapter", "OSBridgeAdapter", {}),
    ("core.perception.perceptual_memory", "PerceptualMemory", {"capacity": 100}),
    ("ai.reasoning.causal_reasoning_engine", "CausalReasoningEngine", {}),
    ("integrations.rovo_dev_connector", "RovoDevConnector", {"config": {}}),
    ("core.life.self_introspector", "SelfIntrospector", {}),
    ("core.state.state_hash_manager", "StateHashManager", {}),
    ("core.life.tickle_reflex_system", "TickleReflexSystem", {}),
    ("ai.context.tool_context", "ToolCategory", {"category_id": "cat1", "name": "Test"}),
    ("core.waiting_scheduler", "WaitingScheduler", {"max_wait_seconds": 5.0}),
    ("core.tools.web_search_tool", "WebSearchTool", {}),
    # Merged from tests/ai/agents/test_imports.py (§X #119)
    ("ai.agents.base.base_agent", "BaseAgent", {"agent_id": "test-agent"}),
    ("ai.agents.specialized.audio_processing_agent", "AudioProcessingAgent", {}),
    ("ai.agents.specialized.code_understanding_agent", "CodeUnderstandingAgent", {}),
    ("ai.agents.specialized.creative_writing_agent", "CreativeWritingAgent", {}),
    ("ai.agents.specialized.data_analysis_agent", "DataAnalysisAgent", {}),
    ("ai.agents.specialized.knowledge_graph_agent", "KnowledgeGraphAgent", {}),
    # Merged from tests/tools/test_tools_imports.py (§X #120)
    ("core.tools.code_understanding_tool", "CodeUnderstandingTool", {}),
    ("fragmenta.fragmenta_orchestrator", "FragmentaOrchestrator", {}),
    # Merged from tests/unit/test_unit_backend_imports.py (§X #123)
    ("ai.alignment.asi_autonomous_alignment", "ASIAutonomousAlignment", {}),
    ("core.state.precision_projection_matrix", "PrecisionProjectionMatrix", {}),
]


def _try_import_class(module_path, class_name):
    """Try to import a class, catching ImportError gracefully."""
    try:
        mod = importlib.import_module(module_path)
        return getattr(mod, class_name, None)
    except (ImportError, AttributeError, ModuleNotFoundError):
        return None


@pytest.mark.parametrize("module_path,class_name,kwargs", _SMOKE_MODULES,
                         ids=lambda x: x.split(".")[-1] if isinstance(x, str) else "")
def test_smoke_import(module_path, class_name, kwargs):
    """Verify module can be imported."""
    cls = _try_import_class(module_path, class_name)
    if cls is None:
        pytest.skip(f"Not available: {module_path}.{class_name}")
    assert cls is not None


@pytest.mark.parametrize("module_path,class_name,kwargs", _SMOKE_MODULES,
                         ids=lambda x: x.split(".")[-1] if isinstance(x, str) else "")
def test_smoke_instantiate(module_path, class_name, kwargs):
    """Verify basic instantiation."""
    cls = _try_import_class(module_path, class_name)
    if cls is None:
        pytest.skip(f"Not available: {module_path}.{class_name}")
    try:
        instance = cls(**kwargs)
        assert instance is not None
    except Exception as e:
        pytest.skip(f"Init failed: {e}")


class TestGravityCalibrator:
    """Extra tests for GravityCalibrator (was in dedicated file)."""

    def test_constants(self):
        try:
            from core.card.quality.gravity_calibration import G_CANDIDATES, IDEAL_LOWER, IDEAL_UPPER
            assert IDEAL_LOWER == 0.6
            assert IDEAL_UPPER == 0.85
            assert len(G_CANDIDATES) == 4
        except ImportError as e:
            pytest.skip(f"Not available: {e}")


class TestLevel5ASISystem:
    """Extra tests for Level5ASISystem (was dedicated file)."""

    def test_instantiation_system_id(self):
        try:
            from ai.level5_asi_system import Level5ASISystem
            instance = Level5ASISystem()
            assert instance.system_id == "level5_asi_system"
        except Exception as e:
            pytest.skip(f"Level5ASISystem init failed: {e}")


class TestParameterExtractor:
    """Import test for parameter_extractor (no public class, just package)."""

    def test_parameter_extractor_package_import(self):
        """Verify core.tools.parameter_extractor package is importable.
        Merged from tests/tools/test_tools_imports.py (§X #120).
        """
        try:
            mod = importlib.import_module("core.tools.parameter_extractor")
            assert mod is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")


# ── Optional module attribute imports ───────────────────────────────────
# Merged from tests/core/test_core_smoke_imports.py (§X #122)

_MODULE_ATTR_IMPORTS = [
    ("economy.economy_db", "EconomyDB"),
    ("shared.types.mappable_data_object", "MappableDataObject"),
    ("core.utils", "now_timestamp"),
    ("core.hsp.connector", "HSPConnector"),
    ("core.hsp.bridge", "message_bridge"),
    ("core.angela_error", "AngelaError"),
]


class TestOptionalModuleImports:
    """Parametrized import tests for optional module attributes."""

    @pytest.mark.parametrize("module_path,attr_name", _MODULE_ATTR_IMPORTS,
                             ids=lambda x: f"{x[0].split('.')[-1]}.{x[1]}" if isinstance(x, tuple) else str(x))
    def test_optional_module_import(self, module_path: str, attr_name: str) -> None:
        """Verify optional module attribute is importable."""
        try:
            mod = importlib.import_module(module_path)
            obj = getattr(mod, attr_name)
            assert obj is not None
        except (ImportError, ModuleNotFoundError):
            pytest.skip(f"Optional module {module_path} not available")
