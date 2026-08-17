# GARDEN SNN Memory Optimization — Analysis & Plan

> 狀態: active | 日期: 2026-08-17
> 起因: 重訓在 V≈9,200 後反覆 OOM（7.5GB 機器），`snn.pt` 反覆膨脹到 5.3GB。
> 使用者核心洞察: SNN+字典**應該**比普通 AI 有更高壓縮倍率（多 token 共享 cell / 多 cell 共享 token），
> 實作卻讓 10,917 樣本訓練出 5GB 模型。且就算 10GB，也**不該 OOM**——掛載/釋放是工程問題，不是容量問題。

---

## 1. 現況 (實測)

| 項目 | 值 |
|---|---|
| 訓練樣本 | 10,917 (garden) |
| 字典 entries | 9,573 |
| 字典 surface forms | 36,654 → 4× 壓縮到 entries ✓ |
| SNN live V | 20,573 |
| SNN `_W` 分配 | **36,376² = 5.0 GB** (float32) |
| `_W` 浪費率 | (36376²-20573²)/36376² = **68% 死區** |
| checkpoint 檔案 | snn.pt 5.3GB + dictionary.json + engine_meta.json |
| 機器 RAM | 7.5 GB（重訓時約 4.5GB 可用） |

---

## 2. 為何「SNN+字典」該壓縮卻巨大 — 4 個根本原因

### 2.1 稠密 V×V 矩陣存儲（根本原因）

`TensorSNNCore._W` 是 `[V,V]` float32 **稠密**張量（snn_core.py:257）。
- `hebbian_update` 只寫入 `src×tgt` 小區塊（snn_core.py:637-644）→ **稀疏寫入**
- `forward` 只讀 live 切片 `_W[:V,:V]`（snn_core.py:496）→ **稀疏讀取**
- **但存儲是 `[V,V]` 全分配**，未共現的 (i,j) 值=0 照樣佔 4 bytes

→ 字典層壓縮了 4×（forms→entries），但 SNN 層把這 4× 又加倍還回去：
V=20,573 → 稠密 1.7GB，而真實非零連邊（被 Hebbian 碰過的）估計 <5% → 稀疏可縮到 ~百 MB。

### 2.2 加倍成長放大 (`_grow_matrix`, snn_core.py:423-438)

```
target = max(new_size, int(old_size * 2))   # 滿了就 ×2
```
V 到 20,573 時分配跳到 36,376²（=18,188×2，是 preset 9,094 加倍兩次）。
**這是重訓崩潰的直接原因**: 載入 1.6GB 壓縮檔後，新 batch 讓 V 突破 → 加倍 → 又 5GB → OOM。

### 2.3 字典/SNN 不同步 (`_prune_for_growth`, dictionary.py:510-549)

字典到 `max_entries`(=10,000) 時 `_prune_for_growth` 刪低價值條目——
**只刪 dictionary.entries + surface_set，完全不碰 SNN `_W`/`_idx_to_key`**。
→ 字典縮到 9,573，SNN 死 key 累積到 20,573（多出 1 倍），矩陣白大 2×。

### 2.4 max_vocab 配置過大 (compute.default.yaml:124)

```yaml
garden_snn:
  max_vocab: 51812   # → 51,812²×4 = 10GB 矩陣 (註釋明寫 "10 GB model target")
```
在 7.5GB 機器上從配置層就註定 OOM。且 `laptop_normal`/`desktop_igpu` profile 都是 51,812。

---

## 3. 為何「10GB 也不該 OOM」— 載入路徑分析

### 3.1 運行時載入 (providers/garden.py:71-83)

```python
def _get_engine(self):
    if self._engine is None:
        engine = GARDENEngine(compatibility_mode=True)
        engine.load(self.checkpoint)   # np.load / torch.load 整顆進 RAM
```
- **惰性載入**（首次 query 才載，非啟動即載）✓ 但
- **全量載入**（`np.load`/`torch.load` 把整個矩陣 materialize 進 RAM）✗

### 3.2 SNN load (snn_core.py:171-196, 712-724)

- `np.load(npy_path)` → **完整 in-RAM dense copy**（無 mmap）
- `torch.load(..., map_location="cpu")` → 完整進 RAM
- `self._W = state["W"]` → **無 resize、無 clamp、無 compact**，照單全收

### 3.3 現成但未接線的基礎設施

