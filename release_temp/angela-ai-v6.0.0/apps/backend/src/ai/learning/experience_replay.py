import random
from collections import deque
from typing import Any, Dict, List, Tuple

class ExperienceReplayBuffer:
    """
    Stores agent experiences to enable learning from past actions.
    Supports sampling for training and analysis.
    """

    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)

    def add(self, experience: Dict[str, Any]):
        """
        Adds an experience to the buffer.
        Experience should be a dictionary containing relevant data (state, action, reward, etc.).
        """
        self.buffer.append(experience)

    def sample(self, batch_size: int) -> List[Dict[str, Any]]:
        """
        Samples a batch of experiences from the buffer.
        """
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)

    def clear(self):
        self.buffer.clear()
