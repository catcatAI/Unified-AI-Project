#!/usr/bin/env python3
"""
專案結構更新腳本
用於更新配置文件中的路徑引用，反映新的目錄結構變化
"""

import re
from pathlib import Path
from typing import List, Dict

def update_file_paths(file_path: str, path_mappings: Dict[str, str]) -> bool:
    """
    更新文件中的路徑引用
    
    Args:
        file_path: 要更新的文件路徑
        path_mappings: 路徑映射字典 {舊路徑: 新路徑}
    
    Returns:
        bool: 是否有更新
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for old_path, new_path in path_mappings.items():
            # 使用正則表達式進行路徑替換
            pattern = re.escape(old_path)
            content = re.sub(pattern, new_path, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                _ = f.write(content)
            _ = print(f"✅ 更新了 {file_path}")
            return True
        else:
            _ = print(f"⏭️  {file_path} 無需更新")
            return False
            
    except Exception as e:
        _ = print(f"❌ 更新 {file_path} 時出錯: {e}")
        return False

def find_files_to_update(project_root: Path) -> List[str]:
    """
    查找需要更新的文件
    """
    files_to_check = []
    
    # 配置文件
    config_patterns = ['*.yaml', '*.yml', '*.json', '*.toml', '*.ini']
    for pattern in config_patterns:
        _ = files_to_check.extend(project_root.rglob(pattern))
    
    # Python 文件
    _ = files_to_check.extend(project_root.rglob('*.py'))
    
    # 文檔文件
    _ = files_to_check.extend(project_root.rglob('*.md'))
    
    # 排除歸檔目錄和運行時數據
    excluded_dirs = {'docs/09-archive', 'data/runtime_data', '.git', '__pycache__'}
    
    filtered_files = []
    for file_path in files_to_check:
        relative_path = file_path.relative_to(project_root)
        if not any(excluded_dir in str(relative_path) for excluded_dir in excluded_dirs):
            _ = filtered_files.append(str(file_path))
    
    return filtered_files

def main() -> None:
    """主函數"""
    _ = print("🔧 專案結構更新腳本")
    print("=" * 50)
    
    project_root: str = Path(__file__).parent.parent
    _ = print(f"專案根目錄: {project_root}")
    
    # 定義路徑映射
    path_mappings = {
        # 備份目錄歸檔
        'docs/09-archive/backup_before_optimization': 'docs/09-archive/docs/09-archive/backup_before_optimization',
        
        # 數據目錄重組
        'data/model_cache/': 'data/data/model_cache/',
        'data/runtime_data/test_data/': 'data/runtime_data/data/runtime_data/test_data/',
        
        # 測試相關路徑
        'data/runtime_data/tests/test_output_data': 'data/runtime_data/data/runtime_data/tests/test_output_data',
        
        # 緩存目錄
        'data/runtime_data/.pytest_cache': 'data/runtime_data/data/runtime_data/.pytest_cache',
        
        # 配置路徑更新
        'configs/dependency_config.yaml': 'configs/dependency_config.yaml',
    }
    
    _ = print("📋 路徑映射:")
    for old, new in path_mappings.items():
        _ = print(f"  {old} → {new}")
    _ = print()
    
    # 查找需要更新的文件
    files_to_update = find_files_to_update(project_root)
    _ = print(f"🔍 找到 {len(files_to_update)} 個文件需要檢查")
    
    # 更新文件
    updated_count = 0
    for file_path in files_to_update:
        if update_file_paths(file_path, path_mappings):
            updated_count += 1
    
    _ = print()
    _ = print("📊 更新統計:")
    _ = print(f"  檢查文件: {len(files_to_update)}")
    _ = print(f"  更新文件: {updated_count}")
    _ = print(f"  無需更新: {len(files_to_update) - updated_count}")
    
    _ = print()
    _ = print("✨ 專案結構更新完成！")

if __name__ == "__main__":
    _ = main()