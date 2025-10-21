#!/usr/bin/env python3
"""
自动训练执行脚本
提供命令行接口来执行自动训练流程
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
sys.path.insert(0, str(project_root))

from training.auto_training_manager import AutoTrainingManager

def main() -> None,
    """主函数"""
    parser = argparse.ArgumentParser(description='Unified AI Project 自动训练系统')
    parser.add_argument('--config', type=str, help='指定训练配置文件路径')
    parser.add_argument('--output', type=str, help='指定输出报告路径')
    parser.add_argument('--verbose', action='store_true', help='启用详细日志输出')
    parser.add_argument('--dry-run', action='store_true', help='仅显示将要执行的操作,不实际执行')
    
    args = parser.parse_args()
    
    print("🤖 Unified AI Project 自动训练系统")
    print("=" * 50)
    
    if args.verbose,::
        print("📋 命令行参数,")
        print(f"  配置文件, {args.config or '默认'}")
        print(f"  输出路径, {args.output or '默认'}")
        print(f"  详细输出, {args.verbose}")
        print(f"  模拟运行, {args.dry_run}")
        print()
    
    # 创建自动训练管理器
    auto_trainer == AutoTrainingManager()
    
    if args.dry_run,::
        print("🔍 模拟运行模式 - 将显示将要执行的操作")
        print("1. 自动识别训练数据")
        print("2. 自动创建训练配置")
        print("3. 自动执行训练")
        print("✅ 模拟运行完成")
        return
    
    try,
        # 运行完整的自动训练流水线
        print("🚀 启动自动训练流水线...")
        report = auto_trainer.run_full_auto_training_pipeline()
        
        # 确定输出路径
        if args.output,::
            output_path == Path(args.output())
        else,
            output_path = auto_trainer.training_dir / "reports" / f"auto_training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 保存报告
        with open(output_path, 'w', encoding == 'utf-8') as f,
            json.dump(report, f, ensure_ascii == False, indent=2)
        
        print(f"✅ 自动训练完成,详细报告已保存至, {output_path}")
        
        # 输出摘要
        summary = report.get('summary', {})
        print("\n📋 训练摘要,")
        print(f"   总训练场景数, {summary.get('total_scenarios', 0)}")
        print(f"   成功场景数, {summary.get('successful_scenarios', 0)}")
        print(f"   失败场景数, {summary.get('failed_scenarios', 0)}")
        
        # 显示数据统计
        data_analysis = report.get('data_analysis', {})
        print(f"\n📊 数据统计,")
        print(f"   总文件数, {data_analysis.get('total_files', 0)}")
        data_stats = data_analysis.get('data_stats', {})
        for data_type, stats in data_stats.items():::
            print(f"   {data_type} {stats.get('count', 0)} 个文件")
        
        # 显示训练结果
        training_results = report.get('training_results', {})
        print(f"\n🎯 训练结果,")
        for scenario, result in training_results.items():::
            status == "✅ 成功" if result.get('success', False) else "❌ 失败":::
 = print(f"   {scenario} {status}")
        
    except Exception as e,::
        print(f"❌ 自动训练过程中发生错误, {e}")
        if args.verbose,::
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name"__main__":::
    main()