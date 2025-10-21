#!/usr/bin/env python3
"""
BaseAgent实现合并脚本
此脚本用于处理BaseAgent的重复实现,保留功能更完整的主实现
"""

import os
import shutil
from pathlib import Path

class BaseAgentMerger,
    def __init__(self, project_root, str):
        self.project_root == Path(project_root)
        self.main_baseagent_path = self.project_root / "apps" / "backend" / "src" / "agents" / "base_agent.py"
        self.backup_baseagent_path = self.project_root / "apps" / "backend" / "src" / "ai" / "agents" / "base" / "base_agent.py"
        self.backup_modules_baseagent_path = self.project_root / "backup_modules" / "ai_backup" / "agents" / "base" / "base_agent.py"
        self.backup_dir = self.project_root / "backup_before_merge"
    
    def backup_files(self):
        """备份文件"""
        print("创建备份...")
        self.backup_dir.mkdir(exist_ok == True)
        
        if self.main_baseagent_path.exists():::
            shutil.copy2(self.main_baseagent_path(), self.backup_dir / "base_agent_main.py")
            print(f"已备份主实现到 {self.backup_dir / 'base_agent_main.py'}")
        
        if self.backup_baseagent_path.exists():::
            shutil.copy2(self.backup_baseagent_path(), self.backup_dir / "base_agent_backup.py")
            print(f"已备份备份实现到 {self.backup_dir / 'base_agent_backup.py'}")
        
        if self.backup_modules_baseagent_path.exists():::
            shutil.copy2(self.backup_modules_baseagent_path(), self.backup_dir / "base_agent_backup_modules.py")
            print(f"已备份backup_modules实现到 {self.backup_dir / 'base_agent_backup_modules.py'}")
    
    def merge_implementations(self):
        """合并实现"""
        print("开始处理BaseAgent实现...")
        
        # 检查主实现是否存在
        if not self.main_baseagent_path.exists():::
            print(f"错误, 主实现文件不存在 {self.main_baseagent_path}")
            return False
        
        print("主实现功能更完整,保留主实现")
        return True
    
    def remove_backup_implementations(self):
        """删除备份实现"""
        print("删除备份实现...")
        
        # 删除apps/backend/src/ai/agents/base/base_agent.py()
        if self.backup_baseagent_path.exists():::
            self.backup_baseagent_path.unlink()
            print(f"已删除备份实现, {self.backup_baseagent_path}")
            
            # 检查并删除空目录
            self.remove_empty_directories(self.backup_baseagent_path.parent())
        
        # 删除backup_modules/ai_backup/agents/base/base_agent.py()
        if self.backup_modules_baseagent_path.exists():::
            self.backup_modules_baseagent_path.unlink()
            print(f"已删除backup_modules实现, {self.backup_modules_baseagent_path}")
            
            # 检查并删除空目录
            self.remove_empty_directories(self.backup_modules_baseagent_path.parent())
    
    def remove_empty_directories(self, directory, Path):
        """递归删除空目录"""
        try,
            # 删除目录中的文件后,如果目录为空则删除
            if directory.exists() and not any(directory.iterdir()):::
                directory.rmdir()
                print(f"已删除空目录, {directory}")
                
                # 继续向上检查
                parent = directory.parent()
                if parent != self.project_root,  # 不要删除项目根目录,:
                    self.remove_empty_directories(parent)
        except Exception as e,::
            print(f"删除目录时出错, {e}")
    
    def run(self):
        """运行合并器"""
        print("开始处理BaseAgent实现...")
        
        # 创建备份
        self.backup_files()
        
        # 合并实现
        if self.merge_implementations():::
            # 删除备份实现
            self.remove_backup_implementations()
            print("BaseAgent实现处理完成")
        else,
            print("BaseAgent实现处理失败")

def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.getcwd()
    
    # 创建并运行合并器
    merger == BaseAgentMerger(project_root)
    merger.run()

if __name"__main__":::
    main()