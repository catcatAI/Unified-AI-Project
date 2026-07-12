"""
記憶整合循環

主動收集、分析、結構化記憶，
更新知識庫，生成新模板。
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.system.config.magic_numbers import (
    batch_value,
    behavior_threshold,
    cache_value,
    limit_value,
    loop_sleep,
    threshold_value,
)

logger = logging.getLogger(__name__)


@dataclass
class MemoryInfo:
    """記憶信息"""

    content: str
    type: str
    timestamp: datetime
    importance: float = 0.5
    structured: bool = False
    integrated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "content": self.content,
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "structured": self.structured,
            "integrated": self.integrated,
        }


@dataclass
class KnowledgePattern:
    """知識模式"""

    pattern: str
    frequency: int
    confidence: float
    last_seen: datetime
    examples: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "pattern": self.pattern,
            "frequency": self.frequency,
            "confidence": self.confidence,
            "last_seen": self.last_seen.isoformat(),
            "examples": self.examples,
        }


class MemoryIntegrationLoop:
    """
    記憶整合循環

    功能：
    - 收集新信息
    - 分析模式
    - 結構化記憶
    - 更新知識庫
    - 生成新模板

    這讓 Angela 能夠主動整理和學習記憶。
    """

    def __init__(
        self,
        memory_manager: Any,
        learning_engine: Any,
        loop_interval: float = 180.0,  # 整合循環間隔（秒，3分鐘）
        min_loop_interval: float = 120.0,
        max_loop_interval: float = 300.0,
    ):
        self.memory_manager = memory_manager
        self.learning_engine = learning_engine

        self.loop_interval = loop_interval
        self.min_loop_interval = min_loop_interval
        self.max_loop_interval = max_loop_interval

        self.is_running = False
        self._integration_task: Optional[asyncio.Task] = None

        # 記憶信息
        self.memory_infos: List[MemoryInfo] = []
        self.max_infos = cache_value("memory_loop_history", 1000)

        # 知識模式
        self.knowledge_patterns: Dict[str, KnowledgePattern] = {}

        # 整合隊列
        self.integration_queue: List[MemoryInfo] = []

        # 神經可塑性系統 (Phase 5.3)
        self._neuroplasticity: Optional[Any] = None

        # 統計信息
        self.stats = {
            "total_memories": 0,
            "structured_memories": 0,
            "integrated_memories": 0,
            "patterns_found": 0,
            "templates_generated": 0,
            "knowledge_base_updates": 0,
            "neuroplasticity_encodings": 0,
            "promotions_to_long_term": 0,
            "importance_boosts": 0,
        }

        logger.info("MemoryIntegrationLoop initialized")

    async def start(self) -> None:
        """啟動整合循環"""
        if self.is_running:
            logger.warning("MemoryIntegrationLoop is already running", exc_info=True)
            return

        self.is_running = True
        self._integration_task = asyncio.create_task(self._integration_loop())
        logger.info("MemoryIntegrationLoop started")

    async def stop(self) -> None:
        """停止整合循環"""
        if not self.is_running:
            return

        self.is_running = False

        if self._integration_task:
            self._integration_task.cancel()
            try:
                await self._integration_task
            except asyncio.CancelledError:
                pass

        logger.info("MemoryIntegrationLoop stopped")

    def connect_neuroplasticity(self, neuroplasticity_system: Any) -> None:
        """Connect a neuroplasticity system for memory encoding (Phase 5.3)."""
        self._neuroplasticity = neuroplasticity_system
        logger.info("Neuroplasticity system connected to MemoryIntegrationLoop")

    async def _integration_loop(self) -> None:
        """整合循環"""
        logger.info("Memory integration loop started")

        while self.is_running:
            try:
                # 動態調整循環間隔
                interval = self._calculate_interval()

                # 執行整合流程
                await self._process_integration()

                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:  # broad exception acceptable: loop must be resilient to prevent process termination
                logger.error(f"Error in integration loop: {e}", exc_info=True)
                await asyncio.sleep(loop_sleep("memory_loop_tight", 1.0))  # 防止緊密循環

    def _calculate_interval(self) -> float:
        """動態計算循環間隔"""
        # 根據待整合記憶數量調整
        if len(self.integration_queue) > batch_value("ai.memory_integration_loop.fast_queue_threshold", 50):
            return self.min_loop_interval
        elif len(self.integration_queue) > batch_value("ai.memory_integration_loop.normal_queue_threshold", 20):
            return self.loop_interval
        else:
            return self.max_loop_interval

    async def _process_integration(self) -> None:
        """處理整合流程"""
        try:
            # 1. 收集新信息
            await self._collect_new_info()

            # 2. 分析模式
            await self._analyze_patterns()

            # 3. 結構化記憶 (with neuroplasticity integration)
            await self._structure_memory()

            # 4. 更新知識庫
            await self._update_knowledge_base()

            # 5. 生成新模板
            await self._generate_templates()

            # 6. Promote frequently accessed memories (Phase 5.3)
            await self._promote_memories()

        except Exception as e:
            logger.error(f"Error processing integration: {e}", exc_info=True)

    async def _collect_new_info(self) -> None:
        """收集新信息"""
        try:
            # 從記憶管理器獲取最近的記憶
            if hasattr(self.memory_manager, "get_recent_memories"):
                recent_memories = await self.memory_manager.get_recent_memories(limit=batch_value("recent_memories", 20))

                for mem in recent_memories:
                    # 檢查是否已經處理
                    if not any(m.content == str(mem) for m in self.memory_infos):
                        info = MemoryInfo(
                            content=str(mem),
                            type="conversation",
                            timestamp=datetime.now(),
                            importance=0.5,
                        )
                        self.memory_infos.append(info)
                        self.integration_queue.append(info)
                        self.stats["total_memories"] += 1

            # 限制數量
            if len(self.memory_infos) > self.max_infos:
                self.memory_infos = self.memory_infos[-self.max_infos :]

        except Exception as e:  # broad exception acceptable: collecting new info should not crash integration loop
            logger.warning(f"Error collecting new info: {e}", exc_info=True)

    async def _analyze_patterns(self) -> None:
        """分析模式"""
        try:
            # 簡單的模式分析
            content_list = [info.content for info in self.memory_infos]

            # 分析常見的主題/關鍵詞
            keyword_frequency: Dict[str, int] = {}

            for content in content_list:
                words = content.split()
                for word in words:
                    if len(word) > 2:  # 忽略短詞
                        keyword_frequency[word] = keyword_frequency.get(word, 0) + 1

            # 提取高頻關鍵詞作為模式
            for keyword, freq in keyword_frequency.items():
                if freq >= batch_value("ai.memory_integration_loop.pattern_freq_threshold", 3):
                    pattern_key = f"keyword_{keyword}"

                    if pattern_key in self.knowledge_patterns:
                        self.knowledge_patterns[pattern_key].frequency += freq
                        self.knowledge_patterns[pattern_key].confidence = min(
                            1.0, self.knowledge_patterns[pattern_key].confidence + behavior_threshold("ai.memory_integration_loop.confidence_increment", 0.1)
                        )
                        self.knowledge_patterns[pattern_key].last_seen = datetime.now()
                    else:
                        self.knowledge_patterns[pattern_key] = KnowledgePattern(
                            pattern=keyword,
                            frequency=freq,
                            confidence=threshold_value("ai.memory_integration_loop.pattern_initial_confidence", 0.3),
                            last_seen=datetime.now(),
                            examples=[content for content in content_list if keyword in content][
                                :3
                            ],
                        )
                        self.stats["patterns_found"] += 1

        except Exception as e:  # broad exception acceptable: pattern analysis should not crash the loop
            logger.warning(f"Error analyzing patterns: {e}", exc_info=True)

    async def _structure_memory(self) -> None:
        """結構化記憶 with neuroplasticity integration (Phase 5.3)."""
        for info in self.integration_queue[:batch_value("ai.memory_integration_loop.structure_batch", 10)]:
            if not info.structured:
                try:
                    # 簡單的結構化：提取關鍵信息
                    structured_data = self._simple_structure(info.content)

                    # Phase 5.3: Neuroplasticity encoding
                    if self._neuroplasticity is not None:
                        try:
                            if hasattr(self._neuroplasticity, 'encode'):
                                self._neuroplasticity.encode(info.content)
                                self.stats["neuroplasticity_encodings"] += 1
                            if hasattr(self._neuroplasticity, 'consolidate'):
                                self._neuroplasticity.consolidate()
                        except Exception as e:
                            logger.debug("Neuroplasticity encoding failed: %s", e)

                    # Phase 5.3: Importance boosting based on access count
                    if info.importance < 1.0 and info.integrated:
                        boost = 0.0
                        if hasattr(info, '_access_count') and info._access_count > 5:
                            boost = 0.2
                        elif hasattr(self.memory_manager, 'get_access_count'):
                            count = await self.memory_manager.get_access_count(info.content)
                            if count > 5:
                                boost = 0.2
                        if boost > 0:
                            info.importance = min(1.0, info.importance + boost)
                            self.stats["importance_boosts"] += 1

                    # 存儲結構化數據
                    if hasattr(self.memory_manager, "store_structured_memory"):
                        await self.memory_manager.store_structured_memory(
                            content=info.content, structured_data=structured_data
                        )

                    info.structured = True
                    self.stats["structured_memories"] += 1

                except Exception as e:
                    logger.warning(f"Error structuring memory: {e}", exc_info=True)

    def _simple_structure(self, content: str) -> Dict[str, Any]:
        """簡單的記憶結構化"""
        # 提取基本信息
        words = content.split()
        sentences = content.split(".")

        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "keywords": words[:limit_value("ai.memory_integration_loop.keyword_limit", 5)],
            "first_sentence": sentences[0] if sentences else "",
            "timestamp": datetime.now().isoformat(),
        }

    async def _update_knowledge_base(self) -> None:
        """更新知識庫"""
        try:
            # 將結構化的記憶整合到知識庫
            for info in self.integration_queue:
                if info.structured and not info.integrated:
                    # 存儲到知識庫
                    if hasattr(self.memory_manager, "add_to_knowledge_base"):
                        await self.memory_manager.add_to_knowledge_base(
                            content=info.content, importance=info.importance
                        )

                    info.integrated = True
                    self.stats["integrated_memories"] += 1
                    self.stats["knowledge_base_updates"] += 1

            # 清理已整合的
            self.integration_queue = [
                info for info in self.integration_queue if not info.integrated
            ]

        except Exception as e:  # broad exception acceptable: knowledge base updates should be fault-tolerant
            logger.warning(f"Error updating knowledge base: {e}", exc_info=True)

    async def _generate_templates(self) -> None:
        """生成新模板"""
        try:
            # 基於模式生成模板
            if len(self.knowledge_patterns) > batch_value("ai.memory_integration_loop.template_min_patterns", 5):
                # 選擇高置信度的模式
                high_confidence_patterns = [
                    p for p in self.knowledge_patterns.values() if p.confidence > threshold_value("ai.memory_integration_loop.high_confidence_threshold", 0.6)
                ]

                if high_confidence_patterns and hasattr(self.memory_manager, "generate_template"):
                    for pattern in high_confidence_patterns[:batch_value("ai.memory_integration_loop.template_batch", 3)]:
                        template = {
                            "pattern": pattern.pattern,
                            "examples": pattern.examples,
                            "frequency": pattern.frequency,
                            "created_at": datetime.now().isoformat(),
                        }

                        await self.memory_manager.generate_template(template)
                        self.stats["templates_generated"] += 1

        except Exception as e:
            logger.warning(f"Error generating templates: {e}", exc_info=True)

    async def _promote_memories(self) -> None:
        """Promote frequently accessed short-term memories to long-term (Phase 5.3)."""
        try:
            if not hasattr(self.memory_manager, 'promote_to_long_term'):
                return

            for info in self.memory_infos:
                if info.type != "short_term":
                    continue
                access_count = 0
                if hasattr(info, '_access_count'):
                    access_count = info._access_count
                elif hasattr(self.memory_manager, 'get_access_count'):
                    access_count = await self.memory_manager.get_access_count(info.content)

                if access_count > 10:
                    success = await self.memory_manager.promote_to_long_term(info.content)
                    if success:
                        info.type = "long_term"
                        self.stats["promotions_to_long_term"] += 1
                        logger.debug("Promoted memory to long-term: %s", info.content[:50])

        except Exception as e:
            logger.debug("Memory promotion failed: %s", e)

    def add_memory(self, content: str, memory_type: str = "general", importance: float = 0.5) -> None:
        """添加記憶"""
        info = MemoryInfo(
            content=content, type=memory_type, timestamp=datetime.now(), importance=importance
        )

        self.memory_infos.append(info)
        self.integration_queue.append(info)
        self.stats["total_memories"] += 1

        logger.debug(f"Added memory: {content[:50]}...")

    def get_memory_infos(self, limit: int = 20) -> List[Dict[str, Any]]:
        """獲取記憶信息"""
        return [info.to_dict() for info in self.memory_infos[-limit:]]

    def get_patterns(self, limit: int = 10) -> Dict[str, Dict[str, Any]]:
        """獲取知識模式"""
        patterns = sorted(
            self.knowledge_patterns.items(), key=lambda x: x[1].confidence, reverse=True
        )[:limit]

        return {k: v.to_dict() for k, v in patterns}

    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            "is_running": self.is_running,
            "loop_interval": self.loop_interval,
            "total_memories": self.stats["total_memories"],
            "structured_memories": self.stats["structured_memories"],
            "integrated_memories": self.stats["integrated_memories"],
            "patterns_found": self.stats["patterns_found"],
            "templates_generated": self.stats["templates_generated"],
            "knowledge_base_updates": self.stats["knowledge_base_updates"],
            "neuroplasticity_encodings": self.stats["neuroplasticity_encodings"],
            "promotions_to_long_term": self.stats["promotions_to_long_term"],
            "importance_boosts": self.stats["importance_boosts"],
            "pending_integrations": len(self.integration_queue),
            "patterns_count": len(self.knowledge_patterns),
            "neuroplasticity_connected": self._neuroplasticity is not None,
        }


