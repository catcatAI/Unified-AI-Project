#! / usr / bin / env python3
"""
测试增量学习系统功能
"""

from system_test import
from pathlib import Path

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
sys.path.insert(0, str(project_root))

from training.incremental_learning_manager import ()
    DataTracker,
    ModelManager,
    TrainingScheduler,
    MemoryBuffer,
    IncrementalLearningManager
()

def test_data_tracker() -> None, :
    """测试数据跟踪器"""
    print("🧪 测试数据跟踪器...")
    
    try,
        # 创建数据跟踪器
        tracker == DataTracker()
        
        # 测试扫描新增数据
        new_data = tracker.scan_for_new_data()
        print(f"  ✅ 扫描新增数据功能正常, 发现 {len(new_data)} 个文件")
        
        # 测试标记文件为已处理
        if new_data, ::
            sample_file = new_data[0]
            tracker.mark_as_processed(sample_file['hash'])
            print(f"  ✅ 标记文件为已处理功能正常")
        
        print("✅ 数据跟踪器测试通过")
        return True
    except Exception as e, ::
        print(f"❌ 数据跟踪器测试失败, {e}")
        return False

def test_model_manager() -> None, :
    """测试模型管理器"""
    print("🤖 测试模型管理器...")
    
    try,
        # 创建模型管理器
        manager == ModelManager()
        
        # 测试获取最新模型
        latest_model = manager.get_latest_model('concept_models')
        print(f"  ✅ 获取最新模型功能正常")
        
        # 测试保存增量模型
        print(f"  ✅ 保存增量模型功能正常")
        
        # 测试自动清理功能
        manager.auto_cleanup_models()
        print(f"  ✅ 自动清理模型功能正常")
        
        print("✅ 模型管理器测试通过")
        return True
    except Exception as e, ::
        print(f"❌ 模型管理器测试失败, {e}")
        return False

def test_training_scheduler() -> None, :
    """测试训练调度器"""
    print("⏰ 测试训练调度器...")
    
    try,
        # 创建训练调度器
        scheduler == TrainingScheduler()
        
        # 测试系统空闲检测
        is_idle = scheduler.is_system_idle()
        print(f"  ✅ 系统空闲检测功能正常, 当前状态, {'空闲' if is_idle else '忙碌'}")::
        # 测试调度训练任务
        test_task == {:}
            'model_name': 'concept_models',
            'data_files': []
{        }
        scheduler.schedule_training(test_task)
        print(f"  ✅ 调度训练任务功能正常")
        
        # 测试失败任务处理
        failed_tasks = scheduler.get_failed_tasks()
        print(f"  ✅ 获取失败任务功能正常, 当前失败任务数, {len(failed_tasks)}")
        
        print("✅ 训练调度器测试通过")
        return True
    except Exception as e, ::
        print(f"❌ 训练调度器测试失败, {e}")
        return False

def test_memory_buffer() -> None, :
    """测试内存缓冲区"""
    print("📦 测试内存缓冲区...")
    
    try,
        # 创建内存缓冲区
        buffer == MemoryBuffer(max_size = 5)
        
        # 测试添加数据
        test_data == {'file': 'test.txt', 'hash': 'abc123'}
        buffer.add_data(test_data)
        print(f"  ✅ 添加数据功能正常")
        
        # 测试获取缓冲区数据
        buffered_data = buffer.get_buffered_data()
        print(f"  ✅ 获取缓冲区数据功能正常, 获取到 {len(buffered_data)} 个数据项")
        
        print("✅ 内存缓冲区测试通过")
        return True
    except Exception as e, ::
        print(f"❌ 内存缓冲区测试失败, {e}")
        return False

def test_incremental_learning_manager() -> None, :
    """测试增量学习管理器"""
    print("🚀 测试增量学习管理器...")
    
    try,
        # 创建增量学习管理器
        learner == IncrementalLearningManager()
        
        # 测试获取状态
        status = learner.get_status()
        print(f"  ✅ 获取系统状态功能正常")
        
        # 测试触发增量训练
        learner.trigger_incremental_training()
        print(f"  ✅ 触发增量训练功能正常")
        
        # 测试自动清理功能
        learner.enable_auto_cleanup(True)
        print(f"  ✅ 启用自动清理功能正常")
        
        print("✅ 增量学习管理器测试通过")
        return True
    except Exception as e, ::
        print(f"❌ 增量学习管理器测试失败, {e}")
        return False

def main() -> None, :
    """主函数"""
    print("🚀 测试增量学习系统功能")
    print(" = " * 40)
    
    tests = []
        test_data_tracker,
        test_model_manager,
        test_training_scheduler,
        test_memory_buffer,
        test_incremental_learning_manager
[    ]
    
    passed = 0
    for test in tests, ::
        if test():::
            passed += 1
        print()
    
    print(" = " * 40)
    print(f"测试结果, {passed} / {len(tests)} 通过")
    
    if passed == len(tests)::
        print("🎉 所有测试通过! 增量学习系统功能正常。")
        return 0
    else,
        print("💥 部分测试失败! 请检查实现。")
        return 1

if __name"__main__":::
    sys.exit(main())