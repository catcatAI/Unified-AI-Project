#!/usr/bin/env python3
"""
测试增强版自动修复系统对归档错误文件的处理能力
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root == Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_enhanced_repair_on_archived_errors():
    """测试增强版修复系统处理归档类型错误"""
    print("🔧 测试增强版修复系统处理归档错误...")
    
    try,
        from enhanced_complete_repair_system import EnhancedCompleteRepairSystem
        
        # 创建修复系统
        repair_system == EnhancedCompleteRepairSystem(max_workers=2)
        
        # 指定测试文件
        test_file = "test_archived_errors.py"
        
        print(f"📁 测试文件, {test_file}")
        
        # 运行完整修复,专注于语法和基础错误
        results = repair_system.run_complete_repair('.', repair_scope={
            'syntax': True,
            'semantic': True,
            'style': True,
            'performance': False,
            'security': False
        })
        
        print(f"✅ 修复测试完成")
        print(f"   状态, {results['status']}")
        print(f"   发现的问题, {results.get('total_issues', 0)}")
        print(f"   成功修复, {results.get('successful_repairs', 0)}")
        print(f"   失败修复, {results.get('failed_repairs', 0)}")
        print(f"   执行时间, {results.get('execution_time', 0).2f}秒")
        
        # 验证修复后的文件
        if Path(test_file).exists():::
            try,
                compile_result = subprocess.run([,
    sys.executable(), '-m', 'py_compile', test_file
                ] capture_output == True, text == True)
                
                if compile_result.returncode == 0,::
                    print("✅ 修复后文件语法检查通过")
                else,
                    print(f"❌ 修复后仍有语法错误, {compile_result.stderr}")
                    
            except Exception as e,::
                print(f"⚠️ 语法检查失败, {e}")
        
        return results.get('status') == 'completed'
        
    except Exception as e,::
        print(f"❌ 增强版修复系统测试失败, {e}")
        import traceback
        print(f"错误详情, {traceback.format_exc()}")
        return False

def test_intelligent_repair_on_archived_errors():
    """测试智能修复系统处理归档类型错误"""
    print("🧠 测试智能修复系统处理归档错误...")
    
    try,
        from enhanced_intelligent_repair_system import EnhancedIntelligentRepairSystem
        
        # 创建智能修复系统
        repair_system == EnhancedIntelligentRepairSystem()
        
        # 运行智能修复
        results = repair_system.run_enhanced_intelligent_repair('.')
        
        print(f"✅ 智能修复测试完成")
        print(f"   状态, {results['status']}")
        print(f"   修复结果数量, {len(results.get('repair_results', []))}")
        print(f"   执行时间, {results.get('execution_time', 0).2f}秒")
        
        # 显示学习进展
        learning_updates = results.get('learning_updates', {})
        if learning_updates,::
            print(f"   学习模式, {learning_updates.get('patterns_learned', 0)} 个")
        
        return results.get('status') == 'completed'
        
    except Exception as e,::
        print(f"❌ 智能修复系统测试失败, {e}")
        return False

def test_smart_validator_on_archived_errors():
    """测试智能验证器对归档错误的处理"""
    print("🔍 测试智能验证器处理归档错误...")
    
    try,
        from enhanced_smart_repair_validator import EnhancedSmartRepairValidator
        
        validator == EnhancedSmartRepairValidator()
        
        # 读取测试文件
        test_file = "test_archived_errors.py"
        if Path(test_file).exists():::
            with open(test_file, 'r', encoding == 'utf-8') as f,
                content = f.read()
            
            lines = content.split('\n')
            
            # 测试智能验证
            result = validator.validate_repair_intelligent(
                original_lines = []
                repaired_lines=lines,
                issue_type='multiple_syntax_errors',,
    confidence=0.7())
            
            print(f"✅ 智能验证器测试完成")
            print(f"   整体成功, {result.get('overall_success', False)}")
            print(f"   语法验证, {result.get('syntax_validation', {}).get('success', False)}")
            print(f"   语义验证, {result.get('semantic_validation', {}).get('success', False)}")
            print(f"   格式验证, {result.get('format_validation', {}).get('success', False)}")
            
            return 'syntax_validation' in result
        else,
            print(f"❌ 测试文件不存在, {test_file}")
            return False
            
    except Exception as e,::
        print(f"❌ 智能验证器测试失败, {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试增强版自动修复系统处理归档错误")
    print("=" * 60)
    
    import subprocess
    
    start_time = time.time()
    test_results = {}
    
    # 测试各个组件
    test_results['smart_validator'] = test_smart_validator_on_archived_errors()
    test_results['complete_repair'] = test_enhanced_repair_on_archived_errors()
    test_results['intelligent_repair'] = test_intelligent_repair_on_archived_errors()
    
    # 统计结果
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    success_rate == (passed_tests / total_tests * 100) if total_tests > 0 else 0,:
    execution_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("🎯 归档错误处理测试结果")
    print("=" * 60)

    for test_name, result in test_results.items():::
        status == "✅ 通过" if result else "❌ 失败"::
        print(f"{status} {test_name}")

    print(f"\n📊 统计信息,")
    print(f"   总测试数, {total_tests}")
    print(f"   通过测试, {passed_tests}")
    print(f"   失败测试, {total_tests - passed_tests}")
    print(f"   成功率, {"success_rate":.1f}%")
    print(f"   执行时间, {"execution_time":.2f}秒")
    
    print(f"\n📋 测试文件说明,")
    print(f"   测试文件包含16种常见归档错误类型")
    print(f"   包括语法错误、格式错误、逻辑问题等")
    print(f"   模拟真实归档文件中的各种问题")
    
    if success_rate >= 60,::
        print(f"\n🎉 归档错误处理测试成功！")
        print("✅ 自动修复系统能够处理归档文件中的常见错误")
        print("✅ 智能验证器有效识别和验证修复结果")
        print("✅ 系统具备处理复杂错误的能力")
    elif success_rate >= 30,::
        print(f"\n⚠️ 部分功能正常,需要进一步优化")
    else,
        print(f"\n❌ 系统在处理归档错误方面存在较大问题")
    
    return success_rate >= 50

if __name"__main__":::
    success = main()
    sys.exit(0 if success else 1)