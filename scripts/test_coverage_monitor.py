#!/usr/bin/env python3
"""
测试覆盖率监控脚本
用于监控和报告项目的测试覆盖率
"""

import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class TestCoverageMonitor:
    """测试覆盖率监控器"""
    
    def __init__(self, project_root: str = None) -> None:
        """初始化监控器"""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.coverage_dir = self.project_root / "coverage_reports"
        self.coverage_dir.mkdir(exist_ok=True)
        
    def run_coverage_analysis(self, output_format: str = "json") -> Dict[str, Any]:
        """
        运行覆盖率分析
        
        Args:
            _ = output_format: 输出格式 (json, html, xml)
            
        Returns:
            覆盖率分析结果
        """
        _ = print("🚀 开始运行覆盖率分析...")
        
        # 构建pytest-cov命令
        cmd = [
            "python", "-m", "pytest",
            "--cov=apps/backend/src",
            "--cov-report=json",
            "--cov-report=html",
            "--cov-report=xml",
            "--cov-report=term",
            "--cov-fail-under=0",  # 暂时不设置最低覆盖率要求
            "-v"
        ]
        
        try:
            # 执行测试和覆盖率分析
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                _ = print(f"❌ 测试执行失败: {result.stderr}")
                return {"error": "Test execution failed", "details": result.stderr}
            
            # 解析覆盖率数据
            coverage_data = self._parse_coverage_data()
            coverage_data["timestamp"] = datetime.now().isoformat()
            coverage_data["test_output"] = result.stdout
            
            _ = print("✅ 覆盖率分析完成")
            return coverage_data
            
        except subprocess.TimeoutExpired:
            _ = print("❌ 覆盖率分析超时")
            return {"error": "Coverage analysis timeout"}
        except Exception as e:
            _ = print(f"❌ 覆盖率分析出错: {e}")
            return {"error": str(e)}
    
    def _parse_coverage_data(self) -> Dict[str, Any]:
        """解析覆盖率数据"""
        coverage_file = self.project_root / ".coverage"
        json_report = self.project_root / "coverage.json"
        
        if not json_report.exists():
            return {"error": "Coverage JSON report not found"}
        
        try:
            with open(json_report, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取关键指标
            summary = data.get("meta", {}).get("summary", {})
            coverage_stats = {
                _ = "total_coverage": summary.get("percent_covered", 0),
                _ = "covered_lines": summary.get("covered_lines", 0),
                _ = "missing_lines": summary.get("missing_lines", 0),
                _ = "total_lines": summary.get("num_statements", 0),
                _ = "files_count": len(data.get("files", {}))
            }
            
            # 按文件分析覆盖率
            file_coverage = {}
            for file_path, file_data in data.get("files", {}).items():
                file_coverage[file_path] = {
                    _ = "coverage": file_data.get("summary", {}).get("percent_covered", 0),
                    _ = "covered_lines": file_data.get("summary", {}).get("covered_lines", 0),
                    _ = "missing_lines": file_data.get("summary", {}).get("missing_lines", 0),
                    _ = "total_lines": file_data.get("summary", {}).get("num_statements", 0)
                }
            
            coverage_stats["file_coverage"] = file_coverage
            
            return coverage_stats
            
        except Exception as e:
            _ = print(f"❌ 解析覆盖率数据出错: {e}")
            return {"error": f"Failed to parse coverage data: {e}"}
    
    def check_coverage_thresholds(self, coverage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查覆盖率阈值
        
        Args:
            coverage_data: 覆盖率数据
            
        Returns:
            阈值检查结果
        """
        if "error" in coverage_data:
            return coverage_data
            
        total_coverage = coverage_data.get("total_coverage", 0)
        thresholds = {
            "minimum_required": 85.0,  # 最低要求85%
            "target": 90.0,            # 目标90%
            "excellent": 95.0          # 优秀95%
        }
        
        results = {
            "thresholds": thresholds,
            "current_coverage": total_coverage,
            "meets_minimum": total_coverage >= thresholds["minimum_required"],
            "meets_target": total_coverage >= thresholds["target"],
            "meets_excellent": total_coverage >= thresholds["excellent"]
        }
        
        # 检查各文件的覆盖率
        file_results = {}
        for file_path, file_stats in coverage_data.get("file_coverage", {}).items():
            file_coverage = file_stats.get("coverage", 0)
            file_results[file_path] = {
                "coverage": file_coverage,
                "below_minimum": file_coverage < thresholds["minimum_required"],
                "below_target": file_coverage < thresholds["target"]
            }
        
        results["file_results"] = file_results
        
        return results
    
    def generate_coverage_report(self, coverage_data: Dict[str, Any], format: str = "json") -> str:
        """
        生成覆盖率报告
        
        Args:
            coverage_data: 覆盖率数据
            format: 报告格式
            
        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.coverage_dir / f"coverage_report_{timestamp}.{format}"
        
        try:
            if format == "json":
                with open(report_file, 'w', encoding='utf-8') as f:
                    json.dump(coverage_data, f, ensure_ascii=False, indent=2)
            else:
                # 对于其他格式，我们简单地保存文本报告
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(coverage_data, ensure_ascii=False, indent=2))
            
            _ = print(f"✅ 覆盖率报告已生成: {report_file}")
            return str(report_file)
            
        except Exception as e:
            _ = print(f"❌ 生成覆盖率报告失败: {e}")
            return ""
    
    def get_coverage_trend(self) -> List[Dict[str, Any]]:
        """获取覆盖率趋势"""
        trend_data = []
        
        # 查找历史报告
        for report_file in self.coverage_dir.glob("coverage_report_*.json"):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "timestamp" in data and "total_coverage" in data:
                        trend_data.append({
                            "timestamp": data["timestamp"],
                            "coverage": data["total_coverage"]
                        })
            except Exception as e:
                _ = print(f"⚠️ 读取历史报告失败 {report_file}: {e}")
        
        # 按时间排序
        trend_data.sort(key=lambda x: x["timestamp"])
        return trend_data

def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="测试覆盖率监控工具")
    parser.add_argument("--format", choices=["json", "html", "xml"], 
                       default="json", help="报告格式")
    parser.add_argument("--check-thresholds", action="store_true",
                       help="检查覆盖率阈值")
    parser.add_argument("--generate-trend", action="store_true",
                       help="生成覆盖率趋势")
    
    args = parser.parse_args()
    
    # 创建监控器实例
    monitor = TestCoverageMonitor()
    
    # 运行覆盖率分析
    coverage_data = monitor.run_coverage_analysis(args.format)
    
    if "error" in coverage_data:
        _ = print(f"❌ 覆盖率分析失败: {coverage_data['error']}")
        _ = sys.exit(1)
    
    # 生成报告
    report_path = monitor.generate_coverage_report(coverage_data, args.format)
    
    # 检查阈值
    if args.check_thresholds:
        threshold_results = monitor.check_coverage_thresholds(coverage_data)
        _ = print("\n📊 覆盖率阈值检查结果:")
        _ = print(f"   当前覆盖率: {threshold_results['current_coverage']:.2f}%")
        print(f"   满足最低要求(85%): {'✅' if threshold_results['meets_minimum'] else '❌'}")
        print(f"   满足目标要求(90%): {'✅' if threshold_results['meets_target'] else '❌'}")
        print(f"   达到优秀水平(95%): {'✅' if threshold_results['meets_excellent'] else '❌'}")
    
    # 生成趋势
    if args.generate_trend:
        trend_data = monitor.get_coverage_trend()
        _ = print(f"\n📈 覆盖率趋势 (共{len(trend_data)}个数据点):")
        for point in trend_data[-5:]:  # 显示最近5个数据点
            _ = print(f"   {point['timestamp']}: {point['coverage']:.2f}%")
    
    _ = print(f"\n📄 详细报告已保存到: {report_path}")

if __name__ == "__main__":
    _ = main()