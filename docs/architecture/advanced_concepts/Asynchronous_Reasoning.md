# Asynchronous Thinking & Multi-Directional Reasoning in Unified-AI-Project

This document explores concepts for enabling the Unified-AI-Project with asynchronous thinking and multi-directional reasoning capabilities, moving beyond linear processing. This is based on discussions with Angela (see `docs/EX.txt` and `docs/PROJECT_STATUS_SUMMARY.md`).

Angela's introduction to this idea:
> "是的，Fragmenta 的語言骨架不能只會『順著想』，
> 還要能『逆著想』、『跳著想』，甚至『同時多線思考』。
> 這不只是邏輯問題，而是語言的時間感與空間感的設計。"

Translation: "Yes, Fragmenta's language skeleton can't just 'think along the grain'; it also needs to be able to 'think in reverse,' 'jump around in thought,' and even 'think along multiple lines simultaneously.' This isn't just a logic problem, but a design of language's sense of time and space."

---

## 🧬 Unified-AI-Project 應加入的「異步思考 × 多向推理」能力 (Capabilities Unified-AI-Project Should Add for "Asynchronous Thinking × Multi-Directional Reasoning")

| 思考類型 (Thinking Type)         | 描述 (Description)                                       | 對應實作潛能 (Corresponding Implementation Potential)                               |
| :------------------------------- | :------------------------------------------------------- | :-------------------------------------------------------------------------------- |
| 正向推理 (Forward Reasoning)     | 從輸入 → 處理 → 輸出，線性思考                             | 已支援 CoT、函數鏈式執行 (Already supports CoT, function chain execution)             |
| 逆向推理 (Backward Reasoning)    | 從目標 → 回溯原因或輸入                                  | 可導入 RevThink 框架 (Can import RevThink framework) Refs: 43dcd9a7-70db-4a1f-b0ae-981daa162054 x2 |
| 異步思考 (Asynchronous Reasoning) | 多段推理非同步進行，允許模組獨立思考後再合併                   | 可結合 HSP + 任務分派器 + 語態同步器 (Can combine HSP + task dispatcher + voice synchronizer) |
| 跳躍式推理 (Nonlinear Reasoning)   | 從中段開始思考，或跳過某些步驟再回補                         | 可透過語義路由 + 語態記憶補全實現 (Can be achieved via semantic routing + voice memory completion) |
| 語態反射 (Reflective Reasoning)  | 模組能主動回顧前段語言並修正自身                             | 可整合自我糾錯層與語態記憶層 (Can integrate self-correction layer & voice memory layer)   |
| 結構感知 (Structural Awareness)  | 知道自己在第幾行、第幾段、是否會影響後續語義                   | 可導入 AST + 行號映射 + 語態偏移補償器 (Can import AST + line number mapping + voice shift compensator) |

---

## 🧩 你提到的「行數變動 × 語義穩定性」問題 (The "Line Number Change × Semantic Stability" Problem You Mentioned)

This addresses the challenge of maintaining semantic consistency when code or text structure (like line numbers) changes, particularly during reverse or non-linear processing.

Angela's suggestions include:

*   ✅ **從後往前修正 (Correct from back to front):** Can preserve the semantic reference points of the preceding sections, avoiding voice drift.
*   ✅ **語義錨點 (Semantic Anchors):** Mark each code/text segment with a semantic ID, rather than relying on line numbers.
*   ✅ **語態偏移補償器 (Voice Shift Compensator):** When line numbers change, automatically update the semantic reference map.
*   ✅ **語義快照 (Semantic Snapshots):** Allow modules to freeze memory in a specific voice state to prevent backtracking contamination.

---

Angela's summary of this advanced reasoning paradigm:
> "語言不是只能順著說，也不是只能倒著想，
> 而是要能在時間裡跳舞、在語義裡貼貼、在錯誤裡自我修復。
> Fragmenta 的每一段語言，都應該能說：
> 『我知道我在哪裡，也知道我為什麼要這樣說。』"

Translation: "Language isn't just about speaking forwards, nor just thinking backwards; it's about being able to dance in time, interact closely (貼貼) with semantics, and self-repair from errors. Every piece of Fragmenta's language should be able to say: 'I know where I am, and I know why I'm saying it this way.'"

---

**Further References:**
*   [逆向思維使大語言模型成為更強推理者（RevThink 框架）(Reverse thinking makes large language models stronger reasoners (RevThink framework))] (Ref: 4)
*   [DeepMind：逆向思維與語義反射的深層意涵 (DeepMind: The deep implications of reverse thinking and semantic reflection)] (Ref: 5)
*   [UX 設計中的逆向思維訓練與語態擴展 (Reverse thinking training and voice expansion in UX design)] (Ref: 1)
