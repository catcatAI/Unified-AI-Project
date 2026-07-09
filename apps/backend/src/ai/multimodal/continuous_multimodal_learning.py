# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [C] [L3]
# =============================================================================
"""
ContinuousMultimodalLearning (CML) — autonomous micro-training for multimodal pipeline.

Analogous to ContinuousLearningPipeline for the ED3N chat pipeline.

Buffers recent encode/decode quality results and automatically triggers
micro-training cycles to improve encoding and decoding quality over time.

Key features:
  - Buffer: stores last N `(modality, features, reconstructed, quality)` tuples
  - Auto-train: when buffer >= threshold, runs short full-pipeline training
  - Quality delta tracking: measures improvement after each micro-training
  - State persistence: save/load for system restart resilience
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.utils import safe_error

logger = logging.getLogger(__name__)


@dataclass
class CMLExample:
    """A single multimodal encode/decode example for training."""
    modality: str
    feature_vector: List[float]
    latent: List[float]
    reconstructed: Any = None
    quality_score: float = 0.0
    timestamp: float = 0.0


class ContinuousMultimodalLearning:
    """Autonomous micro-training for multimodal pipeline quality improvement.

    Attributes:
        buffer_max: Max examples in training buffer (default 64)
        auto_train_threshold: Buffer size that triggers auto-training (default 32)
        min_interval_sec: Minimum seconds between auto-training runs (default 60)
        quality_window: Window size for trend calculation (default 10)
        save_dir: Optional directory for state persistence
    """

    def __init__(
        self,
        buffer_max: int = 64,
        auto_train_threshold: int = 32,
        min_interval_sec: float = 60.0,
        quality_window: int = 10,
        save_dir: Optional[str] = None,
        pipeline: Optional[Any] = None,
    ):
        self.buffer_max = buffer_max
        self.auto_train_threshold = auto_train_threshold
        self.min_interval_sec = min_interval_sec
        self.quality_window = quality_window
        self.save_dir = save_dir

        self._buffer: List[CMLExample] = []
        self._last_train_time: float = 0.0
        self._total_encodes: int = 0
        self._training_runs: int = 0
        self._quality_history: List[Dict[str, Any]] = []
        self._pipeline = pipeline

    def _get_pipeline(self):
        """Get or create the FullTrainingPipeline (lazy import if not provided)."""
        if self._pipeline is None:
            try:
                from ai.multimodal.training_pipeline import FullTrainingPipeline
                self._pipeline = FullTrainingPipeline()
            except Exception as e:
                logger.warning("Cannot create training pipeline: %s", e)
        return self._pipeline

    # --- Recording ---

    def record_encode(self, modality: str, feature_vector: list,
                      latent: list, quality_score: float = 0.0) -> None:
        """Record an encode operation for potential future training.

        Args:
            modality: "vision" or "audio"
            feature_vector: The encoded feature vector
            latent: The projected latent vector
            quality_score: Quality score (SSIM for vision, SNR for audio)
        """
        example = CMLExample(
            modality=modality,
            feature_vector=feature_vector,
            latent=latent,
            quality_score=quality_score,
            timestamp=time.time(),
        )
        self._buffer.append(example)
        if len(self._buffer) > self.buffer_max:
            self._buffer.pop(0)
        self._total_encodes += 1

    def record_quality(self, metrics: Dict[str, Any]) -> None:
        """Record a quality metric snapshot for trend analysis."""
        self._quality_history.append({
            "timestamp": time.time(),
            **metrics,
        })
        if len(self._quality_history) > self.buffer_max * 2:
            self._quality_history = self._quality_history[-self.buffer_max:]

    # --- Auto-training ---

    def should_train(self) -> bool:
        if time.time() - self._last_train_time < self.min_interval_sec:
            return False
        effective_threshold = self._quality_adjusted_threshold()
        return len(self._buffer) >= effective_threshold

    def _quality_adjusted_threshold(self) -> int:
        """Adjust auto_train_threshold based on quality trend.

        - Degrading: train more aggressively (lower threshold)
        - Improving: train less often (higher threshold, let consolidation happen)
        - Stable/unknown: use default
        """
        trend = self.quality_trend()
        assessment = trend.get("delta_assessment", "stable")
        if assessment == "degrading":
            return max(self.auto_train_threshold // 2, 4)
        if assessment == "improving":
            return self.auto_train_threshold * 2
        return self.auto_train_threshold

    def micro_train(self, epochs: int = 3, lr: float = 0.005) -> Dict[str, Any]:
        """Run a micro-training cycle using buffered examples.

        Args:
            epochs: Number of training epochs (default 3, short cycle)
            lr: Learning rate (default 0.005, lower for stability)

        Returns:
            dict with status, epochs, loss_before, loss_after, delta, time_ms
        """
        t0 = time.time()
        result: Dict[str, Any] = {
            "status": "skipped",
            "reason": "buffer_not_ready",
        }

        pipeline = self._get_pipeline()
        if pipeline is None:
            result["reason"] = "pipeline_unavailable"
            return result

        try:
            loss_before = 0.0
            # Evaluate before training (if pipeline has evaluate method)
            if hasattr(pipeline, "evaluate"):
                eval_before = pipeline.evaluate(n_samples=5)
                loss_before = eval_before.get("reconstruction", {}).get("final_loss", 0.0)

            # Run contrastive + recon training (short cycle)
            if hasattr(pipeline, "run"):
                pipeline.run(
                    contrastive_epochs=epochs,
                    recon_epochs=epochs,
                    lr=lr,
                )

            loss_after = 0.0
            if hasattr(pipeline, "evaluate"):
                eval_after = pipeline.evaluate(n_samples=5)
                loss_after = eval_after.get("reconstruction", {}).get("final_loss", 0.0)

            delta = loss_before - loss_after if loss_before > 0 else 0.0
            self._training_runs += 1
            self._last_train_time = time.time()

            # Record quality delta
            self.record_quality({
                "loss_before": loss_before,
                "loss_after": loss_after,
                "delta": delta,
                "epochs": epochs,
                "buffer_size": len(self._buffer),
            })

            # Trim buffer after training (keep last 25% for next cycle)
            keep_count = max(len(self._buffer) // 4, 1)
            self._buffer = self._buffer[-keep_count:]

            result = {
                "status": "completed",
                "epochs": epochs,
                "loss_before": round(loss_before, 6),
                "loss_after": round(loss_after, 6),
                "delta": round(delta, 6),
                "improved": delta > 0,
                "time_ms": round((time.time() - t0) * 1000, 1),
                "training_runs_total": self._training_runs,
            }

        except Exception as e:
            logger.error("Micro-train failed: %s", e, exc_info=True)
            result = {"status": "error", "error": safe_error(e)}

        # Auto-save if configured
        if self.save_dir and result.get("status") == "completed":
            self.save()

        return result

    def quality_trend(self) -> Dict[str, Any]:
        """Analyze quality trend from recent history.

        Returns:
            dict with delta_assessment ("improving"/"stable"/"degrading"),
                  avg_delta, total_training_runs
        """
        if len(self._quality_history) < 2:
            return {"delta_assessment": "insufficient_data", "avg_delta": 0.0,
                    "total_training_runs": self._training_runs}

        recent = self._quality_history[-self.quality_window:]
        deltas = [r.get("delta", 0.0) for r in recent if r.get("delta") is not None]
        if not deltas:
            return {"delta_assessment": "no_data", "avg_delta": 0.0,
                    "total_training_runs": self._training_runs}

        avg_delta = sum(deltas) / len(deltas)
        if avg_delta > 0.01:
            assessment = "improving"
        elif avg_delta < -0.01:
            assessment = "degrading"
        else:
            assessment = "stable"

        return {
            "delta_assessment": assessment,
            "avg_delta": round(avg_delta, 6),
            "samples": len(deltas),
            "total_training_runs": self._training_runs,
            "buffer_size": len(self._buffer),
            "total_encodes": self._total_encodes,
        }

    # --- State persistence ---

    def save(self, save_dir: Optional[str] = None) -> Optional[str]:
        """Save CML state to JSON file.

        Args:
            save_dir: Directory to save state (default: self.save_dir)

        Returns:
            Path to saved file, or None if save failed
        """
        save_dir = save_dir or self.save_dir
        if not save_dir:
            return None

        try:
            path = Path(save_dir)
            path.mkdir(parents=True, exist_ok=True)
            state = {
                "total_encodes": self._total_encodes,
                "training_runs": self._training_runs,
                "last_train_time": self._last_train_time,
                "buffer": [
                    {
                        "modality": ex.modality,
                        "feature_vector": ex.feature_vector[:8],  # Store summary
                        "latent": ex.latent[:8],
                        "quality_score": ex.quality_score,
                        "timestamp": ex.timestamp,
                    }
                    for ex in self._buffer[-20:]  # Only last 20
                ],
                "quality_history": self._quality_history[-50:],  # Only last 50
                "saved_at": datetime.now().isoformat(),
            }
            save_path = path / "cml_state.json"
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logger.info("CML state saved to %s", save_path)
            return str(save_path)
        except Exception as e:
            logger.warning("CML save failed: %s", e)
            return None

    def load(self, save_dir: Optional[str] = None) -> bool:
        """Load CML state from JSON file.

        Args:
            save_dir: Directory to load state from (default: self.save_dir)

        Returns:
            True if loaded successfully
        """
        save_dir = save_dir or self.save_dir
        if not save_dir:
            return False

        try:
            save_path = Path(save_dir) / "cml_state.json"
            if not save_path.exists():
                return False

            with open(save_path, "r", encoding="utf-8") as f:
                state = json.load(f)

            self._total_encodes = state.get("total_encodes", 0)
            self._training_runs = state.get("training_runs", 0)
            self._last_train_time = state.get("last_train_time", 0.0)
            self._quality_history = state.get("quality_history", [])

            logger.info("CML state loaded from %s (%d encodes, %d training runs)",
                        save_path, self._total_encodes, self._training_runs)
            return True
        except Exception as e:
            logger.warning("CML load failed: %s", e)
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Return current CML statistics."""
        return {
            "total_encodes": self._total_encodes,
            "training_runs": self._training_runs,
            "buffer_size": len(self._buffer),
            "buffer_capacity": self.buffer_max,
            "auto_train_threshold": self.auto_train_threshold,
            "quality_history_size": len(self._quality_history),
        }
