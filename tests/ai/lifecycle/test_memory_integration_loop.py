"""Tests for the memory integration loop module."""

import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

_MODULE_MOCKS = {}
for name, mock in _MODULE_MOCKS.items():
    if name not in sys.modules:
        sys.modules[name] = mock


@pytest.fixture
def mock_memory_manager():
    manager = MagicMock()
    manager.get_recent_memories = AsyncMock(return_value=[
        '用户喜欢听音乐',
        '用户问了关于AI的问题',
        '用户谈到了天气',
    ])
    manager.store_structured_memory = AsyncMock()
    manager.add_to_knowledge_base = AsyncMock()
    manager.generate_template = AsyncMock()
    return manager


@pytest.fixture
def mock_learning_engine():
    return MagicMock()


@pytest.fixture
def integration_loop(mock_memory_manager, mock_learning_engine):
    from ai.lifecycle.memory_integration_loop import MemoryIntegrationLoop
    return MemoryIntegrationLoop(
        memory_manager=mock_memory_manager,
        learning_engine=mock_learning_engine,
        loop_interval=180.0,
    )


class TestMemoryInfo:
    """Tests for MemoryInfo dataclass."""

    def test_memory_info_creation(self):
        from ai.lifecycle.memory_integration_loop import MemoryInfo
        now = datetime.now()
        info = MemoryInfo(
            content='User likes music',
            type='conversation',
            timestamp=now,
            importance=0.7,
        )
        assert info.content == 'User likes music'
        assert info.type == 'conversation'
        assert info.importance == 0.7
        assert not info.structured
        assert not info.integrated

    def test_memory_info_to_dict(self):
        from ai.lifecycle.memory_integration_loop import MemoryInfo
        now = datetime.now()
        info = MemoryInfo(
            content='Test content',
            type='question',
            timestamp=now,
            importance=0.9,
            structured=True,
            integrated=True,
        )
        result = info.to_dict()
        assert result['content'] == 'Test content'
        assert result['type'] == 'question'
        assert result['importance'] == 0.9
        assert result['structured'] is True
        assert result['integrated'] is True

    def test_memory_info_defaults(self):
        from ai.lifecycle.memory_integration_loop import MemoryInfo
        info = MemoryInfo(
            content='Default test',
            type='general',
            timestamp=datetime.now(),
        )
        assert info.importance == 0.5
        assert not info.structured
        assert not info.integrated


class TestKnowledgePattern:
    """Tests for KnowledgePattern dataclass."""

    def test_pattern_creation(self):
        from ai.lifecycle.memory_integration_loop import KnowledgePattern
        now = datetime.now()
        pattern = KnowledgePattern(
            pattern='AI',
            frequency=5,
            confidence=0.7,
            last_seen=now,
            examples=['AI is great', 'Learning AI'],
        )
        assert pattern.pattern == 'AI'
        assert pattern.frequency == 5
        assert pattern.confidence == 0.7
        assert len(pattern.examples) == 2

    def test_pattern_to_dict(self):
        from ai.lifecycle.memory_integration_loop import KnowledgePattern
        now = datetime.now()
        pattern = KnowledgePattern(
            pattern='music',
            frequency=3,
            confidence=0.5,
            last_seen=now,
            examples=['likes music'],
        )
        result = pattern.to_dict()
        assert result['pattern'] == 'music'
        assert result['frequency'] == 3
        assert result['confidence'] == 0.5


class TestMemoryIntegrationLoopInit:
    """Tests for MemoryIntegrationLoop initialization."""

    def test_init_defaults(self, integration_loop):
        assert not integration_loop.is_running
        assert integration_loop.loop_interval == 180.0
        assert integration_loop.memory_infos == []
        assert integration_loop.integration_queue == []
        assert integration_loop.knowledge_patterns == {}
        assert integration_loop.stats['total_memories'] == 0
        assert integration_loop.stats['structured_memories'] == 0
        assert integration_loop.stats['integrated_memories'] == 0
        assert integration_loop.stats['patterns_found'] == 0

    def test_init_with_custom_values(self, mock_memory_manager, mock_learning_engine):
        from ai.lifecycle.memory_integration_loop import MemoryIntegrationLoop
        loop = MemoryIntegrationLoop(
            memory_manager=mock_memory_manager,
            learning_engine=mock_learning_engine,
            loop_interval=300.0,
            min_loop_interval=200.0,
            max_loop_interval=600.0,
        )
        assert loop.loop_interval == 300.0
        assert loop.min_loop_interval == 200.0
        assert loop.max_loop_interval == 600.0
    async def test_start_stop(self, integration_loop):
        await integration_loop.start()
        assert integration_loop.is_running
        assert integration_loop._integration_task is not None
        await integration_loop.stop()
        assert not integration_loop.is_running
    async def test_start_when_already_running(self, integration_loop):
        await integration_loop.start()
        await integration_loop.start()
        assert integration_loop.is_running
        await integration_loop.stop()
    async def test_stop_when_not_running(self, integration_loop):
        await integration_loop.stop()
        assert not integration_loop.is_running


