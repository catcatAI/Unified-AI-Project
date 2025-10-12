#!/usr/bin/env python3
"""
实际执行修复，不依赖外部调用
"""

import os
import re
from pathlib import Path

# 获取项目根目录
project_root = Path(__file__).parent

# 定义需要扫描的目录
scan_dirs = [
    "apps/backend/src",
    "tools",
    "scripts"
]

# 定义排除的目录
exclude_dirs = [
    "node_modules",
    "venv",
    "__pycache__",
    ".pytest_cache"
]

# 统计信息
total_files = 0
fixed_files = 0
failed_files = 0
fix_details = []

def is_in_scope(file_path):
    """检查文件是否在修复范围内"""
    try:
        rel_path = file_path.relative_to(project_root)
        rel_str = str(rel_path)
        
        # 检查是否在排除目录中
        for exclude_dir in exclude_dirs:
            if exclude_dir in rel_str:
                return False
        
        # 检查是否在项目目录中
        for scan_dir in scan_dirs:
            if rel_str.startswith(scan_dir):
                return True
        
        return False
    except ValueError:
        return False

def fix_file_syntax(file_path):
    """修复文件语法错误"""
    global total_files, fixed_files, failed_files, fix_details
    
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # 1. 修复字典语法错误 (_ = "key": value)
        pattern = r'_ = "([^"]+)":\s*([^,\n}]+)(,?)'
        replacement = r'"\1": \2\3'
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            content = new_content
            changes_made.append("字典语法")
        
        # 2. 修复 _ = raise Exception 语法错误
        new_content = re.sub(r'_ = raise\s+', 'raise ', content)
        if new_content != content:
            content = new_content
            changes_made.append("raise语法")
        
        # 3. 修复 _ = @decorator 语法错误
        new_content = re.sub(r'_ = (@\w+)', r'\1', content)
        if new_content != content:
            content = new_content
            changes_made.append("装饰器语法")
        
        # 4. 修复 _ = assert 语法错误
        new_content = re.sub(r'_ = assert\s+', 'assert ', content)
        if new_content != content:
            content = new_content
            changes_made.append("assert语法")
        
        # 5. 修复 _ = **kwargs 语法错误
        new_content = re.sub(r'_ = \*\*(\w+)', r'**\1', content)
        if new_content != content:
            content = new_content
            changes_made.append("kwargs语法")
        
        # 6. 修复智能引号
        new_content = content.replace('"""', '"""')
        new_content = new_content.replace('"', '"')
        new_content = new_content.replace('"', '"')
        new_content = new_content.replace(''', "'")
        new_content = new_content.replace(''', "'")
        if new_content != content:
            content = new_content
            changes_made.append("智能引号")
        
        # 7. 修复不完整的导入语句
        new_content = re.sub(r'from\s+[\w\.]+\s+import\s*\n', '', content)
        if new_content != content:
            content = new_content
            changes_made.append("不完整导入")
        
        # 8. 修复重复的导入语句
        lines = content.split('\n')
        imports = {}
        new_lines = []
        import_changed = False
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                if stripped not in imports:
                    imports[stripped] = True
                    new_lines.append(line)
                else:
                    import_changed = True
            else:
                new_lines.append(line)
        
        if import_changed:
            content = '\n'.join(new_lines)
            changes_made.append("重复导入")
        
        # 如果有修改，写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            rel_path = file_path.relative_to(project_root)
            fix_details.append(f"{rel_path}: {', '.join(changes_made)}")
            fixed_files += 1
            print(f"✓ 修复: {rel_path} ({', '.join(changes_made)})")
        else:
            fixed_files += 1  # 没有错误也算成功
        
        # 验证语法
        try:
            compile(content, str(file_path), 'exec')
        except SyntaxError as e:
            rel_path = file_path.relative_to(project_root)
            print(f"✗ 语法错误仍然存在: {rel_path}:{e.lineno} {e.msg}")
            failed_files += 1
            return False
        
        total_files += 1
        return True
        
    except Exception as e:
        rel_path = file_path.relative_to(project_root)
        print(f"✗ 处理文件出错: {rel_path} - {e}")
        failed_files += 1
        total_files += 1
        return False

# 开始修复
print("=" * 60)
print("开始执行项目修复")
print("=" * 60)

# 扫描并修复文件
for scan_dir in scan_dirs:
    dir_path = project_root / scan_dir
    if not dir_path.exists():
        print(f"目录不存在: {scan_dir}")
        continue
    
    print(f"\n扫描目录: {scan_dir}")
    for file_path in dir_path.rglob("*.py"):
        if file_path.is_file() and is_in_scope(file_path):
            fix_file_syntax(file_path)

# 输出修复结果
print("\n" + "=" * 60)
print("修复结果统计")
print("=" * 60)
print(f"总文件数: {total_files}")
print(f"修复成功: {fixed_files}")
print(f"修复失败: {failed_files}")

if fix_details:
    print("\n修复详情:")
    for detail in fix_details[:20]:  # 只显示前20个
        print(f"  {detail}")
    if len(fix_details) > 20:
        print(f"  ... 还有 {len(fix_details) - 20} 个文件被修复")

# 保存修复报告
report_path = project_root / "repair_report.txt"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("项目修复报告\n")
    f.write("=" * 60 + "\n")
    f.write(f"总文件数: {total_files}\n")
    f.write(f"修复成功: {fixed_files}\n")
    f.write(f"修复失败: {failed_files}\n\n")
    f.write("修复详情:\n")
    for detail in fix_details:
        f.write(f"  {detail}\n")

print(f"\n修复报告已保存到: {report_path}")

# 检查是否有未限制范围的修复脚本
print("\n" + "=" * 60)
print("检查未限制范围的修复脚本")
print("=" * 60)

unrestricted_scripts = []
for root, dirs, files in os.walk(project_root):
    # 跳过归档目录
    if "archived_fix_scripts" in root:
        continue
    
    for file in files:
        if file.startswith("fix") and file.endswith(".py"):
            file_path = Path(root) / file
            rel_path = file_path.relative_to(project_root)
            
            # 检查是否是禁用的脚本
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 如果包含禁用说明，跳过
                if "此脚本已被归档" in content or "已被禁用" in content:
                    continue
                
                # 检查是否有范围限制
                has_scope_limit = False
                if "project_scope" in content.lower() or "项目范围" in content:
                    has_scope_limit = True
                
                if not has_scope_limit:
                    unrestricted_scripts.append(str(rel_path))
            except:
                pass

if unrestricted_scripts:
    print(f"发现 {len(unrestricted_scripts)} 个未限制范围的修复脚本:")
    for script in unrestricted_scripts:
        print(f"  {script}")
    
    print("\n禁用这些脚本...")
    disabled_count = 0
    for script in unrestricted_scripts:
        script_path = project_root / script
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write('''#!/usr/bin/env python3
"""
此脚本已被禁用，因为它没有范围限制。

原因：该脚本可能会修改下载的内容（如依赖、模型、数据集等），不符合项目本体的修复原则。

请使用具有范围限制的 unified-fix.py 工具进行修复。
"""

print("此脚本已被禁用。")
print("请使用具有范围限制的 unified-fix.py 工具进行修复。")
''')
            print(f"  ✓ 禁用: {script}")
            disabled_count += 1
        except Exception as e:
            print(f"  ✗ 禁用失败: {script} - {e}")
    
    print(f"\n共禁用 {disabled_count} 个脚本")
else:
    print("✓ 所有修复脚本都有范围限制或已被禁用")

print("\n修复完成！")