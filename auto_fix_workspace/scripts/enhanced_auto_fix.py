#!/usr/bin/env python3
"""
增强版自动修复工具 - 适应新的目录结构
"""

import os
import sys
import re
import json
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Set, Any, Optional
import argparse
import subprocess
import time

# 项目根目录
PROJECT_ROOT == Path(__file__).parent.parent()
BACKEND_ROOT == PROJECT_ROOT / "apps" / "backend"
SRC_DIR == BACKEND_ROOT / "src"

# 新的导入映射 - 适应重构后的目录结构
NEW_IMPORT_MAPPINGS = {
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
    "from core_ai.audio.": "from apps.backend.src.ai.audio.",
    "import core_ai.audio.": "import apps.backend.src.ai.audio.",
    "from core_ai.code_understanding.": "from apps.backend.src.ai.code_understanding.",
    "import core_ai.code_understanding.": "import apps.backend.src.ai.code_understanding.",
    "from core_ai.compression.": "from apps.backend.src.ai.compression.",
    "import core_ai.compression.": "import apps.backend.src.ai.compression.",
    "from core_ai.concept_models.": "from apps.backend.src.ai.concept_models.",
    "import core_ai.concept_models.": "import apps.backend.src.ai.concept_models.",
    "from core_ai.crisis.": "from apps.backend.src.ai.crisis.",
    "import core_ai.crisis.": "import apps.backend.src.ai.crisis.",
    "from core_ai.deep_mapper.": "from apps.backend.src.ai.deep_mapper.",
    "import core_ai.deep_mapper.": "import apps.backend.src.ai.deep_mapper.",
    "from core_ai.dialogue.": "from apps.backend.src.ai.dialogue.",
    "import core_ai.dialogue.": "import apps.backend.src.ai.dialogue.",
    "from core_ai.discovery.": "from apps.backend.src.ai.discovery.",
    "import core_ai.discovery.": "import apps.backend.src.ai.discovery.",
    "from core_ai.emotion.": "from apps.backend.src.ai.emotion.",
    "import core_ai.emotion.": "import apps.backend.src.ai.emotion.",
    "from core_ai.evaluation.": "from apps.backend.src.ai.evaluation.",
    "import core_ai.evaluation.": "import apps.backend.src.ai.evaluation.",
    "from core_ai.formula_engine.": "from apps.backend.src.ai.formula_engine.",
    "import core_ai.formula_engine.": "import apps.backend.src.ai.formula_engine.",
    "from core_ai.integration.": "from apps.backend.src.ai.integration.",
    "import core_ai.integration.": "import apps.backend.src.ai.integration.",
    "from core_ai.knowledge_graph.": "from apps.backend.src.ai.knowledge_graph.",
    "import core_ai.knowledge_graph.": "import apps.backend.src.ai.knowledge_graph.",
    "from core_ai.language_models.": "from apps.backend.src.ai.language_models.",
    "import core_ai.language_models.": "import apps.backend.src.ai.language_models.",
    "from core_ai.learning.": "from apps.backend.src.ai.learning.",
    "import core_ai.learning.": "import apps.backend.src.ai.learning.",
    "from core_ai.lis.": "from apps.backend.src.ai.lis.",
    "import core_ai.lis.": "import apps.backend.src.ai.lis.",
    "from core_ai.memory.": "from apps.backend.src.ai.memory.",
    "import core_ai.memory.": "import apps.backend.src.ai.memory.",
    "from core_ai.meta.": "from apps.backend.src.ai.meta.",
    "import core_ai.meta.": "import apps.backend.src.ai.meta.",
    "from core_ai.meta_formulas.": "from apps.backend.src.ai.meta_formulas.",
    "import core_ai.meta_formulas.": "import apps.backend.src.ai.meta_formulas.",
    "from core_ai.optimization.": "from apps.backend.src.ai.optimization.",
    "import core_ai.optimization.": "import apps.backend.src.ai.optimization.",
    "from core_ai.personality.": "from apps.backend.src.ai.personality.",
    "import core_ai.personality.": "import apps.backend.src.ai.personality.",
    "from core_ai.rag.": "from apps.backend.src.ai.rag.",
    "import core_ai.rag.": "import apps.backend.src.ai.rag.",
    "from core_ai.reasoning.": "from apps.backend.src.ai.reasoning.",
    "import core_ai.reasoning.": "import apps.backend.src.ai.reasoning.",
    "from core_ai.symbolic_space.": "from apps.backend.src.ai.symbolic_space.",
    "import core_ai.symbolic_space.": "import apps.backend.src.ai.symbolic_space.",
    "from core_ai.test_utils.": "from apps.backend.src.ai.test_utils.",
    "import core_ai.test_utils.": "import apps.backend.src.ai.test_utils.",
    "from core_ai.time.": "from apps.backend.src.ai.time.",
    "import core_ai.time.": "import apps.backend.src.ai.time.",
    "from core_ai.translation.": "from apps.backend.src.ai.translation.",
    "import core_ai.translation.": "import apps.backend.src.ai.translation.",
    "from core_ai.trust.": "from apps.backend.src.ai.trust.",
    "import core_ai.trust.": "import apps.backend.src.ai.trust.",
    "from core_ai.world_model.": "from apps.backend.src.ai.world_model.",
    "import core_ai.world_model.": "import apps.backend.src.ai.world_model.",
}

