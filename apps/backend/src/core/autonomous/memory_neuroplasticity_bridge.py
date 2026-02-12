"""
Angela AI v6.0 - Memory-Neuroplasticity Bridge
记忆-神经可塑性桥接

Bridges the gap between explicit memory systems (CDM/LU/HSM/HAM) and the
biological neuroplasticity system for memory reinforcement and forgetting.

Features:
- Connects memory systems with neuroplasticity
- Memory reinforcement through biological mechanisms
- Biologically-inspired forgetting
- Memory consolidation triggers

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime, timedelta
import asyncio
import logging
logger = logging.getLogger(__name__)

from .neuroplasticity import NeuroplasticitySystem


@dataclass
class MemoryConsolidation:
    """记忆巩固 / Memory consolidation event"""
    memory_id: str
    consolidation_level: float  # 0-1
    sleep_cycles: int = 0
    emotional_intensity: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MemoryReinforcement:
    """记忆强化 / Memory reinforcement event"""
    memory_id: str
    reinforcement_strength: float  # How much LTP to apply
    association_count: int = 0
    access_frequency: float = 0.0
    last_accessed: datetime = field(default_factory=datetime.now)


class MemoryNeuroplasticityBridge:
    """
    记忆-神经可塑性桥接器主类 / Main memory-neuroplasticity bridge class
    
    Connects Angela's memory systems with the biological neuroplasticity system,
    enabling biologically-inspired memory formation, reinforcement, and forgetting.
    
    Attributes:
        neuroplasticity: The neuroplasticity system instance
        memory_traces: Mapping of memory IDs to neuroplasticity traces
        consolidation_queue: Memories pending consolidation
        reinforcement_map: Active reinforcement tracking
        bridge_config: Configuration for bridging operations
    
    Example:
        >>> bridge = MemoryNeuroplasticityBridge()
        >>> await bridge.initialize()
        >>> 
        >>> # Register a memory from external system
        >>> bridge.register_memory(
        ...     memory_id="mem_001",
        ...     content="Important conversation with user",
        ...     emotional_weight=0.8
        ... )
        >>> 
        >>> # Access memory (triggers reinforcement)
        >>> bridge.access_memory("mem_001")
        >>> 
        >>> # Trigger consolidation (e.g., during sleep)
        >>> bridge.trigger_consolidation()
        >>> 
        >>> # Check retention
        >>> retention = bridge.get_memory_retention("mem_001")
        >>> print(f"Retention: {retention:.2%}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core systems
        self.neuroplasticity: NeuroplasticitySystem = NeuroplasticitySystem()
        
        # Memory mappings
        self._external_to_neuro: Dict[str, str] = {}  # Maps external IDs to neuroplasticity IDs
        self._memory_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Consolidation and reinforcement tracking
        self.consolidation_queue: List[str] = []
        self.reinforcement_map: Dict[str, MemoryReinforcement] = {}
        
        # Configuration
        self._ltp_threshold_accesses = self.config.get("ltp_threshold", 3)
        self._consolidation_threshold = self.config.get("consolidation_threshold", 0.7)
        self._forgetting_curve_enabled = self.config.get("use_forgetting_curve", True)
        
        # Running state
        self._running = False
        self._maintenance_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._consolidation_callbacks: List[Callable[[str], None]] = []
        self._forgetting_callbacks: List[Callable[[str, float], None]] = []
    
    async def initialize(self):
        """Initialize the memory bridge"""
        self._running = True
        await self.neuroplasticity.initialize()
        
        # Start maintenance loop
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
    
    async def shutdown(self):
        """Shutdown the memory bridge"""
        self._running = False
        
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass
        
        await self.neuroplasticity.shutdown()
    
    async def _maintenance_loop(self):
        """Background maintenance for memory health"""
        while self._running:
            await self._update_reinforcement_stats()
            await self._check_forgetting()
            await asyncio.sleep(300)  # Every 5 minutes
    
    async def _update_reinforcement_stats(self):
        """Update reinforcement statistics"""
        for memory_id, reinforcement in self.reinforcement_map.items():
            # Decay access frequency over time
            reinforcement.access_frequency *= 0.95
    
    async def _check_forgetting(self):
        """Check memories for forgetting"""
        if not self._forgetting_curve_enabled:
            return
        
        for memory_id in list(self._external_to_neuro.keys()):
            retention = self.get_memory_retention(memory_id)
            
            if retention < 0.1:  # Below 10% retention
                # Notify forgetting
                for callback in self._forgetting_callbacks:
                    try:
                        callback(memory_id, retention)
                    except Exception as e:
                        logger.error(f'Error in {__name__}: {e}', exc_info=True)
                        pass

    
    def register_memory(
        self,
        memory_id: str,
        content: Any,
        emotional_weight: float = 0.5,
        category: str = "general",
        tags: Optional[List[str]] = None,
        initial_strength: float = 0.5
    ) -> str:
        """
        Register a memory from external system
        
        Args:
            memory_id: Unique identifier from external system
            content: Memory content
            emotional_weight: Emotional significance (0-1)
            category: Memory category
            tags: Memory tags
            initial_strength: Initial memory strength
            
        Returns:
            Internal bridge ID
        """
        # Create neuroplasticity trace
        neuro_id = f"np_{memory_id}"
        
        trace = self.neuroplasticity.create_memory_trace(
            memory_id=neuro_id,
            content=content,
            initial_weight=initial_strength,
            emotional_tags=tags or []
        )
        
        # Store mapping
        self._external_to_neuro[memory_id] = neuro_id
        
        # Store metadata
        self._memory_metadata[memory_id] = {
            "category": category,
            "emotional_weight": emotional_weight,
            "tags": tags or [],
            "created_at": datetime.now(),
            "access_count": 0,
        }
        
        # Initialize reinforcement tracking
        self.reinforcement_map[memory_id] = MemoryReinforcement(
            memory_id=memory_id,
            reinforcement_strength=initial_strength,
            association_count=0,
            access_frequency=0.0
        )
        
        # Add to consolidation queue
        self.consolidation_queue.append(memory_id)
        
        return neuro_id
    
    def access_memory(self, memory_id: str) -> Optional[Any]:
        """
        Access a memory (triggers biological reinforcement)
        
        Args:
            memory_id: Memory ID to access
            
        Returns:
            Memory content if found, None otherwise
        """
        if memory_id not in self._external_to_neuro:
            return None
        
        neuro_id = self._external_to_neuro[memory_id]
        
        # Access through neuroplasticity system
        trace = self.neuroplasticity.access_memory(neuro_id)
        
        if trace:
            # Update reinforcement
            if memory_id in self.reinforcement_map:
                reinforcement = self.reinforcement_map[memory_id]
                reinforcement.access_frequency += 1.0
                reinforcement.last_accessed = datetime.now()
                
                # Apply LTP if threshold reached
                if reinforcement.access_frequency >= self._ltp_threshold_accesses:
                    self.neuroplasticity.apply_ltp(
                        neuro_id,
                        frequency=15.0,
                        duration=5.0
                    )
                    reinforcement.reinforcement_strength = min(
                        1.0,
                        reinforcement.reinforcement_strength + 0.1
                    )
            
            # Update metadata
            if memory_id in self._memory_metadata:
                self._memory_metadata[memory_id]["access_count"] += 1
            
            return trace.content
        
        return None
    
    def associate_memories(self, memory_id_1: str, memory_id_2: str) -> bool:
        """
        Create association between two memories
        
        Args:
            memory_id_1: First memory ID
            memory_id_2: Second memory ID
            
        Returns:
            True if association created
        """
        if (memory_id_1 not in self._external_to_neuro or
            memory_id_2 not in self._external_to_neuro):
            return False
        
        neuro_id_1 = self._external_to_neuro[memory_id_1]
        neuro_id_2 = self._external_to_neuro[memory_id_2]
        
        # Create association in neuroplasticity
        self.neuroplasticity.associate_memories(neuro_id_1, neuro_id_2)
        
        # Update reinforcement
        for mid in [memory_id_1, memory_id_2]:
            if mid in self.reinforcement_map:
                self.reinforcement_map[mid].association_count += 1
        
        return True
    
    def trigger_consolidation(self, memory_ids: Optional[List[str]] = None):
        """
        Trigger memory consolidation (e.g., during rest/sleep)
        
        Args:
            memory_ids: Specific memories to consolidate, or None for all pending
        """
        targets = memory_ids or self.consolidation_queue
        
        neuro_targets = []
        for mid in targets:
            if mid in self._external_to_neuro:
                neuro_targets.append(self._external_to_neuro[mid])
        
        if neuro_targets:
            self.neuroplasticity.consolidate_memories(neuro_targets)
            
            # Update queue
            for mid in targets:
                if mid in self.consolidation_queue:
                    self.consolidation_queue.remove(mid)
                
                # Notify callbacks
                for callback in self._consolidation_callbacks:
                    try:
                        callback(mid)
                    except Exception as e:
                        logger.error(f'Error in {__name__}: {e}', exc_info=True)
                        pass

    
    def get_memory_retention(self, memory_id: str) -> float:
        """
        Get current retention level of a memory
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Retention rate (0-1)
        """
        if memory_id not in self._external_to_neuro:
            return 0.0
        
        neuro_id = self._external_to_neuro[memory_id]
        return self.neuroplasticity.get_memory_retention(neuro_id)
    
    def get_weak_memories(self, threshold: float = 0.3) -> List[str]:
        """
        Get list of weak memories that need reinforcement
        
        Args:
            threshold: Retention threshold
            
        Returns:
            List of memory IDs with low retention
        """
        weak = []
        for ext_id, neuro_id in self._external_to_neuro.items():
            retention = self.neuroplasticity.get_memory_retention(neuro_id)
            if retention < threshold:
                weak.append(ext_id)
        return weak
    
    def get_strong_memories(self, threshold: float = 0.8) -> List[str]:
        """
        Get list of strongly consolidated memories
        
        Args:
            threshold: Retention threshold
            
        Returns:
            List of memory IDs with high retention
        """
        strong = []
        for ext_id, neuro_id in self._external_to_neuro.items():
            retention = self.neuroplasticity.get_memory_retention(neuro_id)
            if retention >= threshold:
                strong.append(ext_id)
        return strong
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        neuro_stats = self.neuroplasticity.get_system_stats()
        
        total_memories = len(self._external_to_neuro)
        
        # Calculate average retention
        if total_memories > 0:
            avg_retention = sum(
                self.get_memory_retention(mid)
                for mid in self._external_to_neuro.keys()
            ) / total_memories
        else:
            avg_retention = 0.0
        
        return {
            "total_memories": total_memories,
            "consolidated_memories": len([
                mid for mid in self._external_to_neuro.keys()
                if self.get_memory_retention(mid) > 0.7
            ]),
            "weak_memories": len(self.get_weak_memories()),
            "strong_memories": len(self.get_strong_memories()),
            "pending_consolidation": len(self.consolidation_queue),
            "average_retention": avg_retention,
            "neuroplasticity_stats": neuro_stats,
        }
    
    def get_optimal_review_schedule(self, memory_id: str) -> List[float]:
        """
        Get optimal review times for spaced repetition
        
        Args:
            memory_id: Memory ID
            
        Returns:
            List of optimal review times in hours
        """
        if memory_id not in self._external_to_neuro:
            return []
        
        neuro_id = self._external_to_neuro[memory_id]
        return self.neuroplasticity.get_optimal_review_schedule(neuro_id)
    
    def reinforce_memory(self, memory_id: str, strength: float = 0.1):
        """
        Manually reinforce a memory
        
        Args:
            memory_id: Memory to reinforce
            strength: Reinforcement amount
        """
        if memory_id not in self._external_to_neuro:
            return
        
        neuro_id = self._external_to_neuro[memory_id]
        
        # Apply LTP
        self.neuroplasticity.apply_ltp(
            neuro_id,
            frequency=10.0 + strength * 10,
            duration=5.0
        )
        
        # Update reinforcement map
        if memory_id in self.reinforcement_map:
            self.reinforcement_map[memory_id].reinforcement_strength = min(
                1.0,
                self.reinforcement_map[memory_id].reinforcement_strength + strength
            )
    
    def consolidate_memory(
        self,
        memory_id: str,
        emotional_intensity: float = 0.5,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        实现记忆巩固关键逻辑 / Implement critical memory consolidation logic
        
        连接CDM（短期记忆）到HSM（长期记忆）的关键桥接：
        - 将短期记忆转换为长期存储
        - 实现记忆的LTP增强（长时程增强）
        - 根据情绪强度调整记忆权重（情绪标记增强）
        - 实现记忆的优先级排序（重要记忆优先巩固）
        - 添加记忆的时间衰减计算
        
        Critical bridge connecting CDM (short-term) to HSM (long-term):
        - Transforms short-term memories to long-term storage
        - Implements LTP enhancement for memory strengthening
        - Adjusts memory weights based on emotional intensity (emotional tagging)
        - Implements memory priority sorting (important memories consolidate first)
        - Adds time decay calculation for memories
        
        Args:
            memory_id: External memory identifier to consolidate
            emotional_intensity: Emotional intensity of the memory (0-1), 
                               higher values lead to stronger consolidation
            priority: Consolidation priority - "high", "normal", or "low"
                     High priority memories consolidate faster
            
        Returns:
            Dict containing consolidation results:
            - success: Whether consolidation was successful
            - consolidation_level: Final consolidation strength (0-1)
            - ltp_applied: Amount of LTP enhancement applied
            - time_decay: Calculated time decay factor
            - priority_multiplier: Priority boost applied
            
        Raises:
            ValueError: If memory_id is not found in the system
            
        Example:
            >>> result = bridge.consolidate_memory(
            ...     memory_id="mem_001",
            ...     emotional_intensity=0.8,
            ...     priority="high"
            ... )
            >>> print(f"Consolidation level: {result['consolidation_level']:.2%}")
        """
        import math
        
        results = {
            "memory_id": memory_id,
            "success": False,
            "consolidation_level": 0.0,
            "ltp_applied": 0.0,
            "time_decay": 1.0,
            "priority_multiplier": 1.0,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Validate memory exists
            if memory_id not in self._external_to_neuro:
                raise ValueError(f"Memory {memory_id} not found in bridge registry")
            
            neuro_id = self._external_to_neuro[memory_id]
            
            # Get current memory trace
            trace = self.neuroplasticity.access_memory(neuro_id)
            if not trace:
                raise ValueError(f"Memory trace {neuro_id} not found in neuroplasticity system")
            
            # 1. 计算优先级乘数 / Calculate priority multiplier
            priority_multipliers = {
                "high": 1.5,
                "normal": 1.0,
                "low": 0.7
            }
            priority_mult = priority_multipliers.get(priority, 1.0)
            results["priority_multiplier"] = priority_mult
            
            # 2. 计算时间衰减 / Calculate time decay
            age_hours = (datetime.now() - trace.created_at).total_seconds() / 3600.0
            # Exponential decay: newer memories consolidate better
            time_decay = math.exp(-age_hours / 24.0)  # 24-hour half-life
            results["time_decay"] = time_decay
            
            # 3. 应用LTP增强 / Apply LTP enhancement
            # Higher emotional intensity = stronger LTP
            base_ltp_frequency = 10.0
            emotional_boost = emotional_intensity * 10.0  # 0-10 Hz boost
            ltp_frequency = (base_ltp_frequency + emotional_boost) * priority_mult * time_decay
            ltp_duration = 5.0 + emotional_intensity * 5.0  # 5-10 seconds
            
            self.neuroplasticity.apply_ltp(
                neuro_id,
                frequency=ltp_frequency,
                duration=ltp_duration
            )
            results["ltp_applied"] = ltp_frequency * ltp_duration / 100.0  # Normalized LTP amount
            
            # 4. 情绪标记增强 / Emotional tagging enhancement
            if emotional_intensity > 0.6:
                # High emotional memories get extra consolidation boost
                emotional_boost = (emotional_intensity - 0.6) * 0.5  # 0-0.2 boost
                trace.consolidation_strength = min(1.0, trace.consolidation_strength + emotional_boost)
                results["emotional_boost"] = emotional_boost
            
            # 5. 更新巩固强度 / Update consolidation strength
            base_consolidation_increase = 0.3 * priority_mult * time_decay
            trace.consolidation_strength = min(
                1.0,
                trace.consolidation_strength + base_consolidation_increase
            )
            
            # 6. 更新记忆权重 / Update memory weight
            weight_increase = 0.1 * priority_mult * (1 + emotional_intensity * 0.5) * time_decay
            trace.current_weight = min(1.0, trace.current_weight + weight_increase)
            
            # 7. 检查是否完全巩固 / Check if fully consolidated
            if trace.consolidation_strength >= self._consolidation_threshold:
                trace.is_consolidated = True
                results["is_fully_consolidated"] = True
                
                # 从队列中移除 / Remove from queue
                if memory_id in self.consolidation_queue:
                    self.consolidation_queue.remove(memory_id)
                
                # 通知回调 / Notify callbacks
                for callback in self._consolidation_callbacks:
                    try:
                        callback(memory_id)
                    except Exception as e:
                        logger.error(f'Error in {__name__}: {e}', exc_info=True)
                        pass

            else:
                results["is_fully_consolidated"] = False
                # Add to queue if not already there
                if memory_id not in self.consolidation_queue:
                    self.consolidation_queue.append(memory_id)
            
            # 8. 更新元数据 / Update metadata
            if memory_id in self._memory_metadata:
                self._memory_metadata[memory_id]["consolidation_level"] = trace.consolidation_strength
                self._memory_metadata[memory_id]["last_consolidation"] = datetime.now()
                self._memory_metadata[memory_id]["emotional_intensity"] = emotional_intensity
            
            results["consolidation_level"] = trace.consolidation_strength
            results["success"] = True
            
        except ValueError as e:
            results["error"] = str(e)
            results["error_type"] = "ValueError"
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            results["error"] = str(e)

            results["error_type"] = type(e).__name__
        
        return results
    
    def reinforce_memory(
        self,
        memory_id: str,
        strength: float = 0.1,
        emotional_context: Optional[str] = None,
        source: str = "manual"
    ) -> Dict[str, Any]:
        """
        实现记忆强化关键逻辑 / Implement critical memory reinforcement logic
        
        记忆桥接关键功能：
        - 连接CDM到HSM的记忆强化通路
        - 实现LTP（长时程增强）效应
        - 根据情绪强度调整记忆权重
        - 实现记忆的优先级排序
        - 添加记忆的时间衰减和保护机制
        
        Critical memory bridge functionality:
        - Connects CDM to HSM memory reinforcement pathway
        - Implements LTP (Long-Term Potentiation) effects
        - Adjusts memory weights based on emotional intensity
        - Implements memory priority sorting
        - Adds time decay calculation and memory protection
        
        Args:
            memory_id: Memory identifier to reinforce
            strength: Reinforcement strength (0-1), determines LTP intensity
            emotional_context: Optional emotional context for reinforcement
                             (e.g., "joy", "stress", "nostalgia")
            source: Source of reinforcement - "manual", "access", "association",
                   or "emotional_trigger"
                   
        Returns:
            Dict containing reinforcement results:
            - success: Whether reinforcement was successful
            - reinforcement_strength: Final reinforcement level
            - ltp_applied: LTP parameters applied
            - weight_change: Change in memory weight
            - access_count: Updated access count
            - emotional_boost: Extra boost from emotional context
            
        Raises:
            ValueError: If memory_id is not found or strength is invalid
            
        Example:
            >>> result = bridge.reinforce_memory(
            ...     memory_id="mem_001",
            ...     strength=0.3,
            ...     emotional_context="nostalgia",
            ...     source="emotional_trigger"
            ... )
            >>> print(f"New reinforcement level: {result['reinforcement_strength']:.2%}")
        """
        import math
        
        results = {
            "memory_id": memory_id,
            "success": False,
            "reinforcement_strength": 0.0,
            "ltp_applied": {},
            "weight_change": 0.0,
            "access_count": 0,
            "emotional_boost": 0.0,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Validate inputs
            if not 0 <= strength <= 1:
                raise ValueError(f"Strength must be between 0 and 1, got {strength}")
            
            # Validate memory exists
            if memory_id not in self._external_to_neuro:
                raise ValueError(f"Memory {memory_id} not found in bridge registry")
            
            neuro_id = self._external_to_neuro[memory_id]
            
            # Get reinforcement tracking
            if memory_id not in self.reinforcement_map:
                self.reinforcement_map[memory_id] = MemoryReinforcement(
                    memory_id=memory_id,
                    reinforcement_strength=0.0,
                    association_count=0,
                    access_frequency=0.0
                )
            
            reinforcement = self.reinforcement_map[memory_id]
            
            # 1. 更新访问统计 / Update access statistics
            reinforcement.access_frequency += 1.0
            reinforcement.last_accessed = datetime.now()
            results["access_count"] = int(reinforcement.access_frequency)
            
            # 2. 根据来源调整基础强度 / Adjust base strength by source
            source_multipliers = {
                "manual": 1.0,
                "access": 0.7,  # Regular access has lower reinforcement
                "association": 0.8,  # Association-based reinforcement
                "emotional_trigger": 1.3  # Emotional triggers are stronger
            }
            adjusted_strength = strength * source_multipliers.get(source, 1.0)
            
            # 3. 情绪上下文增强 / Emotional context enhancement
            emotional_boost = 0.0
            if emotional_context:
                # Different emotions provide different boosts
                emotion_multipliers = {
                    "joy": 0.15,
                    "love": 0.20,
                    "nostalgia": 0.12,
                    "pride": 0.10,
                    "stress": 0.08,  # Stress can also reinforce (flashbulb memory)
                    "fear": 0.10,
                }
                emotional_boost = emotion_multipliers.get(emotional_context, 0.05)
                adjusted_strength += emotional_boost
            
            results["emotional_boost"] = emotional_boost
            
            # 4. 应用LTP / Apply LTP
            # Calculate LTP parameters based on adjusted strength
            base_frequency = 10.0
            ltp_frequency = base_frequency + adjusted_strength * 15.0  # 10-25 Hz
            ltp_duration = 5.0 + adjusted_strength * 10.0  # 5-15 seconds
            
            self.neuroplasticity.apply_ltp(
                neuro_id,
                frequency=ltp_frequency,
                duration=ltp_duration
            )
            
            results["ltp_applied"] = {
                "frequency": ltp_frequency,
                "duration": ltp_duration,
                "intensity": adjusted_strength
            }
            
            # 5. 更新强化强度 / Update reinforcement strength
            # Apply diminishing returns for very high access frequencies
            if reinforcement.access_frequency > 20:
                # Diminishing returns after 20 accesses
                diminishing_factor = 1.0 / math.sqrt(reinforcement.access_frequency / 20)
                adjusted_strength *= diminishing_factor
            
            old_strength = reinforcement.reinforcement_strength
            reinforcement.reinforcement_strength = min(
                1.0,
                reinforcement.reinforcement_strength + adjusted_strength
            )
            results["reinforcement_strength"] = reinforcement.reinforcement_strength
            results["weight_change"] = reinforcement.reinforcement_strength - old_strength
            
            # 6. 更新神经可塑性追踪 / Update neuroplasticity trace
            trace = self.neuroplasticity.access_memory(neuro_id)
            if trace:
                trace.current_weight = min(1.0, trace.current_weight + adjusted_strength * 0.1)
                trace.access_count += 1
                trace.last_accessed = datetime.now()
                
                # Add emotional tags if provided
                if emotional_context and emotional_context not in trace.emotional_tags:
                    trace.emotional_tags.append(emotional_context)
            
            # 7. 检查LTP阈值 / Check LTP threshold
            if reinforcement.access_frequency >= self._ltp_threshold_accesses:
                # Bonus reinforcement for repeated access
                bonus_strength = 0.05
                reinforcement.reinforcement_strength = min(
                    1.0,
                    reinforcement.reinforcement_strength + bonus_strength
                )
                results["ltp_threshold_bonus"] = bonus_strength
            
            # 8. 更新元数据 / Update metadata
            if memory_id in self._memory_metadata:
                self._memory_metadata[memory_id]["access_count"] = int(reinforcement.access_frequency)
                self._memory_metadata[memory_id]["last_accessed"] = datetime.now()
                if emotional_context:
                    if "emotional_contexts" not in self._memory_metadata[memory_id]:
                        self._memory_metadata[memory_id]["emotional_contexts"] = []
                    if emotional_context not in self._memory_metadata[memory_id]["emotional_contexts"]:
                        self._memory_metadata[memory_id]["emotional_contexts"].append(emotional_context)
            
            results["success"] = True
            
        except ValueError as e:
            results["error"] = str(e)
            results["error_type"] = "ValueError"
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            results["error"] = str(e)

            results["error_type"] = type(e).__name__
        
        return results
    
    def register_consolidation_callback(self, callback: Callable[[str], None]):
        """Register callback for memory consolidation events"""
        self._consolidation_callbacks.append(callback)
    
    def register_forgetting_callback(self, callback: Callable[[str, float], None]):
        """Register callback for memory forgetting events"""
        self._forgetting_callbacks.append(callback)
    
    def get_bridge_summary(self) -> Dict[str, Any]:
        """Get bridge system summary"""
        return {
            "registered_memories": len(self._external_to_neuro),
            "consolidation_queue_size": len(self.consolidation_queue),
            "average_reinforcement": sum(
                r.reinforcement_strength
                for r in self.reinforcement_map.values()
            ) / len(self.reinforcement_map) if self.reinforcement_map else 0,
            "bridge_health": "active" if self._running else "inactive",
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        bridge = MemoryNeuroplasticityBridge()
        await bridge.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - 记忆-神经可塑性桥接演示")
        print("Memory-Neuroplasticity Bridge Demo")
        print("=" * 60)
        
        # Register memories
        print("\n注册记忆 / Registering memories:")
        for i in range(5):
            bridge.register_memory(
                memory_id=f"mem_{i:03d}",
                content=f"Memory content {i}",
                emotional_weight=0.5 + i * 0.1,
                initial_strength=0.4 + i * 0.1
            )
            print(f"  已注册 mem_{i:03d}")
        
        # Access memories (reinforcement)
        print("\n访问记忆（强化）/ Accessing memories (reinforcement):")
        for i in range(3):
            bridge.access_memory("mem_000")
            print(f"  访问 mem_000 (第 {i+1} 次)")
        
        # Check retention
        print("\n记忆保持率 / Memory retention:")
        for i in range(5):
            retention = bridge.get_memory_retention(f"mem_{i:03d}")
            print(f"  mem_{i:03d}: {retention:.2%}")
        
        # Associate memories
        print("\n记忆关联 / Memory association:")
        bridge.associate_memories("mem_000", "mem_001")
        print("  mem_000 <-> mem_001")
        
        # Consolidation
        print("\n记忆巩固 / Memory consolidation:")
        bridge.trigger_consolidation()
        print("  已触发巩固")
        
        # Stats
        print("\n统计信息 / Statistics:")
        stats = bridge.get_memory_stats()
        print(f"  总记忆数: {stats['total_memories']}")
        print(f"  已巩固: {stats['consolidated_memories']}")
        print(f"  平均保持率: {stats['average_retention']:.2%}")
        
        await bridge.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
