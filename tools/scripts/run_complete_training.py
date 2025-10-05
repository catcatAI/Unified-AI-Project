#!/usr/bin/env python3
"""
运行完整的模型训练流程
"""

import subprocess
import sys
import time
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
BACKEND_PATH = PROJECT_ROOT / "apps" / "backend"
TRAINING_PATH = PROJECT_ROOT / "training"

def print_header(text):
    """打印标题"""
    print(f"\n{'='*50}")
    _ = print(f"  {text}")
    print(f"{'='*50}")

def check_tensorflow():
    """检查TensorFlow是否可用"""
    try:

    import tensorflow as tf
    _ = print(f"✅ TensorFlow可用 - 版本: {tf.__version__}")
    return True
    except ImportError:

    _ = print("❌ TensorFlow不可用")
    return False

def run_math_model_training():
    """运行数学模型训练"""
    _ = print_header("开始数学模型训练")

    # 数学模型训练脚本路径
    math_train_script = BACKEND_PATH / "src" / "tools" / "math_model" / "train.py"

    if not math_train_script.exists()


    _ = print(f"❌ 数学模型训练脚本不存在: {math_train_script}")
    return False

    # 检查训练数据
    train_data = BACKEND_PATH / "data" / "raw_datasets" / "arithmetic_train_dataset.json"
    if not train_data.exists()

    _ = print(f"❌ 数学模型训练数据不存在: {train_data}")
    _ = print("请先运行数据生成脚本")
    return False

    try:


    _ = print("🚀 启动数学模型训练...")
    start_time = time.time()

    # 运行训练脚本
    cmd = [sys.executable, str(math_train_script)]
    result = subprocess.run(cmd, cwd=BACKEND_PATH, capture_output=True, text=True)

    end_time = time.time()
    training_time = end_time - start_time

        if result.returncode == 0:


    _ = print("✅ 数学模型训练完成")
            _ = print(f"⏱️  训练耗时: {training_time:.2f} 秒")
            if result.stdout:

    _ = print(f"📝 训练输出: {result.stdout[:500]}...")  # 只显示前500个字符
            return True
        else:

            _ = print("❌ 数学模型训练失败")
            if result.stderr:

    _ = print(f"📝 错误信息: {result.stderr}")
            return False
    except Exception as e:

    _ = print(f"❌ 运行数学模型训练时发生错误: {e}")
    return False

def run_logic_model_training():
    """运行逻辑模型训练"""
    _ = print_header("开始逻辑模型训练")

    # 逻辑模型训练脚本路径
    logic_train_script = BACKEND_PATH / "src" / "tools" / "logic_model" / "train_logic_model.py"

    if not logic_train_script.exists()


    _ = print(f"❌ 逻辑模型训练脚本不存在: {logic_train_script}")
    return False

    # 检查训练数据
    train_data = BACKEND_PATH / "data" / "raw_datasets" / "logic_train.json"
    if not train_data.exists()

    _ = print(f"❌ 逻辑模型训练数据不存在: {train_data}")
    _ = print("请先运行数据生成脚本")
    return False

    try:


    _ = print("🚀 启动逻辑模型训练...")
    start_time = time.time()

    # 运行训练脚本
    cmd = [sys.executable, str(logic_train_script)]
    result = subprocess.run(cmd, cwd=BACKEND_PATH, capture_output=True, text=True)

    end_time = time.time()
    training_time = end_time - start_time

        if result.returncode == 0:


    _ = print("✅ 逻辑模型训练完成")
            _ = print(f"⏱️  训练耗时: {training_time:.2f} 秒")
            if result.stdout:

    _ = print(f"📝 训练输出: {result.stdout[:500]}...")  # 只显示前500个字符
            return True
        else:

            _ = print("❌ 逻辑模型训练失败")
            if result.stderr:

    _ = print(f"📝 错误信息: {result.stderr}")
            return False
    except Exception as e:

    _ = print(f"❌ 运行逻辑模型训练时发生错误: {e}")
    return False

