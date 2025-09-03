#!/usr/bin/env python3
"""
测试自动训练流水线
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from training.auto_training_manager import AutoTrainingManager

def test_auto_training():
    """测试自动训练流水线"""
    print("🧪 开始测试自动训练流水线...")
    
    try:
        # 创建自动训练管理器
        auto_trainer = AutoTrainingManager()
        
        # 运行完整的自动训练流水线
        print("🚀 启动完整的自动训练流水线...")
        report = auto_trainer.run_full_auto_training_pipeline()
        
        # 检查报告内容
        print("📋 检查报告内容...")
        if report:
            print("✅ 自动训练流水线执行完成")
            
            # 检查报告结构
            required_keys = ['pipeline_completed_at', 'data_analysis', 'training_config', 'training_results', 'summary']
            missing_keys = [key for key in required_keys if key not in report]
            
            if missing_keys:
                print(f"❌ 报告缺少必要字段: {missing_keys}")
                return False
            else:
                print("✅ 报告结构完整")
                
            # 检查摘要信息
            summary = report.get('summary', {})
            print(f"📊 训练摘要:")
            print(f"   总训练场景数: {summary.get('total_scenarios', 0)}")
            print(f"   成功场景数: {summary.get('successful_scenarios', 0)}")
            print(f"   失败场景数: {summary.get('failed_scenarios', 0)}")
            
            return True
        else:
            print("❌ 自动训练流水线执行失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_auto_training()
    if success:
        print("\n🎉 自动训练流水线测试通过!")
        sys.exit(0)
    else:
        print("\n💥 自动训练流水线测试失败!")
        sys.exit(1)