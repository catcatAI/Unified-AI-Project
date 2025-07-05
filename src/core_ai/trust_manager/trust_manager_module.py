from typing import Dict, Optional, Union

class TrustManager:
    """
    Manages trust scores for other AI entities interacting via HSP.
    Scores range from 0.0 (completely untrusted) to 1.0 (fully trusted).
    """
    DEFAULT_TRUST_SCORE = 0.5  # Neutral trust for unknown AIs
    MIN_TRUST_SCORE = 0.0
    MAX_TRUST_SCORE = 1.0

    def __init__(self, initial_trust_scores: Optional[Dict[str, float]] = None):
        """
        Initializes the TrustManager.

        Args:
            initial_trust_scores (Optional[Dict[str, float]]):
                Predefined trust scores for specific AI IDs.
        """
        self.trust_scores: Dict[str, float] = {}
        if initial_trust_scores:
            for ai_id, score in initial_trust_scores.items():
                self.trust_scores[ai_id] = self._clamp_score(score)

        print(f"TrustManager initialized. Default score for new AIs: {self.DEFAULT_TRUST_SCORE}")

    def _clamp_score(self, score: float) -> float:
        """Ensures score is within [MIN_TRUST_SCORE, MAX_TRUST_SCORE]."""
        return max(self.MIN_TRUST_SCORE, min(self.MAX_TRUST_SCORE, score))

    def get_trust_score(self, ai_id: str) -> float:
        """
        Retrieves the trust score for a given AI ID.
        Returns the default trust score if the AI ID is not found.
        """
        score = self.trust_scores.get(ai_id, self.DEFAULT_TRUST_SCORE)
        # print(f"TrustManager: Trust score for '{ai_id}': {score}") # Can be verbose
        return score

    def update_trust_score(
        self,
        ai_id: str,
        adjustment: Optional[float] = None,
        new_absolute_score: Optional[float] = None
    ) -> float:
        """
        Updates the trust score for a given AI ID.
        Either an adjustment (e.g., +0.1, -0.05) or a new_absolute_score can be provided.
        If both are provided, new_absolute_score takes precedence.
        The score is always clamped between MIN_TRUST_SCORE and MAX_TRUST_SCORE.

        Args:
            ai_id (str): The identifier of the AI whose trust score is to be updated.
            adjustment (Optional[float]): A positive or negative value to add to the current score.
            new_absolute_score (Optional[float]): A specific new score to set.

        Returns:
            float: The new, clamped trust score for the AI ID.
        """
        current_score = self.trust_scores.get(ai_id, self.DEFAULT_TRUST_SCORE)

        if new_absolute_score is not None:
            updated_score = self._clamp_score(new_absolute_score)
            self.trust_scores[ai_id] = updated_score
            print(f"TrustManager: Trust score for '{ai_id}' SET to {updated_score:.3f} (was {current_score:.3f}).")
        elif adjustment is not None:
            updated_score = self._clamp_score(current_score + adjustment)
            self.trust_scores[ai_id] = updated_score
            print(f"TrustManager: Trust score for '{ai_id}' ADJUSTED by {adjustment:+.3f} to {updated_score:.3f} (was {current_score:.3f}).")
        else:
            # No change requested, return current score
            print(f"TrustManager: No trust update specified for '{ai_id}'. Score remains {current_score:.3f}.")
            return current_score

        return updated_score

    def set_default_trust_score(self, ai_id: str) -> float:
        """Sets an AI's trust score to the default if not already known, or returns existing."""
        if ai_id not in self.trust_scores:
            self.trust_scores[ai_id] = self.DEFAULT_TRUST_SCORE
            print(f"TrustManager: Trust score for new AI '{ai_id}' initialized to default {self.DEFAULT_TRUST_SCORE:.3f}.")
            return self.DEFAULT_TRUST_SCORE
        return self.trust_scores[ai_id]

    def get_all_trust_scores(self) -> Dict[str, float]:
        """Returns a copy of all known trust scores."""
        return self.trust_scores.copy()


