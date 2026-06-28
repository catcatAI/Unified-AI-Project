"""
Perception module — visual/auditory/tactile sampling, attention, memory.

P30: PerceptionEngine (multi-modal fusion, confidence estimation).
P31: AttentionController (saliency, IOR, scan path).
P32: VisualSampler, AuditorySampler, TactileSampler (particle-based sampling).
PerceptualMemory, AuditoryMemory, TactileMemory (per-modality short-term memory).
"""

from core.perception.attention_controller import AttentionMode, AttentionController
from core.perception.auditory_attention import AuditoryAttentionController
from core.perception.auditory_memory import AuditoryMemory
from core.perception.auditory_sampler import AuditorySampler, AudioParticle, AudioFeatureType
from core.perception.fallback_perception import FallbackPerception
from core.perception.perception_engine import PerceptionEngine
from core.perception.perceptual_memory import PerceptualMemory, PerceivedObject
from core.perception.tactile_memory import TactileMemory
from core.perception.tactile_sampler import TactileSampler, TactileProperties, TactileContactPoint, MaterialType
from core.perception.visual_sampler import VisualSampler, SamplingParticle, SamplingDistribution

__all__ = [
    "AttentionMode",
    "AttentionController",
    "AuditoryAttentionController",
    "AuditoryMemory",
    "AuditorySampler",
    "AudioParticle",
    "AudioFeatureType",
    "FallbackPerception",
    "PerceptionEngine",
    "PerceptualMemory",
    "PerceivedObject",
    "TactileMemory",
    "TactileSampler",
    "TactileProperties",
    "TactileContactPoint",
    "MaterialType",
    "VisualSampler",
    "SamplingParticle",
    "SamplingDistribution",
]
