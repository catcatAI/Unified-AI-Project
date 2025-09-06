# Unified AI Project 統一執行指南

## 📋 概述

本指南提供了 Unified AI Project 的統一執行方法，包括腳本整合、CLI工具、圖形啟動器等的使用說明。

## 🚀 快速開始

### 主要執行入口

1. **人類用戶**: `unified-ai.bat` - 圖形化菜單界面
2. **AI代理**: `ai-runner.bat` - 命令行自動化工具
3. **統一CLI**: `tools\core\unified-cli.bat` - 統一命令行工具
4. **圖形啟動器**: `graphic-launcher` - Electron桌面應用

## 📁 腳本架構

### 新的腳本組織結構

```
tools/
├── core/                    # 核心腳本
│   ├── health-check.bat     # 健康檢查
│   ├── start-dev.bat        # 啟動開發環境
│   ├── run-tests.bat        # 運行測試
│   └── unified-cli.bat      # 統一CLI工具
├── training/                # 訓練腳本
│   ├── setup-training.bat   # 訓練設置
│   └── train-manager.bat    # 訓練管理
├── maintenance/             # 維護腳本
│   ├── git-cleanup.bat      # Git清理
│   └── fix-deps.bat         # 依賴修復
└── utilities/               # 實用工具
    └── backup.bat           # 備份管理
```

## 🛠️ 統一腳本功能

### 1. 測試腳本 (`tools/core/run-tests.bat`)

**功能**: 統一的測試執行工具，支持多種測試模式

**使用方法**:
```bash
# 運行所有測試
run-tests.bat --all --verbose

# 運行單元測試
run-tests.bat --unit --coverage

# 運行整合測試
run-tests.bat --integration --parallel

# 運行端到端測試
run-tests.bat --e2e --verbose
```

**選項**:
- `--unit`: 只運行單元測試
- `--integration`: 只運行整合測試
- `--e2e`: 只運行端到端測試
- `--all`: 運行所有測試 (默認)
- `--verbose`: 詳細輸出
- `--coverage`: 生成覆蓋率報告
- `--parallel`: 並行運行測試

### 2. 依賴修復腳本 (`tools/maintenance/fix-deps.bat`)

**功能**: 統一的依賴修復工具，支持Python和Node.js依賴

**使用方法**:
```bash
# 修復所有依賴
fix-deps.bat --all --verbose

# 只修復Python依賴
fix-deps.bat --python --force

# 只修復Node.js依賴
fix-deps.bat --node --verbose

# 重新創建虛擬環境
fix-deps.bat --all --recreate-venv
```

**選項**:
- `--python`: 只修復Python依賴
- `--node`: 只修復Node.js依賴
- `--all`: 修復所有依賴 (默認)
- `--force`: 強制重新安裝所有包
- `--verbose`: 詳細輸出
- `--recreate-venv`: 重新創建虛擬環境

### 3. 備份腳本 (`tools/utilities/backup.bat`)

**功能**: 統一的備份管理工具，支持多種備份模式

**使用方法**:
```bash
# 創建完整備份
backup.bat --full --compress

# 創建增量備份
backup.bat --incremental --name daily_backup

# 只備份配置文件
backup.bat --config --no-compress

# 只備份數據文件
backup.bat --data --include-logs
```

**選項**:
- `--full`: 完整備份 (默認)
- `--incremental`: 增量備份
- `--config`: 只備份配置文件
- `--data`: 只備份數據文件
- `--compress`: 壓縮備份 (默認)
- `--no-compress`: 不壓縮備份
- `--include-logs`: 包含日誌文件
- `--include-node-modules`: 包含node_modules
- `--name NAME`: 指定備份名稱

### 4. Git清理腳本 (`tools/maintenance/git-cleanup.bat`)

**功能**: 統一的Git管理工具，支持多種Git操作

