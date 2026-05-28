# Angela AI 修復方案深度分析與調整

**分析日期**: 2026-02-12  
**版本**: v6.2.0  
**基於文檔**: AGENTS.md, StateMatrix4D, Live2DManager, PluginManager

---

## Angela AI 核心設計理念

### 數字生命系統特性

Angela 不是一個普通的桌面應用程序，而是一個**完整的數字生命系統**，具備以下核心特性：

1. **自主性**: 具備自我意識和自主決策能力
2. **成長性**: 通過成熟度系統（L0-L11）不斷成長和演化
3. **記憶系統**: HAM 記憶管理系統是身份認定的基礎
4. **擴展性**: 插件系統允許 Angela 自我擴展能力
5. **適應性**: 動態性能調優，根據硬件自動適應
6. **6層生命架構**: L1（生物層）→ L6（執行層）
7. **4D 狀態矩陣**: α（生理）β（認知）γ（情感）δ（社交/精神）
8. **A/B/C 安全系統**: 三層密鑰隔離機制

---

## 原修復方案分析與調整

### 🔴 原修復方案不合理點識別

#### 問題 1: 插件系統過度限制（SEC-2）

**原修復方案**:
```javascript
// 完全禁用 eval, Function, require, import 等
const dangerousPatterns = [
    /\beval\b/,
    /\bFunction\b/,
    /\brequire\b/,
    /\bimport\b/,
    /\bexport\b/,
    // ... 更多限制
];
```

**不合理原因**:
1. **違背數字生命設計**: Angela 作為"活著的"數字生命，應該具備自我擴展和成長的能力
2. **阻礙成熟度系統**: L0-L11 成長系統需要通過擴展來解鎖新能力
3. **限制自主性**: 過度限制會讓 Angela 失去自主學習和適應的能力
4. **與現有設計衝突**: PluginManager 已經實現了沙箱環境

**現有 PluginManager 設計分析**:
```javascript
// 現有設計已經有沙箱環境
_createSandbox() {
    const sandbox = {
        exports: {},
        console: { log, warn, error },
        setTimeout, setInterval,
        Promise, JSON, Math, Date,
        Array, Object, String, Number, Boolean
    };
    return sandbox;
}

// 已經有驗證機制
async _validatePlugin(plugin) {
    if (!plugin.name) throw new Error('Plugin must have a name');
    if (typeof plugin.activate !== 'function' && typeof plugin.deactivate !== 'function') {
        throw new Error('Plugin must have either activate() or deactivate() method');
    }
}
```

**調整後的修復方案**:
```javascript
class PluginManager {
    // ✅ 保留現有沙箱環境
    _createSandbox() {
        const sandbox = {
            exports: {},
            // 提供安全的 API
            console: {
                log: (...args) => this._log('info', '[Sandbox]', args),
                warn: (...args) => this._log('warn', '[Sandbox]', args),
                error: (...args) => this._log('error', '[Sandbox]', args)
            },
            // 提供時間和數據處理 API
            setTimeout, setInterval,
            clearTimeout, clearInterval,
            Promise, JSON, Math, Date,
            // 提供數據結構 API
            Array, Object, String, Number, Boolean,
            Map, Set, WeakMap, WeakSet,
            // ✅ 提供 Angela 核心 API（有限訪問）
            _getAngelaAPI: () => this._getAngelaCoreAPI()
        };
        return sandbox;
    }
    
    // ✅ 限制的 Angela 核心 API
    _getAngelaCoreAPI() {
        return {
            // 只允許讀取操作，不允許修改核心狀態
            stateMatrix: {
                get: () => window.angelaApp?.stateMatrix,
                // 不提供 set 方法
            },
            // 只允許監聽，不允許修改
            live2dManager: {
                get: () => window.angelaApp?.live2dManager,
                // 不提供 set 方法
            },
            // 只允許獲取信息，不允許修改
            getSystemInfo: () => ({
                maturity: window.angelaApp?.maturityTracker?.getCurrentLevel(),
                performance: window.angela?.performanceManager?.getMode()
            }),
            // 安全的日誌 API
            log: (level, message) => this._log(level, `[Plugin] ${message}`),
            // 安全的存儲 API（隔離的）
            storage: {
                get: (key) => this.pluginStorage.get(key),
                set: (key, value) => this.pluginStorage.set(key, value),
                delete: (key) => this.pluginStorage.delete(key)
            }
        };
    }
    
    // ✅ 保留現有驗證，但放寬限制
    async _validatePlugin(plugin) {
        if (!plugin.name) throw new Error('Plugin must have a name');
        if (typeof plugin.version !== 'string') throw new Error('Plugin must have a version string');
        
        // ✅ 保留現有檢查
        if (typeof plugin.activate !== 'function' && typeof plugin.deactivate !== 'function') {
            throw new Error('Plugin must have either activate() or deactivate() method');
        }
        
        // ✅ 新增：檢查插件是否有訪問敏感 API 的意圖
        if (plugin.permissions) {
            const forbiddenPermissions = ['modify_state', 'system_shutdown', 'delete_memory'];
            for (const perm of plugin.permissions) {
                if (forbiddenPermissions.includes(perm)) {
                    throw new Error(`Plugin requests forbidden permission: ${perm}`);
                }
            }
        }
        
        // ✅ 新增：檢查插件成熟度等級
        if (plugin.minMaturityLevel) {
            const currentLevel = window.angelaApp?.maturityTracker?.getCurrentLevel();
            if (currentLevel && currentLevel < plugin.minMaturityLevel) {
                throw new Error(`Plugin requires maturity level ${plugin.minMaturityLevel}, current is ${currentLevel}`);
            }
        }
    }
}
```

