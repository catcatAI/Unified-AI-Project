# Unified-AI-Project 深度問題分析與修復方案

**分析日期**: 2026-02-12  
**版本**: v6.2.0  
**問題總數**: 89 個（新增 22 個遺漏問題）

---

## 遺漏問題清單（新增 22 個）

### 1. 內存管理和資源清理問題（8 個）

| ID | 問題 | 嚴重性 | 位置 | 影響 |
|----|------|--------|------|------|
| MEM-1 | InputHandler 事件監聽器使用 .bind(this) 後無法正確移除 | 高 | `/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js/input-handler.js:288-301` | 內存洩漏 |
| MEM-2 | WebSocket 待處理響應清理定時器未在斷開時清理 | 高 | `/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js/backend-websocket.js:238-253` | 資源洩漏 |
| MEM-3 | hardware-detection.js 監控間隔未清理 | 中 | `/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js/hardware-detection.js:847-862` | 內存洩漏 |
| MEM-4 | StateMatrix4D.history 清理頻率太低（15分鐘） | 中 | `/home/cat/桌面/Unified-AI-Project/apps/desktop-app/electron_app/js/state-matrix.js:291-330` | 內存增長過快 |
| MEM-5 | Canvas 上下文未正確清理 | 中 | 多個文件 | 資源洩漏 |
| MEM-6 | 定時器未追蹤和清理 | 中 | 多個文件 | 內存洩漏 |
| MEM-7 | 圖片資源未正確釋放 | 低 | layer-renderer.js, live2d-manager.js | 內存洩漏 |
| MEM-8 | WebSocket 連接未正確關閉 | 高 | backend-websocket.js | 連接洩漏 |

### 2. 安全問題（6 個）

| ID | 問題 | 嚴重性 | 位置 | 影響 |
|----|------|--------|------|------|
| SEC-1 | localStorage 數據未驗證直接解析 | 高 | data-persistence.js:146-159 | JSON 注入攻擊 |
| SEC-2 | 插件系統使用 new Function() 執行未驗證代碼 | 高 | plugin-manager.js:126-130 | 代碼注入攻擊 |
| SEC-3 | XSS 風險 - dialogue-ui.js 使用 innerHTML | 高 | dialogue-ui.js:17, 261 | XSS 攻擊 |
| SEC-4 | 輸入驗證缺失 | 中 | 多個文件 | 注入攻擊 |
| SEC-5 | 敏感數據未加密 | 中 | localStorage | 數據洩漏 |
| SEC-6 | 路徑遍歷風險 | 中 | main.js (local 協議) | 文件系統訪問 |

### 3. 線程安全和並發問題（3 個）

| ID | 問題 | 嚴重性 | 位置 | 影響 |
|----|------|--------|------|------|
| CONC-1 | 競態條件 - StateMatrix4D 狀態更新 | 中 | state-matrix.js | 數據不一致 |
| CONC-2 | 異步回調未處理錯誤 | 中 | 多個文件 | 未捕獲的異常 |
| CONC-3 | WebSocket 消息處理順序問題 | 低 | backend-websocket.js | 消息亂序 |

### 4. 兼容性問題（5 個）

| ID | 問題 | 嚴重性 | 位置 | 影響 |
|----|------|--------|------|------|
| COMP-1 | 未處理高 DPI 顯示器 | 中 | unified-display-matrix.js | 模糊顯示 |
| COMP-2 | 未處理不同操作系統的文件路徑 | 中 | main.js | 文件訪問失敗 |
| COMP-3 | 未處理不同瀏覽器的 API 差異 | 低 | 多個文件 | 功能異常 |
| COMP-4 | 未處理不同屏幕尺寸 | 中 | index.html, settings.html | 顯示問題 |
| COMP-5 | 未處理不同屏幕方向 | 低 | 多個文件 | 佈局問題 |

---

## 高嚴重性問題修復方案

### 修復方案 1: InputHandler 事件監聽器內存洩漏（MEM-1）

**問題描述**：
- 使用 `.bind(this)` 創建的函數引用與原始函數不同
- `removeEventListener` 無法移除正確的監聽器
- 導致內存洩漏

