# Enhanced Sandbox Executor (增強型沙盒執行器)

## 總覽 (Overview)

`EnhancedSandboxExecutor` 是 Unified AI 系統中一個關鍵的安全元件。其核心職責是提供一個高度隔離且受嚴格控制的環境，用於執行由 AI 動態產生或來自不受信任來源的 Python 程式碼。這使得系統可以在不危及主應用程式或主機安全的情況下，利用動態程式碼來擴展其能力。

## 核心安全機制 (Core Security Mechanisms)

此沙盒採用了多層防禦策略來確保執行安全：

1.  **行程隔離 (Process Isolation)**:
    - 每一段程式碼都在一個完全獨立的子行程 (subprocess) 中執行。這確保了沙盒內的程式碼無法存取主應用程式的記憶體空間、變數或物件。

2.  **資源限制 (`ResourceMonitor`)**:
    - 一個獨立的監控執行緒會即時追蹤沙盒行程的資源使用情況，包括 CPU 佔用率、記憶體用量和總執行時間。
    - 如果任何一項資源超出預設限制（例如，CPU 超過 50%，記憶體超過 256MB），監控器會立即終止該沙盒行程，有效防止阻斷服務攻擊（如無限迴圈、記憶體炸彈）。

3.  **權限控制 (`PermissionControlSystem`)**:
    - 在執行任何程式碼之前，沙盒會呼叫 `PermissionControlSystem` 來驗證發起操作的使用者或代理是否具有 `SANDBOX_EXECUTION` 權限。

4.  **靜態程式碼分析 (`_validate_code`)**:
    - 在執行前，沙盒會對傳入的程式碼字串進行靜態掃描，使用正規表示式來偵測並拒絕包含危險模組（如 `os`, `sys`, `subprocess`）或危險模式（如 `open()`, `eval()`）的程式碼。

5.  **危險內建函式禁用**: 
    - 沙盒的執行器範本 (`ENHANCED_SANDBOX_RUNNER_TEMPLATE`) 在執行使用者程式碼之前，會先從 Python 的 `builtins` 模組中移除一系列高風險函式，例如 `exec`, `eval`, `open`, `__import__` 等。這從根本上杜絕了許多常見的攻擊向量。

6.  **檔案系統存取限制**:
    - 可透過 `SandboxConfig` 設定允許或禁止存取的檔案路徑，將程式碼的活動範圍限制在安全的暫存目錄內。

7.  **全面審計 (`AuditLogger`)**:
    - 所有沙盒操作，包括權限檢查、執行嘗試、成功、失敗以及任何安全違規，都會被 `AuditLogger` 詳細記錄，以便進行後續的安全分析和追蹤。

## 執行工作流程 (Execution Workflow)

1.  **接收請求**: `EnhancedSandboxExecutor.execute()` 接收到包含程式碼、使用者ID、類別/方法名稱和參數的請求。
2.  **權限檢查**: 呼叫 `PermissionControlSystem` 驗證權限。如果失敗，則拒絕執行並記錄日誌。
3.  **程式碼驗證**: 呼叫 `_validate_code()` 對程式碼進行靜態分析。如果發現危險模式，則拒絕執行。
4.  **建立沙盒環境**: 
    - 系統建立一個暫存目錄。
    - 將使用者程式碼寫入一個暫存檔案 (`_sandboxed_tool.py`)。
    - 將沙盒執行器範本 (`ENHANCED_SANDBOX_RUNNER_TEMPLATE`) 寫入另一個暫存檔案。
5.  **啟動子行程**: 
    - 系統啟動一個新的子行程來執行沙盒執行器範本，並將使用者程式碼的路徑和參數作為命令列引數傳遞。
    - `ResourceMonitor` 同步啟動，開始監控此子行程。
6.  **等待與通訊**: 主行程等待子行程完成，並設定超時。子行程的執行結果（或錯誤）透過 `stdout` 以 JSON 格式返回。
7.  **結果處理**: 主行程解析子行程的輸出，取得結果或錯誤訊息。
8.  **記錄與返回**: `AuditLogger` 記錄最終執行結果，並將結果或錯誤返回給呼叫者。

## 使用範例 (Usage Example)

```python
# sandbox_executor 是一個 EnhancedSandboxExecutor 的實例

user_code = """
class MyTool:
    def run(self, numbers):
        # 此程式碼將在沙盒中執行
        return sum(numbers)
"""

result, error = sandbox_executor.execute(
    user_id="agent_alpha_007",
    code_string=user_code,
    class_name="MyTool",
    method_name="run",
    method_params={"numbers": [10, 20, 30]}
)

if error:
    print(f"沙盒執行失敗: {error}")
else:
    print(f"沙盒執行成功，結果: {result}")
```
