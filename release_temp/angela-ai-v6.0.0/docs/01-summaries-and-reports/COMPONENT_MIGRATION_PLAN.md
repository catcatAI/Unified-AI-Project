# 組件遷移計劃

## 1. 遷移目標
將 `core_ai` 目錄中未遷移的組件遷移至 `ai` 目錄，並確保所有依賴關係和導入路徑正確更新。

## 2. 組件分析結果

### 2.1 已識別的組件
1. **compression** - 數據壓縮模塊
   - 包含 AlphaDeepModel 類和 DNADataChain 類
   - 與 UnifiedSymbolicSpace 有依賴關係
   - 在 concept_models 目錄中存在另一個 AlphaDeepModel 版本，需要合併

2. **deep_mapper** - 深度映射模塊
   - 包含 DeepMapper 類
   - 與 MappableDataObject 有依賴關係

3. **code_understanding** - 代碼理解模塊
   - 包含 LightweightCodeModel 類
   - 與工具系統緊密相關

4. **symbolic_space** - 符號空間模塊
   - 包含 UnifiedSymbolicSpace 類
   - 被 compression 模塊依賴

### 2.2 代碼重複問題
- AlphaDeepModel 在 `core_ai/compression` 和 `ai/concept_models` 中都有實現，需要合併
- UnifiedSymbolicSpace 在 `core_ai/symbolic_space` 中實現，但未在 `ai` 目錄中找到對應組件

### 2.3 不完整或錯誤的組件
- compression 模塊依賴的 UnifiedSymbolicSpace 未遷移
- 所有未遷移的組件在 `ai` 目錄中都沒有對應目錄

## 3. 詳細遷移計劃

### 3.1 第一階段：基礎組件遷移
1. 創建缺失的目錄結構：
   - `ai/compression`
   - `ai/deep_mapper`
   - `ai/code_understanding`
   - `ai/symbolic_space`
   - `ai/dialogue`
   - `ai/evaluation`
   - `ai/formula_engine`
   - `ai/learning`
   - `ai/meta`
   - `ai/optimization`
   - `ai/personality`
   - `ai/rag`
   - `ai/reasoning`
   - `ai/test_utils`
   - `ai/world_model`

2. 遷移 symbolic_space 模塊
   - 將 `core_ai/symbolic_space/unified_symbolic_space.py` 移動到 `ai/symbolic_space/`
   - 更新文件中的導入路徑

### 3.2 第二階段：核心組件遷移
1. 遷移 compression 模塊
   - 將 `core_ai/compression/` 目錄內容移動到 `ai/compression/`
   - 合併 `core_ai/compression/alpha_deep_model.py` 和 `ai/concept_models/alpha_deep_model.py`
   - 更新導入路徑

2. 遷移 deep_mapper 模塊
   - 將 `core_ai/deep_mapper/` 目錄內容移動到 `ai/deep_mapper/`
   - 更新導入路徑

### 3.3 第三階段：其他組件遷移
1. 遷移 code_understanding 模塊
2. 遷移 dialogue 模塊
3. 遷移 evaluation 模塊
4. 遷移 formula_engine 模塊
5. 遷移 learning 模塊
6. 遷移 meta 模塊
7. 遷移 optimization 模塊
8. 遷移 personality 模塊
9. 遷移 rag 模塊
10. 遷移 reasoning 模塊
11. 遷移 test_utils 模塊
12. 遷移 world_model 模塊

### 3.4 第四階段：依賴關係更新
1. 更新所有文件中的導入路徑
2. 更新 `core_services.py` 中的導入路徑
3. 檢查並更新其他可能引用這些組件的文件

### 3.5 第五階段：測試驗證
1. 運行所有測試確保功能正常
2. 驗證所有導入路徑正確
3. 確認沒有因遷移而引入新的錯誤

## 4. 風險與緩解措施
1. **導入路徑錯誤**：通過全面的測試驗證來確保所有導入路徑正確
2. **功能缺失**：在遷移前仔細檢查所有文件，確保沒有遺漏重要組件
3. **代碼合併衝突**：仔細比較 AlphaDeepModel 的兩個版本，合併最佳特性
4. **兼容性問題**：在合併後進行全面測試，確保所有功能正常運行