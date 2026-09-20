<!--
  =============================================================================
  FILE_PATH: docs/user_guide/unsupported.md
  FILE_TYPE: documentation
  PURPOSE: 正式版明確不支援項 — 與 RELEASE_CRITERIA.md 同步的單一真相源
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-09-17
  AUDIENCE: users, support
  =============================================================================
-->

# 明確不支援項（正式版）

> 本頁列出 Angela
> AI 正式版**明確不支援**的功能。每項都附替代方案。依據：`docs/06-project-management/RELEASE_CRITERIA.md`「正式版明確不支援項」表。系統對這些項目**不會沉默失敗**：相關指令會走 agent→LLM 降級並明確告知不支援，或直接給出指名回應。

## 使用者可感知的不支援項

| 項目                                                | 實際行為                              | 替代方案                          |
| --------------------------------------------------- | ------------------------------------- | --------------------------------- |
| COMMAND／設備控制（打開設置、調音量、開關 WiFi 等） | 無對應 handler，走 agent→LLM 降級回答 | 手動操作系統設置                  |
| 實時音訊串流輸入／輸出                              | 不接受麥克風串流                      | 提供音訊檔案做離線轉錄（whisper） |
| 視頻通話／螢幕共享                                  | 無相關 handler                        | 不適用                            |
| 自動程式碼生成／修改專案代碼                        | 僅支援代碼解析與分析                  | 使用者自行修改，AI 提供分析       |
| 資料庫直接操作（SQL 執行）                          | 僅支援向量／記憶體查詢                | 使用向量搜尋或記憶查詢指令        |
| 系統級權限操作（sudo、驅動安裝）                    | 執行閘門直接拒絕                      | 使用者手動以管理員權限執行        |

## 架構限制（非 bug，屬設計邊界）

| 項目                            | 說明                               | 詳見                                             |
| ------------------------------- | ---------------------------------- | ------------------------------------------------ |
| 多使用者並發會話隔離            | 單用戶架構，多人同時使用不隔離狀態 | [limitations.md](../architecture/limitations.md) |
| 分散式部署／多節點協同          | 單機部署                           | [limitations.md](../architecture/limitations.md) |
| 硬體加速推理（CUDA/ROCm/Metal） | 僅 CPU 推理                        | [hardware.md](hardware.md)                       |

## 離線模式的能力邊界（誠實聲明）

- **可用（離線）**：基礎反射、確定性數學（MathVerifier）、字典查詢、部分知識檢索、本地引擎（ED3N/GARDEN）的確定性任務、離線 whisper 轉錄。
- **不可用（離線）**：開放域自然語言高品質生成——此能力依賴雲端或本地 LLM（Ollama 等）。
- 啟動時若無任何可用後端，server log 會發出 `[FirstRun]` 警告並附修復指引（見
  `core/system/bootstrap/first_run_detection.py`）。

## 能力誠實拆分

「架構完成度」不等於「模型能力完成度」。智能評分與確定性／神經泛化的拆分見
`docs/INTELLIGENCE_ASSESSMENT.md`；正式版驗收門檻見
`docs/06-project-management/RELEASE_CRITERIA.md`。
