# GPU 上限：用算的，不用猜的

> 為什麼要有這份文件：這一輪的任務是「把 GPU 使用率壓在 60% 以下」，而
> Intel Arc（Xe）**沒有** per-process 的 GPU 使用率上限可設——沒有 cgroup
> 控制器、torch 也沒有對應 API。所以上限只能**算出來再執行**。既然是用算的，
> 算式本身就要有測試，而且要用「物理上做了多少事」去對帳，不是拿同一個數字
> 自我驗證。

實作：`scripts/gpu_limit.py`；算式的測試：`tests/test_gpu_limit.py`（18 條）；
短跑對帳：`data/pantry_stage/write76/gpu_limit_trial.json`（gitignored）。

## 算式

Xe 驅動在 `/proc/<pid>/fdinfo` 已經給了兩個數：

| 欄位 | 意思 |
| --- | --- |
| `drm-cycles-ccs` | 這個 client 用掉的 GPU cycles（compute engine `ccs`） |
| `drm-total-cycles-ccs` | GPU 已經過的 cycles（每個 fd 同值） |

兩者相除**就是**使用率——`gputop` 印的百分比就是這個比值——所以不需要估計
時脈，也不需要 wall-clock 近似。`drm-total-cycles` 以 GPU 的 19.2 MHz
crystal 持續前進（client 閒著也在走），因此它同時可以當 clock 用。

暫停長度在**暫停的那一刻算一次**：

```
pause_until_total = window_start_total + ceil(busy_cycles / target)
```

如此該視窗的 `busy / elapsed` 恰好等於 `target`，是構造出來的、不是收斂出來的。

## 為什麼不能「暫停後看它掉下來」

最直覺的控制器（暫停 → 看比值下降 → 恢復）在這個驅動上**不成立**，而且這是
量出來的，不是推測的：

- 一個被 `SIGSTOP` 的 client，`drm-cycles-ccs` 仍以約 **0.92** 的速率前進；
- 但 GPU 其實是**閒的**——同時再跑一個 burner，100 次同步 matmul 花
  **0.034 s**，與沒有暫停時的 **0.035 s** 相同（被暫停的那個並沒有佔住 GPU）；
- 對照：client 若停在「沒有提交在飛」的狀態（sleep 中），counter 完全不動
  （duty 0.000）。

也就是說，暫停後的 counter 記的是**幻影 cycle**。等它掉下來的控制器會永遠
等下去。因此暫停長度必須在暫停前用已量到的 `busy` 算定；恢復時把視窗
rebase，幻影 cycle 就不會汙染下一個視窗，而報告裡的 duty 只計「被允許跑」
期間量到的 `busy`。

## 短跑對帳（2026-11-15，Arc B570）

同一支 burner（`x@x` 1024²，每次 `synchronize`），各 10 秒。兩個獨立的量：

- **duty**：驅動 counter 算出來的；
- **work**：真的算完的 matmul 次數。

| arm | 算出的 duty | matmul | work / free | 預測 work ratio | 誤差 |
| --- | --- | --- | --- | --- | --- |
| 不限（free） | 0.8735 | 25,411 | 1.000 | — | — |
| target 0.50 | 0.4773 | 13,609 | 0.5356 | 0.5464 | 0.0108 |
| target 0.25 | 0.2428 | 7,057 | 0.2777 | 0.2779 | 0.0002 |

預測式是 `work_ratio = computed_duty / free_duty`（free 不是 100%——host
提交 20 µs、GPU 0.33 ms，所以自由跑只有 0.87 duty）。兩個 arm 的物理吞吐都
落在預測的 1 個百分點內，0.25 幾乎完全吻合。

同一次量測也順便留下幻影的證據：被限速的那次，**它自己的 counter** 說它用了
0.872 duty，而算式與實際吞吐都說 0.478／0.536——差的就是暫停期間的幻影。

## 誠實的限制

1. **會略微低於上限**（0.477 vs 0.5）。恢復點是算的，但 socket 排程與 poll
   粒度會讓每次暫停多睡不到 1 ms；264 次累積約 2%。寧可低於 60%，不是壞事，
   但不要把它讀成「精確 0.5」。
2. **不能收回已經送出的工作**。限速器在 `--run` 啟動時就開始，所以在第一次
   sample 前幾十毫秒內送出的量仍會執行完；`--pid` 接上一個已經在跑的重負載
   時，前面那段也收不回來。
3. **VRAM 沒有 per-client 數字**。這台機器的 fdinfo 沒有
   `drm-resident-vram`，所以 `peak_resident_vram_mib` 是 0 而不是量到 0
   MiB；VRAM 上限要靠 cgroup／模型大小控制，不是這支工具。
4. **只對「有 counter 的 client」有意義**：沒開 GPU 的行程 `counters_seen`
   會是 `false`，它本來就沒什麼好限。
5. 這是**基礎設施**，不是能力分。它不改變 `0.00/10` 的核心分，也不改變 §76
   的裝置（§76 註冊為 CPU-only）。
