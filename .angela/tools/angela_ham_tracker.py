#!/usr/bin/env python3
# =============================================================================
# FILE_HASH: ANG001
# FILE_PATH: .angela/tools/angela_ham_tracker.py
# FILE_TYPE: angela_tool
# PURPOSE: HAM (Hierarchical Associative Memory) 系统追踪器 - Angela专用
# VERSION: 6.2.1
# STATUS: production_ready
# LAYER: L2 (Memory Layer)
# DEPENDENCIES: ANG002, ANG003
# =============================================================================

"""
Angela HAM Tracker - HAM记忆系统专用追踪工具

Angela Matrix: [L2:MEM] [HAM] Memory System Tracker
α: L2 | β: 0.95 | γ: 0.95 | δ: 0.90

功能:
1. 追踪HAM记忆条目和关联关系
2. 验证HAM存储完整性
3. 分析记忆访问模式
4. 生成HAM健康报告

此工具专门用于Angela AI项目的HAM记忆系统，与通用hash_annotator不同：
- 理解HAM的层级结构
- 支持HAM特定的元数据格式
- 集成HAM的加密和压缩特性
- 遵循Angela的6层架构规范

使用方法:
    # 扫描HAM存储
    python .angela/tools/angela_ham_tracker.py scan

    # 验证HAM完整性
    python .angela/tools/angela_ham_tracker.py verify

    # 分析记忆关联
    python .angela/tools/angela_ham_tracker.py analyze --memory-id <id>

    # 生成HAM报告
    python .angela/tools/angela_ham_tracker.py report

与通用工具的区别:
    - 通用工具(hash_annotator): 适用于任何项目的文件哈希管理
    - 本工具(angela_ham_tracker): 专门为Angela的HAM系统设计
"""

import os
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
import logging
logger = logging.getLogger(__name__)

# Angela项目配置
ANGELA_ROOT = Path(__file__).parent.parent.parent
HAM_STORAGE_PATH = ANGELA_ROOT / "apps" / "backend" / "data" / "ham_storage"
HAM_HASH_DB = Path(__file__).parent.parent / "hashes" / "ham_memory_hashes.json"


@dataclass
class HAMMemoryEntry:
    """HAM记忆条目

    Angela Matrix: [L2:MEM] [HAM:ENTRY]
    """

    memory_id: str
    content_hash: str
    vector_hash: Optional[str]
    emotion_tag: Optional[str]
    priority: int
    access_count: int
    created_at: str
    last_accessed: Optional[str]
    associated_memories: List[str]
    layer: str  # L1-L6


