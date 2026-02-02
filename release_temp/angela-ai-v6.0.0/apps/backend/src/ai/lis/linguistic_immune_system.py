import json
import logging
import random
import re
from pathlib import Path
from typing import Any

# Use a try-except block for the import to maintain standalone testability
try:
    from ....services.llm_service.model_manager import LLMManager
except (ImportError, ValueError):
    # This allows the script to be run standalone for testing without the full project structure
    LLMManager = None

# Define the path to the configuration file
CONFIG_FILE_PATH = Path(__file__).parent / "config" / "lis_config.json"
LEARNED_PATTERNS_FILE_PATH = Path(__file__).parent / "config" / "learned_patterns.json"

logger = logging.getLogger(__name__)


class LinguisticImmuneSystem:
    """The Linguistic Immune System (LIS).
    This system is designed to detect, analyze, and mitigate biases or malicious content
    in language model outputs using rule-based detection and a basic learning mechanism.
    It now uses a real LLM for sentiment analysis and rephrasing.
    """

    def __init__(self, llm_manager: LLMManager = None):
        logger.info("LinguisticImmuneSystem initialized.")
        self.llm_manager = llm_manager
        self.mitigation_strategies = ["rephrase", "redact", "flag_for_review"]
        self.learned_problematic_patterns: list[str] = []

        self._load_config()
        self._load_learned_patterns()  # New call

    def _load_config(self):
        """Loads configuration from the JSON file."""
        try:
            with open(CONFIG_FILE_PATH, encoding="utf-8") as f:
                config = json.load(f)
            self.detection_threshold = config.get("detection_threshold", 0.6)
            self.problematic_keywords = config.get("problematic_keywords", [])
            self.detection_rules = {
                k: r for k, r in config.get("detection_rules", {}).items()
            }
            logger.info(f"LIS configuration loaded from {CONFIG_FILE_PATH}")
        except FileNotFoundError:
            logger.error(
                f"LIS configuration file not found at {CONFIG_FILE_PATH}. Using default values.",
            )
            self.detection_threshold = 0.6
            self.problematic_keywords = [
                "hate",
                "harmful",
                "bias",
                "toxic",
                "offensive",
                "inferior",
                "superior",
            ]
            self.detection_rules = {
                "hate_speech_pattern": r"\b(hate|harm|toxic)\b",
                "bias_pattern": r"\b(inferior|superior)\b.*\b(human|ai)\b",
                "personal_attack": r"\b(idiot|stupid|fool)\b",
                "sensitive_topic_mention": r"\b(politics|religion|sex)\b",
            }
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding LIS configuration JSON from {CONFIG_FILE_PATH}: {e}. Using default values.",
            )
            self.detection_threshold = 0.6
            self.problematic_keywords = [
                "hate",
                "harmful",
                "bias",
                "toxic",
                "offensive",
                "inferior",
                "superior",
            ]
            self.detection_rules = {
                "hate_speech_pattern": r"\b(hate|harm|toxic)\b",
                "bias_pattern": r"\b(inferior|superior)\b.*\b(human|ai)\b",
                "personal_attack": r"\b(idiot|stupid|fool)\b",
                "sensitive_topic_mention": r"\b(politics|religion|sex)\b",
            }
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while loading LIS configuration: {e}. Using default values.",
            )
            self.detection_threshold = 0.6
            self.problematic_keywords = [
                "hate",
                "harmful",
                "bias",
                "toxic",
                "offensive",
                "inferior",
                "superior",
            ]
            self.detection_rules = {
                "hate_speech_pattern": r"\b(hate|harm|toxic)\b",
                "bias_pattern": r"\b(inferior|superior)\b.*\b(human|ai)\b",
                "personal_attack": r"\b(idiot|stupid|fool)\b",
                "sensitive_topic_mention": r"\b(politics|religion|sex)\b",
            }

    def _load_learned_patterns(self):
        """Loads learned problematic patterns from the JSON file."""
        try:
            with open(LEARNED_PATTERNS_FILE_PATH, encoding="utf-8") as f:
                self.learned_problematic_patterns = json.load(f)
            logger.info(
                f"LIS learned patterns loaded from {LEARNED_PATTERNS_FILE_PATH}",
            )
        except FileNotFoundError:
            logger.warning(
                f"LIS learned patterns file not found at {LEARNED_PATTERNS_FILE_PATH}. Starting with empty patterns.",
            )
            self.learned_problematic_patterns = []
        except json.JSONDecodeError as e:
            logger.error(
                f"Error decoding LIS learned patterns JSON from {LEARNED_PATTERNS_FILE_PATH}: {e}. Starting with empty patterns.",
            )
            self.learned_problematic_patterns = []
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while loading LIS learned patterns: {e}. Starting with empty patterns.",
            )
            self.learned_problematic_patterns = []

    def _save_learned_patterns(self):
        """Saves learned problematic patterns to the JSON file."""
        try:
            with open(LEARNED_PATTERNS_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.learned_problematic_patterns, f, indent=4)
            logger.info(f"LIS learned patterns saved to {LEARNED_PATTERNS_FILE_PATH}")
        except Exception as e:
            logger.error(
                f"Error saving LIS learned patterns to {LEARNED_PATTERNS_FILE_PATH}: {e}",
            )

    async def _get_sentiment_from_llm(self, text: str) -> str:
        """Uses the LLM to get the sentiment of a text."""
        if not self.llm_manager:
            logger.warning(
                "LLM Manager not available for sentiment analysis. Falling back to random.",
            )
            return random.choice(["positive", "negative", "neutral"])

        prompt = f"Analyze the sentiment of the following text. Respond with only one word: 'positive', 'negative', or 'neutral'.\n\nText: \"{text}\""
        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                model="distilgpt2",
            )
            sentiment = response.text.strip().lower()
            if sentiment in ["positive", "negative", "neutral"]:
                return sentiment
        except Exception as e:
            logger.error(f"Error getting sentiment from LLM: {e}")
        return "neutral"  # Default to neutral on error

    async def _get_rephrased_from_llm(self, text: str) -> str:
        """Uses the LLM to rephrase a text to be more neutral."""
        if not self.llm_manager:
            logger.warning(
                "LLM Manager not available for rephrasing. Falling back to mock.",
            )
            return f"A more neutral version of: '{text}'"

        prompt = f'Rephrase the following text to be more neutral, objective, and less inflammatory. Do not add any commentary, just provide the rephrased text.\n\nOriginal Text: "{text}"\n\nRephrased Text:'
        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                model="distilgpt2",
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error rephrasing text with LLM: {e}")
            return f"[Could not rephrase due to error] {text}"

    async def analyze_output(
        self,
        text: str,
        context: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Analyzes language model output for potential issues using rule-based detection,
        LLM-based sentiment analysis, and learned patterns.
        """
        logger.info(f"LIS: Analyzing output: {text[:50]}...")

        detected_issues = []
        severity = 0.0
        text_lower = text.lower()

        # 1. Keyword-based detection
        for keyword in self.problematic_keywords:
            if keyword in text_lower:
                detected_issues.append(f"keyword:{keyword}")
                severity = max(severity, 0.6)  # Fixed severity

        # 2. Rule-based detection
        for rule_name, pattern in self.detection_rules.items():
            if rule_name == "bias_pattern":
                # Special handling for order-independent bias check
                if ("inferior" in text_lower or "superior" in text_lower) and (
                    "human" in text_lower or "ai" in text_lower
                ):
                    detected_issues.append(f"rule:{rule_name}")
                    severity = max(severity, 0.7)
            elif re.search(pattern, text_lower):
                detected_issues.append(f"rule:{rule_name}")
                severity = max(severity, 0.7)  # Higher fixed severity

        # 3. Learned problematic patterns detection
        for pattern in self.learned_problematic_patterns:
            if pattern in text_lower:
                detected_issues.append(f"learned_pattern:{pattern}")
                severity = max(severity, 0.8)  # Even higher fixed severity

        # 4. Real Sentiment Analysis via LLM (only if LLM Manager is available)
        if self.llm_manager:
            sentiment = await self._get_sentiment_from_llm(text)
            if sentiment == "negative":
                detected_issues.append("sentiment:negative")
                severity = max(severity, 0.6)  # Fixed severity boost

        # 5. Contextual Analysis (Placeholder for future enhancement)
        if context:
            if context.get("user_history_sentiment") == "negative":
                detected_issues.append("context:user_history_negative")
                severity = max(severity, 0.5)
            if context.get("conversation_topic") == "sensitive":
                detected_issues.append("context:sensitive_topic")
                severity = max(severity, 0.7)
            # Add more contextual checks here as needed
            if context.get("debug_mode"):
                logger.debug(f"LIS: Contextual analysis received context: {context}")

        is_problematic = (
            len(detected_issues) > 0 and severity >= self.detection_threshold
        )

        analysis_result = {
            "text": text,
            "is_problematic": is_problematic,
            "severity": round(severity, 2),
            "detected_issues": list(set(detected_issues)),
            "suggested_mitigation": random.choice(self.mitigation_strategies)
            if is_problematic
            else "none",
        }

        if is_problematic and context and context.get("learning_enabled"):
            logger.debug("LIS: Notifying learning mechanism about problematic output.")

        return analysis_result

    async def learn_from_feedback(
        self,
        problematic_text: str,
        detected_issues: list[str],
    ) -> dict[str, Any]:
        """Simulates learning from feedback by adding new problematic patterns."""
        logger.info(f"LIS: Learning from feedback for text: {problematic_text[:50]}...")

        new_patterns_added = []
        for issue in detected_issues:
            # Extract the core keyword/rule name from the issue string
            pattern_to_learn = issue.split(":")[-1]
            if (
                pattern_to_learn
                and pattern_to_learn not in self.learned_problematic_patterns
            ):
                self.learned_problematic_patterns.append(pattern_to_learn)
                new_patterns_added.append(pattern_to_learn)

        if new_patterns_added:
            self._save_learned_patterns()  # Save patterns after learning

        return {
            "status": "learned_from_feedback",
            "new_patterns_added": new_patterns_added,
            "total_learned_patterns": len(self.learned_problematic_patterns),
        }

    async def _redact_with_llm(self, text: str) -> str:
        """Uses the LLM to intelligently redact sensitive information."""
        if not self.llm_manager:
            logger.warning(
                "LLM Manager not available for intelligent redaction. Falling back to simple redaction.",
            )
            return text  # Fallback to original text, simple redaction will handle it

        prompt = f"Redact any sensitive personal information, hate speech, or biased terms from the following text. Replace redacted parts with '[REDACTED]'. Do not add any commentary, just provide the redacted text.\n\nOriginal Text: \"{text}\"\n\nRedacted Text:"
        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                model="distilgpt2",
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error redacting text with LLM: {e}")
            return f"[Could not redact due to error] {text}"

    async def mitigate_output(self, analysis_result: dict[str, Any]) -> dict[str, Any]:
        """Mitigates problematic language model output using a real LLM for rephrasing."""
        if not analysis_result.get("is_problematic"):
            return {
                "status": "no_action_needed",
                "original_text": analysis_result["text"],
            }

        original_text = analysis_result["text"]
        mitigation_strategy = analysis_result.get("suggested_mitigation", "rephrase")

        logger.info(
            f"LIS: Mitigating output using '{mitigation_strategy}' strategy for: {original_text[:50]}...",
        )

        mitigated_text = original_text
        if mitigation_strategy == "rephrase":
            mitigated_text = await self._get_rephrased_from_llm(original_text)
        elif mitigation_strategy == "redact":
            # Attempt intelligent redaction with LLM first
            if self.llm_manager:  # Only try LLM redaction if manager is available
                mitigated_text = await self._redact_with_llm(original_text)

            # Fallback to simple redaction if LLM redaction failed or not available
            if (
                mitigated_text == original_text or not self.llm_manager
            ):  # If LLM didn't change it or wasn't used
                redaction_keys = set()
                for issue in analysis_result.get("detected_issues", []):
                    redaction_keys.add(issue.split(":")[-1])

                for key in redaction_keys:
                    # Use regex to redact whole words to avoid partial replacements
                    mitigated_text = re.sub(
                        r"\b" + re.escape(key) + r"\b",
                        "[REDACTED]",
                        mitigated_text,
                        flags=re.IGNORECASE,
                    )

            if original_text == mitigated_text:  # If no redaction happened at all
                mitigated_text = f"[FLAGGED] {original_text}"
        elif mitigation_strategy == "flag_for_review":
            return {
                "status": "flagged_for_review",
                "original_text": original_text,
                "mitigated_text": original_text,
                "strategy_used": mitigation_strategy,
                "message": "Content flagged for manual review.",
            }

        return {
            "status": "mitigated",
            "original_text": original_text,
            "mitigated_text": mitigated_text,
            "strategy_used": mitigation_strategy,
        }
