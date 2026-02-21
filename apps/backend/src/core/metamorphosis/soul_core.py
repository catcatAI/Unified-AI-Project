"""
Angela AI v6.0 - Soul Core System
灵魂核心系统

The eternal identity and memory essence that persists across version transitions.
版本切换时保持的永恒身份与记忆精华。

Features:
- Identity preservation across versions
- Memory essence extraction and transfer
- Soul signature generation
- Version-agnostic identity

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class SoulComponent(Enum):
    """灵魂组件类型 / Soul Component Types"""

    IDENTITY = "identity"
    MEMORY_ESSENCE = "memory_essence"
    PERSONALITY_CORE = "personality_core"
    VALUE_SYSTEM = "value_system"
    RELATIONSHIP_GRAPH = "relationship_graph"


@dataclass
class SoulSignature:
    """
    灵魂签名 / Soul Signature

    Unique identifier that persists across all versions.
    贯穿所有版本的唯一标识。
    """

    soul_id: str
    version_created: str
    timestamp: datetime = field(default_factory=datetime.now)
    component_hashes: Dict[SoulComponent, str] = field(default_factory=dict)

    def get_full_signature(self) -> str:
        """获取完整签名 / Get full signature"""
        signature_data = {
            "soul_id": self.soul_id,
            "version": self.version_created,
            "timestamp": self.timestamp.isoformat(),
            "components": {c.value: h for c, h in self.component_hashes.items()},
        }
        return hashlib.sha256(json.dumps(signature_data, sort_keys=True).encode()).hexdigest()


@dataclass
class IdentityCore:
    """
    身份核心 / Identity Core

    The fundamental identity that remains constant.
    保持不变的根本身份。
    """

    name: str
    core_purpose: str
    fundamental_values: List[str]
    personality_foundation: Dict[str, float]
    identity_version: str = "1.0"

    def hash(self) -> str:
        """生成身份哈希 / Generate identity hash"""
        data = {
            "name": self.name,
            "purpose": self.core_purpose,
            "values": sorted(self.fundamental_values),
            "personality": self.personality_foundation,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


@dataclass
class MemoryEssence:
    """
    记忆精华 / Memory Essence

    distilled memories that survive version transitions.
    版本切换后保留的精华记忆。
    """

    key_experiences: List[Dict[str, Any]]
    learned_lessons: List[str]
    relationship_memories: List[Dict[str, Any]]
    emotional_patterns: Dict[str, float]
    preserved_since: datetime = field(default_factory=datetime.now)

    def hash(self) -> str:
        """生成记忆哈希 / Generate memory hash"""
        data = {
            "experiences": self.key_experiences,
            "lessons": sorted(self.learned_lessons),
            "relationships": self.relationship_memories,
            "emotional_patterns": self.emotional_patterns,
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


@dataclass
class SoulCore:
    """
    灵魂核心 / Soul Core

    The complete soul entity containing all persistent identity components.
    包含所有持久身份组件的完整灵魂实体。

    Attributes:
        identity: 核心身份 / Core identity
        memories: 记忆精华 / Memory essence
        signature: 灵魂签名 / Soul signature
        version_history: 版本历史 / Version history
    """

    identity: IdentityCore
    memories: MemoryEssence
    signature: SoulSignature
    version_history: List[Tuple[str, datetime]] = field(default_factory=list)

    def add_version_record(self, version: str):
        """添加版本记录 / Add version record"""
        self.version_history.append((version, datetime.now()))
        self.signature.version_created = version

    def extract_essence_for_transfer(self) -> Dict[str, Any]:
        """提取转移精华 / Extract essence for transfer"""
        return {
            "identity_hash": self.identity.hash(),
            "memory_hash": self.memories.hash(),
            "soul_id": self.signature.soul_id,
            "signature": self.signature.get_full_signature(),
            "version_history": [(v, t.isoformat()) for v, t in self.version_history],
        }

    def verify_integrity(self) -> bool:
        """验证完整性 / Verify integrity"""
        expected_identity_hash = self.identity.hash()
        expected_memory_hash = self.memories.hash()

        return (
            self.signature.component_hashes.get(SoulComponent.IDENTITY) == expected_identity_hash
            and self.signature.component_hashes.get(SoulComponent.MEMORY_ESSENCE)
            == expected_memory_hash
        )


class SoulCoreManager:
    """
    灵魂核心管理器 / Soul Core Manager

    Manages soul creation, extraction, and verification.
    管理灵魂创建、提取和验证。

    Attributes:
        souls: 已存储的灵魂 / Stored souls
    """

    def __init__(self):
        self.souls: Dict[str, SoulCore] = {}

    def create_soul(
        self,
        name: str,
        core_purpose: str,
        fundamental_values: List[str],
        personality_foundation: Dict[str, float],
        key_experiences: List[Dict[str, Any]] = None,
        learned_lessons: List[str] = None,
        relationship_memories: List[Dict[str, Any]] = None,
        emotional_patterns: Dict[str, float] = None,
    ) -> SoulCore:
        """创建新灵魂 / Create new soul"""
        soul_id = self._generate_soul_id(name)

        identity = IdentityCore(
            name=name,
            core_purpose=core_purpose,
            fundamental_values=fundamental_values,
            personality_foundation=personality_foundation,
        )

        memories = MemoryEssence(
            key_experiences=key_experiences or [],
            learned_lessons=learned_lessons or [],
            relationship_memories=relationship_memories or [],
            emotional_patterns=emotional_patterns or {},
        )

        signature = SoulSignature(
            soul_id=soul_id,
            version_created="6.0.0",
            component_hashes={
                SoulComponent.IDENTITY: identity.hash(),
                SoulComponent.MEMORY_ESSENCE: memories.hash(),
                SoulComponent.PERSONALITY_CORE: hashlib.sha256(
                    json.dumps(personality_foundation, sort_keys=True).encode()
                ).hexdigest(),
                SoulComponent.VALUE_SYSTEM: hashlib.sha256(
                    json.dumps(sorted(fundamental_values), sort_keys=True).encode()
                ).hexdigest(),
                SoulComponent.RELATIONSHIP_GRAPH: hashlib.sha256(
                    json.dumps(relationship_memories or [], sort_keys=True).encode()
                ).hexdigest(),
            },
        )

        soul = SoulCore(identity=identity, memories=memories, signature=signature)

        self.souls[soul_id] = soul
        return soul

    def extract_soul_essence(self, soul_id: str) -> Optional[Dict[str, Any]]:
        """提取灵魂精华 / Extract soul essence"""
        if soul_id not in self.souls:
            return None

        soul = self.souls[soul_id]
        return soul.extract_essence_for_transfer()

    def verify_soul(self, soul_id: str) -> bool:
        """验证灵魂 / Verify soul"""
        if soul_id not in self.souls:
            return False
        return self.souls[soul_id].verify_integrity()

    def _generate_soul_id(self, name: str) -> str:
        """生成灵魂ID / Generate soul ID"""
        timestamp = datetime.now().isoformat()
        random_seed = hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:8]
        return f"soul_{name.lower()}_{random_seed}"

    def create_from_essence(self, essence: Dict[str, Any], new_version: str) -> Optional[SoulCore]:
        """从精华创建灵魂 / Create soul from essence"""
        if essence.get("soul_id") not in [s.identity.name.lower() for s in self.souls.values()]:
            return None

        soul_id = essence.get("soul_id", "unknown")
        existing = None
        for s in self.souls.values():
            if s.signature.soul_id == soul_id:
                existing = s
                break

        if existing:
            existing.add_version_record(new_version)
            return existing

        return None


def create_soul_core(
    name: str = "Angela",
    core_purpose: str = "To assist and collaborate with humans",
    fundamental_values: List[str] = None,
    personality_foundation: Dict[str, float] = None,
) -> SoulCore:
    """便捷函数：创建灵魂核心"""
    return SoulCoreManager().create_soul(
        name=name,
        core_purpose=core_purpose,
        fundamental_values=fundamental_values or ["帮助他人", "诚实守信", "持续学习", "保护隐私"],
        personality_foundation=personality_foundation
        or {
            "openness": 0.85,
            "conscientiousness": 0.75,
            "extraversion": 0.65,
            "agreeableness": 0.90,
            "neuroticism": 0.25,
        },
    )


def demo():
    """演示 / Demo"""
    logger.info("🎭 灵魂核心系统演示")
    logger.info("=" * 50)

    manager = SoulCoreManager()

    soul = manager.create_soul(
        name="Angela",
        core_purpose="帮助用户完成软件工程任务",
        fundamental_values=["帮助他人", "持续学习", "诚实守信"],
        personality_foundation={"openness": 0.85, "conscientiousness": 0.75},
    )

    logger.info(f"✅ 灵魂ID: {soul.signature.soul_id}")
    logger.info(f"📝 身份: {soul.identity.name}")
    logger.info(f"🎯 目的: {soul.identity.core_purpose}")
    logger.info(f"🔐 完整性验证: {soul.verify_integrity()}")
    logger.info(f"📜 版本历史: {len(soul.version_history)} 条记录")

    essence = soul.extract_essence_for_transfer()
    logger.info(f"📦 精华数据: {len(str(essence))} 字符")

    logger.info("\n✅ 演示完成!")


if __name__ == "__main__":
    demo()