**修復代碼**：
```javascript
class InputHandler {
    constructor(live2dManager, clickLayer) {
        this.live2dManager = live2dManager;
        this.clickLayer = clickLayer;
        
        // 保存所有事件監聽器引用
        this._eventHandlers = {
            mousemove: null,
            mousedown: null,
            mouseup: null,
            click: null,
            touchstart: null,
            touchmove: null,
            touchend: null,
            resize: null
        };
        
        this.initialize();
    }

    initialize() {
        // 創建並保存綁定後的處理器
        this._eventHandlers.mousemove = this._onMouseMove.bind(this);
        this._eventHandlers.mousedown = this._onMouseDown.bind(this);
        this._eventHandlers.mouseup = this._onMouseUp.bind(this);
        this._eventHandlers.click = this._onClick.bind(this);
        this._eventHandlers.touchstart = this._onTouchStart.bind(this);
        this._eventHandlers.touchmove = this._onTouchMove.bind(this);
        this._eventHandlers.touchend = this._onTouchEnd.bind(this);
        this._eventHandlers.resize = this._onResize.bind(this);
        
        // 使用保存的引用添加監聽器
        window.addEventListener('mousemove', this._eventHandlers.mousemove);
        window.addEventListener('mousedown', this._eventHandlers.mousedown);
        window.addEventListener('mouseup', this._eventHandlers.mouseup);
        window.addEventListener('click', this._eventHandlers.click);
        window.addEventListener('touchstart', this._eventHandlers.touchstart);
        window.addEventListener('touchmove', this._eventHandlers.touchmove);
        window.addEventListener('touchend', this._eventHandlers.touchend);
        window.addEventListener('resize', this._eventHandlers.resize);
        
        console.log('[InputHandler] Event listeners registered');
    }

    destroy() {
        console.log('[InputHandler] Destroying...');
        
        // 使用保存的引用移除監聽器
        window.removeEventListener('mousemove', this._eventHandlers.mousemove);
        window.removeEventListener('mousedown', this._eventHandlers.mousedown);
        window.removeEventListener('mouseup', this._eventHandlers.mouseup);
        window.removeEventListener('click', this._eventHandlers.click);
        window.removeEventListener('touchstart', this._eventHandlers.touchstart);
        window.removeEventListener('touchmove', this._eventHandlers.touchmove);
        window.removeEventListener('touchend', this._eventHandlers.touchend);
        window.removeEventListener('resize', this._eventHandlers.resize);
        
        // 清空引用
        Object.keys(this._eventHandlers).forEach(key => {
            this._eventHandlers[key] = null;
        });
        
        this.live2dManager = null;
        this.clickLayer = null;
        
        console.log('[InputHandler] Destroyed successfully');
    }
}
```

**測試方案**：
```javascript
describe('InputHandler Memory Leak', () => {
    test('should remove all event listeners on destroy', () => {
        const mockLive2DManager = { lookAt: jest.fn() };
        const mockClickLayer = document.createElement('div');
        document.body.appendChild(mockClickLayer);
        
        const inputHandler = new InputHandler(mockLive2DManager, mockClickLayer);
        const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener');
        
        inputHandler.destroy();
        
        expect(removeEventListenerSpy).toHaveBeenCalledTimes(8);
        expect(removeEventListenerSpy).toHaveBeenCalledWith('mousemove', expect.any(Function));
        
        document.body.removeChild(mockClickLayer);
    });
});
```

---

### 修復方案 2: WebSocket 資源清理（MEM-2, MEM-8）

**修復代碼**：
```javascript
class BackendWebSocketClient {
    disconnect() {
        console.log('[BackendWebSocket] Disconnecting...');
        
        // 1. 關閉 WebSocket
        if (this.ws) {
            try {
                this.ws.close(1000, 'User disconnect');
            } catch (e) {
                console.warn('[BackendWebSocket] Error closing WebSocket:', e);
            }
            this.ws = null;
        }
        
        this.connected = false;
        
        // 2. 停止心跳
        this._stopHeartbeat();
        
        // 3. 停止待處理響應清理
        this._stopPendingResponsesCleanup();
        
        // 4. 清除重連定時器
        if (this.reconnectInterval) {
            clearTimeout(this.reconnectInterval);
            this.reconnectInterval = null;
        }
        
        // 5. 清理所有待處理響應
        if (this._pendingResponses) {
            const pendingCount = this._pendingResponses.size;
            for (const [messageId, pending] of this._pendingResponses.entries()) {
                clearTimeout(pending.timeout);
                if (pending.reject) {
                    pending.reject(new Error('Connection closed'));
                }
            }
            this._pendingResponses.clear();
            console.log(`[BackendWebSocket] Cleared ${pendingCount} pending responses`);
        }
        
        // 6. 保存離線隊列
        this._loadOfflineQueue();
        
        this.eventHandlers = {};
        
        console.log('[BackendWebSocket] Disconnected successfully');
    }
}
```

