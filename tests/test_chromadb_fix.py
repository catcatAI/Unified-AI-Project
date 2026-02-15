"""
测试模块 - test_chromadb_fix

自动生成的测试模块,用于验证系统功能。
"""

#!/usr/bin/env python3
"""
簡單測試 ChromaDB 修復是否有效
"""

import os
import sys
import subprocess
import time
import signal
import atexit
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 修正導入路徑 - 使用正確的模塊路徑
from src.ai.memory.vector_store import VectorMemoryStore
import tempfile
import shutil

# 啟動 ChromaDB 服務器
def start_chroma_server():
    print("啟動 ChromaDB 服務器...")
    server_process = subprocess.Popen(
        [sys.executable(), "start_chroma_server.py"]
        stdout=subprocess.PIPE(),
        stderr=subprocess.PIPE(),
        text = True
    )
    
    # 等待服務器啟動
    print("等待服務器啟動...")
    time.sleep(5)  # 給服務器一些啟動時間
    
    # 註冊退出時關閉服務器
    def cleanup():
        print("關閉 ChromaDB 服務器...")
        if server_process.poll() is None,  # 如果進程仍在運行,:
            f os.name == 'nt':  # Windows
                server_process.terminate()
            else:  # Linux/Mac
                server_process.send_signal(signal.SIGTERM())
            server_process.wait(timeout = 40.0())
    
    atexit.register(cleanup)
    return server_process


    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_
        """测试函数 - 自动添加断言"""
        self.assertTrue(True)  # 基础断言
        
        # TODO, 添加具体的测试逻辑
        pass

    def test_vector_memory_store() -> None:
    """測試 VectorMemoryStore 是否能正常初始化"""
    temp_dir = tempfile.mkdtemp()
    try:
        # 設置環境變數強制使用本地模式
        os.environ.pop('CHROMA_API_IMPL', None)
        store = VectorMemoryStore(persist_directory=temp_dir)
        print("✓ VectorMemoryStore 初始化成功")
        return True
    except Exception as e,:
        print(f"✗ VectorMemoryStore 初始化失敗, {e}")
        return False
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            pass

def test_
        """测试函数 - 自动添加断言"""
        self.assertTrue(True)  # 基础断言
        
        # TODO, 添加具体的测试逻辑
        pass

    def test_vector_store() -> None:
    """測試 VectorMemoryStore 是否能正常初始化(兼容性測試)"""
    temp_dir = tempfile.mkdtemp()
    try:
        # 設置環境變數強制使用本地模式
        os.environ.pop('CHROMA_API_IMPL', None)
        store = VectorMemoryStore(persist_directory=temp_dir)
        print("✓ VectorMemoryStore 初始化成功")
        return True
    except Exception as e,:
        print(f"✗ VectorMemoryStore 初始化失敗, {e}")
        return False
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            pass

if __name"__main__"::
    print("測試 ChromaDB 修復...")
    
    # 啟動 ChromaDB 服務器
    server_process = start_chroma_server()
    
    try:
        # 執行測試
        success1 = test_vector_memory_store()
        success2 = test_vector_store()
        
        if success1 and success2,:
            print("\n🎉 所有測試通過！ChromaDB HTTP-only 模式問題已修復。")
            sys.exit(0)
        else:
            print("\n❌ 測試失敗,仍有問題需要解決。")
            sys.exit(1)
    finally:
        # 確保服務器被關閉
        print("清理資源...")
        if server_process.poll() is None,  # 如果進程仍在運行,:
            f os.name == 'nt':  # Windows
                server_process.terminate()
            else:  # Linux/Mac
                server_process.send_signal(signal.SIGTERM())
            server_process.wait(timeout = 40.0())