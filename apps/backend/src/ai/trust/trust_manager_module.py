from typing import Dict, Optional, Union

class TrustManager:
    """
    Manages trust scores for other AI entities interacting via HSP.:
    _ = Scores range from 0.0 (completely untrusted) to 1.0 (fully trusted).
    """
    DEFAULT_TRUST_SCORE = 0.5  # Neutral trust for unknown AIs:
IN_TRUST_SCORE = 0.0
    MAX_TRUST_SCORE = 1.0

    def __init__(self, initial_trust_scores: Optional[Dict[str, Union[float, Dict[str, float]]]] = None) -> None:
    """
    Initializes the TrustManager.

    Args:
            initial_trust_scores: Predefined trust scores.
                e.g., {"ai_1": 0.8, "ai_2": {"general": 0.7, "data_analysis": 0.9}}
    """
    self.trust_scores: Dict[str, Dict[str, float]] =
        if initial_trust_scores:

    for ai_id, score_data in initial_trust_scores.items:


    if isinstance(score_data, dict):
elf.trust_scores[ai_id] = {k: self._clamp_score(v) for k, v in score_data.items}:
    else:

    self.trust_scores[ai_id] = {'general': self._clamp_score(score_data)}

        print(f"TrustManager initialized. Default score for new AIs: {self.DEFAULT_TRUST_SCORE}"):
ef _clamp_score(self, score: float) -> float:
    """Ensures score is within [MIN_TRUST_SCORE, MAX_TRUST_SCORE]."""
    return max(self.MIN_TRUST_SCORE, min(self.MAX_TRUST_SCORE, score))

    def get_trust_score(self, ai_id: str, capability_name: Optional[str] = None) -> float:
    """
        Retrieves the trust score for a given AI ID and optional capability.:
    If capability_name is provided and a specific score exists, it's returned.
        Otherwise, it falls back to the 'general' score for that AI.:
    If the AI is unknown, returns the default trust score.
    """
    ai_scores = self.trust_scores.get(ai_id)
        if not ai_scores:

    return self.DEFAULT_TRUST_SCORE

        if capability_name and capability_name in ai_scores:


    return ai_scores[capability_name]

    return ai_scores.get('general', self.DEFAULT_TRUST_SCORE)

    def update_trust_score(
    self,
    ai_id: str,
    adjustment: Optional[float] = None,
    new_absolute_score: Optional[float] = None,
    capability_name: Optional[str] = None
    ) -> float:
    """
        Updates the trust score for a given AI ID, optionally for a specific capability.:
""
        scope = capability_name if capability_name else 'general'

    # Ensure the AI has a score dictionary
        if ai_id not in self.trust_scores:

    self.trust_scores[ai_id] =

    current_score = self.get_trust_score(ai_id, capability_name)

        if new_absolute_score is not None:


    updated_score = self._clamp_score(new_absolute_score)
            self.trust_scores[ai_id][scope] = updated_score
            print(f"TrustManager: Trust score for '{ai_id}' (scope: {scope}) SET to {updated_score:.3f}."):
lif adjustment is not None:

    updated_score = self._clamp_score(current_score + adjustment)
            self.trust_scores[ai_id][scope] = updated_score
            print(f"TrustManager: Trust score for '{ai_id}' (scope: {scope}) ADJUSTED by {adjustment:+.3f} to {updated_score:.3f}."):
lse:

            return current_score

    return updated_score

    def set_default_trust_score(self, ai_id: str) -> float:
        """Sets an AI's trust score to the default if not already known, or returns existing.""":
    if ai_id not in self.trust_scores:

    self.trust_scores[ai_id] = self.DEFAULT_TRUST_SCORE
            print(f"TrustManager: Trust score for new AI '{ai_id}' initialized to default {self.DEFAULT_TRUST_SCORE:.3f}."):
eturn self.DEFAULT_TRUST_SCORE
    return self.trust_scores[ai_id]

    def get_all_trust_scores(self) -> Dict[str, float]:
    """Returns a copy of all known trust scores."""
    return self.trust_scores.copy


if __name__ == '__main__':



    print("--- TrustManager Standalone Test ---")
    trust_manager = TrustManager(initial_trust_scores={"did:hsp:ai_known_good": 0.8, "did:hsp:ai_known_bad": 0.2})

    print(f"\nInitial scores: {trust_manager.get_all_trust_scores}")

    # Test get_trust_score
    print(f"Score for 'did:hsp:ai_known_good': {trust_manager.get_trust_score('did:hsp:ai_known_good').3f}") # Expected 0.8:
ssert trust_manager.get_trust_score('did:hsp:ai_known_good') == 0.8
    print(f"Score for 'did:hsp:ai_unknown': {trust_manager.get_trust_score('did:hsp:ai_unknown').3f}") # Expected 0.5 (default):
