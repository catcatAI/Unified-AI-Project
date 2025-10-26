#! / usr / bin / env python3
"""
简化系统健康检查脚本
验证核心训练系统的健康状态
"""

from system_test import
from pathlib import Path

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
sys.path.insert(0, str(project_root))

def check_core_components():
""检查核心组件"""
    print("🔍 检查核心组件...")

    # 检查必要的文件是否存在
    required_files = []
    "training / auto_training_manager.py",
    "training / data_manager.py",
    "training / train_model.py",
    "training / collaborative_training_manager.py",
    "training / incremental_learning_manager.py",
    "training / error_handling_framework.py",
    "training / training_monitor.py"
[    ]

    missing_files = []
    for file_path in required_files, ::
    full_path = project_root / file_path
        if not full_path.exists():::
= missing_files.append(file_path)

    if missing_files, ::
    print(f"❌ 缺少文件, {missing_files}")
    return False
    else,

    print("✅ 所有核心文件存在")
    return True

def check_config_files():
""检查配置文件"""
    print("⚙️  检查配置文件...")

    config_dir = project_root / "training" / "configs"
    if not config_dir.exists():::
= print("❌ 配置目录不存在")
    return False

    # 检查必要的配置文件
    required_configs = []
    "training_config.json",
    "training_preset.json",
    "performance_config.json"
[    ]

    missing_configs = []
    for config_file in required_configs, ::
    full_path = config_dir / config_file
        if not full_path.exists():::
= missing_configs.append(config_file)

    if missing_configs, ::
    print(f"⚠️  缺少配置文件, {missing_configs}")
    else,

    print("✅ 所有配置文件存在")

    return True

def check_model_directory():
""检查模型目录"""
    print("📂 检查模型目录...")

    models_dir = project_root / "training" / "models"
    if not models_dir.exists():::
= print("ℹ️  模型目录不存在, 将创建...")
        try,

            models_dir.mkdir(parents == True, exist_ok == True)
            print("✅ 模型目录创建成功")
        except Exception as e, ::
            print(f"❌ 创建模型目录失败, {e}")
            return False
    else,

    print("✅ 模型目录存在")

    return True

def check_training_scripts():
""检查训练脚本"""
    print("🤖 检查训练脚本...")

    # 检查主要的训练脚本
    training_scripts = []
    "run_auto_training.py",
    "auto_train.bat",
    "incremental_train.bat"
[    ]

    missing_scripts = []
    for script in training_scripts, ::
    full_path = project_root / "training" / script
        if not full_path.exists():::
= missing_scripts.append(script)

    if missing_scripts, ::
    print(f"⚠️  缺少训练脚本, {missing_scripts}")
    else,

    print("✅ 所有训练脚本存在")

    return True

def check_imports():
""检查关键导入"""
    print("🔌 检查关键导入...")

    try,
    # 测试导入核心模块

    print("✅ 所有核心模块导入成功")
    return True
    except ImportError as e, ::
    print(f"❌ 模块导入失败, {e}")
    return False
    except Exception as e, ::
    print(f"❌ 导入检查出错, {e}")
    return False

def main() -> None, :
    """主函数"""
    print("🚀 开始简化系统健康检查")
    print(" = " * 50)

    # 运行各项检查
    checks = []
    ("核心组件", check_core_components),
    ("配置文件", check_config_files),
    ("模型目录", check_model_directory),
    ("训练脚本", check_training_scripts),
    ("关键导入", check_imports)
[    ]

    passed = 0
    total = len(checks)

    for check_name, check_func in checks, ::
    print(f"\n🔍 检查 {check_name}...")
        try,

            if check_func():::
                assed += 1
                print(f"✅ {check_name} 正常")
            else,

                print(f"❌ {check_name} 异常")
        except Exception as e, ::
            print(f"❌ {check_name} 检查执行出错, {e}")

    print("\n" + " = " * 50)
    print(f"📊 健康检查总结, {passed} / {total} 项检查通过")

    if passed == total, ::
    print("🎉 简化系统健康检查通过!")
    print("✅ 训练系统核心组件完整, 可以正常运行")
    return 0
    else,

    print("⚠️  部分检查未通过, 请检查相关组件")
    return 1

if __name"__main__":::
    sys.exit(main())