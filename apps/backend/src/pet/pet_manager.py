import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class PetManager:
    """Manages the state, behavior, and interactions of the desktop pet.
    Designed to allow for dynamic personalities and behaviors that can be updated by the core AI.

    修复版本：改进状态管理逻辑
    - 重新设计状态更新逻辑
    - 添加合理的数值范围限制
    - 实现状态衰减机制
    - 添加状态历史记录
    """

    def __init__(self, pet_id: str, config: Dict[str, Any], biological_integrator: Any = None, broadcast_callback: Optional[callable] = None) -> None:
        """Initializes the PetManager for a specific pet."""
        self.pet_id = pet_id
        self.config = config
        self.biological_integrator = biological_integrator
        self.broadcast_callback = broadcast_callback
        self.economy_manager = None  # To be set via setter or during init

        # ========== 修复：改进的初始状态 ==========
        self.state: Dict[str, Any] = {
            "happiness": 80,      # 初始 80（更合理）
            "hunger": 10,         # 初始 10（轻度饥饿）
            "energy": 90,         # 初始 90（精力充沛）
            "health": 100,        # 新增：健康状态
            "position": {"x": 0, "y": 0},
            "scale": 1.0,
            "current_animation": "idle",
            "current_expression": "neutral"
        }

        # 状态历史记录（修复：新增）
        self.state_history: List[Dict[str, Any]] = []
        self.max_history_size = 100

        self.personality: Dict[str, Any] = self.config.get("initial_personality", {"curiosity": 0.7, "playfulness": 0.8})
        self.behavior_rules: Dict[str, Any] = self.config.get("initial_behaviors", {"on_interaction": "show_happiness"})

        # Action queue for AI-initiated actions / AI 主動行為隊列
        self.action_queue: List[Dict[str, Any]] = []
        self.max_queue_size = 10

        # ========== 修复：改进的生存设置 ==========
        # 状态衰减率（每小时）
        self.decay_rates = {
            "hunger": 5.0,      # 饥饿每小时增加 5
            "energy": 3.0,      # 精力每小时减少 3
            "happiness": 2.0,   # 快乐每小时减少 2
            "health": 0.5       # 健康每小时减少 0.5（如果状态不好）
        }

        # 状态阈值
        self.thresholds = {
            "critical": 20.0,   # 临界值（触发紧急行为）
            "warning": 40.0,    # 警告值
            "good": 70.0,       # 良好值
            "excellent": 90.0   # 优秀值
        }

        # 状态限制
        self.state_limits = {
            "happiness": (0, 100),
            "hunger": (0, 100),
            "energy": (0, 100),
            "health": (0, 100)
        }

        logger.info(f"PetManager for pet '{self.pet_id}' initialized with improved state management.")
        
        # Initialize last decay time
        self._last_decay_time = datetime.now()

    # ========== 修复：状态管理辅助方法 ==========

    def _validate_state(self):
        """验证并修正状态值在合理范围内"""
        for key, (min_val, max_val) in self.state_limits.items():
            if key in self.state:
                self.state[key] = max(min_val, min(max_val, self.state[key]))

    def _record_state_change(self, reason: str):
        """记录状态变更历史"""
        state_snapshot = {
            "timestamp": datetime.now().isoformat(),
            "state": self.state.copy(),
            "reason": reason
        }
        self.state_history.append(state_snapshot)

        # 限制历史记录大小
        if len(self.state_history) > self.max_history_size:
            self.state_history.pop(0)

    def get_state_status(self, state_name: str) -> str:
        """获取状态状态（critical/warning/good/excellent）"""
        value = self.state.get(state_name, 50)

        if value <= self.thresholds["critical"]:
            return "critical"
        elif value <= self.thresholds["warning"]:
            return "warning"
        elif value >= self.thresholds["excellent"]:
            return "excellent"
        elif value >= self.thresholds["good"]:
            return "good"
        else:
            return "normal"

    def calculate_overall_wellbeing(self) -> float:
        """计算整体健康状况（0-100）"""
        happiness = self.state.get("happiness", 50)
        energy = self.state.get("energy", 50)
        health = self.state.get("health", 50)
        hunger = 100 - self.state.get("hunger", 50)  # 反转饥饿值

        # 加权平均
        weights = {"happiness": 0.35, "energy": 0.25, "health": 0.25, "hunger": 0.15}
        overall = (
            happiness * weights["happiness"] +
            energy * weights["energy"] +
            health * weights["health"] +
            hunger * weights["hunger"]
        )

        return max(0, min(100, overall))

    def sync_with_biological_state(self):
        """Syncs pet state with internal biological simulation (hormones, arousal)."""
        if not self.biological_integrator:
            return

        bio_state = self.biological_integrator.get_biological_state()
        
        # Map arousal to happiness/energy
        arousal = bio_state.get("arousal", 50.0)
        mood = bio_state.get("mood", 0.5) # Pleasure dimension
        
        # Update happiness based on pleasure/mood
        self.state["happiness"] = int(mood * 100)
        
        # Map dominant emotion to expression
        emotion_map = {
            "joy": "happy",
            "trust": "happy",
            "fear": "scared",
            "surprise": "surprised",
            "sadness": "sad",
            "disgust": "annoyed",
            "anger": "angry",
            "calm": "neutral",
            "love": "happy"
        }
        dominant_emotion = bio_state.get("dominant_emotion", "unknown")
        self.state["current_expression"] = emotion_map.get(dominant_emotion, "neutral")
        
        # Map stress to animation if high
        stress = bio_state.get("stress_level", 0.0)
        if stress > 15.0: # Arbitrary threshold
            self.state["current_animation"] = "anxious"
        elif arousal < 20.0:
            self.state["current_animation"] = "sleepy"

        logger.debug(f"Pet '{self.pet_id}' synced with biological state. Happiness: {self.state['happiness']}")
        # Schedule async notification only if there's a running event loop
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._notify_state_change("sync_bio"))
        except RuntimeError:
            # No running event loop during module import, skip notification
            pass

    async def _notify_state_change(self, reason: str):
        """Notifies external clients about pet state changes (e.g., via WebSocket)."""
        if self.broadcast_callback:
            try:
                # If broadcast_callback is coro, await it
                import asyncio
                payload = {
                    "pet_id": self.pet_id,
                    "reason": reason,
                    "state": self.state,
                    "timestamp": datetime.now().isoformat()
                }
                if asyncio.iscoroutinefunction(self.broadcast_callback):
                    await self.broadcast_callback("pet_state_update", payload)
                else:
                    self.broadcast_callback("pet_state_update", payload)
            except Exception as e:
                logger.error(f"Failed to broadcast pet state change: {e}")

    async def handle_interaction(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles user interaction and updates the pet's state based on behavior rules.

        修复版本：改进的状态更新逻辑
        - 考虑多种因素（饥饿、精力、健康等）
        - 使用状态验证和限制
        - 记录状态变更历史
        """
        interaction_type = interaction_data.get("type")
        logger.debug(f"Handling interaction: '{interaction_type}' for pet '{self.pet_id}'")

        # ========== 修复：改进的状态更新逻辑 ==========
        if interaction_type == "pet":
            # 摸头：增加快乐，但受饥饿和精力影响
            if self.state["hunger"] < self.thresholds["warning"] and self.state["energy"] > self.thresholds["warning"]:
                self.state["happiness"] += 12  # 饱腹和精力充沛时更快乐
            else:
                self.state["happiness"] += 6   # 饿或累时快乐增加较少

            self.state["current_expression"] = "happy"
            self.state["current_animation"] = "respond_to_pet"

        elif interaction_type == "feed":
            # 喂食：减少饥饿，增加快乐和健康
            self.state["hunger"] -= 25
            self.state["happiness"] += 8
            self.state["health"] += 3
            self.state["current_expression"] = "joy"
            self.state["current_animation"] = "eat"

        elif interaction_type == "play":
            # 玩耍：消耗精力，增加快乐，增加饥饿
            if self.state["energy"] > self.thresholds["warning"]:
                self.state["energy"] -= 15
                self.state["happiness"] += 18  # 玩耍带来的快乐更多
                self.state["hunger"] += 5
                self.state["current_animation"] = "dance"
            else:
                # 太累了，无法玩耍
                self.state["happiness"] -= 5  # 失望
                self.state["current_expression"] = "tired"
                self.state["current_animation"] = "refuse_play"

        elif interaction_type == "rest":
            # 休息：恢复精力，减少饥饿
            self.state["energy"] += 25
            self.state["happiness"] += 5  # 休息也带来快乐
            self.state["hunger"] += 3
            self.state["current_expression"] = "relaxed"
            self.state["current_animation"] = "sleep"

        elif interaction_type == "heal":
            # 治疗：恢复健康
            self.state["health"] += 20
            self.state["happiness"] += 5
            self.state["current_expression"] = "relieved"
            self.state["current_animation"] = "heal"

        # ========== 修复：验证状态值 ==========
        self._validate_state()

        # ========== 修复：记录状态变更 ==========
        self._record_state_change(f"interaction_{interaction_type}")

        logger.info(f"Pet '{self.pet_id}' handled interaction '{interaction_type}'. Current state: {self.state}")
        # Notify immediately on interaction
        await self._notify_state_change(f"interaction_{interaction_type}")
        return {"status": "success", "new_state": self.state, "wellbeing": self.calculate_overall_wellbeing()}

    def get_current_state(self) -> Dict[str, Any]:
        """Returns the current state of the pet."""
        return self.state

    def update_position(self, x: float, y: float, scale: float = None):
        """Update pet's desktop position and scale / 更新寵物在桌面上的位置和縮放"""
        self.state["position"] = {"x": x, "y": y}
        if scale is not None:
            self.state["scale"] = scale
        logger.debug(f"Pet '{self.pet_id}' position updated to ({x}, {y}), scale: {self.state['scale']}")

    def add_action(self, action_type: str, data: Dict[str, Any] = None):
        """Add an action for the desktop pet to perform / 為桌面端添加待執行動作"""
        action = {
            "action_id": str(uuid.uuid4()),
            "type": action_type,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        self.action_queue.append(action)
        if len(self.action_queue) > self.max_queue_size:
            self.action_queue.pop(0)
        logger.info(f"Added action '{action_type}' to queue for pet '{self.pet_id}'")

    async def apply_resource_decay(self, delta_time_factor: float = 1.0):
        """
        Simulates the passage of time on pet needs (Hunger, Energy, Happiness, Health).

        """
        # Calculate real time delta
        now = datetime.now()
        time_delta = (now - self._last_decay_time).total_seconds()
        self._last_decay_time = now
        
        # Convert to hours for rate calculation
        # If delta_time_factor is provided, it acts as a speed multiplier (e.g. 2.0 = 2x speed), not a raw value
        hours_passed = (time_delta / 3600.0) * delta_time_factor
        
        # Prevent massive jumps if system slept/paused (cap at 1 hour)
        if hours_passed > 1.0:
            hours_passed = 1.0
            
        # ========== 修复：改进的衰减逻辑 ==========
        # 饥饿增加
        self.state["hunger"] += self.decay_rates["hunger"] * hours_passed
        
        # 精力减少（受饥饿影响：饿的时候精力下降更快）
        hunger_factor = 1.0 + (self.state["hunger"] / 200.0)  # 饥饿越高，精力下降越快
        self.state["energy"] -= self.decay_rates["energy"] * hours_passed * hunger_factor

        # 快乐减少（受饥饿和精力影响）
        if self.state["hunger"] > self.thresholds["warning"] or self.state["energy"] < self.thresholds["warning"]:
            # 不好状态：快乐下降更快
            self.state["happiness"] -= self.decay_rates["happiness"] * hours_passed * 1.5
        else:
            # 良好状态：快乐下降正常
            self.state["happiness"] -= self.decay_rates["happiness"] * hours_passed

        # 健康减少（受饥饿、精力、快乐的综合影响）
        if (self.state["hunger"] > self.thresholds["critical"] or
            self.state["energy"] < self.thresholds["critical"] or
            self.state["happiness"] < self.thresholds["critical"]):
            # 临界状态：健康下降更快
            self.state["health"] -= self.decay_rates["health"] * hours_passed * 3.0
        elif (self.state["hunger"] > self.thresholds["warning"] or
              self.state["energy"] < self.thresholds["warning"] or
              self.state["happiness"] < self.thresholds["warning"]):
            # 警告状态：健康下降正常
            self.state["health"] -= self.decay_rates["health"] * hours_passed * 1.5
        else:
            # 良好状态：健康下降缓慢
            self.state["health"] -= self.decay_rates["health"] * hours_passed

        # ========== 修复：验证状态值 ==========
        self._validate_state()

        # ========== 修复：记录状态变更 ==========
        self._record_state_change("decay")

        logger.debug(f"Applied decay to pet '{self.pet_id}'. Current: H:{self.state['hunger']}, E:{self.state['energy']}, Hap:{self.state['happiness']}, He:{self.state['health']}")

        # Check if pet needs to take action
        await self.check_survival_needs()
        await self._notify_state_change("decay")

    async def check_survival_needs(self):
        """
        Proactively checks survival bars and triggers economic activity if needed.

        修复版本：改进的生存需求检查
        - 使用新的阈值系统
        - 优先级排序（健康 > 饥饿 > 精力）
        - 记录状态变更
        """
        if not self.economy_manager:
            logger.error(f"DEBUG: Pet '{self.pet_id}' has NO linked economy_manager!")
            return

        logger.info(f"DEBUG: Pet '{self.pet_id}' checking survival needs. Hunger: {self.state['hunger']}, Energy: {self.state['energy']}, Health: {self.state['health']}")

        # ========== 修复：改进的生存需求检查（优先级排序）==========

        # 1. Health Check (Highest Priority)
        if self.state["health"] < self.thresholds["critical"]:
            logger.info(f"Pet '{self.pet_id}' is critically ill ({self.state['health']}). Attempting to heal.")
            result = self.economy_manager.purchase_item(self.pet_id, "medical_kit")
            if result["success"]:
                self.state["health"] += result["effects"].get("health", 30)
                self.add_action("heal_autonomous", {"item": "medical_kit"})
                await self._notify_state_change("autonomous_purchase_health")
            self._validate_state()

        # 2. Hunger Check (High Priority)
        elif self.state["hunger"] > (100 - self.thresholds["critical"]):
            logger.info(f"Pet '{self.pet_id}' is critically hungry ({self.state['hunger']}). Attempting purchase.")
            result = self.economy_manager.purchase_item(self.pet_id, "premium_bio_pellets")
            if result["success"]:
                self.state["hunger"] -= result["effects"].get("hunger", 30)
                self.state["happiness"] += result["effects"].get("happiness", 10)
                self.add_action("eat_autonomous", {"item": "premium_bio_pellets"})
                await self._notify_state_change("autonomous_purchase_food")
            self._validate_state()

        # 3. Energy Check (Medium Priority)
        elif self.state["energy"] < self.thresholds["critical"]:
            logger.info(f"Pet '{self.pet_id}' is critically tired ({self.state['energy']}). Attempting purchase.")
            result = self.economy_manager.purchase_item(self.pet_id, "digital_energy_drink")
            if result["success"]:
                self.state["energy"] += result["effects"].get("energy", 30)
                self.add_action("drink_autonomous", {"item": "digital_energy_drink"})
                await self._notify_state_change("autonomous_purchase_energy")
            self._validate_state()

        # 4. Happiness Check (Low Priority)
        elif self.state["happiness"] < self.thresholds["critical"]:
            logger.info(f"Pet '{self.pet_id}' is critically sad ({self.state['happiness']}). Attempting to cheer up.")
            result = self.economy_manager.purchase_item(self.pet_id, "toy")
            if result["success"]:
                self.state["happiness"] += result["effects"].get("happiness", 20)
                self.add_action("play_autonomous", {"item": "toy"})
                await self._notify_state_change("autonomous_purchase_happiness")
            self._validate_state()

        # ========== 修复：记录状态变更 ==========
        self._record_state_change("survival_check")

    def set_economy_manager(self, eco_manager):
        """Link the economy manager for autonomous spending."""
        self.economy_manager = eco_manager
        logger.info(f"PetManager linked to EconomyManager.")

    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get and clear pending actions / 獲取並清除待執行動作"""
        actions = self.action_queue.copy()
        self.action_queue.clear()
        return actions

    def update_behavior(self, new_behaviors: Dict[str, Any]):
        """Allows the core AI to dynamically update the pet's behavior rules."""
        logger.info(f"Updating behavior for pet '{self.pet_id}' from {self.behavior_rules} to {new_behaviors}")
        self.behavior_rules.update(new_behaviors)
        logger.info(f"Behavior for pet '{self.pet_id}' updated successfully.")
