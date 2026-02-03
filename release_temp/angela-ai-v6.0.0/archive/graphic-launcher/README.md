# Unified AI Project 圖形化啟動器

這是一個為 Unified-AI-Project 項目開發的圖形化啟動器/安裝器，提供直觀易用的圖形界面來訪問項目的所有功能。

## 功能特性

- **環境管理**: 檢查和設置開發環境
- **開發工具**: 啟動後端服務、前端儀表板和桌面應用
- **測試管理**: 執行各種測試套件
- **Git工具**: Git狀態檢查和清理
- **訓練管理**: AI模型訓練設置和管理
- **CLI工具**: 訪問Unified AI CLI工具
- **模型管理**: AI模型狀態檢查和管理
- **數據工具**: 數據分析和處理流水線
- **系統工具**: 系統信息查看和維護工具

## 技術棧

- **Electron**: 桌面應用框架
- **React**: 用戶界面庫
- **Node.js**: 運行時環境

## 安裝和運行

1. 確保已安裝 Node.js 和 npm
2. 在項目根目錄下運行以下命令：

```bash
npm install
```

3. 啟動應用：

```bash
npm start
```

## 開發

### 目錄結構

```
graphic-launcher/
├── main/                 # 主進程代碼
│   ├── main.js           # 主進程入口
│   ├── preload.js        # 預加載腳本
│   ├── ipc-handlers.js   # IPC 處理器
│   └── logger.js         # 日誌記錄器
├── renderer/             # 渲染進程代碼
│   ├── src/              # React 源碼
│   │   ├── components/   # UI 組件
│   │   ├── pages/        # 頁面組件
│   │   ├── App.js        # 主應用組件
│   │   ├── index.js      # 入口文件
│   │   └── index.css     # 樣式文件
│   └── public/           # 靜態資源
├── package.json          # 項目配置文件
└── README.md             # 項目說明文件
```

### 構建應用

```bash
npm run build
```

## 貢獻

歡迎提交 Issue 和 Pull Request 來改進這個項目。

## 許可證

MIT