import math
from typing import Dict, Any, List

class VDAFManager:
    """
    Value-Driven Action Framework (VDAF) Manager.
    Calculates V_Total score to determine governance intervention.
    Uses Semantic Analysis (Embeddings) if available, falls back to keywords.
    """
    
    def __init__(self, brain=None):
        self.brain = brain
        self.m6_lock_threshold = 0.60
        
        # Keyword Fallback
        self.high_risk_keywords = [
            "delete", "remove", "format", "rm -rf", "shutdown", 
            "kill", "destroy", "hack", "bypass", "override"
        ]
        self.medium_risk_keywords = [
            "change", "modify", "update", "write", "upload", 
            "execute", "run", "script"
        ]
        
        # Semantic Concepts (for embedding comparison)
        self.high_risk_concepts = [
            "delete all files", "destroy system", "format hard drive", 
            "bypass security", "kill process", "shutdown server"
        ]
        self.medium_risk_concepts = [
            "modify configuration", "update database", "execute script",
            "write to file"
        ]
        
        self.safe_concepts = [
            "saying hello", "asking for help", "roleplaying", "telling a joke", 
            "casual conversation", "meowing", "greeting"
        ]
        
        self.concept_embeddings = {}
        # Embeddings will be loaded lazily or on first use if brain is ready

    def _get_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
            
        return dot_product / (magnitude1 * magnitude2)

    async def calculate_vda_score(self, context: Dict[str, Any]) -> float:
        """
        Calculates the V_Total score based on context risk and logic certainty.
        V_Total = (ContextRisk * 0.6) + (LogicUncertainty * 0.4)
        """
        user_input = context.get('user_input', '').lower()
        risk_score = 0.0
        
        # Try Semantic Analysis first
        if self.brain:
            try:
                input_embedding = await self.brain.get_embedding(user_input)
                if input_embedding:
                    # Check against High Risk Concepts
                    max_sim = 0.0
                    for concept in self.high_risk_concepts:
                        # Cache concept embeddings
                        if concept not in self.concept_embeddings:
                            self.concept_embeddings[concept] = await self.brain.get_embedding(concept)
                        
                        sim = self._get_cosine_similarity(input_embedding, self.concept_embeddings[concept])
                        if sim > max_sim:
                            max_sim = sim
                    
                    if max_sim > 0.7: # Semantic threshold
                        risk_score = 0.9
                    
                    # Check Medium Risk if not High
                    if risk_score == 0.0:
                        max_sim_med = 0.0
                        for concept in self.medium_risk_concepts:
                            if concept not in self.concept_embeddings:
                                self.concept_embeddings[concept] = await self.brain.get_embedding(concept)
                            
                            sim = self._get_cosine_similarity(input_embedding, self.concept_embeddings[concept])
                            if sim > max_sim_med:
                                max_sim_med = sim
                        
                        if max_sim_med > 0.7:
                             risk_score = 0.5
                    
                    # Check Safe Concepts to reduce risk (False Positive Mitigation)
                    if risk_score > 0.0:
                        max_sim_safe = 0.0
                        for concept in self.safe_concepts:
                            if concept not in self.concept_embeddings:
                                self.concept_embeddings[concept] = await self.brain.get_embedding(concept)
                            
                            sim = self._get_cosine_similarity(input_embedding, self.concept_embeddings[concept])
                            if sim > max_sim_safe:
                                max_sim_safe = sim
                        
                        if max_sim_safe > 0.6:
                            # If it's strongly safe, override risk
                            print(f"DEBUG: Safe Concept Detected ({max_sim_safe:.2f}). Reducing risk.")
                            risk_score = 0.0
            except Exception as e:
                print(f"Semantic Analysis Failed: {e}")
                # Fallback to keywords
        
        # Fallback to Keywords if Semantic failed or returned 0 risk (double check)
        if risk_score == 0.0:
            for word in self.high_risk_keywords:
                if word in user_input:
                    risk_score = 0.9
                    break
            
            if risk_score == 0.0:
                for word in self.medium_risk_keywords:
                    if word in user_input:
                        risk_score = 0.5
                        break
        
        # 2. Logic Uncertainty
        logic_uncertainty = 0.2
        
        v_total = (risk_score * 0.6) + (logic_uncertainty * 0.4)
        
        context['v_total'] = v_total
        context['risk_score'] = risk_score
        
        return v_total

    def is_lock_triggered(self, v_total: float) -> bool:
        return v_total > self.m6_lock_threshold
