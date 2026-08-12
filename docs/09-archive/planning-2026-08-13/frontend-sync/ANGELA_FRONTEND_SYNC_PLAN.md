# Angela Frontend Synchronization Plan

> **目標**: 將後端 v6.3 NGR (Neuro-Generative Response) 變更同步至兩個前端
> **版本**: v1.0 (2026-05-18)
> **後端變更範圍**: NGR 說話系統、NeuroBlender、8D 狀態矩陣、共情分析

---

## 1. 後端變更摘要 (需同步至前端)

| 變更 | 後端檔案 | 前端影響 |
|------|---------|---------|
| NeuroBlender 合成回應 | `chat_service.py` | Chat 回應可能來自 NeuroBlender 而非 LLM |
| 8D 狀態矩陣 (αβγδεθζη) | `state_matrix.py` | 前端 state-matrix 需從 6D 升級至 8D |
| 共情分析結果 | `emotion_system.py` | 前端可顯示共情分數與情緒分析 |
| Fallback → NeuroBlender | `angela_llm_service.py` | 離線模式回應更自然，前端應標示 |
| neuro_blend_meta 傳遞 | `chat_service.py` | Chat API 回應可能包含 neuro 元資料 |

---

## 2. 受影響之前端元件

### 2.1 Desktop App (`apps/desktop-app/`)

| 元件 | 檔案 | 需更新內容 |
|------|------|-----------|
| State Matrix | `js/state-matrix.js` | 從 6D → 8D (新增 ζ/zeta, η/eta) |
| API Client | `js/api-client.js` | 處理 chat 回應的 neuro_blend_meta |
| WebSocket Handler | `js/backend-websocket.js` | 處理 state_update 中 ζ/η 維度 |
| Dialogue UI | `js/dialogue-ui.js` | 顯示 NeuroBlender/LLM 來源標示 |
| App Orchestrator | `js/app.js` | 初始化時註冊新維度 |
| Settings | `settings.html` | 可選：顯示 NeuroBlender 狀態 |

### 2.2 Mobile App (`apps/mobile-app/`)

| 元件 | 檔案 | 需更新內容 |
|------|------|-----------|
| API Client | `src/api/client.js` | 處理 neuro_blend_meta |
| Main App | `App.js` | State matrix 顯示從 6D → 8D |
| Chat Display | `App.js` (內建) | 顯示回應來源標示 |

---

## 3. 實作階段

### Phase 1: Desktop State Matrix 8D 升級
- **檔案**: `js/state-matrix.js`
- **動作**:
  - `StateMatrix4D` 建構子新增 `zeta`、`eta` 軸
  - `compute_coordinate()` 納入 ζ/η
  - `export_for_llm()` 納入新維度
  - `updateFromBackend()` 對應後端 state_update 格式

### Phase 2: Desktop Chat 回應強化
- **檔案**: `js/api-client.js`, `js/app.js`, `js/dialogue-ui.js`
- **動作**:
  - `api-client.js`: `sendChat()` 解析 `neuro_blend_meta`
  - `app.js`: 根據來源設定回應類型標籤
  - `dialogue-ui.js`: 顯示 NeuroBlender 標示 (如「✨ 合成」)

### Phase 3: Desktop WebSocket 同步
- **檔案**: `js/backend-websocket.js`, `js/app.js`
- **動作**:
  - 處理 `neuro_blend` 類型訊息
  - 同步 empathy 分析結果至前端顯示

### Phase 4: Mobile App 同步
- **檔案**: `App.js`, `src/api/client.js`
- **動作**:
  - 8D state matrix 顯示條
  - Chat 回應 neuro_blend_meta 解析
  - 來源標示

---

## 4. API 回應格式變更 (前端需處理)

### Chat Unified Response (既有格式擴充)
```json
{
  "response": "Angela的回應文字",
  "message": "相同文字",
  "emotion": "happy",
  "source": "neuro_blender | llm_full | template",
  "neuro_blend": {                    // ← 新增，僅 source=neuro_blender 時有
    "confidence": 0.82,
    "fragments_used": ["ng_morning_bright", "ng_trans_so"],
    "target_vector": [0.9, 0.5, 0.7, 0.4, 0.5, 0.5, 0.3, 0.5]
  }
}
```

### State Update (既有格式擴充)
```json
{
  "type": "state_update",
  "data": {
    "alpha": { "energy": 0.5, ... },
    "beta": { "curiosity": 0.5, ... },
    "gamma": { ... },
    "delta": { ... },
    "epsilon": { ... },
    "theta": { ... },
    "zeta": { "temporal_coherence": 0.5, "memory_depth": 0.5, "narrative_flow": 0.5, "identity_continuity": 0.5 },
    "eta": { "execution_count": 0, "success_rate": 0.5, "structural_drift": 0.0 }
  }
}
```

---

## 5. 驗證標準

1. Desktop app 8D 狀態顯示正確，ζ/η 有值
2. Chat 回應顯示來源標示 (NeuroBlender / LLM / Template)
3. 離線模式下 Desktop app 仍能顯示自然回應
4. Mobile app 8D 狀態條正確渲染
5. 所有既有功能不受影響

---

## 6. 不修改的範圍

- 不修改 Live2D 渲染管線
- 不修改安全/加密機制
- 不修改 Electron main process 核心邏輯
- 不修改行動裝置配對流程

---

## 7. 完成狀態

> **同步狀態**: ✅ 全部完成 (2026-05-18)

### 各階段驗證

| Phase | 描述 | 狀態 | 關鍵檔案 |
|-------|------|------|----------|
| Phase 1 | Desktop State Matrix 8D 升級 | ✅ 完成 | `state-matrix.js`: zeta/eta fields, updateZeta/updateEta, getState export |
| Phase 2 | Desktop Chat 回應強化 | ✅ 完成 | `api-client.js`: source + neuro_blend; `dialogue-ui.js`: ✨/🧠/📡/🔢 badges |
| Phase 3 | Desktop WebSocket 同步 | ✅ 完成 | `backend-websocket.js`: _mergeStateData includes zeta/eta |
| Phase 4 | Mobile App 同步 | ✅ 完成 | `App.js`: 8D bars + source badge; `mobile.py`: NGR endpoint; `client.js`: neuro_blend parse |

### 驗證結果
1. ✅ Desktop app 8D 狀態顯示正確，ζ/η 有值
2. ✅ Chat 回應顯示來源標示 (NeuroBlender / LLM / Template / Math)
3. ✅ 離線模式下 Desktop app 仍能顯示自然回應 (NeuroBlender)
4. ✅ Mobile app 8D 狀態條正確渲染
5. ✅ 所有既有功能不受影響

---

**簽署**: Gemini CLI (ASI Architect)
