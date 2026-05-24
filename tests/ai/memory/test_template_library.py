import pytest

from apps.backend.src.ai.memory.template_library import (
    TemplateLibrary,
    PredefinedTemplate,
    get_template_library,
)
from apps.backend.src.ai.memory.memory_template import (
    MemoryTemplate,
    ResponseCategory,
    AngelaState,
    UserImpression,
)


class TestPredefinedTemplate:

    def test_members(self):
        assert PredefinedTemplate.GREETING_MORNING.value == 'greeting_morning'
        assert PredefinedTemplate.GREETING_GENERAL.value == 'greeting_general'
        assert PredefinedTemplate.FAREWELL_GENERAL.value == 'farewell_general'
        assert PredefinedTemplate.UNKNOWN.value == 'unknown'

    def test_count(self):
        assert len(PredefinedTemplate) == 46


class TestTemplateLibraryInit:

    def test_init_populates_templates(self):
        lib = TemplateLibrary()
        count = lib.get_template_count()
        assert count > 0
        assert count == 45

    def test_init_contains_known_ids(self):
        lib = TemplateLibrary()
        assert lib.get_by_id('greeting_morning').id == 'greeting_morning'
        assert lib.get_by_id('farewell_general').id == 'farewell_general'
        assert lib.get_by_id('comfort_sad').id == 'comfort_sad'


class TestTemplateLibraryGet:

    @pytest.fixture
    def lib(self):
        return TemplateLibrary()

    def test_get_all_templates(self, lib):
        templates = lib.get_all_templates()
        assert len(templates) == 45
        ids = [t.id for t in templates]
        assert 'greeting_morning' in ids
        assert 'farewell_general' in ids
        assert 'comfort_sad' in ids

    def test_get_by_id_exists(self, lib):
        tpl = lib.get_by_id('greeting_general')
        assert tpl is not None
        assert tpl.content == '你好呀！见到你真开心~'

    def test_get_by_id_missing(self, lib):
        tpl = lib.get_by_id('nonexistent')
        assert tpl is None

    def test_get_by_category_greeting(self, lib):
        templates = lib.get_by_category(ResponseCategory.GREETING)
        assert len(templates) == 6
        assert all(t.category == ResponseCategory.GREETING for t in templates)

    def test_get_by_category_emotional(self, lib):
        templates = lib.get_by_category(ResponseCategory.EMOTIONAL)
        assert all(t.category == ResponseCategory.EMOTIONAL for t in templates)

    def test_get_by_category_empty(self, lib):
        templates = lib.get_by_category(ResponseCategory.RESEARCH)
        assert templates == []

    def test_get_template_count(self, lib):
        assert lib.get_template_count() == 45


class TestTemplateLibraryCategoryCounts:

    @pytest.fixture
    def lib(self):
        return TemplateLibrary()

    def test_get_category_counts(self, lib):
        counts = lib.get_category_counts()
        assert sum(counts.values()) == 45
        assert ResponseCategory.GREETING in counts
        assert ResponseCategory.FAREWELL in counts
        assert ResponseCategory.EMOTIONAL in counts
        assert ResponseCategory.SMALL_TALK in counts
        assert ResponseCategory.AFFIRMATION in counts
        assert ResponseCategory.NEGATION in counts
        assert ResponseCategory.CURIOSITY in counts
        assert ResponseCategory.INTIMACY in counts
        assert ResponseCategory.HELP in counts

    def test_greeting_count(self, lib):
        assert lib.get_category_counts()[ResponseCategory.GREETING] == 6


class TestTemplateLibraryAddRemove:

    @pytest.fixture
    def lib(self):
        return TemplateLibrary()

    def test_add_custom_template(self, lib):
        tpl = MemoryTemplate(
            id='custom_1',
            category=ResponseCategory.QUESTION,
            content='custom content',
        )
        before = lib.get_template_count()
        lib.add_custom_template(tpl)
        assert lib.get_template_count() == before + 1
        assert lib.get_by_id('custom_1').id == 'custom_1'

    def test_add_custom_template_overwrite(self, lib):
        tpl = MemoryTemplate(
            id='greeting_morning',
            category=ResponseCategory.QUESTION,
            content='overwritten',
        )
        lib.add_custom_template(tpl)
        fetched = lib.get_by_id('greeting_morning')
        assert fetched.category == ResponseCategory.QUESTION

    def test_remove_template_exists(self, lib):
        before = lib.get_template_count()
        result = lib.remove_template('greeting_morning')
        assert result is True
        assert lib.get_template_count() == before - 1
        assert lib.get_by_id('greeting_morning') is None

    def test_remove_template_missing(self, lib):
        result = lib.remove_template('nonexistent')
        assert result is False

    @pytest.mark.asyncio
    async def test_add_custom_template_async(self, lib):
        tpl = MemoryTemplate(
            id='async_custom',
            category=ResponseCategory.FAREWELL,
            content='async test',
        )
        before = lib.get_template_count()
        await lib.add_custom_template_async(tpl)
        assert lib.get_template_count() == before + 1
        assert lib.get_by_id('async_custom') is not None


class TestTemplateLibrarySingleton:

    def test_get_template_library_singleton(self):
        lib1 = get_template_library()
        lib2 = get_template_library()
        assert lib1 is lib2

    def test_singleton_is_template_library(self):
        lib = get_template_library()
        assert lib.get_template_count() == 45
