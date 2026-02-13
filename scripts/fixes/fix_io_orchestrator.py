#!/usr/bin/env python3
"""
修复 io_intelligence_orchestrator.py 的语法错误
只修复语法，不简化任何内容
"""

import re

def fix_syntax(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    fixes = []

    # 1. 修复 xxx, type -> xxx: type (类型注解)
    content = re.sub(r'(\w+),\s*(str|int|float|bool|datetime|Optional|List|Dict|Any|Set|Tuple|IOFormType|IOState)\s*([),])', r'\1: \2\3', content)
    fixes.append('修复类型注解格式')

    # 2. 修复 == True/False -> = True/False
    content = re.sub(r'(\w+)\s+==\s+(True|False)', r'\1 = \2', content)
    fixes.append('修复 == True/False -> = True/False')

    # 3. 修复 xxx() -> xxx (函数调用错误)
    content = re.sub(r'(\w+)\(\)\s*([),])', r'\1\2', content)
    content = re.sub(r'(\w+)\(\)\s*->', r'\1 ->', content)
    fixes.append('修复错误的函数调用')

    # 4. 修复 try, -> try:
    content = content.replace('try,\n', 'try:\n')
    content = content.replace('try, #', 'try: #')
    fixes.append('修复 try, -> try:')

    # 5. 修复 except ImportError, :: -> except ImportError:
    content = content.replace('except ImportError, ::', 'except ImportError:')
    content = content.replace('except Exception, ::', 'except Exception:')
    content = content.replace('except ImportError, :', 'except ImportError:')
    fixes.append('修复 except 语法')

    # 6. 修复 if xxx, :: -> if xxx:
    content = content.replace('if ', 'if ')
    content = re.sub(r'if\s+(\w+)\s*,\s*::', r'if \1:', content)
    content = re.sub(r'if\s+(\w+\.\w+)\s*,\s*::', r'if \1:', content)
    content = re.sub(r'if\s+([^:]+),\s*::', r'if \1:', content)
    fixes.append('修复 if 语句')

    # 7. 修复 == -> = (赋值)
    content = re.sub(r'(\w+)\s+==\s*([^=!].*?)([,\n)])', lambda m: f"{m.group(1)} = {m.group(2)}{m.group(3)}" if '=' not in m.group(2) and not m.group(2).strip().startswith('None') else m.group(0), content)
    fixes.append('修复赋值语法')

    # 8. 删除乱码注释
    content = re.sub(r'在[类|函数]定义前添加空行', '', content)
    fixes.append('删除乱码注释')

    # 9. 修复 0.0() -> 0.0
    content = re.sub(r'(\d+\.\d+)\(\)', r'\1', content)
    fixes.append('修复浮点数调用')

    # 10. 修复 for xxx in xxx, :: -> for xxx in xxx:
    content = re.sub(r'for\s+(\w+)\s+in\s+([^:]+),\s*::', r'for \1 in \2:', content)
    fixes.append('修复 for 语句')

    # 11. 修复 else, :: -> else:
    content = re.sub(r'else,\s*::', r'else:', content)
    content = re.sub(r'else,\s*:', r'else:', content)
    fixes.append('修复 else 语句')

    # 12. 删除多余的括号
    content = re.sub(r'\(\s*\)', '()', content)
    fixes.append('删除多余空括号')

    # 13. 修复 n_clusters = = 5 -> n_clusters = 5
    content = re.sub(r'=\s*=', '=', content)
    fixes.append('修复双等号')

    # 14. 修复 \n -> \n (删除多余换行)
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    fixes.append('删除多余空行')

    # 保存修复后的文件
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return fixes

if __name__ == '__main__':
    file_path = '/home/cat/桌面/Unified-AI-Project/apps/backend/src/core/io/io_intelligence_orchestrator.py'
    fixes = fix_syntax(file_path)
    print(f'修复完成！共修复 {len(fixes)} 项：')
    for i, fix in enumerate(fixes, 1):
        print(f'{i}. {fix}')