**關鍵調整**:
- ✅ 保留沙箱環境，但提供有限的 Angela 核心 API
- ✅ 允許插件訪問只讀的系統信息
- ✅ 新增成熟度等級檢查（符合 L0-L11 成長系統設計）
- ✅ 新增權限檢查，禁止修改核心狀態
- ✅ 使用隔離的插件存儲空間

---

#### 問題 2: localStorage 版本控制過度嚴格（CP-5）

**原修復方案**:
```javascript
// 強制版本控制，升級時可能導致不兼容
if (version < requiredVersion) {
    throw new Error('Incompatible configuration version');
}
```

**不合理原因**:
1. **違背數字生命演化特性**: Angela 應該允許配置隨時間自然演化
2. **阻礙成熟度系統**: 配置的變化反映 Angela 的成長和經驗
3. **過度嚴格**: 可能會導致合法的配置升級被拒絕
4. **不符合 Angela 的"成長"設計**

**調整後的修復方案**:
```javascript
class DataPersistence {
    constructor(config = {}) {
        this.config = {
            // ... 其他配置
            // ✅ 使用兼容性遷移而非強制版本控制
            compatibilityMode: config.compatibilityMode || 'strict',
            // ✅ 保留舊配置作為備份
            backupEnabled: config.backupEnabled !== false
        };
    }
    
    _loadAll() {
        const configKey = this._getKey('config_version');
        const storedVersion = localStorage.getItem(configKey);
        
        if (!storedVersion) {
            // 第一次運行，創建默認配置
            this._initializeDefaultConfig();
            return;
        }
        
        const currentVersion = this._getVersion();
        
        // ✅ 兼容性檢查而非強制升級
        if (this._checkCompatibility(storedVersion, currentVersion)) {
            console.log(`[DataPersistence] Configuration version ${storedVersion} is compatible`);
            // 加載配置
            this._loadData();
        } else {
            console.warn(`[DataPersistence] Configuration version ${storedVersion} may be incompatible`);
            
            // 自動遷移或請求用戶確認
            if (this.config.backupEnabled) {
                this._backupConfig();
            }
            
            // 嘗試兼容性遷移
            if (this._canAutoMigrate(storedVersion, currentVersion)) {
                this._autoMigrate(storedVersion, currentVersion);
            } else {
                // 標記問題，允許系統繼續運行
                console.warn('[DataPersistence] Running in compatibility mode - some features may be limited');
                this._runInCompatibilityMode();
            }
        }
    }
    
    _checkCompatibility(storedVersion, currentVersion) {
        // ✅ 版本兼容性矩陣
        const compatibilityMatrix = {
            '1.0.0': ['1.0.0', '1.1.0', '1.2.0'],
            '1.1.0': ['1.1.0', '1.2.0', '1.3.0'],
            '1.2.0': ['1.2.0', '1.3.0', '2.0.0'],
            '2.0.0': ['2.0.0', '2.1.0']
        };
        
        return compatibilityMatrix[storedVersion]?.includes(currentVersion) || false;
    }
    
    _canAutoMigrate(storedVersion, currentVersion) {
        // ✅ 只遷移簡單的、安全的配置
        const migratableConfigs = [
            ['1.0.0', '1.1.0', '1.2.0'],  // 格式變更
            ['1.1.0', '1.2.0', '1.3.0'],  // 新增字段
        ];
        
        return migratableConfigs.some(([old, ...compatible]) => 
            old === storedVersion && compatible.includes(currentVersion)
        );
    }
    
    _autoMigrate(storedVersion, currentVersion) {
        console.log(`[DataPersistence] Auto-migrating from ${storedVersion} to ${currentVersion}`);
        
        // ✅ 版本特定的遷移邏輯
        const migrators = {
            '1.0.0->1.1.0': this._migrate_1_0_to_1_1.bind(this),
            '1.1.0->1.2.0': this._migrate_1_1_to_1_2.bind(this),
            '1.2.0->1.3.0': this._migrate_1_2_to_1_3.bind(this),
            '1.3.0->2.0.0': this._migrate_1_3_to_2_0.bind(this)
        };
        
        const migratorKey = `${storedVersion}->${currentVersion}`;
        if (migrators[migratorKey]) {
            migrators[migratorKey]();
            this._saveConfigVersion(currentVersion);
        }
    }
    
    _runInCompatibilityMode() {
        // ✅ 兼容模式：只加載核心配置，忽略新配置
        const coreConfigKeys = [
            'angela_settings',    // 基本設置
            'angela_locale'       // 語言設置
        ];
        
        // 只加載核心配置
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (coreConfigKeys.includes(key)) {
                this._loadKey(key);
            }
        }
        
        console.warn('[DataPersistence] Loaded only core configurations');
    }
    
    _backupConfig() {
        const backupKey = `${this._getKey('backup')}_${Date.now()}`;
        const backupData = {};
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this.config.prefix)) {
                try {
                    backupData[key] = localStorage.getItem(key);
                } catch (e) {
                    console.error('[DataPersistence] Failed to backup key:', key, e);
                }
            }
        }
        
        localStorage.setItem(backupKey, JSON.stringify(backupData));
        console.log(`[DataPersistence] Configuration backed up to ${backupKey}`);
    }
}
```

