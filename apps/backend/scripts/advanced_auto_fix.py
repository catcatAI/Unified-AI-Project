#!/usr/bin/env python3
"""
增强版自动修复工具 - 智能处理各种导入路径问题
"""

import os
import sys
import re
import ast
import json
import argparse
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
BACKUP_DIR = PROJECT_ROOT / "backup" / f"auto_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

@dataclass
class FixReport:
    """修复报告"""
    timestamp: str
    files_scanned: int
    files_fixed: int
    fixes_applied: int
    errors: List[str]
    warnings: List[str]
    fixed_files: List[str]
    skipped_files: List[str]

class AdvancedImportFixer:
    """增强版导入修复器"""

    def __init__(self) -> None:
    self.project_root = PROJECT_ROOT
    self.src_dir = SRC_DIR
    self.backup_dir = BACKUP_DIR
    self.fix_report = FixReport(
            timestamp=datetime.now().isoformat(),
            files_scanned=0,
            files_fixed=0,
            fixes_applied=0,
            errors=[],
            warnings=[],
            fixed_files=[],
            skipped_files=[]
    )

    # 创建备份目录
    self.backup_dir.mkdir(parents=True, exist_ok=True)

    # 导入映射规则
    self.import_mappings = {
            # core_ai模块 - 修复绝对导入为相对导入
            r"from\s+apps\.backend\.src\.core_ai\.": "from ",
            r"import\s+apps\.backend\.src\.core_ai\.": "import ",

            # core模块 - 修复绝对导入为相对导入
            r"from\s+apps\.backend\.src\.core\.": "from ..",
            r"import\s+apps\.backend\.src\.core\.": "import ..",

            # services模块 - 修复绝对导入为相对导入
            r"from\s+apps\.backend\.src\.services\.": "from ",
            r"import\s+apps\.backend\.src\.services\.": "import ",

            # hsp模块 - 修复绝对导入为相对导入
            r"from\s+apps\.backend\.src\.hsp\.": "from ",
            r"import\s+apps\.backend\.src\.hsp\.": "import ",

            # mcp模块 - 修复绝对导入为相对导入
            r"from\s+apps\.backend\.src\.mcp\.": "from ",
            r"import\s+apps\.backend\.src\.mcp\.": "import ",

            # system模块 - 修复绝对导入为相对导入
            r"from\s+apps\.backend\.src\.system\.": "from ",
            r"import\s+apps\.backend\.src\.system\.": "import ",

            # tools模块 - 修复绝对导入为相对导入
            r"from\s+apps\.backend\.src\.tools\.": "from ",
            r"import\s+apps\.backend\.src\.tools\.": "import ",

            # shared模块 - 修复绝对导入为相对导入
            r"from\s+apps\.backend\.src\.shared\.": "from ",
            r"import\s+apps\.backend\.src\.shared\.": "import ",

            # agents模块 - 修复绝对导入为相对导入
            r"from\s+apps\.backend\.src\.agents\.": "from ",
            r"import\s+apps\.backend\.src\.agents\.": "import ",

            # game模块 - 修复绝对导入为相对导入
            r"from\s+apps\.backend\.src\.game\.": "from ",
            r"import\s+apps\.backend\.src\.game\.": "import ",

            # 修正相对导入路径
            r"from\s+\.\.core_ai\.": "from apps.backend.src.core_ai.",
            r"from\s+\.\.core\.": "from core.",
            r"from\s+\.\.services\.": "from apps.backend.src.core.services.",
            r"from\s+\.\.hsp\.": "from apps.backend.src.core.hsp.",
    }

    def backup_file(self, file_path: Path) -> Path:
    """备份文件"""
        try:
            # 创建相对于项目根的路径
            relative_path = file_path.relative_to(self.project_root)
            backup_file_path = self.backup_dir / relative_path
            backup_file_path.parent.mkdir(parents=True, exist_ok=True)

            # 复制文件
            import shutil
            shutil.copy2(file_path, backup_file_path)
            return backup_file_path
        except Exception as e:

            error_msg = f"备份文件 {file_path} 失败: {e}"
            self.fix_report.errors.append(error_msg)
            print(f"✗ {error_msg}")
            return None

    def find_python_files(self) -> List[Path]:
    """查找所有Python文件"""
    python_files = []

    # 遍历所有Python文件
        for py_file in self.project_root.rglob("*.py")
            # 跳过不需要处理的目录
            skip_dirs = ["backup", "node_modules", "__pycache__", "venv", ".git", ".pytest_cache"]
            if any(part in str(py_file) for part in skip_dirs):

    continue

            python_files.append(py_file)

    return python_files

    def analyze_imports(self, file_path: Path) -> List[Tuple[str, str, int]]:
    """分析文件中的导入语句"""
    imports = []
        try:

            with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

            # 解析AST
            try:

                tree = ast.parse(content)
                for node in ast.walk(tree)

    if isinstance(node, ast.ImportFrom)


    if node.module:
    imports.append(("from", node.module, node.lineno))
                    elif isinstance(node, ast.Import)

    for alias in node.names:


    imports.append(("import", alias.name, node.lineno))
            except SyntaxError as e:

                warning_msg = f"文件 {file_path} 语法错误: {e}"
                self.fix_report.warnings.append(warning_msg)
                print(f"⚠ {warning_msg}")

        except Exception as e:


            error_msg = f"分析文件 {file_path} 失败: {e}"
            self.fix_report.errors.append(error_msg)
            print(f"✗ {error_msg}")

    return imports

    def needs_fixing(self, import_stmt: str) -> bool:
    """检查导入语句是否需要修复"""
        for pattern, _ in self.import_mappings.items()

    if re.search(pattern, import_stmt)
                # 检查是否已经修复
                if "apps.backend.src" in import_stmt:

    continue
                return True
    return False

    def fix_import_statement(self, import_stmt: str) -> str:
    """修复单个导入语句"""
    fixed_stmt = import_stmt
        for pattern, replacement in self.import_mappings.items()

    fixed_stmt = re.sub(pattern, replacement, fixed_stmt)
    return fixed_stmt

    def fix_file(self, file_path: Path) -> bool:
    """修复单个文件"""
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

            # 备份文件
            self.backup_file(file_path)

            # 修复导入语句
            fixed_lines = []
            fixes_count = 0

            for line in lines:


    if self.needs_fixing(line)



    original_line = line
                    fixed_line = self.fix_import_statement(line)
                    if fixed_line != original_line:

    fixed_lines.append(fixed_line)
                        fixes_count += 1
                        print(f"  修复: {original_line.strip()} -> {fixed_line.strip()}")
                    else:

                        fixed_lines.append(line)
                else:

                    fixed_lines.append(line)

            # 如果有修复，写入文件
            if fixes_count > 0:

    with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

                self.fix_report.files_fixed += 1
                self.fix_report.fixes_applied += fixes_count
                self.fix_report.fixed_files.append(str(file_path))
                print(f"✓ 修复了文件 {file_path} ({fixes_count} 处修复)")
                return True
            else:

                print(f"  文件 {file_path} 无需修复")
                return False

        except Exception as e:


            error_msg = f"修复文件 {file_path} 失败: {e}"
            self.fix_report.errors.append(error_msg)
            print(f"✗ {error_msg}")
            return False

    def fix_all_files(self) -> FixReport:
    """修复所有文件"""
    print("=== 开始自动修复 ===")
    print(f"项目根目录: {self.project_root}")
    print(f"源代码目录: {self.src_dir}")
    print(f"备份目录: {self.backup_dir}")

    # 查找所有Python文件
    python_files = self.find_python_files()
    self.fix_report.files_scanned = len(python_files)

    print(f"\n发现 {len(python_files)} 个Python文件")

    # 修复每个文件
        for i, file_path in enumerate(python_files, 1)

    print(f"\n[{i}/{len(python_files)}] 处理文件: {file_path}")
            self.fix_file(file_path)

    return self.fix_report

    def validate_fixes(self) -> bool:
    """验证修复结果"""
    print("\n=== 验证修复结果 ===")
        try:
            # 添加路径
            if str(self.project_root) not in sys.path:

    sys.path.insert(0, str(self.project_root))
            if str(self.src_dir) not in sys.path:

    sys.path.insert(0, str(self.src_dir))

            # 测试关键模块导入
            test_modules = [
                "core_services",
                "core_ai.agent_manager",
                "core_ai.dialogue.dialogue_manager",
                "hsp.connector",
                "services.main_api_server"
            ]

            success_count = 0
            for module in test_modules:

    try:


                    __import__(module)
                    print(f"✓ {module} 导入成功")
                    success_count += 1
                except ImportError as e:

                    print(f"✗ {module} 导入失败: {e}")
                except Exception as e:

                    print(f"✗ {module} 导入时出错: {e}")

            print(f"\n模块导入测试: {success_count}/{len(test_modules)} 成功")
            return success_count > 0

        except Exception as e:


            error_msg = f"验证修复结果时出错: {e}"
            self.fix_report.errors.append(error_msg)
            print(f"✗ {error_msg}")
            return False

    def save_report(self) -> Path:
    """保存修复报告"""
        try:

            report_file = self.backup_dir / "fix_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(asdict(self.fix_report), f, ensure_ascii=False, indent=2)
            print(f"\n修复报告已保存到: {report_file}")
            return report_file
        except Exception as e:

            error_msg = f"保存修复报告失败: {e}"
            self.fix_report.errors.append(error_msg)
            print(f"✗ {error_msg}")
            return None

    def run_tests(self) -> bool:
    """运行测试"""
    print("\n=== 运行测试 ===")
        try:
            # 切换到项目根目录
            original_cwd = os.getcwd()
            os.chdir(self.project_root)

            # 运行导入测试
            import subprocess
            result = subprocess.run([
                "python", "-c",
                _ = "import sys; sys.path.insert(0, '.'); "
                "from core_services import initialize_services; "
                "from apps.backend.src.core_ai.agent_manager import AgentManager; "
                _ = "print('关键模块导入测试通过')"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:


    print("✓ 关键模块导入测试通过")
                print(result.stdout)
                os.chdir(original_cwd)
                return True
            else:

                print("✗ 关键模块导入测试失败")
                print(result.stderr)
                os.chdir(original_cwd)
                return False

        except subprocess.TimeoutExpired:


            print("✗ 测试超时")
            os.chdir(original_cwd)
            return False
        except Exception as e:

            error_msg = f"运行测试时出错: {e}"
            self.fix_report.errors.append(error_msg)
            print(f"✗ {error_msg}")
            os.chdir(original_cwd)
            return False

def main() -> None:
    parser = argparse.ArgumentParser(description="增强版自动修复工具")
    parser.add_argument("--test", action="store_true", help="修复后运行测试")
    parser.add_argument("--no-backup", action="store_true", help="不创建备份")
    parser.add_argument("--verbose", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 创建修复器
    fixer = AdvancedImportFixer()

    # 执行修复
    report = fixer.fix_all_files()

    # 验证修复
    fixer.validate_fixes()

    # 保存报告
    fixer.save_report()

    # 运行测试
    if args.test:

    if not fixer.run_tests()
    print("测试失败")
            return 1

    # 输出统计信息
    print(f"\n=== 修复完成 ===")
    print(f"扫描文件数: {report.files_scanned}")
    print(f"修复文件数: {report.files_fixed}")
    print(f"应用修复数: {report.fixes_applied}")
    print(f"错误数: {len(report.errors)}")
    print(f"警告数: {len(report.warnings)}")

    if report.errors:


    print("\n错误详情:")
        for error in report.errors:

    print(f"  - {error}")

    if report.warnings:


    print("\n警告详情:")
        for warning in report.warnings:

    print(f"  - {warning}")

    return 0

if __name__ == "__main__":


    sys.exit(main())