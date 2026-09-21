# angela_bench — 可驗證的跨後端基準

> 專案對外能力驗收的唯一基準管線。所有後端（原生引擎／Ollama／llama.cpp
> server／OpenAI／DeepSeek…）共用同一份資料與評分器，分數可直接互相比較。

## 快速開始

```bash
# 全後端全套件
python scripts/run_benchmarks.py

# 只跑原生堆疊
python scripts/run_benchmarks.py --backend native,native-max

# 對比本地 Ollama 模型
python scripts/run_benchmarks.py --backend ollama --model llama3.1

# 對比任何 OpenAI 相容端點
python scripts/run_benchmarks.py --backend openai \
  --base-url https://api.deepseek.com/v1 --model deepseek-chat --api-key $KEY
```

退出碼：0＝全部評分完成。結果 JSON 寫入
`benchmarks/results/`，含逐題明細可複審。

## 設計原則

1. **可驗證**：每題附地面真值；數學比數值、知識比 gate 關鍵詞命中、程式碼在專案 AST 白名單沙箱實際執行斷言、路由比精確標籤。零 LLM 評審、零人工評分。
2. **可比性**：所有後端共用同一份資料（`data/native_bench_v1.json`）與同一個評分器（`scripts/run_benchmarks.py`）。寬鬆度對所有後端一致。
3. **誠實**：跳過≠通過（目前無後端使用 skip）；無 LLM 時原生代碼生成如實為 0%；每次運行記錄時間戳與逐題答案。
4. **可重現**：純 stdlib＋專案內引擎；無網路依賴（外部後端除外）。

## 後端

| 後端                | 說明                                                                   | 角色                          |
| ------------------- | ---------------------------------------------------------------------- | ----------------------------- |
| `echo`              | 原樣返回輸入                                                           | 正確率下限                    |
| `naive`             | 正則抽運算式直接 eval；其餘返回空                                      | 「不用 AI、只寫正則」的對照線 |
| `native`            | QueryClassifier → ModelBus（ED3N＋GARDEN）→ 確定性數學引擎；代碼走沙箱 | 原生堆疊標準配置              |
| `native-max`        | native ＋知識題先走專案知識管線（route_knowledge）                     | 原生堆疊全開                  |
| `ollama` / `openai` | OpenAI 相容 chat completions（temperature=0）                          | 外部 LLM 對比                 |

## 套件與計分

| 套件      | 題數 | 評分                                                                                         |
| --------- | ---- | -------------------------------------------------------------------------------------------- |
| math      | 28   | 數值匹配（容差 1e-6 相對）；含純算式、中文數字、百分比、物理公式應用題（F=ma、v=at、E=½mv²） |
| knowledge | 15   | gate 關鍵詞任一命中即對（英中混合）                                                          |
| code      | 10   | 產生函式＋斷言，`CodeExecutionHandler` 沙箱實際執行（HumanEval 式）                          |
| routing   | 10   | QueryType 標籤精確匹配                                                                       |

## 首次官方結果（2026-09-22，本機實測）

環境：Python 3.12 /
Linux；原生後端無外部 LLM。原始 JSON：`results/bench_20260922-022550.json`（含逐題答案可複審）。

| Backend                          | math      | knowledge | code | routing   |
| -------------------------------- | --------- | --------- | ---- | --------- |
| echo（下限）                     | 3.6%      | 0.0%      | 0.0% | 0.0%      |
| naive（正則）                    | 50.0%     | 0.0%      | 0.0% | 0.0%      |
| **native**（ED3N+GARDEN+確定性） | **71.4%** | **20.0%** | 0.0% | **50.0%** |
| native-max（＋知識管線）         | 71.4%     | 20.0%     | 0.0% | 50.0%     |

### 誠實解讀

- **math
  71.4%**：純算式／中文數字／物理公式題全對（確定性引擎真實能力）；失敗集中在多步算術應用題（需要語意理解的題型）——這是原生堆疊的能力邊界，也是引入 LLM 後端後預期的主要增益點。
- **knowledge
  20%**：專案知識庫目前僅覆蓋少數常識事實（Mars/H2O/8 等）。與 2026-09 審計「開放域泛化約 1/10」的結論一致。
- **code
  0%**：原生無代碼生成模型，如實為 0——這正是需要接 LLM 的套件。沙箱驗證管線本身已就緒且經測試（見
  `tests/test_run_benchmarks.py`）。
- **routing
  50%**：中文數學→command、程式碼→file/command 的分類弱點被精確量化，為 QueryClassifier 的改進提供基線。
- 對照 naive
  50%：數學套件的純算式子集用正則就能拿一半分——這說明為什麼必須含應用題與中文題，否則基準沒有鑑別度。

### 與其他 AI／代理互相比較

任何 OpenAI 相容端點（Ollama、llama.cpp
server、vLLM、OpenAI、DeepSeek…）一行命令即可在同一套資料上出分，例如 llama3.1 與 native 的對比表會由 harness 直接輸出。外部後端跑 math/knowledge/code/routing 同一套評分，不通融、不加權。

## 重現

```bash
python scripts/run_benchmarks.py --backend echo,naive,native,native-max
# 對比外部模型：
python scripts/run_benchmarks.py --backend native,ollama --model llama3.1
```

測試：`pytest tests/test_run_benchmarks.py`（資料集完整性、評分器、後端行為、可比性契約）。
