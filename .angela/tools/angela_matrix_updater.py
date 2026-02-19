#!/usr/bin/env python3
# =============================================================================
# FILE_HASH: ANG003
# FILE_PATH: .angela/tools/angela_matrix_updater.py
# FILE_TYPE: angela_tool
# PURPOSE: Angela Matrix 标记自动更新器 - 更新代码中的Angela Matrix注释
# VERSION: 6.2.1
# STATUS: production_ready
# LAYER: ALL
# DEPENDENCIES: ANG001, ANG002
# =============================================================================

"""
Angela Matrix Updater - Angela Matrix标记自动更新器

Angela Matrix: [META] [UTIL] Matrix Annotation Updater
α: L0 | β: 0.95 | γ: 0.90 | δ: 0.95

功能:
1. 自动计算和更新Angela Matrix标记 (αβγδ)
2. 验证Matrix标记的准确性
3. 批量更新项目中的Matrix注释
4. 生成Matrix覆盖率报告

Angela Matrix标记系统:
- α (Alpha): 架构层级 (L0-L6)
- β (Beta):  功能完整度 (0.0-1.0)
- γ (Gamma): 代码完整度 (0.0-1.0)
- δ (Delta): 稳定性评分 (0.0-1.0)

此工具专门维护Angela项目的Matrix标记系统，确保所有代码文件都有准确的
Matrix评估。

使用方法:
    # 扫描并更新所有Matrix标记
    python .angela/tools/angela_matrix_updater.py update --all

    # 更新特定文件
    python .angela/tools/angela_matrix_updater.py update --file path/to/file.py

    # 验证Matrix标记
    python .angela/tools/angela_matrix_updater.py validate

    # 生成覆盖率报告
    python .angela/tools/angela_matrix_updater.py report
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
logger = logging.getLogger(__name__)

# Angela配置
ANGELA_ROOT = Path(__file__).parent.parent.parent
MATRIX_PATTERN = re.compile(
    r"Angela Matrix:\s*\[([^\]]+)\]\s*\[([^\]]+)\]\s*\n"
    r"α:\s*([\d.]+)\s*\|\s*β:\s*([\d.]+)\s*\|\s*γ:\s*([\d.]+)\s*\|\s*δ:\s*([\d.]+)",
    re.IGNORECASE,
)

LAYER_MAP = {
    "L0": 0,
    "L1": 1,
    "L2": 2,
    "L3": 3,
    "L4": 4,
    "L5": 5,
    "L6": 6,
    "ALL": -1,
    "META": -2,
}


@dataclass
class MatrixMetrics:
    """Matrix指标"""

    alpha: str  # 架构层级
    beta: float  # 功能完整度
    gamma: float  # 代码完整度
    delta: float  # 稳定性
    category: str  # 类别
    description: str  # 描述


class MatrixAnalyzer:
    """Matrix分析器"""

    def __init__(self):
        self.root = ANGELA_ROOT

    def analyze_file(self, filepath: Path) -> Optional[MatrixMetrics]:
        """分析文件并计算Matrix指标"""
        if not filepath.exists():
            return None

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            lines = content.split("\n")
            total_lines = len(lines)

            # 计算代码行数
            code_lines = sum(
                1 for line in lines if line.strip() and not line.strip().startswith("#")
            )

            # 计算注释行数
            comment_lines = sum(1 for line in lines if line.strip().startswith("#"))

            # 检测层级 (从文件路径推断)
            alpha = self._detect_layer(filepath, content)

            # 计算功能完整度 (β)
            beta = self._calculate_beta(content, comment_lines, total_lines)

            # 计算代码完整度 (γ)
            gamma = self._calculate_gamma(content, code_lines, total_lines)

            # 计算稳定性 (δ)
            delta = self._calculate_delta(content)

            # 检测类别
            category = self._detect_category(filepath)

            return MatrixMetrics(
                alpha=alpha,
                beta=round(beta, 2),
                gamma=round(gamma, 2),
                delta=round(delta, 2),
                category=category,
                description=self._generate_description(filepath, alpha, category),
            )

        except Exception as e:
            print(f"警告: 无法分析 {filepath}: {e}")
            return None

    def _detect_layer(self, filepath: Path, content: str) -> str:
        """检测架构层级"""
        path_str = str(filepath).lower()

        # 从路径推断层级
        if "autonomous" in path_str or "endocrine" in path_str or "tactile" in path_str:
            return "L1"
        elif (
            "memory" in path_str
            or "ham" in path_str
            or "cdm" in path_str
            or "lu_logic" in path_str
        ):
            return "L2"
        elif "identity" in path_str or "self_" in path_str:
            return "L3"
        elif "creation" in path_str or "avatar" in path_str or "generator" in path_str:
            return "L4"
        elif "presence" in path_str or "live2d" in path_str:
            return "L5"
        elif "execution" in path_str or "managers" in path_str or "tools" in path_str:
            return "L6"
        elif "core" in path_str and "state" in path_str:
            return "L0"
        elif "tracing" in path_str:
            return "L0"

        # 从已有Matrix注释推断
        match = MATRIX_PATTERN.search(content)
        if match:
            existing_alpha = match.group(1).strip()
            if existing_alpha in LAYER_MAP:
                return existing_alpha

        return "L0"  # 默认为L0

    def _calculate_beta(
        self, content: str, comment_lines: int, total_lines: int
    ) -> float:
        """计算功能完整度 (β)"""
        if total_lines == 0:
            return 0.0

        # 基础分数
        beta = 0.5

        # 如果有TODO或FIXME，降低分数
        if "TODO" in content or "FIXME" in content:
            beta -= 0.1

        # 如果大部分是注释，可能是骨架
        if comment_lines > total_lines * 0.6:
            beta -= 0.2

        # 检查是否有完整的类或函数实现
        if "class " in content and "def " in content:
            beta += 0.2

        # 检查是否有文档字符串
        if '"""' in content or "'''" in content:
            beta += 0.1

        return min(1.0, max(0.0, beta))

    def _calculate_gamma(
        self, content: str, code_lines: int, total_lines: int
    ) -> float:
        """计算代码完整度 (γ)"""
        if total_lines == 0:
            return 0.0

        # 代码行比例
        code_ratio = code_lines / total_lines

        # 基础分数
        gamma = code_ratio

        # 检查是否有pass语句（空实现）
        pass_count = content.count("pass")
        if pass_count > 3:
            gamma -= 0.1 * min(pass_count - 3, 5) / 5

        # 检查是否有NotImplementedError
        if "NotImplementedError" in content or "raise Exception" in content:
            gamma -= 0.15

        # 检查类型提示
        if ": " in content and "-> " in content:
            gamma += 0.1

        return min(1.0, max(0.0, gamma))

    def _calculate_delta(self, content: str) -> float:
        """计算稳定性 (δ)"""
        delta = 0.7  # 基础分数

        # 如果有测试，增加稳定性
        if "test_" in content or "pytest" in content:
            delta += 0.1

        # 如果有错误处理，增加稳定性
        if "try:" in content and "except" in content:
            delta += 0.1

        # 如果有日志记录，增加稳定性
        if "logger" in content or "logging" in content:
            delta += 0.05

        # 如果标记为实验性，降低稳定性
        if "experimental" in content.lower() or "draft" in content.lower():
            delta -= 0.2

        return min(1.0, max(0.0, delta))

    def _detect_category(self, filepath: Path) -> str:
        """检测类别"""
        path_str = str(filepath).lower()
        filename = filepath.name.lower()

        if "test" in filename:
            return "TEST"
        elif "__init__" in filename:
            return "INIT"
        elif "manager" in filename:
            return "MGR"
        elif "service" in filename:
            return "SVC"
        elif "tool" in path_str:
            return "TOOL"
        elif "config" in filename or "settings" in filename:
            return "CONFIG"
        elif "model" in filename:
            return "MODEL"
        elif "api" in path_str or "endpoint" in path_str:
            return "API"
        elif "angela" in path_str:
            return "ANG"
        else:
            return "CORE"

    def _generate_description(self, filepath: Path, alpha: str, category: str) -> str:
        """生成描述"""
        layer_names = {
            "L0": "Foundation",
            "L1": "Biology",
            "L2": "Memory",
            "L3": "Identity",
            "L4": "Creation",
            "L5": "Presence",
            "L6": "Execution",
        }

        layer_name = layer_names.get(alpha, "Unknown")
        return f"{layer_name} {category}"


