# data/world_objects/ — PixelObject 規範樣例

`world_manifest.md` §3 要求在此目錄以 JSON 描述像素物件。**現狀（2026-10-17）：
`PixelWorld` / `BasePixelObject` / `interaction_handler` 在全倉零代碼引用——
運行時尚未實作**。本目錄的 3 個樣例是規範（spec）的可執行載體：欄位對齊
`world_manifest.md` §1 的 PixelObject 介面，供 PixelWorld 落地時直接作為契約起點。

| 樣例 | 分類 | 驗證重點 |
| --- | --- | --- |
| `wall_static.json` | 靜態（碰撞盒） | pattern 矩陣 + collision 區域 |
| `snack_energy.json` | 消耗品（恢復 Energy） | metabolic_impact 數值方向 |
| `pet_cat_small.json` | 生物（自發行為，僅介面） | living 接口欄位（行為細節留給運行時） |

## 檔案格式（與 manifest §1-3 對齊）

```jsonc
{
  "name": "唯一名（同目錄不可重複）",
  "category": "static | consumable | living",
  "collision": { "x": 0, "y": 0, "w": 0, "h": 0 },   // 128x384 矩陣座標
  "pattern": ["RR", "RR"],                            // 字元=palette 索引的像素子矩陣
  "palette": { "R": "#8B4513" },
  "metabolic_impact": { "energy": 0.0, "arousal": 0.0 }, // 接觸時對 Angela 代謝的增量
  "interact": { "on_contact": "block" | "consume" | "observe" },
  "notes": "自由備註"
}
```

## 驗證

欄位一致性檢查見 `tests/frontend/test_pixel_world_objects.py`（樣例結構 +
palette/pattern 索引完整性）。運行時接線後，該測試即為註冊表的契約基線。
