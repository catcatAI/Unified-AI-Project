#!/usr/bin/env python3
"""
项目修复脚本 - 使用自动修复系统对项目进行全面修复
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_repair_engine():
    """创建修复引擎"""
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        engine = UnifiedFixEngine(project_root)
        print("✓ 修复引擎创建成功")
        return engine
    except Exception as e:
        print(f"✗ 修复引擎创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_repair_context(dry_run=False):
    """创建修复上下文"""
    try:
        from unified_auto_fix_system.core.fix_result import FixContext
        from unified_auto_fix_system.core.fix_types import FixScope, FixPriority
        
        context = FixContext(
            project_root=project_root,
            scope=FixScope.PROJECT,
            priority=FixPriority.NORMAL,
            backup_enabled=True,
            dry_run=dry_run,
            ai_assisted=False,
            excluded_paths=[
                "node_modules", "__pycache__", ".git", "venv", ".venv",
                "backup", "unified_fix_backups", "logs", ".pytest_cache",
                "model_cache", "training/models", "training/checkpoints"
            ]
        )
        print("✓ 修复上下文创建成功")
        return context
    except Exception as e:
        print(f"✗ 修复上下文创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_project(engine, context):
    """分析项目问题"""
    try:
        print("开始分析项目问题...")
        analysis_result = engine.analyze_project(context)
        
        # 统计问题
        total_issues = sum(analysis_result.get("statistics", {}).values())
        print(f"✓ 项目分析完成，发现 {total_issues} 个问题")
        
        # 显示各类问题统计
        for fix_type, count in analysis_result.get("statistics", {}).items():
            if count > 0:
                print(f"  - {fix_type}: {count} 个问题")
        
        return analysis_result
    except Exception as e:
        print(f"✗ 项目分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def fix_project_issues(engine, context):
    """修复项目问题"""
    try:
        print("开始修复项目问题...")
        fix_report = engine.fix_issues(context)
        
        # 显示修复结果
        print(f"✓ 修复完成: {fix_report.get_summary()}")
        
        # 详细统计
        successful_fixes = fix_report.get_successful_fixes()
        failed_fixes = fix_report.get_failed_fixes()
        total_found = fix_report.get_total_issues_found()
        total_fixed = fix_report.get_total_issues_fixed()
        
        print(f"  - 成功修复: {len(successful_fixes)} 个模块")
        print(f"  - 修复失败: {len(failed_fixes)} 个模块")
        print(f"  - 总计发现问题: {total_found} 个")
        print(f"  - 总计修复问题: {total_fixed} 个")
        
        return fix_report
    except Exception as e:
        print(f"✗ 项目修复失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_repair_report(report, filename=None):
    """保存修复报告"""
    try:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"repair_report_{timestamp}.json"
        
        report_path = project_root / filename
        
        # 确保报告目录存在
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✓ 修复报告已保存: {report_path}")
        return report_path
    except Exception as e:
        print(f"✗ 修复报告保存失败: {e}")
        return None

def validate_repair_system():
    """验证修复系统"""
    print("验证自动修复系统...")
    
    try:
        # 验证核心组件
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus
        from unified_auto_fix_system.core.fix_result import FixResult, FixContext
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        from unified_auto_fix_system.modules.dependency_fixer import DependencyFixer
        
        print("✓ 所有核心组件导入成功")
        
        # 验证基本功能
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=1,
            issues_fixed=1
        )
        assert result.is_successful()
        print("✓ 数据类功能正常")
        
        # 验证修复引擎创建
        engine = UnifiedFixEngine(project_root)
        assert len(engine.modules) > 0
        print("✓ 修复引擎功能正常")
        
        # 验证修复器创建
        syntax_fixer = EnhancedSyntaxFixer(project_root)
        import_fixer = ImportFixer(project_root)
        dependency_fixer = DependencyFixer(project_root)
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
    print("开始使用自动修复系统对项目进行全面修复...")
    print("=" * 50)
    
    # 1. 验证修复系统
    if not validate_repair_system():
        print("❌ 修复系统验证失败，无法继续修复")
        return 1
    
    print()
    
    # 2. 创建修复引擎和上下文
    engine = create_repair_engine()
    if engine is None:
        print("❌ 无法创建修复引擎")
        return 1
    
    context = create_repair_context(dry_run=False)
    if context is None:
        print("❌ 无法创建修复上下文")
        return 1
    
    print()
    
    # 3. 分析项目问题（干运行模式）
    print("第一步：分析项目问题（干运行模式）")
    dry_run_context = create_repair_context(dry_run=True)
    analysis_result = analyze_project(engine, dry_run_context)
    
    if analysis_result is None:
        print("❌ 项目分析失败")
        return 1
    
    print()
    
    # 4. 实际修复项目问题
    print("第二步：实际修复项目问题")
    fix_report = fix_project_issues(engine, context)
    
    if fix_report is None:
        print("❌ 项目修复失败")
        return 1
    
    print()
    
    # 5. 保存修复报告
    print("第三步：保存修复报告")
    report_path = save_repair_report(fix_report)
    
    if report_path is None:
        print("⚠️ 修复报告保存失败")
    
    print()
    
    # 6. 最终验证
    print("第四步：最终验证")
    final_context = create_repair_context(dry_run=True)
    final_analysis = analyze_project(engine, final_context)
    
    if final_analysis:
        final_issues = sum(final_analysis.get("statistics", {}).values())
        print(f"✓ 最终验证完成，剩余 {final_issues} 个问题")
        
        if final_issues == 0:
            print("🎉 项目修复完成，所有问题已解决！")
        else:
            print(f"⚠️ 项目修复基本完成，但仍存在 {final_issues} 个问题需要手动处理")
    
    print()
    print("=" * 50)
    print("项目修复过程完成")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())