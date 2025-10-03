#!/usr/bin/env python3
"""
HAM记忆系统实现合并脚本
此脚本用于合并主实现和备份实现的功能
"""

import os
import shutil
from pathlib import Path

class HAMMerger:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.main_ham_path = self.project_root / "apps" / "backend" / "src" / "ai" / "memory" / "ham_memory_manager.py"
        self.backup_ham_path = self.project_root / "backup_modules" / "ai_backup" / "memory" / "ham_memory_manager.py"
        self.backup_dir = self.project_root / "backup_before_merge"
    
    def backup_files(self):
        """备份文件"""
        print("创建备份...")
        self.backup_dir.mkdir(exist_ok=True)
        
        if self.main_ham_path.exists():
            shutil.copy2(self.main_ham_path, self.backup_dir / "ham_memory_manager_main.py")
            print(f"已备份主实现到 {self.backup_dir / 'ham_memory_manager_main.py'}")
        
        if self.backup_ham_path.exists():
            shutil.copy2(self.backup_ham_path, self.backup_dir / "ham_memory_manager_backup.py")
            print(f"已备份备份实现到 {self.backup_dir / 'ham_memory_manager_backup.py'}")
    
    def merge_implementations(self):
        """合并实现"""
        print("开始合并HAM记忆系统实现...")
        
        # 检查文件是否存在
        if not self.main_ham_path.exists():
            print(f"错误: 主实现文件不存在 {self.main_ham_path}")
            return False
        
        if not self.backup_ham_path.exists():
            print(f"警告: 备份实现文件不存在 {self.backup_ham_path}")
            return True
        
        # 读取两个文件的内容
        with open(self.main_ham_path, 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        with open(self.backup_ham_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()
        
        # 分析备份实现中独有的功能
        backup_functions = self.extract_functions(backup_content)
        main_functions = self.extract_functions(main_content)
        
        # 找出备份实现中独有的函数
        unique_functions = {}
        for func_name, func_code in backup_functions.items():
            if func_name not in main_functions:
                unique_functions[func_name] = func_code
                print(f"发现备份实现独有函数: {func_name}")
        
        # 如果有独有函数，需要手动合并
        if unique_functions:
            print("备份实现中包含主实现没有的函数，需要手动合并:")
            for func_name in unique_functions:
                print(f"  - {func_name}")
            
            # 将这些函数添加到主实现中
            print("正在将备份实现独有函数添加到主实现...")
            merged_content = self.add_functions_to_main(main_content, unique_functions)
            
            # 保存合并后的内容
            with open(self.main_ham_path, 'w', encoding='utf-8') as f:
                f.write(merged_content)
            
            print("已将备份实现独有函数合并到主实现")
        else:
            print("备份实现中没有主实现没有的函数")
        
        return True
    
    def extract_functions(self, content: str) -> dict:
        """提取函数"""
        functions = {}
        lines = content.split('\n')
        current_function = None
        current_code = []
        
        for line in lines:
            # 检查是否是函数定义
            if line.strip().startswith('def ') or line.strip().startswith('async def '):
                # 保存之前的函数
                if current_function:
                    functions[current_function] = '\n'.join(current_code)
                
                # 开始新的函数
                current_function = line.split('(')[0].split()[-1]
                current_code = [line]
            elif current_function:
                # 继续收集当前函数的代码
                current_code.append(line)
        
        # 保存最后一个函数
        if current_function:
            functions[current_function] = '\n'.join(current_code)
        
        return functions
    
    def add_functions_to_main(self, main_content: str, functions: dict) -> str:
        """将函数添加到主实现"""
        # 在文件末尾添加函数
        merged_content = main_content
        
        # 添加一个分隔注释
        merged_content += "\n\n# 从备份实现合并的函数\n"
        
        # 添加函数
        for func_name, func_code in functions.items():
            merged_content += f"\n{func_code}\n"
        
        return merged_content
    
    def remove_backup_implementation(self):
        """删除备份实现"""
        print("删除备份实现...")
        if self.backup_ham_path.exists():
            self.backup_ham_path.unlink()
            print(f"已删除备份实现: {self.backup_ham_path}")
        
        # 检查备份实现所在的目录是否为空，如果为空则删除
        backup_memory_dir = self.backup_ham_path.parent
        if backup_memory_dir.exists() and not any(backup_memory_dir.iterdir()):
            backup_memory_dir.rmdir()
            print(f"已删除空目录: {backup_memory_dir}")
            
            # 继续向上检查目录
            backup_ai_dir = backup_memory_dir.parent
            if backup_ai_dir.exists() and not any(backup_ai_dir.iterdir()):
                backup_ai_dir.rmdir()
                print(f"已删除空目录: {backup_ai_dir}")
                
                backup_modules_dir = backup_ai_dir.parent
                if backup_modules_dir.exists() and not any(backup_modules_dir.iterdir()):
                    backup_modules_dir.rmdir()
                    print(f"已删除空目录: {backup_modules_dir}")
    
    def run(self):
        """运行合并器"""
        print("开始合并HAM记忆系统实现...")
        
        # 创建备份
        self.backup_files()
        
        # 合并实现
        if self.merge_implementations():
            # 删除备份实现
            self.remove_backup_implementation()
            print("HAM记忆系统实现合并完成")
        else:
            print("HAM记忆系统实现合并失败")

def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.getcwd()
    
    # 创建并运行合并器
    merger = HAMMerger(project_root)
    merger.run()

if __name__ == "__main__":
    main()