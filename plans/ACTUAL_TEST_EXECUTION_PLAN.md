# 實際測試執行計劃

## 問題診斷

### 當前測試失敗原因
1. **Python執行環境問題**
   - 可能是權限問題
   - 路徑配置問題
   - 依賴包缺失

2. **Redis依賴問題**
   - Redis服務未啟動
   - 連接配置問題

3. **模塊導入問題**
   - sys.path配置
   - 相對導入問題

## 解決方案

### 1. 環境準備

#### 檢查Python環境
```bash
# 檢查Python版本和路徑
python --version
where python

# 檢查pip
pip --version

# 檢查已安裝包
pip list
```

#### 安裝必要依賴
```bash
# 安裝Redis客戶端
pip install redis

# 安裝其他依賴
pip install numpy
pip install fastapi
pip install uvicorn
pip install paho-mqtt
```

#### 啟動Redis服務
```bash
# Windows下啟動Redis
redis-server

# 或使用Docker
docker run -d -p 6379:6379 redis
```

### 2. 測試執行步驟

#### 步驟1：基礎導入測試
創建 `test_basic_import.py`：
```python
import sys
import os

# 添加路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

try:
    print("測試基礎導入...")
    
    # 測試基礎模塊
    import asyncio
    import logging
    from datetime import datetime
    
    print("✓ 基礎模塊導入成功")
    
    # 測試numpy
    import numpy as np
    print("✓ numpy導入成功")
    
    # 測試Redis（可選）
    try:
        import redis.asyncio as redis
        print("✓ redis導入成功")
    except ImportError:
        print("⚠️ redis未安裝，將使用模擬模式")
    
    print("基礎導入測試通過")
    
except Exception as e:
    print(f"基礎導入測試失敗: {e}")
    import traceback
    traceback.print_exc()
```

#### 步驟2：組件導入測試
創建 `test_component_import.py`：
```python
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

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

#### 步驟3：功能測試
創建 `test_functionality.py`：
```python
import asyncio
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

async def test_ai_ops_functionality():
    """測試AI運維功能"""
    try:
        from ai.ops.ai_ops_engine import AIOpsEngine
        
        # 創建實例
        ai_ops = AIOpsEngine()
        
        # 測試數據
        test_metrics = {
            "cpu_usage": 85.0,
            "memory_usage": 75.0,
            "error_rate": 2.5,
            "response_time": 450
        }
        
        # 執行異常檢測
        start_time = time.time()
        anomalies = await ai_ops.detect_anomalies("test_component", test_metrics)
        end_time = time.time()
        
        print(f"✓ 異常檢測完成，耗時: {end_time - start_time:.3f}秒")
        print(f"  檢測到 {len(anomalies)} 個異常")
        
        return True
        
    except Exception as e:
        print(f"✗ AI運維功能測試失敗: {e}")
        return False

async def test_maintenance_functionality():
    """測試預測性維護功能"""
    try:
        from ai.ops.predictive_maintenance import PredictiveMaintenanceEngine
        
        # 創建實例
        maintenance = PredictiveMaintenanceEngine()
        
        # 測試數據
        test_metrics = {
            "cpu_usage": 75.0,
            "memory_usage": 60.0,
            "response_time": 300,
            "error_rate": 1.0
        }
        
        # 執行健康評估
        start_time = time.time()
        health_score = maintenance._simple_health_assessment(test_metrics)
        end_time = time.time()
        
        print(f"✓ 健康評估完成，耗時: {end_time - start_time:.3f}秒")
        print(f"  健康分數: {health_score:.1f}")
        
        return True
        
    except Exception as e:
        print(f"✗ 預測性維護功能測試失敗: {e}")
        return False

async def main():
    """主測試函數"""
    print("功能測試")
    print("="*50)
    
    tests = [
        ("AI運維功能", test_ai_ops_functionality),
        ("預測性維護功能", test_maintenance_functionality),
    ]
    
    results = []
    
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            start_time = time.time()
            result = await test_func()
            end_time = time.time()
            
            print(f"執行時間: {end_time - start_time:.3f}秒")
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} 測試異常: {e}")
            results.append((name, False))
    
    # 輸出結果
    print("\n" + "="*50)
    print("功能測試結果")
    print("="*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, result in results:
        status = "通過" if result else "失敗"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")
    
    print(f"\n結果: {passed}/{total} 通過")

if __name__ == "__main__":
    asyncio.run(main())
```

#### 步驟4：性能測試
創建 `test_performance.py`：
```python
import asyncio
import sys
import os
import time
import statistics

sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'backend', 'src'))

