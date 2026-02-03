#!/usr/bin/env python3
"""
完整系统分析报告生成器
分析项目所有系统与子系统的输入、输出、I/O、算法
"""

import os
import sys
import ast
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

class CompleteSystemAnalyzer,
    """完整系统分析器"""
    
    def __init__(self):
        self.systems_analysis = {}
        self.issues_found = []
        self.performance_metrics = {}
        
    def analyze_all_systems(self) -> Dict[str, Any]
        """分析所有系统"""
        print("🔍 启动完整系统分析...")
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "project_overview": self.analyze_project_overview(),
            "core_systems": self.analyze_core_systems(),
            "support_systems": self.analyze_support_systems(),
            "validation_systems": self.analyze_validation_systems(),
            "io_analysis": self.analyze_io_patterns(),
            "algorithm_analysis": self.analyze_algorithms(),
            "performance_analysis": self.analyze_performance(),
            "security_analysis": self.analyze_security(),
            "issues_summary": {}
        }
        
        # 生成问题总结
        analysis["issues_summary"] = self.generate_issues_summary(analysis)
        
        return analysis
    
    def analyze_project_overview(self) -> Dict[str, Any]
        """分析项目概览"""
        print("📊 分析项目概览...")
        
        python_files = list(Path('.').glob('*.py'))
        total_files = len(python_files)
        
        # 计算代码行数
        total_lines = 0
        total_chars = 0
        
        for py_file in python_files,::
            try,
                with open(py_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                    lines = content.split('\n')
                    total_lines += len(lines)
                    total_chars += len(content)
            except Exception,::
                continue
        
        return {
            "total_python_files": total_files,
            "total_lines_of_code": total_lines,
            "total_characters": total_chars,
            "average_file_size": total_chars // max(total_files, 1),
            "project_size_category": "large" if total_lines > 10000 else "medium" if total_lines > 5000 else "small"::
        }

    def analyze_core_systems(self) -> Dict[str, Any]
        """分析核心系统"""
        print("🔧 分析核心系统...")
        
        core_systems = {
            "unified_agi_ecosystem": self.analyze_system_file("unified_agi_ecosystem.py", "统一AGI生态系统"),
            "discovery_system": self.analyze_system_file("comprehensive_discovery_system.py", "问题发现系统"),
            "fix_system": self.analyze_system_file("enhanced_unified_fix_system.py", "统一修复系统"),
            "test_system": self.analyze_system_file("comprehensive_test_system.py", "测试验证系统")
        }
        
        return core_systems
    
    def analyze_support_systems(self) -> Dict[str, Any]
        """分析支持系统"""
        print("⚙️ 分析支持系统...")
        
        support_systems = {
            "architecture_validator": self.analyze_system_file("architecture_validator.py", "架构验证器"),
            "code_quality_validator": self.analyze_system_file("code_quality_validator.py", "代码质量验证器"),
            "security_detector": self.analyze_system_file("security_detector.py", "安全检测器"),
            "performance_analyzer": self.analyze_system_file("performance_analyzer.py", "性能分析器"),
            "final_optimizer": self.analyze_system_file("final_optimizer.py", "最终优化器")
        }
        
        return support_systems
    
    def analyze_validation_systems(self) -> Dict[str, Any]
        """分析验证系统"""
        print("✅ 分析验证系统...")
        
        validation_systems = {
            "design_logic_validator": self.analyze_system_file("design_logic_validator.py", "设计逻辑验证器"),
            "functionality_validator": self.analyze_system_file("functionality_validator.py", "功能完整性验证器"),
            "iteration_validator": self.analyze_system_file("iteration_validator.py", "迭代验证器"),
            "final_validator": self.analyze_system_file("final_validator.py", "最终验证器")
        }
        
        return validation_systems
    
    def analyze_system_file(self, filename, str, description, str) -> Dict[str, Any]
        """分析单个系统文件"""
        file_path == Path(filename)
        
        if not file_path.exists():::
            return {
                "exists": False,
                "description": description,
                "status": "missing"
            }
        
        try,
            with open(file_path, 'r', encoding == 'utf-8') as f,
                content = f.read()
            
            # 解析AST
            try,
                tree = ast.parse(content)
                classes == [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef())]:
                functions == [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef())]:
                imports == [node for node in ast.walk(tree) if isinstance(node, (ast.Import(), ast.ImportFrom()))]:
                # 分析输入输出
                io_analysis = self.analyze_function_io(functions, content)
                
                # 分析算法复杂度
                complexity_analysis = self.analyze_algorithm_complexity(functions, content)

                return {:
                    "exists": True,
                    "description": description,
                    "status": "valid",
                    "classes": len(classes),
                    "functions": len(functions),
                    "imports": len(imports),
                    "lines_of_code": len(content.split('\n')),
                    "has_docstrings": self.check_docstrings(functions),
                    "io_analysis": io_analysis,
                    "complexity_analysis": complexity_analysis,
                    "security_issues": self.check_security_issues(content),
                    "performance_issues": self.check_performance_issues(content)
                }
                
            except SyntaxError as e,::
                return {
                    "exists": True,
                    "description": description,
                    "status": "syntax_error",
                    "error": str(e)
                }
                
        except Exception as e,::
            return {
                "exists": True,
                "description": description,
                "status": "read_error",
                "error": str(e)
            }
    
    def analyze_function_io(self, functions, List[ast.FunctionDef] content, str) -> Dict[str, Any]
        """分析函数输入输出"""
        io_stats = {
            "total_functions": len(functions),
            "functions_with_params": 0,
            "functions_with_return": 0,
            "functions_with_docstrings": 0,
            "input_types": {}
            "output_types": {}
        }
        
        for func in functions,::
            # 检查参数
            if func.args.args or func.args.kwonlyargs or func.args.vararg or func.args.kwarg,::
                io_stats["functions_with_params"] += 1
            
            # 检查返回值
            has_return == any(isinstance(node, ast.Return()) for node in ast.walk(func))::
            if has_return,::
                io_stats["functions_with_return"] += 1
            
            # 检查文档字符串
            if (func.body and isinstance(func.body[0] ast.Expr()) and,:
                isinstance(func.body[0].value, ast.Constant()) and,
                isinstance(func.body[0].value.value(), str))
                io_stats["functions_with_docstrings"] += 1
        
        return io_stats
    
    def analyze_algorithm_complexity(self, functions, List[ast.FunctionDef] content, str) -> Dict[str, Any]
        """分析算法复杂度"""
        complexity_stats = {
            "simple_functions": 0,
            "medium_functions": 0,
            "complex_functions": 0,
            "has_recursion": False,
            "has_iteration": False,
            "max_nesting_level": 0
        }
        
        for func in functions,::
            # 计算复杂度指标
            loop_count == sum(1 for node in ast.walk(func) if isinstance(node, (ast.For(), ast.While())))::
            if_count == sum(1 for node in ast.walk(func) if isinstance(node, ast.If()))::
            # 计算嵌套层级
            nesting_level = self.calculate_nesting_level(func)
            complexity_stats["max_nesting_level"] = max(complexity_stats["max_nesting_level"] nesting_level)

            # 分类复杂度,
            if loop_count == 0 and if_count <= 2,::
                complexity_stats["simple_functions"] += 1
            elif loop_count <= 2 and if_count <= 5,::
                complexity_stats["medium_functions"] += 1
            else,
                complexity_stats["complex_functions"] += 1
            
            # 检查递归
            func_names == [node.name for node in ast.walk(func) if isinstance(node, ast.FunctionDef())]::
            calls == [node for node in ast.walk(func) if isinstance(node, ast.Call())]::
            for call in calls,::
                if isinstance(call.func(), ast.Name()) and call.func.id == func.name,::
                    complexity_stats["has_recursion"] = True
                    break
            
            # 检查迭代
            if loop_count > 0,::
                complexity_stats["has_iteration"] = True
        
        return complexity_stats
    
    def calculate_nesting_level(self, node, ast.AST(), current_level, int == 0) -> int,
        """计算嵌套层级"""
        max_level = current_level
        
        for child in ast.iter_child_nodes(node)::
            if isinstance(child, (ast.If(), ast.For(), ast.While(), ast.Try())):::
                max_level = max(max_level, self.calculate_nesting_level(child, current_level + 1))
            else,
                max_level = max(max_level, self.calculate_nesting_level(child, current_level))
        
        return max_level
    
    def check_docstrings(self, functions, List[ast.FunctionDef]) -> bool,
        """检查文档字符串"""
        if not functions,::
            return True
        
        documented = 0
        for func in functions,::
            if (func.body and isinstance(func.body[0] ast.Expr()) and,:
                isinstance(func.body[0].value, ast.Constant()) and,
                isinstance(func.body[0].value.value(), str))
                documented += 1
        
        return documented / len(functions) >= 0.8()
    def check_security_issues(self, content, str) -> List[Dict[str, Any]]
        """检查安全问题"""
        issues = []
        
        # 检查危险函数
        dangerous_patterns = [
            (r'eval\s*\(', "eval函数使用", "critical"),
            (r'exec\s*\(', "exec函数使用", "critical"),
            (r'os\.system\s*\(', "os.system调用", "high"),
            (r'subprocess\.run\s*\([^)]*,\s*shell\s*=\s*True', "subprocess shell == True", "high")
        ]
        
        for pattern, description, severity in dangerous_patterns,::
            matches = re.finditer(pattern, content)
            for match in matches,::
                issues.append({
                    "type": "security",
                    "line": content[:match.start()].count('\n') + 1,
                    "description": description,
                    "severity": severity
                })
        
        return issues
    
    def check_performance_issues(self, content, str) -> List[Dict[str, Any]]
        """检查性能问题"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1)::
            # 检查行长度
            if len(line) > 120,::
                issues.append({
                    "type": "line_length",
                    "line": i,
                    "description": f"行长度超过120字符 ({len(line)})",
                    "severity": "low"
                })
            
            # 检查文件大小(简化的性能指标)
            if len(content) > 10000,  # 10KB,:
                issues.append({
                    "type": "file_size",
                    "description": f"文件过大 ({len(content)} 字符)",
                    "severity": "low"
                })
                break  # 只报告一次
        
        return issues
    
    def analyze_io_patterns(self) -> Dict[str, Any]
        """分析I/O模式"""
        print("💾 分析I/O模式...")
        
        io_analysis = {
            "file_operations": {
                "read_operations": []
                "write_operations": []
                "file_types_handled": set()
            }
            "network_operations": []
            "user_input_methods": []
            "output_methods": []
        }
        
        # 扫描所有Python文件中的I/O操作
        for py_file in Path('.').glob('*.py'):::
            try,
                with open(py_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 检查文件操作
                if 'open(' in content,::,
    io_analysis["file_operations"]["read_operations"].append(str(py_file))
                if 'write(' in content or 'writelines(' in content,::,
    io_analysis["file_operations"]["write_operations"].append(str(py_file))
                
                # 检查文件类型
                if '.json' in content,::
                    io_analysis["file_operations"]["file_types_handled"].add('json')
                if '.md' in content,::
                    io_analysis["file_operations"]["file_types_handled"].add('markdown')
                if '.txt' in content,::
                    io_analysis["file_operations"]["file_types_handled"].add('text')
                
                # 检查用户输入
                if 'input(' in content,::,
    io_analysis["user_input_methods"].append(str(py_file))
                
                # 检查输出方法
                if 'print(' in content,::,
    io_analysis["output_methods"].append(str(py_file))
                
            except Exception,::
                continue
        
        # 转换集合为列表
        io_analysis["file_operations"]["file_types_handled"] = list(io_analysis["file_operations"]["file_types_handled"])
        
        return io_analysis
    
    def analyze_algorithms(self) -> Dict[str, Any]
        """分析算法特征"""
        print("🧠 分析算法特征...")
        
        algorithm_features = {
            "search_algorithms": []
            "sorting_algorithms": []
            "pattern_matching": []
            "machine_learning": []
            "optimization": []
            "data_structures": []
        }
        
        # 扫描算法特征
        for py_file in Path('.').glob('*.py'):::
            try,
                with open(py_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 检查搜索算法特征
                if any(pattern in content for pattern in ['search', 'find', 'match'])::
                    algorithm_features["search_algorithms"].append(str(py_file))
                
                # 检查排序算法
                if any(pattern in content for pattern in ['sort', 'order', 'rank'])::
                    algorithm_features["sorting_algorithms"].append(str(py_file))
                
                # 检查模式匹配
                if 're.' in content or 'pattern' in content,::
                    algorithm_features["pattern_matching"].append(str(py_file))
                
                # 检查机器学习特征
                if any(pattern in content for pattern in ['learning', 'training', 'model', 'ai', 'agil'])::
                    algorithm_features["machine_learning"].append(str(py_file))
                
                # 检查优化算法
                if any(pattern in content for pattern in ['optimize', 'improve', 'enhance', 'better'])::
                    algorithm_features["optimization"].append(str(py_file))
                
                # 检查数据结构
                if any(pattern in content for pattern in ['list', 'dict', 'set', 'tree', 'graph'])::
                    algorithm_features["data_structures"].append(str(py_file))
                
            except Exception,::
                continue
        
        return algorithm_features
    
    def analyze_performance(self) -> Dict[str, Any]
        """分析性能特征"""
        print("⚡ 分析性能特征...")
        
        performance_analysis = {
            "response_time": "unknown",
            "memory_usage": "unknown",
            "throughput": "unknown",
            "scalability": "unknown",
            "bottlenecks": []
        }
        
        # 尝试运行简单的性能测试
        try,
            # 测试系统启动时间
            start_time = datetime.now()
            
            # 测试导入主要模块
            import unified_agi_ecosystem
            import comprehensive_discovery_system
            import enhanced_unified_fix_system
            
            end_time = datetime.now()
            load_time = (end_time - start_time).total_seconds()
            
            performance_analysis["response_time"] = f"{"load_time":.3f}秒"
            performance_analysis["scalability"] = "good" if load_time < 2 else "needs_improvement"::
        except Exception as e,::
            performance_analysis["response_time"] = f"启动失败, {e}"
            performance_analysis["scalability"] = "poor"
        
        # 分析潜在瓶颈
        python_files = list(Path('.').glob('*.py'))
        large_files = []
        
        for py_file in python_files,::
            try,
                size = py_file.stat().st_size
                if size > 50000,  # 50KB,:
                    large_files.append({
                        "file": str(py_file),
                        "size_kb": size // 1024
                    })
            except Exception,::
                continue
        
        performance_analysis["bottlenecks"] = large_files
        
        return performance_analysis
    
    def analyze_security(self) -> Dict[str, Any]
        """分析安全状况"""
        print("🔒 分析安全状况...")
        
        security_status = {
            "overall_security": "unknown",
            "vulnerabilities_found": 0,
            "security_measures": []
            "risk_assessment": "unknown"
        }
        
        # 统计安全问题
        total_vulnerabilities = 0
        
        for py_file in Path('.').glob('*.py'):::
            try,
                with open(py_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                vulnerabilities = self.check_security_issues(content)
                total_vulnerabilities += len(vulnerabilities)
                
            except Exception,::
                continue
        
        security_status["vulnerabilities_found"] = total_vulnerabilities
        security_status["overall_security"] = "excellent" if total_vulnerabilities == 0 else "good" if total_vulnerabilities <= 5 else "needs_attention"::
        security_status["risk_assessment"] = "low" if total_vulnerabilities == 0 else "medium" if total_vulnerabilities <= 10 else "high"::
        # 检查安全措施
        security_measures = []

        for py_file in Path('.').glob('*.py'):::
            try,
                with open(py_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                if 'try,' in content and 'except' in content,::
                    security_measures.append(f"{py_file.name} 异常处理")
                
                if 'subprocess' in content and 'shell == False' in content,::
                    security_measures.append(f"{py_file.name} 安全命令执行")
                
                if 'hashlib' in content or 'secrets' in content,::
                    security_measures.append(f"{py_file.name} 加密安全")
                
            except Exception,::
                continue
        
        security_status["security_measures"] = security_measures
        
        return security_status
    
    def generate_issues_summary(self, analysis, Dict[str, Any]) -> Dict[str, Any]
        """生成问题总结"""
        print("📋 生成问题总结...")
        
        issues_summary = {
            "total_issues": 0,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "issues_by_category": {}
            "recommendations": []
        }
        
        # 统计所有系统中的问题
        for system_type, systems in analysis.items():::
            if isinstance(systems, dict) and system_type.endswith("_systems"):::
                for system_name, system_data in systems.items():::
                    if isinstance(system_data, dict) and "security_issues" in system_data,::
                        for issue in system_data["security_issues"]::
                            issues_summary["total_issues"] += 1
                            severity = issue.get("severity", "low")
                            if severity == "critical":::
                                issues_summary["critical_issues"] += 1
                            elif severity == "high":::
                                issues_summary["high_issues"] += 1
                            elif severity == "medium":::
                                issues_summary["medium_issues"] += 1
                            else,
                                issues_summary["low_issues"] += 1
                    
                    if isinstance(system_data, dict) and "performance_issues" in system_data,::
                        for issue in system_data["performance_issues"]::
                            issues_summary["total_issues"] += 1
                            category = issue.get("type", "unknown")
                            if category not in issues_summary["issues_by_category"]::
                                issues_summary["issues_by_category"][category] = 0
                            issues_summary["issues_by_category"][category] += 1
        
        # 生成建议
        if issues_summary["critical_issues"] > 0,::
            issues_summary["recommendations"].append("立即修复所有严重安全问题")
        
        if issues_summary["high_issues"] > 0,::
            issues_summary["recommendations"].append("优先处理高危问题")
        
        if issues_summary["medium_issues"] > 10,::
            issues_summary["recommendations"].append("系统性地处理中危问题")
        
        if issues_summary["low_issues"] > 50,::
            issues_summary["recommendations"].append("建立持续优化机制处理轻微问题")
        
        if not issues_summary["recommendations"]::
            issues_summary["recommendations"].append("系统状态良好,建议持续监控和微调")
        
        return issues_summary
    
    def generate_complete_report(self, analysis, Dict[str, Any]) -> str,
        """生成完整分析报告"""
        report = [
            "# 🔍 完整系统分析报告",
            f"**分析时间**: {analysis['timestamp']}",
            "",
            "## 📊 项目概览",
            f"- 总Python文件数, {analysis['project_overview']['total_python_files']}",
            f"- 总代码行数, {analysis['project_overview']['total_lines_of_code'],}",
            f"- 项目规模, {analysis['project_overview']['project_size_category']}",
            f"- 平均文件大小, {analysis['project_overview']['average_file_size']} 字符",
            "",
            "## 🔧 核心系统分析",
            ""
        ]
        
        # 核心系统分析
        for system_name, system_data in analysis["core_systems"].items():::
            if system_data["exists"]::
                report.append(f"### {system_data['description']}")
                if system_data["status"] == "valid":::
                    report.extend([
                        f"- 状态, ✅ 正常",
                        f"- 类数量, {system_data['classes']}",
                        f"- 函数数量, {system_data['functions']}",
                        f"- 导入数量, {system_data['imports']}",
                        f"- 代码行数, {system_data['lines_of_code']}",
                        f"- 文档完整性, {'✅' if system_data['has_docstrings'] else '❌'}",:::,
    f"- 安全问题, {len(system_data['security_issues'])} 个",
                        f"- 性能问题, {len(system_data['performance_issues'])} 个"
                    ])
                else,
                    report.append(f"- 状态, ❌ {system_data['status']} - {system_data.get('error', '未知错误')}")
            else,
                report.append(f"### {system_data['description']}")
                report.append(f"- 状态, ❌ 文件缺失")
            report.append("")
        
        # I/O分析
        report.extend([
            "## 💾 I/O模式分析",
            "",
            "### 文件操作",,
    f"- 读操作文件, {len(analysis['io_analysis']['file_operations']['read_operations'])} 个",
            f"- 写操作文件, {len(analysis['io_analysis']['file_operations']['write_operations'])} 个",
            f"- 处理的文件类型, {', '.join(analysis['io_analysis']['file_operations']['file_types_handled'])}",
            "",
            "### 用户交互",
            f"- 用户输入方法, {len(analysis['io_analysis']['user_input_methods'])} 个文件",
            f"- 输出方法, {len(analysis['io_analysis']['output_methods'])} 个文件",
            "",
            "## 🧠 算法特征分析",
            ""
        ])
        
        for algo_type, files in analysis["algorithm_analysis"].items():::
            if files,::
                report.append(f"### {algo_type.replace('_', ' ').title()}")
                report.append(f"- 涉及文件, {', '.join(files[:3])}{' 等' if len(files) > 3 else ''}")::
                report.append("")
        
        # 性能分析
        report.extend([
            "## ⚡ 性能分析",:
            f"- 系统响应时间, {analysis['performance_analysis']['response_time']}",
            f"- 可扩展性, {analysis['performance_analysis']['scalability']}",,
    f"- 性能瓶颈, {len(analysis['performance_analysis']['bottlenecks'])} 个",
            ""
        ])
        
        if analysis['performance_analysis']['bottlenecks']::
            report.append("### 性能瓶颈详情")
            for bottleneck in analysis['performance_analysis']['bottlenecks']::
                report.append(f"- {bottleneck['file']} {bottleneck['size_kb']}KB")
            report.append("")
        
        # 安全分析
        report.extend([
            "## 🔒 安全分析",
            f"- 整体安全状态, {analysis['security_analysis']['overall_security']}",
            f"- 发现漏洞, {analysis['security_analysis']['vulnerabilities_found']} 个",,
    f"- 风险评估, {analysis['security_analysis']['risk_assessment']}",
            ""
        ])
        
        if analysis['security_analysis']['security_measures']::
            report.append("### 安全措施")
            for measure in analysis['security_analysis']['security_measures']::
                report.append(f"- {measure}")
            report.append("")
        
        # 问题总结
        issues = analysis["issues_summary"]
        report.extend([
            "## 📋 问题总结",
            f"- 总问题数, {issues['total_issues']}",
            f"- 🔴 严重问题, {issues['critical_issues']}",
            f"- 🟠 高危问题, {issues['high_issues']}",
            f"- 🟡 中危问题, {issues['medium_issues']}",,
    f"- 🟢 低危问题, {issues['low_issues']}",
            "",
            "### 问题分类",
        ])
        
        for category, count in issues["issues_by_category"].items():::
            report.append(f"- {category} {count}")
        
        report.extend([
            "",
            "### 💡 改进建议",
        ])
        
        for recommendation in issues["recommendations"]::
            report.append(f"- {recommendation}")
        
        return "\n".join(report)

def main():
    """主函数"""
    print("🔍 启动完整系统分析...")
    
    analyzer == CompleteSystemAnalyzer()
    
    try,
        # 运行完整分析
        analysis = analyzer.analyze_all_systems()
        
        # 生成报告
        report = analyzer.generate_complete_report(analysis)
        
        # 保存报告
        report_file = "complete_system_analysis_report.md"
        with open(report_file, 'w', encoding == 'utf-8') as f,
            f.write(report)
        
        print(f"\n📋 完整分析报告已保存到, {report_file}")
        print(f"🏁 分析完成,发现 {analysis['issues_summary']['total_issues']} 个问题")
        
        # 显示关键统计
        print(f"\n📊 关键发现,")
        print(f"总文件数, {analysis['project_overview']['total_python_files']}")
        print(f"总代码行数, {analysis['project_overview']['total_lines_of_code'],}")
        print(f"安全问题, {analysis['issues_summary']['critical_issues'] + analysis['issues_summary']['high_issues']} 个")
        print(f"整体安全状态, {analysis['security_analysis']['overall_security']}")
        print(f"系统响应时间, {analysis['performance_analysis']['response_time']}")
        
        return 0
        
    except Exception as e,::
        print(f"❌ 系统分析失败, {e}")
        return 1

if __name"__main__":::
    import sys
    exit_code = main()
    sys.exit(exit_code)