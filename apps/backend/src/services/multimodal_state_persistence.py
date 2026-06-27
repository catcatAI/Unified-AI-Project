"""
MultimodalStatePersistence — state persistence for multimodal pipeline.

Analogous to state persistence in chat pipeline. Provides:
  - save_checkpoint: save full multimodal state (weights + CML + memory)
  - load_checkpoint: restore from a checkpoint
  - list_checkpoints: enumerate available checkpoints
  - prune_checkpoints: keep only N most recent checkpoints

P37: Production hardening — state persistence layer.

ANGELA-MATRIX: [L5] [βγδ] [B] [L4]
"""

import json
import logging
import os
import shutil
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _json_default(obj):
    """JSON serializer for numpy/mock types in checkpoint serialization."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, 'tolist'):
        try:
            result = obj.tolist()
            if isinstance(result, (list, tuple)):
                return result
        except Exception:
            pass
    return str(obj)


class MultimodalStatePersistence:
    """Persistent checkpoint management for multimodal pipeline state.

    Manages save/load/list operations for checkpoints containing:
      - Decoder weights (.npz via service.save_weights)
      - CML buffer state (if service has _get_cml)
      - Memory store index (if service has _get_memory_store)
      - Registry items summary
      - Metadata (timestamp, label, component versions)
    """

    DEFAULT_CHECKPOINT_DIR = os.path.join("data", "multimodal", "checkpoints")
    MAX_CHECKPOINTS = 10

    def __init__(self, service, checkpoint_dir: Optional[str] = None):
        """Initialize with a MultimodalService instance.

        Args:
            service: Object with multimodal operations
            checkpoint_dir: Directory for checkpoint storage
        """
        self._service = service
        self._checkpoint_dir = checkpoint_dir or self.DEFAULT_CHECKPOINT_DIR
        os.makedirs(self._checkpoint_dir, exist_ok=True)

    # --- Save ---

    async def save_checkpoint(self, label: Optional[str] = None) -> Dict[str, Any]:
        label = label or f"cp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        cp_dir = os.path.join(self._checkpoint_dir, label)
        os.makedirs(cp_dir, exist_ok=True)

        components_saved: List[str] = []
        await self._save_weight_component(cp_dir, components_saved)
        await self._save_cml_component(cp_dir, components_saved)
        await self._save_memory_component(cp_dir, components_saved)
        await self._save_registry_component(cp_dir, components_saved)
        metadata = self._write_checkpoint_metadata(cp_dir, label, components_saved)
        await self.prune_checkpoints()

        logger.info("Checkpoint '%s' saved with %d components: %s",
                     label, len(components_saved), components_saved)
        return {
            "label": label,
            "path": cp_dir,
            "timestamp": metadata["timestamp"],
            "components_saved": components_saved,
            "status": "saved",
        }

    async def _save_weight_component(self, cp_dir, components_saved):
        try:
            if hasattr(self._service, "save_weights"):
                w_result = await self._service.save_weights(os.path.join(cp_dir, "weights.npz"))
                if w_result.get("status") == "saved":
                    components_saved.append("weights")
                else:
                    logger.warning("Weight save returned: %s", w_result)
        except Exception as e:
            logger.warning("Failed to save weights: %s", e)

    async def _save_cml_component(self, cp_dir, components_saved):
        try:
            if not hasattr(self._service, "_get_cml"):
                return
            cml = self._service._get_cml()
            if not hasattr(cml, "state_dict"):
                return
            cml_state = cml.state_dict()
            if not isinstance(cml_state, dict):
                return
            cml_serializable = json.loads(json.dumps(cml_state, default=_json_default))
            cml_path = os.path.join(cp_dir, "cml_state.json")
            with open(cml_path, "w", encoding="utf-8") as f:
                json.dump(cml_serializable, f, indent=2)
            components_saved.append("cml")
        except Exception as e:
            logger.warning("Failed to save CML state: %s", e)

    async def _save_memory_component(self, cp_dir, components_saved):
        try:
            if not hasattr(self._service, "_get_memory_store"):
                return
            mem = self._service._get_memory_store()
            if not hasattr(mem, "save_index"):
                return
            mem_path = os.path.join(cp_dir, "memory_index.json")
            if await mem.save_index(mem_path):
                components_saved.append("memory_index")
        except Exception as e:
            logger.warning("Failed to save memory index: %s", e)

    async def _save_registry_component(self, cp_dir, components_saved):
        try:
            if not hasattr(self._service, "list_items"):
                return
            items = await self._service.list_items()
            registry_path = os.path.join(cp_dir, "registry_summary.json")
            with open(registry_path, "w", encoding="utf-8") as f:
                json.dump({"count": items.get("count", 0), "items": {k: v for k, v in items.get("items", {}).items()}}, f, indent=2)
            components_saved.append("registry_summary")
        except Exception as e:
            logger.warning("Failed to save registry summary: %s", e)

    def _write_checkpoint_metadata(self, cp_dir, label, components_saved):
        metadata = {
            "label": label,
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "components_saved": components_saved,
            "checkpoint_dir": cp_dir,
        }
        meta_path = os.path.join(cp_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        return metadata

    # --- Load ---

    async def load_checkpoint(self, label: str) -> Dict[str, Any]:
        """Load a checkpoint by label.

        Args:
            label: Checkpoint label to restore from

        Returns:
            dict with {label, path, components_loaded, status}
        """
        cp_dir = os.path.join(self._checkpoint_dir, label)
        if not os.path.isdir(cp_dir):
            return {"status": "error", "error": f"Checkpoint not found: {label}"}

        components_loaded: List[str] = []

        # 1. Load metadata
        meta_path = os.path.join(cp_dir, "metadata.json")
        metadata = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except Exception:
                pass

        # 2. Load weights
        weights_path = os.path.join(cp_dir, "weights.npz")
        if os.path.exists(weights_path):
            try:
                if hasattr(self._service, "load_weights"):
                    l_result = await self._service.load_weights(str(weights_path))
                    if l_result.get("status") == "loaded":
                        components_loaded.append("weights")
            except Exception as e:
                logger.warning("Failed to load weights: %s", e)

        # 3. Load CML state
        cml_path = os.path.join(cp_dir, "cml_state.json")
        if os.path.exists(cml_path):
            try:
                if hasattr(self._service, "_get_cml"):
                    cml = self._service._get_cml()
                    if hasattr(cml, "load_state_dict"):
                        with open(cml_path, "r", encoding="utf-8") as f:
                            cml_state = json.load(f)
                        cml.load_state_dict(cml_state)
                        components_loaded.append("cml")
            except Exception as e:
                logger.warning("Failed to load CML state: %s", e)

        # 4. Load memory index
        mem_path = os.path.join(cp_dir, "memory_index.json")
        if os.path.exists(mem_path):
            try:
                if hasattr(self._service, "_get_memory_store"):
                    mem = self._service._get_memory_store()
                    if hasattr(mem, "load_index"):
                        loaded = await mem.load_index(mem_path)
                        if loaded:
                            components_loaded.append("memory_index")
            except Exception as e:
                logger.warning("Failed to load memory index: %s", e)

        status = "loaded" if components_loaded else "empty"
        logger.info("Checkpoint '%s' loaded with %d components: %s",
                     label, len(components_loaded), components_loaded)
        return {
            "label": label,
            "path": cp_dir,
            "components_loaded": components_loaded,
            "metadata": metadata,
            "status": status,
        }

    # --- List ---

    async def list_checkpoints(self) -> Dict[str, Any]:
        """List all available checkpoints.

        Returns:
            dict with {checkpoints: [{label, timestamp, components, age_hours}], count}
        """
        if not os.path.isdir(self._checkpoint_dir):
            return {"checkpoints": [], "count": 0}

        checkpoints = []
        now = time.time()
        for name in sorted(os.listdir(self._checkpoint_dir)):
            cp_dir = os.path.join(self._checkpoint_dir, name)
            if not os.path.isdir(cp_dir):
                continue
            meta_path = os.path.join(cp_dir, "metadata.json")
            meta = {}
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass
            ts = meta.get("timestamp", os.path.getmtime(cp_dir))
            age_hours = round((now - ts) / 3600, 1)
            checkpoints.append({
                "label": name,
                "timestamp": ts,
                "age_hours": age_hours,
                "components": meta.get("components_saved", []),
            })

        # Sort newest first
        checkpoints.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "checkpoints": checkpoints,
            "count": len(checkpoints),
            "directory": self._checkpoint_dir,
        }

    # --- Prune ---

    async def prune_checkpoints(self, keep: Optional[int] = None) -> int:
        """Remove old checkpoints, keeping only the N most recent.

        Args:
            keep: Number of most recent checkpoints to retain

        Returns:
            Number of checkpoints removed
        """
        keep = keep or self.MAX_CHECKPOINTS
        cp_list = await self.list_checkpoints()
        all_cps = cp_list.get("checkpoints", [])
        if len(all_cps) <= keep:
            return 0

        removed = 0
        for cp in all_cps[keep:]:
            cp_dir = os.path.join(self._checkpoint_dir, cp["label"])
            if os.path.isdir(cp_dir):
                try:
                    shutil.rmtree(cp_dir)
                    removed += 1
                    logger.info("Pruned old checkpoint: %s", cp["label"])
                except Exception as e:
                    logger.warning("Failed to prune checkpoint %s: %s",
                                   cp["label"], e)

        return removed

    # --- Get checkpoint path ---

    def get_checkpoint_path(self, label: str) -> Optional[str]:
        """Get the filesystem path for a checkpoint label.

        Returns None if the checkpoint doesn't exist.
        """
        cp_dir = os.path.join(self._checkpoint_dir, label)
        return cp_dir if os.path.isdir(cp_dir) else None
