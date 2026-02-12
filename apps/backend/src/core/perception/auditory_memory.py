import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import uuid
import logging
logger = logging.getLogger(__name__)

@dataclass
class VoiceprintProfile:
    """聲紋與聲音特徵檔案"""
    profile_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "unknown_speaker"
    label: str = "unknown"
    
    # 聲紋特徵向量 (128維)
    embedding: np.ndarray = field(default_factory=lambda: np.zeros(128))
    
    # 統計資訊
    last_heard: datetime = field(default_factory=datetime.now)
    total_duration: float = 0.0
    confidence_score: float = 0.0
    
    # 關聯元數據
    metadata: Dict[str, Any] = field(default_factory=dict)

class AuditoryMemory:
    """聽覺記憶：負責存儲聲紋、環境音特徵，並進行相似度匹配"""
    
    def __init__(self, capacity: int = 500):
        self.capacity = capacity
        self.profiles: Dict[str, VoiceprintProfile] = {}
        self.threshold = 0.75 # 聲紋匹配閾值 (餘弦相似度)
        
    def identify_or_register(self, embedding: np.ndarray, metadata: Optional[Dict] = None) -> VoiceprintProfile:
        """識別現有聲紋或註冊新聲紋"""
        best_match_id = self._find_best_match(embedding)
        
        if best_match_id:
            profile = self.profiles[best_match_id]
            profile.last_heard = datetime.now()
            # 簡單的特徵向量平滑更新
            profile.embedding = 0.9 * profile.embedding + 0.1 * embedding
            profile.embedding /= np.linalg.norm(profile.embedding) # 保持單位長度
            return profile
        else:
            # 註冊新聲音來源
            label = "speaker" if metadata and metadata.get('is_speech') else "sound_source"
            new_profile = VoiceprintProfile(
                embedding=embedding / np.linalg.norm(embedding),
                label=label,
                metadata=metadata or {}
            )
            self.profiles[new_profile.profile_id] = new_profile
            
            # 容量管理
            if len(self.profiles) > self.capacity:
                self._evict_oldest()
                
            return new_profile

    def _find_best_match(self, embedding: np.ndarray) -> Optional[str]:
        """尋找最相似的聲紋 (餘弦相似度)"""
        if not self.profiles:
            return None
            
        target = embedding / np.linalg.norm(embedding)
        best_score = -1.0
        best_id = None
        
        for pid, profile in self.profiles.items():
            score = np.dot(profile.embedding, target)
            if score > best_score and score > self.threshold:
                best_score = score
                best_id = pid
                
        return best_id

    def _evict_oldest(self):
        """淘汰最久未聽見的記憶"""
        oldest_id = min(self.profiles.keys(), key=lambda k: self.profiles[k].last_heard)
        self.profiles.pop(oldest_id)

    def get_user_profile(self) -> Optional[VoiceprintProfile]:
        """獲取已標記為 'user' 的聲紋"""
        for p in self.profiles.values():
            if p.label == "user":
                return p
        return None
