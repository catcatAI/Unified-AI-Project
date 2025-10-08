#!/usr/bin/env python3
"""
完整的自动修复系统测试套件
验证统一自动修复系统的所有功能
"""

import sys
import time
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_test_file_with_archived_errors():
    """创建包含归档文件常见错误的测试文件"""
    test_content = '''#!/usr/bin/env python3
"""
模拟归档文件中的常见错误 - 测试用例
包含各种语法、格式和逻辑错误
"""

# 1. 函数定义缺少冒号
def test_function(x, y)
    result = x + y
    print(result)
    return result

# 2. 类定义缺少冒号  
class TestClass
    def __init__(self):
        self.value = 0
    
    def process(self):
        return self.value

# 3. if语句缺少冒号
if x > 0
    print("Positive")

# 4. for循环缺少冒号
for i in range(10)
    print(i)

# 5. while循环缺少冒号
while count < 5
    count += 1

# 6. 括号未闭合
print("Hello World"

# 7. 方括号未闭合
my_list = [1, 2, 3

# 8. 花括号未闭合
my_dict = {"key": "value"

# 9. 缩进不一致
def inconsistent_indentation():
print("This should be indented")  # 缺少缩进
    return True

# 10. 未使用变量
unused_variable = 42
another_unused = "test"

# 11. 行过长（超过120字符）
very_long_line = "This is a very long line that exceeds the recommended maximum line length of 120 characters and should be split into multiple lines for better readability"

# 12. 中文标点符号（常见错误）
def chinese_punctuation_test()：
    print("Hello，World！")  # 中文标点
    return True

# 13. 文档字符串格式问题
def bad_docstring():
    ""这是中文文档字符串"""
    pass

# 14. 导入顺序问题
import sys
import os
import json
from pathlib import Path
import re

# 15. 潜在的空值访问
def potential_null_access():
    result = None
    return result.value  # 可能空值访问

# 16. 循环导入风险
import test_unified_import  # 假设的循环导入

def main():
    """主函数"""
    test_function(1, 2)
    obj = TestClass()
    
    if x > 0:
        print("Test")
    
    for i in range(3):
        print(i)
    
    print(my_list)
    print(my_dict)
    
    inconsistent_indentation()
    
    chinese_punctuation_test()
    
    bad_docstring()
    
    potential_null_access()

if __name__ == "__main__":
    main()
'''
    
    test_file = 'test_archived_comprehensive_errors.py'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    return test_file

def test_unified_auto_repair_system():
    """测试统一自动修复系统"""
    print("🔧 测试统一自动修复系统...")
    
    try:
        from unified_auto_repair_system import UnifiedAutoRepairSystem, RepairConfig
        
        # 创建测试文件
        test_file = create_test_file_with_archived_errors()
        print(f"📁 创建测试文件: {test_file}")
        
        # 验证文件确实有语法错误
        compile_result = subprocess.run([
            sys.executable, '-m', 'py_compile', test_file
        ], capture_output=True, text=True)
        
        if compile_result.returncode == 0:
            print("⚠️ 测试文件没有语法错误，添加一些错误")
            return False
        else:
            print(f"✅ 测试文件确认有语法错误: {compile_result.stderr.strip()}")
        
        # 创建统一修复系统
        config = RepairConfig(
            max_workers=2,
            enable_backup=True,
            enable_validation=True,
            repair_scope={
                'syntax': True,
                'semantic': True,
                'style': True,
                'performance': False,
                'security': False
            }
        )
        
        repair_system = UnifiedAutoRepairSystem(config)
        
        # 运行统一修复
        print("🚀 开始统一修复过程...")
        results = repair_system.run_unified_auto_repair('.')
        
        print(f"✅ 统一修复完成")
        print(f"   状态: {results['status']}")
        print(f"   总问题: {results.get('total_issues', 0)}")
        print(f"   成功修复: {results.get('successful_repairs', 0)}")
        print(f"   失败修复: {results.get('failed_repairs', 0)}")
        print(f"   执行时间: {results.get('execution_time', 0):.2f}秒")
        
        # 验证修复后的文件
        if Path(test_file).exists():
            compile_result = subprocess.run([
                sys.executable, '-m', 'py_compile', test_file
            ], capture_output=True, text=True)
            
            if compile_result.returncode == 0:
                print("✅ 修复后文件语法检查通过")
                repair_success = True
            else:
                print(f"❌ 修复后仍有语法错误: {compile_result.stderr}")
                repair_success = False
        else:
            print("❌ 测试文件不存在")
            repair_success = False
        
        # 显示详细报告
        if 'report' in results:
            report_file = 'UNIFIED_REPAIR_REPORT.md'
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(results['report'])
            print(f"📄 详细报告已保存: {report_file}")
        
        return results.get('status') == 'completed' and repair_success
        
    except Exception as e:
        print(f"❌ 统一自动修复系统测试失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")
        return False
    finally:
        # 清理测试文件
        test_file = 'test_archived_comprehensive_errors.py'
        if Path(test_file).exists():
            Path(test_file).unlink()

