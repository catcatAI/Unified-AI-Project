"""
Angela AI 2030 - Digital Life Constants
Provides the 'Why' behind the numbers. Baseline biological and governance thresholds.
"""

class MetabolicConstants:
    # Baseline decay rates (per heartbeat)
    BASE_FATIGUE_INCREASE = 0.02
    RECOVERY_RATE_IDLE = 0.05
    
    # Resource stress multipliers
    CPU_STRESS_FACTOR = 0.005 # 1% CPU = 0.005 base stress
    BATTERY_STARVATION_THRESHOLD = 20.0 # Starts panicking below 20%
    
class SensoryConstants:
    # Reflex sensitivity
    TOUCH_AROUSAL_BOOST = 1.2
    REPETITIVE_TOUCH_STRESS_THRESHOLD = 0.8 # Multi-tap irritation
    
class GovernanceConstants:
    # GSI-4 M-Series Weights
    EXPLORATION_BASE_FACTOR = 0.1
    COGNITIVE_GAP_RECOVERY = 0.05
    ALPHA_MODE_THRESHOLD = 0.65
    STRATEGIC_VALUE_INCREMENT = 0.05 # Contribution to V_total per strategic task

class ActionGeometricMapping:
    """
    行為-幾何映射 (L4-S1)
    定義不同行為在 3D 空間中的「標準方向」。
    """
    # 休息行為 -> 向原點收縮
    REST = (0.0, 0.0, 0.0)
    
    # 認知/邏輯行為 -> 向正 X 軸與 Z 軸擴張 (高能耗、高複雜度)
    COGNITIVE_HEAVY = (10.0, 5.0, 2.0)
    
    # 社交/情緒行為 -> 向 Y 軸與對角線偏移 (共感、互動)
    SOCIAL_ACTIVE = (2.0, 10.0, 5.0)
    
    # 逃避/防禦行為 -> 向負座標軸偏移
    DEFENSIVE = (-5.0, -5.0, -5.0)
    
    # 隨機探索行為 -> 高熵偏移
    RANDOM_EXPLORE = (5.0, 5.0, 5.0)

