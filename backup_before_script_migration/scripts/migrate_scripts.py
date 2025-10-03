#!/usr/bin/env python3
"""
脚本文件迁移脚本
此脚本用于将scripts目录下的文件迁移到tools/scripts目录
"""

import os
import shutil
from pathlib import Path

class ScriptMigrator:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.source_dir = self.project_root / "scripts"
        self.target_dir = self.project_root / "tools" / "scripts"
        self.backup_dir = self.project_root / "backup_before_script_migration"
    
    def backup_scripts(self):
        """备份scripts目录"""
        print("创建scripts目录备份...")
        if self.source_dir.exists():
            # 创建备份目录
            self.backup_dir.mkdir(exist_ok=True)
            
            # 复制整个scripts目录到备份目录
            backup_scripts_dir = self.backup_dir / "scripts"
            if backup_scripts_dir.exists():
                shutil.rmtree(backup_scripts_dir)
            
            shutil.copytree(self.source_dir, backup_scripts_dir)
            print(f"已备份scripts目录到 {backup_scripts_dir}")
    
    def migrate_scripts(self):
        """迁移脚本文件"""
        print("开始迁移脚本文件...")
        
        # 检查源目录是否存在
        if not self.source_dir.exists():
            print(f"源目录不存在: {self.source_dir}")
            return False
        
        # 检查目标目录是否存在
        if not self.target_dir.exists():
            print(f"目标目录不存在: {self.target_dir}")
            return False
        
        # 迁移文件
        migrated_count = 0
        for item in self.source_dir.iterdir():
            # 跳过__pycache__目录
            if item.name == "__pycache__":
                continue
                
            # 跳过子目录（除了core, data_migration, data_processing, modules, prototypes, utils）
            if item.is_dir() and item.name not in ["core", "data_migration", "data_processing", "modules", "prototypes", "utils"]:
                print(f"跳过目录: {item.name}")
                continue
            
            # 构造目标路径
            target_path = self.target_dir / item.name
            
            # 如果目标路径已存在，先备份
            if target_path.exists():
                backup_path = self.backup_dir / "tools_scripts" / item.name
                backup_path.parent.mkdir(exist_ok=True, parents=True)
                if target_path.is_dir():
                    if backup_path.exists():
                        shutil.rmtree(backup_path)
                    shutil.copytree(target_path, backup_path)
                else:
                    shutil.copy2(target_path, backup_path)
                print(f"已备份现有文件: {target_path} -> {backup_path}")
            
            # 移动文件或目录
            if target_path.exists():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
            
            shutil.move(str(item), str(target_path))
            print(f"已迁移: {item.name}")
            migrated_count += 1
        
        print(f"共迁移 {migrated_count} 个文件/目录")
        return True
    
    def update_imports(self):
        """更新导入路径"""
        print("更新导入路径...")
        # 这里可以添加具体的导入路径更新逻辑
        # 由于这是一个复杂的任务，我们只打印提示信息
        print("请手动更新项目中对迁移脚本的引用路径")
        print("将 'from scripts.xxx import yyy' 更新为 'from tools.scripts.xxx import yyy'")
    
    def run(self):
        """运行脚本迁移器"""
        print("开始迁移脚本文件...")
        
        # 创建备份
        self.backup_scripts()
        
        # 迁移脚本
        if self.migrate_scripts():
            # 更新导入路径提示
            self.update_imports()
            print("脚本文件迁移完成")
        else:
            print("脚本文件迁移失败")

def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.getcwd()
    
    # 创建并运行脚本迁移器
    migrator = ScriptMigrator(project_root)
    migrator.run()

if __name__ == "__main__":
    main()