class DataPersistence {
    constructor(config = {}) {
        this.config = {
            prefix: config.prefix || 'angela',
            encrypt: config.encrypt || false,
            autoSave: config.autoSave !== false,
            autoSaveInterval: config.autoSaveInterval || 60000,
            compression: config.compression || false
        };
        
        this.data = {};
        this.autoSaveTimer = null;
        this.pendingSave = false;
        this.changeCallbacks = [];
        
        this._init();
    }
    
    _init() {
        this._loadAll();
        
        if (this.config.autoSave) {
            this._startAutoSave();
        }
        
        window.addEventListener('beforeunload', () => {
            this.saveAll();
        });
        
        window.addEventListener('storage', (e) => {
            if (e.key && e.key.startsWith(this.config.prefix)) {
                this._handleStorageChange(e);
            }
        });
    }
    
    _startAutoSave() {
        this.autoSaveTimer = setInterval(() => {
            this.saveAll();
        }, this.config.autoSaveInterval);
    }
    
    _stopAutoSave() {
        if (this.autoSaveTimer) {
            clearInterval(this.autoSaveTimer);
            this.autoSaveTimer = null;
        }
    }
    
    _getKey(key) {
        return `${this.config.prefix}_${key}`;
    }
    
    _handleStorageChange(event) {
        if (event.newValue !== null) {
            try {
                const key = event.key.replace(`${this.config.prefix}_`, '');
                const value = JSON.parse(event.newValue);
                this.data[key] = value;
                this._notifyChange(key, value, 'external');
            } catch (e) {
                console.error('Failed to handle storage change:', e);
            }
        }
    }
    
    _notifyChange(key, value, source = 'local') {
        this.changeCallbacks.forEach(callback => {
            try {
                callback(key, value, source);
            } catch (e) {
                console.error('Persistence change callback error:', e);
            }
        });
    }
    
    get(key, defaultValue = null) {
        if (key in this.data) {
            return this.data[key];
        }
        return defaultValue;
    }
    
    set(key, value, autoSave = true) {
        const oldValue = this.data[key];
        this.data[key] = value;
        
        if (JSON.stringify(oldValue) !== JSON.stringify(value)) {
            this._notifyChange(key, value, 'local');
            
            if (autoSave && this.config.autoSave) {
                this._scheduleSave(key);
            }
        }
        
        return value;
    }
    
    update(key, updates, autoSave = true) {
        const currentValue = this.get(key, {});
        const updatedValue = { ...currentValue, ...updates };
        return this.set(key, updatedValue, autoSave);
    }
    
    delete(key, autoSave = true) {
        if (key in this.data) {
            const value = this.data[key];
            delete this.data[key];
            
            try {
                localStorage.removeItem(this._getKey(key));
            } catch (e) {
                console.error('Failed to delete key from storage:', e);
            }
            
            this._notifyChange(key, null, 'local');
            
            if (autoSave && this.config.autoSave) {
                this._scheduleSave(key);
            }
            
            return true;
        }
        return false;
    }
    
    has(key) {
        return key in this.data;
    }
    
    getKeys(pattern = null) {
        let keys = Object.keys(this.data);
        
        if (pattern) {
            const regex = new RegExp(pattern);
            keys = keys.filter(key => regex.test(key));
        }
        
        return keys;
    }
    
