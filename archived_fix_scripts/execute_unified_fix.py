#!/usr/bin/env python3
"""
执行统一自动修复系统
"""

import sys
import time
sys.path.append('.')
from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
from unified_auto_fix_system.core.fix_types import FixScope, FixStatus
from pathlib import Path

def execute_unified_fix():
    """执行统一自动修复"""
    project_root = Path('D:/Projects/Unified-AI-Project')
    
    print('=== 统一自动修复系统执行 ===')
    print(f'项目根目录: {project_root}')
    
    # 初始化修复引擎
    engine = UnifiedFixEngine(project_root)
    print(f'已加载 {len(engine.modules)} 个修复模块')
    
    # 创建修复上下文 - 只针对Python文件
    context = FixContext(
        project_root=project_root,
        scope=FixScope.PROJECT,
        backup_enabled=True,
        dry_run=False,  # 实际修复
        ai_assisted=True,
        excluded_paths=['node_modules', '__pycache__', '.git', 'venv', '.venv', 'backup', 'unified_fix_backups', 'dist', 'build']
    )
    
    print('\n=== 开始执行修复 ===')
    start_time = time.time()
    
    try:
        # 执行修复 - 只针对语法问题
        print('正在修复语法问题...')
        result = engine.fix_issues(context, specific_issues=['syntax_fix'])
        
        duration = time.time() - start_time
        
        print(f'\n=== 修复完成 ===')
        print(f'修复状态: {result.status}')
        print(f'总发现问题: {result.statistics.get("total_issues_found", 0)}')
        print(f'总修复问题: {result.statistics.get("total_issues_fixed", 0)}')
        print(f'成功修复: {result.statistics.get("successful_fixes", 0)}')
        print(f'失败修复: {result.statistics.get("failed_fixes", 0)}')
        print(f'耗时: {duration:.2f}秒')
        
        if result.errors:
            print(f'错误信息: {len(result.errors)}个错误')
            for error in result.errors[:5]:
                print(f'  - {error}')
        
        if result.backup_path:
            print(f'备份路径: {result.backup_path}')
        
        # 显示各模块修复结果
        print(f'\n=== 各模块修复详情 ===')
        for fix_type, fix_result in result.fix_results.items():
            if fix_result.issues_found > 0:
                print(f'{fix_type.value}: 发现{fix_result.issues_found}个，修复{fix_result.issues_fixed}个，状态:{fix_result.status.value}')
        
        return result.status == FixStatus.SUCCESS or result.status == FixStatus.PARTIAL_SUCCESS
        
    except Exception as e:
        print(f'修复过程失败: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = execute_unified_fix()
    print(f'\n修复执行{"成功" if success else "失败"}')
    sys.exit(0 if success else 1)