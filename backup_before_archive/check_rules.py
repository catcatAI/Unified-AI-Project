#!/usr/bin/env python3
"""
检查统一自动修复系统的问题发现规则和修复规则
"""

def check_rules():
    """检查规则和修复规则"""
    print("🔍 检查统一自动修复系统的问题发现规则和修复规则...")
    
    try:
        # 检查语法发现规则
        from unified_auto_fix_system.modules.base_fixer import EnhancedSyntaxFixer
        syntax_fixer = EnhancedSyntaxFixer()
        rules = syntax_fixer.get_fix_rules()
        print(f"✅ 语法发现规则: {len(rules)} 条规则")
        
        # 显示一些规则示例
        if rules:
            print("  📋 规则示例:")
            for i, rule in enumerate(rules[:3]):
                print(f"    {i+1}. {rule.get('name', '未知规则')}: {rule.get('description', '无描述')}")
        
        # 检查修复规则类型
        from unified_auto_fix_system.core.fix_types import FixType
        fix_types = [ft for ft in FixType]
        print(f"✅ 修复规则类型: {len(fix_types)} 种")
        print("  📋 修复类型:")
        for ft in fix_types[:5]:
            print(f"    - {ft.value}: {ft.name}")
        
        # 检查统一系统模块
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        engine = UnifiedFixEngine('.')
        print(f"✅ 统一修复引擎: {len(engine.modules)} 个模块")
        print("  📋 可用模块:")
        for module_name in engine.modules.keys():
            print(f"    - {module_name}")
        
        print("✅ 问题发现规则和修复规则检查完成")
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

if __name__ == "__main__":
    check_rules()