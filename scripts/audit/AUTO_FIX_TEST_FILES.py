#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修復測試文件中的語法錯誤
"""

import os
import re
from pathlib import Path

def fix_syntax_errors_in_file(file_path: Path) -> tuple:
    """修復單個文件中的語法錯誤"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 修復規則1: try, -> try:
        content = re.sub(r'\btry\s*,\s*$', 'try:', content, flags=re.MULTILINE)

        # 修復規則2: except Exception as e,:: -> except Exception as e:
        content = re.sub(r'\bexcept\s+([^\n]+)\s*,::', r'except \1:', content)
        content = re.sub(r'\bexcept\s+([^\n:]+)\s*,:', r'except \1:', content)

        # 修復規則3: if nlp,:: -> if nlp:
        content = re.sub(r'\b(if|elif|else|for|while|with|def|class)\s*,\s*$', r'\1:', content, flags=re.MULTILINE)

        # 修復規則4: :: -> :
        content = re.sub(r'\s*::\s*$', ':', content, flags=re.MULTILINE)
        content = re.sub(r':::', ':', content)

        # 修復規則5: 賦值錯誤 analyzer == ContentAnalyzerModule() -> analyzer = ContentAnalyzerModule()
        content = re.sub(r'\b(\w+)\s*==\s*([A-Z]\w+\(.*?\))', r'\1 = \2', content)
        content = re.sub(r'\b(\w+)\s*==\s*None', r'\1 = None', content)

        # 修復規則6: for node, data in ... data == True) -> for node, data in ... data=True)
        content = re.sub(r'(\w+)\s*==\s*True\)', r'\1=True)', content)

        # 修復規則7: import xxx,:: -> import xxx:
        content = re.sub(r'import\s+([^\n]+)\s*,:', r'import \1', content)

        # 修復規則8: 編碼聲明錯誤 # -*- coding, utf-8 -*- -> # -*- coding: utf-8 -*-
        content = re.sub(r'# -\*- coding,\s*utf-8\s*-\*-', '# -*- coding: utf-8 -*-', content)

        # 修復規則9: 條件語句中的錯誤 if nlp,::
        content = re.sub(r'\b(if|elif)\s+(\w+)\s*,\s*::', r'\1 \2:', content)

        # 修復規則10: for 循環中的錯誤 for ent in doc.ents,::
        content = re.sub(r'\bfor\s+([^\n:]+)\s*::', r'for \1:', content)

        # 修復規則11: 錯誤的打印格式 "Error, {e}" -> "Error: {e}"
        content = re.sub(r'"([^"]*),\s*\{([^}]+)\}"', r'"\1: {\2}"', content)
        content = re.sub(r"'([^']*),\s*\{([^}]+)\}'", r"'\1: {\2}'", content)

        # 修復規則12: 括號後的逗號
        content = re.sub(r'\)\s*,\s*$', '),', content, flags=re.MULTILINE)

        # 如果沒有變化，返回
        if content == original_content:
            return False, "無需修復"

        # 驗證修復後的語法
        import ast
        try:
            ast.parse(content)
            # 語法正確，寫回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, "修復成功"
        except SyntaxError as e:
            # 修復後仍有錯誤，返回錯誤信息
            return False, f"修復後仍有錯誤: {e.msg} (line {e.lineno})"

    except Exception as e:
        return False, f"處理失敗: {str(e)}"

def fix_all_test_files(project_root: Path):
    """修復所有測試文件"""
    test_dir = project_root / 'tests'

    if not test_dir.exists():
        print(f"測試目錄不存在: {test_dir}")
        return

    py_files = list(test_dir.rglob("*.py"))

    print(f"找到 {len(py_files)} 個測試文件")
    print("=" * 60)

    success_count = 0
    fail_count = 0
    no_fix_count = 0

    for py_file in py_files:
        # 跳過 __pycache__
        if '__pycache__' in str(py_file):
            continue

        success, message = fix_syntax_errors_in_file(py_file)
        rel_path = py_file.relative_to(project_root)

        if success:
            print(f"✓ {rel_path} - {message}")
            success_count += 1
        elif message == "無需修復":
            # 跳過顯示
            no_fix_count += 1
        else:
            print(f"✗ {rel_path} - {message}")
            fail_count += 1

    print("=" * 60)
    print(f"修復統計:")
    print(f"  成功修復: {success_count} 個文件")
    print(f"  無需修復: {no_fix_count} 個文件")
    print(f"  修復失敗: {fail_count} 個文件")

    return success_count, fail_count

def main():
    """主函數"""
    project_root = Path(__file__).parent / 'Unified-AI-Project'

    print("開始批量修復測試文件...")
    print(f"項目根目錄: {project_root}")
    print()

    success_count, fail_count = fix_all_test_files(project_root)

    if fail_count > 0:
        print(f"\n⚠ 警告: {fail_count} 個文件修復失敗，需要手動處理")
        exit(1)
    elif success_count > 0:
        print(f"\n✓ 成功修復 {success_count} 個文件")
        exit(0)
    else:
        print(f"\n✓ 所有測試文件都正常")
        exit(0)

if __name__ == '__main__':
    main()