class TestAddMemory:
    """Tests for add_memory method."""

    def test_add_memory(self, integration_loop):
        integration_loop.add_memory('Test memory', 'general', 0.7)
        assert len(integration_loop.memory_infos) == 1
        assert len(integration_loop.integration_queue) == 1
        assert integration_loop.stats['total_memories'] == 1
        info = integration_loop.memory_infos[0]
        assert info.content == 'Test memory'
        assert info.type == 'general'
        assert info.importance == 0.7

    def test_add_memory_defaults(self, integration_loop):
        integration_loop.add_memory('Default memory')
        assert len(integration_loop.memory_infos) == 1
        info = integration_loop.memory_infos[0]
        assert info.type == 'general'
        assert info.importance == 0.5


class TestCollectNewInfo:
    """Tests for collecting new information."""
    async def test_collect_new_info_from_memory_manager(self, integration_loop, mock_memory_manager):
        await integration_loop._collect_new_info()
        assert len(integration_loop.memory_infos) == 3
        assert len(integration_loop.integration_queue) == 3
        assert integration_loop.stats['total_memories'] == 3
    async def test_collect_new_info_skips_duplicates(self, integration_loop, mock_memory_manager):
        await integration_loop._collect_new_info()
        assert integration_loop.stats['total_memories'] == 3
        await integration_loop._collect_new_info()  # same content, should skip
        assert integration_loop.stats['total_memories'] == 3
    async def test_collect_new_info_without_memory_method(self, mock_learning_engine):
        from ai.lifecycle.memory_integration_loop import MemoryIntegrationLoop
        bare_manager = MagicMock(spec=[])  # no get_recent_memories
        loop = MemoryIntegrationLoop(
            memory_manager=bare_manager,
            learning_engine=mock_learning_engine,
        )
        await loop._collect_new_info()
        assert len(loop.memory_infos) == 0
    async def test_collect_new_info_limits_count(self, integration_loop, mock_memory_manager):
        integration_loop.max_infos = 2
        mock_memory_manager.get_recent_memories.return_value = [
            'memory1', 'memory2', 'memory3',
        ]
        await integration_loop._collect_new_info()
        assert len(integration_loop.memory_infos) <= 2


class TestAnalyzePatterns:
    """Tests for pattern analysis."""
    async def test_analyze_patterns_finds_keywords(self, integration_loop):
        from ai.lifecycle.memory_integration_loop import MemoryInfo

        # Add enough memory info with repeated keywords
        now = datetime.now()
        for content in ['用户话题 音乐话题 喜欢', '用户话题 编程话题 喜欢', '用户话题 AI 喜欢']:
            integration_loop.memory_infos.append(MemoryInfo(
                content=content, type='conversation', timestamp=now,
            ))
        await integration_loop._analyze_patterns()
        assert any('keyword_用户话题' in k or 'keyword_喜欢' in k for k in integration_loop.knowledge_patterns)
    async def test_analyze_patterns_updates_existing(self, integration_loop):
        from ai.lifecycle.memory_integration_loop import KnowledgePattern, MemoryInfo
        now = datetime.now()
        # Pre-populate with a pattern
        integration_loop.knowledge_patterns['keyword_python'] = KnowledgePattern(
            pattern='python', frequency=2, confidence=0.3,
            last_seen=now, examples=['python is cool'],
        )
        for content in ['python python test', 'python python fun', 'python python everywhere']:
            integration_loop.memory_infos.append(MemoryInfo(
                content=content, type='conversation', timestamp=now,
            ))
        await integration_loop._analyze_patterns()
        assert integration_loop.knowledge_patterns['keyword_python'].frequency > 2
        assert integration_loop.knowledge_patterns['keyword_python'].confidence > 0.3
    async def test_analyze_patterns_ignores_short_words(self, integration_loop):
        from ai.lifecycle.memory_integration_loop import MemoryInfo
        now = datetime.now()
        integration_loop.memory_infos.append(MemoryInfo(
            content='a b c d e', type='conversation', timestamp=now,
        ))
        await integration_loop._analyze_patterns()
        # No word > 2 chars should appear
        assert len(integration_loop.knowledge_patterns) == 0
    async def test_analyze_patterns_handles_exception(self, integration_loop):
        integration_loop.add_memory('test test test', 'conversation', 0.5)
        with patch.object(integration_loop.memory_infos[0], 'content', 123):
            await integration_loop._analyze_patterns()  # should not raise
        assert len(integration_loop.knowledge_patterns) == 0