async def performance_test():
    """性能測試"""
    try:
        from ai.ops.ai_ops_engine import AIOpsEngine
        
        # 創建實例
        ai_ops = AIOpsEngine()
        
        # 測試參數
        test_count = 100
        concurrent = 10
        
        print(f"性能測試: {test_count}次請求，{concurrent}並發")
        
        # 執行測試
        response_times = []
        
        semaphore = asyncio.Semaphore(concurrent)
        
        async def single_request():
            async with semaphore:
                start_time = time.time()
                
                try:
                    await ai_ops.detect_anomalies(
                        "test_component",
                        {
                            "cpu_usage": 85.0,
                            "memory_usage": 75.0,
                            "error_rate": 2.5,
                            "response_time": 450
                        }
                    )
                    
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    return True
                    
                except Exception as e:
                    print(f"請求失敗: {e}")
                    return False
        
        # 執行測試
        start_time = time.time()
        tasks = [single_request() for _ in range(test_count)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # 計算結果
        success_count = sum(results)
        total_time = end_time - start_time
        
        if response_times:
            avg_time = statistics.mean(response_times)
            p50 = sorted(response_times)[int(len(response_times) * 0.5)]
            p95 = sorted(response_times)[int(len(response_times) * 0.95)]
            p99 = sorted(response_times)[int(len(response_times) * 0.99)]
        else:
            avg_time = p50 = p95 = p99 = 0
        
        print(f"\n性能測試結果:")
        print(f"  成功率: {success_count}/{test_count} ({success_count/test_count:.2%})")
        print(f"  總耗時: {total_time:.3f}秒")
        print(f"  RPS: {test_count/total_time:.2f}")
        print(f"  平均響應時間: {avg_time:.3f}秒")
        print(f"  P50響應時間: {p50:.3f}秒")
        print(f"  P95響應時間: {p95:.3f}秒")
        print(f"  P99響應時間: {p99:.3f}秒")
        
        return {
            'success_rate': success_count/test_count,
            'rps': test_count/total_time,
            'avg_response_time': avg_time,
            'p50_response_time': p50,
            'p95_response_time': p95,
            'p99_response_time': p99
        }
        
    except Exception as e:
        print(f"性能測試失敗: {e}")
        return None

if __name__ == "__main__":
    print("性能測試")
    print("="*50)
    
    result = asyncio.run(performance_test())
    
    if result:
        print("\n性能評估:")
        if result['p95_response_time'] < 0.5:
            print("✓ P95響應時間達標 (<500ms)")
        else:
            print("✗ P95響應時間未達標")
            
        if result['rps'] > 1000:
            print("✓ 吞吐量達標 (>1000 RPS)")
        else:
            print("✗ 吞吐量未達標")
            
        if result['success_rate'] > 0.99:
            print("✓ 成功率達標 (>99%)")
        else:
            print("✗ 成功率未達標")
```

### 3. 執行計劃

#### 階段1：環境診斷（1小時）
1. 檢查Python環境
2. 安裝缺失依賴
3. 啟動Redis服務
4. 驗證基礎導入

#### 階段2：組件測試（2小時）
1. 執行組件導入測試
2. 修復導入問題
3. 驗證組件實例化
4. 測試基礎功能

#### 階段3：功能測試（2小時）
1. 執行功能測試
2. 驗證核心功能
3. 測試錯誤處理
4. 記錄實際性能

#### 階段4：性能測試（3小時）
1. 執行性能測試
2. 收集真實數據
3. 對比理論值
4. 生成測試報告

### 4. 成功標準

#### 基礎成功
- 所有組件導入成功
- 基礎功能正常
- 無致命錯誤

#### 完整成功
- 所有測試通過
- 性能指標達標
- 數據與理論值匹配

#### 企業級成功
- 高負載測試通過
- 極端場景穩定
- 監控體系正常

## 風險評估

### 高風險
- Python環境無法修復
- 依賴包衝突
- Redis服務無法啟動

### 中風險
- 性能不達標
- 內存洩漏
- 並發問題

### 低風險
- 小功能缺陷
- 日誌格式問題
- 文檔不完整

## 應急方案

### 如果測試失敗
1. 記錄詳細錯誤信息
2. 分析失敗原因
3. 制定修復計劃
4. 重新執行測試

### 如果性能不達標
1. 識別瓶頸
2. 優化算法
3. 調整配置
4. 重新測試

## 執行時間表

- 第1天：環境診斷和修復
- 第2天：組件測試
- 第3天：功能測試
- 第4天：性能測試
- 第5天：報告生成

總計：5個工作日