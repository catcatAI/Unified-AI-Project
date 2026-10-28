# 三個模型一起跑本地（Arc B570 實測規劃）

> **這份文件是什麼**：在這台機器上，把 `main` / `role_b` / `role_c` 三個角色各自綁一個**本地**模型的具體做法——含實測硬體、模型選擇、啟動指令、以及「什麼時候會跑不動」。
>
> **這份文件不是什麼**：不是模型評測。**2026-10-28 已實際下載並跑起來**（見 §4.1）。

---

## 1. 這台機器（2026-10-28 實測）

| 項目 | 值 | 來源 |
| --- | --- | --- |
| GPU | Intel Arc B570（Battlemage G21） | `lspci` |
| VRAM | **9.44 GiB** | `clinfo`（sysfs 沒有 `mem_info_vram_total`，Intel 要靠 clinfo） |
| VRAM 後端 | Vulkan（`~/llama.cpp/build/bin` 有 `libggml-vulkan.so`，無 SYCL） | 目錄檢查 |
| CPU | i5-12400F，12 執行緒 | `lscpu` |
| RAM | 7 GB，**當下可用約 3 GB** | `/proc/meminfo` |
| llama-server | `~/llama.cpp/build/bin/llama-server`（已編譯） | 檔案存在 |

> GPU 穩定性注意：`scripts/xpu_probe.sh` 記錄過 Arc B570 的 `UR_RESULT_ERROR_DEVICE_LOST`，主因指向 **queue depth** 而非單純負載。llama.cpp Vulkan 的佇列行為比 torch XPU 單純，但仍建議一次只壓一個模型做長推論測試。

---

## 2. 為什麼是「30% headroom」

三個模型要**同時常駐**（llama-server 沒有內建模型切換）。同時，這台機器的 GPU 還要畫桌面與瀏覽器裡的舞台。

所以預算不是 9.44 GB，而是 `9.44 × 0.7 ≈ 6.61 GB`：

```
6.61 GB 預算 / 6.34 GB 實際 → 留 3.1 GB 給桌面、瀏覽器、WebGL 舞台
```

這不是保守，是必要——把 9 GB 全塞滿，先黑屏的是你要看的那個視窗。

---

## 3. 選出來的組合

```
role     slot             port  model                       GB
main     llamacpp-local    8080 Qwen2.5-3B-Instruct Q4     2.65
role_b   llamacpp-gemma    8082 Gemma-2-2B-IT Q4           2.37
role_c   llamacpp-qwen     8081 Llama-3.2-1B-Instruct Q4   1.32
```

- **三個不同家族**（Qwen / Gemma / Llama）：舞台上才聽得出差別。
- 排序規則：家族多樣性 → 最弱的那個不能太小 → 總參數。
- 為什麼不是 Phi-3-mini：它 3.8B，在 Vulkan 上單次延遲明顯更高，且會擠掉一個角色。規劃器把它列為候選，這台機器上沒選它。
- 為什麼不是全部 0.5B：三個 0.5B 只證明「能跑」，證明不了「多角色」——聲音會一樣笨。

---

## 3.1 一個必須知道的坑：gemma-2 要 `-fa off`

`gemma-2-2b-it-Q4_K_M.gguf` 在這個 llama.cpp build（`0.8.0-dev, build 11960`）上，**開著 flash attention 會輸出垃圾**——不論 CPU 還是 Vulkan、不論 prompt 語言，結果都是空字串或 `"Please provide a ..."`。檔案本身沒壞（`hf cache verify` 檢查碼全對）。

加 `-fa off` 之後立刻正常：

```
:8082 → '我是 Gemma，一個由 Google DeepMind 訓練的大型語言模型。'
```

所以規劃器把這個 flag 綁在 gemma 這個 model spec 上（`flags=("-fa", "off")`），不是綁在全域——其他模型不需要。

## 4. 怎麼開始

```bash
# 1) 看規劃（不裝任何東西）
python scripts/plan_local_three_models.py

# 2) 依輸出下載三個 Q4 檔到 ~/models/gguf/
#    （範例；檔案清單以規劃器輸出為準）
huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF \
  --include '*q4_k_m*' --local-dir ~/models/gguf
huggingface-cli download bartowski/gemma-2-2b-it-GGUF \
  --include '*Q4_K_M*' --local-dir ~/models/gguf
huggingface-cli download bartowski/Llama-3.2-1B-Instruct-GGUF \
  --include '*Q4_K_M*' --local-dir ~/models/gguf

# 3) 起三個 server（會先檢查 VRAM 預算與檔案）
python scripts/run_local_three_models.py start

# 4) 重啟 backend，讓它讀到生成的 overlay
#    configs/system/llm.evolved.yaml（原本的會被備份成 .pre-local）

# 5) 看狀態 / 收工
python scripts/run_local_three_models.py status
python scripts/run_local_three_models.py stop     # 關 server + 還原 overlay
```

