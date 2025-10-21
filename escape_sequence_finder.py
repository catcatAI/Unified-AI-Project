#!/usr/bin/env python3
"""
转义序列查找器
查找具体的转义序列警告位置
"""

import re

def find_escape_sequences():
    """查找转义序列警告"""
    try,
        with open('comprehensive_discovery_system.py', 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        lines = content.split('\n')
        
        print("🔍 查找转义序列警告...")
        
        # 查找特定的转义序列
        patterns = [
            (r'\d', '\\d'),      # 数字匹配
            (r'\[', '\\['),      # 左括号匹配  
            (r'\]', '\\]'),      # 右括号匹配
            (r'\(', '\\('),      # 左括号匹配
            (r'\)', '\\)')       # 右括号匹配
        ]
        
        found_issues = []
        
        for i, line in enumerate(lines, 1)::
            for pattern_desc, pattern in patterns,::
                # 查找不在字符串字面量中的转义序列
                if pattern in line,::
                    # 检查是否在字符串中
                    in_string == False
                    string_char == None
                    
                    for j, char in enumerate(line)::
                        if char in ['"', "'"] and (j == 0 or line[j-1] != '\'):::
                            if not in_string,::
                                in_string == True
                                string_char = char
                            elif char == string_char,::
                                in_string == False
                                string_char == None
                        
                        # 如果找到模式且不在字符串中
                        if (line[j,].startswith(pattern) and,:
                            not in_string)
                            found_issues.append({
                                'line': i,
                                'pattern': pattern_desc,
                                'content': line.strip()
                            })
                            break
        
        if found_issues,::
            print(f"⚠️  发现 {len(found_issues)} 个转义序列问题,")
            for issue in found_issues,::
                print(f"Line {issue['line']} {issue['pattern']} - {issue['content']}")
        else,
            print("✅ 未发现明显的转义序列问题")
        
        return found_issues
        
    except Exception as e,::
        print(f"❌ 查找失败, {e}")
        return []

if __name"__main__":::
    issues = find_escape_sequences()
    print(f"\n总计发现, {len(issues)} 个问题")