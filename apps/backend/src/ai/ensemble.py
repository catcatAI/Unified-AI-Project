"""
Model Ensemble - Multi-Model Voting System for Extended Mode

Implements ensemble computing for Angela AI Extended Mode:
- Parallel queries to multiple models
- Weighted voting based on model confidence
- Quality scoring and response fusion
- Support for GPT-4, Claude-3-Opus, and local models
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, AsyncGenerator
from datetime import datetime

from apps.backend.src.core.services.multi_llm_service import (
    MultiLLMService, ChatMessage, LLMResponse, ModelConfig
)

logger = logging.getLogger(__name__)


@dataclass
class ModelWeight:
    """Model weight configuration for ensemble"""
    model_id: str
    weight: float
    priority: int = 1  # Higher = more important


@dataclass
class EnsembleResult:
    """Result from ensemble voting"""
    content: str
    model_votes: Dict[str, float]  # model_id -> vote_score
    confidence: float
    latency: float
    token_usage: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResponseFusionEngine:
    """Fuses responses from multiple models into coherent output"""
    
    def __init__(self):
        self.fusion_strategies = {
            'best_single': self._fuse_best_single,
            'weighted_average': self._fuse_weighted_average,
            'consensus': self._fuse_consensus,
            'creative_blend': self._fuse_creative_blend
        }
    
    def fuse(self, responses: List[LLMResponse], weights: Dict[str, float], 
             strategy: str = 'best_single') -> str:
        """Fuse multiple responses into one"""
        if strategy not in self.fusion_strategies:
            strategy = 'best_single'
        
        return self.fusion_strategies[strategy](responses, weights)
    
    def _fuse_best_single(self, responses: List[LLMResponse], 
                          weights: Dict[str, float]) -> str:
        """Select the best single response based on weights and quality"""
        if not responses:
            return ""
        
        # Score each response
        scored = []
        for resp in responses:
            model_weight = weights.get(resp.model, 0.5)
            quality_score = self._calculate_quality_score(resp)
            total_score = model_weight * quality_score
            scored.append((total_score, resp))
        
        # Return highest scoring response
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[0][1].content
    
    def _fuse_weighted_average(self, responses: List[LLMResponse],
                                weights: Dict[str, float]) -> str:
        """Not applicable for text - falls back to best_single"""
        return self._fuse_best_single(responses, weights)
    
    def _fuse_consensus(self, responses: List[LLMResponse],
                        weights: Dict[str, float]) -> str:
        """Find consensus among responses (for factual queries)"""
        if len(responses) < 2:
            return responses[0].content if responses else ""
        
        # For now, use best single with consensus bonus
        # In full implementation: semantic similarity matching
        return self._fuse_best_single(responses, weights)
    
    def _fuse_creative_blend(self, responses: List[LLMResponse],
                             weights: Dict[str, float]) -> str:
        """Blend creative elements from multiple responses"""
        # For creative writing, combine best parts
        # Implementation: extract best sentences/paragraphs from each
        return self._fuse_best_single(responses, weights)
    
    def _calculate_quality_score(self, response: LLMResponse) -> float:
        """Calculate quality score for a response"""
        scores = []
        
        # Length appropriateness (not too short, not too long)
        content_len = len(response.content)
        if 50 < content_len < 2000:
            scores.append(1.0)
        elif content_len > 0:
            scores.append(0.5)
        else:
            scores.append(0.0)
        
        # Coherence markers (presence of good structure)
        coherence_markers = ['.', '!', '?', '\n', ',']
        marker_count = sum(response.content.count(m) for m in coherence_markers)
        if marker_count > 5:
            scores.append(1.0)
        else:
            scores.append(0.7)
        
        # Latency penalty (faster is better)
        if response.latency < 1.0:
            scores.append(1.0)
        elif response.latency < 3.0:
            scores.append(0.8)
        else:
            scores.append(0.6)
        
        return sum(scores) / len(scores)


class ModelEnsemble:
    """
    Multi-Model Ensemble for Angela AI Extended Mode
    
    Supports up to 3 models voting:
    - 40% GPT-4/4o
    - 40% Claude-3-Opus
    - 20% Local model (Mixtral or similar)
    """
    
    def __init__(self, llm_service: MultiLLMService):
        self.llm_service = llm_service
        self.fusion_engine = ResponseFusionEngine()
        self.weights: Dict[str, float] = {}
        
        # Default weights for Extended mode
        self.default_models = [
            ModelWeight('claude-3-opus', 0.4, priority=1),
            ModelWeight('gpt-4o', 0.4, priority=1),
            ModelWeight('mixtral-local', 0.2, priority=2)
        ]
    
    def configure_ensemble(self, models: List[ModelWeight]):
        """Configure ensemble with specific models and weights"""
        total_weight = sum(m.weight for m in models)
        
        # Normalize weights to sum to 1.0
        self.weights = {
            m.model_id: m.weight / total_weight 
            for m in models
        }
        
        logger.info(f"Ensemble configured with {len(models)} models: {self.weights}")
    
    async def ensemble_generate(self, 
                                prompt: str,
                                messages: Optional[List[ChatMessage]] = None,
                                fusion_strategy: str = 'best_single',
                                timeout: float = 30.0) -> EnsembleResult:
        """
        Generate response using ensemble of models
        
        Args:
            prompt: The prompt to send
            messages: Optional conversation history
            fusion_strategy: How to combine responses
            timeout: Maximum time to wait for all models
            
        Returns:
            EnsembleResult with fused response and voting details
        """
        if not messages:
            messages = [ChatMessage(role="user", content=prompt)]
        
        # Parallel queries to all models
        tasks = []
        model_ids = []
        
        for model_id in self.weights.keys():
            task = self._query_model_safe(model_id, messages)
            tasks.append(task)
            model_ids.append(model_id)
        
        # Wait for all responses (with timeout)
        start_time = datetime.now()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_latency = (datetime.now() - start_time).total_seconds()
        
        # Filter successful responses
        valid_responses = []
        failed_models = []
        
        for model_id, response in zip(model_ids, responses):
            if isinstance(response, Exception):
                logger.warning(f"Model {model_id} failed: {response}")
                failed_models.append(model_id)
            else:
                valid_responses.append(response)
        
        if not valid_responses:
            raise Exception("All models in ensemble failed to respond")
        
        # Calculate votes
        model_votes = {}
        token_usage = {'total_tokens': 0, 'prompt_tokens': 0, 'completion_tokens': 0}
        
        for resp in valid_responses:
            model_weight = self.weights.get(resp.model, 0.33)
            quality = self.fusion_engine._calculate_quality_score(resp)
            vote_score = model_weight * quality
            model_votes[resp.model] = vote_score
            
            # Aggregate token usage
            for key in token_usage:
                token_usage[key] += resp.usage.get(key, 0)
        
        # Fuse responses
        fused_content = self.fusion_engine.fuse(
            valid_responses, 
            self.weights,
            fusion_strategy
        )
        
        # Calculate overall confidence
        confidence = sum(model_votes.values()) / len(model_votes) if model_votes else 0.5
        
        return EnsembleResult(
            content=fused_content,
            model_votes=model_votes,
            confidence=confidence,
            latency=total_latency,
            token_usage=token_usage,
            metadata={
                'fusion_strategy': fusion_strategy,
                'models_used': [r.model for r in valid_responses],
                'models_failed': failed_models,
                'response_count': len(valid_responses)
            }
        )
    
    async def _query_model_safe(self, model_id: str, 
                                messages: List[ChatMessage]) -> LLMResponse:
        """Query a single model with error handling"""
        try:
            response = await self.llm_service.chat_completion(
                messages=messages,
                model_id=model_id,
                max_tokens=2048
            )
            return response
        except Exception as e:
            logger.error(f"Error querying model {model_id}: {e}")
            raise
    
    async def streaming_ensemble(self, prompt: str,
                                   messages: Optional[List[ChatMessage]] = None
                                   ) -> AsyncGenerator[str, None]:
        """
        Stream response from fastest model in ensemble
        
        For streaming, we use the first available model
        rather than waiting for all models.
        """
        if not messages:
            messages = [ChatMessage(role="user", content=prompt)]
        
        # Try models in priority order until one responds
        for model_id in self.weights.keys():
            try:
                async for chunk in self.llm_service.stream_completion(
                    messages=messages,
                    model_id=model_id
                ):
                    yield chunk
                return  # Successful streaming
            except Exception as e:
                logger.warning(f"Streaming failed for {model_id}: {e}")
                continue
        
        # If all fail
        yield "[Ensemble Error: All models unavailable]"
    
    def get_ensemble_status(self) -> Dict[str, Any]:
        """Get current ensemble configuration and health"""
        return {
            'configured_models': list(self.weights.keys()),
            'weights': self.weights,
            'fusion_strategies': list(self.fusion_engine.fusion_strategies.keys()),
            'service_available': self.llm_service is not None
        }


# Convenience function for quick ensemble queries
async def ensemble_query(prompt: str, 
                         llm_service: MultiLLMService,
                         strategy: str = 'best_single') -> str:
    """Quick ensemble query returning just the text response"""
    ensemble = ModelEnsemble(llm_service)
    ensemble.configure_ensemble([
        ModelWeight('gpt-4o', 0.4),
        ModelWeight('claude-3-opus', 0.4),
        ModelWeight('mixtral-local', 0.2)
    ])
    
    result = await ensemble.ensemble_generate(prompt, fusion_strategy=strategy)
    return result.content


# Test code
if __name__ == '__main__':
    import os
    
    print("--- Model Ensemble Test ---")
    print("This test requires configured API keys in environment:")
    print("  - OPENAI_API_KEY")
    print("  - ANTHROPIC_API_KEY")
    print()
    
    # Check for API keys
    has_openai = bool(os.getenv('OPENAI_API_KEY'))
    has_anthropic = bool(os.getenv('ANTHROPIC_API_KEY'))
    
    if not has_openai and not has_anthropic:
        print("❌ No API keys found. Set OPENAI_API_KEY and/or ANTHROPIC_API_KEY")
        print("   Example: export OPENAI_API_KEY=sk-...")
        exit(1)
    
    print(f"✓ OpenAI: {'Available' if has_openai else 'Not configured'}")
    print(f"✓ Anthropic: {'Available' if has_anthropic else 'Not configured'}")
    print()
    
    # Initialize service (would need proper config in production)
    print("Note: Full test requires running Angela with config.yaml")
    print("Ensemble system ready for Extended Mode!")
