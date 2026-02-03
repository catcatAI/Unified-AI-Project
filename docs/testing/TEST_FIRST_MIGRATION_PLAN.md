# 測試優先的目錄遷移計劃

## 背景
項目中仍有部分組件未從 `core_ai` 遷移至 `ai` 目錄，同時 `tests/core_ai` 目錄仍存在。為確保遷移過程中不引入新的問題，需要制定一個測試優先的遷移計劃。

## 目標
1. 確保所有測試在遷移前正常運行
2. 逐步遷移剩餘組件
3. 保持項目的穩定性和功能完整性

## 當前狀態分析

### 未遷移的組件
根據 DIRECTORY_MERGE_SUMMARY.md，以下組件仍未遷移：
- code_understanding
- compression
- deep_mapper
- dialogue
- evaluation
- formula_engine
- learning
- meta
- meta_formulas
- optimization
- personality
- rag
- reasoning
- symbolic_space
- test_utils
- world_model
- 多個 Python 文件如 agent_collaboration_manager.py, agent_manager.py 等

### 測試狀態
- 根目錄下已建立 `tests` 目錄
- 但 `tests/core_ai` 目錄仍然存在

## 計劃階段

### 第一階段：測試穩定性驗證
1. 運行所有現有測試確保通過
   ```bash
   python -m pytest tests/ -v
   ```
2. 修復任何測試失敗問題
3. 確認測試覆蓋率穩定

### 第二階段：組件遷移準備
1. 分析未遷移組件的依賴關係
2. 確認每個組件的測試文件位置
3. 創建遷移清單和優先級排序

### 第三階段：逐個組件遷移
1. 選擇一個組件進行遷移（建議從依賴較少的開始）
2. 遷移源代碼文件
3. 遷移對應的測試文件
4. 更新導入路徑
5. 運行相關測試確保通過
6. 重複以上步驟直到所有組件遷移完成

### 第四階段：最終清理
1. 刪除空的 `core_ai` 目錄
2. 刪除空的 `tests/core_ai` 目錄
3. 運行完整測試套件驗證
4. 更新相關文檔

## 風險控制
1. 在每步操作前進行完整備份
2. 每次遷移後立即運行相關測試
3. 保持版本控制，便於回滾
4. 詳細記錄每步操作和結果

## 預期結果
1. 完全消除 `core_ai` 目錄
2. 所有組件統一在 `ai` 目錄下管理
3. 測試文件完全集中到 `tests` 目錄
4. 項目保持穩定運行