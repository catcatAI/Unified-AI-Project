#!/usr/bin/env python3
# =============================================================================
# FILE_HASH: ANG002
# FILE_PATH: .angela/tools/angela_layer_validator.py
# FILE_TYPE: angela_tool
# PURPOSE: Angela 6层架构验证器 - 验证L1-L6层完整性
# VERSION: 6.2.1
# STATUS: production_ready
# LAYER: ALL (L1-L6)
# DEPENDENCIES: ANG001, ANG003
# =============================================================================

"""
Angela Layer Validator - 6层生命架构验证器

Angela Matrix: [L1-L6] [ARCH] Layer Architecture Validator
α: ALL | β: 0.90 | γ: 0.85 | δ: 0.80

功能:
1. 验证6层架构的完整性
2. 检查层间依赖关系
3. 分析各层实现状态
4. 生成架构健康报告

6层架构:
- L1: Biology Layer (生物层) - 内分泌系统、触觉系统
- L2: Memory Layer (记忆层) - HAM, CDM, HSM, LU  [✅ 已实现]
- L3: Identity Layer (身份层) - 自我意识、身份认知
- L4: Creation Layer (创造层) - 创造力、美学
- L5: Presence Layer (存在层) - 环境感知
- L6: Execution Layer (执行层) - 行动执行  [✅ 已实现]

与通用工具的区别:
- 通用工具: 检查代码结构和依赖
- 本工具: 专门验证Angela的6层生命架构实现
"""

import argparse
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Angela配置
ANGELA_ROOT = Path(__file__).parent.parent.parent
LAYERS = {
    "L1": {
        "name": "Biology Layer",
        "description": "生物层 - 内分泌系统、触觉系统",
        "key_files": [
            "apps/backend/src/core/autonomous/endocrine_system.py",
            "apps/backend/src/core/autonomous/physiological_tactile.py",
        ],
        "status": "partial",
    },
    "L2": {
        "name": "Memory Layer",
        "description": "记忆层 - HAM, CDM, HSM, LU",
        "key_files": [
            "apps/backend/src/ai/memory/ham_memory/ham_manager.py",
            "apps/backend/src/ai/memory/lu_logic/logic_unit.py",
            "apps/backend/src/core/cdm_dividend_model.py",
        ],
        "status": "implemented",
    },
    "L3": {
        "name": "Identity Layer",
        "description": "身份层 - 自我意识、身份认知",
        "key_files": [
            "apps/backend/src/core/autonomous/self_generation.py",
            "apps/backend/src/ai/identity/",
        ],
        "status": "partial",
    },
    "L4": {
        "name": "Creation Layer",
        "description": "创造层 - 创造力、美学",
        "key_files": [
            "apps/backend/src/core/autonomous/live2d_avatar_generator.py",
        ],
        "status": "skeleton",
    },
    "L5": {
        "name": "Presence Layer",
        "description": "存在层 - 环境感知",
        "key_files": [
            "apps/backend/src/core/autonomous/live2d_integration.py",
        ],
        "status": "partial",
    },
    "L6": {
        "name": "Execution Layer",
        "description": "执行层 - 行动执行",
        "key_files": [
            "apps/backend/src/core/managers/execution_manager.py",
            "apps/backend/src/core/tools/",
        ],
        "status": "implemented",
    },
}


