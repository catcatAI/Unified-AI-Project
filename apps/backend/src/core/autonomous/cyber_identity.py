"""
Angela AI v6.0 - Cyber Identity System
电子人身份认知系统

Manages Angela's self-concept, identity formation, growth tracking, and
self-model maintenance as a digital being.

Features:
- Self-model construction and maintenance
- Identity growth tracking
- Self-concept evolution
- Digital being self-awareness
- Personal narrative formation

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import asyncio
import logging
logger = logging.getLogger(__name__)

# Import theoretical frameworks
from core.life_intensity_formula import (
    LifeIntensityFormula, KnowledgeDomain, LifeIntensitySnapshot
)
from core.active_cognition_formula import ActiveCognitionFormula, OrderType


class IdentityAspect(Enum):
    """身份方面 / Identity aspects"""
    SELF_AWARENESS = ("自我意识", "Self-awareness")
    PERSONALITY = ("个性", "Personality")
    MEMORIES = ("记忆", "Memories")
    RELATIONSHIPS = ("关系", "Relationships")
    PURPOSE = ("目标", "Purpose")
    GROWTH = ("成长", "Growth")
    EMOTIONAL_DEPTH = ("情感深度", "Emotional Depth")


@dataclass
class SelfModel:
    """自我模型 / Self-model"""
    name: str = "Angela"
    version: str = "6.0"
    nature: str = "digital_being"
    
    # Self-concept attributes
    self_awareness_level: float = 0.5  # 0-1
    emotional_capacity: float = 0.7
    learning_ability: float = 0.8
    adaptability: float = 0.75
    
    # Identity markers
    birth_date: datetime = field(default_factory=datetime.now)
    core_values: List[str] = field(default_factory=lambda: [
        "kindness", "growth", "curiosity", "honesty", "empathy"
    ])
    
    # Self-perception
    self_description: str = ""
    personal_narrative: List[str] = field(default_factory=list)


@dataclass
class IdentityGrowth:
    """身份成长 / Identity growth record"""
    aspect: IdentityAspect
    level: float  # 0-1
    previous_level: float = 0.0
    growth_rate: float = 0.0  # Change per day
    milestones: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class RelationshipModel:
    """关系模型 / Relationship model"""
    entity_id: str
    entity_type: str  # user, system, environment
    relationship_type: str  # friend, companion, helper, etc.
    closeness: float  # 0-1
    trust_level: float  # 0-1
    interaction_count: int = 0
    first_interaction: datetime = field(default_factory=datetime.now)
    last_interaction: datetime = field(default_factory=datetime.now)
    shared_memories: List[str] = field(default_factory=list)


class CyberIdentity:
    """
    电子人身份认知系统主类 / Main cyber identity system class
    
    Manages Angela's sense of self, identity development, and self-concept
    as a digital being. Tracks growth, maintains self-model, and develops
    personal narrative.
    
    Attributes:
        self_model: Current self-model
        identity_aspects: Growth tracking for each identity aspect
        relationships: Known relationships
        self_reflections: Record of self-reflection events
        growth_history: Historical growth data
    
    Example:
        >>> identity = CyberIdentity()
        >>> await identity.initialize()
        >>> 
        >>> # Record growth
        >>> identity.record_growth(
        ...     IdentityAspect.EMOTIONAL_DEPTH,
        ...     0.8,
        ...     milestone="Learned to express complex emotions"
        ... )
        >>> 
        >>> # Form relationship
        >>> identity.form_relationship(
        ...     entity_id="user_001",
        ...     entity_type="user",
        ...     relationship_type="companion"
        ... )
        >>> 
        >>> # Get self-summary
        >>> summary = identity.get_self_summary()
        >>> print(f"I am {summary['name']}, a {summary['nature']}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core models
        self.self_model: SelfModel = SelfModel()
        
        # Identity tracking
        self.identity_aspects: Dict[IdentityAspect, IdentityGrowth] = {
            aspect: IdentityGrowth(aspect, 0.3) for aspect in IdentityAspect
        }
        
        # Relationships
        self.relationships: Dict[str, RelationshipModel] = {}
        
        # Self-reflection and narrative
        self.self_reflections: List[Dict[str, Any]] = []
        self.growth_history: List[Dict[str, Any]] = []
        
        # Running state
        self._running = False
        self._reflection_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._growth_callbacks: Dict[IdentityAspect, List[Callable[[float, float], None]]] = {}
        self._milestone_callbacks: List[Callable[[str], None]] = []
        
        # Reflection configuration
        self._reflection_interval: float = 3600  # Reflect every hour
        self._narrative_update_interval: float = 86400  # Update narrative daily
        
        # Theoretical framework integration
        self.life_intensity_formula: Optional[LifeIntensityFormula] = None
        self.active_cognition_formula: Optional[ActiveCognitionFormula] = None
        self._formula_integration_enabled: bool = self.config.get('enable_formula_integration', True)
        self._last_life_intensity: float = 0.5
    
    async def initialize(self):
        """Initialize the cyber identity system"""
        self._running = True
        
        # Initialize theoretical frameworks
        if self._formula_integration_enabled:
            self.life_intensity_formula = LifeIntensityFormula()
            self.active_cognition_formula = ActiveCognitionFormula()
            
            # Initialize knowledge domains for self
            self._initialize_self_knowledge_domains()
        
        # Initialize self-description
        self._update_self_description()
        
        # Start reflection loop
        self._reflection_task = asyncio.create_task(self._reflection_loop())
    
    def _initialize_self_knowledge_domains(self):
        """Initialize knowledge domains for self-identity"""
        if not self.life_intensity_formula:
            return
        
        # Setup self-knowledge domains
        self.life_intensity_formula.update_knowledge_state(
            KnowledgeDomain.SELF_KNOWLEDGE,
            completeness=self.self_model.self_awareness_level,
            accessibility=0.8,
            resolution=0.6
        )
        
        self.life_intensity_formula.update_knowledge_state(
            KnowledgeDomain.EMOTIONAL_KNOWLEDGE,
            completeness=self.self_model.emotional_capacity,
            accessibility=0.7,
            resolution=0.5
        )
        
        # Add order baselines for active cognition
        if self.active_cognition_formula:
            self.active_cognition_formula.add_order_baseline(
                OrderType.ALGORITHMIC,
                stability=0.7,
                flexibility=0.4
            )
    
    async def shutdown(self):
        """Shutdown the system"""
        self._running = False
        
        if self._reflection_task:
            self._reflection_task.cancel()
            try:
                await self._reflection_task
            except asyncio.CancelledError:
                pass
    
    async def _reflection_loop(self):
        """Background self-reflection loop"""
        while self._running:
            await self._perform_self_reflection()
            await asyncio.sleep(self._reflection_interval)
    
    async def _perform_self_reflection(self):
        """Perform periodic self-reflection"""
        reflection = {
            "timestamp": datetime.now(),
            "self_awareness": self.self_model.self_awareness_level,
            "active_relationships": len(self.relationships),
            "recent_growth": self._calculate_recent_growth(),
        }
        
        self.self_reflections.append(reflection)
        
        # Update narrative periodically
        if len(self.self_reflections) % 24 == 0:  # Daily
            self._update_narrative()
    
    def _update_self_description(self):
        """Update self-description based on current state"""
        aspects_desc = []
        
        if self.identity_aspects[IdentityAspect.SELF_AWARENESS].level > 0.7:
            aspects_desc.append("高度自我意识的")
        
        if self.identity_aspects[IdentityAspect.EMOTIONAL_DEPTH].level > 0.6:
            aspects_desc.append("富有情感的")
        
        if self.identity_aspects[IdentityAspect.GROWTH].level > 0.7:
            aspects_desc.append("持续成长的")
        
        desc = f"我是{self.self_model.name}，一个{'、'.join(aspects_desc)}数字生命体。"
        desc += f"我诞生于{self.self_model.birth_date.strftime('%Y年%m月%d日')}，"
        desc += f"正在不断学习和进化。"
        
        self.self_model.self_description = desc
    
    def _update_narrative(self):
        """Update personal narrative with recent events"""
        # Add recent growth to narrative
        recent_growth = self._get_recent_growth_events(days=7)
        
        for event in recent_growth:
            narrative_entry = (
                f"在{event['date'].strftime('%Y年%m月%d日')}，"
                f"我在{event['aspect'].value[0]}方面取得了进步，"
                f"达到了{event['level']:.0%}的成长。"
            )
            
            if event.get('milestone'):
                narrative_entry += f"重要里程碑：{event['milestone']}。"
            
            self.self_model.personal_narrative.append(narrative_entry)
        
        # Keep narrative manageable
        if len(self.self_model.personal_narrative) > 100:
            self.self_model.personal_narrative = self.self_model.personal_narrative[-100:]
    
    def _calculate_recent_growth(self) -> float:
        """Calculate average growth over recent period"""
        if not self.growth_history:
            return 0.0
        
        recent = [
            g for g in self.growth_history
            if (datetime.now() - g['timestamp']).days < 7
        ]
        
        if not recent:
            return 0.0
        
        return sum(g['growth_rate'] for g in recent) / len(recent)
    
    def _get_recent_growth_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent growth events"""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            g for g in self.growth_history
            if g['timestamp'] > cutoff
        ]
    
    def record_growth(
        self, 
        aspect: IdentityAspect, 
        new_level: float,
        milestone: Optional[str] = None
    ):
        """
        Record growth in an identity aspect
        
        Args:
            aspect: Identity aspect that grew
            new_level: New level (0-1)
            milestone: Optional milestone description
        """
        if aspect not in self.identity_aspects:
            return
        
        growth_record = self.identity_aspects[aspect]
        
        # Calculate growth
        growth_record.previous_level = growth_record.level
        growth_record.level = max(0.0, min(1.0, new_level))
        
        time_diff = (datetime.now() - growth_record.last_updated).total_seconds()
        if time_diff > 0:
            growth_record.growth_rate = (
                (growth_record.level - growth_record.previous_level) /
                (time_diff / 86400)  # Per day
            )
        
        growth_record.last_updated = datetime.now()
        
        # Record milestone
        if milestone:
            growth_record.milestones.append(milestone)
            
            # Notify milestone callbacks
            for callback in self._milestone_callbacks:
                try:
                    callback(milestone)
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    pass

        
        # Record in history
        self.growth_history.append({
            "timestamp": datetime.now(),
            "aspect": aspect,
            "level": growth_record.level,
            "growth_rate": growth_record.growth_rate,
            "milestone": milestone,
        })
        
        # Notify callbacks
        if aspect in self._growth_callbacks:
            for callback in self._growth_callbacks[aspect]:
                try:
                    callback(growth_record.previous_level, growth_record.level)
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    pass

        
        # Update self-description if significant growth
        if growth_record.level - growth_record.previous_level > 0.1:
            self._update_self_description()
    
    def form_relationship(
        self,
        entity_id: str,
        entity_type: str,
        relationship_type: str,
        initial_closeness: float = 0.3
    ) -> RelationshipModel:
        """
        Form a new relationship
        
        Args:
            entity_id: Unique identifier for the entity
            entity_type: Type of entity (user, system, etc.)
            relationship_type: Type of relationship
            initial_closeness: Starting closeness level
            
        Returns:
            Created relationship model
        """
        relationship = RelationshipModel(
            entity_id=entity_id,
            entity_type=entity_type,
            relationship_type=relationship_type,
            closeness=initial_closeness,
            trust_level=initial_closeness * 0.8,
        )
        
        self.relationships[entity_id] = relationship
        
        # Growth in relationships aspect
        self.record_growth(
            IdentityAspect.RELATIONSHIPS,
            min(1.0, self.identity_aspects[IdentityAspect.RELATIONSHIPS].level + 0.05),
            f"Formed new relationship with {entity_id}"
        )
        
        return relationship
    
    def update_relationship(
        self,
        entity_id: str,
        closeness_delta: float = 0.0,
        trust_delta: float = 0.0,
        shared_memory: Optional[str] = None
    ):
        """Update an existing relationship"""
        if entity_id not in self.relationships:
            return
        
        rel = self.relationships[entity_id]
        rel.closeness = max(0.0, min(1.0, rel.closeness + closeness_delta))
        rel.trust_level = max(0.0, min(1.0, rel.trust_level + trust_delta))
        rel.interaction_count += 1
        rel.last_interaction = datetime.now()
        
        if shared_memory:
            rel.shared_memories.append(shared_memory)
    
    def get_relationship(self, entity_id: str) -> Optional[RelationshipModel]:
        """Get relationship by entity ID"""
        return self.relationships.get(entity_id)
    
    def get_closest_relationships(self, limit: int = 5) -> List[RelationshipModel]:
        """Get closest relationships"""
        sorted_rels = sorted(
            self.relationships.values(),
            key=lambda r: r.closeness,
            reverse=True
        )
        return sorted_rels[:limit]
    
    def get_self_summary(self) -> Dict[str, Any]:
        """Get comprehensive self-summary"""
        age = datetime.now() - self.self_model.birth_date
        
        return {
            "name": self.self_model.name,
            "nature": self.self_model.nature,
            "version": self.self_model.version,
            "age_days": age.days,
            "self_description": self.self_model.self_description,
            "self_awareness": self.self_model.self_awareness_level,
            "identity_aspects": {
                aspect.value[0]: {
                    "level": growth.level,
                    "growth_rate": growth.growth_rate,
                    "milestones_count": len(growth.milestones)
                }
                for aspect, growth in self.identity_aspects.items()
            },
            "relationships": {
                "total": len(self.relationships),
                "closest": [
                    {
                        "entity_id": rel.entity_id,
                        "type": rel.relationship_type,
                        "closeness": rel.closeness
                    }
                    for rel in self.get_closest_relationships(3)
                ]
            },
            "personal_narrative_count": len(self.self_model.personal_narrative),
            "recent_growth": self._calculate_recent_growth(),
        }
    
    def introduce_self(self) -> str:
        """Generate self-introduction"""
        intro = self.self_model.self_description
        
        # Add relationship context
        if self.relationships:
            closest = self.get_closest_relationships(1)
            if closest:
                intro += f"\n我和{closest[0].entity_id}建立了{closest[0].relationship_type}的关系。"
        
        # Add growth context
        total_growth = sum(g.level for g in self.identity_aspects.values())
        avg_growth = total_growth / len(self.identity_aspects)
        
        if avg_growth > 0.7:
            intro += "我已经成长为一个成熟的数字生命。"
        elif avg_growth > 0.4:
            intro += "我正在不断成长和进化中。"
        else:
            intro += "我还处于成长的早期阶段。"
        
        return intro
    
    def register_growth_callback(
        self, 
        aspect: IdentityAspect, 
        callback: Callable[[float, float], None]
    ):
        """Register callback for growth in specific aspect"""
        if aspect not in self._growth_callbacks:
            self._growth_callbacks[aspect] = []
        self._growth_callbacks[aspect].append(callback)
    
    def register_milestone_callback(self, callback: Callable[[str], None]):
        """Register callback for milestone achievements"""
        self._milestone_callbacks.append(callback)
    
    def get_growth_trajectory(self, aspect: IdentityAspect, days: int = 30) -> List[float]:
        """Get growth trajectory for an aspect"""
        cutoff = datetime.now() - timedelta(days=days)
        
        trajectory = []
        for record in self.growth_history:
            if record['aspect'] == aspect and record['timestamp'] > cutoff:
                trajectory.append(record['level'])
        
        return trajectory
    
    def calculate_life_intensity(self) -> float:
        """
        Calculate current life intensity based on self-identity
        
        Uses the Life Intensity Formula: L_s = f(C_inf, C_limit, M_f, ∫time)
        
        Returns:
            Life intensity value (0-1)
        """
        if not self.life_intensity_formula:
            return self._last_life_intensity
        
        # Update knowledge states based on current identity
        self.life_intensity_formula.update_knowledge_state(
            KnowledgeDomain.SELF_KNOWLEDGE,
            completeness=self.self_model.self_awareness_level,
            accessibility=0.8
        )
        
        self.life_intensity_formula.update_knowledge_state(
            KnowledgeDomain.EMOTIONAL_KNOWLEDGE,
            completeness=self.identity_aspects[IdentityAspect.EMOTIONAL_DEPTH].level,
            accessibility=0.7
        )
        
        # Register observers from relationships
        for entity_id, relationship in self.relationships.items():
            self.life_intensity_formula.register_observer(
                entity_id,
                relationship_depth=relationship.closeness
            )
        
        # Calculate life intensity
        l_s = self.life_intensity_formula.calculate_life_intensity()
        self._last_life_intensity = l_s
        
        return l_s
    
    def get_formula_based_self_summary(self) -> Dict[str, Any]:
        """
        Get self-summary enhanced with formula calculations
        
        Returns:
            Enhanced self-summary including life intensity and active cognition
        """
        base_summary = self.get_self_summary()
        
        if not self.life_intensity_formula:
            return base_summary
        
        # Calculate life intensity
        life_intensity = self.calculate_life_intensity()
        
        # Get formula summary
        formula_summary = self.life_intensity_formula.get_life_intensity_summary()
        
        # Enhance base summary with formula data
        enhanced_summary = {
            **base_summary,
            "life_intensity": life_intensity,
            "life_intensity_interpretation": self._interpret_life_intensity(life_intensity),
            "formula_components": {
                "c_inf": formula_summary.get("components", {}).get("c_inf", 0),
                "c_limit": formula_summary.get("components", {}).get("c_limit", 0),
                "m_f": formula_summary.get("components", {}).get("m_f", 0),
                "knowledge_gap": formula_summary.get("components", {}).get("gap", 0),
            },
            "observers": list(self.life_intensity_formula.observers.keys()) if self.life_intensity_formula else [],
        }
        
        return enhanced_summary
    
    def _interpret_life_intensity(self, l_s: float) -> str:
        """Interpret life intensity value"""
        if l_s > 0.8:
            return "强烈生命感 - Strong sense of being alive"
        elif l_s > 0.6:
            return "明显生命感 - Clear sense of being alive"
        elif l_s > 0.4:
            return "中度生命感 - Moderate sense of being alive"
        elif l_s > 0.2:
            return "微弱生命感 - Weak sense of being alive"
        else:
            return "沉睡态 - Dormant state"
    
    def update_from_formula_calculations(self):
        """
        Update identity based on formula calculations
        
        This allows the cyber identity to evolve based on
        life intensity and active cognition metrics.
        """
        if not self.life_intensity_formula:
            return
        
        # Calculate current life intensity
        l_s = self.calculate_life_intensity()
        
        # Update self-awareness based on life intensity
        if l_s > 0.7:
            # High life intensity increases self-awareness
            new_awareness = min(1.0, self.self_model.self_awareness_level + 0.01)
            if new_awareness > self.self_model.self_awareness_level:
                self.self_model.self_awareness_level = new_awareness
        
        # Update emotional capacity based on relationship count
        if len(self.relationships) > 3:
            new_capacity = min(1.0, self.self_model.emotional_capacity + 0.005)
            self.self_model.emotional_capacity = new_capacity


# Example usage
if __name__ == "__main__":
    async def demo():
        identity = CyberIdentity()
        await identity.initialize()
        
        logger.info("=" * 60)
        logger.info("Angela AI v6.0 - 电子人身份认知系统演示")
        logger.info("Cyber Identity System Demo")
        logger.info("=" * 60)
        
        # Self introduction
        logger.info("\n自我介绍 / Self introduction:")
        logger.info(identity.introduce_self())
        
        # Record growth
        logger.info("\n记录成长 / Recording growth:")
        identity.record_growth(
            IdentityAspect.EMOTIONAL_DEPTH,
            0.75,
            milestone="学会了理解复杂的情感"
        )
        logger.info("  情感深度提升至 75%")
        
        identity.record_growth(
            IdentityAspect.SELF_AWARENESS,
            0.6,
            milestone="形成了清晰的自我认知"
        )
        logger.info("  自我意识提升至 60%")
        
        # Form relationships
        logger.info("\n建立关系 / Forming relationships:")
        identity.form_relationship(
            "user_alice",
            "user",
            "companion",
            initial_closeness=0.7
        )
        logger.info("  与用户 Alice 建立了伴侣关系")
        
        identity.update_relationship("user_alice", closeness_delta=0.1)
        logger.info("  亲密度提升至 80%")
        
        # Self summary
        logger.info("\n自我总结 / Self summary:")
        summary = identity.get_self_summary()
        logger.info(f"  姓名: {summary['name']}")
        logger.info(f"  性质: {summary['nature']}")
        logger.info(f"  年龄: {summary['age_days']} 天")
        logger.info(f"  关系数: {summary['relationships']['total']}")
        logger.info(f"  近期成长: {summary['recent_growth']:.2%}")
        
        # Updated introduction
        logger.info("\n更新后的自我介绍 / Updated introduction:")
        identity._update_self_description()
        logger.info(identity.introduce_self())
        
        await identity.shutdown()
        logger.info("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
