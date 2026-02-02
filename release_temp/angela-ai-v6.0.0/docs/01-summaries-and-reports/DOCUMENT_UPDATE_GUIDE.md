# 專案文件更新指南

## 概述

本指南提供了系統化的專案文件更新計畫，旨在確保代碼與文檔的同步更新，提高專案的可維護性和可理解性。

## 文件更新流程

### 1. 識別與收集階段

- 使用 `document_update_plan.py` 腳本掃描整個專案目錄
- 自動建立完整的檔案清單與路徑映射表
- 標記所有代碼檔案與對應的MD文檔

```bash
python scripts/document_update_plan.py
```

執行後將生成：
- `doc_update_status.json`：文檔更新狀態追蹤文件
- `doc_update_plan.json`：文檔更新計畫
- `doc_update_report.md`：文檔更新報告

### 2. 分組配對作業

腳本會自動：
- 將代碼檔案與相關MD文檔建立關聯組
- 為每組建立更新任務項
- 按目錄結構組織文檔更新任務

### 3. 內容更新流程

對於每個需要更新的文檔，請遵循以下步驟：

1. **分析代碼現狀**
   - 檢查關聯代碼文件的功能、結構和依賴關係
   - 理解代碼的設計意圖和實現方式

2. **比對MD現有內容**
   - 檢查現有文檔是否準確反映代碼實際情況
   - 標記需要更新的部分

3. **更新MD文檔**
   - 更新代碼現況說明
   - 補充設計目標與未來規劃
   - 完善重要接口與功能描述
   - 添加使用示例和注意事項

### 4. 文件規範審查

- 檢查MD存放路徑是否符合現行規範
  - 模組文檔應與代碼位於同一目錄
  - 通用文檔應位於專案根目錄或 `docs/` 目錄
- 必要時調整文件存放結構
- 統一文件格式標準

### 5. 進度管理

- 使用 `doc_update_status.json` 追蹤更新狀態
- 更新文檔後，手動更新狀態：
  - 待更新 → 更新中 → 已更新
  - 必要時標記為「需審查」或「無需更新」
- 定期執行腳本重新生成報告，檢視整體進度

### 6. 最終整理

- 校驗所有MD內容完整性
- 確保代碼與文檔版本一致性
- 生成最終更新報告摘要

## 文檔模板

以下是推薦的文檔模板結構：

```markdown
# 模組名稱

## 概述
[在此描述此模組的主要功能和用途]

## 功能特性
- [功能點1]
- [功能點2]
- [功能點3]

## 相關代碼文件
- `path/to/file1.py`
- `path/to/file2.py`

## 主要接口
```python
# 示例代碼
def example_function(param1, param2):
    """函數說明"""
    # 實現細節
    pass
```

## 使用示例
```python
# 使用示例代碼
```

## 依賴關係
- [依賴項1]
- [依賴項2]

## 未來規劃
- [規劃項1]
- [規劃項2]

## 注意事項
- [注意事項1]
- [注意事項2]
```

## 最佳實踐

1. **保持同步更新**：代碼變更時立即更新相關文檔
2. **清晰簡潔**：使用簡潔明了的語言描述功能和用途
3. **提供示例**：為關鍵功能提供使用示例
4. **標記TODO**：對於未完成的部分使用TODO標記
5. **定期審查**：定期審查文檔內容，確保準確性
6. **版本一致**：確保文檔描述的功能與當前代碼版本一致

## 自動化腳本使用說明

### 初始掃描

```bash
python scripts/document_update_plan.py
```

### 查看更新報告

生成的報告位於專案根目錄：`doc_update_report.md`

### 更新狀態

可以直接編輯 `doc_update_status.json` 文件更新狀態，或開發額外的工具輔助狀態更新。

## 命令行用法示例（非互動）

以下操作基於腳本 `scripts/update_doc_status.py` 與狀態檔 `doc_update_status.json`：

- 列出待更新文檔（可加上目錄過濾）：
  ```bash
  python scripts/update_doc_status.py list --status 待更新
  python scripts/update_doc_status.py list --status 待更新 --dir apps/backend
  ```

- 查看特定文檔詳細資訊：
  ```bash
  python scripts/update_doc_status.py show PROJECT_OVERVIEW.md
  ```

- 標記文檔為已更新並附註：
  ```bash
  python scripts/update_doc_status.py update PROJECT_OVERVIEW.md 已更新 --notes "目錄結構與依賴關係已同步至代碼現狀"
  python scripts/update_doc_status.py update tools/README_DOC_TOOLS.md 已更新 --notes "修正狀態檔名，補充命令行示例"
  ```

- 生成 Markdown 報告（輸出至根目錄 `doc_update_report.md`）：
  ```bash
  python scripts/update_doc_status.py report
  ```