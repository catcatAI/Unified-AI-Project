#!/usr/bin/env python3
"""
快速硬件测试脚本
用于验证集成显卡支持和硬件兼容性改进
"""

import sys
import logging
from pathlib import Path
import json
import platform
import psutil

# 添加项目路径
project_root: str = Path(__file__).parent.parent
backend_path: str = project_root / "apps" / "backend"
_ = sys.path.insert(0, str(project_root))
_ = sys.path.insert(0, str(backend_path))
_ = sys.path.insert(0, str(backend_path / "src"))

# 配置日志
logging.basicConfig(
    level: str=logging.INFO,
    format: str='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        _ = logging.StreamHandler()
    ]
)
logger: Any = logging.getLogger(__name__)

def test_system_info() -> None:
    """测试系统基本信息"""
    logger.info("=== 系统基本信息 ===")
    
    # CPU信息
    logger.info(f"CPU核心数: {psutil.cpu_count()} (逻辑), {psutil.cpu_count(logical=False)} (物理)")
    
    # 内存信息
    memory = psutil.virtual_memory()
    _ = logger.info(f"总内存: {memory.total / (1024**3):.2f} GB")
    _ = logger.info(f"可用内存: {memory.available / (1024**3):.2f} GB")
    
    # 系统信息
    _ = logger.info(f"操作系统: {platform.system()} {platform.release()}")
    _ = logger.info(f"架构: {platform.machine()}")
    
    return True