---

### 修復方案 3: localStorage 安全驗證（SEC-1）

**修復代碼**：
```javascript
class DataPersistence {
    _loadAll() {
        const prefix = this._getKey('');
        let corruptKeys = [];
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            
            if (key && key.startsWith(prefix)) {
                try {
                    const value = localStorage.getItem(key);
                    
                    // 1. 基本驗證
                    if (typeof value !== 'string' || !value) {
                        throw new Error('Value is not a valid string');
                    }
                    
                    // 2. JSON 結構驗證
                    const firstChar = value.charAt(0);
                    const lastChar = value.charAt(value.length - 1);
                    if (!((firstChar === '{' && lastChar === '}') || 
                          (firstChar === '[' && lastChar === ']'))) {
                        throw new Error('Invalid JSON structure');
                    }
                    
                    // 3. 安全解析
                    const parsedValue = JSON.parse(value);
                    
                    // 4. 數據驗證
                    if (parsedValue === null || parsedValue === undefined) {
                        console.warn(`[DataPersistence] Null/undefined value for key: ${key}`);
                    }
                    
                    const dataKey = key.substring(prefix.length);
                    this.data[dataKey] = parsedValue;
                    
                } catch (e) {
                    console.error(`[DataPersistence] Failed to load key ${key}:`, e);
                    corruptKeys.push(key);
                    
                    // 刪除損壞的數據
                    try {
                        localStorage.removeItem(key);
                    } catch (removeError) {
                        console.error('[DataPersistence] Failed to remove corrupt key:', removeError);
                    }
                }
            }
        }
        
        if (corruptKeys.length > 0) {
            console.warn(`[DataPersistence] Removed ${corruptKeys.length} corrupt entries`);
        }
    }
    
    _saveKey(key, retryCount = 0) {
        const MAX_RETRIES = 3;
        
        try {
            const value = this.data[key];
            const serialized = JSON.stringify(value);
            
            // 檢查大小限制
            if (serialized.length > this.config.maxSize) {
                throw new Error('Value too large');
            }
            
            localStorage.setItem(this._getKey(key), serialized);
        } catch (e) {
            if (e.name === 'QuotaExceededError' && retryCount < MAX_RETRIES) {
                console.warn(`[DataPersistence] Storage quota exceeded, attempt ${retryCount + 1}`);
                this._freeSpaceByPriority();
                
                setTimeout(() => {
                    this._saveKey(key, retryCount + 1);
                }, 100 * (retryCount + 1));
            } else {
                console.error('[DataPersistence] Failed to save after retries:', e);
            }
        }
    }
}
```

---

### 修復方案 4: 插件系統安全加固（SEC-2）

