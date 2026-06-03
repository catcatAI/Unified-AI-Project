# =============================================================================
# ANGELA-MATRIX: 密鑰生成工具
# =============================================================================
# 職責: 生成強隨機系統密鑰並更新環境變量
# =============================================================================

import os
import secrets
import string
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class KeyGenerator:
    """系統密鑰生成器"""
    
    @staticmethod
    def generate_secure_key(length: int = 32) -> str:
        """生成一個強隨機密鑰"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def update_env_file(self, keys: Dict[str, str], env_path: str = ".env") -> None:
        """更新 .env 文件中的密鑰"""
        if not os.path.exists(env_path):
            logger.info(f"創建新的 {env_path} 文件")
            with open(env_path, "w") as f:
                for name, val in keys.items():
                    f.write(f"{name}={val}\n")
            return

        with open(env_path, "r") as f:
            lines = f.readlines()

        new_lines = []
        updated_keys = set()

        for line in lines:
            match = False
            for key_name in keys:
                if line.startswith(f"{key_name}="):
                    new_lines.append(f"{key_name}={keys[key_name]}\n")
                    updated_keys.add(key_name)
                    match = True
                    break
            if not match:
                new_lines.append(line)

        # 添加不存在的密鑰
        for key_name, val in keys.items():
            if key_name not in updated_keys:
                new_lines.append(f"{key_name}={val}\n")

        with open(env_path, "w") as f:
            f.writelines(new_lines)
        
        logger.info(f"成功更新 {env_path} 文件")

def main() -> None:
    """Generate and update system core keys in the .env file."""
    logging.basicConfig(level=logging.INFO)
    gen = KeyGenerator()
    
    keys = {
        "ANGELA_KEY_A": gen.generate_secure_key(48),
        "ANGELA_KEY_B": gen.generate_secure_key(48),
        "ANGELA_KEY_C": gen.generate_secure_key(48),
    }
    
    logger.info("🔐 正在生成 Angela 系統核心密鑰...")
    
    # 查找 .env 文件路徑 (向上查找)
    env_path = ".env"
    for _ in range(3):
        if os.path.exists(env_path) or os.path.exists(env_path + ".example"):
            break
        env_path = os.path.join("..", env_path)
    
    gen.update_env_file(keys, env_path)
    logger.info("✅ 密鑰生成完畢。請重啟系統以應用更改。")

if __name__ == "__main__":
    main()
