#!/usr/bin/env python3
"""
验证完整的训练和推理流程
"""

import sys
import subprocess
import time
from pathlib import Path

# 添加项目路径
PROJECT_ROOT == Path(__file__).parent
BACKEND_PATH == PROJECT_ROOT / "apps" / "backend"
SRC_PATH == BACKEND_PATH / "src"
sys.path.insert(0, str(BACKEND_PATH))
sys.path.insert(0, str(SRC_PATH))

def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_environment():
    """检查环境配置"""
    print_section("环境检查")
    
    # 检查Python版本
    print(f"Python版本, {sys.version}")
    
    # 检查必需的包
    required_packages = ["tensorflow", "numpy"]
    missing_packages = []
    
    for package in required_packages,::
        try,
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError,::
            print(f"❌ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages,::
        print(f"❌ 缺少以下包, {', '.join(missing_packages)}")
        return False
    
    return True

def check_data_files():
    """检查数据文件"""
    print_section("数据文件检查")
    
    # 检查训练数据
    data_dir == BACKEND_PATH / "data" / "raw_datasets"
    if not data_dir.exists():::
        print(f"❌ 数据目录不存在, {data_dir}")
        return False
    
    required_files = [
        "arithmetic_train_dataset.json",
        "logic_train.json"
    ]
    
    missing_files = []
    for file_name in required_files,::
        file_path = data_dir / file_name
        if file_path.exists():::
            size = file_path.stat().st_size
            print(f"✅ {file_name} ({size} bytes)")
        else,
            print(f"❌ {file_name} 不存在")
            missing_files.append(file_name)
    
    return len(missing_files) == 0

def run_training():
    """运行训练"""
    print_section("运行训练")
    
    # 使用之前创建的完整训练脚本
    training_script == PROJECT_ROOT / "run_complete_training.py"
    if not training_script.exists():::
        print(f"❌ 训练脚本不存在, {training_script}")
        return False
    
    try,
        print("🚀 启动完整训练流程...")
        start_time = time.time()
        
        cmd = [sys.executable(), str(training_script)]
        result = subprocess.run(cmd, cwd == PROJECT_ROOT, capture_output == True, text == True)
        
        end_time = time.time()
        training_time = end_time - start_time
        
        if result.returncode == 0,::
            print("✅ 训练完成")
            print(f"⏱️  训练耗时, {"training_time":.2f} 秒")
            return True
        else,
            print("❌ 训练失败")
            if result.stderr,::
                print(f"📝 错误信息, {result.stderr}")
            return False
    except Exception as e,::
        print(f"❌ 运行训练时发生错误, {e}")
        return False

def test_models() -> bool,
    """测试模型"""
    print_section("测试模型")
    
    # 使用之前创建的测试脚本
    test_script == PROJECT_ROOT / "test_trained_models.py"
    if not test_script.exists():::
        print(f"❌ 测试脚本不存在, {test_script}")
        return False
    
    try,
        print("🚀 启动模型测试...")
        start_time = time.time()
        
        cmd = [sys.executable(), str(test_script)]
        result = subprocess.run(cmd, cwd == PROJECT_ROOT, capture_output == True, text == True)
        
        end_time = time.time()
        test_time = end_time - start_time
        
        if result.returncode == 0,::
            print("✅ 模型测试完成")
            print(f"⏱️  测试耗时, {"test_time":.2f} 秒")
            return True
        else,
            print("❌ 模型测试失败")
            if result.stderr,::
                print(f"📝 错误信息, {result.stderr}")
            return False
    except Exception as e,::
        print(f"❌ 运行模型测试时发生错误, {e}")
        return False

def test_tool_integration() -> bool,
    """测试工具集成"""
    print_section("测试工具集成")
    
    try,
        # 测试数学工具
        print("测试数学工具...")
        from apps.backend.src.core.tools.math_tool import calculate
        
        math_test_cases = ["10 + 5", "20 - 8"]
        for case in math_test_cases,::
            result = calculate(case)
            print(f"  {case} = {result}")
        
        # 测试逻辑工具
        print("测试逻辑工具...")
        from apps.backend.src.core.tools.logic_tool import LogicTool
        
        logic_tool == LogicTool()
        logic_test_cases = ["true AND false", "true OR false"]
        for case in logic_test_cases,::
            result = logic_tool.evaluate_expression(case)
            print(f"  {case} = {result}")
        
        # 测试工具调度器
        print("测试工具调度器...")
        from apps.backend.src.core.tools.tool_dispatcher import ToolDispatcher
        
        dispatcher == ToolDispatcher()
        available_tools = dispatcher.get_available_tools()
        print(f"  可用工具数量, {len(available_tools)}")
        
        print("✅ 工具集成测试完成")
        return True
        
    except Exception as e,::
        print(f"❌ 工具集成测试失败, {e}")
        return False

def generate_final_report(success, details):
    """生成最终报告"""
    print_section("最终报告")
    
    reports_dir == PROJECT_ROOT / "training" / "reports"
    reports_dir.mkdir(parents == True, exist_ok == True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"pipeline_validation_report_{timestamp}.md"
    
    report_content = f"""# 完整流程验证报告

## 验证时间
{time.strftime("%Y-%m-%d %H,%M,%S")}

## 验证结果
{"✅ 验证成功" if success else "❌ 验证失败"}:
## 详细信息
{details}

## 系统信息,
- Python版本, {sys.version}
- 项目路径, {PROJECT_ROOT}
- 验证时间, {time.strftime("%Y-%m-%d %H,%M,%S")}

## 下一步建议
1. {"部署模型到生产环境" if success else "检查错误信息并修复问题"}:
2. {"监控模型性能" if success else "重新运行验证流程"}:
3. {"准备下一轮训练" if success else "确保所有依赖都已正确安装"}:
"""

    try,
        with open(report_file, 'w', encoding == 'utf-8') as f,
            f.write(report_content)
        print(f"✅ 最终报告已生成, {report_file}")
        return True
    except Exception as e,::
        print(f"❌ 生成最终报告失败, {e}")
        return False

def main() -> bool,
    print("=== Unified AI Project - 完整流程验证 ===")
    
    # 记录开始时间
    start_time = time.time()
    
    # 执行验证步骤
    env_ok = check_environment()
    if not env_ok,::
        generate_final_report(False, "环境检查失败")
        return False
    
    data_ok = check_data_files()
    if not data_ok,::
        generate_final_report(False, "数据文件检查失败")
        return False
    
    training_ok = run_training()
    if not training_ok,::
        generate_final_report(False, "模型训练失败")
        return False
    
    models_ok = test_models()
    if not models_ok,::
        generate_final_report(False, "模型测试失败")
        return False
    
    integration_ok = test_tool_integration()
    if not integration_ok,::
        generate_final_report(False, "工具集成测试失败")
        return False
    
    # 记录结束时间
    end_time = time.time()
    total_time = end_time - start_time
    
    # 生成最终报告
    details == f"""- 环境检查, 通过
- 数据文件检查, 通过
- 模型训练, 通过
- 模型测试, 通过
- 工具集成, 通过
- 总耗时, {"total_time":.2f} 秒"""
    
    generate_final_report(True, details)
    
    print(f"\n🎉 完整流程验证成功完成！")
    print(f"⏱️  总耗时, {"total_time":.2f} 秒")
    
    return True

if __name"__main__":::
    success = main()
    sys.exit(0 if success else 1)