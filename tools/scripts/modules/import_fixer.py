#!/usr/bin/env python3
"""
导入修复模块 - 处理导入路径问题
"""

import re
import traceback
from pathlib import Path
from typing import Dict, List, Tuple

class ImportFixer:
    """导入修复器"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.backend_root = project_root / "apps" / "backend"
        self.src_dir = self.backend_root / "src"

    # 导入映射表 - 从enhanced_auto_fix.py迁移
    self.import_mappings = {
            # 旧的core_ai导入映射
            "from core_ai.": "from apps.backend.src.ai.",
            "import core_ai.": "import apps.backend.src.ai.",
            "from core.": "from apps.backend.src.core.",
            "import core.": "import apps.backend.src.core.",
            "from services.": "from apps.backend.src.core.services.",
            "import services.": "import apps.backend.src.core.services.",
            "from tools.": "from apps.backend.src.core.tools.",
            "import tools.": "import apps.backend.src.core.tools.",
            "from hsp.": "from apps.backend.src.core.hsp.",
            "import hsp.": "import apps.backend.src.core.hsp.",
            "from shared.": "from apps.backend.src.core.shared.",
            "import shared.": "import apps.backend.src.core.shared.",
            "from agents.": "from apps.backend.src.ai.agents.",
            "import agents.": "import apps.backend.src.ai.agents.",

            # 具体模块映射
            "from core_ai.audio.": "from apps.backend.src.ai.audio.",
            "from core_ai.code_understanding.": "from apps.backend.src.ai.code_understanding.",
            "from core_ai.compression.": "from apps.backend.src.ai.compression.",
            "from core_ai.concept_models.": "from apps.backend.src.ai.concept_models.",
            "from core_ai.crisis.": "from apps.backend.src.ai.crisis.",
            "from core_ai.deep_mapper.": "from apps.backend.src.ai.deep_mapper.",
            "from core_ai.dialogue.": "from apps.backend.src.ai.dialogue.",
            "from core_ai.discovery.": "from apps.backend.src.ai.discovery.",
            "from core_ai.emotion.": "from apps.backend.src.ai.emotion.",
            "from core_ai.evaluation.": "from apps.backend.src.ai.evaluation.",
            "from core_ai.formula_engine.": "from apps.backend.src.ai.formula_engine.",
            "from core_ai.integration.": "from apps.backend.src.ai.integration.",
            "from core_ai.knowledge_graph.": "from apps.backend.src.ai.knowledge_graph.",
            "from core_ai.language_models.": "from apps.backend.src.ai.language_models.",
            "from core_ai.learning.": "from apps.backend.src.ai.learning.",
            "from core_ai.lis.": "from apps.backend.src.ai.lis.",
            "from core_ai.memory.": "from apps.backend.src.ai.memory.",
            "from core_ai.meta.": "from apps.backend.src.ai.meta.",
            "from core_ai.meta_formulas.": "from apps.backend.src.ai.meta_formulas.",
            "from core_ai.optimization.": "from apps.backend.src.ai.optimization.",
            "from core_ai.personality.": "from apps.backend.src.ai.personality.",
            "from core_ai.rag.": "from apps.backend.src.ai.rag.",
            "from core_ai.reasoning.": "from apps.backend.src.ai.reasoning.",
            "from core_ai.symbolic_space.": "from apps.backend.src.ai.symbolic_space.",
            "from core_ai.test_utils.": "from apps.backend.src.ai.test_utils.",
            "from core_ai.time.": "from apps.backend.src.ai.time.",
            "from core_ai.translation.": "from apps.backend.src.ai.translation.",
            "from core_ai.trust.": "from apps.backend.src.ai.trust.",
            "from core_ai.world_model.": "from apps.backend.src.ai.world_model.",

            # 测试文件导入映射
            "from tests.core_ai.": "from tests.",
            "from tests.agents.": "from tests.agents.",
            "from tests.hsp.": "from tests.hsp.",
            "from tests.services.": "from tests.services.",
            "from tests.shared.": "from tests.shared.",
            "from tests.tools.": "from tests.tools.",
    }

    # 相对导入修复模式
    self.relative_patterns = [
            # 单点相对导入
            (r'from\s+\.\s+core_ai\s*\.', 'from apps.backend.src.ai.'),
            (r'from\s+\.\s+core\s*\.', 'from apps.backend.src.core.'),
            (r'from\s+\.\s+services\s*\.', 'from apps.backend.src.core.services.'),
            (r'from\s+\.\s+tools\s*\.', 'from apps.backend.src.core.tools.'),
            (r'from\s+\.\s+hsp\s*\.', 'from apps.backend.src.core.hsp.'),
            (r'from\s+\.\s+shared\s*\.', 'from apps.backend.src.core.shared.'),
            (r'from\s+\.\s+agents\s*\.', 'from apps.backend.src.ai.agents.'),

            # 双点相对导入
            (r'from\s+\.\.\s+core_ai\s*\.', 'from apps.backend.src.ai.'),
            (r'from\s+\.\.\s+core\s*\.', 'from apps.backend.src.core.'),
            (r'from\s+\.\.\s+services\s*\.', 'from apps.backend.src.core.services.'),
            (r'from\s+\.\.\s+tools\s*\.', 'from apps.backend.src.core.tools.'),
            (r'from\s+\.\.\s+hsp\s*\.', 'from apps.backend.src.core.hsp.'),
            (r'from\s+\.\.\s+shared\s*\.', 'from apps.backend.src.core.shared.'),
            (r'from\s+\.\.\s+agents\s*\.', 'from apps.backend.src.ai.agents.'),
    ]

    def find_python_files(self, target: str = None) -> List[Path]:
        """查找Python文件"""
        python_files = []

        if target:
            # 处理特定目标
            target_path = Path(target)
            if target_path.is_absolute():
                search_path = target_path
            else:
                search_path = self.project_root / target

            if search_path.is_file() and search_path.suffix == '.py':
                _ = python_files.append(search_path)
            elif search_path.is_dir():
                _ = python_files.extend(search_path.rglob("*.py"))
        else:
            # 搜索整个项目
            for py_file in self.project_root.rglob("*.py"):
                # 跳过特定目录
                if any(part in str(py_file) for part in [
                    "backup", "node_modules", "__pycache__", "venv",
                    ".git", "dist", "build", "data/runtime_data/.pytest_cache"
                ]):
                    continue
                _ = python_files.append(py_file)

        return python_files

    def fix_imports_in_file(self, file_path: Path) -> Tuple[bool, str, Dict]:
        """修复文件中的导入"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content
            fixes_made = []

            # 应用导入映射
            for old_import, new_import in self.import_mappings.items():
                if old_import in content and new_import not in content:
                    content = content.replace(old_import, new_import)
                    _ = fixes_made.append(f"映射替换: {old_import} -> {new_import}")

            # 应用相对导入修复
            for pattern, replacement in self.relative_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    for match in matches:
                        _ = fixes_made.append(f"相对导入修复: {match} -> {replacement}")

            # 如果内容有变化，写入文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    _ = f.write(content)

                details = {
                    "file": str(file_path),
                    "fixes_count": len(fixes_made),
                    "fixes_made": fixes_made
                }

                return True, f"修复了 {len(fixes_made)} 处导入", details
            else:
                return True, "无需修复", {"file": str(file_path), "fixes_count": 0}

        except Exception as e:
            error_details = {
                "file": str(file_path),
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            return False, f"修复文件时出错: {str(e)}", error_details

    def fix(self, target: str = None, **kwargs) -> Tuple[bool, str, Dict]:
        """执行导入修复"""
        _ = print("开始执行导入修复...")

        python_files = self.find_python_files(target)

        if not python_files:
            return True, "未找到需要修复的Python文件", {"files_processed": 0}

    _ = print(f"发现 {len(python_files)} 个Python文件")

    files_fixed = 0
    total_fixes = 0
    errors = []

        for file_path in python_files:
            try:
                fixed, message, details = self.fix_imports_in_file(file_path)

                if fixed:
                    if details.get("fixes_count", 0) > 0:
                        files_fixed += 1
                        total_fixes += details["fixes_count"]
                        _ = print(f"✓ 修复了文件: {file_path} ({details['fixes_count']} 处)")
                    else:
                        _ = print(f"- 跳过文件: {file_path} (无需修复)")
                else:
                    errors.append({
                        "file": str(file_path),
                        "error": message,
                        "details": details
                    })
                    _ = print(f"✗ 修复文件失败: {file_path} - {message}")

            except Exception as e:
                error_msg = f"处理文件时发生异常: {str(e)}"
                errors.append({
                    "file": str(file_path),
                    "error": error_msg,
                    "traceback": traceback.format_exc()
                })
                _ = print(f"✗ 处理文件异常: {file_path} - {error_msg}")

        # 生成结果摘要
        result_details = {
            "files_processed": len(python_files),
            "files_fixed": files_fixed,
            "total_fixes": total_fixes,
            "errors": errors
        }

        if files_fixed > 0:
            message = f"导入修复完成: 修复了 {files_fixed} 个文件中的 {total_fixes} 处导入"
            if errors:
                message += f", {len(errors)} 个错误"
            return True, message, result_details
        else:
            if errors:
                return False, f"导入修复失败: {len(errors)} 个错误", result_details
            else:
                return True, "导入修复完成: 所有文件都正常", result_details

def main() -> None:
    """测试函数"""
    from pathlib import Path

    project_root: str = Path(__file__).parent.parent.parent
    fixer = ImportFixer(project_root)

    success, message, details = fixer.fix()
    _ = print(f"结果: {success}")
    _ = print(f"消息: {message}")
    _ = print(f"详情: {details}")

if __name__ == "__main__":
    _ = main()