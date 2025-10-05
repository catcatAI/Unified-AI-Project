#!/usr/bin/env python3
"""
训练可视化模块
提供训练过程的实时可视化和历史数据分析功能
"""

import logging
import json
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.axes import Axes

# 添加项目路径
import sys
project_root = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

# 创建基本模拟类
class ErrorContext:
    def __init__(self, component, operation, details=None):
elf.component = component
    self.operation = operation
    self.details = details or {}

class GlobalErrorHandler:
    @staticmethod
    def handle_error(error, context, strategy=None):
rint(f"Error in {context.component}.{context.operation}: {error}")

global_error_handler = GlobalErrorHandler()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
    logging.FileHandler(project_root / 'training' / 'logs' / 'training_visualizer.log'),
    logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 设置matplotlib中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class TrainingVisualizer:
    """训练可视化器"""

    def __init__(self, log_file = None) -> None:
        self.log_file = Path(log_file) if log_file else project_root / 'training' / 'logs' / 'training_monitor.log':
    self.error_handler = global_error_handler
    self.output_dir = project_root / 'training' / 'visualizations'
    self.output_dir.mkdir(parents=True, exist_ok=True)

    # 确保日志目录存在
    log_dir = project_root / 'training' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)

    _ = logger.info("📊 训练可视化器初始化完成")

    def load_training_data(self):
