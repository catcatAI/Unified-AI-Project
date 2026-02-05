from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import uuid

@dataclass
class PerceivedObject:
    """感知到的物體模型"""
    object_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "unknown"
    label: str = "unlabeled"
    confidence: float = 0.0
    
    # 空間資訊 (歸一化座標 0.0 - 1.0)
    position: Tuple[float, float] = (0.5, 0.5) 
    bounds: Optional[Tuple[float, float, float, float]] = None # xmin, ymin, xmax, ymax
    
    # 特徵資訊
    features: Dict[str, Any] = field(default_factory=dict)
    last_seen: datetime = field(default_factory=datetime.now)
    seen_count: int = 1
    
    # 語義關聯
    metadata: Dict[str, Any] = field(default_factory=dict)

class PerceptualMemory:
    """感知記憶模組：負責存儲、檢索與更新已識別的物體"""
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.objects: Dict[str, PerceivedObject] = {}
        # 空間索引：簡單起見使用標籤或ID檢索，未來可擴展為 KD-Tree 或 R-Tree
        self.label_index: Dict[str, List[str]] = {}
        
    def add_or_update(self, obj_data: Dict[str, Any]) -> PerceivedObject:
        """新增或更新一個感知到的物體"""
        # 根據座標或標籤嘗試匹配現有物體 (簡單的距離匹配)
        pos = obj_data.get("position", (0.5, 0.5))
        label = obj_data.get("label", "unlabeled")
        
        existing_id = self._find_matching_object(pos, label)
        
        if existing_id:
            obj = self.objects[existing_id]
            obj.last_seen = datetime.now()
            obj.seen_count += 1
            obj.confidence = (obj.confidence + obj_data.get("confidence", 0.0)) / 2
            # 更新特徵
            if "features" in obj_data:
                obj.features.update(obj_data["features"])
            if "position" in obj_data:
                obj.position = obj_data["position"]
        else:
            # 建立新物體
            obj = PerceivedObject(
                name=obj_data.get("name", label),
                label=label,
                confidence=obj_data.get("confidence", 0.0),
                position=pos,
                bounds=obj_data.get("bounds"),
                features=obj_data.get("features", {}),
                metadata=obj_data.get("metadata", {})
            )
            self.objects[obj.object_id] = obj
            
            # 更新索引
            if label not in self.label_index:
                self.label_index[label] = []
            self.label_index[label].append(obj.object_id)
            
        # 容量管理 (LRU)
        if len(self.objects) > self.capacity:
            self._evict_oldest()
            
        return obj

    def get_by_label(self, label: str) -> List[PerceivedObject]:
        """根據標籤獲取物體列表"""
        ids = self.label_index.get(label, [])
        return [self.objects[oid] for oid in ids if oid in self.objects]

    def get_nearest(self, position: Tuple[float, float], threshold: float = 0.1) -> Optional[PerceivedObject]:
        """獲取指定位置附近最接近的物體"""
        match_id = self._find_matching_object(position, threshold=threshold)
        return self.objects.get(match_id) if match_id else None

    def _find_matching_object(self, pos: Tuple[float, float], label: Optional[str] = None, threshold: float = 0.05) -> Optional[str]:
        """尋找匹配的物體 ID"""
        for obj_id, obj in self.objects.items():
            # 計算歐氏距離
            dist = ((obj.position[0] - pos[0])**2 + (obj.position[1] - pos[1])**2)**0.5
            if dist < threshold:
                if label is None or obj.label == label:
                    return obj_id
        return None

    def _evict_oldest(self):
        """淘汰最舊的記憶"""
        oldest_id = min(self.objects.keys(), key=lambda k: self.objects[k].last_seen)
        obj = self.objects.pop(oldest_id)
        if obj.label in self.label_index:
            self.label_index[obj.label].remove(oldest_id)

    def clear(self):
        self.objects.clear()
        self.label_index.clear()
