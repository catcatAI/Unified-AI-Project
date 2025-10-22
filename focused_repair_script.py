#!/usr/bin/env python3
"""
聚焦修复脚本 - 针对特定目录使用自动修复系统进行修复
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def repair_specific_directory(directory_name):
    """修复特定目录"""
    print(f"开始修复目录: {directory_name}")
    
    try:
        # 导入必要的模块
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        from unified_auto_fix_system.core.fix_result import FixContext, FixResult
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope, FixPriority
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        
        # 确定目标目录
        target_dir = project_root / directory_name
        if not target_dir.exists():
            print(f"⚠️ 目录不存在: {target_dir}")
            return False
        
        print(f"✓ 目标目录: {target_dir}")
        
        # 创建修复上下文（针对特定目录）
        context = FixContext(
            project_root=project_root,
            target_path=target_dir,
            scope=FixScope.SPECIFIC_DIRECTORY,
            priority=FixPriority.NORMAL,
            backup_enabled=True,
            dry_run=False,
            ai_assisted=False,
            excluded_paths=[
                "node_modules", "__pycache__", ".git", "venv", ".venv",
                "backup", "unified_fix_backups", "logs", ".pytest_cache",
                "model_cache", "training/models", "training/checkpoints"
            ]
        )
        
        print("✓ 修复上下文创建成功")
        
        # 创建修复器实例
        syntax_fixer = EnhancedSyntaxFixer(project_root)
        import_fixer = ImportFixer(project_root)
        
        print("✓ 修复器创建成功")
        
        # 执行语法修复
        print("开始语法修复...")
        syntax_result = syntax_fixer.fix(context)
        print(f"✓ 语法修复完成: {syntax_result.summary()}")
        
        # 执行导入修复
        print("开始导入修复...")
        import_result = import_fixer.fix(context)
        print(f"✓ 导入修复完成: {import_result.summary()}")
        
        # 创建修复报告
        from unified_auto_fix_system.core.fix_result import FixReport
        report = FixReport(
            timestamp=datetime.now(),
            project_root=project_root,
            context=context,
            fix_results={
                FixType.SYNTAX_FIX: syntax_result,
                FixType.IMPORT_FIX: import_result
            }
        )
        
        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{directory_name}_repair_report_{timestamp}.json"
        report_path = project_root / "repair_reports" / report_filename
        
        # 确保报告目录存在
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✓ 修复报告已保存: {report_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ 目录修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def repair_unified_auto_fix_system():
    """修复统一自动修复系统自身"""
    print("开始修复统一自动修复系统...")
    
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        from unified_auto_fix_system.core.fix_result import FixContext
        from unified_auto_fix_system.core.fix_types import FixScope, FixPriority
        
        # 创建修复上下文
        context = FixContext(
            project_root=project_root,
            target_path=project_root / "unified_auto_fix_system",
            scope=FixScope.SPECIFIC_DIRECTORY,
            priority=FixPriority.HIGH,
            backup_enabled=True,
            dry_run=False,
            ai_assisted=False
        )
        
        # 创建修复引擎
        engine = UnifiedFixEngine(project_root)
        print("✓ 修复引擎创建成功")
        
        # 修复统一自动修复系统
        report = engine.fix_issues(context)
        print(f"✓ 统一自动修复系统修复完成: {report.get_summary()}")
        
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

def validate_repair_system():
    """验证修复系统"""
    print("验证自动修复系统...")
    
    try:
        # 验证核心组件
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus
        from unified_auto_fix_system.core.fix_result import FixResult
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        
        print("✓ 核心组件导入成功")
        
        # 验证基本功能
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=1,
            issues_fixed=1
        )
        assert result.is_successful()
        print("✓ 数据类功能正常")
        
        # 验证修复器创建
        syntax_fixer = EnhancedSyntaxFixer(project_root)
        import_fixer = ImportFixer(project_root)
        print("✓ 修复器创建正常")
        
        print("✓ 自动修复系统验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 自动修复系统验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始聚焦修复...")
    print("=" * 30)
    
    # 1. 验证修复系统
    if not validate_repair_system():
        print("❌ 修复系统验证失败")
        return 1
    
    print()
    
    # 2. 修复统一自动修复系统自身
    print("第一步：修复统一自动修复系统自身")
    if not repair_unified_auto_fix_system():
        print("❌ 统一自动修复系统修复失败")
        return 1
    
    print()
    
    # 3. 修复其他关键目录
    key_directories = [
        "apps/backend/src",
        "apps/backend/tests", 
        "training",
        "analysis"
    ]
    
    for directory in key_directories:
        print(f"第二步：修复目录 {directory}")
        repair_specific_directory(directory)
        print()
    
    print("=" * 30)
    print("聚焦修复完成")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())