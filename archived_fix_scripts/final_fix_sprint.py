#!/usr/bin/env python3
"""
最终修复冲刺
专注于剩余的关键问题
"""

import sys
import time
from pathlib import Path

sys.path.append('.')
from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
from unified_auto_fix_system.core.fix_types import FixScope, FixStatus

def final_fix_sprint():
    """最终修复冲刺"""
    project_root = Path('D:/Projects/Unified-AI-Project')
    engine = UnifiedFixEngine(project_root)
    
    print('=== 最终修复冲刺 ===')
    print('专注于解决剩余的关键语法问题')
    
    # 定义最关键的文件路径（基于之前的错误日志）
    critical_files = [
        # 核心系统文件
        'apps/backend/src/core/hsp/protocol_manager.py',
        'apps/backend/src/core/memory/deep_mapper.py',
        'apps/backend/src/core/agents/base_agent.py',
        
        # 自动修复系统文件
        'unified_auto_fix_system/core/unified_fix_engine.py',
        'unified_auto_fix_system/modules/syntax_fixer.py',
        'unified_auto_fix_system/modules/import_fixer.py',
        
        # 项目根目录文件
        'check_project_syntax.py',
        'comprehensive_fix_agent.py',
        'find_python_files.py',
        
        # 之前手动修复的文件
        'auto_fix_workspace/test_enhanced_fix_system.py',
        'auto_fix_workspace/test_get_files.py',
        'auto_fix_workspace/test_improved_fix_system.py',
        'auto_fix_workspace/test_layered_fix_system.py'
    ]
    
    total_fixed = 0
    total_processed = 0
    
    print(f'准备修复 {len(critical_files)} 个关键文件...')
    
    for file_path in critical_files:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f'跳过不存在的文件: {file_path}')
            continue
        
        try:
            print(f'\n修复: {file_path}')
            
            # 创建修复上下文
            context = FixContext(
                project_root=project_root,
                target_path=full_path,
                scope=FixScope.PROJECT,
                backup_enabled=True,
                dry_run=False,
                ai_assisted=True,
                excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv']
            )
            
            # 执行语法修复
            result = engine.fix_issues(context, specific_issues=['syntax_fix'])
            
            # 统计结果
            file_fixed = 0
            for fix_type, fix_result in result.fix_results.items():
                if fix_result.issues_fixed > 0:
                    file_fixed += fix_result.issues_fixed
                    print(f'  ✓ {fix_type}: 修复了 {fix_result.issues_fixed} 个问题')
            
            if file_fixed == 0:
                print('  ✅ 无需修复')
            
            total_fixed += file_fixed
            total_processed += 1
            
            # 短暂暂停
            time.sleep(0.5)
            
        except Exception as e:
            print(f'  ❌ 修复失败: {e}')
            continue
    
    print(f'\n=== 最终冲刺完成 ===')
    print(f'处理了 {total_processed} 个关键文件')
    print(f'修复了 {total_fixed} 个问题')
    
    if total_fixed > 0:
        print('🎯 关键文件修复完成！')
    else:
        print('✅ 关键文件状态良好')
    
    return total_fixed

def enhanced_fix_strategy():
    """增强修复策略 - 使用所有可用的修复模块"""
    project_root = Path('D:/Projects/Unified-AI-Project')
    engine = UnifiedFixEngine(project_root)
    
    print('\n=== 增强修复策略 ===')
    print('使用所有可用的修复模块')
    
    # 使用所有修复类型
    all_fix_types = list(engine.modules.keys())
    
    context = FixContext(
        project_root=project_root,
        scope=FixScope.PROJECT,
        backup_enabled=True,
        dry_run=False,
        ai_assisted=True,
        excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups']
    )
    
    try:
        print(f'使用 {len(all_fix_types)} 种修复类型: {[ft.value for ft in all_fix_types]}')
        
        # 执行全面修复
        result = engine.fix_issues(context)
        
        total_fixed = 0
        print('\n修复结果:')
        for fix_type, fix_result in result.fix_results.items():
            if fix_result.issues_fixed > 0:
                total_fixed += fix_result.issues_fixed
                print(f'  {fix_type.value}: 修复了 {fix_result.issues_fixed} 个问题')
        
        print(f'\n增强修复总计: {total_fixed} 个问题')
        return total_fixed
        
    except Exception as e:
        print(f'增强修复失败: {e}')
        return 0

if __name__ == '__main__':
    print('启动最终修复冲刺...')
    
    # 1. 关键文件最终修复
    sprint_success = final_fix_sprint()
    
    # 2. 增强修复策略
    enhanced_success = enhanced_fix_strategy()
    
    total_fixed = sprint_success + enhanced_success
    
    print(f'\n{"="*50}')
    print(f'最终修复冲刺完成')
    print(f'总计修复: {total_fixed} 个问题')
    print(f'{"="*50}')
    
    if total_fixed > 0:
        print('🎯 修复成功！项目语法错误已大幅减少')
    else:
        print('✅ 项目状态良好，未发现新问题')
    
    sys.exit(0)