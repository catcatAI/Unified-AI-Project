import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from ai.multimodal.audio_decoder import AudioWaveformDecoder, load_default_audio_decoder_weights
from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder
from ai.multimodal.generator.sequence_generator import SequenceGenerator
from ai.multimodal.quality_metrics import snr
from ai.multimodal.reconstruction_cycle import ReconstructionCycle
from ai.multimodal.shared_latent_space import SharedLatentSpace
from ai.multimodal.visual_decoder import VisualDecoder
from ai.multimodal.visual_encoder import VisualEncoder

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================


logger = logging.getLogger(__name__)


# Type alias for contrastive pair: (mod_a, feat_a, mod_b, feat_b)
ContrastivePair = Tuple[str, np.ndarray, str, np.ndarray]


# Default weight save path
DEFAULT_WEIGHTS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent
    / "data"
    / "multimodal"
    / "weights"
)
DEFAULT_WEIGHTS_PATH = str(DEFAULT_WEIGHTS_DIR / "p29_trained.npz")


class ContrastiveBatchTrainer:
    """Batch contrastive trainer for SharedLatentSpace.

    Generates training pairs from synthetic modality data and trains
    the latent space projection matrices via contrastive loss.
    """

    def __init__(
        self,
        latent_space: SharedLatentSpace,
        visual_encoder: Optional[VisualEncoder] = None,
        audio_encoder: Optional[AudioSpectralEncoder] = None,
    ):
        self._ls = latent_space
        self._visual_encoder = visual_encoder or VisualEncoder()
        self._audio_encoder = audio_encoder or AudioSpectralEncoder()

    def generate_pairs(
        self, n_pairs: int, img_dim: int = 256, aud_dim: int = 128
    ) -> Tuple[List, List]:
        """Generate synthetic positive/negative training pairs.

        Returns (pos_pairs, neg_pairs) where each element is
        (mod_a, feat_a, mod_b, feat_b).
        """
        pos_pairs: List[ContrastivePair] = []
        neg_pairs: List[ContrastivePair] = []
        rng = np.random.RandomState(42)
        for _ in range(n_pairs):
            seed = rng.randn(img_dim).astype(np.float32)
            feat_img = seed + rng.randn(img_dim).astype(np.float32) * 0.1
            feat_aud = seed[:aud_dim] + rng.randn(aud_dim).astype(np.float32) * 0.1
            pos_pairs.append(("vision", feat_img, "audio", feat_aud))
            feat_img2 = rng.randn(img_dim).astype(np.float32)
            feat_aud2 = rng.randn(aud_dim).astype(np.float32)
            neg_pairs.append(("vision", feat_img2, "audio", feat_aud2))
        return pos_pairs, neg_pairs

    def train_epoch(
        self, pos_pairs: List, neg_pairs: List, lr: float = 0.01, margin: float = 0.5
    ) -> float:
        """Train one epoch over the given pairs.

        Returns average contrastive loss.
        """
        return self._ls._train_epoch(pos_pairs, neg_pairs, lr, margin)

    def train(
        self, n_epochs: int = 10, n_pairs_per_epoch: int = 20, lr: float = 0.01, margin: float = 0.5
    ) -> Dict:
        """Full training run. Returns dict with final_loss and loss_history."""
        pos_pairs, neg_pairs = self.generate_pairs(n_pairs_per_epoch)
        return self._ls.train(pos_pairs, neg_pairs, epochs=n_epochs, lr=lr, margin=margin)

    def train_on_real_pairs(
        self,
        pos_pairs: List[ContrastivePair],
        neg_pairs: List[ContrastivePair],
        epochs: int = 5,
        lr: float = 0.01,
        margin: float = 0.5,
    ) -> Dict:
        """Train on real data pairs from data loaders.

        Args:
            pos_pairs: List of (mod, feat, mod, feat) — same-class pairs
            neg_pairs: List of (mod, feat, mod, feat) — different-class pairs
            epochs: Number of training epochs
            lr: Learning rate

        Returns:
            dict with 'final_loss' and 'history'
        """
        return self._ls.train(pos_pairs, neg_pairs, epochs=epochs, lr=lr, margin=margin)


class ReconstructionTrainer:
    """Trains decoders via feature-level reconstruction on synthetic data."""

    def __init__(self, latent_space: SharedLatentSpace, reconstruction_cycle: ReconstructionCycle):
        self._ls = latent_space
        self._rc = reconstruction_cycle

    def generate_features(self, n_samples: int) -> Dict[str, List[np.ndarray]]:
        """Generate synthetic training features for each registered modality."""
        rng = np.random.RandomState(123)
        result: Dict[str, List[np.ndarray]] = {}
        for mod in self._ls._projections:
            # Use correct dimension per modality
            if mod == "vision":
                feat_dim = 256
            elif mod == "audio":
                feat_dim = 128
            else:
                feat_dim = 64
            samples = [rng.randn(feat_dim).astype(np.float32) for _ in range(n_samples)]
            result[mod] = samples
        return result

    def train(self, n_epochs: int = 10, n_samples: int = 10, lr: float = 0.005) -> Dict:
        """Train reconstruction cycle over all modalities using synthetic features.

        Returns dict per modality with final_loss and history.
        """
        results: Dict[str, Dict] = {}
        for mod in self._ls._projections:
            features = self.generate_features(n_samples)
            mod_features = features.get(mod, [])
            if not mod_features:
                continue
            mod_results = self._rc.train(mod, mod_features, epochs=n_epochs, lr=lr)
            results[mod] = {
                "final_loss": mod_results["final_loss"],
                "history": mod_results["history"][-5:] if mod_results.get("history") else [],
            }
        return results

    def train_on_real_features(
        self, real_features: Dict[str, List[np.ndarray]], epochs: int = 5, lr: float = 0.005
    ) -> Dict:
        """Train reconstruction on real encoded features.

        Args:
            real_features: {modality: [feature_vectors]}
            epochs: Training epochs
            lr: Learning rate

        Returns:
            dict per modality with 'final_loss' and 'history'
        """
        results: Dict[str, Dict] = {}
        for mod, features in real_features.items():
            if not features:
                continue
            mod_results = self._rc.train(mod, features, epochs=epochs, lr=lr)
            results[mod] = {
                "final_loss": mod_results["final_loss"],
                "history": mod_results["history"][-5:] if mod_results.get("history") else [],
            }
        return results


