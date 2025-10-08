#!/usr/bin/env python3
"""
文档检测器
分析项目中的文档问题
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

class DocumentationDetector:
    """文档问题检测器"""
    
    def __init__(self):
        self.doc_issues = []
        self.file_stats = {}
    
    def scan_project_documentation(self, project_path: str = ".") -> Dict[str, Any]:
        """扫描项目文档"""
        print("🔍 扫描项目文档...")
        
        project_path = Path(project_path)
        
        # 扫描不同类型的文档文件
        doc_files = list(project_path.glob("**/*.md"))
        doc_files.extend(project_path.glob("**/*.rst"))
        doc_files.extend(project_path.glob("**/*.txt"))
        
        # 扫描代码文件中的文档字符串
        code_files = list(project_path.glob("**/*.py"))
        
        results = {
            "total_files": len(doc_files) + len(code_files),
            "doc_files": len(doc_files),
            "code_files": len(code_files),
            "issues": [],
            "recommendations": []
        }
        
        # 检查文档文件
        for doc_file in doc_files:
            issues = self.check_documentation_file(doc_file)
            results["issues"].extend(issues)
        
        # 检查代码文件中的文档
        for code_file in code_files:
            issues = self.check_code_documentation(code_file)
            results["issues"].extend(issues)
        
        return results
    
    def check_documentation_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """检查文档文件"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查空文件
            if not content.strip():
                issues.append({
                    "type": "empty_file",
                    "file": str(file_path),
                    "message": "文档文件为空",
                    "severity": "medium"
                })
                return issues
            
            # 检查标题格式
            if file_path.suffix == '.md':
                title_issues = self.check_markdown_format(content, file_path)
                issues.extend(title_issues)
            
            # 检查链接有效性
            link_issues = self.check_links(content, file_path)
            issues.extend(link_issues)
            
            # 检查图片引用
            image_issues = self.check_image_references(content, file_path)
            issues.extend(image_issues)
            
        except Exception as e:
            issues.append({
                "type": "read_error",
                "file": str(file_path),
                "message": f"无法读取文件: {e}",
                "severity": "high"
            })
        
        return issues
    
    def check_code_documentation(self, file_path: Path) -> List[Dict[str, Any]]:
        """检查代码文档"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查模块文档字符串
            if not content.strip().startswith('"""'):
                issues.append({
                    "type": "missing_module_docstring",
                    "file": str(file_path),
                    "message": "缺少模块文档字符串",
                    "severity": "low"
                })
            
            # 检查函数文档字符串
            functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', content)
            docstring_functions = re.findall(r'def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\):\s*\n\s*"""', content)
            
            if len(functions) > len(docstring_functions):
                issues.append({
                    "type": "missing_function_docstrings",
                    "file": str(file_path),
                    "message": f"{len(functions) - len(docstring_functions)} 个函数缺少文档字符串",
                    "severity": "low"
                })
            
            # 检查类文档字符串
            classes = re.findall(r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)', content)
            docstring_classes = re.findall(r'class\s+[a-zA-Z_][a-zA-Z0-9_]*[^(]*:\s*\n\s*"""', content)
            
            if len(classes) > len(docstring_classes):
                issues.append({
                    "type": "missing_class_docstrings",
                    "file": str(file_path),
                    "message": f"{len(classes) - len(docstring_classes)} 个类缺少文档字符串",
                    "severity": "low"
                })
            
        except Exception as e:
            issues.append({
                "type": "read_error",
                "file": str(file_path),
                "message": f"无法读取文件: {e}",
                "severity": "high"
            })
        
        return issues
    
    def check_markdown_format(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """检查Markdown格式"""
        issues = []
        
        lines = content.split('\n')
        
        # 检查标题层级
        prev_level = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                level = len(line.split()[0])
                if prev_level > 0 and level > prev_level + 1:
                    issues.append({
                        "type": "heading_hierarchy",
                        "file": str(file_path),
                        "line": i + 1,
                        "message": f"标题层级跳跃: 从 {prev_level} 跳到 {level}",
                        "severity": "low"
                    })
                prev_level = level
        
        return issues
    
    def check_links(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """检查链接有效性"""
        issues = []
        
        # 查找Markdown链接
        md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        for link_text, link_url in md_links:
            # 检查外部链接格式
            if link_url.startswith('http'):
                if not link_url.startswith(('http://', 'https://')):
                    issues.append({
                        "type": "invalid_url_format",
                        "file": str(file_path),
                        "message": f"无效的外部链接格式: {link_url}",
                        "severity": "medium"
                    })
            
            # 检查内部链接
            elif not link_url.startswith('#'):
                linked_path = file_path.parent / link_url
                if not linked_path.exists():
                    issues.append({
                        "type": "broken_internal_link",
                        "file": str(file_path),
                        "message": f"内部链接不存在: {link_url}",
                        "severity": "medium"
                    })
        
        return issues
    
    def check_image_references(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """检查图片引用"""
        issues = []
        
        # 查找Markdown图片
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)
        
        for alt_text, image_path in images:
            # 检查图片文件是否存在
            image_full_path = file_path.parent / image_path
            if not image_full_path.exists():
                issues.append({
                    "type": "missing_image",
                    "file": str(file_path),
                    "message": f"引用的图片文件不存在: {image_path}",
                    "severity": "medium"
                })
            
            # 检查替代文本
            if not alt_text.strip():
                issues.append({
                    "type": "missing_alt_text",
                    "file": str(file_path),
                    "message": f"图片缺少替代文本: {image_path}",
                    "severity": "low"
                })
        
        return issues
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """生成检查报告"""
        report = []
        
        report.append("# 📚 文档问题检查报告")
        report.append(f"\n**检查时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**总文件数**: {results['total_files']}")
        report.append(f"**文档文件**: {results['doc_files']}")
        report.append(f"**代码文件**: {results['code_files']}")
        report.append(f"**发现问题**: {len(results['issues'])}")
        
        if results['issues']:
            report.append("\n## ⚠️ 发现的问题")
            
            # 按严重程度分组
            high_issues = [issue for issue in results['issues'] if issue['severity'] == 'high']
            medium_issues = [issue for issue in results['issues'] if issue['severity'] == 'medium']
            low_issues = [issue for issue in results['issues'] if issue['severity'] == 'low']
            
            if high_issues:
                report.append("\n### 🔴 高严重程度问题")
                for issue in high_issues:
                    file_info = f"文件 {issue.get('file', '项目')}: " if 'file' in issue else ""
                    line_info = f" (行 {issue['line']})" if 'line' in issue else ""
                    report.append(f"- {file_info}{issue['message']}{line_info}")
            
            if medium_issues:
                report.append("\n### 🟡 中等严重程度问题")
                for issue in medium_issues:
                    file_info = f"文件 {issue.get('file', '项目')}: " if 'file' in issue else ""
                    line_info = f" (行 {issue['line']})" if 'line' in issue else ""
                    report.append(f"- {file_info}{issue['message']}{line_info}")
            
            if low_issues:
                report.append("\n### 🟢 低严重程度问题")
                for issue in low_issues:
                    file_info = f"文件 {issue.get('file', '项目')}: " if 'file' in issue else ""
                    line_info = f" (行 {issue['line']})" if 'line' in issue else ""
                    report.append(f"- {file_info}{issue['message']}{line_info}")
        
        if results['recommendations']:
            report.append("\n## 💡 建议")
            for recommendation in results['recommendations']:
                report.append(f"- {recommendation}")
        
        return "\n".join(report)

def main():
    """主函数"""
    print("🔍 启动文档问题检测器...")
    
    detector = DocumentationDetector()
    
    # 扫描项目文档
    results = detector.scan_project_documentation()
    
    # 生成报告
    report = detector.generate_report(results)
    
    # 保存报告
    report_file = "documentation_check_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📋 检查报告已保存到: {report_file}")
    print(f"🏁 检查完成，发现 {len(results['issues'])} 个问题")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)