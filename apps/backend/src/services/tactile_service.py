import logging
import asyncio
import time
from datetime import datetime
from typing import Any, Dict, Optional, List, Tuple

from core.perception.tactile_sampler import TactileSampler, TactileProperties, TactileContactPoint
from core.perception.tactile_memory import TactileMemory
from core.sync.realtime_sync import sync_manager, SyncEvent

logger = logging.getLogger(__name__)

class TactileService:
    """觸覺服務：整合視覺預測建模與觸碰反饋模擬"""

    def __init__(self, config: Optional[Dict] = None) -> None:
        self.config = config or {}
        self.enabled = True
        self.sampler = TactileSampler(self.config.get('sampler_config'))
        self.memory = TactileMemory(capacity=self.config.get('memory_capacity', 200))
        
        # 預設一些基礎材質記憶
        self._init_standard_materials()
        
        # 註冊同步事件監聽
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._init_sync_listener())
        except RuntimeError:
            # No running event loop, this is fine during import or sync tests
            logger.debug("No running event loop, sync listener will not be initialized automatically")
        
        logger.info("Tactile Service initialized with material modeling capabilities")

    async def _init_sync_listener(self):
        """初始化同步監聽器"""
        try:
            await sync_manager.register_client("tactile_service", self._handle_sync_event)
            logger.info("Tactile Service registered to sync manager")
        except Exception as e:
            logger.error(f"Failed to register Tactile Service to sync manager: {e}")

    async def _handle_sync_event(self, event: SyncEvent):
        """處理同步事件"""
        if event.type == "module_control":
            module = event.data.get("module")
            enabled = event.data.get("enabled")
            if module == "tactile":
                self.enabled = enabled
                logger.info(f"Tactile Service enabled status changed to: {enabled}")

    def _init_standard_materials(self):
        """初始化一些標準材質的記憶"""
        self.memory.learn_material("polished_steel", TactileProperties(roughness=0.05, hardness=0.95, temperature=18.0))
        self.memory.learn_material("oak_wood", TactileProperties(roughness=0.4, hardness=0.7, temperature=24.0))
        self.memory.learn_material("soft_cotton", TactileProperties(roughness=0.8, hardness=0.1, temperature=27.0))

    async def model_object_tactile(self, visual_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根據視覺數據（模型、紋理、光影）建模物體的觸覺屬性
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Tactile system is currently disabled"}

        object_id = visual_data.get('object_id', 'unknown_obj')
        logger.info(f"Modeling tactile properties for object: {object_id}")
        
        # 1. 透過採樣器從視覺特徵推斷物理屬性
        props = self.sampler.infer_properties_from_visuals(visual_data)
        
        # 2. 存儲/更新記憶
        self.memory.learn_material(f"material_{object_id}", props)
        
        return {
            "object_id": object_id,
            "tactile_properties": {
                "roughness": props.roughness,
                "hardness": props.hardness,
                "temperature": props.temperature,
                "friction": props.friction
            },
            "timestamp": datetime.now().isoformat()
        }

    async def simulate_touch(self, object_id: str, contact_point: Dict[str, Any]) -> Dict[str, Any]:
        """
        模擬觸摸行為並產生精確的反饋
        """
        # 1. 獲取物體材質屬性 (從記憶或預設)
        props = self.memory.get_known_properties(f"material_{object_id}")
        if not props:
            # 如果沒有記憶，使用中性屬性
            props = TactileProperties()

        # 2. 建立觸摸點對象
        contact = TactileContactPoint(
            position=contact_point.get('position', (0, 0, 0)),
            body_part=contact_point.get('body_part', 'finger_tip'),
            pressure=contact_point.get('pressure', 0.5),
            area=contact_point.get('area', 1.0),
            timestamp=time.time()
        )
        
        # 3. 產生細緻反饋
        feedback = self.sampler.generate_contact_feedback(props, contact)
        
        # 4. 記錄此次互動到物體地圖
        self.memory.update_object_map(object_id, feedback)
        
        return {
            "status": "success",
            "feedback": feedback,
            "object_id": object_id
        }

    async def process(self, input_data: Any) -> Dict[str, Any]:
        """統一的處理方法"""
        if isinstance(input_data, dict):
            action = input_data.get('action')
            if action == 'model':
                return await self.model_object_tactile(input_data.get('visual_data', {}))
            elif action == 'touch':
                return await self.simulate_touch(
                    input_data.get('object_id'), 
                    input_data.get('contact_point', {})
                )
        return {"error": "Invalid input format for tactile processing"}
