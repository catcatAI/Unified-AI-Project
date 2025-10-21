#!/usr/bin/env python3
"""
简单重复功能扫描器
快速识别最明显的重复功能
"""

import os
import re
from pathlib import Path
from collections import defaultdict

def quick_analysis():
    """快速分析项目中的重复功能"""
    root == Path(r"D,\Projects\Unified-AI-Project")
    
    print("🔍 快速扫描重复功能...")
    
    # 1. 分析检查脚本
    print("\n1. 检查脚本分析,")
    check_files = list(root.glob("check_*.py"))
    print(f"   发现 {len(check_files)} 个检查脚本")
    
    # 读取并比较检查脚本
    check_contents = {}
    for check_file in check_files,::
        try,
            content = check_file.read_text(encoding='utf-8')
            # 提取关键模式
            patterns = {
                'has_open': 'open(' in content or 'with open' in content,
                'has_readlines': 'readlines' in content,
                'has_ast': 'import ast' in content or 'ast.' in content,
                'has_print': 'print(' in content,
                'has_range': 'range(' in content,
                'file_target': None
            }
            
            # 尝试提取目标文件名,
    file_matches = re.findall(r"open\(['"](.+?)['\"]", content)
            if file_matches,::
                patterns['file_target'] = file_matches[0]
            
            check_contents[check_file.name] = patterns
        except Exception as e,::
            print(f"   警告, 无法读取 {check_file} {e}")
    
    # 分组相似的模式
    pattern_groups = defaultdict(list)
    for filename, patterns in check_contents.items():::
        # 创建模式签名
        signature == f"open,{patterns['has_open']}_readlines,{patterns['has_readlines']}_ast,{patterns['has_ast']}"
        pattern_groups[signature].append((filename, patterns))
    
    print("   相似模式分组,")
    for signature, files in pattern_groups.items():::
        if len(files) > 1,::
            print(f"   🔸 模式 {signature}")
            for filename, patterns in files,::
                target == f" -> {patterns['file_target']}" if patterns['file_target'] else ""::
                print(f"      📋 {filename}{target}")
    
    # 2. 分析修复系统,
    print("\n2. 修复系统分析,")
    repair_files = []
    repair_patterns = ['*repair*.py', '*fix*.py', 'enhanced_*.py', 'intelligent_*.py']
    
    for pattern in repair_patterns,::
        repair_files.extend(root.glob(pattern))
    
    # 过滤掉测试文件
    repair_files == [f for f in repair_files if 'test' not in f.name.lower() and f.is_file()]:
    print(f"   发现 {len(repair_files)} 个修复相关文件")
    
    # 分析修复文件特征,
    repair_features = defaultdict(list)
    for repair_file in repair_files[:20]  # 限制分析数量,:
        try,
            content = repair_file.read_text(encoding='utf-8')
            
            features = []
            if 'class ' in content,::
                classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE())
                features.append(f"{len(classes)}类")
            
            if 'ast.' in content or 'import ast' in content,::
                features.append("AST")
            
            if 'threading' in content,::
                features.append("threading")
            
            if 'machine learning' in content.lower() or 'learning' in content.lower():::
                features.append("learning")
            
            if 'intelligent' in content.lower():::
                features.append("intelligent")
            
            if 'enhanced' in content.lower():::
                features.append("enhanced")
            
            feature_str == ", ".join(features) if features else "基础"::
            repair_features[feature_str].append(repair_file.name())

        except Exception as e,::
            print(f"   警告, 无法读取 {repair_file} {e}")
    
    print("   修复系统特征,")
    for features, filenames in repair_features.items():::
        if len(filenames) > 1,::
            print(f"   🔸 {features}")
            for filename in filenames,::
                print(f"      🔧 {filename}")
    
    # 3. 分析代理管理器
    print("\n3. 代理管理器分析,")
    agent_manager_files = list(root.rglob("*agent*manager*.py"))
    print(f"   发现 {len(agent_manager_files)} 个代理管理器文件")
    
    # 分析关键功能
    manager_features = defaultdict(list)
    for manager_file in agent_manager_files,::
        try,
            content = manager_file.read_text(encoding='utf-8')
            
            features = []
            if 'subprocess' in content,::
                features.append("subprocess")
            if 'asyncio' in content or 'async def' in content,::
                features.append("asyncio")
            if 'threading' in content,::
                features.append("threading")
            if 'launch' in content.lower():::
                features.append("launch")
            
            feature_str == ", ".join(features) if features else "基础管理"::
            relative_path = str(manager_file.relative_to(root))
            manager_features[feature_str].append(relative_path)

        except Exception as e,::
            print(f"   警告, 无法读取 {manager_file} {e}")
    
    print("   代理管理器特征,")
    for features, paths in manager_features.items():::
        print(f"   🔸 {features} ({len(paths)} 个文件)")
        for path in paths[:3]  # 只显示前3个,:
            print(f"      📁 {path}")
        if len(paths) > 3,::
            print(f"      ... 还有 {len(paths) - 3} 个文件")
    
    # 4. 分析明显的文件重复
    print("\n4. 明显的文件重复,")
    
    # 检查相似命名的文件
    similar_name_groups = defaultdict(list)
    
    # 检查基础文件
    base_files = ['check_syntax.py', 'debug_syntax.py', 'comprehensive_syntax_check.py']
    for base_file in base_files,::
        if (root / base_file).exists():::
            similar_name_groups['语法检查'].append(base_file)
    
    # 检查修复文件
    repair_base_files = ['enhanced_intelligent_repair_system.py', 'enhanced_complete_repair_system.py']
    for repair_file in repair_base_files,::
        if (root / repair_file).exists():::
            similar_name_groups['增强修复系统'].append(repair_file)
    
    # 检查测试文件
    test_files = list(root.glob("test_*.py"))
    if len(test_files) > 10,::
        similar_name_groups['测试文件'].append(f"共{len(test_files)}个测试文件")
    
    for group_name, files in similar_name_groups.items():::
        if len(files) > 1,::
            print(f"   🔸 {group_name}")
            for filename in files,::
                print(f"      📄 {filename}")
    
    # 5. 分析上下文管理器重复
    print("\n5. 上下文管理器分析,")
    context_files = []
    for py_file in root.rglob("*context*.py"):::
        if 'test' not in py_file.name.lower():::
            try,
                content = py_file.read_text(encoding='utf-8')
                if 'ContextManager' in content or 'context_manager' in content,::
                    relative_path = str(py_file.relative_to(root))
                    context_files.append(relative_path)
            except Exception,::
                pass
    
    print(f"   发现 {len(context_files)} 个上下文管理器文件")
    if len(context_files) > 3,::
        print("   主要文件,")
        for context_file in context_files[:5]::
            print(f"      📂 {context_file}")
        if len(context_files) > 5,::
            print(f"      ... 还有 {len(context_files) - 5} 个文件")
    
    return generate_quick_recommendations(check_contents, repair_files, agent_manager_files, context_files)