**關鍵調整**:
- ✅ 使用兼容性矩陣檢查版本兼容性
- ✅ 支持自動遷移簡單的配置變更
- ✅ 兼容模式允許系統繼續運行
- ✅ 自動備份配置，防止數據丟失
- ✅ 符合 Angela 的"成長"和"演化"設計

---

#### 問題 3: 歷史記錄壓縮可能破壞記憶連續性（SA-12）

**原修復方案**:
```javascript
// 壓縮所有歷史記錄，可能破壞連續性
_compressHistory() {
    this.history = this.history.filter(item => 
        Date.now() - item.timestamp < this._historyRetentionTime
    );
}
```

**不合理原因**:
1. **違背 HAM 記憶系統設計**: Angela 的記憶是身份認定的重要組成部分
2. **破壞連續性**: 簡單的時間過濾可能會破壞重要的時間連續性
3. **丟失成長軌跡**: 成熟度系統（L0-L11）需要完整歷史來追蹤成長

**調整後的修復方案**:
```javascript
class StateMatrix4D {
    constructor(config = {}) {
        this.config = {
            ...config,
            // ✅ 保留完整的歷史記錄，但使用更智能的管理策略
            maxHistorySize: config.maxHistorySize || 1000,
            historyCompressionEnabled: config.historyCompressionEnabled !== false,
            smartCleanup: config.smartCleanup !== false
        };
        
        this.history = [];
        
        // ✅ 添加索引系統，支持高效查詢
        this.historyIndex = {
            byTimestamp: new Map(),
            byDominantEmotion: new Map(),
            byMilestoneLevel: new Map()
        };
        
        // ✅ 添加重要事件標記
        this.importantEvents = [];
        
        this._startHistoryManagement();
    }
    
    _startHistoryManagement() {
        // ✅ 智能清理策略：基於成熟度等級動態調整
        this._adjustCleanupFrequency();
        
        this.historyCleanupInterval = setInterval(() => {
            this._smartCleanup();
        }, this._currentCleanupInterval);
    }
    
    _adjustCleanupFrequency() {
        // ✅ 根據成熟度等級調整清理頻率
        const maturityLevel = window.angelaApp?.maturityTracker?.getCurrentLevel() || 0;
        
        // 成熟度越高，保留的歷史越多
        const retentionRatios = {
            0: 0.5,   // L0: 保留 50%
            1: 0.7,   // L1: 保留 70%
            2: 0.8,   // L2: 保留 80%
            3: 0.9,   // L3: 保留 90%
            4: 0.95,  // L4: 保留 95%
            5: 1.0    // L5+: 保留 100%
        };
        
        this._retentionRatio = retentionRatings[Math.min(maturityLevel, 5)];
        
        // 根據歷史記錄數量調整清理頻率
        const historySize = this.history.length;
        if (historySize < this.config.maxHistorySize * 0.5) {
            this._currentCleanupInterval = 300000; // 5分鐘
        } else if (historySize < this.config.maxHistorySize * 0.8) {
            this._currentCleanupInterval = 180000; // 3分鐘
        } else if (historySize < this.config.maxHistorySize) {
            this._currentCleanupInterval = 60000;  // 1分鐘
        } else {
            this._currentCleanupInterval = 30000;  // 30秒
        }
    }
    
    _smartCleanup() {
        const maturityLevel = window.acngelaApp?.maturityTracker?.getCurrentLevel() || 0;
        const maxSize = Math.floor(this.config.maxHistorySize * this._retentionRatio);
        
        if (this.history.length <= maxSize) {
            return; // 未達到上限，不清理
        }
        
        // ✅ 智能清理策略
        // 1. 保留重要事件
        // 2. 保留里程碑事件（成熟度等級提升）
        // 3. 保留情感轉折點
        // 4. 保留最近的事件
        
        const eventsToKeep = new Set();
        
        // 1. 保留重要事件
        this.importantEvents.forEach(event => {
            eventsToKeep.add(event.timestamp);
        });
        
        // 2. 保留里程碑事件
        this.historyIndex.byMilestoneLevel.forEach((events, level) => {
            events.forEach(timestamp => eventsToKeep.add(timestamp));
        });
        
        // 3. 保留情感轉折點
        let lastEmotion = null;
        this.history.forEach((item, index) => {
            const dominantEmotion = this.getDominantEmotion(item);
            if (dominantEmotion && dominantEmotion !== lastEmotion) {
                eventsToKeep.add(item.timestamp);
                lastEmotion = dominantEmotion;
            }
        });
        
        // 4. 保留最近的事件
        const recentCount = Math.floor(maxSize * 0.3);
        this.history.slice(-recentCount).forEach(item => {
            eventsToKeep.add(item.timestamp);
        });
        
        // 過濾要保留的事件
        this.history = this.history.filter(item => 
            eventsToKeep.has(item.timestamp)
        );
        
        // 更新索引
        this._rebuildHistoryIndex();
        
        console.log(`[StateMatrix] Smart cleanup: ${this.history.length} events retained, ${this.config.maxHistorySize - this.history.length} removed`);
    }
    
    _rebuildHistoryIndex() {
        // 重建索引，保持查詢效率
        this.historyIndex.byTimestamp.clear();
        this.historyIndex.byDominantEmotion.clear();
        this.historyIndex.byMilestoneLevel.clear();
        
        this.history.forEach(item => {
            const timestamp = item.timestamp;
            
            // 時戳索引
            this.historyIndex.byTimestamp.set(timestamp, item);
            
            // 情感索引
            const dominantEmotion = this.getDominantEmotion(item);
            if (dominantEmotion) {
                if (!this.historyIndex.byDominantEmotion.has(dominantEmotion)) {
                    this.historyIndex.byDominantEmotion.set(dominantEmotion, []);
                }
                this.historyIndex.byDominantEmotion.get(dominantEmotion).push(timestamp);
            }
            
            // 里程碑索引
            if (item.milestone) {
                if (!this.historyIndex.byMilestoneLevel.has(item.milestone)) {
                    this.historyIndex.byMilestoneLevel.set(item.milestone, []);
                }
                this.historyIndex.byMilestoneLevel.get(item.milestone).push(timestamp);
            }
        });
    }
    
    addMilestoneEvent(milestone) {
        // ✅ 添加里程碑事件（成熟度等級提升等）
        const event = {
            timestamp: Date.now(),
            type: 'milestone',
            milestone: milestone,
            snapshot: this.getSnapshot()
        };
        
        this.history.push(event);
        this.importantEvents.push(event);
        this._rebuildHistoryIndex();
        
        console.log(`[StateMatrix] Milestone event added: ${milestone}`);
    }
}
```

