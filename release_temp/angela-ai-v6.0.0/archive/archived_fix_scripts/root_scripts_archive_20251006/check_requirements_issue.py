import sys
sys.path.append('.')

from pathlib import Path
from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
from unified_auto_fix_system.core.fix_types import FixContext, FixScope, FixPriority

print('=== 检查requirements.txt具体问题 ===')

try:
    engine = UnifiedFixEngine('.')
    
    context = FixContext(
        project_root=Path('.'),
        scope=FixScope.SPECIFIC_FILE,
        target_path=Path('requirements.txt'),
        priority=FixPriority.NORMAL,
        backup_enabled=True,
        dry_run=True
    )
    
    # 获取语法修复器
    from unified_auto_fix_system.core.fix_types import FixType
    syntax_fixer = engine.modules.get(FixType.SYNTAX_FIX)
    
    # 分析问题
    issues = syntax_fixer.analyze(context)
    
    print(f'发现 {len(issues)} 个语法问题:')
    for i, issue in enumerate(issues, 1):
        print(f'  {i}. 第{issue.line_number}行: {issue.error_message}')
        if hasattr(issue, 'suggested_fix'):
            print(f'     建议修复: {issue.suggested_fix}')
    
except Exception as e:
    print(f'分析失败: {e}')
    import traceback
    traceback.print_exc()