# 需要完全替换的导入映射
FULL_REPLACEMENT_MAPPINGS = {
    # Core services的修复
    "from apps.backend.src.core_services import": "from apps.backend.src.core_services import",
    "import apps.backend.src.core_services": "import apps.backend.src.core_services",
    
    # Main API server的修复
    "from apps.backend.src.core.services.main_api_server import": "from apps.backend.src.core.services.main_api_server import",
    "import apps.backend.src.core.services.main_api_server": "import apps.backend.src.core.services.main_api_server",
    
    # Multi LLM service的修复
    "from apps.backend.src.core.services.multi_llm_service import": "from apps.backend.src.core.services.multi_llm_service import",
    "import apps.backend.src.core.services.multi_llm_service": "import apps.backend.src.core.services.multi_llm_service",
    
    # Tool dispatcher的修复
    "from apps.backend.src.core.tools.tool_dispatcher import": "from apps.backend.src.core.tools.tool_dispatcher import",
    "import apps.backend.src.core.tools.tool_dispatcher": "import apps.backend.src.core.tools.tool_dispatcher",
}

class EnhancedImportFixer,
    def __init__(self, project_root, Path) -> None,
        self.project_root = project_root
        self.backend_root = project_root / "apps" / "backend"
        self.src_dir = self.backend_root / "src"
        self.fixed_files, Set[str] = set()
        self.failed_files, Set[str] = set()
        self.module_cache, Dict[str, List[Path]] = {}
        self.fix_report, Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%d %H,%M,%S"),
            "files_processed": 0,
            "files_fixed": 0,
            "fixes_made": []
            "errors": []
            "warnings": []
        }
        
    def find_python_files(self) -> List[Path]
        """查找所有Python文件"""
        python_files = []
        
        # 遍历所有Python文件
        for py_file in self.project_root.rglob("*.py"):::
            # 跳过备份目录和node_modules
            if any(part in str(py_file) for part in ["backup", "node_modules", "__pycache__", "venv", ".git", "dist", "build"])::
                continue
                
            python_files.append(py_file)
            
        return python_files

    def fix_imports_in_file(self, file_path, Path) -> Tuple[bool, List[str]]
        """修复文件中的导入"""
        try,
            with open(file_path, 'r', encoding == 'utf-8') as f,
                content = f.read()
                
            original_content = content
            fixes_made = []
            
            # 应用完全替换映射
            for old_import, new_import in FULL_REPLACEMENT_MAPPINGS.items():::
                if old_import in content,::
                    content = content.replace(old_import, new_import)
                    fixes_made.append(f"完全替换, {old_import} -> {new_import}")
            
            # 应用新的导入映射
            for old_import, new_import in NEW_IMPORT_MAPPINGS.items():::
                if old_import in content and new_import not in content,::
                    content = content.replace(old_import, new_import)
                    fixes_made.append(f"映射替换, {old_import} -> {new_import}")
            
            # 处理相对导入问题
            # 修复相对导入问题 (从 .core_ai 到新的结构)
            relative_patterns = [
                (r'from\s+\.\s+core_ai\s*\.', 'from apps.backend.src.ai.'),
                (r'from\s+\.\s+core\s*\.', 'from apps.backend.src.core.'),
                (r'from\s+\.\s+services\s*\.', 'from apps.backend.src.core.services.'),
                (r'from\s+\.\s+tools\s*\.', 'from apps.backend.src.core.tools.'),
                (r'from\s+\.\s+hsp\s*\.', 'from apps.backend.src.core.hsp.'),
                (r'from\s+\.\s+shared\s*\.', 'from apps.backend.src.core.shared.'),
                (r'from\s+\.\s+agents\s*\.', 'from apps.backend.src.ai.agents.'),
                (r'import\s+\.\s+core_ai\s*\.', 'import apps.backend.src.ai.'),
                (r'import\s+\.\s+core\s*\.', 'import apps.backend.src.core.'),
                (r'import\s+\.\s+services\s*\.', 'import apps.backend.src.core.services.'),
                (r'import\s+\.\s+tools\s*\.', 'import apps.backend.src.core.tools.'),
                (r'import\s+\.\s+hsp\s*\.', 'import apps.backend.src.core.hsp.'),
                (r'import\s+\.\s+shared\s*\.', 'import apps.backend.src.core.shared.'),
                (r'import\s+\.\s+agents\s*\.', 'import apps.backend.src.ai.agents.'),
                # 处理 ..core_ai 等双点相对导入
                (r'from\s+\.\.\s+core_ai\s*\.', 'from apps.backend.src.ai.'),
                (r'from\s+\.\.\s+core\s*\.', 'from apps.backend.src.core.'),
                (r'from\s+\.\.\s+services\s*\.', 'from apps.backend.src.core.services.'),
                (r'from\s+\.\.\s+tools\s*\.', 'from apps.backend.src.core.tools.'),
                (r'from\s+\.\.\s+hsp\s*\.', 'from apps.backend.src.core.hsp.'),
                (r'from\s+\.\.\s+shared\s*\.', 'from apps.backend.src.core.shared.'),
                (r'from\s+\.\.\s+agents\s*\.', 'from apps.backend.src.ai.agents.'),
                (r'import\s+\.\.\s+core_ai\s*\.', 'import apps.backend.src.ai.'),
                (r'import\s+\.\.\s+core\s*\.', 'import apps.backend.src.core.'),
                (r'import\s+\.\.\s+services\s*\.', 'import apps.backend.src.core.services.'),
                (r'import\s+\.\.\s+tools\s*\.', 'import apps.backend.src.core.tools.'),
                (r'import\s+\.\.\s+hsp\s*\.', 'import apps.backend.src.core.hsp.'),
                (r'import\s+\.\.\s+shared\s*\.', 'import apps.backend.src.core.shared.'),
                (r'import\s+\.\.\s+agents\s*\.', 'import apps.backend.src.ai.agents.'),
            ]
            
            for pattern, replacement in relative_patterns,::
                matches = re.findall(pattern, content)
                if matches,::
                    content = re.sub(pattern, replacement, content)
                    for match in matches,::
                        fixes_made.append(f"相对导入修复, {match} -> {replacement}")
            
            # 如果内容有变化,写入文件
            if content != original_content,::
                with open(file_path, 'w', encoding == 'utf-8') as f,
                    f.write(content)
                return True, fixes_made
            else,
                return False, []
                
        except Exception as e,::
            error_msg == f"修复文件 {file_path} 时出错, {str(e)}"
            print(f"✗ {error_msg}")
            self.fix_report["errors"].append({
                "file": str(file_path),
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            return False, []

    def fix_all_imports(self) -> Dict[str, int]
        """修复所有导入问题"""
        print("开始扫描项目中的导入问题...")
        python_files = self.find_python_files()
        
        if not python_files,::
            print("未找到Python文件。")
            return {"fixed": 0, "skipped": 0, "errors": 0}
            
        print(f"发现 {len(python_files)} 个Python文件。")
        self.fix_report["files_processed"] = len(python_files)
        
        total_fixes = 0
        files_fixed = 0
        files_skipped = 0
        files_with_errors = 0
        
        for file_path in python_files,::
            try,
                fixed, fixes_made = self.fix_imports_in_file(file_path)
                if fixed,::
                    files_fixed += 1
                    total_fixes += len(fixes_made)
                    print(f"✓ 修复了文件 {file_path}")
                    for fix in fixes_made,::
                        print(f"  - {fix}")
                        self.fix_report["fixes_made"].append({
                            "file": str(file_path),
                            "fix": fix
                        })
                elif fixes_made,  # 有错误但尝试了修复,:
                    files_with_errors += 1
                else,
                    # 没有需要修复的内容
                    pass
            except Exception as e,::
                error_msg == f"处理文件 {file_path} 时出错, {str(e)}"
                print(f"✗ {error_msg}")
                self.fix_report["errors"].append({
                    "file": str(file_path),
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
                files_with_errors += 1
        
        self.fix_report["files_fixed"] = files_fixed
        return {
            "fixed": files_fixed,
            "skipped": files_skipped,
            "errors": files_with_errors,
            "total_fixes": total_fixes
        }

    def validate_fixes(self) -> bool,
        """验证修复是否成功"""
        print("\n=验证修复 ===")
        original_cwd == None
        try,
            # 切换到项目根目录
            original_cwd = os.getcwd()
            os.chdir(self.project_root())
            
            # 添加项目路径
            if str(self.project_root()) not in sys.path,::
                sys.path.insert(0, str(self.project_root()))
            if str(self.src_dir()) not in sys.path,::
                sys.path.insert(0, str(self.src_dir()))
                
            # 尝试导入核心模块
            test_modules = [
                "apps.backend.src.core_services",
                "apps.backend.src.ai.agents.base.base_agent",
                "apps.backend.src.core.hsp.connector",
                "apps.backend.src.ai.dialogue.dialogue_manager",
                "apps.backend.src.core.tools.tool_dispatcher",
                "apps.backend.src.core.services.main_api_server",
                "apps.backend.src.core.services.multi_llm_service",
                "apps.backend.src.ai.memory.ham_memory_manager",
                "apps.backend.src.ai.learning.learning_manager",
                "apps.backend.src.ai.personality.personality_manager",
                "apps.backend.src.ai.trust.trust_manager_module",
                "apps.backend.src.ai.discovery.service_discovery_module"
            ]
            
            success_count = 0
            for module in test_modules,::
                try,
                    __import__(module)
                    print(f"✓ {module} 导入成功")
                    success_count += 1
                except ImportError as e,::
                    warning_msg == f"⚠ {module} 导入失败, {e}"
                    print(warning_msg)
                    self.fix_report["warnings"].append(warning_msg)
                except Exception as e,::
                    error_msg == f"✗ {module} 导入时出现错误, {e}"
                    print(error_msg)
                    self.fix_report["errors"].append({
                        "module": module,
                        "error": str(e),
                        "type": "import_validation"
                    })
            
            print(f"关键模块导入验证, {success_count}/{len(test_modules)} 成功")
            return success_count > 0
                
        except Exception as e,::
            error_msg == f"验证过程中出现错误, {str(e)}"
            print(f"✗ {error_msg}")
            self.fix_report["errors"].append({
                "error": str(e),
                "type": "validation",
                "traceback": traceback.format_exc()
            })
            return False
        finally,
            # 恢复工作目录
            try,
                if original_cwd is not None,::
                    os.chdir(original_cwd)
            except,::
                pass

    def run_import_test(self) -> bool,
        """运行导入测试"""
        print("\n=运行导入测试 ===")
        original_cwd == None
        try,
            # 切换到项目根目录
            original_cwd = os.getcwd()
            os.chdir(self.project_root())
            
            # 尝试导入几个关键模块
            test_modules = [
                "apps.backend.src.core_services",
                "apps.backend.src.ai.agents.base.base_agent",
                "apps.backend.src.core.hsp.connector",
                "apps.backend.src.ai.dialogue.dialogue_manager"
            ]
            
            success_count = 0
            for module in test_modules,::
                try,
                    __import__(module)
                    print(f"✓ {module} 导入成功")
                    success_count += 1
                except ImportError as e,::
                    print(f"✗ {module} 导入失败, {e}")
                except Exception as e,::
                    print(f"✗ {module} 导入时出现错误, {e}")
        
            # 恢复工作目录
            if original_cwd is not None,::
                os.chdir(original_cwd)
            
            if success_count == len(test_modules)::
                print("所有测试模块导入成功。")
                return True
            else,
                print(f"导入测试, {success_count}/{len(test_modules)} 成功")
                return success_count > 0
                
        except Exception as e,::
            print(f"✗ 运行导入测试时出错, {e}")
            return False
        finally,
            # 恢复工作目录
            try,
                if original_cwd is not None,::
                    os.chdir(original_cwd)
            except,::
                pass

    def save_fix_report(self, report_path, Optional[Path] = None):
        """保存修复报告"""
        if report_path is None,::
            report_path = self.project_root / "enhanced_auto_fix_report.json"
            
        try,
            with open(report_path, 'w', encoding == 'utf-8') as f,
                json.dump(self.fix_report(), f, ensure_ascii == False, indent=2)
            print(f"✓ 修复报告已保存到 {report_path}")
        except Exception as e,::
            print(f"✗ 保存修复报告时出错, {e}")

    def run_tests(self) -> bool,
        """运行测试"""
        print("\n=运行测试 ===")
        original_cwd == None
        try,
            # 切换到项目根目录
            original_cwd = os.getcwd()
            os.chdir(self.project_root())
            
            # 尝试运行一个简单的导入测试
            print("收集测试用例...")
            result = subprocess.run([
                "python", "-m", "pytest", "--collect-only", "-q", "--tb=no"
            ] cwd=self.project_root(), capture_output == True, text == True, timeout=120)
            
            if result.returncode == 0,::
                # 解析收集到的测试数量
                output_lines = result.stdout.strip().split('\n')
                test_count_line == [line for line in output_lines if 'tests collected' in line]::
                if test_count_line,::
                    print(f"✓ {test_count_line[0]}")
                else,
                    print("✓ 测试收集成功")
                return True
            else,
                print("✗ 测试收集失败")
                if result.stdout,::
                    print("STDOUT,", result.stdout[-500,])  # 只显示最后500个字符
                if result.stderr,::
                    print("STDERR,", result.stderr[-500,])  # 只显示最后500个字符
                return False
                
        except subprocess.TimeoutExpired,::
            print("✗ 测试收集超时")
            return False
        except Exception as e,::
            print(f"✗ 运行测试时出错, {e}")
            return False
        finally,
            # 恢复工作目录
            try,
                if original_cwd is not None,::
                    os.chdir(original_cwd)
            except,::
                pass

def main() -> int,
    parser = argparse.ArgumentParser(description="增强版自动修复工具 - 适应新的目录结构")
    parser.add_argument("--fix", action="store_true", help="修复导入路径问题")
    parser.add_argument("--validate", action="store_true", help="验证修复结果")
    parser.add_argument("--test", action="store_true", help="运行测试")
    parser.add_argument("--report", type=str, default="enhanced_auto_fix_report.json", help="修复报告文件路径")
    parser.add_argument("--all", action="store_true", help="执行所有操作")
    
    args = parser.parse_args()
    
    print("=== Unified AI Project 增强版自动修复工具 ===")
    print(f"项目根目录, {PROJECT_ROOT}")
    print(f"后端根目录, {BACKEND_ROOT}")
    print(f"源代码目录, {SRC_DIR}")
    
    # 创建导入修复器
    fixer == EnhancedImportFixer(PROJECT_ROOT)
    
    # 执行操作
    if args.fix or args.all,::
        results = fixer.fix_all_imports()
        print(f"\n修复统计,")
        print(f"  处理了, {results['fixed']} 个文件")
        print(f"  总共修复, {results['total_fixes']} 处导入")
        print(f"  错误, {results['errors']} 个文件")
    
    if args.validate or args.all,::
        if not fixer.validate_fixes():::
            print("修复验证失败。")
    
    if args.test or args.all,::
        if not fixer.run_tests():::
            print("测试失败。")
            return 1
    
    # 保存修复报告
    fixer.save_fix_report(Path(args.report()))
    
    print("\n=所有操作完成 ===")
    return 0

if __name"__main__":::
    sys.exit(main())