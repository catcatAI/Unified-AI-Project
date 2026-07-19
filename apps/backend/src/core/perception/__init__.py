"""
Perception module — visual/auditory/tactile sampling, attention, memory.

P30: PerceptionEngine (multi-modal fusion, confidence estimation).
P31: AttentionController (saliency, IOR, scan path).
P32: VisualSampler, AuditorySampler, TactileSampler (particle-based sampling).
PerceptualMemory, AuditoryMemory, TactileMemory (per-modality short-term memory).
"""

from core.perception.attention_controller import AttentionController, AttentionMode
from core.perception.auditory_attention import AuditoryAttentionController
from core.perception.auditory_memory import AuditoryMemory
from core.perception.auditory_sampler import AudioFeatureType, AudioParticle, AuditorySampler
from core.perception.fallback_perception import FallbackPerception
from core.perception.perception_engine import PerceptionEngine
from core.perception.perceptual_memory import PerceivedObject, PerceptualMemory
from core.perception.tactile_memory import TactileMemory
from core.perception.tactile_sampler import (
    MaterialType,
    TactileContactPoint,
    TactileProperties,
    TactileSampler,
)
from core.perception.visual_sampler import SamplingDistribution, SamplingParticle, VisualSampler

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
