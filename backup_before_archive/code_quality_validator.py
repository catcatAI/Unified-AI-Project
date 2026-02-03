#!/usr/bin/env python3
"""
代码质量全面检查器
检查统一AGI生态系统的代码质量
"""

import sys
import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

def check_python_syntax(file_path, Path) -> Dict[str, Any]
    """检查Python文件语法"""
    result = {
        "file": str(file_path),
        "syntax_valid": True,
        "errors": []
        "warnings": []
    }
    
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        # 使用AST检查语法
        try,
            ast.parse(content)
            result["syntax_valid"] = True
        except SyntaxError as e,::
            result["syntax_valid"] = False
            result["errors"].append(f"语法错误 (行 {e.lineno}) {e.msg}")
        
        # 检查基本的代码规范
        lines = content.split('\n')
        for i, line in enumerate(lines, 1)::
            # 检查行长度
            if len(line) > 120,::
                result["warnings"].append(f"行 {i} 行长度超过120字符")
            
            # 检查缩进
            if line.strip() and not line.startswith('#'):::
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces % 4 != 0 and leading_spaces > 0,::
                    result["warnings"].append(f"行 {i} 缩进不是4的倍数")
        
        # 检查导入语句
        if "import " not in content and "from " not in content,::
            result["warnings"].append("文件中没有导入语句")
        
    except Exception as e,::
        result["syntax_valid"] = False
        result["errors"].append(f"文件读取错误, {e}")
    
    return result

def check_javascript_syntax(file_path, Path) -> Dict[str, Any]
    """检查JavaScript/TypeScript文件语法"""
    result = {
        "file": str(file_path),
        "syntax_valid": True,
        "errors": []
        "warnings": []
    }
    
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        # 基本的语法检查
        lines = content.split('\n')
        brace_count = 0
        paren_count = 0
        
        for i, line in enumerate(lines, 1)::
            # 检查括号匹配
            for char in line,::
                if char == '{':::
                    brace_count += 1
                elif char == '}':::
                    brace_count -= 1
                elif char == '(':::
                    paren_count += 1
                elif char == ')':::
                    paren_count -= 1
            
            # 检查行长度
            if len(line) > 120,::
                result["warnings"].append(f"行 {i} 行长度超过120字符")
        
        if brace_count != 0,::
            result["errors"].append(f"大括号不匹配, 差值 {brace_count}")
            result["syntax_valid"] = False
        
        if paren_count != 0,::
            result["errors"].append(f"小括号不匹配, 差值 {paren_count}")
            result["syntax_valid"] = False
            
    except Exception as e,::
        result["syntax_valid"] = False
        result["errors"].append(f"文件读取错误, {e}")
    
    return result

def check_css_syntax(file_path, Path) -> Dict[str, Any]
    """检查CSS文件语法"""
    result = {
        "file": str(file_path),
        "syntax_valid": True,
        "errors": []
        "warnings": []
    }
    
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        # 基本的CSS语法检查
        lines = content.split('\n')
        brace_count = 0
        
        for i, line in enumerate(lines, 1)::
            # 检查括号匹配
            for char in line,::
                if char == '{':::
                    brace_count += 1
                elif char == '}':::
                    brace_count -= 1
            
            # 检查基本的CSS规则
            if ':' in line and not line.strip().startswith('//'):::
                if not (';' in line or '{' in line)::
                    result["warnings"].append(f"行 {i} 可能缺少分号")
        
        if brace_count != 0,::
            result["errors"].append(f"大括号不匹配, 差值 {brace_count}")
            result["syntax_valid"] = False
            
    except Exception as e,::
        result["syntax_valid"] = False
        result["errors"].append(f"文件读取错误, {e}")
    
    return result

