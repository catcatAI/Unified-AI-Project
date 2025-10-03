#!/usr/bin/env python3
"""
导入路径更新脚本
此脚本用于更新项目中所有文件的引用路径
"""

import os
import re
from pathlib import Path

class ImportPathUpdater:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.updated_files = []
        self.failed_files = []
    
    def update_python_imports(self, file_path: Path):
        """更新Python文件中的导入路径"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 保存原始内容用于比较
            original_content = content
            
            # 更新scripts导入路径
            # 将 "from scripts." 替换为 "from tools.scripts."
            content = re.sub(r'from scripts\.', 'from tools.scripts.', content)
            # 将 "import scripts." 替换为 "import tools.scripts."
            content = re.sub(r'import scripts\.', 'import tools.scripts.', content)
            
            # 如果内容有变化，写回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.updated_files.append(str(file_path))
                print(f"已更新: {file_path}")
                return True
            
            return False
        except Exception as e:
            print(f"更新文件 {file_path} 时出错: {e}")
            self.failed_files.append((str(file_path), str(e)))
            return False
    
    def update_bat_imports(self, file_path: Path):
        """更新批处理文件中的路径引用"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 保存原始内容用于比较
            original_content = content
            
            # 更新scripts目录引用
            content = content.replace('scripts\\', 'tools\\scripts\\')
            content = content.replace('scripts/', 'tools/scripts/')
            
            # 如果内容有变化，写回文件
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.updated_files.append(str(file_path))
                print(f"已更新: {file_path}")
                return True
            
            return False
        except Exception as e:
            print(f"更新文件 {file_path} 时出错: {e}")
            self.failed_files.append((str(file_path), str(e)))
            return False
    
    def update_all_imports(self):
        """更新所有文件的导入路径"""
        print("开始更新导入路径...")
        
        # 支持的文件类型
        python_extensions = ['.py']
        bat_extensions = ['.bat', '.ps1']
        
        # 遍历项目中的所有文件
        for root, dirs, files in os.walk(self.project_root):
            # 跳过某些目录
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules', 'backup_before_merge', 'backup_before_script_migration']]
            
            for file in files:
                file_path = Path(root) / file
                file_extension = file_path.suffix.lower()
                
                # 更新Python文件中的导入路径
                if file_extension in python_extensions:
                    self.update_python_imports(file_path)
                
                # 更新批处理文件中的路径引用
                elif file_extension in bat_extensions:
                    self.update_bat_imports(file_path)
        
        print(f"导入路径更新完成")
        print(f"已更新 {len(self.updated_files)} 个文件")
        if self.failed_files:
            print(f"更新失败 {len(self.failed_files)} 个文件")
    
    def generate_report(self):
        """生成更新报告"""
        report_file = self.project_root / "IMPORT_PATH_UPDATE_REPORT.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 导入路径更新报告\n\n")
            f.write("## 1. 更新概述\n")
            f.write(f"- 总文件数: {len(self.updated_files) + len(self.failed_files)}\n")
            f.write(f"- 成功更新: {len(self.updated_files)}\n")
            f.write(f"- 更新失败: {len(self.failed_files)}\n")
            f.write(f"- 更新成功率: {len(self.updated_files) / (len(self.updated_files) + len(self.failed_files)) * 100:.2f}%\n\n")
            
            f.write("## 2. 成功更新的文件\n")
            for file_path in self.updated_files:
                f.write(f"- `{file_path}`\n")
            
            if self.failed_files:
                f.write("\n## 3. 更新失败的文件\n")
                for file_path, error in self.failed_files:
                    f.write(f"- `{file_path}`: {error}\n")
        
        print(f"更新报告已生成: {report_file}")
    
    def run(self):
        """运行导入路径更新器"""
        print("开始更新导入路径...")
        
        # 更新所有导入路径
        self.update_all_imports()
        
        # 生成报告
        self.generate_report()
        
        print("导入路径更新完成")

def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.getcwd()
    
    # 创建并运行导入路径更新器
    updater = ImportPathUpdater(project_root)
    updater.run()

if __name__ == "__main__":
    main()