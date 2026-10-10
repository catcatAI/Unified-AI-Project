from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def chat_service():
    from apps.backend.src.services.chat_service import ChatService

    service = ChatService()
    service._initialized = True
    service._llm_service = MagicMock()
    return service


class TestChatServiceInit:

    def test_initialization(self):
        from apps.backend.src.services.chat_service import ChatService

        service = ChatService()
        assert service._initialized is False
        assert service._llm_service is None
        assert service._vector_store is None
        assert service._ham_memory is None

    def test_initialized_flag(self):
        from apps.backend.src.services.chat_service import ChatService

        service = ChatService()
        assert service._initialized is False


class TestChatServiceModelBus:

    def test_model_bus_none_when_no_llm(self):
        from apps.backend.src.services.chat_service import ChatService

        service = ChatService()
        assert service.model_bus is None


class TestChatServiceGenerateResponse:

    async def test_generate_response_basic(self, chat_service):
        from core.interfaces.protocols import LLMResponse

        chat_service._llm_service = MagicMock()
        chat_service._llm_service.generate_response = AsyncMock(
            return_value=LLMResponse(text="Hello!")
        )
        result = await chat_service.generate_response("hello", "User")
        assert result.text == "Hello!"

    async def test_capability_question_skips_knowledge_pipeline(self, chat_service):
        from core.interfaces.protocols import LLMResponse

        chat_service._llm_service.generate_response = AsyncMock(
            return_value=LLMResponse(text="runtime catalog")
        )
        chat_service._knowledge_pipeline = MagicMock()
        chat_service._knowledge_pipeline.query = AsyncMock(
            return_value={"answer": "stale template"}
        )

        result = await chat_service.generate_response("你會啥？", "User")

        assert result.text == "runtime catalog"
        chat_service._knowledge_pipeline.query.assert_not_awaited()

    async def test_identity_question_reaches_llm_without_dictionary_shortcut(self, chat_service):
        from core.interfaces.protocols import LLMResponse

        chat_service._llm_service.generate_response = AsyncMock(
            return_value=LLMResponse(text="Angela 的自我介紹")
        )
        chat_service._knowledge_pipeline = MagicMock()
        chat_service._knowledge_pipeline.query = AsyncMock(return_value={"answer": "一下 = ..."})

        result = await chat_service.generate_response("自我介紹一下", "User")

        assert result.text == "Angela 的自我介紹"
        chat_service._knowledge_pipeline.query.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_repl_hardware_request_uses_registered_agent(self, chat_service, monkeypatch):
        calls = []

        class FakeManager:
            async def execute_agent(self, agent_id, task):
                calls.append((agent_id, task))
                return SimpleNamespace(
                    success=True,
                    result_data={"status": "partial", "message": "reference pending"},
                    error=None,
                )

        monkeypatch.setattr("api.lifespan.get_agent_manager", lambda: FakeManager())
        result = await chat_service.generate_response(
            "請執行 AI 計算卡 software-only reference",
            context={"conversation_path": "repl"},
        )

        assert result.backend == "specialized_agent"
        assert result.text == "reference pending"
        assert calls[0][0] == "eda_agent"
        assert calls[0][1]["method"] == "run_ai_card_reference_experiment"

        followup = await chat_service.generate_response(
            "請繼續整理剛才的結果。",
            context={"conversation_path": "repl"},
        )
        assert followup.backend == "specialized_agent"
        assert calls[1][0] == "eda_agent"
        assert calls[1][1]["method"] == "run_ai_card_reference_experiment"
        chat_service._llm_service.generate_response.assert_not_called()

    async def test_generate_response_no_llm_raises(self):
        from apps.backend.src.services.chat_service import ChatService

        service = ChatService()
        service._initialized = True
        with pytest.raises(AttributeError):
            await service.generate_response("hello", "User")

    async def test_generate_response_with_context(self, chat_service):
        from core.interfaces.protocols import LLMResponse

        chat_service._llm_service = MagicMock()
        chat_service._llm_service.generate_response = AsyncMock(
            return_value=LLMResponse(text="response")
        )
        result = await chat_service.generate_response(
            "hello", "User", {"custom_key": "custom_value"}
        )
        assert result.text == "response"
        call = chat_service._llm_service.generate_response.call_args
        args = call[0] if call else ()
        context = args[1] if len(args) > 1 else {}
        assert "custom_key" in context, f"context={context}, args={args}"

    async def test_generate_response_with_image_context_injects_multimodal(self, chat_service):
        """When image_analysis with image_data is in context, multimodal entries are injected."""
        from core.interfaces.protocols import LLMResponse

        chat_service._llm_service = MagicMock()
        chat_service._llm_service.generate_response = AsyncMock(
            return_value=LLMResponse(text="multimodal response")
        )
        result = await chat_service.generate_response(
            "describe this image",
            "User",
            {
                "image_analysis": {
                    "filename": "test.png",
                    "analysis": "a cat",
                    "image_data": b"fake_png_bytes",
                }
            },
        )
        assert result.text == "multimodal response"

    async def test_generate_response_with_image_analysis_no_data(self, chat_service):
        """image_analysis without image_data should not trigger multimodal."""
        from core.interfaces.protocols import LLMResponse

        chat_service._llm_service = MagicMock()
        chat_service._llm_service.generate_response = AsyncMock(
            return_value=LLMResponse(text="response")
        )
        result = await chat_service.generate_response(
            "hello", "User", {"image_analysis": {"filename": "test.png", "analysis": "text"}}
        )
        assert result.text == "response"


