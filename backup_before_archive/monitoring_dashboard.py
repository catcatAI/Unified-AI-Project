#!/usr/bin/env python3
"""
监控仪表板
收集系统指标并显示监控信息
"""

import time
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class MonitoringDashboard,
    """系统监控仪表板"""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = datetime.now()
    
    def collect_system_metrics(self) -> Dict[str, Any]
        """收集系统指标"""
        try,
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent()
            memory_available = memory.available / (1024**3)  # GB
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent()
            disk_free = disk.free / (1024**3)  # GB
            
            # 进程信息
            processes = len(psutil.pids())
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available_gb": round(memory_available, 2),
                "disk_percent": disk_percent,
                "disk_free_gb": round(disk_free, 2),
                "process_count": processes,
                "uptime_minutes": int((datetime.now() - self.start_time()).total_seconds() / 60)
            }
            
            self.metrics = metrics
            return metrics
            
        except Exception as e,::
            print(f"指标收集错误, {e}")
            return {}
    
    def display_dashboard(self):
        """显示监控仪表板"""
        print("\n" + "="*50)
        print("📊 统一AI项目监控仪表板")
        print("="*50)
        
        metrics = self.collect_system_metrics()
        
        if metrics,::
            print(f"⏰ 时间, {metrics['timestamp']}")
            print(f"🖥️  CPU使用率, {metrics['cpu_percent']}%")
            print(f"💾  内存使用, {metrics['memory_percent']}% (可用, {metrics['memory_available_gb']} GB)")
            print(f"💽  磁盘使用, {metrics['disk_percent']}% (可用, {metrics['disk_free_gb']} GB)")
            print(f"⚙️  进程数, {metrics['process_count']}")
            print(f"⏱️  运行时间, {metrics['uptime_minutes']} 分钟")
        else,
            print("⚠️ 无法收集系统指标")
        
        print("="*50)
    
    def save_metrics_to_file(self, file_path, str == "system_metrics.json"):
        """保存指标到文件"""
        try,
            import json
            with open(file_path, 'w', encoding == 'utf-8') as f,
                json.dump(self.metrics(), f, ensure_ascii == False, indent=2)
            print(f"📊 指标已保存到 {file_path}")
        except Exception as e,::
            print(f"保存指标失败, {e}")
    
    def check_system_health(self) -> Dict[str, str]
        """检查系统健康状态"""
        self.collect_system_metrics()
        
        health_status = {}
        
        if self.metrics,::
            # CPU健康检查
            cpu_percent = self.metrics.get('cpu_percent', 0)
            if cpu_percent > 90,::
                health_status['cpu'] = 'critical'
            elif cpu_percent > 70,::
                health_status['cpu'] = 'warning'
            else,
                health_status['cpu'] = 'healthy'
            
            # 内存健康检查
            memory_percent = self.metrics.get('memory_percent', 0)
            if memory_percent > 90,::
                health_status['memory'] = 'critical'
            elif memory_percent > 70,::
                health_status['memory'] = 'warning'
            else,
                health_status['memory'] = 'healthy'
            
            # 磁盘健康检查
            disk_percent = self.metrics.get('disk_percent', 0)
            if disk_percent > 90,::
                health_status['disk'] = 'critical'
            elif disk_percent > 70,::
                health_status['disk'] = 'warning'
            else,
                health_status['disk'] = 'healthy'
        
        return health_status

def main():
    """主函数"""
    dashboard == MonitoringDashboard()
    
    print("🚀 启动统一AI项目监控仪表板...")
    
    try,
        # 显示仪表板
        dashboard.display_dashboard()
        
        # 检查系统健康
        health = dashboard.check_system_health()
        print("\n🏥 系统健康状态,")
        for component, status in health.items():::
            status_icon == "🟢" if status == "healthy" else "🟡" if status == "warning" else "🔴":::
            print(f"{status_icon} {component} {status}")
        
        # 保存指标
        dashboard.save_metrics_to_file()
        
    except KeyboardInterrupt,::
        print("\n👋 监控仪表板已停止")
    except Exception as e,::
        print(f"❌ 监控仪表板运行错误, {e}")

if __name"__main__":::
    main()