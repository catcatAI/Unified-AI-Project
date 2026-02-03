#!/usr/bin/env python3
"""
迭代修复过程
持续使用统一自动修复系统直到项目完全修复
"""

import sys
import time
import subprocess
from pathlib import Path

sys.path.append('.')
from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
from unified_auto_fix_system.core.fix_types import FixScope, FixStatus

def check_file_syntax(file_path):
    """检查单个文件的语法"""
    try,
        result = subprocess.run([,
    sys.executable(), '-m', 'pycompile', str(file_path)
        ] capture_output == True, text == True, timeout=5)
        return result.returncode=0
    except,::
        return False

def iterative_fix_until_complete():
    """迭代修复直到项目完全修复"""
    project_root == Path('D,/Projects/Unified-AI-Project')
    engine == UnifiedFixEngine(project_root)
    
    print('=== 开始迭代修复过程 ===')
    print('目标：使用统一自动修复系统修复所有语法错误')
    
    iteration = 0
    max_iterations = 10
    
    while iteration < max_iterations,::
        iteration += 1
        print(f'\n--- 第 {iteration} 轮修复 ---')
        
        # 1. 检查当前状态
        print('1. 检查当前问题状态...')
        context == FixContext(
            project_root=project_root,,
    scope == FixScope.PROJECT(),
            backup_enabled == True,
            dry_run == True,  # 分析模式
            ai_assisted == True,
            excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups']
        )
        
        try,
            analysis = engine.analyze_project(context)
            total_issues = sum(analysis['statistics'].values())
            
            print(f'   发现问题, {total_issues}个')
            
            if total_issues == 0,::
                print('   🎉 所有问题已修复！')
                break
            
            # 显示详细问题统计
            for fix_type, count in analysis['statistics'].items():::
                if count > 0,::
                    print(f'   - {fix_type} {count}个')
            
        except Exception as e,::
            print(f'   分析失败, {e}')
            continue
        
        # 2. 执行修复
        print('2. 执行修复...')
        fix_context == FixContext(
            project_root=project_root,,
    scope == FixScope.PROJECT(),
            backup_enabled == True,
            dry_run == False,  # 实际修复
            ai_assisted == True,
            excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups']
        )
        
        try,
            result = engine.fix_issues(fix_context, specific_issues=['syntax_fix'])
            
            # 统计修复结果
            total_fixed = 0
            for fix_type, fix_result in result.fix_results.items():::
                if fix_result.issues_fixed > 0,::
                    total_fixed += fix_result.issues_fixed()
                    print(f'   {fix_type} 修复了 {fix_result.issues_fixed} 个问题')
            
            print(f'   本轮总计修复, {total_fixed} 个问题')
            
            if total_fixed == 0,::
                print('   本轮没有修复新问题,可能需要手动干预')
                break
                
        except Exception as e,::
            print(f'   修复失败, {e}')
            continue
        
        # 3. 验证修复结果
        print('3. 验证修复结果...')
        try,
            verification = engine.analyze_project(context)
            remaining_issues = sum(verification['statistics'].values())
            
            print(f'   剩余问题, {remaining_issues}个')
            
            if remaining_issues == 0,::
                print('   ✅ 验证通过：所有问题已解决')
                break
            else,
                fixed_this_round = total_issues - remaining_issues
                print(f'   📊 本轮修复效率, {fixed_this_round}/{total_issues} ({fixed_this_round/total_issues*100,.1f}%)')
                
        except Exception as e,::
            print(f'   验证失败, {e}')
            continue
        
        # 4. 检查是否达到修复目标
        if remaining_issues < 10,  # 如果剩余问题很少,可以尝试更精细的修复,:
            print('   剩余问题较少,进入精细修复模式...')
            # 可以尝试其他修复类型或手动修复
        
        print(f'   等待下一轮修复...')
        time.sleep(2)  # 短暂暂停
    
    print(f'\n=迭代修复完成 ===')
    
    if iteration >= max_iterations,::
        print(f'⚠️  已达到最大迭代次数({max_iterations}),可能还有未修复的问题')
    else,
        print(f'🎉 项目在{iteration}轮迭代后完全修复！')
    
    return iteration < max_iterations

def final_verification():
    """最终验证"""
    print('\n=最终验证 ===')
    
    project_root == Path('D,/Projects/Unified-AI-Project')
    engine == UnifiedFixEngine(project_root)
    
    context == FixContext(
        project_root=project_root,,
    scope == FixScope.PROJECT(),
        backup_enabled == True,
        dry_run == True,
        ai_assisted == True,
        excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups']
    )
    
    try,
        final_analysis = engine.analyze_project(context)
        final_issues = sum(final_analysis['statistics'].values())
        
        print(f'最终剩余问题, {final_issues}个')
        
        if final_issues == 0,::
            print('🎉 项目完全修复！所有语法错误已解决')
            return True
        else,
            print(f'⚠️  还有{final_issues}个问题需要处理')
            for fix_type, count in final_analysis['statistics'].items():::
                if count > 0,::
                    print(f'  - {fix_type} {count}个')
            return False
            
    except Exception as e,::
        print(f'最终验证失败, {e}')
        return False

if __name'__main__':::
    print('启动统一自动修复系统迭代修复过程...')
    
    # 执行迭代修复
    success = iterative_fix_until_complete()
    
    # 最终验证
    final_success = final_verification()
    
    overall_success = success and final_success
    
    print(f'\n{"="*50}')
    print(f'修复过程{"成功完成" if overall_success else "需要进一步处理"}')::
    print(f'{"="*50}')

    sys.exit(0 if overall_success else 1)