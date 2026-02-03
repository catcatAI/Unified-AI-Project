#!/usr/bin/env python3
"""
修复统一自动修复系统目录
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def repair_unified_auto_fix_system():
    """修复统一自动修复系统目录"""
    print("开始修复统一自动修复系统目录...")
    
    try:
        # 导入必要的模块
        from unified_auto_fix_system.core.fix_result import FixContext, FixResult
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope, FixPriority
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        from unified_auto_fix_system.modules.dependency_fixer import DependencyFixer
        
        # 确定目标目录
        target_dir = project_root / "unified_auto_fix_system"
        if not target_dir.exists():
            print(f"❌ 目录不存在: {target_dir}")
            return False
        
        print(f"✓ 目标目录: {target_dir}")
        
        # 创建修复上下文
        context = FixContext(
            project_root=project_root,
            target_path=target_dir,
            scope=FixScope.SPECIFIC_DIRECTORY,
            priority=FixPriority.HIGH,
            backup_enabled=True,
            dry_run=False,
            ai_assisted=False,
            excluded_paths=[
                "node_modules", "__pycache__", ".git", "venv", ".venv",
                "backup", "unified_fix_backups", "logs", ".pytest_cache"
            ]
        )
        
        print("✓ 修复上下文创建成功")
        
        # 创建修复器实例
        syntax_fixer = EnhancedSyntaxFixer(project_root)
        import_fixer = ImportFixer(project_root)
        dependency_fixer = DependencyFixer(project_root)
        
        print("✓ 修复器创建成功")
        
        # 执行语法修复
        print("开始语法修复...")
        syntax_result = syntax_fixer.fix(context)
        print(f"✓ 语法修复完成: {syntax_result.summary()}")
        
        # 执行导入修复
        print("开始导入修复...")
        import_result = import_fixer.fix(context)
        print(f"✓ 导入修复完成: {import_result.summary()}")
        
        # 执行依赖修复
        print("开始依赖修复...")
        dependency_result = dependency_fixer.fix(context)
        print(f"✓ 依赖修复完成: {dependency_result.summary()}")
        
        # 创建修复报告
        from unified_auto_fix_system.core.fix_result import FixReport
        report = FixReport(
            timestamp=datetime.now(),
            project_root=project_root,
            context=context,
            fix_results={
                FixType.SYNTAX_FIX: syntax_result,
                FixType.IMPORT_FIX: import_result,
                FixType.DEPENDENCY_FIX: dependency_result
            }
        )
        
        # 显示修复摘要
        print("\n修复摘要:")
        print(report.get_summary())
        
        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"unified_auto_fix_system_repair_report_{timestamp}.json"
        report_path = project_root / "repair_reports" / report_filename
        
        # 确保报告目录存在
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✓ 修复报告已保存: {report_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ 统一自动修复系统修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_before_repair():
    """修复前验证"""
    print("修复前验证...")
    
    try:
        # 验证目录存在
        target_dir = project_root / "unified_auto_fix_system"
        if not target_dir.exists():
            print(f"❌ 目标目录不存在: {target_dir}")
            return False
        
        # 验证核心文件存在
        core_files = [
            "core/fix_types.py",
            "core/fix_result.py", 
            "core/unified_fix_engine.py",
            "modules/base_fixer.py",
            "modules/syntax_fixer.py",
            "modules/import_fixer.py"
        ]
        
        for file_path in core_files:
            full_path = target_dir / file_path
            if not full_path.exists():
                print(f"⚠️  核心文件缺失: {full_path}")
        
        print("✓ 修复前验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 修复前验证失败: {e}")
        return False

def validate_after_repair():
    """修复后验证"""
    print("修复后验证...")
    
    try:
        # 验证系统仍能正常导入
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        
        # 创建实例测试
        engine = UnifiedFixEngine(project_root)
        fixer = EnhancedSyntaxFixer(project_root)
        
        print("✓ 修复后验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 修复后验证失败: {e}")
        return False

def main():
    """主函数"""
    print("开始修复统一自动修复系统...")
    print("=" * 30)
    
    # 1. 修复前验证
    if not validate_before_repair():
        print("❌ 修复前验证失败")
        return 1
    
    print()
    
    # 2. 执行修复
    if not repair_unified_auto_fix_system():
        print("❌ 修复失败")
        return 1
    
    print()
    
    # 3. 修复后验证
    if not validate_after_repair():
        print("❌ 修复后验证失败")
        return 1
    
    print()
    print("=" * 30)
    print("🎉 统一自动修复系统修复完成！")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())