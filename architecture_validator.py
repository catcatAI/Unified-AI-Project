#!/usr/bin/env python3
"""
架构完整性验证器
检查统一AGI生态系统的架构完整性
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from unified_agi_ecosystem import UnifiedAGIEcosystem, AGILevel
except ImportError as e:
    print(f"❌ 无法导入统一AGI生态系统模块: {e}")
    sys.exit(1)

def check_system_architecture() -> Dict[str, Any]:
    """检查系统架构完整性"""
    print("🔍 开始系统架构完整性检查...")
    
    results = {
        "status": "unknown",
        "issues": [],
        "components": {},
        "recommendations": []
    }
    
    try:
        # 1. 检查核心生态系统文件
        ecosystem_file = Path("unified_agi_ecosystem.py")
        if ecosystem_file.exists():
            print(f"✅ 核心生态系统文件存在: {ecosystem_file}")
            results["components"]["core_ecosystem"] = "present"
        else:
            print(f"❌ 核心生态系统文件缺失: {ecosystem_file}")
            results["issues"].append("核心生态系统文件缺失")
            results["components"]["core_ecosystem"] = "missing"
        
        # 2. 检查子系统组件
        required_subsystems = [
            "comprehensive_discovery_system.py",
            "enhanced_unified_fix_system.py", 
            "comprehensive_test_system.py",
            "intelligent_repair_system.py",
            "monitoring_dashboard.py",
            "adaptive_learning_controller",
            "unified_auto_fix_system"
        ]
        
        for subsystem in required_subsystems:
            subsystem_path = Path(subsystem)
            if subsystem_path.exists():
                print(f"✅ 子系统存在: {subsystem}")
                results["components"][subsystem] = "present"
            else:
                print(f"⚠️  子系统缺失: {subsystem}")
                results["issues"].append(f"子系统缺失: {subsystem}")
                results["components"][subsystem] = "missing"
        
        # 3. 检查配置文件
        config_files = [
            "package.json",
            "requirements.txt", 
            "pnpm-workspace.yaml",
            "eslint.config.mjs"
        ]
        
        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                print(f"✅ 配置文件存在: {config_file}")
                results["components"][config_file] = "present"
            else:
                print(f"⚠️  配置文件缺失: {config_file}")
                results["issues"].append(f"配置文件缺失: {config_file}")
                results["components"][config_file] = "missing"
        
        # 4. 检查关键目录结构
        key_directories = [
            "apps",
            "packages", 
            "docs",
            "tests",
            "tools",
            "training",
            "auto_fix_workspace"
        ]
        
        for directory in key_directories:
            dir_path = Path(directory)
            if dir_path.exists() and dir_path.is_dir():
                print(f"✅ 目录存在: {directory}")
                results["components"][directory] = "present"
            else:
                print(f"⚠️  目录缺失: {directory}")
                results["issues"].append(f"目录缺失: {directory}")
                results["components"][directory] = "missing"
        
        # 5. 检查生态系统实例化
        try:
            ecosystem = UnifiedAGIEcosystem()
            print(f"✅ 统一AGI生态系统实例化成功")
            print(f"   当前AGI等级: {ecosystem.current_level.value}")
            print(f"   目标AGI等级: {ecosystem.target_level.value}")
            results["components"]["ecosystem_instance"] = "working"
        except Exception as e:
            print(f"❌ 统一AGI生态系统实例化失败: {e}")
            results["issues"].append(f"生态系统实例化失败: {e}")
            results["components"]["ecosystem_instance"] = "broken"
        
        # 6. 总体评估
        total_components = len(results["components"])
        working_components = sum(1 for status in results["components"].values() 
                            if status in ["present", "working"])
        
        health_percentage = (working_components / total_components) * 100
        
        if health_percentage >= 90:
            results["status"] = "excellent"
            print(f"🎉 系统架构健康度: {health_percentage:.1f}% - 优秀")
        elif health_percentage >= 80:
            results["status"] = "good" 
            print(f"✅ 系统架构健康度: {health_percentage:.1f}% - 良好")
        elif health_percentage >= 70:
            results["status"] = "fair"
            print(f"⚠️  系统架构健康度: {health_percentage:.1f}% - 一般")
        else:
            results["status"] = "poor"
            print(f"❌ 系统架构健康度: {health_percentage:.1f}% - 较差")
        
        results["health_percentage"] = health_percentage
        results["working_components"] = working_components
        results["total_components"] = total_components
        
    except Exception as e:
        print(f"❌ 架构检查过程中出现错误: {e}")
        results["issues"].append(f"检查过程错误: {e}")
        results["status"] = "error"
    
    return results

def generate_architecture_report(results: Dict[str, Any]) -> str:
    """生成架构检查报告"""
    report = []
    report.append("# 🔍 系统架构完整性检查报告")
    report.append(f"\n**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**整体状态**: {results['status']}")
    report.append(f"**健康度**: {results['health_percentage']:.1f}%")
    report.append(f"**工作组件**: {results['working_components']}/{results['total_components']}")
    
    if results['issues']:
        report.append("\n## ⚠️ 发现的问题")
        for issue in results['issues']:
            report.append(f"- {issue}")
    
    report.append("\n## 📊 组件状态详情")
    for component, status in results['components'].items():
        status_icon = "✅" if status in ["present", "working"] else "❌"
        report.append(f"{status_icon} {component}: {status}")
    
    if results['recommendations']:
        report.append("\n## 💡 建议")
        for rec in results['recommendations']:
            report.append(f"- {rec}")
    
    return "\n".join(report)

def main():
    """主函数"""
    print("🚀 启动统一AGI生态系统架构完整性检查...")
    
    # 执行架构检查
    results = check_system_architecture()
    
    # 生成报告
    report = generate_architecture_report(results)
    
    # 保存报告
    report_file = "architecture_validation_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📋 检查报告已保存到: {report_file}")
    print(f"🏁 检查完成，系统状态: {results['status']}")
    
    # 如果状态不佳，提出修复建议
    if results['status'] in ['poor', 'error']:
        print("\n🔧 建议立即进行系统修复和优化")
        return 1
    elif results['status'] == 'fair':
        print("\n⚠️  建议进行系统优化和组件补充")
        return 0
    else:
        print("\n✅ 系统架构完整性良好")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)