class TestStructureMemory:
    """Tests for memory structuring."""
    async def test_structure_memory_processes_queue(self, integration_loop, mock_memory_manager):
        from ai.lifecycle.memory_integration_loop import MemoryInfo
        now = datetime.now()
        info = MemoryInfo(content='Test content', type='conversation', timestamp=now)
        integration_loop.integration_queue.append(info)
        await integration_loop._structure_memory()
        assert info.structured is True
        assert integration_loop.stats['structured_memories'] == 1
    async def test_structure_memory_skips_already_structured(self, integration_loop, mock_memory_manager):
        from ai.lifecycle.memory_integration_loop import MemoryInfo
        now = datetime.now()
        info = MemoryInfo(content='Test', type='conversation', timestamp=now, structured=True)
        integration_loop.integration_queue.append(info)
        await integration_loop._structure_memory()
        assert integration_loop.stats['structured_memories'] == 0
    async def test_structure_memory_limits_batch(self, integration_loop, mock_memory_manager):
        from ai.lifecycle.memory_integration_loop import MemoryInfo
        now = datetime.now()
        for i in range(15):
            integration_loop.integration_queue.append(MemoryInfo(
                content=f'Test {i}', type='conversation', timestamp=now,
            ))
        await integration_loop._structure_memory()
        assert integration_loop.stats['structured_memories'] == 10  # max 10 per call
    async def test_structure_memory_without_manager_method(self, mock_learning_engine):
        from ai.lifecycle.memory_integration_loop import MemoryInfo, MemoryIntegrationLoop
        bare_manager = MagicMock(spec=[])
        now = datetime.now()
        loop = MemoryIntegrationLoop(
            memory_manager=bare_manager, learning_engine=mock_learning_engine,
        )
        loop.integration_queue.append(MemoryInfo(
            content='Test', type='conversation', timestamp=now,
        ))
        await loop._structure_memory()
        # Info still gets structured=True even without manager method
        assert loop.stats['structured_memories'] == 1

    def test_simple_structure(self, integration_loop):
        result = integration_loop._simple_structure('Hello world. This is a test')
        assert result['word_count'] == 6
        assert result['sentence_count'] == 2
        assert 'Hello' in result['keywords']


class TestUpdateKnowledgeBase:
    """Tests for knowledge base updates."""
    async def test_update_knowledge_base_integrates_structured(self, integration_loop, mock_memory_manager):
        from ai.lifecycle.memory_integration_loop import MemoryInfo
        now = datetime.now()
        info = MemoryInfo(
            content='Test memory', type='conversation',
            timestamp=now, structured=True, integrated=False,
        )
        integration_loop.integration_queue.append(info)
        await integration_loop._update_knowledge_base()
        assert info.integrated is True
        assert integration_loop.stats['integrated_memories'] == 1
        assert integration_loop.stats['knowledge_base_updates'] == 1
    async def test_update_knowledge_base_skips_unstructured(self, integration_loop, mock_memory_manager):
        from ai.lifecycle.memory_integration_loop import MemoryInfo
        now = datetime.now()
        info = MemoryInfo(
            content='Test', type='conversation', timestamp=now,
            structured=False, integrated=False,
        )
        integration_loop.integration_queue.append(info)
        await integration_loop._update_knowledge_base()
        assert not info.integrated
        assert integration_loop.stats['integrated_memories'] == 0
    async def test_update_knowledge_base_cleans_up(self, integration_loop, mock_memory_manager):
        from ai.lifecycle.memory_integration_loop import MemoryInfo
        now = datetime.now()
        integrated = MemoryInfo(
            content='Done', type='conversation', timestamp=now,
            structured=True, integrated=True,
        )
        pending = MemoryInfo(
            content='Pending', type='conversation', timestamp=now,
            structured=True, integrated=False,
        )
        integration_loop.integration_queue.extend([integrated, pending])
        await integration_loop._update_knowledge_base()
        assert pending not in integration_loop.integration_queue  # should be removed
        assert integrated not in integration_loop.integration_queue  # removed too
    async def test_update_knowledge_base_without_manager_method(self, mock_learning_engine):
        from ai.lifecycle.memory_integration_loop import MemoryInfo, MemoryIntegrationLoop
        bare_manager = MagicMock(spec=[])
        now = datetime.now()
        loop = MemoryIntegrationLoop(
            memory_manager=bare_manager, learning_engine=mock_learning_engine,
        )
        info = MemoryInfo(
            content='Test', type='conversation', timestamp=now,
            structured=True, integrated=False,
        )
        loop.integration_queue.append(info)
        await loop._update_knowledge_base()
        # Info gets integrated=True even without manager
        assert info.integrated is True


