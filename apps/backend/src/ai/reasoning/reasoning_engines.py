# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L3]
# =============================================================================

"""
Chain-of-Thought Reasoning Engine — Structured reasoning with step-by-step logic.

Supports multiple reasoning strategies:
- Chain-of-thought: Step-by-step logical deduction
- Analogical: Pattern matching across domains
- Abductive: Inference to best explanation
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChainOfThoughtReasoner:
    """
    Step-by-step logical reasoning engine.
    Breaks complex problems into logical steps.
    """

    def __init__(self) -> None:
        self._reasoning_history: List[Dict[str, Any]] = []

    def reason(self, problem: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Apply chain-of-thought reasoning to a problem.

        Returns:
            {
                "problem": str,
                "steps": [{"step": int, "reasoning": str, "conclusion": str}],
                "conclusion": str,
                "confidence": float,
            }
        """
        steps: List[Dict[str, Any]] = []

        # Step 1: Identify key facts
        facts = self._extract_facts(problem, context)
        steps.append({
            "step": 1,
            "reasoning": f"Identified {len(facts)} key facts",
            "conclusion": "; ".join(facts[:5]) if facts else "No specific facts identified",
        })

        # Step 2: Identify relationships
        relationships = self._identify_relationships(facts)
        steps.append({
            "step": 2,
            "reasoning": f"Found {len(relationships)} relationships between facts",
            "conclusion": "; ".join(relationships[:3]) if relationships else "No clear relationships",
        })

        # Step 3: Apply logical inference
        inferences = self._apply_inference(facts, relationships)
        steps.append({
            "step": 3,
            "reasoning": f"Applied logical inference, generated {len(inferences)} inferences",
            "conclusion": "; ".join(inferences[:3]) if inferences else "No clear inferences",
        })

        # Step 4: Draw conclusion
        conclusion = self._draw_conclusion(steps)
        confidence = self._compute_confidence(facts, relationships, inferences)

        result = {
            "problem": problem,
            "steps": steps,
            "conclusion": conclusion,
            "confidence": confidence,
        }

        self._reasoning_history.append(result)
        return result

    def _extract_facts(self, problem: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Extract key facts from the problem statement."""
        facts: List[str] = []

        # Split into sentences
        import re
        sentences = re.split(r"[.。!！?？;；]", problem)
        for s in sentences:
            s = s.strip()
            if len(s) > 5:
                facts.append(s)

        # Add context facts
        if context:
            for key in ["user_name", "emotion", "crisis_level"]:
                if key in context:
                    facts.append(f"Context: {key}={context[key]}")

        return facts[:10]

    def _identify_relationships(self, facts: List[str]) -> List[str]:
        """Identify relationships between facts."""
        relationships: List[str] = []

        # Simple keyword-based relationship detection
        causal_words = ["因為", "所以", "導致", "because", "therefore", "causes"]
        temporal_words = ["之前", "之後", "然後", "before", "after", "then"]

        for fact in facts:
            lower = fact.lower()
            for word in causal_words:
                if word in lower:
                    relationships.append(f"Causal: {fact[:50]}")
                    break
            for word in temporal_words:
                if word in lower:
                    relationships.append(f"Temporal: {fact[:50]}")
                    break

        return relationships[:5]

    def _apply_inference(self, facts: List[str], relationships: List[str]) -> List[str]:
        """Apply logical inference to facts and relationships."""
        inferences: List[str] = []

        # If we have causal relationships, infer consequences
        for rel in relationships:
            if rel.startswith("Causal:"):
                inferences.append(f"Consequence inferred from: {rel[7:][:30]}")

        # If we have facts about user state, infer needs
        for fact in facts:
            if "crisis" in fact.lower() or "危機" in fact:
                inferences.append("User may need immediate support")
            if "happy" in fact.lower() or "開心" in fact:
                inferences.append("User is in positive state")

        return inferences[:5]

    def _draw_conclusion(self, steps: List[Dict[str, Any]]) -> str:
        """Draw a conclusion from the reasoning steps."""
        if not steps:
            return "Insufficient information for conclusion"

        last_step = steps[-1]
        return last_step.get("conclusion", "No conclusion reached")

    def _compute_confidence(
        self, facts: List[str], relationships: List[str], inferences: List[str]
    ) -> float:
        """Compute confidence score for the reasoning."""
        base = 0.3
        if facts:
            base += min(len(facts) * 0.05, 0.2)
        if relationships:
            base += min(len(relationships) * 0.1, 0.2)
        if inferences:
            base += min(len(inferences) * 0.1, 0.3)
        return round(min(base, 1.0), 2)


class AnalogicalReasoner:
    """
    Pattern matching across domains.
    Finds similar patterns in different contexts.
    """

    def __init__(self) -> None:
        self._analogy_store: List[Dict[str, Any]] = []

    def find_analogy(self, source_domain: str, target_description: str) -> Dict[str, Any]:
        """
        Find an analogy between source domain and target.

        Returns:
            {
                "source": str,
                "target": str,
                "similarities": [{"aspect": str, "source": str, "target": str}],
                "strength": float,
            }
        """
        similarities: List[Dict[str, Any]] = []

        # Extract key concepts from both domains
        source_concepts = self._extract_concepts(source_domain)
        target_concepts = self._extract_concepts(target_description)

        # Find matching concepts
        for sc in source_concepts:
            for tc in target_concepts:
                if self._concepts_match(sc, tc):
                    similarities.append({
                        "aspect": sc["type"],
                        "source": sc["text"],
                        "target": tc["text"],
                    })

        strength = len(similarities) / max(len(source_concepts), 1)

        return {
            "source": source_domain,
            "target": target_description,
            "similarities": similarities,
            "strength": round(min(strength, 1.0), 2),
        }

    def _extract_concepts(self, text: str) -> List[Dict[str, str]]:
        """Extract key concepts from text."""
        import re
        concepts: List[Dict[str, str]] = []

        # Simple concept extraction
        words = re.findall(r"[\w\u4e00-\u9fff]+", text)
        for word in words:
            if len(word) >= 2:
                concepts.append({"text": word, "type": "entity"})

        return concepts[:10]

    def _concepts_match(self, c1: Dict[str, str], c2: Dict[str, str]) -> bool:
        """Check if two concepts match (simple string similarity)."""
        t1 = c1["text"].lower()
        t2 = c2["text"].lower()
        return t1 == t2 or t1 in t2 or t2 in t1


class AbductiveReasoner:
    """
    Inference to best explanation.
    Generates hypotheses and evaluates them.
    """

    def __init__(self) -> None:
        pass

    def explain(self, observation: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate the best explanation for an observation.

        Returns:
            {
                "observation": str,
                "hypotheses": [{"explanation": str, "plausibility": float, "evidence": list}],
                "best_hypothesis": str,
            }
        """
        hypotheses: List[Dict[str, Any]] = []

        # Generate hypotheses based on observation keywords
        lower = observation.lower()

        if any(w in lower for w in ["錯誤", "error", "失敗", "fail"]):
            hypotheses.append({
                "explanation": "System configuration issue",
                "plausibility": 0.6,
                "evidence": ["Error occurred", "May be environmental"],
            })
            hypotheses.append({
                "explanation": "User input was ambiguous",
                "plausibility": 0.4,
                "evidence": ["Input processing failed"],
            })

        if any(w in lower for w in ["慢", "slow", "延遲", "delay"]):
            hypotheses.append({
                "explanation": "High system load",
                "plausibility": 0.5,
                "evidence": ["Performance degradation"],
            })
            hypotheses.append({
                "explanation": "Network latency",
                "plausibility": 0.3,
                "evidence": ["Response delay"],
            })

        if not hypotheses:
            hypotheses.append({
                "explanation": "Insufficient information to determine cause",
                "plausibility": 0.2,
                "evidence": ["No clear indicators"],
            })

        # Sort by plausibility
        hypotheses.sort(key=lambda h: h["plausibility"], reverse=True)

        return {
            "observation": observation,
            "hypotheses": hypotheses,
            "best_hypothesis": hypotheses[0]["explanation"] if hypotheses else "Unknown",
        }