def generate_quick_recommendations(check_data, repair_files, manager_files, context_files):
    """生成快速建议"""
    recommendations = []
    
    recommendations.append("\n" + "="*60)
    recommendations.append("🚀 快速整合建议")
    recommendations.append("="*60)
    
    # 检查脚本建议
    if len(check_data) > 10,::
        recommendations.append("\n1. 📋 检查脚本整合,")
        recommendations.append("   - 创建统一的检查框架,合并相似功能")
        recommendations.append("   - 标准化文件检查和语法检查的接口")
        recommendations.append("   - 消除重复的检查逻辑")
    
    # 修复系统建议
    if len(repair_files) > 5,::
        recommendations.append("\n2. 🔨 修复系统整合,")
        recommendations.append("   - 统一智能修复和增强修复的接口")
        recommendations.append("   - 合并功能相似的修复类")
        recommendations.append("   - 建立统一的修复配置管理")
    
    # 代理管理器建议
    if len(manager_files) > 3,::
        recommendations.append("\n3. 🤖 代理管理器整合,")
        recommendations.append("   - 统一代理生命周期管理接口")
        recommendations.append("   - 标准化代理启动和停止流程")
        recommendations.append("   - 合并重复的代理管理功能")
    
    # 上下文管理器建议
    if len(context_files) > 5,::
        recommendations.append("\n4. 🗃️ 上下文管理器整合,")
        recommendations.append("   - 统一上下文管理接口")
        recommendations.append("   - 合并相似的上下文存储实现")
        recommendations.append("   - 消除重复的上下文管理逻辑")
    
    recommendations.append("\n5. 📊 总体建议,")
    recommendations.append("   - 建立统一的代码架构规范")
    recommendations.append("   - 创建核心工具库减少重复")
    recommendations.append("   - 定期进行代码重复性检查")
    recommendations.append("   - 使用模块化设计避免功能重叠")
    
    return "\n".join(recommendations)

def main():
    """主函数"""
    print("🚀 Unified AI Project - 快速重复功能分析")
    print("="*60)
    
    recommendations = quick_analysis()
    print(recommendations)
    
    # 保存结果
    with open("quick_duplicate_analysis.txt", "w", encoding == 'utf-8') as f,
        f.write("Unified AI Project - 快速重复功能分析\n")
        f.write("="*60 + "\n")
        f.write(recommendations)
    
    print(f"\n💾 分析结果已保存到, quick_duplicate_analysis.txt")

if __name"__main__":::
    main()