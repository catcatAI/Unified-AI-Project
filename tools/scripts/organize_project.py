#!/usr/bin/env python3
"""
项目文件整理脚本
用于整理项目根目录下的零散文件
"""

import os
import shutil
from pathlib import Path
import glob

def create_directories():
    """创建必要的目录结构"""
    directories = [
        'docs',
        'scripts/backup',
        'scripts/test',
        'scripts/utils',
        'configs',
        'logs',
        'backup',
        'test_reports',
        'test_data'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"创建目录: {directory}")

def move_documentation_files():
    """移动文档文件到docs目录"""
    # 获取所有.md文件（除了README.md和CHANGELOG.md）
    md_files = glob.glob("*.md")
    
    # 排除重要文件
    important_files = ['README.md', 'CHANGELOG.md']
    files_to_move = [f for f in md_files if f not in important_files]
    
    for file in files_to_move:
        try:
            shutil.move(file, f"docs/{file}")
            print(f"移动文档文件: {file} -> docs/{file}")
        except Exception as e:
            print(f"移动文件 {file} 失败: {e}")

def move_script_files():
    """移动脚本文件到scripts目录"""
    # Python脚本
    py_files = glob.glob("*.py")
    for file in py_files:
        # 跳过项目必要的脚本文件
        if file in ['check_file.py']:
            continue
        try:
            shutil.move(file, f"scripts/{file}")
            print(f"移动Python脚本: {file} -> scripts/{file}")
        except Exception as e:
            print(f"移动文件 {file} 失败: {e}")
    
    # Batch脚本
    bat_files = glob.glob("*.bat")
    for file in bat_files:
        try:
            shutil.move(file, f"scripts/{file}")
            print(f"移动Batch脚本: {file} -> scripts/{file}")
        except Exception as e:
            print(f"移动文件 {file} 失败: {e}")
    
    # PowerShell脚本
    ps1_files = glob.glob("*.ps1")
    for file in ps1_files:
        try:
            shutil.move(file, f"scripts/{file}")
            print(f"移动PowerShell脚本: {file} -> scripts/{file}")
        except Exception as e:
            print(f"移动文件 {file} 失败: {e}")

def move_test_files():
    """移动测试相关文件"""
    # 测试报告文件
    test_report_files = glob.glob("*.json")
    for file in test_report_files:
        if 'test' in file.lower() or 'report' in file.lower():
            try:
                shutil.move(file, f"test_reports/{file}")
                print(f"移动测试报告: {file} -> test_reports/{file}")
            except Exception as e:
                print(f"移动文件 {file} 失败: {e}")
    
    # 测试数据文件
    test_data_files = glob.glob("*.txt")
    for file in test_data_files:
        if 'test' in file.lower():
            try:
                shutil.move(file, f"test_data/{file}")
                print(f"移动测试数据: {file} -> test_data/{file}")
            except Exception as e:
                print(f"移动文件 {file} 失败: {e}")

def move_config_files():
    """移动配置文件到configs目录"""
    config_files = [
        'pyrightconfig.json',
        'pytest.ini'
    ]
    
    for file in config_files:
        if os.path.exists(file):
            try:
                shutil.move(file, f"configs/{file}")
                print(f"移动配置文件: {file} -> configs/{file}")
            except Exception as e:
                print(f"移动文件 {file} 失败: {e}")

def cleanup_temporary_files():
    """清理临时文件"""
    # 临时的txt文件
    temp_files = glob.glob("temp_*.txt")
    for file in temp_files:
        try:
            os.remove(file)
            print(f"删除临时文件: {file}")
        except Exception as e:
            print(f"删除文件 {file} 失败: {e}")
    
    # 其他临时文件
    temp_files = glob.glob("*.tmp")
    for file in temp_files:
        try:
            os.remove(file)
            print(f"删除临时文件: {file}")
        except Exception as e:
            print(f"删除文件 {file} 失败: {e}")

def main():
    """主函数"""
    print("开始整理项目文件...")
    
    # 创建目录结构
    create_directories()
    
    # 移动各类文件
    move_documentation_files()
    move_script_files()
    move_test_files()
    move_config_files()
    
    # 清理临时文件
    cleanup_temporary_files()
    
    print("项目文件整理完成!")

if __name__ == "__main__":
    main()