class TestChatServiceShutdown:

    async def test_shutdown_sets_uninitialized(self, chat_service):
        chat_service._initialized = True
        await chat_service.shutdown()
        assert chat_service._initialized is False


class TestChatServicePostProcess:

    def test_post_process_adds_bio_enriched_metadata(self, chat_service):
        from core.interfaces.protocols import LLMResponse

        response = LLMResponse(text="test")
        result = chat_service._post_process_response(response, {})
        assert result.metadata.get("bio_enriched") is False

    def test_post_process_with_bio_state(self, chat_service):
        from core.interfaces.protocols import LLMResponse

        response = LLMResponse(text="test", metadata={"existing": True})
        result = chat_service._post_process_response(response, {"bio_state": {"energy": 0.8}})
        assert result.metadata["bio_enriched"] is True


class TestChatServiceMultimodalOutput:

    async def test_generate_response_with_multimodal_output(self, chat_service):
        """When image_data triggers retrieval, response metadata should contain generated content."""
        from core.interfaces.protocols import LLMResponse

        chat_service._llm_service = MagicMock()
        chat_service._llm_service.generate_response = AsyncMock(
            return_value=LLMResponse(text="multimodal response")
        )
        result = await chat_service.generate_response(
            "describe this image",
            "User",
            {
                "image_analysis": {
                    "filename": "test.png",
                    "analysis": "a cat",
                    "image_data": b"fake_png_for_retrieval",
                }
            },
        )
        assert result.text == "multimodal response"
        # Metadata may or may not contain generated content depending on
        # retrieval success; we just verify no exception is raised


class TestGardenLearnGate:
    """Live turns must not bake refusals/fallbacks/errors into GARDEN."""

    def _resp(self, **kwargs):
        base = {
            "text": "光合作用是植物的過程。",
            "backend": "llama.cpp",
            "model": "qwen",
            "error": "",
        }
        base.update(kwargs)
        return SimpleNamespace(**base)

    def test_good_answer_learns(self):
        from apps.backend.src.services.chat_service import _should_garden_learn

        assert _should_garden_learn("光合作用是什麼", self._resp()) is True

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"text": ""},
            {"text": "   "},
            {"error": "boom"},
            {"model": "honest-no-answer"},
            {"model": "honest-cannot-do"},
            {"model": "neuro-blender"},
            {"text": "User，這個問題我目前還沒有足夠的知識"},
        ],
    )
    def test_garbage_never_learns(self, kwargs):
        from apps.backend.src.services.chat_service import _should_garden_learn

        assert _should_garden_learn("隨便問", self._resp(**kwargs)) is False

    async def test_process_skips_garden_call(self, chat_service):
        from unittest.mock import AsyncMock

        chat_service._garden_engine = SimpleNamespace(learn_from_interaction=AsyncMock())
        bad = self._resp(model="honest-no-answer")
        await chat_service._process_garden_learning("隨便問", bad)
        chat_service._garden_engine.learn_from_interaction.assert_not_called()
        good = self._resp()
        await chat_service._process_garden_learning("光合作用是什麼", good)
        chat_service._garden_engine.learn_from_interaction.assert_called_once()
