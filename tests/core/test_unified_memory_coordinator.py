"""C1 — UnifiedMemoryCoordinator unit tests"""

import sys, asyncio
sys.path.insert(0, 'apps/backend/src')


class TestUnifiedMemoryCoordinator:

    def setup_method(self):
        from ai.lifecycle.unified_memory_coordinator import UnifiedMemoryCoordinator
        self.c = UnifiedMemoryCoordinator()

    def test_empty_coordinator(self):
        assert self.c.logic_unit is None
        assert self.c.cdm_model is None
        assert self.c.memory_manager is None

    def test_empty_query(self):
        q = asyncio.run(self.c.unified_query())
        assert q['memories'] == []
        assert q['rule_action'] is None
        assert 'cognitive_stats' in q

    def test_empty_store(self):
        mid = asyncio.run(self.c.store_experience('data', 'test'))
        assert mid is None

    def test_empty_evaluate_rules(self):
        assert self.c.evaluate_rules({'x': 1}) is None

    def test_empty_get_stats(self):
        stats = self.c.get_stats()
        assert stats['ham']['connected'] is False
        assert stats['lu']['connected'] is False
        assert stats['cdm']['connected'] is False

    def test_with_mock_ham(self):
        from ai.lifecycle.unified_memory_coordinator import UnifiedMemoryCoordinator

        class MockHAM:
            async def query_core_memory(self, keywords=None, limit=10):
                return ['mem1', 'mem2']

            async def store_experience(self, raw_data, data_type, metadata=None, *a, **kw):
                return 'mid_001'

        c2 = UnifiedMemoryCoordinator(memory_manager=MockHAM())
        q = asyncio.run(c2.unified_query(keywords=['test']))
        assert len(q['memories']) == 2
        assert q['memories'] == ['mem1', 'mem2']

        stats = c2.get_stats()
        assert stats['ham']['connected'] is True

        mid = asyncio.run(c2.store_experience('x', 'test'))
        assert mid == 'mid_001'

    def test_with_mock_lu(self):
        from ai.lifecycle.unified_memory_coordinator import UnifiedMemoryCoordinator

        class MockLU:
            def evaluate(self, context):
                return 'rule_result'

            def list_rules(self):
                return ['r1', 'r2']

        c2 = UnifiedMemoryCoordinator(logic_unit=MockLU())
        assert c2.evaluate_rules({'t': 1}) == 'rule_result'

        q = asyncio.run(c2.unified_query(context={'t': 1}))
        assert q['rule_action'] == 'rule_result'

        stats = c2.get_stats()
        assert stats['lu']['connected'] is True
        assert stats['lu']['rule_count'] == 2

    def test_with_mock_cdm(self):
        from ai.lifecycle.unified_memory_coordinator import UnifiedMemoryCoordinator

        class MockCDM:
            def get_conversion_statistics(self):
                return {'avg': 0.7, 'trend': 'improving'}

            def record_investment(self, *args, **kwargs):
                pass

        c2 = UnifiedMemoryCoordinator(cdm_model=MockCDM())
        q = asyncio.run(c2.unified_query())
        assert q['cognitive_stats']['avg'] == 0.7
        assert q['cognitive_stats']['trend'] == 'improving'

        stats = c2.get_stats()
        assert stats['cdm']['connected'] is True

    def test_full_integration_mocks(self):
        from ai.lifecycle.unified_memory_coordinator import UnifiedMemoryCoordinator

        class MockHAM:
            async def query_core_memory(self, keywords=None, limit=10):
                return [{'id': 'm1', 'content': 'memory data'}]

            async def store_experience(self, raw_data, data_type, metadata=None, *a, **kw):
                return 'mid_002'

        class MockLU:
            def evaluate(self, context):
                return 'matched_rule'

            def list_rules(self):
                return ['r1']

        class MockCDM:
            def get_conversion_statistics(self):
                return {'avg': 0.85, 'trend': 'improving', 'total': 100}

            def record_investment(self, *args, **kwargs):
                pass

        c2 = UnifiedMemoryCoordinator(
            memory_manager=MockHAM(),
            logic_unit=MockLU(),
            cdm_model=MockCDM(),
        )

        q = asyncio.run(c2.unified_query(
            keywords=['hello'],
            context={'user': 'test'},
        ))
        assert len(q['memories']) == 1
        assert q['rule_action'] == 'matched_rule'
        assert q['cognitive_stats']['avg'] == 0.85
