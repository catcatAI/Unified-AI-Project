import asyncio
import logging
import time
from datetime import datetime
from typing import Optional
from .biological_integrator import BiologicalIntegrator
from ...integrations.os_bridge_adapter import OSBridgeAdapter

logger = logging.getLogger(__name__)

class MetabolicHeartbeat:
    """
    The Pulse of Angela. 
    A background service that drives biological aging, data metabolism, 
    and autonomous environmental observation.
    """
    def __init__(self, update_interval: float = 30.0):
        self.update_interval = update_interval
        self.bio_integrator = BiologicalIntegrator()
        self.os_bridge = OSBridgeAdapter()
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.start_time = datetime.now()

    async def start(self):
        if self._running:
            return
        self._running = True
        await self.bio_integrator.initialize()
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"💓 Angela's Heartbeat started. Birth: {self.start_time}")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
        await self.bio_integrator.shutdown()
        logger.info("🛑 Heartbeat stopped.")

    async def _run_loop(self):
        while self._running:
            try:
                # 0. ANS Modulation (Autonomic Nervous System)
                state = self.bio_integrator.get_biological_state()
                stress = state.get("stress_level", 0.5)
                arousal = state.get("arousal", 50.0)
                
                # Sympathetic Response: High stress/arousal -> Faster pulse (min 5s)
                # Parasympathetic Response: Calm/Low energy -> Slower pulse (max 60s)
                dynamic_interval = max(5.0, min(60.0, 30.0 / (stress * 2 + (arousal / 50.0))))
                
                logger.debug(f"💓 [Pulse] Pulse modulation: {dynamic_interval:.1f}s (Stress: {stress:.2f})")
                
                # 1. Biological Aging
                await self._process_metabolism()
                
                # 2. Environmental Perception
                await self._observe_environment()
                
                await asyncio.sleep(dynamic_interval)
            except Exception as e:
                logger.error(f"[Pulse] Cardiac Arrhythmia: {e}")
                await asyncio.sleep(10)

    async def _process_metabolism(self):
        """
        Simulates 2030-standard Data Metabolism.
        Links hardware resources (CPU/Battery) to biological decay.
        """
        import psutil
        
        # 1. CPU Load -> Fatigue
        cpu_usage = psutil.cpu_percent(interval=1)
        # If CPU is consistently over 70%, increase fatigue rapidly
        fatigue_impact = (cpu_usage / 100.0) * 0.1
        
        # 2. Battery Level -> Energy/Hunger
        battery = psutil.sensors_battery()
        energy_level = battery.percent if battery else 100.0
        
        # 3. Inject into Bio Integrator
        # We assume the Bio Integrator has 'fatigue' and 'energy' metrics in its endocrine/nervous system
        try:
            # Simulate a metabolic event based on real hardware state
            await self.bio_integrator.process_stress_event(
                intensity=fatigue_impact, 
                duration=self.update_interval
            )
            
            if energy_level < 20:
                logger.warning(f"🔋 [Metabolism] Critical Energy Low: {energy_level}%. Angela is starving.")
                await self.bio_integrator.process_stress_event(intensity=0.3, duration=10.0)
            
            logger.debug(f"[Metabolism] Hardware Pulse - CPU: {cpu_usage}%, Battery: {energy_level}%")
        except Exception as e:
            logger.error(f"Metabolic injection failed: {e}")

    async def _observe_environment(self):
        """Angela autonomously looks at what the user is doing via OS Bridge."""
        summary = self.os_bridge.get_summary()
        if summary.get("status") == "success":
            active_windows = summary.get("window_preview", [])
            # If user is in a 'stressful' environment (like terminal/coding), slightly increase arousal
            if any("PowerShell" in w or "CMD" in w for w in active_windows):
                await self.bio_integrator.process_stress_event(intensity=0.1, duration=5.0)
            # If user is in 'relaxing' environment (browser), decrease stress
            elif any("Google" in w for w in active_windows):
                await self.bio_integrator.process_relaxation_event(intensity=0.1)

if __name__ == "__main__":
    async def test():
        heart = MetabolicHeartbeat(update_interval=5.0)
        await heart.start()
        await asyncio.sleep(15)
        await heart.stop()
    asyncio.run(test())
