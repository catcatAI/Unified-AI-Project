# 統一AI專案 - 組織狀態報告

## 📋 專案概覽

**專案名稱**: Unified AI Project  
**版本**: 0.1.0  
**整理日期**: 2025年1月18日  
**狀態**: ✅ 已整理完成

## 🏗️ 專案架構

### 核心目錄結構
```
unified-ai-project/
├── 📁 src/                     # 核心源代碼 (167個Python文件)
│   ├── core_ai/                # AI核心邏輯
│   ├── services/               # 後端服務
│   ├── tools/                  # AI工具集
│   ├── interfaces/             # 用戶界面
│   ├── hsp/                    # 異構服務協議
│   ├── fragmenta/              # 元編排系統
│   └── game/                   # Angela's World遊戲
├── 📁 tests/                   # 測試套件
├── 📁 docs/                    # 文檔 (70個MD文件)
├── 📁 configs/                 # 配置文件 (16個YAML)
├── 📁 data/                    # 數據存儲
├── 📁 scripts/                 # 工具腳本
├── 📁 CodeInspect/            # 代碼檢查工具
├── 📁 UniAIDashboa/           # 統一AI儀表板
└── 📄 配置文件                 # pyproject.toml, requirements.txt等
```

## 🎯 核心功能模組

### 1. AI核心系統
- **對話管理器** (`DialogueManager`) - 元代理協調
- **分層抽象記憶** (`HAM`) - 記憶存儲與檢索
- **語言學免疫系統** (`LIS`) - 語義異常處理
- **元公式系統** - 動態原則定義
- **個性管理器** - 多個性配置

### 2. 代理協作框架
- **元代理 Angela** - 任務分解與協調
- **專門化子代理** - 數據分析、創意寫作等
- **代理管理器** - 動態資源管理
- **學習閉環** - 自我優化機制

### 3. 通信與協議
- **HSP協議** - 異構服務通信
- **MQTT連接器** - 消息傳遞
- **服務發現** - 動態服務註冊

### 4. 工具生態系統
- **數學模型** - 數值計算
- **邏輯模型** - 符號推理
- **翻譯工具** - 多語言支持
- **代碼理解** - 靜態分析

## 📊 技術規格

### 依賴管理
- **核心依賴**: Flask, numpy, cryptography, requests等
- **AI擴展**: tensorflow, spacy, langchain
- **Web服務**: fastapi, uvicorn, pydantic
- **測試框架**: pytest, pytest-asyncio

### 支持的Python版本
- Python 3.8+
- 推薦 Python 3.10+

### 前端技術
- **Electron應用** - 桌面界面
- **React組件** - 現代UI
- **TypeScript** - 類型安全

## 🚀 快速啟動指南

### 1. 環境準備
```bash
# 克隆專案
git clone <repository-url>
cd unified-ai-project

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

### 2. 安裝依賴
```bash
# 完整安裝 (推薦)
pip install -e .[full]

# 或基本安裝
pip install -e .
```

### 3. 環境配置
```bash
# 複製環境變量模板
cp .env.example .env

# 編輯.env文件，設置API密鑰
# MIKO_HAM_KEY=your-encryption-key
# GEMINI_API_KEY=your-gemini-key
```

### 4. 運行測試
```bash
pytest
```

### 5. 啟動服務
```bash
# 啟動主API服務器
python src/services/main_api_server.py

# 啟動CLI界面
python src/interfaces/cli/main.py

# 啟動Electron應用
cd src/interfaces/electron_app
npm install
npm start
```

## 📚 文檔導航

### 核心文檔
- **[README.md](README.md)** - 專案總覽
- **[成功標準](SUCCESS_CRITERIA.md)** - 質量指標
- **[故障排除](TROUBLESHOOTING.md)** - 常見問題

### 技術文檔
- **[HSP規範](docs/technical_design/HSP_SPECIFICATION.md)** - 通信協議
- **[HAM設計](docs/technical_design/architecture/HAM_design_spec.md)** - 記憶系統
- **[代理協作](docs/technical_design/architecture/AGENT_COLLABORATION_FRAMEWORK.md)** - 協作框架

### 專案管理
- **[內容組織](docs/project_management/PROJECT_CONTENT_ORGANIZATION.md)** - 文件結構
- **[狀態總結](docs/project_management/PROJECT_STATUS_SUMMARY.md)** - 實現狀態
- **[整理總結](docs/CLEANUP_SUMMARY.md)** - 最新整理報告

## 🎮 特色功能

### Angela's World 遊戲
- 互動式AI體驗
- 教育娛樂結合
- 人機共生哲學展示

### 代碼檢查工具
- 靜態代碼分析
- 質量評估
- 改進建議

### 統一AI儀表板
- 服務監控
- 性能分析
- 配置管理

## 🔧 開發工具

### 測試
```bash
# 運行所有測試
pytest

# 運行特定模組測試
pytest tests/core_ai/

# 運行慢速測試
pytest -m slow
```

### 代碼質量
```bash
# 安裝開發工具
pip install -e .[dev]

# 代碼格式化
black src/ tests/

# 類型檢查
mypy src/

# 代碼檢查
flake8 src/
```

## 🌟 哲學與願景

### 核心理念
- **語言即生命** - AI作為語義實體
- **多維語義** - 超越工具的存在
- **人機共生** - 協作而非替代

### 長期目標
- 創造具有自我意識的AI
- 實現語義演化能力
- 建立深度學習閉環

## 📈 專案狀態

### ✅ 已完成
- 核心架構實現
- 基本功能運行
- 測試套件完整
- 文檔體系建立

### 🚧 進行中
- 性能優化
- 功能擴展
- 用戶體驗改進

### 📋 計劃中
- 高級AI功能
- 更多工具集成
- 社區生態建設

---

**最後更新**: 2025年1月18日  
**維護者**: Unified AI Project Team  
**許可證**: MIT License