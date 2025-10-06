#!/usr/bin/env python3
"""深度检查自动修复系统"""

from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
from unified_auto_fix_system.core.fix_types import FixType
import sys

def deep_system_check():
    print('=== 自动修复系统深度检查 ===')
    
    try:
        engine = UnifiedFixEngine('.')
        print('✅ 引擎创建成功')
        
        # 检查所有模块
        print(f'已加载模块: {len(engine.modules)}')
        
        issues_found = []
        
        for fix_type, module in engine.modules.items():
            print(f'  {fix_type.value}: {module.__class__.__name__}')
            
            # 检查必需的方法
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
            
            # 检查增强模块
            if hasattr(module, 'ai_strategies'):
                print(f'    ℹ️  AI策略: {len(module.ai_strategies) if hasattr(module, "ai_strategies") else 0}')
            
        # 检查配置
        print(f'\n配置检查:')
        print(f'  备份启用: {engine.config.get("backup_enabled", False)}')
        print(f'  干运行: {engine.config.get("dry_run", False)}')
        print(f'  AI辅助: {engine.config.get("ai_assisted", False)}')
        
        # 检查增强模块
        enhanced_modules = getattr(engine, 'enhanced_modules', {})
        if enhanced_modules:
            print(f'\n增强模块: {len(enhanced_modules)}')
            for name, module in enhanced_modules.items():
                print(f'  {name}: {type(module).__name__}')
        
        return len(issues_found) == 0, issues_found
        
    except Exception as e:
        print(f'❌ 系统检查失败: {e}')
        import traceback
        traceback.print_exc()
        return False, [str(e)]

if __name__ == '__main__':
    success, issues = deep_system_check()
    
    if success:
        print('\n✅ 系统检查通过 - 未发现严重问题')
        sys.exit(0)
    else:
        print(f'\n❌ 发现 {len(issues)} 个问题:')
        for issue in issues:
            print(f'  - {issue}')
        sys.exit(1)