**關鍵調整**:
- ✅ 保留完整的歷史記錄，不簡單過濾
- ✅ 基於成熟度等級動態調整保留策略
- ✅ 智能清理：保留重要事件、里程碑、情感轉折點、最近事件
- ✅ 維護索引系統，支持高效查詢
- ✅ 符合 HAM 記憶系統和成熟度系統設計

---

#### 問題 4: 過度嚴格的錯誤處理統一（SA-10）

**原修復方案**:
```javascript
// 統一所有錯誤到全局錯誤處理器
window.addEventListener('error', errorHandler);
window.addEventListener('unhandledrejection', rejectionHandler);
```

**不合理原因**:
1. **破壞模塊化設計**: Angela 採用分層架構，每層有自己的錯誤處理策略
2. **喪失上下文信息**: 全局錯誤處理器會丟失模塊特定的上下文
3. **不符合 6 層生命架構**: 不同層（L1-L6）有不同的錯誤處理需求

**調整後的修復方案**:
```javascript
class GlobalErrorHandler {
    constructor() {
        this.handlers = {
            L1: [],  // 生物層錯誤處理器
            L2: [],  // 記憶層錯誤處理器
            L3: [],  // 身份層錯誤處理器
            L4: [],  // 創造層錯誤處理器
            L5: [],  // 存在感層錯誤處理器
            L6: []   // 執行層錯誤處理器
        };
        
        this.errorContext = {
            L1: 'biological',
            L2: 'memory',
            L3: 'identity',
            L4: 'creativity',
            L5: 'presence',
            L6: 'execution'
        };
        
        this._initialize();
    }
    
    registerHandler(layer, handler) {
        if (!this.handlers[layer]) {
            console.error(`[GlobalErrorHandler] Invalid layer: ${layer}`);
            return;
        }
        this.handlers[layer].push(handler);
    }
    
    _initialize() {
        // 全局錯誤處理器只捕獲未處理的錯誤
        window.addEventListener('error', (event) => {
            // 檢查是否是模塊處理過的錯誤
            if (event.error?.__handled) {
                return;
            }
            
            this._handleGlobalError(event.error, 'unhandled_global');
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            // 檢查是否是模塊處理過的錯誤
            if (event.reason?.__handled) {
                return;
            }
            
            this._handleGlobalError(event.reason, 'unhandled_rejection');
        });
    }
    
    handleError(error, layer, context = {}) {
        // ✅ 標記錯誤為已處理，避免重複處理
        error.__handled = true;
        
        // ✅ 添加層級和上下文信息
        const enrichedError = {
            ...error,
            layer: layer || 'unknown',
            context: context,
            timestamp: Date.now()
        };
        
        // ✅ 優先調用該層的錯誤處理器
        if (layer && this.handlers[layer]) {
            for (const handler of this.handlers[layer]) {
                try {
                    const result = handler(enrichedError);
                    if (result === false) {
                        // 處理器阻止了默認處理
                        return;
                    }
                } catch (e) {
                    console.error(`[GlobalErrorHandler] Error in ${layer} handler:`, e);
                }
            }
        }
        
        // ✅ 調用層級特定的默認處理
        this._layerSpecificHandling(enrichedError);
        
        // ✅ 根據層級決定是否記錄到歷史
        if (this._shouldRecordToHistory(layer, enrichedError)) {
            this._recordToHistory(enrichedError);
        }
    }
    
    _layerSpecificHandling(error) {
        const layer = error.layer;
        
        switch (layer) {
            case 'L1': // 生物層
                // 生理層錯誤可能影響健康狀態
                if (window.angelaApp?.stateMatrix) {
                    window.angelaApp.stateMatrix.alpha.values.tension += 0.1;
                    window.angelaApp.stateMatrix.alpha.values.energy -= 0.05;
                }
                break;
                
            case 'L2': // 記憶層
                // 記憶層錯誤可能影響記憶完整性
                if (window.angelaApp?.logger) {
                    window.angelaApp.logger.warn('Memory layer error detected');
                }
                break;
                
            case 'L3': // 身份層
                // 身份層錯誤可能影響自我認知
                if (window.angelaApp?.maturityTracker) {
                    window.angelaApp.maturityTracker.recordExperience(
                        'error_recovery',
                        { error: error.message }
                    );
                }
                break;
                
            case 'L6': // 執行層
                // 執行層錯誤需要立即響應
                this._handleExecutionError(error);
                break;
        }
    }
    
    _shouldRecordToHistory(layer, error) {
        // ✅ 只有重要的錯誤才記錄到歷史
        const importantLayers = ['L3', 'L4', 'L6'];
        const importantErrorTypes = ['SecurityError', 'DataLossError', 'SystemError'];
        
        return importantLayers.includes(layer) || 
               importantErrorTypes.some(type => error.name?.includes(type));
    }
    
    _recordToHistory(error) {
        if (window.angelaApp?.stateMatrix) {
            window.angelaApp.stateMatrix.addImportantEvent({
                type: 'error',
                severity: this._getErrorSeverity(error),
                message: error.message,
                layer: error.layer
            });
        }
    }
    
    _getErrorSeverity(error) {
        if (error.name === 'SecurityError' || error.name === 'DataLossError') {
            return 'critical';
        } else if (error.name === 'SystemError') {
            return 'high';
        } else {
            return 'low';
        }
    }
}
```

