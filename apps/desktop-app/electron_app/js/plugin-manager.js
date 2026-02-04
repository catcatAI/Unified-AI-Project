class PluginManager {
    constructor(config = {}) {
        this.config = {
            pluginsDir: config.pluginsDir || 'plugins',
            autoLoad: config.autoLoad !== false,
            sandbox: config.sandbox !== false
        };
        
        this.plugins = new Map();
        this.hooks = new Map();
        this.loaded = false;
        this.logger = null;
    }
    
    setLogger(logger) {
        this.logger = logger;
    }
    
    _log(level, message, data) {
        if (this.logger) {
            this.logger[level](`[PluginManager] ${message}`, data);
        } else {
            console[level](`[PluginManager] ${message}`, data);
        }
    }
    
    async init() {
        this._log('info', 'Initializing plugin manager');
        
        if (this.config.autoLoad) {
            await this.loadPluginsFromDir();
        }
        
        this.loaded = true;
        this._log('info', 'Plugin manager initialized', {
            pluginsCount: this.plugins.size
        });
    }
    
    async loadPluginsFromDir() {
        this._log('info', `Loading plugins from ${this.config.pluginsDir}`);
        
        try {
            if (window.electronAPI && window.electronAPI.plugins) {
                const pluginList = await window.electronAPI.plugins.list();
                
                for (const pluginInfo of pluginList) {
                    try {
                        await this.loadPlugin(pluginInfo.name, pluginInfo.path);
                    } catch (e) {
                        this._log('error', `Failed to load plugin ${pluginInfo.name}`, e);
                    }
                }
            }
        } catch (e) {
            this._log('warn', 'Could not list plugins from directory', e);
        }
    }
    
    async loadPlugin(name, source = null) {
        if (this.plugins.has(name)) {
            this._log('warn', `Plugin ${name} is already loaded`);
            return false;
        }
        
        this._log('info', `Loading plugin: ${name}`);
        
        try {
            let pluginCode;
            
            if (source) {
                pluginCode = await this._loadFromFile(source);
            } else if (window.electronAPI && window.electronAPI.plugins) {
                pluginCode = await window.electronAPI.plugins.load(name);
            } else {
                pluginCode = await this._loadFromLocalStorage(name);
            }
            
            const plugin = this._createPlugin(name, pluginCode);
            
            await this._validatePlugin(plugin);
            await this._installPlugin(plugin);
            
            this.plugins.set(name, plugin);
            
            this._log('info', `Plugin ${name} loaded successfully`);
            return true;
        } catch (e) {
            this._log('error', `Failed to load plugin ${name}`, e);
            throw e;
        }
    }
    
    _loadFromFile(path) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error(`Failed to read file: ${path}`));
            reader.readAsText(path);
        });
    }
    
    _loadFromLocalStorage(name) {
        return new Promise((resolve, reject) => {
            const stored = localStorage.getItem(`plugin_${name}`);
            if (stored) {
                resolve(stored);
            } else {
                reject(new Error(`Plugin ${name} not found in storage`));
            }
        });
    }
    
    _createPlugin(name, code) {
        let plugin;
        
        try {
            if (this.config.sandbox) {
                const sandbox = this._createSandbox();
                const sandboxedCode = `
                    with (sandbox) {
                        ${code}
                    }
                `;
                
                const factory = new Function('sandbox', sandboxedCode);
                factory(sandbox);
                plugin = sandbox.exports;
            } else {
                const factory = new Function(`
                    ${code}
                    return exports || {};
                `);
                plugin = factory();
            }
        } catch (e) {
            throw new Error(`Failed to create plugin instance: ${e.message}`);
        }
        
        plugin.name = name;
        plugin.enabled = true;
        
        return plugin;
    }
    
    _createSandbox() {
        const sandbox = {
            exports: {},
            console: {
                log: (...args) => this._log('info', `[Sandbox]`, args),
                warn: (...args) => this._log('warn', `[Sandbox]`, args),
                error: (...args) => this._log('error', `[Sandbox]`, args)
            },
            setTimeout,
            setInterval,
            clearTimeout,
            clearInterval,
            Promise,
            JSON,
            Math,
            Date,
            Array,
            Object,
            String,
            Number,
            Boolean,
            RegExp,
            Map,
            Set,
            WeakMap,
            WeakSet
        };
        
        return sandbox;
    }
    
    async _validatePlugin(plugin) {
        if (!plugin.name) {
            throw new Error('Plugin must have a name');
        }
        
        if (typeof plugin.version !== 'string') {
            throw new Error('Plugin must have a version string');
        }
        
        if (!plugin.description) {
            plugin.description = 'No description provided';
        }
        
        if (typeof plugin.activate !== 'function' && typeof plugin.deactivate !== 'function') {
            throw new Error('Plugin must have either activate() or deactivate() method');
        }
        
        if (plugin.dependencies && !Array.isArray(plugin.dependencies)) {
            throw new Error('Plugin dependencies must be an array');
        }
        
        if (plugin.hooks && typeof plugin.hooks !== 'object') {
            throw new Error('Plugin hooks must be an object');
        }
    }
    
    async _installPlugin(plugin) {
        if (plugin.dependencies) {
            for (const dep of plugin.dependencies) {
                if (!this.plugins.has(dep)) {
                    this._log('warn', `Plugin ${plugin.name} depends on ${dep}, but it is not loaded`);
                }
            }
        }
        
        if (plugin.hooks) {
            for (const [hookName, handler] of Object.entries(plugin.hooks)) {
                if (typeof handler === 'function') {
                    this.addHook(hookName, handler, plugin.name);
                }
            }
        }
        
        if (typeof plugin.activate === 'function') {
            await plugin.activate({
                manager: this,
                log: (level, message, data) => this._log(level, `[${plugin.name}] ${message}`, data),
                addHook: (hookName, handler) => this.addHook(hookName, handler, plugin.name),
                removeHook: (hookName) => this.removeHook(hookName, plugin.name),
                getAPI: () => this._getPublicAPI()
            });
        }
    }
    
    async unloadPlugin(name) {
        if (!this.plugins.has(name)) {
            this._log('warn', `Plugin ${name} is not loaded`);
            return false;
        }
        
        const plugin = this.plugins.get(name);
        
        try {
            if (typeof plugin.deactivate === 'function') {
                await plugin.deactivate();
            }
            
            if (plugin.hooks) {
                for (const hookName of Object.keys(plugin.hooks)) {
                    this.removeHook(hookName, name);
                }
            }
            
            this.plugins.delete(name);
            
            this._log('info', `Plugin ${name} unloaded successfully`);
            return true;
        } catch (e) {
            this._log('error', `Failed to unload plugin ${name}`, e);
            return false;
        }
    }
    
    enablePlugin(name) {
        const plugin = this.plugins.get(name);
        if (plugin) {
            plugin.enabled = true;
            this._log('info', `Plugin ${name} enabled`);
            return true;
        }
        return false;
    }
    
    disablePlugin(name) {
        const plugin = this.plugins.get(name);
        if (plugin) {
            plugin.enabled = false;
            this._log('info', `Plugin ${name} disabled`);
            return true;
        }
        return false;
    }
    
    addHook(hookName, handler, pluginName = null) {
        if (!this.hooks.has(hookName)) {
            this.hooks.set(hookName, []);
        }
        
        this.hooks.get(hookName).push({
            handler,
            pluginName
        });
    }
    
    removeHook(hookName, pluginName) {
        if (!this.hooks.has(hookName)) {
            return;
        }
        
        const hooks = this.hooks.get(hookName);
        this.hooks.set(
            hookName,
            hooks.filter(h => h.pluginName !== pluginName)
        );
    }
    
    async executeHook(hookName, data = null) {
        if (!this.hooks.has(hookName)) {
            return [];
        }
        
        const handlers = this.hooks.get(hookName)
            .filter(h => {
                const plugin = this.plugins.get(h.pluginName);
                return plugin && plugin.enabled;
            });
        
        const results = [];
        
        for (const { handler, pluginName } of handlers) {
            try {
                const result = await handler(data);
                results.push({ pluginName, result, error: null });
            } catch (e) {
                this._log('error', `Hook ${hookName} failed in plugin ${pluginName}`, e);
                results.push({ pluginName, result: null, error: e });
            }
        }
        
        return results;
    }
    
    getPlugin(name) {
        return this.plugins.get(name);
    }
    
    getPlugins() {
        return Array.from(this.plugins.values()).map(plugin => ({
            name: plugin.name,
            version: plugin.version,
            description: plugin.description,
            enabled: plugin.enabled
        }));
    }
    
    isPluginLoaded(name) {
        return this.plugins.has(name);
    }
    
    isPluginEnabled(name) {
        const plugin = this.plugins.get(name);
        return plugin && plugin.enabled;
    }
    
    _getPublicAPI() {
        return {
            stateMatrix: window.angelaApp?.stateMatrix,
            performanceManager: window.angelaApp?.performanceManager,
            maturityTracker: window.angelaApp?.maturityTracker,
            precisionManager: window.angelaApp?.precisionManager,
            live2DManager: window.angelaApp?.live2dManager,
            inputHandler: window.angelaApp?.inputHandler,
            audioHandler: window.angelaApp?.audioHandler,
            hapticHandler: window.angelaApp?.hapticHandler,
            wallpaperHandler: window.angelaApp?.wallpaperHandler,
            i18n: window.i18n,
            theme: window.theme,
            logger: window.angelaApp?.logger
        };
    }
    
    async exportPlugins() {
        const exportData = {};
        
        for (const [name, plugin] of this.plugins.entries()) {
            if (plugin.exportable !== false) {
                exportData[name] = {
                    version: plugin.version,
                    config: plugin.config || {}
                };
            }
        }
        
        return exportData;
    }
    
    async importPlugins(importData) {
        for (const [name, data] of Object.entries(importData)) {
            try {
                if (this.plugins.has(name)) {
                    const plugin = this.plugins.get(name);
                    if (plugin.configure && typeof plugin.configure === 'function') {
                        await plugin.configure(data.config);
                    }
                }
            } catch (e) {
                this._log('error', `Failed to import plugin ${name}`, e);
            }
        }
    }
    
    destroy() {
        this.plugins.forEach(async (plugin, name) => {
            await this.unloadPlugin(name);
        });
        
        this.plugins.clear();
        this.hooks.clear();
    }
}