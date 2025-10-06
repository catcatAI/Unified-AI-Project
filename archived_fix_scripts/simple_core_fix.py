#!/usr/bin/env python3
"""
简单核心文件修复脚本
"""

from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
from pathlib import Path

def fix_core_files():
    """修复核心文件"""
    # 初始化修复引擎
    project_root = Path('D:/Projects/Unified-AI-Project')
    engine = UnifiedFixEngine(project_root)
    
    # 定义要修复的核心文件
    core_files = [
        'apps/backend/src/core/hsp/__init__.py',
        'apps/backend/src/core/memory/__init__.py',
        'apps/backend/src/core/agents/__init__.py'
    ]
    
    total_fixed = 0
    total_found = 0
    
    for file_path in core_files:
        try:
            print(f'开始修复 {file_path}...')
            
            # 创建修复上下文
            context = FixContext(
                target_path=project_root / file_path,
                dry_run=False,
                backup_enabled=True,
                ai_assisted=True
            )
            
            # 执行修复
            result = engine.fix_issues(context, fix_types=['syntax_fix'])
            
            print(f'  修复结果: {result.status}')
            print(f'  发现问题: {result.issues_found}, 修复问题: {result.issues_fixed}')
            
            total_found += result.issues_found
            total_fixed += result.issues_fixed
            
            if result.error_message:
                print(f'  错误: {result.error_message}')
                
        except Exception as e:
            print(f'修复 {file_path} 失败: {e}')
    
    print(f'\n总计 - 发现问题: {total_found}, 修复问题: {total_fixed}')
    return total_fixed > 0

if __name__ == '__main__':
    success = fix_core_files()
    print(f'修复成功: {success}')