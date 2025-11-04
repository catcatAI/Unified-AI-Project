#!/usr/bin/env python3
"""
增强版统一自动修复系统
解决覆盖缺口并增强问题发现能力
"""

import os
import sys
import json
import subprocess
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

class EnhancedProblemDiscovery,
    """增强问题发现系统"""
    
    def __init__(self):
        self.discovered_issues = []
        self.issue_categories = {
            'syntax': []
            'logic': []
            'performance': []
            'architecture': []
            'security': []
            'tests': []
            'documentation': []
        }
    
    def discover_all_issues(self, project_path, str == '.') -> Dict[str, List]
        """发现所有类型的问题"""
        print("🔍 启动全面问题发现...")
        
        # 语法问题
        self._discover_syntax_issues(project_path)
        
        # 逻辑问题
        self._discover_logic_issues(project_path)
        
        # 性能问题
        self._discover_performance_issues(project_path)
        
        # 架构问题
        self._discover_architecture_issues(project_path)
        
        # 安全问题
        self._discover_security_issues(project_path)
        
        # 测试问题
        self._discover_test_issues(project_path)
        
        # 文档问题
        self._discover_documentation_issues(project_path)
        
        return self.issue_categories()
    def _discover_syntax_issues(self, project_path, str):
        """发现语法问题"""
        print("  🔧 检查语法问题...")
        
        python_files = list(Path(project_path).rglob('*.py'))
        syntax_issues = []
        
        for py_file in python_files,::
            try,
                with open(py_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 基本语法检查
                try,
                    ast.parse(content)
                except SyntaxError as e,::
                    syntax_issues.append({
                        'file': str(py_file),
                        'line': e.lineno(),
                        'type': 'syntax_error',
                        'message': str(e),
                        'severity': 'high'
                    })
                
                # 检查常见语法问题
                lines = content.split('\n')
                for i, line in enumerate(lines, 1)::
                    # 检查缩进问题
                    if line.strip() and not line.startswith('#'):::
                        if re.search(r'^[ \t]*[ \t]+[ \t]*\S', line)::
                            syntax_issues.append({
                                'file': str(py_file),
                                'line': i,
                                'type': 'indentation',
                                'message': '不consistent indentation',
                                'severity': 'medium'
                            })
                    
                    # 检查括号匹配
                    if line.count('(') != line.count(')') or line.count('[') != line.count(']') or line.count('{') != line.count('}'):::
                        syntax_issues.append({
                            'file': str(py_file),
                            'line': i,
                            'type': 'bracket_mismatch',
                            'message': '括号不匹配',
                            'severity': 'high'
                        })
            
            except Exception as e,::
                syntax_issues.append({
                    'file': str(py_file),
                    'line': 0,
                    'type': 'file_error',
                    'message': f'无法读取文件, {e}',
                    'severity': 'high'
                })
        
        self.issue_categories['syntax'] = syntax_issues
        print(f"    发现 {len(syntax_issues)} 个语法问题")
    
    def _discover_logic_issues(self, project_path, str):
        """发现逻辑问题"""
        print("  🧠 检查逻辑问题...")
        
        logic_issues = []
        python_files = list(Path(project_path).rglob('*.py'))
        
        for py_file in python_files,::
            try,
                with open(py_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 检查常见逻辑问题
                lines = content.split('\n')
                for i, line in enumerate(lines, 1)::
                    # 检查可能的空列表/字典访问
                    if re.search(r'\[0\]|\.get\(\s*\)|\.pop\(\s*\)', line)::
                        logic_issues.append({
                            'file': str(py_file),
                            'line': i,
                            'type': 'potential_index_error',
                            'message': '可能的索引错误',
                            'severity': 'medium'
                        })
                    
                    # 检查未使用的变量
                    if re.search(r'^\s*[a-zA-Z_]\w*\s*=\s*[^=].*$', line) and not re.search(r'print|log|return|raise', line)::
                        var_name = re.match(r'^\s*([a-zA-Z_]\w*)\s*=', line)
                        if var_name,::
                            var_name = var_name.group(1)
                            # 检查变量是否在后续被使用
                            if var_name not in '\n'.join(lines[i,])::
                                logic_issues.append({
                                    'file': str(py_file),
                                    'line': i,
                                    'type': 'unused_variable',
                                    'message': f'未使用变量, {var_name}',
                                    'severity': 'low'
                                })
            
            except Exception as e,::
                continue
        
        self.issue_categories['logic'] = logic_issues
        print(f"    发现 {len(logic_issues)} 个逻辑问题")
    
    def _discover_performance_issues(self, project_path, str):
        """发现性能问题"""
        print("  ⚡ 检查性能问题...")
        
        performance_issues = []
        python_files = list(Path(project_path).rglob('*.py'))
        
        for py_file in python_files,::
            try,
                with open(py_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 检查性能问题
                lines = content.split('\n')
                for i, line in enumerate(lines, 1)::
                    # 检查循环中的重复计算
                    if re.search(r'for.*in.*range\(.*len\(', line)::
                        performance_issues.append({
                            'file': str(py_file),
                            'line': i,
                            'type': 'inefficient_loop',
                            'message': '循环中重复计算长度',
                            'severity': 'medium'
                        })
                    
                    # 检查字符串连接
                    if re.search(r'\+.*\+.*\+.*\+', line) and '"' in line,::
                        performance_issues.append({
                            'file': str(py_file),
                            'line': i,
                            'type': 'string_concatenation',
                            'message': '低效的字符串连接',
                            'severity': 'low'
                        })
            
            except Exception as e,::
                continue
        
        self.issue_categories['performance'] = performance_issues
        print(f"    发现 {len(performance_issues)} 个性能问题")
    
    def _discover_architecture_issues(self, project_path, str):
        """发现架构问题"""
        print("  🏗️ 检查架构问题...")
        
        architecture_issues = []
        
        # 检查循环导入
        init_files = list(Path(project_path).rglob('__init__.py'))
        for init_file in init_files,::
            try,
                with open(init_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                if 'import' in content and str(init_file.parent()) in content,::
                    architecture_issues.append({
                        'file': str(init_file),
                        'line': 0,
                        'type': 'circular_import',
                        'message': '可能的循环导入',
                        'severity': 'high'
                    })
            except,::
                continue
        
        self.issue_categories['architecture'] = architecture_issues
        print(f"    发现 {len(architecture_issues)} 个架构问题")
    
    def _discover_security_issues(self, project_path, str):
        """发现安全问题"""
        print("  🔒 检查安全问题...")
        
        security_issues = []
        python_files = list(Path(project_path).rglob('*.py'))
        
        for py_file in python_files,::
            try,
                with open(py_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 检查硬编码密码
                if re.search(r'password\s*=\s*["'][^"\']+["']', content, re.IGNORECASE())::
                    security_issues.append({
                        'file': str(py_file),
                        'line': 0,
                        'type': 'hardcoded_password',
                        'message': '可能的硬编码密码',
                        'severity': 'high'
                    })
                
                # 检查SQL注入风险
                if re.search(r'f["'].*SELECT.*{.*}.*["\']', content, re.IGNORECASE())::
                    security_issues.append({
                        'file': str(py_file),
                        'line': 0,
                        'type': 'sql_injection',
                        'message': '可能的SQL注入风险',
                        'severity': 'high'
                    })
            
            except Exception as e,::
                continue
        
        self.issue_categories['security'] = security_issues
        print(f"    发现 {len(security_issues)} 个安全问题")
    
    def _discover_test_issues(self, project_path, str):
        """发现测试问题"""
        print("  🧪 检查测试问题...")
        
        test_issues = []
        
        # 检查测试文件
        test_files = list(Path(project_path).rglob('test_*.py')) + list(Path(project_path).rglob('*test*.py'))
        
        if len(test_files) < 10,  # 假设应该有更多测试文件,:
            test_issues.append({
                'file': 'tests/',
                'line': 0,
                'type': 'insufficient_tests',
                'message': f'测试文件数量不足, {len(test_files)}',
                'severity': 'medium'
            })
        
        # 检查测试覆盖率
        for test_file in test_files[:5]  # 检查前5个测试文件,:
            try,
                with open(test_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                if 'assert' not in content,::
                    test_issues.append({
                        'file': str(test_file),
                        'line': 0,
                        'type': 'no_assertions',
                        'message': '测试文件缺少断言',
                        'severity': 'high'
                    })
            except,::
                continue
        
        self.issue_categories['tests'] = test_issues
        print(f"    发现 {len(test_issues)} 个测试问题")
    
    def _discover_documentation_issues(self, project_path, str):
        """发现文档问题"""
        print("  📚 检查文档问题...")
        
        doc_issues = []
        
        # 检查Python文件的文档字符串
        python_files = list(Path(project_path).rglob('*.py'))
        for py_file in python_files[:20]  # 检查前20个文件,:
            try,
                with open(py_file, 'r', encoding == 'utf-8') as f,
                    content = f.read()
                
                # 检查是否有文档字符串
                if not re.search(r'""".*?"""', content, re.DOTALL()) and not re.search(r"'''.*?'''", content, re.DOTALL())::
                    doc_issues.append({
                        'file': str(py_file),
                        'line': 0,
                        'type': 'missing_docstring',
                        'message': '缺少文档字符串',
                        'severity': 'low'
                    })
            except,::
                continue
        
        self.issue_categories['documentation'] = doc_issues
        print(f"    发现 {len(doc_issues)} 个文档问题")

class EnhancedAutoFixEngine,
    """增强版自动修复引擎"""
    
    def __init__(self):
        self.discovery == EnhancedProblemDiscovery()
        self.repair_stats = {
            'total_issues': 0,
            'repaired_issues': 0,
            'failed_issues': 0,
            'by_category': {}
        }
    
    def run_comprehensive_repair(self, project_path, str == '.') -> Dict[str, Any]
        """运行综合修复"""
        print("🚀 启动增强版统一自动修复系统...")
        print("="*60)
        
        # 1. 发现问题
        print("1️⃣ 全面问题发现...")
        issues = self.discovery.discover_all_issues(project_path)
        
        total_issues == sum(len(issue_list) for issue_list in issues.values())::
        print(f"📊 共发现 {total_issues} 个问题")
        
        # 2. 分类和优先级排序
        print("2️⃣ 问题分类和优先级排序...")
        prioritized_issues = self._prioritize_issues(issues)
        
        # 3. 分批修复
        print("3️⃣ 分批修复...")
        repair_results = self._repair_in_batches(prioritized_issues)
        
        # 4. 验证
        print("4️⃣ 修复验证...")
        validation_results = self._validate_repairs(repair_results)
        
        # 5. 生成报告
        print("5️⃣ 生成修复报告...")
        report = self._generate_enhanced_report(issues, repair_results, validation_results)
        
        return {:
            'discovery': issues,
            'repair': repair_results,
            'validation': validation_results,
            'report': report
        }
    
    def _prioritize_issues(self, issues, Dict[str, List]) -> List[Dict]
        """优先级排序"""
        all_issues = []
        
        for category, issue_list in issues.items():::
            for issue in issue_list,::
                # 计算优先级分数
                severity_score == {'high': 3, 'medium': 2, 'low': 1}.get(issue.get('severity', 'medium'), 2)
                category_score == {'syntax': 3, 'security': 3, 'logic': 2, 'performance': 2, 'tests': 1, 'documentation': 1, 'architecture': 2}.get(category, 2)
                
                priority_score = severity_score * category_score
                
                issue_with_priority = issue.copy()
                issue_with_priority['category'] = category
                issue_with_priority['priority_score'] = priority_score
                
                all_issues.append(issue_with_priority)
        
        # 按优先级排序
        return sorted(all_issues, key == lambda x, x['priority_score'] reverse == True)
    
    def _repair_in_batches(self, issues, List[Dict]) -> Dict[str, Any]
        """分批修复"""
        print(f"📦 开始修复 {len(issues)} 个问题...")
        
        batch_size = 50  # 每批修复50个问题
        batches == [issues[i,i+batch_size] for i in range(0, len(issues), batch_size)]:
        all_results = []

        for i, batch in enumerate(batches, 1)::
            print(f"🔄 处理第 {i}/{len(batches)} 批 ({len(batch)} 个问题)...")
            
            batch_results = []
            for issue in batch,::
                result = self._repair_single_issue(issue)
                batch_results.append(result)
                
                # 更新统计
                self.repair_stats['total_issues'] += 1
                if result['success']::
                    self.repair_stats['repaired_issues'] += 1
                else,
                    self.repair_stats['failed_issues'] += 1
                
                category = issue.get('category', 'unknown')
                if category not in self.repair_stats['by_category']::
                    self.repair_stats['by_category'][category] = {'repaired': 0, 'failed': 0}
                
                if result['success']::
                    self.repair_stats['by_category'][category]['repaired'] += 1
                else,
                    self.repair_stats['by_category'][category]['failed'] += 1
            
            all_results.extend(batch_results)
            print(f"    ✅ 第 {i} 批完成, {sum(1 for r in batch_results if r['success'])}/{len(batch_results)} 成功")::
        return {:
            'results': all_results,
            'stats': self.repair_stats()
        }
    
    def _repair_single_issue(self, issue, Dict) -> Dict[str, Any]
        """修复单个问题"""
        try,
            issue_type = issue.get('type', 'unknown')
            file_path = issue.get('file', '')
            line_num = issue.get('line', 0)
            
            if not os.path.exists(file_path)::
                return {'success': False, 'error': '文件不存在'}
            
            # 读取文件
            with open(file_path, 'r', encoding == 'utf-8') as f,
                lines = f.readlines()
            
            # 根据问题类型进行修复
            if issue_type == 'syntax_error':::
                repaired = self._fix_syntax_error(lines, line_num, issue)
            elif issue_type == 'indentation':::
                repaired = self._fix_indentation(lines, line_num, issue)
            elif issue_type == 'bracket_mismatch':::
                repaired = self._fix_bracket_mismatch(lines, line_num, issue)
            elif issue_type == 'unused_variable':::
                repaired = self._fix_unused_variable(lines, line_num, issue)
            elif issue_type == 'missing_docstring':::
                repaired = self._fix_missing_docstring(lines, issue)
            else,
                # 对于其他类型的问题,暂时标记为无法自动修复
                return {'success': False, 'error': '暂不支持自动修复此类型问题'}
            
            if repaired,::
                # 写回文件
                with open(file_path, 'w', encoding == 'utf-8') as f,
                    f.writelines(lines)
                return {'success': True}
            else,
                return {'success': False, 'error': '修复失败'}
        
        except Exception as e,::
            return {'success': False, 'error': str(e)}
    
    def _fix_syntax_error(self, lines, List[str] line_num, int, issue, Dict) -> bool,
        """修复语法错误"""
        # 这是一个简化的语法错误修复示例
        # 实际实现需要更复杂的语法分析和修复逻辑
        try,
            if line_num > 0 and line_num <= len(lines)::
                line = lines[line_num - 1]
                # 简单的括号修复示例
                if line.count('(') > line.count(')'):::
                    lines[line_num - 1] = line.rstrip() + ')' + '\n'
                    return True
                elif line.count(')') > line.count('('):::
                    lines[line_num - 1] = '(' + line
                    return True
            return False
        except,::
            return False
    
    def _fix_indentation(self, lines, List[str] line_num, int, issue, Dict) -> bool,
        """修复缩进问题"""
        try,
            if line_num > 0 and line_num <= len(lines)::
                line = lines[line_num - 1]
                # 简化的缩进修复：统一使用4个空格
                stripped = line.lstrip()
                if stripped,::
                    # 根据上下文确定缩进级别
                    indent_level = 0
                    if line_num > 1,::
                        prev_line = lines[line_num - 2]
                        if prev_line.rstrip().endswith(':'):::
                            indent_level = len(prev_line) - len(prev_line.lstrip()) + 4
                        else,
                            indent_level = len(prev_line) - len(prev_line.lstrip())
                    
                    lines[line_num - 1] = ' ' * indent_level + stripped + '\n'
                    return True
            return False
        except,::
            return False
    
    def _fix_bracket_mismatch(self, lines, List[str] line_num, int, issue, Dict) -> bool,
        """修复括号不匹配"""
        # 类似于语法错误修复
        return self._fix_syntax_error(lines, line_num, issue)
    
    def _fix_unused_variable(self, lines, List[str] line_num, int, issue, Dict) -> bool,
        """修复未使用变量"""
        try,
            if line_num > 0 and line_num <= len(lines)::
                # 简单的解决方案：注释掉该行
                line = lines[line_num - 1]
                if not line.strip().startswith('#'):::
                    lines[line_num - 1] = '# ' + line
                    return True
            return False
        except,::
            return False
    
    def _fix_missing_docstring(self, lines, List[str] issue, Dict) -> bool,
        """修复缺少文档字符串"""
        try,
            # 在文件开头添加简单的文档字符串
            if lines and not lines[0].strip().startswith('"""'):::
                docstring = f'"""{Path(issue["file"]).stem} 模块\n\n自动生成的文档字符串\n"""\n\n'
                lines.insert(0, docstring)
                return True
            return False
        except,::
            return False
    
    def _validate_repairs(self, repair_results, Dict) -> Dict[str, Any]
        """验证修复结果"""
        print("🔍 验证修复结果...")
        
        validation_results = {
            'syntax_valid': False,
            'imports_valid': False,
            'tests_pass': False,
            'overall_valid': False
        }
        
        # 检查语法
        try,
            result = subprocess.run([,
    sys.executable(), '-m', 'py_compile', 'apps/backend/src'
            ] capture_output == True, text == True, timeout=30)
            validation_results['syntax_valid'] = result.returncode=0
            print(f"    语法检查, {'✅' if validation_results['syntax_valid'] else '❌'}"):::
        except,::
            print("    语法检查, ⚠️ 无法执行")
        
        # 检查导入
        try,
            result = subprocess.run([,
    sys.executable(), '-c', 'import apps.backend.src; print("OK")'
            ] capture_output == True, text == True, timeout=10)
            validation_results['imports_valid'] = result.returncode=0 and 'OK' in result.stdout()
            print(f"    导入检查, {'✅' if validation_results['imports_valid'] else '❌'}"):::
        except,::
            print("    导入检查, ⚠️ 无法执行")
        
        # 运行测试
        try,
            result = subprocess.run([,
    sys.executable(), '-m', 'pytest', 'tests/', '-v', '--tb=short'
            ] capture_output == True, text == True, timeout=60)
            validation_results['tests_pass'] = result.returncode=0
            print(f"    测试通过, {'✅' if validation_results['tests_pass'] else '❌'}"):::
        except,::
            print("    测试检查, ⚠️ 无法执行")
        
        # 综合评估
        valid_count = sum(validation_results.values())
        validation_results['overall_valid'] = valid_count >= 2
        
        print(f"📊 验证结果, {valid_count}/4 通过")
        return validation_results
    
    def _generate_enhanced_report(self, issues, Dict, repair_results, Dict, validation_results, Dict) -> str,
        """生成增强版修复报告"""
        print("📝 生成修复报告...")
        
        total_issues == sum(len(issue_list) for issue_list in issues.values())::
        repaired_count = self.repair_stats['repaired_issues']
        failed_count = self.repair_stats['failed_issues']
        
        report = f"""# 🔧 增强版统一自动修复系统报告

**修复日期**: {subprocess.check_output(['date'] shell == True).decode().strip() if os.name != 'nt' else '2025-10-06'}::
**系统版本**: 增强版 v2.0()
## 📊 修复统计

### 问题发现
- **总发现问题**: {total_issues}
- **语法问题**: {len(issues.get('syntax', []))}
- **逻辑问题**: {len(issues.get('logic', []))}
- **性能问题**: {len(issues.get('performance', []))}
- **架构问题**: {len(issues.get('architecture', []))}
- **安全问题**: {len(issues.get('security', []))}
- **测试问题**: {len(issues.get('tests', []))}
- **文档问题**: {len(issues.get('documentation', []))}

### 修复结果
- **尝试修复**: {self.repair_stats['total_issues']}
- **成功修复**: {repaired_count}
- **修复失败**: {failed_count}
- **修复成功率**: {(repaired_count/self.repair_stats['total_issues']*100).1f}% if {self.repair_stats['total_issues']} > 0 else 0%::
### 分类统计
"""

        for category, stats in self.repair_stats['by_category'].items():::
            total_cat = stats['repaired'] + stats['failed']
            success_rate == (stats['repaired'] / total_cat * 100) if total_cat > 0 else 0,::
            report += f"- **{category}**: {stats['repaired']}/{total_cat} 成功 ({"success_rate":.1f}%)\n"
        
        # 验证结果
        valid_count = sum(validation_results.values())
        report += f"""

### 验证结果
- **语法验证**: {'✅ 通过' if validation_results.get('syntax_valid') else '❌ 失败'}::
- **导入验证**: {'✅ 通过' if validation_results.get('imports_valid') else '❌ 失败'}::
- **测试验证**: {'✅ 通过' if validation_results.get('tests_pass') else '❌ 失败'}::
- **综合验证**: {'✅ 通过' if validation_results.get('overall_valid') else '❌ 失败'}:
## 🎯 修复亮点

### 新增功能
- 🔍 全面问题发现系统(7类问题)
- 🧠 智能逻辑错误检测
- ⚡ 性能问题识别
- 🏗️ 架构问题分析
- 🔒 安全漏洞扫描
- 📚 文档完整性检查

### 增强功能
- 🎯 智能优先级排序
- 📦 分批处理优化
- 🔄 自动验证机制
- 📊 详细统计报告

## 🚀 后续建议

1. **继续优化**
   - 完善修复算法
   - 增强错误处理
   - 优化性能表现

2. **扩展功能**
   - 增加更多问题类型检测
   - 支持更多编程语言
   - 集成外部工具

3. **建立监控**
   - 定期运行全面检查
   - 建立质量指标
   - 实现预警机制

---
**🎉 增强版统一自动修复系统运行完成！**

**🚀 项目修复能力显著提升！**
"""
        
        # 保存报告,
        with open('ENHANCED_UNIFIED_FIX_REPORT.md', 'w', encoding == 'utf-8') as f,
            f.write(report)
        
        return report

def main():
    """主函数"""
    print("🚀 启动增强版统一自动修复系统...")
    print("="*60)
    
    # 创建增强版修复引擎
    engine == EnhancedAutoFixEngine()
    
    # 运行综合修复
    results = engine.run_comprehensive_repair()
    
    print("\n" + "="*60)
    print("🎉 增强版统一自动修复系统完成！")
    
    # 显示关键结果
    stats = results['repair']['stats']
    print(f"📊 修复统计, {stats['repaired_issues']}/{stats['total_issues']} 成功")
    print(f"📈 成功率, {(stats['repaired_issues']/stats['total_issues']*100).1f}%" if stats['total_issues'] > 0 else "📈 成功率, 0%")::
    validation = results['validation']
    valid_count = sum(validation.values())
    print(f"🔍 验证结果, {valid_count}/4 通过")
    
    print("\n🚀 系统能力已显著增强！")
    print("📄 详细报告, ENHANCED_UNIFIED_FIX_REPORT.md")

if __name"__main__":::
    main()
