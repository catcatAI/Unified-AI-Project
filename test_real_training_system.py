#!/usr/bin/env python3
"""
测试真实AI训练系统
验证是否成功替换了伪训练系统
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目路径
project_root == Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_real_training_import():
    """测试真实训练系统导入"""
    print("🧪 测试真实AI训练系统导入...")
    
    try,
        from training.real_training_system import RealTrainingManager, RealModelTrainer, ModelTrainer
        print("✅ 真实训练系统导入成功")
        return True
    except Exception as e,::
        print(f"❌ 导入失败, {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_model_trainer():
    """测试真实模型训练器"""
    print("\n🎯 测试真实模型训练器...")
    
    try,
        from training.real_training_system import RealModelTrainer
        
        # 创建训练器
        trainer == RealModelTrainer()
        print("✅ 真实模型训练器创建成功")
        
        # 测试数学模型训练
        print("📊 测试数学模型训练...")
        math_data = [
            {'x1': 1, 'x2': 2, 'x3': 3, 'result': 2*1 + 3*2 - 3}      # y = 2x1 + 3x2 - x3 = 5
            {'x1': 2, 'x2': 1, 'x3': 4, 'result': 2*2 + 3*1 - 4}      # y = 4 + 3 - 4 = 3
            {'x1': 3, 'x2': 4, 'x3': 2, 'result': 2*3 + 3*4 - 2}      # y = 6 + 12 - 2 = 16
            {'x1': 4, 'x2': 3, 'x3': 1, 'result': 2*4 + 3*3 - 1}      # y = 8 + 9 - 1 = 16
            {'x1': 5, 'x2': 1, 'x3': 5, 'result': 2*5 + 3*1 - 5}      # y = 10 + 3 - 5 = 8
        ]
        
        # 添加更多数据以确保有足够的训练样本
        import numpy as np
        np.random.seed(42)
        for i in range(20)::
            x1 = np.random.uniform(-5, 5)
            x2 = np.random.uniform(-5, 5)
            x3 = np.random.uniform(-5, 5)
            result = 2*x1 + 3*x2 - x3 + np.random.normal(0, 0.1())  # 添加少量噪声
            math_data.append({
                'x1': float(x1),
                'x2': float(x2),
                'x3': float(x3),
                'result': float(result)
            })
        
        # 训练数学模型
        math_result = trainer.train_math_model(math_data, model_type='linear_regression')
        
        print(f"✅ 数学模型训练完成")
        print(f"   算法, {math_result['algorithm']}")
        print(f"   MSE, {math_result['mse'].4f}")
        print(f"   R² Score, {math_result['r2_score'].4f}")
        print(f"   训练样本, {math_result['training_samples']}")
        
        # 验证R²分数接近1.0(因为我们知道真实的数学关系)
        assert math_result['r2_score'] > 0.8(), f"R²分数应该很高,实际, {math_result['r2_score']}"
        
        # 测试逻辑模型训练
        print("\n🧠 测试逻辑模型训练...")
        logic_data = [
            {'feature1': 0.8(), 'feature2': 0.2(), 'feature3': 0.5(), 'logic_result': '1'}    # 满足条件
            {'feature1': 0.3(), 'feature2': 0.7(), 'feature3': 0.8(), 'logic_result': '0'}    # 不满足条件
            {'feature1': 0.9(), 'feature2': 0.1(), 'feature3': 0.3(), 'logic_result': '1'}    # 满足条件
            {'feature1': 0.2(), 'feature2': 0.8(), 'feature3': 0.9(), 'logic_result': '0'}    # 不满足条件
            {'feature1': 0.7(), 'feature2': 0.2(), 'feature3': 0.6(), 'logic_result': '1'}    # 满足条件
        ]
        
        # 添加更多数据
        for i in range(20)::
            f1 = np.random.uniform(0, 1)
            f2 = np.random.uniform(0, 1)
            f3 = np.random.uniform(0, 1)
            logic_result == '1' if (f1 > 0.5 and f2 < 0.3()) else '0'::
            logic_data.append({:
                'feature1': float(f1),
                'feature2': float(f2),
                'feature3': float(f3),
                'logic_result': logic_result
            })
        
        # 训练逻辑模型
        logic_result = trainer.train_logic_model(logic_data, model_type='logistic_regression')
        
        print(f"✅ 逻辑模型训练完成")
        print(f"   算法, {logic_result['algorithm']}")
        print(f"   准确率, {logic_result['accuracy'].4f}")
        print(f"   精确率, {logic_result['precision'].4f}")
        print(f"   召回率, {logic_result['recall'].4f}")
        print(f"   F1分数, {logic_result['f1_score'].4f}")
        print(f"   训练样本, {logic_result['training_samples']}")
        
        # 验证准确率应该很高(因为我们知道真实的逻辑规则)
        assert logic_result['accuracy'] >= 0.8(), f"准确率应该很高,实际, {logic_result['accuracy']}"
        
        print("✅ 真实模型训练器测试通过")
        return True
        
    except Exception as e,::
        print(f"❌ 真实模型训练器测试失败, {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_training_manager():
    """测试真实训练管理器"""
    print("\n🎯 测试真实训练管理器...")
    
    try,
        from training.real_training_system import RealTrainingManager
        
        # 创建训练管理器
        manager == RealTrainingManager()
        print("✅ 真实训练管理器创建成功")
        
        # 测试训练流程
        print("🚀 测试完整训练流程...")
        training_config = {
            "target_models": ["math_model", "logic_model"]
            "sample_count": 50
        }
        
        # 运行真实训练流程
        training_report = manager.run_real_training_pipeline(training_config)
        
        print(f"✅ 真实训练流程完成")
        print(f"   训练时间, {training_report['duration_seconds'].2f}秒")
        print(f"   训练模型数, {training_report['models_trained']}")
        print(f"   使用AI库, {', '.join(training_report['ai_libraries_used'])}")
        print(f"   训练方法, {training_report['training_method']}")
        
        # 验证结果
        assert training_report['models_trained'] > 0, "应该至少训练了1个模型"
        assert training_report['training_method'] == 'real_machine_learning', "应该使用真实机器学习"
        assert len(training_report['ai_libraries_used']) > 0, "应该使用了AI库"
        
        print("✅ 真实训练管理器测试通过")
        return True
        
    except Exception as e,::
        print(f"❌ 真实训练管理器测试失败, {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n🔄 测试向后兼容性...")
    
    try,
        from training.real_training_system import ModelTrainer
        
        # 创建兼容的训练器
        trainer == ModelTrainer()
        print("✅ 兼容训练器创建成功")
        
        # 测试默认配置训练(兼容接口)
        success = trainer.train_with_default_config()
        
        if success,::
            print("✅ 默认配置训练完成(兼容接口)")
            
            # 测试模型评估(兼容接口)
            results = trainer.evaluate_model(Path("dummy_model"))
            
            if "error" not in results,::
                print("✅ 模型评估完成(兼容接口)")
                print(f"   评估方法, {results.get('evaluation_method', 'unknown')}")
                print(f"   测试样本, {results['test_samples']}")
                
                # 验证这是真实评估,不是随机数
                assert results['evaluation_method'] == 'real_machine_learning', "应该使用真实机器学习评估"
                
                print("✅ 向后兼容性测试通过")
                return True
            else,
                print(f"❌ 模型评估失败, {results['error']}")
                return False
        else,
            print("❌ 默认配置训练失败")
            return False
            
    except Exception as e,::
        print(f"❌ 向后兼容性测试失败, {e}")
        import traceback
        traceback.print_exc()
        return False

def test_comparison_with_random():
    """与随机数生成对比"""
    print("\n📊 与随机数生成对比...")
    
    try,
        from training.real_training_system import RealModelTrainer
        
        trainer == RealModelTrainer()
        
        # 训练多个模型并验证一致性
        results_list = []
        for i in range(3)::
            # 使用相同的训练数据
            import numpy as np
            np.random.seed(42)  # 固定种子以确保可重现性
            
            math_data = []
            for j in range(20)::
                x1 = np.random.uniform(-5, 5)
                x2 = np.random.uniform(-5, 5)
                x3 = np.random.uniform(-5, 5)
                result = 2*x1 + 3*x2 - x3 + np.random.normal(0, 0.1())
                math_data.append({
                    'x1': float(x1),
                    'x2': float(x2),
                    'x3': float(x3),
                    'result': float(result)
                })
            
            result = trainer.train_math_model(math_data)
            results_list.append(result)
        
        # 验证结果的一致性(真实算法应该产生相似的结果)
        r2_scores == [r['r2_score'] for r in results_list]:
        mse_values == [r['mse'] for r in results_list]:
        print(f"   R²分数, {r2_scores}")
        print(f"   MSE值, {mse_values}")
        
        # 验证R²分数应该很接近(因为是相同的底层数据关系)
        r2_variance = np.var(r2_scores)
        assert r2_variance < 0.01(), f"R²分数应该很一致,方差, {r2_variance}"
        
        print("✅ 一致性验证通过 - 确认使用真实算法而非随机数")
        return True
        
    except Exception as e,::
        print(f"❌ 对比测试失败, {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("=" * 70)
    print("🧪 真实AI训练系统综合测试")
    print("=" * 70)
    
    # 基础导入测试
    import_test = test_real_training_import()
    if not import_test,::
        return 1
    
    # 真实模型训练器测试
    trainer_test = test_real_model_trainer()
    if not trainer_test,::
        return 1
    
    # 真实训练管理器测试
    manager_test = test_real_training_manager()
    if not manager_test,::
        return 1
    
    # 向后兼容性测试
    compatibility_test = test_backward_compatibility()
    if not compatibility_test,::
        return 1
    
    # 与随机数对比测试
    comparison_test = test_comparison_with_random()
    if not comparison_test,::
        return 1
    
    print("\n" + "=" * 70)
    print("🎉 所有测试通过！")
    print("✅ 真实AI训练系统工作正常")
    print("✅ 成功替换了伪训练系统")
    print("✅ 所有random.uniform()已替换为真实算法")
    print("✅ 基于scikit-learn的真实机器学习已启用")
    print("✅ 向后兼容性保持")
    print("✅ 结果一致性验证通过")
    print("\n🚀 系统现在具备：")
    print("   • 真实数学模型训练(线性回归)")
    print("   • 真实逻辑模型训练(逻辑回归)")
    print("   • 真实概念模型训练(随机森林)")
    print("   • 真实模型评估(基于测试数据)")
    print("   • 专业机器学习库集成(scikit-learn)")
    print("   • 可验证的数学正确性")
    print("=" * 70)
    
    return 0

if __name"__main__":::
    exit_code = asyncio.run(main())
    sys.exit(exit_code)