class MatrixUpdater:
    """Matrix更新器"""

    def __init__(self):
        self.root = ANGELA_ROOT
        self.analyzer = MatrixAnalyzer()

    def update_file(self, filepath: Path, dry_run: bool = False) -> bool:
        """更新文件的Matrix标记"""
        metrics = self.analyzer.analyze_file(filepath)

        if not metrics:
            return False

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # 检查是否已有Matrix标记
            has_matrix = MATRIX_PATTERN.search(content)

            # 生成新的Matrix标记
            new_matrix = f"Angela Matrix: [{metrics.alpha}] [{metrics.category}] {metrics.description}\n"
            new_matrix += f"α: {metrics.alpha} | β: {metrics.beta:.2f} | γ: {metrics.gamma:.2f} | δ: {metrics.delta:.2f}"

            if dry_run:
                print(f"[DRY-RUN] {filepath}")
                print(f"  新Matrix: {new_matrix}")
                return True

            if has_matrix:
                # 替换现有标记
                new_content = MATRIX_PATTERN.sub(new_matrix, content)
            else:
                # 添加新标记（在文件头注释后）
                lines = content.split("\n")
                insert_pos = 0

                # 找到合适的插入位置
                for i, line in enumerate(lines):
                    if (
                        line.startswith("#")
                        or line.startswith('"""')
                        or line.startswith("'''")
                    ):
                        insert_pos = i + 1
                    elif line.strip() and not line.startswith("#"):
                        break

                lines.insert(insert_pos, f"\n# {new_matrix}")
                new_content = "\n".join(lines)

            # 写入文件
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)

            print(f"✓ 已更新: {filepath}")
            return True

        except Exception as e:
            print(f"✗ 更新失败: {filepath} - {e}")
            return False

    def scan_project(self) -> List[Path]:
        """扫描项目中的所有Python文件"""
        files = []

        for py_file in self.root.rglob("*.py"):
            # 排除不需要的文件
            if any(
                x in str(py_file)
                for x in ["__pycache__", ".git", "venv", "node_modules"]
            ):
                continue

            files.append(py_file)

        return files

    def validate_all(self) -> Dict:
        """验证所有文件的Matrix标记"""
        files = self.scan_project()

        results = {
            "total_files": len(files),
            "with_matrix": 0,
            "without_matrix": 0,
            "invalid_matrix": 0,
            "files": [],
        }

        for filepath in files:
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                has_matrix = bool(MATRIX_PATTERN.search(content))

                file_info = {
                    "path": str(filepath.relative_to(self.root)),
                    "has_matrix": has_matrix,
                }

                if has_matrix:
                    results["with_matrix"] += 1
                    # 验证Matrix值
                    metrics = self.analyzer.analyze_file(filepath)
                    if metrics:
                        file_info["metrics"] = {
                            "alpha": metrics.alpha,
                            "beta": metrics.beta,
                            "gamma": metrics.gamma,
                            "delta": metrics.delta,
                        }
                else:
                    results["without_matrix"] += 1

                results["files"].append(file_info)

            except Exception as e:
                logger.error(f'Error in angela_matrix_updater.py: {e}', exc_info=True)
                results["invalid_matrix"] += 1

                print(f"警告: 无法验证 {filepath}: {e}")

        return results

    def generate_coverage_report(self) -> Dict:
        """生成Matrix覆盖率报告"""
        validation = self.validate_all()

        total = validation["total_files"]
        with_matrix = validation["with_matrix"]

        coverage = (with_matrix / total * 100) if total > 0 else 0

        # 按层级统计
        layer_stats = {}
        for file_info in validation["files"]:
            if file_info.get("metrics"):
                alpha = file_info["metrics"]["alpha"]
                layer_stats[alpha] = layer_stats.get(alpha, 0) + 1

        return {
            "report_time": datetime.now().isoformat(),
            "total_files": total,
            "with_matrix": with_matrix,
            "without_matrix": validation["without_matrix"],
            "coverage_percentage": round(coverage, 2),
            "layer_distribution": layer_stats,
            "recommendations": [
                f"建议为 {validation['without_matrix']} 个文件添加Matrix标记"
                if validation["without_matrix"] > 0
                else "所有文件都有Matrix标记 ✓"
            ],
        }


