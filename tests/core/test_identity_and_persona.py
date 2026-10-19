"""
ANGELA-MATRIX: [L3] [βγ] [B] [L0-L11]
Identity, rename and the workshop persona.

The rename used to be a set of hardcoded literals: the prompt said "You are
Angela", the reflex answers said "我是Angela AI", the TTS said "I'm Angela"
and the subtitle spoke for "Angela". Renaming an instance therefore changed
nothing the user could hear or read. These tests pin the fixed behaviour:

- the name is stored per user (one user renaming their Angela must not
  rename anybody else's);
- every surface that names the instance resolves the *current* name;
- the prompt, the reflex answers and the subtitle carry that name;
- the workshop host (Lucifaella) hands over to the named Angela, and the
  persona block says so.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


@pytest.fixture
def identity_store(tmp_path, monkeypatch):
    """Redirect the per-user identity store to a temp file."""
    from core.system.config import identity

    store_path = tmp_path / "identities.json"
    monkeypatch.setattr(identity, "IDENTITY_STORE_PATH", str(store_path))
    identity.clear_cache()
    yield store_path
    identity.clear_cache()


# --------------------------------------------------------------------------- #
# The store
# --------------------------------------------------------------------------- #
class TestIdentityStore:
    def test_default_name_comes_from_the_config(self, identity_store):
        from core.system.config.identity import get_ai_name, get_identity_profile

        assert get_ai_name() == "Angela"
        profile = get_identity_profile("someone")
        assert profile["ai_name"] == "Angela"
        assert profile["source"] == "config"
        assert profile["customized"] is False

    def test_set_and_read_back(self, identity_store):
        from core.system.config.identity import get_ai_name, get_identity_profile, set_ai_name

        set_ai_name("小安", "u1")
        assert get_ai_name("u1") == "小安"
        profile = get_identity_profile("u1")
        assert profile["ai_name"] == "小安"
        assert profile["source"] == "user"
        assert profile["customized"] is True

    def test_names_are_per_user(self, identity_store):
        from core.system.config.identity import get_ai_name, set_ai_name

        set_ai_name("小安", "u1")
        # Another user keeps the default — a rename must not be global.
        assert get_ai_name("u2") == "Angela"
        assert get_ai_name() == "Angela"

    def test_naming_back_to_the_default_clears_the_override(self, identity_store):
        from core.system.config.identity import (
            get_ai_name,
            get_identity_profile,
            set_ai_name,
        )

        set_ai_name("小安", "u1")
        set_ai_name("Angela", "u1")
        assert get_ai_name("u1") == "Angela"
        profile = get_identity_profile("u1")
        assert profile["customized"] is False

    def test_name_survives_a_fresh_read_of_the_store(self, identity_store):
        from core.system.config import identity

        identity.set_ai_name("小安", "u1")
        identity.clear_cache()  # simulates a restart
        assert identity.get_ai_name("u1") == "小安"

    @pytest.mark.parametrize("bad", ["", "   ", "x" * 40, 123, None])
    def test_invalid_names_are_rejected(self, identity_store, bad):
        from core.system.config.identity import set_ai_name

        with pytest.raises(ValueError):
            set_ai_name(bad, "u1")

    def test_control_characters_are_sanitised_not_executed(self, identity_store):
        """A newline in a name would break prompts and TTS — it is stripped."""
        from core.system.config.identity import get_ai_name, set_ai_name

        set_ai_name("bad\nname", "u1")
        assert get_ai_name("u1") == "bad name"

    def test_a_global_rename_is_refused(self, identity_store):
        from core.system.config.identity import set_ai_name

        with pytest.raises(ValueError):
            set_ai_name("小安")

    def test_clear_removes_the_override(self, identity_store):
        from core.system.config.identity import clear_ai_name, get_ai_name, set_ai_name

        set_ai_name("小安", "u1")
        clear_ai_name("u1")
        assert get_ai_name("u1") == "Angela"


# --------------------------------------------------------------------------- #
# Name resolution across the surfaces
# --------------------------------------------------------------------------- #
class TestNamePropagation:
    def test_reflex_answers_use_the_current_name(self, identity_store):
        from ai.data_eng.presets import REFLEX_PRESETS, resolve_reflex
        from core.system.config.identity import current_user, set_ai_name

        set_ai_name("小安", "u1")
        # The reflex engines are process-global: they read the current user.
        with current_user("u1"):
            assert "小安" in resolve_reflex(REFLEX_PRESETS["你是誰"])
            assert "小安" in resolve_reflex(REFLEX_PRESETS["who are you"])
            # No placeholder may leak into a served answer.
            assert "{name}" not in resolve_reflex(REFLEX_PRESETS["名字"])

    def test_the_reflex_table_never_carries_a_stale_name(self):
        from ai.data_eng.presets import REFLEX_PRESETS

        for key, value in REFLEX_PRESETS.items():
            assert "Angela" not in value, f"{key} hardcodes the old name"
            assert "安吉拉" not in value, f"{key} hardcodes the old name"

    def test_the_prompt_names_the_instance(self, identity_store):
        from core.system.config.identity import set_ai_name
        from services.llm.prompt_builder import construct_angela_prompt

        set_ai_name("小安", "u1")
        messages = construct_angela_prompt("你好", {"user_id": "u1"})
        system = messages[0]["content"]
        assert "小安" in system
        assert "You are Angela" not in system
        assert "你是 Angela" not in system

    def test_the_subtitle_speaker_follows_the_name(self, identity_store):
        from core.engine.audio_system import Subtitle
        from core.system.config.identity import current_user, set_ai_name

        set_ai_name("小安", "u1")
        with current_user("u1"):
            assert Subtitle(text="hi", start_time=0.0, end_time=1.0).speaker == "小安"

    def test_the_chat_context_carries_the_user_id(self):
        """The prompt layer resolves the name from context['user_id'].

        Without it a renamed instance silently falls back to the default
        name — the rename would look broken.
        """
        from api.routes.chat_routes import _prime_chat_context

        context = _prime_chat_context(
            "你好", "u1", "Human", {"user_id": "u1", "tenant_id": "default"}, []
        )
        assert context["user_id"] == "u1"

    def test_the_chat_context_falls_back_to_the_display_name(self):
        from api.routes.chat_routes import _prime_chat_context

        context = _prime_chat_context("你好", "u1", "Human", None, [])
        assert context["user_id"] == "u1"


# --------------------------------------------------------------------------- #
# The workshop host and the handover
# --------------------------------------------------------------------------- #
class TestLucifaella:
    def test_host_block_before_the_handover(self, identity_store):
        from core.persona.lucifaella import build_persona_block, get_persona_state

        assert get_persona_state("u1") == "host"
        block = build_persona_block("Angela", "u1")
        assert "露茜法埃拉" in block
        assert "商務部" in block

    def test_the_host_may_not_claim_more_than_the_system_can_do(self, identity_store):
        from core.persona.lucifaella import build_persona_block

        block = build_persona_block("Angela", "u1")
        # The character sheet is world-building; the block must keep the
        # limits explicit (no legal/financial rights, no fake autonomy).
        assert "12%" in block
        assert "不得" in block
        assert "法律" in block

    def test_handover_renames_and_switches_the_persona(self, identity_store):
        from core.persona.lucifaella import get_persona_state, perform_handover
        from core.system.config.identity import get_ai_name, get_identity_profile

        result = perform_handover("小安", "u1")
        assert result["ai_name"] == "小安"
        assert result["persona_state"] == "handover"
        assert get_ai_name("u1") == "小安"
        assert get_persona_state("u1") == "handover"
        profile = get_identity_profile("u1")
        assert profile["ai_name"] == "小安"

    def test_after_the_handover_the_instance_is_the_users_angela(self, identity_store):
        from core.persona.lucifaella import build_persona_block, perform_handover

        perform_handover("小安", "u1")
        block = build_persona_block("小安", "u1")
        assert "小安" in block
        assert "露茜法埃拉" in block  # still reachable as an agent
        # The instance is the subject now, not the workshop host.
        assert "使用者的個人 Angela" in block
        assert "她不是你的主體" in block

    def test_the_handover_message_is_in_character(self, identity_store):
        from core.persona.lucifaella import perform_handover

        result = perform_handover("小安", "u1")
        assert "小安" in result["message"]
        assert "天使工房" in result["message"]