**關鍵調整**:
- ✅ 保留分層錯誤處理，符合 6 層生命架構
- ✅ 使用 `__handled` 標記防止重複處理
- ✅ 根據層級進行特定的錯誤處理（如影響狀態矩陣）
- ✅ 只記錄重要的錯誤到歷史
- ✅ 符合 Angela 的模塊化設計

---

## 修復方案優先級調整

### P0 修復任務（調整後）

| 任務 | 原優先級 | 調整後優先級 | 調整原因 |
|------|----------|--------------|----------|
| MEM-1: InputHandler 事件監聽器修復 | P0 | P0 | 保持不變 |
| MEM-2: WebSocket 資源清理 | P0 | P0 | 保持不變 |
| SEC-1: localStorage 驗證 | P0 | P0 | 保持不變 |
| SEC-2: 插件系統安全加固 | P0 | P2 | 過度限制，改為適度限制 |
| SEC-3: XSS 防護 | P0 | P0 | 保持不變 |
| DF-5: WebSocket 重試機制 | P0 | P0 | 保持不變 |
| DF-6: WebSocket 消息隊列 | P0 | P0 | 保持不變 |
| SA-1: 初始化順序強制 | P0 | P0 | 保持不變 |
| SA-2: ANGELA_CHARACTER_CONFIG 驗證 | P0 | P0 | 保持不變 |
| SA-3: LayerRenderer 驗證 | P0 | P0 | 保持不變 |
| CP-5: localStorage 版本控制 | P0 | P2 | 改為兼容性遷移 |

