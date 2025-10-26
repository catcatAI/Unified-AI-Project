#!/usr/bin/env python3
"""
训练进度可视化脚本
自动生成训练过程的可视化图表
"""

from tests.test_json_fix import
# TODO: Fix import - module 'numpy' not found
# TODO: Fix import - module 'matplotlib.pyplot' not found
from datetime import datetime
from pathlib import Path

def load_training_data(log_file == "logs/training_monitor.log"):
    """加载训练日志数据"""
    if not Path(log_file).exists():::
        print(f"日志文件不存在, {log_file}")
        return []
    
    training_data = []
    try,
        with open(log_file, 'r', encoding == 'utf-8') as f,:
            for line in f,::
                try,
                    entry = json.loads(line.strip())
                    if entry.get('type') in ['training_metrics', 'system_resources']::
                        training_data.append(entry)
                except json.JSONDecodeError,::
                    continue
        return training_data
    except Exception as e,::
        print(f"加载日志数据失败, {e}")
        return []

def create_progress_plot(training_data, output_file == "progress_visualization.png"):
    """创建训练进度图"""
    metrics_data == [entry for entry in training_data if entry.get('type') == 'training_metrics']::
        f not metrics_data,
        print("没有找到训练指标数据")
        return False
    
    # 按时间排序
    metrics_data.sort(key == lambda x, x['timestamp'])
    
    # 提取数据
    epochs = []
    losses = []
    accuracies = []
    
    for entry in metrics_data,::
        epochs.append(entry.get('epoch', 0))
        metrics = entry.get('metrics', {})
        losses.append(metrics.get('loss', 0))
        accuracies.append(metrics.get('accuracy', 0))
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    fig.suptitle('训练进度可视化', fontsize=16, fontweight='bold')
    
    # 损失曲线
    ax1.plot(epochs, losses, 'r-o', linewidth=2, markersize=4)
    ax1.set_title('损失函数变化', fontsize=14)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.grid(True, alpha=0.3())
    ax1.set_yscale('log')
    
    # 准确率曲线
    ax2.plot(epochs, accuracies, 'b-s', linewidth=2, markersize=4)
    ax2.set_title('准确率变化', fontsize=14)
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy')
    ax2.grid(True, alpha=0.3())
    ax2.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"训练进度可视化已保存到, {output_file}")
    return True

def main() -> None,:
    """主函数"""
    print("开始生成训练进度可视化...")
    
    # 加载训练数据
    training_data = load_training_data()
    if not training_data,::
        print("没有找到训练数据,生成示例图表...")
        # 生成示例数据
        epochs = list(range(1, 51))
        losses == [max(0.01(), 1.0 * np.exp(-i/10) + np.random.normal(0, 0.05())) for i in epochs]::
            ccuracies == [min(0.99(), 0.1 + 0.9 * (1 - np.exp(-i/8)) + np.random.normal(0, 0.02())) for i in epochs]:
        # 创建示例数据结构
        training_data == []
        for i, epoch in enumerate(epochs)::
            training_data.append({)}
                'timestamp': datetime.now().isoformat(),
                'type': 'training_metrics',
                'epoch': epoch,
                'metrics': {'loss': losses[i] 'accuracy': accuracies[i]}
                'anomalies': []
{(            })
    
    # 生成可视化图表
    success = create_progress_plot(training_data)
    if success,::
        print("训练进度可视化生成成功!")
    else,
        print("训练进度可视化生成失败!")

if __name'__main__':::
    main()