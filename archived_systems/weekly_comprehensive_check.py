#!/usr/bin/env python3
"""
周综合检查器
执行每周的综合系统检查
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class WeeklyComprehensiveCheck:
    """周综合检查器"""
    
    def __init__(self):
        self.check_results = {}
        self.check_history = []
        self.check_date = datetime.now()
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """运行综合检查"""
        print("🔍 启动周综合检查...")
        
        results = {
            "check_date": self.check_date.isoformat(),
            "check_type": "weekly_comprehensive",
            "system_status": self.check_system_status(),
            "code_quality": self.check_code_quality(),
            "security_status": self.check_security_status(),
            "performance_status": self.check_performance_status(),
            "documentation_status": self.check_documentation_status(),
            "recommendations": []
        }
        
        # 生成建议
        results["recommendations"] = self.generate_recommendations(results)
        
        self.check_results = results
        return results
    
    def check_system_status(self) -> Dict[str, Any]:
        """检查系统状态"""
        print("📊 检查系统状态...")
        
        status = {
            "overall_health": "unknown",
            "critical_issues": 0,
            "warning_issues": 0,
            "info_issues": 0,
            "components": {}
        }
        
        # 检查关键文件
        critical_files = [
            "unified_agi_ecosystem.py",
            "comprehensive_discovery_system.py",
            "enhanced_unified_fix_system.py",
            "comprehensive_test_system.py"
        ]
        
        for file_name in critical_files:
            file_path = Path(file_name)
            if file_path.exists():
                status["components"][file_name] = "present"
            else:
                status["components"][file_name] = "missing"
                status["critical_issues"] += 1
        
        # 检查目录结构
        key_directories = ["apps", "packages", "docs", "tests", "tools"]
        for directory in key_directories:
            dir_path = Path(directory)
            if dir_path.exists() and dir_path.is_dir():
                status["components"][directory] = "present"
            else:
                status["components"][directory] = "missing"
                status["warning_issues"] += 1
        
        # 总体健康评估
        if status["critical_issues"] == 0:
            status["overall_health"] = "healthy"
        elif status["critical_issues"] <= 2:
            status["overall_health"] = "warning"
        else:
            status["overall_health"] = "critical"
        
        return status
    
    def check_code_quality(self) -> Dict[str, Any]:
        """检查代码质量"""
        print("📝 检查代码质量...")
        
        quality = {
            "total_files": 0,
            "syntax_errors": 0,
            "style_issues": 0,
            "complexity_issues": 0,
            "overall_score": 0
        }
        
        # 扫描Python文件
        python_files = list(Path('.').glob('*.py'))
        quality["total_files"] = len(python_files)
        
        for py_file in python_files:
            if py_file.name.startswith('test_'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 基本语法检查
                try:
                    compile(content, py_file, 'exec')
                except SyntaxError:
                    quality["syntax_errors"] += 1
                
                # 风格检查
                lines = content.split('\n')
                for line in lines:
                    if len(line) > 120:
                        quality["style_issues"] += 1
                    # 检查缩进
                    if line.strip() and not line.startswith('#'):
                        leading_spaces = len(line) - len(line.lstrip())
                        if leading_spaces % 4 != 0 and leading_spaces > 0:
                            quality["style_issues"] += 1
                
                # 复杂度检查（简单版本）
                if content.count('if ') > 10 or content.count('for ') > 5:
                    quality["complexity_issues"] += 1
                    
            except Exception as e:
                quality["syntax_errors"] += 1
        
        # 计算总体分数
        error_rate = quality["syntax_errors"] / max(quality["total_files"], 1)
        style_rate = quality["style_issues"] / max(quality["total_files"], 1)
        
        if error_rate == 0 and style_rate < 2:
            quality["overall_score"] = 100
        elif error_rate < 0.1 and style_rate < 5:
            quality["overall_score"] = 80
        elif error_rate < 0.2:
            quality["overall_score"] = 60
        else:
            quality["overall_score"] = 40
        
        return quality
    
    def check_security_status(self) -> Dict[str, Any]:
        """检查安全状态"""
        print("🔒 检查安全状态...")
        
        security = {
            "vulnerabilities": 0,
            "high_risk": 0,
            "medium_risk": 0,
            "low_risk": 0,
            "secure_files": 0,
            "total_files": 0
        }
        
        # 扫描Python文件
        python_files = list(Path('.').glob('*.py'))
        security["total_files"] = len(python_files)
        
        for py_file in python_files:
            if py_file.name.startswith('test_'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_risks = 0
                
                # 检查硬编码敏感信息
                secret_patterns = [
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'api_key\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']'
                ]
                
                for pattern in secret_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        file_risks += 1
                        security["high_risk"] += 1
                
                # 检查SQL注入风险
                sql_patterns = [
                    r'execute\s*\(\s*["\'].*%.*["\']',
                    r'execute\s*\(\s*["\'].*\+.*["\']'
                ]
                
                for pattern in sql_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        file_risks += 1
                        security["medium_risk"] += 1
                
                # 检查XSS风险
                if re.search(r'innerHTML\s*=\s*|eval\s*\(', content, re.IGNORECASE):
                    file_risks += 1
                    security["medium_risk"] += 1
                
                if file_risks == 0:
                    security["secure_files"] += 1
                
                security["vulnerabilities"] += file_risks
                
            except Exception:
                continue
        
        security["low_risk"] = security["total_files"] - security["high_risk"] - security["medium_risk"] - security["secure_files"]
        
        return security
    
    def check_performance_status(self) -> Dict[str, Any]:
        """检查性能状态"""
        print("⚡ 检查性能状态...")
        
        performance = {
            "bottlenecks": [],
            "recommendations": [],
            "overall_rating": "unknown"
        }
        
        # 检查文件大小
        large_files = []
        for py_file in Path('.').glob('*.py'):
            if py_file.stat().st_size > 100 * 1024:  # 100KB
                large_files.append((py_file.name, py_file.stat().st_size))
        
        if large_files:
            performance["bottlenecks"].append("large_files")
            performance["recommendations"].append("考虑拆分大文件")
        
        # 检查导入复杂度
        complex_imports = 0
        for py_file in Path('.').glob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import_lines = len(re.findall(r'^import |^from .* import ', content, re.MULTILINE))
                if import_lines > 20:
                    complex_imports += 1
                    
            except Exception:
                continue
        
        if complex_imports > 0:
            performance["bottlenecks"].append("complex_imports")
            performance["recommendations"].append("简化导入结构")
        
        # 总体评级
        if len(performance["bottlenecks"]) == 0:
            performance["overall_rating"] = "excellent"
        elif len(performance["bottlenecks"]) <= 2:
            performance["overall_rating"] = "good"
        else:
            performance["overall_rating"] = "needs_improvement"
        
        return performance
    
    def check_documentation_status(self) -> Dict[str, Any]:
        """检查文档状态"""
        print("📚 检查文档状态...")
        
        docs = {
            "readme_exists": False,
            "api_docs": 0,
            "code_docs": 0,
            "missing_docs": []
        }
        
        # 检查README
        readme_files = list(Path('.').glob('README*'))
        if readme_files:
            docs["readme_exists"] = True
        
        # 检查代码文档
        python_files = list(Path('.').glob('*.py'))
        for py_file in python_files:
            if py_file.name.startswith('test_'):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查模块文档字符串
                if content.strip().startswith('"""'):
                    docs["code_docs"] += 1
                else:
                    docs["missing_docs"].append(f"{py_file.name}: 缺少模块文档")
                
                # 检查函数文档
                functions = len(re.findall(r'def\s+', content))
                docstrings = len(re.findall(r'"""', content))
                
                if functions > 0 and docstrings < functions:
                    docs["missing_docs"].append(f"{py_file.name}: 函数缺少文档")
                    
            except Exception:
                continue
        
        return docs
    
    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 系统状态建议
        system_status = results["system_status"]
        if system_status["overall_health"] != "healthy":
            recommendations.append("修复系统关键组件问题")
        
        # 代码质量建议
        code_quality = results["code_quality"]
        if code_quality["overall_score"] < 80:
            recommendations.append("提升代码质量，修复语法错误")
        
        # 安全建议
        security_status = results["security_status"]
        if security_status["high_risk"] > 0:
            recommendations.append("修复高危安全风险")
        
        # 性能建议
        performance_status = results["performance_status"]
        if performance_status["overall_rating"] != "excellent":
            recommendations.append("优化系统性能瓶颈")
        
        # 文档建议
        docs_status = results["documentation_status"]
        if not docs_status["readme_exists"]:
            recommendations.append("创建项目README文档")
        
        if docs_status["missing_docs"]:
            recommendations.append("完善代码文档")
        
        return recommendations
    
    def save_results(self, results: Dict[str, Any]):
        """保存检查结果"""
        try:
            # 保存到历史文件
            history_file = "weekly_check_history.json"
            
            history = []
            if Path(history_file).exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            history.append(results)
            
            # 只保留最近12周的数据
            if len(history) > 12:
                history = history[-12:]
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            print(f"📊 检查结果已保存到 {history_file}")
            
        except Exception as e:
            print(f"⚠️ 保存结果失败: {e}")
    
    def generate_weekly_report(self, results: Dict[str, Any]) -> str:
        """生成周报"""
        report = []
        
        report.append("# 📅 周综合检查报告")
        report.append(f"\n**检查日期**: {results['check_date']}")
        report.append(f"**检查类型**: {results['check_type']}")
        
        # 系统状态
        system_status = results["system_status"]
        report.append(f"\n## 📊 系统状态")
        report.append(f"- 整体健康度: {system_status['overall_health']}")
        report.append(f"- 严重问题: {system_status['critical_issues']}")
        report.append(f"- 警告问题: {system_status['warning_issues']}")
        
        # 代码质量
        code_quality = results["code_quality"]
        report.append(f"\n## 📝 代码质量")
        report.append(f"- 总文件数: {code_quality['total_files']}")
        report.append(f"- 语法错误: {code_quality['syntax_errors']}")
        report.append(f"- 风格问题: {code_quality['style_issues']}")
        report.append(f"- 质量评分: {code_quality['overall_score']}/100")
        
        # 安全状态
        security_status = results["security_status"]
        report.append(f"\n## 🔒 安全状态")
        report.append(f"- 漏洞总数: {security_status['vulnerabilities']}")
        report.append(f"- 高危风险: {security_status['high_risk']}")
        report.append(f"- 中危风险: {security_status['medium_risk']}")
        report.append(f"- 低危风险: {security_status['low_risk']}")
        
        # 性能状态
        performance_status = results["performance_status"]
        report.append(f"\n## ⚡ 性能状态")
        report.append(f"- 总体评级: {performance_status['overall_rating']}")
        report.append(f"- 性能瓶颈: {', '.join(performance_status['bottlenecks']) if performance_status['bottlenecks'] else '无'}")
        
        # 文档状态
        docs_status = results["documentation_status"]
        report.append(f"\n## 📚 文档状态")
        report.append(f"- README存在: {'是' if docs_status['readme_exists'] else '否'}")
        report.append(f"- 代码文档化文件: {docs_status['code_docs']}")
        
        # 建议
        recommendations = results["recommendations"]
        if recommendations:
            report.append(f"\n## 💡 改进建议")
            for i, rec in enumerate(recommendations, 1):
                report.append(f"{i}. {rec}")
        
        return "\n".join(report)

def main():
    """主函数"""
    print("📅 启动周综合检查器...")
    
    checker = WeeklyComprehensiveCheck()
    
    try:
        # 运行综合检查
        results = checker.run_comprehensive_check()
        
        # 生成报告
        report = checker.generate_weekly_report(results)
        
        # 保存报告
        report_file = f"weekly_check_report_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # 保存结果到历史
        checker.save_results(results)
        
        print(f"\n📋 周检查报告已保存到: {report_file}")
        print(f"🏁 检查完成，发现 {len(results['recommendations'])} 个改进建议")
        
        # 显示关键结果
        print(f"\n📊 关键指标:")
        print(f"系统健康度: {results['system_status']['overall_health']}")
        print(f"代码质量评分: {results['code_quality']['overall_score']}/100")
        print(f"安全漏洞: {results['security_status']['vulnerabilities']}")
        print(f"性能评级: {results['performance_status']['overall_rating']}")
        
    except Exception as e:
        print(f"❌ 周检查失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)