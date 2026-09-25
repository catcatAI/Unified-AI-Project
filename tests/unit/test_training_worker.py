"""
TrainingCoordinator execution ownership (REFACTOR_PLAN §13.4).

The ingest path only enqueues. The coordinator's own worker dispatches queued
samples to the processor registered by each domain owner, and defers samples
whose domain has no owner yet instead of dropping them silently.
"""

import asyncio

import pytest


class TestTrainingWorker:
    def test_enqueue_is_bounded_and_drops_lowest_priority(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator(max_train_queue=3)
        for index in range(5):
            tc.enqueue("knowledge", {"input": f"sample-{index}"}, priority=index / 10.0)

        assert tc.pending_training_count() == 3
        drained = tc.drain_priority_queue()
        assert [item["sample"]["input"] for item in drained] == [
            "sample-4",
            "sample-3",
            "sample-2",
        ]
        assert tc.get_worker_stats()["dropped"] == 2

    def test_drain_limit_keeps_remainder_ordered(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        for index in range(4):
            tc.enqueue("knowledge", {"input": f"s{index}"}, priority=index / 10.0)

        first = tc.drain_priority_queue(limit=2)

        assert [item["sample"]["input"] for item in first] == ["s3", "s2"]
        assert tc.pending_training_count() == 2
        second = tc.drain_priority_queue()
        assert [item["sample"]["input"] for item in second] == ["s1", "s0"]

    @pytest.mark.asyncio
    async def test_processor_receives_queued_sample(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        seen = []

        async def processor(sample):
            seen.append(sample)

        tc.register_processor("knowledge", processor)
        tc.enqueue("knowledge", {"input": "datasheet"}, priority=0.5)

        stats = await tc.process_pending_training()

        assert seen == [{"input": "datasheet"}]
        assert stats["processed"] == 1
        assert tc.pending_training_count() == 0

    @pytest.mark.asyncio
    async def test_sync_processor_is_supported(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        seen = []
        tc.register_processor("garden", seen.append)
        tc.enqueue("garden", {"input": "x"})

        stats = await tc.process_pending_training()

        assert seen == [{"input": "x"}]
        assert stats["processed"] == 1

    @pytest.mark.asyncio
    async def test_unowned_domain_is_deferred_not_dropped(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        tc.enqueue("knowledge", {"input": "datasheet"}, priority=0.9)

        stats = await tc.process_pending_training()

        assert stats["deferred"] == 1
        assert stats["processed"] == 0
        assert tc.pending_training_count() == 1

        seen = []
        tc.register_processor("knowledge", seen.append)
        stats = await tc.process_pending_training()
        assert stats["processed"] == 1
        assert seen == [{"input": "datasheet"}]
        assert tc.pending_training_count() == 0

    @pytest.mark.asyncio
    async def test_processor_failure_does_not_kill_worker(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()

        def boom(_sample):
            raise RuntimeError("trainer exploded")

        tc.register_processor("knowledge", boom)
        tc.enqueue("knowledge", {"input": "a"})
        tc.enqueue("knowledge", {"input": "b"})

        stats = await tc.process_pending_training()

        assert stats["failed"] == 2
        assert tc.pending_training_count() == 0
        assert tc.get_worker_stats()["failed"] == 2

    @pytest.mark.asyncio
    async def test_worker_loop_dispatches_automatically(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        done = asyncio.Event()

        async def processor(_sample):
            done.set()

        tc.register_processor("math", processor)
        tc.enqueue("math", {"input": "1+1"})

        await tc.start_training_worker(interval=0.01)
        try:
            await asyncio.wait_for(done.wait(), timeout=2.0)
        finally:
            await tc.stop_training_worker()

        assert tc.pending_training_count() == 0

    @pytest.mark.asyncio
    async def test_worker_start_and_stop_are_idempotent(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        await tc.start_training_worker(interval=0.01)
        await tc.start_training_worker(interval=0.01)
        await tc.stop_training_worker()
        await tc.stop_training_worker()

    @pytest.mark.asyncio
    async def test_dispatch_respects_priority_order(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        order = []
        tc.register_processor("knowledge", lambda sample: order.append(sample["input"]))
        tc.enqueue("knowledge", {"input": "low"}, priority=0.1)
        tc.enqueue("knowledge", {"input": "high"}, priority=0.9)
        tc.enqueue("knowledge", {"input": "mid"}, priority=0.5)

        await tc.process_pending_training()

        assert order == ["high", "mid", "low"]

    def test_registered_domains_and_unregister(self):
        from ai.core.training_coordinator import TrainingCoordinator

        tc = TrainingCoordinator()
        tc.register_processor("a", lambda _s: None)
        tc.register_processor("b", lambda _s: None)
        assert tc.registered_domains() == ["a", "b"]

        tc.unregister_processor("a")
        assert tc.registered_domains() == ["b"]
        assert tc.get_worker_stats()["domains"] == 1
