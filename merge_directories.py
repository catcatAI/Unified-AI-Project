#!/usr/bin/env python3
"""
目錄合併腳本
此腳本用於自動完成 Unified AI 項目的目錄合併重構
"""

import os
import shutil
import sys
from pathlib import Path

def merge_directories():
    """執行目錄合併操作"""
    # 定義項目根目錄
    project_root = Path(__file__).parent
    backend_src = project_root / "apps" / "backend" / "src"
    
    # 定義源目錄和目標目錄
    core_ai_dir = backend_src / "core_ai"
    ai_dir = backend_src / "ai"
    
    # 檢查源目錄是否存在
    if not core_ai_dir.exists():
        print(f"源目錄 {core_ai_dir} 不存在")
        return False
    
    # 創建目標目錄（如果不存在）
    ai_dir.mkdir(exist_ok=True)
    
    # 定義需要移動的子目錄
    subdirs = ["memory", "agents", "context", "concept_models"]
    
    # 移動子目錄
    for subdir in subdirs:
        source = core_ai_dir / subdir
        target = ai_dir / subdir
        
        if source.exists():
            # 如果目標目錄已存在，先刪除
            if target.exists():
                shutil.rmtree(target)
            
            # 移動目錄
            shutil.move(str(source), str(target))
            print(f"已移動 {source} 到 {target}")
        else:
            print(f"源目錄 {source} 不存在，跳過")
    
    # 刪除空的 core_ai 目錄
    try:
        core_ai_dir.rmdir()
        print(f"已刪除空目錄 {core_ai_dir}")
    except OSError as e:
        print(f"無法刪除目錄 {core_ai_dir}: {e}")
    
    return True

def update_import_paths():
    """更新導入路徑"""
    project_root = Path(__file__).parent
    backend_src = project_root / "apps" / "backend" / "src"
    
    # 需要更新的文件列表
    files_to_update = [
        backend_src / "core_services.py"
    ]
    
    # 導入路徑映射
    import_mapping = {
        "apps.backend.src.core_ai": "apps.backend.src.ai",
        ".core_ai": ".ai",
        "core_ai.": "ai."
    }
    
    # 更新每個文件中的導入路徑
    for file_path in files_to_update:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替換導入路徑
            original_content = content
            for old_path, new_path in import_mapping.items():
                content = content.replace(old_path, new_path)
            
            # 如果內容有變化，寫回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"已更新 {file_path} 中的導入路徑")
            else:
                print(f"{file_path} 中沒有需要更新的導入路徑")
        else:
            print(f"文件 {file_path} 不存在")

def main():
    """主函數"""
    print("開始目錄合併過程...")
    
    # 執行目錄合併
    if merge_directories():
        print("目錄合併完成")
    else:
        print("目錄合併失敗")
        sys.exit(1)
    
    # 更新導入路徑
    print("開始更新導入路徑...")
    update_import_paths()
    print("導入路徑更新完成")
    
    print("所有操作已完成，請運行測試以驗證更改")

if __name__ == "__main__":
    main()