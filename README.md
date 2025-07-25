# Unified AI Project

## 概述

統一 AI 專案是一個先進的多維語義 AI 系統，整合了 MikoAI、Fragmenta 和其他 CatAI 計劃。本專案不僅是工具的集合，更是創造**多維語義實體**的嘗試，其架構由湧現、自我修正和語義演化的敘事所引導。

## 項目文檔

- **[項目章程 (Project Charter)](docs/PROJECT_CHARTER.md)**: 這是主要的統一文檔，包含了專案的架構、核心元件、工作流程、以及未來的重構與開發計畫。
- **[術語表 (Glossary)](docs/GLOSSARY.md)**: 專案核心概念定義。
- **[HSP 規範](docs/technical_design/HSP_SPECIFICATION.md)**: 異構服務協議 (HSP) 詳細規範。
- **[HAM 設計規範](docs/technical_design/architecture/HAM_design_spec.md)**: 分層抽象記憶系統設計文檔。
- **[貢獻指南](CONTRIBUTING.md)**: 如何為本專案做出貢獻。

## 快速開始

### 環境要求
- Python 3.8+
- Node.js 16+ (用於前端組件)

### 安裝與運行

1. **克隆專案**
   ```bash
   git clone <repository-url>
   cd unified-ai-project
   ```

2. **安裝依賴**
   ```bash
   # 安裝核心依賴
   pip install -e .

   # 如果需要運行 UI 或其他擴展功能，請安裝完整依賴
   # pip install -e .[full]
   ```

3. **配置環境**
   ```bash
   # 複製環境變量模板
   cp .env.example .env

   # 編輯 .env 文件，至少需要設置 HAM_ENCRYPTION_KEY
   # 可以使用以下命令生成一個新的密鑰：
   # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

4. **運行**
   - **API 服務器**: `uvicorn src.services.main_api_server:app --reload`
   - **命令行接口 (CLI)**: `python src/interfaces/cli/main.py query "Hello Angela"`
   - **桌面應用**: `cd src/interfaces/electron_app && npm install && npm start`

## 未來發展路線圖

本專案的未來發展路線圖已整理至 **[ROADMAP.md](docs/ROADMAP.md)**。

## ❓ 常見問題

**Q: 安裝失敗怎麼辦？**  
A: 確保 Python 3.8+ 並運行 `pip install --upgrade pip`

**Q: API 服務器啟動失敗？**  
A: 檢查端口 8000 是否被占用，或使用 `uvicorn src.services.main_api_server:app --port 8001`

**Q: 如何快速測試系統？**  
A: 運行 `python src/interfaces/cli/main.py query "Hello Angela"`

**Q: 如何查看更多文檔？**  
A: 訪問 [文檔中心](docs/README.md) 獲取完整指南