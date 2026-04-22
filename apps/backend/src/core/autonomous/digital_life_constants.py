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
