#!/usr/bin/env python3
"""
硬件兼容性测试脚本
用于测试项目在不同硬件配置下的运行效果，包括核显支持
"""

import sys
import logging
from pathlib import Path
import json
from datetime import datetime

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
        _ = logging.FileHandler(project_root / 'hardware_compatibility_test.log'),
        _ = logging.StreamHandler()
    ]
)
logger: Any = logging.getLogger(__name__)

def test_hardware_detection() -> None:
    """测试硬件检测功能"""
    logger.info("=== 测试硬件检测功能 ===")
    
    try:
        # 直接导入而不是通过apps.backend.src.system
            HardwareProbe,
            get_hardware_profile
        )
        
        # 检测硬件
        probe = HardwareProbe()
        profile = probe.detect_all()
        
        _ = logger.info(f"硬件检测结果:")
        _ = logger.info(f"  平台: {profile.platform} {profile.os_version}")
        _ = logger.info(f"  性能等级: {profile.performance_tier}")
        _ = logger.info(f"  AI能力评分: {profile.ai_capability_score:.1f}/100")
        _ = logger.info(f"  CPU: {profile.cpu.brand} ({profile.cpu.cores_logical}逻辑核心)")
        _ = logger.info(f"  内存: {profile.memory.total} MB 总计, {profile.memory.available} MB 可用")
        _ = logger.info(f"  存储: {profile.storage.total} GB {profile.storage.disk_type}")
        
        if profile.gpu:
            for i, gpu in enumerate(profile.gpu):
                _ = logger.info(f"  GPU {i}: {gpu.name} ({gpu.memory_total} MB)")
                # 检查是否为集成显卡
                integrated_keywords = ['intel', 'amd', 'radeon', 'hd graphics', 'uhd graphics', 'integrated']
                is_integrated = any(keyword in gpu.name.lower() for keyword in integrated_keywords)
                _ = logger.info(f"    集成显卡: {is_integrated}")
        
        # 保存硬件配置文件
        _ = probe.save_profile(profile)
        _ = logger.info("✅ 硬件检测测试通过")
        return profile
    except Exception as e:
        _ = logger.error(f"❌ 硬件检测测试失败: {e}")
        import traceback
        _ = logger.error(f"详细错误信息: {traceback.format_exc()}")
        return None

def test_integrated_graphics_optimization(profile) -> None:
    """测试集成显卡优化功能"""
    logger.info("=== 测试集成显卡优化功能 ===")
    
    if not profile:
        _ = logger.warning("跳过集成显卡优化测试，没有硬件配置文件")
        return False
    
    try:
        # 直接导入而不是通过apps.backend.src.system
        from apps.backend.src.system.integrated_graphics_optimizer import (
            IntegratedGraphicsOptimizer
        )
        
        # 创建集成显卡优化器
        optimizer = IntegratedGraphicsOptimizer(profile)
        
        # 检查是否为集成显卡系统
        is_ig_system = optimizer.is_integrated_graphics_system()
        _ = logger.info(f"集成显卡系统: {is_ig_system}")
        
        if is_ig_system:
            # 获取优化建议
            recommendations = optimizer.get_optimization_recommendations()
            logger.info(f"优化建议: {json.dumps(recommendations, ensure_ascii=False, indent=2)}")
            
            # 应用所有优化
            optimization_results = optimizer.apply_all_optimizations()
            logger.info(f"优化结果: {json.dumps(optimization_results, ensure_ascii=False, indent=2)}")
            
            # 测试批处理大小调整
            original_batch_size = 32
            adjusted_batch_size = optimizer.adjust_batch_size_for_integrated_graphics(original_batch_size)
            _ = logger.info(f"批处理大小调整: {original_batch_size} -> {adjusted_batch_size}")
            
            # 测试精度调整
            precision_config = optimizer.enable_precision_adjustment()
            _ = logger.info(f"精度配置: {precision_config}")
            
            # 测试CPU-GPU协调
            coordination_config = optimizer.coordinate_cpu_gpu_usage()
            _ = logger.info(f"CPU-GPU协调配置: {coordination_config}")
            
            # 测试模型压缩
            compression_config = optimizer.apply_model_compression()
            _ = logger.info(f"模型压缩配置: {compression_config}")
        
        _ = logger.info("✅ 集成显卡优化测试通过")
        return True
    except Exception as e:
        _ = logger.error(f"❌ 集成显卡优化测试失败: {e}")
        import traceback
        _ = logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

def test_simple_integrated_graphics_check() -> None:
    """简单的集成显卡检查测试"""
    logger.info("=== 简单集成显卡检查测试 ===")
    
    try:
        import platform
        system = platform.system().lower()
        
        if system == "windows":
            import subprocess
            import json
            
            result = subprocess.run([
                "powershell.exe", 
                "Get-WmiObject -Class Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Json"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                gpu_data = json.loads(result.stdout)
                
                # Handle both single GPU and multiple GPU cases
                if isinstance(gpu_data, list):
                    gpu_list = gpu_data
                else:
                    gpu_list = [gpu_data]
                
                # Check if any GPU is integrated graphics
                integrated_graphics_found = False
                for gpu_info in gpu_list:
                    name = gpu_info.get('Name', '').lower()
                    if any(keyword in name for keyword in ['intel', 'amd', 'radeon', 'hd graphics', 'uhd graphics']):
                        _ = logger.info(f"检测到集成显卡: {gpu_info.get('Name')}")
                        integrated_graphics_found = True
                
                if integrated_graphics_found:
                    _ = logger.info("✅ 简单集成显卡检查测试通过")
                    return True
                else:
                    _ = logger.info("未检测到集成显卡")
                    return False
            else:
                _ = logger.warning("无法获取GPU信息")
                return False
        else:
            _ = logger.info("非Windows系统，跳过集成显卡检查")
            return True
            
    except Exception as e:
        _ = logger.error(f"❌ 简单集成显卡检查测试失败: {e}")
        return False

def main() -> None:
    """主测试函数"""
    _ = logger.info("开始硬件兼容性测试")
    start_time = datetime.now()
    
    # 运行测试
    results = []
    
    # 测试简单集成显卡检查
    simple_check_result = test_simple_integrated_graphics_check()
    _ = results.append(("简单集成显卡检查", simple_check_result))
    
    # 如果简单检查通过，再测试完整功能
    if simple_check_result:
        # 测试硬件检测
        hardware_profile = test_hardware_detection()
        _ = results.append(("硬件检测", hardware_profile is not None))
        
        # 测试集成显卡优化
        if hardware_profile:
            ig_optimization_result = test_integrated_graphics_optimization(hardware_profile)
            _ = results.append(("集成显卡优化", ig_optimization_result))
    
    # 输出测试结果摘要
    logger.info("=== 测试结果摘要 ===")
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        _ = logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info(f"=== 测试完成 ===")
    _ = logger.info(f"总测试数: {len(results)}")
    _ = logger.info(f"通过: {passed}")
    _ = logger.info(f"失败: {failed}")
    _ = logger.info(f"测试耗时: {duration}")
    
    if failed == 0:
        _ = logger.info("🎉 所有测试通过！项目在当前硬件配置下运行正常。")
        return 0
    else:
        _ = logger.error(f"⚠️  {failed} 个测试失败，请检查相关功能。")
        return 1

if __name__ == "__main__":
    _ = sys.exit(main())