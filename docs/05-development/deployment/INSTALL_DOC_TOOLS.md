# 文檔更新工具安裝指南

## 系統需求

- Windows 操作系統
- Python 3.6 或更高版本
- 管理員權限（用於創建桌面快捷方式）

## 快速安裝

### 方法一：使用安裝腳本（推薦）

1. 打開命令提示符或PowerShell
2. 導航到專案目錄
3. 執行以下命令之一：

```
# 使用命令提示符
tools\setup-doc-tools.bat

# 或使用PowerShell
.\tools\setup-doc-tools.ps1
```

安裝腳本將自動：
- 檢查Python環境
- 安裝必要的Python套件
- 驗證文檔更新工具腳本
- 運行測試確保功能正常
- 創建桌面快捷方式

### 方法二：手動安裝

如果您偏好手動安裝，請按照以下步驟操作：

1. 確保已安裝Python 3.6或更高版本
2. 安裝必要的Python套件：
   ```
   pip install pyyaml colorama tqdm
   ```
3. 確認以下文件存在：
   - `scripts/document_update_plan.py`
   - `scripts/update_doc_status.py`
   - `tools/update-docs.bat`（或`tools/update-docs.ps1`）
   - `DOCUMENT_UPDATE_GUIDE.md`

## 啟動文檔更新工具

安裝完成後，您可以通過以下方式啟動文檔更新工具：

1. 雙擊桌面上的「文檔更新工具」快捷方式
2. 在專案根目錄執行：
   ```
   update-docs.bat  # 或 .\update-docs.ps1
   ```
3. 在tools目錄執行：
   ```
   update-docs.bat  # 或 .\update-docs.ps1
   ```

## 驗證安裝

要驗證文檔更新工具是否正確安裝，您可以運行測試腳本：

```
# 使用命令提示符
tools\test-doc-tools.bat

# 或使用PowerShell
.\tools\test-doc-tools.ps1
```

如果測試成功完成，則表示文檔更新工具已正確安裝並可以使用。

## 故障排除

### Python未找到

如果安裝腳本報告「未找到Python環境」，請確保：

1. Python已正確安裝
2. Python已添加到系統PATH環境變量
3. 重新打開命令提示符或PowerShell後再試

### 套件安裝失敗

如果Python套件安裝失敗，請嘗試：

1. 手動安裝必要的套件：
   ```
   pip install --upgrade pip
   pip install pyyaml colorama tqdm
   ```
2. 檢查網絡連接
3. 如果使用公司網絡，可能需要設置代理

### 腳本未找到

如果安裝腳本報告「未找到文檔更新計畫腳本」或「未找到文檔狀態管理腳本」，請確保：

1. 您在正確的專案目錄中運行安裝腳本
2. 所有必要的文件都已存在於正確的位置

## 更多信息

有關文檔更新工具的詳細使用說明，請參考：

- `DOCUMENT_UPDATE_GUIDE.md`：文檔更新流程和最佳實踐
- `tools/README_DOC_TOOLS.md`：工具功能和技術細節

如有其他問題，請聯繫專案管理員或技術支持團隊。