def test_integrated_graphics_detection() -> None:
    """测试集成显卡检测"""
    logger.info("=== 集成显卡检测 ===")
    
    try:
        system = platform.system().lower()
        
        if system == "windows":
            _ = logger.info("Windows系统，尝试检测集成显卡...")
            
            # 使用更简单的命令
            import subprocess
            
            # 先测试是否有nvidia gpu
            try:
                result = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    _ = logger.info("检测到NVIDIA GPU:")
                    for line in result.stdout.strip().split('\n'):
                        _ = logger.info(f"  NVIDIA: {line.strip()}")
            except:
                _ = logger.info("未检测到NVIDIA GPU或nvidia-smi不可用")
            
            # 检测所有显卡
            try:
                result = subprocess.run([
                    "wmic", "path", "win32_VideoController", "get", "name"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    # 过滤掉空行和标题行
                    gpu_names = [line.strip() for line in lines if line.strip() and not line.startswith('Name')]
                    
                    _ = logger.info(f"检测到 {len(gpu_names)} 个GPU:")
                    for gpu_name in gpu_names:
                        _ = logger.info(f"  GPU: {gpu_name}")
                        
                        # 检查是否为集成显卡
                        integrated_keywords = ['intel', 'amd', 'radeon', 'hd graphics', 'uhd graphics', 'integrated']
                        is_integrated = any(keyword in gpu_name.lower() for keyword in integrated_keywords)
                        if is_integrated:
                            _ = logger.info(f"    -> 集成显卡: 是")
                        else:
                            _ = logger.info(f"    -> 集成显卡: 否")
                else:
                    _ = logger.warning("无法通过wmic获取GPU信息")
            except Exception as e:
                _ = logger.error(f"检测GPU时出错: {e}")
        else:
            _ = logger.info(f"非Windows系统 ({system})，跳过集成显卡检测")
            
        return True
    except Exception as e:
        _ = logger.error(f"集成显卡检测失败: {e}")
        return False

def test_imports() -> None:
    """测试关键模块导入"""
    logger.info("=== 模块导入测试 ===")
    
    modules_to_test = [
        _ = ("硬件探测模块", "apps.backend.src.system.hardware_probe"),
        _ = ("集成显卡优化器", "apps.backend.src.system.integrated_graphics_optimizer"),
        _ = ("部署管理器", "apps.backend.src.system.deployment_manager"),
        _ = ("训练模型", "training.train_model"),
        _ = ("GPU优化器", "training.gpu_optimizer"),
        _ = ("资源管理器", "training.resource_manager"),
        _ = ("智能资源分配器", "training.smart_resource_allocator")
    ]
    
    results = []
    for name, module in modules_to_test:
        try:
            __import__(module)
            _ = logger.info(f"  {name}: ✅ 导入成功")
            _ = results.append(True)
        except ImportError as e:
            _ = logger.warning(f"  {name}: ❌ 导入失败 - {e}")
            _ = results.append(False)
        except Exception as e:
            _ = logger.error(f"  {name}: ❌ 导入出错 - {e}")
            _ = results.append(False)
    
    return all(results) if results else False

def test_integrated_graphics_optimizer() -> None:
    """测试集成显卡优化器功能"""
    logger.info("=== 集成显卡优化器测试 ===")
    
    try:
        # 测试导入
        from apps.backend.src.system.integrated_graphics_optimizer import (
            IntegratedGraphicsOptimizer
        )
        _ = logger.info("集成显卡优化器导入成功")
        
        # 创建一个模拟的硬件配置文件（集成显卡）
        from apps.backend.src.system.hardware_probe import (
            HardwareProfile, CPUInfo, GPUInfo, MemoryInfo, StorageInfo, NetworkInfo
        )
        
        # 模拟集成显卡硬件配置
        gpu_info = [GPUInfo(
            name="Intel HD Graphics 620",
            memory_total=1024,  # 1GB
            memory_available=512,
            driver_version="Unknown",
            cuda_version=None,
            opencl_support=True,
            vulkan_support=True
        )]
        
        cpu_info = CPUInfo(
            cores_physical=2,
            cores_logical=4,
            frequency_max=2400.0,
            frequency_current=2000.0,
            architecture="x86_64",
            brand="Intel Core i5-7200U",
            usage_percent=25.0
        )
        
        memory_info = MemoryInfo(
            total=8192,  # 8GB
            available=4096,
            used=4096,
            usage_percent=50.0
        )
        
        storage_info = StorageInfo(
            total=256,
            available=128,
            used=128,
            disk_type="SSD"
        )
        
        network_info = NetworkInfo(
            bandwidth_download=50.0,
            bandwidth_upload=25.0,
            latency=30.0,
            connection_type="WiFi"
        )
        
        hardware_profile = HardwareProfile(
            cpu=cpu_info,
            gpu=gpu_info,
            memory=memory_info,
            storage=storage_info,
            network=network_info,
            platform="windows",
            os_version="10.0.19042",
            performance_tier="Low",
            ai_capability_score=35.0
        )
        
        # 测试优化器
        optimizer = IntegratedGraphicsOptimizer(hardware_profile)
        
        _ = logger.info(f"是否为集成显卡系统: {optimizer.is_integrated_graphics_system()}")
        
        recommendations = optimizer.get_optimization_recommendations()
        logger.info(f"优化建议: {json.dumps(recommendations, ensure_ascii=False, indent=2)}")
        
        batch_size = optimizer.adjust_batch_size_for_integrated_graphics(32)
        _ = logger.info(f"调整后的批处理大小: {batch_size}")
        
        precision_config = optimizer.enable_precision_adjustment()
        _ = logger.info(f"精度配置: {precision_config}")
        
        coordination_config = optimizer.coordinate_cpu_gpu_usage()
        _ = logger.info(f"CPU-GPU协调配置: {coordination_config}")
        
        compression_config = optimizer.apply_model_compression()
        _ = logger.info(f"模型压缩配置: {compression_config}")
        
        all_results = optimizer.apply_all_optimizations()
        _ = logger.info("所有优化测试通过")
        
        return True
    except Exception as e:
        _ = logger.error(f"集成显卡优化器测试失败: {e}")
        import traceback
        _ = logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

def main() -> None:
    """主测试函数"""
    _ = logger.info("开始快速硬件兼容性测试")
    
    # 运行所有测试
    tests = [
        _ = ("系统信息", test_system_info),
        _ = ("集成显卡检测", test_integrated_graphics_detection),
        _ = ("模块导入", test_imports),
        _ = ("集成显卡优化器", test_integrated_graphics_optimizer)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            _ = logger.info(f"\n--- 运行 {test_name} 测试 ---")
            result = test_func()
            _ = results.append((test_name, result))
        except Exception as e:
            _ = logger.error(f"{test_name} 测试出错: {e}")
            _ = results.append((test_name, False))
    
    # 输出测试结果摘要
    logger.info("\n=== 测试结果摘要 ===")
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        _ = logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info(f"\n=== 测试完成 ===")
    _ = logger.info(f"总测试数: {len(results)}")
    _ = logger.info(f"通过: {passed}")
    _ = logger.info(f"失败: {failed}")
    
    if failed == 0:
        _ = logger.info("\n🎉 所有测试通过！硬件兼容性改进已正确实现。")
        return 0
    else:
        _ = logger.error(f"\n⚠️  {failed} 个测试失败，请检查相关功能。")
        return 1

if __name__ == "__main__":
    _ = sys.exit(main())