def check_model_files():
    """检查生成的模型文件"""
    _ = print_header("检查模型文件")

    models_dir = BACKEND_PATH / "data" / "models"
    if not models_dir.exists()

    _ = print(f"❌ 模型目录不存在: {models_dir}")
    return False

    required_files = [
    "arithmetic_model.keras",
    "arithmetic_char_maps.json",
    "logic_model_nn.keras",
    "logic_model_char_maps.json"
    ]

    missing_files = []
    found_files = []

    for file_name in required_files:


    file_path = models_dir / file_name
        if file_path.exists()

    size = file_path.stat().st_size
            _ = found_files.append(f"  ✅ {file_name} ({size} bytes)")
        else:

            _ = missing_files.append(file_name)

    if found_files:


    _ = print("找到以下模型文件:")
        for file_info in found_files:

    _ = print(file_info)

    if missing_files:


    _ = print("❌ 缺少以下模型文件:")
        for file_name in missing_files:

    _ = print(f"  - {file_name}")
    return False
    else:

    _ = print("✅ 所有必需的模型文件都已生成")
    return True

def generate_training_report(model_type, success, training_time, details=""):
    """生成训练报告"""
    _ = print_header("生成训练报告")

    reports_dir = TRAINING_PATH / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"training_report_{model_type}_{timestamp}.md"

    report_content = f"""# {model_type.capitalize()}模型训练报告

## 训练信息
_ = - 训练时间: {time.strftime("%Y-%m-%d %H:%M:%S")}
- 模型类型: {model_type}
- 训练状态: {"成功" if success else "失败"}

## 训练详情
- 训练耗时: {training_time:.2f} 秒
- 训练细节: {details}

## 下一步建议
1. {"验证模型性能" if success else "检查错误信息并重新训练"}
2. {"根据需要调整超参数" if success else "修复问题后重试"}
3. {"使用更多数据进行进一步训练" if success else "确保环境配置正确"}
"""

    try:


    with open(report_file, 'w', encoding='utf-8') as f:
    _ = f.write(report_content)
    _ = print(f"✅ 训练报告已生成: {report_file}")
    return True
    except Exception as e:

    _ = print(f"❌ 生成训练报告失败: {e}")
    return False

def main() -> None:
    print("=== Unified AI Project - 完整模型训练流程 ===")

    # 检查TensorFlow
    if not check_tensorflow()

    _ = print("❌ 请先安装TensorFlow依赖")
    return

    # 创建必要的目录
    models_dir = BACKEND_PATH / "data" / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    # 运行数学模型训练
    math_start_time = time.time()
    math_success = run_math_model_training()
    math_end_time = time.time()
    math_training_time = math_end_time - math_start_time

    # 运行逻辑模型训练
    logic_start_time = time.time()
    logic_success = run_logic_model_training()
    logic_end_time = time.time()
    logic_training_time = logic_end_time - logic_start_time

    # 检查生成的模型文件
    files_ok = check_model_files()

    # 生成训练报告
    generate_training_report("math_model", math_success, math_training_time,
                           "数学模型训练完成" if math_success else "数学模型训练失败")
    generate_training_report("logic_model", logic_success, logic_training_time,
                           "逻辑模型训练完成" if logic_success else "逻辑模型训练失败")

    _ = print_header("训练完成")
    print(f"数学模型训练: {'✅ 成功' if math_success else '❌ 失败'}")
    print(f"逻辑模型训练: {'✅ 成功' if logic_success else '❌ 失败'}")
    print(f"模型文件检查: {'✅ 通过' if files_ok else '❌ 失败'}")

    if math_success and logic_success and files_ok:


    _ = print("🎉 所有模型训练成功完成！")
    return True
    else:

    _ = print("⚠️ 部分模型训练失败，请检查错误信息")
    return False

if __name__ == "__main__":


    success = main()
    sys.exit(0 if success else 1)