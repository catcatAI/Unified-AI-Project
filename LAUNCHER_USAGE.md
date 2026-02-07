# Angela AI 啟動器使用說明

## 問題：啟動時出現多個終端窗口

### 原因
之前的 `run_angela.py` 在啟動桌面應用時總是創建新的控制台窗口，導致：
- 後端 API 在一個終端運行
- Desktop App 在另一個終端運行
- 可能還有其他子進程的終端

### 解決方案
已修復 `run_angela.py`，現在根據運行模式決定是否創建新終端：

#### User 模式（默認）
```bash
python run_angela.py --mode user
# 或
AngelaLauncher.bat
```
- ✅ 後端在當前終端運行
- ✅ Desktop App 在後台運行（無新終端）
- ✅ 只有一個終端窗口

#### Dev 模式（開發者）
```bash
python run_angela.py --mode dev
```
- ✅ 後端在新終端運行
- ✅ Desktop App 在新終端運行
- ✅ 方便調試，可以看到所有日誌

## 啟動選項

### 完整啟動（默認）
```bash
python run_angela.py
```
啟動後端 + 桌面應用

### 只啟動後端
```bash
python run_angela.py --api-only
```

### 只啟動桌面應用
```bash
python run_angela.py --desktop-only
```

### 創建桌面快捷方式
```bash
python run_angela.py --install-shortcut
```

## 關閉 Angela

按 `Ctrl+C` 在啟動器終端中，會自動關閉所有子進程。

## 技術細節

### 修改內容
- **Line 121**: 添加 `subprocess.CREATE_NO_WINDOW` 標誌（user 模式）
- **Line 121**: 保留 `subprocess.CREATE_NEW_CONSOLE`（dev 模式）

### Windows 進程創建標誌
- `CREATE_NEW_CONSOLE`: 創建新的控制台窗口
- `CREATE_NO_WINDOW`: 在後台運行，不創建窗口
- `0`: 繼承父進程的控制台
