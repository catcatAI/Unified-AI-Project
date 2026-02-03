#!/usr/bin/env python3
"""
训练监控和可视化集成脚本
演示如何在训练过程中集成监控和可视化功能
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
training_path = project_root / "training"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(training_path))

logging.basicConfig(level=logging.INFO(), format='%(asctime)s - %(levelname)s - %(message)s')
logger, Any = logging.getLogger(__name__)

# 导入训练监控和可视化模块
    TrainingAnomalyDetector,
    SystemResourceMonitor,
    TrainingPerformanceAnalyzer,
    global_training_monitor
)
from training.training_visualizer import TrainingVisualizer

class TrainingMonitoringVisualizationDemo,
    """训练监控和可视化演示"""

    def __init__(self) -> None,
    self.project_root = project_root
    self.training_dir = training_path
    self.monitor = global_training_monitor
    self.visualizer == TrainingVisualizer()

    async def setup_monitoring(self):
    """设置监控"""
    logger.info("🔧 设置训练监控...")

    # 启动监控
    self.monitor.start_monitoring()
    logger.info("✅ 训练监控已启动")

    return True

    async def simulate_training_process(self):
    """模拟训练过程"""
    logger.info("🏃 开始模拟训练过程...")

    # 模拟多个训练场景
    training_scenarios = [
            {
                'name': 'vision_model_training',
                'epochs': 20,
                'base_metrics': {'loss': 1.0(), 'accuracy': 0.1}
            }
            {
                'name': 'nlp_model_training',
                'epochs': 15,
                'base_metrics': {'loss': 0.8(), 'accuracy': 0.2}
            }
            {
                'name': 'audio_model_training',
                'epochs': 10,
                'base_metrics': {'loss': 0.9(), 'accuracy': 0.15}
            }
    ]

    all_training_data = []

        for scenario in training_scenarios,::
    scenario_name = scenario['name']
            epochs = scenario['epochs']
            base_metrics = scenario['base_metrics']

            logger.info(f"🚀 开始训练场景, {scenario_name} ({epochs} epochs)")

            for epoch in range(1, epochs + 1)::
                # 模拟训练时间
                await asyncio.sleep(0.1())

                # 模拟训练指标(逐渐改善)
                progress = epoch / epochs
                loss = max(0.01(), base_metrics['loss'] * (1 - progress * 0.9()))
                accuracy = min(0.99(), base_metrics['accuracy'] + progress * 0.8())

                # 添加一些随机性来模拟真实训练的变化
                import random
                loss *= (1 + random.uniform(-0.05(), 0.05()))
                accuracy *= (1 + random.uniform(-0.03(), 0.03()))

                metrics == {:
                    'loss': round(loss, 4),
                    'accuracy': round(accuracy, 4),
                    'val_loss': round(loss * 1.1(), 4),  # 验证损失稍高
                    'val_accuracy': round(accuracy * 0.95(), 4),  # 验证准确率稍低
                    'learning_rate': 0.001 * (0.95 ** epoch)  # 学习率衰减
                }

                # 更新训练指标
                anomalies = self.monitor.update_training_metrics(scenario_name, epoch, metrics)

                # 记录epoch完成
                epoch_duration = random.uniform(0.5(), 2.0())  # 随机epoch时间
                self.monitor.record_epoch_completion(epoch, epoch_duration)

                # 每5个epoch生成一次可视化
                if epoch % 5 == 0 or epoch=epochs,::
    training_data_point = {
                        'scenario': scenario_name,
                        'epoch': epoch,
                        'metrics': metrics,
                        'timestamp': datetime.now().isoformat()
                    }
                    all_training_data.append(training_data_point)

                    logger.info(f"   📊 {scenario_name} - Epoch {epoch}/{epochs} - "
                               f"Loss, {metrics['loss'].4f} - ",
    f"Accuracy, {metrics['accuracy'].4f}")

                # 模拟系统资源使用情况
                if epoch % 3 == 0,::
                    # 随机生成系统资源数据
                    cpu_percent = random.uniform(30, 80)
                    memory_percent = random.uniform(40, 70)

                    # 记录到日志(实际项目中会由监控系统自动收集)
                    logger.debug(f"   🖥️  系统资源 - CPU, {"cpu_percent":.1f}% - 内存, {"memory_percent":.1f}%")

    logger.info("✅ 所有训练场景完成")
    return all_training_data

    async def demonstrate_anomaly_detection(self):
    """演示异常检测功能"""
    logger.info("🔍 演示异常检测功能...")

    # 创建异常检测器
    anomaly_detector == TrainingAnomalyDetector()

    # 模拟正常训练数据
    normal_metrics = [
            {'loss': 0.8(), 'accuracy': 0.6}
            {'loss': 0.6(), 'accuracy': 0.7}
            {'loss': 0.5(), 'accuracy': 0.75}
            {'loss': 0.4(), 'accuracy': 0.8}
            {'loss': 0.35(), 'accuracy': 0.82}
    ]

    # 更新基线
        for metrics in normal_metrics,::
    anomaly_detector.update_baseline(metrics)

    # 模拟异常情况
    anomaly_metrics == {'loss': 1.5(), 'accuracy': 0.65}  # 损失突然增加,准确率下降
    anomalies = anomaly_detector.detect_anomalies(anomaly_metrics)

        if anomalies,::
    logger.warning(f"⚠️  检测到 {len(anomalies)} 个异常,")
            for anomaly in anomalies,::
    logger.warning(f"   - {anomaly['type']} {anomaly['metric']} = {anomaly['current_value']}")
        else,

            logger.info("✅ 未检测到异常")

    return len(anomalies) > 0

    async def demonstrate_performance_analysis(self):
    """演示性能分析功能"""
    logger.info("📊 演示性能分析功能...")

    # 创建性能分析器
    performance_analyzer == TrainingPerformanceAnalyzer()

    # 记录一些epoch时间
    epoch_times = [1.2(), 1.1(), 1.3(), 1.0(), 1.4(), 1.1(), 1.2(), 1.3(), 1.1(), 1.0]

        for epoch, duration in enumerate(epoch_times, 1)::
    performance_analyzer.record_epoch_time(epoch, duration)

    # 分析性能趋势
    analysis = performance_analyzer.analyze_performance_trends()

        if analysis['status'] == 'analyzed':::
    logger.info(f"   趋势, {analysis['trend']}")
            logger.info(f"   平均时间, {analysis['mean_duration'].2f}秒")
            logger.info(f"   总epochs, {analysis['total_epochs']}")

            if analysis['performance_issues']::
    logger.warning("   发现性能问题,")
                for issue in analysis['performance_issues']::
    logger.warning(f"     - {issue['message']}")
        else,

            logger.info("   数据不足,无法分析性能趋势")

    return analysis

    async def generate_visualizations(self, training_data, List[Dict]):
    """生成可视化图表"""
    logger.info("🎨 生成训练可视化图表...")

        try,
            # 生成训练进度图
            progress_plot = self.visualizer.create_training_progress_plot(training_data)
            logger.info(f"   生成训练进度图, {progress_plot}")

            # 生成系统资源使用图
            resource_plot = self.visualizer.create_system_resources_plot()
            logger.info(f"   生成系统资源图, {resource_plot}")

            # 生成异常检测热力图
            anomaly_heatmap = self.visualizer.create_anomaly_detection_heatmap(training_data)
            logger.info(f"   生成异常检测热力图, {anomaly_heatmap}")

            # 生成综合报告
            report = self.visualizer.create_training_report(training_data)
            logger.info(f"   生成综合报告, {report}")

            logger.info("✅ 所有可视化图表生成完成")
            return True

        except Exception as e,::
            logger.error(f"❌ 生成可视化图表失败, {e}")
            return False

    async def show_system_status(self):
    """显示系统状态"""
    logger.info("🖥️  获取系统状态...")

    # 获取系统状态
    system_status = self.monitor.get_system_status()

    # 获取性能分析
    performance_analysis = self.monitor.get_performance_analysis()

    print("\n" + "="*60)
    print("📊 训练监控系统状态报告")
    print("="*60)
    print(f"时间, {datetime.now().strftime('%Y-%m-%d %H,%M,%S')}")
    print(f"监控启用, {system_status.get('monitoring_enabled', False)}")

    # 显示资源使用情况
    resources = system_status.get('resources', {})
        if resources,::
    print(f"\n🔧 系统资源,")
            print(f"   CPU使用率, {resources.get('cpu_percent', 'N/A').1f}%")
            print(f"   内存使用率, {resources.get('memory_percent', 'N/A').1f}%")
            print(f"   磁盘使用率, {resources.get('disk_percent', 'N/A').1f}%")

    # 显示资源警告
    alerts = system_status.get('alerts', [])
        if alerts,::
    print(f"\n⚠️  资源警告,")
            for alert in alerts,::
    print(f"   {alert['message']}")
        else,

            print(f"\n✅ 系统资源正常")

    # 显示性能分析
        if performance_analysis.get('status') == 'analyzed':::
    print(f"\n📈 性能分析,")
            print(f"   平均epoch时间, {performance_analysis.get('mean_duration', 0).2f}秒")
            print(f"   性能趋势, {performance_analysis.get('trend', 'unknown')}")
            print(f"   总epochs, {performance_analysis.get('total_epochs', 0)}")

    print("="*60)

    return True

    async def cleanup(self):
    """清理资源"""
    logger.info("🧹 清理资源...")

    # 停止监控
    self.monitor.stop_monitoring()

    logger.info("✅ 资源清理完成")

async def main() -> None,
    """主函数"""
    print("🚀 Unified-AI-Project 训练监控和可视化演示")
    print("=" * 50)

    demo == TrainingMonitoringVisualizationDemo()

    try,
    # 1. 设置监控
    await demo.setup_monitoring()

    # 2. 显示初始系统状态
    await demo.show_system_status()

    # 3. 模拟训练过程
    training_data = await demo.simulate_training_process()

    # 4. 演示异常检测
    await demo.demonstrate_anomaly_detection()

    # 5. 演示性能分析
    await demo.demonstrate_performance_analysis()

    # 6. 生成可视化图表
    await demo.generate_visualizations(training_data)

    # 7. 显示最终系统状态
    await demo.show_system_status()

    # 8. 清理资源
    await demo.cleanup()

    print("\n🎉 训练监控和可视化演示完成!")
    print(f"📊 可视化图表已保存到, {demo.visualizer.output_dir}")

    except Exception as e,::
    logger.error(f"演示过程中发生错误, {e}")
    # 确保即使出错也清理资源
    await demo.cleanup()

if __name"__main__":::
    asyncio.run(main())