# 測試超時策略

本文檔描述了專案中測試的超時策略和相關設置。

## 超時設置原則

1. **基本單元測試**：5秒超時
   - 簡單的功能測試
   - 無外部依賴的測試
   - 同步測試

2. **集成測試**：10秒超時
   - 涉及多個模組的測試
   - 有外部依賴的測試
   - 異步測試
   - 數據庫操作測試
   - 網絡請求測試

3. **性能測試**：30秒或更長
   - 壓力測試
   - 負載測試
   - 長時間運行的測試
   - 大數據量處理測試

## 自動化超時設置

專案中提供了自動化腳本 `scripts/add_pytest_timeouts.py` 來為測試文件添加超時設置：

```bash
# 為所有測試文件添加超時設置
python scripts/add_pytest_timeouts.py
```

腳本會根據文件路徑和名稱自動設置適當的超時時間：
- 位於 `integration` 目錄下的測試：10秒
- 位於 `performance` 目錄下的測試：30秒
- 其他測試：5秒

特殊文件的超時設置可以在腳本的 `SPECIAL_TIMEOUTS` 字典中配置。

## 如何添加超時

使用 `pytest-timeout` 插件為測試添加超時：

```python
import pytest

# 基本測試 - 5秒超時
@pytest.mark.timeout(5)
def test_basic_functionality():
    # 測試代碼
    pass

# 集成測試 - 10秒超時
@pytest.mark.timeout(10)
def test_integration():
    # 測試代碼
    pass

# 異步測試
@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_async_function():
    # 異步測試代碼
    pass
```

## 運行測試

### 基本命令

```bash
# 運行所有測試，啟用超時檢測
pytest --timeout=10 --timeout_method=thread

# 運行特定測試文件
pytest tests/core_ai/memory/test_ham_memory_manager.py --timeout=10

# 運行特定測試類或方法
pytest tests/core_ai/memory/test_ham_memory_manager.py::TestHAMMemoryManager::test_store_experience --timeout=5
```

### 在 CI/CD 中運行

在 GitHub Actions 或其他 CI/CD 環境中，建議設置更長的超時時間：

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install pytest-timeout
    pytest --timeout=30 --timeout_method=thread tests/
```

### 調試超時問題

如果測試超時，可以使用以下方法調試：

1. 增加超時時間：
   ```bash
   pytest --timeout=60 tests/slow_test.py
   ```

2. 顯示超時測試的堆棧跟蹤：
   ```bash
   pytest --timeout=10 --timeout_method=thread --timeout_debug
   ```

3. 跳過特定測試的超時：
   ```python
   @pytest.mark.timeout(None)  # 禁用超時
   def test_long_running():
       # 長時間運行的測試
       pass
   ```

## 測試設計最佳實踐

1. **保持測試獨立**：
   - 每個測試應該能夠獨立運行
   - 避免測試之間的依賴
   - 使用 `setup` 和 `teardown` 方法管理測試環境

2. **合理設置超時時間**：
   - 基本測試：5秒
   - 集成測試：10秒
   - 性能測試：30秒或更長

3. **處理外部依賴**：
   - 使用 mock 對象模擬外部服務
   - 考慮使用測試數據庫
   - 避免在測試中進行真實的網絡請求

4. **異步測試**：
   - 使用 `pytest-asyncio` 進行異步測試
   - 確保為異步測試設置足夠的超時時間
   - 使用 `asyncio` 的 `wait_for` 處理特定的超時邏輯

## 常見問題排查

### 測試超時

1. **問題**：測試經常超時
   **解決方案**：
   - 檢查是否有無限循環
   - 優化數據庫查詢
   - 增加超時時間（僅在必要時）

2. **問題**：異步測試卡住
   **解決方案**：
   - 確保所有異步操作都有適當的 `await`
   - 使用 `asyncio.wait_for` 設置超時
   - 檢查是否有未完成的協程

3. **問題**：CI 環境中超時
   **解決方案**：
   - 在 CI 配置中增加超時時間
   - 考慮將長時間運行的測試標記為 `@pytest.mark.slow` 並單獨運行
   - 優化測試數據和環境設置

## 維護與更新

1. **定期審查**：
   - 定期檢查測試的超時設置
   - 移除不必要的長時間超時
   - 更新過時的測試

2. **文檔**：
   - 在測試文件中添加註釋說明超時設置的原因
   - 記錄特殊的測試環境要求
   - 更新本文檔以反映當前的測試策略

3. **工具支持**：
   - 使用 `pytest-timeout` 插件管理超時
   - 考慮使用 `pytest-xdist` 進行並行測試
   - 使用 `pytest-cov` 檢查測試覆蓋率

## 參考資源

- [pytest-timeout 文檔](https://pypi.org/project/pytest-timeout/)
- [pytest-asyncio 文檔](https://pypi.org/project/pytest-asyncio/)
- [Python 測試最佳實踐](https://docs.pytest.org/en/stable/goodpractices.html)
- [異步測試指南](https://docs.pytest.org/en/stable/asyncio.html)
