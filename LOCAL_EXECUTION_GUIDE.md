# 本機運行指南與問題解決方案

## 當前運行問題分析

### 1. Python執行環境問題
**問題現象**：
- Python腳本無法正常執行
- 模塊導入失敗
- 路徑配置問題

**根本原因**：
1. **路徑配置錯誤**：sys.path設置不正確
2. **依賴缺失**：必要包未安裝
3. **權限問題**：文件執行權限不足
4. **環境變量**：Python環境變量配置問題

### 2. Redis依賴問題
**問題現象**：
- Redis連接失敗
- 緩存功能無法使用
- 会话管理異常

**解決方案**：
```bash
# 方案1：安裝Redis服務
# Windows
choco install redis-64
# 或下載Redis for Windows

# 方案2：使用Docker
docker run -d -p 6379:6379 redis

# 方案3：使用模擬模式（已實現）
# 所有組件已修改為支持無Redis模式
```

### 3. 依賴包問題
**缺失的包**：
- redis
- numpy
- fastapi
- uvicorn
- paho-mqtt
- chromadb

## 本機運行解決方案

### 步驟1：環境準備

#### 1.1 檢查Python環境
```bash
# 確認Python版本（需要3.8+）
python --version

# 確認pip
pip --version

# 升級pip
python -m pip install --upgrade pip
```

#### 1.2 安裝必要依賴
```bash
# 安裝核心依賴
pip install numpy
pip install fastapi
pip install uvicorn
pip install redis
pip install paho-mqtt
pip install chromadb
pip install psutil
pip install aiofiles
pip install python-multipart
pip install python-jose[cryptography]
pip install passlib[bcrypt]

# 安裝開發依賴
pip install pytest
pip install pytest-asyncio
```

#### 1.3 配置環境變量
```bash
# Windows
set PYTHONPATH=%CD%\apps\backend\src;%PYTHONPATH%

# Linux/Mac
export PYTHONPATH=$PWD/apps/backend/src:$PYTHONPATH
```

### 步驟2：測試基礎功能

#### 2.1 創建測試腳本
```python
# test_basic.py
import sys
import os

# 添加項目路徑
project_root = os.path.dirname(os.path.abspath(__file__))
backend_src = os.path.join(project_root, 'apps', 'backend', 'src')
sys.path.insert(0, backend_src)

try:
    print("測試基礎導入...")
    
    # 測試基礎模塊
    import asyncio
    import logging
    from datetime import datetime
    print("✓ 基礎模塊導入成功")
    
    # 測試numpy
    import numpy as np
    print(f"✓ numpy {np.__version__} 導入成功")
    
    # 測試FastAPI
    from fastapi import FastAPI
    print("✓ FastAPI 導入成功")
    
    # 測試Redis（可選）
    try:
        import redis.asyncio as redis
        print("✓ Redis 客戶端導入成功")
    except ImportError:
        print("⚠️ Redis 未安裝，將使用模擬模式")
    
    print("\n基礎環境測試通過！")
    
except Exception as e:
    print(f"錯誤: {e}")
    import traceback
    traceback.print_exc()
```

#### 2.2 測試組件導入
```python
# test_components.py
import sys
import os

# 添加項目路徑
project_root = os.path.dirname(os.path.abspath(__file__))
backend_src = os.path.join(project_root, 'apps', 'backend', 'src')
sys.path.insert(0, backend_src)

def test_imports():
    """測試所有組件導入"""
    components = [
        ("AI運維引擎", "ai.ops.ai_ops_engine", "AIOpsEngine"),
        ("預測性維護", "ai.ops.predictive_maintenance", "PredictiveMaintenanceEngine"),
        ("性能優化器", "ai.ops.performance_optimizer", "PerformanceOptimizer"),
        ("容量規劃器", "ai.ops.capacity_planner", "CapacityPlanner"),
        ("智能運維管理器", "ai.ops.intelligent_ops_manager", "IntelligentOpsManager"),
    ]
    
    results = []
    
    for name, module_name, class_name in components:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            
            # 創建實例
            instance = cls()
            
            results.append((name, True, None))
            print(f"✓ {name}: 導入和實例化成功")
            
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"✗ {name}: {e}")
    
    return results

if __name__ == "__main__":
    print("組件導入測試")
    print("="*50)
    
    results = test_imports()
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    print(f"\n結果: {passed}/{total} 通過")
    
    if passed == total:
        print("所有組件導入成功！")
    else:
        print("部分組件導入失敗，需要檢查")
```

