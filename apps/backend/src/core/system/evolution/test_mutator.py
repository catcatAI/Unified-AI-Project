"""
Test script for ConfigMutator
"""

from core.system.evolution.config_mutator import ConfigMutator


def test_config_mutator() -> None:
    """Test config mutator behavior."""
    print("Testing ConfigMutator (Phase 6)...")
    mutator = ConfigMutator()
    
    # 1. Test Proposal
    updates = {
        "hormones": {
            "ADRENALINE": {"half_life": 10.0}
        }
    }
    proposal = mutator.propose_change("biological", updates)
    print(f"Proposal: {proposal}")
    assert proposal["ready_to_apply"] is True
    
    # 2. Test Validation Failure
    bad_updates = {
        "hormones": {
            "ADRENALINE": {"half_life": -5.0}
        }
    }
    bad_proposal = mutator.propose_change("biological", bad_updates)
    print(f"Bad Proposal validation: {bad_proposal['validation']['is_valid']}")
    assert bad_proposal["ready_to_apply"] is False
    
    # 3. Test LLM Key Validation (Mocking environment)
    import os
    os.environ["MOCK_KEY"] = "this_is_a_mock_key_with_sufficient_length_32_chars"
    llm_updates = {
        "custom-provider": {
            "api_key_env": "MOCK_KEY"
        }
    }
    llm_proposal = mutator.propose_change("llm", llm_updates)
    print(f"LLM Proposal: {llm_proposal}")
    assert llm_proposal["ready_to_apply"] is True
    
    print("\n✅ ConfigMutator basic tests passed!")

if __name__ == "__main__":
    test_config_mutator()
