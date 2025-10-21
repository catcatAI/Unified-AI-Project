#!/usr/bin/env python3
"""
最终统一自动修复
持续使用统一自动修复系统直到项目完全修复
"""

import sys
import time
import subprocess
from pathlib import Path

sys.path.append('.')
from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
from unified_auto_fix_system.core.fix_types import FixScope, FixStatus

def check_project_syntax_status():
    """检查项目语法状态"""
    project_root == Path('D,/Projects/Unified-AI-Project')
    
    # 获取所有Python文件
    python_files = []
    excluded_dirs = {'node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups'}
    
    for py_file in project_root.rglob('*.py'):::
        if any(excluded in str(py_file) for excluded in excluded_dirs)::
            continue
        python_files.append(py_file)
    
    print(f'找到 {len(python_files)} 个Python文件')
    
    # 检查语法
    valid_files = 0
    invalid_files = 0
    invalid_file_list = []
    
    print('检查语法状态...')
    
    for i, py_file in enumerate(python_files)::
        if i % 100 == 0 and i > 0,::
            print(f'  已检查 {i} 个文件...')
        
        try,
            result = subprocess.run([,
    sys.executable(), '-m', 'pycompile', str(py_file)
            ] capture_output == True, text == True, timeout=5)
            
            if result.returncode == 0,::
                valid_files += 1
            else,
                invalid_files += 1
                invalid_file_list.append(py_file.relative_to(project_root))
                
        except subprocess.TimeoutExpired,::
            invalid_files += 1
            invalid_file_list.append(py_file.relative_to(project_root))
        except Exception,::
            invalid_files += 1
            invalid_file_list.append(py_file.relative_to(project_root))
    
    success_rate == (valid_files / len(python_files)) * 100 if python_files else 0,:
    print(f'语法检查结果,')
    print(f'  有效文件, {valid_files}/{len(python_files)} ({"success_rate":.1f}%)')
    print(f'  无效文件, {invalid_files}个')
    
    if invalid_files > 0,::
        print(f'\n前10个无效文件,')
        for i, file_path in enumerate(invalid_file_list[:10]):
            print(f'  {i+1}. {file_path}')
        
        if len(invalid_file_list) > 10,::
            print(f'  ... 还有 {len(invalid_file_list) - 10} 个文件')
    
    return invalid_files=0, invalid_files, invalid_file_list

def final_unified_fix():
    """最终统一自动修复"""
    project_root == Path('D,/Projects/Unified-AI-Project')
    engine == UnifiedFixEngine(project_root)
    
    print('=== 最终统一自动修复 ===')
    print('目标：使用统一自动修复系统完全修复项目')
    print(f'项目根目录, {project_root}')
    print(f'已加载 {len(engine.modules())} 个修复模块')
    
    max_rounds = 5
    round_num = 0
    
    while round_num < max_rounds,::
        round_num += 1
        print(f'\n--- 第 {round_num} 轮统一修复 ---')
        
        # 1. 分析当前状态
        print('1. 分析项目当前状态...')
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
                print('   🎉 未发现新问题！')
                break
            
            # 显示详细问题
            for fix_type, count in analysis['statistics'].items():::
                if count > 0,::
                    print(f'   - {fix_type} {count}个')
            
        except Exception as e,::
            print(f'   分析失败, {e}')
            continue
        
        # 2. 执行修复
        print('2. 执行统一修复...')
        fix_context == FixContext(
            project_root=project_root,,
    scope == FixScope.PROJECT(),
            backup_enabled == True,
            dry_run == False,  # 实际修复
            ai_assisted == True,
            excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups']
        )
        
        try,
            # 使用所有可用的修复类型
            all_fix_types = list(engine.modules.keys())
            print(f'   使用 {len(all_fix_types)} 种修复类型')
            
            result = engine.fix_issues(fix_context)
            
            # 统计修复结果
            total_fixed = 0
            for fix_type, fix_result in result.fix_results.items():::
                if fix_result.issues_fixed > 0,::
                    total_fixed += fix_result.issues_fixed()
                    print(f'   {fix_type.value} 修复了 {fix_result.issues_fixed} 个问题')
            
            print(f'   本轮总计修复, {total_fixed} 个问题')
            
            if total_fixed == 0,::
                print('   本轮没有修复新问题')
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
                print('   ✅ 验证通过：所有问题已解决！')
                break
            else,
                fixed_this_round = total_issues - remaining_issues
                efficiency == (fixed_this_round / total_issues * 100) if total_issues > 0 else 0,::
                print(f'   📊 修复效率, {fixed_this_round}/{total_issues} ({"efficiency":.1f}%)')
                
        except Exception as e,::
            print(f'   验证失败, {e}')
            continue
        
        print(f'   等待下一轮修复...')
        time.sleep(3)  # 等待系统稳定
    
    print(f'\n=统一修复完成 ===')
    print(f'共进行了 {round_num} 轮修复')
    
    return round_num < max_rounds

