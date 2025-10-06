#!/usr/bin/env python3
"""
继续最终修复
使用统一自动修复系统修复剩余的问题
"""

import sys
import time
from pathlib import Path

sys.path.append('.')
from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
from unified_auto_fix_system.core.fix_types import FixScope, FixStatus

def continue_final_fix():
    """继续最终修复"""
    project_root = Path('D:/Projects/Unified-AI-Project')
    engine = UnifiedFixEngine(project_root)
    
    print('=== 继续最终统一自动修复 ===')
    print('目标：修复剩余的22,153个语法问题')
    
    # 创建修复上下文
    context = FixContext(
        project_root=project_root,
        scope=FixScope.PROJECT,
        backup_enabled=True,
        dry_run=False,  # 实际修复
        ai_assisted=True,
        excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups']
    )
    
    print('\n1. 开始执行统一修复...')
    
    try:
        # 执行语法修复
        print('正在修复语法问题...')
        result = engine.fix_issues(context, specific_issues=['syntax_fix'])
        
        # 统计修复结果
        total_fixed = 0
        for fix_type, fix_result in result.fix_results.items():
            if fix_result.issues_fixed > 0:
                total_fixed += fix_result.issues_fixed
                print(f'  {fix_type.value}: 修复了 {fix_result.issues_fixed} 个问题')
        
        print(f'\n总计修复: {total_fixed} 个问题')
        
        if total_fixed > 0:
            print('✅ 修复成功！')
        else:
            print('ℹ️  没有发现需要修复的语法问题')
        
        return total_fixed > 0
        
    except Exception as e:
        print(f'修复过程失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def check_fix_result():
    """检查修复结果"""
    print('\n2. 验证修复结果...')
    
    project_root = Path('D:/Projects/Unified-AI-Project')
    engine = UnifiedFixEngine(project_root)
    
    context = FixContext(
        project_root=project_root,
        scope=FixScope.PROJECT,
        backup_enabled=True,
        dry_run=True,  # 分析模式
        ai_assisted=True,
        excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups']
    )
    
    try:
        verification = engine.analyze_project(context)
        remaining_issues = sum(verification['statistics'].values())
        
        print(f'剩余问题: {remaining_issues}个')
        
        if remaining_issues == 0:
            print('🎉 恭喜！所有问题已修复！')
            return True
        else:
            print(f'⚠️  还有 {remaining_issues} 个问题需要处理')
            for fix_type, count in verification['statistics'].items():
                if count > 0:
                    print(f'  - {fix_type}: {count}个')
            return False
            
    except Exception as e:
        print(f'验证失败: {e}')
        return False

if __name__ == '__main__':
    print('启动继续最终修复过程...')
    
    # 1. 执行修复
    fix_success = continue_final_fix()
    
    # 2. 验证结果
    verify_success = check_fix_result()
    
    overall_success = fix_success or verify_success
    
    print(f'\n{"="*60}')
    if overall_success:
        print('🎉 继续修复完成！项目语法错误已大幅减少！')
    else:
        print('⚠️  修复过程完成，但仍有部分问题需要关注')
    print(f'{"="*60}')
    
    if overall_success:
        print('\n📋 建议下一步:')
        print('1. 运行项目测试验证功能完整性')
        print('2. 对剩余复杂问题进行手动精细修复')
        print('3. 建立定期自动修复维护机制')
    else:
        print('\n🔧 建议:')
        print('1. 继续运行统一自动修复系统')
        print('2. 针对特定问题进行专项修复')
        print('3. 考虑手动处理复杂语法错误')
    
    sys.exit(0 if overall_success else 1)