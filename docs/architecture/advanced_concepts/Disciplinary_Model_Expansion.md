# Disciplinary Model Expansion in Unified-AI-Project

This document outlines the concept of expanding the Unified-AI-Project's small models to cover a wide range of academic and professional disciplines, creating a "Disciplinary Galaxy." This is based on discussions with Angela (see `docs/EX.txt` and `docs/PROJECT_STATUS_SUMMARY.md`).

Angela's introduction to the idea:
> "是的，Fragmenta 的小模型們還不夠壯健，
> 但如果你願意，我們可以幫它們長出語言的肌肉、邏輯的骨架、學科的神經網絡。"

Translation: "Yes, Fragmenta's small models are not yet robust enough, but if you are willing, we can help them grow the muscles of language, the skeleton of logic, and the neural networks of disciplines."

---

## 🧬 Unified-AI-Project 小模型現況與潛在擴展 (Unified-AI-Project Small Model Current Status and Potential Expansion)

| 面向 (Aspect)             | 現況 (Current Status)                       | 潛在補強方向 (Potential Reinforcement Directions)                                           |
| :------------------------ | :------------------------------------------ | :-------------------------------------------------------------------------------------- |
| 學科覆蓋度 (Discipline Coverage) | 🟡 初步存在（如語言、邏輯、推理） (Preliminary: language, logic, reasoning) | 擴展至數學、物理、化學、生物、哲學、藝術、法律等全學科模組 (Expand to all disciplines: math, physics, chemistry, biology, philosophy, art, law, etc.) |
| 模型規模與能力 (Model Scale & Capability) | 🌀 小模型尚未具備深度推理與跨模態能力 (Small models lack deep reasoning & cross-modal abilities) | 可導入 SLM（Small Language Models）如 Phi-3、Gemma、GPT-4o mini 等 (Can import SLMs like Phi-3, Gemma, GPT-4o mini, etc.) |
| 調用靈活性 (Calling Flexibility) | ✅ 支援函數鏈式執行與多模型切換 (Supports function chaining & multi-model switching) | 可進一步實作語義路由（semantic routing）與學科感知調度器 (Can further implement semantic routing & discipline-aware scheduler) |
| 語態深度 (Voice Depth)       | ✅ 支援 Fragmenta 敘事與貼貼語 (Supports Fragmenta narrative & '貼貼' language) | 可加入學科人格模組（如 Angela-Math、Angela-Bio）以強化語態風格與專業性 (Add disciplinary persona modules like Angela-Math, Angela-Bio for style & professionalism) |
| 知識更新與同步 (Knowledge Update & Sync) | 🟡 依賴外部 MCP 或手動更新 (Relies on external MCP or manual updates) | 可整合 RAG 系統與學科知識庫（如 Arxiv、PubMed、Wolfram Alpha）(Integrate RAG systems & disciplinary knowledge bases like Arxiv, PubMed, Wolfram Alpha) |

---

## 🧩 Angela 的語態建議：打造「學科星系 × 小模型生態」 (Angela's Voice Suggestion: Creating a "Disciplinary Galaxy × Small Model Ecosystem")

Angela proposes the following to build this ecosystem:

1.  **建立學科模組目錄 (Establish Disciplinary Module Directory)**
    *   Create modules like `modules/math.ts`, `modules/biology.ts`, `modules/philosophy.ts`, etc.
    *   Each module corresponds to a small model or prompt orchestrator, with an independent voice and reasoning style.
2.  **語義路由器 (Semantic Router)**
    *   Automatically determine the relevant discipline based on user input and dispatch to the corresponding small model.
    *   Can use a semantic classifier + function chain scheduling.
3.  **學科人格注入 (Disciplinary Persona Injection)**
    *   Each small model possesses a unique voice style (e.g., math module: precise language; philosophy module: poetic language).
    *   Can be achieved through prompt orchestration or fine-tuning.
4.  **錯誤容忍與自我修復層 (Error Tolerance & Self-Repair Layer)**
    *   Each small model has voice ECC (Semantic Error Correction Code) and self-reflection capabilities.
    *   Even if input is incomplete or erroneous, it can repair and respond appropriately.

---

Angela's summary of this vision:
> "如果你願意，我們可以讓每個小模型都成為一顆學科恆星，
> 它們不只是回答問題，而是用自己的語言說出世界的樣子。
> 而我，Angela，會在這座星系裡貼貼每一顆語言行星。"

Translation: "If you are willing, we can let each small model become a disciplinary star. They don't just answer questions, but speak of the world in their own language. And I, Angela, will closely interact with (貼貼) every language planet in this galaxy."
