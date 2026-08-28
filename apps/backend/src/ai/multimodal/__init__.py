# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
Multimodal module — real modality encoders/decoders and shared latent space.

Lazy-import design: only SharedLatentSpace is eagerly imported (it's tiny).
Heavy classes (encoders, decoders, torch-based modules) are imported on first
use to avoid dragging torch/CLIP/Whisper into every `import ai.multimodal`.
"""

from ai.multimodal.shared_latent_space import SharedLatentSpace

# Lazy re-exports: only imported when accessed via `from ai.multimodal import X`
# This avoids loading torch/CLIP/Whisper at module import time.
_LAZY_IMPORTS = {
    "AudioWaveformDecoder": "ai.multimodal.audio_decoder",
    "AudioSpectralEncoder": "ai.multimodal.audio_encoder_spectral",
    "DualEncoderRouter": "ai.multimodal.dual_encoder_router",
    "MultimodalBridge": "ai.multimodal.multimodal_bridge",
    "MultimodalED3NAdapter": "ai.multimodal.multimodal_ed3n_adapter",
    "MultimodalMemoryStore": "ai.multimodal.multimodal_memory",
    "MultimodalRAGEngine": "ai.multimodal.multimodal_rag_engine",
    "MultimodalRetriever": "ai.multimodal.multimodal_retriever",
    "MultimodalSimilarityService": "ai.multimodal.similarity_service",
    "SemanticAudioEncoder": "ai.multimodal.semantic_audio",
    "SemanticVisualEncoder": "ai.multimodal.semantic_visual",
    "SemanticKeyMapper": "ai.multimodal.semantic_key_mapper",
    "ThreeLayerVisual": "ai.multimodal.three_layer_visual",
    "VisualDecoder": "ai.multimodal.visual_decoder",
    "VisualEncoder": "ai.multimodal.visual_encoder",
    "ContinuousMultimodalLearning": "ai.multimodal.continuous_multimodal_learning",
    "CMLExample": "ai.multimodal.continuous_multimodal_learning",
    "ReconstructionCycle": "ai.multimodal.reconstruction_cycle",
    "CrossModalSynthesizer": "ai.multimodal.reconstruction_cycle",
}

# Quality metrics are small pure-numpy — safe to import eagerly
from ai.multimodal.quality_metrics import psnr, quality_report, snr, ssim

__all__ = [
    "SharedLatentSpace",
    "ssim",
    "psnr",
    "snr",
    "quality_report",
] + list(_LAZY_IMPORTS.keys())


def __getattr__(name: str):
    """Lazy import: only loads the module when the attribute is first accessed."""
    if name in _LAZY_IMPORTS:
        import importlib

        module = importlib.import_module(_LAZY_IMPORTS[name])
        cls = getattr(module, name)
        # Cache so subsequent access is fast
        globals()[name] = cls
        return cls
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
