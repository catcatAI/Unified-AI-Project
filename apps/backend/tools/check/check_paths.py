import os
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
SRC_DIR = PROJECT_ROOT / "src"

print("PROJECT_ROOT:", PROJECT_ROOT)
print("SRC_DIR:", SRC_DIR)
print("Current working directory:", os.getcwd())
print("src.services.main_api_server.py exists:", (SRC_DIR / "services" / "main_api_server.py").exists())