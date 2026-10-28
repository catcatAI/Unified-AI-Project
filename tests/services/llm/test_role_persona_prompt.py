# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""Role persona reaches the prompt — otherwise a role turn keeps Angela's voice."""

from ai.roleplay import Role
from ai.roleplay.runtime import build_role_persona
from services.llm.prompt_builder import _append_role_persona, construct_angela_prompt


def role():
    return Role(role_id="role_b", display_name="Gemma 角色", memory_namespace="ns_b")


# --------------------------------------------------------------------------
# builder-level
# --------------------------------------------------------------------------
def test_block_is_appended_to_the_system_message():
    messages = [{"role": "system", "content": "base"}]
    _append_role_persona(messages, {"_role_persona": "ROLE-BLOCK"})
    assert messages[0]["content"].startswith("base")
    assert messages[0]["content"].endswith("ROLE-BLOCK")


def test_without_a_role_nothing_changes():
    messages = [{"role": "system", "content": "base"}]
    _append_role_persona(messages, {})
    assert messages[0]["content"] == "base"


def test_blank_block_is_ignored():
    messages = [{"role": "system", "content": "base"}]
    _append_role_persona(messages, {"_role_persona": "   "})
    assert messages[0]["content"] == "base"


# --------------------------------------------------------------------------
# the block itself
# --------------------------------------------------------------------------
def test_block_names_the_role_and_forbids_angela():
    block = build_role_persona(role())
    assert "Gemma 角色" in block
    assert "role_b" in block
    assert "不要自稱 Angela" in block
    assert "優先" in block


# --------------------------------------------------------------------------
# end to end through construct_angela_prompt
# --------------------------------------------------------------------------
def test_construct_includes_the_role_block():
    context = {
        "state_for_llm": None,
        "user_id": "u1",
        "_role_id": "role_b",
        "_role_persona": build_role_persona(role()),
    }
    messages = construct_angela_prompt("你好", context)
    system = messages[0]["content"]
    assert "Gemma 角色" in system
    assert "不要自稱 Angela" in system


def test_construct_without_a_role_has_no_role_block():
    messages = construct_angela_prompt("你好", {"state_for_llm": None, "user_id": "u1"})
    assert "本回合優先於上述身份" not in messages[0]["content"]
