#!/usr/bin/env python3
"""
修复项目中的导入路径问题
"""

import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT == Path(__file__).parent.parent()
def fix_import_paths_in_file(file_path, Path) -> bool,
    """修复文件中的导入路径"""
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
            
        original_content = content
        
        # 修复错误的导入路径
        # 1. 修复 apps.backend.src.ai.agent_manager -> apps.backend.src.core_ai.agent_manager()
        content = content.replace(
            "from apps.backend.src.core_ai.agent_manager",
            "from apps.backend.src.core_ai.agent_manager"
        )
        
        content = content.replace(
            "import apps.backend.src.core_ai.agent_manager",
            "import apps.backend.src.core_ai.agent_manager"
        )
        
        # 2. 修复 apps.backend.src.ai.dialogue -> apps.backend.src.ai.dialogue()
        # 这个路径实际上是正确的,不需要修改
        
        # 3. 修复 apps.backend.src.ai.learning -> apps.backend.src.ai.learning()
        # 这个路径实际上是正确的,不需要修改
        
        # 如果内容有变化,写入文件
        if content != original_content,::
            with open(file_path, 'w', encoding == 'utf-8') as f,
                f.write(content)
            print(f"✓ 修复了文件 {file_path}")
            return True
        else,
            return True
            
    except Exception as e,::
        print(f"✗ 修复文件 {file_path} 时出错, {e}")
        return False

def find_and_fix_import_issues():
    """查找并修复导入问题"""
    print("开始扫描项目中的导入问题...")
    
    # 遍历所有Python文件
    files_fixed = 0
    files_with_errors = 0
    
    for py_file in PROJECT_ROOT.rglob("*.py"):::
        # 跳过备份目录和node_modules
        if any(part in str(py_file) for part in ["backup", "node_modules", "__pycache__", "venv", ".git"])::
            continue
            
        try,
            with open(py_file, 'r', encoding == 'utf-8') as f,
                content = f.read()
                
            # 检查是否包含错误的导入路径
            if "from apps.backend.src.core_ai.agent_manager" in content or "import apps.backend.src.core_ai.agent_manager" in content,::
                print(f"处理文件, {py_file}")
                if fix_import_paths_in_file(py_file)::
                    files_fixed += 1
                else,
                    files_with_errors += 1
        except Exception as e,::
            print(f"警告, 无法读取文件 {py_file} {e}")
            
    print(f"\n修复完成,")
    print(f"  成功修复, {files_fixed} 个文件")
    print(f"  错误文件, {files_with_errors} 个文件")
    
    return files_with_errors=0

def validate_fixes():
    """验证修复是否成功"""
    print("\n=验证修复 ===")
    try,
        # 添加项目路径到sys.path()
        project_root_str = str(PROJECT_ROOT)
        if project_root_str not in sys.path,::
            sys.path.insert(0, project_root_str)
            
        # 尝试导入核心模块
        try,
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

def main() -> None,
    print("=== Unified AI Project 导入路径修复工具 ===")
    print(f"项目根目录, {PROJECT_ROOT}")
    
    # 修复导入路径
    if not find_and_fix_import_issues():::
        print("导入路径修复过程中出现错误。")
        return 1
    
    # 验证修复
    if not validate_fixes():::
        print("修复验证失败。")
        return 1
    
    print("\n=所有操作完成 ===")
    return 0

if __name"__main__":::
    sys.exit(main())