class HAMTracker:
    """HAM记忆系统追踪器

    专门追踪和管理HAM (Hierarchical Associative Memory) 系统的记忆条目。
    与通用文件追踪器不同，此工具理解HAM的层级结构和关联关系。
    """

    def __init__(self):
        self.root = ANGELA_ROOT
        self.storage_path = HAM_STORAGE_PATH
        self.db_path = HAM_HASH_DB
        self.db = self._load_db()

    def _load_db(self) -> Dict:
        """加载HAM哈希数据库"""
        if self.db_path.exists():
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "memories": {},
            "associations": {},
            "metadata": {"created": datetime.now().isoformat(), "version": "6.2.1"},
        }

    def _save_db(self):
        """保存HAM哈希数据库"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.db, f, indent=2, ensure_ascii=False)

    def scan_ham_storage(self) -> List[HAMMemoryEntry]:
        """扫描HAM存储目录

        Returns:
            HAM记忆条目列表
        """
        entries = []

        if not self.storage_path.exists():
            print(f"HAM存储路径不存在: {self.storage_path}")
            return entries

        # 扫描记忆文件
        for mem_file in self.storage_path.rglob("*.json"):
            try:
                with open(mem_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                entry = HAMMemoryEntry(
                    memory_id=data.get("memory_id", ""),
                    content_hash=self._compute_content_hash(data),
                    vector_hash=data.get("vector_hash"),
                    emotion_tag=data.get("emotion_tag"),
                    priority=data.get("priority", 0),
                    access_count=data.get("access_count", 0),
                    created_at=data.get("created_at", ""),
                    last_accessed=data.get("last_accessed"),
                    associated_memories=data.get("associated_memories", []),
                    layer=data.get("layer", "L2"),
                )

                entries.append(entry)

                # 更新数据库
                self.db["memories"][entry.memory_id] = asdict(entry)

            except Exception as e:
                print(f"警告: 无法解析 {mem_file}: {e}")

        self._save_db()
        return entries

    def _compute_content_hash(self, data: Dict) -> str:
        """计算内容哈希"""
        content = json.dumps(data, sort_keys=True)
        return hashlib.blake2b(content.encode()).hexdigest()[:16].upper()

    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """验证HAM存储完整性

        Returns:
            (是否完整, 问题列表)
        """
        issues = []

        if not self.storage_path.exists():
            return False, ["HAM存储路径不存在"]

        # 检查记忆条目
        memories = self.scan_ham_storage()

        for entry in memories:
            # 检查关联记忆是否存在
            for assoc_id in entry.associated_memories:
                if assoc_id not in self.db["memories"]:
                    issues.append(
                        f"记忆 {entry.memory_id} 关联的记忆 {assoc_id} 不存在"
                    )

        # 检查是否有孤立记忆
        all_memory_ids = set(self.db["memories"].keys())
        referenced_ids = set()
        for entry in memories:
            referenced_ids.update(entry.associated_memories)

        orphaned = all_memory_ids - referenced_ids
        if orphaned:
            issues.append(f"发现 {len(orphaned)} 个孤立记忆: {list(orphaned)[:5]}...")

        return len(issues) == 0, issues

    def analyze_memory_patterns(self, memory_id: str) -> Dict:
        """分析记忆访问模式

        Args:
            memory_id: 记忆ID

        Returns:
            访问模式分析
        """
        if memory_id not in self.db["memories"]:
            return {"error": "记忆不存在"}

        memory = self.db["memories"][memory_id]

        # 分析关联网络
        network_depth = self._calculate_network_depth(memory_id, set())

        # 统计访问频率
        access_frequency = memory.get("access_count", 0)

        # 分析情感标签分布
        emotion = memory.get("emotion_tag", "neutral")

        return {
            "memory_id": memory_id,
            "network_depth": network_depth,
            "access_frequency": access_frequency,
            "emotion_tag": emotion,
            "layer": memory.get("layer", "L2"),
            "priority": memory.get("priority", 0),
            "associated_count": len(memory.get("associated_memories", [])),
            "health_score": self._calculate_health_score(memory),
        }

    def _calculate_network_depth(
        self, memory_id: str, visited: Set[str], depth: int = 0
    ) -> int:
        """计算关联网络深度"""
        if memory_id in visited or depth > 10:
            return depth

        visited.add(memory_id)

        memory = self.db["memories"].get(memory_id, {})
        associated = memory.get("associated_memories", [])

        if not associated:
            return depth

        max_depth = depth
        for assoc_id in associated:
            if assoc_id in self.db["memories"]:
                child_depth = self._calculate_network_depth(
                    assoc_id, visited.copy(), depth + 1
                )
                max_depth = max(max_depth, child_depth)

        return max_depth

    def _calculate_health_score(self, memory: Dict) -> float:
        """计算记忆健康分数"""
        score = 1.0

        # 关联数量适中为健康
        assoc_count = len(memory.get("associated_memories", []))
        if assoc_count == 0:
            score -= 0.3
        elif assoc_count > 100:
            score -= 0.2

        # 访问频率适中为健康
        access_count = memory.get("access_count", 0)
        if access_count == 0:
            score -= 0.2

        # 有情感标签更健康
        if not memory.get("emotion_tag"):
            score -= 0.1

        return max(0.0, score)

    def generate_report(self) -> Dict:
        """生成HAM系统健康报告"""
        memories = self.scan_ham_storage()

        total_memories = len(memories)
        if total_memories == 0:
            return {"status": "empty", "message": "HAM存储为空"}

        # 统计信息
        layer_distribution = {}
        emotion_distribution = {}
        total_associations = 0
        avg_health = 0.0

        for entry in memories:
            # 层级分布
            layer = entry.layer
            layer_distribution[layer] = layer_distribution.get(layer, 0) + 1

            # 情感分布
            emotion = entry.emotion_tag or "neutral"
            emotion_distribution[emotion] = emotion_distribution.get(emotion, 0) + 1

            # 关联总数
            total_associations += len(entry.associated_memories)

            # 健康分数
            memory_dict = self.db["memories"].get(entry.memory_id, {})
            avg_health += self._calculate_health_score(memory_dict)

        avg_health /= total_memories
        avg_associations = total_associations / total_memories

        # 完整性检查
        is_intact, issues = self.verify_integrity()

        return {
            "report_time": datetime.now().isoformat(),
            "total_memories": total_memories,
            "total_associations": total_associations,
            "avg_associations_per_memory": round(avg_associations, 2),
            "avg_health_score": round(avg_health, 2),
            "layer_distribution": layer_distribution,
            "emotion_distribution": emotion_distribution,
            "integrity_status": "healthy" if is_intact else "issues_found",
            "issues": issues[:10] if issues else [],
            "recommendations": self._generate_recommendations(memories, issues),
        }

    def _generate_recommendations(
        self, memories: List[HAMMemoryEntry], issues: List[str]
    ) -> List[str]:
        """生成优化建议"""
        recommendations = []

        if not memories:
            recommendations.append("HAM系统为空，建议导入初始记忆数据")
            return recommendations

        # 检查低访问记忆
        low_access = [m for m in memories if m.access_count < 5]
        if len(low_access) > len(memories) * 0.5:
            recommendations.append(
                f"发现 {len(low_access)} 个低访问记忆，建议进行记忆整合"
            )

        # 检查孤立记忆
        orphaned = [m for m in memories if not m.associated_memories]
        if orphaned:
            recommendations.append(f"发现 {len(orphaned)} 个孤立记忆，建议建立关联关系")

        # 检查L1层记忆过多
        l1_memories = [m for m in memories if m.layer == "L1"]
        if len(l1_memories) > len(memories) * 0.3:
            recommendations.append("L1层记忆占比过高，建议向上层提升重要记忆")

        if issues:
            recommendations.append(f"发现 {len(issues)} 个完整性问题，需要修复")

        return recommendations


def main():
    parser = argparse.ArgumentParser(
        description="Angela HAM Tracker - HAM记忆系统专用追踪工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Angela Matrix: [L2:MEM] [HAM]

示例:
    # 扫描HAM存储
    python .angela/tools/angela_ham_tracker.py scan
    
    # 验证完整性
    python .angela/tools/angela_ham_tracker.py verify
    
    # 分析特定记忆
    python .angela/tools/angela_ham_tracker.py analyze --memory-id <id>
    
    # 生成报告
    python .angela/tools/angela_ham_tracker.py report --output ham_report.json

注意：此工具专门为Angela AI的HAM系统设计，与通用文件追踪工具不同。
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # scan 命令
    scan_parser = subparsers.add_parser("scan", help="扫描HAM存储")

    # verify 命令
    verify_parser = subparsers.add_parser("verify", help="验证HAM完整性")

    # analyze 命令
    analyze_parser = subparsers.add_parser("analyze", help="分析记忆模式")
    analyze_parser.add_argument("--memory-id", required=True, help="记忆ID")

    # report 命令
    report_parser = subparsers.add_parser("report", help="生成HAM报告")
    report_parser.add_argument("--output", "-o", help="输出文件")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tracker = HAMTracker()

    if args.command == "scan":
        memories = tracker.scan_ham_storage()
        print(f"✓ 扫描完成，发现 {len(memories)} 个记忆条目")

        # 显示统计
        layer_dist = {}
        for m in memories:
            layer_dist[m.layer] = layer_dist.get(m.layer, 0) + 1

        print("\n层级分布:")
        for layer, count in sorted(layer_dist.items()):
            print(f"  {layer}: {count}")

    elif args.command == "verify":
        is_intact, issues = tracker.verify_integrity()

        if is_intact:
            print("✓ HAM存储完整性验证通过")
        else:
            print(f"✗ 发现 {len(issues)} 个问题:")
            for issue in issues[:10]:
                print(f"  - {issue}")

    elif args.command == "analyze":
        analysis = tracker.analyze_memory_patterns(args.memory_id)

        print(f"\n记忆分析: {args.memory_id}")
        print(f"  层级: {analysis.get('layer', 'N/A')}")
        print(f"  网络深度: {analysis.get('network_depth', 0)}")
        print(f"  访问频率: {analysis.get('access_frequency', 0)}")
        print(f"  健康分数: {analysis.get('health_score', 0):.2f}")
        print(f"  关联数量: {analysis.get('associated_count', 0)}")

    elif args.command == "report":
        report = tracker.generate_report()

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"✓ 报告已保存: {args.output}")
        else:
            print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
