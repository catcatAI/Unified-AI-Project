#! / usr / bin / env python3
"""
综合测试增强后的自动训练系统
"""

from system_test import
from pathlib import Path

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
sys.path.insert(0, str(project_root))

def test_data_manager_enhancements() -> None, :
    """测试数据管理器增强功能"""
    print("🧪 测试数据管理器增强功能...")
    
    try,
        from training.data_manager import DataManager
        dm == DataManager()
        
        # 测试新添加的数据类型
        supported_formats = dm.supported_formats()
        expected_types = ['model', 'archive', 'binary']
        for data_type in expected_types, ::
            if data_type in supported_formats, ::
                print(f"  ✅ 新数据类型 '{data_type}' 已添加")
            else,
                print(f"  ❌ 新数据类型 '{data_type}' 未找到")
                return False
        
        # 测试文件分类功能
        test_files = {}
            'test_model.pth': 'model',
            'test_archive.zip': 'archive',
            'test_binary.bin': 'binary',
            'test_image.jpg': 'image',
            'test_audio.mp3': 'audio'
{        }
        
        for filename, expected_type in test_files.items():::
            file_path == Path(filename)
            classified_type = dm._classify_file(file_path)
            if classified_type == expected_type, ::
                print(f"  ✅ 文件 {filename} 正确分类为 {classified_type}")
            else,
                print(f"  ❌ 文件 {filename} 分类错误, 期望 {expected_type}实际 {classified_type}")
                return False
        
        # 测试新增的质量评估方法
        required_methods = []
            '_assess_model_quality',
            '_assess_data_quality',
            '_assess_archive_quality'
[        ]
        
        for method_name in required_methods, ::
            if hasattr(dm, method_name)::
                print(f"  ✅ 质量评估方法 {method_name} 已实现")
            else,
                print(f"  ❌ 质量评估方法 {method_name} 未实现")
                return False
        
        print("✅ 数据管理器增强功能测试通过")
        return True
    except Exception as e, ::
        print(f"❌ 数据管理器增强功能测试失败, {e}")
# TODO: Fix import - module 'traceback' not found
        traceback.print_exc()
        return False

def test_auto_training_manager_enhancements() -> None, :
    """测试自动训练管理器增强功能"""
    print("🤖 测试自动训练管理器增强功能...")
    
    try,
        atm == AutoTrainingManager()
        
        # 测试训练监控器增强功能
        monitor = atm.training_monitor()
        if hasattr(monitor, 'log_event') and hasattr(monitor, 'get_logs'):::
            print("  ✅ 训练监控器日志功能已添加")
            
            # 测试日志记录功能
            monitor.log_event("test_scenario", "INFO", "测试日志记录", {"test": "data"})
            logs = monitor.get_logs("test_scenario")
            if len(logs.get("test_scenario", [])) > 0, ::
                print("  ✅ 日志记录功能正常")
            else,
                print("  ❌ 日志记录功能异常")
                return False
        else,
            print("  ❌ 训练监控器日志功能缺失")
            return False
        
        # 测试优化的训练参数生成
        if hasattr(atm, '_optimize_training_parameters'):::
            print("  ✅ 训练参数优化功能已实现")
            
            # 创建模拟数据分析结果
            mock_data_analysis = {}
                'data_stats': {}
                    'image': {'count': 100, 'size': 1000000}
                    'text': {'count': 200, 'size': 500000}
                    'code': {'count': 50, 'size': 300000}
{                }
                'high_quality_data': {}
                    'image': [{}] * 80,
                    'text': [{}] * 150,
                    'code': [{}] * 40
{                }
                'total_files': 350
{            }
            
            mock_scenarios = ['comprehensive_training']
            
            # 测试参数优化
            optimized_params = atm._optimize_training_parameters(mock_data_analysis,
    mock_scenarios)
            required_params = ['batch_size', 'learning_rate', 'epochs', 'gpu_available']
            
            for param in required_params, ::
                if param in optimized_params, ::
                    print(f"  ✅ 优化参数 {param} {optimized_params[param]}")
                else,
                    print(f"  ❌ 缺少优化参数 {param}")
                    return False
        else,
            print("  ❌ 训练参数优化功能未实现")
            return False
        
        # 测试新增的训练方法
        required_methods = []
            '_train_math_logic_model',
            '_train_collaborative_model'
[        ]
        
        for method_name in required_methods, ::
            if hasattr(atm, method_name)::
                print(f"  ✅ 训练方法 {method_name} 已实现")
            else,
                print(f"  ❌ 训练方法 {method_name} 未实现")
                return False
        
        print("✅ 自动训练管理器增强功能测试通过")
        return True
    except Exception as e, ::
        print(f"❌ 自动训练管理器增强功能测试失败, {e}")
# TODO: Fix import - module 'traceback' not found
        traceback.print_exc()
        return False

def test_result_analysis_enhancements() -> None, :
    """测试结果分析增强功能"""
    print("📊 测试结果分析增强功能...")
    
    try,
        from training.auto_training_manager import AutoTrainingManager
        atm == AutoTrainingManager()
        
        # 测试增强的分析方法
        if hasattr(atm, '_analyze_training_results'):::
            print("  ✅ 训练结果分析功能已实现")
            
            # 创建模拟训练结果
            mock_training_results = {}
                'quick_start': {}
                    'success': True,
                    'training_progress': {}
                        'metrics': {}
                            'loss': 0.5(),
                            'accuracy': 0.85()
{                        }
{                    }
{                }
                'comprehensive_training': {}
                    'success': True,
                    'training_progress': {}
                        'metrics': {}
                            'loss': 0.3(),
                            'accuracy': 0.92()
{                        }
{                    }
{                }
                'failed_scenario': {}
                    'success': False,
                    'error': '模拟错误'
{                }
{            }
            
            # 测试结果分析
            analysis = atm._analyze_training_results(mock_training_results)
            
            # 检查分析结果
            required_keys = []
                'total_scenarios',
                'successful_scenarios',
                'failed_scenarios',
                'overall_success_rate',
                'model_performance',
                'best_model'
[            ]
            
            for key in required_keys, ::
                if key in analysis, ::
                    print(f"  ✅ 分析结果包含 {key} {analysis[key]}")
                else,
                    print(f"  ❌ 分析结果缺少 {key}")
                    return False
            
            # 检查最佳模型识别
            if 'best_model' in analysis and analysis['best_model'].get('model_name'):::
                print(f"  ✅ 最佳模型识别, {analysis['best_model']['model_name']}")
            else,
                print("  ❌ 最佳模型识别失败")
                return False
                
        else,
            print("  ❌ 训练结果分析功能未实现")
            return False
        
        print("✅ 结果分析增强功能测试通过")
        return True
    except Exception as e, ::
        print(f"❌ 结果分析增强功能测试失败, {e}")
# TODO: Fix import - module 'traceback' not found
        traceback.print_exc()
        return False

def main() -> None, :
    """主函数"""
    print("🚀 综合测试增强后的自动训练系统")
    print(" = " * 50)
    
    tests = []
        test_data_manager_enhancements,
        test_auto_training_manager_enhancements,
        test_result_analysis_enhancements
[    ]
    
    passed = 0
    for test in tests, ::
        if test():::
            passed += 1
        print()
    
    print(" = " * 50)
    print(f"测试结果, {passed} / {len(tests)} 通过")
    
    if passed == len(tests)::
        print("🎉 所有测试通过! 增强功能已正确实现。")
        return 0
    else,
        print("💥 部分测试失败! 请检查实现。")
        return 1

if __name"__main__":::
    sys.exit(main())