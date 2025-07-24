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

### 安裝步驟

1. **克隆專案**
```bash
git clone <repository-url>
cd unified-ai-project
```

2. **安裝依賴**
   建議使用專案提供的安裝程式來管理依賴。它會讀取 `dependency_config.yaml` 中的配置，並引導您完成安裝。
   ```bash
   python installer_cli.py
   ```
   您將被提示選擇所需的安裝類型（例如 `minimal`, `standard`, `full` 等）。

3. **環境配置**
```bash
# 複製環境變量模板
cp .env.example .env

# 編輯 .env 文件，設置必要的API密鑰
# 您可以使用以下命令生成 HAM 加密密鑰
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

4. **運行應用**
   本專案提供多種運行方式，詳細資訊請參閱 **[項目章程](docs/PROJECT_CHARTER.md)** 中的「運行應用程序」一節。
   - **API 服務器**: `uvicorn src.services.main_api_server:app --reload`
   - **命令行接口 (CLI)**: `python src/interfaces/cli/main.py query "Your query"`
   - **Electron 桌面應用**: `cd src/interfaces/electron_app && npm start`

## 未來發展路線圖

本專案的未來發展路線圖已整理至 **[ROADMAP.md](docs/ROADMAP.md)**。