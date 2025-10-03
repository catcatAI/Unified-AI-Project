#!/usr/bin/env python3
"""
重构验证脚本
此脚本用于验证重构后的项目是否正常工作
"""

import os
import sys
from pathlib import Path

class RefactorVerifier:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues = []
        self.success_count = 0
    
    def verify_directory_structure(self):
        """验证目录结构"""
        print("验证目录结构...")
        
        required_dirs = [
            "docs/architecture",
            "docs/development", 
            "docs/api",
            "docs/testing",
            "docs/deployment",
            "docs/reports",
            "tools/scripts",
            "tools/dev-tools",
            "tools/build-tools",
            "tools/test-tools",
            "tools/deployment-tools"
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                self.issues.append(f"缺少目录: {dir_path}")
                print(f"❌ 缺少目录: {dir_path}")
            else:
                self.success_count += 1
                print(f"✅ 目录存在: {dir_path}")
    
    def verify_file_migration(self):
        """验证文件迁移"""
        print("\n验证文件迁移...")
        
        # 检查scripts目录是否为空或不存在
        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists() and any(scripts_dir.iterdir()):
            # 检查是否有非目录文件
            has_files = False
            for item in scripts_dir.iterdir():
                if item.is_file():
                    has_files = True
                    break
            
            if has_files:
                self.issues.append("scripts目录中仍有文件未迁移")
                print("❌ scripts目录中仍有文件未迁移")
            else:
                self.success_count += 1
                print("✅ scripts目录已清理")
        else:
            self.success_count += 1
            print("✅ scripts目录已清理")
        
        # 检查tools/scripts目录是否有文件
        tools_scripts_dir = self.project_root / "tools" / "scripts"
        if tools_scripts_dir.exists() and any(tools_scripts_dir.iterdir()):
            self.success_count += 1
            print("✅ tools/scripts目录中有文件")
        else:
            self.issues.append("tools/scripts目录为空")
            print("❌ tools/scripts目录为空")
        
        # 检查docs目录是否有文件
        docs_dir = self.project_root / "docs"
        md_files = list(docs_dir.rglob("*.md"))
        if len(md_files) > 100:  # 应该有大量文档文件
            self.success_count += 1
            print(f"✅ docs目录中有 {len(md_files)} 个文档文件")
        else:
            self.issues.append(f"docs目录中文档文件过少: {len(md_files)}")
            print(f"❌ docs目录中文档文件过少: {len(md_files)}")
    
    def verify_import_paths(self):
        """验证导入路径"""
        print("\n验证导入路径...")
        
        # 检查一些关键文件是否使用了新的导入路径
        key_files = [
            "tools/scripts/execute_refactor_plan.py",
            "tools/scripts/analyze_ham_duplicates.py",
            "tools/scripts/analyze_baseagent_duplicates.py"
        ]
        
        for file_path in key_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 检查是否还存在旧的导入路径
                    if "from scripts." in content:
                        self.issues.append(f"文件 {file_path} 中仍存在旧的导入路径")
                        print(f"❌ 文件 {file_path} 中仍存在旧的导入路径")
                    else:
                        self.success_count += 1
                        print(f"✅ 文件 {file_path} 中导入路径已更新")
                except Exception as e:
                    self.issues.append(f"读取文件 {file_path} 时出错: {e}")
                    print(f"❌ 读取文件 {file_path} 时出错: {e}")
            else:
                self.issues.append(f"文件不存在: {file_path}")
                print(f"❌ 文件不存在: {file_path}")
    
    def verify_duplicate_removal(self):
        """验证重复文件删除"""
        print("\n验证重复文件删除...")
        
        # 检查备份实现是否已删除
        backup_files = [
            "backup_modules/ai_backup/memory/ham_memory_manager.py",
            "apps/backend/src/ai/agents/base/base_agent.py",
            "backup_modules/ai_backup/agents/base/base_agent.py"
        ]
        
        deleted_count = 0
        for file_path in backup_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                deleted_count += 1
                self.success_count += 1
                print(f"✅ 已删除重复文件: {file_path}")
            else:
                self.issues.append(f"重复文件未删除: {file_path}")
                print(f"❌ 重复文件未删除: {file_path}")
        
        if deleted_count == len(backup_files):
            print("✅ 所有重复文件已删除")
    
    def run(self):
        """运行验证器"""
        print("开始验证重构结果...")
        
        # 执行各项验证
        self.verify_directory_structure()
        self.verify_file_migration()
        self.verify_import_paths()
        self.verify_duplicate_removal()
        
        # 输出总结
        print("\n" + "="*50)
        print("重构验证总结")
        print("="*50)
        print(f"成功项: {self.success_count}")
        print(f"问题项: {len(self.issues)}")
        
        if self.issues:
            print("\n发现的问题:")
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")
            print(f"\n重构验证完成，发现 {len(self.issues)} 个问题需要处理")
            return False
        else:
            print("\n✅ 重构验证通过！所有检查项均正常")
            return True

def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.getcwd()
    
    # 创建并运行验证器
    verifier = RefactorVerifier(project_root)
    success = verifier.run()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
