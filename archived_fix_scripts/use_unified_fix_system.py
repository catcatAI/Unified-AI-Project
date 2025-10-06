#!/usr/bin/env python3
"""
使用统一自动修复系统修复项目
专注于核心目录和文件
"""

import sys
import time
import traceback
from pathlib import Path

# 添加项目路径
sys.path.append('.')
from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
from unified_auto_fix_system.core.fix_types import FixScope, FixStatus

def fix_core_directories():
    """修复核心目录"""
    project_root = Path('D:/Projects/Unified-AI-Project')
    
    print('=== 使用统一自动修复系统 ===')
    print(f'项目根目录: {project_root}')
    
    # 初始化修复引擎
    engine = UnifiedFixEngine(project_root)
    print(f'已加载 {len(engine.modules)} 个修复模块')
    
    # 定义核心目录，按优先级排序
    core_directories = [
        'apps/backend/src/core',           # 核心系统
        'apps/backend/src/ai',             # AI模块
        'unified_auto_fix_system',         # 自动修复系统本身
        'auto_fix_workspace',              # 自动修复工作区
        'tests',                           # 测试文件
        'tools',                           # 工具脚本
        'training',                        # 训练系统
    ]
    
    total_fixed = 0
    total_found = 0
    
    for dir_name in core_directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            print(f'跳过不存在的目录: {dir_name}')
            continue
            
        print(f'\n=== 修复目录: {dir_name} ===')
        
        try:
            # 创建针对特定目录的修复上下文
            context = FixContext(
                project_root=project_root,
                target_path=dir_path,
                scope=FixScope.PROJECT,
                backup_enabled=True,
                dry_run=False,
                ai_assisted=True,
                excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups']
            )
            
            # 执行修复 - 只修复语法问题
            print(f'开始修复 {dir_name} 中的语法问题...')
            result = engine.fix_issues(context, specific_issues=['syntax_fix'])
            
            # 统计结果
            dir_fixed = 0
            dir_found = 0
            
            for fix_type, fix_result in result.fix_results.items():
                if fix_result.issues_found > 0:
                    dir_found += fix_result.issues_found
                    dir_fixed += fix_result.issues_fixed
                    print(f'  {fix_type.value}: 发现{fix_result.issues_found}个，修复{fix_result.issues_fixed}个')
            
            total_fixed += dir_fixed
            total_found += dir_found
            
            print(f'目录 {dir_name} 修复完成: 发现{dir_found}个，修复{dir_fixed}个')
            
            # 如果修复成功，暂停一下让系统稳定
            if dir_fixed > 0:
                time.sleep(1)
                
        except Exception as e:
            print(f'修复目录 {dir_name} 失败: {e}')
            traceback.print_exc()
            continue
    
    print(f'\n=== 修复总结 ===')
    print(f'总发现问题: {total_found}个')
    print(f'总修复问题: {total_fixed}个')
    print(f'修复成功率: {(total_fixed/total_found*100):.1f}%' if total_found > 0 else 'N/A')
    
    return total_fixed > 0

def fix_specific_files():
    """修复之前手动修复过的特定文件，验证自动修复系统效果"""
    project_root = Path('D:/Projects/Unified-AI-Project')
    engine = UnifiedFixEngine(project_root)
    
    # 之前手动修复的文件列表
    previously_fixed_files = [
        'check_project_syntax.py',
        'comprehensive_fix_agent.py', 
        'find_python_files.py',
        'auto_fix_workspace/test_enhanced_fix_system.py',
        'auto_fix_workspace/test_get_files.py',
        'auto_fix_workspace/test_improved_fix_system.py',
        'auto_fix_workspace/test_layered_fix_system.py'
    ]
    
    print('\n=== 验证之前修复的文件 ===')
    
    total_fixed = 0
    for file_path in previously_fixed_files:
        full_path = project_root / file_path
        if not full_path.exists():
            continue
            
        try:
            context = FixContext(
                project_root=project_root,
                target_path=full_path,
                scope=FixScope.PROJECT,
                backup_enabled=True,
                dry_run=False,
                ai_assisted=True
            )
            
            result = engine.fix_issues(context, specific_issues=['syntax_fix'])
            
            for fix_type, fix_result in result.fix_results.items():
                if fix_result.issues_fixed > 0:
                    print(f'  {file_path}: 额外修复了{fix_result.issues_fixed}个问题')
                    total_fixed += fix_result.issues_fixed
                    
        except Exception as e:
            print(f'  {file_path}: 修复失败 - {e}')
    
    if total_fixed > 0:
        print(f'额外修复了 {total_fixed} 个问题')
    else:
        print('之前修复的文件状态良好，无需额外修复')
    
    return total_fixed

if __name__ == '__main__':
    print('开始统一自动修复系统执行...')
    
    # 1. 修复核心目录
    core_success = fix_core_directories()
    
    # 2. 验证之前修复的文件
    verification_success = fix_specific_files()
    
    overall_success = core_success or verification_success
    
    print(f'\n统一自动修复系统执行{"完成" if overall_success else "完成（无新问题）"}')
    sys.exit(0 if overall_success else 0)  # 即使没修复新问题也算成功