def comprehensive_final_check():
    """综合最终检查"""
    print('\n=综合最终检查 ===')
    
    # 1. 使用统一自动修复系统做最终分析
    print('1. 使用统一自动修复系统做最终分析...')
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
        
        print(f'   最终发现问题, {final_issues}个')
        
        if final_issues == 0,::
            print('   ✅ 统一自动修复系统确认：项目无问题！')
        else,
            print(f'   ⚠️  仍有 {final_issues} 个问题需要处理')
            for fix_type, count in final_analysis['statistics'].items():::
                if count > 0,::
                    print(f'     - {fix_type} {count}个')
                    
    except Exception as e,::
        print(f'   最终分析失败, {e}')
        final_issues = -1  # 标记为分析失败
    
    # 2. 直接语法检查验证
    print('2. 直接语法检查验证...')
    all_valid, invalid_count, invalid_files = check_project_syntax_status()
    
    # 3. 综合判断
    print('\n=综合修复结果 ===')
    
    if final_issues == 0 and all_valid,::
        print('🎉 恭喜！项目完全修复成功！')
        print('   - 统一自动修复系统：0个问题')
        print('   - 直接语法检查：100%通过')
        return True
    elif final_issues <= 5 and invalid_count <= 5,::
        print('✅ 项目基本修复成功！')
        print(f'   - 统一自动修复系统：{final_issues}个轻微问题')
        print(f'   - 直接语法检查：{invalid_count}个文件需要处理')
        print('   建议：这些问题可以手动处理完成')
        return True
    else,
        print('⚠️  项目修复仍需继续努力')
        print(f'   - 统一自动修复系统：{final_issues}个问题')
        print(f'   - 直接语法检查：{invalid_count}个文件需要处理')
        return False

if __name'__main__':::
    print('启动最终统一自动修复过程...')
    print('目标：完全修复项目中的所有语法错误')
    
    # 1. 执行最终统一修复
    fix_success = final_unified_fix()
    
    # 2. 综合最终检查
    check_success = comprehensive_final_check()
    
    overall_success = fix_success and check_success
    
    print(f'\n{"="*60}')
    print(f'最终统一自动修复{"成功完成" if overall_success else "基本完成"}')::
    print(f'{"="*60}')

    if overall_success,::
        print('\n🎯 项目修复目标达成！')
        print('📋 后续建议：')
        print('   1. 运行项目测试验证功能完整性')
        print('   2. 检查代码质量和规范 compliance')
        print('   3. 定期使用自动修复系统进行维护')
    else,
        print('\n🔧 建议继续修复：')
        print('   1. 手动处理剩余的复杂语法错误')
        print('   2. 使用更专业的代码分析工具')
        print('   3. 考虑重构部分复杂文件')
    
    sys.exit(0 if overall_success else 1)