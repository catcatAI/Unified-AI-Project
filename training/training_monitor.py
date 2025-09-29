#!/usr/bin/env python3
"""
训练过程监控和异常检测
实现训练过程的实时监控、性能分析和异常检测功能
"""

import logging
import time
import threading
import psutil
import json
from pathlib import Path
from datetime import datetime
import numpy as np
from collections import defaultdict, deque

# 添加项目路径
import sys
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))


# 配置日志
logging.basicConfig(
    level: str=logging.INFO,
    format: str='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        _ = logging.FileHandler(project_root / 'training' / 'logs' / 'training_monitor.log'),
        _ = logging.StreamHandler()
    ]
)
logger: Any = logging.getLogger(__name__)

class TrainingAnomalyDetector:
    """训练异常检测器"""
    
    def __init__(self, window_size: int = 10) -> None:
        self.window_size = window_size
        self.metrics_history = defaultdict(lambda: deque(maxlen=window_size))
        self.baseline_metrics = {}
        self.anomaly_thresholds = {
            'loss': 2.0,  # 损失异常阈值（标准差倍数）
            'accuracy': 0.1,  # 准确率异常阈值（与基线的差异）
            'loss_spike': 0.5,  # 损失尖峰阈值（单步变化）
            'accuracy_drop': 0.05  # 准确率下降阈值（单步变化）
        }
        self.error_handler = global_error_handler
    
    def update_baseline(self, metrics: Dict[str, float]):
        """更新基线指标"""
        context = ErrorContext("TrainingAnomalyDetector", "update_baseline")
        try:
            for metric_name, value in metrics.items():
                if metric_name not in self.baseline_metrics:
                    self.baseline_metrics[metric_name] = []
                _ = self.baseline_metrics[metric_name].append(value)
                
                # 保持基线历史不超过100个点
                if len(self.baseline_metrics[metric_name]) > 100:
                    _ = self.baseline_metrics[metric_name].pop(0)
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 更新基线指标失败: {e}")
    
    def detect_anomalies(self, current_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """检测异常"""
        context = ErrorContext("TrainingAnomalyDetector", "detect_anomalies")
        anomalies = []
        
        try:
            for metric_name, current_value in current_metrics.items():
                # 添加到历史记录
                _ = self.metrics_history[metric_name].append(current_value)
                
                # 如果历史记录不足，跳过异常检测
                if len(self.metrics_history[metric_name]) < 3:
                    continue
                
                # 获取历史数据
                history = list(self.metrics_history[metric_name])
                
                # 检测损失尖峰
                if metric_name == 'loss' and len(history) >= 2:
                    recent_change = abs(history[-1] - history[-2])
                    if recent_change > self.anomaly_thresholds['loss_spike']:
                        anomalies.append({
                            'type': 'loss_spike',
                            'metric': metric_name,
                            'current_value': current_value,
                            'previous_value': history[-2],
                            'change': recent_change,
                            'threshold': self.anomaly_thresholds['loss_spike'],
                            _ = 'timestamp': datetime.now().isoformat()
                        })
                
                # 检测准确率下降
                if metric_name == 'accuracy' and len(history) >= 2:
                    recent_change = history[-2] - history[-1]  # 注意这里是下降
                    if recent_change > self.anomaly_thresholds['accuracy_drop']:
                        anomalies.append({
                            'type': 'accuracy_drop',
                            'metric': metric_name,
                            'current_value': current_value,
                            'previous_value': history[-2],
                            'change': recent_change,
                            'threshold': self.anomaly_thresholds['accuracy_drop'],
                            _ = 'timestamp': datetime.now().isoformat()
                        })
                
                # 基于统计的异常检测
                if len(history) >= 5:
                    mean_val = np.mean(history[:-1])  # 排除当前值
                    std_val = np.std(history[:-1])
                    
                    # 检测偏离均值过多的值
                    if std_val > 0:
                        z_score = abs(current_value - mean_val) / std_val
                        if z_score > self.anomaly_thresholds['loss']:
                            anomalies.append({
                                'type': 'statistical_anomaly',
                                'metric': metric_name,
                                'current_value': current_value,
                                'mean': mean_val,
                                'std': std_val,
                                'z_score': z_score,
                                'threshold': self.anomaly_thresholds['loss'],
                                _ = 'timestamp': datetime.now().isoformat()
                            })
            
            # 检测基线偏离
            for metric_name, baseline_history in self.baseline_metrics.items():
                if metric_name in current_metrics and len(baseline_history) >= 10:
                    current_value = current_metrics[metric_name]
                    baseline_mean = np.mean(baseline_history)
                    baseline_std = np.std(baseline_history)
                    
                    # 如果基线标准差为0，使用小的默认值
                    if baseline_std == 0:
                        baseline_std = 1e-6
                    
                    # 计算与基线的偏离
                    baseline_deviation = abs(current_value - baseline_mean) / baseline_std
                    
                    if metric_name == 'accuracy' and current_value < baseline_mean - self.anomaly_thresholds['accuracy']:
                        anomalies.append({
                            'type': 'baseline_deviation',
                            'metric': metric_name,
                            'current_value': current_value,
                            'baseline_mean': baseline_mean,
                            'baseline_std': baseline_std,
                            'deviation': baseline_deviation,
                            'threshold': self.anomaly_thresholds['accuracy'],
                            _ = 'timestamp': datetime.now().isoformat()
                        })
            
            if anomalies:
                _ = logger.warning(f"⚠️  检测到 {len(anomalies)} 个异常")
                for anomaly in anomalies:
                    logger.warning(f"   {anomaly['type']}: {anomaly['metric']} = {anomaly['current_value']}")
            
            return anomalies
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 异常检测失败: {e}")
            return []

class SystemResourceMonitor:
    """系统资源监控器"""
    
    def __init__(self) -> None:
        self.error_handler = global_error_handler
        self.resource_history = deque(maxlen=100)  # 保存最近100个时间点的资源数据
    
    def get_system_resources(self) -> Dict[str, Any]:
        """获取系统资源使用情况"""
        context = ErrorContext("SystemResourceMonitor", "get_system_resources")
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available = memory.available
            memory_total = memory.total
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_free = disk.free
            
            # 网络IO
            net_io = psutil.net_io_counters()
            bytes_sent = net_io.bytes_sent
            bytes_recv = net_io.bytes_recv
            
            resources = {
                _ = 'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                _ = 'memory_available_gb': memory_available / (1024**3),
                _ = 'memory_total_gb': memory_total / (1024**3),
                'disk_percent': disk_percent,
                _ = 'disk_free_gb': disk_free / (1024**3),
                'network_bytes_sent': bytes_sent,
                'network_bytes_recv': bytes_recv
            }
            
            # 添加到历史记录
            _ = self.resource_history.append(resources)
            
            return resources
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 获取系统资源失败: {e}")
            return {}
    
    def check_resource_alerts(self) -> List[Dict[str, Any]]:
        """检查资源警告"""
        context = ErrorContext("SystemResourceMonitor", "check_resource_alerts")
        alerts = []
        
        try:
            if not self.resource_history:
                return alerts
            
            current = self.resource_history[-1]
            
            # CPU使用率警告
            if current['cpu_percent'] > 90:
                alerts.append({
                    'type': 'high_cpu',
                    'level': 'critical',
                    'message': f"CPU使用率过高: {current['cpu_percent']:.1f}%",
                    'value': current['cpu_percent'],
                    'threshold': 90,
                    'timestamp': current['timestamp']
                })
            elif current['cpu_percent'] > 80:
                alerts.append({
                    'type': 'high_cpu',
                    'level': 'warning',
                    'message': f"CPU使用率较高: {current['cpu_percent']:.1f}%",
                    'value': current['cpu_percent'],
                    'threshold': 80,
                    'timestamp': current['timestamp']
                })
            
            # 内存使用率警告
            if current['memory_percent'] > 90:
                alerts.append({
                    'type': 'high_memory',
                    'level': 'critical',
                    'message': f"内存使用率过高: {current['memory_percent']:.1f}%",
                    'value': current['memory_percent'],
                    'threshold': 90,
                    'timestamp': current['timestamp']
                })
            elif current['memory_percent'] > 80:
                alerts.append({
                    'type': 'high_memory',
                    'level': 'warning',
                    'message': f"内存使用率较高: {current['memory_percent']:.1f}%",
                    'value': current['memory_percent'],
                    'threshold': 80,
                    'timestamp': current['timestamp']
                })
            
            # 磁盘空间警告
            if current['disk_percent'] > 95:
                alerts.append({
                    'type': 'low_disk',
                    'level': 'critical',
                    'message': f"磁盘空间不足: {current['disk_free_gb']:.2f}GB 可用",
                    'value': current['disk_free_gb'],
                    'threshold': 5,  # GB
                    'timestamp': current['timestamp']
                })
            elif current['disk_percent'] > 90:
                alerts.append({
                    'type': 'low_disk',
                    'level': 'warning',
                    'message': f"磁盘空间紧张: {current['disk_free_gb']:.2f}GB 可用",
                    'value': current['disk_free_gb'],
                    'threshold': 10,  # GB
                    'timestamp': current['timestamp']
                })
            
            if alerts:
                for alert in alerts:
                    if alert['level'] == 'critical':
                        _ = logger.critical(f"🚨 {alert['message']}")
                    else:
                        _ = logger.warning(f"⚠️  {alert['message']}")
            
            return alerts
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 检查资源警告失败: {e}")
            return []

class TrainingPerformanceAnalyzer:
    """训练性能分析器"""
    
    def __init__(self) -> None:
        self.epoch_times = deque(maxlen=50)  # 保存最近50个epoch的时间
        self.error_handler = global_error_handler
    
    def record_epoch_time(self, epoch: int, duration: float):
        """记录epoch训练时间"""
        context = ErrorContext("TrainingPerformanceAnalyzer", "record_epoch_time")
        try:
            self.epoch_times.append({
                'epoch': epoch,
                'duration': duration,
                _ = 'timestamp': datetime.now().isoformat()
            })
            
            _ = logger.info(f"⏱️  Epoch {epoch} 完成，耗时 {duration:.2f} 秒")
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 记录epoch时间失败: {e}")
    
    def analyze_performance_trends(self) -> Dict[str, Any]:
        """分析性能趋势"""
        context = ErrorContext("TrainingPerformanceAnalyzer", "analyze_performance_trends")
        try:
            if len(self.epoch_times) < 3:
                return {'status': 'insufficient_data'}
            
            durations = [record['duration'] for record in self.epoch_times]
            epochs = [record['epoch'] for record in self.epoch_times]
            
            # 计算基本统计信息
            mean_duration = np.mean(durations)
            std_duration = np.std(durations)
            min_duration = np.min(durations)
            max_duration = np.max(durations)
            
            # 计算趋势（使用线性回归的斜率）
            if len(epochs) >= 2:
                slope = np.polyfit(epochs, durations, 1)[0]
                trend = 'increasing' if slope > 0.1 else 'decreasing' if slope < -0.1 else 'stable'
            else:
                slope = 0
                trend = 'unknown'
            
            # 检测性能异常
            performance_issues = []
            recent_durations = durations[-5:] if len(durations) >= 5 else durations
            if len(recent_durations) >= 3:
                recent_mean = np.mean(recent_durations)
                if recent_mean > mean_duration * 1.5:
                    performance_issues.append({
                        'type': 'performance_degradation',
                        _ = 'message': f"最近epoch平均时间显著增加 ({recent_mean:.2f}s vs {mean_duration:.2f}s)",
                        'severity': 'warning'
                    })
            
            analysis = {
                'status': 'analyzed',
                'mean_duration': mean_duration,
                'std_duration': std_duration,
                'min_duration': min_duration,
                'max_duration': max_duration,
                'trend': trend,
                'slope': slope,
                _ = 'total_epochs': len(self.epoch_times),
                'performance_issues': performance_issues
            }
            
            # 记录分析结果
            _ = logger.info(f"📊 性能分析: 平均 {mean_duration:.2f}s/epoch, 趋势: {trend}")
            
            return analysis
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 性能分析失败: {e}")
            return {'status': 'error', 'message': str(e)}

class TrainingMonitor:
    """训练监控器主类"""
    
    def __init__(self, log_file: str = None) -> None:
        self.log_file = Path(log_file) if log_file else project_root / 'training' / 'logs' / 'training_monitor.log'
        self.anomaly_detector = TrainingAnomalyDetector()
        self.resource_monitor = SystemResourceMonitor()
        self.performance_analyzer = TrainingPerformanceAnalyzer()
        self.error_handler = global_error_handler
        self.monitoring_enabled = True
        self.monitoring_thread = None
        self.stop_monitoring_flag = False  # 修改变量名以避免冲突
        
        # 确保日志目录存在
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        _ = logger.info("🔄 训练监控器初始化完成")
    
    def start_monitoring(self):
        """开始监控"""
        context = ErrorContext("TrainingMonitor", "start_monitoring")
        try:
            if self.monitoring_thread is None or not self.monitoring_thread.is_alive():
                self.stop_monitoring_flag = False  # 修改变量名
                self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
                _ = self.monitoring_thread.start()
                _ = logger.info("✅ 训练监控已启动")
            else:
                _ = logger.info("ℹ️  训练监控已在运行中")
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 启动监控失败: {e}")
    
    def stop_monitoring(self):
        """停止监控"""
        context = ErrorContext("TrainingMonitor", "stop_monitoring")
        try:
            self.stop_monitoring_flag = True  # 修改变量名
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            _ = logger.info("⏹️  训练监控已停止")
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 停止监控失败: {e}")
    
    def _monitoring_loop(self):
        """监控循环"""
        context = ErrorContext("TrainingMonitor", "_monitoring_loop")
        try:
            while not self.stop_monitoring_flag:  # 修改变量名
                # 获取系统资源
                resources = self.resource_monitor.get_system_resources()
                
                # 检查资源警告
                alerts = self.resource_monitor.check_resource_alerts()
                
                # 记录到日志文件
                if self.log_file:
                    log_entry = {
                        _ = 'timestamp': datetime.now().isoformat(),
                        'type': 'system_resources',
                        'data': resources,
                        'alerts': alerts
                    }
                    try:
                        with open(self.log_file, 'a', encoding='utf-8') as f:
                            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                    except Exception as e:
                        _ = logger.error(f"❌ 写入日志文件失败: {e}")
                
                # 每5秒检查一次
                for _ in range(5):
                    if self.stop_monitoring_flag:  # 修改变量名
                        break
                    _ = time.sleep(1)
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 监控循环出错: {e}")
    
    def update_training_metrics(self, scenario_name: str, epoch: int, metrics: Dict[str, float]):
        """更新训练指标"""
        context = ErrorContext("TrainingMonitor", "update_training_metrics", {"scenario_name": scenario_name})
        try:
            # 更新异常检测器的基线
            _ = self.anomaly_detector.update_baseline(metrics)
            
            # 检测异常
            anomalies = self.anomaly_detector.detect_anomalies(metrics)
            
            # 记录到日志
            log_entry = {
                _ = 'timestamp': datetime.now().isoformat(),
                'type': 'training_metrics',
                'scenario': scenario_name,
                'epoch': epoch,
                'metrics': metrics,
                'anomalies': anomalies
            }
            
            if self.log_file:
                try:
                    with open(self.log_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                except Exception as e:
                    _ = logger.error(f"❌ 写入训练指标日志失败: {e}")
            
            # 如果检测到严重异常，记录警告
            critical_anomalies = [a for a in anomalies if a.get('type') in ['loss_spike', 'accuracy_drop']]
            if critical_anomalies:
                for anomaly in critical_anomalies:
                    logger.warning(f"⚠️  训练异常检测: {anomaly['type']} - {anomaly['metric']} = {anomaly['current_value']}")
            
            return anomalies
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 更新训练指标失败: {e}")
            return []
    
    def record_epoch_completion(self, epoch: int, duration: float):
        """记录epoch完成"""
        context = ErrorContext("TrainingMonitor", "record_epoch_completion")
        try:
            _ = self.performance_analyzer.record_epoch_time(epoch, duration)
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 记录epoch完成失败: {e}")
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """获取性能分析"""
        context = ErrorContext("TrainingMonitor", "get_performance_analysis")
        try:
            return self.performance_analyzer.analyze_performance_trends()
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 获取性能分析失败: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        context = ErrorContext("TrainingMonitor", "get_system_status")
        try:
            resources = self.resource_monitor.get_system_resources()
            alerts = self.resource_monitor.check_resource_alerts()
            
            status = {
                'resources': resources,
                'alerts': alerts,
                'monitoring_enabled': self.monitoring_enabled
            }
            
            return status
        except Exception as e:
            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 获取系统状态失败: {e}")
            return {'status': 'error', 'message': str(e)}

# 创建全局训练监控器实例
global_training_monitor = TrainingMonitor()

def main() -> None:
    """主函数，用于测试监控器"""
    _ = print("🔬 测试训练监控器...")
    
    # 创建监控器实例
    monitor = TrainingMonitor()
    
    # 启动监控
    _ = monitor.start_monitoring()
    
    # 模拟训练过程
    _ = print("🔄 模拟训练过程...")
    
    # 模拟正常训练指标
    normal_metrics = [
        {'loss': 0.8, 'accuracy': 0.6},
        {'loss': 0.6, 'accuracy': 0.7},
        {'loss': 0.5, 'accuracy': 0.75},
        {'loss': 0.4, 'accuracy': 0.8},
        {'loss': 0.35, 'accuracy': 0.82}
    ]
    
    for epoch, metrics in enumerate(normal_metrics, 1):
        _ = print(f"Epoch {epoch}: {metrics}")
        anomalies = monitor.update_training_metrics("test_scenario", epoch, metrics)
        _ = monitor.record_epoch_completion(epoch, 2.5)  # 假设每个epoch耗时2.5秒
        _ = time.sleep(1)  # 模拟训练间隔
    
    # 模拟异常情况
    _ = print("\n⚠️  模拟异常情况...")
    anomaly_metrics = {'loss': 1.5, 'accuracy': 0.65}  # 损失突然增加，准确率下降
    _ = print(f"异常指标: {anomaly_metrics}")
    anomalies = monitor.update_training_metrics("test_scenario", 6, anomaly_metrics)
    
    # 获取性能分析
    _ = print("\n📊 性能分析:")
    performance_analysis = monitor.get_performance_analysis()
    _ = print(f"  {performance_analysis}")
    
    # 获取系统状态
    _ = print("\n🖥️  系统状态:")
    system_status = monitor.get_system_status()
    _ = print(f"  CPU使用率: {system_status['resources'].get('cpu_percent', 'N/A')}%")
    _ = print(f"  内存使用率: {system_status['resources'].get('memory_percent', 'N/A')}%")
    
    # 停止监控
    _ = monitor.stop_monitoring()
    
    _ = print("\n✅ 训练监控器测试完成")

if __name__ == "__main__":
    _ = main()