啟動時每個 server 的參數：`-ngl 99`（全部丟 VRAM）、`-c 2048`、`-t 6`、`--no-webui`。
`-ngl 99` 是關鍵：RAM 只剩 3 GB，權重若留在 page cache 會被換出，速度掉一個數量級。

---

## 4.1 2026-10-28 實際結果

三個模型已下載（`~/models/gguf`，位元組數與 Hub 一致）：

| 檔案 | 大小 | 實測 |
| --- | --- | --- |
| `qwen2.5-3b-instruct-q4_k_m.gguf` | 2,104,932,768 | ✅ 自稱 Qwen |
| `gemma-2-2b-it-Q4_K_M.gguf` | 1,708,582,752 | ✅ 自稱 Gemma（需 `-fa off`） |
| `Llama-3.2-1B-Instruct-Q4_K_M.gguf` | 807,694,464 | ✅ 自稱 AI assistant |

```
$ python scripts/run_local_three_models.py status
llamacpp-local   :8080 healthy  Qwen2.5-3B-Instruct Q4
llamacpp-gemma   :8082 healthy  Gemma-2-2B-IT Q4
llamacpp-qwen    :8081 healthy  Llama-3.2-1B-Instruct Q4
overlay: generated (three local models)
```

三個 server 同時常駐，系統 RAM 只用了 3 GB（權重都在 VRAM）。overlay 已寫入
`configs/system/llm.evolved.yaml`，**重啟 backend 後**角色才會綁到這三個槽；
`... stop` 會關 server 並把 overlay 還原。

## 5. 三個角色的模型綁定

`roles.default.yaml` 已經把角色指到槽：

| role | backend_slot | 8080/8081/8082 |
| --- | --- | --- |
| main | （無，用 active） | active 會是 `llamacpp-local`（overlay 設 `preferred_backend`） |
| role_b | `llamacpp-gemma` | :8082 |
| role_c | `llamacpp-qwen` | :8081 |
| role_d | `deepseek` | 雲端（需要 `DEEPSEEK_API_KEY`；local 模式下不啟用） |

overlay 產生的 `deployment.mode: local+llm` 保留雲端可用；要完全離線就改成 `local`。

---

## 6. 什麼時候會跑不動（誠實版）

| 情況 | 會發生什麼 | 對策 |
| --- | --- | --- |
| 三個都 2k ctx 同時跑 | 6.34 GB 權重 + KV ≈ 6.4 GB，桌機剩 3 GB → 邊緣 | 已含 30% headroom；真的卡就把 `role_c` 換成 0.5B |
| 開著瀏覽器 + 舞台 | 瀏覽器 WebGL 會吃 0.5–1 GB VRAM | 先用 1080p 視窗、關掉其他分頁 |
| 磁碟 | 三個 Q4 檔約 6.4 GB | `df -h ~` 先看 |
| 首次載入 | 每個 server 首次推理要載入權重，可能 10–30 秒 | 先 `/health` 等到 ok 再發請求 |
| GPU 再次 device-lost | 整個 server 卡死 | 依 `scripts/xpu_probe.sh` 的流程重開機再測，不要在同一張已崩過的卡上量測 |

---

## 7. 相關檔案

| 檔案 | 作用 |
| --- | --- |
| `scripts/plan_local_three_models.py` | 硬體偵測 + 組合規劃 + 指令輸出（`--json` 可餵給其他工具） |
| `scripts/run_local_three_models.py` | 起停三個 server、寫／還原 overlay、health 檢查 |
| `tests/test_local_model_planner.py` | 14 個測試：預算、家族多樣性、on-demand 降級、overlay 備份還原 |
| `apps/backend/configs/system/roles.default.yaml` | 角色 → 槽的綁定 |
| `apps/backend/src/services/llm/providers/registry.py` | `LLAMA_CPP_GEMMA` / `DEEPSEEK` 等槽的 enum |