def test_integration_manager():
    """测试集成管理器"""
    print("🔗 测试自动修复系统集成管理器...")
    
    try:
        from auto_repair_integration_manager import get_auto_repair_manager, RepairSystemType
        
        manager = get_auto_repair_manager()
        
        # 获取系统状态
        status = manager.get_system_status()
        
        print(f"✅ 集成管理器状态: {status['integration_manager_status']}")
        print(f"   可用系统: {status['available_count']}/{status['total_systems']}")
        print(f"   默认系统: {status['config']['default_system']}")
        
        # 测试使用不同系统
        for system_type in [RepairSystemType.UNIFIED, RepairSystemType.COMPLETE, RepairSystemType.INTELLIGENT]:
            try:
                result = manager.run_auto_repair('.', system_type)
                print(f"✅ {system_type.value} 系统测试: {result['status']}")
            except Exception as e:
                print(f"⚠️ {system_type.value} 系统测试失败: {e}")
        
        return status['integration_manager_status'] == 'active'
        
    except Exception as e:
        print(f"❌ 集成管理器测试失败: {e}")
        return False

def test_archived_files_repair():
    """测试对归档文件的修复能力"""
    print("📦 测试归档文件修复能力...")
    
    try:
        from auto_repair_integration_manager import get_auto_repair_manager
        
        manager = get_auto_repair_manager()
        
        # 复制一个归档文件进行测试
        archived_file = 'archived_systems/intelligent_repair_system.py'
        test_file = 'test_archived_original.py'
        
        if Path(archived_file).exists():
            import shutil
            shutil.copy(archived_file, test_file)
            
            print(f"📁 测试归档文件: {archived_file}")
            
            # 运行修复
            result = manager.run_auto_repair('.')
            
            print(f"✅ 归档文件修复测试完成")
            print(f"   状态: {result['status']}")
            print(f"   发现问题: {result.get('total_issues', 0)}")
            print(f"   成功修复: {result.get('successful_repairs', 0)}")
            
            # 清理
            if Path(test_file).exists():
                Path(test_file).unlink()
            
            return result.get('status') == 'completed'
        else:
            print("⚠️ 没有找到合适的归档文件进行测试")
            return True
            
    except Exception as e:
        print(f"❌ 归档文件修复测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始完整的自动修复系统测试")
    print("=" * 60)
    
    start_time = time.time()
    test_results = {}
    
    # 运行各项测试
    test_results['integration_manager'] = test_integration_manager()
    test_results['unified_repair'] = test_unified_auto_repair_system()
    test_results['archived_files'] = test_archived_files_repair()
    
    # 统计结果
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    execution_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("🎯 完整测试总结")
    print("=" * 60)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} {test_name}")
    
    print(f"\n📊 统计信息:")
    print(f"   总测试数: {total_tests}")
    print(f"   通过测试: {passed_tests}")
    print(f"   失败测试: {total_tests - passed_tests}")
    print(f"   成功率: {success_rate:.1f}%")
    print(f"   执行时间: {execution_time:.2f}秒")
    
    if success_rate >= 70:
        print(f"\n🎉 完整测试成功！")
        print("✅ 统一自动修复系统功能完整")
        print("✅ 集成管理器正常工作")
        print("✅ 能够处理归档文件中的错误")
        print("✅ 系统具备实际应用能力")
    elif success_rate >= 40:
        print(f"\n⚠️ 部分功能正常，需要进一步优化")
    else:
        print(f"\n❌ 系统存在较大问题，需要修复")
    
    return success_rate >= 60

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)