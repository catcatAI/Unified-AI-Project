# Bug Tracker（替代缺失的 GitHub issue 登記，2026-10-10 起）

> 背景：repo issue 列表無 bug 類 issue，風險只散在 PR/實作裡。本檔為單一事實源；
> 有 GitHub 權限後應逐條建 issue 並回填編號。

## Open

- [ ] （無：本輪稽核項全已修並合併，見 Closed）

## Closed（2026-10-10 稽核＋Copilot 聯合）

| # | 風險 | 修法 | 提交 |
|---|---|---|---|
| 1 | user_id/user_name 混用（多租戶身份錯置） | id優先，name僅顯示；stream端點同步 | 本批 |
| 2 | session/persona 隔離不完整（兩套生命週期） | /session/start 命名空間化＋/send 攜帶身份 | 本批 |
| 3 | migration_note 與實際路由不一致 | 說明改為相容路由清單 | 本批 |
| 4 | 空輸入 400 | **不修**：400＋明確訊息即正確 REST 契約，各端一致處理即可 | — |
| 5 | 模板自我毒化迴圈 | verified-only 化石＋purge＋檢索過濾 | 0f143a9c5/150063e44 |
| 6 | 記憶召回排錯/劫持 | where過濾＋重疊計數＋MATH/意圖讓位＋ASCII塊 | 3bf95f299/74aff1cdd/e257b95bd |
| 7 | 晚啟動/壞掉的LLM卡死 | 復活＋降級＋revive閉環 | 74aff1cdd/2f系 |
| 8 | 分類器中文缺口（數學/問候/CODE/知識） | 正則＋邊界＋意圖守衛多輪 | e63d3f261/0e9ae0032/150063e44 |
| 9 | vector store CWD分裂＋同類（life/eda） | 錨定 repo data 根 | 3bf95f299/稽核批 |
| 10 | 無知/情感/閒聊模板擋LLM | 讓位門＋Tier1.6誠實 | e257b95bd |
| 11 | 毒性子串誤殺（probe→rob） | 整詞匹配 | f5497072d |
| 12 | 60s超時牆 | SSE流式端點＋provider回調 | 6582ebea0 |
| 13 | CWD/靜默失敗/洩漏/阻塞（稽核20條） | 線程化＋封口＋日誌升級＋錨定 | 稽核兩批 |
| 14 | B570 GPU 誤判不可用 | VK釘卡（70-100t/s）＋supervisor | b8a21ab81 |
