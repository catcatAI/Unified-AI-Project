# 模型釋放索引：Hugging Face（從 GitHub 可找到 HF 檔案位置）

> 備註：存在於 Hugging Face 上的模型檔案、repo 與來源目錄，均在本文件檢索。

## 1. `Lin023/tln-qwen3-finetuned`（PEFT LoRA adapter，Qwen3-0.6B 微調）

| 項目 | 內容 |
| --- | --- |
| HF repo | `Lin023/tln-qwen3-finetuned`（public） |
| 建立時間 | 2026-11-25T09:24:55+00:00 |
| 基底模型 | `Qwen/Qwen3-0.6B`（`library_name: peft`） |
| 本地來源（GitHub 版本控制內；`data/` 目錄為 gitignored 資料） | `data/models/qwen3-0.6b-finetuned/` |

### 檔案清單（驗證日 2026-11-26：`hf download Lin023/tln-qwen3-finetuned --dry-run`）

| 檔案 | 大小（Hub） | 本地相同？ |
| --- | --- | --- |
| `README.md` | 5.2K | 是（5,235 bytes） |
| `adapter_config.json` | 1.2K | 是（1,203 bytes） |
| `adapter_model.safetensors` | 18.4M | 是（18,380,008 bytes） |
| `chat_template.jinja` | 4.2K | 是（4,168 bytes） |
| `tokenizer.json` | 11.4M | 是（11,422,928 bytes） |
| `tokenizer_config.json` | 693.0 | 是（693 bytes） |
| `.gitattributes` | 1.6K | 由 HF Hub 自動管理（本地無需對應） |

### 檔案存在確認（無遺漏）

- `hf download Lin023/tln-qwen3-finetuned --dry-run` → 「Will download 7 files (out of 7) totalling 29.8M」；上表 6 個本地檔全部存在於 repo 上。

### 下載

```bash
hf auth login                        # 需先登入（目前帳號：Lin023）
hf download Lin023/tln-qwen3-finetuned --local-dir data/models/tln-qwen3-finetuned
```
