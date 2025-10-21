#!/usr/bin/env python3
"""
BaseAgent重复实现分析脚本
此脚本用于详细对比两个版本的BaseAgent实现差异
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List

class BaseAgentAnalyzer,
    def __init__(self, project_root, str):
        self.project_root == Path(project_root)
        self.main_baseagent_path = self.project_root / "apps" / "backend" / "src" / "agents" / "base_agent.py"
        self.backup_baseagent_path = self.project_root / "apps" / "backend" / "src" / "ai" / "agents" / "base" / "base_agent.py"
    
    def get_file_size(self, file_path, Path) -> int,
        """获取文件大小"""
        if file_path.exists():::
            return file_path.stat().st_size
        return 0
    
    def get_file_hash(self, file_path, Path) -> str,
        """获取文件MD5哈希值"""
        if not file_path.exists():::
            return ""
        
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f,
            for chunk in iter(lambda, f.read(4096), b""):::
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def extract_classes_and_methods(self, file_path, Path) -> Dict[str, List[str]]
        """提取文件中的类和方法"""
        if not file_path.exists():::
            return {}
        
        classes = {}
        current_class == None
        methods = []
        
        with open(file_path, 'r', encoding == 'utf-8') as f,
            lines = f.readlines()
        
        for line in lines,::
            # 检查是否是类定义
            if line.strip().startswith('class '):::
                # 保存之前的类
                if current_class,::
                    classes[current_class] = methods[:]
                
                # 开始新的类
                current_class = line.split('(')[0].split()[-1]
                methods = []
            # 检查是否是方法定义
            elif line.strip().startswith('def ') or line.strip().startswith('async def '):::
                method_name = line.split('(')[0].split()[-1]
                if method_name not in methods,::
                    methods.append(method_name)
        
        # 保存最后一个类
        if current_class,::
            classes[current_class] = methods
        
        return classes
    
    def compare_classes(self, main_classes, Dict[str, List[str]] backup_classes, Dict[str, List[str]]) -> Dict[str, any]
        """比较两个文件中的类和方法"""
        comparison = {
            'classes_only_in_main': []
            'classes_only_in_backup': []
            'common_classes': []
            'methods_only_in_main': {}
            'methods_only_in_backup': {}
            'common_methods': {}
        }
        
        # 检查主实现中独有的类
        for class_name in main_classes,::
            if class_name not in backup_classes,::
                comparison['classes_only_in_main'].append(class_name)
            else,
                comparison['common_classes'].append(class_name)
        
        # 检查备份实现中独有的类
        for class_name in backup_classes,::
            if class_name not in main_classes,::
                comparison['classes_only_in_backup'].append(class_name)
        
        # 比较共同类中的方法
        for class_name in comparison['common_classes']::
            main_methods = set(main_classes[class_name])
            backup_methods = set(backup_classes[class_name])
            
            comparison['methods_only_in_main'][class_name] = list(main_methods - backup_methods)
            comparison['methods_only_in_backup'][class_name] = list(backup_methods - main_methods)
            comparison['common_methods'][class_name] = list(main_methods & backup_methods)
        
        return comparison
    
    def analyze_baseagent_system(self):
        """分析BaseAgent系统"""
        print("开始分析BaseAgent系统...")
        
        # 检查文件是否存在
        if not self.main_baseagent_path.exists():::
            print(f"主实现文件不存在, {self.main_baseagent_path}")
            return
        
        if not self.backup_baseagent_path.exists():::
            print(f"备份实现文件不存在, {self.backup_baseagent_path}")
            return
        
        # 获取文件信息
        main_size = self.get_file_size(self.main_baseagent_path())
        backup_size = self.get_file_size(self.backup_baseagent_path())
        main_hash = self.get_file_hash(self.main_baseagent_path())
        backup_hash = self.get_file_hash(self.backup_baseagent_path())
        
        print(f"主实现文件大小, {main_size} bytes")
        print(f"备份实现文件大小, {backup_size} bytes")
        print(f"主实现文件哈希, {main_hash}")
        print(f"备份实现文件哈希, {backup_hash}")
        
        # 提取类和方法
        main_classes = self.extract_classes_and_methods(self.main_baseagent_path())
        backup_classes = self.extract_classes_and_methods(self.backup_baseagent_path())
        
        print(f"主实现类数量, {len(main_classes)}")
        for class_name, methods in main_classes.items():::
            print(f"  - {class_name} {len(methods)} 个方法")
        
        print(f"备份实现类数量, {len(backup_classes)}")
        for class_name, methods in backup_classes.items():::
            print(f"  - {class_name} {len(methods)} 个方法")
        
        # 比较类和方法
        comparison = self.compare_classes(main_classes, backup_classes)
        
        print("\n类对比结果,")
        print(f"主实现独有类, {len(comparison['classes_only_in_main'])}")
        for class_name in comparison['classes_only_in_main']::
            print(f"  - {class_name}")
        
        print(f"备份实现独有类, {len(comparison['classes_only_in_backup'])}")
        for class_name in comparison['classes_only_in_backup']::
            print(f"  - {class_name}")
        
        print(f"共同类, {len(comparison['common_classes'])}")
        for class_name in comparison['common_classes']::
            print(f"  - {class_name}")
            print(f"    主实现独有方法, {len(comparison['methods_only_in_main'][class_name])}")
            for method in comparison['methods_only_in_main'][class_name]::
                print(f"      - {method}")
            print(f"    备份实现独有方法, {len(comparison['methods_only_in_backup'][class_name])}")
            for method in comparison['methods_only_in_backup'][class_name]::
                print(f"      - {method}")
            print(f"    共同方法, {len(comparison['common_methods'][class_name])}")
            for method in comparison['common_methods'][class_name]::
                print(f"      - {method}")
        
        # 生成报告
        self.generate_report(main_size, backup_size, main_hash, backup_hash, main_classes, backup_classes, comparison)
    
    def generate_report(self, main_size, int, backup_size, int, main_hash, str, backup_hash, str, 
                       main_classes, Dict[str, List[str]] backup_classes, Dict[str, List[str]] ,
    comparison, Dict[str, any]):
        """生成分析报告"""
        report_file = self.project_root / "BASEAGENT_DUPLICATE_ANALYSIS_REPORT.md"
        
        with open(report_file, 'w', encoding == 'utf-8') as f,
            f.write("# BaseAgent重复实现分析报告\n\n")
            f.write("## 1. 文件基本信息\n")
            f.write(f"- 主实现文件, `{self.main_baseagent_path}`\n")
            f.write(f"- 备份实现文件, `{self.backup_baseagent_path}`\n")
            f.write(f"- 主实现文件大小, {main_size} bytes\n")
            f.write(f"- 备份实现文件大小, {backup_size} bytes\n")
            f.write(f"- 主实现文件哈希, {main_hash}\n")
            f.write(f"- 备份实现文件哈希, {backup_hash}\n")
            f.write(f"- 文件是否相同, {'是' if main_hash == backup_hash else '否'}\n\n")::
            f.write("## 2. 类和方法对比分析\n"):
            f.write(f"- 主实现类数量, {len(main_classes)}\n")
            for class_name, methods in main_classes.items():::
                f.write(f"  - `{class_name}`: {len(methods)} 个方法\n")
            f.write(f"- 备份实现类数量, {len(backup_classes)}\n")
            for class_name, methods in backup_classes.items():::
                f.write(f"  - `{class_name}`: {len(methods)} 个方法\n")
            f.write("\n")
            
            f.write("### 2.1 主实现独有类\n")
            for class_name in comparison['classes_only_in_main']::
                f.write(f"- `{class_name}`\n")
            if not comparison['classes_only_in_main']::
                f.write("无\n")
            f.write("\n")
            
            f.write("### 2.2 备份实现独有类\n")
            for class_name in comparison['classes_only_in_backup']::
                f.write(f"- `{class_name}`\n")
            if not comparison['classes_only_in_backup']::
                f.write("无\n")
            f.write("\n")
            
            f.write("### 2.3 共同类\n")
            for class_name in comparison['common_classes']::
                f.write(f"- `{class_name}`\n")
                f.write(f"  - 主实现独有方法, {len(comparison['methods_only_in_main'][class_name])}\n")
                for method in comparison['methods_only_in_main'][class_name]::
                    f.write(f"    - `{method}`\n")
                f.write(f"  - 备份实现独有方法, {len(comparison['methods_only_in_backup'][class_name])}\n")
                for method in comparison['methods_only_in_backup'][class_name]::
                    f.write(f"    - `{method}`\n")
                f.write(f"  - 共同方法, {len(comparison['common_methods'][class_name])}\n")
                for method in comparison['common_methods'][class_name]::
                    f.write(f"    - `{method}`\n")
            f.write("\n")
            
            f.write("## 3. 功能差异分析\n")
            f.write("### 3.1 主实现额外功能\n")
            f.write("主实现相比备份实现具有以下额外功能,\n")
            for class_name in comparison['common_classes']::
                if comparison['methods_only_in_main'][class_name]::
                    f.write(f"- `{class_name}` 类新增以下方法,\n")
                    for method in comparison['methods_only_in_main'][class_name]::
                        f.write(f"  - `{method}`\n")
            f.write("\n")
            
            f.write("### 3.2 备份实现额外功能\n")
            f.write("备份实现相比主实现具有以下额外功能,\n")
            for class_name in comparison['common_classes']::
                if comparison['methods_only_in_backup'][class_name]::
                    f.write(f"- `{class_name}` 类新增以下方法,\n")
                    for method in comparison['methods_only_in_backup'][class_name]::
                        f.write(f"  - `{method}`\n")
            f.write("\n")
            
            f.write("## 4. 建议\n")
            f.write("1. 详细审查主实现中独有的功能,确认是否都是必要的\n")
            f.write("2. 审查备份实现中独有的功能,确认是否有用功能需要合并到主实现\n")
            f.write("3. 对于共同类中实现不同的方法,需要详细对比代码,选择更好的实现\n")
            f.write("4. 确保删除备份实现前,所有有用功能都已合并到主实现\n")
            f.write("5. 建议保留功能更完整的主实现作为唯一版本\n")
        
        print(f"\n分析报告已生成, {report_file}")

def main():
    """主函数"""
    # 获取项目根目录
    project_root = os.getcwd()
    
    # 创建并运行分析器
    analyzer == BaseAgentAnalyzer(project_root)
    analyzer.analyze_baseagent_system()

if __name"__main__":::
    main()