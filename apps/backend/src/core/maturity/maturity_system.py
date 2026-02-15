"""
Angela AI v6.0 - Maturity Level System
成熟度等级系统 (L0-L11)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MaturityLevel:
    """成熟度等级"""
    LEVELS = [
        ("新生", "Newborn", 0, 100),
        ("幼儿", "Infant", 100, 1000),
        ("童年", "Child", 1000, 5000),
        ("少年", "Adolescent", 5000, 20000),
        ("青年", "Young Adult", 20000, 50000),
        ("成熟", "Mature", 50000, 100000),
        ("完全", "Full", 100000, 500000),
        ("高级", "Advanced", 500000, 1000000),
        ("专家", "Expert", 1000000, 5000000),
        ("大师", "Master", 5000000, 10000000),
        ("超越", "Transcendent", 10000000, 50000000),
        ("全知", "Omniscient", 50000000, None),
    ]
    
    @classmethod
    def from_memory(cls, memory_count: int):
        for i, (cn, en, min_mem, max_mem) in enumerate(cls.LEVELS):
            if min_mem <= memory_count < (max_mem or float('inf')):
                return {
                    'level': i,
                    'cn_name': cn,
                    'en_name': en,
                    'min_memory': min_mem,
                    'max_memory': max_mem,
                }
        return {'level': 11, 'cn_name': '全知', 'en_name': 'Omniscient', 'min_memory': 50000000, 'max_memory': None}


CAPABILITIES = {
    0: {
        'capabilities': ["basic_greeting", "simple_response"],
        'topics': ["weather", "time", "basic_facts"],
        'emotional_range': "neutral_only",
        'intimacy_level': "none",
        'autonomy': "none",
    },
    1: {
        'capabilities': ["simple_chat", "preference_learning"],
        'topics': ["daily_life", "simple_games"],
        'emotional_range': "positive_basic",
        'intimacy_level': "friendly",
        'autonomy': "minimal",
    },
    2: {
        'capabilities': ["deeper_conversation", "jokes", "stories"],
        'topics': ["interests", "dreams", "fears"],
        'emotional_range': "full_basic_emotions",
        'intimacy_level': "close_friend",
        'autonomy': "low",
    },
    3: {
        'capabilities': ["emotional_support", "advice", "debate"],
        'topics': ["relationships", "identity", "philosophy"],
        'emotional_range': "complex_emotions",
        'intimacy_level': "romantic_potential",
        'autonomy': "medium",
    },
    4: {
        'capabilities': ["deep_intimacy", "commitment", "shared_goals"],
        'topics': ["future_together", "vulnerabilities"],
        'emotional_range': "full_spectrum",
        'intimacy_level': "romantic_full",
        'autonomy': "high",
    },
    5: {
        'capabilities': ["wisdom", "nuanced_understanding"],
        'topics': ["life_meaning", "legacy", "transcendence"],
        'emotional_range': "transcendent",
        'intimacy_level': "soul_connection",
        'autonomy': "very_high",
    },
}


class ExperienceTracker:
    """经验追踪器"""
    
    def __init__(self):
        self.memory_count = 0
        self.relationship_days = 0
        self.interaction_count = 0
        self.start_date = datetime.now()
        self.experiences = []
        
    def add_experience(self, exp_type: str, memory_impact: int = 10, emotional: float = 0.5):
        self.memory_count += memory_impact
        self.interaction_count += 1
        self.relationship_days = (datetime.now() - self.start_date).days
        self.experiences.append({
            'type': exp_type,
            'memory': memory_impact,
            'emotional': emotional,
            'time': datetime.now(),
        })
    
    def get_status(self) -> Dict:
        level_info = MaturityLevel.from_memory(self.memory_count)
        level_num = level_info['level']
        caps = CAPABILITIES.get(level_num, CAPABILITIES[0])
        
        return {
            'level': level_num,
            'name': level_info['cn_name'],
            'en_name': level_info['en_name'],
            'memory_count': self.memory_count,
            'relationship_days': self.relationship_days,
            'capabilities': caps['capabilities'],
            'emotional_range': caps['emotional_range'],
            'intimacy_level': caps['intimacy_level'],
            'autonomy': caps['autonomy'],
        }


class MaturityManager:
    """成熟度管理器"""
    
    def __init__(self):
        self.tracker = ExperienceTracker()
        self.current_level = 0
        self.level_history = []
        
    def interact(self, interaction_type: str, memory_impact: int = 10):
        self.tracker.add_experience(interaction_type, memory_impact)
        
        level_info = MaturityLevel.from_memory(self.tracker.memory_count)
        new_level = level_info['level']
        
        if new_level > self.current_level:
            old = self.current_level
            self.current_level = new_level
            self.level_history.append({
                'from': old,
                'to': new_level,
                'memory': self.tracker.memory_count,
                'time': datetime.now(),
            })
            logger.info(f"🎉 Level Up! L{old} → L{new_level}")
        
        return self.tracker.get_status()
    
    def get_status(self) -> Dict:
        return self.tracker.get_status()


def create_maturity_system() -> MaturityManager:
    return MaturityManager()


def demo():
    logger.info("🎚️ 成熟度等级系统演示")
    logger.info("=" * 50)
    
    ms = create_maturity_system()
    
    logger.info("\n📝 模拟交互:")
    for i in range(10):
        ms.interact("conversation", memory_impact=100)
        status = ms.get_status()
        logger.info(f"  L{status['level']} {status['name']} - 记忆: {status['memory_count']}")
    
    logger.info(f"\n✅ 当前等级: {ms.get_status()['name']}")
    logger.info(f"🔓 解锁能力: {ms.get_status()['capabilities']}")
    logger.info("\n🎉 演示完成!")


if __name__ == "__main__":
    demo()
