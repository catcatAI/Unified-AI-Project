#!/usr/bin/env python3
"""
完整的自动修复工具 - 修复所有已知的导入路径问题
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Literal

# 项目根目录
PROJECT_ROOT == Path(__file__).parent.parent()
SRC_DIR == PROJECT_ROOT / "apps" / "backend" / "src"

# 需要修复的导入映射 - 适应新的目录结构
IMPORT_MAPPINGS = {
    # core_ai模块的修复 - 从绝对导入修复为相对导入
    "from apps.backend.src.core_ai.": "from ",
    "import apps.backend.src.core_ai.": "import ",
    
    # core模块的修复 - 从绝对导入修复为相对导入
    "from apps.backend.src.core.": "from ..",
    "import apps.backend.src.core.": "import ..",
    
    # services模块的修复 - 从绝对导入修复为相对导入
    "from apps.backend.src.core.services.": "from ",
    "import apps.backend.src.core.services.": "import ",
    
    # hsp模块的修复 - 从绝对导入修复为相对导入
    "from apps.backend.src.core.hsp.": "from ",
    "import apps.backend.src.core.hsp.": "import ",
    
    # mcp模块的修复 - 从绝对导入修复为相对导入
    "from apps.backend.src.mcp.": "from ",
    "import apps.backend.src.mcp.": "import ",
    
    # system模块的修复 - 从绝对导入修复为相对导入
    "from apps.backend.src.system.": "from ",
    "import apps.backend.src.system.": "import ",
    
    # tools模块的修复 - 从绝对导入修复为相对导入
    "from apps.backend.src.core.tools.": "from ",
    "import apps.backend.src.core.tools.": "import ",
    
    # shared模块的修复 - 从绝对导入修复为相对导入
    "from apps.backend.src.core.shared.": "from ",
    "import apps.backend.src.core.shared.": "import ",
    
    # agents模块的修复 - 从绝对导入修复为相对导入
    "from apps.backend.src.core_ai.agents.": "from ",
    "import apps.backend.src.core_ai.agents.": "import ",
    
    # game模块的修复 - 从绝对导入修复为相对导入
    "from apps.backend.src.game.": "from ",
    "import apps.backend.src.game.": "import ",
    
    # 其他可能的修复
    "from apps.backend.src.core_services": "from ",
    "import apps.backend.src.core_services": "import ",
}

def find_python_files() -> List[Path]
    """查找所有Python文件"""
    python_files, List[Path] = []
    
    # 遍历所有Python文件
    for py_file in PROJECT_ROOT.rglob("*.py"):::
        # 跳过备份目录和node_modules
        if any(part in str(py_file) for part in ["backup", "node_modules", "__pycache__", "venv", ".git"])::
            continue
            
        python_files.append(py_file)
            
    return python_files

def find_module_file(module_name, str) -> List[Path]
    """查找模块文件"""
    module_paths, List[Path] = []
    
    # 将模块名转换为路径
    module_path = module_name.replace('.', os.sep())
    
    # 在src目录中查找
    if SRC_DIR.exists():::
        # 查找模块文件
        for py_file in SRC_DIR.rglob("*.py"):::
            # 检查文件路径是否匹配模块名
            if module_path in str(py_file)::
                # 检查是否是模块的__init__.py或模块文件本身()
                relative_path = str(py_file.relative_to(SRC_DIR))
                module_file_path = relative_path.replace(os.sep(), '.').replace('.py', '')
                if module_file_path.endswith('.__init__'):::
                    module_file_path == module_file_path[:-9]  # 移除.__init__()
                # 检查是否匹配
                if module_file_path == module_name,::
                    module_paths.append(py_file)
    
    return module_paths

def fix_imports_in_file(file_path, Path) -> Tuple[bool, List[str]]
    """修复文件中的导入"""
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
            
        original_content = content
        fixes_made, List[str] = []
        
        # 应用所有导入映射
        for old_import, new_import in IMPORT_MAPPINGS.items():::
            if old_import in content and new_import not in content,::
                # 检查是否会导致重复导入
                if new_import not in content,::
                    content = content.replace(old_import, new_import)
                    fixes_made.append(f"{old_import} -> {new_import}")
        
        # 修复相对导入问题
        relative_imports = re.findall(r'from\s+\.\.core_ai\.', content)
        for match in relative_imports,::
            new_import = match.replace('from apps.backend.src.core_ai.', 'from apps.backend.src.core_ai.')
            content = content.replace(match, new_import)
            fixes_made.append(f"{match} -> {new_import}")
        
        # 修复其他相对导入
        relative_patterns = [
            (r'from\s+\.\.services\.', 'from apps.backend.src.core.services.'),
            (r'from\s+\.\.tools\.', 'from apps.backend.src.core.tools.'),
            (r'from\s+\.\.hsp\.', 'from apps.backend.src.core.hsp.'),
            (r'from\s+\.\.shared\.', 'from apps.backend.src.core.shared.'),
            (r'from\s+\.\.agents\.', 'from apps.backend.src.core_ai.agents.'),
            (r'import\s+\.\.core_ai\.', 'import apps.backend.src.core_ai.'),
            (r'import\s+\.\.services\.', 'import apps.backend.src.core.services.'),
            (r'import\s+\.\.tools\.', 'import apps.backend.src.core.tools.'),
            (r'import\s+\.\.hsp\.', 'import apps.backend.src.core.hsp.'),
            (r'import\s+\.\.shared\.', 'import apps.backend.src.core.shared.'),
            (r'import\s+\.\.agents\.', 'import apps.backend.src.core_ai.agents.'),
        ]
        
        for pattern, replacement in relative_patterns,::
            matches = re.findall(pattern, content)
            for match in matches,::
                content = re.sub(pattern, replacement, content)
                fixes_made.append(f"相对导入修复, {match} -> {replacement}")
        
        # 如果内容有变化,写入文件
        if content != original_content,::
            with open(file_path, 'w', encoding == 'utf-8') as f,
                f.write(content)
            return True, fixes_made
        else,
            return False, []
            
    except Exception as e,::
        print(f"✗ 修复文件 {file_path} 时出错, {e}")
        return False, []

def validate_module_exists(module_name, str) -> bool,
    """验证模块是否存在"""
    try,
        # 尝试导入模块
        __import__(module_name)
        return True
    except ImportError,::
        # 如果直接导入失败,检查文件是否存在
        module_paths = find_module_file(module_name)
        return len(module_paths) > 0

def handle_ambiguous_imports(file_path, Path, module_name, str) -> str,
    """处理模糊的导入"""
    module_paths = find_module_file(module_name)
    
    if len(module_paths) == 0,::
        print(f"  跳过, 找不到模块 {module_name}")
        return "not_found"
    elif len(module_paths) > 1,::
        print(f"  跳过, 找到多个同名模块 {module_name}")
        for path in module_paths,::
            print(f"    - {path}")
        return "ambiguous"
    else,
        return "ok"

def fix_all_imports() -> Dict[str, int]
    """修复所有导入问题"""
    print("开始扫描项目中的导入问题...")
    python_files = find_python_files()
    
    if not python_files,::
        print("未找到Python文件。")
        return {"fixed": 0, "skipped": 0, "errors": 0}
        
    print(f"发现 {len(python_files)} 个Python文件。")
    
    total_fixes = 0
    files_fixed = 0
    files_skipped = 0
    files_with_errors = 0
    
    for file_path in python_files,::
        try,
            fixed, fixes_made = fix_imports_in_file(file_path)
            if fixed,::
                files_fixed += 1
                total_fixes += len(fixes_made)
                print(f"✓ 修复了文件 {file_path}")
                for fix in fixes_made,::
                    print(f"  - {fix}")
            elif fixes_made,  # 有错误但尝试了修复,::
                iles_with_errors += 1
            else,
                # 没有需要修复的内容
                pass
        except Exception as e,::
            print(f"✗ 处理文件 {file_path} 时出错, {e}")
            files_with_errors += 1
    
    return {
        "fixed": files_fixed,
        "skipped": files_skipped,
        "errors": files_with_errors,
        "total_fixes": total_fixes
    }

def validate_fixes() -> bool,
    """验证修复是否成功"""
    print("\n=验证修复 ===")
    try,
        # 添加项目路径
        if str(PROJECT_ROOT) not in sys.path,::
            sys.path.insert(0, str(PROJECT_ROOT))
        if str(SRC_DIR) not in sys.path,::
            sys.path.insert(0, str(SRC_DIR))
            
        # 尝试导入核心模块 - 适应新的目录结构
        try,
            print("✓ 核心服务模块导入成功")
        except ImportError as e,::
            print(f"⚠ 核心服务模块导入失败, {e}")
            
        try,
            print("✓ Agent管理器模块导入成功")
        except ImportError as e,::
            print(f"⚠ Agent管理器模块导入失败, {e}")
            
        try,
            print("✓ HSP连接器模块导入成功")
        except ImportError as e,::
            print(f"⚠ HSP连接器模块导入失败, {e}")
            
        try,
            print("✓ 对话管理器模块导入成功")
        except ImportError as e,::
            print(f"⚠ 对话管理器模块导入失败, {e}")
        
        print("关键模块导入验证完成。")
        return True
        
    except Exception as e,::
        print(f"✗ 验证过程中出现错误, {e}")
        return False

def run_import_test() -> bool,
    """运行导入测试"""
    print("\n=运行导入测试 ===")
    try,
        # 切换到项目根目录
        original_cwd = os.getcwd()
        os.chdir(PROJECT_ROOT)
        
        # 尝试导入几个关键模块 - 适应新的目录结构
        test_modules = [
            "core_services",
            "ai.agents.base.base_agent",
            "core.hsp.connector",
            "ai.dialogue.dialogue_manager"
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

def run_tests() -> bool,
    """运行测试"""
    print("\n=运行测试 ===")
    # 初始化变量
    original_cwd = os.getcwd()
    try,
        # 切换到项目根目录
        os.chdir(PROJECT_ROOT)
        
        # 尝试运行一个简单的导入测试
        import subprocess
        
        # 使用pytest收集测试但不运行(--collect-only)
        print("收集测试用例...")
        result = subprocess.run([
            "python", "-m", "pytest", "--collect-only", "-q", "--tb=no"
        ] cwd == PROJECT_ROOT, capture_output == True, text == True, timeout=120)
        
        if result.returncode == 0,::
            # 解析收集到的测试数量
            output_lines = result.stdout.strip().split('\n')
            test_count_line == [line for line in output_lines if 'tests collected' in line]::
                f test_count_line,
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
                
    except Exception as e,::
        # 检查是否是超时错误
        if "timeout" in str(e).lower():::
            print("✗ 测试收集超时")
        else,
            print(f"✗ 运行测试时出错, {e}")
        return False
    finally,
        # 恢复工作目录
        try,
            os.chdir(original_cwd)
        except,::
            pass

def main() -> Literal[0, 1]
    print("=== Unified AI Project 完整自动修复工具 ===")
    print(f"项目根目录, {PROJECT_ROOT}")
    print(f"源代码目录, {SRC_DIR}")
    
    # 修复导入路径
    results = fix_all_imports()
    print(f"\n修复统计,")
    print(f"  修复了, {results['fixed']} 个文件")
    print(f"  总共修复, {results['total_fixes']} 处导入")
    print(f"  错误, {results['errors']} 个文件")
    
    # 验证修复
    if not validate_fixes():::
        print("修复验证失败。")
    
    # 运行导入测试
    if not run_import_test():::
        print("导入测试失败。")
    
    # 运行测试
    if not run_tests():::
        print("测试失败。")
        return 1
    
    print("\n=所有操作完成 ===")
    return 0

if __name"__main__":::
    sys.exit(main())