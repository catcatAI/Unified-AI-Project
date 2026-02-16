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
from system.hardware_probe import HardwareProbe

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
        self.hardware_probe = HardwareProbe()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._update_interval = 60.0  # Sync every minute

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
        brain_summary = self.digital_life.get_formula_metrics()
        if not brain_summary:
            return

        # Prepare metrics record
        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "life_intensity": brain_summary.get("current_metrics", {}).get(
                "life_intensity", 0.0
            ),
            "active_cognition": brain_summary.get("current_metrics", {}).get(
                "a_c", 0.0
            ),
            "cognitive_gap": brain_summary.get("current_metrics", {}).get(
                "cognitive_gap", 0.0
            ),
            "coexistence_active": brain_summary.get("current_metrics", {}).get(
                "coexistence_active", False
            ),
            "hormonal_balance": self.digital_life.biological_integrator.get_biological_state().get(
                "hormonal_effects", {}
            ),
        }

        # In a real implementation, we would parse metrics.md and update the table.
        # For now, we update a secondary JSON status for the API to consume
        # and we log to indicate the "bridge" is active.
        status_file = Path("apps/backend/data/brain_status.json")
        status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=4)

        logger.info(
            f"Brain Metrics Synced: L_s={metrics_data['life_intensity']:.4f}, A_c={metrics_data['active_cognition']:.4f}"
        )

    def get_current_status(self) -> Dict[str, Any]:
        """Return the bridged metrics for API consumption"""
        brain_summary = self.digital_life.get_formula_metrics()
        bio_state = self.digital_life.biological_integrator.get_biological_state()

        return {
            "brain": brain_summary,
            "biological": bio_state,
            "timestamp": datetime.now().isoformat(),
        }
