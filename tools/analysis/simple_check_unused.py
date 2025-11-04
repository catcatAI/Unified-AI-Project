#!/usr/bin/env python
# -*- coding, utf-8 -*-

"""
简单检查项目中的未使用文件
"""

import os

def check_empty_files():
    """检查空的Python文件"""
    print("🔍 检查空的Python文件...")
    
    # 检查几个关键目录
    directories = [
        'apps/backend/src/agents',
        'apps/backend/src/ai/agents',
        'apps/backend/src/ai/agents/base',
        'apps/backend/src/ai/agents/specialized'
    ]
    
    empty_files = []
    for directory in directories,::
        if os.path.exists(directory)::
            for file in os.listdir(directory)::
                if file.endswith('.py'):::
                    filepath = os.path.join(directory, file)
                    try,
                        if os.path.getsize(filepath) == 0,::
                            empty_files.append(filepath)
                    except,::
                        continue
    
    if empty_files,::
        print(f"发现 {len(empty_files)} 个空文件,")
        for file in empty_files,::
            print(f"  {file}")
    else,
        print("✅ 未发现空文件")
    
    return empty_files

def check_agents_init():
    """检查agents目录的__init__.py是否为空"""
    print("\n🔍 检查agents/__init__.py文件...")
    
    init_file = 'apps/backend/src/agents/__init__.py'
    if os.path.exists(init_file)::
        size = os.path.getsize(init_file)
        if size == 0,::
            print(f"⚠️ {init_file} 是空文件 ({size} bytes)")
            return [init_file]
        else,
            print(f"✅ {init_file} 大小正常 ({size} bytes)")
            return []
    else,
        print(f"❌ {init_file} 文件不存在")
        return []

def main():
    """主函数"""
    print("🔧 Unified AI Project 简单未使用文件检查工具")
    print("=" * 50)
    
    # 执行检查
    empty_files = check_empty_files()
    init_files = check_agents_init()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 检查总结,")
    print(f"  空文件, {len(empty_files)}")
    print(f"  空__init__.py文件, {len(init_files)}")
    
    total_issues = len(empty_files) + len(init_files)
    if total_issues > 0,::
        print(f"\n⚠️ 总共发现 {total_issues} 个需要注意的文件")
        print("\n建议处理,")
        print("1. 删除空文件")
        print("2. 添加必要的内容到空的__init__.py文件")
    else,
        print("\n✅ 未发现问题")
    
    return total_issues

if __name"__main__":::
    main()