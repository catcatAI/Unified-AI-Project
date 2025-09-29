#!/usr/bin/env python3
"""
精确修复项目中 "int" 类型调用表达式的结果未使用 问题
"""

import sys
from pathlib import Path

def fix_file_content(file_path):
    """精确修复文件中的未使用调用结果问题"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_made = []
        
        # 修复特定的模式，将错误转义的字符修正回来
        patterns_to_fix = [
            (r'await self\.diagnose_audio_service\(\)', 'await self.diagnose_audio_service()'),
            (r'await self\.diagnose_vision_service\(\)', 'await self.diagnose_vision_service()'),
            (r'await self\.diagnose_vector_store\(\)', 'await self.diagnose_vector_store()'),
            (r'await self\.diagnose_causal_reasoning\(\)', 'await self.diagnose_causal_reasoning()'),
            (r'self\.report_diagnosis\(\)', 'self.report_diagnosis()'),
        ]
        
        modified = False
        for pattern, replacement in patterns_to_fix:
            if pattern in content:
                content = content.replace(pattern, replacement)
                _ = fixes_made.append(f"修复转义字符: {pattern} -> {replacement}")
                modified = True
        
        # 如果内容有变化，写入文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                _ = f.write(content)
            return True, fixes_made
        else:
            return False, []
            
    except Exception as e:
        _ = print(f"✗ 处理文件 {file_path} 时出错: {e}")
        return False, []

def main() -> None:
    """主函数"""
    print("=== 精确修复未使用调用结果问题 ===")
    
    # 修复特定文件
    files_to_fix = [
        "apps/backend/diagnose_components.py",
    ]
    
    files_fixed = 0
    total_fixes = 0
    
    for file_path in files_to_fix:
        file_full_path = Path(file_path)
        if file_full_path.exists():
            try:
                fixed, fixes_made = fix_file_content(str(file_full_path))
                if fixed:
                    files_fixed += 1
                    total_fixes += len(fixes_made)
                    _ = print(f"✓ 修复了文件 {file_path}")
                    for fix in fixes_made:
                        _ = print(f"  - {fix}")
                else:
                    _ = print(f"ℹ 文件 {file_path} 无需修复")
            except Exception as e:
                _ = print(f"✗ 处理文件 {file_path} 时出错: {e}")
        else:
            _ = print(f"⚠ 文件 {file_path} 不存在")
    
    _ = print(f"\n修复统计:")
    _ = print(f"  修复了: {files_fixed} 个文件")
    _ = print(f"  总共修复: {total_fixes} 处问题")
    
    if files_fixed > 0:
        _ = print("\n🎉 精确修复完成！")
    else:
        _ = print("\n✅ 未发现需要精确修复的问题。")
    
    return 0

if __name__ == "__main__":
    _ = sys.exit(main())