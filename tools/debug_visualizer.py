#!/usr/bin/env python3
"""
调试信息可视化工具
用于可视化调试日志、性能指标和系统状态
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from collections import defaultdict
import numpy as np

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class DebugVisualizer:
    """调试信息可视化工具"""
    
    def __init__(self, log_db_path: str = None):
        self.log_db_path = Path(log_db_path) if log_db_path else \
                          Path(__file__).parent.parent / "logs" / "debug" / "debug_logs.db"
        self.output_dir = Path(__file__).parent.parent / "logs" / "visualizations"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置图形样式
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        print(f"DebugVisualizer initialized with log DB: {self.log_db_path}")
        print(f"Visualization output directory: {self.output_dir}")
    
    def load_log_data(self, start_time: str = None, end_time: str = None, 
                     component: str = None, event_type: str = None) -> pd.DataFrame:
        """加载日志数据"""
        try:
            # 连接数据库
            conn = sqlite3.connect(self.log_db_path)
            
            # 构建查询条件
            conditions = []
            params = []
            
            if start_time:
                conditions.append("timestamp >= ?")
                params.append(start_time)
            
            if end_time:
                conditions.append("timestamp <= ?")
                params.append(end_time)
            
            if component:
                conditions.append("component = ?")
                params.append(component)
            
            if event_type:
                conditions.append("event_type = ?")
                params.append(event_type)
            
            # 构建SQL查询
            sql = "SELECT * FROM debug_logs"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY timestamp"
            
            # 读取数据到DataFrame
            df = pd.read_sql_query(sql, conn, params=params)
            conn.close()
            
            # 转换时间戳列
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['details'] = df['details'].apply(lambda x: json.loads(x) if x else {})
            
            print(f"Loaded {len(df)} log entries")
            return df
            
        except Exception as e:
            print(f"Error loading log data: {e}")
            return pd.DataFrame()
    
    def visualize_log_timeline(self, df: pd.DataFrame, output_file: str = None) -> str:
        """可视化日志时间线"""
        try:
            if df.empty:
                print("No data to visualize")
                return ""
            
            # 创建图形
            fig, ax = plt.subplots(figsize=(15, 8))
            
            # 按事件类型分组绘制
            event_types = df['event_type'].unique()
            colors = plt.cm.Set3(np.linspace(0, 1, len(event_types)))
            
            for i, event_type in enumerate(event_types):
                type_data = df[df['event_type'] == event_type]
                if not type_data.empty:
                    ax.scatter(type_data['timestamp'], [i] * len(type_data), 
                              c=[colors[i]], label=event_type, alpha=0.7, s=50)
            
            # 设置图形属性
            ax.set_xlabel('时间')
            ax.set_ylabel('事件类型')
            ax.set_title('调试日志时间线')
            ax.set_yticks(range(len(event_types)))
            ax.set_yticklabels(event_types)
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            
            # 格式化时间轴
            fig.autofmt_xdate()
            
            # 保存图形
            if not output_file:
                output_file = self.output_dir / f"log_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            else:
                output_file = self.output_dir / output_file
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Log timeline visualization saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"Error creating log timeline visualization: {e}")
            return ""
    
    def visualize_component_activity(self, df: pd.DataFrame, output_file: str = None) -> str:
        """可视化组件活动"""
        try:
            if df.empty:
                print("No data to visualize")
                return ""
            
            # 统计各组件的活动数量
            component_counts = df['component'].value_counts()
            
            # 创建图形
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 绘制柱状图
            bars = ax.bar(range(len(component_counts)), component_counts.values, 
                         color=plt.cm.viridis(np.linspace(0, 1, len(component_counts))))
            
            # 设置图形属性
            ax.set_xlabel('组件')
            ax.set_ylabel('日志条目数量')
            ax.set_title('各组件活动统计')
            ax.set_xticks(range(len(component_counts)))
            ax.set_xticklabels(component_counts.index, rotation=45, ha='right')
            
            # 添加数值标签
            for bar, count in zip(bars, component_counts.values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                       str(count), ha='center', va='bottom')
            
            # 保存图形
            if not output_file:
                output_file = self.output_dir / f"component_activity_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            else:
                output_file = self.output_dir / output_file
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Component activity visualization saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"Error creating component activity visualization: {e}")
            return ""
    
    def visualize_error_analysis(self, df: pd.DataFrame, output_file: str = None) -> str:
        """可视化错误分析"""
        try:
            if df.empty:
                print("No data to visualize")
                return ""
            
            # 筛选错误和严重错误
            error_df = df[df['event_type'].isin(['error', 'critical'])]
            if error_df.empty:
                print("No error data to visualize")
                return ""
            
            # 按组件统计错误
            error_by_component = error_df.groupby(['component', 'event_type']).size().unstack(fill_value=0)
            
            # 创建图形
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # 绘制堆叠柱状图
            error_by_component.plot(kind='bar', stacked=True, ax=ax, 
                                  color=['#ff6b6b', '#ff0000'])
            
            # 设置图形属性
            ax.set_xlabel('组件')
            ax.set_ylabel('错误数量')
            ax.set_title('错误分析 - 按组件分布')
            ax.legend(title='错误类型')
            plt.xticks(rotation=45, ha='right')
            
            # 保存图形
            if not output_file:
                output_file = self.output_dir / f"error_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            else:
                output_file = self.output_dir / output_file
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Error analysis visualization saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"Error creating error analysis visualization: {e}")
            return ""
    
    def visualize_performance_metrics(self, df: pd.DataFrame, output_file: str = None) -> str:
        """可视化性能指标"""
        try:
            if df.empty:
                print("No data to visualize")
                return ""
            
            # 筛选性能指标数据
            perf_df = df[df['event_type'] == 'performance']
            if perf_df.empty:
                print("No performance data to visualize")
                return ""
            
            # 解析性能指标详情
            perf_data = []
            for _, row in perf_df.iterrows():
                details = row['details']
                if isinstance(details, str):
                    try:
                        details = json.loads(details)
                    except:
                        continue
                
                if isinstance(details, dict):
                    perf_data.append({
                        'timestamp': row['timestamp'],
                        'component': row['component'],
                        'metric': details.get('metric', 'unknown'),
                        'value': details.get('value', 0),
                        'unit': details.get('unit', '')
                    })
            
            if not perf_data:
                print("No valid performance data to visualize")
                return ""
            
            perf_df = pd.DataFrame(perf_data)
            
            # 按指标类型分组绘制
            metrics = perf_df['metric'].unique()
            
            # 创建图形
            fig, axes = plt.subplots(len(metrics), 1, figsize=(15, 5*len(metrics)))
            if len(metrics) == 1:
                axes = [axes]
            
            for i, metric in enumerate(metrics):
                metric_data = perf_df[perf_df['metric'] == metric]
                if metric_data.empty:
                    continue
                
                # 按组件分组绘制时间序列
                for component in metric_data['component'].unique():
                    comp_data = metric_data[metric_data['component'] == component]
                    axes[i].plot(comp_data['timestamp'], comp_data['value'], 
                               marker='o', label=component, linewidth=2, markersize=4)
                
                axes[i].set_title(f'性能指标: {metric}')
                axes[i].set_xlabel('时间')
                axes[i].set_ylabel(f'值 ({metric_data["unit"].iloc[0] if not metric_data.empty else ""})')
                axes[i].legend()
                axes[i].grid(True, alpha=0.3)
                fig.autofmt_xdate()
            
            # 保存图形
            if not output_file:
                output_file = self.output_dir / f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            else:
                output_file = self.output_dir / output_file
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Performance metrics visualization saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"Error creating performance metrics visualization: {e}")
            return ""
    
    def visualize_severity_distribution(self, df: pd.DataFrame, output_file: str = None) -> str:
        """可视化严重性分布"""
        try:
            if df.empty:
                print("No data to visualize")
                return ""
            
            # 创建图形
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # 按事件类型统计
            event_type_counts = df['event_type'].value_counts()
            ax1.pie(event_type_counts.values, labels=event_type_counts.index, autopct='%1.1f%%',
                   startangle=90, colors=plt.cm.Set3(np.linspace(0, 1, len(event_type_counts))))
            ax1.set_title('事件类型分布')
            
            # 按严重性等级统计
            severity_labels = ['Debug', 'Info', 'Warning', 'Error', 'Critical']
            severity_ranges = [(0, 20), (20, 40), (40, 60), (60, 90), (90, 100)]
            severity_counts = []
            
            for min_sev, max_sev in severity_ranges:
                count = len(df[(df['severity'] >= min_sev) & (df['severity'] < max_sev)])
                severity_counts.append(count)
            
            ax2.bar(severity_labels, severity_counts, 
                   color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#000000'])
            ax2.set_xlabel('严重性等级')
            ax2.set_ylabel('日志条目数量')
            ax2.set_title('严重性分布')
            
            # 添加数值标签
            for i, count in enumerate(severity_counts):
                ax2.text(i, count + 0.5, str(count), ha='center', va='bottom')
            
            # 保存图形
            if not output_file:
                output_file = self.output_dir / f"severity_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            else:
                output_file = self.output_dir / output_file
            
            plt.tight_layout()
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Severity distribution visualization saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"Error creating severity distribution visualization: {e}")
            return ""
    
    def generate_comprehensive_report(self, hours: int = 24) -> Dict[str, Any]:
        """生成综合报告"""
        try:
            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # 加载数据
            df = self.load_log_data(start_time.isoformat(), end_time.isoformat())
            
            if df.empty:
                return {"error": "No data available for the specified time range"}
            
            # 生成统计信息
            report = {
                "report_generated_at": end_time.isoformat(),
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat(),
                    "duration_hours": hours
                },
                "summary": {
                    "total_entries": len(df),
                    "components": df['component'].nunique(),
                    "event_types": df['event_type'].nunique()
                },
                "event_type_distribution": df['event_type'].value_counts().to_dict(),
                "component_activity": df['component'].value_counts().to_dict(),
                "severity_distribution": {
                    "debug": len(df[df['severity'] < 20]),
                    "info": len(df[(df['severity'] >= 20) & (df['severity'] < 40)]),
                    "warning": len(df[(df['severity'] >= 40) & (df['severity'] < 60)]),
                    "error": len(df[(df['severity'] >= 60) & (df['severity'] < 90)]),
                    "critical": len(df[df['severity'] >= 90])
                },
                "top_components": df['component'].value_counts().head(10).to_dict(),
                "error_analysis": {
                    "total_errors": len(df[df['event_type'].isin(['error', 'critical'])]),
                    "errors_by_component": df[df['event_type'] == 'error']['component'].value_counts().to_dict(),
                    "critical_errors_by_component": df[df['event_type'] == 'critical']['component'].value_counts().to_dict()
                }
            }
            
            # 添加性能指标摘要
            perf_df = df[df['event_type'] == 'performance']
            if not perf_df.empty:
                perf_summary = {}
                for _, row in perf_df.iterrows():
                    details = row['details']
                    if isinstance(details, str):
                        try:
                            details = json.loads(details)
                        except:
                            continue
                    
                    if isinstance(details, dict):
                        metric = details.get('metric', 'unknown')
                        if metric not in perf_summary:
                            perf_summary[metric] = {
                                "count": 0,
                                "avg_value": 0,
                                "min_value": float('inf'),
                                "max_value": float('-inf')
                            }
                        
                        value = details.get('value', 0)
                        perf_summary[metric]["count"] += 1
                        perf_summary[metric]["avg_value"] += value
                        perf_summary[metric]["min_value"] = min(perf_summary[metric]["min_value"], value)
                        perf_summary[metric]["max_value"] = max(perf_summary[metric]["max_value"], value)
                
                # 计算平均值
                for metric in perf_summary:
                    if perf_summary[metric]["count"] > 0:
                        perf_summary[metric]["avg_value"] /= perf_summary[metric]["count"]
                
                report["performance_summary"] = perf_summary
            
            # 保存报告
            report_file = self.output_dir / f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"Comprehensive report saved to: {report_file}")
            return report
            
        except Exception as e:
            print(f"Error generating comprehensive report: {e}")
            return {"error": str(e)}
    
    def create_dashboard(self, hours: int = 24) -> List[str]:
        """创建完整的可视化仪表板"""
        try:
            # 计算时间范围
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # 加载数据
            df = self.load_log_data(start_time.isoformat(), end_time.isoformat())
            
            if df.empty:
                print("No data available for dashboard creation")
                return []
            
            # 生成所有可视化图表
            output_files = []
            
            # 1. 日志时间线
            timeline_file = self.visualize_log_timeline(df, f"dashboard_timeline_{hours}h.png")
            if timeline_file:
                output_files.append(timeline_file)
            
            # 2. 组件活动
            activity_file = self.visualize_component_activity(df, f"dashboard_activity_{hours}h.png")
            if activity_file:
                output_files.append(activity_file)
            
            # 3. 错误分析
            error_file = self.visualize_error_analysis(df, f"dashboard_errors_{hours}h.png")
            if error_file:
                output_files.append(error_file)
            
            # 4. 性能指标
            perf_file = self.visualize_performance_metrics(df, f"dashboard_performance_{hours}h.png")
            if perf_file:
                output_files.append(perf_file)
            
            # 5. 严重性分布
            severity_file = self.visualize_severity_distribution(df, f"dashboard_severity_{hours}h.png")
            if severity_file:
                output_files.append(severity_file)
            
            print(f"Dashboard created with {len(output_files)} visualizations")
            return output_files
            
        except Exception as e:
            print(f"Error creating dashboard: {e}")
            return []

def main():
    """主函数 - 演示工具使用"""
    # 创建可视化工具实例
    visualizer = DebugVisualizer()
    
    # 生成24小时内的综合报告
    print("Generating comprehensive report...")
    report = visualizer.generate_comprehensive_report(24)
    
    if "error" not in report:
        print("Report generated successfully")
        print(f"Total entries: {report['summary']['total_entries']}")
        print(f"Components: {report['summary']['components']}")
        print(f"Event types: {report['summary']['event_types']}")
    else:
        print(f"Error generating report: {report['error']}")
    
    # 创建仪表板
    print("\nCreating dashboard...")
    dashboard_files = visualizer.create_dashboard(24)
    
    if dashboard_files:
        print(f"Dashboard created with {len(dashboard_files)} files:")
        for file in dashboard_files:
            print(f"  - {file}")
    else:
        print("No dashboard files created")

if __name__ == "__main__":
    main()