`BinaryStore`（binary_store.py:140-168）已有**完整 numpy.memmap** 實作
（lazy open、r/r+/c 模式、flush/close、V×V float32 shape）。
**但只被 `kg_import.py` 離線 export 使用，SNN 存儲/載入/推理完全沒用上。**

### 3.4 結論

「10GB 不 OOM」的關鍵 = **memmap 掛載**（頁面按需載入）+ **稠密→稀疏** 存儲。
前者讓載入不爆 RAM；後者讓根本不需要 10GB。

---

## 4. 修復計畫（依收益排序）

### Fix A — `_grow_matrix` 加速成長 + 死區回收（立即, 最直接）

問題: `_compact` 的 `alloc = max(new_size, cap, int(old_W.shape[0]))`（snn_core.py:382）
→ **永遠不小於目前分配**，無法縮。`_grow_matrix` 倍增至 2×。

修復:
1. `_compact` 改 `alloc = max(new_size, int(old_W.shape[0]))`（去掉 `cap` 從 max）
   → 保持或縮小，不放大到 max_vocab。
2. `_grow_matrix` 成長步距從 `×2` 改 `×1.25`（減少過度分配，攤平仍 O(V²)）。
3. `save()` 前強制 compact 到 live V（或 save 只存 live 切片 `_W[:V,:V]`）。

### Fix B — 字典 prune 連動 SNN（根治死 key）

問題: `_prune_for_growth`（dictionary.py:510）刪字典條目不連動 SNN。

修復: 字典 prune 後回傳被刪 keys → `VectorDictionary` 或 `GARDENEngine.learn_batch`
呼叫 `snn.compact_removed(removed_keys)` 同步移除 `_W` 對應行列 → V 不再死撐。

### Fix C — 稀疏存儲（最大收益）

問題: 稠密 `[V,V]` 浪費 ~95%（未共現對 = 0 照佔）。

修復（分階段）:
- **C1 (checkpoint 稀疏化)**: save 時只存非零 `(i,j,val)` 三元組（COO）→
  5GB → 幾十 MB。load 時重建稠密（或維持稀疏）。**先做，檔案即瘦**。
- **C2 (runtime 稀疏 forward)**: `forward` 用 `scipy.sparse` / torch sparse
  只跑 active rows → 推理記憶體也瘦。**後做（大工程）**。

### Fix D — memmap 載入（10GB 不 OOM）

問題: `np.load`/`torch.load` 全量進 RAM。

修復: 把 `BinaryStore.memmap` 接線到 `snn.load`——
- 若 checkpoint 是 BinaryStore 格式 `.bin` → `np.memmap(..., mode='r')` 掛載，
  頁面按需載入，V=51,812 的 10GB 檔案只佔已存取頁。
- `forward` 讀取自動 page-in（OS 層面），不 OOM。
- **未接線的 BinaryStore 是現成的**，接上即可。

### Fix E — 配置降 max_vocab（工程上直接）

問題: 所有 profile 都 51,812。

修復: 按 RAM 自動降（magic_numbers 已有 `[bytes, %ram]` cascade）。
7.5GB 機器 → max_vocab ≈ 12,000（矩陣 ~576MB），live 分配有上限。
`laptop_normal`/`desktop_igpu`/`laptop_power_saver` 都該有合理的 max_vocab。

---

## 5. 影響評估（保守，其餘保持原樣）

| 修復 | 觸及的檔案 | 影響面 | 風險 |
|---|---|---|---|
| A | snn_core.py | `_grow_matrix`/`_compact`/`save` | 低（純分配邏輯，語義不變） |
| B | dictionary.py + snn_core.py + garden_engine.py | prune→SNN 連動 | 中（新增一個回呼，需測 prune 正確性） |
| C1 | snn_core.py `_save_checkpoint`/`_load_checkpoint` | 檔案格式 | 中（舊檔相容性需保留 torch/npy 讀取） |
| D | snn_core.py `load` + binary_store.py | 載入路徑 | 中（新增 .bin 格式，保留舊格式讀取） |
| E | compute.default.yaml ×2 | 配置 | 低 |

**原則**: 不重寫、不新建大系統。更新/修復現有代碼 + 接線現成的 BinaryStore。
與記憶體無關的行為（字典語義、forward 結果、對話輸出）**保持原樣**。

---

## 6. 驗證計畫

