"""
Angela AI v6.0 - Body Adapter System
肉身适配器系统

Handles state transfer and adaptation between different Angela versions.
处理不同Angela版本之间的状态转移与适配。

Features:
- State serialization and deserialization
- Version-specific adaptation
- Smooth state transition
- Compatibility verification

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class TransferStatus(Enum):
    """转移状态 / Transfer Status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class CompatibilityLevel(Enum):
    """兼容性级别 / Compatibility Level"""

    FULL = "full"
    PARTIAL = "partial"
    LIMITED = "limited"
    INCOMPATIBLE = "incompatible"


@dataclass
class StateSnapshot:
    """
    状态快照 / State Snapshot

    A complete snapshot of system state at a point in time.
    系统在某一时刻的完整状态快照。
    """

    timestamp: datetime = field(default_factory=datetime.now)
    version: str = "6.0.0"
    state_data: Dict[str, Any] = field(default_factory=dict)
    emotional_state: Dict[str, float] = field(default_factory=dict)
    cognitive_state: Dict[str, Any] = field(default_factory=dict)
    memory_state: Dict[str, Any] = field(default_factory=dict)
    skill_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def serialize(self) -> str:
        """序列化 / Serialize"""
        return json.dumps(
            {
                "timestamp": self.timestamp.isoformat(),
                "version": self.version,
                "state_data": self.state_data,
                "emotional_state": self.emotional_state,
                "cognitive_state": self.cognitive_state,
                "memory_state": self.memory_state,
                "skill_states": self.skill_states,
            },
            ensure_ascii=False,
            indent=2,
        )

    @classmethod
    def deserialize(cls, data: str) -> StateSnapshot:
        """反序列化 / Deserialize"""
        parsed = json.loads(data)
        snapshot = cls()
        snapshot.timestamp = datetime.fromisoformat(parsed["timestamp"])
        snapshot.version = parsed["version"]
        snapshot.state_data = parsed.get("state_data", {})
        snapshot.emotional_state = parsed.get("emotional_state", {})
        snapshot.cognitive_state = parsed.get("cognitive_state", {})
        snapshot.memory_state = parsed.get("memory_state", {})
        snapshot.skill_states = parsed.get("skill_states", {})
        return snapshot


@dataclass
class TransferRecord:
    """
    转移记录 / Transfer Record

    A record of a state transfer operation.
    状态转移操作的记录。
    """

    source_version: str
    target_version: str
    status: TransferStatus
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    transferred_states: List[str] = field(default_factory=list)
    adapted_states: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    rollback_point: Optional[StateSnapshot] = None

    def mark_completed(self):
        """标记完成 / Mark completed"""
        self.status = TransferStatus.COMPLETED
        self.completed_at = datetime.now()

    def mark_failed(self, error: str):
        """标记失败 / Mark failed"""
        self.status = TransferStatus.FAILED
        self.errors.append(error)


@dataclass
class AdaptationRule:
    """
    适配规则 / Adaptation Rule

    Rules for adapting states between versions.
    版本间状态适配规则。
    """

    source_version_pattern: str
    target_version_pattern: str
    field_mappings: Dict[str, str]
    transformations: List[Dict[str, Any]]
    compatibility_check: Dict[str, Any]