class LayerValidator:
    """6层架构验证器"""

    def __init__(self):
        self.root = ANGELA_ROOT
        self.layers = LAYERS

    def validate_layer(self, layer_id: str) -> Dict:
        """验证指定层"""
        if layer_id not in self.layers:
            return {"error": f"未知层级: {layer_id}"}

        layer = self.layers[layer_id]
        results = {
            "layer_id": layer_id,
            "name": layer["name"],
            "description": layer["description"],
            "expected_files": [],
            "existing_files": [],
            "missing_files": [],
            "implementation_status": layer["status"],
            "completeness": 0.0,
        }

        for file_pattern in layer["key_files"]:
            full_path = self.root / file_pattern

            if "*" in file_pattern:
                # 通配符模式
                matching_files = list(self.root.glob(file_pattern))
                if matching_files:
                    results["existing_files"].extend(
                        [str(f.relative_to(self.root)) for f in matching_files]
                    )
                else:
                    results["missing_files"].append(file_pattern)
            else:
                # 具体文件
                results["expected_files"].append(file_pattern)
                if full_path.exists():
                    results["existing_files"].append(file_pattern)

                    # 检查文件是否完整（非骨架）
                    completeness = self._check_file_completeness(full_path)
                    results["completeness"] = max(results["completeness"], completeness)
                else:
                    results["missing_files"].append(file_pattern)

        # 计算完成度
        if results["expected_files"]:
            file_ratio = len(results["existing_files"]) / len(results["expected_files"])
            results["completeness"] = (file_ratio + results["completeness"]) / 2

        return results

    def _check_file_completeness(self, filepath: Path) -> float:
        """检查文件完成度"""
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            lines = content.split("\n")
            total_lines = len(lines)

            # 计算注释掉的代码比例
            commented_lines = sum(1 for line in lines if line.strip().startswith("#"))
            empty_lines = sum(1 for line in lines if not line.strip())

            # 实际代码行
            code_lines = total_lines - commented_lines - empty_lines

            if total_lines == 0:
                return 0.0

            # 如果大部分是注释，完成度低
            if commented_lines > code_lines * 2:
                return 0.3  # 骨架状态
            elif commented_lines > code_lines:
                return 0.6  # 部分实现
            else:
                return 0.9  # 基本完成

        except Exception as e:
            logger.error(f"Error in angela_layer_validator.py: {e}", exc_info=True)
            return 0.0

    def validate_all_layers(self) -> Dict[str, Dict]:
        """验证所有层"""
        results = {}

        for layer_id in ["L1", "L2", "L3", "L4", "L5", "L6"]:
            results[layer_id] = self.validate_layer(layer_id)

        return results

    def check_layer_dependencies(self) -> List[Dict]:
        """检查层间依赖关系"""
        issues = []

        # L2应该依赖L1
        l2_files = self._get_layer_files("L2")
        for filepath in l2_files:
            if self._file_imports_from(filepath, "L1"):
                pass  # 正常
            else:
                issues.append(
                    {
                        "severity": "warning",
                        "message": f"L2文件 {filepath} 可能缺少对L1的引用",
                        "layer": "L2",
                    }
                )

        # L6应该依赖L2
        l6_files = self._get_layer_files("L6")
        for filepath in l6_files:
            if self._file_imports_from(filepath, "L2"):
                pass  # 正常
            else:
                issues.append(
                    {
                        "severity": "info",
                        "message": f"L6文件 {filepath} 未直接引用L2",
                        "layer": "L6",
                    }
                )

        return issues

    def _get_layer_files(self, layer_id: str) -> List[str]:
        """获取层的所有文件"""
        layer = self.layers.get(layer_id, {})
        files = []

        for pattern in layer.get("key_files", []):
            if "*" in pattern:
                files.extend([str(f.relative_to(self.root)) for f in self.root.glob(pattern)])
            else:
                files.append(pattern)

        return files

    def _file_imports_from(self, filepath: str, from_layer: str) -> bool:
        """检查文件是否导入自指定层"""
        full_path = self.root / filepath

        if not full_path.exists():
            return False

        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # 检查是否导入自指定层的文件
            from_layer_files = self._get_layer_files(from_layer)

            for from_file in from_layer_files:
                module_name = from_file.replace("/", ".").replace(".py", "")
                if module_name in content or from_file.replace("/", ".") in content:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error in angela_layer_validator.py: {e}", exc_info=True)
            return False

    def generate_architecture_report(self) -> Dict:
        """生成架构健康报告"""
        validation_results = self.validate_all_layers()
        dependency_issues = self.check_layer_dependencies()

        # 统计
        total_layers = 6
        implemented_layers = sum(
            1 for r in validation_results.values() if r.get("completeness", 0) > 0.8
        )
        partial_layers = sum(
            1 for r in validation_results.values() if 0.4 < r.get("completeness", 0) <= 0.8
        )
        missing_layers = sum(
            1 for r in validation_results.values() if r.get("completeness", 0) <= 0.4
        )

        # 计算整体健康度
        total_completeness = sum(r.get("completeness", 0) for r in validation_results.values())
        overall_health = total_completeness / total_layers

        return {
            "report_time": datetime.now().isoformat(),
            "overall_health": round(overall_health, 2),
            "summary": {
                "total_layers": total_layers,
                "implemented": implemented_layers,
                "partial": partial_layers,
                "missing": missing_layers,
            },
            "layer_details": validation_results,
            "dependency_issues": dependency_issues,
            "recommendations": self._generate_recommendations(validation_results),
        }

    def _generate_recommendations(self, results: Dict[str, Dict]) -> List[str]:
        """生成架构建议"""
        recommendations = []

        # 按完成度排序
        sorted_layers = sorted(results.items(), key=lambda x: x[1].get("completeness", 0))

        for layer_id, result in sorted_layers:
            completeness = result.get("completeness", 0)

            if completeness < 0.3:
                recommendations.append(f"🔴 {layer_id} ({result['name']}): 严重缺失，需要立即实现")
            elif completeness < 0.6:
                recommendations.append(f"🟡 {layer_id} ({result['name']}): 部分实现，需要继续完善")
            elif result.get("missing_files"):
                recommendations.append(
                    f"🟢 {layer_id} ({result['name']}): 基本实现，但缺少文件: {', '.join(result['missing_files'][:3])}"
                )

        return recommendations


