"""
Image generation must be reachable from chat, and must not be swallowed by the
vision handler.

Regression (verified against a live server before the fix):
  「生成一張貓咪的圖片」 → classified vision → ExecutionGate dispatched the vision
  *analysis* handler → the user received 「請提供圖片路徑」. Two further defects
  hid behind mocked tests: the route's models_dir resolved to apps/models (one
  level too high) so /image/generate always answered 503, and it read metric keys
  the optimizer never returns (result["iterations"] / result["final_loss"]).
"""

import asyncio

import pytest


class TestImageGenerationIntent:
    def test_intent_is_declared_with_executable_handler(self):
        from core.intent_registry import IntentRegistry

        registry = IntentRegistry()
        name, confidence = registry.detect("生成一張貓咪的圖片", category="image_generation")
        assert name == "image_generation"
        assert confidence >= 0.2
        pattern = registry.get_pattern(name)
        assert pattern.metadata.get("handler_id") == "image_generate"

    @pytest.mark.parametrize(
        "text",
        [
            "生成一個 RTL 電路",
            "幫我生成 verilog 模組",
            "生成 PCB layout",
        ],
    )
    def test_eda_requests_are_not_treated_as_images(self, text):
        from core.intent_registry import IntentRegistry

        name, _ = IntentRegistry().detect(text, category="image_generation")
        assert name is None, f"{text!r} belongs to the EDA agent, not image generation"

    @pytest.mark.parametrize("text", ["這張圖片看起來如何", "分析這張圖片"])
    def test_image_analysis_requests_are_not_generation(self, text):
        from core.intent_registry import IntentRegistry

        name, _ = IntentRegistry().detect(text, category="image_generation")
        assert name is None, f"{text!r} is vision analysis, not generation"


class TestImageGenerationHandler:
    def test_subject_extraction_drops_the_instruction(self):
        from services.handlers.image_generation_handler import ImageGenerationHandler

        handler = ImageGenerationHandler()
        assert handler._subject("生成一張貓咪的圖片") == "貓咪的圖片"
        assert handler._subject("幫我畫一隻柴犬") == "柴犬"
        assert handler._subject("生成") == ""

    @pytest.mark.asyncio
    async def test_handler_reports_pipeline_unavailable_honestly(self, monkeypatch):
        import services.handlers.image_generation_handler as mod

        def _boom(*_a, **_k):
            raise RuntimeError("GVV pipeline not available")

        monkeypatch.setattr("ai.multimodal.generator.gvv_generator.generate_image", _boom)
        text = await mod.ImageGenerationHandler().handle("生成一張貓咪的圖片")
        assert "不可用" in text
        assert "pic" not in text.lower() or "抽象畫" in text

    @pytest.mark.asyncio
    async def test_handler_returns_a_real_result(self, monkeypatch, tmp_path):
        import base64

        import services.handlers.image_generation_handler as mod

        png = base64.b64encode(b"\x89PNG\r\n\x1a\nfake").decode()
        monkeypatch.setattr(
            "ai.multimodal.generator.gvv_generator.generate_image",
            lambda *a, **k: {
                "image_base64": png,
                "width": 128,
                "height": 128,
                "metrics": {"concept": "truck", "similarity": 0.44},
            },
        )
        handler = mod.ImageGenerationHandler(output_dir=str(tmp_path))
        text = await handler.handle("生成一張貓咪的圖片")

        assert "128x128" in text
        assert "truck" in text
        # Must not imply a photorealistic result — the GVV vocabulary is 50
        # geometric words.
        assert "抽象畫" in text
        assert list(tmp_path.glob("*.png")), "PNG must actually be written"


class TestImageGenerationDispatch:
    @pytest.mark.asyncio
    async def test_owner_dispatches_image_generation_handler(self):
        from ai.core.execution_gate import ExecutionGate
        from services.execution.gate_execution import (
            OUTCOME_EXECUTED,
            get_gate_execution_owner,
        )

        ExecutionGate().reset_feedback_stats()

        class _Bus:
            def __init__(self):
                self.calls = []

            async def execute_handler(self, handler_id, query, context):
                self.calls.append((handler_id, query))
                return {"type": handler_id, "success": True, "result": "generated"}

        bus = _Bus()
        outcome = await get_gate_execution_owner().process("生成一張貓咪的圖片", {}, "img-1", bus)

        assert outcome.action == OUTCOME_EXECUTED
        assert outcome.handler == "image_generate"
        assert bus.calls == [("image_generate", "生成一張貓咪的圖片")]
        assert ExecutionGate().get_feedback_stats()["image_generate"]["success"] == 1

    @pytest.mark.asyncio
    async def test_eda_request_is_not_dispatched_to_image_generation(self):
        from ai.core.execution_gate import ExecutionGate
        from services.execution.gate_execution import get_gate_execution_owner

        ExecutionGate().reset_feedback_stats()

        class _Bus:
            def __init__(self):
                self.calls = []

            async def execute_handler(self, handler_id, query, context):
                self.calls.append(handler_id)
                return {"success": True, "result": ""}

        bus = _Bus()
        await get_gate_execution_owner().process("生成一個 RTL 電路", {}, "img-2", bus)
        assert "image_generate" not in bus.calls

    @pytest.mark.asyncio
    async def test_image_analysis_still_reaches_the_vision_handler(self):
        from ai.core.execution_gate import ExecutionGate
        from services.execution.gate_execution import get_gate_execution_owner

        ExecutionGate().reset_feedback_stats()

        class _Bus:
            def __init__(self):
                self.calls = []

            async def execute_handler(self, handler_id, query, context):
                self.calls.append(handler_id)
                return {"type": handler_id, "success": True, "result": "ok"}

        bus = _Bus()
        await get_gate_execution_owner().process("分析這張貓咪圖片", {}, "img-3", bus)
        assert "image_generate" not in bus.calls


class TestGVVPipelineOwner:
    def test_models_directory_is_actually_found(self):
        from ai.multimodal.generator.gvv_generator import _find_models_dir

        models_dir = _find_models_dir()
        assert models_dir is not None, (
            "GVV model files must resolve; the previous os.path.join(__file__, "
            "'..'*4, 'models') pointed at apps/models and always 503'd"
        )
        import os

        assert os.path.exists(os.path.join(models_dir, "geometric_vocabulary.json"))

    def test_generate_image_reads_keys_the_optimizer_returns(self, monkeypatch):
        import ai.multimodal.generator.gvv_generator as gvv

        class _Mapper:
            _concept_space = None

            def map_text_to_primitives(self, vec):
                return {"concept": "circle", "similarity": 0.5}

        from ai.multimodal.primitives.primitive_types import TOTAL_DIM

        class _Optimizer:
            def optimize_from_text(self, vec, n_iterations, lr):
                # Exactly the real InstanceOptimizer contract: no "iterations",
                # no "final_loss".
                return {
                    "vector": [0.0] * TOTAL_DIM,
                    "loss": 0.25,
                    "concept": "circle",
                    "elapsed": 0.1,
                }

        monkeypatch.setattr(
            gvv, "get_gvv", lambda: {"concept_mapper": _Mapper(), "optimizer": _Optimizer()}
        )
        monkeypatch.setattr(gvv, "encode_text_with_clip", lambda t: [0.0] * 8)
        result = gvv.generate_image("a circle", canvas_size=8, num_iterations=1)
        assert result["metrics"]["concept"] == "circle"
        assert result["metrics"]["loss"] == 0.25
        assert result["image_base64"]
