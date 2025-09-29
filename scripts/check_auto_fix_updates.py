#!/usr/bin/env python3
"""
自动修复工具更新检查脚本
在完成其他任务后检查自动修复工具是否需要更新
"""

from pathlib import Path
from typing import Dict, List

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = PROJECT_ROOT / "apps" / "backend"
SRC_DIR = BACKEND_ROOT / "src"

def check_directory_structure() -> Dict[str, List[str]]:
    """检查当前目录结构"""
    structure = {
        "ai_modules": [],
        "core_modules": [],
        "service_modules": [],
        "tool_modules": [],
        "hsp_modules": [],
        "shared_modules": []
    }
    
    # 检查AI模块
    if (SRC_DIR / "ai").exists():
        for item in (SRC_DIR / "ai").iterdir():
            if item.is_dir():
                _ = structure["ai_modules"].append(item.name)
    
    # 检查核心模块
    if (SRC_DIR / "core").exists():
        for item in (SRC_DIR / "core").iterdir():
            if item.is_dir():
                _ = structure["core_modules"].append(item.name)
    
    return structure

def check_import_mappings() -> Dict[str, str]:
    """检查导入映射是否需要更新"""
    # 当前的导入映射
    current_mappings = {
        # AI模块的修复
        "from core_ai.": "from apps.backend.src.ai.",
        "import core_ai.": "import apps.backend.src.ai.",
        
        # Core模块的修复
        "from core.": "from apps.backend.src.core.",
        "import core.": "import apps.backend.src.core.",
        
        # Services模块的修复
        "from services.": "from apps.backend.src.core.services.",
        "import services.": "import apps.backend.src.core.services.",
        
        # Tools模块的修复
        "from tools.": "from apps.backend.src.core.tools.",
        "import tools.": "import apps.backend.src.core.tools.",
        
        # HSP模块的修复
        "from hsp.": "from apps.backend.src.core.hsp.",
        "import hsp.": "import apps.backend.src.core.hsp.",
        
        # Shared模块的修复
        "from shared.": "from apps.backend.src.core.shared.",
        "import shared.": "import apps.backend.src.core.shared.",
        
        # Agents模块的修复
        "from agents.": "from apps.backend.src.ai.agents.",
        "import agents.": "import apps.backend.src.ai.agents.",
    }
    
    # 检查是否有新的模块需要添加到映射中
    structure = check_directory_structure()
    
    # 为AI模块添加映射
    for module in structure["ai_modules"]:
        if module not in ["agents", "base", "specialized"]:  # 排除已特殊处理的模块
            key1 = f"from core_ai.{module}."
            value1 = f"from apps.backend.src.ai.{module}."
            key2 = f"import core_ai.{module}."
            value2 = f"import apps.backend.src.ai.{module}."
            
            if key1 not in current_mappings:
                current_mappings[key1] = value1
            if key2 not in current_mappings:
                current_mappings[key2] = value2
    
    # 为核心模块添加映射
    for module in structure["core_modules"]:
        if module not in ["services", "tools", "hsp", "shared", "managers", "memory"]:  # 排除已特殊处理的模块
            key1 = f"from core.{module}."
            value1 = f"from apps.backend.src.core.{module}."
            key2 = f"import core.{module}."
            value2 = f"import apps.backend.src.core.{module}."
            
            if key1 not in current_mappings:
                current_mappings[key1] = value1
            if key2 not in current_mappings:
                current_mappings[key2] = value2
    
    return current_mappings

