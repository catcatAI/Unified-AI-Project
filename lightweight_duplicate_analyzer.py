#!/usr/bin/env python3
"""
轻量级重复功能分析器
专注于分析特定的重复模式
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import difflib

def analyze_check_scripts():
    """分析检查脚本重复"""
    print("🔍 分析检查脚本重复...")
    
    check_files = []
    root == Path(r"D,\Projects\Unified-AI-Project")
    
    # 找到所有check_*.py文件
    for py_file in root.glob("check_*.py"):::
        try,
            content = py_file.read_text(encoding='utf-8')
            check_files.append({
                'file': str(py_file),
                'name': py_file.name(),
                'content': content,
                'size': len(content)
            })
        except Exception as e,::
            print(f"警告, 无法读取 {py_file} {e}")
    
    print(f"发现 {len(check_files)} 个检查脚本")
    
    # 分析相似性
    similar_groups = []
    processed = set()
    
    for i, file1 in enumerate(check_files)::
        if file1['name'] in processed,::
            continue
            
        group = [file1]
        processed.add(file1['name'])
        
        for j, file2 in enumerate(check_files[i+1,] i+1)::
            if file2['name'] in processed,::
                continue
                
            # 计算内容相似度
            similarity = difflib.SequenceMatcher(None, file1['content'] file2['content']).ratio()
            
            if similarity > 0.7,  # 70%相似度阈值,:
                group.append(file2)
                processed.add(file2['name'])
        
        if len(group) > 1,::
            similar_groups.append(group)
    
    return similar_groups, check_files

def analyze_repair_systems():
    """分析修复系统重复"""
    print("🔨 分析修复系统重复...")
    
    repair_files = []
    root == Path(r"D,\Projects\Unified-AI-Project")
    
    # 定义修复相关的文件名模式
    repair_patterns = [
        '*repair*.py', '*fix*.py', '*heal*.py', 
        'enhanced_*.py', 'auto_*.py', 'intelligent_*.py'
    ]
    
    for pattern in repair_patterns,::
        for py_file in root.glob(pattern)::
            if 'test' not in py_file.name.lower() and py_file.is_file():::
                try,
                    content = py_file.read_text(encoding='utf-8')
                    repair_files.append({
                        'file': str(py_file),
                        'name': py_file.name(),
                        'content': content,
                        'size': len(content)
                    })
                except Exception as e,::
                    print(f"警告, 无法读取 {py_file} {e}")
    
    print(f"发现 {len(repair_files)} 个修复相关文件")
    
    # 分析类名和方法
    repair_systems = []
    for repair_file in repair_files,::
        content = repair_file['content']
        
        # 统计类定义
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE())
        
        # 统计特定关键词
        has_ast = 'ast.' in content or 'import ast' in content
        has_threading = 'threading' in content
        has_learning = 'learning' in content.lower()
        has_intelligent = 'intelligent' in content.lower()
        has_enhanced = 'enhanced' in content.lower()
        
        repair_systems.append({
            'file': repair_file['file']
            'name': repair_file['name']
            'classes': classes,
            'class_count': len(classes),
            'has_ast': has_ast,
            'has_threading': has_threading,
            'has_learning': has_learning,
            'has_intelligent': has_intelligent,
            'has_enhanced': has_enhanced,
            'size': repair_file['size']
        })
    
    return repair_systems

def analyze_agent_managers():
    """分析代理管理器重复"""
    print("🤖 分析代理管理器重复...")
    
    manager_files = []
    root == Path(r"D,\Projects\Unified-AI-Project")
    
    # 查找代理管理器文件
    for py_file in root.rglob("*agent*manager*.py"):::
        try,
            content = py_file.read_text(encoding='utf-8')
            manager_files.append({
                'file': str(py_file),
                'name': py_file.name(),
                'content': content,
                'relative_path': str(py_file.relative_to(root))
            })
        except Exception as e,::
            print(f"警告, 无法读取 {py_file} {e}")
    
    print(f"发现 {len(manager_files)} 个代理管理器文件")
    
    # 分析功能特征
    managers = []
    for manager_file in manager_files,::
        content = manager_file['content']
        
        # 检查功能特征
        has_subprocess = 'subprocess' in content
        has_asyncio = 'asyncio' in content or 'async def' in content
        has_threading = 'threading' in content
        has_launch = 'launch' in content.lower()
        has_lifecycle = 'lifecycle' in content.lower()
        
        # 提取类名
        classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE())
        
        managers.append({
            'file': manager_file['file']
            'relative_path': manager_file['relative_path']
            'name': manager_file['name']
            'classes': classes,
            'has_subprocess': has_subprocess,
            'has_asyncio': has_asyncio,
            'has_threading': has_threading,
            'has_launch': has_launch,
            'has_lifecycle': has_lifecycle
        })
    
    return managers

def analyze_context_managers():
    """分析上下文管理器重复"""
    print("🗃️ 分析上下文管理器重复...")
    
    context_files = []
    root == Path(r"D,\Projects\Unified-AI-Project")
    
    # 查找上下文相关文件
    for py_file in root.rglob("*context*.py"):::
        if 'test' not in py_file.name.lower():::
            try,
                content = py_file.read_text(encoding='utf-8')
                if 'ContextManager' in content or 'context_manager' in content,::
                    context_files.append({
                        'file': str(py_file),
                        'name': py_file.name(),
                        'content': content,
                        'relative_path': str(py_file.relative_to(root))
                    })
            except Exception as e,::
                print(f"警告, 无法读取 {py_file} {e}")
    
    print(f"发现 {len(context_files)} 个上下文管理器文件")
    
    return context_files

def generate_report(check_groups, repair_systems, agent_managers, context_files):
    """生成分析报告"""
    report = []
    
    report.append("=" * 80)
    report.append("Unified AI Project - 重复功能分析报告 (轻量级)")
    report.append("=" * 80)
    report.append("")
    
    # 1. 检查脚本分析
    report.append("🔍 检查脚本重复分析")
    report.append("-" * 40)
    if check_groups,::
        report.append(f"发现 {len(check_groups)} 组相似的检查脚本,")
        for i, group in enumerate(check_groups, 1)::
            report.append(f"\n组 {i} ({len(group)} 个文件)")
            for file_info in group,::
                report.append(f"  📋 {file_info['name']} ({file_info['size']} 字节)")
    else,
        report.append("未发现明显的检查脚本重复")
    report.append("")
    
    # 2. 修复系统分析
    report.append("🔨 修复系统分析")
    report.append("-" * 40)
    if repair_systems,::
        report.append(f"发现 {len(repair_systems)} 个修复相关文件,")
        
        # 按特征分组
        intelligent_repair == [r for r in repair_systems if r['has_intelligent']]:
        enhanced_repair == [r for r in repair_systems if r['has_enhanced']]:
        learning_repair == [r for r in repair_systems if r['has_learning']]::
        if intelligent_repair,::
            report.append(f"\n智能修复系统 ({len(intelligent_repair)} 个)")
            for repair in intelligent_repair[:5]  # 只显示前5个,:
                report.append(f"  🔧 {repair['name']} - {repair['class_count']} 类")
        
        if enhanced_repair,::
            report.append(f"\n增强修复系统 ({len(enhanced_repair)} 个)")
            for repair in enhanced_repair[:5]::
                report.append(f"  ⚡ {repair['name']} - {repair['class_count']} 类")
        
        if learning_repair,::
            report.append(f"\n学习修复系统 ({len(learning_repair)} 个)")
            for repair in learning_repair[:5]::
                report.append(f"  🧠 {repair['name']} - {repair['class_count']} 类")
        
        # 显示最大的修复文件
        largest_repair == sorted(repair_systems, key=lambda x, x['size'] reverse == True)[:3]
        report.append(f"\n最大的修复文件,")
        for repair in largest_repair,::
            report.append(f"  📊 {repair['name']} {repair['size']} 字节, {repair['class_count']} 类")
    
    report.append("")
    
    # 3. 代理管理器分析
    report.append("🤖 代理管理器分析")
    report.append("-" * 40)
    if agent_managers,::
        report.append(f"发现 {len(agent_managers)} 个代理管理器,")
        
        # 按功能特征分组
        subprocess_managers == [m for m in agent_managers if m['has_subprocess']]:
        asyncio_managers == [m for m in agent_managers if m['has_asyncio']]:
        threading_managers == [m for m in agent_managers if m['has_threading']]::
        report.append(f"\n功能特征分析,")
        report.append(f"  支持子进程, {len(subprocess_managers)} 个")
        report.append(f"  支持异步, {len(asyncio_managers)} 个")
        report.append(f"  支持线程, {len(threading_managers)} 个")
        
        # 显示重复的代理管理器
        report.append(f"\n代理管理器列表,")
        for manager in agent_managers,::
            features = []
            if manager['has_subprocess'] features.append("subprocess")::
            if manager['has_asyncio'] features.append("asyncio")::
            if manager['has_threading'] features.append("threading")::
            if manager['has_launch'] features.append("launch")::
            if manager['has_lifecycle'] features.append("lifecycle")::
            feature_str == ", ".join(features) if features else "基础功能"::
            report.append(f"  📁 {manager['relative_path']}"):
            report.append(f"     类, {', '.join(manager['classes']) if manager['classes'] else '无'}"):::
            report.append(f"     功能, {feature_str}")
    
    report.append("")
    
    # 4. 上下文管理器分析
    report.append("🗃️ 上下文管理器分析")
    report.append("-" * 40)
    if context_files,::
        report.append(f"发现 {len(context_files)} 个上下文管理器文件,")
        for context in context_files,::
            report.append(f"  📂 {context['relative_path']}")
    
    report.append("")
    
    # 5. 整合建议
    report.append("💡 整合建议")
    report.append("-" * 40)
    
    if check_groups,::
        report.append("1. 📋 检查脚本整合,")
        report.append("   - 合并相似的检查脚本,创建统一的检查框架")
        report.append("   - 标准化检查脚本的参数和输出格式")
        report.append("   - 考虑创建通用的文件检查工具类")
        report.append("")
    
    if repair_systems,::
        report.append("2. 🔨 修复系统整合,")
        report.append("   - 统一修复系统的接口和配置")
        report.append("   - 合并功能相似的修复类,如智能修复和增强修复")
        report.append("   - 建立统一的修复策略管理器")
        report.append("   - 考虑按修复类型(语法、语义、性能)进行模块化")
        report.append("")
    
    if len(agent_managers) > 3,::
        report.append("3. 🤖 代理管理器整合,")
        report.append("   - 统一代理生命周期管理接口")
        report.append("   - 标准化代理通信协议")
        report.append("   - 合并重复的代理管理功能")
        report.append("   - 考虑创建统一的AgentManager基类")
        report.append("")
    
    if context_files,::
        report.append("4. 🗃️ 上下文管理器整合,")
        report.append("   - 统一上下文管理接口")
        report.append("   - 合并相似的上下文存储实现")
        report.append("   - 标准化上下文生命周期管理")
        report.append("")
    
    report.append("5. 📊 总体建议,")
    report.append("   - 建立统一的代码架构规范")
    report.append("   - 创建核心工具库,减少重复实现")
    report.append("   - 使用组合而非继承来减少代码重复")
    report.append("   - 定期进行代码审查,防止新的重复产生")
    
    return "\n".join(report)

def main():
    """主函数"""
    print("开始轻量级重复功能分析...")
    
    # 分析检查脚本
    check_groups, check_files = analyze_check_scripts()
    
    # 分析修复系统
    repair_systems = analyze_repair_systems()
    
    # 分析代理管理器
    agent_managers = analyze_agent_managers()
    
    # 分析上下文管理器
    context_files = analyze_context_managers()
    
    # 生成报告
    report = generate_report(check_groups, repair_systems, agent_managers, context_files)
    
    # 保存报告
    report_file = "lightweight_duplicate_analysis_report.txt"
    with open(report_file, 'w', encoding == 'utf-8') as f,
        f.write(report)
    
    print(f"\n分析完成！报告已保存到, {report_file}")
    print("\n" + "="*80)
    print(report)

if __name"__main__":::
    main()