#!/usr/bin/env python3
"""
HAM记忆系统重复实现分析脚本
此脚本用于详细对比主实现和备份实现的HAM记忆系统差异
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

class HAMAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.main_ham_path = self.project_root / "apps" / "backend" / "src" / "ai" / "memory" / "ham_memory_manager.py"
        self.backup_ham_path = self.project_root / "backup_modules" / "ai_backup" / "memory" / "ham_memory_manager.py"
    
    def get_file_size(self, file_path: Path) -> int:
        """获取文件大小"""
        if file_path.exists():
            return file_path.stat().st_size
        return 0
    
    def get_file_hash(self, file_path: Path) -> str:
        """获取文件MD5哈希值"""
        if not file_path.exists():
            return ""
        
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def extract_functions(self, file_path: Path) -> Dict[str, str]:
        """提取文件中的函数"""
        if not file_path.exists():
            return {}
        
        functions = {}
        current_function = None
        current_code = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            # 检查是否是函数定义
            if line.strip().startswith('def ') or line.strip().startswith('async def '):
                # 保存之前的函数
                if current_function:
                    functions[current_function] = ''.join(current_code)
                
                # 开始新的函数
                current_function = line.split('(')[0].split()[-1]
                current_code = [line]
            elif current_function:
                # 继续收集当前函数的代码
                current_code.append(line)
        
        # 保存最后一个函数
        if current_function:
            functions[current_function] = ''.join(current_code)
        
        return functions
    
    def compare_functions(self, main_functions: Dict[str, str], backup_functions: Dict[str, str]) -> Dict[str, str]:
        """比较两个文件中的函数"""
        comparison = {
            'only_in_main': [],
            'only_in_backup': [],
            'different_implementation': []
        }
        
        # 检查主实现中独有的函数
        for func_name in main_functions:
            if func_name not in backup_functions:
                comparison['only_in_main'].append(func_name)
        
        # 检查备份实现中独有的函数
        for func_name in backup_functions:
            if func_name not in main_functions:
                comparison['only_in_backup'].append(func_name)
        
        # 检查实现不同的函数
        for func_name in main_functions:
            if func_name in backup_functions:
                main_hash = hashlib.md5(main_functions[func_name].encode()).hexdigest()
                backup_hash = hashlib.md5(backup_functions[func_name].encode()).hexdigest()
                if main_hash != backup_hash:
                    comparison['different_implementation'].append(func_name)
        
        return comparison
    
    def analyze_ham_system(self):
        """分析HAM记忆系统"""
        print("开始分析HAM记忆系统...")
        
        # 检查文件是否存在
        if not self.main_ham_path.exists():
            print(f"主实现文件不存在: {self.main_ham_path}")
            return
        
        if not self.backup_ham_path.exists():
            print(f"备份实现文件不存在: {self.backup_ham_path}")
            return
        
        # 获取文件信息
        main_size = self.get_file_size(self.main_ham_path)
        backup_size = self.get_file_size(self.backup_ham_path)
        main_hash = self.get_file_hash(self.main_ham_path)
        backup_hash = self.get_file_hash(self.backup_ham_path)
        
        print(f"主实现文件大小: {main_size} bytes")
        print(f"备份实现文件大小: {backup_size} bytes")
        print(f"主实现文件哈希: {main_hash}")
        print(f"备份实现文件哈希: {backup_hash}")
        
        # 提取函数
        main_functions = self.extract_functions(self.main_ham_path)
        backup_functions = self.extract_functions(self.backup_ham_path)
        
        print(f"主实现函数数量: {len(main_functions)}")
        print(f"备份实现函数数量: {len(backup_functions)}")
        
        # 比较函数
        comparison = self.compare_functions(main_functions, backup_functions)
        
        print("\n函数对比结果:")
        print(f"主实现独有函数: {len(comparison['only_in_main'])}")
        for func in comparison['only_in_main']:
            print(f"  - {func}")
        
        print(f"\n备份实现独有函数: {len(comparison['only_in_backup'])}")
        for func in comparison['only_in_backup']:
            print(f"  - {func}")
        
        print(f"\n实现不同的函数: {len(comparison['different_implementation'])}")
        for func in comparison['different_implementation']:
            print(f"  - {func}")
        
        # 生成报告
        self.generate_report(main_size, backup_size, main_hash, backup_hash, comparison)
    
    def generate_report(self, main_size: int, backup_size: int, main_hash: str, backup_hash: str, comparison: Dict[str, List[str]]):
        """生成分析报告"""
        report_file = self.project_root / "HAM_DUPLICATE_ANALYSIS_REPORT.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# HAM记忆系统重复实现分析报告\n\n")
            f.write("## 1. 文件基本信息\n")
            f.write(f"- 主实现文件: `{self.main_ham_path}`\n")
            f.write(f"- 备份实现文件: `{self.backup_ham_path}`\n")
            f.write(f"- 主实现文件大小: {main_size} bytes\n")
            f.write(f"- 备份实现文件大小: {backup_size} bytes\n")
            f.write(f"- 主实现文件哈希: {main_hash}\n")
            f.write(f"- 备份实现文件哈希: {backup_hash}\n")
            f.write(f"- 文件是否相同: {'是' if main_hash == backup_hash else '否'}\n\n")
            
            f.write("## 2. 函数对比分析\n")
            f.write(f"- 主实现函数数量: {len([f for f in comparison.keys() if f != 'only_in_main' and f != 'only_in_backup' and f != 'different_implementation']) + len(comparison['only_in_main'])}\n")
            f.write(f"- 备份实现函数数量: {len([f for f in comparison.keys() if f != 'only_in_main' and f != 'only_in_backup' and f != 'different_implementation']) + len(comparison['only_in_backup'])}\n\n")
            
            f.write("### 2.1 主实现独有函数\n")
            for func in comparison['only_in_main']:
                f.write(f"- `{func}`\n")
            if not comparison['only_in_main']:
                f.write("无\n")
            f.write("\n")
            
            f.write("### 2.2 备份实现独有函数\n")
            for func in comparison['only_in_backup']:
                f.write(f"- `{func}`\n")
            if not comparison['only_in_backup']:
                f.write("无\n")
            f.write("\n")
            
            f.write("### 2.3 实现不同的函数\n")
            for func in comparison['different_implementation']:
                f.write(f"- `{func}`\n")
            if not comparison['different_implementation']:
                f.write("无\n")
            f.write("\n")
            
            f.write("## 3. 建议\n")
            f.write("1. 详细审查备份实现中独有的函数，确认是否有用功能需要合并到主实现\n")
            f.write("2. 对于实现不同的函数，需要详细对比代码，选择更好的实现\n")
            f.write("3. 确保删除备份实现前，所有有用功能都已合并到主实现\n")
        
        print(f"\n分析报告已生成: {report_file}")

def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.getcwd()
    
    # 创建并运行分析器
    analyzer = HAMAnalyzer(project_root)
    analyzer.analyze_ham_system()

if __name__ == "__main__":
    main()