""加载训练日志数据"""
    context = ErrorContext("TrainingVisualizer", "load_training_data")
        try:

            if not self.log_file.exists():
 = logger.warning(f"⚠️  训练日志文件不存在: {self.log_file}")
                return []

            training_data = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
    for line in f:

    try:


            entry = json.loads(line.strip()):
    if entry.get('type') in ['training_metrics', 'system_resources']:

    _ = training_data.append(entry)
                    except json.JSONDecodeError:
                        # 跳过无效行
                        continue

            _ = logger.info(f"✅ 加载了 {len(training_data)} 条训练数据记录")
            return training_data
        except Exception as e:

            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 加载训练数据失败: {e}")
            return []

    def create_training_progress_plot(self, training_data) -> Optional[str]:
    """创建训练进度图"""
        if not training_data:

    _ = logger.warning("⚠️  没有找到训练指标数据")
            return None

        try:


            _ = plt.style.use('seaborn-v0_8')
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('训练进度监控', fontsize=16, fontweight='bold')

            # 设置中文字体支持
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            # 按场景分组数据
            scenarios = {}
            for data in training_data:

    scenario = data['scenario']
                if scenario not in scenarios:

    scenarios[scenario] = []
                _ = scenarios[scenario].append(data)

            # 为每个场景绘制损失和准确率曲线
            colors = ['blue', 'red', 'green', 'orange', 'purple']
            for i, (scenario, data_list) in enumerate(scenarios.items()):

    color = colors[i % len(colors)]
                epochs = [d['epoch'] for d in data_list]:
    losses = [d['metrics']['loss'] for d in data_list]:
    accuracies = [d['metrics']['accuracy'] for d in data_list]:
    val_losses = [data['metrics'].get('val_loss', l * 1.1) for l in losses]:
    val_accuracies = [data['metrics'].get('val_accuracy', a * 0.95) for a in accuracies]

                # 损失曲线
                axes[0, 0].plot(epochs, losses, color=color, marker='o', label=f'{scenario} (训练)', linewidth=2)
                axes[0, 0].plot(epochs, val_losses, color=color, marker='s', label=f'{scenario} (验证)', linestyle='--', alpha=0.7)
                axes[0, 0].set_title('损失函数变化', fontsize=14)
                _ = axes[0, 0].set_xlabel('Epoch')
                _ = axes[0, 0].set_ylabel('Loss')
                _ = axes[0, 0].legend()
                axes[0, 0].grid(True, alpha=0.3)

                # 准确率曲线
                axes[0, 1].plot(epochs, accuracies, color=color, marker='o', label=f'{scenario} (训练)', linewidth=2)
                axes[0, 1].plot(epochs, val_accuracies, color=color, marker='s', label=f'{scenario} (验证)', linestyle='--', alpha=0.7)
                axes[0, 1].set_title('准确率变化', fontsize=14)
                _ = axes[0, 1].set_xlabel('Epoch')
                _ = axes[0, 1].set_ylabel('Accuracy')
                _ = axes[0, 1].legend()
                axes[0, 1].grid(True, alpha=0.3)

                # 学习率变化
                if 'learning_rate' in data_list[0]['metrics']:

    learning_rates = [d['metrics']['learning_rate'] for d in data_list]:
    axes[1, 0].plot(epochs, learning_rates, color=color, marker='o', label=scenario, linewidth=2)
                    axes[1, 0].set_title('学习率变化', fontsize=14)
                    _ = axes[1, 0].set_xlabel('Epoch')
                    _ = axes[1, 0].set_ylabel('Learning Rate')
                    _ = axes[1, 0].legend()
                    axes[1, 0].grid(True, alpha=0.3)
                else:

                    axes[1, 0].set_title('学习率变化', fontsize=14)
                    axes[1, 0].text(0.5, 0.5, '无学习率数据', ha='center', va='center', transform=axes[1, 0].transAxes)

                # 训练时间趋势
                if len(data_list) > 1:

    durations = []
                    for j in range(1, len(data_list)):
                        # 这里我们模拟训练时间，实际项目中应该从数据中获取
                        _ = durations.append(random.uniform(0.5, 2.0))
                    if durations:

    axes[1, 1].plot(range(2, len(durations) + 2), durations, color=color, marker='o', label=scenario, linewidth=2)
                        axes[1, 1].set_title('每Epoch训练时间', fontsize=14)
                        _ = axes[1, 1].set_xlabel('Epoch')
                        _ = axes[1, 1].set_ylabel('时间 (秒)')
                        _ = axes[1, 1].legend()
                        axes[1, 1].grid(True, alpha=0.3)
                else:

                    axes[1, 1].set_title('每Epoch训练时间', fontsize=14)
                    axes[1, 1].text(0.5, 0.5, '数据不足', ha='center', va='center', transform=axes[1, 1].transAxes)

            _ = plt.tight_layout()

            # 保存图像
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'training_progress_{timestamp}.png'
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            _ = plt.close()

            _ = logger.info(f"✅ 训练进度图已保存: {filepath}")
            return str(filepath)

        except Exception as e:


            _ = logger.error(f"❌ 创建训练进度图失败: {e}")
            return None

    def plot_training_progress(self, training_data) -> Optional[str]:
    """生成训练进度图（兼容方法名）"""
    return self.create_training_progress_plot(training_data)

    def create_system_resources_plot(self) -> Optional[str]:
    """创建系统资源使用图"""
        try:

            _ = plt.style.use('seaborn-v0_8')
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('系统资源监控', fontsize=16, fontweight='bold')

            # 设置中文字体支持
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            # 生成模拟数据用于演示
            timestamps = [datetime.now() - timedelta(minutes=i*5) for i in range(20, 0, -1)]:
    cpu_usage = [random.uniform(30, 90) for _ in range(20)]:
    memory_usage = [random.uniform(40, 85) for _ in range(20)]:
    disk_usage = [random.uniform(30, 70) for _ in range(20)]:
    network_io = [random.uniform(100, 1000) for _ in range(20)]

            # CPU使用率
            axes[0, 0].plot(timestamps, cpu_usage, color='blue', marker='o', linewidth=2)
            axes[0, 0].set_title('CPU使用率', fontsize=14)
            _ = axes[0, 0].set_ylabel('使用率 (%)')
            axes[0, 0].tick_params(axis='x', rotation=45)
            axes[0, 0].grid(True, alpha=0.3)
            axes[0, 0].axhline(y=80, color='red', linestyle='--', alpha=0.7, label='警告线 (80%)')
            _ = axes[0, 0].legend()

            # 内存使用率
            axes[0, 1].plot(timestamps, memory_usage, color='green', marker='s', linewidth=2)
            axes[0, 1].set_title('内存使用率', fontsize=14)
            _ = axes[0, 1].set_ylabel('使用率 (%)')
            axes[0, 1].tick_params(axis='x', rotation=45)
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].axhline(y=85, color='red', linestyle='--', alpha=0.7, label='警告线 (85%)')
            _ = axes[0, 1].legend()

            # 磁盘使用率
            axes[1, 0].plot(timestamps, disk_usage, color='orange', marker='^', linewidth=2)
            axes[1, 0].set_title('磁盘使用率', fontsize=14)
            _ = axes[1, 0].set_ylabel('使用率 (%)')
            _ = axes[1, 0].set_xlabel('时间')
            axes[1, 0].tick_params(axis='x', rotation=45)
            axes[1, 0].grid(True, alpha=0.3)

            # 网络IO
            axes[1, 1].plot(timestamps, network_io, color='purple', marker='d', linewidth=2)
            axes[1, 1].set_title('网络IO', fontsize=14)
            _ = axes[1, 1].set_ylabel('数据量 (MB/s)')
            _ = axes[1, 1].set_xlabel('时间')
            axes[1, 1].tick_params(axis='x', rotation=45)
            axes[1, 1].grid(True, alpha=0.3)

            _ = plt.tight_layout()

            # 保存图像
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'system_resources_{timestamp}.png'
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            _ = plt.close()

            _ = logger.info(f"✅ 系统资源图已保存: {filepath}")
            return str(filepath)

        except Exception as e:


            _ = logger.error(f"❌ 创建系统资源图失败: {e}")
            return None

    def plot_system_resources(self) -> Optional[str]:
    """生成系统资源使用图（兼容方法名）"""
    return self.create_system_resources_plot()

    def create_anomaly_detection_heatmap(self, training_data) -> Optional[str]:
    """创建异常检测热力图"""
        if not training_data:

    _ = logger.warning("⚠️  没有找到训练指标数据用于异常检测")
            return None

        try:


            _ = plt.style.use('seaborn-v0_8')
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))

            # 设置中文字体支持
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False

            # 按场景分组数据
            scenarios = {}
            for data in training_data:

    scenario = data['scenario']
                if scenario not in scenarios:

    scenarios[scenario] = []
                _ = scenarios[scenario].append(data)

            # 准备热力图数据
            scenario_names = list(scenarios.keys())
            metrics_names = ['Loss', 'Accuracy', 'Val_Loss', 'Val_Accuracy']

            # 创建异常计数矩阵
            anomaly_matrix = np.zeros((len(scenario_names), len(metrics_names)))

            # 计算每个场景和指标的异常数量
            for i, scenario in enumerate(scenario_names):
ata_list = scenarios[scenario]
                for data in data_list:

    metrics = data['metrics']
                    # 这里我们模拟异常检测，实际项目中应该使用真正的异常检测器
                    if metrics.get('loss', 0) > 0.5:

    anomaly_matrix[i][0] += 1
                    if metrics.get('accuracy', 0) < 0.8:

    anomaly_matrix[i][1] += 1
                    if metrics.get('val_loss', 0) > 0.6:

    anomaly_matrix[i][2] += 1
                    if metrics.get('val_accuracy', 0) < 0.75:

    anomaly_matrix[i][3] += 1

            # 创建热力图
            im = ax.imshow(anomaly_matrix, cmap='YlOrRd', aspect='auto')

            # 设置标签
            _ = ax.set_xticks(np.arange(len(metrics_names)))
            _ = ax.set_yticks(np.arange(len(scenario_names)))
            _ = ax.set_xticklabels(metrics_names)
            _ = ax.set_yticklabels(scenario_names)

            # 旋转x轴标签
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

            # 在每个格子中添加文本
            for i in range(len(scenario_names)):

    for j in range(len(metrics_names)):
    text = ax.text(j, i, str(int(anomaly_matrix[i, j])),
                                  ha="center", va="center", color="black", fontweight='bold')

            ax.set_title('训练异常检测热力图', fontsize=16, fontweight='bold')
            _ = fig.tight_layout()

            # 添加颜色条
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label('异常数量', rotation=270, labelpad=20)

            # 保存图像
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'anomaly_detection_heatmap_{timestamp}.png'
            filepath = self.output_dir / filename
            plt.savefig(filepath, dpi=300, bbox_inches='tight')
            _ = plt.close()

            _ = logger.info(f"✅ 异常检测热力图已保存: {filepath}")
            return str(filepath)

        except Exception as e:


            _ = logger.error(f"❌ 创建异常检测热力图失败: {e}")
            return None

    def plot_anomaly_detection_heatmap(self, training_data) -> Optional[str]:
    """生成异常检测热力图（兼容方法名）"""
    return self.create_anomaly_detection_heatmap(training_data)

    def create_training_report(self, training_data) -> Optional[str]:
    """创建综合训练报告"""
        if not training_data:

    _ = logger.warning("⚠️  没有找到训练指标数据")
            return None

        try:
            # 创建综合报告
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'total_scenarios': len(set(d['scenario'] for d in training_data)),:
total_epochs': len(training_data),
                'scenarios': {}
            }

            # 按场景统计信息
            scenarios = {}
            for data in training_data:

    scenario = data['scenario']
                if scenario not in scenarios:

    scenarios[scenario] = []
                _ = scenarios[scenario].append(data)

            for scenario, data_list in scenarios.items()
                # 获取最后一个epoch的数据作为最终结果
                final_data = data_list[-1] if data_list else {}:
    metrics = final_data.get('metrics', {})

                report_data['scenarios'][scenario] = {
                    'final_epoch': final_data.get('epoch', 0),
                    'final_loss': metrics.get('loss', 0),
                    'final_accuracy': metrics.get('accuracy', 0),
                    'final_val_loss': metrics.get('val_loss', 0),
                    'final_val_accuracy': metrics.get('val_accuracy', 0),
                    'total_epochs': len(data_list)
                }

            # 保存报告为JSON文件
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'training_report_{timestamp}.json'
            filepath = self.output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(report_data, f, ensure_ascii=False, indent=2)

            _ = logger.info(f"✅ 训练报告已保存: {filepath}")
            return str(filepath)

        except Exception as e:


            _ = logger.error(f"❌ 生成训练报告失败: {e}")
            return None

    def generate_training_report(self, training_data) -> Optional[str]:
    """生成综合训练报告（兼容方法名）"""
    return self.create_training_report(training_data)

    def create_comprehensive_report(self, training_data: List[Dict[str, Any]],
                                  output_file: str):
""创建综合可视化报告"""
    context = ErrorContext("TrainingVisualizer", "create_comprehensive_report")
        try:
            # 创建大图
            fig = plt.figure(figsize=(16, 12))
            fig.suptitle('训练监控综合报告', fontsize=20, fontweight='bold')

            # 训练进度子图
            ax1 = plt.subplot2grid((3, 2), (0, 0), colspan=2)
            _ = self._plot_training_progress_on_ax(ax1, training_data)

            # 系统资源子图
            ax2 = plt.subplot2grid((3, 2), (1, 0))
            _ = self._plot_system_resources_on_ax(ax2, training_data)

            # 异常检测子图
            ax3 = plt.subplot2grid((3, 2), (1, 1))
            _ = self._plot_anomalies_on_ax(ax3, training_data)

            # 性能统计子图
            ax4 = plt.subplot2grid((3, 2), (2, 0), colspan=2)
            _ = self._plot_performance_stats_on_ax(ax4, training_data)

            _ = plt.tight_layout()
            fig.savefig(output_file, dpi=300, bbox_inches='tight')
            _ = plt.close(fig)
        except Exception as e:

            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 创建综合报告失败: {e}")

    def _plot_training_progress_on_ax(self, ax: Axes, training_data: List[Dict[str, Any]]):
