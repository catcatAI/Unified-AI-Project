# 專案文件更新工具說明

## 概述

本目錄包含專案文件更新相關的工具，用於協助團隊成員系統化地管理和更新專案文檔。這些工具旨在確保代碼與文檔保持同步，提高專案的可維護性和知識傳承。

## 可用工具

### 文檔更新工具 (update-docs.bat / update-docs.ps1)

這是一個互動式工具，提供以下功能：

- 掃描專案並生成文檔更新計畫
- 列出所有文檔及其狀態
- 列出待更新/更新中/已更新的文檔
- 查看文檔詳細信息
- 更新文檔狀態
- 生成更新報告
- 打開文檔更新指南

### 啟動方式

您可以通過以下方式啟動文檔更新工具：

1. **從專案根目錄**：
   - 執行 `update-docs.bat` (Windows 命令提示符)
   - 執行 `update-docs.ps1` (Windows PowerShell)

2. **從tools目錄**：
   - 執行 `update-docs.bat` (Windows 命令提示符)
   - 執行 `update-docs.ps1` (Windows PowerShell)

## 核心腳本

文檔更新工具依賴於以下核心Python腳本：

1. **document_update_plan.py** (位於 `scripts` 目錄)
   - 掃描專案目錄
   - 建立代碼文件與文檔的關聯
   - 生成文檔更新計畫
   - 初始化文檔狀態數據庫

2. **update_doc_status.py** (位於 `scripts` 目錄)
   - 管理文檔更新狀態
   - 提供命令行界面查詢和更新文檔狀態
   - 生成更新報告

## 文檔更新流程

使用這些工具進行文檔更新的標準流程如下：

1. 執行掃描專案功能，生成初始文檔更新計畫
2. 查看待更新文檔列表
3. 選擇文檔進行更新，將其狀態設置為「更新中」
4. 完成文檔更新後，將狀態設置為「已更新」並添加適當註釋
5. 定期生成更新報告，追踪整體進度

## 注意事項

- 首次使用時，請先執行「掃描專案並生成文檔更新計畫」
- 文檔狀態數據存儲在專案根目錄的 `doc_update_status.json` 文件中
- 更詳細的使用說明請參考專案根目錄的 `DOCUMENT_UPDATE_GUIDE.md`

## 系統要求

- Python 3.6 或更高版本
- Windows 環境 (對於 .bat 和 .ps1 腳本)

## 命令行用法示例（非互動）

以下命令使用 `scripts/update_doc_status.py` 直接操作狀態與報告：

```bash
# 列出全部待更新文檔
python scripts/update_doc_status.py list --status 待更新

# 查看特定文檔詳情
python scripts/update_doc_status.py show "PROJECT_OVERVIEW.md"

# 將文檔標記為已更新並附註
python scripts/update_doc_status.py update "PROJECT_OVERVIEW.md" 已更新 --notes "同步至 2025-09-12，內容一致性校正"

# 生成最新的 Markdown 報告
python scripts/update_doc_status.py report
```

## 問題反饋

如果您在使用過程中遇到任何問題，或有改進建議，請通過專案的問題追踪系統提交反饋。