if __name__ == '__main__':
    print("--- TrustManager Standalone Test ---")
    trust_manager = TrustManager(initial_trust_scores={"did:hsp:ai_known_good": 0.8, "did:hsp:ai_known_bad": 0.2})

    print(f"\nInitial scores: {trust_manager.get_all_trust_scores()}")

    # Test get_trust_score
    print(f"Score for 'did:hsp:ai_known_good': {trust_manager.get_trust_score('did:hsp:ai_known_good'):.3f}") # Expected 0.8
    assert trust_manager.get_trust_score('did:hsp:ai_known_good') == 0.8
    print(f"Score for 'did:hsp:ai_unknown': {trust_manager.get_trust_score('did:hsp:ai_unknown'):.3f}") # Expected 0.5 (default)
    assert trust_manager.get_trust_score('did:hsp:ai_unknown') == TrustManager.DEFAULT_TRUST_SCORE

    # Test update_trust_score (adjustment)
    new_score_good = trust_manager.update_trust_score("did:hsp:ai_known_good", adjustment=0.1) # 0.8 + 0.1 = 0.9
    print(f"New score for 'did:hsp:ai_known_good' after +0.1: {new_score_good:.3f}")
    assert new_score_good == 0.9

    new_score_unknown = trust_manager.update_trust_score("did:hsp:ai_unknown", adjustment=-0.2) # 0.5 - 0.2 = 0.3
    print(f"New score for 'did:hsp:ai_unknown' after -0.2: {new_score_unknown:.3f}")
    assert new_score_unknown == 0.3

    # Test clamping (adjustment)
    trust_manager.update_trust_score("did:hsp:ai_known_good", adjustment=0.5) # 0.9 + 0.5 = 1.4 -> clamped to 1.0
    assert trust_manager.get_trust_score("did:hsp:ai_known_good") == TrustManager.MAX_TRUST_SCORE
    print(f"Score for 'did:hsp:ai_known_good' after +0.5 (clamped): {trust_manager.get_trust_score('did:hsp:ai_known_good'):.3f}")

    trust_manager.update_trust_score("did:hsp:ai_unknown", adjustment=-0.5) # 0.3 - 0.5 = -0.2 -> clamped to 0.0
    assert trust_manager.get_trust_score("did:hsp:ai_unknown") == TrustManager.MIN_TRUST_SCORE
    print(f"Score for 'did:hsp:ai_unknown' after -0.5 (clamped): {trust_manager.get_trust_score('did:hsp:ai_unknown'):.3f}")

    # Test update_trust_score (new_absolute_score)
    abs_score_bad = trust_manager.update_trust_score("did:hsp:ai_known_bad", new_absolute_score=0.15)
    print(f"New absolute score for 'did:hsp:ai_known_bad': {abs_score_bad:.3f}")
    assert abs_score_bad == 0.15

    # Test clamping (new_absolute_score)
    trust_manager.update_trust_score("did:hsp:ai_known_bad", new_absolute_score=1.5) # Clamped to 1.0
    assert trust_manager.get_trust_score("did:hsp:ai_known_bad") == TrustManager.MAX_TRUST_SCORE
    print(f"Score for 'did:hsp:ai_known_bad' after set to 1.5 (clamped): {trust_manager.get_trust_score('did:hsp:ai_known_bad'):.3f}")

    trust_manager.update_trust_score("did:hsp:ai_known_bad", new_absolute_score=-0.5) # Clamped to 0.0
    assert trust_manager.get_trust_score("did:hsp:ai_known_bad") == TrustManager.MIN_TRUST_SCORE
    print(f"Score for 'did:hsp:ai_known_bad' after set to -0.5 (clamped): {trust_manager.get_trust_score('did:hsp:ai_known_bad'):.3f}")

    # Test set_default_trust_score
    trust_manager.set_default_trust_score("did:hsp:ai_new_peer")
    assert trust_manager.get_trust_score("did:hsp:ai_new_peer") == TrustManager.DEFAULT_TRUST_SCORE
    # Calling again should not change it if it exists
    trust_manager.update_trust_score("did:hsp:ai_new_peer", adjustment=0.1) # Now 0.6
    trust_manager.set_default_trust_score("did:hsp:ai_new_peer") # Should still be 0.6
    assert trust_manager.get_trust_score("did:hsp:ai_new_peer") == 0.6


    print(f"\nFinal scores: {trust_manager.get_all_trust_scores()}")
    print("\nTrustManager standalone test finished.")
```
