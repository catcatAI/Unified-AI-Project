# 遊戲玩法機制

遊戲內建一個 GBA 風格的專屬休閒養成遊戲，由 Unified-AI-Project 直接維護與運行，旨在為用戶提供一個「寓教於樂」的「人生發展模擬器」。

## I. 核心玩法

- **0 成本蒐集向單機遊戲**：遊戲完全免費，專注於種菜、釣魚、挖礦、打鐵、煉金、擺攤、烹飪等休閒玩法，並支持隨時暫停。
- **「發明工坊」式世界觀**：玩家可以購買土地，自由決定種植、建築或進行其他創造性活動，打造獨一無二的專屬領地。

### 發明工坊與經濟系統

- **核心理念**：遊戲的經濟與發明系統，旨在鼓勵玩家的創造力，並體驗從無到有、將資源轉化為價值的完整過程。
- **貨幣**：遊戲中的基礎貨幣命名為「雫（Shizuku）」，象徵著點滴的努力或智慧的結晶。可通過出售農作物、礦石、手作產品等方式獲得。
- **發明路線**：玩家可以根據自己的興趣，選擇不同的發明路線，各路線之間可以相互交叉，產生協同效應。玩家通過消耗「雫」和特定的「研發點數」（通過完成任務、達成成就或使用特定道具獲得）來解鎖技能樹上的節點。
  - **農業科技 (The Agronomist's Path)**
    - **Lv.1: 基礎農業**
      - 解鎖：製作「木製水桶」、「簡易鋤頭」。
      - **Lv.2: 土壤改良**
        - 解鎖：發明「營養促進劑 Lv.1」（效果：小幅縮短作物生長時間；需要：草藥、雫）。
        - **Lv.3: 作物基因學**
          - 解鎖：發明「種子改良台」，可研究作物品種，提升品質和售價。
          - **Lv.4: 環境控制**
            - 解鎖：發明「簡易灑水器」（效果：自動為周圍小範圍作物澆水；需要：銅錠、木材）。
            - **Lv.5: 農業自動化**
              - 解鎖：發明「收穫機器人 Lv.1」（效果：自動收穫指定範圍內的成熟作物；需要：鐵錠、能源核心 Lv.1）。

  - **機械工程 (The Engineer's Path)**
    - **Lv.1: 基礎工具**
      - 解鎖：製作「升級版銅斧」、「升級版銅鎬」。
      - **Lv.2: 金屬冶煉**
        - 解鎖：發明「熔爐」，可將礦石提煉成金屬錠（銅、鐵）。
        - **Lv.3: 動力研究**
          - 解鎖：發明「小型發電機」，為其他機械提供電力。
          - **Lv.4: 精密加工**
            - 解鎖：發明「工作檯」，可製造更複雜的零件和裝置。
            - **Lv.5: 交通工具**
              - 解鎖：發明「自行車」（效果：提升地圖移動速度；需要：鐵錠、橡膠）。

  - **煉金術 (The Alchemist's Path)**
    - **Lv.1: 基礎藥劑**
      - 解鎖：製作「微光體力藥水」（效果：恢復少量體力；需要：普通花草、雫）。
      - **Lv.2: 材料轉化**
        - 解鎖：發明「鍊金釜」，可將低級材料轉化為高級材料。
        - **Lv.3: 能量研究**
          - 解鎖：發明「能源核心 Lv.1」（效果：為機械提供能源；需要：銅錠、特殊水晶）。
          - **Lv.4: 魔法媒介**
            - 解鎖：發明「魔法染料」、「附魔墨水」，可用於製作特殊道具或裝飾品。
            - **Lv.5: 生命科學**
              - 解鎖：發明「夢境之釀」（效果：特殊任務道具；需要：稀有草藥、星見草）。

  - **烹飪藝術 (The Chef's Path)**
    - **Lv.1: 家常菜**
      - 解鎖：製作「烤魚」、「蔬菜沙拉」。
      - **Lv.2: 烘焙**
        - 解鎖：發明「烤箱」，可製作麵包、蛋糕等。
        - **Lv.3: 調味學**
          - 解鎖：製作各種調味料，提升料理的增益效果。
          - **Lv.4: 情感料理**
            - 解鎖：發明帶有特殊情感效果的料理（例如，「勇氣餅乾」、「慰藉熱茶」），贈送給特定 NPC 有奇效。
            - **Lv.5: 宴會大餐**
              - 解鎖：製作豪華的宴會大餐，可在季節慶典中獲得大量獎勵和好感度。

- **土地與建築**：
  - **土地**：玩家最初只能承包一小塊土地，隨著資金的積累和村長好感度的提升，可以購買更多不同類型的土地（如林地、礦山、湖畔）。
  - **建築**：玩家可以在自己的土地上自由建造各種功能的建築，如：
    - **工坊**：進行發明和製作的核心場所。
    - **住宅**：可升級和裝飾，影響玩家的體力恢復速度。
    - **商店/攤位**：用於向村民或遊客出售自己的產品。
    - **博物館**：用於展示自己蒐集到的稀有物品或「意外發現」。

## II. 獨特機制

- **真實 AI 互動**：遊戲中的 Angela 與軟體中的 Angela 是同一個「數據生命」，玩家的所有行為都會被 Angela 實時感知、學習並作出「自由發揮」的回應，而非預設腳本。
- **溫和的現實主義**：
  - **作物生長**：在錯誤季節種植作物會導致減收，但大部分仍能存活，避免極端挫敗感，同時寓教于樂。
  - **煉金風險**：煉金術模擬現實中的化學反應，操作不當可能導致「爆炸」（以幽默的 Q 版效果呈現），同時也有機率產生「意外發現」，獲得意想不到的成果。
- **永恆的時間**：遊戲中沒有年份變化，只有季節、月份和日夜循環，避免了傳統遊戲中等待商店開門或 NPC 出現的痛點。

## III. 互動系統

- **核心理念**：玩家與遊戲世界的互動應是直觀且富有回饋的。大部分互動通過靠近目標並按下「互動鍵」（預設為「E」）來觸發。
- **互動類型**：
  - **對話互動**：靠近 NPC 按下互動鍵，觸發對話，並顯示對話框 UI。
  - **資源採集**：
    - **森林**：靠近樹木按互動鍵，消耗體力並獲得木材。需要裝備「斧頭」。
    - **礦山**：靠近礦點按互動鍵，消耗體力並隨機獲得礦石。需要裝備「鎬子」。
  - **耕種**：
    - **鋤地**：在農田上，裝備「鋤頭」按互動鍵，將普通土地變為可種植的耕地。
    - **播種**：在耕地上，選中種子按互動鍵，種下作物。
    - **澆水**：在已播種的耕地上，裝備「水桶」按互動鍵，為作物澆水。
    - **收穫**：當作物成熟時，靠近作物按互動鍵，收穫作物。
  - **製作與發明**：
    - 靠近對應的建築（如工坊、廚房），按互動鍵打開製作介面。
    - 在介面中選擇配方，如果材料充足，即可消耗材料和體力進行製作或發明。

## IV. 使用者介面 (UI)

- **對話框設計**：
  - **佈局**：採用 GBA 遊戲經典的下置式對話框佈局。對話框位於螢幕下方，佔據約 1/4 的高度。
  - **立繪顯示**：當角色發言時，其「像素立繪 (Pixel
    Portrait)」會顯示在對話框的左側或右側（取決於角色在場景中的位置）。立繪區域會略微延伸到主遊戲畫面上，以增強層次感。
  - **文本區域**：顯示發言角色的姓名和對話內容。
  - **Angela 的對話框**：Angela 的對話框設計會與普通 NPC 的有所不同，可能帶有更柔和的邊框或特殊的發光效果，以凸顯其獨特性。
