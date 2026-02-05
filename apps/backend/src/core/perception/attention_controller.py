from enum import Enum, auto
from typing import Dict, List, Any, Optional, Tuple
import time
import random

class AttentionMode(Enum):
    EXPLORE = auto() # 隨機/全局探索
    FOCUS = auto()   # 聚焦特定物體/區域
    TRACK = auto()   # 持續追蹤
    IDLE = auto()    # 待機

class AttentionController:
    """注意力控制器：決定視覺焦點的移動與切換邏輯"""
    
    def __init__(self):
        self.mode = AttentionMode.EXPLORE
        self.current_target_id: Optional[str] = None
        self.last_focus_pos: Tuple[float, float] = (0.5, 0.5)
        self.focus_start_time: float = 0
        self.saccade_cooldown: float = 0.2 # 眼跳 (Saccade) 冷卻時間 (秒)
        self.last_saccade_time: float = 0
        
        # 參數
        self.interest_decay = 0.1 # 興趣衰減率
        self.min_focus_duration = 0.5 # 最短聚焦時間
        self.max_focus_duration = 3.0 # 最長聚焦時間
        
    def update_target(self, pos: Tuple[float, float], target_id: Optional[str] = None):
        """主動切換焦點"""
        now = time.time()
        if now - self.last_saccade_time < self.saccade_cooldown:
            return False # 還在眼跳冷卻中
            
        self.last_focus_pos = pos
        self.current_target_id = target_id
        self.mode = AttentionMode.FOCUS if target_id else AttentionMode.EXPLORE
        self.focus_start_time = now
        self.last_saccade_time = now
        return True

    def get_next_focus_point(self, discovered_objects: List[Any]) -> Tuple[Tuple[float, float], Optional[str]]:
        """根據目前狀態與發現的物體，計算下一個焦點，返回 (位置, 目標ID)"""
        now = time.time()
        
        # 如果目前在聚焦，判斷是否該切換 (興趣衰減或超時)
        duration = now - self.focus_start_time
        if self.mode == AttentionMode.FOCUS:
            if duration > self.max_focus_duration:
                # 聚焦太久，切換到探索模式或下一個未識別物體
                return self._suggest_exploration_or_new_target(discovered_objects)
            return self.last_focus_pos, self.current_target_id
            
        # 探索模式：隨機跳轉或轉向感興趣的區域
        return self._suggest_exploration_or_new_target(discovered_objects)

    def _suggest_exploration_or_new_target(self, discovered_objects: List[Any]) -> Tuple[Tuple[float, float], Optional[str]]:
        """建議下一個探索點或新目標"""
        # 如果有發現物體但未曾聚焦過，優先選擇
        if discovered_objects:
            # 優先選擇信度高但未被詳細識別的
            target = random.choice(discovered_objects)
            pos = (0.5, 0.5)
            target_id = None
            
            if hasattr(target, 'position'):
                pos = target.position
            elif isinstance(target, dict) and 'position' in target:
                pos = target['position']
            
            if hasattr(target, 'object_id'):
                target_id = target.object_id
            elif isinstance(target, dict) and 'object_id' in target:
                target_id = target['object_id']
                
            return pos, target_id
                
        # 否則隨機探索
        return (random.uniform(0.1, 0.9), random.uniform(0.1, 0.9)), None

    def reset(self):
        self.mode = AttentionMode.EXPLORE
        self.current_target_id = None
        self.last_focus_pos = (0.5, 0.5)