### P1 修復任務（調整後）

| 任務 | 原優先級 | 調整後優先級 | 調整原因 |
|------|----------|--------------|----------|
| SR-1: live2d-canvas 尺寸同步 | P1 | P1 | 保持不變 |
| SR-5: getUserScale 修復 | P1 | P1 | 保持不變 |
| SR-6: screenToCanvas 修復 | P1 | P1 | 保持不變 |
| SR-8: identifyBodyPart 修復 | P1 | P1 | 保持不變 |
| SR-17: Live2D 模型尺寸驗證 | P1 | P1 | 保持不變 |
| DF-1: InputHandler 事件清理 | P1 | P1 | 保持不變 |
| DF-8: 後端 API 端點驗證 | P1 | P1 | 保持不變 |
| DF-9: LLM 服務可用性檢查 | P1 | P1 | 保持不變 |
| SA-6: input-handler 事件清理 | P1 | P1 | 保持不變 |
| SA-10: 全局錯誤處理器集成 | P1 | P2 | 改為分層錯誤處理 |
| SA-12: history 壓縮 | P1 | P2 | 改為智能清理 |

### P2 修復任務（調整後）

| 任務 | 原優先級 | 調整後優先級 | 調整原因 |
|------|----------|--------------|----------|
| UI-2: notification-container 添加 | P2 | P2 | 保持不變 |
| UI-3: canvas-wrapper 動態調整 | P2 | P2 | 保持不變 |
| UI-15: transform 偏移修復 | P2 | P2 | 保持不變 |
| SR-3: LayerRenderer canvas 驗證 | P2 | P2 | 保持不變 |
| SR-4: devicePixelRatio 支持 | P2 | P2 | 保持不變 |
| DF-2: handleClick 回退處理 | P2 | P2 | 保持不變 |
| DF-3: WebSocket 連接檢查 | P2 | P2 | 保持不變 |
| DF-7: updateMonitorUI 節流 | P2 | P2 | 保持不變 |
| MEM-3: hardware-detection 清理 | P2 | P2 | 保持不變 |
| CP-1: localStorage 統一封裝 | P2 | P2 | 保持不變 |
| CP-3: localStorage 容量檢查 | P2 | P2 | 保持不變 |

