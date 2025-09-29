#!/usr/bin/env python3
"""
自动修复项目中 "int" 类型调用表达式的结果未使用 问题
"""

import os
import sys
import re
from pathlib import Path

def find_python_files(root_path):
    """查找所有Python文件"""
    python_files = []
    exclude_dirs = {
        'node_modules', '__pycache__', '.git', 'venv', 'dist', 'build',
        'backup', 'chroma_db', 'context_storage', 'model_cache',
        'test_reports', 'automation_reports', 'docs', 'scripts/venv',
        'apps/backend/venv', 'apps/desktop-app', 'graphic-launcher', 'packages'
    }
    
    for root, dirs, files in os.walk(root_path):
        # 排除不需要检查的目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                # 排除特定文件
                if 'external_connector.py' not in file_path and 'install_gmqtt.py' not in file_path:
                    _ = python_files.append(file_path)
    
    return python_files

def fix_unused_call_results_in_file(file_path):
    """修复文件中的未使用调用结果问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_made = []
        
        # 查找可能的函数调用模式（以换行符或分号结尾的函数调用）
        # 匹配类似: function_name()
        # 但排除已经在赋值语句中的情况
        pattern = r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\)\s*$'
        
        lines = content.split('\n')
        new_lines = []
        modified = False
        
        for i, line in enumerate(lines):
            # 检查是否是独立的函数调用行（不是赋值语句的一部分）
            if (re.match(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(', line) and 
                not re.match(r'^\s*(elif|else|if|while|for|try|except|finally|with|return|yield)', line) and
                not re.match(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=', line) and
                not re.match(r'^\s*\w+\s*\+=', line) and
                not re.match(r'^\s*\w+\s*\*=*', line) and
                not re.match(r'^\s*await\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(', line) and
                not re.match(r'^\s*_[^a-zA-Z0-9_]', line) and  # 不处理已经赋值给下划线的
                not 'print(' in line and  # 不处理print语句
                not 'import ' in line and  # 不处理import语句
                not '#' in line.split('#')[0] and  # 不处理注释行
                line.strip().endswith(')') and  # 确保是以)结尾的函数调用
                not line.strip().startswith('_ =')):  # 不处理已经赋值给下划线的
                
                # 检查这是否是一个可能返回值未被使用的函数调用
                # 我们简单地假设所有不以赋值形式出现的函数调用都需要修复
                # 实际项目中可能需要更复杂的逻辑来判断
                
                # 为了安全起见，我们只处理一些明确的模式
                if (re.match(r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*\)\s*$', line) or
                    re.match(r'^\s*await\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*\)\s*$', line)):
                    
                    # 修复：在函数调用前添加 "_ = "
                    if line.strip().startswith('await '):
                        # 对于异步调用，保留await但添加赋值
                        fixed_line = line.replace('await ', '_ = await ', 1)
                    else:
                        # 对于普通调用，添加赋值
                        fixed_line = line.replace(line.lstrip(), '_ = ' + line.lstrip(), 1)
                    
                    _ = new_lines.append(fixed_line)
                    _ = fixes_made.append(f"第 {i+1} 行: {line.strip()} -> {fixed_line.strip()}")
                    modified = True
                    continue
            
            _ = new_lines.append(line)
        
        # 如果内容有变化，写入文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                _ = f.write('\n'.join(new_lines))
            return True, fixes_made
        else:
            return False, []
            
    except Exception as e:
        _ = print(f"✗ 处理文件 {file_path} 时出错: {e}")
        return False, []

def check_specific_patterns():
    """检查特定的已知问题模式"""
    _ = print("检查特定的已知问题模式...")
    
    # 检查diagnose_components.py中的问题
    diagnose_file = Path("apps/backend/diagnose_components.py")
    if diagnose_file.exists():
        try:
            with open(diagnose_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fixes_made = []
            modified = False
            
            # 检查诊断方法调用
            patterns_to_fix = [
                r'await self\.diagnose_audio_service\(\)',
                r'await self\.diagnose_vision_service\(\)',
                r'await self\.diagnose_vector_store\(\)',
                r'await self\.diagnose_causal_reasoning\(\)',
                r'self\.report_diagnosis\(\)'
            ]
            
            for pattern in patterns_to_fix:
                matches = re.findall(pattern, content)
                if matches:
                    # 替换为赋值形式
                    new_content = re.sub(pattern, '_ = ' + pattern, content)
                    if new_content != content:
                        content = new_content
                        fixes_made.extend([f"修复模式: {pattern}" for _ in matches])
                        modified = True
            
            if modified:
                with open(diagnose_file, 'w', encoding='utf-8') as f:
                    _ = f.write(content)
                _ = print(f"✓ 修复了 {diagnose_file} 中的 {len(fixes_made)} 个问题")
                for fix in fixes_made:
                    _ = print(f"  - {fix}")
                return True
                
        except Exception as e:
            _ = print(f"✗ 检查 {diagnose_file} 时出错: {e}")
    
    return False

def main() -> None:
    """主函数"""
    print("=== 自动修复未使用调用结果问题 ===")
    
    # 检查特定模式
    _ = check_specific_patterns()
    
    # 查找所有Python文件
    project_root: str = Path(__file__).parent
    python_files = find_python_files(project_root)
    
    _ = print(f"发现 {len(python_files)} 个Python文件")
    
    files_fixed = 0
    total_fixes = 0
    
    # 处理每个文件
    for file_path in python_files:
        try:
            fixed, fixes_made = fix_unused_call_results_in_file(file_path)
            if fixed:
                files_fixed += 1
                total_fixes += len(fixes_made)
                _ = print(f"✓ 修复了文件 {file_path}")
                for fix in fixes_made:
                    _ = print(f"  - {fix}")
        except Exception as e:
            _ = print(f"✗ 处理文件 {file_path} 时出错: {e}")
    
    _ = print(f"\n修复统计:")
    _ = print(f"  修复了: {files_fixed} 个文件")
    _ = print(f"  总共修复: {total_fixes} 处问题")
    
    if files_fixed > 0:
        _ = print("\n🎉 修复完成！建议重新运行类型检查以验证修复效果。")
    else:
        _ = print("\n✅ 未发现需要修复的问题。")
    
    return 0

if __name__ == "__main__":
    _ = sys.exit(main())