    _loadAll() {
        const prefix = this._getKey('');
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            
            if (key && key.startsWith(prefix)) {
                try {
                    const value = localStorage.getItem(key);
                    if (value) {
                        const dataKey = key.substring(prefix.length);
                        
                        // FIX: Handle non-JSON values (legacy data or corrupted entries)
                        let parsedValue;
                        try {
                            // Try to parse as JSON first
                            parsedValue = JSON.parse(value);
                        } catch (jsonError) {
                            // If JSON parsing fails, use the raw value
                            // This handles legacy data that wasn't stored as JSON
                            console.warn(`Key ${key} is not valid JSON, using raw value`);
                            parsedValue = value;
                        }
                        
                        this.data[dataKey] = parsedValue;
                        console.log(`Loaded key: ${dataKey}`);
                    }
                } catch (e) {
                    console.error(`Failed to load key ${key}:`, e);
                    // Continue loading other keys even if one fails
                }
            }
        }
        console.log(`_loadAll complete: ${Object.keys(this.data).length} keys loaded`);
    }
    
    saveAll() {
        Object.keys(this.data).forEach(key => {
            this._saveKey(key);
        });
        
        this.pendingSave = false;
    }
    
    _saveKey(key) {
        try {
            const value = this.data[key];
            const serialized = JSON.stringify(value);
            localStorage.setItem(this._getKey(key), serialized);
        } catch (e) {
            if (e.name === 'QuotaExceededError') {
                console.warn('Storage quota exceeded, attempting to free space...');
                this._freeSpace();
                
                try {
                    const serialized = JSON.stringify(this.data[key]);
                    localStorage.setItem(this._getKey(key), serialized);
                } catch (retryError) {
                    console.error('Failed to save after freeing space:', retryError);
                }
            } else {
                console.error(`Failed to save key ${key}:`, e);
            }
        }
    }
    
    _scheduleSave(key) {
        if (!this.pendingSave) {
            this.pendingSave = true;
            requestAnimationFrame(() => {
                this._saveKey(key);
                this.pendingSave = false;
            });
        }
    }
    
    _freeSpace() {
        const keys = this.getKeys();
        const sizeLimit = 100;
        
        if (keys.length > sizeLimit) {
            const keysToDelete = keys.slice(0, keys.length - sizeLimit);
            keysToDelete.forEach(key => {
                this.delete(key, false);
            });
            console.log(`Freed space by deleting ${keysToDelete.length} keys`);
        }
    }
    
    clear(autoSave = true) {
        const keys = this.getKeys();
        keys.forEach(key => {
            this.delete(key, false);
        });
        
        if (autoSave && this.config.autoSave) {
            this.saveAll();
        }
    }
    
    export(keys = null) {
        const exportData = keys 
            ? keys.reduce((acc, key) => {
                acc[key] = this.get(key);
                return acc;
            }, {})
            : { ...this.data };
        
        return JSON.stringify(exportData, null, 2);
    }
    
    import(jsonString, merge = true) {
        try {
            const data = JSON.parse(jsonString);
            
            Object.keys(data).forEach(key => {
                if (merge || !this.has(key)) {
                    this.set(key, data[key], false);
                }
            });
            
            this.saveAll();
            
            return { success: true, importedKeys: Object.keys(data) };
        } catch (e) {
            console.error('Failed to import data:', e);
            return { success: false, error: e.message };
        }
    }
    
    getStorageInfo() {
        let totalSize = 0;
        let keyCount = 0;
        
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this._getKey(''))) {
                const value = localStorage.getItem(key);
                totalSize += value.length * 2;
                keyCount++;
            }
        }
        
        const maxSize = 5 * 1024 * 1024;
        const usagePercent = (totalSize / maxSize) * 100;
        
        return {
            keyCount,
            totalSize,
            maxSize,
            usagePercent,
            availableSpace: maxSize - totalSize
        };
    }
    
    onChange(callback) {
        this.changeCallbacks.push(callback);
    }
    
    offChange(callback) {
        const index = this.changeCallbacks.indexOf(callback);
        if (index > -1) {
            this.changeCallbacks.splice(index, 1);
        }
    }
    
    enableAutoSave() {
        if (!this.config.autoSave) {
            this.config.autoSave = true;
            this._startAutoSave();
        }
    }
    
    disableAutoSave() {
        this.config.autoSave = false;
        this._stopAutoSave();
    }
    
    destroy() {
        this._stopAutoSave();
        this.changeCallbacks = [];
        this.data = {};
    }
}

class StatePersistence extends DataPersistence {
    constructor(config = {}) {
        super({
            ...config,
            prefix: config.prefix || 'angela_state'
        });
        
        this.stateKey = config.stateKey || 'current_state';
        this.historyKey = config.historyKey || 'state_history';
        this.maxHistorySize = config.maxHistorySize || 100;
    }
    
    saveState(state) {
        this.set(this.stateKey, state);
        this._addToHistory(state);
    }
    
    loadState() {
        return this.get(this.stateKey);
    }
    
    _addToHistory(state) {
        const history = this.get(this.historyKey, []);
        
        history.push({
            state: { ...state },
            timestamp: Date.now()
        });
        
        if (history.length > this.maxHistorySize) {
            history.shift();
        }
        
        this.set(this.historyKey, history);
    }
    
    getHistory(limit = null) {
        const history = this.get(this.historyKey, []);
        return limit ? history.slice(-limit) : history;
    }
    
    restoreFromHistory(index) {
        const history = this.get(this.historyKey, []);
        
        if (index >= 0 && index < history.length) {
            const snapshot = history[index];
            this.saveState(snapshot.state);
            return snapshot.state;
        }
        
        return null;
    }
    
    clearHistory() {
        this.set(this.historyKey, []);
    }
}