### 步驟3：運行完整測試

#### 3.1 運行單元測試
```bash
# 運行完整測試套件
cd D:\Projects\Unified-AI-Project
python tests\unit\test_ai_ops_complete.py
```

#### 3.2 運行功能測試
```bash
# 運行功能測試
python test_functionality.py
```

#### 3.3 運行性能測試
```bash
# 運行性能測試
python test_performance.py
```

## 常見問題解決

### 問題1：ModuleNotFoundError
**症狀**：
```
ModuleNotFoundError: No module named 'ai.ops.ai_ops_engine'
```

**解決方案**：
```python
# 在腳本開頭添加
import sys
import os
project_root = os.path.dirname(os.path.abspath(__file__))
backend_src = os.path.join(project_root, 'apps', 'backend', 'src')
sys.path.insert(0, backend_src)
```

### 問題2：Redis連接失敗
**症狀**：
```
redis.exceptions.ConnectionError: Error 10061
```

**解決方案**：
1. 啟動Redis服務
2. 或使用模擬模式（已實現）
3. 修改配置使用本地Redis

### 問題3：依賴包版本衝突
**症狀**：
```
ERROR: pip's dependency resolver does not currently take into account...
```

**解決方案**：
```bash
# 使用虛擬環境
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 問題4：權限問題
**症狀**：
```
PermissionError: [Errno 13] Permission denied
```

**解決方案**：
1. 以管理員身份運行
2. 修改文件權限
3. 使用用戶目錄

## 離線運行配置

### 1. 完全離線模式
所有組件已修改為支持無Redis、無網絡模式：

```python
# 在配置中設置
config = {
    'redis_host': None,  # 禁用Redis
    'enable_network': False,  # 禁用網絡
    'mock_mode': True  # 啟用模擬模式
}
```

### 2. 本地數據存儲
使用本地文件替代Redis：
```python
import json
import os

class LocalStorage:
    def __init__(self, base_dir="./local_storage"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    
    def set(self, key, value):
        with open(os.path.join(self.base_dir, f"{key}.json"), 'w') as f:
            json.dump(value, f)
    
    def get(self, key):
        try:
            with open(os.path.join(self.base_dir, f"{key}.json"), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
```

### 3. 模擬服務
```python
class MockService:
    def __init__(self):
        self.data = {}
    
    async def call(self, method, *args, **kwargs):
        # 模擬延遲
        await asyncio.sleep(0.1)
        return {"status": "success", "data": "mock_data"}
```

## 性能優化建議

### 1. 內存優化
- 使用對象池
- 及時釋放不需要的對象
- 監控內存使用

### 2. 異步優化
- 使用asyncio
- 避免阻塞操作
- 合理設置並發數

### 3. 緩存策略
- 本地緩存熱點數據
- 使用LRU緩存
- 定期清理緩存

## 監控和調試

### 1. 日誌配置
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
```

### 2. 性能監控
```python
import time
import psutil

def monitor_performance():
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    
    print(f"CPU: {cpu_percent}%, Memory: {memory_percent}%")
```

### 3. 調試工具
- 使用pdb調試器
- 添加日誌輸出
- 使用性能分析器

## 下一步計劃

1. **短期**：
   - 解決當前環境問題
   - 完成基礎功能測試
   - 優化導入機制

2. **中期**：
   - 完善錯誤處理
   - 增加更多測試用例
   - 優化性能

3. **長期**：
   - 建立CI/CD流水線
   - 自動化測試
   - 生產環境部署

## 總結

通過以上解決方案，應該能夠解決大部分本機運行問題。關鍵是：
1. 正確配置Python路徑
2. 安裝必要依賴
3. 使用模擬模式處理外部依賴
4. 添加適當的錯誤處理

如果仍有問題，建議：
1. 檢查Python版本兼容性
2. 使用虛擬環境
3. 逐步調試每個組件
4. 記錄詳細錯誤信息