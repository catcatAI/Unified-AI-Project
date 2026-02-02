import sys
sys.path.append('.')

print('=== 自动修复系统深度检查 ===')

try:
    from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
    from unified_auto_fix_system.core.fix_types import FixType
    
    engine = UnifiedFixEngine('.')
    print('✅ 引擎创建成功')
    
    print(f'已加载模块: {len(engine.modules)}')
    issues_found = []
    
    for fix_type, module in engine.modules.items():
        print(f'  {fix_type.value}: {module.__class__.__name__}')
        
        missing_methods = []
        if not hasattr(module, 'analyze'):
            missing_methods.append('analyze')
        if not hasattr(module, 'fix'):
            missing_methods.append('fix')
        if not hasattr(module, '_get_target_files'):
            missing_methods.append('_get_target_files')
            
        if missing_methods:
            print(f'    ❌ 缺少方法: {missing_methods}')
            issues_found.append(f'{fix_type.value}: 缺少方法 {missing_methods}')
        else:
            print(f'    ✅ 方法完整')
    
    print('\n配置检查:')
    print(f'  备份启用: {engine.config.get("backup_enabled", False)}')
    print(f'  干运行: {engine.config.get("dry_run", False)}')
    print(f'  AI辅助: {engine.config.get("ai_assisted", False)}')
    
    if issues_found:
        print(f'\n❌ 发现 {len(issues_found)} 个问题:')
        for issue in issues_found:
            print(f'  - {issue}')
        exit(1)
    else:
        print('\n✅ 系统检查通过 - 未发现严重问题')
        exit(0)
        
except Exception as e:
    print(f'❌ 系统检查失败: {e}')
    import traceback
    traceback.print_exc()
    exit(1)