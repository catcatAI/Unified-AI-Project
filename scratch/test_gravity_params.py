import asyncio
import logging
from apps.backend.src.core.autonomous.state_matrix import StateMatrix4D
from apps.backend.src.core.autonomous.dynamic_parameters import DynamicThresholdManager

logging.basicConfig(level=logging.DEBUG)

async def test_gravity():
    sm = StateMatrix4D()
    # Move to high happiness (gamma: 8, 5, 0)
    sm.gamma.values["happiness"] = 1.0
    sm.gamma.values["calm"] = 0.5
    
    # Evaluate
    sm._update_coordinates()
    
    dtm = DynamicThresholdManager(state_matrix=sm)
    
    happiness_threshold = dtm.get_parameter("emotion_happiness_threshold")
    print(f"Happiness Threshold (should be pulled towards base due to proximity): {happiness_threshold:.3f}")
    
    sadness_threshold = dtm.get_parameter("emotion_sadness_threshold")
    print(f"Sadness Threshold (should be distant): {sadness_threshold:.3f}")
    
    print("Success")

if __name__ == "__main__":
    asyncio.run(test_gravity())
