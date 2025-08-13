#!/usr/bin/env python3
"""
啟動 ChromaDB 服務器
"""

import os
import sys
import chromadb
from chromadb.config import Settings

def start_chroma_server():
    """
    啟動 ChromaDB 服務器
    """
    print("啟動 ChromaDB 服務器...")
    # 設置數據存儲路徑
    chroma_db_path = os.path.join(os.getcwd(), "chroma_db")
    os.makedirs(chroma_db_path, exist_ok=True)
    
    # 啟動服務器
    settings = Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=chroma_db_path,
        anonymized_telemetry=False
    )
    
    # 創建服務器實例
    server = chromadb.Server(settings=settings)
    
    # 啟動服務器
    server.run(host="localhost", port=8000)

if __name__ == "__main__":
    start_chroma_server()