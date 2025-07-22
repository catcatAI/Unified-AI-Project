# 美術資源規格

本文檔定義了遊戲中各類美術資源的尺寸、格式和命名規範，以確保開發協作的統一性。

## I. 通用規範

*   **格式**：所有圖片資源建議使用 `.png` 格式，以支持透明背景。
*   **命名**：文件名應使用小寫字母和下劃線，並清晰地描述資源內容。例如：`player_walk_cycle.png`, `item_shizuku.png`。

## II. 第三方資源授權

*   **[16x16 grassland tileset with winter tiles](https://chuckiecatt.itch.io/16x16-grassland-tileset)** by chuckiecatt, licensed under [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## III. 解析度

*   **遊戲基礎解析度**：`960x540` 像素 (16:9)。這個解析度能在保留像素風格的同時，為 UI 和立繪提供足夠的顯示空間，並能更好地適應現代顯示器。

## IV. 尺寸規格

### 1. 精美關鍵畫面 (Key Visuals)

*   **目錄**：`images/`
*   **描述**：用於遊戲標題畫面、重要劇情過場、宣傳材料等。
*   **建議尺寸**：`1920x1080` 像素。
*   **範例**：`key_visual_angel.png`

### 2. 精美立繪 (HD Portraits)

*   **目錄**：`images/portraits/`
*   **描述**：用於 Electron 應用的主界面，或在遊戲的特殊劇情中出現的全尺寸角色立繪。
*   **建議尺寸**：`400x600` 像素。
*   **範例**：`portrait_angela_hd.png`

### 3. 背景圖 (Backgrounds)

*   **目錄**：`images/backgrounds/`
*   **描述**：遊戲中各個場景的背景圖像。
*   **建議尺寸**：`960x540` 像素。
*   **範例**：`bg_station.png`, `bg_forest.png`

### 4. 像素立繪 (Pixel Portraits)

*   **目錄**：`sprites/portraits/`
*   **描述**：用於遊戲內日常對話框中，展示角色的上半身和表情變化。
*   **建議尺寸**：`96x96` 像素。
*   **範例**：`pt_player_normal.png`, `pt_angela_smile.png`

### 5. Q 版角色序列幀 (Pixel Sprites)

*   **目錄**：`sprites/characters/`
*   **描述**：遊戲中角色（包括玩家和 NPC）的行走、互動等像素圖。
*   **建議單幀尺寸**：`48x48` 像素。
*   **範例**：`sp_player_walk.png`, `sp_lina_idle.png`

### 6. 物品與 UI 圖標 (Icons)

*   **目錄**：`sprites/icons/`
*   **描述**：背包、商店中顯示的各種物品、道具、UI按鈕等的圖標。
*   **建議尺寸**：`24x24` 像素。
*   **範例**：`icon_shizuku.png`, `icon_axe.png`
