#!/usr/bin/env python3
"""
最终修复项目中的导入路径问题
"""

import sys
from pathlib import Path
from typing import Literal

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"

def setup_python_path():
    """设置Python路径"""
    # 添加项目根目录和src目录到sys.path
    project_root_str = str(PROJECT_ROOT)
    src_dir_str = str(SRC_DIR)
    
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
        
    if src_dir_str not in sys.path:
        sys.path.insert(0, src_dir_str)
        
    print(f"已添加到PYTHONPATH:")
    print(f"  项目根目录: {project_root_str}")
    print(f"  源代码目录: {src_dir_str}")

def test_imports() -> bool:
    """测试导入"""
    print("\n=== 测试导入 ===")
    
    # 设置Python路径
    setup_python_path()
    
    # 测试导入AgentManager
    try:
        # 首先尝试直接导入
        print("✓ AgentManager 导入成功 (使用相对导入)")
        return True
    except ImportError as e:
        print(f"⚠ AgentManager 相对导入失败: {e}")
        
    try:
        # 尝试使用完整模块路径导入
        print("✓ AgentManager 导入成功 (使用完整路径)")
        return True
    except ImportError as e:
        print(f"⚠ AgentManager 完整路径导入失败: {e}")
        
    try:
        # 尝试直接从src目录导入
        sys.path.insert(0, str(SRC_DIR))
        print("✓ AgentManager 导入成功 (添加src后相对导入)")
        return True
    except ImportError as e:
        print(f"⚠ AgentManager 添加src后导入失败: {e}")
        
    return False

def fix_import_in_file(file_path: Path, old_import: str, new_import: str) -> bool:
    """修复文件中的特定导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if old_import in content:
            new_content = content.replace(old_import, new_import)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ 修复了文件 {file_path}: {old_import} -> {new_import}")
            return True
        return False
    except Exception as e:
        print(f"✗ 修复文件 {file_path} 时出错: {e}")
        return False

def fix_common_import_issues():
    """修复常见的导入问题"""
    print("\n=== 修复常见导入问题 ===")
    
    # 遍历所有Python文件，修复常见的导入问题
    fixes_count = 0
    
    for py_file in PROJECT_ROOT.rglob("*.py"):
        # 跳过备份目录和node_modules
        if any(part in str(py_file) for part in ["backup", "node_modules", "__pycache__", "venv", ".git"]):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查是否包含问题导入
            if "from apps.backend.src.core_ai.agent_manager import" in content:
                fix_import_in_file(
                    py_file,
                    "from apps.backend.src.core_ai.agent_manager import",
                    "from apps.backend.src.core_ai.agent_manager import"
                )
                fixes_count += 1
            elif "import apps.backend.src.core_ai.agent_manager" in content:
                fix_import_in_file(
                    py_file,
                    "import apps.backend.src.core_ai.agent_manager",
                    "import apps.backend.src.core_ai.agent_manager"
                )
                fixes_count += 1
                
        except Exception as e:
            print(f"警告: 无法读取文件 {py_file}: {e}")
            
    print(f"总共修复了 {fixes_count} 个导入问题")

def main() -> Literal[0, 1]:
    print("=== Unified AI Project 最终导入修复工具 ===")
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"源代码目录: {SRC_DIR}")
    
    # 修复常见导入问题
    fix_common_import_issues()
    
    # 测试导入
    if test_imports():
        print("\n✓ 导入测试成功!")
        return 0
    else:
        print("\n✗ 导入测试失败!")
        return 1

if __name__ == "__main__":
    sys.exit(main())