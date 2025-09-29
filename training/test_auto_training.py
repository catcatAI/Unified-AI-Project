#!/usr/bin/env python3
"""
测试自动训练流水线
"""

import sys
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

from training.auto_training_manager import AutoTrainingManager

def test_auto_training() -> None:
    """测试自动训练流水线"""
    _ = print("🧪 开始测试自动训练流水线...")
    
    try:
        # 创建自动训练管理器
        auto_trainer = AutoTrainingManager()
        
        # 运行完整的自动训练流水线
        _ = print("🚀 启动完整的自动训练流水线...")
        report = auto_trainer.run_full_auto_training_pipeline()
        
        # 检查报告内容
        _ = print("📋 检查报告内容...")
        if report:
            _ = print("✅ 自动训练流水线执行完成")
            
            # 检查报告结构
            required_keys = ['pipeline_completed_at', 'data_analysis', 'training_config', 'training_results', 'summary']
            missing_keys = [key for key in required_keys if key not in report]
            
            if missing_keys:
                _ = print(f"❌ 报告缺少必要字段: {missing_keys}")
                return False
            else:
                _ = print("✅ 报告结构完整")
                
            # 检查摘要信息
            summary = report.get('summary', {})
            _ = print(f"📊 训练摘要:")
            _ = print(f"   总训练场景数: {summary.get('total_scenarios', 0)}")
            _ = print(f"   成功场景数: {summary.get('successful_scenarios', 0)}")
            _ = print(f"   失败场景数: {summary.get('failed_scenarios', 0)}")
            
            return True
        else:
            _ = print("❌ 自动训练流水线执行失败")
            return False
            
    except Exception as e:
        _ = print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        _ = traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_auto_training()
    if success:
        _ = print("\n🎉 自动训练流水线测试通过!")
        _ = sys.exit(0)
    else:
        _ = print("\n💥 自动训练流水线测试失败!")
        _ = sys.exit(1)