def main():
    parser = argparse.ArgumentParser(
        description="Angela Matrix Updater - Matrix标记自动更新器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Angela Matrix: [META] [UTIL]

示例:
    # 更新所有文件的Matrix标记
    python .angela/tools/angela_matrix_updater.py update --all
    
    # 预览更新（不实际修改）
    python .angela/tools/angela_matrix_updater.py update --all --dry-run
    
    # 更新特定文件
    python .angela/tools/angela_matrix_updater.py update --file path/to/file.py
    
    # 验证Matrix覆盖率
    python .angela/tools/angela_matrix_updater.py validate
    
    # 生成覆盖率报告
    python .angela/tools/angela_matrix_updater.py report --output matrix_coverage.json

注意：此工具专门维护Angela的Matrix标记系统。
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # update 命令
    upd_parser = subparsers.add_parser("update", help="更新Matrix标记")
    upd_parser.add_argument("--all", action="store_true", help="更新所有文件")
    upd_parser.add_argument("--file", help="更新特定文件")
    upd_parser.add_argument("--dry-run", action="store_true", help="预览模式")

    # validate 命令
    val_parser = subparsers.add_parser("validate", help="验证Matrix标记")

    # report 命令
    rep_parser = subparsers.add_parser("report", help="生成覆盖率报告")
    rep_parser.add_argument("--output", "-o", help="输出文件")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    updater = MatrixUpdater()

    if args.command == "update":
        if args.all:
            files = updater.scan_project()
            print(f"扫描到 {len(files)} 个Python文件\n")

            success = 0
            for filepath in files:
                if updater.update_file(filepath, args.dry_run):
                    success += 1

            mode = "预览" if args.dry_run else "更新"
            print(f"\n{mode}完成: {success}/{len(files)} 个文件")

        elif args.file:
            filepath = Path(args.file)
            if not filepath.is_absolute():
                filepath = ANGELA_ROOT / filepath

            if updater.update_file(filepath, args.dry_run):
                print("✓ 成功")
            else:
                print("✗ 失败")
        else:
            print("错误: 必须指定 --all 或 --file")

    elif args.command == "validate":
        results = updater.validate_all()

        print(f"\nAngela Matrix 验证结果")
        print("=" * 60)
        print(f"总文件数: {results['total_files']}")
        print(
            f"有Matrix标记: {results['with_matrix']} ({results['with_matrix'] / results['total_files'] * 100:.1f}%)"
        )
        print(f"无Matrix标记: {results['without_matrix']}")
        print(f"无效标记: {results['invalid_matrix']}")

    elif args.command == "report":
        report = updater.generate_coverage_report()

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"✓ 报告已保存: {args.output}")
        else:
            print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
