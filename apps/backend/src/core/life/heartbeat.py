# =============================================================================
# ANGELA-MATRIX: L1[生物層] αβγδ [A] L2+
# =============================================================================
# 職責: 代謝心跳驅動器 (Metabolic Heartbeat).
# 維度: 四維全狀態同步，將硬體負載與環境感知轉化為生命體徵。
# =============================================================================

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional
from core.bio.biological_integrator import BiologicalIntegrator
from core.bio.endocrine_system import HormoneType
from core.system.config.magic_numbers import loop_sleep, heartbeat_value as _hb
from integrations.os_bridge_adapter import OSBridgeAdapter

logger = logging.getLogger(__name__)

class MetabolicHeartbeat:
    def __init__(self, update_interval: float = 30.0):
        self.update_interval = update_interval
        self.bio_integrator = BiologicalIntegrator()
        self.os_bridge = OSBridgeAdapter()
        
        # 2030 Standard: Cerebellum & Sensory Integration
        from core.bio.cerebellum_engine import CerebellumEngine
        from core.bio.input_sensor import GlobalInputSensor
        self.cerebellum = CerebellumEngine()
        self.input_sensor = GlobalInputSensor()
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.start_time = datetime.now()
        
        # --- Spatial State (Angela's physical presence) ---
        self.screen_w = 1920
        self.screen_h = 1080
        self.x = 200.0
        self.y = 0.0
        self.target_x = 200.0
        from core.system.config.tiered_loader import get_config as _gc
        self._beh_cfg = _gc("standard/behavior/behavior")
        self.velocity = self._beh_cfg.get("movement", {}).get("base_velocity", 0.05)
        self.posture = {"spine_bend": 0.0, "theta_matrix": [0.0]*9}

    async def _integration_loop(self) -> None:
        """Integration loop."""
        while self._running:
            try:
                dist_to_target = abs(self.target_x - self.x)
                intent_pose = "walking" if dist_to_target > self._beh_cfg.get("movement", {}).get("walk_threshold", 5.0) else "standing"
                
                bio_state = self.bio_integrator.get_biological_state()
                
                # 1.5 [Task N.4.3] L4 Art Learning Sync
                color_overrides = await self.bio_integrator.art_workflow.update_visual_state()

                # 呼叫小腦：執行指令並獲取細節
                cerebellum_res = self.cerebellum.execute_command(
                    pose_name=intent_pose,
                    bio_state=bio_state
                )
                
                # 更新空間姿態物件 (包含 9 段脊椎矩陣與五指矩陣)
                self.posture = {
                    "pose_name": cerebellum_res["pose_name"],
                    "theta_matrix": cerebellum_res["theta_matrix"],
                    "finger_matrix": cerebellum_res.get("finger_matrix", {"left": [0.0]*5, "right": [0.0]*5}),
                    "color_overrides": color_overrides,
                    "tremor_active": cerebellum_res.get("tremor_active", False)
                }
                
                move_th = self._beh_cfg.get("movement", {}).get("move_threshold", 1.0)
                if dist_to_target > move_th:
                    stress = bio_state.get("stress_level", 0.0)
                    stress_speed_factor = self._beh_cfg.get("movement", {}).get("stress_speed_factor", 0.5)
                    speed = self.velocity * (1.0 - stress * stress_speed_factor)
                    self.x += (self.target_x - self.x) * speed
                
                await asyncio.sleep(loop_sleep("sleep_short", 0.1))
            except Exception as e:
                logger.error(f"[Cerebellum-Sync] Loop error: {e}", exc_info=True)
                await asyncio.sleep(loop_sleep("sleep_long", 1.0))

    async def start(self) -> None:
        """Start the metabolic heartbeat loop."""
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

    async def stop(self) -> None:
        """Stop the metabolic heartbeat loop."""
        self._running = False
        if self._task:
            self._task.cancel()
        await self.bio_integrator.shutdown()
        logger.info("🛑 Heartbeat stopped.")

    async def _run_loop(self) -> None:
        """Run loop."""
        while self._running:
            try:
                hb_cfg = self._beh_cfg.get("heartbeat", {})
                state = self.bio_integrator.get_biological_state()
                stress = state.get("stress_level", hb_cfg.get("default_stress", 0.5))
                arousal = state.get("arousal", hb_cfg.get("default_arousal", 50.0))
                
                # Dynamic Interval
                min_int = _hb("heartbeat.min_interval", 5.0)
                max_int = _hb("heartbeat.max_interval", 60.0)
                base_rate = _hb("heartbeat.base_rate", 30.0)
                div = _hb("heartbeat.stress_divisor", 50.0)
                mul = _hb("heartbeat.stress_multiplier", 2)
                dynamic_interval = max(min_int, min(max_int, base_rate / (stress * mul + (arousal / div))))
                
                # --- NEW: Spatial Decision Making ---
                await self._update_spatial_state(arousal, stress)
                
                # 1. Metabolism & 2. Environment
                await self._process_metabolism()
                await self._observe_environment()
                
                await asyncio.sleep(dynamic_interval)
            except Exception as e:  # broad exception acceptable: heartbeat loop must be resilient to errors
                logger.error(f"[Pulse] Cardiac Arrhythmia: {e}", exc_info=True)
                await asyncio.sleep(loop_sleep("sleep_very_long", 10.0))

    async def _update_spatial_state(self, arousal, stress) -> None:
        """Update spatial position based on arousal and stress levels."""
        import random
        mov_conf = self._beh_cfg.get("movement", {})
        
        arousal_thresh = mov_conf.get("arousal_threshold", 0.7)
        jump_prob = mov_conf.get("jump_probability", 0.1)
        
        if arousal > arousal_thresh and random.random() < jump_prob:
            from app_config_loader import get_formula_config
            spatial_conf = get_formula_config("spatial")
            max_x = spatial_conf.get("screen", {}).get("width", 1920)
            offset = mov_conf.get("max_x_offset", 100)
            self.target_x = random.randint(50, max_x - offset)
            logger.info(f"🚶 [Spatial] Intent Jump: Target set to x={self.target_x} (Arousal: {arousal:.2f})")
        
        from core.engine.cognitive_operations import PotentialFieldEngine
        engine = PotentialFieldEngine()
        
        # 速度與壓力影響係數從配置讀取
        vel_scale = mov_conf.get("velocity_scaling", 1.0)
        stress_impact = mov_conf.get("stress_impact", 0.8)
        
        dx, _, _ = engine.calculate_attractive_displacement(
            (self.x, 0, 0),
            (self.target_x, 0, 0),
            pull_factor=self.velocity * vel_scale * (1.0 - stress * stress_impact)
        )
        
        if dx != 0:
            next_x = self.x + dx
            if not self._check_collision(next_x):
                self.x = next_x
            else:
                from .bio_reflex_manager import BiogenicReflexManager
                reflex_mgr = BiogenicReflexManager(self.bio_integrator)
                damage = mov_conf.get("collision_damage", 0.7)
                asyncio.create_task(reflex_mgr.trigger_physical_trauma("leg", damage))
                self.target_x = self.x

    def _check_collision(self, next_x) -> bool:
        """Check if the next position collides with screen boundaries."""
        mov = self._beh_cfg.get("movement", {})
        left = mov.get("border_margin_left", 20)
        right = mov.get("border_margin_right", 150)
        if next_x < left or next_x > (self.screen_w - right):
            return True

        wb_left = mov.get("whiteboard_left", 1450)
        wb_right = mov.get("whiteboard_right", 1700)
        if wb_left < next_x < wb_right:
            logger.info("🚧 [Collision] Angela touched the Whiteboard.")
            return True

        return False

    async def _process_metabolism(self) -> None:
        """
        Simulates 2030-standard Data Metabolism.
        Links hardware resources (CPU/Battery) to biological decay.
        """
        import psutil
        
        hb_cfg = self._beh_cfg.get("heartbeat", {})
        cpu_usage = psutil.cpu_percent(interval=hb_cfg.get("cpu_poll_interval", 1))
        fatigue_impact = (cpu_usage / 100.0) * hb_cfg.get("fatigue_scale", 0.1)
        
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
            
            if energy_level < _hb("heartbeat.low_battery_threshold", 20):
                logger.warning(f"🔋 [Metabolism] Critical Energy Low: {energy_level}%. Angela is starving.", exc_info=True)
                await self.bio_integrator.process_stress_event(
                    intensity=hb_cfg.get("low_battery_stress_intensity", 0.3),
                    duration=hb_cfg.get("low_battery_stress_duration", 10.0),
                )
            
            logger.debug(f"[Metabolism] Hardware Pulse - CPU: {cpu_usage}%, Battery: {energy_level}%")
        except Exception as e:  # broad exception acceptable: metabolism processing should be resilient to hardware errors
            logger.error(f"Metabolic injection failed: {e}", exc_info=True)

    async def _observe_environment(self) -> None:
        """
        [N.6.1] Angela autonomously looks at what the user is doing via GlobalInputSensor.
        Maps categorized activities to biological triggers.
        """
        # 1. 執行環境嗅探
        self.input_sensor.sniff_environment()
        metrics = self.input_sensor.get_activity_metrics()
        category = metrics.get("active_category", "neutral")
        
        hb_cfg = self._beh_cfg.get("heartbeat", {})
        if category == "gaming":
            await self.bio_integrator.process_stress_event(
                intensity=hb_cfg.get("gaming_stress_intensity", 0.2),
                duration=hb_cfg.get("gaming_stress_duration", 10.0),
            )
            self.bio_integrator.emotional_system.apply_influence("external", "joy", 0.3, 0.5)
        elif category == "coding":
            await self.bio_integrator.process_stress_event(
                intensity=hb_cfg.get("coding_stress_intensity", 0.1),
                duration=hb_cfg.get("coding_stress_duration", 30.0),
            )
        elif category == "media":
            await self.bio_integrator.process_relaxation_event(
                intensity=hb_cfg.get("media_relaxation_intensity", 0.3)
            )
        elif category == "social":
            await self.bio_integrator.endocrine_system.adjust_hormone(
                HormoneType.OXYTOCIN, hb_cfg.get("social_oxytocin_adjust", 10.0)
            )

        logger.debug(f"🌍 [Environment] Activity: {category}, BPM: {metrics['input_density_bpm']:.1f}")

if __name__ == "__main__":
    async def test() -> None:
        """Run a quick test of the MetabolicHeartbeat."""
        heart = MetabolicHeartbeat(update_interval=5.0)
        await heart.start()
        await asyncio.sleep(15)
        await heart.stop()
    asyncio.run(test())
