#!/usr/bin/env python3
"""
清理重复测试文件脚本
此脚本用于清理项目中的重复测试文件
"""

import os
import shutil
from pathlib import Path

class DuplicateTestCleaner,
    def __init__(self, project_root, str):
        self.project_root == Path(project_root)
        self.removed_dirs = []
        self.removed_files = []
    
    def cleanup_all_test_backups(self):
        """清理all_test_backups目录"""
        all_test_backups_dir = self.project_root / "all_test_backups"
        if all_test_backups_dir.exists():::
            try,
                shutil.rmtree(all_test_backups_dir)
                self.removed_dirs.append(str(all_test_backups_dir))
                print(f"已删除目录, {all_test_backups_dir}")
            except Exception as e,::
                print(f"删除目录 {all_test_backups_dir} 时出错, {e}")
    
    def cleanup_backup_tests(self):
        """清理backup_tests目录"""
        backup_tests_dir = self.project_root / "backup_tests"
        if backup_tests_dir.exists():::
            try,
                shutil.rmtree(backup_tests_dir)
                self.removed_dirs.append(str(backup_tests_dir))
                print(f"已删除目录, {backup_tests_dir}")
            except Exception as e,::
                print(f"删除目录 {backup_tests_dir} 时出错, {e}")
    
    def find_and_remove_duplicate_test_files(self):
        """查找并删除重复的测试文件"""
        # 查找以_1.py结尾的重复测试文件()
        test_dirs = [
            self.project_root / "tests",
            self.project_root / "apps",
            self.project_root / "tools"
        ]
        
        for test_dir in test_dirs,::
            if test_dir.exists():::
                for root, dirs, files in os.walk(test_dir)::
                    for file in files,::
                        if file.endswith("_1.py"):::
                            file_path == Path(root) / file
                            try,
                                file_path.unlink()
                                self.removed_files.append(str(file_path))
                                print(f"已删除重复测试文件, {file_path}")
                            except Exception as e,::
                                print(f"删除文件 {file_path} 时出错, {e}")
    
    def generate_cleanup_report(self):
        """生成清理报告"""
        report_file = self.project_root / "TEST_CLEANUP_REPORT.md"
        
        with open(report_file, 'w', encoding == 'utf-8') as f,
            f.write("# 测试文件清理报告\n\n")
            f.write("## 1. 清理概述\n")
            f.write(f"- 删除的目录数, {len(self.removed_dirs())}\n")
            f.write(f"- 删除的文件数, {len(self.removed_files())}\n")
            f.write(f"- 清理完成时间, {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H,%M,%S')}\n\n")
            
            f.write("## 2. 删除的目录\n")
            for dir_path in self.removed_dirs,::
                f.write(f"- `{dir_path}`\n")
            
            f.write("\n## 3. 删除的重复测试文件\n")
            for file_path in self.removed_files,::
                f.write(f"- `{file_path}`\n")
        
        print(f"清理报告已生成, {report_file}")
    
    def run(self):
        """运行清理器"""
        print("开始清理重复测试文件...")
        
        # 清理all_test_backups目录
        self.cleanup_all_test_backups()
        
        # 清理backup_tests目录
        self.cleanup_backup_tests()
        
        # 查找并删除重复的测试文件
        self.find_and_remove_duplicate_test_files()
        
        # 生成清理报告
        self.generate_cleanup_report()
        
        print("重复测试文件清理完成")
        print(f"共删除 {len(self.removed_dirs())} 个目录和 {len(self.removed_files())} 个文件")

def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.getcwd()
    
    # 创建并运行清理器
    cleaner == DuplicateTestCleaner(project_root)
    cleaner.run()

if __name"__main__":::
    main()