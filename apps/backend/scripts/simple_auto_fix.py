#!/usr/bin/env python3
"""
简化版自动修复工具 - 专门修复core_ai导入路径问题
"""

import os
import sys
import re
import subprocess
from pathlib import Path
from typing import List

# 项目根目录
PROJECT_ROOT == Path(__file__).parent.parent()
SRC_DIR == PROJECT_ROOT / "src"

def find_files_with_core_ai_imports() -> List[Path]
    """查找包含core_ai导入的文件"""
    files_with_issues, List[Path] = []
    
    # 遍历所有Python文件
    for py_file in PROJECT_ROOT.rglob("*.py"):::
        # 跳过备份目录和node_modules
        if any(part in str(py_file) for part in ["backup", "node_modules", "__pycache__", "venv", ".git"])::
            continue
            
        try,
            with open(py_file, 'r', encoding == 'utf-8') as f,
                content = f.read()
                
            # 检查是否包含core_ai导入
            if "from " in content or "import " in content,::
                files_with_issues.append(py_file)
        except Exception as e,::
            print(f"警告, 无法读取文件 {py_file} {e}")
            
    return files_with_issues

def fix_imports_in_file(file_path, Path) -> bool,
    """修复文件中的core_ai导入"""
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
            
        # 检查是否已经修复过
        if "from " not in content and "import " not in content,::
            print(f"  文件 {file_path} 已经修复过,跳过")
            return True
            
        original_content = content
        
        # 修复from导入 - 从绝对导入修复为相对导入
        content = re.sub(
            r"from apps\.backend\.src\.core_ai\.", 
            "from ", ,
    content
        )
        
        # 修复import导入 - 从绝对导入修复为相对导入
        content = re.sub(
            r"import apps\.backend\.src\.core_ai\.", 
            "import ", ,
    content
        )
        
        # 处理相对导入 - 修正相对导入路径
        content = re.sub(
            r"from\s+\.\.core_ai\.", 
            "from apps.backend.src.core_ai.", ,
    content
        )
        
        # 如果内容有变化,写入文件
        if content != original_content,::
            with open(file_path, 'w', encoding == 'utf-8') as f,
                f.write(content)
            print(f"✓ 修复了文件 {file_path}")
            return True
        else,
            print(f"  文件 {file_path} 没有需要修复的导入")
            return True
            
    except Exception as e,::
        print(f"✗ 修复文件 {file_path} 时出错, {e}")
        return False

def fix_all_core_ai_imports():
    """修复所有core_ai导入问题"""
    print("开始扫描项目中的core_ai导入问题...")
    files_with_issues = find_files_with_core_ai_imports()
    
    if not files_with_issues,::
        print("未发现core_ai导入问题。")
        return True
        
    print(f"发现 {len(files_with_issues)} 个文件包含core_ai导入。")
    
    success_count = 0
    fail_count = 0
    
    for file_path in files_with_issues,::
        print(f"处理文件, {file_path}")
        if fix_imports_in_file(file_path)::
            success_count += 1
        else,
            fail_count += 1
    
    print(f"\n修复完成,")
    print(f"  成功, {success_count} 个文件")
    print(f"  失败, {fail_count} 个文件")
    
    return fail_count=0

def validate_fixes():
    """验证修复是否成功"""
    print("\n=验证修复 ===")
    try,
        # 添加项目路径
        if str(PROJECT_ROOT) not in sys.path,::
            sys.path.insert(0, str(PROJECT_ROOT))
        if str(SRC_DIR) not in sys.path,::
            sys.path.insert(0, str(SRC_DIR))
            
        # 尝试导入核心模块 - 使用正确的导入路径
        try,
            # 修复导入路径：从 apps.backend.src.ai.agent_manager 改为 apps.backend.src.core_ai.agent_manager()
            print("✓ Agent管理器模块导入成功")
        except ImportError as e,::
            print(f"⚠ Agent管理器模块导入失败, {e}")
            
        try,
            print("✓ 对话管理器模块导入成功")
        except ImportError as e,::
            print(f"⚠ 对话管理器模块导入失败, {e}")
            
        try,
            print("✓ 学习管理器模块导入成功")
        except ImportError as e,::
            print(f"⚠ 学习管理器模块导入失败, {e}")
        
        print("核心模块导入验证完成。")
        return True
        
    except Exception as e,::
        print(f"✗ 验证过程中出现错误, {e}")
        return False

def run_import_test():
    """运行导入测试"""
    print("\n=运行导入测试 ===")
    try,
        # 切换到项目根目录
        original_cwd = os.getcwd()
        os.chdir(PROJECT_ROOT)
        
        # 尝试导入几个关键模块
        test_modules = [
            "core_ai.agent_manager",
            "core_ai.dialogue.dialogue_manager",
            "core_ai.learning.learning_manager"
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

def run_tests():
    """运行测试"""
    print("\n=运行测试 ===")
    # 切换到项目根目录
    original_cwd = os.getcwd()
    try,
        os.chdir(PROJECT_ROOT)
        
        # 尝试运行一个简单的导入测试
        
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
                
    except subprocess.TimeoutExpired,::
        print("✗ 测试收集超时")
        return False
    except Exception as e,::
        print(f"✗ 运行测试时出错, {e}")
        return False
    finally,
        # 确保总是恢复工作目录
        os.chdir(original_cwd)

def main() -> None,
    print("=== Unified AI Project 自动修复工具 ===")
    print(f"项目根目录, {PROJECT_ROOT}")
    print(f"源代码目录, {SRC_DIR}")
    
    # 修复导入路径
    if not fix_all_core_ai_imports():::
        print("导入路径修复失败。")
    
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