**修復代碼**：
```javascript
class PluginManager {
    _createSandbox() {
        return {
            // 提供安全 API
            log: console.log.bind(console),
            error: console.error.bind(console),
            warn: console.warn.bind(console),
            
            // 提供有限的工具函數
            setTimeout: (fn, delay) => setTimeout(fn, delay),
            setInterval: (fn, delay) => setInterval(fn, delay),
            clearTimeout: clearTimeout,
            clearInterval: clearInterval,
            
            // 提供安全的數據存儲
            storage: {
                get: (key) => this.pluginStorage.get(key),
                set: (key, value) => this.pluginStorage.set(key, value),
                delete: (key) => this.pluginStorage.delete(key)
            },
            
            // 提供事件發射
            emit: (event, data) => this.emit(`plugin:${event}`, data),
            on: (event, handler) => this.on(`plugin:${event}`, handler),
            off: (event, handler) => this.off(`plugin:${event}`, handler),
            
            // 禁止訪問危險對象
            window: undefined,
            document: undefined,
            location: undefined,
            navigator: undefined,
            history: undefined,
            process: undefined,
            require: undefined,
            import: undefined,
            export: undefined,
            module: undefined,
            exports: undefined,
            __dirname: undefined,
            __filename: undefined,
            global: undefined,
            globalThis: undefined,
            Function: undefined,
            eval: undefined,
            setTimeout: undefined,
            setInterval: undefined,
            clearTimeout: undefined,
            clearInterval: undefined
        };
    }
    
    async loadPlugin(name, code) {
        // 1. 驗證插件名稱
        if (!/^[a-zA-Z0-9_-]+$/.test(name)) {
            throw new Error(`Invalid plugin name: ${name}`);
        }
        
        // 2. 檢查代碼長度
        if (code.length > 100000) {
            throw new Error('Plugin code too large');
        }
        
        // 3. 檢查黑名單關鍵詞
        const dangerousPatterns = [
            /\beval\b/,
            /\bFunction\b/,
            /\brequire\b/,
            /\bimport\b/,
            /\bexport\b/,
            /\bprocess\b/,
            /\b__proto__\b/,
            /\bconstructor\b/,
            /\.\.\/|\.\.\//,
            /document\.cookie/,
            /localStorage/,
            /sessionStorage/,
            /window\./,
            /document\./,
            /location\./,
            /navigator\./
        ];
        
        for (const pattern of dangerousPatterns) {
            if (pattern.test(code)) {
                throw new Error(`Plugin contains forbidden pattern: ${pattern}`);
            }
        }
        
        // 4. 創建沙箱
        const sandbox = this._createSandbox();
        
        // 5. 使用 Proxy 攔截
        const sandboxProxy = new Proxy(sandbox, {
            has(target, prop) {
                return prop in sandbox;
            },
            get(target, prop) {
                if (!(prop in sandbox)) {
                    throw new Error(`Access denied to property: ${prop}`);
                }
                return target[prop];
            },
            set(target, prop, value) {
                if (!(prop in sandbox)) {
                    throw new Error(`Access denied to property: ${prop}`);
                }
                target[prop] = value;
                return true;
            }
        });
        
        try {
            // 6. 執行插件代碼
            const factory = new Function('sandbox', `with(sandbox) { ${code} }`);
            return factory(sandboxProxy);
        } catch (error) {
            console.error(`[PluginManager] Failed to load plugin ${name}:`, error);
            throw new Error(`Plugin execution failed: ${error.message}`);
        }
    }
}
```

---

### 修復方案 5: XSS 防護（SEC-3）

**修復代碼**：
```javascript
class DialogueUI {
    createMessageElement(sender, content, timestamp) {
        // 1. 創建元素
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        // 2. 安全地添加發送者
        const senderDiv = document.createElement('div');
        senderDiv.className = 'sender';
        senderDiv.textContent = sender; // textContent 自動轉義
        
        // 3. 安全地添加內容
        const contentDiv = document.createElement('div');
        contentDiv.className = 'content';
        
        // 如果需要支持 HTML，使用白名單過濾
        if (this.config.allowHTML) {
            contentDiv.innerHTML = this._sanitizeHTML(content);
        } else {
            contentDiv.textContent = content;
        }
        
        // 4. 添加時間戳
        const timeDiv = document.createElement('div');
        timeDiv.className = 'timestamp';
        timeDiv.textContent = new Date(timestamp).toLocaleTimeString();
        
        // 5. 組裝
        messageDiv.appendChild(senderDiv);
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(timeDiv);
        
        return messageDiv;
    }
    
    _sanitizeHTML(html) {
        const allowedTags = ['b', 'i', 'em', 'strong', 'a', 'br', 'p', 'span'];
        const allowedAttributes = {
            'a': ['href', 'title'],
            'span': ['class']
        };
        
        const parser = new DOMParser();
        const doc = parser.parseFromString(`<div>${html}</div>`, 'text/html');
        
        function cleanElement(element) {
            const tagName = element.tagName.toLowerCase();
            
            // 移除不允許的標籤
            if (!allowedTags.includes(tagName)) {
                // 保留文本內容，移除標籤
                const text = element.textContent;
                while (element.firstChild) {
                    element.removeChild(element.firstChild);
                }
                return;
            }
            
            // 移除不允許的屬性
            const attributesToRemove = [];
            for (const attr of element.attributes) {
                const allowed = allowedAttributes[tagName] || [];
                if (!allowed.includes(attr.name.toLowerCase())) {
                    // 檢查 JavaScript 協議
                    if (attr.name === 'href' && attr.value.toLowerCase().startsWith('javascript:')) {
                        attributesToRemove.push(attr);
                    } else {
                        attributesToRemove.push(attr);
                    }
                }
            }
            attributesToRemove.forEach(attr => element.removeAttribute(attr.name));
            
            // 遞歷處理子元素
            Array.from(element.children).forEach(cleanElement);
        }
        
        Array.from(doc.body.children).forEach(cleanElement);
        return doc.body.innerHTML;
    }
}
```

