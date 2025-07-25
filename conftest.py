import os
import pytest
import os
import asyncio
import pytest
from cryptography.fernet import Fernet

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """設置測試環境變量"""
    # 設置測試用的 MIKO_HAM_KEY
    if not os.environ.get('MIKO_HAM_KEY'):
        # 生成一個測試用的密鑰
        test_key = Fernet.generate_key().decode()
        os.environ['MIKO_HAM_KEY'] = test_key
    
    # 設置其他測試環境變量
    os.environ['TESTING'] = 'true'
    
    yield
    
    # 清理（如果需要）
    pass

@pytest.fixture(scope="function")
def clean_test_files():
    """清理測試文件"""
    import glob
    
    # 在測試前清理
    test_files = glob.glob("data/processed_data/test_*.json")
    for file in test_files:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
    
    yield
    
    # 在測試後清理
    test_files = glob.glob("data/processed_data/test_*.json")
    for file in test_files:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass
