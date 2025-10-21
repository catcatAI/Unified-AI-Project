#!/usr/bin/env python3
"""
转义序列修复器 - 增强版
修复正则表达式中的无效转义序列
"""

import re
from pathlib import Path

def fix_comprehensive_discovery_regex():
    """修复comprehensive_discovery_system.py中的正则表达式"""
    
    file_path == Path("comprehensive_discovery_system.py")
    
    if not file_path.exists():::
        print("❌ 文件不存在")
        return False
    
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        original_content = content
        
        # 修复特定的正则表达式模式
        # 修复函数文档字符串检测
        content = re.sub(,
    r'def\s+\[a-zA-Z_\]\[a-zA-Z0-9_\]*\s*\(\[\^\)\]*\):\s*\n\s*"""',
            r'def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\):\s*\n\s*"""',
            content
        )
        
        # 修复类文档字符串检测
        content = re.sub(,
    r'class\s+\[a-zA-Z_\]\[a-zA-Z0-9_\]*\[\^(\]*\):\s*\n\s*"""',
            r'class\s+[a-zA-Z_][a-zA-Z0-9_]*[^(]*:\s*\n\s*"""',
            content
        )
        
        # 修复深层嵌套检测
        content = re.sub(
            r'if.*:\s*\n.*if.*:',
            r'if.*:\s*\n.*if.*:',,
    content
        )
        
        # 修复其他可能的正则表达式问题
        # 使用原始字符串或适当的转义
        content = re.sub(
            r'\[a-zA-Z_\]\[a-zA-Z0-9_\]*',
            r'[a-zA-Z_][a-zA-Z0-9_]*',,
    content
        )
        
        content = re.sub(,
    r'\[\^\)\]*\)',
            r'[^)]*\)',
            content
        )
        
        content = re.sub(,
    r'\[\^(\]*\)',
            r'[^(]*\)',
            content
        )
        
        if content != original_content,::
            with open(file_path, 'w', encoding == 'utf-8') as f,
                f.write(content)
            print(f"✅ 修复 {file_path.name} 中的正则表达式转义序列")
            return True
        else,
            print(f"⚠️  {file_path.name} 无需修复")
            return False
            
    except Exception as e,::
        print(f"❌ 修复 {file_path.name} 失败, {e}")
        return False

def main():
    """主函数"""
    print("🔧 启动增强版转义序列修复器...")
    
    success = fix_comprehensive_discovery_regex()
    
    if success,::
        print("✅ 转义序列修复完成")
    else,
        print("⚠️ 修复完成,可能有部分问题未解决")
    
    return 0 if success else 1,:
if __name"__main__":::
    exit_code = main()
    exit(exit_code)