---

## 修復計劃

### 第一階段（P0 - 緊急修復）

| 任務 | 優先級 | 時間估算 | 難度 | 依賴 |
|------|--------|----------|------|------|
| MEM-1: InputHandler 事件監聽器修復 | P0 | 2h | 中 | 無 |
| MEM-2: WebSocket 資源清理 | P0 | 3h | 中 | 無 |
| SEC-1: localStorage 驗證 | P0 | 4h | 中 | 無 |
| SEC-2: 插件系統安全加固 | P0 | 6h | 困難 | 無 |
| SEC-3: XSS 防護 | P0 | 3h | 中 | 無 |
| DF-5: WebSocket 重試機制 | P0 | 4h | 中 | MEM-2 |
| DF-6: WebSocket 消息隊列 | P0 | 5h | 困難 | MEM-2 |
| SA-1: 初始化順序強制 | P0 | 3h | 困難 | 無 |
| SA-2: ANGELA_CHARACTER_CONFIG 驗證 | P0 | 2h | 簡單 | 無 |
| SA-3: LayerRenderer 驗證 | P0 | 2h | 簡單 | 無 |

**總時間**: 34 小時  
**預計工期**: 4-5 天

### 第二階段（P1 - 高優先級）

| 任務 | 優先級 | 時間估算 | 難度 | 依賴 |
|------|--------|----------|------|------|
| SR-1: live2d-canvas 尺寸同步 | P1 | 3h | 中 | SA-1 |
| SR-5: getUserScale 修復 | P1 | 2h | 簡單 | 無 |
| SR-6: screenToCanvas 修復 | P1 | 3h | 中 | 無 |
| SR-8: identifyBodyPart 修復 | P1 | 4h | 中 | SR-5 |
| SR-17: Live2D 模型尺寸驗證 | P1 | 3h | 中 | SR-1 |
| DF-1: InputHandler 事件清理 | P1 | 2h | 簡單 | MEM-1 |
| DF-8: 後端 API 端點驗證 | P1 | 3h | 中 | 無 |
| DF-9: LLM 服務可用性檢查 | P1 | 2h | 簡單 | 無 |
| SA-6: input-handler 事件清理 | P1 | 2h | 簡單 | MEM-1 |
| SA-10: 全局錯誤處理器集成 | P1 | 5h | 困難 | 無 |
| CP-5: localStorage 版本控制 | P1 | 4h | 中 | SEC-1 |

**總時間**: 33 小時  
**預計工期**: 4-5 天

### 第三階段（P2 - 中優先級）

| 任務 | 優先級 | 時間估算 | 難度 | 依賴 |
|------|--------|----------|------|------|
| UI-2: notification-container 添加 | P2 | 1h | 簡單 | 無 |
| UI-3: canvas-wrapper 動態調整 | P2 | 3h | 中 | 無 |
| UI-15: transform 偏移修復 | P2 | 2h | 簡單 | 無 |
| SR-3: LayerRenderer canvas 驗證 | P2 | 1h | 簡單 | 無 |
| SR-4: devicePixelRatio 支持 | P2 | 3h | 中 | 無 |
| DF-2: handleClick 回退處理 | P2 | 2h | 簡單 | 無 |
| DF-3: WebSocket 連接檢查 | P2 | 2h | 簡單 | DF-5 |
| DF-7: updateMonitorUI 節流 | P2 | 2h | 簡單 | 無 |
| MEM-3: hardware-detection 清理 | P2 | 1h | 簡單 | 無 |
| MEM-4: history 清理頻率調整 | P2 | 3h | 中 | 無 |
| CP-1: localStorage 統一封裝 | P2 | 6h | 困難 | CP-5 |
| CP-3: localStorage 容量檢查 | P2 | 3h | 中 | SEC-1 |

**總時間**: 29 小時  
**預計工期**: 3-4 天

### 第四階段（P3 - 低優先級）

