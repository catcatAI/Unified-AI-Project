from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def setup_env_file(
    project_root: Path = Path("."), env_example_name: str = ".env.example", env_name: str = ".env"
) -> bool:
    """設置環境變量文件。
    如果 .env 文件不存在, 則從 .env.example 複製。

    Args:
        project_root: 項目根目錄的路徑。
        env_example_name: .env.example 文件的名稱。
        env_name: .env 文件的名稱。

    Returns:
        bool 如果 .env 文件已存在或成功創建, 則為 True, 否則為 False。
    """
    logger.info("🔧 設置環境變量...")

    env_example_path = project_root / env_example_name
    env_file_path = project_root / env_name

    if not env_example_path.exists():
        logger.error(f"❌ {env_example_path} 文件不存在")
        return False

    if not env_file_path.exists():
        try:
            # 複製示例文件
            with open(env_example_path, "r", encoding="utf-8") as f_example:
                content = f_example.read()
            with open(env_file_path, "w", encoding="utf-8") as f_env:
                f_env.write(content)

            logger.info(f"✅ 已創建 {env_file_path} 文件")
            logger.warning("⚠️  请編輯 .env 文件, 添加你的 API 密鑰")
        except Exception as e:
            logger.error(f"❌ 創建 {env_file_path} 失敗: {e}")
            return False
    else:
        logger.info(f"✅ {env_file_path} 文件已存在")

    return True


def add_env_variable(
    key: str, value: str, project_root: Path = Path("."), env_name: str = ".env"
) -> bool:
    """向 .env 文件添加或更新環境變量。

    Args:
        key: 環境變量的鍵。
        value: 環境變量的值。
        project_root: 項目根目錄的路徑。
        env_name: .env 文件的名稱。

    Returns:
        bool 如果成功添加或更新, 則為 True, 否則為 False。
    """
    env_file_path = project_root / env_name
    if not env_file_path.exists():
        logger.warning(f"⚠️  {env_file_path} 不存在, 無法添加環境變量 {key}")
        return False

    try:
        lines = []
        updated = False
        with open(env_file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    updated = True
                else:
                    lines.append(line)

        if not updated:
            lines.append(f"\n{key}={value}\n")

        with open(env_file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        logger.info(f"✅ 環境變量 {key} 已更新或添加至 {env_file_path}")
        return True
    except Exception as e:
        logger.error(f"❌ 更新 {env_file_path} 失敗: {e}")
        return False
