#!/usr/bin/env python3
"""
报告生成器核心模块 - 生成各种类型的报告
"""

import json
import time
from pathlib import Path
from enum import Enum
from typing import Dict, List, Optional, Any

class ReportType(Enum):
    """报告类型枚举"""
    SUMMARY = "summary"              # 摘要报告
    DETAILED = "detailed"            # 详细报告
    TEST = "test"                    # 测试报告
    FIX = "fix"                      # 修复报告
    ENVIRONMENT = "environment"      # 环境报告
    CLEANUP = "cleanup"              # 清理报告
    PERFORMANCE = "performance"      # 性能报告
    HTML = "html"                    # HTML报告
    MARKDOWN = "markdown"            # Markdown报告

class ReportFormat(Enum):
    """报告格式枚举"""
    JSON = "json"                    # JSON格式
    HTML = "html"                    # HTML格式
    MARKDOWN = "markdown"            # Markdown格式
    TEXT = "text"                    # 文本格式
    CSV = "csv"                      # CSV格式

class ReportGenerator:
    """报告生成器"""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.reports_dir = project_root / "reports"

        # 确保报告目录存在
        self.reports_dir.mkdir(exist_ok=True)

        # 报告模板
        self.report_templates = {
            "summary": {
                "title": "项目执行摘要报告",
                "sections": ["overview", "statistics", "recommendations"]
            },
            "test": {
                "title": "测试执行报告",
                "sections": ["test_summary", "test_results", "failed_tests", "performance"]
            },
            "fix": {
                "title": "自动修复报告",
                "sections": ["fix_summary", "fix_details", "errors", "recommendations"]
            },
            "environment": {
                "title": "环境检查报告",
                "sections": ["environment_summary", "component_status", "issues", "recommendations"]
            },
            "cleanup": {
                "title": "项目清理报告",
                "sections": ["cleanup_summary", "cleanup_details", "space_saved", "recommendations"]
            }
        }

    def generate_summary_report(self, data: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """生成摘要报告"""
        if output_path is None:
            timestamp = int(time.time())
            output_path = self.reports_dir / f"summary_report_{timestamp}.json"

        report_data = {
            "report_type": "summary",
            "title": self.report_templates["summary"]["title"],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_root": str(self.project_root),
            "data": data
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            print(f"✓ 摘要报告已生成: {output_path}")
            return output_path

        except Exception as e:
            print(f"✗ 生成摘要报告时出错: {e}")
            raise

    def generate_test_report(self, test_results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
        """生成测试报告"""
        if output_path is None:
            timestamp = int(time.time())
            output_path = self.reports_dir / f"test_report_{timestamp}.json"

        # 计算测试统计信息
        total_tests = sum(r.get("tests_collected", 0) for r in test_results)
        total_passed = sum(r.get("tests_passed", 0) for r in test_results)
        total_failed = sum(r.get("tests_failed", 0) for r in test_results)
        total_skipped = sum(r.get("tests_skipped", 0) for r in test_results)
        total_duration = sum(r.get("duration", 0) for r in test_results)

        # 按测试类型分组
        grouped_results: Dict[str, List[Dict[str, Any]]] = {}
        for result in test_results:
            test_type = result.get("test_type", "unknown")
            if test_type not in grouped_results:
                grouped_results[test_type] = []
            grouped_results[test_type].append(result)

        report_data = {
            "report_type": "test",
            "title": self.report_templates["test"]["title"],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_root": str(self.project_root),
            "summary": {
                "total_tests": total_tests,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "total_skipped": total_skipped,
                "success_rate": f"{(total_passed / total_tests * 100):.1f}%" if total_tests > 0 else "0%",
                "total_duration": f"{total_duration:.2f}秒",
                "test_runs": len(test_results),
                "overall_success": total_failed == 0
            },
            "grouped_results": grouped_results,
            "detailed_results": test_results
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            print(f"✓ 测试报告已生成: {output_path}")
            return output_path

        except Exception as e:
            print(f"✗ 生成测试报告时出错: {e}")
            raise

    def generate_fix_report(self, fix_results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """生成修复报告"""
        if output_path is None:
            timestamp = int(time.time())
            output_path = self.reports_dir / f"fix_report_{timestamp}.json"

        report_data = {
            "report_type": "fix",
            "title": self.report_templates["fix"]["title"],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_root": str(self.project_root),
            "fix_summary": {
                "total_fixes": len(fix_results.get("fixes_made", [])),
                "files_processed": fix_results.get("files_processed", 0),
                "files_fixed": fix_results.get("files_fixed", 0),
                "errors_count": len(fix_results.get("errors", [])),
                "warnings_count": len(fix_results.get("warnings", [])),
                "overall_success": fix_results.get("overall_success", False)
            },
            "fix_details": fix_results.get("fixes_made", []),
            "errors": fix_results.get("errors", []),
            "warnings": fix_results.get("warnings", [])
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            print(f"✓ 修复报告已生成: {output_path}")
            return output_path

        except Exception as e:
            print(f"✗ 生成修复报告时出错: {e}")
            raise

    def generate_environment_report(self, env_results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """生成环境检查报告"""
        if output_path is None:
            timestamp = int(time.time())
            output_path = self.reports_dir / f"environment_report_{timestamp}.json"

        # 计算环境统计信息
        healthy_count = sum(1 for r in env_results.get("results", {}).values() if r.get("status") == "healthy")
        warning_count = sum(1 for r in env_results.get("results", {}).values() if r.get("status") == "warning")
        error_count = sum(1 for r in env_results.get("results", {}).values() if r.get("status") == "error")
        total_count = len(env_results.get("results", {}))

        report_data = {
            "report_type": "environment",
            "title": self.report_templates["environment"]["title"],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_root": str(self.project_root),
            "summary": {
                "total_components": total_count,
                "healthy_components": healthy_count,
                "warning_components": warning_count,
                "error_components": error_count,
                "health_percentage": f"{(healthy_count / total_count * 100):.1f}%" if total_count > 0 else "0%",
                "overall_status": env_results.get("summary", {}).get("overall_status", "unknown")
            },
            "component_results": env_results.get("results", {}),
            "recommendations": self._generate_environment_recommendations(env_results.get("results", {}))
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            print(f"✓ 环境检查报告已生成: {output_path}")
            return output_path

        except Exception as e:
            print(f"✗ 生成环境检查报告时出错: {e}")
            raise

    def generate_cleanup_report(self, cleanup_results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """生成清理报告"""
        if output_path is None:
            timestamp = int(time.time())
            output_path = self.reports_dir / f"cleanup_report_{timestamp}.json"

        report_data = {
            "report_type": "cleanup",
            "title": self.report_templates["cleanup"]["title"],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project_root": str(self.project_root),
            "summary": {
                "items_removed": cleanup_results.get("items_removed", 0),
                "space_freed_mb": round(cleanup_results.get("space_freed", 0) / (1024 * 1024), 2),
                "errors_count": len(cleanup_results.get("errors", [])),
                "warnings_count": len(cleanup_results.get("warnings", [])),
                "details_count": len(cleanup_results.get("details", []))
            },
            "cleanup_details": cleanup_results.get("details", []),
            "errors": cleanup_results.get("errors", []),
            "warnings": cleanup_results.get("warnings", [])
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            print(f"✓ 清理报告已生成: {output_path}")
            return output_path

        except Exception as e:
            print(f"✗ 生成清理报告时出错: {e}")
            raise

    def generate_html_report(self, report_data: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """生成HTML报告"""
        if output_path is None:
            timestamp = int(time.time())
            output_path = self.reports_dir / f"html_report_{timestamp}.html"

        # HTML模板
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
    .section {{ margin: 20px 0; }}
    .success {{ color: green; }}
    .warning {{ color: orange; }}
    .error {{ color: red; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    th {{ background-color: #f2f2f2; }}
    pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
    <h1>{title}</h1>
    <p>生成时间: {generated_at}</p>
    <p>项目路径: {project_root}</p>
    </div>

    {content}
</body>
</html>
        """

        # 生成内容
        content = self._generate_html_content(report_data)

        # 填充模板
        html_content = html_template.format(
            title=report_data.get("title", "项目报告"),
            generated_at=report_data.get("generated_at", ""),
            project_root=report_data.get("project_root", ""),
            content=content
        )

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"✓ HTML报告已生成: {output_path}")
            return output_path

        except Exception as e:
            print(f"✗ 生成HTML报告时出错: {e}")
            raise

    def generate_markdown_report(self, report_data: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
        """生成Markdown报告"""
        if output_path is None:
            timestamp = int(time.time())
            output_path = self.reports_dir / f"markdown_report_{timestamp}.md"

        # 生成Markdown内容
        md_content = f"""# {report_data.get("title", "项目报告")}

**生成时间:** {report_data.get("generated_at", "")}
**项目路径:** {report_data.get("project_root", "")}

{self._generate_markdown_content(report_data)}
"""

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            print(f"✓ Markdown报告已生成: {output_path}")
            return output_path

        except Exception as e:
            print(f"✗ 生成Markdown报告时出错: {e}")
            raise

    def _generate_html_content(self, data: Dict[str, Any]) -> str:
        """生成HTML内容"""
        content = ""

        if "summary" in data:
            content += "<div class='section'><h2>摘要</h2>"
            for key, value in data["summary"].items():
                content += f"<p><strong>{key}:</strong> {value}</p>"
            content += "</div>"

        if "detailed_results" in data:
            content += "<div class='section'><h2>详细结果</h2>"
            for result in data["detailed_results"]:
                status_class = "success" if result.get("success") else "error"
                content += f"<div class='{status_class}'>"
                content += f"<h3>{result.get('test_type', 'Unknown')}</h3>"
                content += f"<p>状态: {'通过' if result.get('success') else '失败'}</p>"
                content += f"<p>持续时间: {result.get('duration', 0):.2f}秒</p>"
                if result.get("errors"):
                    content += "<p>错误:</p><ul>"
                    for error in result["errors"]:
                        content += f"<li>{error}</li>"
                    content += "</ul>"
                content += "</div>"
            content += "</div>"

        return content

    def _generate_markdown_content(self, data: Dict[str, Any]) -> str:
        """生成Markdown内容"""
        content = ""

        if "summary" in data:
            content += "## 摘要\n\n"
            for key, value in data["summary"].items():
                content += f"**{key}:** {value}\n"
            content += "\n"

        if "detailed_results" in data:
            content += "## 详细结果\n\n"
            for result in data["detailed_results"]:
                status = "✅" if result.get("success") else "❌"
                content += f"### {status} {result.get('test_type', 'Unknown')}\n\n"
                content += f"- **状态:** {'通过' if result.get('success') else '失败'}\n"
                content += f"- **持续时间:** {result.get('duration', 0):.2f}秒\n"
                if result.get("errors"):
                    content += "- **错误:**\n"
                    for error in result["errors"]:
                        content += f"  - {error}\n"
                content += "\n"

        return content

    def _generate_environment_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成环境建议"""
        recommendations = []

        for component, result in results.items():
            if result.get("status") == "error":
                recommendations.append(f"修复 {component} 组件的错误")
            elif result.get("status") == "warning":
                recommendations.append(f"检查 {component} 组件的警告")

        return recommendations

    def convert_report_format(self, input_path: Path, output_format: ReportFormat, output_path: Optional[Path] = None) -> Path:
        """转换报告格式"""
        try:
            # 读取原始报告
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 根据目标格式生成报告
            if output_format == ReportFormat.HTML:
                return self.generate_html_report(data, output_path)
            elif output_format == ReportFormat.MARKDOWN:
                return self.generate_markdown_report(data, output_path)
            elif output_format == ReportFormat.JSON:
                if output_path is None:
                    output_path = input_path.with_suffix(".json")
                return self.generate_summary_report(data, output_path)
            else:
                raise ValueError(f"不支持的输出格式: {output_format.value}")

        except Exception as e:
            print(f"✗ 转换报告格式时出错: {e}")
            raise

    def list_reports(self, report_type: Optional[ReportType] = None) -> List[Path]:
        """列出报告文件"""
        reports = []

        for report_file in self.reports_dir.glob("*"):
            if report_file.is_file():
                if report_type:
                    if report_type.value in report_file.name:
                        reports.append(report_file)
                else:
                    reports.append(report_file)

        # 按修改时间排序（最新的在前）
        reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        return reports

    def cleanup_old_reports(self, keep_count: int = 10) -> None:
        """清理旧报告"""
        reports = self.list_reports()

        if len(reports) > keep_count:
            # 删除最旧的报告
            for report in reports[keep_count:]:
                try:
                    report.unlink()
                    print(f"✓ 删除旧报告: {report}")
                except Exception as e:
                    print(f"✗ 删除报告 {report} 失败: {e}")