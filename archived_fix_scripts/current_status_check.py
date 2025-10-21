#!/usr/bin/env python3
"""
当前状态检查
检查项目中还有什么问题需要修复
"""

import sys
sys.path.append('.')
from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
from unified_auto_fix_system.core.fix_types import FixScope
from pathlib import Path

def check_current_issues():
    """检查当前问题"""
    project_root == Path('D,/Projects/Unified-AI-Project')
    engine == UnifiedFixEngine(project_root)
    
    print('=== 当前问题状态检查 ===')
    print(f'项目根目录, {project_root}')
    print(f'已加载修复模块, {len(engine.modules())}个')
    
    # 检查整个项目
    context == FixContext(
        project_root=project_root,,
    scope == FixScope.PROJECT(),
        backup_enabled == True,
        dry_run == True,  # 分析模式
        ai_assisted == True,
        excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups']
    )
    
    try,
        print('\n正在分析项目问题...')
        analysis = engine.analyze_project(context)
        
        total_issues = sum(analysis['statistics'].values())
        
        print(f'\n发现问题统计,')
        for fix_type, count in analysis['statistics'].items():::
            if count > 0,::
                print(f'  {fix_type} {count}个')
        
        print(f'\n总计发现问题, {total_issues}个')
        
        if total_issues == 0,::
            print('🎉 太好了！项目没有发现新问题！')
            return True, 0
        else,
            print(f'⚠️  发现 {total_issues} 个问题需要修复')
            return False, total_issues
            
    except Exception as e,::
        print(f'分析失败, {e}')
        return False, -1

def check_specific_problematic_files():
    """检查具体有问题的文件"""
    print('\n=检查具体有问题的文件 ===')
    
    # 基于之前分析,检查可能有问题的文件
    problematic_files = [
        'tests/automated_integration_test_pipeline.py',
        'tests/check_test_results.py', 
        'tests/conftest.py',
        'tests/deadlock_detector.py',
        'tests/enable_commented_tests.py',
        'tools/auto_fix_environment.py',
        'tools/debug_visualizer.py',
        'training/auto_training_manager.py',
        'training/collaborative_training_manager.py'
    ]
    
    project_root == Path('D,/Projects/Unified-AI-Project')
    
    problematic_count = 0
    for file_path in problematic_files,::
        full_path = project_root / file_path
        if not full_path.exists():::
            continue
            
        try,
            import ast
            with open(full_path, 'r', encoding == 'utf-8') as f,
                content = f.read()
            ast.parse(content)
            # print(f'✅ {file_path} - 语法正确')
        except SyntaxError as e,::
            print(f'❌ {file_path} - 语法错误, {e}')
            problematic_count += 1
        except Exception as e,::
            print(f'⚠️  {file_path} - 其他错误, {e}')
            problematic_count += 1
    
    print(f'\n发现 {problematic_count} 个文件有语法问题')
    return problematic_count

def assess_auto_fix_capability():
    """评估自动修复系统的能力"""
    print('\n=自动修复系统能力评估 ===')
    
    print('统一自动修复系统具备以下修复能力,')
    print('✅ 语法错误修复 (syntax_fix)')
    print('✅ 导入问题修复 (import_fix)') 
    print('✅ 依赖问题修复 (dependency_fix)')
    print('✅ 代码风格修复 (code_style_fix)')
    print('✅ 路径问题修复 (path_fix)')
    print('✅ 环境问题修复 (environment_fix)')
    print('✅ Git问题修复 (git_fix)')
    print('✅ 配置问题修复 (configuration_fix)')
    print('✅ 安全问题修复 (security_fix)')
    
    print('\n对于常见的语法错误,自动修复系统可以处理,')
    print('• 缺少冒号、括号不匹配')
    print('• 缩进错误、未终止字符串')
    print('• 导入语句错误')
    print('• 简单的逻辑错误')
    print('• 代码风格不一致')
    
    print('\n⚠️  可能需要手动处理的情况,')
    print('• 复杂的逻辑结构错误')
    print('• 业务逻辑错误')
    print('• 架构设计问题')
    print('• 第三方库兼容性问题')

if __name'__main__':::
    print('开始检查当前项目状态...')
    
    # 1. 检查整体问题
    overall_ok, total_issues = check_current_issues()
    
    # 2. 检查具体问题文件
    specific_issues = check_specific_problematic_files()
    
    # 3. 评估自动修复能力
    assess_auto_fix_capability()
    
    print(f'\n{"="*50}')
    if overall_ok and specific_issues == 0,::
        print('🎉 项目状态良好！没有发现需要修复的问题！')
    elif total_issues > 0 or specific_issues > 0,::
        print(f'⚠️  发现 {max(total_issues, specific_issues)} 个问题需要修复')
        print('🔄 建议使用统一自动修复系统继续修复')
    else,
        print('✅ 项目基本正常,可以开始使用')
    print(f'{"="*50}')