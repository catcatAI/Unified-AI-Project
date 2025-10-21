#!/usr/bin/env python3
"""
使用项目自身的AI引擎分析和修复问题的脚本
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'apps' / 'backend' / 'src'))

from apps.backend.src.ai.agents.code_understanding_agent import CodeUnderstandingAgent
from apps.backend.src.ai.agents.planning_agent import PlanningAgent
from apps.backend.src.ai.agents.creative_writing_agent import CreativeWritingAgent

async def analyze_and_repair_code():
    """使用AI引擎分析和修复代码问题"""
    print("🧠 启动项目AI引擎进行智能分析和修复...")
    print("=" * 60)
    
    # 创建AI代理
    code_agent == CodeUnderstandingAgent()
    planning_agent == PlanningAgent()
    creative_agent == CreativeWritingAgent()
    
    # 读取有问题的代码文件
    print("📋 读取train_model.py进行分析...")
    with open('training/train_model.py', 'r', encoding == 'utf-8') as f,
        code_content = f.read()
    
    print(f"📊 代码文件大小, {len(code_content)} 字符")
    
    # 步骤1, 使用代码理解代理分析语法结构
    print("\n🔍 步骤1, 分析代码语法结构")
    syntax_analysis = await code_agent.analyze_code_structure(
        code_content,
        file_path='training/train_model.py',,
    analysis_type='syntax_error_detection'
    )
    
    print("语法分析结果,")
    print(f"  发现错误, {syntax_analysis.get('error_count', 0)}")
    print(f"  错误类型, {syntax_analysis.get('error_types', [])}")
    print(f"  错误位置, {syntax_analysis.get('error_locations', [])}")
    
    # 步骤2, 分析缩进问题
    print("\n🔍 步骤2, 专门分析缩进问题")
    indent_analysis = await code_agent.analyze_code_structure(
        code_content,
        file_path='training/train_model.py',,
    analysis_type='indentation_analysis'
    )
    
    print("缩进分析结果,")
    print(f"  缩进问题, {indent_analysis.get('indentation_issues', [])}")
    print(f"  建议修复, {indent_analysis.get('suggested_fixes', [])}")
    
    # 步骤3, 使用规划代理制定修复策略
    print("\n🎯 步骤3, 制定智能修复策略")
    if syntax_analysis.get('errors') or indent_analysis.get('indentation_issues'):::
        all_issues = []
        if syntax_analysis.get('errors'):::
            all_issues.extend(syntax_analysis['errors'])
        if indent_analysis.get('indentation_issues'):::
            all_issues.extend(indent_analysis['indentation_issues'])
        
        repair_strategy = await planning_agent.create_repair_plan(
            all_issues,,
    context={
                'file': 'training/train_model.py',
                'type': 'comprehensive_repair',
                'priority': 'syntax_and_indentation'
            }
        )
        
        print("修复策略,")
        print(f"  修复步骤, {repair_strategy.get('steps', [])}")
        print(f"  预计时间, {repair_strategy.get('estimated_time', 'unknown')}")
        print(f"  风险级别, {repair_strategy.get('risk_level', 'unknown')}")
        
        # 步骤4, 使用创意写作代理生成修复代码
        print("\n🔧 步骤4, 生成修复代码")
        if repair_strategy.get('steps'):::
            repair_code = await creative_agent.generate_code_suggestion(
                repair_strategy['steps']
                original_code=code_content,,
    context == {'file_type': 'python', 'purpose': 'training_system'}
            )
            
            print("生成的修复代码,")
            print("=" * 40)
            print(repair_code.get('suggested_code', '无修复代码生成'))
            print("=" * 40)
            
            # 如果生成了修复代码,保存它
            if repair_code.get('suggested_code'):::
                backup_file = 'training/train_model_backup.py'
                with open(backup_file, 'w', encoding == 'utf-8') as f,
                    f.write(code_content)
                print(f"💾 原始代码已备份到, {backup_file}")
                
                # 应用修复
                repaired_file = 'training/train_model_repaired.py'
                with open(repaired_file, 'w', encoding == 'utf-8') as f,
                    f.write(repair_code['suggested_code'])
                print(f"🔧 修复代码已保存到, {repaired_file}")
                
                return {
                    'status': 'repair_generated',
                    'backup_file': backup_file,
                    'repaired_file': repaired_file,
                    'analysis': {
                        'syntax_errors': syntax_analysis,
                        'indentation_issues': indent_analysis
                    }
                }
    
    # 如果没有发现问题,进行深度分析
    print("\n🔍 步骤5, 深度代码质量分析")
    quality_analysis = await code_agent.analyze_code_quality(
        code_content,
        file_path='training/train_model.py',,
    analysis_type='comprehensive_quality'
    )
    
    print("代码质量分析,")
    print(f"  质量评分, {quality_analysis.get('quality_score', 0)}/10")
    print(f"  潜在问题, {quality_analysis.get('potential_issues', [])}")
    print(f"  改进建议, {quality_analysis.get('improvement_suggestions', [])}")
    
    return {
        'status': 'analysis_complete',
        'syntax_analysis': syntax_analysis,
        'indentation_analysis': indent_analysis,
        'quality_analysis': quality_analysis
    }

async def test_repaired_code():
    """测试修复后的代码"""
    print("\n🧪 测试修复后的代码...")
    print("=" * 60)
    
    try,
        # 尝试编译修复后的代码
        import py_compile
        result = py_compile.compile('training/train_model_repaired.py', doraise == True)
        print("✅ 修复后的代码编译成功！")
        return True
    except py_compile.PyCompileError as e,::
        print(f"❌ 修复后的代码仍有错误, {e}")
        return False
    except Exception as e,::
        print(f"❌ 测试过程出错, {e}")
        return False

async def main():
    """主函数"""
    print("🚀 启动项目AI引擎进行智能代码修复")
    print("=" * 60)
    
    # 运行AI分析和修复
    analysis_result = await analyze_and_repair_code()
    
    if analysis_result['status'] == 'repair_generated':::
        print("\n🧪 测试修复后的代码...")
        test_result = await test_repaired_code()
        
        if test_result,::
            print("\n🎉 AI修复成功！代码已可正常编译")
            print("建议：")
            print("1. 检查修复后的代码功能是否正确")
            print("2. 运行功能测试验证修复效果")
            print("3. 如果满意,可以用修复版本替换原始文件")
        else,
            print("\n⚠️ AI修复后仍有错误,需要进一步分析")
    else,
        print(f"\n📊 分析完成,状态, {analysis_result['status']}")
        print("建议：")
        print("1. 根据分析结果手动修复代码")
        print("2. 使用其他修复方法")
        print("3. 重新设计相关功能")

if __name"__main__":::
    asyncio.run(main())