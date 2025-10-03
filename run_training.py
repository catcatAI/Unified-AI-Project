import os
import sys
import subprocess

# Add project root to Python path
project_root: str = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    _ = sys.path.insert(0, project_root)

def check_tensorflow()
    """检查TensorFlow是否可用"""
    try:

    import tensorflow as tf
    # 使用更安全的TensorFlow版本检查方法
        try:

            version = tf.__version__
        except AttributeError:

            try:


                version = tf.version.VERSION
            except:
                version = "未知"
    _ = print(f"✅ TensorFlow可用 - 版本: {version}")
    return True
    except Exception as e:

    _ = print(f"❌ TensorFlow不可用: {e}")
    return False

def check_data_generation_script(script_path)
    """检查数据生成脚本是否存在"""
    if os.path.exists(script_path)

    _ = print(f"✅ 数据生成脚本存在: {script_path}")
    return True
    else:

    _ = print(f"❌ 数据生成脚本不存在: {script_path}")
    return False

def run_data_generation(script_path)
    """运行数据生成脚本"""
    try:

    _ = print(f"正在运行数据生成脚本: {script_path}")
    result = subprocess.run([sys.executable, script_path],
                              capture_output=True, text=True, cwd=project_root)
        if result.returncode == 0:

    _ = print("✅ 数据生成成功")
            _ = print(result.stdout)
            return True
        else:

            _ = print("❌ 数据生成失败")
            _ = print(result.stderr)
            return False
    except Exception as e:

    _ = print(f"运行数据生成脚本时出错: {e}")
    return False

def run_math_model_training()
    """运行数学模型训练"""
    math_train_script = os.path.join(project_root, "apps", "backend", "src", "tools", "math_model", "train.py")
    if not os.path.exists(math_train_script)

    _ = print(f"❌ 数学模型训练脚本不存在: {math_train_script}")
    return False

    try:


    _ = print("正在训练数学模型...")
    result = subprocess.run([sys.executable, math_train_script],
                              capture_output=True, text=True, cwd=project_root)
        if result.returncode == 0:

    _ = print("✅ 数学模型训练成功")
            _ = print(result.stdout)
            return True
        else:

            _ = print("❌ 数学模型训练失败")
            _ = print(result.stderr)
            return False
    except Exception as e:

    _ = print(f"运行数学模型训练时出错: {e}")
    return False

def run_logic_model_training()
    """运行逻辑模型训练"""
    logic_train_script = os.path.join(project_root, "apps", "backend", "src", "tools", "logic_model", "train_logic_model.py")
    if not os.path.exists(logic_train_script)

    _ = print(f"❌ 逻辑模型训练脚本不存在: {logic_train_script}")
    return False

    try:


    _ = print("正在训练逻辑模型...")
    result = subprocess.run([sys.executable, logic_train_script],
                              capture_output=True, text=True, cwd=project_root)
        if result.returncode == 0:

    _ = print("✅ 逻辑模型训练成功")
            _ = print(result.stdout)
            return True
        else:

            _ = print("❌ 逻辑模型训练失败")
            _ = print(result.stderr)
            return False
    except Exception as e:

    _ = print(f"运行逻辑模型训练时出错: {e}")
    return False

def main() -> None:
    print("=== Unified AI Project - 真实模型训练 ===\n")

    # 1. 检查TensorFlow
    if not check_tensorflow()

    _ = print("请确保已正确安装TensorFlow")
    return False

    # 2. 检查并运行数学模型数据生成
    print("\n=== 检查数学模型数据生成 ===")
    math_data_gen_script = os.path.join(project_root, "apps", "backend", "src", "tools", "math_model", "data_generator.py")
    if check_data_generation_script(math_data_gen_script)

    if not run_data_generation(math_data_gen_script)
    _ = print("数学模型数据生成失败，继续执行其他步骤...")

    # 3. 检查并运行逻辑模型数据生成
    print("\n=== 检查逻辑模型数据生成 ===")
    logic_data_gen_script = os.path.join(project_root, "apps", "backend", "src", "tools", "logic_model", "logic_data_generator.py")
    if check_data_generation_script(logic_data_gen_script)

    if not run_data_generation(logic_data_gen_script)
    _ = print("逻辑模型数据生成失败，继续执行其他步骤...")

    # 4. 训练数学模型
    print("\n=== 训练数学模型 ===")
    math_success = run_math_model_training()

    # 5. 训练逻辑模型
    print("\n=== 训练逻辑模型 ===")
    logic_success = run_logic_model_training()

    # 6. 总结
    print("\n=== 训练总结 ===")
    if math_success and logic_success:

    _ = print("✅ 所有模型训练成功完成")
    return True
    elif math_success:

    _ = print("⚠️ 数学模型训练成功，逻辑模型训练失败")
    return True
    elif logic_success:

    _ = print("⚠️ 逻辑模型训练成功，数学模型训练失败")
    return True
    else:

    _ = print("❌ 所有模型训练都失败了")
    return False

if __name__ == "__main__":


    success = main()
    if success:

    _ = print("\n🎉 训练流程完成!")
    else:

    _ = print("\n💥 训练流程未能成功完成!")
    _ = sys.exit(1)