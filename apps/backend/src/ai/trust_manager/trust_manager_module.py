import logging
from typing import Dict, Optional, Union, List

logger = logging.getLogger(__name__)

class TrustManager:
    """
    Manages trust scores for other AI entities interacting via HSP.
    Scores range from 0.0 (completely untrusted) to 1.0 (fully trusted).
    """
    DEFAULT_TRUST_SCORE = 0.5
    MIN_TRUST_SCORE = 0.0
    MAX_TRUST_SCORE = 1.0

    def __init__(self, initial_trust_scores: Optional[Dict[str, Union[float, Dict[str, float]]]] = None) -> None:
        """
        Initializes the TrustManager.

        Args:
            initial_trust_scores: Predefined trust scores.
                e.g., {"ai_1": 0.8, "ai_2": {"general": 0.7, "data_analysis": 0.9}}
        """
        self.trust_scores: Dict[str, Dict[str, float]] = {}
        if initial_trust_scores:
            for ai_id, score_data in initial_trust_scores.items():
                if isinstance(score_data, dict):
                    self.trust_scores[ai_id] = {k: self._clamp_score(v) for k, v in score_data.items()}
                else:
                    self.trust_scores[ai_id] = {'general': self._clamp_score(score_data)}

        logger.info(f"TrustManager initialized. Default score for new AIs: {self.DEFAULT_TRUST_SCORE}")

    def _clamp_score(self, score: float) -> float:
        """Ensures score is within [MIN_TRUST_SCORE, MAX_TRUST_SCORE]."""
        return max(self.MIN_TRUST_SCORE, min(self.MAX_TRUST_SCORE, score))

    def get_trust_score(self, ai_id: str, capability_name: Optional[str] = None) -> float:
        """
        Retrieves the trust score for a given AI ID and optional capability.
        """
        ai_scores = self.trust_scores.get(ai_id)
        if not ai_scores:
            return self.DEFAULT_TRUST_SCORE
        
        if capability_name and capability_name in ai_scores:
            return ai_scores[capability_name]

        return ai_scores.get('general', self.DEFAULT_TRUST_SCORE)

    def update_trust_score(self, ai_id: str, adjustment: Optional[float] = None,
                           new_absolute_score: Optional[float] = None,
                           capability_name: Optional[str] = None) -> float:
        """
        Updates the trust score for a given AI ID, optionally for a specific capability.
        """
        scope = capability_name if capability_name else 'general'
        if ai_id not in self.trust_scores:
            self.trust_scores[ai_id] = {}

        current_score = self.get_trust_score(ai_id, capability_name)

        if new_absolute_score is not None:
            updated_score = self._clamp_score(new_absolute_score)
            self.trust_scores[ai_id][scope] = updated_score
            logger.info(f"TrustManager: Trust score for '{ai_id}' (scope: {scope}) SET to {updated_score:.3f}.")
        elif adjustment is not None:
            updated_score = self._clamp_score(current_score + adjustment)
            self.trust_scores[ai_id][scope] = updated_score
            logger.info(f"TrustManager: Trust score for '{ai_id}' (scope: {scope}) ADJUSTED by {adjustment:+.3f} to {updated_score:.3f}.")
        else:
            return current_score

        return updated_score

    def set_default_trust_score(self, ai_id: str) -> float:
        """Sets an AI's trust score to the default if not already known, or returns existing."""
        if ai_id not in self.trust_scores:
            self.trust_scores[ai_id] = {'general': self.DEFAULT_TRUST_SCORE}
            return self.DEFAULT_TRUST_SCORE
        return self.trust_scores[ai_id].get('general', self.DEFAULT_TRUST_SCORE)

    def get_all_trust_scores(self) -> Dict[str, Dict[str, float]]:
        """Returns a copy of all known trust scores."""
        return self.trust_scores.copy()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logger.info("TrustManager standalone test finished.")