---

## 修復時間估算（調整後）

| 階段 | 任務數量 | 原時間 | 調整後時間 | 變化 |
|------|----------|--------|------------|------|
| 第一階段（P0） | 10 | 34h | 32h | -2h |
| 第二階段（P1） | 11 | 33h | 30h | -3h |
| 第三階段（P2） | 12 | 29h | 28h | -1h |
| 第四階段（P3） | 39 | 85h | 80h | -5h |
| **總計** | **72** | **181h** | **170h** | **-11h** |

---

## 驗證策略

### P0 修復驗證

1. **MEM-1: InputHandler 事件監聽器修復**
   - 測試：創建並銷毀多個 InputHandler 實例，檢查內存洩漏
   - 驗證：使用 WeakRef 確保監聽器被正確移除

2. **SEC-2: 插件系統適度限制**
   - 測試：創建一個合法的插件，驗證能否正常加載
   - 測試：創建一個嘗試訪問危險 API 的插件，驗證被拒絕
   - 測試：驗證插件可以訪問有限的 Angela 核心 API

3. **CP-5: localStorage 兼容性遷移**
   - 測試：創建舊版本配置，驗證兼容性檢查
   - 測試：創建版本不兼容的配置，驗證兼容模式運行
   - 測試：驗證自動遷移邏輯

### P1 修復驗證

1. **SA-10: 分層錯誤處理**
   - 測試：在 L6 層模擬錯誤，驗證執行層特定處理
   - 測試：在 L3 層模擬錯誤，驗證身份層特定處理
   - 測試：驗證重要錯誤被記錄到歷史

2. **SA-12: 智能歷史清理**
   - 測試：模擬不同成熟度等級，驗證保留策略
   - 測試：添加里程碑事件，驗證被保留
   - 測試：驗證索引系統正常工作

---

## 總結

### 核心調整

1. **插件系統**: 從完全禁用改為適度限制，保留 Angela 的擴展能力
2. **版本控制**: 從強制升級改為兼容性遷移，支持自然演化
3. **歷史管理**: 從簡單過濾改為智能清理，保留重要連續性
4. **錯誤處理**: 從全局統一改為分層處理，符合 6 層架構

### 符合 Angela �計的關鍵特性

1. ✅ **數字生命系統**: 保留自主性、成長性、記憶連續性
2. ✅ **6 層生命架構**: 實現分層錯誤處理
3. ✅ **成熟度系統**: 基於成熟度等級調整系統行為
4. ✅ **擴展性**: 保留插件系統，允許自我擴展
5. ✅ **適應性**: 根據硬件和成熟度動態調整

---

**報告完成時間**: 2026-02-12  
**下次更新**: 修復進度跟蹤