class TextureTrainer:
    """Trains VisualDecoder texture branch via pixel-level reconstruction.

    Uses the existing VisualEncoder to encode images → latents, then trains
    the texture branch (W_hidden, W_featmap, tex_kernels) to minimize pixel MSE
    between the full decoder output and the original image.

    Can operate in two modes:
    1. Synthetic mode: generates random latents + synthetic target images
    2. Real mode: uses real images from RealDataProvider
    """

    def __init__(
        self,
        reconstruction_cycle: ReconstructionCycle,
        visual_decoder: VisualDecoder,
        visual_encoder: Optional[VisualEncoder] = None,
    ):
        self._rc = reconstruction_cycle
        self._decoder = visual_decoder
        self._visual_encoder = visual_encoder or VisualEncoder()

    def generate_synthetic_batch(self, batch_size: int, rng_seed: int = 42) -> tuple:
        """Generate a batch of (latent, target_image) pairs from scratch.

        Creates random latents, runs the projection branch only to get base
        images as targets. This trains texture to produce zero output initially,
        providing a clean baseline from which texture can learn structure.
        """
        rng = np.random.RandomState(rng_seed)
        z = rng.randn(batch_size, self._decoder.LATENT_DIM).astype(np.float32)
        targets = np.zeros(
            (batch_size, self._decoder.INPUT_SIZE, self._decoder.INPUT_SIZE, 3), dtype=np.uint8
        )
        for b in range(batch_size):
            raw = self._decoder._W @ z[b] + self._decoder._b
            spatial = raw[: self._decoder.SPATIAL_FEATURES]
            color = raw[
                self._decoder.SPATIAL_FEATURES : self._decoder.SPATIAL_FEATURES
                + self._decoder.COLOR_FEATURES
            ]
            img = self._decoder._layout_to_image(spatial)
            img = self._decoder._apply_color_adjust(img, color)
            targets[b] = np.clip(img, 0, 255).astype(np.uint8)
        return z, targets

    def train(
        self, batch_size: int = 4, steps: int = 50, lr: float = 0.001, rng_seed: int = 42
    ) -> Dict:
        """Train texture branch using synthetic data.

        Args:
            batch_size: Samples per step
            steps: Number of gradient steps
            lr: Learning rate

        Returns:
            Dict with 'final_loss' and 'history'
        """
        history = []
        for step in range(steps):
            z, targets = self.generate_synthetic_batch(batch_size, rng_seed=rng_seed + step)
            loss = self._rc.train_texture_step(z, targets, lr=lr)
            history.append(loss)
        return {"final_loss": history[-1] if history else 0.0, "history": history}

    def train_on_real(
        self, real_images: List[np.ndarray], steps: int = 50, lr: float = 0.001
    ) -> Dict:
        """Train texture branch using real images.

        Encodes each image → latent, then trains texture to reconstruct
        the original pixel image.

        Args:
            real_images: List of (H, W, 3) uint8 images
            steps: Number of gradient steps over the dataset (epochs)
            lr: Learning rate

        Returns:
            Dict with 'final_loss' and 'history'
        """
        if not real_images:
            return {"final_loss": 0.0, "history": []}

        latents = []
        for img in real_images:
            feats = self._visual_encoder.encode(img)
            if hasattr(self._rc._ls, "project"):
                z = self._rc._ls.project("vision", feats)
            else:
                z = np.zeros(self._decoder.LATENT_DIM, dtype=np.float32)
            latents.append(z)

        history = []
        for step in range(steps):
            total_loss = 0.0
            for z, img in zip(latents, real_images):
                z_batch = z.reshape(1, -1)
                img_batch = img.reshape(1, *img.shape)
                loss = self._rc.train_texture_step(z_batch, img_batch, lr=lr)
                total_loss += loss
            avg_loss = total_loss / max(len(real_images), 1)
            history.append(avg_loss)

        return {"final_loss": history[-1] if history else 0.0, "history": history}