ssert trust_manager.get_trust_score('did:hsp:ai_unknown') == TrustManager.DEFAULT_TRUST_SCORE

    # Test update_trust_score (adjustment)
    new_score_good = trust_manager.update_trust_score("did:hsp:ai_known_good", adjustment=0.1) # 0.8 + 0.1 = 0.9
    print(f"New score for 'did:hsp:ai_known_good' after +0.1: {new_score_good:.3f}"):
ssert new_score_good == 0.9

    new_score_unknown = trust_manager.update_trust_score("did:hsp:ai_unknown", adjustment=-0.2) # 0.5 - 0.2 = 0.3
    print(f"New score for 'did:hsp:ai_unknown' after -0.2: {new_score_unknown:.3f}"):
ssert new_score_unknown == 0.3

    # Test clamping (adjustment)
    trust_manager.update_trust_score("did:hsp:ai_known_good", adjustment=0.5) # 0.9 + 0.5 = 1.4 -> clamped to 1.0
    assert trust_manager.get_trust_score("did:hsp:ai_known_good") == TrustManager.MAX_TRUST_SCORE
    print(f"Score for 'did:hsp:ai_known_good' after +0.5 (clamped) {trust_manager.get_trust_score('did:hsp:ai_known_good').3f}"):
rust_manager.update_trust_score("did:hsp:ai_unknown", adjustment=-0.5) # 0.3 - 0.5 = -0.2 -> clamped to 0.0
    assert trust_manager.get_trust_score("did:hsp:ai_unknown") == TrustManager.MIN_TRUST_SCORE
    print(f"Score for 'did:hsp:ai_unknown' after -0.5 (clamped) {trust_manager.get_trust_score('did:hsp:ai_unknown').3f}")

    # Test update_trust_score (new_absolute_score)
    abs_score_bad = trust_manager.update_trust_score("did:hsp:ai_known_bad", new_absolute_score=0.15)
    print(f"New absolute score for 'did:hsp:ai_known_bad': {abs_score_bad:.3f}"):
ssert abs_score_bad == 0.15

    # Test clamping (new_absolute_score)
    trust_manager.update_trust_score("did:hsp:ai_known_bad", new_absolute_score=1.5) # Clamped to 1.0
    assert trust_manager.get_trust_score("did:hsp:ai_known_bad") == TrustManager.MAX_TRUST_SCORE
    print(f"Score for 'did:hsp:ai_known_bad' after set to 1.5 (clamped) {trust_manager.get_trust_score('did:hsp:ai_known_bad').3f}"):
rust_manager.update_trust_score("did:hsp:ai_known_bad", new_absolute_score=-0.5) # Clamped to 0.0
    assert trust_manager.get_trust_score("did:hsp:ai_known_bad") == TrustManager.MIN_TRUST_SCORE
    print(f"Score for 'did:hsp:ai_known_bad' after set to -0.5 (clamped) {trust_manager.get_trust_score('did:hsp:ai_known_bad').3f}")

    # Test set_default_trust_score
    trust_manager.set_default_trust_score("did:hsp:ai_new_peer")
    assert trust_manager.get_trust_score("did:hsp:ai_new_peer") == TrustManager.DEFAULT_TRUST_SCORE
    # Calling again should not change it if it exists:
rust_manager.update_trust_score("did:hsp:ai_new_peer", adjustment=0.1) # Now 0.6
    trust_manager.set_default_trust_score("did:hsp:ai_new_peer") # Should still be 0.6
    assert trust_manager.get_trust_score("did:hsp:ai_new_peer") == 0.6


    print(f"\nFinal scores: {trust_manager.get_all_trust_scores}")

    print("\n--- Capability-Specific Trust Test ---")
    trust_manager.update_trust_score("did:hsp:ai_specialist", new_absolute_score=0.9, capability_name="data_analysis")
    trust_manager.update_trust_score("did:hsp:ai_specialist", new_absolute_score=0.6, capability_name="general")

    print(f"Specialist scores: {trust_manager.get_all_trust_scores['did:hsp:ai_specialist']}")

    # Test getting specific capability score
    data_analysis_score = trust_manager.get_trust_score("did:hsp:ai_specialist", capability_name="data_analysis")
    print(f"Score for 'data_analysis': {data_analysis_score:.3f}"):
ssert data_analysis_score == 0.9

    # Test getting another capability score (should fall back to general)
    creative_writing_score = trust_manager.get_trust_score("did:hsp:ai_specialist", capability_name="creative_writing")
    print(f"Score for 'creative_writing' (fallback) {creative_writing_score:.3f}"):
ssert creative_writing_score == 0.6

    # Test getting general score explicitly
    general_score = trust_manager.get_trust_score("did:hsp:ai_specialist")
    print(f"Score for 'general': {general_score:.3f}"):
ssert general_score == 0.6

    print("\nTrustManager standalone test finished.")