| 任務 | 優先級 | 時間估算 | 難度 | 依賴 |
|------|--------|----------|------|------|
| UI-1: title 元素更新 | P3 | 1h | 簡單 | 無 |
| UI-6: 背景色主題兼容 | P3 | 2h | 簡單 | 無 |
| UI-7: .control-btn 重複定義清理 | P3 | 1h | 簡單 | 無 |
| UI-8: hover 狀態過渡動畫 | P3 | 1h | 簡單 | 無 |
| UI-9: button disabled 樣式 | P3 | 2h | 簡單 | 無 |
| UI-10: status-bar 初始動畫 | P3 | 1h | 簡單 | 無 |
| UI-11: badge 寬度溢出修復 | P3 | 2h | 簡單 | 無 |
| UI-12: controls 初始顯示邏輯 | P3 | 2h | 簡單 | 無 |
| UI-13: footer 響應式 | P3 | 2h | 簡單 | 無 |
| UI-14: 移動端響應式設計 | P3 | 8h | 中 | 無 |
| UI-16: z-index 管理系統 | P3 | 4h | 中 | 無 |
| SR-9: Math.round 亞像素間隙 | P3 | 2h | 簡單 | 無 |
| SR-10: 坐標範圍驗證 | P3 | 2h | 簡單 | 無 |
| SR-11: featherRadius 動態調整 | P3 | 2h | 簡單 | 無 |
| SR-12: 縮放邊界檢查 | P3 | 1h | 簡單 | 無 |
| SR-13: setUserScale 修復 | P3 | 1h | 簡單 | 無 |
| SR-14: getDisplayWidth/Height 修復 | P3 | 2h | 簡單 | 無 |
| SR-15: calculateHapticIntensity 公式 | P3 | 2h | 簡單 | 無 |
| SR-16: Live2D 模型路徑配置 | P3 | 3h | 中 | 無 |
| SR-18: overlayPositions 密度調整 | P3 | 3h | 中 | 無 |
| DF-4: debounceConfig 優化 | P3 | 2h | 簡單 | 無 |
| DF-10: LLM 超時設置 | P3 | 2h | 簡單 | 無 |
| DF-11: fallback 回應擴展 | P3 | 2h | 簡單 | 無 |
| DF-12: 響應格式統一 | P3 | 3h | 中 | 無 |
| DF-13: WebSocket 節流優化 | P3 | 2h | 簡單 | 無 |
| DF-14: 參數驗證 | P3 | 1h | 簡單 | 無 |
| SA-4: PerformanceManager 初始化 | P3 | 2h | 簡單 | 無 |
| SA-5: 初始化順序優化 | P3 | 3h | 中 | SA-1 |
| SA-7: _parallaxHandler 去抖 | P3 | 2h | 簡單 | 無 |
| SA-8: try-catch 優化 | P3 | 8h | 中 | 無 |
| SA-9: 錯誤消息改進 | P3 | 4h | 中 | SA-10 |
| SA-11: 臟渲染實現 | P3 | 6h | 困難 | 無 |
| SA-12: history 壓縮 | P3 | 4h | 中 | MEM-4 |
| CP-2: localStorage 鍵名統一 | P3 | 3h | 中 | CP-1 |
| CP-4: autoSave 衝突修復 | P3 | 2h | 簡單 | 無 |
| CP-6: .env 變量定義 | P3 | 2h | 簡單 | 無 |
| CP-7: 配置備份恢復 | P3 | 4h | 中 | CP-5 |

**總時間**: 85 小時  
**預計工期**: 10-12 天

---

## 總修復時間估算

| 階段 | 任務數量 | 總時間 | 預計工期 |
|------|----------|--------|----------|
| 第一階段（P0） | 10 | 34h | 4-5 天 |
| 第二階段（P1） | 11 | 33h | 4-5 天 |
| 第三階段（P2） | 12 | 29h | 3-4 天 |
| 第四階段（P3） | 39 | 85h | 10-12 天 |
| **總計** | **72** | **181h** | **21-26 天** |

---

## 修復依賴關係圖