**使用方法**:
```bash
# 顯示Git狀態
git-cleanup.bat --status

# 清理未跟踪文件
git-cleanup.bat --clean --force

# 修復Git 10K+文件問題
git-cleanup.bat --fix-10k --verbose

# 緊急恢復
git-cleanup.bat --emergency --force
```

**選項**:
- `--status`: 顯示Git狀態 (默認)
- `--clean`: 清理未跟踪文件
- `--reset`: 重置倉庫到HEAD
- `--stash`: 暫存未提交的更改
- `--fix-10k`: 修復Git 10K+文件問題
- `--emergency`: 緊急恢復
- `--force`: 強制操作
- `--verbose`: 詳細輸出
- `--no-backup`: 不創建備份

## 🖥️ 統一CLI工具

### 使用方法

```bash
# 交互式菜單
tools\core\unified-cli.bat

# 直接命令
tools\core\unified-cli.bat health
tools\core\unified-cli.bat dev start
tools\core\unified-cli.bat train setup
tools\core\unified-cli.bat git status
tools\core\unified-cli.bat backup --compress
```

### 可用命令

#### 1. 健康檢查 (`health`)
```bash
unified-cli.bat health
```
檢查系統健康狀態，包括Python、Node.js、依賴等。

#### 2. 開發工具 (`dev`)
```bash
unified-cli.bat dev start    # 啟動開發環境
unified-cli.bat dev stop     # 停止開發環境
unified-cli.bat dev test     # 運行測試
unified-cli.bat dev build    # 構建項目
```

#### 3. 訓練管理 (`train`)
```bash
unified-cli.bat train setup  # 設置訓練環境
unified-cli.bat train start  # 開始訓練
unified-cli.bat train stop   # 停止訓練
unified-cli.bat train status # 顯示訓練狀態
```

#### 4. 數據管理 (`data`)
```bash
unified-cli.bat data process  # 處理數據
unified-cli.bat data analyze  # 分析數據
unified-cli.bat data backup   # 備份數據
unified-cli.bat data restore  # 恢復數據
```

#### 5. 模型管理 (`model`)
```bash
unified-cli.bat model list    # 列出模型
unified-cli.bat model info    # 模型信息
unified-cli.bat model train   # 訓練模型
```

#### 6. Git操作 (`git`)
```bash
unified-cli.bat git status    # Git狀態
unified-cli.bat git clean     # 清理Git
unified-cli.bat git fix       # 修復Git問題
unified-cli.bat git emergency # 緊急恢復
```

#### 7. 備份管理 (`backup`)
```bash
unified-cli.bat backup        # 創建備份
```

#### 8. 系統信息 (`system`)
```bash
unified-cli.bat system        # 顯示系統信息
```

## 🎯 主要管理工具

### 1. 統一管理工具 (`unified-ai.bat`)

**功能**: 人類用戶的主要管理界面

**新增功能**:
- 整合了新的統一腳本
- 改進了Git管理選項
- 增強了錯誤處理
- 支持向後兼容

**菜單選項**:
1. 健康檢查 - 檢查開發環境
2. 環境設置 - 安裝依賴和設置
3. 啟動開發 - 啟動開發服務器
4. 運行測試 - 執行測試套件
5. Git管理 - Git狀態和清理 (新增多個選項)
6. 訓練設置 - 準備AI訓練
7. 訓練管理 - 管理訓練數據和過程
8. CLI工具 - 訪問Unified AI CLI工具
9. 模型管理 - 管理AI模型和DNA鏈
10. 數據分析 - 分析項目數據和統計
11. 數據流水線 - 運行自動化數據處理流水線
12. 緊急Git修復 - 從Git問題中恢復
13. 修復依賴 - 解決依賴問題
14. 系統信息 - 顯示系統信息
15. 退出

### 2. AI代理工具 (`ai-runner.bat`)

**功能**: AI代理的自動化工具

**命令**:
- `setup` - 設置開發環境
- `start` - 啟動開發服務器
- `test` - 運行測試
- `train` - 設置訓練環境
- `health` - 運行健康檢查
- `clean` - 清理git狀態

