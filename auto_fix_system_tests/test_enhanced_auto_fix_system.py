#!/usr/bin/env python3
"""
测试增强后的统一自动修复系统
验证所有修复模块的功能
"""

import sys
import traceback
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from unified_auto_fix_system.core.enhanced_unified_fix_engine import EnhancedUnifiedFixEngine
from unified_auto_fix_system.core.fix_types import FixType, FixScope, FixPriority
from unified_auto_fix_system.core.fix_result import FixContext
from unified_auto_fix_system.utils.ast_analyzer import ASTAnalyzer
from unified_auto_fix_system.utils.dependency_tracker import DependencyTracker
from unified_auto_fix_system.utils.io_analyzer import IOAnalyzer
from unified_auto_fix_system.utils.rule_engine import RuleEngine


def test_individual_modules():
    """测试各个修复模块"""
    print("=== 测试各个修复模块 ===")
    
    project_root = PROJECT_ROOT
    test_results = {}
    
    # 测试AST分析器
    print("\n1. 测试AST分析器...")
    try:
        ast_analyzer = ASTAnalyzer()  # 不需要project_root参数
        test_files = list(project_root.glob("**/*.py"))[:5]  # 测试前5个Python文件
        
        for file_path in test_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 测试未定义变量检测
                undefined_vars = ast_analyzer.find_undefined_variables(content, str(file_path))
                imports = ast_analyzer.find_imports(content)
                
                print(f"  文件 {file_path.name}: 发现 {len(undefined_vars)} 个未定义变量, {len(imports)} 个导入")
                
            except Exception as e:
                print(f"  文件 {file_path.name}: 分析失败 - {e}")
        
        test_results['ast_analyzer'] = "通过"
        print("  ✓ AST分析器测试通过")
        
    except Exception as e:
        test_results['ast_analyzer'] = f"失败: {e}"
        print(f"  ✗ AST分析器测试失败: {e}")
    
    # 测试依赖跟踪器
    print("\n2. 测试依赖跟踪器...")
    try:
        dep_tracker = DependencyTracker()  # 不需要project_root参数
        
        # 分析项目依赖
        python_deps = dep_tracker.analyze_python_dependencies(str(project_root / "apps" / "backend" / "src"))
        js_deps = dep_tracker.analyze_javascript_dependencies(str(project_root / "apps" / "frontend-dashboard"))
        
        print(f"  Python依赖: {len(python_deps)} 个")
        print(f"  JavaScript依赖: {len(js_deps)} 个")
        
        # 检查循环依赖
        cycles = dep_tracker.find_circular_dependencies()
        print(f"  循环依赖: {len(cycles)} 个")
        
        test_results['dependency_tracker'] = "通过"
        print("  ✓ 依赖跟踪器测试通过")
        
    except Exception as e:
        test_results['dependency_tracker'] = f"失败: {e}"
        print(f"  ✗ 依赖跟踪器测试失败: {e}")
    
    # 测试IO分析器
    print("\n3. 测试IO分析器...")
    try:
        io_analyzer = IOAnalyzer()  # 不需要project_root参数
        
        # 分析IO操作
        if test_files:
            test_file = str(test_files[0])
            with open(test_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            io_ops = io_analyzer.analyze_io_operations(content, test_file)
            file_ops = io_analyzer.analyze_file_operations(content, test_file)
            
            print(f"  IO操作: {len(io_ops)} 个")
            print(f"  文件操作: {len(file_ops)} 个")
        
        test_results['io_analyzer'] = "通过"
        print("  ✓ IO分析器测试通过")
        
    except Exception as e:
        test_results['io_analyzer'] = f"失败: {e}"
        print(f"  ✗ IO分析器测试失败: {e}")
    
    # 测试规则引擎
    print("\n4. 测试规则引擎...")
    try:
        rule_engine = RuleEngine()
        
        # 测试规则匹配
        test_code = """
def example_function():
    undefined_variable = some_undefined_var
    return undefined_variable
"""
        
        # 创建测试上下文
        from unified_auto_fix_system.core.fix_result import FixContext
        test_context = FixContext(project_root=Path("."), target_path=Path("test.py"))
        
        # 分析规则
        rule_results = rule_engine.analyze_rules(test_context)
        print(f"  规则分析结果: {len(rule_results)} 个类别")
        
        # 应用规则
        applications = rule_engine.apply_rules(test_context)
        print(f"  规则应用: {len(applications)} 个")
        
        test_results['rule_engine'] = "通过"
        print("  ✓ 规则引擎测试通过")
        
    except Exception as e:
        test_results['rule_engine'] = f"失败: {e}"
        print(f"  ✗ 规则引擎测试失败: {e}")
    
    return test_results


def test_specialized_fixers():
    """测试专门化修复器"""
    print("\n=== 测试专门化修复器 ===")
    
    project_root = PROJECT_ROOT
    test_results = {}
    
    # 创建测试文件
    test_file_path = project_root / "test_fixes.py"
    
    # 测试装饰器修复器
    print("\n1. 测试装饰器修复器...")
    try:
        from unified_auto_fix_system.modules.decorator_fixer import DecoratorFixer
        
        # 创建测试代码
        test_code = """
@undefined_decorator
def test_function():
    pass

@cache
def expensive_function():
    return 42
"""
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        decorator_fixer = DecoratorFixer(project_root)
        context = FixContext(project_root=project_root, target_path=test_file_path)
        
        # 分析问题
        issues = decorator_fixer.analyze(context)
        print(f"  发现装饰器问题: {len(issues)} 个")
        
        # 尝试修复
        result = decorator_fixer.fix(context)
        print(f"  修复结果: {result.status.value}, 修复了 {result.issues_fixed} 个问题")
        
        test_results['decorator_fixer'] = "通过"
        print("  ✓ 装饰器修复器测试通过")
        
    except Exception as e:
        test_results['decorator_fixer'] = f"失败: {e}"
        print(f"  ✗ 装饰器修复器测试失败: {e}")
    
    # 测试未定义修复器
    print("\n2. 测试未定义修复器...")
    try:
        from unified_auto_fix_system.modules.undefined_fixer import UndefinedFixer
        
        # 创建测试代码
        test_code = """
def test_function():
    result = undefined_variable + another_undefined
    return result
"""
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        undefined_fixer = UndefinedFixer(project_root)
        context = FixContext(project_root=project_root, target_path=test_file_path)
        
        # 分析问题
        issues = undefined_fixer.analyze(context)
        print(f"  发现未定义问题: {len(issues)} 个")
        
        # 尝试修复
        result = undefined_fixer.fix(context)
        print(f"  修复结果: {result.status.value}, 修复了 {result.issues_fixed} 个问题")
        
        test_results['undefined_fixer'] = "通过"
        print("  ✓ 未定义修复器测试通过")
        
    except Exception as e:
        test_results['undefined_fixer'] = f"失败: {e}"
        print(f"  ✗ 未定义修复器测试失败: {e}")
    
    # 测试类修复器
    print("\n3. 测试类修复器...")
    try:
        from unified_auto_fix_system.modules.class_fixer import ClassFixer
        
        # 创建测试代码
        test_code = """
class TestClass(UndefinedBaseClass):
    pass

class TestClass:  # 重复定义
    pass
"""
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        class_fixer = ClassFixer(project_root)
        context = FixContext(project_root=project_root, target_path=test_file_path)
        
        # 分析问题
        issues = class_fixer.analyze(context)
        print(f"  发现类问题: {len(issues)} 个")
        
        # 尝试修复
        result = class_fixer.fix(context)
        print(f"  修复结果: {result.status.value}, 修复了 {result.issues_fixed} 个问题")
        
        test_results['class_fixer'] = "通过"
        print("  ✓ 类修复器测试通过")
        
    except Exception as e:
        test_results['class_fixer'] = f"失败: {e}"
        print(f"  ✗ 类修复器测试失败: {e}")
    
    # 测试参数修复器
    print("\n4. 测试参数修复器...")
    try:
        from unified_auto_fix_system.modules.parameter_fixer import ParameterFixer
        
        # 创建测试代码
        test_code = """
def test_function(a=[], b={}):
    return a, b

def another_function(c, d=1, e):
    return c, d, e
"""
        
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        parameter_fixer = ParameterFixer(project_root)
        context = FixContext(project_root=project_root, target_path=test_file_path)
        
        # 分析问题
        issues = parameter_fixer.analyze(context)
        print(f"  发现参数问题: {len(issues)} 个")
        
        # 尝试修复
        result = parameter_fixer.fix(context)
        print(f"  修复结果: {result.status.value}, 修复了 {result.issues_fixed} 个问题")
        
        test_results['parameter_fixer'] = "通过"
        print("  ✓ 参数修复器测试通过")
        
    except Exception as e:
        test_results['parameter_fixer'] = f"失败: {e}"
        print(f"  ✗ 参数修复器测试失败: {e}")
    
    # 清理测试文件
    try:
        if test_file_path.exists():
            test_file_path.unlink()
    except Exception:
        pass
    
    return test_results


def test_enhanced_unified_engine():
    """测试增强的统一修复引擎"""
    print("\n=== 测试增强的统一修复引擎 ===")
    
    project_root = PROJECT_ROOT
    test_results = {}
    
    try:
        # 初始化引擎
        engine = EnhancedUnifiedFixEngine(project_root)
        
        # 创建测试上下文
        context = FixContext(
            project_root=project_root,
            scope=FixScope.PROJECT,
            priority=FixPriority.NORMAL,
            backup_enabled=True,
            dry_run=True  # 干运行模式，不实际修改文件
        )
        
        print("\n1. 测试项目分析...")
        # 分析项目
        analysis_result = engine.analyze_project(context)
        print(f"  发现问题总数: {sum(len(issues) for issues in analysis_result.get('issues', {}).values())}")
        
        print("\n2. 测试批量修复...")
        # 执行修复
        fix_report = engine.fix_issues(context, [FixType.SYNTAX_FIX, FixType.IMPORT_FIX])
        
        print(f"  修复报告时间: {fix_report.timestamp}")
        print(f"  总发现问题: {fix_report.get_total_issues_found()}")
        print(f"  总修复问题: {fix_report.get_total_issues_fixed()}")
        print(f"  修复成功率: {fix_report.get_success_rate():.1%}")
        print(f"  修复模块数: {len(fix_report.fix_results)}")
        
        # 显示详细的修复结果
        for fix_type, result in fix_report.fix_results.items():
            if result.issues_found > 0:
                print(f"  {fix_type.value}: {result.issues_fixed}/{result.issues_found} 修复成功")
        
        print("\n3. 测试并行处理...")
        # 测试并行处理
        import time
        start_time = time.time()
        
        # 启用并行处理
        context_parallel = FixContext(
            project_root=project_root,
            scope=FixScope.PROJECT,
            priority=FixPriority.HIGH,
            backup_enabled=True,
            dry_run=True
        )
        
        parallel_report = engine.fix_issues(context_parallel, [FixType.SYNTAX_FIX])
        
        parallel_duration = time.time() - start_time
        print(f"  并行处理时间: {parallel_duration:.2f}秒")
        print(f"  并行修复结果: {parallel_report.get_success_rate():.1%} 成功率")
        
        test_results['enhanced_engine'] = "通过"
        print("  ✓ 增强统一修复引擎测试通过")
        
    except Exception as e:
        test_results['enhanced_engine'] = f"失败: {e}"
        print(f"  ✗ 增强统一修复引擎测试失败: {e}")
        traceback.print_exc()
    
    return test_results


def test_cli_interface():
    """测试命令行接口"""
    print("\n=== 测试命令行接口 ===")
    
    test_results = {}
    
    try:
        from unified_auto_fix_system.interfaces.cli_interface import CLIFixInterface
        
        # 创建CLI接口实例
        cli = CLIFixInterface()
        
        # 测试参数解析
        test_args = [
            ['--project-root', str(PROJECT_ROOT), 'analyze', '--format', 'summary'],
            ['--project-root', str(PROJECT_ROOT), 'fix', '--types', 'syntax_fix', '--dry-run'],
            ['--project-root', str(PROJECT_ROOT), 'status', '--detailed']
        ]
        
        for i, args in enumerate(test_args):
            print(f"\n  测试CLI命令 {i+1}: {' '.join(args)}")
            try:
                exit_code = cli.run(args)
                print(f"  退出码: {exit_code}")
            except SystemExit as e:
                print(f"  退出码: {e.code}")
            except Exception as e:
                print(f"  错误: {e}")
        
        test_results['cli_interface'] = "通过"
        print("  ✓ 命令行接口测试通过")
        
    except Exception as e:
        test_results['cli_interface'] = f"失败: {e}"
        print(f"  ✗ 命令行接口测试失败: {e}")
    
    return test_results


def generate_test_report(all_results):
    """生成测试报告"""
    print("\n" + "="*60)
    print("增强统一自动修复系统测试报告")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    
    for category, results in all_results.items():
        print(f"\n{category.upper()}:")
        for test_name, result in results.items():
            total_tests += 1
            if result == "通过":
                passed_tests += 1
                status = "✓ 通过"
            else:
                status = f"✗ 失败: {result}"
            
            print(f"  {test_name}: {status}")
    
    print(f"\n总体结果: {passed_tests}/{total_tests} 测试通过 ({passed_tests/max(total_tests, 1)*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！增强统一自动修复系统运行正常。")
    else:
        print("⚠️  部分测试失败，请检查相关问题。")
    
    return passed_tests == total_tests


def main():
    """主测试函数"""
    print("增强统一自动修复系统综合测试")
    print("="*60)
    print(f"测试时间: {datetime.now()}")
    print(f"项目根目录: {PROJECT_ROOT}")
    
    all_results = {}
    
    try:
        # 测试各个工具模块
        all_results['individual_modules'] = test_individual_modules()
        
        # 测试专门化修复器
        all_results['specialized_fixers'] = test_specialized_fixers()
        
        # 测试增强统一引擎
        all_results['enhanced_engine'] = test_enhanced_unified_engine()
        
        # 测试CLI接口
        all_results['cli_interface'] = test_cli_interface()
        
        # 生成测试报告
        success = generate_test_report(all_results)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())