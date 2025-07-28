# catcatAI 統一協作與技術指南

## 專案總覽

catcatAI 組織下目前主要有兩個相關專案：

| 專案名稱                        | 主要方向               | 主要語言    | 次要語言                        | 專案描述             |
|---------------------------------|------------------------|-------------|---------------------------------|----------------------|
| Unified-AI-Project              | AI平台/後端服務集成    | Python 94%  | TypeScript, JavaScript, HTML等  | AI 能力統一整合平台  |
| github-connect-quest            | GitHub集成/自動化工具  | Python 81%  | TypeScript, JavaScript, HTML等  | 與 GitHub 互動的自動化工具 |

---

## 技術棧與架構

### Unified-AI-Project

- **定位**：AI 能力整合與後端服務，提供統一 API。
- **技術棧**：
  - Python 為主（AI/ML、數據處理、服務端）。
  - 輔以 TypeScript/JavaScript，實現前端交互或管理界面。
  - Shell、Batchfile 輔助自動化部署與跨平台支持。
- **推薦模組/結構**：
  - `api/`：AI 功能與服務接口。
  - `web/`：前端相關模組。
  - `scripts/`：自動化腳本與部署工具。

### github-connect-quest

- **定位**：GitHub API 接入、自動化、數據同步與插件工具。
- **技術棧**：
  - Python 為主，用於後端自動化、任務調度、API 集成。
  - TypeScript/JavaScript 用於前端展示、交互或插件開發。
  - 較少腳本，重點在於功能和前後端聯動。
- **推薦模組/結構**：
  - `backend/`：GitHub API 集成與自動化腳本。
  - `frontend/`：可視化界面或用戶交互部分。
  - `integrations/`：第三方服務集成模組。

---

## 協作分工與整合建議

1. **分工明確**
   - Unified-AI-Project 專注於 AI 能力和服務端 API 實現。
   - github-connect-quest 專注於 GitHub 連接、自動化與用戶操作界面。

2. **API 對接**
   - Unified-AI-Project 將 AI 能力封裝為 RESTful API 或 gRPC 服務。
   - github-connect-quest 做為客戶端，通過 HTTP 調用 Unified-AI-Project 的 API 實現各種自動化與智能功能。

3. **前後端協作**
   - 前端統一使用 TypeScript/React，提升維護性和互操作性。
   - 定義統一的 API 文檔（建議使用 OpenAPI/Swagger），便於雙方調用和測試。

4. **開發規範與文檔**
   - 統一定義程式碼風格（如 PEP8, ESLint）。
   - 每個服務和模組需配備對應的 README/USAGE 說明。
   - 所有 API 調用需有接口文檔與調用範例。

5. **自動化流程**
   - 推薦使用 GitHub Actions 進行 CI/CD，自動測試與部署。
   - 定期同步兩個專案的開發進度和需求變更。

---

## 未來發展建議

- **功能對齊**：隨著專案發展，定期審視兩個專案的功能分界，避免重複建設。
- **文檔完善**：增補示例與用戶案例，提升新成員上手速度。
- **社群協作**：開放 Issue 和 PR 模板，規範協作者流程。
- **安全與維護**：定期依賴升級與安全審查。

---

## 參考資源

- [GitHub REST API 文檔](https://docs.github.com/en/rest)
- [OpenAPI/Swagger 官方文檔](https://swagger.io/docs/)
- [PEP8 Python 代碼風格](https://pep8.org/)

---

> 如需更詳細的功能模組劃分、API 規格或專案 README 模板，請聯繫管理員或在對應倉庫提出 Issue。