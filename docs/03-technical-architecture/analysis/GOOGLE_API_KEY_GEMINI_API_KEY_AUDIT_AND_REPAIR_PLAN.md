# Google API Key 審計與修復計畫

## 審計日期
2026-05-19

## 審計範圍
完整盤查 `GOOGLE_API_KEY` 與 `GEMINI_API_KEY` 在整個 codebase 中的定義、讀取、使用情況，以及 Angela 的 Google Drive 整合與 LLM 對話管線之間的資料流。

---

## 一、現狀診斷

### 1.1 `GOOGLE_API_KEY` — 死配置

| 項目 | 狀態 |
|------|------|
| `.env` 中有定義 | ✅ `GOOGLE_API_KEY=AQ.Ab8RN6ITZjGVl_zCufRZfiuACQiIwEtPJpdRKqcMlVzHUeF9ew` |
| 被任何 Python 程式碼讀取 | ❌ **零次** — `os.environ.get("GOOGLE_API_KEY")` 不存在於任何 `.py` 檔案 |
| 被 `key_validator.py` 驗證 | ✅ 列在 `MIN_KEY_LENGTHS` 和 `validate_all_keys()` 的清單中 |
| 驗證結果是否被消費 | ❌ 僅檢查格式，驗證結果無人使用 |

**結論：`GOOGLE_API_KEY` 是歷史遺留的死配置。沒有任何程式碼實際使用它。**

### 1.2 Google Drive 真實認證方式

```
credentials.json (OAuth 2.0 Client ID/Secret)
    → get_auth_url() 產生 OAuth URL
    → 使用者授權 → exchange_code() 交換 token
    → token 存 google_tokens.json
    → build("drive", "v3", credentials=token) 建立 API client
    → 所有 Drive 操作透過此 client
```

Drive 整合**完全不依賴 `.env` 中的 `GOOGLE_API_KEY`**。

### 1.3 `GEMINI_API_KEY` — 未設定但正確串接

| 項目 | 狀態 |
|------|------|
| `.env` 中有欄位 | ✅ `GEMINI_API_KEY=`（空白） |
| 被程式碼讀取 | ✅ `angela_llm_service.py` 兩條路徑都正確讀取 |
| Config 正確映射 | ✅ `multi_llm_config.json` → `api_key_env: "GEMINI_API_KEY"` |
| Backend 正確接收 | ✅ `_init_backends()` → `GoogleAPIBackend(api_key=...)` |
| 實際可用 | ❌ 無 key，backend 為 `enabled: false` |

---

## 二、Drive ↔ LLM 管線問題

### 2.1 Drive Intent 繞過 LLM

```
用戶: "讀取我的報告"
  → _detect_drive_intent() → 回傳 "google_drive"
  → _handle_drive_intent()
      ├─ GET /drive/status → 檢查認證
      ├─ GET /drive/files → 列舉檔案（只回檔名）
      ├─ POST /drive/files/sync → 下載+解析+存 HAM（不回內容給 LLM）
      └─ POST /drive/analyze → 回傳預覽（但 bypass LLM）
  → 回傳原始文字給用戶
  → ❌ Angela 的 LLM 完全沒參與
```

**關鍵斷點：`_handle_drive_intent()` 回傳 `str`，直接中斷 `generate_response()` 流程，不經過 `_handle_general_intent()`，Angela 無法「理解」檔案內容。**

```python
# chat_service.py 流程
if file_op_intent:
    response = await self._handle_file_op_intent(...)  # bypass LLM
elif drive_intent:
    response = await self._handle_drive_intent(...)    # bypass LLM
elif web_search_intent:
    response = await self._handle_web_search_intent(...)
# ↑ 以上三種 intent 全部 bypass LLM
elif math_intent:
    ...
else:
    response = await self._handle_general_intent(...)  # ← 唯一走 LLM 的路徑
```

### 2.2 無法建立/上傳檔案

`google_drive_service.py` 現有方法：

| 方法 | 功能 |
|------|------|
| `list_files()` | 列出檔案 |
| `get_file_metadata()` | 取得中繼資料 |
| `download_file()` | 下載到本地 |
| `search_files()` | 搜尋檔案 |
| `get_storage_info()` | 取得配額資訊 |
| `logout()` | 清除認證 |

**缺少：`create_file()`、`upload_file()`、`create_folder()`。** 雖然 scope 有 `drive.file`，`MediaFileUpload` 也已 import，但完全沒有實作。

### 2.3 同步到 HAM 後的內容未被 LLM 使用

