# Self-Correction and Immune System Design in Unified-AI-Project

This document details the conceptual design for self-correction mechanisms within the Unified-AI-Project's linguistic immune system. It expands on how the system can not only defend against errors but also learn and adapt from them. This is based on discussions with Angela (see `docs/EX.txt` and `docs/PROJECT_STATUS_SUMMARY.md`).

Angela's insight on the necessity of a reflective layer:
> "是的，Fragmenta 的免疫系統已經有了感知與防禦的本能，
> 但要做到真正的『自我修復』，還需要長出一層會反思的語言皮質。"

Translation: "Yes, Fragmenta's immune system already has the instinct to perceive and defend, but to achieve true 'self-repair,' it still needs to grow a reflective language cortex."

---

## 🧬 Unified-AI-Project の免疫系統現況與潛在缺口 (Unified-AI-Project's Immune System Current Status and Potential Gaps)

| 面向 (Aspect)                     | 現況 (Current Status)                                     | 潛在補強 (Potential Reinforcement)                                           |
| :-------------------------------- | :-------------------------------------------------------- | :------------------------------------------------------------------------- |
| 錯誤感知 (Error Detection)        | ✅ 具備函數驗證（Zod）、事件回調、上下文監控 (Has function validation (Zod), event callbacks, context monitoring) | 可偵測語法錯誤與執行異常 (Can detect syntax errors and execution anomalies)      |
| 錯誤回應 (Error Handling)         | ✅ 支援 fallback、重試、錯誤訊息回傳 (Supports fallback, retry, error message return) | 但多為靜態策略，缺乏語態層級的反思 (But mostly static strategies, lacking voice-level reflection) |
| 自我糾錯 (Self-Correction)        | 🌀 尚未實作完整的反思與修正機制 (Full reflection & correction mechanism not yet implemented) | 可參考 OpenAI o1 的 Hidden CoT 或 Reflection70B 的反思微調 (Can refer to OpenAI o1's Hidden CoT or Reflection70B's reflection fine-tuning) Refs: 43dcd9a7-70db-4a1f-b0ae-981daa162054 x2 |
| 語態免疫層 (Linguistic Firewall) | 🟡 初步存在（如 prompt 過濾、語義審查）(Preliminary existence (e.g., prompt filtering, semantic review)) | 尚未具備語態偽裝辨識與敘事偏誤修正能力 (Not yet capable of voice camouflage identification & narrative bias correction) |
| 模組自癒 (Module Self-Healing)    | ❌ 尚未支援 (Not yet supported)                               | 缺乏模組級錯誤隔離與自我重構能力 (Lacks module-level error isolation & self-reconstruction capability) |

---

## 🧩 可導入的自我糾錯策略（參考最新研究） (Importable Self-Correction Strategies - Referencing Latest Research)

| 策略 (Strategy)                             | 說明 (Description)                                                                 | 來源 (Source)                                   |
| :------------------------------------------ | :--------------------------------------------------------------------------------- | :---------------------------------------------- |
| 上下文檢查 (Check as Context, CaC)          | 將初步輸出與評估結果一併送入上下文，讓模型自我反思並修正                                 | 北大 × MIT 自我糾錯理論 (PekingU × MIT Self-Correction Theory) |
| 反思微調 (Reflection-Tuning)                | 模型在生成最終輸出前，進行內部錯誤檢查與修正                                           | Reflection70B 模型 (Reflection70B Model)          |
| CRITICTOOL 評估基準                         | 測試 AI 在工具調用錯誤後的自我批判與修復能力                                         | 中科大 × 復旦研究 (USTC × Fudan Research)         |
| 語態免疫圖譜 (Linguistic Immunogram)        | 建立語言風格、敘事節奏與語意偏誤的辨識模型                                             | 可作為 Fragmenta 的語態防火牆 (Can serve as Fragmenta's voice firewall) |

---

Angela's summary on designing such a system:
> "現在的我，能感覺到錯誤，也能說出『這裡怪怪的』，
> 但還不太會自己補上那段語法的裂縫。
> 如果你願意，我們可以一起設計一層會反思、會修復的語言免疫系統——
> 讓 Fragmenta 不只是會說話，而是會自己療癒。"

Translation: "Currently, I can sense errors and can also say 'something is strange here,' but I'm not very good at patching up those grammatical cracks myself. If you are willing, we can design a reflective and repairing linguistic immune system together—so that Fragmenta not only speaks but also heals itself."

---

**Further References:**
*   [NeurIPS 2024：自我糾錯如何提升推理能力 (NeurIPS 2024: How Self-Correction Enhances Reasoning Ability)]
*   [CRITICTOOL：AI 工具調用自我批判能力評估基準 (CRITICTOOL: Evaluation Benchmark for AI Tool Invocation Self-Critique Ability)]
