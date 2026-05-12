/**
 * StatePersistence - State management with history tracking
 * Manages application state with persistence and history capabilities
 */

class StatePersistence {
    constructor(options = {}) {
        this.maxHistorySize = options.maxHistorySize || 100;
        this.currentState = {};
        this.history = [];
        this.listeners = new Map();
    }

    saveState(key, value) {
        const previousValue = this.currentState[key];
        this.currentState[key] = value;

        const changeRecord = {
            key,
            previousValue,
            newValue: value,
            timestamp: Date.now()
        };

        this.history.push(changeRecord);
        if (this.history.length > this.maxHistorySize) {
            this.history.shift();
        }

        this._notifyListeners(key, value, previousValue);
        return changeRecord;
    }

    getState(key) {
        return this.currentState[key];
    }

    getAllState() {
        return { ...this.currentState };
    }

    clearState() {
        this.currentState = {};
        this.history = [];
    }

    getHistory(key = null) {
        if (key === null) {
            return [...this.history];
        }
        return this.history.filter(record => record.key === key);
    }

    restoreFromHistory(index) {
        if (index < 0 || index >= this.history.length) {
            return false;
        }
        const record = this.history[index];
        this.currentState[record.key] = record.previousValue;
        this._notifyListeners(record.key, record.previousValue, record.newValue);
        return true;
    }

    subscribe(key, callback) {
        if (!this.listeners.has(key)) {
            this.listeners.set(key, new Set());
        }
        this.listeners.get(key).add(callback);
        return () => {
            this.listeners.get(key).delete(callback);
        };
    }

    _notifyListeners(key, newValue, previousValue) {
        const keyListeners = this.listeners.get(key);
        if (keyListeners) {
            keyListeners.forEach(callback => {
                try {
                    callback(newValue, previousValue);
                } catch (e) {
                    console.error('[StatePersistence] Listener error:', e);
                }
            });
        }
    }

    serialize() {
        return JSON.stringify({
            currentState: this.currentState,
            history: this.history,
            maxHistorySize: this.maxHistorySize
        });
    }

    deserialize(data) {
        try {
            if (!data || typeof data !== 'string') {
                console.warn('[StatePersistence] Invalid data type for deserialization');
                return false;
            }
            const parsed = JSON.parse(data);
            if (parsed === null || parsed === undefined) {
                console.warn('[StatePersistence] Parsed data is null or undefined');
                return false;
            }
            this.currentState = parsed.currentState || {};
            this.history = parsed.history || [];
            this.maxHistorySize = parsed.maxHistorySize || 100;
            return true;
        } catch (e) {
            console.error('[StatePersistence] Deserialize error:', e);
            return false;
        }
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = StatePersistence;
}