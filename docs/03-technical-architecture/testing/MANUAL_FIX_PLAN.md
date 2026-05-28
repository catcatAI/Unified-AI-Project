# 手動修復計劃

## 概述
項目中仍有831個Python文件存在語法錯誤。自動修復腳本無法完全解決這些問題，需要手動修復關鍵文件。

## 修復優先級
1. 核心模塊文件
2. 測試文件
3. 腳本文件
4. 其他文件

## 需要手動修復的關鍵文件

### 1. 核心模塊文件
- `apps/backend/src/agents/nlp_processing_agent.py` - 之前已部分修復，但仍存在語法錯誤
- `apps/backend/src/core_services.py` - 項目核心服務文件
- `apps/backend/src/ai/agent_manager.py` - AI代理管理器
- `apps/backend/src/ai/learning/content_analyzer_module.py` - 內容分析模塊
- `apps/backend/src/hsp/connector.py` - HSP連接器

### 2. 測試文件
- `tests/agents/test_base_agent.py` - 基礎代理測試
- `tests/conftest.py` - 測試配置
- `tests/test_basic.py` - 基礎測試

### 3. 腳本文件
- `scripts/auto_fix_project.py` - 自動修復腳本
- `scripts/fix_project_syntax.py` - 語法修復腳本
- `scripts/run_training.py` - 訓練運行腳本

## 修復步驟

### 第一階段：修復核心模塊文件
1. 修復 `apps/backend/src/agents/nlp_processing_agent.py`
2. 修復 `apps/backend/src/core_services.py`
3. 修復 `apps/backend/src/ai/agent_manager.py`

### 第二階段：修復測試文件
1. 修復 `tests/agents/test_base_agent.py`
2. 修復 `tests/conftest.py`
3. 修復 `tests/test_basic.py`

### 第三階段：修復腳本文件
1. 修復 `scripts/auto_fix_project.py`
2. 修復 `scripts/fix_project_syntax.py`
3. 修復 `scripts/run_training.py`

## 修復指南

### 1. 缺少冒號的問題
- 類定義：`class ClassName` → `class ClassName:`
- 函數定義：`def function_name()` → `def function_name():`
- 控制流語句：`if condition` → `if condition:`, `for item in list` → `for item in list:`, `while condition` → `while condition:`

### 2. 縮進問題
- 確保使用4個空格進行縮進
- 保持一致的縮進級別
- 修復嵌套塊的縮進

### 3. 括號不匹配問題
- 檢查圓括號、方括號和花括號的匹配
- 確保所有左括號都有對應的右括號

## 驗證方法
1. 使用 `python -m py_compile file.py` 檢查語法
2. 運行相關測試確保功能正常
3. 檢查導入是否正常工作

## 完成標準
- 所有列出的關鍵文件都沒有語法錯誤
- 可以成功運行項目的核心功能
- 測試可以正常執行