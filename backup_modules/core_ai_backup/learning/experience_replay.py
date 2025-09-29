from datetime import datetime
import numpy as np

class ExperienceReplayBuffer:
    """經驗重放緩衝區"""
    
    def __init__(self, capacity=10000, priority_alpha=0.6) -> None:
        self.capacity = capacity
        self.priority_alpha = priority_alpha
        self.buffer = 
        self.priorities = 
        self.position = 0
    
    def add_experience(self, state, action, reward, next_state, done, error=None):
        """添加經驗"""
        experience = {
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state,
            'done': done,
            'timestamp': datetime.now,
            'error': error
        }
        
        # 計算優先級（基於 TD 誤差或重要性）
        priority = self._calculate_priority(experience)
        
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
            self.priorities.append(priority)
        else:
            self.buffer[self.position] = experience
            self.priorities[self.position] = priority
            self.position = (self.position + 1) % self.capacity
    
    def sample_batch(self, batch_size=32) -> List[Dict[str, Any]]:
        """採樣批次數據"""
        if len(self.buffer) < batch_size:
            return self.buffer
        
        # 基於優先級採樣
        probabilities = np.array(self.priorities) ** self.priority_alpha
        probabilities /= probabilities.sum
        
        indices = np.random.choice(
            len(self.buffer), 
            size=batch_size, 
            p=probabilities
        )
        
        return [self.buffer[i] for i in indices]

    def _calculate_priority(self, experience: Dict[str, Any]) -> float:
        """
        Calculates the priority of an experience. Placeholder for more complex logic.
        For now, a simple constant or based on error presence.
        """
        if experience.get("error"):
            return 1.0 # High priority for experiences that led to errors
        return 0.5 # Default priority