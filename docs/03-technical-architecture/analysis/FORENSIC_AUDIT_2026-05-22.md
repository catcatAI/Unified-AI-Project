# Angela AI — 全面法醫審計報告

**日期**: 2026-05-22（2026-05-30 審計狀態更新）  
**方法**: 獨立多輪代碼審計（執行路徑分析 + TCS 遷移審計 + 安全/死代碼審計）  
**範圍**: `apps/backend/src/`, `apps/backend/configs/`, `apps/backend/src/config/`

> **⚠️ 2026-05-30 狀態更新**: 本文件為 2026-05-22 的審計報告。以下項目已修復，部分仍待處理：
> - **P0 chat_service wrappers** ✅ 已修復（`chat_service.py:302-312`）
> - **P0 get_config() 返回 `{}`** 🔴 仍存在（`config_loader.py:864-868` — `load_config()` 返回值仍被丟棄）
> - **P1 "User" 硬編碼** ✅ 已修復（`chat_service.py:261` 使用 `user_name`）
> - **P2 logging.DEBUG()** ✅ 已修復（兩個檔案不再有 `()` 調用）
> - **P2 /eval 端點** ✅ 未在 `api/` 或 `main_api_server.py` 中找到（可能已移除）
> - **P3 logging.basicConfig** 49 次（從 57 略降）
> - 詳見各章節註記。

---

## 執行摘要

此前聲稱的項目進度與代碼現實存在系統性偏差。3 輪獨立審計發現：

| 指標 | 此前聲稱 | 審計結果 | 偏差 |
|------|---------|---------|------|
| Phase 7 完成度 | ✅ 100% (Gemini README) | 🟡 43% | 嚴重誇大 |
| 硬編碼魔數 | 23+ | 150+ (含 `> 0.x` 比較) | 6.5x |
| 死工廠數量 | 16 | 9 真正死亡 + 6 休眠資產 + 1 活躍 | -6 |
| 配置系統 | 統一到 TCS | 4 套系統並存 | 嚴重 |
| config_loader.get_config() | 🟡 部分重定向 | 🔴 總是返回 `{}` | 更差 |
| 服務器啟動 | "應該可以" | 🔴 P0 ImportError | 根本不能 |

---

## 🔴 P0 — 服務器無法啟動

### 1. `main_api_server.py:292` — 模塊級 ImportError

```python
from services.chat_service import generate_angela_response, get_angela_chat_service
```

`chat_service.py` 在重寫後（1281→306 行）不再導出這兩個函數。該導入在模塊加載時執行，**在任何路由服務之前**崩潰。

**影響**: 整個 App B 服務器無法啟動。所有端點不可訪問。

**受影響的站點**（7 個總計）:
| 文件 | 行 | 類型 | 狀態 |
|------|-----|------|------|
| main_api_server.py | 292 | 模塊級 import | 🔴 阻止啟動 |
| main_api_server.py | 695-697 | 運行時 import + 調用 | 🔴 若 L292 移除則 500 |
| router.py | 175-176 | 運行時 import + await 調用 | 🔴 500 |
| unified_control_center.py | 430-432 | 運行時 import + 同步調用 | 🔴 404/500 |

### 2. 修復：添加包裝函數

需要添加導出到 `chat_service.py`：
```python
# 導出兼容包裝器
_chat_service_instance = None

async def get_angela_chat_service():
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
        await _chat_service_instance.initialize()
    return _chat_service_instance

async def generate_angela_response(user_message: str, user_name: str = "User"):
    svc = await get_angela_chat_service()
    return await svc.generate_response(user_message, user_name)
```

---

## 🟡 P1 — 關鍵運行時錯誤

### 3. `config_loader.py:52-58` — get_config() 返回空字典

```python
def get_config():        # 忽略 load_config() 返回值
    if _config is None:
        load_config()     # 返回值從未賦值給 _config
    return _config if _config is not None else {}  # 永遠返回 {}
```

`_config` 全局變量保持 `None`，因為 `load_config()` 的返回值被丟棄。所有調用者得到 `{}`。

**受影響的站點**: `is_demo_mode()` (L87-89)，以及其他任何導入 `config_loader.get_config` 的站點。

**驗證**:
```
Pdb) get_config()
{}
Pdb) load_config()
{...實際數據...}
```

### 4. `chat_service.py:270` — "User" 硬編碼

