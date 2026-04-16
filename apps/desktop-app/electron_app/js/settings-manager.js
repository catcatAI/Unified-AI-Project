/**
 * Angela AI - Settings Manager (Renderer Side)
 * 
 * Handles settings retrieval and persistence via Electron IPC.
 * Replaces legacy localStorage-based storage.
 */

class SettingsManager {
    constructor() {
        this.settings = {};
        this.isInitialized = false;
        this.listeners = [];
    }

    /**
     * Initialize settings by loading them from the main process
     */
    async initialize() {
        if (this.isInitialized) return;

        try {
            if (window.electronAPI && window.electronAPI.settings) {
                // Try to get settings from main process
                this.settings = await window.electronAPI.settings.getAll() || {};
                console.log('[SettingsManager] Loaded from main process');
            } else {
                // Fallback to localStorage if IPC not available (e.g. browser testing)
                const legacy = localStorage.getItem('angela_settings');
                this.settings = legacy ? JSON.parse(legacy) : {};
                console.warn('[SettingsManager] IPC not available, using localStorage fallback');
            }
            this.isInitialized = true;
            return true;
        } catch (error) {
            console.error('[SettingsManager] Initialization failed:', error);
            return false;
        }
    }

    /**
     * Get a setting value
     * @param {string} key - Setting key (e.g. 'appearance.theme')
     * @param {*} defaultValue - Value to return if key doesn't exist
     */
    get(key, defaultValue = null) {
        const parts = key.split('.');
        let current = this.settings;

        for (const part of parts) {
            if (current === null || current === undefined || typeof current !== 'object') {
                return defaultValue;
            }
            current = current[part];
        }

        return current !== undefined ? current : defaultValue;
    }

    /**
     * Set a setting value
     * @param {string} key - Setting key
     * @param {*} value - New value
     */
    async set(key, value) {
        const parts = key.split('.');
        let current = this.settings;

        // Traverse to the parent object
        for (let i = 0; i < parts.length - 1; i++) {
            const part = parts[i];
            if (!(part in current)) {
                current[part] = {};
            }
            current = current[part];
        }

        const lastPart = parts[parts.length - 1];
        current[lastPart] = value;

        // Persist
        await this.sync();
        
        // Notify listeners
        this._notify(key, value);
    }

    /**
     * Sync local settings object to the main process
     */
    async sync() {
        try {
            if (window.electronAPI && window.electronAPI.settings) {
                await window.electronAPI.settings.setAll(this.settings);
            } else {
                localStorage.setItem('angela_settings', JSON.stringify(this.settings));
            }
        } catch (error) {
            console.error('[SettingsManager] Sync failed:', error);
        }
    }

    /**
     * Reset all settings to defaults
     */
    async reset() {
        try {
            if (window.electronAPI && window.electronAPI.settings) {
                this.settings = await window.electronAPI.settings.reset();
            } else {
                this.settings = {};
                localStorage.removeItem('angela_settings');
            }
            this._notify('all', this.settings);
        } catch (error) {
            console.error('[SettingsManager] Reset failed:', error);
        }
    }

    /**
     * Listen for setting changes
     */
    onChange(callback) {
        this.listeners.push(callback);
    }

    _notify(key, value) {
        this.listeners.forEach(cb => cb(key, value));
    }
}

// Export singleton
const settingsManager = new SettingsManager();
if (typeof module !== 'undefined' && module.exports) {
    module.exports = settingsManager;
} else {
    window.settingsManager = settingsManager;
}