def main():
    parser = argparse.ArgumentParser(
        description="Angela 6层架构验证器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Angela Matrix: [L1-L6] [ARCH]

6层生命架构:
  L1 (Biology)    : 生物层 - 内分泌系统、触觉系统
  L2 (Memory)     : 记忆层 - HAM, CDM, HSM, LU  [✅ 已实现]
  L3 (Identity)   : 身份层 - 自我意识、身份认知
  L4 (Creation)   : 创造层 - 创造力、美学
  L5 (Presence)   : 存在层 - 环境感知
  L6 (Execution)  : 执行层 - 行动执行  [✅ 已实现]

示例:
    # 验证所有层
    python .angela/tools/angela_layer_validator.py validate

    # 验证特定层
    python .angela/tools/angela_layer_validator.py validate --layer L2

    # 检查层间依赖
    python .angela/tools/angela_layer_validator.py dependencies

    # 生成完整报告
    python .angela/tools/angela_layer_validator.py report --output angela_arch_report.json

注意：此工具专门验证Angela的6层生命架构，与通用代码结构检查工具不同。
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # validate 命令
    val_parser = subparsers.add_parser("validate", help="验证层")
    val_parser.add_argument("--layer", choices=["L1", "L2", "L3", "L4", "L5", "L6"], help="特定层")

    # dependencies 命令
    dep_parser = subparsers.add_parser("dependencies", help="检查层间依赖")

    # report 命令
    rep_parser = subparsers.add_parser("report", help="生成架构报告")
    rep_parser.add_argument("--output", "-o", help="输出文件")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    validator = LayerValidator()

    if args.command == "validate":
        if args.layer:
            result = validator.validate_layer(args.layer)
            print(f"\n{args.layer}: {result['name']}")
            print(f"  状态: {result['implementation_status']}")
            print(f"  完成度: {result['completeness'] * 100:.1f}%")
            print(f"  现有文件: {len(result['existing_files'])}")
            print(f"  缺失文件: {len(result['missing_files'])}")

            if result["missing_files"]:
                print(f"\n  缺失:")
                for f in result["missing_files"]:
                    print(f"    - {f}")
        else:
            results = validator.validate_all_layers()

            print("\n" + "=" * 60)
            print("Angela 6层架构验证结果")
            print("=" * 60)

            for layer_id, result in results.items():
                status_icon = {
                    "implemented": "✅",
                    "partial": "🟡",
                    "skeleton": "🔴",
                }.get(result["implementation_status"], "⚪")

                print(f"\n{status_icon} {layer_id}: {result['name']}")
                print(f"   完成度: {result['completeness'] * 100:.1f}%")
                print(f"   文件: {len(result['existing_files'])}/{len(result['expected_files'])}")

    elif args.command == "dependencies":
        issues = validator.check_layer_dependencies()

        if issues:
            print(f"\n发现 {len(issues)} 个依赖问题:")
            for issue in issues:
                icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue["severity"], "•")
                print(f"  {icon} [{issue['layer']}] {issue['message']}")
        else:
            print("\n✅ 层间依赖关系正常")

    elif args.command == "report":
        report = validator.generate_architecture_report()

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"✓ 报告已保存: {args.output}")
        else:
            print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
