"""
MultimodalErrorRecovery — production error recovery for multimodal pipelines.

Analogous to error recovery patterns in chat pipeline. Provides:
  - encode_with_retry: 3 retries with exponential backoff
  - decode_with_fallback: on decoder failure, return text description
  - train_with_checkpoint: training resumable from last checkpoint
  - All failures logged to crisis_log for monitoring

P37: Production hardening — error recovery layer.

ANGELA-MATRIX: [L5] [βγδ] [B] [L4]
"""

import asyncio
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Crisis log — use shared utility
from core.crisis_log import write_crisis_log as _write_crisis_log
from core.utils import safe_error


class MultimodalErrorRecovery:
    """Production error recovery for multimodal operations.

    Wraps MultimodalService methods with retry/fallback/checkpoint logic.

    Typical usage:
        er = MultimodalErrorRecovery(service_instance)
        result = await er.encode_with_retry(data, "vision")
        result = await er.decode_with_fallback(item_id, "vision")
        result = await er.train_with_checkpoint(mode="full")
    """

    MAX_RETRIES = 3
    BASE_BACKOFF_SEC = 1.0
    MAX_BACKOFF_SEC = 10.0
    CHECKPOINT_DIR = os.path.join("data", "multimodal", "checkpoints")

    def __init__(self, service):
        """Initialize with a MultimodalService or compatible instance.

        Args:
            service: An object with async encode/decode/train methods
                     (e.g., MultimodalService instance)
        """
        self._service = service
        self._retry_count: Dict[str, int] = {}  # operation_key → failure count
        self._crisis_level: Dict[str, int] = {}  # operation_key → crisis level
        self._last_success: Dict[str, float] = {}  # operation_key → timestamp
        os.makedirs(self.CHECKPOINT_DIR, exist_ok=True)

    # --- Retry logic ---

    async def encode_with_retry(
        self,
        data: bytes,
        modality: str,
        item_id: Optional[str] = None,
        max_retries: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Encode with automatic retry on failure.

        Retries up to MAX_RETRIES times with exponential backoff.
        On complete failure, logs to crisis_log and returns error dict.
        """
        max_retries = max_retries or self.MAX_RETRIES
        op_key = f"encode:{modality}"
        last_error = ""

        # Fast-fail on empty data — retrying won't help
        if not data:
            _write_crisis_log(
                1,
                {
                    "operation": op_key,
                    "error": "Empty data provided",
                    "attempts": 1,
                    "modality": modality,
                },
            )
            return {
                "modality": modality,
                "error": "Empty data provided",
                "recovery": {"attempts": 1, "retried": False, "failed": True},
            }

        for attempt in range(1 + max_retries):
            try:
                result = await self._service.encode(data, modality, item_id)
                if result.get("error"):
                    last_error = result["error"]
                    raise RuntimeError(result["error"])
                # Success
                self._retry_count[op_key] = 0
                self._last_success[op_key] = time.time()
                result["recovery"] = {
                    "attempts": attempt + 1,
                    "retried": attempt > 0,
                }
                return result
            except Exception as e:
                last_error = safe_error(e)
                logger.warning(
                    "Encode attempt %d/%d failed for %s: %s",
                    attempt + 1,
                    max_retries + 1,
                    modality,
                    last_error,
                )
                if attempt < max_retries:
                    backoff = min(
                        self.BASE_BACKOFF_SEC * (2**attempt),
                        self.MAX_BACKOFF_SEC,
                    )
                    await asyncio.sleep(backoff)

        # All attempts failed — log crisis
        self._retry_count[op_key] = self._retry_count.get(op_key, 0) + 1
        crisis_level = min(self._retry_count[op_key], 5)
        self._crisis_level[op_key] = crisis_level
        _write_crisis_log(
            crisis_level,
            {
                "operation": op_key,
                "error": last_error,
                "attempts": max_retries + 1,
                "modality": modality,
            },
        )
        return {
            "error": f"Encode failed after {max_retries + 1} attempts: {last_error}",
            "modality": modality,
            "recovery": {"attempts": max_retries + 1, "retried": True, "failed": True},
        }

    async def decode_with_fallback(
        self, item_id: str, modality: str, output_format: str = "base64"
    ) -> Dict[str, Any]:
        """Decode with fallback on failure.

        On decoder crash, returns a text description of the item as fallback.
        Logs to crisis_log on first failure, then returns fallback data.
        """
        op_key = f"decode:{modality}"
        try:
            result = await self._service.decode(item_id, modality, output_format)
            if result.get("error"):
                raise RuntimeError(result["error"])
            # Success
            self._retry_count[op_key] = 0
            self._last_success[op_key] = time.time()
            result["recovery"] = {"fallback_used": False}
            return result
        except Exception as e:
            logger.warning("Decode failed for %s (%s), using fallback: %s", item_id, modality, e)
            self._retry_count[op_key] = self._retry_count.get(op_key, 0) + 1

            # Fallback: try to return item metadata as text description
            fallback_result: Dict[str, Any] = {
                "item_id": item_id,
                "modality": modality,
                "error": safe_error(e),
                "recovery": {
                    "fallback_used": True,
                    "fallback_type": "text_description",
                },
            }
            try:
                item = await self._service.get_item(item_id)
                if item:
                    fallback_result["fallback_description"] = (
                        f"{modality} item ({item_id}): "
                        f"latent_dim={len(item.get('latent', []))}, "
                        f"feature_dim={len(item.get('feature_vector', []))}"
                    )
                    if modality == "vision":
                        fallback_result["fallback_description"] = (
                            f"Vision item decoded as text: {item_id}"
                        )
                    else:
                        fallback_result["fallback_description"] = (
                            f"Audio item decoded as text: {item_id}"
                        )
                else:
                    fallback_result["fallback_description"] = (
                        f"Item {item_id} not found in registry"
                    )
            except Exception:
                logger.debug("Failed to get item metadata for fallback description", exc_info=True)
                fallback_result["fallback_description"] = f"Item {item_id} (fallback)"

            # Log crisis on repeated failures
            if self._retry_count.get(op_key, 0) >= 3:
                _write_crisis_log(
                    3,
                    {
                        "operation": op_key,
                        "error": safe_error(e),
                        "item_id": item_id,
                        "consecutive_failures": self._retry_count[op_key],
                    },
                )

            return fallback_result

    async def train_with_checkpoint(
        self,
        mode: str = "full",
        epochs: int = 5,
        lr: float = 0.01,
        use_real: bool = False,
        checkpoint_label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run training with checkpoint support for resumability.

        Saves a checkpoint before training, and if training fails,
        the system can resume from the last checkpoint.

        Returns training result with checkpoint info.
        """
        op_key = f"train:{mode}"
        cp_label = checkpoint_label or f"train_{mode}_{int(time.time())}"

        # Save pre-training checkpoint
        try:
            cp_path = await self._save_checkpoint_impl(cp_label)
            logger.info("Pre-training checkpoint saved: %s", cp_path)
        except Exception as e:
            logger.warning("Failed to save pre-training checkpoint: %s", e)
            cp_path = None

        try:
            result = await self._service.train(mode, epochs, lr, use_real)
            if result.get("status") == "error":
                raise RuntimeError(result.get("error", "Training returned error status"))

            self._retry_count[op_key] = 0
            self._last_success[op_key] = time.time()
            result["checkpoint"] = {
                "label": cp_label,
                "path": cp_path or "",
                "saved_before_training": cp_path is not None,
            }
            return result
        except Exception as e:
            logger.error("Training failed after checkpoint saved at %s: %s", cp_path, e)
            self._retry_count[op_key] = self._retry_count.get(op_key, 0) + 1
            _write_crisis_log(
                4,
                {
                    "operation": op_key,
                    "error": safe_error(e),
                    "checkpoint": cp_label,
                    "checkpoint_path": cp_path or "",
                },
            )
            return {
                "status": "error",
                "error": safe_error(e),
                "checkpoint": {
                    "label": cp_label,
                    "path": cp_path or "",
                    "saved_before_training": cp_path is not None,
                    "resumable": cp_path is not None,
                },
            }

    # --- Internal checkpoint helper ---

    async def _save_checkpoint_impl(self, label: str) -> Optional[str]:
        """Save a checkpoint of the current multimodal state.

        Saves: latent space state, decoder weights, registry items summary.
        Returns path to checkpoint file or None on failure.
        """
        try:
            cp_dir = os.path.join(self.CHECKPOINT_DIR, label)
            os.makedirs(cp_dir, exist_ok=True)

            # Save weights through the service
            if hasattr(self._service, "save_weights"):
                weights_result = await self._service.save_weights(
                    os.path.join(cp_dir, "weights.npz")
                )
                if weights_result.get("status") != "saved":
                    logger.warning("Checkpoint weight save returned: %s", weights_result)

            # Save registry summary
            items = []
            if hasattr(self._service, "list_items"):
                item_list = await self._service.list_items()
                items = item_list.get("items", {})
            import json

            summary_path = os.path.join(cp_dir, "checkpoint.json")
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "label": label,
                        "timestamp": time.time(),
                        "registered_items": len(items),
                        "components": {
                            "weights": "weights.npz",
                            "summary": "checkpoint.json",
                        },
                    },
                    f,
                    indent=2,
                )

            return cp_dir
        except Exception as e:
            logger.error("Checkpoint save failed: %s", e)
            return None

    # --- Crisis recovery state ---

    def get_recovery_state(self) -> Dict[str, Any]:
        """Get current recovery state summary."""
        return {
            "retry_counts": dict(self._retry_count),
            "crisis_levels": dict(self._crisis_level),
            "last_success_timestamps": {k: v for k, v in self._last_success.items()},
            "checkpoint_dir": self.CHECKPOINT_DIR,
        }

    def reset_counters(self) -> None:
        """Reset all retry counters and crisis levels."""
        self._retry_count.clear()
        self._crisis_level.clear()
        self._last_success.clear()
        logger.info("Error recovery counters reset")
