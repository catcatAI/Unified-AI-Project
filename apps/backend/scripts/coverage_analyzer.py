#!/usr/bin/env python3
"""
测试覆盖率分析器
用于分析、统计和报告集成测试的代码覆盖率
"""

import os
import sys
import subprocess
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CoverageAnalyzer:
    """测试覆盖率分析器"""
    
    def __init__(self, project_root: str = None):
        """
        初始化覆盖率分析器
        
        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.coverage_file = self.project_root / "coverage.xml"
        self.coverage_data = None
    
    def run_coverage_analysis(self, source_dirs: List[str] = None, output_format: str = "xml") -> bool:
        """
        运行覆盖率分析
        
        Args:
            source_dirs: 要分析的源代码目录列表
            output_format: 输出格式 (xml, html, json)
            
        Returns:
            bool: 分析是否成功
        """
        logger.info("Running coverage analysis...")
        
        if source_dirs is None:
            source_dirs = ["src"]
        
        try:
            # 构建coverage命令
            cmd = [
                sys.executable,
                "-m",
                "coverage",
                "run",
                "-m",
                "pytest",
                "tests/integration/",
                "--tb=short"
            ]
            
            # 运行测试并收集覆盖率数据
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Coverage analysis failed: {result.stderr}")
                return False
            
            # 生成覆盖率报告
            report_cmd = [
                sys.executable,
                "-m",
                "coverage",
                "report",
                "-m"
            ]
            
            report_result = subprocess.run(
                report_cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if report_result.returncode != 0:
                logger.error(f"Coverage report generation failed: {report_result.stderr}")
                return False
            
            # 生成指定格式的报告
            if output_format == "xml":
                self._generate_xml_report()
            elif output_format == "html":
                self._generate_html_report()
            elif output_format == "json":
                self._generate_json_report()
            
            logger.info("Coverage analysis completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error running coverage analysis: {e}")
            return False
    
    def _generate_xml_report(self):
        """生成XML格式的覆盖率报告"""
        try:
            cmd = [
                sys.executable,
                "-m",
                "coverage",
                "xml",
                "-o",
                str(self.coverage_file)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"XML report generation failed: {result.stderr}")
            else:
                logger.info(f"XML coverage report generated: {self.coverage_file}")
                
        except Exception as e:
            logger.error(f"Error generating XML report: {e}")
    
    def _generate_html_report(self):
        """生成HTML格式的覆盖率报告"""
        try:
            html_dir = self.project_root / "htmlcov"
            cmd = [
                sys.executable,
                "-m",
                "coverage",
                "html",
                "-d",
                str(html_dir)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"HTML report generation failed: {result.stderr}")
            else:
                logger.info(f"HTML coverage report generated: {html_dir}")
                
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
    
    def _generate_json_report(self):
        """生成JSON格式的覆盖率报告"""
        try:
            cmd = [
                sys.executable,
                "-m",
                "coverage",
                "json"
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"JSON report generation failed: {result.stderr}")
            else:
                logger.info("JSON coverage report generated: coverage.json")
                
        except Exception as e:
            logger.error(f"Error generating JSON report: {e}")
    
    def parse_coverage_xml(self) -> Dict[str, Any]:
        """
        解析覆盖率XML文件
        
        Returns:
            Dict: 解析后的覆盖率数据
        """
        if not self.coverage_file.exists():
            logger.warning(f"Coverage XML file not found: {self.coverage_file}")
            return {}
        
        try:
            tree = ET.parse(self.coverage_file)
            root = tree.getroot()
            
            coverage_data = {
                "timestamp": root.get("timestamp", ""),
                "version": root.get("version", ""),
                "sources": [],
                "packages": [],
                "summary": {
                    "lines_valid": int(root.get("lines-valid", 0)),
                    "lines_covered": int(root.get("lines-covered", 0)),
                    "line_rate": float(root.get("line-rate", 0)),
                    "branches_valid": int(root.get("branches-valid", 0)),
                    "branches_covered": int(root.get("branches-covered", 0)),
                    "branch_rate": float(root.get("branch-rate", 0)),
                    "complexity": float(root.get("complexity", 0))
                }
            }
            
            # 解析源代码路径
            sources_elem = root.find("sources")
            if sources_elem is not None:
                for source_elem in sources_elem.findall("source"):
                    coverage_data["sources"].append(source_elem.text)
            
            # 解析包信息
            packages_elem = root.find("packages")
            if packages_elem is not None:
                for package_elem in packages_elem.findall("package"):
                    package_data = {
                        "name": package_elem.get("name", ""),
                        "classes": []
                    }
                    
                    # 解析类信息
                    for class_elem in package_elem.findall("classes/class"):
                        class_data = {
                            "name": class_elem.get("name", ""),
                            "filename": class_elem.get("filename", ""),
                            "line_rate": float(class_elem.get("line-rate", 0)),
                            "branch_rate": float(class_elem.get("branch-rate", 0)),
                            "complexity": float(class_elem.get("complexity", 0)),
                            "methods": [],
                            "lines": []
                        }
                        
                        # 解析方法信息
                        methods_elem = class_elem.find("methods")
                        if methods_elem is not None:
                            for method_elem in methods_elem.findall("method"):
                                method_data = {
                                    "name": method_elem.get("name", ""),
                                    "signature": method_elem.get("signature", ""),
                                    "line_rate": float(method_elem.get("line-rate", 0)),
                                    "branch_rate": float(method_elem.get("branch-rate", 0)),
                                    "complexity": float(method_elem.get("complexity", 0)),
                                    "lines": []
                                }
                                
                                # 解析方法行信息
                                lines_elem = method_elem.find("lines")
                                if lines_elem is not None:
                                    for line_elem in lines_elem.findall("line"):
                                        method_data["lines"].append({
                                            "number": int(line_elem.get("number", 0)),
                                            "hits": int(line_elem.get("hits", 0)),
                                            "branch": line_elem.get("branch", "false") == "true",
                                            "condition_coverage": line_elem.get("condition-coverage", "")
                                        })
                                
                                class_data["methods"].append(method_data)
                        
                        # 解析类行信息
                        lines_elem = class_elem.find("lines")
                        if lines_elem is not None:
                            for line_elem in lines_elem.findall("line"):
                                class_data["lines"].append({
                                    "number": int(line_elem.get("number", 0)),
                                    "hits": int(line_elem.get("hits", 0)),
                                    "branch": line_elem.get("branch", "false") == "true",
                                    "condition_coverage": line_elem.get("condition-coverage", "")
                                })
                        
                        package_data["classes"].append(class_data)
                    
                    coverage_data["packages"].append(package_data)
            
            self.coverage_data = coverage_data
            return coverage_data
            
        except Exception as e:
            logger.error(f"Error parsing coverage XML: {e}")
            return {}
    
    def analyze_coverage_by_module(self) -> Dict[str, Dict[str, float]]:
        """
        按模块分析覆盖率
        
        Returns:
            Dict: 按模块分组的覆盖率数据
        """
        if self.coverage_data is None:
            self.parse_coverage_xml()
        
        if not self.coverage_data:
            return {}
        
        module_coverage = {}
        
        # 遍历包和类，按模块分组
        for package in self.coverage_data.get("packages", []):
            package_name = package.get("name", "")
            for class_data in package.get("classes", []):
                filename = class_data.get("filename", "")
                # 从文件路径提取模块名
                if "/" in filename:
                    module_name = filename.split("/")[0]
                else:
                    module_name = package_name
                
                if module_name not in module_coverage:
                    module_coverage[module_name] = {
                        "line_rate_sum": 0,
                        "class_count": 0,
                        "total_line_rate": 0
                    }
                
                module_coverage[module_name]["line_rate_sum"] += class_data.get("line_rate", 0)
                module_coverage[module_name]["class_count"] += 1
        
        # 计算平均覆盖率
        for module_name, data in module_coverage.items():
            if data["class_count"] > 0:
                data["average_line_rate"] = data["line_rate_sum"] / data["class_count"]
            else:
                data["average_line_rate"] = 0
            
            # 删除临时计算字段
            del data["line_rate_sum"]
            del data["class_count"]
        
        return module_coverage
    
    def identify_low_coverage_areas(self, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        识别低覆盖率区域
        
        Args:
            threshold: 覆盖率阈值
            
        Returns:
            List: 低覆盖率区域列表
        """
        if self.coverage_data is None:
            self.parse_coverage_xml()
        
        if not self.coverage_data:
            return []
        
        low_coverage_areas = []
        
        # 遍历包和类，找出低覆盖率的类
        for package in self.coverage_data.get("packages", []):
            package_name = package.get("name", "")
            for class_data in package.get("classes", []):
                line_rate = class_data.get("line_rate", 0)
                if line_rate < threshold:
                    low_coverage_areas.append({
                        "package": package_name,
                        "class": class_data.get("name", ""),
                        "filename": class_data.get("filename", ""),
                        "line_rate": line_rate,
                        "branch_rate": class_data.get("branch_rate", 0)
                    })
        
        # 按行覆盖率排序
        low_coverage_areas.sort(key=lambda x: x["line_rate"])
        return low_coverage_areas
    
    def generate_coverage_report(self, output_file: str = None) -> str:
        """
        生成覆盖率报告
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            str: 生成的报告路径
        """
        if self.coverage_data is None:
            self.parse_coverage_xml()
        
        if not self.coverage_data:
            logger.error("No coverage data available")
            return ""
        
        if output_file is None:
            output_file = self.project_root / "coverage_analysis_report.json"
        else:
            output_file = Path(output_file)
        
        # 分析模块覆盖率
        module_coverage = self.analyze_coverage_by_module()
        
        # 识别低覆盖率区域
        low_coverage_areas = self.identify_low_coverage_areas()
        
        # 构建报告数据
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "coverage_summary": self.coverage_data.get("summary", {}),
            "module_coverage": module_coverage,
            "low_coverage_areas": low_coverage_areas,
            "recommendations": self._generate_recommendations(low_coverage_areas)
        }
        
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Coverage analysis report generated: {output_file}")
            return str(output_file)
        except Exception as e:
            logger.error(f"Error generating coverage report: {e}")
            return ""
    
    def _generate_recommendations(self, low_coverage_areas: List[Dict[str, Any]]) -> List[str]:
        """
        生成改进建议
        
        Args:
            low_coverage_areas: 低覆盖率区域列表
            
        Returns:
            List: 改进建议列表
        """
        recommendations = []
        
        if not low_coverage_areas:
            recommendations.append("Overall coverage is good. No immediate improvements needed.")
            return recommendations
        
        # 按模块分组低覆盖率区域
        module_areas = {}
        for area in low_coverage_areas:
            module = area["package"]
            if module not in module_areas:
                module_areas[module] = []
            module_areas[module].append(area)
        
        # 为每个模块生成建议
        for module, areas in module_areas.items():
            avg_line_rate = sum(area["line_rate"] for area in areas) / len(areas)
            recommendations.append(
                f"Module '{module}' has low coverage ({avg_line_rate:.2%}). "
                f"Consider adding tests for {len(areas)} classes."
            )
        
        # 通用建议
        recommendations.append(
            "Consider focusing on the lowest coverage areas first: "
            f"{', '.join([area['class'] for area in low_coverage_areas[:3]])}"
        )
        
        recommendations.append(
            "Implement targeted testing strategies for uncovered branches and edge cases."
        )
        
        return recommendations


