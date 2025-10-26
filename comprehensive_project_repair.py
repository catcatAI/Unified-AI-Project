#!/usr/bin/env python3
"""
全面项目修复脚本 - 使用自动修复系统对项目进行全面修复
"""

import sys
import os
import json
import traceback
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_repair_system():
    """验证修复系统完整性"""
    print("验证自动修复系统...")
    
    try:
        # 验证核心组件
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus
        from unified_auto_fix_system.core.fix_result import FixResult, FixContext
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        from unified_auto_fix_system.modules.dependency_fixer import DependencyFixer
        
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
        
        # 验证修复引擎
        engine = UnifiedFixEngine(project_root)
        assert len(engine.modules) > 0
        print("✓ 修复引擎功能正常")
        
        # 验证修复器
        syntax_fixer = EnhancedSyntaxFixer(project_root)
        import_fixer = ImportFixer(project_root)
        dependency_fixer = DependencyFixer(project_root)
        print("✓ 修复器功能正常")
        
        print("✓ 自动修复系统验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 自动修复系统验证失败: {e}")
        traceback.print_exc()
        return False

def create_repair_context(scope_dir=None, dry_run=False):
    """创建修复上下文"""
    try:
        from unified_auto_fix_system.core.fix_result import FixContext
        from unified_auto_fix_system.core.fix_types import FixScope, FixPriority
        
        context = FixContext(
            project_root=project_root,
            target_path=Path(scope_dir) if scope_dir else None,
            scope=FixScope.SPECIFIC_DIRECTORY if scope_dir else FixScope.PROJECT,
            priority=FixPriority.NORMAL,
            backup_enabled=True,
            dry_run=dry_run,
            ai_assisted=False,
            excluded_paths=[
                "node_modules", "__pycache__", ".git", "venv", ".venv",
                "backup", "unified_fix_backups", "logs", ".pytest_cache",
                "model_cache", "training/models", "training/checkpoints",
                "unified_auto_fix_system",  # 避免递归修复
                # 添加以下归档目录以忽略其中的已知损坏脚本
                "archived_fix_scripts",
                "archived_systems",
                "auto_fix_workspace",
                "project_archives"
            ]
        )
        
        return context
    except Exception as e:
        print(f"创建修复上下文失败: {e}")
        return None

def repair_project_scope(engine, context, scope_name):
    """修复特定范围"""
    print(f"\n开始修复范围: {scope_name}")
    
    try:
        # 执行修复
        report = engine.fix_issues(context)
        
        # 显示结果
        print(f"✓ {scope_name} 修复完成:")
        print(f"  {report.get_summary()}")
        
        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{scope_name.replace('/', '_')}_repair_report_{timestamp}.json"
        report_path = project_root / "repair_reports" / report_filename
        
        # 确保报告目录存在
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"  报告已保存: {report_path}")
        
        return report
    except Exception as e:
        print(f"✗ {scope_name} 修复失败: {e}")
        traceback.print_exc()
        return None

def repair_key_project_areas():
    """修复关键项目区域"""
    print("开始修复关键项目区域...")
    
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        
        # 创建修复引擎
        engine = UnifiedFixEngine(project_root)
        print("✓ 修复引擎创建成功")
        
        # 定义要修复的关键区域
        key_areas = [
            ("apps/backend/src", "后端源码"),
            ("apps/backend/tests", "后端测试"),
            ("training", "训练系统"),
            ("analysis", "分析模块"),
            ("cli", "命令行工具")
        ]
        
        # 修复每个区域
        reports = []
        for area_path, area_name in key_areas:
            area_full_path = project_root / area_path
            if area_full_path.exists():
                context = create_repair_context(area_full_path)
                if context:
                    report = repair_project_scope(engine, context, area_name)
                    if report:
                        reports.append((area_name, report))
            else:
                print(f"⚠️  区域不存在: {area_path}")
        
        return reports
    except Exception as e:
        print(f"✗ 关键区域修复失败: {e}")
        traceback.print_exc()
        return []

def validate_repair_results(reports):
    """验证修复结果"""
    print("\n验证修复结果...")
    
    try:
        total_issues_found = 0
        total_issues_fixed = 0
        successful_repairs = 0
        failed_repairs = 0
        
        for area_name, report in reports:
            issues_found = report.get_total_issues_found()
            issues_fixed = report.get_total_issues_fixed()
            success_rate = report.get_success_rate()
            
            total_issues_found += issues_found
            total_issues_fixed += issues_fixed
            
            if success_rate > 0:
                successful_repairs += 1
            else:
                failed_repairs += 1
            
            print(f"  {area_name}: 发现{issues_found}个问题，修复{issues_fixed}个问题")
        
        print(f"\n总体修复统计:")
        print(f"  总计发现问题: {total_issues_found}")
        print(f"  总计修复问题: {total_issues_fixed}")
        print(f"  成功修复区域: {successful_repairs}")
        print(f"  修复失败区域: {failed_repairs}")
        
        return True
    except Exception as e:
        print(f"✗ 修复结果验证失败: {e}")
        return False

def main():
    """主函数"""
    print("开始全面项目修复...")
    print("=" * 30)
    
    # 1. 验证修复系统
    if not validate_repair_system():
        print("❌ 自动修复系统验证失败，无法继续")
        return 1
    
    print()
    
    # 2. 修复关键项目区域
    reports = repair_key_project_areas()
    
    if not reports:
        print("⚠️  没有区域需要修复或修复失败")
        return 1
    
    print()
    
    # 3. 验证修复结果
    if not validate_repair_results(reports):
        print("⚠️  修复结果验证失败")
        return 1
    
    print("\n" + "=" * 30)
    print("🎉 全面项目修复完成！")
    print(f"成功修复了 {len(reports)} 个关键区域")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())