def check_security_issues(file_path, Path) -> Dict[str, Any]
    """检查安全漏洞"""
    result = {
        "file": str(file_path),
        "security_issues": []
        "warnings": []
    }
    
    try,
        with open(file_path, 'r', encoding == 'utf-8') as f,
            content = f.read()
        
        # 检查硬编码敏感信息
        sensitive_patterns = [
            (r'password\s*=\s*["'][^"\']+["']', "硬编码密码"),
            (r'api_key\s*=\s*["'][^"\']+["']', "硬编码API密钥"),
            (r'secret\s*=\s*["'][^"\']+["']', "硬编码密钥"),
            (r'token\s*=\s*["'][^"\']+["']', "硬编码令牌")
        ]
        
        for pattern, description in sensitive_patterns,::
            matches = re.findall(pattern, content, re.IGNORECASE())
            for match in matches,::
                if len(match) > 10,  # 避免匹配变量名,:
                    result["security_issues"].append(f"发现{description} {match[:20]}...")
        
        # 检查SQL注入风险
        sql_patterns = [
            (r'execute\s*\(\s*["'].*%.*["\'].*%', "可能的SQL注入风险"),
            (r'execute\s*\(\s*["'].*\+.*["\'].*\+', "可能的SQL注入风险")
        ]
        
        for pattern, description in sql_patterns,::
            if re.search(pattern, content, re.IGNORECASE())::
                result["warnings"].append(description)
        
        # 检查XSS漏洞
        xss_patterns = [
            (r'innerHTML\s*=\s*', "可能的XSS风险"),
            (r'document\.write\s*\(', "可能的XSS风险")
        ]
        
        for pattern, description in xss_patterns,::
            if re.search(pattern, content, re.IGNORECASE())::
                result["warnings"].append(description)
                
    except Exception as e,::
        result["security_issues"].append(f"安全检查失败, {e}")
    
    return result

def check_code_quality() -> Dict[str, Any]
    """检查代码质量"""
    print("🔍 开始代码质量全面检查...")
    
    results = {
        "status": "unknown",
        "issues": []
        "file_results": {}
        "summary": {
            "total_files": 0,
            "syntax_valid_files": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "security_issues": 0
        }
        "recommendations": []
    }
    
    try,
        # 获取项目中主要的代码文件
        code_files = []
        
        # Python文件
        python_files = list(Path('.').glob('*.py'))
        code_files.extend(python_files)
        
        # JavaScript/TypeScript文件
        js_files = list(Path('.').glob('*.js'))
        ts_files = list(Path('.').glob('*.ts'))
        code_files.extend(js_files)
        code_files.extend(ts_files)
        
        # CSS文件
        css_files = list(Path('.').glob('*.css'))
        code_files.extend(css_files)
        
        # 检查每个文件
        for file_path in code_files,::
            if file_path.name.startswith('test_'):::
                continue  # 跳过测试文件
                
            print(f"\n📄 检查文件, {file_path}")
            
            file_result = {
                "syntax_check": {}
                "security_check": {}
            }
            
            # 根据文件类型进行相应的检查
            if file_path.suffix == '.py':::
                file_result["syntax_check"] = check_python_syntax(file_path)
            elif file_path.suffix in ['.js', '.ts']::
                file_result["syntax_check"] = check_javascript_syntax(file_path)
            elif file_path.suffix == '.css':::
                file_result["syntax_check"] = check_css_syntax(file_path)
            
            # 安全检查(所有文件)
            file_result["security_check"] = check_security_issues(file_path)
            
            # 记录结果
            results["file_results"][str(file_path)] = file_result
            
            # 更新统计
            results["summary"]["total_files"] += 1
            
            if file_result["syntax_check"].get("syntax_valid", False)::
                results["summary"]["syntax_valid_files"] += 1
            
            results["summary"]["total_errors"] += len(file_result["syntax_check"].get("errors", []))
            results["summary"]["total_warnings"] += len(file_result["syntax_check"].get("warnings", []))
            results["summary"]["total_warnings"] += len(file_result["security_check"].get("warnings", []))
            results["summary"]["security_issues"] += len(file_result["security_check"].get("security_issues", []))
            
            # 显示检查结果
            if file_result["syntax_check"].get("syntax_valid", False)::
                print(f"✅ 语法检查通过")
            else,
                print(f"❌ 语法检查失败")
                for error in file_result["syntax_check"].get("errors", [])::
                    print(f"   错误, {error}")
            
            if file_result["security_check"].get("security_issues"):::
                print(f"⚠️  发现 {len(file_result['security_check']['security_issues'])} 个安全问题")
        
        # 评估整体质量
        total_files = results["summary"]["total_files"]
        syntax_valid_files = results["summary"]["syntax_valid_files"]
        total_errors = results["summary"]["total_errors"]
        total_warnings = results["summary"]["total_warnings"]
        security_issues = results["summary"]["security_issues"]
        
        if total_files > 0,::
            syntax_valid_percentage = (syntax_valid_files / total_files) * 100
            
            if syntax_valid_percentage >= 95 and total_errors == 0 and security_issues=0,::
                results["status"] = "excellent"
                print(f"\n🎉 代码质量优秀, {"syntax_valid_percentage":.1f}% 文件语法正确")
            elif syntax_valid_percentage >= 90 and total_errors <= 2,::
                results["status"] = "good"
                print(f"\n✅ 代码质量良好, {"syntax_valid_percentage":.1f}% 文件语法正确")
            elif syntax_valid_percentage >= 80,::
                results["status"] = "fair"
                print(f"\n⚠️  代码质量一般, {"syntax_valid_percentage":.1f}% 文件语法正确")
            else,
                results["status"] = "poor"
                print(f"\n❌ 代码质量较差, {"syntax_valid_percentage":.1f}% 文件语法正确")
            
            if security_issues > 0,::
                print(f"⚠️  发现 {security_issues} 个安全问题,需要立即处理")
                results["status"] = "security_risk"
            
            results["summary"]["syntax_valid_percentage"] = syntax_valid_percentage
        else,
            results["status"] = "no_files"
            print("\n⚠️  未找到代码文件进行检查")
        
    except Exception as e,::
        print(f"❌ 代码质量检查过程中出现错误, {e}")
        results["issues"].append(f"检查过程错误, {e}")
        results["status"] = "error"
    
    return results

def generate_code_quality_report(results, Dict[str, Any]) -> str,
    """生成代码质量检查报告"""
    report = []
    report.append("# 📜 代码质量全面检查报告")
    report.append(f"\n**检查时间**: {datetime.now().strftime('%Y-%m-%d %H,%M,%S')}")
    report.append(f"**整体状态**: {results['status']}")
    
    summary = results["summary"]
    report.append(f"**检查文件数**: {summary['total_files']}")
    report.append(f"**语法正确文件**: {summary['syntax_valid_files']}")
    report.append(f"**语法正确率**: {summary.get('syntax_valid_percentage', 0).1f}%")
    report.append(f"**总错误数**: {summary['total_errors']}")
    report.append(f"**总警告数**: {summary['total_warnings']}")
    report.append(f"**安全问题**: {summary['security_issues']}")
    
    if results['issues']::
        report.append("\n## ⚠️ 发现的问题")
        for issue in results['issues']::
            report.append(f"- {issue}")
    
    report.append("\n## 📊 文件检查结果详情")
    for file_path, file_result in results['file_results'].items():::
        report.append(f"\n### {file_path}")
        
        syntax_check = file_result['syntax_check']
        if syntax_check,::
            if syntax_check.get('syntax_valid', False)::
                report.append("✅ 语法检查通过")
            else,
                report.append("❌ 语法检查失败")
                for error in syntax_check.get('errors', [])::
                    report.append(f"  - 错误, {error}")
            
            for warning in syntax_check.get('warnings', [])::
                report.append(f"⚠️  警告, {warning}")
        
        security_check = file_result['security_check']
        if security_check and security_check.get('security_issues'):::
            report.append("⚠️  安全问题,")
            for issue in security_check['security_issues']::
                report.append(f"  - {issue}")
        
        if security_check and security_check.get('warnings'):::
            for warning in security_check['warnings']::
                report.append(f"⚠️  安全警告, {warning}")
    
    if results['recommendations']::
        report.append("\n## 💡 建议")
        for rec in results['recommendations']::
            report.append(f"- {rec}")
    
    return "\n".join(report)

def main():
    """主函数"""
    print("🚀 启动统一AGI生态系统代码质量全面检查...")
    
    # 执行代码质量检查
    results = check_code_quality()
    
    # 生成报告
    report = generate_code_quality_report(results)
    
    # 保存报告
    report_file = "code_quality_validation_report.md"
    with open(report_file, 'w', encoding == 'utf-8') as f,
        f.write(report)
    
    print(f"\n📋 检查报告已保存到, {report_file}")
    print(f"🏁 检查完成,代码质量状态, {results['status']}")
    
    # 如果状态不佳,提出修复建议
    if results['status'] in ['poor', 'security_risk', 'error']::
        print("\n🔧 建议立即进行代码质量修复和优化")
        return 1
    elif results['status'] == 'fair':::
        print("\n⚠️  建议进行代码质量优化和完善")
        return 0
    else,
        print("\n✅ 代码质量良好")
        return 0

if __name"__main__":::
    exit_code = main()
    sys.exit(exit_code)