class WavetableTrainer:
    """Trains AudioWaveformDecoder wavetable + hidden branch via waveform MSE.

    Like TextureTrainer, this trains the non-projection weight arrays
    (W_hidden, b_hidden, W_wavetable, b_wavetable, W_noise, b_noise)
    using synthetic targets derived from the projection branch.

    The projection branch determines frequency/envelope; the wavetable
    branch learns to produce structured harmonic content at those
    frequencies.
    """

    def __init__(
        self, reconstruction_cycle: ReconstructionCycle, audio_decoder: AudioWaveformDecoder
    ):
        self._rc = reconstruction_cycle
        self._decoder = audio_decoder

    def generate_target(self, latent: np.ndarray) -> np.ndarray:
        """Generate target waveform from projection parameters only.

        Creates a clean harmonic waveform using the projection's frequency
        and envelope outputs, giving the wavetable branch a structured target.
        """
        raw = self._decoder._W @ latent + self._decoder._b
        spectral_env = raw[:40]
        temporal_env = raw[40:50]

        n_samples = int(self._decoder.SAMPLE_RATE * self._decoder.DURATION)
        t = np.arange(n_samples, dtype=np.float32) / self._decoder.SAMPLE_RATE

        waveform = np.zeros(n_samples, dtype=np.float32)

        for band_idx, (lo, hi) in enumerate(self._decoder.BAND_LIMITS):
            feats = spectral_env[
                band_idx
                * (len(spectral_env) // self._decoder.N_BANDS) : (band_idx + 1)
                * (len(spectral_env) // self._decoder.N_BANDS)
            ]
            freq_hz = 200.0 + np.abs(feats[:5]).mean() * (hi - lo) / 800.0
            freq_hz = np.clip(freq_hz, lo, hi)

            band_wave = np.sin(2 * np.pi * freq_hz * t)
            for h_idx in range(3):
                h_freq = freq_hz * (h_idx + 2)
                if h_freq < self._decoder.SAMPLE_RATE / 2:
                    band_wave += (1.0 / (h_idx + 2)) * np.sin(2 * np.pi * h_freq * t)

            band_peak = max(np.abs(band_wave).max(), 1e-8)
            band_wave /= band_peak
            waveform += band_wave / self._decoder.N_BANDS

        n_env = len(temporal_env)
        env_points = np.linspace(0, n_samples, n_env + 1).astype(int)
        envelope = np.zeros(n_samples, dtype=np.float32)
        for i in range(n_env):
            start = env_points[i]
            end = env_points[i + 1]
            val = np.clip(np.abs(temporal_env[i]), 0.0, 1.0)
            envelope[start:end] = val
        waveform *= envelope

        peak = max(np.abs(waveform).max(), 1e-8)
        waveform /= peak
        return waveform.astype(np.float32)

    def generate_synthetic_batch(self, batch_size: int, rng_seed: int = 42) -> tuple:
        """Generate a batch of (latent, target_waveform) pairs."""
        rng = np.random.RandomState(rng_seed)
        z = rng.randn(batch_size, self._decoder.LATENT_DIM).astype(np.float32)
        targets = np.zeros(
            (batch_size, int(self._decoder.SAMPLE_RATE * self._decoder.DURATION)), dtype=np.float32
        )
        for b in range(batch_size):
            targets[b] = self.generate_target(z[b])
        return z, targets

    def train(
        self, batch_size: int = 4, steps: int = 50, lr: float = 0.001, rng_seed: int = 42
    ) -> Dict:
        """Train wavetable branch using synthetic data.

        Args:
            batch_size: Samples per gradient step
            steps: Number of gradient steps
            lr: Learning rate

        Returns:
            Dict with 'final_loss' and 'history'
        """
        history = []
        for step in range(steps):
            z, targets = self.generate_synthetic_batch(batch_size, rng_seed=rng_seed + step)
            loss = self._rc.train_wavetable_step(z, targets, lr=lr)
            history.append(loss)
        return {"final_loss": history[-1] if history else 0.0, "history": history}


class SequenceTrainer:
    """Trains SequenceGenerator RNN via CLIP→primitive MSE with synthetic data.

    Generates random (CLIP embedding, primitive_sequence) pairs using
    TrainingDataGenerator, then trains the RNN weights via the fixed
    train_step() with proper BPTT.
    """

    def __init__(self, sequence_generator: SequenceGenerator):
        self._gen = sequence_generator

    def generate_synthetic_batch(self, batch_size: int, rng_seed: int = 42) -> tuple:
        """Generate a batch of (clip_embeddings, primitive_sequences) pairs."""
        from ai.multimodal.generator.training_data import TrainingDataGenerator

        tdg = TrainingDataGenerator()
        data = tdg.generate_random_primitives(
            n_samples=batch_size,
            primitive_dim=self._gen.primitive_dim,
            seed=rng_seed,
        )
        return data["clip_embeddings"], data["primitive_sequences"]

    def train(
        self, batch_size: int = 4, steps: int = 50, lr: float = 0.001, rng_seed: int = 42
    ) -> Dict:
        """Train SequenceGenerator using synthetic data.

        Args:
            batch_size: Samples per step
            steps: Number of gradient steps
            lr: Learning rate

        Returns:
            Dict with 'final_loss' and 'history'
        """
        history = []
        for step in range(steps):
            clip_embs, sequences = self.generate_synthetic_batch(
                batch_size, rng_seed=rng_seed + step
            )
            total_loss = 0.0
            for clip_emb, seq in zip(clip_embs, sequences):
                total_loss += self._gen.train_step(clip_emb, seq, lr=lr)
            avg_loss = total_loss / max(len(clip_embs), 1)
            history.append(avg_loss)
        return {"final_loss": history[-1] if history else 0.0, "history": history}


class LatentReasoningTrainer:
    """Trains LatentReasoningNetwork: latent(64) → MLP → text tokens.

    Phase 4: Uses (latent_vector, target_text) pairs from chat interactions
    or synthetic data to train the LRN to generate meaningful text from latent
    representations. This bridges the latent space to natural language.
    """

    def __init__(self, latent_reasoning_network):
        self._lrn = latent_reasoning_network

    def train_from_chat_data(
        self, latent_space, chat_history: list, epochs: int = 5, lr: float = 0.01
    ) -> dict:
        """Train LRN using chat interactions projected through SharedLatentSpace.

        Args:
            latent_space: SharedLatentSpace instance
            chat_history: List of (user_text, response_text) tuples
            epochs: Number of training epochs
            lr: Learning rate

        Returns:
            Dict with 'final_loss' and 'history'
        """
        if not chat_history:
            return {"final_loss": 0.0, "history": []}

        history = []
        for epoch in range(epochs):
            total_loss = 0.0
            count = 0
            for user_text, response_text in chat_history:
                # Encode response text to latent via SharedLatentSpace
                from ai.multimodal.text_encoder import TextEncoder

                text_encoder = TextEncoder(feature_dim=512)
                features = text_encoder.encode(response_text)
                if features is None or features.sum() == 0:
                    continue
                latent = latent_space.project("text", features)
                if latent is None:
                    continue

                # Train LRN: given this latent, predict the response text
                loss = self._lrn.train_step(latent, response_text, lr=lr)
                total_loss += loss
                count += 1

            avg_loss = total_loss / max(count, 1)
            history.append(avg_loss)

        return {"final_loss": history[-1] if history else 0.0, "history": history}

    def train_from_interaction(
        self, latent_space, user_text: str, response_text: str, lr: float = 0.01
    ) -> float:
        """Train LRN on a single interaction pair.

        Returns the training loss.
        """
        from ai.multimodal.text_encoder import TextEncoder

        text_encoder = TextEncoder(feature_dim=512)
        features = text_encoder.encode(response_text)
        if features is None or features.sum() == 0:
            return 0.0
        latent = latent_space.project("text", features)
        if latent is None:
            return 0.0
        return self._lrn.train_step(latent, response_text, lr=lr)


class PrimitiveTrainer:
    """Trains PrimitiveEncoder autoencoder on a library of geometric primitives.

    Phase 3d: Populates a PrimitiveLibrary with basic geometric shapes (circles,
    squares, triangles, lines, dots), then trains the PrimitiveEncoder as an
    autoencoder on these shapes. After training, decode() produces faithful
    geometric primitives instead of random noise.

    Optionally re-trains the SequenceGenerator on the library's embeddings so
    that generate() produces on-manifold embeddings that decode to recognizable
    shapes.
    """

    def __init__(self, primitive_encoder, sequence_generator=None):
        self._encoder = primitive_encoder
        self._gen = sequence_generator
        self._library = None

    def _create_library_shapes(self):
        """Create a library of basic geometric shapes with various colors and positions."""
        from .primitives.primitive_types import Arc, Circle, DrawingInstructions, Line, Plane, Point

        shapes = []
        colors = [
            (255, 0, 0),
            (0, 255, 0),
            (0, 0, 255),
            (255, 255, 0),
            (0, 255, 255),
            (255, 165, 0),
            (128, 0, 128),
            (255, 0, 255),
        ]

        bg = (255, 255, 255)

        # Circles: 3 radii × 3 positions × 8 colors (limited to avoid explosion)
        for cx, cy in [(0.5, 0.5), (0.3, 0.3), (0.7, 0.7)]:
            for r in [0.1, 0.2, 0.3]:
                for color in colors[:4]:
                    shapes.append(
                        DrawingInstructions(
                            circles=[Circle(cx, cy, r, color, (0, 0, 0), 0.02)], background_color=bg
                        )
                    )

        # Squares (rectangular planes): 2 sizes × 3 positions × 4 colors
        for cx, cy in [(0.5, 0.5), (0.3, 0.5), (0.5, 0.3)]:
            for rx, ry in [(0.15, 0.15), (0.25, 0.15), (0.15, 0.25)]:
                for color in colors[4:6]:
                    shapes.append(
                        DrawingInstructions(
                            planes=[
                                Plane(
                                    [
                                        Point(cx - rx, cy - ry, (0, 0, 0), 0),
                                        Point(cx + rx, cy - ry, (0, 0, 0), 0),
                                        Point(cx + rx, cy + ry, (0, 0, 0), 0),
                                        Point(cx - rx, cy + ry, (0, 0, 0), 0),
                                    ],
                                    color,
                                    (0, 0, 0),
                                    0.02,
                                )
                            ],
                            background_color=bg,
                        )
                    )

        # Triangles: 3-point planes × 4 colors
        tri_verts = [
            [(0.5, 0.2), (0.3, 0.8), (0.7, 0.8)],
            [(0.2, 0.5), (0.5, 0.2), (0.8, 0.5)],
            [(0.3, 0.3), (0.7, 0.3), (0.5, 0.7)],
        ]
        for verts in tri_verts:
            for color in colors[:4]:
                shapes.append(
                    DrawingInstructions(
                        planes=[
                            Plane(
                                [Point(x, y, (0, 0, 0), 0) for x, y in verts],
                                color,
                                (0, 0, 0),
                                0.02,
                            )
                        ],
                        background_color=bg,
                    )
                )

        # Lines: horizontal, vertical, diagonal × 4 colors
        line_defs = [
            [(0.1, 0.5), (0.9, 0.5)],
            [(0.5, 0.1), (0.5, 0.9)],
            [(0.1, 0.1), (0.9, 0.9)],
            [(0.9, 0.1), (0.1, 0.9)],
        ]
        for (sx, sy), (ex, ey) in line_defs:
            for color in colors[:4]:
                shapes.append(
                    DrawingInstructions(
                        lines=[
                            Line(
                                Point(sx, sy, (0, 0, 0), 0),
                                Point(ex, ey, (0, 0, 0), 0),
                                0.04,
                                color,
                            )
                        ],
                        background_color=bg,
                    )
                )

        # Dots: single points × 4 colors × 3 positions
        for px, py in [(0.3, 0.3), (0.5, 0.5), (0.7, 0.7)]:
            for color in colors[:4]:
                shapes.append(
                    DrawingInstructions(points=[Point(px, py, color, 0.15)], background_color=bg)
                )

        # Arcs: partial circles × 4 colors
        for start_angle, end_angle in [(0, 3.14), (3.14, 6.28), (1.57, 4.71)]:
            for color in colors[:4]:
                shapes.append(
                    DrawingInstructions(
                        arcs=[Arc(0.5, 0.5, 0.3, start_angle, end_angle, 0.04, color)],
                        background_color=bg,
                    )
                )

        return shapes

    def train(
        self,
        epochs: int = 100,
        lr: float = 0.001,
        seq_epochs: int = 50,
        seq_lr: float = 0.001,
        n_seq_samples: int = 500,
    ) -> dict:
        """Train PrimitiveEncoder autoencoder and optionally re-train SequenceGenerator.

        Phase 3d:
          1. Create library of geometric shapes
          2. PrimitiveEncoder autoencoder training
          3. Re-encode library with trained encoder
          4. Optionally train SequenceGenerator on library embeddings

        Args:
            epochs: PrimitiveEncoder training epochs
            lr: PrimitiveEncoder learning rate
            seq_epochs: SequenceGenerator re-training epochs (0 to skip)
            seq_lr: SequenceGenerator learning rate
            n_seq_samples: Number of synthetic training pairs for SequenceGenerator

        Returns:
            Dict with 'encoder_result', 'library_size', and optional 'sequence_result'
        """
        from .primitives.primitive_library import PrimitiveLibrary

        # Step 1: Create shapes and encode with current (possibly untrained) encoder
        shapes = self._create_library_shapes()
        self._library = PrimitiveLibrary(
            embedding_dim=self._encoder.embedding_dim,
            max_primitives=len(shapes) + 100,
        )
        for i, shape in enumerate(shapes):
            emb = self._encoder.encode(shape)
            self._library.add_primitive(f"shape_{i:04d}", shape, emb)

        logger.info("PrimitiveTrainer: library populated with %d shapes", len(shapes))

        # Step 2: Train encoder autoencoder
        encoder_result = self._encoder.train(shapes, epochs=epochs, lr=lr)
        logger.info(
            "PrimitiveTrainer: encoder trained — best loss: %.6f", encoder_result["best_loss"]
        )

        # Step 3: Re-encode library with trained encoder
        for name in self._library._names:
            shape = self._library.get_primitive(name)
            emb = self._encoder.encode(shape)
            self._library._primitives[name]["embedding"] = emb
        self._library._dirty = True
        logger.info("PrimitiveTrainer: library re-encoded with trained encoder")

        result = {
            "encoder_result": encoder_result,
            "library_size": self._library.size,
        }

        # Step 4: Train SequenceGenerator on synthetic (clip, primitive) pairs
        if self._gen is not None and seq_epochs > 0:
            seq_result = self._train_sequence_generator(
                n_samples=n_seq_samples, epochs=seq_epochs, lr=seq_lr
            )
            result["sequence_result"] = seq_result

        return result

    def _train_sequence_generator(self, n_samples: int, epochs: int, lr: float) -> dict:
        """Create synthetic training data from library and train SequenceGenerator."""
        rng = np.random.default_rng(42)

        clip_embeddings = []
        primitive_sequences = []

        names = list(self._library._names)
        for _ in range(n_samples):
            name = rng.choice(names)
            prim_emb = self._library.get_embedding(name)
            if prim_emb is None:
                continue
            # Random CLIP-like vector
            clip_vec = rng.normal(0, 1, 512).astype(np.float32)
            clip_vec = clip_vec / (np.linalg.norm(clip_vec) + 1e-8)
            clip_embeddings.append(clip_vec)
            primitive_sequences.append([prim_emb.copy()])

        if not clip_embeddings:
            return {"final_loss": 0.0, "history": [], "epochs_trained": 0}

        logger.info(
            "PrimitiveTrainer: training SequenceGenerator on %d pairs", len(clip_embeddings)
        )
        result = self._gen.train(clip_embeddings, primitive_sequences, epochs=epochs, lr=lr)
        logger.info(
            "PrimitiveTrainer: SequenceGenerator trained — final loss: %.6f", result["final_loss"]
        )
        return result

    @property
    def library(self):
        return self._library

    @property
    def encoder(self):
        return self._encoder


class FullTrainingPipeline:
    """End-to-end training pipeline: contrastive pre-training + reconstruction fine-tuning.

    P27: Pure numpy — no external data dependencies. Uses synthetic data to train
    the projection matrices and decoder weights.

    P28: Supports real data via RealDataProvider. When real data is available,
    uses ESC-50 audio + CIFAR-10 images instead of random noise.
    """

    def __init__(
        self,
        latent_space: Optional[SharedLatentSpace] = None,
        visual_encoder: Optional[VisualEncoder] = None,
        audio_encoder: Optional[AudioSpectralEncoder] = None,
        visual_decoder=None,
        audio_decoder=None,
    ):
        if latent_space is not None:
            self._ls = latent_space
        else:
            from ai.multimodal.shared_latent_space import get_shared_latent_space

            self._ls = get_shared_latent_space(latent_dim=64)
        self._visual_encoder = visual_encoder or VisualEncoder()
        self._audio_encoder = audio_encoder or AudioSpectralEncoder()
        from ai.multimodal.visual_decoder import VisualDecoder, load_default_visual_decoder_weights

        self._visual_decoder = visual_decoder or VisualDecoder()
        load_default_visual_decoder_weights(self._visual_decoder)
        self._audio_decoder = audio_decoder or AudioWaveformDecoder()
        load_default_audio_decoder_weights(self._audio_decoder)
        self._reconstruction = ReconstructionCycle(
            self._ls, self._visual_decoder, self._audio_decoder
        )
        self._contrastive = ContrastiveBatchTrainer(
            self._ls, self._visual_encoder, self._audio_encoder
        )
        self._primitive_encoder = None  # lazy init in train_primitives
        self._primitive_library = None  # populated by PrimitiveTrainer
        self._sequence_generator = SequenceGenerator()

    def run(
        self,
        contrastive_epochs: int = 10,
        contrastive_pairs: int = 20,
        recon_epochs: int = 10,
        recon_samples: int = 10,
        lr: float = 0.01,
    ) -> Dict:
        """Run full training pipeline.

        Phase 1: Contrastive pre-training of SharedLatentSpace.
        Phase 2: Reconstruction fine-tuning of decoders.
        """
        logger.info("=== Phase 1: Contrastive training ===")
        pos_pairs, neg_pairs = self._contrastive.generate_pairs(contrastive_pairs)
        contrastive_result = self._ls.train(
            pos_pairs,
            neg_pairs,
            epochs=contrastive_epochs,
            lr=lr,
        )
        logger.info("Contrastive final loss: %.6f", contrastive_result["final_loss"])

        logger.info("=== Phase 2: Reconstruction training ===")
        recon_result = ReconstructionTrainer(self._ls, self._reconstruction).train(
            n_epochs=recon_epochs, n_samples=recon_samples, lr=lr * 0.5
        )
        for mod, res in recon_result.items():
            logger.info("  %s reconstruction final loss: %.6f", mod, res["final_loss"])

        return {
            "contrastive": contrastive_result,
            "reconstruction": recon_result,
        }

    def run_on_real(
        self,
        data_provider: "RealDataProvider",
        contrastive_epochs: int = 5,
        recon_epochs: int = 5,
        pairs_per_modality: int = 30,
        recon_samples_per_modality: int = 30,
        lr: float = 0.01,
    ) -> Dict:
        """Run full training pipeline on real data from RealDataProvider.

        Phase 1: Contrastive pre-training with real class-labeled pairs.
        Phase 2: Reconstruction fine-tuning with real encoded features.

        Falls back to synthetic data if real data is unavailable.
        """
        from ai.multimodal.data_loader import RealDataProvider as RDP

        if not isinstance(data_provider, RDP) or not data_provider.has_data():
            logger.warning("Real data unavailable, falling back to synthetic")
            return self.run(
                contrastive_epochs=contrastive_epochs,
                contrastive_pairs=pairs_per_modality,
                recon_epochs=recon_epochs,
                recon_samples=recon_samples_per_modality,
                lr=lr,
            )

        logger.info("=== Phase 1: Real contrastive training ===")
        pos_pairs, neg_pairs = data_provider.contrastive_pairs(
            n_per_modality=pairs_per_modality, same_prob=0.5
        )
        logger.info(
            "  Generated %d pos + %d neg pairs from real data", len(pos_pairs), len(neg_pairs)
        )
        contrastive_result = self._ls.train(
            pos_pairs,
            neg_pairs,
            epochs=contrastive_epochs,
            lr=lr,
        )
        logger.info("  Contrastive final loss: %.6f", contrastive_result["final_loss"])

        logger.info("=== Phase 2: Real reconstruction training ===")
        recon_features = data_provider.reconstruction_samples(
            n_per_modality=recon_samples_per_modality
        )
        recon_result = {}
        trainer = ReconstructionTrainer(self._ls, self._reconstruction)
        for mod, features in recon_features.items():
            if not features:
                continue
            mod_result = trainer.train_on_real_features(
                {mod: features}, epochs=recon_epochs, lr=lr * 0.5
            )
            if mod in mod_result:
                recon_result[mod] = mod_result[mod]
                logger.info(
                    "  %s reconstruction final loss: %.6f", mod, mod_result[mod]["final_loss"]
                )

        return {
            "contrastive": contrastive_result,
            "reconstruction": recon_result,
            "data_source": "real",
        }

    def train_texture(
        self, batch_size: int = 4, steps: int = 50, lr: float = 0.001, rng_seed: int = 42
    ) -> Dict:
        """Train the VisualDecoder texture branch (Phase 3).

        Uses TextureTrainer with synthetic data to train the 5 texture
        weight arrays (W_hidden, b_hidden, W_featmap, b_featmap, tex_kernels).

        The projection branch weights are frozen during this phase.

        Args:
            batch_size: Samples per gradient step
            steps: Number of gradient steps
            lr: Learning rate for texture weights
            rng_seed: Random seed for synthetic data generation

        Returns:
            Dict with 'final_loss' and 'history'
        """
        logger.info("=== Phase 3: Texture branch training ===")
        trainer = TextureTrainer(self._reconstruction, self._visual_decoder, self._visual_encoder)
        result = trainer.train(batch_size=batch_size, steps=steps, lr=lr, rng_seed=rng_seed)
        logger.info("Texture training final loss: %.6f", result["final_loss"])
        return result

    def train_wavetable(
        self, batch_size: int = 4, steps: int = 50, lr: float = 0.001, rng_seed: int = 42
    ) -> Dict:
        """Train the AudioWaveformDecoder wavetable + hidden branch (Phase 3b).

        Uses WavetableTrainer with synthetic data to train the 6 non-projection
        weight arrays (W_hidden, b_hidden, W_wavetable, b_wavetable, W_noise, b_noise).

        The projection branch weights are frozen during this phase.

        Args:
            batch_size: Samples per gradient step
            steps: Number of gradient steps
            lr: Learning rate for wavetable + hidden weights
            rng_seed: Random seed for synthetic data generation

        Returns:
            Dict with 'final_loss' and 'history'
        """
        logger.info("=== Phase 3b: Wavetable branch training ===")
        trainer = WavetableTrainer(self._reconstruction, self._audio_decoder)
        result = trainer.train(batch_size=batch_size, steps=steps, lr=lr, rng_seed=rng_seed)
        logger.info("Wavetable training final loss: %.6f", result["final_loss"])
        return result

    def train_sequence(
        self, batch_size: int = 4, steps: int = 50, lr: float = 0.001, rng_seed: int = 42
    ) -> Dict:
        """Train the SequenceGenerator RNN (Phase 3c).

        Uses SequenceTrainer with synthetic data to train all RNN weights
        (W_ih, b_ih, W_ph, b_ph, W_hh, b_hh, W_ho, b_ho, W_stop, b_stop).

        Args:
            batch_size: Samples per gradient step
            steps: Number of gradient steps
            lr: Learning rate for RNN weights
            rng_seed: Random seed for synthetic data generation

        Returns:
            Dict with 'final_loss' and 'history'
        """
        logger.info("=== Phase 3c: Sequence generator training ===")
        trainer = SequenceTrainer(self._sequence_generator)
        result = trainer.train(batch_size=batch_size, steps=steps, lr=lr, rng_seed=rng_seed)
        logger.info("Sequence training final loss: %.6f", result["final_loss"])
        return result

    def train_lrn(
        self, steps: int = 50, lr: float = 0.01, chat_history: Optional[list] = None
    ) -> Dict:
        """Train the LatentReasoningNetwork (Phase 4).

        Trains the MLP that maps 64-dim latent vectors to text tokens.
        Uses synthetic (latent, text) pairs if no chat history provided.

        Args:
            steps: Number of training steps
            lr: Learning rate
            chat_history: Optional list of (user_text, response_text) tuples

        Returns:
            Dict with 'final_loss' and 'history'
        """
        logger.info("=== Phase 4: LatentReasoningNetwork training ===")
        from ai.multimodal.latent_reasoning_network import LatentReasoningNetwork

        lrn = LatentReasoningNetwork(latent_dim=64, vocab_size=500)
        trainer = LatentReasoningTrainer(lrn)

        if chat_history:
            result = trainer.train_from_chat_data(self._ls, chat_history, epochs=steps, lr=lr)
        else:
            # Synthetic training: random latents → random text targets
            import numpy as np

            history = []
            for step in range(steps):
                latent = np.random.randn(64).astype(np.float32)
                # Use synthetic target text
                targets = ["hello", "thank you", "goodbye", "yes", "no"]
                target = targets[step % len(targets)]
                loss = lrn.train_step(latent, target, lr=lr)
                history.append(loss)
            result = {"final_loss": history[-1] if history else 0.0, "history": history}

        logger.info("LRN training final loss: %.6f", result["final_loss"])
        return result

    def train_encoders(self, steps: int = 50, lr: float = 0.001) -> Dict:
        """Train VisualEncoder and AudioEncoder projection matrices (Phase 0).

        Uses random image/audio data with random target latents to train
        the projection matrices in both encoders. This is a warm-up phase
        to ensure the encoders produce features that map to the latent space.

        Args:
            steps: Number of training steps
            lr: Learning rate

        Returns:
            Dict with 'visual_loss' and 'audio_loss'
        """
        logger.info("=== Phase 0: Encoder projection training ===")
        import numpy as np

        visual_losses = []
        audio_losses = []

        for step in range(steps):
            # Generate random target latent
            target_latent = np.random.randn(64).astype(np.float32)

            # Train visual encoder with random image
            dummy_image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
            import io

            from PIL import Image

            img = Image.fromarray(dummy_image)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_bytes = buf.getvalue()

            v_loss = self._visual_encoder.train_step(img_bytes, target_latent, lr=lr)
            visual_losses.append(v_loss)

            # Train audio encoder with random audio
            dummy_audio = np.random.randn(16000).astype(np.float32)
            a_loss = self._audio_encoder.train_step(dummy_audio.tobytes(), target_latent, lr=lr)
            audio_losses.append(a_loss)

        result = {
            "visual_loss": visual_losses[-1] if visual_losses else 0.0,
            "audio_loss": audio_losses[-1] if audio_losses else 0.0,
        }
        logger.info(
            "Encoder training - visual: %.6f, audio: %.6f",
            result["visual_loss"],
            result["audio_loss"],
        )
        return result

    def run_full(
        self,
        contrastive_epochs: int = 10,
        contrastive_pairs: int = 20,
        recon_epochs: int = 10,
        recon_samples: int = 10,
        texture_steps: int = 50,
        texture_lr: float = 0.001,
        wavetable_steps: int = 50,
        wavetable_lr: float = 0.001,
        seq_steps: int = 50,
        seq_lr: float = 0.001,
        prim_epochs: int = 100,
        prim_lr: float = 0.001,
        seq_prim_epochs: int = 50,
        seq_prim_lr: float = 0.001,
        lrn_steps: int = 50,
        lrn_lr: float = 0.01,
        encoder_steps: int = 50,
        encoder_lr: float = 0.001,
        lr: float = 0.01,
    ) -> Dict:
        """Run all pipeline phases end-to-end.

        Phase 0: Encoder projection training (VisualEncoder + AudioEncoder)
        Phase 1: Contrastive pre-training (SharedLatentSpace)
        Phase 2: Reconstruction fine-tuning (decoders)
        Phase 3: Texture branch (VisualDecoder)
        Phase 3b: Wavetable branch (AudioWaveformDecoder)
        Phase 3c: Sequence generator (RNN)
        Phase 3d: Primitive encoder + SequenceGenerator retrain
        Phase 4: LatentReasoningNetwork (latent → text)

        Args:
            contrastive_epochs: Phase 1 epochs
            contrastive_pairs: Phase 1 pairs per epoch
            recon_epochs: Phase 2 epochs
            recon_samples: Phase 2 samples per epoch
            texture_steps: Phase 3 gradient steps
            texture_lr: Phase 3 learning rate
            wavetable_steps: Phase 3b gradient steps
            wavetable_lr: Phase 3b learning rate
            seq_steps: Phase 3c gradient steps
            seq_lr: Phase 3c learning rate
            prim_epochs: Phase 3d PrimitiveEncoder epochs
            prim_lr: Phase 3d PrimitiveEncoder learning rate
            seq_prim_epochs: Phase 3d SequenceGenerator retrain epochs
            seq_prim_lr: Phase 3d SequenceGenerator retrain learning rate
            lrn_steps: Phase 4 LatentReasoningNetwork steps
            lrn_lr: Phase 4 LatentReasoningNetwork learning rate
            encoder_steps: Phase 0 encoder projection steps
            encoder_lr: Phase 0 encoder projection learning rate
            lr: Learning rate for Phases 1-2

        Returns:
            Dict with results from all phases
        """
        results = {}
        results["phase0_encoder"] = self.train_encoders(steps=encoder_steps, lr=encoder_lr)
        results["phase1_contrastive"] = self.run(
            contrastive_epochs=contrastive_epochs,
            contrastive_pairs=contrastive_pairs,
            recon_epochs=recon_epochs,
            recon_samples=recon_samples,
            lr=lr,
        )
        results["phase3_texture"] = self.train_texture(
            batch_size=4, steps=texture_steps, lr=texture_lr
        )
        results["phase3b_wavetable"] = self.train_wavetable(
            batch_size=4, steps=wavetable_steps, lr=wavetable_lr
        )
        results["phase3c_sequence"] = self.train_sequence(batch_size=4, steps=seq_steps, lr=seq_lr)
        results["phase3d_primitives"] = self.train_primitives(
            epochs=prim_epochs,
            lr=prim_lr,
            seq_epochs=seq_prim_epochs,
            seq_lr=seq_prim_lr,
        )
        results["phase4_lrn"] = self.train_lrn(steps=lrn_steps, lr=lrn_lr)
        return results

    def train_primitives(
        self,
        epochs: int = 100,
        lr: float = 0.001,
        seq_epochs: int = 50,
        seq_lr: float = 0.001,
        n_seq_samples: int = 500,
    ) -> Dict:
        """Train the PrimitiveEncoder autoencoder + retrain SequenceGenerator (Phase 3d).

        Phase 3d populates a PrimitiveLibrary with basic geometric shapes
        (circles, squares, triangles, lines, arcs, dots), trains the
        PrimitiveEncoder as an autoencoder on these shapes, then re-encodes
        the library and optionally retrains the SequenceGenerator on
        (CLIP-like, primitive_embedding) pairs derived from the library.

        Args:
            epochs: PrimitiveEncoder autoencoder training epochs
            lr: PrimitiveEncoder learning rate
            seq_epochs: SequenceGenerator retraining epochs (0 to skip)
            seq_lr: SequenceGenerator learning rate
            n_seq_samples: Number of synthetic clip→primitive training pairs

        Returns:
            Dict with 'encoder_result', 'library_size', and optional 'sequence_result'
        """
        from .primitives.primitive_encoder import PrimitiveEncoder

        logger.info("=== Phase 3d: Primitive encoder training ===")
        self._primitive_encoder = PrimitiveEncoder(embedding_dim=128)
        trainer = PrimitiveTrainer(self._primitive_encoder, self._sequence_generator)
        result = trainer.train(
            epochs=epochs,
            lr=lr,
            seq_epochs=seq_epochs,
            seq_lr=seq_lr,
            n_seq_samples=n_seq_samples,
        )
        self._primitive_library = trainer.library
        logger.info(
            "Primitive training done — library size: %d, " "encoder best loss: %.6f",
            result["library_size"],
            result["encoder_result"]["best_loss"],
        )
        if "sequence_result" in result:
            logger.info(
                "  SequenceGenerator retrained — final loss: %.6f",
                result["sequence_result"]["final_loss"],
            )
        return result

    def save_weights(self, path: Optional[str] = None) -> str:
        """Save trained weights to a .npz file.

        Args:
            path: Output path (default: data/multimodal/weights/p29_trained.npz)

        Returns:
            Path where weights were saved, or empty string on failure.
        """
        save_path = path or DEFAULT_WEIGHTS_PATH
        try:
            vis = self._ls._projections.get("vision", {})
            aud = self._ls._projections.get("audio", {})
            save_data = {
                "vision_W": vis.get("W", np.zeros(1)).copy(),
                "vision_b": vis.get("b", np.zeros(1)).copy(),
                "audio_W": aud.get("W", np.zeros(1)).copy(),
                "audio_b": aud.get("b", np.zeros(1)).copy(),
                "visual_decoder_W": self._visual_decoder._W.copy(),
                "visual_decoder_b": self._visual_decoder._b.copy(),
                "texture_W_hidden": self._visual_decoder._W_hidden.copy(),
                "texture_b_hidden": self._visual_decoder._b_hidden.copy(),
                "texture_W_featmap": self._visual_decoder._W_featmap.copy(),
                "texture_b_featmap": self._visual_decoder._b_featmap.copy(),
                "texture_tex_kernels": self._visual_decoder._tex_kernels.copy(),
                "audio_decoder_W": self._audio_decoder._W.copy(),
                "audio_decoder_b": self._audio_decoder._b.copy(),
                "audio_W_hidden": self._audio_decoder._W_hidden.copy(),
                "audio_b_hidden": self._audio_decoder._b_hidden.copy(),
                "audio_W_wavetable": self._audio_decoder._W_wavetable.copy(),
                "audio_b_wavetable": self._audio_decoder._b_wavetable.copy(),
                "audio_W_noise": self._audio_decoder._W_noise.copy(),
                "audio_b_noise": self._audio_decoder._b_noise.copy(),
                "seq_W_ih": self._sequence_generator._W_ih.copy(),
                "seq_b_ih": self._sequence_generator._b_ih.copy(),
                "seq_W_ph": self._sequence_generator._W_ph.copy(),
                "seq_b_ph": self._sequence_generator._b_ph.copy(),
                "seq_W_hh": self._sequence_generator._W_hh.copy(),
                "seq_b_hh": self._sequence_generator._b_hh.copy(),
                "seq_W_ho": self._sequence_generator._W_ho.copy(),
                "seq_b_ho": self._sequence_generator._b_ho.copy(),
                "seq_W_stop": self._sequence_generator._W_stop.copy(),
                "seq_b_stop": self._sequence_generator._b_stop.copy(),
            }
            # Append primitive encoder weights if available
            if self._primitive_encoder is not None:
                pe = self._primitive_encoder
                save_data["prim_enc_W_encode"] = pe._W_encode.copy()
                save_data["prim_enc_b_encode"] = pe._b_encode.copy()
                save_data["prim_enc_W_decode"] = pe._W_decode.copy()
                save_data["prim_enc_b_decode"] = pe._b_decode.copy()
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            np.savez(save_path, **save_data)
            logger.info("Trained weights saved to %s", save_path)
            return save_path
        except Exception as e:
            logger.warning("Failed to save weights: %s", e)
            return ""

    def load_weights(self, path: str) -> bool:
        """Load trained weights from a .npz file.

        Args:
            path: Path to .npz weights file

        Returns:
            True on success
        """
        try:
            data = np.load(path, allow_pickle=False)
        except Exception as e:
            logger.warning("Failed to load weights from %s: %s", path, e)
            return False

        try:
            if "vision_W" in data:
                self._ls._projections["vision"]["W"][:] = data["vision_W"]
                self._ls._projections["vision"]["b"][:] = data["vision_b"]
            if "audio_W" in data:
                self._ls._projections["audio"]["W"][:] = data["audio_W"]
                self._ls._projections["audio"]["b"][:] = data["audio_b"]
            if "visual_decoder_W" in data:
                self._visual_decoder._W[:] = data["visual_decoder_W"]
                self._visual_decoder._b[:] = data["visual_decoder_b"]
            if "texture_W_hidden" in data:
                self._visual_decoder._W_hidden[:] = data["texture_W_hidden"]
                self._visual_decoder._b_hidden[:] = data["texture_b_hidden"]
                self._visual_decoder._W_featmap[:] = data["texture_W_featmap"]
                self._visual_decoder._b_featmap[:] = data["texture_b_featmap"]
                self._visual_decoder._tex_kernels[:] = data["texture_tex_kernels"]
            if "audio_decoder_W" in data:
                self._audio_decoder._W[:] = data["audio_decoder_W"]
                self._audio_decoder._b[:] = data["audio_decoder_b"]
            if "audio_W_hidden" in data:
                self._audio_decoder._W_hidden[:] = data["audio_W_hidden"]
                self._audio_decoder._b_hidden[:] = data["audio_b_hidden"]
                self._audio_decoder._W_wavetable[:] = data["audio_W_wavetable"]
                self._audio_decoder._b_wavetable[:] = data["audio_b_wavetable"]
                self._audio_decoder._W_noise[:] = data["audio_W_noise"]
                self._audio_decoder._b_noise[:] = data["audio_b_noise"]
            if "seq_W_ih" in data:
                self._sequence_generator._W_ih[:] = data["seq_W_ih"]
                self._sequence_generator._b_ih[:] = data["seq_b_ih"]
                self._sequence_generator._W_ph[:] = data["seq_W_ph"]
                self._sequence_generator._b_ph[:] = data["seq_b_ph"]
                self._sequence_generator._W_hh[:] = data["seq_W_hh"]
                self._sequence_generator._b_hh[:] = data["seq_b_hh"]
                self._sequence_generator._W_ho[:] = data["seq_W_ho"]
                self._sequence_generator._b_ho[:] = data["seq_b_ho"]
                self._sequence_generator._W_stop[:] = data["seq_W_stop"]
                self._sequence_generator._b_stop[:] = data["seq_b_stop"]
                self._sequence_generator._trained = True
            if "prim_enc_W_encode" in data:
                from .primitives.primitive_encoder import PrimitiveEncoder

                self._primitive_encoder = PrimitiveEncoder(
                    embedding_dim=data["prim_enc_W_encode"].shape[0]
                )
                self._primitive_encoder._W_encode[:] = data["prim_enc_W_encode"]
                self._primitive_encoder._b_encode[:] = data["prim_enc_b_encode"]
                self._primitive_encoder._W_decode[:] = data["prim_enc_W_decode"]
                self._primitive_encoder._b_decode[:] = data["prim_enc_b_decode"]
                self._primitive_encoder._trained = True
                self._primitive_encoder._best_loss = 0.0
            logger.info("Weights loaded from %s", path)
            return True
        except Exception as e:
            logger.warning("Failed to apply weights: %s", e)
            return False

    def evaluate(
        self, n_samples: int = 5, real_features: Optional[Dict[str, List[np.ndarray]]] = None
    ) -> Dict:
        """Evaluate current model quality on synthetic or real data.

        Args:
            n_samples: Number of synthetic samples (ignored if real_features given)
            real_features: Optional dict of real encoded features per modality

        Returns dict of quality metrics per modality.
        """
        result: Dict = {}

        if real_features:
            for mod, features in real_features.items():
                if not features:
                    continue
                losses = []
                for f in features[:n_samples]:
                    loss = self._reconstruction.train_step(mod, f, lr=0.0)
                    losses.append(loss)
                result[mod] = {
                    "avg_reconstruction_loss": float(np.mean(losses)),
                }
        else:
            rng = np.random.RandomState(999)
            for mod in ["vision", "audio"]:
                feat_dim = 256 if mod == "vision" else 128
                losses = []
                for _ in range(n_samples):
                    f = rng.randn(feat_dim).astype(np.float32)
                    loss = self._reconstruction.train_step(mod, f, lr=0.0)
                    losses.append(loss)
                result[mod] = {
                    "avg_reconstruction_loss": float(np.mean(losses)),
                }
        return result
