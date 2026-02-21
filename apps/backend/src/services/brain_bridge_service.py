"""
Angela AI v6.1.0 - Brain Bridge Service
Bridges the theoretical Brain/Body metrics to the user-facing status and documentation.
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from core.autonomous.digital_life_integrator import DigitalLifeIntegrator
from shared.utils.hardware_detector import SystemHardwareProbe

logger = logging.getLogger(__name__)


class BrainBridgeService:
    """
    Bridges the gap between internal AGI formulas and observable metrics.
    """

    def __init__(
        self, digital_life: DigitalLifeIntegrator, metrics_path: str = "metrics.md"
    ):
        self.digital_life = digital_life
        self.metrics_path = Path(metrics_path)
        self.hardware_detector = SystemHardwareProbe()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._update_interval = 5.0  # Sync every 5 seconds (Increased for real-time dialogue awareness)

    async def start(self):
        """Start the bridge sync service"""
        self._running = True
        self._task = asyncio.create_task(self._sync_loop())
        logger.info("Brain Bridge Service started.")

    async def stop(self):
        """Stop the bridge sync service"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Brain Bridge Service stopped.")

    async def _sync_loop(self):
        """Periodic sync loop"""
        while self._running:
            try:
                await self.sync_metrics()
            except Exception as e:
                logger.error(f"Error in Brain Bridge sync: {e}")
            await asyncio.sleep(self._update_interval)

    async def sync_metrics(self):
        """Sync internal brain metrics to metrics.md and system state"""
        # Prepare full status record
        full_status = self.get_current_status()
        
        # We also need to add 'life_intensity' at the top level if LLM service expects it there
        # based on angela_llm_service.py:828 (intensity = data.get("life_intensity", 0.0))
        brain_metrics = full_status.get("brain") or {}
        brain_current = brain_metrics.get("current_metrics", {}) if brain_metrics else {}
        full_status["life_intensity"] = brain_current.get("life_intensity", 0.0)

        # Update secondary JSON status for the API to consume
        status_file = Path("apps/backend/data/brain_status.json")
        status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(full_status, f, indent=4)

        logger.info(
            f"Brain Metrics Synced: LifeIntensity={full_status['life_intensity']:.4f}"
        )

    def get_current_status(self) -> Dict[str, Any]:
        """Return the bridged metrics for API consumption"""
        brain_summary = self.digital_life.get_formula_metrics()
        bio_state = self.digital_life.biological_integrator.get_biological_state()
        hw_profile = self.hardware_detector.detect()

        return {
            "brain": brain_summary,
            "biological": bio_state,
            "hardware": {
                "performance_tier": hw_profile.performance_tier,
                "ai_score": hw_profile.ai_capability_score,
                "accelerator": hw_profile.accelerator_type.value
            },
            "timestamp": datetime.now().isoformat(),
        }
