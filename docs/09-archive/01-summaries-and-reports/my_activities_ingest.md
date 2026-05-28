# 我的活動檔案匯入說明

## 目的
將 `D:\Projects\Unified-AI-Project\我的活動` 資料夾內的所有中文 `.txt` 檔案讀取，產生向量嵌入，並存入系統的 **VectorMemoryStore**（向量資料庫），讓 AI 在對話或推理時能夠檢索與使用這些活動記錄。

## 使用方式
1. **確保環境**
   - 已安裝專案相依套件（`pnpm install` 只影響前端，Python 端請執行 `pip install -r requirements.txt`）。
   - 若要使用真實 LLM，請設定環境變數 `USE_MOCK_LLM="false"`；若僅測試，可保留 `true`。
2. **執行腳本**
   ```bash
   python scripts/ingest_my_activities.py
   ```
   - 腳本會自動偵測 `我的活動` 資料夾，遞迴搜尋所有 `*.txt`。
   - 每個檔案的內容會透過 `HybridBrain` 產生嵌入向量，並以檔案相對路徑作為 `doc_id` 存入向量資料庫。
3. **驗證**
   - 完成後會在終端印出 `All files processed` 訊息。
   - 可使用 `apps/backend/src/core/ai/memory/vector_store.py` 提供的查詢介面測試檢索，例如:
   ```python
   from apps.backend.src.core.ai.memory.vector_store import VectorMemoryStore
   store = VectorMemoryStore()
   results = store.query("今天的活動", top_k=5)
   print(results)
   ```

## 注意事項
- **編碼**：所有檔案以 UTF‑8 讀取，確保中文不會出現亂碼。
- **向量資料庫**：目前使用 ChromaDB（在 `vector_store.py` 中實作），資料會保存在專案根目錄的 `chroma_db` 資料夾。
- **效能**：腳本使用 `asyncio.gather` 同時處理多個檔案，若檔案數量極大，可自行調整併發數量。
- **錯誤處理**：若檔案讀取失敗或無法產生嵌入，腳本會印出警告並繼續處理其他檔案。

## 後續擴充
- **自訂 Metadata**：可在 `metadata` 中加入時間戳記、標籤等資訊，以便於後續的篩選與聚類。
- **增量更新**：若新增或修改檔案，可再次執行腳本，`VectorMemoryStore.upsert` 會自動覆寫相同 `doc_id` 的向量。
- **搜尋介面**：可在前端或 API 中加入 `/search_activities` 端點，呼叫 `VectorMemoryStore.query` 讓使用者即時查詢過往活動。