## 🖼️ 圖形啟動器

### 啟動方法
```bash
cd graphic-launcher
npm start
```

### 功能模塊
1. **儀表板** - 系統狀態總覽
2. **開發工具** - 一鍵啟動開發環境
3. **訓練管理** - 圖形化訓練控制
4. **數據工具** - 數據處理和可視化
5. **系統監控** - 實時性能監控
6. **日誌查看** - 統一日誌查看器

## 📊 日誌系統

### 統一日誌格式
```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [SCRIPT] [FUNCTION] MESSAGE
```

### 日誌文件位置
- 主日誌: `logs/unified-ai.log`
- 測試日誌: `logs/test-runner.log`
- 依賴修復日誌: `logs/fix-deps.log`
- Git清理日誌: `logs/git-cleanup.log`
- 備份日誌: `logs/backup.log`
- CLI日誌: `logs/unified-cli.log`

## ⚙️ 配置管理

### 環境變量
```bash
UNIFIED_AI_ROOT          # 專案根目錄
UNIFIED_AI_CONFIG        # 配置文件路徑
UNIFIED_AI_LOG_LEVEL     # 日誌級別
UNIFIED_AI_BACKEND_URL   # 後端URL
UNIFIED_AI_FRONTEND_URL  # 前端URL
```

### 配置文件
- 主配置: `unified-ai-config.yaml` (計劃中)
- 測試配置: `pytest.ini`
- 日誌配置: `logging.yaml` (計劃中)

## 🔧 故障排除

### 常見問題

1. **腳本找不到**
   - 檢查腳本路徑是否正確
   - 確保在專案根目錄執行

2. **權限問題**
   - 以管理員身份運行
   - 檢查文件權限

3. **依賴問題**
   - 運行 `fix-deps.bat --all --force`
   - 檢查Python和Node.js版本

4. **Git問題**
   - 運行 `git-cleanup.bat --fix-10k`
   - 檢查.gitignore文件

### 錯誤代碼
- `0` - 成功
- `1` - 一般錯誤
- `2` - 參數錯誤
- `3` - 文件不存在
- `4` - 權限錯誤
- `5` - 網絡錯誤
- `6` - 依賴錯誤
- `7` - 配置錯誤
- `8` - 系統錯誤
- `9` - 未知錯誤

## 📈 性能優化

### 腳本優化
- 使用統一的錯誤處理
- 優化日誌記錄
- 減少重複代碼
- 改進參數解析

### 執行優化
- 並行執行測試
- 增量備份
- 智能依賴檢查
- 緩存機制

## 🔄 向後兼容

### 舊腳本支持
- 保持舊腳本可用
- 逐步遷移到新腳本
- 提供遷移指南
- 維護兼容性

### 遷移計劃
1. **階段1**: 創建新腳本結構
2. **階段2**: 更新主管理工具
3. **階段3**: 遷移現有腳本
4. **階段4**: 清理舊腳本

## 📚 相關文檔

- [README.md](README.md) - 專案主要說明
- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - 專案全貌
- [SIMPLE_GUIDE.md](SIMPLE_GUIDE.md) - 簡化使用指南
- [CLI_USAGE_GUIDE.md](docs/CLI_USAGE_GUIDE.md) - CLI使用指南
- [BATCH_SCRIPTS_USAGE_GUIDE.md](docs/BATCH_SCRIPTS_USAGE_GUIDE.md) - 批處理腳本指南

## 🆕 更新日誌

### v1.0.1 (2025-09-06)
- 創建統一的腳本架構
- 整合重複功能腳本
- 統一參數和選項格式
- 改進錯誤處理和日誌記錄
- 創建統一CLI工具
- 更新主管理工具
- 建立統一的執行指南

---

**最後更新**: 2025年9月6日  
**版本**: 1.0.1  
**維護者**: Unified AI Project Team
