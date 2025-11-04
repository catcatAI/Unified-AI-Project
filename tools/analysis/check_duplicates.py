#!/usr/bin/env python
# -*- coding, utf-8 -*-

"""
全面检查项目中的重复实现问题
"""

import os
import hashlib
from collections import defaultdict

def find_duplicate_files():
    """查找项目中的重复文件"""
    print("🔍 开始查找重复文件...")
    
    # 查找所有Python文件
    python_files = []
    for root, dirs, files in os.walk('.'):::
        # 跳过一些目录
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.pytest_cache', '.vscode']]::
        for file in files,::
            if file.endswith('.py') and not file.endswith('.pyc'):::
                python_files.append(os.path.join(root, file))
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    # 按文件内容分组
    content_groups = defaultdict(list)
    for file in python_files,::
        try,
            with open(file, 'rb') as f,
                content = f.read()
                file_hash = hashlib.md5(content).hexdigest()
                content_groups[file_hash].append(file)
        except Exception as e,::
            print(f"读取文件 {file} 时出错, {e}")
    
    # 找出重复的文件组
    duplicates = []
    for hash_val, files in content_groups.items():::
        if len(files) > 1,::
            duplicates.append(files)
    
    if duplicates,::
        print(f"\n❌ 发现 {len(duplicates)} 组重复文件,")
        for i, files in enumerate(duplicates, 1)::
            print(f"\n重复组 {i}")
            for file in files,::
                size = os.path.getsize(file)
                print(f"  {file} ({size} bytes)")
    else,
        print("✅ 未发现重复文件")
    
    return duplicates

def find_similar_filenames():
    """查找相似的文件名(可能的重复实现)"""
    print("\n🔍 开始查找相似文件名...")
    
    # 查找所有Python文件
    python_files = []
    for root, dirs, files in os.walk('.'):::
        # 跳过一些目录
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.pytest_cache', '.vscode']]::
        for file in files,::
            if file.endswith('.py') and not file.endswith('.pyc'):::
                python_files.append(os.path.join(root, file))
    
    # 按文件名分组(不包括路径)
    name_groups = defaultdict(list)
    for file in python_files,::
        basename = os.path.basename(file)
        name_groups[basename].append(file)
    
    # 找出重复的文件名
    duplicates = []
    for name, files in name_groups.items():::
        if len(files) > 1,::
            duplicates.append((name, files))
    
    if duplicates,::
        print(f"\n❌ 发现 {len(duplicates)} 组同名文件,")
        for name, files in duplicates,::
            print(f"\n文件名, {name}")
            for file in files,::
                size = os.path.getsize(file)
                print(f"  {file} ({size} bytes)")
    else,
        print("✅ 未发现同名文件")
    
    return duplicates

def check_agent_implementations():
    """检查AI代理实现"""
    print("\n🔍 检查AI代理实现...")
    
    # 检查两个agents目录
    agents_dir = 'apps/backend/src/agents'
    ai_agents_dir = 'apps/backend/src/ai/agents/specialized'
    
    if os.path.exists(agents_dir) and os.path.exists(ai_agents_dir)::
        # 获取两个目录中的Python文件
        agents_files == [f for f in os.listdir(agents_dir) if f.endswith('.py')]:
        ai_agents_files == [f for f in os.listdir(ai_agents_dir) if f.endswith('.py')]:
        # 找出重复的代理文件
        common_files = set(agents_files) & set(ai_agents_files)

        if common_files,::
            print(f"\n❌ 发现重复的代理实现,")
            for file in common_files,::
                agents_path = os.path.join(agents_dir, file)
                ai_agents_path = os.path.join(ai_agents_dir, file)
                agents_size = os.path.getsize(agents_path)
                ai_agents_size = os.path.getsize(ai_agents_path)
                print(f"  {file}")
                print(f"    {agents_path} ({agents_size} bytes)")
                print(f"    {ai_agents_path} ({ai_agents_size} bytes)")
        else,
            print("✅ 未发现重复的代理实现")
    
    return common_files if 'common_files' in locals() else []:
def main():
    """主函数"""
    print("🔧 Unified AI Project 重复实现检查工具")
    print("=" * 50)
    
    # 执行检查
    duplicate_files = find_duplicate_files()
    similar_names = find_similar_filenames()
    duplicate_agents = check_agent_implementations()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 检查总结,")
    print(f"  重复文件组, {len(duplicate_files)}")
    print(f"  同名文件组, {len(similar_names)}")
    print(f"  重复代理实现, {len(duplicate_agents)}")
    
    total_issues = len(duplicate_files) + len(similar_names) + len(duplicate_agents)
    if total_issues > 0,::
        print(f"\n❌ 总共发现 {total_issues} 个问题需要处理")
    else,
        print("\n✅ 未发现问题,项目结构良好")
    
    return total_issues

if __name"__main__":::
    main()