def main():
    """主函数"""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Coverage Analyzer")
    parser.add_argument(
        "action",
        choices=["analyze", "report", "low-coverage", "recommend"],
        help="Action to perform"
    )
    parser.add_argument(
        "--source-dirs",
        nargs="+",
        default=["src"],
        help="Source directories to analyze"
    )
    parser.add_argument(
        "--format",
        choices=["xml", "html", "json"],
        default="xml",
        help="Output format for coverage analysis"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Coverage threshold for identifying low coverage areas"
    )
    parser.add_argument(
        "--output",
        help="Output file for reports"
    )
    
    args = parser.parse_args()
    
    # 创建覆盖率分析器
    analyzer = CoverageAnalyzer()
    
    # 执行操作
    if args.action == "analyze":
        success = analyzer.run_coverage_analysis(args.source_dirs, args.format)
        sys.exit(0 if success else 1)
        
    elif args.action == "report":
        # 运行分析并生成报告
        if analyzer.run_coverage_analysis(args.source_dirs, "xml"):
            report_file = analyzer.generate_coverage_report(args.output)
            if report_file:
                print(f"Coverage report generated: {report_file}")
            else:
                print("Failed to generate coverage report")
                sys.exit(1)
        else:
            print("Coverage analysis failed")
            sys.exit(1)
            
    elif args.action == "low-coverage":
        # 识别低覆盖率区域
        analyzer.parse_coverage_xml()
        low_coverage_areas = analyzer.identify_low_coverage_areas(args.threshold)
        
        if low_coverage_areas:
            print(f"Found {len(low_coverage_areas)} low coverage areas:")
            for area in low_coverage_areas:
                print(f"  - {area['package']}.{area['class']}: "
                      f"Line Rate {area['line_rate']:.2%}, "
                      f"Branch Rate {area['branch_rate']:.2%}")
        else:
            print("No low coverage areas found")
            
    elif args.action == "recommend":
        # 生成改进建议
        analyzer.parse_coverage_xml()
        low_coverage_areas = analyzer.identify_low_coverage_areas(args.threshold)
        recommendations = analyzer._generate_recommendations(low_coverage_areas)
        
        print("Coverage Improvement Recommendations:")
        for i, recommendation in enumerate(recommendations, 1):
            print(f"  {i}. {recommendation}")


if __name__ == "__main__":
    main()