1. 單元測試: `_compact` 能縮小到 live V；`_grow_matrix` 不過度分配
2. 字典 prune 後 SNN V 同步縮小
3. 5GB checkpoint → 稀疏存儲後檔案 <100MB；載入/推理結果與稠密一致
4. memmap 載入 10GB 模擬檔在 7.5GB 機器不 OOM（RSS < 2GB）
5. 重訓 resume 全程 RSS < 3GB，無 OOM
6. `apps/backend/tests/` 全綠

## 7. 決策

- [x] 使用者要求全部實作（A-E）
- [x] 先分析寫 MD → 實作
- [x] 實作後重訓驗證

---

## 8. 實作結果（2026-08-17 實測）

### 8.1 實作摘要（commits）

| 修復 | 實作 | commit |
|---|---|---|
| A | `_grow_matrix` ×2→×1.25+64；`_compact` `alloc=max(new, 1.25×new+64)`（可縮小）；`save` 只存 live 切片；`load` 重新 compact 配置 | `d2d6a4f9` |
| B | `dictionary._prune_for_growth` 記錄 `_pruned_keys` + `drain_pruned_keys()`；`learn_batch` Stage 2c 呼叫 `snn.compact_removed_keys()` | `d2d6a4f9` |
| C1 | `_save_checkpoint` 稀疏 COO（density<30% 才轉）；`_load_checkpoint` 讀取稀疏並 densify | `643b9e59` |
| D | `torch.load(mmap=True)` + `np.load(mmap_mode='r')`；`load()` 只複製 live VxV | `643b9e59` |
| E | `TensorSNNCore.__init__` RAM clamp（capacity cascade，80% RAM）；51812→40131@7.5GB | `643b9e59` |
| 工具 | `scripts/compact_garden_ckpt.py` 一次性遷移（mmap+dead-key 移除+sparse） | `643b9e59` |

### 8.2 驗證數據

**單元層（`_compact` 可縮小）：**
- 2000 keys 訓練 → compact 到 500 keys → `_W` 從 2000² 縮到 **689²**（舊邏輯會固定 51,812²=10GB）
- 1000→2000 keys 成長: 精確 2000²（×1.25，無 2× 死區）

**Checkpoint 遷移（真實污染檔）：**
- 543 MB 稠密 → **13.7 MB sparse COO**（峰值 1.7 GB）
- 5.3 GB 大檔 mmap 載入成功（峰值 5.4 GB，未崩）— 舊邏輯載入即 OOM

**重訓（10,917 乾淨樣本，全程無 OOM）：**
| 里程碑 | V | RSS |
|---|---|---|
| 500 樣本 | 3,844 | 834 MB |
| 2,000 | 7,406 | 1.28 GB |
| 4,000 | 9,920 | 1.82 GB |
| 6,000（首輪 prune+compact） | 9,994→9,103 | 1.61 GB |
| 9,000 | 9,219 | 1.67 GB |
| **10,917（完成）** | **9,473** | 峰值 ~1.8 GB |

- **全程 RSS < 1.9 GB**（舊版 V≈9,200 即 OOM 6.4GB）
- **Fix B 驗證**: prune 1000 條 → `snn.compact_removed_keys` 移除 1000-2000 keys → **字典=SNN=9,473 完全同步**（舊版 desync: 字典 9,573 vs SNN 20,573）
- **Fix C1 驗證**: checkpoint snn.pt **4.4 MB**（舊版 543 MB，123× 壓縮）
- 最終: dict 9,473 = SNN V 9,473，0 污染條目，reflex 36 patterns 正常
- 訓練耗時: 11,116 s（~3.1 小時），22 batches

### 8.3 意外損失（遷移腳本 bug）

- 遷移腳本初次執行時 dictionary key 解析錯誤（`d["entries"]` 是 list 不是 dict），
  導致把 5.3GB 的 9200-batch 乾淨進度 checkpoint 覆寫成 V=0 → 無法恢復。
- 因此改採**全新乾淨重訓**（見 8.2），產物更乾淨（V 與字典同步、0 污染）。
- 教訓: 遷移腳本預設不該覆寫輸入檔（已改為 `--out` 語義風險，正式使用需明確指定）。

### 8.4 剩餘事項

- [ ] C2 (runtime 稀疏 forward) — 大工程，暫緩
- [ ] `forward` 推理品質本身（Hebbian 收斂 ≠ 理解，open-domain 仍 ≈0）— 非記憶體問題