<!-- DEPRECATED: Superseded by planning/project-management/planning-docs/STATUS_AND_ACTIONS.md (rolling) -->
# 當前狀況整理與行動計劃

## 📋 當前專案狀態總結

### ✅ 已完成的工作
- OpenAPI 導出：新增 /api/v1/openapi 與 export_openapi.py 腳本（導出到 docs/api/openapi.json）
- Atlassian 建立 Issue 支援：priority、labels（acli --priority/--labels）
- CLI 第二階段：client.py、--json/--timeout/--token、console script、tests + CI（.github/workflows/cli-tests.yml）
- Desktop App：新增 Atlassian 頁面與 IPC handlers（status/projects/issues/create/spaces/search）

1. **目錄重構**: apps/ 和 packages/ 結構已建立
2. **配置文件**: pnpm-workspace.yaml 和 package.json 已更新
3. **文檔更新**: 所有 README.md 文件已更新並保持一致
4. **安裝器腳本**: 路徑問題已修復
5. **臨時文件清理**: 污染源已清除

### ⚠️ 當前問題
1. **後端測試**: msgpack 依賴缺失，測試無法運行
2. **前端編譯**: class-variance-authority 依賴缺失
3. **環境變數**: MIKO_HAM_KEY 未設置
4. **路徑問題**: 可能還有遺漏的舊路徑引用

## 🎯 立即行動計劃

### 第一步：解決依賴問題
```bash
# 1. 修復後端依賴
cd Unified-AI-Project/apps/backend
pip install msgpack
echo "msgpack" >> requirements.txt

# 2. 修復前端依賴  
cd ../../packages/ui
pnpm install class-variance-authority

# 3. 設置環境變數
cd ../../apps/backend
echo "MIKO_HAM_KEY=jhSMKpG03Z_CHKPLoHZSbvljIRA23ILegbeH2ev6G10=" > .env
```

### 第二步：全面路徑檢查
```bash
# 搜索所有可能的舊路徑引用
cd Unified-AI-Project
grep -r "packages/backend" . --exclude-dir=node_modules
grep -r "packages/desktop-app" . --exclude-dir=node_modules
grep -r "packages/frontend-dashboard" . --exclude-dir=node_modules
```

### 第三步：驗證修復效果
```bash
# 測試後端
cd apps/backend
pytest --cov=src --cov-report=term-missing

# 測試前端
cd ../..
pnpm dev
```

## 🔧 我需要做的具體工作

### 立即執行
1. **修復依賴問題** - 確保所有包都能正常安裝和運行
2. **完整路徑掃描** - 找出所有遺漏的路徑問題
3. **逐一修復路徑** - 系統性地解決每個路徑問題
4. **驗證功能** - 確保修復後一切正常工作

### 系統性方法
1. **掃描階段**: 全面搜索問題
2. **分類階段**: 按類型和優先級分類
3. **修復階段**: 逐一解決問題
4. **驗證階段**: 測試修復效果
5. **文檔階段**: 更新相關文檔

## 📊 成功標準

### 修復完成的標誌
- [ ] `pnpm test:coverage` 成功運行
- [ ] `pnpm dev` 前後端都正常啟動
- [ ] 沒有路徑相關的錯誤
- [ ] 所有依賴正確安裝
- [ ] 功能正常工作

### 質量檢查
- [ ] 所有搜索結果都是正確的路徑
- [ ] 沒有舊的 packages/ 引用
- [ ] 配置文件一致
- [ ] 文檔準確

## 🚀 開始執行

讓我現在開始系統性地解決這些問題，一步一步來：

1. 首先解決依賴問題
2. 然後進行全面路徑掃描
3. 逐一修復發現的問題
4. 最後驗證所有功能

這樣可以確保不遺漏任何問題，並且有條理地完成所有修復工作。