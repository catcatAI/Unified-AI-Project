class UserManager {
    constructor(config = {}) {
        this.config = {
            storageKey: config.storageKey || 'angela_users',
            currentKey: config.currentKey || 'angela_current_user',
            autoSave: config.autoSave !== false
        };
        
        this.users = new Map();
        this.currentUser = null;
        this.changeCallbacks = [];
        
        this._init();
    }
    
    _init() {
        this._loadUsers();
        this._loadCurrentUser();
        
        if (!this.currentUser && this.users.size > 0) {
            const firstUser = Array.from(this.users.values())[0];
            this.setCurrentUser(firstUser.id);
        }
    }
    
    _loadUsers() {
        try {
            const data = localStorage.getItem(this.config.storageKey);
            if (data) {
                const usersData = JSON.parse(data);
                usersData.forEach(userData => {
                    this.users.set(userData.id, userData);
                });
            }
        } catch (e) {
            console.error('Failed to load users:', e);
        }
    }
    
    _saveUsers() {
        if (!this.config.autoSave) return;
        
        try {
            const usersData = Array.from(this.users.values());
            localStorage.setItem(this.config.storageKey, JSON.stringify(usersData));
        } catch (e) {
            console.error('Failed to save users:', e);
        }
    }
    
    _loadCurrentUser() {
        try {
            const userId = localStorage.getItem(this.config.currentKey);
            if (userId && this.users.has(userId)) {
                this.currentUser = this.users.get(userId);
            }
        } catch (e) {
            console.error('Failed to load current user:', e);
        }
    }
    
    _saveCurrentUser() {
        if (this.currentUser) {
            localStorage.setItem(this.config.currentKey, this.currentUser.id);
        } else {
            localStorage.removeItem(this.config.currentKey);
        }
    }
    
    getCurrentUser() {
        return this.currentUser;
    }
    
    setCurrentUser(userId) {
        if (!this.users.has(userId)) {
            console.warn(`User ${userId} not found`);
            return false;
        }
        
        const oldUser = this.currentUser;
        this.currentUser = this.users.get(userId);
        this._saveCurrentUser();
        
        this._notifyChange('currentUser', this.currentUser, oldUser);
        return true;
    }
    
    createUser(userData) {
        const userId = userData.id || this._generateUserId();
        
        if (this.users.has(userId)) {
            console.warn(`User ${userId} already exists`);
            return null;
        }
        
        const newUser = {
            id: userId,
            name: userData.name || 'Anonymous',
            avatar: userData.avatar || null,
            preferences: userData.preferences || {},
            stats: {
                interactions: 0,
                clickCount: 0,
                dragCount: 0,
                speechCount: 0,
                touchCount: 0,
                sessionCount: 0,
                firstSeen: Date.now(),
                lastSeen: Date.now()
            },
            relationships: {
                trust: 0.5,
                intimacy: 0.3,
                bond: 0.4
            },
            settings: userData.settings || {},
            createdAt: Date.now(),
            updatedAt: Date.now()
        };
        
        this.users.set(userId, newUser);
        this._saveUsers();
        
        this._notifyChange('userCreated', newUser);
        return newUser;
    }
    
    updateUser(userId, updates) {
        if (!this.users.has(userId)) {
            console.warn(`User ${userId} not found`);
            return false;
        }
        
        const user = this.users.get(userId);
        const updatedUser = {
            ...user,
            ...updates,
            id: user.id,
            updatedAt: Date.now()
        };
        
        this.users.set(userId, updatedUser);
        this._saveUsers();
        
        if (this.currentUser && this.currentUser.id === userId) {
            this.currentUser = updatedUser;
        }
        
        this._notifyChange('userUpdated', updatedUser);
        return true;
    }
    
    deleteUser(userId) {
        if (!this.users.has(userId)) {
            console.warn(`User ${userId} not found`);
            return false;
        }
        
        const deletedUser = this.users.get(userId);
        this.users.delete(userId);
        this._saveUsers();
        
        if (this.currentUser && this.currentUser.id === userId) {
            this.currentUser = null;
            this._saveCurrentUser();
        }
        
        this._notifyChange('userDeleted', deletedUser);
        return true;
    }
    
    getUser(userId) {
        return this.users.get(userId) || null;
    }
    
    getAllUsers() {
        return Array.from(this.users.values());
    }
    
    updateStats(userId, statsUpdates) {
        if (!this.users.has(userId)) {
            return false;
        }
        
        const user = this.users.get(userId);
        user.stats = {
            ...user.stats,
            ...statsUpdates
        };
        user.stats.lastSeen = Date.now();
        user.updatedAt = Date.now();
        
        this._saveUsers();
        
        if (this.currentUser && this.currentUser.id === userId) {
            this.currentUser = user;
        }
        
        return true;
    }
    
    incrementInteraction(userId, type) {
        if (!this.users.has(userId)) {
            return false;
        }
        
        const user = this.users.get(userId);
        user.stats.interactions++;
        
        switch (type) {
            case 'click':
                user.stats.clickCount++;
                user.relationships.trust = Math.min(1, user.relationships.trust + 0.01);
                break;
            case 'drag':
                user.stats.dragCount++;
                user.relationships.intimacy = Math.min(1, user.relationships.intimacy + 0.005);
                break;
            case 'speech':
                user.stats.speechCount++;
                user.relationships.bond = Math.min(1, user.relationships.bond + 0.02);
                break;
            case 'touch':
                user.stats.touchCount++;
                user.relationships.trust = Math.min(1, user.relationships.trust + 0.015);
                user.relationships.intimacy = Math.min(1, user.relationships.intimacy + 0.01);
                break;
        }
        
        user.stats.lastSeen = Date.now();
        user.updatedAt = Date.now();
        
        this._saveUsers();
        
        if (this.currentUser && this.currentUser.id === userId) {
            this.currentUser = user;
        }
        
        return true;
    }
    
    updateRelationship(userId, relationshipUpdates) {
        if (!this.users.has(userId)) {
            return false;
        }
        
        const user = this.users.get(userId);
        user.relationships = {
            ...user.relationships,
            ...relationshipUpdates
        };
        
        Object.keys(user.relationships).forEach(key => {
            user.relationships[key] = Math.max(0, Math.min(1, user.relationships[key]));
        });
        
        user.updatedAt = Date.now();
        
        this._saveUsers();
        
        if (this.currentUser && this.currentUser.id === userId) {
            this.currentUser = user;
        }
        
        return true;
    }
    
    getRelationshipLevel(userId) {
        const user = this.getUser(userId);
        if (!user) return null;
        
        const { trust, intimacy, bond } = user.relationships;
        const average = (trust + intimacy + bond) / 3;
        
        if (average < 0.2) return 'stranger';
        if (average < 0.4) return 'acquaintance';
        if (average < 0.6) return 'friend';
        if (average < 0.8) return 'close_friend';
        return 'intimate';
    }
    
    _generateUserId() {
        return `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
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
    
    _notifyChange(event, data) {
        this.changeCallbacks.forEach(callback => {
            try {
                callback(event, data);
            } catch (e) {
                console.error('User manager change callback error:', e);
            }
        });
    }
    
    exportUser(userId) {
        const user = this.getUser(userId);
        if (!user) return null;
        
        return JSON.stringify(user, null, 2);
    }
    
    exportAllUsers() {
        return JSON.stringify(Array.from(this.users.values()), null, 2);
    }
    
    importUser(jsonString) {
        try {
            const userData = JSON.parse(jsonString);
            
            if (userData.id && this.users.has(userData.id)) {
                this.updateUser(userData.id, userData);
            } else {
                this.createUser(userData);
            }
            
            return { success: true };
        } catch (e) {
            console.error('Failed to import user:', e);
            return { success: false, error: e.message };
        }
    }
    
    clearAllUsers() {
        this.users.clear();
        this.currentUser = null;
        this._saveUsers();
        this._saveCurrentUser();
        
        this._notifyChange('usersCleared', null);
    }
}

class PerformanceMonitor {
    constructor(config = {}) {
        this.config = {
            maxMetrics: config.maxMetrics || 1000,
            sampleInterval: config.sampleInterval || 1000,
            autoCollect: config.autoCollect !== false
        };
        
        this.metrics = [];
        this.startTimestamp = Date.now();
        this.currentSession = {
            startTime: Date.now(),
            frameCount: 0,
            interactionCount: 0
        };
        this.collecting = false;
        this.collectTimer = null;
    }
    
    startCollecting() {
        if (this.collecting) return;
        
        this.collecting = true;
        this.collectTimer = setInterval(() => {
            this._collectMetrics();
        }, this.config.sampleInterval);
    }
    
    stopCollecting() {
        if (!this.collecting) return;
        
        this.collecting = false;
        clearInterval(this.collectTimer);
        this.collectTimer = null;
    }
    
    _collectMetrics() {
        const metrics = {
            timestamp: Date.now(),
            fps: this._measureFPS(),
            memory: this._measureMemory(),
            timing: this._measureTiming(),
            network: this._measureNetwork(),
            custom: {}
        };
        
        this.metrics.push(metrics);
        
        if (this.metrics.length > this.config.maxMetrics) {
            this.metrics.shift();
        }
        
        if (window.performance && window.performance.mark) {
            window.performance.mark('perf-monitor-collect');
        }
    }
    
    _measureFPS() {
        if (!window.performance || !window.performance.now) {
            return null;
        }
        
        const now = performance.now();
        const delta = now - (this.lastFrameTime || now);
        this.lastFrameTime = now;
        
        const fps = 1000 / delta;
        return Math.round(fps * 100) / 100;
    }
    
    _measureMemory() {
        if (!window.performance || !window.performance.memory) {
            return null;
        }
        
        const memory = window.performance.memory;
        return {
            usedJSHeapSize: memory.usedJSHeapSize,
            totalJSHeapSize: memory.totalJSHeapSize,
            jsHeapSizeLimit: memory.jsHeapSizeLimit,
            usedPercent: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
        };
    }
    
    _measureTiming() {
        if (!window.performance || !window.performance.now) {
            return null;
        }
        
        const timing = {
            navigationStart: performance.timing?.navigationStart,
            domContentLoaded: performance.timing?.domContentLoadedEventEnd - performance.timing?.navigationStart,
            pageLoad: performance.timing?.loadEventEnd - performance.timing?.navigationStart,
            now: performance.now()
        };
        
        return timing;
    }
    
    _measureNetwork() {
        if (!window.navigator || !window.navigator.connection) {
            return null;
        }
        
        const connection = navigator.connection;
        return {
            effectiveType: connection.effectiveType,
            downlink: connection.downlink,
            rtt: connection.rtt,
            saveData: connection.saveData
        };
    }
    
    addCustomMetric(name, value) {
        if (!this.collecting) {
            this._collectMetrics();
        }
        
        const latestMetric = this.metrics[this.metrics.length - 1];
        if (latestMetric) {
            latestMetric.custom[name] = value;
        }
    }
    
    recordFrame() {
        this.currentSession.frameCount++;
    }
    
    recordInteraction(type) {
        this.currentSession.interactionCount++;
        
        if (window.performance && window.performance.mark) {
            window.performance.mark(`interaction-${type}`);
        }
    }
    
    getMetrics(count = null) {
        if (count) {
            return this.metrics.slice(-count);
        }
        return [...this.metrics];
    }
    
    getLatestMetric() {
        return this.metrics[this.metrics.length - 1] || null;
    }
    
    getAverageMetrics() {
        if (this.metrics.length === 0) {
            return null;
        }
        
        const avg = {
            fps: 0,
            memory: {
                usedPercent: 0
            },
            count: this.metrics.length
        };
        
        let fpsSum = 0;
        let memoryPercentSum = 0;
        let fpsCount = 0;
        let memoryCount = 0;
        
        this.metrics.forEach(m => {
            if (m.fps !== null) {
                fpsSum += m.fps;
                fpsCount++;
            }
            if (m.memory && m.memory.usedPercent !== null) {
                memoryPercentSum += m.memory.usedPercent;
                memoryCount++;
            }
        });
        
        avg.fps = fpsCount > 0 ? fpsSum / fpsCount : null;
        avg.memory.usedPercent = memoryCount > 0 ? memoryPercentSum / memoryCount : null;
        
        return avg;
    }
    
    getSessionStats() {
        const now = Date.now();
        const duration = now - this.currentSession.startTime;
        
        return {
            duration,
            durationFormatted: this._formatDuration(duration),
            frameCount: this.currentSession.frameCount,
            interactionCount: this.currentSession.interactionCount,
            avgFPS: this.currentSession.frameCount > 0 
                ? (this.currentSession.frameCount / (duration / 1000)) 
                : null,
            interactionsPerMinute: duration > 0 
                ? (this.currentSession.interactionCount / (duration / 60000)) 
                : 0
        };
    }
    
    _formatDuration(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) {
            return `${hours}h ${minutes % 60}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds % 60}s`;
        } else {
            return `${seconds}s`;
        }
    }
    
    exportMetrics() {
        return {
            startTimestamp: this.startTimestamp,
            session: this.getSessionStats(),
            metrics: this.metrics,
            average: this.getAverageMetrics()
        };
    }
    
    clearMetrics() {
        this.metrics = [];
        this.currentSession = {
            startTime: Date.now(),
            frameCount: 0,
            interactionCount: 0
        };
    }
}

const userManager = new UserManager();
const performanceMonitor = new PerformanceMonitor();