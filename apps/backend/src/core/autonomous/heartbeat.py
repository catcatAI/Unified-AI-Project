import asyncio
import logging
import time
from datetime import datetime
from typing import Optional
from .biological_integrator import BiologicalIntegrator
from integrations.os_bridge_adapter import OSBridgeAdapter

logger = logging.getLogger(__name__)

class MetabolicHeartbeat:
    def __init__(self, update_interval: float = 30.0):
        self.update_interval = update_interval
        self.bio_integrator = BiologicalIntegrator()
        self.os_bridge = OSBridgeAdapter()
        
        # 2030 Standard: Cerebellum Integration
        from core.autonomous.cerebellum_engine import CerebellumEngine
        self.cerebellum = CerebellumEngine()
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.start_time = datetime.now()
        
        # --- Spatial State (Angela's physical presence) ---
        self.screen_w = 1920 
        self.screen_h = 1080
        self.x = 200.0
        self.y = 0.0 
        self.target_x = 200.0
        self.velocity = 0.05
        self.posture = {"spine_bend": 0.0, "theta_matrix": [0.0]*9}

    async def _integration_loop(self):
        while self._running:
            try:
                # 1. [Task N.16.1.c] Cerebellum Pose Execution
                # 根據移動狀態決定意圖標籤 (Intent Label)
                dist_to_target = abs(self.target_x - self.x)
                intent_pose = "walking" if dist_to_target > 5.0 else "standing"
                
                bio_state = self.bio_integrator.get_biological_state()
                # 呼叫小腦：執行指令並獲取細節
                cerebellum_res = self.cerebellum.execute_command(
                    pose_name=intent_pose,
                    bio_state=bio_state
                )
                
                # 更新空間姿態物件 (包含 9 段脊椎矩陣)
                self.posture = {
                    "pose_name": cerebellum_res["pose_name"],
                    "theta_matrix": cerebellum_res["theta_matrix"],
                    "tremor_active": cerebellum_res.get("tremor_active", False)
                }
                
                # 3. Spatial Movement Execution
                if dist_to_target > 1.0:
                    stress = bio_state.get("stress_level", 0.0)
                    speed = self.velocity * (1.0 - stress * 0.5)
                    self.x += (self.target_x - self.x) * speed
                
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"[Cerebellum-Sync] Loop error: {e}")
                await asyncio.sleep(1)

    async def start(self):
        if self._running:
            return
        logger.info("💓 [Heartbeat] Starting MetabolicHeartbeat...")
        self._running = True
        await self.bio_integrator.initialize()
        logger.info("💓 [Heartbeat] BioIntegrator initialized.")
        # 啟動雙重循環：1. 生物/代謝循環 2. 小腦/神經整合循環
        self._task = asyncio.create_task(self._run_loop())
        self._integration_task = asyncio.create_task(self._integration_loop())
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
                # 0. ANS Modulation
                state = self.bio_integrator.get_biological_state()
                stress = state.get("stress_level", 0.5)
                arousal = state.get("arousal", 50.0)
                
                # Dynamic Interval
                dynamic_interval = max(5.0, min(60.0, 30.0 / (stress * 2 + (arousal / 50.0))))
                
                # --- NEW: Spatial Decision Making ---
                await self._update_spatial_state(arousal, stress)
                
                # 1. Metabolism & 2. Environment
                await self._process_metabolism()
                await self._observe_environment()
                
                await asyncio.sleep(dynamic_interval)
            except Exception as e:
                logger.error(f"[Pulse] Cardiac Arrhythmia: {e}")
                await asyncio.sleep(10)

    async def _update_spatial_state(self, arousal, stress):
        """Calculates Angela's next move based on bio-state."""
        import random
        # Decision: Higher arousal -> more likely to set a new target
        if random.random() < (arousal / 100.0) * 0.5:
            # We assume a standard screen width for logic, renderer will scale
            self.target_x = random.randint(50, 1800)
            logger.debug(f"🚶 [Spatial] Angela decided to move to x={self.target_x}")
        
        # Simple step towards target (the brain's intention)
        dist = self.target_x - self.x
        if abs(dist) > 5:
            # 2030 Standard: Collision detection linked to pain
            # Assume we have a method to check world collision
            if self._check_collision(self.x + (5 if dist > 0 else -5)):
                from .bio_reflex_manager import BiogenicReflexManager
                reflex_mgr = BiogenicReflexManager(self.bio_integrator)
                asyncio.create_task(reflex_mgr.trigger_physical_trauma("leg", 0.7))
                self.target_x = self.x # Stop moving
            else:
                speed = self.velocity * (1.0 - stress)
                self.x += dist * speed

    def _check_collision(self, next_x):
        # 1. 螢幕邊界檢查
        if next_x < 20 or next_x > (self.screen_w - 150):
            return True
            
        # 2. 實體物件碰撞檢查 (2030 Standard)
        # 假設白板在 1500px, 寬度 200px
        if 1450 < next_x < 1700:
            logger.info("🚧 [Collision] Angela touched the Whiteboard.")
            return True
            
        return False

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