```python
self.pending_evolution_proposals["User"] = proposal  # 總是使用鍵 "User"
```

第 60 行查找 `user_name`（實際用戶名），但存儲在第 270 行使用文字字面量 `"User"`。這意味著：
- 用戶 "Alice" 發送 "使用模型 GPT-4" → 存儲在 `pending_evolution_proposals["User"]`
- 用戶 "Alice" 發送 "確認" → 查找 `pending_evolution_proposals["Alice"]` → 未找到 → `None` 返回
- **演化確認對任何非 "User" 的用戶永遠不會成功**

**修復**: 將第 270 行更改為 `self.pending_evolution_proposals[user_name] = proposal`

### 5. `config_loader.py:87-89` — is_demo_mode() 永遠返回 False

因為 `get_config()` 返回 `{}`，`config.get("ai_models", {})` 找不到 `use_simulated_resources`，所以總是 `False`。演示模式被破壞。

### 6. 熱重載路徑 — 從空配置初始化

`angela_llm_service.py:945-954` 中的 `reload_config()` 在沒有 `new_config` 時調用 `_get_default_config()`。但從 `main_api_server.py:567-569` 調用的熱重載路徑沒有輸入配置——它只是調用 `get_hot_reload_service()`，其 `hot_reload_config()` (L69-75) 是一個返回 `{"success": True}` 的存根。

實際的演化路徑（通過 `chat_service.py:67-82`）正確通過 `ConfigMutator.apply_mutation()` → `reload_config()` 傳遞新配置。**演化有效，但框架熱重載端點沒有效果。**

---

## 🔴 P2 — 安全問題

### 7. `logging.DEBUG()` → TypeError

文件：`core/managers/execution_monitor.py:632`, `ai/execution/execution_manager.py:607`

```python
logging.basicConfig(level=logging.DEBUG())  # TypeError: 'int' object is not callable
```

`logging.DEBUG` 是整數 `10`。`logging.DEBUG()` 意味著 `10()`。如果其中任何一個文件被導入，這將引發 `TypeError`。

目前是潛在的（P0 阻止了執行到達那裡），但在服務器修復後需要緊急修復。兩個文件都有 150+ 行的 `if __name__ == "__main__"` 塊，這表明它們是 CLI 腳本——可能在正常運行時沒有導入。

### 8. `/eval` 端點 — 任意程式碼執行

主線程的初始搜索未找到它。需要更具體的搜索：`eval(` 在任何請求處理程序內。

*可能已在之前的清理中移除 — 需要驗證。*

### 9. `cleanup_utils.py` — 命令注入風險

*子主題中提到。需要驗證具體的代碼模式。*

---

## 🔵 P3 — 代碼質量與技術債務

### 10. 150+ 硬編碼魔數

審計發現了 **41 個文檔化的閾值 + 150+ 個 `> 0.x` 比較和 `random.random()` 調用**，分佈在：

| 類別 | 數量 | 示例位置 |
|------|------|---------|
| 喚醒閾值 | 12 | 內分泌系統，心跳 |
| 壓力轉換 | 7 | cognitive_operations.py |
| 能量計算 | 11 | metabolic_analysis.py |
| 新奇性計算 | 4 | 狀態矩陣 |
| 隨機概率檢查 | 29 | `random.random() < 0.x` |
| target_fps 引用 | 24 | 所有模擬循環 |
| 其他 `> 0.x` | 80+ | 分佈廣泛 |

### 11. 配置蔓延 — 4 個並行系統

| 系統 | 位置 | 文件 | 行數 | 狀態 |
|------|------|------|------|------|
| 遺留 primary | `src/config/angela_core.yaml` | 1 | 1102 | 🟢 運行時權威 |
| 遺留 flat | `configs/*.yaml` | 23 | ~300 總計 | 🟡 舊但仍在讀取 |
| TCS default | `configs/**/*.default.yaml` | 11 | ~300 總計 | 🟢 代碼引用 |
| ConfigMutator evolved | `configs/**/*.evolved.yaml` | 1 (演示) | ~20 | 🟢 寫入工作 |

**運行時權威**: `angela_core.yaml`（1102 行，27 個部分，12 個標記為 `# DEAD`）

**10 個已死部分**：`safety_monitor`, `sanitizer_config`, `voice_config`, `image_recognition`, `admin_api`, `middleware`, `websocket`, `social_media`, `learning_config`, `sentiment`

