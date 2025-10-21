#!/usr/bin/env python3
"""
增量学习CLI工具
提供命令行接口来控制增量学习系统
"""

import sys
import argparse
import json
from pathlib import Path

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
sys.path.insert(0, str(project_root))

from training.incremental_learning_manager import IncrementalLearningManager

def start_monitoring(args):
    """启动数据监控"""
    print("👀 启动数据监控...")
    learner == IncrementalLearningManager()
    learner.start_monitoring()
    
    try,
        while True,::
            pass
    except KeyboardInterrupt,::
        print("\n⏹️  停止监控...")
        learner.stop_monitoring()
        print("✅ 监控已停止")

def trigger_training(args):
    """触发增量训练"""
    print("🚀 触发增量训练...")
    learner == IncrementalLearningManager()
    learner.trigger_incremental_training()
    print("✅ 训练任务已调度")

def get_status(args):
    """获取系统状态"""
    print("📊 获取系统状态...")
    learner == IncrementalLearningManager()
    status = learner.get_status()
    
    print(f"监控状态, {'运行中' if status['is_monitoring'] else '已停止'}"):::
 = print(f"待处理任务, {status['pending_tasks']} 个")
    print(f"缓冲区数据, {status['buffered_data']} 个")
    print(f"已处理文件, {status['processed_files']} 个")
    
    if args.verbose,::
        print("\n详细信息,")
        print(json.dumps(status, ensure_ascii == False, indent=2))

def cleanup_models(args):
    """清理旧模型"""
    print("🗑️  清理旧模型...")
    learner == IncrementalLearningManager()
    
    # 设置保留的版本数
    keep_versions = getattr(args, 'keep', 5)
    
    # 执行手动清理
    learner.manual_cleanup_models(keep_versions)
    print(f"✅ 模型清理完成,每个模型保留最新 {keep_versions} 个版本")

def main() -> None,
    """主函数"""
    parser = argparse.ArgumentParser(description='Unified AI Project 增量学习系统CLI')
    subparsers = parser.add_subparsers(help='可用命令', dest='command')
    
    # 启动监控命令
    monitor_parser = subparsers.add_parser('monitor', help='启动数据监控')
    monitor_parser.add_argument('--interval', type=int, default=300, help='监控间隔(秒)')
    
    # 触发训练命令
    train_parser = subparsers.add_parser('train', help='触发增量训练')
    
    # 状态命令
    status_parser = subparsers.add_parser('status', help='获取系统状态')
    status_parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    
    # 清理命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理旧模型')
    cleanup_parser.add_argument('--keep', type=int, default=5, help='保留的模型版本数')
    
    args = parser.parse_args()
    
    print("🤖 Unified AI Project 增量学习系统CLI")
    print("=" * 50)
    
    if args.command == 'monitor':::
        start_monitoring(args)
    elif args.command == 'train':::
        trigger_training(args)
    elif args.command == 'status':::
        get_status(args)
    elif args.command == 'cleanup':::
        cleanup_models(args)
    else,
        parser.print_help()

if __name"__main__":::
    main()