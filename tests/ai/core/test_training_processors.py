"""
The training queue must have a producer and a consumer.

WHY: the "sorted training execution" path (REFACTOR_PLAN §13.4) was fully
implemented — priority queue, worker, defer-on-missing-owner semantics, tests —
and completely unreachable in production, in two independent ways:

  1. **No producer.** ``mainline_dispatcher.dispatch()`` had no caller anywhere
     outside tests, so the queue never received a sample.
  2. **No consumer.** No processor was registered, so even a queued sample was
     deferred forever.
  3. **Untrainable data.** The queued sample was ``{"input": text, "time": …}``
     with no assistant reply, so no trainer could have learned from it anyway —
     it would have taught "input → nothing".

These tests pin all three: a train request enqueues a complete pair, a domain
owner is registered for every domain the coordinator can queue, and the processor
rejects incomplete samples instead of pretending to train.
"""

import os
import re
from types import SimpleNamespace

import pytest

REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
BACKEND_SRC = os.path.join(REPO_ROOT, "apps", "backend", "src")


class TestDispatcherProducesTrainableSamples:
    def test_train_request_without_response_enqueues_nothing(self):
        from ai.core.training_coordinator import TrainingCoordinator
        from services.mainline_dispatcher import DispatchIntent, dispatch

        tc = TrainingCoordinator()
        decision = dispatch({"text": "訓練這個模式"}, training_coordinator=tc)

        assert decision.intent is DispatchIntent.TRAIN
        assert tc.pending_training_count() == 0, (
            "an input-only sample cannot be trained on; queueing it filled the "
            "queue with rows no processor could ever act on"
        )

    def test_train_request_with_response_enqueues_a_complete_pair(self):
        from ai.core.training_coordinator import TrainingCoordinator
        from services.mainline_dispatcher import DispatchIntent, dispatch

        tc = TrainingCoordinator()
        decision = dispatch(
            {"text": "訓練這個模式"},
            training_coordinator=tc,
            response_text="好，我會記住這個模式。",
        )

        assert decision.intent is DispatchIntent.TRAIN
        assert tc.pending_training_count() == 1
        item = tc.drain_priority_queue()[0]
        assert item["sample"]["input"] == "訓練這個模式"
        assert item["sample"]["output"] == "好，我會記住這個模式。"

    def test_plain_chat_never_enqueues(self):
        from ai.core.training_coordinator import TrainingCoordinator
        from services.mainline_dispatcher import dispatch

        tc = TrainingCoordinator()
        dispatch({"text": "今天天氣如何"}, training_coordinator=tc, response_text="晴。")
        assert tc.pending_training_count() == 0

    def test_plan_actions_omits_train_without_output(self):
        from services.mainline_dispatcher import ActionType, build_envelope, plan_actions

        env = build_envelope({"text": "訓練我"})
        without = {a.action for a in plan_actions(env)}
        with_output = {a.action for a in plan_actions(env, response_text="收到。")}
        assert ActionType.TRAIN not in without
        assert ActionType.TRAIN in with_output