class BodyAdapter:
    """
    肉身适配器 / Body Adapter

    Manages state transfer and adaptation between Angela versions.
    管理Angela版本之间的状态转移与适配。

    Attributes:
        current_version: 当前版本 / Current version
        transfer_records: 转移记录 / Transfer records
        adaptation_rules: 适配规则 / Adaptation rules
    """

    def __init__(self, current_version: str = "6.0.0"):
        self.current_version = current_version
        self.transfer_records: List[TransferRecord] = []
        self.adaptation_rules: List[AdaptationRule] = []

    def create_snapshot(
        self,
        state_data: Dict[str, Any] = None,
        emotional_state: Dict[str, float] = None,
        cognitive_state: Dict[str, Any] = None,
        memory_state: Dict[str, Any] = None,
        skill_states: Dict[str, Dict[str, Any]] = None,
    ) -> StateSnapshot:
        """创建状态快照 / Create state snapshot"""
        return StateSnapshot(
            version=self.current_version,
            state_data=state_data or {},
            emotional_state=emotional_state or {},
            cognitive_state=cognitive_state or {},
            memory_state=memory_state or {},
            skill_states=skill_states or {},
        )

    def prepare_transfer(
        self, source_version: str, target_version: str, snapshot: StateSnapshot
    ) -> TransferRecord:
        """准备转移 / Prepare transfer"""
        record = TransferRecord(
            source_version=source_version,
            target_version=target_version,
            status=TransferStatus.PENDING,
        )

        compatibility = self.check_compatibility(source_version, target_version)
        if compatibility == CompatibilityLevel.INCOMPATIBLE:
            record.mark_failed(f"版本不兼容: {source_version} -> {target_version}")
            self.transfer_records.append(record)
            return record

        record.rollback_point = snapshot
        record.status = TransferStatus.IN_PROGRESS
        self.transfer_records.append(record)
        return record

    def execute_transfer(
        self, record: TransferRecord, snapshot: StateSnapshot
    ) -> Tuple[bool, StateSnapshot]:
        """执行转移 / Execute transfer"""
        if record.status != TransferStatus.IN_PROGRESS:
            return False, snapshot

        try:
            adapted_state = self._adapt_state(
                snapshot, record.source_version, record.target_version
            )

            record.transferred_states = list(adapted_state.state_data.keys())
            record.adapted_states = adapted_state.state_data
            record.mark_completed()

            return True, adapted_state

        except Exception as e:
            logger.error(f"Error in {__name__}: {e}", exc_info=True)
            record.mark_failed(str(e))

            if record.rollback_point:
                return False, record.rollback_point

            return False, snapshot

    def _adapt_state(
        self, snapshot: StateSnapshot, source_version: str, target_version: str
    ) -> StateSnapshot:
        """适配状态 / Adapt state"""
        adapted = StateSnapshot(
            version=target_version,
            state_data=snapshot.state_data.copy(),
            emotional_state=snapshot.emotional_state.copy(),
            cognitive_state=snapshot.cognitive_state.copy(),
            memory_state=snapshot.memory_state.copy(),
            skill_states=snapshot.skill_states.copy(),
        )

        self._apply_field_mappings(adapted, source_version, target_version)
        self._apply_transformations(adapted, source_version, target_version)

        return adapted

    def _apply_field_mappings(self, state: StateSnapshot, source_version: str, target_version: str):
        """应用字段映射 / Apply field mappings"""
        version_specific_mappings = {
            ("6.0.0", "6.0.0"): {
                "old_emotion": "emotional_state",
                "old_cognition": "cognitive_state",
            }
        }

        mappings = version_specific_mappings.get((source_version, target_version), {})

        for old_field, new_field in mappings.items():
            if old_field in state.state_data:
                value = state.state_data.pop(old_field)

                if "emotion" in new_field:
                    state.emotional_state.update(value)
                elif "cognition" in new_field:
                    state.cognitive_state.update(value)

    def _apply_transformations(
        self, state: StateSnapshot, source_version: str, target_version: str
    ):
        """应用转换 / Apply transformations"""
        if source_version == target_version:
            return

        for skill_name, skill_data in state.skill_states.items():
            if isinstance(skill_data, dict):
                if "version" in skill_data:
                    skill_data["version"] = target_version
                if "last_updated" in skill_data:
                    skill_data["last_updated"] = datetime.now().isoformat()

    def check_compatibility(self, source_version: str, target_version: str) -> CompatibilityLevel:
        """检查兼容性 / Check compatibility"""
        source_major = source_version.split(".")[0]
        target_major = target_version.split(".")[0]

        if source_major == target_major:
            return CompatibilityLevel.FULL

        if source_major == "6" and target_major == "6":
            return CompatibilityLevel.PARTIAL

        if int(target_major) > int(source_major):
            return CompatibilityLevel.LIMITED

        return CompatibilityLevel.INCOMPATIBLE

    def get_transfer_history(self) -> List[Dict[str, Any]]:
        """获取转移历史 / Get transfer history"""
        return [
            {
                "source": r.source_version,
                "target": r.target_version,
                "status": r.status.value,
                "started": r.started_at.isoformat(),
                "completed": r.completed_at.isoformat() if r.completed_at else None,
                "errors": r.errors,
            }
            for r in self.transfer_records
        ]


class BodyAdapterFactory:
    """肉身适配器工厂 / Body Adapter Factory"""

    _instances: Dict[str, BodyAdapter] = {}

    @classmethod
    def get_adapter(cls, version: str = "6.0.0") -> BodyAdapter:
        """获取适配器实例 / Get adapter instance"""
        if version not in cls._instances:
            cls._instances[version] = BodyAdapter(version)
        return cls._instances[version]


def create_body_adapter(version: str = "6.0.0") -> BodyAdapter:
    """便捷函数：创建肉身适配器"""
    return BodyAdapterFactory.get_adapter(version)


def demo():
    """演示 / Demo"""
    logger.info("🦾 肉身适配器系统演示")
    logger.info("=" * 50)

    adapter = BodyAdapter()

    snapshot = adapter.create_snapshot(
        state_data={"mode": "conversation", "topic": "software"},
        emotional_state={"happiness": 0.8, "excitement": 0.6},
        cognitive_state={"focus_level": 0.9},
        memory_state={"recent_topics": ["python", "ai"]},
        skill_states={"coding": {"level": 5, "exp": 1500}},
    )

    logger.info(f"✅ 快照版本: {snapshot.version}")
    logger.info(f"📊 状态数据: {snapshot.state_data}")
    logger.info(f"😊 情绪状态: {snapshot.emotional_state}")
    logger.info(f"🧠 认知状态: {snapshot.cognitive_state}")
    logger.info(f"💾 记忆状态: {snapshot.memory_state}")
    logger.info(f"⚡ 技能状态: {snapshot.skill_states}")

    transfer = adapter.prepare_transfer("6.0.0", "6.0.0", snapshot)
    logger.info(f"\n📋 转移记录: {transfer.source_version} -> {transfer.target_version}")

    success, new_snapshot = adapter.execute_transfer(transfer, snapshot)
    logger.info(f"🔄 转移成功: {success}")
    logger.info(f"📦 新快照版本: {new_snapshot.version}")

    compatibility = adapter.check_compatibility("6.0.0", "6.0.0")
    logger.info(f"🔗 兼容性级别: {compatibility.value}")

    logger.info("\n✅ 演示完成!")


if __name__ == "__main__":
    demo()
