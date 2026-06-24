# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
Multimodal module — real modality encoders/decoders and shared latent space.

P15: VisualEncoder (pixel→vector), AudioSpectralEncoder (waveform→vector),
     SharedLatentSpace (unified embedding space with cross-modal similarity).
P17: CNN conv2d Gabor filter bank (visual), MFCC + temporal attention (audio).
P18: VisualDecoder (latent→image), AudioWaveformDecoder (latent→waveform).
P19: ReconstructionCycle (autoencoder feature-level training),
     CrossModalSynthesizer (latent blending + cross-modal generation).
P20: Vectorized conv2d (10-100x faster), decoders in SimilarityService,
     MultimodalBridge for ED3N integration.
P21: MultimodalRetriever (vector index + cosine search),
     MultimodalRAGEngine (cross-modal retrieval → ED3N entries).
P22: VisualDecoder tanh detail enhancement; AudioWaveformDecoder multi-band + noise;
     MultimodalED3NAdapter (ED3N bidirectional wiring).
P24: VisualDecoder CNN transposed-conv texture; AudioWaveformDecoder wavetable synthesis;
     quality_metrics (SSIM/PSNR/SNR).
"""

from ai.multimodal.visual_encoder import VisualEncoder
from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder
from ai.multimodal.shared_latent_space import SharedLatentSpace
from ai.multimodal.similarity_service import MultimodalSimilarityService
from ai.multimodal.multimodal_processor import MultimodalProcessor
from ai.multimodal.visual_decoder import VisualDecoder
from ai.multimodal.audio_decoder import AudioWaveformDecoder
from ai.multimodal.reconstruction_cycle import ReconstructionCycle, CrossModalSynthesizer
from ai.multimodal.multimodal_bridge import MultimodalBridge
from ai.multimodal.multimodal_retriever import MultimodalRetriever
from ai.multimodal.multimodal_rag_engine import MultimodalRAGEngine
from ai.multimodal.multimodal_ed3n_adapter import MultimodalED3NAdapter
from ai.multimodal.quality_metrics import ssim, psnr, snr, quality_report
from ai.multimodal.continuous_multimodal_learning import ContinuousMultimodalLearning, CMLExample
from ai.multimodal.multimodal_memory import MultimodalMemoryStore
from ai.multimodal.semantic_visual import SemanticVisualEncoder
from ai.multimodal.semantic_audio import SemanticAudioEncoder
from ai.multimodal.dual_encoder_router import DualEncoderRouter
from ai.multimodal.semantic_key_mapper import SemanticKeyMapper
from ai.multimodal.three_layer_visual import ThreeLayerVisual

__all__ = [
    "VisualEncoder",
    "AudioSpectralEncoder",
    "SharedLatentSpace",
    "MultimodalSimilarityService",
    "MultimodalProcessor",
    "VisualDecoder",
    "AudioWaveformDecoder",
    "ReconstructionCycle",
    "CrossModalSynthesizer",
    "MultimodalBridge",
    "MultimodalRetriever",
    "MultimodalRAGEngine",
    "MultimodalED3NAdapter",
    "ssim",
    "psnr",
    "snr",
    "quality_report",
    "ContinuousMultimodalLearning",
    "CMLExample",
    "MultimodalMemoryStore",
    "SemanticVisualEncoder",
    "SemanticAudioEncoder",
    "DualEncoderRouter",
    "SemanticKeyMapper",
    "ThreeLayerVisual",
]
