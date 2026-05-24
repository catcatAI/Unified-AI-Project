import pytest
import tempfile
from pathlib import Path
from ai.personality.personality_manager import PersonalityManager


@pytest.fixture
def pm_nonexistent():
    return PersonalityManager(profiles_dir=Path(tempfile.mkdtemp()) / "nonexistent_profiles")


def test_pm_init_nonexistent_dir(pm_nonexistent):
    assert pm_nonexistent.current_personality is None
    assert pm_nonexistent.available_profiles == {}


def test_pm_get_trait_no_personality(pm_nonexistent):
    assert pm_nonexistent.get_current_personality_trait("some.trait") is None


def test_pm_get_trait_with_default(pm_nonexistent):
    assert pm_nonexistent.get_current_personality_trait("some.trait", "fallback") == "fallback"


def test_pm_get_initial_prompt_default(pm_nonexistent):
    assert pm_nonexistent.get_initial_prompt() == "Hello!"


def test_pm_list_available_profiles_empty(pm_nonexistent):
    assert pm_nonexistent.list_available_profiles() == []


def test_pm_load_nonexistent_profile(pm_nonexistent):
    result = pm_nonexistent.load_personality("nonexistent")
    assert result is False
    assert pm_nonexistent.current_personality is None