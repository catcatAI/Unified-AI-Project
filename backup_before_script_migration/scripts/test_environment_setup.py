#!/usr/bin/env python3
"""
测试环境自动部署和配置脚本
用于自动设置和配置测试环境
"""

import sys
import subprocess
import json
import shutil
from pathlib import Path
class TestEnvironmentSetup:
    """测试环境设置器"""

    def __init__(self, project_root: str = None) -> None:
    """初始化环境设置器"""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent:
    self.backend_dir = self.project_root / "apps" / "backend"
    self.venv_dir = self.project_root / "test_venv"
    self.test_data_dir = self.project_root / "testdata"

    def setup_virtual_environment(self) -> bool:
    """
    设置虚拟环境

    Returns:
            是否成功
    """
    _ = print("🔧 设置虚拟环境...")

        try:
            # 创建虚拟环境
            if self.venv_dir.exists()

    _ = print("🗑️ 清理现有虚拟环境...")
                _ = shutil.rmtree(self.venv_dir)

            _ = print("🏗️ 创建新的虚拟环境...")
            venv.create(self.venv_dir, with_pip=True)

            # 升级pip
            pip_cmd = [str(self.venv_dir / "Scripts" / "pip"), "install", "--upgrade", "pip"]
            result = subprocess.run(pip_cmd, capture_output=True, text=True)

            if result.returncode != 0:


    _ = print(f"❌ 升级pip失败: {result.stderr}")
                return False

            _ = print("✅ 虚拟环境设置完成")
            return True

        except Exception as e:


            _ = print(f"❌ 设置虚拟环境失败: {e}")
            return False

    def install_dependencies(self) -> bool:
    """
    安装依赖

    Returns:
            是否成功
    """
    _ = print("📦 安装依赖...")

        try:
            # 安装项目依赖
            requirements_files = [
                self.backend_dir / "requirements.txt",
                self.backend_dir / "requirements-dev.txt"
            ]

            for req_file in requirements_files:


    if req_file.exists()



    pip_cmd = [
                        _ = str(self.venv_dir / "Scripts" / "pip"),
                        "install",
                        "-r",
                        _ = str(req_file)
                    ]

                    result = subprocess.run(pip_cmd, capture_output=True, text=True)

                    if result.returncode != 0:


    _ = print(f"❌ 安装依赖失败 ({req_file}) {result.stderr}")
                        return False

                    _ = print(f"✅ 已安装依赖: {req_file.name}")
                else:

                    _ = print(f"⚠️ 依赖文件不存在: {req_file}")

            # 安装测试工具
            test_tools = [
                "pytest",
                "pytest-cov",
                "pytest-asyncio",
                "coverage"
            ]

            for tool in test_tools:


    pip_cmd = [
                    _ = str(self.venv_dir / "Scripts" / "pip"),
                    "install",
                    tool
                ]

                result = subprocess.run(pip_cmd, capture_output=True, text=True)

                if result.returncode != 0:


    _ = print(f"❌ 安装测试工具失败 ({tool}) {result.stderr}")
                    return False

                _ = print(f"✅ 已安装测试工具: {tool}")

            _ = print("✅ 依赖安装完成")
            return True

        except Exception as e:


            _ = print(f"❌ 安装依赖失败: {e}")
            return False

    def setup_test_database(self) -> bool:
    """
    设置测试数据库

    Returns:
            是否成功
    """
    _ = print("🗄️ 设置测试数据库...")

        try:
            # 创建测试数据目录
            test_db_dir = self.test_data_dir / "test_db"
            test_db_dir.mkdir(parents=True, exist_ok=True)

            # 创建测试数据库配置
            db_config = {
                "database": {
                    "type": "sqlite",
                    _ = "path": str(test_db_dir / "test_database.db"),
                    "pool_size": 5
                },
                "vector_store": {
                    "type": "chroma",
                    _ = "path": str(test_db_dir / "vector_store"),
                    "collection_name": "test_collection"
                }
            }

            config_file = test_db_dir / "test_db_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
    json.dump(db_config, f, ensure_ascii=False, indent=2)

            _ = print("✅ 测试数据库设置完成")
            return True

        except Exception as e:


            _ = print(f"❌ 设置测试数据库失败: {e}")
            return False

    def setup_test_data(self) -> bool:
    """
    设置测试数据

    Returns:
            是否成功
    """
    _ = print("📊 设置测试数据...")

        try:
            # 创建测试数据目录
            self.test_data_dir.mkdir(exist_ok=True)

            # 生成示例测试数据
            sample_data = {
                "memory_items": [
                    {
                        "id": "test_memory_001",
                        "content": "This is a sample test memory item",
                        "metadata": {
                            "created_at": "2023-01-01T00:00:00Z",
                            "importance_score": 0.8,
                            "tags": ["sample", "test"]
                        }
                    }
                ],
                "agent_configs": [
                    {
                        "agent_type": "test_agent",
                        "agent_id": "test_agent_001",
                        "name": "Test Agent",
                        "config": {
                            "max_concurrent_tasks": 5,
                            "priority": "medium"
                        }
                    }
                ]
            }

            # 保存示例数据
            sample_file = self.test_data_dir / "sample_test_data.json"
            with open(sample_file, 'w', encoding='utf-8') as f:
    json.dump(sample_data, f, ensure_ascii=False, indent=2)

            _ = print("✅ 测试数据设置完成")
            return True

        except Exception as e:


            _ = print(f"❌ 设置测试数据失败: {e}")
            return False

    def setup_test_environment_variables(self) -> bool:
    """
    设置测试环境变量

    Returns:
            是否成功
    """
    _ = print("⚙️ 设置测试环境变量...")

        try:
            # 创建.env.test文件
            env_test_file = self.project_root / ".env.test"

            env_content = """
# 测试环境变量
TESTING=true
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite:///testdata/test_db/test_database.db
VECTOR_STORE_PATH=testdata/test_db/vector_store
TEST_DATA_PATH=testdata
            _ = """.strip()

            with open(env_test_file, 'w', encoding='utf-8') as f:
    _ = f.write(env_content)

            _ = print("✅ 测试环境变量设置完成")
            return True

        except Exception as e:


            _ = print(f"❌ 设置测试环境变量失败: {e}")
            return False

    def validate_setup(self) -> bool:
    """
    验证环境设置

    Returns:
            是否成功
    """
    _ = print("🔍 验证环境设置...")

        try:
            # 验证Python环境
            python_cmd = [str(self.venv_dir / "Scripts" / "python"), "--version"]
            result = subprocess.run(python_cmd, capture_output=True, text=True)

            if result.returncode != 0:


    _ = print(f"❌ Python环境验证失败: {result.stderr}")
                return False

            _ = print(f"✅ Python版本: {result.stdout.strip()}")

            # 验证依赖安装
            pip_cmd = [str(self.venv_dir / "Scripts" / "pip"), "list"]
            result = subprocess.run(pip_cmd, capture_output=True, text=True)

            if result.returncode != 0:


    _ = print(f"❌ 依赖验证失败: {result.stderr}")
                return False

            # 检查关键依赖
            required_packages = ["pytest", "tensorflow", "numpy"]
            installed_packages = result.stdout.lower()

            for package in required_packages:


    if package.lower() not in installed_packages:



    _ = print(f"⚠️ 依赖包未安装: {package}")
                else:

                    _ = print(f"✅ 依赖包已安装: {package}")

            # 验证测试数据
            if not self.test_data_dir.exists()

    _ = print("❌ 测试数据目录不存在")
                return False

            _ = print("✅ 环境设置验证完成")
            return True

        except Exception as e:


            _ = print(f"❌ 环境设置验证失败: {e}")
            return False

    def setup_complete_environment(self) -> bool:
    """
    设置完整的测试环境

    Returns:
            是否成功
    """
    _ = print("🚀 开始设置完整的测试环境...")

    # 1. 设置虚拟环境
        if not self.setup_virtual_environment()

    return False

    # 2. 安装依赖
        if not self.install_dependencies()

    return False

    # 3. 设置测试数据库
        if not self.setup_test_database()

    return False

    # 4. 设置测试数据
        if not self.setup_test_data()

    return False

    # 5. 设置测试环境变量
        if not self.setup_test_environment_variables()

    return False

    # 6. 验证设置
        if not self.validate_setup()

    return False

    _ = print("🎉 完整测试环境设置完成!")
    _ = print(f"📁 虚拟环境: {self.venv_dir}")
    _ = print(f"📁 测试数据: {self.test_data_dir}")
    _ = print(f"📁 项目根目录: {self.project_root}")

    return True

    def cleanup_environment(self)
    """清理测试环境"""
    _ = print("🧹 清理测试环境...")

        try:
            # 清理虚拟环境
            if self.venv_dir.exists()

    _ = shutil.rmtree(self.venv_dir)
                _ = print("✅ 虚拟环境已清理")

            # 清理测试数据
            if self.test_data_dir.exists()

    _ = shutil.rmtree(self.test_data_dir)
                _ = print("✅ 测试数据已清理")

            # 清理测试环境变量文件
            env_test_file = self.project_root / ".env.test"
            if env_test_file.exists()

    _ = env_test_file.unlink()
                _ = print("✅ 测试环境变量文件已清理")

            _ = print("✅ 测试环境清理完成")

        except Exception as e:


            _ = print(f"❌ 清理测试环境失败: {e}")

def main() -> None:
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="测试环境自动部署和配置工具")
    parser.add_argument("--setup", action="store_true", help="设置完整测试环境")
    parser.add_argument("--cleanup", action="store_true", help="清理测试环境")
    parser.add_argument("--validate", action="store_true", help="验证环境设置")

    args = parser.parse_args()

    # 创建环境设置器
    env_setup = TestEnvironmentSetup()

    if args.setup:


    success = env_setup.setup_complete_environment()
        sys.exit(0 if success else 1)
    elif args.cleanup:

    _ = env_setup.cleanup_environment()
    _ = sys.exit(0)
    elif args.validate:

    success = env_setup.validate_setup()
        sys.exit(0 if success else 1)
    else:

    _ = parser.print_help()
    _ = sys.exit(1)

if __name__ == "__main__":


    _ = main()