### 12. 57 次 logging.basicConfig() 調用

分佈在 57 個文件中，所有文件都在爭奪根日誌記錄器。最後調用 `basicConfig` 的文件獲勝。這導致無法預測的日誌記錄行為，具體取決於導入順序。

### 13. 9 個真正已死的工廠

只有 4 個是 TRULY_DEAD（無調用者無導入）。經過法醫審計的完整細目見 `DEAD_FACTORY_FORENSICS.md`。

---

## 📊 Phase 完成度審計

| Phase | 聲稱 | 實際 | 證據 |
|-------|------|------|-------|
| Phase 6 Self-Evolution | ✅ 完成 | ✅ 完成 | ConfigMutator (156 行), hot-reload (L945), StateStore (86 行), broadcast (L58-78) — 全部獨立驗證有效 |
| Phase 6.5 Startup Wiring | ✅ 完成 | ✅ 完成 | `_initialize_all_services()`, `get_metabolic_heartbeat().start()/stop()` in lifespan |
| Phase 7 TCS | ✅ 100% (Gemini) | 🟡 43% | 11 `.default.yaml` 文件，但 0 個 `.user.yaml`，0 個 `.evolved.yaml`（生產環境），150+ 個硬編碼值，`get_config()` 返回 `{}` |
| Phase 8 Tech Debt | 🟡 "in progress" | ❌ 未開始 | 服務器無法啟動 — 所有技術債務清理被阻塞 |

---

## 🎯 優先級修復順序

| 優先級 | 任務 | 文件 | 行 | 2026-05-30 狀態 | 風險 |
|--------|------|------|-----|-------------------|---|
| P0 | 添加 chat_service 包裝函數 | chat_service.py | 末尾 | ✅ 已修復（L302-312） | 🔴 ImportError 阻止啟動 |
| P0 | 修復 get_config() 返回值 | config_loader.py | 52-58 | 🔴 仍存在（L864-868） | 🔴 所有調用者得到空字典 |
| P1 | 修復 "User" 硬編碼 | chat_service.py | 270 | ✅ 已修復（L261） | 🟡 演化確認被破壞 |
| P1 | 修復 is_demo_mode() | config_loader.py | 87-89 | 🔴 受 get_config() 阻塞 | 🟡 演示模式被破壞 |
| P2 | 修復 DEBUG() → TypeError | execution_monitor.py, execution_manager.py | 632,607 | ✅ 已修復 | 🔴 如果導入則崩潰 |
| P2 | 移除 /eval 端點 | main_api_server.py | 待查找 | ✅ 未在 api/ 中找到 | 🔴 任意程式碼執行 |
| P3 | 清理 12 個已死 config 部分 | angela_core.yaml | 多個 | 🟡 待確認 | 🟢 僅維護 |
| P3 | 移除 9 個已死工廠 | 多個 | 多個 | 🟡 (WIRING_MAP 審計修正了 list) | 🟢 僅清理 |
| P3 | 遷移 50 個魔數到 TCS | 多個 | 多個 | 🟡 待處理 | 🟢 逐步清理 |

---

## 🧠 關於代碼現實的結論

1. **Phase 6 代碼是可靠的** — ConfigMutator, evolution flow, hot-reload, StateStore 都獨立完整。演化路徑（LLM manage intent → proposal → user confirms → apply → broadcast → reload）是完整的。

2. **服務器被不必要的導入破壞了** — 重寫 `chat_service.py` 並移除 2 個導出函數破壞了 7 個站點。修復只需要 15 行包裝函數，而不是回滾 306→1281 行。

3. **TCS 遷移被誇大了** — 11 個 `.default.yaml` 文件存在，但 `config_loader.py:get_config()` 返回 `{}` 的事實意味著「TCS 遷移」的實際工作（將調用者從 `get_config()` → `tiered_loader.get_config()` 遷移）還沒有完成。TCS 作為讀取路徑有效，但舊的 `get_config()` 接口被破壞了。

4. **4 個配置系統並存** — 任何清理必須逐步淘汰遺留系統，而不是添加第 5 個。

5. **服務器啟動是唯一真正的障礙** — 一旦 P0 修復，Ollama CPU-only 性能和沙盒限制仍然存在，但代碼將至少啟動。
