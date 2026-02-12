from enum import Enum, auto
from typing import Dict, List, Any, Optional, Tuple
import time
import random
import logging
logger = logging.getLogger(__name__)

class AuditoryAttentionMode(Enum):
    SCAN = auto()    # 環境掃描 (監聽所有聲音)
    FOCUS = auto()   # 聚焦特定聲源 (雞尾酒效應)
    TRACK = auto()   # 持續追蹤特定發話者
    IDLE = auto()    # 靜音/待機

class AuditoryAttentionController:
    """聽覺注意力控制器：模擬「雞尾酒效應」，在混亂環境中過濾雜訊並聚焦特定聲源"""
    
    def __init__(self):
        self.mode = AuditoryAttentionMode.SCAN
        self.current_focus_id: Optional[str] = None
        self.focus_start_time: float = 0
        self.min_focus_duration = 0.8
        self.max_focus_duration = 10.0
        
        # 靈敏度參數
        self.noise_threshold = 0.2
        self.user_voice_priority = 2.0
        self.new_source_priority = 1.5
        
    def decide_focus(self, active_sources: List[Any], user_profile_id: Optional[str] = None) -> Optional[str]:
        """決定下一個要聚焦的聲源 ID"""
        now = time.time()
        
        # 1. 如果目前正在聚焦，判斷是否繼續
        if self.mode == AuditoryAttentionMode.FOCUS and self.current_focus_id:
            duration = now - self.focus_start_time
            if duration < self.min_focus_duration:
                return self.current_focus_id
            
            # 如果聚焦太久且有其他高優先級聲音，考慮切換
            if duration > self.max_focus_duration:
                self.mode = AuditoryAttentionMode.SCAN
                
        # 2. 尋找潛在的高優先級目標
        # 優先級：用戶聲紋 > 新出現的響亮聲音 > 其他說話聲 > 環境音
        best_source_id = None
        highest_priority = -1.0
        
        for source in active_sources:
            priority = self._calculate_priority(source, user_profile_id)
            if priority > highest_priority:
                highest_priority = priority
                best_source_id = source.profile_id if hasattr(source, 'profile_id') else source.get('profile_id')
                
        if best_source_id and highest_priority > self.noise_threshold:
            if best_source_id != self.current_focus_id:
                self.current_focus_id = best_source_id
                self.mode = AuditoryAttentionMode.FOCUS
                self.focus_start_time = now
            return best_source_id
            
        return None

    def _calculate_priority(self, source: Any, user_profile_id: Optional[str]) -> float:
        """計算聲源優先級"""
        base_priority = 1.0
        
        # 獲取屬性
        source_id = source.profile_id if hasattr(source, 'profile_id') else source.get('profile_id')
        label = source.label if hasattr(source, 'label') else source.get('label', 'unknown')
        intensity = source.intensity if hasattr(source, 'intensity') else source.get('intensity', 0.5)
        
        # 權重調整
        if source_id == user_profile_id:
            base_priority *= self.user_voice_priority
        elif label == "speaker":
            base_priority *= 1.2
            
        return base_priority * intensity

    def reset(self):
        self.mode = AuditoryAttentionMode.SCAN
        self.current_focus_id = None
        self.focus_start_time = 0
