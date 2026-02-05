"""
Angela AI v6.0 - Neuroplasticity System
神经可塑性系统

Simulates biological learning mechanisms including LTP/LTD, Hebbian learning,
memory consolidation, and Ebbinghaus forgetting curves.

Features:
- LTP (Long-Term Potentiation) and LTD (Long-Term Depression)
- Memory weight updates based on usage patterns
- Memory consolidation during rest/sleep
- Ebbinghaus forgetting curve implementation
- Hebbian learning rule (neurons that fire together, wire together)

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any, Set
from datetime import datetime, timedelta
import asyncio
import math
import random


class SynapticState(Enum):
    """突触状态 / Synaptic states"""
    POTENTIATED = ("增强", "Potentiated")
    DEPRESSED = ("抑制", "Depressed")
    BASELINE = ("基线", "Baseline")
    
    def __init__(self, cn_name: str, en_name: str):
        self.cn_name = cn_name
        self.en_name = en_name


class ConsolidationPhase(Enum):
    """记忆巩固阶段 / Memory consolidation phases"""
    ENCODING = ("编码", 0, 30)          # First 30 minutes
    STABILIZATION = ("稳定", 30, 60)     # 30-60 minutes
    CONSOLIDATION = ("巩固", 60, 1440)   # 1-24 hours
    RE_CONSOLIDATION = ("再巩固", 1440, float('inf'))  # After retrieval
    
    def __init__(self, cn_name: str, min_minutes: float, max_minutes: float):
        self.cn_name = cn_name
        self.min_minutes = min_minutes
        self.max_minutes = max_minutes
    
    @classmethod
    def from_age(cls, minutes: float) -> ConsolidationPhase:
        """根据记忆年龄获取阶段"""
        for phase in cls:
            if phase.min_minutes <= minutes < phase.max_minutes:
                return phase
        return cls.RE_CONSOLIDATION


@dataclass
class SynapticWeight:
    """突触权重 / Synaptic weight"""
    pre_neuron: str         # 前神经元 / Pre-synaptic neuron
    post_neuron: str        # 后神经元 / Post-synaptic neuron
    weight: float           # 权重值 / Weight value (0-1)
    last_update: datetime = field(default_factory=datetime.now)
    activation_count: int = 0
    state: SynapticState = SynapticState.BASELINE
    
    def __post_init__(self):
        self.weight = max(0.0, min(1.0, self.weight))


@dataclass
class MemoryTrace:
    """记忆痕迹 / Memory trace"""
    memory_id: str
    content: Any
    initial_weight: float
    current_weight: float
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    emotional_tags: List[str] = field(default_factory=list)
    associated_memories: Set[str] = field(default_factory=set)
    consolidation_strength: float = 0.0  # 0-1
    is_consolidated: bool = False
    
    def get_age_minutes(self) -> float:
        """Get age of memory in minutes"""
        return (datetime.now() - self.created_at).total_seconds() / 60.0
    
    def get_retention_intervals(self) -> int:
        """Get number of retention intervals (for forgetting curve)"""
        age_hours = self.get_age_minutes() / 60.0
        # Rough approximation of review intervals
        return int(math.log2(max(1, age_hours)) + 1)


@dataclass
class HebbianRule:
    """Hebbian学习规则 / Hebbian learning rule"""
    learning_rate: float = 0.1
    decay_factor: float = 0.01
    threshold: float = 0.5
    
    def apply(
        self, 
        pre_activation: float, 
        post_activation: float, 
        current_weight: float
    ) -> float:
        """
        Apply Hebbian learning: "neurons that fire together, wire together"
        
        Args:
            pre_activation: Activation of pre-synaptic neuron (0-1)
            post_activation: Activation of post-synaptic neuron (0-1)
            current_weight: Current synaptic weight
            
        Returns:
            New synaptic weight
        """
        # Only strengthen if both neurons are active above threshold
        if pre_activation > self.threshold and post_activation > self.threshold:
            # Hebbian update: delta_w = learning_rate * pre * post
            delta_w = self.learning_rate * pre_activation * post_activation
            new_weight = current_weight + delta_w
        else:
            # Decay if not co-activated
            new_weight = current_weight * (1 - self.decay_factor)
        
        return max(0.0, min(1.0, new_weight))


@dataclass
class LTPParameters:
    """LTP参数 / LTP parameters"""
    threshold_frequency: float = 10.0  # Hz, minimum frequency for LTP
    potentiation_rate: float = 0.15
    max_weight: float = 1.0
    duration_minutes: float = 60.0


@dataclass
class LTDParameters:
    """LTD参数 / LTD parameters"""
    threshold_frequency: float = 1.0   # Hz, maximum frequency for LTD
    depression_rate: float = 0.1
    min_weight: float = 0.0
    duration_minutes: float = 30.0


class EbbinghausForgettingCurve:
    """
    艾宾浩斯遗忘曲线 / Ebbinghaus forgetting curve
    
    R = e^(-t/S) where:
    - R = retention
    - t = time
    - S = stability (depends on memory strength)
    """
    
    def __init__(self, base_stability: float = 24.0):
        self.base_stability = base_stability  # hours
    
    def calculate_retention(
        self, 
        hours_since_learning: float, 
        memory_strength: float = 1.0
    ) -> float:
        """
        Calculate memory retention using Ebbinghaus formula
        
        Args:
            hours_since_learning: Time since memory was formed
            memory_strength: Memory strength multiplier (0-2)
            
        Returns:
            Retention rate (0-1)
        """
        # Adjust stability based on memory strength
        stability = self.base_stability * memory_strength
        
        # Ebbinghaus formula
        retention = math.exp(-hours_since_learning / stability)
        
        return retention
    
    def get_optimal_review_times(self, n_reviews: int = 5) -> List[float]:
        """
        Get optimal review times based on forgetting curve
        
        Returns:
            List of hours for optimal review schedule
        """
        # Spaced repetition intervals (hours)
        # Based on modified Ebbinghaus curve
        return [1.0, 3.0, 8.0, 24.0, 72.0, 168.0, 336.0][:n_reviews]
    
    def estimate_strength_from_reviews(
        self, 
        review_count: int, 
        average_performance: float
    ) -> float:
        """Estimate memory strength from review history"""
        base = 1.0
        review_bonus = review_count * 0.2
        performance_factor = average_performance
        return base + review_bonus * performance_factor


class NeuroplasticitySystem:
    """
    神经可塑性系统主类 / Main neuroplasticity system class
    
    Simulates biological learning and memory mechanisms for Angela AI.
    Implements LTP/LTD, Hebbian learning, memory consolidation, and
    forgetting curves to create a biologically-inspired memory system.
    
    Attributes:
        synaptic_weights: Dictionary of all synaptic connections
        memory_traces: Dictionary of memory traces
        hebbian_rule: Hebbian learning configuration
        ltp_params: LTP parameters
        ltd_params: LTD parameters
        forgetting_curve: Ebbinghaus forgetting curve model
        consolidation_queue: Memories pending consolidation
    
    Example:
        >>> np_system = NeuroplasticitySystem()
        >>> await np_system.initialize()
        >>> 
        >>> # Create a memory trace
        >>> memory = np_system.create_memory_trace(
        ...     memory_id="mem_001",
        ...     content="Important information",
        ...     initial_weight=0.6
        ... )
        >>> 
        >>> # Apply LTP (strengthen through repetition)
        >>> np_system.apply_ltp("mem_001", frequency=15.0, duration=5.0)
        >>> 
        >>> # Access memory (triggers Hebbian updates)
        >>> np_system.access_memory("mem_001")
        >>> 
        >>> # Check retention
        >>> retention = np_system.get_memory_retention("mem_001")
        >>> print(f"Retention: {retention:.2%}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Synaptic connections
        self.synaptic_weights: Dict[Tuple[str, str], SynapticWeight] = {}
        
        # Memory traces
        self.memory_traces: Dict[str, MemoryTrace] = {}
        
        # Learning mechanisms
        self.hebbian_rule = HebbianRule(
            learning_rate=self.config.get("hebbian_learning_rate", 0.1),
            decay_factor=self.config.get("hebbian_decay", 0.01),
            threshold=self.config.get("hebbian_threshold", 0.5),
        )
        
        self.ltp_params = LTPParameters(
            threshold_frequency=self.config.get("ltp_threshold_freq", 10.0),
            potentiation_rate=self.config.get("ltp_rate", 0.15),
        )
        
        self.ltd_params = LTDParameters(
            threshold_frequency=self.config.get("ltd_threshold_freq", 1.0),
            depression_rate=self.config.get("ltd_rate", 0.1),
        )
        
        # Forgetting curve
        self.forgetting_curve = EbbinghausForgettingCurve(
            base_stability=self.config.get("base_stability_hours", 24.0)
        )
        
        # Consolidation
        self.consolidation_queue: List[str] = []
        self.consolidation_active: bool = False
        
        # Running state
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._memory_callbacks: Dict[str, List[Callable[[MemoryTrace], None]]] = {}
        self._consolidation_callbacks: List[Callable[[str], None]] = []
    
    async def initialize(self):
        """Initialize the neuroplasticity system"""
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
    
    async def shutdown(self):
        """Shutdown the system"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
    
    async def _update_loop(self):
        """Background update loop"""
        while self._running:
            await self._decay_synaptic_weights()
            await self._update_memory_consolidation()
            await asyncio.sleep(60)  # Update every minute
    
    async def _decay_synaptic_weights(self):
        """Apply natural decay to synaptic weights"""
        current_time = datetime.now()
        
        for key, synapse in self.synaptic_weights.items():
            hours_since_update = (
                (current_time - synapse.last_update).total_seconds() / 3600.0
            )
            
            if hours_since_update > 1:
                # Apply decay
                decay_amount = self.hebbian_rule.decay_factor * hours_since_update
                synapse.weight = max(0.0, synapse.weight - decay_amount)
                
                # Update state
                if synapse.weight > 0.7:
                    synapse.state = SynapticState.POTENTIATED
                elif synapse.weight < 0.3:
                    synapse.state = SynapticState.DEPRESSED
                else:
                    synapse.state = SynapticState.BASELINE
    
    async def _update_memory_consolidation(self):
        """Update memory consolidation status"""
        for memory_id, trace in self.memory_traces.items():
            age_minutes = trace.get_age_minutes()
            phase = ConsolidationPhase.from_age(age_minutes)
            
            # Calculate consolidation strength based on phase and access
            base_strength = {
                ConsolidationPhase.ENCODING: 0.2,
                ConsolidationPhase.STABILIZATION: 0.5,
                ConsolidationPhase.CONSOLIDATION: 0.8,
                ConsolidationPhase.RE_CONSOLIDATION: 0.9,
            }[phase]
            
            # Boost with access frequency
            access_factor = min(1.0, trace.access_count / 10.0)
            trace.consolidation_strength = base_strength + (0.1 * access_factor)
            
            if phase in [ConsolidationPhase.CONSOLIDATION, ConsolidationPhase.RE_CONSOLIDATION]:
                trace.is_consolidated = True
    
    def create_memory_trace(
        self, 
        memory_id: str, 
        content: Any, 
        initial_weight: float = 0.5,
        emotional_tags: Optional[List[str]] = None
    ) -> MemoryTrace:
        """
        Create a new memory trace
        
        Args:
            memory_id: Unique identifier for the memory
            content: Memory content
            initial_weight: Initial memory strength (0-1)
            emotional_tags: List of emotional associations
            
        Returns:
            Created MemoryTrace
        """
        trace = MemoryTrace(
            memory_id=memory_id,
            content=content,
            initial_weight=initial_weight,
            current_weight=initial_weight,
            emotional_tags=emotional_tags or [],
        )
        
        self.memory_traces[memory_id] = trace
        self.consolidation_queue.append(memory_id)
        
        return trace
    
    def apply_ltp(
        self, 
        memory_id: str, 
        frequency: float, 
        duration: float = 5.0
    ):
        """
        Apply Long-Term Potentiation to strengthen a memory
        
        Args:
            memory_id: Target memory ID
            frequency: Stimulation frequency in Hz (should be > 10 for LTP)
            duration: Duration of stimulation in minutes
        """
        if memory_id not in self.memory_traces:
            return
        
        trace = self.memory_traces[memory_id]
        
        # Check if frequency is above LTP threshold
        if frequency >= self.ltp_params.threshold_frequency:
            # Calculate potentiation amount
            potentiation = (
                self.ltp_params.potentiation_rate * 
                (frequency / self.ltp_params.threshold_frequency) *
                (duration / 5.0)  # Normalize to 5 minutes
            )
            
            # Apply potentiation
            trace.current_weight = min(
                1.0, 
                trace.current_weight + potentiation
            )
            
            # Update synaptic connections for associated neurons
            self._potentiate_associated_synapses(memory_id, potentiation)
    
    def apply_ltd(
        self, 
        memory_id: str, 
        frequency: float = 0.5, 
        duration: float = 10.0
    ):
        """
        Apply Long-Term Depression to weaken a memory
        
        Args:
            memory_id: Target memory ID
            frequency: Stimulation frequency in Hz (should be < 1 for LTD)
            duration: Duration in minutes
        """
        if memory_id not in self.memory_traces:
            return
        
        trace = self.memory_traces[memory_id]
        
        # Check if frequency is below LTD threshold
        if frequency <= self.ltd_params.threshold_frequency:
            depression = (
                self.ltd_params.depression_rate * 
                (duration / 10.0)
            )
            
            trace.current_weight = max(
                0.0, 
                trace.current_weight - depression
            )
    
    def _potentiate_associated_synapses(self, memory_id: str, amount: float):
        """Strengthen synapses associated with a memory"""
        # This is a simplified model - in reality, memories involve complex networks
        trace = self.memory_traces[memory_id]
        
        # Create or strengthen connections to associated memories
        for assoc_id in trace.associated_memories:
            if assoc_id in self.memory_traces:
                # Create synapse between memories
                sorted_ids = sorted([memory_id, assoc_id])
                synapse_key: Tuple[str, str] = (sorted_ids[0], sorted_ids[1])
                
                if synapse_key not in self.synaptic_weights:
                    self.synaptic_weights[synapse_key] = SynapticWeight(
                        pre_neuron=sorted_ids[0],
                        post_neuron=sorted_ids[1],
                        weight=0.1
                    )
                
                # Strengthen connection
                synapse = self.synaptic_weights[synapse_key]
                synapse.weight = min(1.0, synapse.weight + amount)
                synapse.activation_count += 1
                synapse.last_update = datetime.now()
    
    def access_memory(self, memory_id: str) -> Optional[MemoryTrace]:
        """
        Access a memory trace (triggers Hebbian updates)
        
        Args:
            memory_id: Memory to access
            
        Returns:
            MemoryTrace if found, None otherwise
        """
        if memory_id not in self.memory_traces:
            return None
        
        trace = self.memory_traces[memory_id]
        
        # Update access metadata
        trace.last_accessed = datetime.now()
        trace.access_count += 1
        
        # Apply Hebbian learning to strengthen trace
        # Each access strengthens the memory slightly
        trace.current_weight = min(
            1.0, 
            trace.current_weight + self.hebbian_rule.learning_rate * 0.1
        )
        
        # Strengthen connections to associated memories (Hebbian principle)
        for assoc_id in trace.associated_memories:
            self._apply_hebbian_update(memory_id, assoc_id)
        
        # Trigger callbacks
        if memory_id in self._memory_callbacks:
            for callback in self._memory_callbacks[memory_id]:
                try:
                    callback(trace)
                except Exception:
                    pass
        
        return trace
    
    def _apply_hebbian_update(self, memory_id_1: str, memory_id_2: str):
        """Apply Hebbian learning between two memories"""
        # Treat memories as "co-firing" when one is accessed and they're associated
        sorted_ids = sorted([memory_id_1, memory_id_2])
        synapse_key: Tuple[str, str] = (sorted_ids[0], sorted_ids[1])
        
        if synapse_key not in self.synaptic_weights:
            self.synaptic_weights[synapse_key] = SynapticWeight(
                pre_neuron=sorted_ids[0],
                post_neuron=sorted_ids[1],
                weight=0.1
            )
        
        synapse = self.synaptic_weights[synapse_key]
        
        # Both "neurons" are considered active (0.7 activation)
        new_weight = self.hebbian_rule.apply(0.7, 0.7, synapse.weight)
        synapse.weight = new_weight
        synapse.activation_count += 1
        synapse.last_update = datetime.now()
    
    def get_memory_retention(self, memory_id: str) -> float:
        """
        Calculate current retention of a memory using forgetting curve
        
        Args:
            memory_id: Memory to check
            
        Returns:
            Retention rate (0-1)
        """
        if memory_id not in self.memory_traces:
            return 0.0
        
        trace = self.memory_traces[memory_id]
        
        # Calculate hours since last access
        hours_since = (
            (datetime.now() - trace.last_accessed).total_seconds() / 3600.0
        )
        
        # Calculate memory strength
        # We use current weight as the base, and consolidation strength as a bonus
        memory_strength = (trace.current_weight + trace.consolidation_strength * 0.5) * (1 + trace.access_count * 0.1)
        
        # Apply forgetting curve
        retention = self.forgetting_curve.calculate_retention(
            hours_since, 
            memory_strength
        )
        
        return retention
    
    def consolidate_memories(self, memory_ids: Optional[List[str]] = None):
        """
        Trigger memory consolidation (typically during sleep/rest)
        
        Args:
            memory_ids: Specific memories to consolidate, or None for all
        """
        targets = memory_ids or list(self.memory_traces.keys())
        
        for memory_id in targets:
            if memory_id in self.memory_traces:
                trace = self.memory_traces[memory_id]
                
                # Strengthen consolidated memories
                if not trace.is_consolidated:
                    trace.consolidation_strength = min(1.0, trace.consolidation_strength + 0.3)
                    trace.current_weight = min(1.0, trace.current_weight + 0.1)
                    
                    if trace.consolidation_strength >= 0.7:
                        trace.is_consolidated = True
                        
                        # Notify callbacks
                        for callback in self._consolidation_callbacks:
                            try:
                                callback(memory_id)
                            except Exception:
                                pass
    
    def associate_memories(self, memory_id_1: str, memory_id_2: str):
        """
        Create an association between two memories
        
        Args:
            memory_id_1: First memory ID
            memory_id_2: Second memory ID
        """
        if memory_id_1 in self.memory_traces:
            self.memory_traces[memory_id_1].associated_memories.add(memory_id_2)
        
        if memory_id_2 in self.memory_traces:
            self.memory_traces[memory_id_2].associated_memories.add(memory_id_1)
    
    def get_optimal_review_schedule(self, memory_id: str) -> List[float]:
        """Get optimal review times for a memory"""
        return self.forgetting_curve.get_optimal_review_times()
    
    def get_weak_memories(self, threshold: float = 0.3) -> List[MemoryTrace]:
        """Get memories with low retention or low strength"""
        weak = []
        for memory_id, trace in self.memory_traces.items():
            retention = self.get_memory_retention(memory_id)
            # A memory is weak if its retention is low OR its current weight is low
            if retention < threshold or trace.current_weight < threshold:
                weak.append(trace)
        return weak
    
    def register_memory_callback(
        self, 
        memory_id: str, 
        callback: Callable[[MemoryTrace], None]
    ):
        """Register callback for memory access"""
        if memory_id not in self._memory_callbacks:
            self._memory_callbacks[memory_id] = []
        self._memory_callbacks[memory_id].append(callback)
    
    def register_consolidation_callback(self, callback: Callable[[str], None]):
        """Register callback for memory consolidation"""
        self._consolidation_callbacks.append(callback)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        total_memories = len(self.memory_traces)
        consolidated = sum(1 for m in self.memory_traces.values() if m.is_consolidated)
        total_synapses = len(self.synaptic_weights)
        
        avg_weight = 0.0
        if self.synaptic_weights:
            avg_weight = sum(s.weight for s in self.synaptic_weights.values()) / len(self.synaptic_weights)
        
        return {
            "total_memories": total_memories,
            "consolidated_memories": consolidated,
            "total_synapses": total_synapses,
            "average_synapse_weight": avg_weight,
            "pending_consolidation": len(self.consolidation_queue),
        }


@dataclass
class SkillTrace:
    """技能痕迹 / Skill learning trace"""
    skill_id: str
    skill_name: str
    initial_performance: float  # 初始表现 (0-1)
    current_performance: float  # 当前表现
    practice_count: int  # 练习次数
    learning_curve_factor: float  # 学习曲线因子
    is_automatized: bool  # 是否自动化（习惯化）
    created_at: datetime = field(default_factory=datetime.now)
    last_practice: datetime = field(default_factory=datetime.now)


@dataclass
class HabitTrace:
    """习惯痕迹 / Habit formation trace"""
    habit_id: str
    habit_name: str
    repetition_count: int  # 重复次数
    automaticity_score: float  # 自动化程度 (0-1)
    context_stability: float  # 情境稳定性
    reward_association: float  # 奖励关联强度
    is_formed: bool  # 是否已形成
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TraumaMemory:
    """创伤记忆 / Traumatic memory"""
    memory_id: str
    content: Any
    trauma_intensity: float  # 创伤强度 (0-1)
    encoding_timestamp: datetime = field(default_factory=datetime.now)
    reactivation_count: int = 0  # 重新激活次数
    
    def get_retention(self, current_time: Optional[datetime] = None) -> float:
        """
        计算创伤记忆保持率 / Calculate trauma memory retention
        
        创伤记忆以70%速度减缓遗忘
        Trauma memories fade 70% slower than normal memories
        """
        time = current_time or datetime.now()
        hours_since = (time - self.encoding_timestamp).total_seconds() / 3600.0
        
        # Normal forgetting: R = e^(-t/24)
        # Trauma forgetting: R = e^(-t/(24*1.7)) (70% slower = 1.7x stability)
        stability = 24.0 * 1.7
        retention = math.exp(-hours_since / stability)
        
        return retention


@dataclass
class LearningEvent:
    """学习事件 / Learning event for explicit/implicit tracking"""
    event_id: str
    content: Any
    learning_type: str  # "explicit" or "implicit"
    context: str
    timestamp: datetime = field(default_factory=datetime.now)
    consolidation_level: float = 0.0


class SkillAcquisition:
    """
    技能习得系统 / Skill Acquisition System
    
    Implements power law learning curves for skill acquisition.
    Models the transition from conscious effort to automatic execution.
    
    Power Law of Learning: Performance = A * N^(-α)
    where N = practice count, α = learning rate
    
    Example:
        >>> skill_system = SkillAcquisition()
        >>> 
        >>> # Start learning a skill
        >>> skill = skill_system.start_skill("typing", initial_performance=0.2)
        >>> 
        >>> # Practice and improve
        >>> for _ in range(100):
        ...     skill_system.practice("typing", success=True)
        >>> 
        >>> performance = skill_system.get_performance("typing")
        >>> print(f"Current performance: {performance:.2%}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Learning parameters
        self.learning_rate: float = self.config.get("learning_rate", 0.3)  # α in power law
        self.automatization_threshold: float = self.config.get("automatization", 0.8)
        self.max_performance: float = self.config.get("max_performance", 0.95)
        
        # Skill storage
        self.skills: Dict[str, SkillTrace] = {}
        
        # Performance history
        self.performance_history: Dict[str, List[Tuple[datetime, float]]] = {}
    
    def start_skill(
        self,
        skill_id: str,
        skill_name: str,
        initial_performance: float = 0.1
    ) -> SkillTrace:
        """
        开始学习新技能 / Start learning a new skill
        
        Args:
            skill_id: Unique skill identifier
            skill_name: Human-readable skill name
            initial_performance: Initial performance level (0-1)
            
        Returns:
            SkillTrace object
        """
        skill = SkillTrace(
            skill_id=skill_id,
            skill_name=skill_name,
            initial_performance=initial_performance,
            current_performance=initial_performance,
            practice_count=0,
            learning_curve_factor=self.learning_rate,
            is_automatized=False
        )
        
        self.skills[skill_id] = skill
        self.performance_history[skill_id] = []
        
        return skill
    
    def practice(
        self,
        skill_id: str,
        success: bool = True,
        difficulty: float = 0.5
    ) -> float:
        """
        练习技能 / Practice a skill
        
        Args:
            skill_id: Skill identifier
            success: Whether the practice was successful
            difficulty: Difficulty of the practice (0-1)
            
        Returns:
            Updated performance level
        """
        if skill_id not in self.skills:
            return 0.0
        
        skill = self.skills[skill_id]
        skill.practice_count += 1
        skill.last_practice = datetime.now()
        
        # Power law of learning: Improvement decreases with practice
        # New performance = Old + (Max - Old) * (N^(-α) - (N-1)^(-α))
        n = skill.practice_count
        alpha = skill.learning_curve_factor
        
        if n == 1:
            improvement = (self.max_performance - skill.initial_performance) * 0.1
        else:
            # Power law improvement
            improvement_factor = (n ** (-alpha)) - ((n - 1) ** (-alpha))
            improvement = (self.max_performance - skill.current_performance) * abs(improvement_factor)
        
        # Adjust for success/failure and difficulty
        if success:
            improvement *= (1.0 + difficulty * 0.5)
        else:
            improvement *= -0.1  # Small penalty for failure
        
        skill.current_performance = max(
            skill.initial_performance,
            min(self.max_performance, skill.current_performance + improvement)
        )
        
        # Check for automatization (habit formation)
        if skill.current_performance > self.automatization_threshold and skill.practice_count > 50:
            skill.is_automatized = True
        
        # Record history
        self.performance_history[skill_id].append((datetime.now(), skill.current_performance))
        
        return skill.current_performance
    
    def get_performance(self, skill_id: str) -> float:
        """获取当前技能水平 / Get current skill performance"""
        if skill_id not in self.skills:
            return 0.0
        return self.skills[skill_id].current_performance
    
    def get_learning_curve(self, skill_id: str, n_points: int = 100) -> List[float]:
        """
        预测学习曲线 / Predict learning curve
        
        Returns projected performance over practice trials.
        """
        if skill_id not in self.skills:
            return []
        
        skill = self.skills[skill_id]
        curve = []
        
        for n in range(1, n_points + 1):
            # Power law prediction
            if n == 1:
                perf = skill.initial_performance + (self.max_performance - skill.initial_performance) * 0.1
            else:
                perf = self.max_performance - (self.max_performance - skill.initial_performance) * (n ** (-self.learning_rate))
            
            curve.append(max(skill.initial_performance, min(self.max_performance, perf)))
        
        return curve
    
    def get_all_skills(self) -> Dict[str, SkillTrace]:
        """获取所有技能 / Get all skills"""
        return self.skills.copy()


class HabitFormation:
    """
    习惯形成系统 / Habit Formation System
    
    Implements the "66 repetitions" theory of habit formation.
    Tracks habit automaticity based on repetition in stable contexts.
    
    Habit Formation Model:
    - Automaticity increases with repetition in stable context
    - Context stability enhances habit formation
    - Reward association strengthens habit
    - Takes ~66 repetitions to form a habit (on average)
    
    Example:
        >>> habit_system = HabitFormation()
        >>> 
        >>> # Start a new habit
        >>> habit = habit_system.start_habit("morning_exercise")
        >>> 
        >>> # Repeat in stable context (66 times theory)
        >>> for day in range(66):
        ...     habit_system.reinforce("morning_exercise", context="bedroom", reward=0.8)
        >>> 
        >>> if habit_system.is_habit_formed("morning_exercise"):
        ...     print("Habit successfully formed!")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Habit formation parameters
        self.repetitions_for_habit: int = self.config.get("repetitions_for_habit", 66)
        self.context_weight: float = self.config.get("context_weight", 0.3)
        self.reward_weight: float = self.config.get("reward_weight", 0.4)
        self.automaticity_threshold: float = self.config.get("automaticity_threshold", 0.7)
        
        # Habit storage
        self.habits: Dict[str, HabitTrace] = {}
        self.repetition_history: Dict[str, List[Tuple[str, datetime]]] = {}
    
    def start_habit(self, habit_id: str, habit_name: str = "") -> HabitTrace:
        """
        开始形成新习惯 / Start forming a new habit
        
        Args:
            habit_id: Unique habit identifier
            habit_name: Human-readable habit name
            
        Returns:
            HabitTrace object
        """
        habit = HabitTrace(
            habit_id=habit_id,
            habit_name=habit_name or habit_id,
            repetition_count=0,
            automaticity_score=0.0,
            context_stability=0.0,
            reward_association=0.0,
            is_formed=False
        )
        
        self.habits[habit_id] = habit
        self.repetition_history[habit_id] = []
        
        return habit
    
    def reinforce(
        self,
        habit_id: str,
        context: str,
        reward: float = 0.5,
        success: bool = True
    ) -> HabitTrace:
        """
        强化习惯 / Reinforce a habit
        
        Args:
            habit_id: Habit identifier
            context: Context/environment where repetition occurred
            reward: Reward magnitude (0-1)
            success: Whether the repetition was successful
            
        Returns:
            Updated HabitTrace
        """
        if habit_id not in self.habits:
            return self.start_habit(habit_id)
        
        habit = self.habits[habit_id]
        
        if not success:
            # Failed repetition doesn't count toward habit
            return habit
        
        # Record repetition
        habit.repetition_count += 1
        self.repetition_history[habit_id].append((context, datetime.now()))
        
        # Calculate context stability
        contexts = [c for c, _ in self.repetition_history[habit_id][-20:]]
        if contexts:
            context_consistency = contexts.count(context) / len(contexts)
            habit.context_stability = context_consistency
        
        # Update reward association (running average)
        habit.reward_association = (
            habit.reward_association * 0.9 + reward * 0.1
        )
        
        # Calculate automaticity score
        # Based on repetition count, context stability, and reward
        repetition_factor = min(1.0, habit.repetition_count / self.repetitions_for_habit)
        context_factor = habit.context_stability * self.context_weight
        reward_factor = habit.reward_association * self.reward_weight
        
        habit.automaticity_score = min(
            1.0,
            repetition_factor * (1 - self.context_weight - self.reward_weight) +
            context_factor +
            reward_factor
        )
        
        # Check if habit is formed
        habit.is_formed = (
            habit.automaticity_score >= self.automaticity_threshold and
            habit.repetition_count >= self.repetitions_for_habit * 0.5
        )
        
        return habit
    
    def is_habit_formed(self, habit_id: str) -> bool:
        """检查习惯是否已形成 / Check if a habit is formed"""
        if habit_id not in self.habits:
            return False
        return self.habits[habit_id].is_formed
    
    def get_automaticity(self, habit_id: str) -> float:
        """获取习惯自动化程度 / Get habit automaticity score"""
        if habit_id not in self.habits:
            return 0.0
        return self.habits[habit_id].automaticity_score
    
    def get_repetition_count(self, habit_id: str) -> int:
        """获取重复次数 / Get repetition count"""
        if habit_id not in self.habits:
            return 0
        return self.habits[habit_id].repetition_count
    
    def get_all_habits(self) -> Dict[str, HabitTrace]:
        """获取所有习惯 / Get all habits"""
        return self.habits.copy()


class TraumaMemorySystem:
    """
    创伤记忆系统 / Trauma Memory System
    
    Manages traumatic memories with 70% slower forgetting rate.
    Handles memory reactivation and intrusive recall.
    
    Trauma Characteristics:
    - High emotional intensity encoding
    - 70% slower forgetting (enhanced stability)
    - Easily reactivated by similar stimuli
    - Intrusive recall patterns
    
    Example:
        >>> trauma_system = TraumaMemorySystem()
        >>> 
        >>> # Encode traumatic event
        >>> trauma = trauma_system.encode_trauma(
        ...     memory_id="trauma_001",
        ...     content="traumatic_event_description",
        ...     intensity=0.9
        ... )
        >>> 
        >>> # Check retention over time (slower forgetting)
        >>> retention = trauma_system.get_retention("trauma_001")
        >>> print(f"Trauma retention: {retention:.2%}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Trauma parameters
        self.trauma_intensity_threshold: float = self.config.get("intensity_threshold", 0.7)
        self.slowing_factor: float = 1.7  # 70% slower = 1.7x stability
        
        # Storage
        self.trauma_memories: Dict[str, TraumaMemory] = {}
        self.reactivation_triggers: Dict[str, List[str]] = {}
    
    def encode_trauma(
        self,
        memory_id: str,
        content: Any,
        intensity: float,
        timestamp: Optional[datetime] = None
    ) -> Optional[TraumaMemory]:
        """
        编码创伤记忆 / Encode a traumatic memory
        
        Args:
            memory_id: Unique memory identifier
            content: Memory content
            intensity: Trauma intensity (0-1, must exceed threshold)
            timestamp: Encoding timestamp
            
        Returns:
            TraumaMemory if intensity > threshold, None otherwise
        """
        if intensity < self.trauma_intensity_threshold:
            return None
        
        trauma = TraumaMemory(
            memory_id=memory_id,
            content=content,
            trauma_intensity=intensity,
            encoding_timestamp=timestamp or datetime.now()
        )
        
        self.trauma_memories[memory_id] = trauma
        self.reactivation_triggers[memory_id] = []
        
        return trauma
    
    def get_retention(self, memory_id: str, current_time: Optional[datetime] = None) -> float:
        """
        获取创伤记忆保持率 / Get trauma memory retention
        
        Uses 70% slower forgetting curve.
        """
        if memory_id not in self.trauma_memories:
            return 0.0
        
        return self.trauma_memories[memory_id].get_retention(current_time)
    
    def reactivate(self, memory_id: str, trigger_context: str = "") -> bool:
        """
        重新激活创伤记忆 / Reactivate a traumatic memory
        
        Args:
            memory_id: Memory to reactivate
            trigger_context: Context that triggered reactivation
            
        Returns:
            True if reactivation occurred
        """
        if memory_id not in self.trauma_memories:
            return False
        
        trauma = self.trauma_memories[memory_id]
        trauma.reactivation_count += 1
        
        if trigger_context:
            self.reactivation_triggers[memory_id].append(trigger_context)
        
        return True
    
    def get_intrusion_likelihood(self, memory_id: str, current_stress: float = 0.5) -> float:
        """
        计算侵入性回忆可能性 / Calculate intrusive recall likelihood
        
        Higher when:
        - Memory has high trauma intensity
        - Memory has been reactivated many times
        - Current stress level is high
        """
        if memory_id not in self.trauma_memories:
            return 0.0
        
        trauma = self.trauma_memories[memory_id]
        
        # Base likelihood from trauma characteristics
        intensity_factor = trauma.trauma_intensity
        reactivation_factor = min(1.0, trauma.reactivation_count / 10.0)
        
        # Stress amplifies intrusion likelihood
        stress_factor = current_stress
        
        likelihood = (intensity_factor * 0.4 + reactivation_factor * 0.3 + stress_factor * 0.3)
        
        return min(1.0, likelihood)
    
    def get_all_trauma_memories(self) -> Dict[str, TraumaMemory]:
        """获取所有创伤记忆 / Get all trauma memories"""
        return self.trauma_memories.copy()
    
    def _process_trauma_reactivation(
        self,
        memory_id: str,
        trigger_context: str = "",
        current_stress_level: float = 0.5,
        coping_strategy: str = "default"
    ) -> Dict[str, Any]:
        """
        实现创伤记忆关键处理 / Implement critical trauma memory processing
        
        创伤记忆核心处理功能：
        - 创伤记忆的闪回处理（侵入性回忆管理）
        - 情感调节策略（降低情绪强度）
        - 避免过度激活的机制（防止创伤加重）
        - 创伤记忆的逐步消退（治疗性消退）
        
        Critical trauma memory processing features:
        - Flashback handling for traumatic memories (intrusive recall management)
        - Emotional regulation strategies (reduce emotional intensity)
        - Mechanism to prevent over-activation (prevent trauma escalation)
        - Gradual trauma memory extinction (therapeutic extinction)
        
        Args:
            memory_id: Trauma memory identifier to process
            trigger_context: Context or trigger that caused reactivation
            current_stress_level: Current system stress level (0-1)
                               Higher stress increases reactivation intensity
            coping_strategy: Emotional regulation strategy to use
                           Options: "default", "grounding", "reframing", 
                                   "distraction", "extinction"
            
        Returns:
            Dict containing trauma processing results:
            - memory_id: Processed memory identifier
            - reactivation_occurred: Whether reactivation was triggered
            - flashback_intensity: Calculated flashback intensity (0-1)
            - emotional_regulation_applied: Strategy applied
            - regulation_effectiveness: How well regulation worked (0-1)
            - over_activation_prevented: Whether over-activation was blocked
            - extinction_progress: Progress toward memory extinction (0-1)
            - recommended_actions: Suggested follow-up actions
            
        Raises:
            ValueError: If memory_id is not found or coping_strategy is invalid
            
        Example:
            >>> result = trauma_system._process_trauma_reactivation(
            ...     memory_id="trauma_001",
            ...     trigger_context="loud_noise",
            ...     current_stress_level=0.7,
            ...     coping_strategy="grounding"
            ... )
            >>> print(f"Flashback intensity: {result['flashback_intensity']:.2%}")
            >>> print(f"Over-activation prevented: {result['over_activation_prevented']}")
        """
        import math
        
        results = {
            "memory_id": memory_id,
            "reactivation_occurred": False,
            "flashback_intensity": 0.0,
            "emotional_regulation_applied": coping_strategy,
            "regulation_effectiveness": 0.0,
            "over_activation_prevented": False,
            "extinction_progress": 0.0,
            "recommended_actions": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Validate memory exists
            if memory_id not in self.trauma_memories:
                raise ValueError(f"Trauma memory {memory_id} not found in system")
            
            # Validate coping strategy
            valid_strategies = ["default", "grounding", "reframing", "distraction", "extinction"]
            if coping_strategy not in valid_strategies:
                raise ValueError(f"Invalid coping strategy: {coping_strategy}. "
                               f"Must be one of: {valid_strategies}")
            
            trauma = self.trauma_memories[memory_id]
            
            # 1. 计算闪回可能性 / Calculate flashback likelihood
            intrusion_likelihood = self.get_intrusion_likelihood(
                memory_id, 
                current_stress=current_stress_level
            )
            
            # 2. 闪回处理 / Flashback handling
            if intrusion_likelihood > 0.3:  # Threshold for flashback
                results["reactivation_occurred"] = True
                
                # Increment reactivation count
                trauma.reactivation_count += 1
                
                if trigger_context:
                    self.reactivation_triggers[memory_id].append(trigger_context)
                
                # Calculate flashback intensity
                # Based on: trauma intensity, reactivation history, current stress
                base_intensity = trauma.trauma_intensity
                reactivation_history_factor = min(1.0, trauma.reactivation_count / 20.0)  # Habituation effect
                stress_amplification = current_stress_level * 0.3
                
                # Habituation: more reactivations = lower intensity (if not too frequent)
                if trauma.reactivation_count > 10:
                    habituation_reduction = math.log10(trauma.reactivation_count) * 0.1
                else:
                    habituation_reduction = 0.0
                
                flashback_intensity = min(1.0, 
                    base_intensity * (1 + reactivation_history_factor + stress_amplification) 
                    - habituation_reduction
                )
                
                results["flashback_intensity"] = flashback_intensity
            else:
                results["flashback_intensity"] = 0.0
            
            # 3. 情感调节策略 / Emotional regulation strategies
            regulation_effects = {
                "default": 0.2,      # Basic regulation
                "grounding": 0.4,    # Present-moment focus (stronger)
                "reframing": 0.35,   # Cognitive reframing
                "distraction": 0.3,  # Attention redirection
                "extinction": 0.5    # Therapeutic exposure (strongest)
            }
            
            base_regulation = regulation_effects.get(coping_strategy, 0.2)
            
            # Effectiveness decreases with higher stress
            stress_impact = current_stress_level * 0.4
            effectiveness = max(0.0, base_regulation - stress_impact)
            
            results["regulation_effectiveness"] = effectiveness
            
            # Apply emotional regulation
            if results["reactivation_occurred"]:
                # Reduce flashback intensity based on regulation
                reduced_intensity = max(0.0, 
                    results["flashback_intensity"] - effectiveness
                )
                results["flashback_intensity"] = reduced_intensity
            
            # 4. 避免过度激活的机制 / Prevent over-activation mechanism
            # Check if this would cause over-activation
            if results["flashback_intensity"] > 0.7 and current_stress_level > 0.6:
                # High risk of over-activation - apply dampening
                dampening = min(0.3, current_stress_level * 0.4)
                results["flashback_intensity"] = max(0.0, 
                    results["flashback_intensity"] - dampening
                )
                results["over_activation_prevented"] = True
                results["recommended_actions"].append("implement_grounding_protocol")
                results["recommended_actions"].append("reduce_stimuli")
            else:
                results["over_activation_prevented"] = False
            
            # 5. 创伤记忆的逐步消退 / Gradual trauma extinction
            if coping_strategy == "extinction":
                # Extinction therapy: controlled reactivation without negative outcome
                # Gradually reduces trauma response
                if results["reactivation_occurred"] and results["flashback_intensity"] < 0.5:
                    # Successful extinction trial
                    extinction_boost = 0.05 + (effectiveness * 0.1)
                    
                    # Reduce trauma intensity slightly (simulating therapeutic extinction)
                    trauma.trauma_intensity = max(0.1, trauma.trauma_intensity - 0.02)
                    
                    results["extinction_progress"] = extinction_boost
                    results["recommended_actions"].append("continue_extinction_therapy")
                    results["recommended_actions"].append("track_extinction_progress")
                else:
                    # Intensity too high for effective extinction
                    results["extinction_progress"] = 0.0
                    results["recommended_actions"].append("reduce_intensity_before_extinction")
            else:
                # Calculate natural extinction progress from repeated safe reactivations
                if trauma.reactivation_count > 5 and results["flashback_intensity"] < 0.4:
                    natural_extinction = min(0.3, trauma.reactivation_count * 0.01)
                    results["extinction_progress"] = natural_extinction
            
            # 6. 生成推荐行动 / Generate recommended actions
            if not results["recommended_actions"]:
                if results["flashback_intensity"] > 0.5:
                    results["recommended_actions"].append("apply_emotional_regulation")
                    results["recommended_actions"].append("monitor_stress_levels")
                
                if trauma.reactivation_count > 15 and results["extinction_progress"] > 0.2:
                    results["recommended_actions"].append("consider_therapeutic_extinction")
                
                if current_stress_level > 0.7:
                    results["recommended_actions"].append("reduce_system_stress")
                
                if not results["recommended_actions"]:
                    results["recommended_actions"].append("continue_monitoring")
            
            # 7. 记录处理结果 / Log processing results
            processing_record = {
                "timestamp": datetime.now().isoformat(),
                "memory_id": memory_id,
                "trigger": trigger_context,
                "stress_level": current_stress_level,
                "strategy": coping_strategy,
                "intensity": results["flashback_intensity"],
                "regulation": results["regulation_effectiveness"],
                "extinction_progress": results["extinction_progress"]
            }
            
            # Store processing history (could be extended to persistent storage)
            if not hasattr(self, '_processing_history'):
                self._processing_history = []
            self._processing_history.append(processing_record)
            
            results["status"] = "processed"
            
        except ValueError as e:
            results["status"] = "error"
            results["error"] = str(e)
            results["error_type"] = "ValueError"
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            results["error_type"] = type(e).__name__
        
        return results


class ExplicitImplicitLearning:
    """
    显性/隐性学习系统 / Explicit and Implicit Learning System
    
    Distinguishes between:
    - Explicit learning: Conscious, declarative, factual
    - Implicit learning: Unconscious, procedural, skill-based
    
    Different consolidation patterns:
    - Explicit: Fast encoding, vulnerable to interference
    - Implicit: Slow encoding, resistant to interference
    
    Example:
        >>> learning = ExplicitImplicitLearning()
        >>> 
        >>> # Explicit learning (facts, conscious)
        >>> learning.learn_explicit(
        ...     event_id="fact_001",
        ...     content="Paris is the capital of France",
        ...     context="study_session"
        ... )
        >>> 
        >>> # Implicit learning (skills, unconscious)
        >>> learning.learn_implicit(
        ...     event_id="skill_001",
        ...     content="riding_bike_procedural_memory",
        ...     context="practice_session"
        ... )
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Learning storage
        self.explicit_memories: Dict[str, LearningEvent] = {}
        self.implicit_memories: Dict[str, LearningEvent] = {}
        
        # Consolidation parameters
        self.explicit_consolidation_rate: float = self.config.get("explicit_rate", 0.3)
        self.implicit_consolidation_rate: float = self.config.get("implicit_rate", 0.1)
        self.explicit_interference: float = self.config.get("explicit_interference", 0.4)
    
    def learn_explicit(
        self,
        event_id: str,
        content: Any,
        context: str,
        timestamp: Optional[datetime] = None
    ) -> LearningEvent:
        """
        显性学习 / Explicit (conscious) learning
        
        Fast encoding but vulnerable to interference.
        """
        event = LearningEvent(
            event_id=event_id,
            content=content,
            learning_type="explicit",
            context=context,
            timestamp=timestamp or datetime.now(),
            consolidation_level=0.2  # Starts low, consolidates quickly
        )
        
        self.explicit_memories[event_id] = event
        
        # Apply interference to other explicit memories
        self._apply_interference(event_id)
        
        return event
    
    def learn_implicit(
        self,
        event_id: str,
        content: Any,
        context: str,
        timestamp: Optional[datetime] = None
    ) -> LearningEvent:
        """
        隐性学习 / Implicit (unconscious) learning
        
        Slow encoding but resistant to interference.
        """
        event = LearningEvent(
            event_id=event_id,
            content=content,
            learning_type="implicit",
            context=context,
            timestamp=timestamp or datetime.now(),
            consolidation_level=0.1  # Starts lower, consolidates slowly
        )
        
        self.implicit_memories[event_id] = event
        
        return event
    
    def _apply_interference(self, new_event_id: str) -> None:
        """应用干扰 / Apply interference to existing explicit memories"""
        new_event = self.explicit_memories[new_event_id]
        
        for event_id, event in self.explicit_memories.items():
            if event_id != new_event_id:
                # Reduce consolidation level due to interference
                event.consolidation_level = max(
                    0.0,
                    event.consolidation_level - self.explicit_interference * 0.1
                )
    
    def consolidate(self, hours_elapsed: float = 1.0) -> None:
        """
        巩固学习记忆 / Consolidate learning memories
        
        Different rates for explicit vs implicit.
        """
        # Consolidate explicit memories (faster)
        for event in self.explicit_memories.values():
            consolidation_increase = self.explicit_consolidation_rate * hours_elapsed / 24.0
            event.consolidation_level = min(1.0, event.consolidation_level + consolidation_increase)
        
        # Consolidate implicit memories (slower but more stable)
        for event in self.implicit_memories.values():
            consolidation_increase = self.implicit_consolidation_rate * hours_elapsed / 24.0
            event.consolidation_level = min(1.0, event.consolidation_level + consolidation_increase)
    
    def get_explicit_memory(self, event_id: str) -> Optional[LearningEvent]:
        """获取显性记忆 / Get explicit memory"""
        return self.explicit_memories.get(event_id)
    
    def get_implicit_memory(self, event_id: str) -> Optional[LearningEvent]:
        """获取隐性记忆 / Get implicit memory"""
        return self.implicit_memories.get(event_id)
    
    def get_consolidation_stats(self) -> Dict[str, Any]:
        """获取巩固统计 / Get consolidation statistics"""
        explicit_consolidated = sum(
            1 for e in self.explicit_memories.values() if e.consolidation_level > 0.7
        )
        implicit_consolidated = sum(
            1 for e in self.implicit_memories.values() if e.consolidation_level > 0.7
        )
        
        return {
            "explicit_count": len(self.explicit_memories),
            "explicit_consolidated": explicit_consolidated,
            "implicit_count": len(self.implicit_memories),
            "implicit_consolidated": implicit_consolidated,
            "avg_explicit_consolidation": (
                sum(e.consolidation_level for e in self.explicit_memories.values()) /
                len(self.explicit_memories) if self.explicit_memories else 0.0
            ),
            "avg_implicit_consolidation": (
                sum(e.consolidation_level for e in self.implicit_memories.values()) /
                len(self.implicit_memories) if self.implicit_memories else 0.0
            ),
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        np_system = NeuroplasticitySystem()
        await np_system.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - 神经可塑性系统演示")
        print("Neuroplasticity System Demo")
        print("=" * 60)
        
        # Create memories
        print("\n创建记忆痕迹 / Creating memory traces:")
        memories = [
            np_system.create_memory_trace(
                f"mem_{i:03d}", 
                f"Information chunk {i}",
                initial_weight=0.5 + i * 0.05
            )
            for i in range(5)
        ]
        
        for mem in memories:
            print(f"  {mem.memory_id}: weight={mem.current_weight:.2f}")
        
        # Associate memories
        print("\n建立记忆关联 / Creating memory associations:")
        np_system.associate_memories("mem_000", "mem_001")
        np_system.associate_memories("mem_001", "mem_002")
        print("  mem_000 <-> mem_001")
        print("  mem_001 <-> mem_002")
        
        # Apply LTP
        print("\n应用LTP增强 / Applying LTP:")
        np_system.apply_ltp("mem_000", frequency=15.0, duration=10.0)
        mem = np_system.memory_traces["mem_000"]
        print(f"  mem_000 new weight: {mem.current_weight:.2f}")
        
        # Access memory (Hebbian)
        print("\n访问记忆（Hebbian学习）/ Accessing memory (Hebbian):")
        np_system.access_memory("mem_000")
        print(f"  mem_000 access count: {mem.access_count}")
        
        # Check retention
        print("\n记忆保持率 / Memory retention:")
        for mem in memories:
            retention = np_system.get_memory_retention(mem.memory_id)
            print(f"  {mem.memory_id}: {retention:.2%}")
        
        # Consolidate memories
        print("\n记忆巩固 / Memory consolidation:")
        np_system.consolidate_memories()
        consolidated = sum(1 for m in np_system.memory_traces.values() if m.is_consolidated)
        print(f"  Consolidated: {consolidated}/{len(memories)}")
        
        # System stats
        print("\n系统统计 / System stats:")
        stats = np_system.get_system_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        await np_system.shutdown()
        print("\n系统已关闭 / System shutdown complete")
        
        # Skill Acquisition Demo
        print("\n" + "=" * 60)
        print("技能习得演示 / Skill Acquisition Demo")
        print("=" * 60)
        
        skill_system = SkillAcquisition()
        skill_system.start_skill("typing", "Typing Skill", initial_performance=0.2)
        
        print("\n1. 幂律学习曲线 / Power law learning curve:")
        for i in range(10):
            skill_system.practice("typing", success=True, difficulty=0.5)
            if i % 3 == 0 or i == 9:
                perf = skill_system.get_performance("typing")
                print(f"   练习 {i+1} 次后 / after {i+1} practices: {perf:.2%}")
        
        print("\n2. 学习曲线预测 / Learning curve prediction:")
        curve = skill_system.get_learning_curve("typing", n_points=5)
        print(f"   预测表现 / Predicted performance: {[f'{c:.2%}' for c in curve]}")
        
        # Habit Formation Demo
        print("\n" + "=" * 60)
        print("习惯形成演示 / Habit Formation Demo")
        print("=" * 60)
        
        habit_system = HabitFormation()
        habit_system.start_habit("morning_exercise", "晨间锻炼")
        
        print("\n3. 66次重复理论 / 66 repetitions theory:")
        for day in range(1, 71):
            habit_system.reinforce("morning_exercise", context="bedroom", reward=0.8)
            if day in [1, 21, 42, 66, 70]:
                auto = habit_system.get_automaticity("morning_exercise")
                formed = habit_system.is_habit_formed("morning_exercise")
                print(f"   第 {day} 天 / Day {day}: 自动化={auto:.2%}, 已形成={formed}")
        
        # Trauma Memory Demo
        print("\n" + "=" * 60)
        print("创伤记忆演示 / Trauma Memory Demo")
        print("=" * 60)
        
        trauma_system = TraumaMemorySystem()
        trauma = trauma_system.encode_trauma(
            "trauma_001",
            "traumatic_event_description",
            intensity=0.85
        )
        
        print("\n4. 创伤记忆70%减缓遗忘 / 70% slower forgetting:")
        hours_list = [1, 24, 168, 720]  # 1 hour, 1 day, 1 week, 1 month
        trauma = trauma_system.trauma_memories.get("trauma_001")
        for hours in hours_list:
            retention = trauma_system.get_retention("trauma_001")
            print(f"   {hours}小时后 / after {hours}h: 保持率={retention:.2%}")
            # Advance time for next check
            if trauma and hasattr(trauma, 'encoding_timestamp'):
                trauma.encoding_timestamp -= timedelta(hours=hours)
        
        print("\n5. 侵入性回忆可能性 / Intrusion likelihood:")
        for stress in [0.2, 0.5, 0.8]:
            likelihood = trauma_system.get_intrusion_likelihood("trauma_001", stress)
            print(f"   压力水平 / stress {stress}: 侵入可能性={likelihood:.2%}")
        
        # Explicit/Implicit Learning Demo
        print("\n" + "=" * 60)
        print("显性/隐性学习演示 / Explicit/Implicit Learning Demo")
        print("=" * 60)
        
        learning = ExplicitImplicitLearning()
        
        print("\n6. 显性学习（易受干扰）/ Explicit learning (vulnerable to interference):")
        for i in range(3):
            learning.learn_explicit(f"fact_{i}", f"Fact number {i}", "study_session")
            stats = learning.get_consolidation_stats()
            print(f"   学习事实 {i} 后 / after fact {i}: 平均巩固度={stats['avg_explicit_consolidation']:.2%}")
        
        print("\n7. 隐性学习（抗干扰）/ Implicit learning (resistant to interference):")
        for i in range(3):
            learning.learn_implicit(f"skill_{i}", f"Skill number {i}", "practice_session")
            stats = learning.get_consolidation_stats()
            print(f"   学习技能 {i} 后 / after skill {i}: 平均巩固度={stats['avg_implicit_consolidation']:.2%}")
        
        print("\n8. 巩固进度 / Consolidation progress:")
        learning.consolidate(hours_elapsed=24)
        stats = learning.get_consolidation_stats()
        print(f"   显性记忆 / Explicit: {stats['avg_explicit_consolidation']:.2%}")
        print(f"   隐性记忆 / Implicit: {stats['avg_implicit_consolidation']:.2%}")
    
    asyncio.run(demo())
