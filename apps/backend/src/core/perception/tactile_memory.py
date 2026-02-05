from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from .tactile_sampler import TactileProperties, MaterialType

class TactileMemory:
    """觸覺記憶：存儲材質屬性檔案與物體表面的觸覺地圖 (Tactile Maps)"""
    
    def __init__(self, capacity: int = 200):
        self.capacity = capacity
        # 材質檔案庫 (已知材質的標準屬性)
        self.material_profiles: Dict[str, TactileProperties] = {}
        # 物體觸覺地圖 (特定物體 ID 及其表面的觸覺分佈)
        self.object_tactile_maps: Dict[str, Dict[str, Any]] = {}
        
    def learn_material(self, name: str, props: TactileProperties):
        """學習並記住一種新材質的觸覺特徵"""
        self.material_profiles[name] = props
        
    def update_object_map(self, object_id: str, contact_data: Dict[str, Any]):
        """更新特定物體的觸覺地圖 (如：發現桌子的左上角比右下角更粗糙)"""
        if object_id not in self.object_tactile_maps:
            self.object_tactile_maps[object_id] = {
                "last_interaction": datetime.now(),
                "points": []
            }
        
        self.object_tactile_maps[object_id]["points"].append(contact_data)
        self.object_tactile_maps[object_id]["last_interaction"] = datetime.now()

    def get_known_properties(self, material_name: str) -> Optional[TactileProperties]:
        """檢索已知材質的屬性"""
        return self.material_profiles.get(material_name)

    def get_object_experience(self, object_id: str) -> Optional[Dict[str, Any]]:
        """獲取對特定物體的歷史觸覺經驗"""
        return self.object_tactile_maps.get(object_id)

    def clear(self):
        self.material_profiles.clear()
        self.object_tactile_maps.clear()