class TestGenerateTemplates:
    """Tests for template generation."""
    async def test_generate_templates_high_confidence(self, integration_loop, mock_memory_manager):
        from ai.lifecycle.memory_integration_loop import KnowledgePattern
        now = datetime.now()
        for i in range(6):  # need > 5 patterns
            integration_loop.knowledge_patterns[f'keyword_word{i}'] = KnowledgePattern(
                pattern=f'word{i}', frequency=5, confidence=0.7,
                last_seen=now, examples=[f'example {i}'],
            )
        await integration_loop._generate_templates()
        assert mock_memory_manager.generate_template.call_count == 3  # max 3 per call
        assert integration_loop.stats['templates_generated'] == 3
    async def test_generate_templates_few_patterns(self, integration_loop, mock_memory_manager):
        from ai.lifecycle.memory_integration_loop import KnowledgePattern
        now = datetime.now()
        integration_loop.knowledge_patterns['keyword_AI'] = KnowledgePattern(
            pattern='AI', frequency=3, confidence=0.5,
            last_seen=now, examples=['AI example'],
        )
        await integration_loop._generate_templates()
        assert integration_loop.stats['templates_generated'] == 0
        mock_memory_manager.generate_template.assert_not_called()
    async def test_generate_templates_low_confidence(self, integration_loop, mock_memory_manager):
        from ai.lifecycle.memory_integration_loop import KnowledgePattern
        now = datetime.now()
        for i in range(6):
            integration_loop.knowledge_patterns[f'keyword_word{i}'] = KnowledgePattern(
                pattern=f'word{i}', frequency=1, confidence=0.2,
                last_seen=now, examples=[f'example {i}'],
            )
        await integration_loop._generate_templates()
        assert integration_loop.stats['templates_generated'] == 0  # all below 0.6


class TestCalculateInterval:
    """Tests for interval calculation."""

    def test_interval_large_queue(self, integration_loop):
        integration_loop.integration_queue = list(range(60))
        interval = integration_loop._calculate_interval()
        assert interval == integration_loop.min_loop_interval

    def test_interval_medium_queue(self, integration_loop):
        integration_loop.integration_queue = list(range(30))
        interval = integration_loop._calculate_interval()
        assert interval == integration_loop.loop_interval

    def test_interval_small_queue(self, integration_loop):
        integration_loop.integration_queue = list(range(10))
        interval = integration_loop._calculate_interval()
        assert interval == integration_loop.max_loop_interval


class TestStatsAndGetters:
    """Tests for statistics and getter methods."""

    def test_get_memory_infos(self, integration_loop):
        from ai.lifecycle.memory_integration_loop import MemoryInfo
        now = datetime.now()
        for i in range(5):
            integration_loop.memory_infos.append(MemoryInfo(
                content=f'Info {i}', type='general', timestamp=now,
            ))
        infos = integration_loop.get_memory_infos(limit=3)
        assert len(infos) == 3
        for entry in infos:
            assert 'content' in entry
            assert 'type' in entry

    def test_get_patterns(self, integration_loop):
        from ai.lifecycle.memory_integration_loop import KnowledgePattern
        now = datetime.now()
        integration_loop.knowledge_patterns['keyword_test'] = KnowledgePattern(
            pattern='test', frequency=5, confidence=0.8,
            last_seen=now, examples=['test example'],
        )
        patterns = integration_loop.get_patterns(limit=5)
        assert 'keyword_test' in patterns

    def test_get_patterns_sorts_by_confidence(self, integration_loop):
        from ai.lifecycle.memory_integration_loop import KnowledgePattern
        now = datetime.now()
        integration_loop.knowledge_patterns['low'] = KnowledgePattern(
            pattern='low', frequency=1, confidence=0.2,
            last_seen=now, examples=['low'],
        )
        integration_loop.knowledge_patterns['high'] = KnowledgePattern(
            pattern='high', frequency=5, confidence=0.9,
            last_seen=now, examples=['high'],
        )
        patterns = integration_loop.get_patterns(limit=5)
        # Should be sorted by confidence descending
        keys = list(patterns.keys())
        assert keys[0] == 'high'  # highest confidence first

    def test_get_stats(self, integration_loop):
        stats = integration_loop.get_stats()
        assert 'is_running' in stats
        assert 'total_memories' in stats
        assert 'structured_memories' in stats
        assert 'integrated_memories' in stats
        assert 'patterns_found' in stats
        assert 'templates_generated' in stats
        assert 'pending_integrations' in stats
        assert 'patterns_count' in stats
