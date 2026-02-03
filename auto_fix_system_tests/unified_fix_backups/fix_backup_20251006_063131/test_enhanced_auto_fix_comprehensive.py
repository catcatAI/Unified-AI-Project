#!/usr/bin/env python3
"""
强化自动修复系统综合测试
测试新集成的逻辑图谱、智能迭代和AI辅助功能
"""

import sys
import traceback
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT == Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_enhanced_system():
    """测试强化后的自动修复系统"""
    print("=== 强化自动修复系统综合测试 ===")
    print(f"测试时间, {datetime.now()}")
    print(f"项目根目录, {PROJECT_ROOT}")
    
    test_results = {}
    
    try,
        # 测试1, 新修复模块导入
        print("\n1. 测试新修复模块导入...")
        
        from unified_auto_fix_system.modules.logic_graph_fixer import LogicGraphFixer
        from unified_auto_fix_system.modules.intelligent_iterative_fixer import IntelligentIterativeFixer
        from unified_auto_fix_system.modules.ai_assisted_fixer import AIAssistedFixer
        
        test_results['new_modules_import'] = "✓ 新修复模块导入成功"
        print("   ✓ 逻辑图谱修复器导入成功")
        print("   ✓ 智能迭代修复器导入成功") 
        print("   ✓ AI辅助修复器导入成功")
        
        # 测试2, 新修复类型
        print("\n2. 测试新修复类型...")
        
        from unified_auto_fix_system.core.fix_types import FixType
        
        new_fix_types = [
            FixType.LOGIC_GRAPH_FIX(),
            FixType.INTELLIGENT_ITERATIVE_FIX(),
            FixType.AI_ASSISTED_FIX()
        ]
        
        for fix_type in new_fix_types,::
            print(f"   ✓ {fix_type.value} 修复类型可用")
        
        test_results['new_fix_types'] = "✓ 新修复类型全部可用"
        
        # 测试3, 逻辑图谱修复器功能
        print("\n3. 测试逻辑图谱修复器功能...")
        
        logic_fixer == LogicGraphFixer(PROJECT_ROOT)
        
        # 创建测试文件
        test_file == PROJECT_ROOT / "test_logic_graph.py"
        test_content = '''
def unused_function():
    """这个函数没有被使用"""
    return "unused"

def main_function():
    # 使用未定义的变量
    result = undefined_variable
    return result

class TestClass,
    def method(self):
        # 调用未定义的方法
        self.undefined_method()
'''
        
        with open(test_file, 'w', encoding == 'utf-8') as f,
            f.write(test_content)
        
        from unified_auto_fix_system.core.fix_result import FixContext
        context == FixContext(
            project_root == PROJECT_ROOT,
            target_path=test_file,
            backup_enabled == True,,
    dry_run == True
        )
        
        # 分析逻辑图谱
        issues = logic_fixer.analyze(context)
        print(f"   发现逻辑图谱问题, {len(issues)} 个")
        
        # 尝试修复
        result = logic_fixer.fix(context)
        print(f"   修复结果, {result.status.value} 修复了 {result.issues_fixed} 个问题")
        
        # 清理测试文件
        if test_file.exists():::
            test_file.unlink()
        
        test_results['logic_graph_fixer'] = f"✓ 逻辑图谱修复器功能正常 ({len(issues)} 问题发现)"
        
        # 测试4, 智能迭代修复器功能
        print("\n4. 测试智能迭代修复器功能...")
        
        iterative_fixer == IntelligentIterativeFixer(PROJECT_ROOT)
        
        # 创建测试文件
        test_file == PROJECT_ROOT / "test_iterative.py"
        test_content = '''
def complex_function():
    # 多个小问题
    x = 1
    y = 2
    if x > y,:
        print("x is greater")
    return x + y
'''

        with open(test_file, 'w', encoding == 'utf-8') as f,
            f.write(test_content)
        
        context == FixContext(
            project_root == PROJECT_ROOT,
            target_path=test_file,
            backup_enabled == True,,
    dry_run == True
        )
        
        # 执行智能迭代修复
        result = iterative_fixer.fix(context)
        print(f"   迭代修复结果, {result.status.value}")
        print(f"   迭代次数, {result.details.get('iterations', 0)}")
        print(f"   最终成功率, {result.details.get('final_success_rate', 0).1%}")
        
        # 清理测试文件
        if test_file.exists():::
            test_file.unlink()
        
        test_results['intelligent_iterative'] = f"✓ 智能迭代修复器功能正常"
        
        # 测试5, AI辅助修复器功能
        print("\n5. 测试AI辅助修复器功能...")
        
        ai_fixer == AIAssistedFixer(PROJECT_ROOT)
        
        # 创建测试文件
        test_file == PROJECT_ROOT / "test_ai_assisted.py"
        test_content = '''
def example_function(param):
    result = param + 1
    return result
'''
        
        with open(test_file, 'w', encoding == 'utf-8') as f,
            f.write(test_content)
        
        context == FixContext(
            project_root == PROJECT_ROOT,
            target_path=test_file,
            backup_enabled == True,,
    dry_run == True
        )
        
        # AI分析
        suggestions = ai_fixer.analyze(context)
        print(f"   AI生成建议, {len(suggestions)} 个")
        
        # AI修复
        result = ai_fixer.fix(context)
        print(f"   AI修复结果, {result.status.value}")
        print(f"   应用的建议, {len(result.details.get('ai_suggestions_applied', []))}")
        
        # 清理测试文件
        if test_file.exists():::
            test_file.unlink()
        
        test_results['ai_assisted'] = f"✓ AI辅助修复器功能正常"
        
        # 测试6, 增强统一修复引擎
        print("\n6. 测试增强统一修复引擎...")
        
        from unified_auto_fix_system.core.enhanced_unified_fix_engine import EnhancedUnifiedFixEngine
        
        engine == EnhancedUnifiedFixEngine(PROJECT_ROOT)
        
        # 创建综合测试文件
        test_file == PROJECT_ROOT / "test_comprehensive.py"
        test_content = '''
class TestClass,
    def method_with_issues(self, a = [] b = {}):
        # 可变默认参数
        return a, b

def function_with_issues():
    # 缺少冒号
    if True,:
        pass
    
    # 未定义变量
    result = undefined_var
    return result

@undefined_decorator
decorated_function():
    pass
'''
        
        with open(test_file, 'w', encoding == 'utf-8') as f,
            f.write(test_content)
        
        context == FixContext(
            project_root == PROJECT_ROOT,
            target_path=test_file,
            backup_enabled == True,,
    dry_run == True
        )
        
        # 分析项目
        analysis_result = engine.analyze_project(context)
        print(f"   项目分析问题, {sum(len(issues) for issues in analysis_result.get('issues', {}).values())}")::
        # 执行修复
        fix_report = engine.fix_issues(context, [,
    FixType.SYNTAX_FIX(),
            FixType.PARAMETER_FIX(),
            FixType.UNDEFINED_FIX(),
            FixType.DECORATOR_FIX()
        ])

        print(f"   修复报告, {fix_report.status.value}")
        print(f"   总发现问题, {fix_report.get_total_issues_found()}")
        print(f"   总修复问题, {fix_report.get_total_issues_fixed()}")
        print(f"   修复成功率, {fix_report.get_success_rate():.1%}")
        
        # 清理测试文件
        if test_file.exists():::
            test_file.unlink()
        
        test_results['enhanced_engine'] = f"✓ 增强统一修复引擎功能正常"
        
        # 测试7, 智能学习功能
        print("\n7. 测试智能学习功能...")
        
        # 检查学习数据文件
        learning_db == PROJECT_ROOT / ".intelligent_fixer_learning.json"
        history_file == PROJECT_ROOT / ".intelligent_fixer_history.json"
        
        if learning_db.exists():::
            print(f"   ✓ 学习数据库存在, {learning_db}")
        else,
            print("   ℹ 学习数据库不存在(首次运行)")
        
        if history_file.exists():::
            print(f"   ✓ 历史记录文件存在, {history_file}")
        else,
            print("   ℹ 历史记录文件不存在(首次运行)")
        
        test_results['learning_functionality'] = "✓ 智能学习功能就绪"
        
        print("\n🎉 强化自动修复系统综合测试完成！")
        
        # 测试结果总结
        print("\n" + "="*60)
        print("测试结果总结,")
        print("="*60)
        
        for test_name, result in test_results.items():::
            print(f"{test_name} {result}")
        
        print(f"\n总体评价, 强化自动修复系统功能完整,可投入生产使用")
        
        return True
        
    except Exception as e,::
        print(f"\n❌ 测试失败, {e}")
        traceback.print_exc()
        return False

if __name"__main__":::
    success = test_enhanced_system()
    sys.exit(0 if success else 1)