class TestProcessorsAreRegistered:
    def test_every_coordinator_domain_has_a_processor(self):
        from ai.core.training_coordinator import DOMAIN_OWNERSHIP, TrainingCoordinator
        from ai.core.training_processors import register_default_processors

        tc = TrainingCoordinator()
        assert tc.registered_domains() == [], "precondition: nothing registered yet"

        registered = register_default_processors(tc)

        assert sorted(registered) == sorted(DOMAIN_OWNERSHIP)
        missing = set(DOMAIN_OWNERSHIP) - set(tc.registered_domains())
        assert not missing, f"domains whose samples would defer forever: {missing}"

    def test_registration_is_idempotent(self):
        from ai.core.training_coordinator import TrainingCoordinator
        from ai.core.training_processors import register_default_processors

        tc = TrainingCoordinator()
        register_default_processors(tc)
        register_default_processors(tc)
        assert len(tc.registered_domains()) == len(set(tc.registered_domains()))

    @pytest.mark.asyncio
    async def test_processor_rejects_incomplete_samples(self):
        from ai.core.training_processors import continuous_learning_processor

        with pytest.raises(ValueError):
            await continuous_learning_processor({"input": "x"})
        with pytest.raises(ValueError):
            await continuous_learning_processor({"output": "y"})

    @pytest.mark.asyncio
    async def test_queued_sample_reaches_the_live_learner(self, monkeypatch):
        """End to end: queue → worker → the live learning owner.

        The owner is Backbone.trigger_learning — what the chat pipeline itself
        uses. ContinuousLearningPipeline is NOT the target: it is only built when
        ANGELA_LEGACY_ED3N=1, so pointing at it fails on every sample in a normal
        run (found by probing a live server).
        """
        from ai.core.training_coordinator import TrainingCoordinator
        from ai.core.training_processors import register_default_processors

        seen = []

        class _FakeBackbone:
            async def trigger_learning(self, user_message, response, context):
                seen.append((user_message, response.text))
                return {"garden": {"status": "PAIRED"}}

        monkeypatch.setattr("core.backbone.get_backbone", lambda: _FakeBackbone())

        tc = TrainingCoordinator()
        register_default_processors(tc)
        tc.enqueue("general", {"input": "我喜歡喝拿鐵", "output": "我也是"}, priority=0.9)

        stats = await tc.process_pending_training()

        assert stats["processed"] == 1
        assert stats["deferred"] == 0, "a registered domain must never defer"
        assert seen == [("我喜歡喝拿鐵", "我也是")]
        assert tc.pending_training_count() == 0

    @pytest.mark.asyncio
    async def test_processor_does_not_target_the_disabled_legacy_pipeline(self):
        """ANGELA_LEGACY_ED3N=1 is required to build ContinuousLearningPipeline."""
        from pathlib import Path

        source = Path(__file__).resolve()
        backend_src = Path(os.path.join(REPO_ROOT, "apps", "backend", "src"))
        processor = (backend_src / "ai/core/training_processors.py").read_text(encoding="utf-8")
        # Ignore prose (the module docstring explains why): only *calls* matter.
        code_lines = re.findall(
            r"^\s*(?:from|import)\s+.*ContinuousLearningPipeline.*$", processor, re.M
        ) + re.findall(r"^\s*\w*\.?_?continuous_learning_pipeline\w*\s*\(.*$", processor, re.M)
        assert not code_lines, (
            "the processor must not call the opt-in legacy pipeline: " f"{code_lines}"
        )
        chat_service = (backend_src / "services/chat_service.py").read_text(encoding="utf-8")
        assert 'ANGELA_LEGACY_ED3N") == "1"' in chat_service, (
            "precondition: the legacy pipeline is opt-in, which is why the "
            "processor must use the backbone instead"
        )
        assert source.exists()

    @pytest.mark.asyncio
    async def test_learner_failure_surfaces_as_a_failed_sample(self, monkeypatch):
        """A learner that reports ERROR must not look like a success."""
        from ai.core.training_coordinator import TrainingCoordinator
        from ai.core.training_processors import register_default_processors

        class _FailingBackbone:
            async def trigger_learning(self, user_message, response, context):
                return {"garden": {"status": "ERROR", "error": "engine not loaded"}}

        monkeypatch.setattr("core.backbone.get_backbone", lambda: _FailingBackbone())
        tc = TrainingCoordinator()
        register_default_processors(tc)
        tc.enqueue("general", {"input": "a", "output": "b"})

        stats = await tc.process_pending_training()

        assert stats["failed"] == 1
        assert stats["processed"] == 0

    @pytest.mark.asyncio
    async def test_failure_is_counted_not_swallowed(self, monkeypatch):
        from ai.core.training_coordinator import TrainingCoordinator
        from ai.core.training_processors import register_default_processors

        monkeypatch.setattr("core.backbone.get_backbone", lambda: None)
        tc = TrainingCoordinator()
        register_default_processors(tc)
        tc.enqueue("general", {"input": "a", "output": "b"})

        stats = await tc.process_pending_training()

        assert stats["failed"] == 1
        assert stats["processed"] == 0


class TestProductionWiring:
    def test_chat_service_hands_train_requests_to_the_queue(self):
        source = open(
            os.path.join(BACKEND_SRC, "services", "chat_service.py"), encoding="utf-8"
        ).read()
        learning = source[source.index("async def _process_learning") :]
        learning = learning[: learning.index("async def _process_continuous_learning")]
        assert (
            "mainline_dispatcher" in learning
        ), "nothing produced queue samples in production before this"
        assert "response_text=response.text" in learning

    def test_lifespan_registers_processors_before_starting_the_worker(self):
        source = open(os.path.join(BACKEND_SRC, "api", "lifespan.py"), encoding="utf-8").read()
        block = source[source.index("TrainingCoordinator owns training execution") :]
        block = block[: block.index("except Exception:")]
        assert "register_default_processors" in block
        assert block.index("register_default_processors") < block.index(
            "start_training_worker"
        ), "processors must exist before the worker starts dispatching"


class TestTrainingOutcomeIsHonest:
    """A queued sample is not a trained model — the reply must say which it is."""

    def _service(self):
        from services.chat_service import ChatService

        svc = ChatService()
        svc._initialized = True
        return svc

    def test_learning_status_reflects_the_opt_in_engines(self):
        svc = self._service()
        status = svc.learning_status()
        assert status == {
            "continuous": False,
            "garden": False,
            "active": False,
            "enable_env": "ANGELA_LEGACY_ED3N",
        }
        svc._garden_engine = object()
        assert svc.learning_status()["active"] is True

    def test_train_request_without_learners_says_so(self):
        from core.interfaces.protocols import LLMResponse

        svc = self._service()
        response = LLMResponse(text="好，我會記住。")
        context = {}
        svc._apply_training_outcome(response, context)

        assert "不會真的訓練模型" in response.text
        assert "ANGELA_LEGACY_ED3N=1" in response.text
        assert context["_training_effective"] is False
        assert context["_training_requested"] is True

    def test_train_request_with_learners_confirms_queueing(self):
        from core.interfaces.protocols import LLMResponse

        svc = self._service()
        svc._garden_engine = object()
        response = LLMResponse(text="好。")
        context = {}
        svc._apply_training_outcome(response, context)

        assert "訓練佇列" in response.text
        assert "不會真的訓練模型" not in response.text
        assert context["_training_effective"] is True

    def test_note_is_not_appended_twice(self):
        from core.interfaces.protocols import LLMResponse

        svc = self._service()
        response = LLMResponse(text="好。")
        svc._apply_training_outcome(response, {})
        once = response.text
        svc._apply_training_outcome(response, {})
        assert response.text == once


def _async_return(value):
    async def _inner():
        return value

    return _inner
