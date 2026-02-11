# =============================================================================
# ANGELA-MATRIX: L6[执行层] 全层级 [A] L2+
# =============================================================================
#
# 职责: 设置环境变量文件
# 维度: 涉及所有维度，配置系统环境
# 安全: 使用 Key A (后端控制) 进行环境配置
# 成熟度: L2+ 等级理解环境配置的概念
#
# =============================================================================

from pathlib import Path
import logging
import shutil

logger = logging.getLogger(__name__)

def setup_env_file(
    project_root: Path = Path("."),
    env_example_name: str = ".env.example",
    env_name: str = ".env"
) -> bool:
    """設置环境变量文件。如果 .env 文件不存在, 則從 .env.example 複製。

    Args:
        project_root: 項目根目錄的路徑。
        env_example_name: .env.example 文件的名稱。
        env_name: .env 文件的名稱。

    Returns:
        bool: 如果 .env 文件已存在或成功創建, 則為 True, 否則為 False。
    """
    logger.info("🔧 設置环境变量...")
    
    env_path = project_root / env_name
    example_path = project_root / env_example_name
    
    # 如果 .env 已存在，不進行任何操作
    if env_path.exists():
        logger.info(f"✅ {env_name} 已存在，跳過創建")
        return True
    
    # 檢查 .env.example 是否存在
    if not example_path.exists():
        logger.warning(f"⚠️  {env_example_name} 不存在，無法創建 {env_name}")
        return False
    
    # 複製 .env.example 到 .env
    try:
        shutil.copy(example_path, env_path)
        logger.info(f"✅ 已從 {env_example_name} 創建 {env_name}")
        return True
    except Exception as e:
        logger.error(f"❌ 創建 {env_name} 失敗: {e}")
        return False