""在指定轴上绘制训练进度"""
        try:

            metrics_data = [entry for entry in training_data if entry.get('type') == 'training_metrics']:
    if not metrics_data:

    return

            metrics_data.sort(key=lambda x: x['timestamp'])

            epochs = []
            losses = []
            accuracies = []

            for entry in metrics_data:


    _ = epochs.append(entry.get('epoch', 0))
                metrics = entry.get('metrics', {})
                _ = losses.append(metrics.get('loss', 0))
                _ = accuracies.append(metrics.get('accuracy', 0))

            ax.plot(epochs, losses, 'r-o', linewidth=2, markersize=4, label='Loss')
            _ = ax.set_yscale('log')
            ax.set_title('训练进度 - 损失函数', fontsize=12)
            _ = ax.set_xlabel('Epoch')
            _ = ax.set_ylabel('Loss')
            ax.grid(True, alpha=0.3)
            _ = ax.legend()
        except Exception as e:

            _ = logger.error(f"绘制训练进度图时出错: {e}")

    def _plot_system_resources_on_ax(self, ax: Axes, training_data: List[Dict[str, Any]]):
""在指定轴上绘制系统资源"""
        try:

            resources_data = [entry for entry in training_data if entry.get('type') == 'system_resources']:
    if not resources_data:

    return

            resources_data.sort(key=lambda x: x['timestamp'])

            timestamps = []
            cpu_usage = []
            memory_usage = []

            for entry in resources_data:


    data = entry.get('data', {})
                _ = timestamps.append(datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00')))
                _ = cpu_usage.append(data.get('cpu_percent', 0))
                _ = memory_usage.append(data.get('memory_percent', 0))

            ax.plot(timestamps, cpu_usage, 'r-', linewidth=2, label='CPU')
            ax.plot(timestamps, memory_usage, 'b-', linewidth=2, label='内存')

            ax.set_title('系统资源使用', fontsize=12)
            _ = ax.set_ylabel('使用率 (%)')
            ax.grid(True, alpha=0.3)
            _ = ax.legend()

            _ = ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        except Exception as e:

            _ = logger.error(f"绘制系统资源图时出错: {e}")

    def _plot_anomalies_on_ax(self, ax: Axes, training_data: List[Dict[str, Any]]):
""在指定轴上绘制异常检测"""
        try:

            metrics_data = [entry for entry in training_data if entry.get('type') == 'training_metrics']:
    if not metrics_data:

    return

            metrics_data.sort(key=lambda x: x['timestamp'])

            epochs = []
            anomalies_count = []

            for entry in metrics_data:


    _ = epochs.append(entry.get('epoch', 0))
                anomalies = entry.get('anomalies', [])
                _ = anomalies_count.append(len(anomalies))

            # 创建热力图
            data = np.array(anomalies_count).reshape(1, -1)
            im = ax.imshow(data, cmap='Reds', aspect='auto')

            ax.set_title('异常检测热力图', fontsize=12)
            _ = ax.set_xlabel('Epoch')
            _ = ax.set_yticks([0])
            _ = ax.set_yticklabels(['异常'])

            # 添加颜色条
            plt.colorbar(im, ax=ax)
        except Exception as e:

            _ = logger.error(f"绘制异常检测图时出错: {e}")

    def _plot_performance_stats_on_ax(self, ax: Axes, training_data: List[Dict[str, Any]]):
""在指定轴上绘制性能统计"""
        try:
            # 计算一些基本统计信息
            metrics_data = [entry for entry in training_data if entry.get('type') == 'training_metrics']:
    resources_data = [entry for entry in training_data if entry.get('type') == 'system_resources']:

    stats_text = "训练统计信息:\n\n"

            if metrics_data:


    losses = [entry['metrics'].get('loss', 0) for entry in metrics_data]:
    accuracies = [entry['metrics'].get('accuracy', 0) for entry in metrics_data]:

    stats_text += f"总训练轮数: {len(metrics_data)}\n"
                stats_text += f"最终损失: {losses[-1]:.4f}\n"
                stats_text += f"最佳准确率: {max(accuracies).4f}\n"
                stats_text += f"平均损失: {np.mean(losses).4f}\n"

            if resources_data:


    cpu_usage = [entry['data'].get('cpu_percent', 0) for entry in resources_data]:
    memory_usage = [entry['data'].get('memory_percent', 0) for entry in resources_data]:

    stats_text += f"\n资源使用统计:\n"
                stats_text += f"平均CPU使用率: {np.mean(cpu_usage).1f}%\n"
                stats_text += f"平均内存使用率: {np.mean(memory_usage).1f}%\n"
                stats_text += f"峰值CPU使用率: {max(cpu_usage).1f}%\n"
                stats_text += f"峰值内存使用率: {max(memory_usage).1f}%\n"

            ax.text(0.1, 0.9, stats_text, transform=ax.transAxes, fontsize=10,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            ax.set_title('性能统计', fontsize=12)
            _ = ax.axis('off')
        except Exception as e:

            _ = logger.error(f"绘制性能统计时出错: {e}")

    def real_time_visualization(self, scenario_name: str = "default"):
""实时可视化训练过程"""
    context = ErrorContext("TrainingVisualizer", "real_time_visualization")
        try:

            _ = logger.info("🔄 启动实时训练可视化...")

            # 创建实时显示图表
            _ = plt.ion()  # 开启交互模式
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('实时训练监控面板', fontsize=16, fontweight='bold')

            # 初始化数据
            epochs = []
            losses = []
            accuracies = []
            cpu_usage = []
            memory_usage = []
            timestamps = []

            # 实时更新循环
            for i in range(100)  # 模拟100个epoch
                # 模拟数据
                epoch = i + 1
                loss = max(0.01, 1.0 * np.exp(-i/20) + np.random.normal(0, 0.05))
                accuracy = min(0.99, 0.1 + 0.9 * (1 - np.exp(-i/15)) + np.random.normal(0, 0.02))
                cpu = 30 + 20 * np.sin(i/10) + np.random.normal(0, 5)
                memory = 40 + 15 * np.cos(i/8) + np.random.normal(0, 3)

                # 更新数据
                _ = epochs.append(epoch)
                _ = losses.append(loss)
                _ = accuracies.append(accuracy)
                _ = cpu_usage.append(max(0, min(100, cpu)))
                _ = memory_usage.append(max(0, min(100, memory)))
                _ = timestamps.append(datetime.now())

                # 清除并重新绘制
                _ = ax1.clear()
                ax1.plot(epochs, losses, 'r-o', linewidth=2, markersize=4)
                _ = ax1.set_title('实时损失监控')
                _ = ax1.set_xlabel('Epoch')
                _ = ax1.set_ylabel('Loss')
                ax1.grid(True, alpha=0.3)
                _ = ax1.set_yscale('log')

                _ = ax2.clear()
                ax2.plot(epochs, accuracies, 'b-s', linewidth=2, markersize=4)
                _ = ax2.set_title('实时准确率监控')
                _ = ax2.set_xlabel('Epoch')
                _ = ax2.set_ylabel('Accuracy')
                ax2.grid(True, alpha=0.3)
                _ = ax2.set_ylim(0, 1)

                _ = ax3.clear()
                ax3.plot(timestamps[-20:] if len(timestamps) > 20 else timestamps, :
    cpu_usage[-20:] if len(cpu_usage) > 20 else cpu_usage, 'r-', linewidth=2, label='CPU'):
    ax3.plot(timestamps[-20:] if len(timestamps) > 20 else timestamps, :
    memory_usage[-20:] if len(memory_usage) > 20 else memory_usage, 'b-', linewidth=2, label='内存'):
    _ = ax3.set_title('实时系统资源')
                _ = ax3.set_ylabel('使用率 (%)')
                ax3.grid(True, alpha=0.3)
                _ = ax3.legend()

                # 格式化时间轴
                _ = ax3.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

                _ = ax4.clear()
                # 显示统计信息
                stats_text = f"当前Epoch: {epoch}\n"
                stats_text += f"当前损失: {loss:.4f}\n"
                stats_text += f"当前准确率: {accuracy:.4f}\n"
                stats_text += f"CPU使用率: {cpu:.1f}%\n"
                stats_text += f"内存使用率: {memory:.1f}%\n"

                ax4.text(0.1, 0.9, stats_text, transform=ax4.transAxes, fontsize=10,
                        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
                _ = ax4.set_title('当前状态')
                _ = ax4.axis('off')

                _ = plt.tight_layout()
                _ = plt.draw()
                _ = plt.pause(0.1)  # 暂停以更新显示

                # 模拟训练时间
                _ = time.sleep(0.05)

            _ = plt.ioff()  # 关闭交互模式
            _ = plt.show()

            _ = logger.info("✅ 实时训练可视化完成")
        except Exception as e:

            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 实时训练可视化失败: {e}")

    def generate_visualization_script(self, output_path = None):
""生成独立的可视化脚本"""
    context = ErrorContext("TrainingVisualizer", "generate_visualization_script")
        try:

            if not output_path:


    output_path = str(project_root / 'training' / 'visualize_progress.py')

            script_content = '''#!/usr/bin/env python3
"""
训练进度可视化脚本
自动生成训练过程的可视化图表
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from pathlib import Path

def load_training_data(log_file="logs/training_monitor.log"):
""加载训练日志数据"""
    if not Path(log_file).exists():
 = print(f"日志文件不存在: {log_file}")
    return []

    training_data = []
    try:

    with open(log_file, 'r', encoding='utf-8') as f:
    for line in f:

    try:


            entry = json.loads(line.strip()):
    if entry.get('type') in ['training_metrics', 'system_resources']:

    _ = training_data.append(entry)
                except json.JSONDecodeError:

                    continue
    return training_data
    except Exception as e:

    _ = print(f"加载日志数据失败: {e}")
    return []

def create_progress_plot(training_data, output_file="progress_visualization.png"):
""创建训练进度图"""
    metrics_data = [entry for entry in training_data if entry.get('type') == 'training_metrics']:
    if not metrics_data:

    _ = print("没有找到训练指标数据")
    return False

    # 按时间排序
    metrics_data.sort(key=lambda x: x['timestamp'])

    # 提取数据
    epochs = []
    losses = []
    accuracies = []

    for entry in metrics_data:


    _ = epochs.append(entry.get('epoch', 0))
    metrics = entry.get('metrics', {})
    _ = losses.append(metrics.get('loss', 0))
    _ = accuracies.append(metrics.get('accuracy', 0))

    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle('训练进度可视化', fontsize=16, fontweight='bold')

    # 损失曲线
    ax1.plot(epochs, losses, 'r-o', linewidth=2, markersize=4)
    ax1.set_title('损失函数变化', fontsize=14)
    _ = ax1.set_xlabel('Epoch')
    _ = ax1.set_ylabel('Loss')
    ax1.grid(True, alpha=0.3)
    _ = ax1.set_yscale('log')

    # 准确率曲线
    ax2.plot(epochs, accuracies, 'b-s', linewidth=2, markersize=4)
    ax2.set_title('准确率变化', fontsize=14)
    _ = ax2.set_xlabel('Epoch')
    _ = ax2.set_ylabel('Accuracy')
    ax2.grid(True, alpha=0.3)
    _ = ax2.set_ylim(0, 1)

    _ = plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    _ = plt.close()

    _ = print(f"训练进度可视化已保存到: {output_file}")
    return True

def main() -> None:
    """主函数"""
    _ = print("开始生成训练进度可视化...")

    # 加载训练数据
    training_data = load_training_data()
    if not training_data:

    _ = print("没有找到训练数据，生成示例图表...")
    # 生成示例数据
    epochs = list(range(1, 51))
        losses = [max(0.01, 1.0 * np.exp(-i/10) + np.random.normal(0, 0.05)) for i in epochs]:
    accuracies = [min(0.99, 0.1 + 0.9 * (1 - np.exp(-i/8)) + np.random.normal(0, 0.02)) for i in epochs]

    # 创建示例数据结构
    training_data = []
        for i, epoch in enumerate(epochs):
raining_data.append({
                _ = 'timestamp': datetime.now().isoformat(),
                'type': 'training_metrics',
                'epoch': epoch,
                'metrics': {'loss': losses[i], 'accuracy': accuracies[i]},
                'anomalies': []
            })

    # 生成可视化图表
    success = create_progress_plot(training_data)
    if success:

    _ = print("训练进度可视化生成成功!")
    else:

    _ = print("训练进度可视化生成失败!")

if __name__ == '__main__':


    _ = main()
'''

            # 写入脚本文件
            with open(output_path, 'w', encoding='utf-8') as f:
    _ = f.write(script_content)

            _ = logger.info(f"✅ 可视化脚本已生成: {output_path}")
            return True

        except Exception as e:


            _ = self.error_handler.handle_error(e, context)
            _ = logger.error(f"❌ 生成可视化脚本失败: {e}")
            return False

# 全局训练可视化器实例
global_training_visualizer = TrainingVisualizer()

def main() -> None:
    """主函数，用于测试可视化器"""
    _ = print("📊 测试训练可视化器...")

    # 创建可视化器实例
    visualizer = TrainingVisualizer()

    # 生成可视化脚本
    _ = print("📝 生成可视化脚本...")
    _ = visualizer.generate_visualization_script()

    # 模拟一些训练数据
    _ = print("🔄 生成模拟训练数据...")

    # 模拟训练指标数据
    training_data = []

    # 添加训练指标数据
    for epoch in range(1, 21):
imestamp = datetime.now().isoformat()
    metrics = {
            'loss': max(0.01, 1.0 * np.exp(-epoch/5) + np.random.normal(0, 0.05)),
            'accuracy': min(0.99, 0.1 + 0.9 * (1 - np.exp(-epoch/4)) + np.random.normal(0, 0.02))
    }
        anomalies = [] if np.random.random() > 0.8 else [{'type': 'loss_spike'}]:
raining_data.append({
            'timestamp': timestamp,
            'type': 'training_metrics',
            'epoch': epoch,
            'metrics': metrics,
            'anomalies': anomalies
    })

    # 添加系统资源数据
        if epoch % 3 == 0:

    resources = {
                'cpu_percent': 30 + 20 * np.random.random(),
                'memory_percent': 40 + 15 * np.random.random(),
                'disk_percent': 50 + 10 * np.random.random()
            }

            training_data.append({
                'timestamp': timestamp,
                'type': 'system_resources',
                'data': resources
            })

    _ = time.sleep(0.01)  # 模拟时间间隔

    _ = print(f"✅ 生成了 {len(training_data)} 条模拟数据")

    # 生成可视化报告
    _ = print("📊 生成可视化报告...")
    generated_file = visualizer.create_training_progress_plot(training_data)

    if generated_file:


    _ = print(f"✅ 生成了可视化文件: {generated_file}")
    else:

    _ = print("❌ 未能生成可视化文件")

    _ = print("\n🎉 训练可视化器测试完成")

if __name__ == "__main__":


    _ = main()