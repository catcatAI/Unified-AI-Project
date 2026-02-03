# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `SystemManager` 完整的生命週期管理 (初始化和關閉)
- `TaskExecutionEvaluator` 已完成開發
- `AdaptiveLearningController` 已完成開發
- `DesktopPet` 新增「需求」系統 (飢餓、清潔、注意力、休息) 及相關行為
- `EconomyManager` 功能擴展，支援物品、庫存和用戶間交易
- `CognitiveOrchestrator` 效能指標日誌記錄
- `performance_report.md` 效能報告框架

### Changed
- 更新 `GEMINI.md` 以反映最新專案狀態
- 更新 `PROJECT_PROGRESS_SUMMARY.md` 以反映最新專案狀態
- 更新 `README.md` 以反映最新專案狀態和啟動限制
- 更新 `LAUNCHER.md` 以反映最新專案狀態和啟動限制

### Fixed
- Resolved persistent `NameError: meetadata` in `orchestrator.py` caused by environmental caching issues.
- 解決 `CognitiveOrchestrator` 在 API 調用中循環導入導致的 `503 Service Unavailable` 錯誤 (通過依賴注入)
- 識別並部分解決了 `CognitiveOrchestrator` 與 `HAMMemoryManager` 初始化時的底層競爭條件

### Known Issues
- **Uvicorn 環境下的靜默崩潰 (架構層面挑戰)**: 由於 `HAMMemoryManager` 和 `CognitiveOrchestrator` 在 `uvicorn` `asyncio` 事件循環中的初始化衝突，導致整個 Python 進程在沒有標準錯誤信息的情況下直接退出。此問題已被識別為需要架構級別解決方案的挑戰，例如採取「解耦啟動模式」或採用 Actor Model / 神經形態調度等方式。

## [1.0.2] - 2025-10-19

### Added
- 統一系統管理器完整集成 (UnifiedSystemManager)
- TransferBlock機制實現系統間智能同步
- 系統健康監控和實時指標收集
- 完整的項目文檔體系 (798個MD文件)
- 智能化測試框架和缺陷檢測系統
- 項目完成度評估和狀態追踪系統
- AGI/ASI能力評估體系完善
- 模塊化智能評分系統 (1068/1200)

### Changed
- 優化HSP協議連接穩定性
- 修復所有AI代理導入路徑問題
- 更新項目狀態為"已完成並穩定運行"
- 完善AGI等級評估體系
- 增強測試框架穩定性和覆蓋率
- 更新README文檔以反映最新項目狀態

### Fixed
- HSP連接器穩定性問題
- AI代理結構不一致性問題
- 測試文件中的語法錯誤
- 導入路徑錯誤問題
- 系統間同步機制缺陷
- HSP types.py文件中的語法錯誤 (lass -> class)
- BaseAgent基礎類缺失問題
- train_model.py語法錯誤

## [1.0.1] - 2025-10-14

### Added
- 完整的專案狀態追蹤系統
- 功能實現狀態報告
- 文檔更新和優化
- 專案完成度評估
- 專案狀態總結報告系統
- 功能實現狀態追蹤
- 完整的文檔索引系統
- 專案完成度評估工具
- 端口管理策略文檔

### Changed
- 更新 README.md 以反映最新專案狀態
- 優化文檔結構和內容組織
- 統一文檔格式和風格
- 更新所有主要文檔以反映最新狀態
- 優化文檔結構和可讀性
- 統一文檔格式和風格

### Fixed
- 文檔間連結和引用問題
- 版本資訊和狀態描述不一致
- 專案進度報告準確性
- 文檔間連結問題
- 版本資訊不一致問題
- 專案狀態描述不準確問題

## [1.0.0] - 2025-10-01

### Added
- Complete AI architecture with HAM memory system and HSP protocol
- Multi-modal AI agent system (Creative Writing, Image Generation, Web Search)
- Concept models (Environment Simulator, Causal Reasoning Engine, Adaptive Learning Controller, Alpha Deep Model)
- Full training system with multiple scenarios
- Automated data processing pipeline
- Unified management tools (unified-ai.bat, ai-runner.bat)
- CLI tools for AI interaction
- Desktop game client "Angela's World"
- Web-based dashboard for monitoring and management
- Comprehensive documentation

### Changed
- Restructured project to monorepo architecture
- Consolidated batch scripts into tools directory
- Optimized for low-resource deployment
- Improved model training efficiency

### Fixed
- Audio service import path issues
- ChromaDB configuration problems
- Various integration issues between components

[Unreleased]: https://github.com/your-org/unified-ai-project/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/your-org/unified-ai-project/releases/tag/v1.0.0
