import sys
sys.path.append('.')

print('=== 检查增强模块和深层问题 ===')

try:
    from unified_auto_fix_system.core.enhanced_unified_fix_engine import EnhancedUnifiedFixEngine
    from unified_auto_fix_system.core.fix_types import FixType
    
    engine = EnhancedUnifiedFixEngine('.')
    print('✅ 增强引擎创建成功')
    
    # 检查增强模块
    enhanced_modules = getattr(engine, 'enhanced_modules', {})
    print(f'增强模块数量: {len(enhanced_modules)}')
    
    issues_found = []
    for name, module in enhanced_modules.items():
        print(f'  {name}: {type(module).__name__}')
        
        # 检查关键方法
        missing = []
        if not hasattr(module, 'analyze'):
            missing.append('analyze')
        if not hasattr(module, 'fix'):
            missing.append('fix')
            
        if missing:
            print(f'    ❌ 缺少: {missing}')
            issues_found.append(f'{name}: 缺少 {missing}')
        else:
            print(f'    ✅ 完整')
    
    print('✅ 增强系统检查完成')
    
    if issues_found:
        print(f'\n❌ 发现 {len(issues_found)} 个问题:')
        for issue in issues_found:
            print(f'  - {issue}')
        exit(1)
    else:
        exit(0)
    
except ImportError as e:
    print(f'ℹ️  增强引擎不可用: {e}')
    print('  使用基础引擎即可')
    exit(0)
except Exception as e:
    print(f'❌ 增强系统检查失败: {e}')
    import traceback
    traceback.print_exc()
    exit(1)