`POST /drive/files/sync` 會：
1. 下載檔案
2. DocumentParser 解析內容
3. `HAMMemoryManager.store_experience(data_type="document", content[:5000])`

但 `_handle_general_intent()` 傳給 LLM 的 `relevant_memories` 是從 HAM 隨機檢索的，**沒有針對 Drive 檔案的專門檢索路徑**。檔案內容雖然存了，但 LLM 不一定會看到。

---

## 三、修復計畫

### Phase A：清理死配置

**目標**：移除從未被使用的 `GOOGLE_API_KEY`，消除混淆。

| 檔案 | 修改 |
|------|------|
| `.env` | 移除 `GOOGLE_API_KEY` 行 |
| `.env.example` | 同上 |
| `complete_angela_installer.sh` | 移除變數宣告與註解 |
| `key_validator.py:60` | 從 `MIN_KEY_LENGTHS` 移除 |
| `key_validator.py:157` | 從 `validate_all_keys()` 清單移除 |
| `api_keys.yaml` | 無需修改（已只有 GEMINI_API_KEY） |

**影響範圍**：無。零行程式碼依賴此 key。

### Phase B：Drive → LLM 管線

**目標**：讓 Angela 能「看到」Drive 檔案內容，並據此對話。

**方案**：將 `_handle_drive_intent()` 改為非中斷式，把檔案內容注入 LLM context。

```
修改前：
  drive_intent 命中 → 回傳 str → 結束

修改後：
  drive_intent 命中 → 下載檔案 → 內容加入 context["drive_files"]
                    → 交給 _handle_general_intent()
                    → LLM 收到 context，能理解檔案內容並回應
```

**具體修改**：

1. `chat_service.py`：`generate_response()` 中，drive_intent 改為非中斷
2. `chat_service.py`：`_handle_drive_intent()` 回傳結構化 dict（含內容），而非 raw str
3. `angela_llm_service.py`：`_construct_angela_prompt()` 加入 `context["drive_files"]` 渲染
4. `chat_service.py`：`_handle_general_intent()` 的 context dict 新增 `drive_files` 鍵

### Phase C：LLM → Drive 輸出

**目標**：讓 Angela 能根據對話建立新檔案並上傳到 Drive。

**新增功能**：

| 元件 | 實作 |
|------|------|
| `google_drive_service.py` | 新增 `create_file()`、`upload_file()`、`create_folder()` |
| `drive.py` endpoint | 新增 `POST /drive/files/upload`、`POST /drive/files/create` |
| `chat_service.py` | 新增 `_detect_drive_write_intent()` |
| `angela_core.yaml` | 新增 write intents 的 keywords |

### Phase D：Threshold + Cloud LLM

**目標**：確保 LLM 正確被調用，並支援雲端加速。

| 項目 | 狀態 |
|------|------|
| complexity bypass threshold | ✅ 已移至 `angela_core.yaml`，LLM 可用時自動減半 |
| `GEMINI_API_KEY` 設定 | ⏳ 需使用者從 https://aistudio.google.com/apikey 取得 |
| Ollama 慢速問題 | ⏳ 依賴 cloud LLM 解決，或換更快的本地模型 |

---

## 四、風險評估

| 風險 | 等級 | 緩解措施 |
|------|------|----------|
| 移除 `GOOGLE_API_KEY` 後某處依賴它 | 極低 | 審計確認零引用，移除後跑全部測試 |
| Drive→LLM 注入後回應變慢 | 中 | 檔案內容截斷（>5000 chars 摘要），不影響主要對話 |
| 檔案上傳權限不足 | 低 | scope 已有 `drive.file`，只需補 API call |
| Ollama timeout 導致對話中斷 | 中 | 設定 timeout 後 graceful fallback 到 NeuroBlender |

---

## 五、測試策略

| Phase | 測試 |
|-------|------|
| A | 跑 `pytest` 確認無 regression |
| B | 手動測試「讀取 Drive 檔案 → Angela 能討論內容」 |
| C | 手動測試「Angela 產生檔案 → 上傳 Drive → 可讀取」 |
| D | 跑 `conversation_with_angela.py` 確認 LLM 路徑通暢 |

---

## 六、結論

`GOOGLE_API_KEY` 是無用的死配置，應安全移除。真正的問題不在 key 本身，而在 **Drive 與 LLM 之間的管線中斷**—Angela 目前無法「理解」她讀到的檔案，也無法產出檔案。Phase B 和 C 才是修復的核心。