def update_enhanced_auto_fix():
    """更新增强版自动修复工具"""
    enhanced_fix_path = PROJECT_ROOT / "scripts" / "enhanced_auto_fix.py"
    
    if not enhanced_fix_path.exists():
        _ = print("未找到增强版自动修复工具")
        return False
    
    # 读取现有文件
    with open(enhanced_fix_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 获取当前的导入映射
    mappings = check_import_mappings()
    
    # 更新导入映射部分
    mapping_lines = []
    _ = mapping_lines.append("# 新的导入映射 - 适应重构后的目录结构")
    mapping_lines.append("NEW_IMPORT_MAPPINGS = {")
    
    for key, value in mappings.items():
        _ = mapping_lines.append(f'    "{key}": "{value}",')
    
    _ = mapping_lines.append("}")
    _ = mapping_lines.append("")
    
    # 替换文件中的导入映射部分
    import_mapping_pattern = r'# 新的导入映射 - 适应重构后的目录结构\nNEW_IMPORT_MAPPINGS = \{.*?\n\}'
    import_mapping_replacement = '\n'.join(mapping_lines[:-1])  # 去掉最后一个空行
    
    import re
    updated_content = re.sub(
        import_mapping_pattern, 
        import_mapping_replacement, 
        content, 
        flags=re.DOTALL
    )
    
    # 写入更新后的内容
    with open(enhanced_fix_path, 'w', encoding='utf-8') as f:
        _ = f.write(updated_content)
    
    _ = print("✓ 增强版自动修复工具已更新")
    return True

def update_backend_enhanced_auto_fix():
    """更新后端增强版自动修复工具"""
    backend_enhanced_fix_path = BACKEND_ROOT / "scripts" / "enhanced_auto_fix.py"
    
    if not backend_enhanced_fix_path.exists():
        _ = print("未找到后端增强版自动修复工具")
        return False
    
    # 读取现有文件
    with open(backend_enhanced_fix_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否需要更新
    if "apps.backend.src" in content:
        _ = print("后端增强版自动修复工具已经是最新版本")
        return True
    
    # 更新导入路径修复函数
    if "_fix_import_paths" in content:
        # 替换导入路径修复函数
        import re
        pattern = r'def _fix_import_paths\(self, content: str\) -> str:\n\s+"""修复导入路径"""\n\s+# 修正src导入为完整路径\n\s+content = re.sub\(\n\s+r"\(from\|import\)\s+src\.",\s*\n\s+r"\\\1 apps.backend.src.",\s*\n\s+content\n\s+\)\n\s+return content'
        replacement = '''def _fix_import_paths(self, content: str) -> str:
        """修复导入路径"""
        # 修正src导入为完整路径
        content = re.sub(
            _ = r"(from|import)\\s+src\\.", 
            r"\\\\1 apps.backend.src.", 
            content
        )
        
        # 修正core_ai导入为完整路径
        content = re.sub(
            _ = r"(from|import)\\s+core_ai\\.", 
            r"\\\\1 apps.backend.src.ai.", 
            content
        )
        
        # 修正services导入为完整路径
        content = re.sub(
            _ = r"(from|import)\\s+services\\.", 
            r"\\\\1 apps.backend.src.core.services.", 
            content
        )
        
        # 修正tools导入为完整路径
        content = re.sub(
            _ = r"(from|import)\\s+tools\\.", 
            r"\\\\1 apps.backend.src.core.tools.", 
            content
        )
        
        # 修正hsp导入为完整路径
        content = re.sub(
            _ = r"(from|import)\\s+hsp\\.", 
            r"\\\\1 apps.backend.src.core.hsp.", 
            content
        )
        
        # 修正shared导入为完整路径
        content = re.sub(
            _ = r"(from|import)\\s+shared\\.", 
            r"\\\\1 apps.backend.src.core.shared.", 
            content
        )
        
        # 修正agents导入为完整路径
        content = re.sub(
            _ = r"(from|import)\\s+agents\\.", 
            r"\\\\1 apps.backend.src.ai.agents.", 
            content
        )
        
        return content'''
        
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # 写入更新后的内容
        with open(backend_enhanced_fix_path, 'w', encoding='utf-8') as f:
            _ = f.write(updated_content)
        
        _ = print("✓ 后端增强版自动修复工具已更新")
        return True
    
    return False

def main() -> None:
    """主函数"""
    print("=== 自动修复工具更新检查 ===")
    
    # 检查目录结构
    structure = check_directory_structure()
    _ = print("当前目录结构:")
    _ = print(f"  AI模块: {structure['ai_modules']}")
    _ = print(f"  核心模块: {structure['core_modules']}")
    
    # 检查并更新导入映射
    mappings = check_import_mappings()
    _ = print(f"\n导入映射项数: {len(mappings)}")
    
    # 更新增强版自动修复工具
    _ = print("\n更新增强版自动修复工具...")
    _ = update_enhanced_auto_fix()
    
    # 更新后端增强版自动修复工具
    _ = print("\n更新后端增强版自动修复工具...")
    _ = update_backend_enhanced_auto_fix()
    
    _ = print("\n✓ 自动修复工具更新检查完成")

if __name__ == "__main__":
    _ = main()