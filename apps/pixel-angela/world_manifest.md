# Angela Pixel World MOD 開發指南 (v1.0)

本指南定義了如何為 Angela 建立像素棲息地與互動物件。

## 1. 架構定義

- **Grid System**: 使用 `NumPy` 矩陣作為基礎空間，座標 (x, y) 對應螢幕像素。
- **PixelObject Interface**: 所有物體必須實現以下接口：
  - `render()`: 回傳矩陣片段。
  - `interact(angela_state)`: 當 Angela 接觸時產生的物理/生物交互。
  - `metabolic_impact`: 定義該物體如何影響 Angela 的代謝。

## 2. 物件分類

- **靜態 (Static)**: 牆壁、桌腳 (作為碰撞盒)。
- **消耗品 (Consumable)**: 食物 (恢復 `Energy`)、能量飲料 (Boost `Arousal`)。
- **生物 (Living)**: 寵物/動物 (具備自發行為，不需實作細節，僅需介面)。

## 3. MOD 實作流程

> **現狀（2026-10-17）**：`PixelWorld` / `BasePixelObject` / `interaction_handler`
> 尚未實作（全倉零代碼引用）。`data/world_objects/` 已建目錄並附 3 個規範樣例
> （`wall_static` / `snack_energy` / `pet_cat_small`，欄位對齊本文件 §1-2），
> 欄位契約由 `tests/frontend/test_pixel_world_objects.py` 守護——運行時落地時
> 以該目錄為註冊表起點，勿改欄位語意。

1.  在 `apps/pixel-angela/data/world_objects/` 建立對應的 `json` 描述檔。
2.  定義物件的像素矩陣圖案 (128x384 矩陣的子集，樣例以 `pattern`+`palette` 表示)。
3.  在 `PixelWorld`（**待實作**）中註冊該物件的 `(x, y, w, h)` 碰撞區域。

## 4. 擴展接口

若要加入複雜物體，請繼承 `BasePixelObject`，並在 `interaction_handler`
中定義交互。
