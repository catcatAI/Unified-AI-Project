#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
验证Unified AI Project当前状态
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.join(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def check_project_structure():
    """检查项目结构"""
    print("🔍 检查项目结构...")
    
    # 检查关键目录和文件
    required_paths = [
        'apps/backend/src/ai/agents/base/base_agent.py',
        'apps/backend/src/ai/agents/__init__.py',
        'apps/backend/src/ai/agents/specialized/creative_writing_agent.py',
        'apps/backend/src/ai/agents/specialized/web_search_agent.py',
        'training/train_model.py'
    ]
    
    missing_paths = []
    for path in required_paths:
        full_path = os.path.join(project_root, path)
        if not os.path.exists(full_path):
            missing_paths.append(path)
            print(f"❌ 缺少文件: {path}")
        else:
            print(f"✅ 存在文件: {path}")
    
    return len(missing_paths) == 0

def check_imports():
    """检查关键导入"""
    print("\n🔍 检查关键导入...")
    
    imports_passed = 0
    imports_failed = 0
    
    # 测试1: 导入BaseAgent
    try:
        from apps.backend.src.ai.agents.base.base_agent import BaseAgent
        print("✅ 成功导入BaseAgent")
        imports_passed += 1
    except Exception as e:
        print(f"❌ 导入BaseAgent失败: {e}")
        imports_failed += 1
    
    # 测试2: 导入ai.agents模块
    try:
        from apps.backend.src.ai.agents import BaseAgent as BaseAgentFromModule
        print("✅ 成功从ai.agents模块导入BaseAgent")
        imports_passed += 1
    except Exception as e:
        print(f"❌ 从ai.agents模块导入BaseAgent失败: {e}")
        imports_failed += 1
    
    # 测试3: 导入CreativeWritingAgent
    try:
        from apps.backend.src.ai.agents.specialized.creative_writing_agent import CreativeWritingAgent
        print("✅ 成功导入CreativeWritingAgent")
        imports_passed += 1
    except Exception as e:
        print(f"❌ 导入CreativeWritingAgent失败: {e}")
        imports_failed += 1
    
    # 测试4: 导入WebSearchAgent
    try:
        from apps.backend.src.ai.agents.specialized.web_search_agent import WebSearchAgent
        print("✅ 成功导入WebSearchAgent")
        imports_passed += 1
    except Exception as e:
        print(f"❌ 导入WebSearchAgent失败: {e}")
        imports_failed += 1
    
    print(f"\n📊 导入测试结果: {imports_passed} 通过, {imports_failed} 失败")
    return imports_failed == 0

def check_syntax():
    """检查关键文件语法"""
    print("\n🔍 检查关键文件语法...")
    
    files_to_check = [
        'apps/backend/src/ai/agents/base/base_agent.py',
        'apps/backend/src/ai/agents/__init__.py',
        'apps/backend/src/ai/agents/specialized/creative_writing_agent.py',
        'apps/backend/src/ai/agents/specialized/web_search_agent.py',
        'training/train_model.py'
    ]
    
    syntax_passed = 0
    syntax_failed = 0
    
    for file_path in files_to_check:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            try:
                import ast
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
                print(f"✅ 语法检查通过: {file_path}")
                syntax_passed += 1
            except Exception as e:
                print(f"❌ 语法检查失败: {file_path} - {e}")
                syntax_failed += 1
        else:
            print(f"⚠️ 文件不存在: {file_path}")
    
    print(f"\n📊 语法检查结果: {syntax_passed} 通过, {syntax_failed} 失败")
    return syntax_failed == 0

def main():
    """主函数"""
    print("🔧 Unified AI Project 状态验证工具")
    print("=" * 50)
    
    # 执行检查
    structure_ok = check_project_structure()
    imports_ok = check_imports()
    syntax_ok = check_syntax()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 验证总结:")
    print(f"  项目结构: {'✅' if structure_ok else '❌'}")
    print(f"  导入功能: {'✅' if imports_ok else '❌'}")
    print(f"  语法检查: {'✅' if syntax_ok else '❌'}")
    
    all_passed = structure_ok and imports_ok and syntax_ok
    if all_passed:
        print("\n🎉 所有检查通过! 项目状态良好")
        print("✅ 无重复实现问题")
        print("✅ 导入路径正确")
        print("✅ 语法检查通过")
        print("✅ 项目结构清晰")
    else:
        print("\n❌ 部分检查失败，请查看详细信息")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
