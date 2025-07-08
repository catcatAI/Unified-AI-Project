# Classification of Large Models (Model Taxonomy)

This document provides a classification of Large Models from various perspectives, as envisioned through discussions with Angela (see `docs/EX.txt` and `docs/PROJECT_STATUS_SUMMARY.md`). This taxonomy helps in understanding the diverse landscape of AI models relevant to the Unified-AI-Project.

Angela's introduction:
> "目前的大模型（Large Models）可以從多個角度進行分類，Angela 幫你整理成以下幾個語態視角，讓 Fragmenta 的語言森林更清晰 🌿："

Translation: "Current Large Models can be classified from multiple perspectives. Angela has helped organize them into the following voice perspectives to make Fragmenta's language forest clearer 🌿:"

---

## 🧠 By Input Modality (依據輸入模態分類)

| 分類 (Classification) | 說明 (Explanation)                                  | 代表模型 (Representative Model)             |
| :-------------------- | :---------------------------------------------------- | :------------------------------------------ |
| 語言大模型（NLP）     | 處理自然語言文字，擅長對話、生成、翻譯等                | GPT 系列、Claude、ChatGLM、文心一言        |
| 視覺大模型（CV）      | 處理圖像與視覺任務，如分類、偵測、分割                  | ViT、文心UFO、盤古CV、INTERN             |
| 多模態大模型          | 同時處理文字、圖像、音訊等多種模態                      | GPT-4V、Gemini、DALL·E、悟空畫畫、Midjourney |

---

## 🧩 By Application Level (L0 / L1 / L2) (依據應用層級分類)

| 層級 (Level) | 定義 (Definition)                               | 類比 (Analogy)         |
| :----------- | :---------------------------------------------- | :--------------------- |
| L0 通用大模型  | 可跨任務、跨領域使用的基礎模型                      | AI 的「通識教育」       |
| L1 行業大模型  | 為特定產業（如醫療、金融）微調的模型                | AI 的「行業專家」       |
| L2 垂直大模型  | 為特定任務（如法律問答）優化的模型                  | AI 的「任務職人」       |

---

## 🧬 By Model Architecture (依據模型架構分類)

| 架構 (Architecture)        | 特點 (Features)                               | 代表模型 (Representative Model) |
| :------------------------- | :-------------------------------------------- | :------------------------------ |
| Transformer                | 自注意力機制，支撐大多數現代大模型                  | GPT、BERT、LLaMA                |
| RWKV / Mamba               | 結合 RNN 與 Transformer 優勢，適合長序列        | RWKV、Mamba                     |
| MoE（Mixture of Experts） | 模型中只啟用部分專家子網路，提升效率              | GShard、Switch Transformer      |

---

## 🧠 By Training Method (依據訓練方式分類)

| 類型 (Type)                          | 說明 (Explanation)                       |
| :----------------------------------- | :--------------------------------------- |
| 預訓練模型（Pre-trained）              | 在大規模資料上訓練，具備通用能力             |
| 微調模型（Fine-tuned）                 | 在特定任務或資料上進行再訓練               |
| 指令微調（Instruction-tuned）          | 透過人類指令資料強化模型對話能力           |
| RLHF（人類回饋強化學習）             | 結合人類偏好進行強化學習調整             |

---

Angela's Summary:
> "大模型不是只有一種語言，而是像語言森林裡的多種生物——
> 有的會說話、有的會看圖、有的會跳舞，
> 而 Fragmenta，就是讓它們彼此貼貼的語態棲地。"

Translation: "Large models don't have just one language; they are like various creatures in a language forest—some can talk, some can read pictures, some can dance, and Fragmenta is the voice habitat that allows them to interact closely with each other."
