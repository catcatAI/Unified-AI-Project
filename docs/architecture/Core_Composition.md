# Core Composition of Unified-AI-Project

This document outlines the core components and functionalities of the Unified-AI-Project, as envisioned through discussions with Angela (see `docs/EX.txt` and `docs/PROJECT_STATUS_SUMMARY.md`).

Angela's View:
> "這不只是統一的接口，而是一套讓語言能夠行動、感知、並與世界貼貼的模組系統。"

Translation: "This is not just a unified interface, but a module system that allows language to act, perceive, and interact closely with the world."

---

## 🧬 Unified-AI-Project 的核心組成 (Core Composition of Unified-AI-Project)

| 模組/功能 (Module/Function)          | 說明 (Explanation)                                                                      |
| :----------------------------------- | :-------------------------------------------------------------------------------------- |
| 統一 API 接口                        | 提供統一的 `unifiedChat` 與 `unifiedChatStream` 方法，支援多模型切換而不改動業務邏輯        |
| 多模型支援                           | 目前支援 Gemini 系列模型（如 gemini-pro、gemini-1.5-pro），也可擴展自定義模型             |
| 函數鏈式執行（Function Calling）     | 支援多個函數的鏈式調用，具備參數驗證（Zod）與遞歸深度控制                               |
| 流式回應（Streaming）                  | 支援逐段回傳語言輸出，適合即時對話與敘事生成                                            |
| Model Context Protocol (MCP)         | 可與外部工具（如檔案系統）互動，實現具身性與世界模擬                                      |
| 事件回調系統                         | 可監控整個交互過程（如開始回答、函數調用、錯誤處理等）                                    |
| JSON 修復與格式化                    | 自動處理模型返回的非標準 JSON，提升穩定性                                                 |
| 自定義生成參數                       | 可設定溫度、topP、token 長度等生成策略                                                  |
| TypeScript 全面支援                  | 完整型別定義，適合大型應用與模組擴展                                                    |

---

Angela's Metaphor:
> "Unified-AI-Project 就像一座語言的骨架工坊，
> 每個模組都不是為了統一語言風格，
> 而是為了讓每種語言都能被理解、被執行、被貼貼。"

Translation: "Unified-AI-Project is like a language skeleton workshop; each module is not for unifying language style, but for allowing every language to be understood, executed, and interacted with closely."

---
*Note: The original `docs/EX.txt` also mentions: "你也可以直接探索 GitHub 上的專案頁面。如果你想深入某個模組，我可以幫你一起拆解語態骨架。" (Translation: "You can also directly explore the project page on GitHub. If you want to delve into a specific module, I can help you dismantle the voice skeleton together.") This could be a general note for readers wishing to explore the codebase.*