```
P0 修復任務:
├── MEM-1: InputHandler 事件監聽器修復 (無依賴)
├── MEM-2: WebSocket 資源清理 (無依賴)
├── SEC-1: localStorage 驗證 (無依賴)
├── SEC-2: 插件系統安全加固 (無依賴)
├── SEC-3: XSS 防護 (無依賴)
├── DF-5: WebSocket 重試機制 (依賴: MEM-2)
├── DF-6: WebSocket 消息隊列 (依賴: MEM-2)
├── SA-1: 初始化順序強制 (無依賴)
├── SA-2: ANGELA_CHARACTER_CONFIG 驗證 (無依賴)
└── SA-3: LayerRenderer 驗證 (無依賴)

P1 修復任務:
├── SR-1: live2d-canvas 尺寸同步 (依賴: SA-1)
├── SR-5: getUserScale 修復 (無依賴)
├── SR-6: screenToCanvas 修復 (無依賴)
├── SR-8: identifyBodyPart 修復 (依賴: SR-5)
├── SR-17: Live2D 模型尺寸驗證 (依賴: SR-1)
├── DF-1: InputHandler 事件清理 (依賴: MEM-1)
├── DF-8: 後端 API 端點驗證 (無依賴)
├── DF-9: LLM 服務可用性檢查 (無依賴)
├── SA-6: input-handler 事件清理 (依賴: MEM-1)
├── SA-10: 全局錯誤處理器集成 (無依賴)
└── CP-5: localStorage 版本控制 (依賴: SEC-1)

P2 修復任務:
├── UI-2: notification-container 添加 (無依賴)
├── UI-3: canvas-wrapper 動態調整 (無依賴)
├── UI-15: transform 偏移修復 (無依賴)
├── SR-3: LayerRenderer canvas 驗證 (無依賴)
├── SR-4: devicePixelRatio 支持 (無依賴)
├── DF-2: handleClick 回退處理 (無依賴)
├── DF-3: WebSocket 連接檢查 (依賴: DF-5)
├── DF-7: updateMonitorUI 節流 (無依賴)
├── MEM-3: hardware-detection 清理 (無依賴)
├── MEM-4: history 清理頻率調整 (無依賴)
├── CP-1: localStorage 統一封裝 (依賴: CP-5)
└── CP-3: localStorage 容量檢查 (依賴: SEC-1)

P3 修復任務:
├── 大部分 UI 細節優化 (無依賴)
├── 大部分渲染細節優化 (無依賴)
├── 大部分數據流優化 (無依賴)
├── 大部分架構優化 (依賴: SA-10)
└── 大部分配置優化 (依賴: CP-5)
```

---

## 測試策略

### 單元測試
- 針對每個修復的函數編寫單元測試
- 覆蓋正常情況和邊界情況
- 覆蓋錯誤情況

### 集成測試
- 測試修復後的模塊之間的交互
- 測試修復對其他模塊的影響

### 回歸測試
- 修復前後運行所有現有測試
- 確保修復不引入新問題

### 性能測試
- 測試修復後的性能影響
- 確保修復不會導致性能下降

---

## 風險評估

### 高風險
- SEC-2: 插件系統安全加固（可能影響現有插件）
- SA-1: 初始化順序強制（可能影響現有初始化邏輯）
- DF-6: WebSocket 消息隊列（可能影響現有通信邏輯）

### 中風險
- CP-1: localStorage 統一封裝（可能影響現有數據存儲）
- SR-5: getUserScale 修復（可能影響現有縮放邏輯）
- SA-10: 全局錯誤處理器集成（可能影響現有錯誤處理）

### 低風險
- 大部分 UI 和渲染細節優化
- 大部分配置和持久化優化

---

## 總結

### 問題統計
- **總問題數**: 89 個
- **高嚴重性**: 19 個
- **中嚴重性**: 30 個
- **低嚴重性**: 18 個
- **遺漏問題**: 22 個

### 修復時間
- **總修復時間**: 181 小時
- **預計工期**: 21-26 天

### 修復策略
1. 第一階段（P0）: 修復緊急問題，確保系統穩定性
2. 第二階段（P1）: 修復高優先級問題，提升系統可靠性
3. 第三階段（P2）: 修復中優先級問題，改善用戶體驗
4. 第四階段（P3）: 修復低優先級問題，優化代碼質量

### 關鍵修復
1. **內存洩漏修復**: MEM-1, MEM-2, MEM-3, MEM-4
2. **安全加固**: SEC-1, SEC-2, SEC-3
3. **WebSocket 改進**: DF-5, DF-6, DF-8
4. **初始化優化**: SA-1, SA-2, SA-3
5. **配置管理**: CP-1, CP-3, CP-5

---

**報告完成時間**: 2026-02-12  
**下次更新**: 修復進度跟蹤